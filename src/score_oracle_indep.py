"""Score the independent mutation set: Part 29 human confirmation, then the judge and the two baseline oracles on the human-confirmed items.
Rules (frozen before any return): analysis/oracle_indep/PLAN.md Amendment 2 and annotation/COORDINATOR_STEPS.md section 7.

  python src/score_oracle_indep.py --self-check
  python src/score_oracle_indep.py [--returns DIR] [--judge FILE] [--out DIR]
Inputs: annotation/oracle_indep_key.csv (PRIVATE), annotation/returns_part29/labels_part29_<ID>.csv, and (run AFTER the returns, on the mutant text only,
by the unchanged production judge) runs/oracle_indep/judge_labels.jsonl with one row per candidate: {"id": "I003", "critical": "<label or null>"}.
Outputs (default analysis/oracle_indep_human/): qc.json, confirmation.csv, scores.csv, summary.json.
Only human-confirmed items count: a mutant when both annotators answer different, a control when both answer same; everything else is unresolved and excluded
(counted by operator). Baselines: src/oracle_baselines.py surface and overlap on the mutant text; an oracle catches an item when it says NOT preserved."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import oracle_baselines as B  # noqa: E402
from labels import critical_match  # noqa: E402

KEY = ROOT / "annotation" / "oracle_indep_key.csv"
JUDGE = ROOT / "runs" / "oracle_indep" / "judge_labels.jsonl"
ANSWERS = ["same", "different", "unsure"]
COMPLETE_MIN = 0.80


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (round(c - h, 4), round(c + h, 4))


def frac(k, n):
    lo, hi = wilson(k, n)
    return {"k": int(k), "n": int(n), "rate": round(k / n, 4) if n else None, "lo": lo, "hi": hi}


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)


def kappa(a, b):
    a, b = list(a), list(b)
    if not a:
        return None
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else round((po - pe) / (1 - pe), 4)


def load_key(path=KEY):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def read_returns(folder):
    fs = sorted(Path(folder).glob("labels_part29_*.csv")) if Path(folder).exists() else []
    parts = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in fs]
    return pd.concat(parts, ignore_index=True).fillna("") if parts else pd.DataFrame()


def qc(ret, key):
    rep = {"rows": int(len(ret)), "practice_dropped": 0, "unknown_item": 0, "wrong_annotator": 0, "duplicate": 0, "missing_or_invalid": 0}
    if ret.empty:
        return ret, rep
    ret = ret[ret["practice"].astype(str) != "1"].copy(); rep["practice_dropped"] = rep["rows"] - len(ret)
    ret["annotator"] = ret["annotator"].str.strip().str.upper()
    pair = set(zip(key.item_id, key.annotator))
    unk = ~ret.item_id.isin(set(key.item_id)); rep["unknown_item"] = int(unk.sum()); ret = ret[~unk]
    bad = pd.Series([(i, a) not in pair for i, a in zip(ret.item_id, ret.annotator)], index=ret.index, dtype=bool)
    rep["wrong_annotator"] = int(bad.sum()); ret = ret[~bad]
    dup = ret.duplicated(["item_id", "annotator"], keep="last"); rep["duplicate"] = int(dup.sum()); ret = ret[~dup]
    inv = ~ret["q1"].isin(ANSWERS); rep["missing_or_invalid"] = int(inv.sum()); ret = ret[~inv]
    return ret, rep


def confirm(ret, key, comp=COMPLETE_MIN):
    """Per candidate: the two answers and the decision (frozen rule)."""
    assigned = key.groupby("annotator").size(); done = ret.groupby("annotator").size().reindex(assigned.index).fillna(0)
    dropped = sorted(a for a in assigned.index if done[a] < comp * assigned[a])
    r = ret[~ret.annotator.isin(dropped)]
    kk = key.set_index(["item_id", "annotator"])["cand_id"].to_dict()
    ans = defaultdict(dict)
    for x in r.itertuples():
        ans[kk[(x.item_id, x.annotator)]][x.annotator] = x.q1
    rows = []
    for cid, g in key.drop_duplicates("cand_id").set_index("cand_id").iterrows():
        a = list(ans.get(cid, {}).values())
        if len(a) == 2 and a[0] == a[1] and a[0] in ("same", "different"):
            status = "changed" if a[0] == "different" else "same"
        else:
            status = "unresolved"
        kind = g["kind"]
        use = (kind == "mutant" and status == "changed") or (kind == "control" and status == "same")
        fail = (kind == "mutant" and status == "same") or (kind == "control" and status == "changed")
        rows.append({"cand_id": cid, "kind": kind, "op": g["op"], "target_dimension": g["target_dimension"], "lex_visible": g["lex_visible"],
                     "answers": "|".join(sorted(a)), "n_answers": len(a), "human": status, "scored": use, "construction_failure": fail})
    return pd.DataFrame(rows), dropped


def agreement(ret, key):
    kk = key.set_index(["item_id", "annotator"])["cand_id"].to_dict()
    d = defaultdict(dict)
    for x in ret.itertuples():
        d[kk[(x.item_id, x.annotator)]][x.annotator] = x.q1
    pairs = [tuple(v.values()) for v in d.values() if len(v) == 2]
    both = [p for p in pairs if all(a != "unsure" for a in p)]
    return {"pairs": len(pairs), "raw_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
            "kappa_three_way": kappa([a for a, _ in pairs], [b for _, b in pairs]), "pairs_same_different_only": len(both),
            "raw_agreement_same_different": round(sum(a == b for a, b in both) / len(both), 4) if both else None,
            "kappa_same_different": kappa([a for a, _ in both], [b for _, b in both])}


def oracle_rows(key, judge_path):
    items = {}
    for f in ("annotation/written/hw_candidates.jsonl", "annotation/written/hw2/hw_candidates.jsonl", "data/items/hw.jsonl"):   # candidates include pairs later dropped
        for l in open(ROOT / f, encoding="utf-8"):
            x = json.loads(l); items[x["family_id"]] = x
    judge = {}
    if Path(judge_path).exists():
        for l in open(judge_path, encoding="utf-8"):
            if l.strip():
                j = json.loads(l); judge[j["id"]] = j.get("critical")
    out = {}
    for _, k in key.drop_duplicates("cand_id").iterrows():
        fam = items[k["family_id"]]; var = fam["variants"][k["variant"]]; other = next(v for kk, v in fam["variants"].items() if kk != k["variant"])
        dim, ref, text = k["target_dimension"], k["target_ref"], k["mutant"]
        d = {"surface_pass": B.surface_pass(dim, ref, text), "overlap_pass": B.overlap_pass(text, var["source"], other["source"])}
        if k["cand_id"] in judge:
            crit = judge[k["cand_id"]]
            d["judge_pass"] = None if crit is None else bool(critical_match(dim, ref, crit))
        else:
            d["judge_pass"] = "missing"
        out[k["cand_id"]] = d
    return out


def score(conf, orc):
    c = conf[conf.scored].copy()
    for o in ("judge", "surface", "overlap"):
        c[f"{o}_pass"] = c.cand_id.map(lambda i: orc[i][f"{o}_pass"])
    have_judge = (c["judge_pass"] != "missing").all() if len(c) else False
    def caught(rows, o, unresolved_as=False):
        k = 0
        for v in rows[f"{o}_pass"]:
            if v is None:
                k += 1 if unresolved_as else 0
            elif v == "missing":
                continue
            else:
                k += (not v)
        return k
    res = {"n_scored_mutants": int((c.kind == "mutant").sum()), "n_scored_controls": int((c.kind == "control").sum()), "judge_scored": bool(have_judge)}
    tab = []
    oracles = ["judge", "surface", "overlap"] if have_judge else ["surface", "overlap"]
    def row(label, g):
        m, ct = g[g.kind == "mutant"], g[g.kind == "control"]
        e = {"group": label, "n_mut": len(m), "n_ctl": len(ct)}
        for o in oracles:
            e[f"{o}_sens"] = frac(caught(m, o), len(m)); e[f"{o}_fa"] = frac(caught(ct, o), len(ct))
        if have_judge:
            e["judge_sens_upper_unresolved_caught"] = frac(caught(m, "judge", True), len(m))
        tab.append(e); return e
    res["all"] = row("all", c)
    res["lex_not_visible"] = row("lex_visible False (non-circular headline)", c[(c.kind == "control") | (c.lex_visible == "False")])
    res["lex_visible"] = row("lex_visible True", c[(c.kind == "control") | (c.lex_visible == "True")])
    for op in sorted(c[c.kind == "mutant"].op.unique()):
        row(f"op:{op}", c[(c.kind == "mutant") & (c.op == op)])
    for d in sorted(c[c.kind == "mutant"].target_dimension.unique()):
        row(f"dim:{d}", c[(c.kind == "mutant") & (c.target_dimension == d)])
    if have_judge:
        m = c[c.kind == "mutant"]; res["mcnemar"] = {}
        for o in ("surface", "overlap"):
            jc = m.judge_pass.map(lambda v: v is False); oc = m[f"{o}_pass"].map(lambda v: v is False)
            b_, c_ = int((jc & ~oc).sum()), int((~jc & oc).sum())
            res["mcnemar"][f"judge_vs_{o}"] = {"judge_only": b_, "baseline_only": c_, "p_exact_two_sided": round(mcnemar_exact(b_, c_), 4)}
    return res, tab, c


def run(returns, judge_path, out, key_path=KEY):
    key = load_key(key_path)
    ret, rep = qc(read_returns(returns), key)
    out.mkdir(parents=True, exist_ok=True)
    res = {"qc": rep}
    if ret.empty:
        (out / "qc.json").write_text(json.dumps(res, indent=1)); return {"res": res}
    conf, dropped = confirm(ret, key)
    res["dropped_annotators"] = dropped; res["agreement"] = agreement(ret[~ret.annotator.isin(dropped)], key)
    res["confirmation"] = {"mutants": dict(Counter(conf[conf.kind == "mutant"].human)), "controls": dict(Counter(conf[conf.kind == "control"].human)),
                           "mutants_by_op": {op: dict(Counter(g.human)) for op, g in conf[conf.kind == "mutant"].groupby("op")},
                           "construction_failures": conf[conf.construction_failure].op.value_counts().to_dict()}
    conf.to_csv(out / "confirmation.csv", index=False)
    orc = oracle_rows(key, judge_path)
    s, tab, c = score(conf, orc)
    res["scores"] = s
    flat = []
    for e in tab:
        f = {"group": e["group"], "n_mut": e["n_mut"], "n_ctl": e["n_ctl"]}
        for k, v in e.items():
            if isinstance(v, dict):
                f[k] = v["rate"]; f[k + "_k"] = v["k"]; f[k + "_n"] = v["n"]; f[k + "_lo"] = v["lo"]; f[k + "_hi"] = v["hi"]
        flat.append(f)
    pd.DataFrame(flat).to_csv(out / "scores.csv", index=False)
    (out / "qc.json").write_text(json.dumps(res["qc"], indent=1)); (out / "summary.json").write_text(json.dumps(res, indent=1, default=str))
    return {"res": res, "conf": conf, "tab": tab}


def synthetic(key, flip_unsure=(), seed=3):
    """Planted annotators: answer by the candidate's own kind (mutant -> different, control -> same), with set deviations."""
    rows = []
    for r in key.itertuples():
        ans = "different" if r.kind == "mutant" else "same"
        if r.cand_id in flip_unsure and r.annotator == key[key.cand_id == r.cand_id].annotator.iloc[0]:
            ans = "unsure"
        rows.append({"item_id": r.item_id, "annotator": r.annotator, "check_id": "part29", "practice": "0", "order": "1", "q1": ans, "note": "", "time_ms": "5000"})
    return pd.DataFrame(rows)


def self_check():
    key = load_key()
    scratch = ROOT / "tmp" / "s7_oracle_selfcheck"; shutil.rmtree(scratch, ignore_errors=True); scratch.mkdir(parents=True)
    fails = []
    def ok(c, m):
        print(("ok   " if c else "FAIL ") + m)
        if not c:
            fails.append(m)
    try:
        ok(key.cand_id.nunique() == 150 and key.annotator.nunique() == 20 and (key.groupby("cand_id").annotator.nunique() == 2).all(), "key: 150 candidates, 2 different annotators each, 20 annotators")
        ok(key.groupby("annotator").size().between(14, 16).all(), "key: 14-16 items per annotator")
        ok((key.kind == "mutant").sum() == 200 and (key.kind == "control").sum() == 100, "key: 100 mutants and 50 controls (x2 rows)")
        ok(key.drop_duplicates("cand_id").mutant_is_sentence.isin(["1", "2"]).all() and key.drop_duplicates("cand_id").mutant_is_sentence.nunique() == 2, "key: sentence order recorded and varied")
        # planted answers: everyone follows the candidate kind, two items get one 'unsure'
        uns = set(key[key.kind == "mutant"].cand_id.iloc[::40]) | set(key[key.kind == "control"].cand_id.iloc[:1])
        s = synthetic(key, flip_unsure=uns)
        d = scratch / "ret"; d.mkdir()
        for a, g in s.groupby("annotator"):
            g.to_csv(d / f"labels_part29_{a}.csv", index=False)
        # planted judge: catches every mutant, passes every control (by labelling with the reference value or a different value)
        jp = scratch / "judge.jsonl"; kd = key.drop_duplicates("cand_id")
        with open(jp, "w") as fh:
            for r in kd.itertuples():
                fh.write(json.dumps({"id": r.cand_id, "critical": ("__other__" if r.kind == "mutant" else r.target_ref)}) + "\n")
        a = run(d, jp, scratch / "out")
        conf, res = a["conf"], a["res"]
        ok(conf.human.isin(["changed", "same", "unresolved"]).all() and (conf.n_answers == 2).all(), "confirmation: every candidate has two answers")
        ok(set(conf[conf.human == "unresolved"].cand_id) == uns, f"confirmation: an 'unsure' from either annotator leaves the item unresolved ({len(uns)} planted)")
        ok(conf[conf.scored].shape[0] == 150 - len(uns) and not conf.construction_failure.any(), "confirmation: all other items are scored, no construction failures")
        sc = res["scores"]
        ok(sc["all"]["judge_sens"]["rate"] == 1.0 and sc["all"]["judge_fa"]["rate"] == 0.0, "scoring: planted judge has sensitivity 1 and false-alarm 0")
        ok(sc["all"]["n_mut"] == 100 - len([c for c in uns if kd[kd.cand_id == c].kind.iloc[0] == "mutant"]), "scoring: only confirmed mutants are in the denominator")
        ok("mcnemar" in sc and set(sc["mcnemar"]) == {"judge_vs_surface", "judge_vs_overlap"}, "scoring: McNemar judge vs each baseline")
        # a mutant both annotators call same is a construction failure, not scored; a disagreement is unresolved
        s2 = s.copy(); m0 = key[key.kind == "mutant"].cand_id.iloc[1]; c0 = key[key.kind == "control"].cand_id.iloc[1]
        s2.loc[s2.item_id.isin(key[key.cand_id == m0].item_id), "q1"] = "same"
        i1 = key[(key.cand_id == c0)].iloc[0]; s2.loc[(s2.item_id == i1.item_id) & (s2.annotator == i1.annotator), "q1"] = "different"
        d2 = scratch / "ret2"; d2.mkdir()
        for a_, g in s2.groupby("annotator"):
            g.to_csv(d2 / f"labels_part29_{a_}.csv", index=False)
        a2 = run(d2, jp, scratch / "out2")
        c2 = a2["conf"].set_index("cand_id")
        ok(c2.loc[m0, "construction_failure"] and not c2.loc[m0, "scored"] and c2.loc[c0, "human"] == "unresolved", "confirmation: mutant called same = construction failure, disagreement = unresolved")
        # QC
        x = pd.read_csv(d / "labels_part29_P01.csv", dtype=str, keep_default_na=False)
        x2 = pd.concat([x, x.iloc[:2], x.iloc[:1].assign(practice="1"), x.iloc[:1].assign(annotator="P02"), x.iloc[:1].assign(q1="maybe", item_id="zz")])
        y, rep = qc(x2, key)
        ok(rep["practice_dropped"] == 1 and rep["duplicate"] == 2 and rep["wrong_annotator"] == 1 and rep["unknown_item"] == 1 and len(y) == len(x), f"qc: practice, duplicates, other annotator's item, unknown id {rep}")
        # incomplete annotator dropped (their items fall to one answer = unresolved)
        s3 = s[~((s.annotator == "P03") & (s.groupby("annotator").cumcount() >= 5))]
        d3 = scratch / "ret3"; d3.mkdir()
        for a_, g in s3.groupby("annotator"):
            g.to_csv(d3 / f"labels_part29_{a_}.csv", index=False)
        a3 = run(d3, jp, scratch / "out3")
        ok(a3["res"]["dropped_annotators"] == ["P03"], "completion: an annotator below 80% is dropped")
        # baselines run without a judge file
        a4 = run(d, scratch / "nojudge.jsonl", scratch / "out4")
        ok(a4["res"]["scores"]["judge_scored"] is False and "surface_sens" in a4["res"]["scores"]["all"], "scoring: baselines are scored before any judge run; the judge is not")
        ok(abs(kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) - 1) < 1e-9 and mcnemar_exact(5, 0) == 0.0625, "stats: kappa and exact McNemar on known cases")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print("SELF-CHECK", "PASSED" if not fails else f"FAILED ({len(fails)})")
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--returns", default=str(ROOT / "annotation" / "returns_part29"))
    ap.add_argument("--judge", default=str(JUDGE))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "oracle_indep_human"))
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    r = run(Path(a.returns), Path(a.judge), Path(a.out))
    print(json.dumps(r["res"], indent=1, default=str)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
