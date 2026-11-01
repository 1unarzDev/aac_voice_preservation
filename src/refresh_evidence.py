"""Offline ACTION 2 refresh. Launch with setsid nohup; no model/server calls.

Use --stage labels first, then --stage reports after reviewing reconciliation.
Every subprocess and its produced artifacts are recorded in refresh_commands.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from freeze_evidence import ROOT, inventory
from resolve_labels import DEFAULT_RUNS

REGISTRY = ROOT / "analysis/refresh_commands.json"


def execute(args):
    before = {str(p.relative_to(ROOT)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in inventory()}
    command = [str(ROOT / ".venv/bin/python"), *args]
    print("RUN " + shlex.join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    registry = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}
    for p in inventory():
        key = str(p.relative_to(ROOT))
        if (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) != before.get(key):
            registry[key] = shlex.join(command)
    REGISTRY.write_text(json.dumps(registry, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=["labels", "reports", "finalize", "freeze"], required=True)
    a = ap.parse_args()
    if a.stage == "labels":
        execute(["src/resolve_labels.py"])
        for run in DEFAULT_RUNS:
            directory = ROOT / "runs" / run
            scored = directory / "scored.parquet"
            previous = directory / "scored_prev.parquet"
            if scored.exists() and not previous.exists():
                frozen = ROOT / "analysis/evidence_prev/runs" / run / "scored.parquet"
                if not frozen.exists() or frozen.read_bytes() != scored.read_bytes():
                    raise RuntimeError(f"Unexpected pre-refresh scored table: {run}")
                shutil.copy2(scored, previous)
            execute(["src/attribute.py", "--run", run, "--resolution", "annotation/label_resolution.jsonl"])
    elif a.stage == "reports":
        execute(["src/analyze.py", "--table", "runs/main1/scored.parquet", "--tag", "main1"])
        execute(["src/analyze.py", "--table", "runs/main1/scored.parquet", "--tag", "main1_quarantine_inclusive", "--include-quarantine"])
        execute(["src/interventions.py", "report", "--guard", "guard1", "--span", "span1",
                 "--out", "analysis/interventions/report.md", "--title", "Interventions (refreshed ACTION 2)"])
        execute(["src/oracle_report.py"])
        execute(["paper/figs/make_figs.py"])
        execute(["paper/figs/make_figs.py", "--include-quarantine", "--out", "paper/figs/quarantine_inclusive"])
        execute(["paper/se4all/make_macros.py"])
    elif a.stage == "finalize":
        execute(["src/reconcile_evidence.py", "--endpoints-only"])
        execute(["src/interventions.py", "report", "--guard", "guard1", "--span", "span1",
                 "--out", "analysis/interventions/report.md", "--title", "Interventions (refreshed ACTION 2)"])
        execute(["paper/figs/make_figs.py"])
        execute(["paper/figs/make_figs.py", "--include-quarantine", "--out", "paper/figs/quarantine_inclusive"])
        execute(["paper/se4all/make_macros.py"])
        execute(["src/refresh_captions.py"])
        execute(["src/reconcile_evidence.py"])
    else:
        execute(["src/verify_reconciliation.py"])
        registry = json.loads(REGISTRY.read_text())
        # These commands actually ran in labels/reports/finalize, including
        # outputs whose bytes did not change. Preserve that provenance too.
        for run in DEFAULT_RUNS:
            registry[f"runs/{run}/scored.parquet"] = shlex.join(
                [str(ROOT / '.venv/bin/python'), 'src/attribute.py', '--run', run,
                 '--resolution', 'annotation/label_resolution.jsonl'])
            registry[f"runs/{run}/endpoints.json"] = shlex.join(
                [str(ROOT / '.venv/bin/python'), 'src/reconcile_evidence.py', '--endpoints-only'])
            if (ROOT / f"runs/{run}/scored_prev.parquet").exists():
                registry[f"runs/{run}/scored_prev.parquet"] = (
                    f"{ROOT}/.venv/bin/python src/refresh_evidence.py --stage labels (shutil.copy2; pre-refresh backup)")
        for tag, inclusive in [('main1',False),('main1_quarantine_inclusive',True)]:
            command = shlex.join([str(ROOT / '.venv/bin/python'), 'src/analyze.py', '--table',
                                  'runs/main1/scored.parquet','--tag',tag] + (['--include-quarantine'] if inclusive else []))
            for p in (ROOT / 'analysis' / tag).rglob('*'):
                if p.is_file():
                    registry[str(p.relative_to(ROOT))] = command
        REGISTRY.write_text(json.dumps(registry, indent=2) + '\n')
        subprocess.run([str(ROOT / '.venv/bin/python'), 'src/freeze_evidence.py',
                        '--commands', 'analysis/refresh_commands.json'], cwd=ROOT, check=True)
        manifest = json.loads((ROOT / 'analysis/EVIDENCE_MANIFEST.json').read_text())
        for entry in manifest['files']:
            p = ROOT / entry['path']
            assert hashlib.sha256(p.read_bytes()).hexdigest() == entry['sha256'], entry['path']
            assert p.stat().st_mtime_ns == entry['mtime_ns'], entry['path']
            assert not any(entry['path'].startswith(f'runs/{run}/') for run in ['r2c1','r2d1','wb1'])
        print(f"verified frozen hashes and mtimes: {len(manifest['files'])} files", flush=True)
    print("DONE " + a.stage, flush=True)


if __name__ == "__main__":
    main()
