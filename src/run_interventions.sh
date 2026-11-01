#!/usr/bin/env bash
# GPU-safe intervention runner (global GPU lock): one local server at a time (PARALLEL=4,
# CTX 1024), terra (API) alongside at concurrency 8 (<= 8). Then assemble + explode.
# usage: src/run_interventions.sh <base_run> <guard_run> <span_run> [models...]
set -u
# Guard-transfer adapter: unchanged G1/G1s policy, frozen W-C inventory, no I2 calls.
# The legacy discovery runner below remains the default entry point.
if [[ "${1:-}" == "--guard-wc" ]]; then
  cd ~/aac-voice-preservation || exit 1
  . .venv/bin/activate
  python analysis/guard_wc/run.py verify || exit 1
  exec 9>/tmp/aacv_gpu.lock; flock 9
  # The lock wait is included in the experiment's four-hour deadline.
  cleanup_guard_wc() {
    bash src/stop_local.sh >/dev/null 2>&1
    if [[ -n "${wc_api_pid:-}" ]]; then kill "$wc_api_pid" 2>/dev/null || true; fi
  }
  trap cleanup_guard_wc EXIT
  trap 'exit 143' TERM INT
  python -u analysis/guard_wc/run.py guard --model gpt-6.1-terra > analysis/guard_wc/api.log 2>&1 &
  wc_api_pid=$!
  declare -A WC_MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
  for wc_model in qwen llama gemma; do
    bash src/stop_local.sh >/dev/null 2>&1
    NGL=99 PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh "$wc_model" || exit 1
    python -u analysis/guard_wc/run.py guard --model "${WC_MID[$wc_model]}" || exit 1
    nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
  done
  bash src/stop_local.sh >/dev/null 2>&1
  flock -u 9
  wait "$wc_api_pid" || exit 1
  wc_api_pid=""
  python -u analysis/guard_wc/run.py assemble || exit 1
  echo GUARD_WC_GENERATION_DONE
  exit 0
fi
# Global GPU lock so only one workstream serves a local model at a time
exec 9>/tmp/aacv_gpu.lock; flock 9
base=$1; grun=$2; srun=$3; shift 3
models=${*:-qwen llama gemma}
declare -A MID=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)
# per-model GPU layers from env, e.g. NGL_QWEN=14 (default 99 = all layers on GPU)
declare -A NGL_MAP=([qwen]=${NGL_QWEN:-99} [llama]=${NGL_LLAMA:-99} [gemma]=${NGL_GEMMA:-99})
cd ~/aac-voice-preservation; . .venv/bin/activate
trap "bash src/stop_local.sh >/dev/null 2>&1" EXIT   # never leave a server up after the lock is released
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
