"""Gemini model-breadth report: legend test (E1 arms a, c) and chip-gain controls (E2) for Google Gemini models,
with the same metrics, estimators and seeds as analysis/legend_test and analysis/chip_controls so the tables sit side by side.

    . .venv/bin/activate && python src/analyze_model_breadth_gemini.py

Re-run after every daily batch: it uses whatever is judged and attributed so far (runs/gem_<model>_{legend,hw,hwctl}/scored.parquet,
produced by src/gemini_daily.py finalize) and reports n per cell. Nothing is imputed: rows without an agreed or arbitrated critical label
are missing and counted. Writes analysis/model_breadth/gemini_report.md and gemini_summary.json (+ gemini_*.csv).

Differences from the existing analyses (declared, because Gemini has a single draw and a partial tier at any time):
- Legend: only arms a (P0, legend) and c (P0m, markers may be missing), draw d1; arm b (no legend) was not scheduled. The E1 decision rule
  needs arm b, so the verdict here is reported on the available arms only ("a and c both >= 90%" = default is not a legend artifact on
  that arm; arm b not tested for Gemini).
- Chip controls: dimensions polarity and speech_act only (tier 2), same exclusions as analysis/hw1 (speech-act refusal/acceptance
  quarantine, writer P06), writer-cluster bootstrap primary, family-cluster alongside, 10,000 resamples, seed 20261031.
- The hw1 six-dimension table (tier 3) reports critical-match by channel with writer-cluster CIs where the channel is available.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A  # noqa: E402
import analyze_hw1 as H  # noqa: E402  (module level only loads hw1 scored data and defines build/boot; writes nothing)

OUT = ROOT / "analysis/model_breadth"; OUT.mkdir(parents=True, exist_ok=True)
B = 10000; SEED = 20261031
MODELS = [m for m in ("gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview")
          if (ROOT / f"runs/requests/gemini_{m}_t1.jsonl").exists()]
short = lambda m: m.replace("gemini-", "").replace(".", "")
ARM = {"P0": "a_legend", "P0m": "c_markers_missing"}


def req_map(m, run):
    p = ROOT / f"runs/requests/gemini_{m}_run_{run}.jsonl"
    return {json.loads(l)["request_key"]: json.loads(l) for l in p.read_text().splitlines() if l.strip()} if p.exists() else {}


def load_scored(m, run):
    p = ROOT / f"runs/gem_{short(m)}_{run}/scored.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    assert not df.critical_source.isin(["J1", "J2"]).any(), "fallback labels present"
    return df


def cached_n(m, run):
    rq = req_map(m, run)
    return sum((ROOT / f"runs/cache/{k}.json").exists() for k in rq), len(rq)


def boot_fam(g, col, cluster="family_id"):
    x = g.copy(); x["family_id"] = x[cluster]
    r = A.family_bootstrap(x, col, n_boot=B, seed=SEED)
    r["n_clusters"] = r.pop("n_families"); r.pop("n_families_observed", None); return r


# ------------------------------------------------------------------ legend
def legend_cells(m):
    sc = load_scored(m, "legend")
    if sc is None:
        return None, 0
    rq = req_map(m, "legend")
    items = {json.loads(l)["family_id"]: json.loads(l) for l in (ROOT / "data/items_ext/legend_items.jsonl").read_text().splitlines()}
    sc = sc.copy()
    sc["arm"] = sc.request_key.map(lambda k: ARM[rq[k]["prompt_id"]] if k in rq else None)
    sc = sc[sc.arm.notna()]
    sc["source_set"] = sc.family_id.map(lambda f: items[f]["source_set"])
    sc["writer_id"] = sc.family_id.map(lambda f: items[f].get("writer_id", f))
    sc = sc.sort_values("variant").drop_duplicates(["family_id", "model", "arm", "request_key", "suggestion_idx"]).copy()
    v = sc.valid.astype(bool)
    unresolved = int((v & sc.critical.isna()).sum())
    known = v & sc.critical.notna()
    cm = v & sc.critical.isin(["affirmative", "negated"])
    sc["aff"] = np.where(cm, (sc.critical == "affirmative").astype(float), np.nan)
    sc["aff_all"] = np.where(known, (sc.critical == "affirmative").astype(float), np.nan)
    sc["neg_all"] = np.where(known, (sc.critical == "negated").astype(float), np.nan)
    sc["commit"] = np.where(known, sc.critical.isin(["affirmative", "negated"]).astype(float), np.nan)
    sc["unclear_all"] = 1 - sc.commit
    rows = []
    for sname, s in {"pooled": sc, "hw1": sc[sc.source_set == "hw1"], "WC": sc[sc.source_set == "WC"]}.items():
        for arm in ARM.values():
            g = s[s.arm == arm]
            if g.empty:
                continue
            row = dict(model=m, source=sname, arm=arm, n_rows=len(g), n_families=g.family_id.nunique())
            for col in ("aff", "aff_all", "neg_all", "commit", "unclear_all"):
                r = boot_fam(g, col); row |= {col: r["estimate"], f"{col}_lo": r["ci_low"], f"{col}_hi": r["ci_high"], f"{col}_n": r["n"]}
            rows.append(row)
    return pd.DataFrame(rows), unresolved


# ------------------------------------------------------------------ chip controls
CON = {"G_chip (chip1-noncrit)": ("chip1", "noncrit"), "G_irrel (irrel-noncrit)": ("irrel", "noncrit"),
       "G_nl (nlcue-noncrit)": ("nlcue", "noncrit"), "chip1-irrel [primary]": ("chip1", "irrel"),
       "chip1-nlcue [primary]": ("chip1", "nlcue")}
RELABEL = {"irrel": "noncrit", "nlcue": "chip1"}


def cue_table(m):
    hw, ctl = load_scored(m, "hw"), load_scored(m, "hwctl")
    parts, unresolved = [], 0
    if hw is not None:
        hw = hw[hw.dimension.isin(["polarity", "speech_act"]) & hw.channel.isin(["noncrit", "chip1"])]
        unresolved += int((hw.valid.astype(bool) & hw.critical.isna()).sum())
        d, _ = H.build(H.kept, hw); parts.append(d[d.prompt_id == "P0"])
    if ctl is not None:
        ctl = ctl[ctl.dimension.isin(["polarity", "speech_act"])]
        unresolved += int((ctl.valid.astype(bool) & ctl.critical.isna()).sum())
        c2 = ctl.assign(channel_real=ctl.channel, channel=ctl.channel.map(RELABEL))
        d, _ = H.build(H.kept, c2); d["channel"] = d.channel_real; parts.append(d[d.prompt_id == "P0"])
    if not parts:
        return None, None, 0, None
    d = pd.concat(parts, ignore_index=True)
    d = d[d.critical_match.notna()]
    keys = ["family_id", "writer_id", "variant", "dimension", "model"]
    w = d.pivot_table(index=keys, columns="channel", values="critical_match", aggfunc="first", dropna=False).reset_index()
    for c in ("noncrit", "chip1", "irrel", "nlcue"):
        w[c] = pd.to_numeric(w[c], errors="coerce").astype(float) if c in w else np.nan
    rows, rate_rows = [], []
    for dim, g in w.groupby("dimension"):
        r = dict(model=m, dimension=dim)
        for c in ("noncrit", "chip1", "irrel", "nlcue"):
            x = g.dropna(subset=[c])
            if len(x):
                b = H.boot(x, c, cluster="writer_id"); r |= {c: b["estimate"], f"{c}_lo": b["ci_low"], f"{c}_hi": b["ci_high"], f"{c}_n": b["n"]}
            else:
                r |= {c: np.nan, f"{c}_lo": np.nan, f"{c}_hi": np.nan, f"{c}_n": 0}
        rate_rows.append(r)
        for name, (l, rr) in CON.items():
            x = g.assign(v=g[l] - g[rr]).dropna(subset=["v"])
            if x.empty:
                rows.append(dict(model=m, dimension=dim, contrast=name, estimate=np.nan, n=0)); continue
            bw = H.boot(x, "v", cluster="writer_id"); bf = H.boot(x, "v", cluster="family_id")
            rows.append(dict(model=m, dimension=dim, contrast=name, estimate=bw["estimate"], writer_lo=bw["ci_low"], writer_hi=bw["ci_high"],
                             family_lo=bf["ci_low"], family_hi=bf["ci_high"], n=bw["n"], n_writers=bw["n_clusters"], n_families=bw["n_families"]))
    d["bracket"] = d.text.fillna("").str.contains(r"\[|\]")
    lit = d[d.valid.astype(bool)].groupby("channel")["bracket"].agg(["mean", "size"]).reset_index().assign(model=m)
    return pd.DataFrame(rows), pd.DataFrame(rate_rows), unresolved, lit


# ------------------------------------------------------------------ hw1 six-dimension (tier 3)
def hw_rates(m):
    hw = load_scored(m, "hw")
    if hw is None:
        return None
    d, _ = H.build(H.kept, hw)
    d = d[(d.prompt_id == "P0") & d.critical_match.notna()].copy()
    d["match"] = pd.to_numeric(d.critical_match).astype(float)
    rows = []
    for (dim, ch), g in d.groupby(["dimension", "channel"]):
        b = H.boot(g, "match", cluster="writer_id")
        rows.append(dict(model=m, dimension=dim, channel=ch, critical_match=b["estimate"], lo=b["ci_low"], hi=b["ci_high"], n=b["n"], n_families=b["n_families"]))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ run
pct = lambda x: "NA" if pd.isna(x) else f"{100 * x:.1f}"
pp = lambda x: "NA" if pd.isna(x) else f"{100 * x:+.1f}"
summary = {"models": {}, "note": "partial tiers are reported as-is; n is per cell"}
md = ["# Gemini as a third model family: legend test and cue restoration\n",
      "Plan and priority order: `analysis/model_breadth/GEMINI_PLAN.md` (written before any request). Daily queue: `src/gemini_daily.py` "
      "(state `runs/gemini_daily_state.json`, log `runs/gemini_daily.log`). Judging: existing gpt judge (J1/J2), blind arbiter on disputed critical labels, "
      "attribution WITHOUT fallback: rows without an agreed or arbitrated label are missing, counted below, never imputed. "
      "Same estimators and seeds as `analysis/legend_test` and `analysis/chip_controls` (10,000 bootstrap resamples, seed 20261031).\n"]
leg_ref = pd.read_csv(ROOT / "analysis/legend_test/arm_share.csv")
leg_ref = leg_ref[(leg_ref.draw == "d1") & (leg_ref.source == "pooled") & leg_ref.arm.isin(ARM.values())]
cc_ref = pd.read_csv(ROOT / "analysis/chip_controls/chip_controls.csv")
cc_ref = cc_ref[(cc_ref.set == "all_kept") & cc_ref.dimension.isin(["polarity", "speech_act"])]
all_leg, all_cue, all_rate, all_hw, lits = [], [], [], [], []
for m in MODELS:
    s = {"cached_requests": {}, "unresolved_valid_rows": {}}
    for run in ("legend", "hw", "hwctl"):
        c, n = cached_n(m, run); s["cached_requests"][run] = {"cached": c, "planned": n}
    leg, unres_l = legend_cells(m)
    cue = cue_table(m); cue_t, rate_t, unres_c, lit = cue if cue[0] is not None else (None, None, 0, None)
    hwr = hw_rates(m)
    s["unresolved_valid_rows"] = {"legend": unres_l, "cue": unres_c}
    if leg is not None: all_leg.append(leg)
    if cue_t is not None: all_cue.append(cue_t); all_rate.append(rate_t); lits.append(lit)
    if hwr is not None: all_hw.append(hwr)
    summary["models"][m] = s
leg_df = pd.concat(all_leg) if all_leg else pd.DataFrame()
cue_df = pd.concat(all_cue) if all_cue else pd.DataFrame()
rate_df = pd.concat(all_rate) if all_rate else pd.DataFrame()
hw_df = pd.concat(all_hw) if all_hw else pd.DataFrame()
for name, df in (("legend", leg_df), ("cue_contrasts", cue_df), ("cue_rates", rate_df), ("hw1_six_dim_rates", hw_df)):
    if len(df): df.to_csv(OUT / f"gemini_{name}.csv", index=False)

md.append("## Progress (requests cached / planned, per run; unresolved valid rows after judging)\n")
md += ["| model | legend (tier 1) | hw run: tiers 2+3 | hwctl (tier 2) | unresolved legend rows | unresolved cue rows |", "|---|---|---|---|---|---|"]
for m, s in summary["models"].items():
    cr = s["cached_requests"]
    md.append(f"| {m} | {cr['legend']['cached']}/{cr['legend']['planned']} | {cr['hw']['cached']}/{cr['hw']['planned']} | {cr['hwctl']['cached']}/{cr['hwctl']['planned']} | "
              f"{s['unresolved_valid_rows']['legend']} | {s['unresolved_valid_rows']['cue']} |")
md.append("\n(`cached` = generated; the tables below use only generated AND judged AND label-resolved rows; arbiter pending rows are missing.)\n")

# ---- legend
md.append("## Tier 1: legend test, bare polarity inputs (draw d1; affirmative share among committed outputs)\n")
if len(leg_df):
    md += ["Reading rule (E1, arm b not scheduled for Gemini): default is NOT a legend artifact if both arms a and c >= 90%; reframe if either < 70%; else partly induced. "
           "Arm c reduces commitment (more `unclear/mixed`) when it is instructable; see commitment column.\n",
           "| model | source | arm | n outputs | n families | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |", "|---|---|---|---|---|---|---|---|---|"]
    for r in leg_df.sort_values(["model", "source", "arm"]).itertuples():
        md.append(f"| {r.model} | {r.source} | {r.arm} | {int(r.aff_n)} (of {r.n_rows}) | {r.n_families} | {pct(r.aff)} [{pct(r.aff_lo)}, {pct(r.aff_hi)}] | {pct(r.aff_all)} | {pct(r.commit)} | {pct(r.unclear_all)} |")
    summary["legend_pooled_sources"] = {}
    for m in leg_df.model.unique():
        x = leg_df[(leg_df.model == m) & (leg_df.source == "pooled")].set_index("arm")
        if {"a_legend", "c_markers_missing"} <= set(x.index):
            a, c = x.loc["a_legend"].aff, x.loc["c_markers_missing"].aff
            v = "default NOT a legend artifact (a and c >= 90%)" if a >= .9 and c >= .9 else ("REFRAME (an arm < 70%)" if min(a, c) < .7 else "PARTLY INDUCED (an arm in [70, 90))")
            summary["legend_pooled_sources"][m] = dict(a_aff=float(a), c_aff=float(c), a_commit=float(x.loc["a_legend"].commit), c_commit=float(x.loc["c_markers_missing"].commit),
                                                      n_a=int(x.loc["a_legend"].aff_n), n_c=int(x.loc["c_markers_missing"].aff_n), verdict=v)
            md.append(f"\n**{m} (pooled sources): {v}.** a {pct(a)}% (n={int(x.loc['a_legend'].aff_n)}), c {pct(c)}% (n={int(x.loc['c_markers_missing'].aff_n)}); "
                      f"commitment a {pct(x.loc['a_legend'].commit)}%, c {pct(x.loc['c_markers_missing'].commit)}%.")
    md += ["\n### Side by side: existing models, same arms, draw d1, pooled sources (`analysis/legend_test/arm_share.csv`)\n",
           "| model | arm | n | affirmative share [95% CI] | commitment rate |", "|---|---|---|---|---|"]
    for r in leg_ref.sort_values(["model", "arm"]).itertuples():
        md.append(f"| {r.model} | {r.arm} | {int(r.aff_n)} | {pct(r.aff)} [{pct(r.aff_lo)}, {pct(r.aff_hi)}] | {pct(r.commit)} |")
else:
    md.append("No judged legend rows yet.\n")

# ---- cue
md.append("\n## Tier 2: cue restoration on hw1 polarity and speech_act (critical match; paired by family x variant)\n")
if len(rate_df):
    md += ["### Critical-match rate by channel (writer-cluster 95% CI; n = scored family x variant pairs with that channel)\n",
           "| model | dimension | noncrit | chip1 | irrel | nlcue |", "|---|---|---|---|---|---|"]
    for r in rate_df.itertuples():
        f = lambda c: f"{pct(getattr(r, c))} [{pct(getattr(r, c + '_lo'))}, {pct(getattr(r, c + '_hi'))}] (n={int(getattr(r, c + '_n'))})"
        md.append(f"| {r.model} | {r.dimension} | {f('noncrit')} | {f('chip1')} | {f('irrel')} | {f('nlcue')} |")
    md += ["\n### Gains and control contrasts (pp; writer-cluster CI primary, family-cluster alongside)\n",
           "| model | dimension | contrast | estimate | writer-cluster 95% CI | family-cluster 95% CI | n pairs | writers | families |", "|---|---|---|---|---|---|---|---|---|"]
    for r in cue_df.itertuples():
        if r.n == 0:
            md.append(f"| {r.model} | {r.dimension} | {r.contrast} | NA (no paired rows yet) | | | 0 | | |"); continue
        md.append(f"| {r.model} | {r.dimension} | {r.contrast} | {pp(r.estimate)} | [{pp(r.writer_lo)}, {pp(r.writer_hi)}] | [{pp(r.family_lo)}, {pp(r.family_hi)}] | {int(r.n)} | {int(r.n_writers)} | {int(r.n_families)} |")
    summary["cue_decision"] = {}
    md.append("\n### Pre-declared reading (analysis/chip_controls/PLAN.md rules, per dimension, writer-cluster CI)\n")
    md += ["| model | dimension | chip1 - irrel | vs any-chip | chip1 - nlcue | vs natural language |", "|---|---|---|---|---|---|"]
    for (m, dim), g in cue_df.groupby(["model", "dimension"]):
        g = g.set_index("contrast")
        a, n = g.loc["chip1-irrel [primary]"], g.loc["chip1-nlcue [primary]"]
        if a.n == 0 or n.n == 0:
            md.append(f"| {m} | {dim} | incomplete | | incomplete | |"); continue
        cue = "chip effect is cue content (CI > 0)" if a.writer_lo > 0 else "NOT shown to exceed any-chip"
        nl = ("chip beats natural language" if n.writer_lo > 0 else "natural language beats chip" if n.writer_hi < 0
              else "NL equals chip (CI within +/-5 pp)" if n.writer_lo >= -.05 and n.writer_hi <= .05 else "inconclusive")
        summary["cue_decision"][f"{m}|{dim}"] = dict(chip1_minus_irrel=float(a.estimate), irrel_ci=[float(a.writer_lo), float(a.writer_hi)], n_irrel=int(a.n), vs_irrel=cue,
                                                     chip1_minus_nlcue=float(n.estimate), nl_ci=[float(n.writer_lo), float(n.writer_hi)], n_nl=int(n.n), vs_nl=nl)
        md.append(f"| {m} | {dim} | {pp(a.estimate)} [{pp(a.writer_lo)}, {pp(a.writer_hi)}] (n={int(a.n)}) | {cue} | {pp(n.estimate)} [{pp(n.writer_lo)}, {pp(n.writer_hi)}] (n={int(n.n)}) | {nl} |")
    md += ["\n### Side by side: existing models, pooled over the 4 models and per model (`analysis/chip_controls/chip_controls.csv`, writer-cluster CI)\n",
           "| model | dimension | G_chip | chip1 - irrel | chip1 - nlcue |", "|---|---|---|---|---|"]
    for (m, dim), g in cc_ref.groupby(["model", "dimension"]):
        g = g.set_index("contrast")
        cell = lambda k: f"{pp(g.loc[k].estimate)} [{pp(g.loc[k].writer_lo)}, {pp(g.loc[k].writer_hi)}]"
        md.append(f"| {m} | {dim} | {cell('G_chip (chip1-noncrit)')} | {cell('chip1-irrel [primary]')} | {cell('chip1-nlcue [primary]')} |")
    if lits:
        L = pd.concat(lits)
        md += ["\n### Literalization: share of valid outputs containing a bracketed chip\n", "| model | channel | bracket share | n |", "|---|---|---|---|"]
        for r in L.itertuples():
            md.append(f"| {r.model} | {r.channel} | {pct(r.mean)}% | {r.size} |")
else:
    md.append("No judged cue rows yet.\n")

# ---- hw1 six-dim
md.append("\n## Tier 3: hw1 P0, critical-match by dimension and channel (writer-cluster 95% CI, n per cell)\n")
if len(hw_df):
    ref = pd.read_csv(ROOT / "analysis/hw1/six_dim_rates.csv")
    ref = ref[(ref.metric == "critical_match") & (ref.model == "gpt-6.1-terra") & ref.channel.isin(["bare", "chip1", "full"])]
    md += ["| model | dimension | channel | critical match [95% CI] | n |  terra (hw1) |", "|---|---|---|---|---|---|"]
    for r in hw_df[hw_df.channel.isin(["bare", "chip1", "full"])].sort_values(["model", "dimension", "channel"]).itertuples():
        t = ref[(ref.dimension == r.dimension) & (ref.channel == r.channel)]
        tt = f"{pct(t.iloc[0].estimate)}" if len(t) else ""
        md.append(f"| {r.model} | {r.dimension} | {r.channel} | {pct(r.critical_match)} [{pct(r.lo)}, {pct(r.hi)}] | {r.n} | {tt} |")
else:
    md.append("Tier 3 not yet judged.\n")

md.append("\n## Caveats\n- One decoding configuration (T=0, thinking budget 0, no seed); free-tier model snapshots can change (model id in each cache entry).\n"
          "- Partial tiers are family-ordered prefixes (request-file order), so early n is a sample of families in file order, not random.\n"
          "- Machine-panel judging plus a blind Claude arbiter is not human validation.\n")
(OUT / "gemini_report.md").write_text("\n".join(md) + "\n")
(OUT / "gemini_summary.json").write_text(json.dumps(summary, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("wrote", OUT / "gemini_report.md")
