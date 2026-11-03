#!/usr/bin/env bash
# Round-2 turn authoring under the blocking GPU lock: mistral-nemo (all 130 families), then qwen2.5-14b (40-family subset).
set -u
cd ~/aac-voice-preservation; . .venv/bin/activate
exec 9>/tmp/aacv_gpu.lock; flock 9
bash src/stop_local.sh >/dev/null 2>&1
PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh nemo || { echo "serve nemo failed"; exit 1; }
python src/frontier_partner_context_stage0b.py --author mistral-nemo-12b --out turns2.jsonl
bash src/stop_local.sh >/dev/null 2>&1
PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh qwen14 || { echo "serve qwen14 failed"; exit 1; }
python src/frontier_partner_context_stage0b.py --author qwen2.5-14b --out turns2_q14.jsonl --n-fam 40
bash src/stop_local.sh >/dev/null 2>&1
flock -u 9
echo STAGE0BDONE
