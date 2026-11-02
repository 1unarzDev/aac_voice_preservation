#!/usr/bin/env bash
# G1r/G1t generation. usage: src/run_guard_baseline.sh api | local
# api  : terra only, concurrency 4, no GPU.
# local: waits for legend1 SEQDONE, then one llama.cpp server at a time under the global GPU lock.
set -u
cd ~/aac-voice-preservation || exit 1; . .venv/bin/activate
if [[ "${1:-}" == "api" ]]; then
  for s in disc wc; do python -u src/guard_baseline.py gen --set $s --model gpt-6.1-terra --concurrency 4 || exit 1; done
  echo GBAPIDONE; exit 0
fi
until grep -q SEQDONE runs/legend1_seq.log && ! pgrep -f "generate.py.*legend1" >/dev/null; do sleep 60; done
exec 9>/tmp/aacv_gpu.lock; flock 9
trap "bash src/stop_local.sh >/dev/null 2>&1" EXIT
declare -A MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
for m in qwen llama gemma; do
  bash src/stop_local.sh >/dev/null 2>&1
  NGL=99 PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $m || { echo "serve $m failed"; exit 1; }
  for s in disc wc; do python -u src/guard_baseline.py gen --set $s --model ${MID[$m]} --concurrency 4 || exit 1; done
done
bash src/stop_local.sh >/dev/null 2>&1
echo GBLOCALDONE
