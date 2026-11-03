#!/usr/bin/env bash
# F2 GPU stage: ONE blocking flock hold. per model: serve (PARALLEL=8), K=256 sampling, verbalised baseline.
cd ~/aac-voice-preservation; . .venv/bin/activate
exec 9>/tmp/aacv_gpu.lock
echo "waiting for lock $(date -Is)"; flock 9; echo "lock acquired $(date -Is)"
declare -A PORT=([qwen]=8091 [llama]=8092); declare -A AL=([qwen]=qwen2.5-7b [llama]=llama3.1-8b)
for k in qwen llama; do
  docker rm -f aacv-$k >/dev/null 2>&1
  PARALLEL=8 CTX_PER_SLOT=1024 bash src/serve_local.sh $k || { echo "serve $k failed"; continue; }
  python src/frontier_knows_not_says_f2_k256.py verbal ${PORT[$k]} ${AL[$k]}
  python src/frontier_knows_not_says_f2_k256.py k256 ${PORT[$k]} ${AL[$k]}
  docker rm -f aacv-$k >/dev/null 2>&1
done
echo "released $(date -Is)"; echo GPUDONE
