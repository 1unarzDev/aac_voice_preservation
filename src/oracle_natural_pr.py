"""Oracle precision / recall / F1 on natural, unseeded outputs.

Reuses the verdict-level 2x2 counts that src/score_gold.py writes into
annotation/judge_validation_<run>.json (judge verdict vs human-consensus verdict,
"judge+/ref+" = judge_T_ref_T).  Sets: main1 (H7 gate), new (Part 10), elic (Part 12),
hw (Part 13).  Scope "primary" (quarantined refusal/acceptance families excluded; identical
to "all" outside main1).  Reference = human consensus; positives are:
  violation            reference says the critical value was changed
  preservation_failure reference says the constraint-preserving verdict is False
  assumption           reference says an assumption was made (bare/noncritical input)
Run: .venv/bin/python src/oracle_natural_pr.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/oracle_natural"
SETS = [("main1", "H7 gate (main1)"), ("new", "Part 10 (gold_new)"),
        ("elic", "Part 12 (elicitation)"), ("hw", "Part 13 (human-written)")]


def wilson(k, n, z=1.959964):
    if not n:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def prf(tp, fp, fn):
    P = tp / (tp + fp) if tp + fp else None
    R = tp / (tp + fn) if tp + fn else None
    F = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "n_ref_pos": tp + fn, "n_judge_pos": tp + fp,
            "precision": P, "precision_ci": wilson(tp, tp + fp),
            "recall": R, "recall_ci": wilson(tp, tp + fn), "f1": F}


def counts(c, flip):
    tt, tf, ft, ff = (c["judge_T_ref_T"], c["judge_T_ref_F"], c["judge_F_ref_T"], c["judge_F_ref_F"])
    if flip:   # positive class = verdict False (preservation failure)
        return ff, ft, tf
    return tt, tf, ft


def main():
    res = {"scope": "primary", "reference": "human consensus", "sets": {}}
    pool = {}
    for key, label in SETS:
        v = json.load(open(ROOT / f"annotation/judge_validation_{key}.json"))["human"]["verdict"]
        res["sets"][key] = {"label": label}
        for name, ent, flip in (("violation", "violation", False),
                                ("preservation_failure", "constraint_preserving", True),
                                ("assumption", "assumption", False)):
            c = (v.get(ent) or {}).get("primary")
            if not c:
                continue
            tp, fp, fn = counts(c, flip)
            r = prf(tp, fp, fn)
            r["n_units"] = c["n"]
            res["sets"][key][name] = r
            if name != "assumption" and key != "elic":
                p = pool.setdefault(name, [0, 0, 0]); p[0] += tp; p[1] += fp; p[2] += fn
    res["pooled_failure_sets"] = {k: prf(*p) for k, p in pool.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(res, indent=1))
    L = ["# Oracle on faults nobody seeded", "",
         "Judge verdict vs human-consensus verdict on the four human-labelled sets of natural model "
         "outputs (counts from `score_gold.py` verdict agreement, scope primary). Wilson 95% CIs.", "",
         "| set | verdict | n | ref+ | TP | FP | FN | precision [CI] | recall [CI] | F1 |", "|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "n/a" if x is None else f"{100*x:.1f}"
    ci = lambda x, c: f"{f(x)} [{f(c[0])}, {f(c[1])}]"
    rows = [(res["sets"][k]["label"], n, res["sets"][k][n]) for k, _ in SETS
            for n in ("violation", "preservation_failure", "assumption") if n in res["sets"][k]]
    rows += [("pooled main1+new+hw", n, dict(r, n_units=None)) for n, r in res["pooled_failure_sets"].items()]
    for lab, n, r in rows:
        L.append(f"| {lab} | {n} | {r['n_units'] or ''} | {r['n_ref_pos']} | {r['tp']} | {r['fp']} | {r['fn']} | "
                 f"{ci(r['precision'], r['precision_ci'])} | {ci(r['recall'], r['recall_ci'])} | {f(r['f1'])} |")
    L += ["", "Notes: few positives in single sets (violation positives are few per set), so intervals are wide; pooled rows "
          "sum main1, Part 10 and Part 13 (distinct items). Part 12 supports only the assumption verdict "
          "(positive = assumption made; 8 negatives). Reference is human consensus, with ties/unsure excluded."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


main()
