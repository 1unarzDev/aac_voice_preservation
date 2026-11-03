#!/usr/bin/env bash
# Runs Stage-1 signals for the three local models sequentially under a BLOCKING flock. Usage: setsid nohup src/frontier_value_of_cue_s1gpu.sh [limit] &
cd "$(dirname "$0")/.." && . .venv/bin/activate
LIM="${1:-}"
for pair in "qwen:qwen2.5-7b:8091" "llama:llama3.1-8b:8092" "gemma:gemma3-4b:8093"; do
  IFS=: read k alias port <<< "$pair"
  flock /tmp/aacv_gpu.lock bash -c "PARALLEL=8 CTX_PER_SLOT=1024 src/serve_local.sh $k && python src/frontier_value_of_cue_s1gpu.py $port $alias $LIM; docker rm -f aacv-$k >/dev/null 2>&1"
done
echo ALLDONE
