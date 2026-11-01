"""Hash the evidence inventory (scope action2: discovery only; scope c3: all current evidence).

Scope c3 (cycle-3 Action 3) adds the completed W-C/W-D/W-B runs, the guard transfer, applicability,
evidence map and R5 artifacts. Target-paper sources (paper/se4all, paper/caleai) are excluded because they
are edited concurrently; writers rebuild them from the inventoried inputs.

Historical producing commands are unknown unless recorded in --commands. Unknown
is explicit (null), never inferred from a file's name. --snapshot copies every
inventoried file before writing the manifest, preserving a reviewable old version.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
RUNS = ("pilot1", "main1", "guard1", "span1", "expB1", "expC1",
        "oracle_inject", "oracle_challenges")


C3_RUNS = ("r2c1", "r2d1", "wb1", "guard_wc")
C3_ANALYSIS = ("r2c", "r2d", "wb", "applicability", "guard_wc", "evidence_c3", "r5_validator")
C3_EXTRA = ("analysis/EVIDENCE_MAP.md", "orchestration/evidence_map.md", "orchestration/PREREG_R2.md",
            "orchestration/SPEC.md", "ideas/cycles/c2/decision.md", "ideas/cycles/c3/decision.md",
            "ideas/cycles/c3/select_story.py", "ideas/cycles/c3/story_evidence.json",
            "ideas/cycles/c3/story_evidence.v2.json", "ideas/cycles/c3/synth_checks.py",
            "ideas/cycles/c3/synth_checks.json", "data/items/wb.jsonl", "data/specs/wb_sample.jsonl",
            "runs/requests/wb1.jsonl")


def inventory(scope="action2"):
    paths = set()
    for run in RUNS:
        for pattern in ("scored*.parquet", "judgments.jsonl", "arbiter.jsonl", "outputs.jsonl",
                        "generations.jsonl", "config.json", "endpoints.json", "judge_report.json"):
            paths.update((ROOT / "runs" / run).glob(pattern))
    for pattern in ("src/**/*.py", "src/**/*.sh", "tests/**/*.py", "prompts/*", "data/items/*.jsonl",
                    "annotation/*.md", "annotation/*.json", "annotation/*.jsonl", "annotation/*.csv",
                    "annotation/returns*/*.csv", "paper/figs/**/*", "paper/se4all/*.py",
                    "paper/se4all/*macros*", "paper/se4all/*examples*", "paper/se4all/*numbers*",
                    "orchestration/BRIEF.md", "orchestration/decision_log.md",
                    "orchestration/claims_ledger.md", "ideas/cycles/c1/decision.md"):
        paths.update(p for p in ROOT.glob(pattern) if p.is_file() and "__pycache__" not in p.parts
                     and not p.name.startswith("wb_"))
    for directory in ("main1", "main1_quarantine_inclusive", "pilot", "oracle", "interventions"):
        paths.update(p for p in (ROOT / "analysis" / directory).rglob("*") if p.is_file())
    for name in ("EVIDENCE_MANIFEST_prev.json", "reconciliation.md", "reconciliation.json", "changed_endpoints.csv",
                 "changed_labels.csv", "label_resolution_summary.json", "refresh_commands.json",
                 "label_sensitivity.csv", "verify_reconciliation.json"):
        p = ROOT / "analysis" / name
        if p.exists():
            paths.add(p)
    if scope == "c3":
        paths = {p for p in paths if not p.is_relative_to(ROOT / "paper/se4all")}
        for run in C3_RUNS:
            for pattern in ("scored*.parquet", "judgments.jsonl", "arbiter.jsonl", "outputs.jsonl",
                            "generations.jsonl", "config.json", "logical_calls.jsonl", "judge_calls.jsonl"):
                paths.update((ROOT / "runs" / run).glob(pattern))
        for directory in C3_ANALYSIS:
            paths.update(p for p in (ROOT / "analysis" / directory).rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts)
        paths.update(ROOT / x for x in C3_EXTRA if (ROOT / x).exists())
    return sorted(paths)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/EVIDENCE_MANIFEST.json")
    ap.add_argument("--commands", type=Path)
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--scope", choices=["action2", "c3"], default="action2")
    a = ap.parse_args()
    commands = json.loads(a.commands.read_text()) if a.commands else {}
    records = []
    for p in inventory(a.scope):
        rel = str(p.relative_to(ROOT))
        before = p.stat()
        data = p.read_bytes()
        after = p.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f"Evidence changed while hashing: {rel}")
        if a.snapshot:
            dest = a.snapshot / rel
            if dest.exists():
                raise FileExistsError(f"Refusing to replace previous evidence: {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
        records.append(dict(path=rel, sha256=hashlib.sha256(data).hexdigest(),
                            mtime=datetime.fromtimestamp(before.st_mtime, timezone.utc).isoformat(),
                            mtime_ns=before.st_mtime_ns, size_bytes=len(data),
                            producing_command=commands.get(rel)))
    c3 = a.scope == "c3"
    result = dict(schema_version=2 if c3 else 1, scope=a.scope, created_at=datetime.now(timezone.utc).isoformat(),
                  command="python src/freeze_evidence.py" + (f" --commands {a.commands}" if a.commands else "")
                  + (" --scope c3" if c3 else ""),
                  scope_runs=list(RUNS) + (list(C3_RUNS) if c3 else []),
                  excluded_runs=[] if c3 else ["r2c1", "r2d1", "wb1"],
                  excluded_paths=["paper/se4all/*", "paper/caleai/*"] if c3 else [],
                  previous_manifest="analysis/evidence_prev/EVIDENCE_MANIFEST_action2.json" if c3 else None,
                  provenance_note="null producing_command = historical command not recorded; source files are inputs",
                  files=records)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {a.out}: {len(records)} files")


if __name__ == "__main__":
    main()
