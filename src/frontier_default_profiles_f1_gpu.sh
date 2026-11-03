#!/usr/bin/env bash
# F1 GPU stage: ONE blocking flock hold; per model: serve, generate local requests, G1 on chip arm, CLAM probe; gemma = CLAM only.
cd ~/aac-voice-preservation; . .venv/bin/activate
exec 9>/tmp/aacv_gpu.lock
echo "waiting for lock $(date -Is)"; flock 9; echo "lock acquired $(date -Is)"
declare -A PORT=([qwen]=8091 [llama]=8092 [gemma]=8093); declare -A AL=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
for k in qwen llama gemma; do
  docker rm -f aacv-$k >/dev/null 2>&1
  PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $k || { echo "serve $k failed"; continue; }
  if [ $k != gemma ]; then
    python src/generate.py --requests runs/frontier_default_profiles_f1_req/f1.jsonl --run-id frontier_default_profiles_f1 --models ${AL[$k]} --local-concurrency 4
    python src/frontier_default_profiles_f1_guard.py --models ${AL[$k]}
  fi
  python src/frontier_default_profiles_f1_clam.py --model ${AL[$k]} --port ${PORT[$k]} --workers 4
  docker rm -f aacv-$k >/dev/null 2>&1
done
echo "released $(date -Is)"; echo GPUDONE
