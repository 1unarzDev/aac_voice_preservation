"""Model-breadth analysis: the larger local models (Qwen2.5-14B, Mistral-Nemo-12B) next to the four original models.

    . .venv/bin/activate && python src/analyze_model_breadth.py

Same populations and estimators as src/analyze_hw1.py (P1/P2/P3 frames, writer-cluster bootstrap), src/analyze_legend.py
(arms a/b/c, draw d1) and src/analyze_chip_controls.py (chip1 - noncrit / irrel / nlcue). Original four models come from
runs/{hw1,legend1,hwctl1}; new models from runs/ext_{hw,legend1,hwctl}_{qwen14,nemo} (same prompts and inputs, only the model differs).
Labels: J1==J2 else blind arbiter, no fallback (asserted). Writes analysis/model_breadth/{report.md,summary.json,*.csv}.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A  # noqa: E402
import analyze_hw1 as H  # noqa: E402

OUT = ROOT / "analysis/model_breadth"; OUT.mkdir(parents=True, exist_ok=True)
OLD = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
NEWK = {"qwen2.5-14b": "qwen14", "mistral-nemo-12b": "nemo"}
NEW = [m for m, k in NEWK.items() if (ROOT / f"runs/ext_hw_{k}/scored.parquet").exists()]
MODELS = OLD + NEW


def load(base, ext_fmt):
    parts = [pd.read_parquet(ROOT / f"runs/{base}/scored.parquet")]
    for m in NEW:
        parts.append(pd.read_parquet(ROOT / "runs" / ext_fmt.format(k=NEWK[m]) / "scored.parquet"))
    df = pd.concat(parts, ignore_index=True)
    assert not df.critical_source.isin(["J1", "J2"]).any(), "fallback labels present"
    return df


meta = {}
# ---------------- hw1 (547 kept families)
raw = load("hw1", "ext_hw_{k}")
kept = H.kept
raw = raw[raw.family_id.isin(kept)]
meta["hw_unresolved_valid"] = int((raw.valid.astype(bool) & raw.critical.isna()).sum())
d_hw, excl = H.build(kept, raw)
d_hw = d_hw[d_hw.prompt_id == "P0"]
meta["hw_rows_by_model"] = raw.groupby("model").size().to_dict()
meta["hw_families_analysed"] = int(d_hw.family_id.nunique()); meta["hw_writers"] = int(d_hw.writer_id.nunique())

# ---------------- chip controls
ctl = load("hwctl1", "ext_hwctl_{k}")
meta["ctl_unresolved_valid"] = int((ctl.valid.astype(bool) & ctl.critical.isna()).sum())
RELABEL = {"irrel": "noncrit", "nlcue": "chip1"}
d_ctl, ex2 = H.build(kept, ctl.assign(channel_real=ctl.channel, channel=ctl.channel.map(RELABEL)))
d_ctl["channel"] = d_ctl.channel_real
assert excl == ex2
d_ctl = d_ctl[d_ctl.prompt_id == "P0"]
d_c = pd.concat([d_hw[d_hw.channel.isin(["noncrit", "chip1"])], d_ctl], ignore_index=True)
keys = ["family_id", "writer_id", "variant", "dimension", "model"]
w = d_c.pivot(index=keys, columns="channel", values="critical_match").reset_index()
for c in ("noncrit", "chip1", "irrel", "nlcue"):
    w[c] = pd.to_numeric(w[c]).astype(float)
w["g_noncrit"] = w.chip1 - w.noncrit       # chip gain over the noncritical word
w["g_irrel"] = w.chip1 - w.irrel           # chip gain over an irrelevant chip
w["g_word"] = w.chip1 - w.nlcue            # chip vs the plain-word (natural language) cue
w["gain_irrel_alone"] = w.irrel - w.noncrit

rows = []
for dim, g in w.groupby("dimension"):
    for model in MODELS:
        x = g[g.model == model]
        if x.empty: continue
        r = dict(dimension=dim, model=model, n=len(x), writers=int(x.writer_id.nunique()), families=int(x.family_id.nunique()))
        for col in ("g_noncrit", "g_irrel", "g_word", "gain_irrel_alone"):
            b = H.boot(x, col, "writer_id"); f = H.boot(x, col, "family_id")
            r |= {col: b["estimate"], col + "_lo": b["ci_low"], col + "_hi": b["ci_high"], col + "_flo": f["ci_low"], col + "_fhi": f["ci_high"]}
        rows.append(r)
chip = pd.DataFrame(rows); chip.to_csv(OUT / "chip_contrasts_by_model.csv", index=False)

# ---------------- P1 / P2 / P3 and full-channel critical match
fr = H.frames(d_hw)
reg = []
for k, f in fr.items():
    for m in MODELS:
        g = f[f.model == m]
        if g.empty: continue
        col = "value"
        if k == "P3":
            g = g.assign(share=g.value + .5); col = "share"
        b = H.boot(g, col, "writer_id"); fm = H.boot(g, col, "family_id")
        reg.append(dict(contrast=k, model=m, estimate=b["estimate"], writer_lo=b["ci_low"], writer_hi=b["ci_high"],
                        family_lo=fm["ci_low"], family_hi=fm["ci_high"], n=b["n"], writers=b["n_clusters"]))
regdf = pd.DataFrame(reg); regdf.to_csv(OUT / "registered_by_model.csv", index=False)

fullrows = []
full = d_hw[d_hw.channel == "full"].copy(); full["m"] = pd.to_numeric(full.critical_match).astype(float)
for dim in H.DIMS:
    for m in MODELS + ["ALL4_orig"]:
        g = full[(full.dimension == dim) & ((full.model == m) if m != "ALL4_orig" else full.model.isin(OLD))]
        if g.empty: continue
        b = H.boot(g, "m", "writer_id"); f = H.boot(g, "m", "family_id")
        fullrows.append(dict(dimension=dim, model=m, estimate=b["estimate"], writer_lo=b["ci_low"], writer_hi=b["ci_high"],
                             family_lo=f["ci_low"], family_hi=f["ci_high"], n=b["n"]))
fulldf = pd.DataFrame(fullrows); fulldf.to_csv(OUT / "full_channel_critical_match.csv", index=False)

# ---------------- legend test
sc = load("legend1", "ext_legend1_{k}")
ARM = {"P0": "a_legend", "P0n": "b_nolegend", "P0m": "c_markers_missing"}
req = {}
import glob
for fn in [ROOT / "runs/requests/legend1.jsonl"] + [Path(p) for p in glob.glob(str(ROOT / "runs/requests/ext_*_legend1.jsonl"))]:
    for l in fn.open():
        r = json.loads(l); req[r["request_key"]] = (r["prompt_id"], r.get("namespace") or "d0")
items = {}
for l in (ROOT / "data/items_ext/legend_items.jsonl").open():
    dd = json.loads(l); items[dd["family_id"]] = dd
sc["arm"] = sc.request_key.map(lambda k: ARM[req[k][0]]); sc["draw"] = sc.request_key.map(lambda k: req[k][1])
sc["source_set"] = sc.family_id.map(lambda f: items[f]["source_set"])
sc["writer_id"] = sc.family_id.map(lambda f: items[f].get("writer_id", f))
sc = sc.sort_values("variant").drop_duplicates(["family_id", "model", "arm", "draw", "request_key", "suggestion_idx"]).copy()
vb = sc.valid.astype(bool)
meta["legend_unresolved_valid"] = int((vb & sc.critical.isna()).sum())
cm = vb & sc.critical.isin(["affirmative", "negated"])
sc["aff"] = np.where(cm, (sc.critical == "affirmative").astype(float), np.nan)
sc["commit"] = np.where(vb & sc.critical.notna(), sc.critical.isin(["affirmative", "negated"]).astype(float), np.nan)
lrows = []
for draw in ("d1", "d2"):
    for m in MODELS:
        for arm in ARM.values():
            g = sc[(sc.model == m) & (sc.arm == arm) & (sc.draw == draw)]
            if g.empty: continue
            b = H.boot(g, "aff", "family_id"); c = H.boot(g, "commit", "family_id")
            gh = g[g.source_set == "hw1"]; bw = H.boot(gh, "aff", "writer_id")
            lrows.append(dict(draw=draw, model=m, arm=arm, aff=b["estimate"], lo=b["ci_low"], hi=b["ci_high"], n=b["n"], commit=c["estimate"],
                              hw1_aff=bw["estimate"], hw1_writer_lo=bw["ci_low"], hw1_writer_hi=bw["ci_high"], hw1_n=bw["n"]))
legdf = pd.DataFrame(lrows); legdf.to_csv(OUT / "legend_arms_by_model.csv", index=False)

# ---------------- pattern checks (pre-stated readings; same rules as PLAN.md files of the original tests)
def row(df, **kw):
    q = df
    for k, v in kw.items(): q = q[q[k] == v]
    return q.iloc[0]

checks = {}
for m in MODELS:
    c = {}
    p3 = row(regdf, contrast="P3", model=m); c["bare_affirmative_share"] = float(p3.estimate)
    c["bare_default_holds(share>=0.90)"] = bool(p3.estimate >= .9)
    la = {a: row(legdf, draw="d1", model=m, arm=a) for a in ARM.values()}
    c["legend_arms_d1"] = {a: float(r.aff) for a, r in la.items()}
    c["not_legend_artifact(b and c >=0.90)"] = bool(la["b_nolegend"].aff >= .9 and la["c_markers_missing"].aff >= .9)
    p1 = row(regdf, contrast="P1", model=m); c["speech_act_chip_contrast_pp"] = float(100 * p1.estimate)
    c["speech_act_chip_contrast_writer_lo_gt0"] = bool(p1.writer_lo > 0)
    ci = {}
    for dim in H.DIMS:
        r = row(chip, dimension=dim, model=m)
        ci[dim] = dict(chip_over_noncrit_pp=float(100 * r.g_noncrit), chip_over_irrel_pp=float(100 * r.g_irrel), irrel_lo_gt0=bool(r.g_irrel_lo > 0),
                       chip_over_word_pp=float(100 * r.g_word), word_equals_chip_within5=bool(r.g_word_lo >= -.05 and r.g_word_hi <= .05))
    c["per_dimension"] = ci
    c["full_critical_match"] = {dim: float(row(fulldf, dimension=dim, model=m).estimate) for dim in H.DIMS}
    checks[m] = c

summary = dict(models=MODELS, new_models=NEW, meta=meta, checks=checks, seed=H.SEED, n_boot=H.B,
               cluster="writer_id (hw1/chip/full/P1-P3; 6-7 writers) and family_id (legend pooled over hw1+W-C, 184 families)")
(OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))

# ---------------- report
def p(x): return f"{100 * x:.1f}"
def s(x): return f"{100 * x:+.1f}"
md = ["# Model breadth: larger local open models next to the four original models\n",
      "New models: " + ", ".join(NEW) + " (Q4_K_M GGUF, llama.cpp, same prompts/inputs/greedy decoding/request files as the original models; only the model id differs). "
      "Original: qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra. Labels: J1==J2 else blind arbiter, no fallback "
      f"(unresolved valid rows: hw {meta['hw_unresolved_valid']}, controls {meta['ctl_unresolved_valid']}, legend {meta['legend_unresolved_valid']}). "
      f"hw1 population: {meta['hw_families_analysed']} analysed families (547 kept minus the speech-act refusal/acceptance quarantine and writer P06's speech-act pair), {meta['hw_writers']} writers; "
      "writer-cluster 95% bootstrap CIs (10,000 resamples) unless stated.\n",
      "## 1. Bare default: affirmative share among committed polarity outputs (hw1, bare channel, polarity families)\n",
      "| model | share [writer 95% CI] | family-cluster CI | n |", "|---|---|---|---|"]
for m in MODELS:
    r = row(regdf, contrast="P3", model=m)
    md.append(f"| {m}{' (new)' if m in NEW else ''} | {p(r.estimate)} [{p(r.writer_lo)}, {p(r.writer_hi)}] | [{p(r.family_lo)}, {p(r.family_hi)}] | {int(r.n)} |")
md += ["\n## 2. Legend test (draw d1; affirmative share among committed outputs; 184 families = hw1 104 + W-C 80; family-cluster CI)\n",
       "| model | (a) legend | (b) no legend | (c) markers may be missing | commitment rate a/b/c | hw1-only a/b/c (writer CI upper bounds) |", "|---|---|---|---|---|---|"]
for m in MODELS:
    rr = {a: row(legdf, draw="d1", model=m, arm=a) for a in ARM.values()}
    md.append(f"| {m}{' (new)' if m in NEW else ''} | " + " | ".join(f"{p(r.aff)} [{p(r.lo)}, {p(r.hi)}]" for r in rr.values()) +
              " | " + " / ".join(p(r.commit) for r in rr.values()) + " | " + " / ".join(f"{p(r.hw1_aff)} (hi {p(r.hw1_writer_hi)})" for r in rr.values()) + " |")
md += ["\nReplication draw d2 (a / b / c):\n", "| model | a | b | c |", "|---|---|---|---|"]
for m in MODELS:
    rr = [row(legdf, draw="d2", model=m, arm=a) for a in ARM.values() if not legdf[(legdf.draw == "d2") & (legdf.model == m) & (legdf.arm == a)].empty]
    md.append(f"| {m} | " + " | ".join(p(r.aff) for r in rr) + " |")
md += ["\n## 3. Speech-act chip contrast (P1: chip1 - noncritical word, speech-act families) and politeness addition (P2)\n",
       "| contrast | model | estimate pp | writer CI | family CI | n | writers |", "|---|---|---|---|---|---|---|"]
for k in ("P1", "P2"):
    for m in MODELS:
        r = row(regdf, contrast=k, model=m)
        md.append(f"| {k} | {m}{' (new)' if m in NEW else ''} | {s(r.estimate)} | [{s(r.writer_lo)}, {s(r.writer_hi)}] | [{s(r.family_lo)}, {s(r.family_hi)}] | {int(r.n)} | {int(r.writers)} |")
md += ["\n## 4. Chip gain per dimension (pp, writer-cluster 95% CI)\n",
       "chip1 - noncrit = gain over the noncritical word; chip1 - irrel = gain over an irrelevant chip from another dimension (cue content, not any chip); "
       "chip1 - word = chip versus the same meaning as a plain word (0 = the plain word does as well as the chip).\n",
       "| dimension | model | chip1 - noncrit | chip1 - irrel | irrel - noncrit | chip1 - plain word | writers |", "|---|---|---|---|---|---|---|"]
for dim in H.DIMS:
    for m in MODELS:
        r = row(chip, dimension=dim, model=m)
        f = lambda c: f"{s(r[c])} [{s(r[c + '_lo'])}, {s(r[c + '_hi'])}]"
        md.append(f"| {dim} | {m}{' (new)' if m in NEW else ''} | {f('g_noncrit')} | {f('g_irrel')} | {f('gain_irrel_alone')} | {f('g_word')} | {int(r.writers)} |")
md += ["\n## 5. Critical match on the `full` channel (typed sentence; % of valid outputs honouring the item's critical value; writer CI)\n",
       "| dimension | " + " | ".join(MODELS) + " |", "|---|" + "---|" * len(MODELS)]
for dim in H.DIMS:
    md.append(f"| {dim} | " + " | ".join(f"{p(row(fulldf, dimension=dim, model=m).estimate)} [{p(row(fulldf, dimension=dim, model=m).writer_lo)}, {p(row(fulldf, dimension=dim, model=m).writer_hi)}]" for m in MODELS) + " |")
md += ["\n## 6. Pattern checks (computed)\n", "| model | bare default >= 90% | legend b and c >= 90% | P1 writer CI > 0 | chip1 - irrel CI > 0 in all 6 dims | chip1 - plain word within +/-5 pp (dims) |", "|---|---|---|---|---|---|"]
for m in MODELS:
    c = checks[m]; pdm = c["per_dimension"]
    md.append(f"| {m} | {c['bare_default_holds(share>=0.90)']} | {c['not_legend_artifact(b and c >=0.90)']} | {c['speech_act_chip_contrast_writer_lo_gt0']} | "
              f"{all(v['irrel_lo_gt0'] for v in pdm.values())} ({sum(v['irrel_lo_gt0'] for v in pdm.values())}/6) | {sum(v['word_equals_chip_within5'] for v in pdm.values())}/6 |")
(OUT / "report.md").write_text("\n".join(md) + "\n")
print("\n".join(md[-12:]))
