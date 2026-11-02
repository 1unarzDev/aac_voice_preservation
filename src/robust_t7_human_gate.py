"""T7: recompute the human extraction gates with stricter reference rules (stored labels only; no judging).

    . .venv/bin/activate && python src/robust_t7_human_gate.py

Gates: H7 / main1 (annotation/returns/A*.csv: annotators A1, A2), main1 Parts 1-3 humans (labels_main1_*: P02 P10 P14),
Part 12 (run elic; returns_gold_elic) and Part 13 (run hw; returns_gold_hw). Internals reused from src/score_gold.py
(load_key, consensus rule, is_cal split, SEED, DIMS) and src/agree_stats.py (cohen_kappa).

Reference rules (judge FINAL label vs human reference, unweighted kappa as in the gate):
  R0  stored rule: plurality; ties and unsure/blank answers excluded.           (reproduces judge_validation_<run>.json)
  R1  ties and items with no usable human label count as DISAGREEMENT (reference = a NO_CONSENSUS category the judge can never match).
  R2  as R1, and every annotator answer flagged unsure or left blank (not skipped) becomes an UNSURE vote that can win the plurality.
Subsets: the seeded TEST split (the gate), and all sampled items. 95% CIs: family-cluster bootstrap (2,000 resamples, seed 20261101).
Also: per-model and per-channel kappa (R1), and human-human Cohen kappa beside judge-human Cohen kappa on the SAME double-coded
items (pooled over annotator pairs; family-cluster bootstrap CIs, including the difference).
"""
from __future__ import annotations
import csv, glob, itertools, json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import score_gold as SG                      # noqa: E402
from agree_stats import cohen_kappa          # noqa: E402
from robust_common import outdir, write_json, md_table   # noqa: E402

OUT = outdir("t7_human_gate"); B = 2000; RS = 20261101; NOCONS = "__NO_CONSENSUS__"; UNS = "__UNSURE__"
GATES = {
    "main1_H7_A1A2": dict(run="main1", pats=["annotation/returns/A*.csv"], stored="annotation/judge_validation_main1.json"),
    "main1_parts1-3_P02P10P14": dict(run="main1", pats=["annotation/returns/labels_main1_*.csv"], stored=None),
    "part12_elic": dict(run="elic", pats=["annotation/returns_gold_elic/*.csv"], stored="annotation/judge_validation_elic.json"),
    "part13_hw": dict(run="hw", pats=["annotation/returns_gold_hw/*.csv"], stored="annotation/judge_validation_hw.json"),
}


def load_raw(patterns, key):
    """item -> annotator -> dim -> (label|None, unsure_flag, skipped); same normalisation as SG.load_returns."""
    ann = {}
    for p in sorted({q for pat in patterns for q in glob.glob(str(ROOT / pat))}):
        for r in SG.read_csv(p):
            iid = r.get("item_id", "")
            if iid.startswith("practice") or str(r.get("practice", "0")) == "1" or iid not in key: continue
            uns = {u.strip() for u in (r.get("unsure_dims") or "").replace(";", ",").replace("|", ",").split(",")}
            skipped = str(r.get("skip", "0")) == "1"
            lab = {}
            for d in SG.DIMS:
                v = (r.get(d) or "").strip() or None
                if v is not None and d in SG.GENERAL_OPTIONS and v not in SG.GENERAL_OPTIONS[d]: pass
                if v is not None and d == "critical":
                    opts = key[iid].get("critical_options") or []
                    if v == "mixed/unclear" and "unclear/mixed" in opts: v = "unclear/mixed"
                    if opts and v not in opts: v = None
                lab[d] = (v, d in uns, skipped)
            ann.setdefault(iid, {})[r["annotator"]] = lab
    return ann


def reference(ann_item, d, rule):
    votes = []
    for a, lab in ann_item.items():
        v, u, sk = lab[d]
        if rule == "R2":
            if v is None or u: votes.append(UNS if not sk else None)
            else: votes.append(v)
        else:
            if v is not None and not u: votes.append(v)
    votes = [x for x in votes if x is not None]
    if not votes: return None if rule == "R0" else NOCONS
    c = Counter(votes).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]: return None if rule == "R0" else NOCONS
    return c[0][0]


def kap(pred, gold):
    return cohen_kappa(list(pred), list(gold))


def fam_boot(pred, gold, fam, reps=B, seed=RS):
    rng = np.random.default_rng(seed); fams = sorted(set(fam)); idx = defaultdict(list)
    for i, f in enumerate(fam): idx[f].append(i)
    pred, gold = np.array(pred, dtype=object), np.array(gold, dtype=object); out = []
    for _ in range(reps):
        pick = rng.choice(len(fams), len(fams))
        ix = [j for k in pick for j in idx[fams[k]]]
        k = kap(pred[ix], gold[ix])
        if k is not None: out.append(k)
    return [float(np.quantile(out, .025)), float(np.quantile(out, .975))] if len(out) > reps // 2 else [None, None]


def attrs(run, key):
    """per-item model list and channel list (main1 from the scored table; multi-run keys from the key columns)."""
    mod, chn = {}, {}
    if run == "main1":
        sc = pd.read_parquet(ROOT / "runs/main1/scored.parquet", columns=["text_id", "model", "channel"])
        tm = sc.groupby("text_id").model.agg(lambda s: sorted(set(s))).to_dict(); tc = sc.groupby("text_id").channel.agg(lambda s: sorted(set(s))).to_dict()
        for i, k in key.items():
            mod[i] = tm.get(k.get("text_id"), []); chn[i] = tc.get(k.get("text_id"), [])
    else:
        for i, k in key.items():
            mod[i] = [k["model"]] if k.get("model") else [m for m in str(k.get("models") or "").split("|") if m]
            chn[i] = sorted({("human" if c.startswith("human_") else c) for c in str(k.get("channels") or "").split("|") if c})
    return mod, chn


def run_gate(name, g):
    key = SG.load_key(g["run"], None)
    ann = load_raw(g["pats"], key)
    ann = {i: v for i, v in ann.items() if key[i]["subset"] == "sampled"}
    items = sorted(ann)
    test = [i for i in items if not SG.is_cal(i, SG.SEED, .25)]
    res = {"gate": name, "run": g["run"], "annotators": sorted({a for v in ann.values() for a in v}), "items": len(items), "test_items": len(test),
           "coders_per_item": dict(Counter(len(v) for v in ann.values())), "dims": {}}
    stored = json.load(open(ROOT / g["stored"]))["human"]["judge"] if g["stored"] else None
    mod, chn = attrs(g["run"], key)
    for d in SG.DIMS:
        rd = {}
        for sub, ids in (("test", test), ("all", items)):
            for rule in ("R0", "R1", "R2"):
                pr, go, fm = [], [], []
                nref_missing = 0
                for i in ids:
                    ref = reference(ann[i], d, rule); jl = key[i].get(d)
                    if jl is None: continue
                    if ref is None: nref_missing += 1; continue
                    pr.append(jl); go.append(ref); fm.append(key[i]["family_id"])
                kk = kap(pr, go)
                rd[f"{sub}/{rule}"] = dict(n=len(pr), kappa=kk, acc=float(np.mean([p == q for p, q in zip(pr, go)])) if pr else None,
                                           ci=fam_boot(pr, go, fm) if kk is not None else [None, None], excluded_no_consensus=nref_missing,
                                           ref_no_consensus=int(sum(x in (NOCONS, UNS) for x in go)))
        if stored and f"sampled_test/final" in stored[d]:
            rd["stored_test_final"] = dict(n=stored[d]["sampled_test/final"]["n"], kappa=stored[d]["sampled_test/final"]["kappa"], ci=stored[d]["sampled_test/final"].get("kappa_ci"))
        # per model / channel (R1, all sampled items; units exploded over the models/channels they occur in)
        for gname, amap in (("model", mod), ("channel", chn)):
            rows = defaultdict(lambda: ([], [], []))
            for i in items:
                ref = reference(ann[i], d, "R1"); jl = key[i].get(d)
                if jl is None: continue
                for v in (amap[i] or ["?"]):
                    p, q, f = rows[v]; p.append(jl); q.append(ref); f.append(key[i]["family_id"])
            rd[f"by_{gname}_R1"] = {v: dict(n=len(p), kappa=kap(p, q), acc=float(np.mean([a == b for a, b in zip(p, q)])),
                                           ci=fam_boot(p, q, f, reps=500) if kap(p, q) is not None and len(set(f)) > 1 else [None, None])
                                    for v, (p, q, f) in sorted(rows.items())}
        # human-human vs judge-human on the same double-coded items (unsure/blank excluded; pooled over annotator pairs)
        hh_a, hh_b, jh_a, jh_b, fm = [], [], [], [], []
        for i in items:
            labs = {a: lab[d][0] for a, lab in ann[i].items() if lab[d][0] is not None and not lab[d][1]}
            jl = key[i].get(d)
            if jl is None: continue
            for a, b in itertools.combinations(sorted(labs), 2):
                hh_a.append(labs[a]); hh_b.append(labs[b]); jh_a.append(jl); jh_b.append(labs[a]); fm.append(key[i]["family_id"])
                hh_a.append(None); hh_b.append(None)   # placeholder removed below
        # rebuild cleanly: observation = (annotator a label, annotator b label, judge label) per item per pair; judge-human uses both members
        obs = []
        for i in items:
            labs = {a: lab[d][0] for a, lab in ann[i].items() if lab[d][0] is not None and not lab[d][1]}; jl = key[i].get(d)
            if jl is None: continue
            for a, b in itertools.combinations(sorted(labs), 2): obs.append((labs[a], labs[b], jl, key[i]["family_id"]))
        if obs:
            A_ = [o[0] for o in obs]; B_ = [o[1] for o in obs]; J_ = [o[2] for o in obs]; F_ = [o[3] for o in obs]
            hh = kap(A_, B_); jh = kap(J_ + J_, A_ + B_)
            rng = np.random.default_rng(RS); fams = sorted(set(F_)); idx = defaultdict(list)
            for k_, f in enumerate(F_): idx[f].append(k_)
            hhs, jhs, dfs = [], [], []
            for _ in range(B):
                ix = [j for k_ in rng.choice(len(fams), len(fams)) for j in idx[fams[k_]]]
                a_ = [A_[j] for j in ix]; b_ = [B_[j] for j in ix]; j_ = [J_[j] for j in ix]
                h1 = kap(a_, b_); j1 = kap(j_ + j_, a_ + b_)
                if h1 is not None and j1 is not None: hhs.append(h1); jhs.append(j1); dfs.append(j1 - h1)
            q = lambda x: [float(np.quantile(x, .025)), float(np.quantile(x, .975))] if len(x) > B // 2 else [None, None]
            rd["human_human_vs_judge_human"] = dict(pairs_observations=len(obs), human_human_kappa=hh, hh_ci=q(hhs), judge_human_kappa=jh, jh_ci=q(jhs),
                                                    difference_jh_minus_hh=None if hh is None or jh is None else round(jh - hh, 3), diff_ci=q(dfs))
        res["dims"][d] = rd
    return res


def main():
    allres = {n: run_gate(n, g) for n, g in GATES.items()}
    write_json(OUT / "summary.json", allres)
    rows = []
    for n, r in allres.items():
        for d, rd in r["dims"].items():
            rec = dict(gate=n, dimension=d)
            for k in ("test/R0", "test/R1", "test/R2", "all/R1"):
                x = rd[k]; rec[f"{k} n"] = x["n"]; rec[f"{k} kappa"] = x["kappa"]; rec[f"{k} ci_lo"] = x["ci"][0]; rec[f"{k} ci_hi"] = x["ci"][1]
            rec["stored_kappa"] = (rd.get("stored_test_final") or {}).get("kappa"); rec["test/R1 ref_no_consensus"] = rd["test/R1"]["ref_no_consensus"]
            h = rd.get("human_human_vs_judge_human") or {}
            rec |= dict(hh_kappa=h.get("human_human_kappa"), hh_lo=(h.get("hh_ci") or [None, None])[0], hh_hi=(h.get("hh_ci") or [None, None])[1], jh_kappa=h.get("judge_human_kappa"),
                        jh_lo=(h.get("jh_ci") or [None, None])[0], jh_hi=(h.get("jh_ci") or [None, None])[1], diff=h.get("difference_jh_minus_hh"),
                        diff_lo=(h.get("diff_ci") or [None, None])[0], diff_hi=(h.get("diff_ci") or [None, None])[1])
            rows.append(rec)
    T = pd.DataFrame(rows); T.to_csv(OUT / "kappa_by_rule.csv", index=False)
    pm = [dict(gate=n, dimension=d, group=g_, value=v, **x) for n, r in allres.items() for d, rd in r["dims"].items() for g_ in ("model", "channel") for v, x in rd[f"by_{g_}_R1"].items()]
    P = pd.DataFrame(pm); P["ci_lo"] = P.ci.map(lambda c: c[0]); P["ci_hi"] = P.ci.map(lambda c: c[1]); P = P.drop(columns="ci"); P.to_csv(OUT / "kappa_by_model_channel.csv", index=False)
    f = lambda x: "NA" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.3f}"
    L = ["# T7: human-gate recomputation (stored labels; 0 generation / 0 judge calls)", "",
         "Script `src/robust_t7_human_gate.py`; tables `kappa_by_rule.csv`, `kappa_by_model_channel.csv`; `summary.json`. Internals from `src/score_gold.py`. "
         "Judge FINAL label vs human reference, unweighted Cohen kappa; CIs are family-cluster bootstrap (2,000 resamples).", "",
         "R0 = stored rule (plurality; ties and unsure/blank excluded; reproduces the stored `sampled_test/final` kappa). R1 = ties and items with no usable human label count as disagreement. "
         "R2 = R1 and each unsure/blank answer is an UNSURE vote that can win. 'test' = the seeded 25/75 split used for the gate; 'all' = all sampled items.", ""]
    for n, r in allres.items():
        L += [f"## {n}", "", f"Annotators {r['annotators']}; {r['items']} sampled items ({r['test_items']} in the test split); coders per item {r['coders_per_item']}.", "",
              "| dimension | stored test kappa | test R0 (n) | test R1 (n) [CI] | test R2 (n) [CI] | all R1 (n) [CI] | no-consensus refs in test R1 | human-human kappa [CI] | judge-human kappa [CI] | difference [CI] |", "|---|---|---|---|---|---|---|---|---|---|"]
        for d, rd in r["dims"].items():
            h = rd.get("human_human_vs_judge_human") or {}
            ci = lambda x: f"[{f(x['ci'][0])}, {f(x['ci'][1])}]"
            L.append(f"| {d} | {f((rd.get('stored_test_final') or {}).get('kappa'))} | {f(rd['test/R0']['kappa'])} ({rd['test/R0']['n']}) | {f(rd['test/R1']['kappa'])} ({rd['test/R1']['n']}) {ci(rd['test/R1'])} | "
                     f"{f(rd['test/R2']['kappa'])} ({rd['test/R2']['n']}) {ci(rd['test/R2'])} | {f(rd['all/R1']['kappa'])} ({rd['all/R1']['n']}) {ci(rd['all/R1'])} | {rd['test/R1']['ref_no_consensus']} | "
                     f"{f(h.get('human_human_kappa'))} [{f((h.get('hh_ci') or [None,None])[0])}, {f((h.get('hh_ci') or [None,None])[1])}] | {f(h.get('judge_human_kappa'))} [{f((h.get('jh_ci') or [None,None])[0])}, {f((h.get('jh_ci') or [None,None])[1])}] | "
                     f"{f(h.get('difference_jh_minus_hh'))} [{f((h.get('diff_ci') or [None,None])[0])}, {f((h.get('diff_ci') or [None,None])[1])}] |")
        L.append("")
    sub = P[P.dimension.eq("critical")]
    L += ["## Per-model and per-channel kappa (critical field, R1, all sampled items; other fields in `kappa_by_model_channel.csv`)", "", md_table(sub[["gate", "group", "value", "n", "kappa", "acc", "ci_lo", "ci_hi"]].round(3), 3), "",
          "## Notes and caveats", "",
          "* R1/R2 can only lower kappa relative to R0: they add reference categories the judge cannot match. The size of the drop shows how much of the gate rests on excluded ties/unsure answers.",
          "* For main1 H7 (two annotators, 100 double-coded, 87 single-coded) a tie is any disagreement on a double-coded item; there is no third vote. Human-human kappa on the double-coded items is therefore the natural ceiling for judge-human kappa.",
          "* Human-human kappa pools all annotator pairs per item; judge-human kappa pools the judge against each member of those same pairs (so it is computed on identical items). Both are family-cluster resampled together for the difference.",
          "* main1 channel/model are recovered from `runs/main1/scored.parquet` by text_id (a text can occur in several channels/models and is then counted in each); elic/hw use the key columns (`model`, `channels`; human_* channels pooled as 'human').",
          "* All gates cover untreated outputs of the stored inventories only; annotators were taught the same codebook as the judge (see CODEBOOK.md).",
          "* The machine panel (`main1_sens_sol_astra`) is not a human reference and is not recomputed here."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
