"""Score human gold: human-human reliability and judge validity (PLAN H7).

  python src/score_gold.py --run pilot1 --csv annotation/returns/*.csv [--seed 20261031]
  python src/score_gold.py --self-check

Inputs
  annotate.html CSV exports (item_id, annotator, critical, polarity, speech_act, agent,
  certainty, politeness, added_content, time_ms, skip, ...). Practice rows are ignored.
  annotation/gold_key_<run>.csv from make_gold.py (judge labels, layer0 labels, pi).
  Optional annotation/adjudicated_<run>.csv (item_id + dims) overrides the consensus.
Outputs
  annotation/judge_validation_<run>.json and .csv
Method
  alpha     Krippendorff nominal alpha per dimension over all annotators (port of
            old/src/reliability.py; cross-checked against the `krippendorff` package).
            Skipped / blank answers are missing data. Unit bootstrap 95% CI.
  consensus majority label among non-skip annotators; ties -> adjudicated file, else
            the item is excluded for that dimension (counted).
  split     calibration vs test by a seeded hash of item_id (default 25% calibration,
            i.e. ~40 of 160). Calibration is for prompt/codebook tuning; report TEST.
  metrics   per dim and source (final, J1, J2, L0): accuracy, Cohen kappa, per-label
            precision/recall, confusion (rows = human), and IPW accuracy (weights 1/pi).
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agree_stats import cohen_kappa, confusion, prf  # noqa: E402
from labels import GENERAL_DIMS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIMS = ["critical"] + GENERAL_DIMS + ["added_content"]
SEED = 20261031
H7_KAPPA = 0.6


# ----------------------------------------------- Krippendorff (from old reliability.py)

def coincidence(units: list[list[int]], k: int) -> list[list[float]]:
    o = [[0.0] * k for _ in range(k)]
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        w = 1.0 / (m - 1)
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[vals[i]][vals[j]] += w
    return o


def alpha_nominal(units: list[list[int]], k: int) -> float | None:
    o = coincidence(units, k)
    marg = [sum(r) for r in o]
    n = sum(marg)
    if n < 2:
        return None
    do = sum(o[c][g] for c in range(k) for g in range(k) if c != g) / n
    de = sum(marg[c] * marg[g] for c in range(k) for g in range(k) if c != g) / (n * (n - 1))
    return None if de == 0 else 1.0 - do / de


def bootstrap_ci(units, k, seed, reps=2000):
    rng = random.Random(seed)
    if len(units) < 2:
        return None
    draws = [a for _ in range(reps)
             if (a := alpha_nominal([units[rng.randrange(len(units))] for _ in units], k)) is not None]
    if len(draws) < reps // 2:
        return None
    draws.sort()
    return round(draws[int(0.025 * len(draws))], 3), round(draws[int(0.975 * len(draws)) - 1], 3)


def self_check() -> int:
    obs = [[1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
           [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
           [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None]]
    units = [[o[u] - 1 for o in obs if o[u] is not None] for u in range(12)]
    units = [u for u in units if len(u) >= 2]
    got = alpha_nominal(units, 5)
    ok = abs(got - 0.675258) < 5e-6           # pinned value from old reliability.py
    try:
        import numpy as np
        import krippendorff as ref
        arr = np.array([[np.nan if v is None else v for v in r] for r in obs], dtype=float)
        want = ref.alpha(reliability_data=arr, level_of_measurement="nominal")
        ok &= abs(got - want) < 1e-9
        print(f"nominal alpha {got:.6f}  pinned 0.675258  krippendorff pkg {want:.6f}")
    except ImportError:
        print(f"nominal alpha {got:.6f}  pinned 0.675258")
    print("self-check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------- io

def read_csv(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def is_cal(item_id: str, seed: int, frac: float) -> bool:
    h = int(hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest()[:8], 16)
    return h / 0xFFFFFFFF < frac


def metrics(pred: list, gold: list, w: list[float]) -> dict:
    n = len(pred)
    if n == 0:
        return {"n": 0}
    acc = sum(p == g for p, g in zip(pred, gold)) / n
    ipw = sum(wi for p, g, wi in zip(pred, gold, w) if p == g) / sum(w)
    labels = sorted(set(gold) | set(pred), key=str)
    return {"n": n, "acc": round(acc, 3), "acc_ipw": round(ipw, 3),
            "kappa": cohen_kappa(pred, gold),
            "per_label": {l: prf(pred, gold, l) for l in labels},
            "confusion_rows_human": confusion(pred, gold)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run")
    ap.add_argument("--csv", nargs="*", default=[])
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--cal-frac", type=float, default=0.25)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not a.run or not a.csv:
        ap.error("--run and --csv are required")
    key = {r["item_id"]: r for r in read_csv(ROOT / f"annotation/gold_key_{a.run}.csv")}
    paths = [p for pat in a.csv for p in glob.glob(pat)]
    ann: dict[str, dict[str, dict]] = {}       # item -> annotator -> row (last wins)
    for p in paths:
        for r in read_csv(p):
            if r.get("item_id", "").startswith("practice") or r.get("item_id") not in key:
                continue
            ann.setdefault(r["item_id"], {})[r["annotator"]] = r
    annotators = sorted({a_ for v in ann.values() for a_ in v})
    adj_p = ROOT / f"annotation/adjudicated_{a.run}.csv"
    adj = {r["item_id"]: r for r in read_csv(adj_p)} if adj_p.exists() else {}

    def lab(r, d):
        v = (r.get(d) or "").strip()   # skipped / unsure questions are exported blank
        return v or None

    rep: dict = {"run": a.run, "annotators": annotators, "n_items_annotated": len(ann),
                 "seed": a.seed, "cal_frac": a.cal_frac, "alpha_nominal": {}, "judge": {}}
    rows_out = []
    for d in DIMS:
        # --- human-human alpha
        cats = sorted({lab(r, d) for v in ann.values() for r in v.values()} - {None})
        idx = {c: i for i, c in enumerate(cats)}
        units = [[idx[x] for r in v.values() if (x := lab(r, d)) is not None] for v in ann.values()]
        units = [u for u in units if len(u) >= 2]
        al = alpha_nominal(units, max(len(cats), 1))
        rep["alpha_nominal"][d] = {"alpha": None if al is None else round(al, 3),
                                   "n_units": len(units), "ci95": bootstrap_ci(units, len(cats), a.seed)}
        # --- consensus
        cons, ties = {}, 0
        for item, v in ann.items():
            if item in adj and (adj[item].get(d) or "").strip():
                cons[item] = adj[item][d].strip()
                continue
            c = Counter(x for r in v.values() if (x := lab(r, d)) is not None).most_common()
            if not c:
                continue
            if len(c) > 1 and c[0][1] == c[1][1]:
                ties += 1
                continue
            cons[item] = c[0][0]
        # --- judge vs human
        rep["judge"][d] = {"consensus_ties_excluded": ties}
        for split in ("calibration", "test"):
            items = [i for i in cons if is_cal(i, a.seed, a.cal_frac) == (split == "calibration")]
            for src in ("final", "J1", "J2", "L0"):
                col = d if src == "final" else f"{src}_{d}"
                if col not in next(iter(key.values())):
                    continue
                pr = [(key[i][col] or None, cons[i], 1 / float(key[i]["pi"])) for i in items]
                pr = [x for x in pr if x[0] is not None]
                m = metrics([x[0] for x in pr], [x[1] for x in pr], [x[2] for x in pr])
                rep["judge"][d][f"{split}/{src}"] = m
                rows_out.append({"dimension": d, "split": split, "source": src, "n": m["n"],
                                 "acc": m.get("acc"), "acc_ipw": m.get("acc_ipw"),
                                 "kappa": m.get("kappa"),
                                 "passes_H7": (m.get("kappa") or 0) >= H7_KAPPA})
    out = ROOT / f"annotation/judge_validation_{a.run}"
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    with out.with_suffix(".csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
    print(f"annotators: {annotators}; items: {len(ann)}")
    for d in DIMS:
        al = rep["alpha_nominal"][d]
        t = rep["judge"][d].get("test/final", {})
        print(f"  {d:13s} alpha={al['alpha']} (n={al['n_units']})  test/final: n={t.get('n')} "
              f"acc={t.get('acc')} kappa={t.get('kappa')}")
    print(f"wrote {out}.json/.csv  (H7 threshold kappa >= {H7_KAPPA} on the test split)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
