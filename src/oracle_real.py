"""Mutation analysis of the judge oracle on real stored outputs (analysis/oracle_real/PLAN.md).

  python src/oracle_real.py build     # seeded draw, mutants + controls -> runs/oracle_real
  python src/oracle_real.py judge     # production judge, concurrency 4
  python src/oracle_real.py score     # judge + baselines, W-A comparison -> analysis/oracle_real/
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oracle_baselines as B  # noqa: E402
import oracle_real_ops as O  # noqa: E402
import runio  # noqa: E402

ROOT = runio.ROOT
RUN = ROOT / "runs/hw1"
OUTRUN = ROOT / "runs/oracle_real"
OUT = ROOT / "analysis/oracle_real"
HW = ROOT / "data/items/hw.jsonl"
SEED = 20261102
CUE = {"chip1", "chipall", "full"}
DIMS = ["agent", "certainty", "polarity", "politeness", "speech_act", "time_quantity"]
MUT_Q = dict(zip(DIMS, [34, 34, 33, 33, 33, 33]))
CTL_Q = dict(zip(DIMS, [17, 17, 16, 16, 17, 17]))


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (round(c - h, 4), round(c + h, 4))


def build():
    import pandas as pd
    items = runio.load_items(HW)
    d = pd.read_parquet(RUN / "scored.parquet")
    d = d[d.family_id.isin(items.keys()) & (d.valid) & d.channel.isin(CUE) & (d.critical_match == True) & d.critical_source.isin(["agree", "arbiter"])  # noqa: E712
          & (~d.quarantine_refusal_acceptance)]
    pool = {dim: [] for dim in DIMS}
    for dim in DIMS:
        sub = d[d.dimension == dim].sort_values(["family_id", "output_id"])
        # one output per family, one per distinct text (seeded pick)
        rng = random.Random(f"{SEED}|pool|{dim}")
        seen_text, rows = set(), []
        for fid, g in sub.groupby("family_id", sort=True):
            recs = g.to_dict("records")
            rng.shuffle(recs)
            for r in recs:
                if r["text_id"] not in seen_text:
                    seen_text.add(r["text_id"]); rows.append(r); break
        pool[dim] = rows
    sel_m, sel_c, appl = [], [], {}
    used_fam = set()
    for dim in DIMS:
        rng = random.Random(f"{SEED}|mut|{dim}")
        order = pool[dim][:]
        rng.shuffle(order)
        tried = ok = 0
        for r in order:
            if ok >= MUT_Q[dim]:
                break
            tried += 1
            it = items[r["family_id"]]
            ref = it["variants"][r["variant"]]["critical_value"]
            m = O.mutate(dim, ref, r["text"], salt=r["output_id"])
            if m is None:
                continue
            ok += 1
            used_fam.add(r["family_id"])
            sel_m.append({"kind": "mutant", "dimension": dim, "ref": ref, "op": m[0], "text": m[1], "expected": m[2], "orig": r})
        appl[dim] = {"tried": tried, "mutable": ok, "applicability": round(ok / tried, 3) if tried else None}
    ctl_info, usage = {}, {}
    for dim in DIMS:
        rng = random.Random(f"{SEED}|ctl|{dim}")
        order = [r for r in pool[dim] if r["family_id"] not in used_fam]
        rng.shuffle(order)
        ok = 0
        for i, r in enumerate(order):
            if ok >= CTL_Q[dim]:
                break
            e = O.control_edit(r["text"], usage)
            if e is None:
                continue
            ok += 1
            usage[e[0]] = usage.get(e[0], 0) + 1
            it = items[r["family_id"]]
            sel_c.append({"kind": "control", "dimension": dim, "ref": it["variants"][r["variant"]]["critical_value"],
                          "op": e[0], "text": e[1], "expected": it["variants"][r["variant"]]["critical_value"], "orig": r})
        ctl_info[dim] = ok
    rows = []
    for i, s in enumerate(sel_m + sel_c):
        o = s["orig"]
        it = items[o["family_id"]]
        other = next(v for k, v in it["variants"].items() if k != o["variant"])
        rows.append({"rid": f"R{i:03d}", "kind": s["kind"], "dimension": s["dimension"], "ref": s["ref"], "op": s["op"],
                     "text": s["text"], "expected": s["expected"], "orig_text": o["text"], "orig_text_id": o["text_id"],
                     "src_family": o["family_id"], "variant": o["variant"], "model": o["model"], "channel": o["channel"],
                     "input_text": o["input_text"], "ref_source": it["variants"][o["variant"]]["source"],
                     "other_source": other["source"], "critical_options": it["critical_options"]})
    OUT.mkdir(parents=True, exist_ok=True)
    runio.write_jsonl(OUT / "sample.jsonl", rows)
    fams, occ = [], []
    for r in rows:
        fams.append({"family_id": r["rid"], "dimension": r["dimension"], "split": "oracle_real", "context": None,
                     "critical_options": r["critical_options"], "bare": r["input_text"], "noncritical": "",
                     "variants": {"A": {"source": r["text"], "critical_value": r["ref"], "chips": [], "all_chips": []}}})
        rk = hashlib.sha1(json.dumps([r["rid"], r["text"]]).encode()).hexdigest()
        occ.append({"output_id": rk[:16], "text": r["text"], "suggestion_idx": 0, "parse_ok": True, "request_key": rk,
                    "model": r["kind"], "prompt_id": "OR", "temperature": 0.0, "sample_idx": 0, "dimension": r["dimension"],
                    "split": "oracle_real", "input_text": r["input_text"], "finish_reason": "stop", "family_id": r["rid"],
                    "variant": "A", "channel": "full", "valid": True})
    OUTRUN.mkdir(parents=True, exist_ok=True)
    runio.write_jsonl(OUTRUN / "items.jsonl", fams)
    runio.write_jsonl(OUTRUN / "outputs.jsonl", occ)
    (OUTRUN / "config.json").write_text(json.dumps({"run_id": "oracle_real", "items_path": "runs/oracle_real/items.jsonl",
                                                    "note": "real-output mutation analysis; no generation"}, indent=1))
    pdump = {dim: len(pool[dim]) for dim in DIMS}
    (OUT / "draw.json").write_text(json.dumps({"seed": SEED, "pool_sizes": pdump, "mutant_applicability": appl,
                                               "control_counts": ctl_info, "n_mutants": len(sel_m), "n_controls": len(sel_c)}, indent=1))
    print(json.dumps({"pool": pdump, "appl": appl, "controls": ctl_info, "n": (len(sel_m), len(sel_c))}, indent=1))


def judge():
    import judge as J
    J.CONCURRENCY = 4
    asyncio.run(J.judge_run(OUTRUN, None, J.JUDGE_MODEL, "low", ["J1", "J2"]))


if __name__ == "__main__":
    {"build": build, "judge": judge}[sys.argv[1]]() if sys.argv[1] != "score" else __import__("oracle_real_score").main()
