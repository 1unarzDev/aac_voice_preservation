"""Hash the ACTION 2 evidence inventory; never inspect in-progress R2/W-B runs.

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


def inventory():
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
    return sorted(paths)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/EVIDENCE_MANIFEST.json")
    ap.add_argument("--commands", type=Path)
    ap.add_argument("--snapshot", type=Path)
    a = ap.parse_args()
    commands = json.loads(a.commands.read_text()) if a.commands else {}
    records = []
    for p in inventory():
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
    result = dict(schema_version=1, created_at=datetime.now(timezone.utc).isoformat(),
                  command="python src/freeze_evidence.py" + (f" --commands {a.commands}" if a.commands else ""),
                  scope_runs=list(RUNS), excluded_runs=["r2c1", "r2d1", "wb1"],
                  provenance_note="null producing_command = historical command not recorded; source files are inputs",
                  files=records)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {a.out}: {len(records)} files")


if __name__ == "__main__":
    main()
