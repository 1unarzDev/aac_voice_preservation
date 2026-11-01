#!/usr/bin/env bash
# GPU-safe runner: serve ONE local model at a time (PARALLEL=4), generate, stop, next.
# usage: src/run_sequential.sh <requests.jsonl> <run_id> [models...]   (default: qwen llama gemma; API runs alongside)
# Reason: 3 concurrent servers (15.2/16.4 GB VRAM) froze the machine on 2026-10-31 (D-008).
set -u
# D-019: global GPU lock so only one workstream serves a local model at a time
exec 9>/tmp/aacv_gpu.lock; flock 9
req=$1; run=$2; shift 2
models=${*:-qwen llama gemma}
declare -A MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/generate.py --requests "$req" --run-id "$run" --models gpt-6.1-terra --api-concurrency 16 > runs/${run}_api.log 2>&1 &
apipid=$!
for m in $models; do
  bash src/stop_local.sh >/dev/null 2>&1
  PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $m || { echo "serve $m failed"; continue; }
  python src/generate.py --requests "$req" --run-id "$run" --models ${MID[$m]} --local-concurrency 4
  nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
done
bash src/stop_local.sh >/dev/null 2>&1
flock -u 9  # D-028: release GPU lock before waiting on API
wait $apipid
python src/generate.py --requests "$req" --run-id "$run" --local-concurrency 1 >/dev/null 2>&1 || true  # assemble from cache (all cached)
python src/explode.py --run "runs/$run"; python src/explode.py --run "runs/$run" --by-input
echo SEQDONE
