#!/usr/bin/env bash
# usage: frontier_whole_message_r2_gpu.sh <stage: p18 | gens>   (holds the blocking GPU flock; one llama-server at a time)
set -u
cd ~/aac-voice-preservation
exec 9>/tmp/aacv_gpu.lock
flock 9
echo "lock acquired $(date -Is) stage=$1"
. .venv/bin/activate
if [ "$1" = "gens" ]; then
  bash src/stop_local.sh >/dev/null 2>&1
  PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh llama && python src/frontier_whole_message_r2_gen.py local llama3.1-8b 8092
  bash src/stop_local.sh >/dev/null 2>&1
fi
for k in qwen14:qwen2.5-14b:8094 nemo:mistral-nemo-12b:8095; do
  IFS=: read key alias port <<< "$k"
  bash src/stop_local.sh >/dev/null 2>&1
  PARALLEL=4 CTX_PER_SLOT=1536 bash src/serve_local.sh $key && python src/frontier_whole_message_r2_local.py $alias $port $([ "$1" = "p18" ] && echo p18 || echo gens)
  bash src/stop_local.sh >/dev/null 2>&1
done
echo "released $(date -Is)"
