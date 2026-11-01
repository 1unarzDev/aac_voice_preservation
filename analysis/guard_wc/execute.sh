#!/usr/bin/env bash
set -euo pipefail
cd /home/lunarz/aac-voice-preservation
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1
PY=.venv/bin/python
finish() {
  wc_exit=$?
  "$PY" analysis/guard_wc/analyze.py --exit-code "$wc_exit" || true
  exit "$wc_exit"
}
trap finish EXIT
wc_remaining=$("$PY" -c 'import json,time; print(max(1,int(json.load(open("analysis/guard_wc/launch.json"))["deadline_epoch"]-time.time()-180)))')
timeout --signal=TERM --kill-after=5s "$wc_remaining" bash -c '
  set -e
  bash src/run_interventions.sh --guard-wc
  .venv/bin/python analysis/guard_wc/run.py judge
'
echo GUARD_WC_COMPLETE
