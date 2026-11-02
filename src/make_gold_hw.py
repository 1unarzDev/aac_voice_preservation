"""Part 13: gold-labelling set (~150 outputs) from the model run on the CHECKED human-written pairs (run hw1).

usage: python src/make_gold_hw.py [--run hw1] [--run-dir runs/hw1] [--items data/items/hw.jsonl] [--n 150]
          [--seed 20261108] [--plan annotation/assignments/plan.json] [--check-key annotation/written/check_key.csv]
          [--part-out annotation_package/stage3/part13_gold_hw.json] [--keep-checked]

Frame: extraction units of the run (src/make_gold.build_units_multi) on data/items/hw.jsonl (families kept by
src/score_pair_checks.py after Stage 2), then independence exclusions for the Part 13 coders
(plan['part13_coders']):
  * families any coder WROTE (writer_id), always;
  * families any coder CHECKED (their Stage 2 file or tie-break file holds the pair, check_key.csv check_id),
    unless --keep-checked; if this leaves fewer than 2n units the checked rule is dropped automatically (logged).
Strata: run x dimension x production critical label (DISAGREE if J1 != J2) x channel group (ambig = bare/noncrit,
chip = chip1/chipall, full). Draw as src/gold_subset.py. Outputs: --part-out (blind, neutral ids),
annotation/gold_key_hw.csv (private), annotation/gold_sample_hw.json. Returns labels_gold_hw_<ID>.csv ->
annotation/returns_gold_hw/.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import gold_subset as GS  # noqa: E402
import make_gold as G  # noqa: E402
import runio  # noqa: E402

CH_GROUP = {"bare": "ambig", "noncrit": "ambig", "chip1": "chip", "chipall": "chip", "full": "full"}


def checked_by(check_key: Path, coders: set) -> set:
    out = set()
    if not check_key.exists():
        return out
    with open(check_key, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            who = {c.rsplit("_check_", 1)[0] if "_check_" in c else c.rsplit("_tiebreak", 1)[0]
                   for c in (r.get("check_id") or "").split()}
            if who & coders:
                out.add(r["family_id"])
    return out


def frame(units, items, coders, checked, n, keep_checked=False):
    def run(use_checked):
        kept, why = [], {"written_by_coder": 0, "checked_by_coder": 0}
        for u in units:
            fams = u["families"].split("|")
            if any(items[f].get("writer_id") in coders for f in fams):
                why["written_by_coder"] += 1; continue
            if use_checked and any(f in checked for f in fams):
                why["checked_by_coder"] += 1; continue
            grp = "|".join(sorted({CH_GROUP.get(c, c) for c in u["channels"].split("|")}))
            u["group"] = "all"
            GS.restratify(u, grp)
            kept.append(u)
        return kept, why
    kept, why = run(not keep_checked)
    why["checked_rule"] = "applied" if not keep_checked else "off (--keep-checked)"
    if not keep_checked and len(kept) < 2 * n:
        kept, why = run(False)
        why["checked_rule"] = f"dropped automatically: frame < 2n ({2 * n})"
    return kept, why


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="hw1"); ap.add_argument("--run-dir")
    ap.add_argument("--items", default=str(ROOT / "data/items/hw.jsonl"))
    ap.add_argument("--n", type=int, default=150); ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--plan", default=str(ROOT / "annotation/assignments/plan.json"))
    ap.add_argument("--check-key", default=str(ROOT / "annotation/written/check_key.csv"))
    ap.add_argument("--keep-checked", action="store_true")
    ap.add_argument("--part-out", default=str(ROOT / "annotation_package/stage3/part13_gold_hw.json"))
    ap.add_argument("--key-out", default=str(ROOT / "annotation/gold_key_hw.csv"))
    ap.add_argument("--sample-out", default=str(ROOT / "annotation/gold_sample_hw.json"))
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    coders = set(plan["part13_coders"])
    items = runio.load_items(a.items)
    import pandas as pd
    rd = Path(a.run_dir) if a.run_dir else ROOT / "runs" / a.run
    # run was judged on ALL candidates (D-052); the frame is the kept pairs only
    not_kept = set(pd.read_parquet(rd / "scored.parquet", columns=["family_id"]).family_id) - set(items)
    units = G.build_units_multi([a.run], not_kept, {a.run: a.run_dir} if a.run_dir else None, items)
    kept, why = frame(units, items, coders, checked_by(Path(a.check_key), coders), a.n, a.keep_checked)
    design = {"run": a.run, "frame_units_before_exclusions": len(units), "exclusions": why,
              "part13_coders": sorted(coders),
              "strata": "run x dimension x production critical label (DISAGREE if J1!=J2) x channel group"}
    GS.draw(kept, {"all": a.n}, "hw", a.seed, Path(a.part_out), Path(a.key_out), Path(a.sample_out), design)
    return 0


if __name__ == "__main__":
    sys.exit(main())
