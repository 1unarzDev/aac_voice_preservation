#!/usr/bin/env python3
"""Strict-rule (ties and unsure count as disagreement) recomputation of the Part 10 human gate.

robust_t7_human_gate.py covers the H7, Part 12 and Part 13 gates but not Part 10 (run `new`,
annotation/returns_gold_new). This script calls the same run_gate on that gate and writes
paper/journal/part10_gate.json. It reads stored labels only (0 generation / 0 judge calls)
and writes nothing under analysis/.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import robust_t7_human_gate as T  # noqa: E402
g = dict(run="new", pats=["annotation/returns_gold_new/*.csv"], stored="annotation/judge_validation_new.json")
res = T.run_gate("part10_new", g)
(Path(__file__).parent / "part10_gate.json").write_text(json.dumps(res, indent=1))
print({d: res["dims"][d]["test/R1"] for d in res["dims"]})
