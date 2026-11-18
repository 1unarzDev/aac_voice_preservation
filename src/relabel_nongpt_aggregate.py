"""B2 aggregate: validate Claude labels, agreement vs human consensus (Part 13/20) and vs GPT judge, P1 re-run with Claude critical labels.
usage: . .venv/bin/activate && python src/relabel_nongpt_aggregate.py   (stored data only; 0 API calls)"""
from __future__ import annotations
import glob, json, sys, io, contextlib
from collections import Counter
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from agree_stats import cohen_kappa            # noqa: E402
from score_gold import wilson, kappa_boot      # noqa: E402
import robust_t6_small_cluster as T6           # noqa: E402
import analyze_hw1 as H1                       # noqa: E402
D = ROOT / "analysis/relabel_nongpt"
FIELDS = ["critical", "polarity", "speech_act", "agent", "certainty", "politeness"]

# ---- load units, validate
units, gen = {}, None
for f in sorted(glob.glob(str(D / "batches/b[0-9][0-9].json"))):
    b = json.load(open(f)); gen = b["general_dimensions"]
    for it in b["items"]: units[it["unit_id"]] = dict(it, batch=Path(f).stem)
umap = json.load(open(D / "unit_map.json")); assert set(umap) == set(units), "unit_map vs batches mismatch"
lab, problems = {}, []
nbatch_missing = [Path(f).stem for f in sorted(glob.glob(str(D / "batches/b[0-9][0-9].json"))) if not Path(f.replace(".json", "_labels.json")).exists()]
for f in sorted(glob.glob(str(D / "batches/*_labels.json"))):
    for r in json.load(open(f)):
        u = r["unit_id"]; L = r["labels"]
        if u not in units: problems.append((u, "unknown unit_id")); continue
        if u in lab: problems.append((u, "duplicate label")); continue
        if f.split("/")[-1].split("_")[0] != units[u]["batch"]: problems.append((u, "label in wrong batch file"))
        for k in FIELDS:
            opts = units[u]["critical_options"] if k == "critical" else gen[k]["options"]
            if L.get(k) not in opts: problems.append((u, f"invalid {k}={L.get(k)!r}"))
        lab[u] = L
missing = sorted(set(units) - set(lab))
bad = {u for u, _ in problems}
print(f"units {len(units)} labelled {len(lab)} missing {len(missing)} problems {len(problems)}")
valid = {u: L for u, L in lab.items() if u not in bad}

# ---- stats helper
def stat(pred, gold, seed=20261117):
    n = len(pred)
    if n == 0: return dict(n=0)
    k = sum(a == b for a, b in zip(pred, gold)); kap = cohen_kappa(pred, gold)
    kb = kappa_boot(pred, gold, seed=seed, reps=1000) if n > 1 else None
    return dict(n=n, agree=k, accuracy=round(k / n, 4), acc_ci=wilson(k, n), kappa=kap, kappa_ci=kb)

# ---- reference tables
hc = pd.read_csv(ROOT / "annotation/human_consensus_hw.csv", dtype=str, keep_default_na=False)
gk = pd.read_csv(ROOT / "annotation/gold_key_hw.csv", dtype=str, keep_default_na=False)
ti = pd.read_csv(ROOT / "analysis/treated_check/items.csv", dtype=str, keep_default_na=False)
tk = pd.read_csv(ROOT / "annotation/treated_check_key.csv", dtype=str, keep_default_na=False)
p13 = {}; p20 = {}
for u, v in umap.items():
    for s in v["sources"]:
        if s["set"] == "p13": p13[s["item_id"]] = u
        if s["set"] == "p20": p20[s["item_id"]] = u
rows = []   # long: set, item, field, claude, human, gpt
gkx = gk.set_index("item_id"); hcx = hc.set_index("item_id")
for i, u in p13.items():
    if u not in valid: continue
    for f in FIELDS:
        rows.append(dict(set="p13", item=i, unit=u, field=f, claude=valid[u][f], human=hcx.at[i, f], gpt=gkx.at[i, f]))
tix = ti.set_index("item_id")
for i, u in p20.items():
    if u not in valid: continue
    for f in FIELDS:
        rows.append(dict(set="p20", item=i, unit=u, field=f, claude=valid[u][f], human=tix.at[i, f"human_{f}"], gpt=tix.at[i, f"judge_{f}"]))
R = pd.DataFrame(rows)

# ---- hw12 GPT critical per source row
raw = pd.concat([pd.read_parquet(ROOT / r / "scored.parquet") for r in ["runs/hw1", "runs/hw2"]], ignore_index=True)
gptc = raw.set_index(["run" if "run" in raw else "family_id", "output_id"]) if False else None
runs = {"hw1": pd.read_parquet(ROOT / "runs/hw1/scored.parquet"), "hw2": pd.read_parquet(ROOT / "runs/hw2/scored.parquet")}
hwrows = []; seen = set()
for u, v in umap.items():
    for s in v["sources"]:
        if s["set"] != "hw12" or (s["run"], s["output_id"], s["channel"]) in seen: continue
        seen.add((s["run"], s["output_id"], s["channel"]))
        r = runs[s["run"]]; r = r[(r.output_id == s["output_id"]) & (r.channel == s["channel"]) & (r.prompt_id == "P0")]
        for x in r.itertuples():
            hwrows.append(dict(unit=u, run=s["run"], output_id=s["output_id"], channel=s["channel"], gpt=x.critical, gpt_src=x.critical_source, J1=x.critical_J1, claude=valid.get(u, {}).get("critical")))
HW = pd.DataFrame(hwrows); HWv = HW[HW.claude.notna() & HW.gpt.notna()]

# ---- agreement tables
out = {"n_units": len(units), "n_labelled": len(lab), "n_valid": len(valid), "missing_units": missing, "batches_without_label_file": nbatch_missing,
       "problems": [list(p) for p in problems]}
def block(df, a, b):
    d = {}
    for f in FIELDS:
        x = df[(df.field == f) & (df[a] != "") & df[a].notna() & (df[b] != "") & df[b].notna()]
        d[f] = stat(list(x[a]), list(x[b]))
    x = df[(df[a] != "") & (df[b] != "")]
    d["all_fields_pooled"] = stat(list(x[a]), list(x[b]))
    return d
agree = {}
for s in ("p13", "p20"):
    d = R[R.set == s]
    agree[f"{s}_claude_vs_human"] = block(d, "claude", "human")
    agree[f"{s}_claude_vs_gpt"] = block(d, "claude", "gpt")
    agree[f"{s}_gpt_vs_human"] = block(d, "gpt", "human")
d = R
agree["p13p20_claude_vs_human"] = block(d, "claude", "human"); agree["p13p20_claude_vs_gpt"] = block(d, "claude", "gpt"); agree["p13p20_gpt_vs_human"] = block(d, "gpt", "human")
agree["hw12_claude_vs_gpt_critical_rows"] = stat(list(HWv.claude), list(HWv.gpt))
agree["hw12_claude_vs_gpt_critical_units"] = stat(list(HWv.drop_duplicates("unit").claude), list(HWv.drop_duplicates("unit").gpt))
for ch in ("chip1", "noncrit"):
    x = HWv[HWv.channel == ch]; agree[f"hw12_claude_vs_gpt_critical_{ch}"] = stat(list(x.claude), list(x.gpt))
# critical, all three sets vs GPT (rows)
allc = pd.concat([R[(R.field == "critical")][["claude", "gpt"]], HWv[["claude", "gpt"]]])
agree["all_sets_claude_vs_gpt_critical"] = stat(list(allc.claude), list(allc.gpt))
out["agreement"] = agree
# disagreement lists
dis = []
for r in R[(R.field == "critical") & (R.human != "") & (R.claude != R.human)].itertuples():
    dis.append(dict(set=r.set, item=r.item, text=units[r.unit]["text"], claude=r.claude, human=r.human, gpt=r.gpt))
out["critical_disagreements_vs_human"] = dis

# ---- P1 re-run
items, rawc = T6.load(["data/items/hw.jsonl", "data/items/hw2.jsonl"], ["runs/hw1", "runs/hw2"])
rawc = rawc.copy()
# map (output_id, channel) -> claude label; run identified via family sets (output_ids unique across runs per request)
cl = {}
for u, v in umap.items():
    if u not in valid: continue
    for s in v["sources"]:
        if s["set"] == "hw12": cl[(s["output_id"], s["channel"])] = valid[u]["critical"]
sel = rawc.prompt_id.eq("P0") & rawc.channel.isin(["chip1", "noncrit"]) & (rawc.dimension == "speech_act")
keys = list(zip(rawc.output_id, rawc.channel))
rep = np.array([k in cl and s for k, s in zip(keys, sel)])
cl_col = pd.Series([cl.get(k) for k in keys], index=rawc.index)
rawc["critical_gpt"] = rawc["critical"]
rawc.loc[rep, "critical"] = cl_col[rep]
out["p1_rows_replaced"] = int(rep.sum()); out["p1_rows_changed_label"] = int((rawc.loc[rep, "critical"] != rawc.loc[rep, "critical_gpt"]).sum())
res = {}; ests = {}
for name, col in (("gpt", "critical_gpt"), ("claude", "critical")):
    r2 = rawc.copy(); r2["critical"] = r2[col]
    d2, excl = H1.build(items, r2); fr = H1.frames(d2); f = fr["P1"]
    rng = np.random.default_rng(T6.SEED)
    r = T6.analyse(f, "P1", rng, {})
    arms = {}
    p0 = d2[d2.prompt_id.eq("P0") & d2.dimension.eq("speech_act")]
    for ch in ("chip1", "noncrit"):
        g = p0[p0.channel.eq(ch) & p0.critical_match.notna()]; arms[ch] = float(g.critical_match.astype(float).mean())
    res[name] = dict(estimate_pp=100 * r["estimate"], t_ci_pp=[100 * r["t_ci_low"], 100 * r["t_ci_high"]], writers=r["writers"], rows=r["rows"], se_pp=100 * r["se_cr1"],
                     writer_means_pp={k: 100 * v for k, v in r["writer_means"].items()}, loo_range_pp=[100 * r["loo_range"][0], 100 * r["loo_range"][1]],
                     sign_flip_p_one_sided=r["sign_flip_randomization"]["p_one_sided"], all_writer_signs_positive=r["sign_flip_randomization"]["all_writer_signs_positive"],
                     wild_webb_ci_pp=[100 * r["wild_webb"]["ci_low"], 100 * r["wild_webb"]["ci_high"]], arm_means_pp={k: 100 * v for k, v in arms.items()})
out["p1"] = res
(D / "summary.json").write_text(json.dumps(out, indent=1, default=str))

# ---- report
def fmt(s):
    if not s or s.get("n", 0) == 0: return "n/a"
    k = s["kappa"]; kc = s.get("kappa_ci")
    return f"{s['n']} | {100*s['accuracy']:.1f}% [{100*s['acc_ci'][0]:.1f}, {100*s['acc_ci'][1]:.1f}] | " + ("undef" if k is None else f"{k:.3f}") + (f" [{kc[0]:.2f}, {kc[1]:.2f}]" if kc else "")
L = ["# B2: Claude (non-GPT) re-label of judge units", "",
     "Disclosure: Claude (Sonnet) is a second-family extractor here, not an independent human check. Claude also served as the arbiter in the production labelling and assisted analysis and writing of this project, so these agreement numbers are not independent of Claude-side choices. Pre-declared rules: `analysis/relabel_nongpt/PLAN.md`; labelling instruction `INSTRUCTION.md` (verbatim in every subagent prompt); script `src/relabel_nongpt_aggregate.py` (stored data, 0 API calls).", "",
     "## Coverage", "",
     f"* Units: {len(units)} in {len(set(u['batch'] for u in units.values()))} batches; labelled {len(lab)}; with all values valid {len(valid)}; missing {len(missing)}; problems {len(problems)}; batches without label file: {nbatch_missing or 'none'}.",
     ("* Gaps and invalid entries: " + "; ".join(f"{a}: {b}" for a, b in problems[:20]) + ("; unlabelled units: " + ", ".join(f"{u} ({units[u]['batch']}, " + "/".join(sorted({x['set'] for x in umap[u]['sources']})) + ")" for u in missing)) + ". Unlabelled units are excluded from every analysis below (the affected rows keep the GPT label in the P1 Claude re-run)." if problems or missing else "* No gaps: every unit is labelled and every value (critical within the unit's options, five general fields within the declared options) is valid."), ""]
for key, title in (("p13_claude_vs_human", "Claude vs human consensus, Part 13 (152 outputs, plurality of 3 coders)"), ("p20_claude_vs_human", "Claude vs human consensus, Part 20 (120 outputs, strict two-coder consensus; items without consensus excluded per field)"),
                   ("p13p20_claude_vs_human", "Claude vs human consensus, Parts 13+20 pooled")):
    L += [f"## {title}", "", "| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |", "|---|---|---|---|"]
    for f in FIELDS + ["all_fields_pooled"]: L.append(f"| {f} | {fmt(agree[key][f])} |")
    L.append("")
for key, title in (("p13_claude_vs_gpt", "Claude vs GPT judge (production label), Part 13"), ("p20_claude_vs_gpt", "Claude vs GPT judge, Part 20"), ("p13p20_claude_vs_gpt", "Claude vs GPT judge, Parts 13+20")):
    L += [f"## {title}", "", "| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |", "|---|---|---|---|"]
    for f in FIELDS + ["all_fields_pooled"]: L.append(f"| {f} | {fmt(agree[key][f])} |")
    L.append("")
L += ["## Reference: GPT judge vs human consensus on the same items (Parts 13+20)", "", "| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |", "|---|---|---|---|"]
for f in FIELDS + ["all_fields_pooled"]: L.append(f"| {f} | {fmt(agree['p13p20_gpt_vs_human'][f])} |")
L += ["", "## hw12 speech-act critical label: Claude vs GPT production label (no human reference)", "", "| subset | n | accuracy [Wilson 95%] | kappa |", "|---|---|---|---|"]
for k, t in (("hw12_claude_vs_gpt_critical_rows", "all rows (hw1+hw2, P0, chip1+noncrit)"), ("hw12_claude_vs_gpt_critical_units", "distinct texts"), ("hw12_claude_vs_gpt_critical_chip1", "chip1"), ("hw12_claude_vs_gpt_critical_noncrit", "noncrit")):
    L.append(f"| {t} | {fmt(agree[k])} |")
L += ["", f"Critical field, all three unit sets vs GPT (rows): {fmt(agree['all_sets_claude_vs_gpt_critical'])}.", "",
      "## P1 re-run (hw1+hw2 speech-act chip1 minus noncrit critical-match gain)", "",
      f"Estimator: `src/robust_t6_small_cluster.py` `analyse` (pooled row-weighted ratio over writers, CR1 SE, t CI with writers-1 df), after `analyze_hw1.build/frames` (same exclusions). Claude's critical label replaced the GPT critical label on {out['p1_rows_replaced']} scored rows ({out['p1_rows_changed_label']} changed); all other rows unchanged.", "",
      "| labels | writers | rows | chip1 match | noncrit match | P1 estimate (pp) | t 95% CI | wild-Webb CI | sign-flip p (1-sided) | all writers positive | leave-one-out |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for n in ("gpt", "claude"):
    r = res[n]; L.append(f"| {n} | {r['writers']} | {r['rows']} | {r['arm_means_pp']['chip1']:.1f} | {r['arm_means_pp']['noncrit']:.1f} | {r['estimate_pp']:+.1f} | [{r['t_ci_pp'][0]:.1f}, {r['t_ci_pp'][1]:.1f}] | [{r['wild_webb_ci_pp'][0]:.1f}, {r['wild_webb_ci_pp'][1]:.1f}] | {r['sign_flip_p_one_sided']:.4f} | {r['all_writer_signs_positive']} | {r['loo_range_pp'][0]:+.1f} to {r['loo_range_pp'][1]:+.1f} |")
L += ["", "Claude writer means (pp): " + ", ".join(f"{k} {v:+.1f}" for k, v in res["claude"]["writer_means_pp"].items()), ""]
L += ["## Items where Claude's critical label differs from human consensus", "", "| set | item | text | Claude | human | GPT |", "|---|---|---|---|---|---|"]
for x in dis: L.append(f"| {x['set']} | {x['item']} | {x['text'].replace('|', '/')} | {x['claude']} | {x['human']} | {x['gpt']} |")
L += ["", "## Caveats", "", "* added_content was not labelled (it needs the input, which would unblind).", "* Claude saw only the output sentence; the GPT judge also saw only the output for these fields (J1 pass A), so the contrast is extractor family, not information.",
      "* The hw12 comparison has no human reference; agreement there is Claude-vs-GPT only.", "* Part 20 consensus is the strict two-coder rule; Part 13 is the stored plurality of three coders. GPT labels are the production labels (arbiter-resolved critical)."]
(D / "report.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:12]))
