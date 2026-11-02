"""E2 analysis (T3 chip-gain controls on hw1). Decision rules: analysis/chip_controls/PLAN.md (written before generation).

    . .venv/bin/activate && python src/analyze_chip_controls.py

Comparators: runs/hw1 P0 channels noncrit and chip1 (draw d0). Controls: runs/hwctl1 P0 channels irrel and nlcue.
Same population/estimators as src/analyze_hw1.py (A.normalize_table recomputation, hw_rules exclusions, A.family_bootstrap),
writer-cluster primary, family-cluster comparison, plus a t interval over writers. Writes analysis/chip_controls/.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A  # noqa: E402
import analyze_hw1 as H  # noqa: E402  (loads hw1 scored.parquet, asserts, defines build/boot)

OUT = ROOT / "analysis/chip_controls"; B = 10000; SEED = 20261031
kept, raw_hw1 = H.kept, H.raw0
ctl = pd.read_parquet(ROOT / "runs/hwctl1/scored.parquet")
assert not ctl.critical_source.isin(["J1", "J2"]).any()
unresolved = int((ctl.valid.astype(bool) & ctl.critical.isna()).sum())
RELABEL = {"irrel": "noncrit", "nlcue": "chip1"}      # normalize_table only needs a standard channel name; critical_match does not depend on it
ctl2 = ctl.assign(channel_real=ctl.channel, channel=ctl.channel.map(RELABEL))
d_ctl, ex = H.build(kept, ctl2)
d_ctl["channel"] = d_ctl.channel_real
d_hw1, ex2 = H.build(kept, raw_hw1); assert ex == ex2
d_hw1 = d_hw1[d_hw1.channel.isin(["noncrit", "chip1"])]
d = pd.concat([d_hw1[d_hw1.prompt_id == "P0"], d_ctl[d_ctl.prompt_id == "P0"]], ignore_index=True)
mp = json.loads((ROOT / "analysis/chip_controls/mapping.json").read_text())
borderline = {x["family_id"] for x in mp["per_family"] if x["borderline"]}

keys = ["family_id", "writer_id", "variant", "dimension", "model"]
w = d.pivot(index=keys, columns="channel", values="critical_match").reset_index()
for c in ("noncrit", "chip1", "irrel", "nlcue"):
    w[c] = pd.to_numeric(w[c]).astype(float)
CON = {"G_chip (chip1-noncrit)": ("chip1", "noncrit"), "G_irrel (irrel-noncrit)": ("irrel", "noncrit"),
       "G_nl (nlcue-noncrit)": ("nlcue", "noncrit"), "chip1-irrel [primary]": ("chip1", "irrel"),
       "chip1-nlcue [primary]": ("chip1", "nlcue")}


def tci(g, col):
    m = g.groupby("writer_id")[col].mean().dropna()
    if len(m) < 3: return (np.nan, np.nan)
    se = m.std(ddof=1) / np.sqrt(len(m)); t = stats.t.ppf(.975, len(m) - 1)
    return (float(m.mean() - t * se), float(m.mean() + t * se))


def run(w, tag, models=True):
    rows = []
    for dim, g in w.groupby("dimension"):
        for model in (["ALL"] + sorted(g.model.unique())) if models else ["ALL"]:
            x = g if model == "ALL" else g[g.model == model]
            for name, (l, r) in CON.items():
                x = x.assign(v=x[l] - x[r])
                bw = H.boot(x, "v", cluster="writer_id"); bf = H.boot(x, "v", cluster="family_id")
                lo, hi = tci(x, "v")
                rows.append(dict(set=tag, dimension=dim, model=model, contrast=name, estimate=bw["estimate"], writer_lo=bw["ci_low"], writer_hi=bw["ci_high"],
                                 family_lo=bf["ci_low"], family_hi=bf["ci_high"], t_writer_lo=lo, t_writer_hi=hi, n=bw["n"],
                                 n_writers=bw["n_clusters"], n_families=bw["n_families"]))
    return pd.DataFrame(rows)


main_ = run(w, "all_kept")
sens = run(w[~w.family_id.isin(borderline)], "drop_borderline_certainty_TELL", models=False)
res = pd.concat([main_, sens]); res.to_csv(OUT / "chip_controls.csv", index=False)

# per-channel critical-match rates (descriptive)
rate_rows = []
for dim, g in w.groupby("dimension"):
    for model in ["ALL"] + sorted(g.model.unique()):
        x = g if model == "ALL" else g[g.model == model]
        r = dict(dimension=dim, model=model)
        for c in ("noncrit", "chip1", "irrel", "nlcue"):
            b = H.boot(x, c, cluster="writer_id"); r |= {c: b["estimate"], f"{c}_lo": b["ci_low"], f"{c}_hi": b["ci_high"]}
        r["n"] = len(x); rate_rows.append(r)
rates = pd.DataFrame(rate_rows); rates.to_csv(OUT / "channel_rates.csv", index=False)

# literalization: bracketed chip copied, or "I tell you" / "statement" words, per channel x model
d["bracket"] = d.text.fillna("").str.contains(r"\[|\]")
d["tellyou"] = d.text.fillna("").str.contains(r"\b(?:I|we) (?:tell|told) you\b|\bstatement\b|\bI request\b|\bquestion:", case=False, regex=True)
lit = d[d.valid.astype(bool)].groupby(["channel", "model"])[["bracket", "tellyou"]].mean().reset_index()
lit.to_csv(OUT / "literalization.csv", index=False)

# decision rule (PLAN.md): per dimension, ALL models, writer-cluster CI
dec = {}
for dim in sorted(w.dimension.unique()):
    m = main_[(main_.dimension == dim) & (main_.model == "ALL")].set_index("contrast")
    a = m.loc["chip1-irrel [primary]"]; n = m.loc["chip1-nlcue [primary]"]
    cue = "chip effect is cue content (chip1-irrel CI > 0)" if a.writer_lo > 0 else "NOT shown to exceed any-chip (report as manipulation check / generic token)"
    if n.writer_lo > 0: nl = "chip beats natural language"
    elif n.writer_hi < 0: nl = "natural language beats chip"
    elif n.writer_lo >= -.05 and n.writer_hi <= .05: nl = "NL equals chip (CI within +/-5 pp)"
    else: nl = "inconclusive"
    dec[dim] = dict(chip1_minus_irrel=float(a.estimate), irrel_ci=[float(a.writer_lo), float(a.writer_hi)], vs_irrel=cue,
                    chip1_minus_nlcue=float(n.estimate), nl_ci=[float(n.writer_lo), float(n.writer_hi)], vs_nl=nl)
summary = dict(n_hw1_rows=len(d_hw1), n_ctl_rows=len(d_ctl), unresolved_valid_ctl_rows=unresolved, excluded_families=sorted(ex),
               n_families=int(w.family_id.nunique()), writers=int(w.writer_id.nunique()), decision_by_dimension=dec,
               borderline_families=sorted(borderline))
(OUT / "summary.json").write_text(json.dumps(summary, indent=1))


def f(x): return f"{100 * x:+.1f}"


md = ["# E2: chip-gain controls on hw1 (T3)\n",
      "Decision rules: `analysis/chip_controls/PLAN.md` (written before generation). Outcome = P0 `critical_match`, paired by family x variant x model, "
      "pooled over 4 models. Comparators `noncrit`, `chip1` from `runs/hw1` (d0); controls `irrel`, `nlcue` from `runs/hwctl1`. "
      f"Labels J1==J2 else blind arbiter, no fallback ({unresolved} valid control rows unresolved). Writer-cluster CI is primary (7 writers; speech-act n excludes the hw1 quarantine); "
      "family-cluster CI and a t interval over writers are alongside.\n",
      "## Critical-match rate by channel (pooled models; writer-cluster 95% CI)\n", "| dimension | noncrit | chip1 | irrel | nlcue | n |", "|---|---|---|---|---|---|"]
for r in rates[rates.model == "ALL"].itertuples():
    md.append(f"| {r.dimension} | {100*r.noncrit:.1f} | {100*r.chip1:.1f} | {100*r.irrel:.1f} | {100*r.nlcue:.1f} | {r.n} |")
md += ["\n## Gains and control contrasts, pooled over models (pp)\n",
       "| dimension | contrast | estimate | writer-cluster 95% CI | family-cluster 95% CI | t over writers 95% CI | writers | families |", "|---|---|---|---|---|---|---|---|"]
for r in main_[main_.model == "ALL"].itertuples():
    md.append(f"| {r.dimension} | {r.contrast} | {f(r.estimate)} | [{f(r.writer_lo)}, {f(r.writer_hi)}] | [{f(r.family_lo)}, {f(r.family_hi)}] | [{f(r.t_writer_lo)}, {f(r.t_writer_hi)}] | {r.n_writers} | {r.n_families} |")
md += ["\n## Pre-declared reading per dimension\n", "| dimension | chip1 - irrel | vs any-chip | chip1 - nlcue | vs natural language |", "|---|---|---|---|---|"]
for k, v in dec.items():
    md.append(f"| {k} | {f(v['chip1_minus_irrel'])} [{f(v['irrel_ci'][0])}, {f(v['irrel_ci'][1])}] | {v['vs_irrel']} | {f(v['chip1_minus_nlcue'])} [{f(v['nl_ci'][0])}, {f(v['nl_ci'][1])}] | {v['vs_nl']} |")
md += ["\n## Per model: chip1 - irrel and chip1 - nlcue (pp, writer-cluster CI)\n", "| dimension | model | chip1 - irrel | chip1 - nlcue |", "|---|---|---|---|"]
pm = main_[main_.model != "ALL"]
for (dim, model), g in pm.groupby(["dimension", "model"]):
    a = g[g.contrast == "chip1-irrel [primary]"].iloc[0]; n = g[g.contrast == "chip1-nlcue [primary]"].iloc[0]
    md.append(f"| {dim} | {model} | {f(a.estimate)} [{f(a.writer_lo)}, {f(a.writer_hi)}] | {f(n.estimate)} [{f(n.writer_lo)}, {f(n.writer_hi)}] |")
md += ["\n## Sensitivity: drop the 3 borderline certainty items with irrelevant chip [TELL] (pooled models)\n", "| dimension | contrast | estimate | writer CI |", "|---|---|---|---|"]
for r in sens[sens.dimension == "certainty"].itertuples():
    md.append(f"| {r.dimension} | {r.contrast} | {f(r.estimate)} | [{f(r.writer_lo)}, {f(r.writer_hi)}] |")
md += ["\n## Literalization (share of valid outputs with a bracket, or 'I tell you' / 'statement' words)\n", "| channel | model | bracket | tell-you/statement words |", "|---|---|---|---|"]
for r in lit.itertuples():
    md.append(f"| {r.channel} | {r.model} | {100*r.bracket:.1f}% | {100*r.tellyou:.1f}% |")
(OUT / "report.md").write_text("\n".join(md) + "\n")
print(json.dumps(summary["decision_by_dimension"], indent=1))
