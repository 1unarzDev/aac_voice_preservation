"""Resolve critical extraction labels across frozen runs, without new judging.

Critical labels have dimension-specific value sets: the extraction key is
(text_id, input_text, dimension), independent of family/model/arm. A text/input
can occur in multiple factorial critical dimensions; these are separate labels.
Arbiter > unanimous available J1/J2 agreements > unresolved. Conflicting labels
at the winning priority remain unresolved, with all provenance retained.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import runio

DEFAULT_RUNS = ["pilot1", "main1", "guard1", "span1", "expB1", "expC1", "oracle_inject"]


def build(runs):
    units = defaultdict(list)
    for run in runs:
        directory = runio.ROOT / "runs" / run
        dimensions = {}
        for filename in ("judgments.jsonl", "arbiter.jsonl"):
            p = directory / filename
            for line_no, row in enumerate(runio.read_jsonl(p) if p.exists() else [], 1):
                base = (row["text_id"], row["family_id"], row["input_text"])
                dim = row.get("dimension") or dimensions.get(base)
                if dim is None:
                    raise ValueError(f"Missing dimension: {p}:{line_no}")
                dimensions[base] = dim
                key = (row["text_id"], row["input_text"], dim)
                is_arbiter = filename == "arbiter.jsonl"
                j1, j2 = row.get("J1_critical"), row.get("J2_critical")
                label = row.get("critical") if is_arbiter else j1 if j1 is not None and j1 == j2 else None
                units[key].append(dict(path=str(p.relative_to(runio.ROOT)), line=line_no,
                                       family_id=row["family_id"], kind="arbiter" if is_arbiter else "judge",
                                       critical=label, J1_critical=j1, J2_critical=j2))
    result = []
    for (tid, inp, dim), evidence in sorted(units.items()):
        arb = {e["critical"] for e in evidence if e["kind"] == "arbiter" and e["critical"] is not None}
        agree = {e["critical"] for e in evidence if e["kind"] == "judge" and e["critical"] is not None}
        candidates = arb or agree
        label = next(iter(candidates)) if len(candidates) == 1 else None
        source = ("arbiter" if arb else "agree") if label is not None else None
        result.append(dict(text_id=tid, input_text=inp, dimension=dim, critical=label,
                           critical_source=source, conflict=len(candidates) > 1,
                           evidence=evidence))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS)
    ap.add_argument("--out", type=Path, default=runio.ROOT / "annotation/label_resolution.jsonl")
    a = ap.parse_args()
    rows = build(a.runs)
    runio.write_jsonl(a.out, rows)
    summary = dict(runs=a.runs, key=["text_id", "input_text", "dimension"], n_units=len(rows),
                   sources=dict(Counter(r["critical_source"] or "unresolved" for r in rows)),
                   conflicts=sum(r["conflict"] for r in rows))
    (runio.ROOT / "analysis/label_resolution_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
