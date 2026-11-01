#!/usr/bin/env bash
# W-B generation: API (terra, conc 8) + local models one at a time under the global GPU lock (D-008/D-019)
set -u
req=$1; run=wb1
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/generate.py --requests "$req" --run-id $run --models gpt-6.1-terra --api-concurrency 8 > runs/${run}_api.log 2>&1 &
apipid=$!
flock /tmp/aacv_gpu.lock bash -c '
  cd ~/aac-voice-preservation; . .venv/bin/activate
  declare -A MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
  for m in qwen llama gemma; do
    bash src/stop_local.sh >/dev/null 2>&1
    PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $m || { echo "serve $m failed"; continue; }
    python src/generate.py --requests '"$req"' --run-id wb1 --models ${MID[$m]} --local-concurrency 4
    nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
  done
  bash src/stop_local.sh >/dev/null 2>&1'
wait $apipid
echo GENDONE
