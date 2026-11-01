"""CPU-only checks for the cycle-3 decision; no generation or judging.

The sole new contrast is the lay review's requested G1 minus G1s comparison.
It is exploratory, uses the existing strict-pass endpoint and quarantine,
and resamples all paired rows jointly by discovery family.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from interventions import CUE, guard_frame

SEED, N_BOOT = 20261101, 10000


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


sc, _ = guard_frame(ROOT / "runs/guard1")
keys = ["base_key", "family_id", "variant", "channel"]
cue = sc[sc.channel.isin(CUE)].copy()
assert not cue.duplicated(keys + ["prompt_id"]).any()
wide = cue.pivot(index=keys, columns="prompt_id", values="strict_fail")
planned = len(wide)
wide = wide.dropna(subset=["P0", "G1", "G1s"])
passed = ~wide.astype(bool)
assert len(wide) == 1392 and planned == 1392
assert passed.sum().to_dict() == {"G1": 1375, "G1s": 1346, "P0": 1312}
gain = (passed.G1.astype(int) - passed.G1s.astype(int)).rename("diff").reset_index()
aggregated = gain.groupby("family_id", sort=True).agg(k=("diff", "sum"), n=("diff", "size"))
weights = np.random.default_rng(SEED).multinomial(
    len(aggregated), np.full(len(aggregated), 1 / len(aggregated)), size=N_BOOT
)
draws = weights @ aggregated[["k", "n"]].to_numpy()
interval = np.quantile(draws[:, 0] / draws[:, 1], [.025, .975])
contrast = {
    "endpoint": "G1 strict-pass share minus G1s strict-pass share",
    "status": "exploratory paired stored-configuration comparison, not feedback causality",
    "n": len(wide), "n_planned": planned, "n_missing": planned - len(wide),
    "n_families": len(aggregated), "pass_counts": {k: int(v) for k, v in passed.sum().items()},
    "G1_only_pass": int((passed.G1 & ~passed.G1s).sum()),
    "G1s_only_pass": int((passed.G1s & ~passed.G1).sum()),
    "net_passes": int(gain["diff"].sum()),
    "estimate_pp": float(gain["diff"].mean() * 100),
    "ci95_pp": (interval * 100).tolist(),
    "by_family": aggregated.reset_index().to_dict("records"),
}

# Verify the c3 illustration manifest without rewriting another worker's file.
story = json.loads((ROOT / "ideas/cycles/c3/story_evidence.json").read_text())
records = [r for card in story["cards"] for r in card["outputs"]]
outputs = {}
for run in {r["run"] for r in records}:
    outputs[run] = [json.loads(line) for line in (ROOT / f"runs/{run}/outputs.jsonl").open()]
for r in records:
    stored = outputs[r["run"]][r["jsonl_line"] - 1]
    assert all(stored[k] == r[k] for k in ["output_id", "request_key", "text", "input_text"]), r
changed = [p for p, h in story["sha256"].items() if digest(p) != h]

human = json.loads((ROOT / "annotation/judge_validation_main1.json").read_text())["human"]
heldout = {d: {k: v["sampled_test/final"][k] for k in ["n", "kappa", "kappa_ci"]}
           for d, v in human["judge"].items()}
paths = ["runs/guard1/scored.parquet", "runs/guard1/generations.jsonl", "src/interventions.py",
         "annotation/label_resolution.jsonl", "ideas/cycles/c3/story_evidence.json",
         "annotation/judge_validation_main1.json", "ideas/cycles/c3/synth_checks.py"]
result = {
    "date": "2026-11-01", "seed": SEED, "n_boot": N_BOOT,
    "method": "95% pointwise percentile CI; whole-family joint multinomial resampling; row-weighted rates",
    "guard_increment": contrast,
    "story_verification": {"verified_occurrences": len(records), "hash_mismatches": changed,
                           "note": "String equality does not establish label correctness or typicality."},
    "human_heldout": heldout,
    "sha256": {p: digest(p) for p in paths},
}
(Path(__file__).with_name("synth_checks.json")).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"guard_increment": {k: v for k, v in contrast.items() if k != "by_family"},
                  "story_verification": result["story_verification"], "human_heldout": heldout}, indent=2))
