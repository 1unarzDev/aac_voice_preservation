#!/usr/bin/env bash
# GPU-safe intervention runner (D-008): one local server at a time (PARALLEL=4, CTX 1024),
# terra (API) alongside at concurrency 8. Then assemble + explode.
# usage: src/run_interventions.sh <base_run> <guard_run> <span_run> [models...]
set -u
base=$1; grun=$2; srun=$3; shift 3
models=${*:-qwen llama gemma}
declare -A MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
# per-model GPU layers from env, e.g. NGL_QWEN=14 (default 99 = all layers on GPU)
declare -A NGL_MAP=([qwen]=${NGL_QWEN:-99} [llama]=${NGL_LLAMA:-99} [gemma]=${NGL_GEMMA:-99})
cd ~/aac-voice-preservation; . .venv/bin/activate
( python src/interventions.py guard --base "$base" --run "$grun" --models gpt-6.1-terra --api-concurrency 8 &&
  python src/interventions.py span --base "$base" --run "$srun" --models gpt-6.1-terra --api-concurrency 8 ) > runs/${grun}_api.log 2>&1 &
apipid=$!
for m in $models; do
  bash src/stop_local.sh >/dev/null 2>&1
  ngl=${NGL_MAP[$m]:-99}; NGL=$ngl PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $m || { echo "serve $m failed"; continue; }
  python src/interventions.py guard --base "$base" --run "$grun" --models ${MID[$m]} --local-concurrency 4
  python src/interventions.py span --base "$base" --run "$srun" --models ${MID[$m]} --local-concurrency 4
  nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
done
bash src/stop_local.sh >/dev/null 2>&1
wait $apipid; cat runs/${grun}_api.log
for r in "$grun" "$srun"; do
  python src/interventions.py assemble --run "$r"
  python src/explode.py --run "runs/$r"; python src/explode.py --run "runs/$r" --by-input
done
echo INTDONE
