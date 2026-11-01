"""Part 12: gold-labelling set (~150 outputs) from the model run on human-elicited keywords (run elic1).

usage: python src/make_gold_elic.py [--run elic1] [--run-dir runs/elic1] [--items data/items/elic.jsonl]
          [--n 150] [--baseline-n 0] [--seed 20261105] [--plan annotation/assignments/plan.json]
          [--elic-key annotation/elicitation_key.jsonl] [--part-out annotation_package/stage2/part12_gold_elic.json]

Frame: extraction units of the run (src/make_gold.build_units_multi: exact text x critical dimension x visible
input; judged, valid rows; refusal/acceptance quarantine excluded), then
  * independence exclusions (Part 12 coders = plan['part12_coders']): every unit of a message in a set any
    coder elicited (plan['part12_excluded_sets'], s01-s04 by design), and every unit whose input is a keyword
    set a coder typed (channel human_<coder>; redundant with the set rule, kept as a guard);
  * group 'human' = the unit's input comes from a human channel (human_<ID>), else 'pos_cap4' (baseline);
    only 'human' is drawn unless --baseline-n > 0.
Strata: run x dimension x production critical label (DISAGREE if J1 != J2) x group. Draw as src/gold_subset.py.
Outputs (blind part file, neutral ids; private key): --part-out, annotation/gold_key_elic.csv,
annotation/gold_sample_elic.json. Returns: labels_gold_elic_<ID>.csv -> annotation/returns_gold_elic/; scoring as
Part 10 (src/score_gold.py with this key).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import gold_subset as GS  # noqa: E402
import make_gold as G  # noqa: E402
import runio  # noqa: E402


def frame(units: list[dict], items: dict, elic_set: dict, excl_sets: set, coders: set) -> tuple[list[dict], dict]:
    kept, why = [], {"excluded_set": 0, "coder_keywords": 0}
    coder_ch = {f"human_{c}" for c in coders}
    for u in units:
        fams = u["families"].split("|")
        sets = {elic_set.get(items[f].get("elic_item_id")) for f in fams}
        chans = set(u["channels"].split("|"))
        if sets & excl_sets:
            why["excluded_set"] += 1; continue
        if chans & coder_ch:
            why["coder_keywords"] += 1; continue
        u["group"] = "human" if any(c.startswith("human_") for c in chans) else "pos_cap4"
        GS.restratify(u, u["group"])
        kept.append(u)
    return kept, why


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="elic1"); ap.add_argument("--run-dir")
    ap.add_argument("--items", default=str(ROOT / "data/items/elic.jsonl"))
    ap.add_argument("--n", type=int, default=150); ap.add_argument("--baseline-n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261105)
    ap.add_argument("--plan", default=str(ROOT / "annotation/assignments/plan.json"))
    ap.add_argument("--elic-key", default=str(ROOT / "annotation/elicitation_key.jsonl"))
    ap.add_argument("--part-out", default=str(ROOT / "annotation_package/stage2/part12_gold_elic.json"))
    ap.add_argument("--key-out", default=str(ROOT / "annotation/gold_key_elic.csv"))
    ap.add_argument("--sample-out", default=str(ROOT / "annotation/gold_sample_elic.json"))
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    coders, excl_sets = set(plan["part12_coders"]), set(plan["part12_excluded_sets"])
    items = runio.load_items(a.items)
    elic_set = {k["item_id"]: k["set"] for k in map(json.loads, Path(a.elic_key).open())}
    units = G.build_units_multi([a.run], set(), {a.run: a.run_dir} if a.run_dir else None, items)
    kept, why = frame(units, items, elic_set, excl_sets, coders)
    alloc = {"human": a.n - a.baseline_n} | ({"pos_cap4": a.baseline_n} if a.baseline_n else {})
    design = {"run": a.run, "frame_units_before_exclusions": len(units), "exclusions": why,
              "part12_coders": sorted(coders), "excluded_sets": sorted(excl_sets),
              "strata": "run x dimension x production critical label (DISAGREE if J1!=J2) x group (human|pos_cap4)"}
    GS.draw(kept, alloc, "elic", a.seed, Path(a.part_out), Path(a.key_out), Path(a.sample_out), design)
    return 0


if __name__ == "__main__":
    sys.exit(main())
