#!/usr/bin/env bash
# Model-breadth extension: serve ONE larger local model under the GPU lock, generate its re-targeted requests, stop.
# usage: src/run_ext_local.sh <qwen14|nemo>   (requests: runs/requests/ext_<model>_{hw,legend1,hwctl}.jsonl -> runs/{hw1,legend1,hwctl1}_<k>)
set -u
exec 9>/tmp/aacv_gpu.lock; flock 9
k=$1; declare -A MID=([qwen14]=qwen2.5-14b [nemo]=mistral-nemo-12b)
m=${MID[$k]}; cd ~/aac-voice-preservation; . .venv/bin/activate
bash src/stop_local.sh >/dev/null 2>&1
PARALLEL=${PARALLEL:-4} CTX_PER_SLOT=1024 bash src/serve_local.sh $k || { echo "serve $k failed"; exit 1; }
sleep 20; nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
for set in hw legend1 hwctl; do
  python src/generate.py --requests runs/requests/ext_${m}_${set}.jsonl --run-id ext_${set}_${k} --models $m --local-concurrency ${PARALLEL:-4}
  nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
  python src/explode.py --run runs/ext_${set}_${k}; python src/explode.py --run runs/ext_${set}_${k} --by-input
done
bash src/stop_local.sh >/dev/null 2>&1
echo EXTDONE $k
