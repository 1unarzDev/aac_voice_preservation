"""Shared draw for gold-labelling subsets of one run (Parts 12 and 13), wrapping src/make_gold.py.

Same design as make_gold.py multi-run mode (B3 / Part 10): extraction units from build_units_multi (exact text x
critical dimension x visible input; production critical label, J1/J2/L0 kept for the key), weights
w = (1 + 3*J1/J2 disagreement + 2*positive) / sqrt(stratum size), Poisson PPS with pi solved so that
sum(pi) = the allocation of each group, units in a fixed sha1 order with one seeded uniform each, random
presentation order, neutral item ids g-<sha1(name|run|text|dim|input)[:10]>. Differences: callers filter the
frame first (annotator-independence exclusions) and may add a stratum suffix (channel kind) and split the
allocation over groups. Blind part file for annotate.html (5 practice items + items carrying only
item_id/text/critical/input_text), private key CSV, design JSON with frame, exclusions and realised composition.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

import make_gold as G
from labels import ADDED_CONTENT_OPTIONS, DEFINITIONS, GENERAL_DIMS, GENERAL_OPTIONS

KEY_COLS = (["item_id", "run", "group", "text_id", "family_id", "families", "dimension", "input_text", "text",
             "model", "models", "channels", "prompts", "variants", "n_occurrences", "stratum", "disagree", "positive",
             "pi", "critical_source"]
            + [f"{v}_{d}" for v in ("J1", "J2") for d in G.JUDGED_DIMS]
            + G.JUDGED_DIMS + [f"L0_{d}" for d in GENERAL_DIMS] + ["text_ids", "output_ids"])


def draw(units: list[dict], alloc: dict[str, int], name: str, seed: int, part_out: Path, key_path: Path,
         sample_path: Path, design: dict) -> list[dict]:
    """units carry 'group' (key of alloc) and 'stratum'. Returns the chosen units (presentation order)."""
    size = Counter(u["stratum"] for u in units)
    for g, n in alloc.items():
        gu = [u for u in units if u["group"] == g]
        w = [(1 + 3 * u["disagree"] + 2 * u["positive"]) / math.sqrt(size[u["stratum"]]) for u in gu]
        for u, pi in zip(gu, G.solve_pi(w, n) if gu else []):
            u["pi"] = pi
    units = [u for u in units if u["group"] in alloc]
    h = lambda u: hashlib.sha1(json.dumps([name, u["run"], u["norm_text"], u["dimension"], u["input_text"]]).encode()).hexdigest()  # noqa: E731
    order = sorted(units, key=h)
    rng = random.Random(seed)
    chosen = [u for u in order if rng.random() < u["pi"]]
    for u in chosen:
        u["item_id"] = "g-" + h(u)[:10]
    assert len({u["item_id"] for u in chosen}) == len(chosen)
    rng.shuffle(chosen)
    payload = {"run": f"gold_{name}", "codebook_version": G.CODEBOOK_VERSION,
               "general_dims": [{"name": d, "definition": DEFINITIONS[d], "options": GENERAL_OPTIONS[d]} for d in GENERAL_DIMS],
               "added_content": {"definition": DEFINITIONS["added_content"], "options": ADDED_CONTENT_OPTIONS},
               "practice": [{**G.item_for_annotator(p), "expected": p["expected"], "feedback": p["feedback"]} for p in G.PRACTICE],
               "items": [G.item_for_annotator(u) for u in chosen], "part": f"gold_{name}"}
    part_out.parent.mkdir(parents=True, exist_ok=True)
    part_out.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with key_path.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=KEY_COLS, extrasaction="ignore")
        wr.writeheader()
        for u in sorted(chosen, key=lambda u: u["item_id"]):
            wr.writerow({k: u.get(k) for k in KEY_COLS})

    def comp(us):
        return {"n": len(us), "disagree": sum(u["disagree"] for u in us), "positive": sum(u["positive"] for u in us),
                "by_dimension": dict(sorted(Counter(u["dimension"] for u in us).items())),
                "by_model": dict(sorted(Counter(u["model"] for u in us).items())),
                "by_stratum": dict(sorted(Counter(u["stratum"] for u in us).items()))}
    summ = {"name": name, "seed": seed, "allocation": alloc, **design,
            "weights": "w=(1+3*J1/J2 disagreement+2*positive)/sqrt(stratum size); Poisson PPS per group; "
                       "fixed sha1 unit order, one seeded uniform per unit",
            "groups": {g: {"frame": comp([u for u in units if u["group"] == g]),
                           "sample": comp([u for u in chosen if u["group"] == g]),
                           "expected_n": round(sum(u["pi"] for u in units if u["group"] == g), 2)} for g in alloc},
            "sample_total": len(chosen),
            "key_sha256": hashlib.sha256(key_path.read_bytes()).hexdigest(),
            "part_sha256": hashlib.sha256(part_out.read_bytes()).hexdigest()}
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.write_text(json.dumps(summ, indent=1) + "\n")
    print(f"{name}: frame {len(units)} units -> sampled {len(chosen)} "
          f"(expected {sum(u['pi'] for u in units):.1f}); wrote {part_out}, {key_path}, {sample_path}")
    return chosen


def restratify(u: dict, suffix: str) -> None:
    crit = "DISAGREE" if u.get("J1_critical") != u.get("J2_critical") else u["critical"]
    u["stratum"] = f"{u['run']}|{u['dimension']}|{crit}|{suffix}"
