#!/usr/bin/env bash
# Serve the three local GGUFs concurrently with llama.cpp server (docker, CUDA).
#
#   src/serve_local.sh            # start all three (default)
#   src/serve_local.sh qwen       # start only one (qwen | llama | gemma), e.g. for sequential mode
#
# Ports: qwen2.5-7b 8091, llama3.1-8b 8092, gemma3-4b 8093. Containers: aacv-<name>.
# Each server: --parallel 8 slots, CTX_PER_SLOT tokens per slot (total ctx = 8*CTX_PER_SLOT),
# all layers on GPU, q8_0 KV cache + flash attention to make all three fit in 16 GB.
# Stop with src/stop_local.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS="$ROOT/models"
IMAGE="ghcr.io/ggml-org/llama.cpp:server-cuda"
PARALLEL="${PARALLEL:-8}"
CTX_PER_SLOT="${CTX_PER_SLOT:-1536}"

declare -A FILE=(
  [qwen]="Qwen2.5-7B-Instruct-Q4_K_M.gguf"
  [llama]="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
  [gemma]="google_gemma-3-4b-it-Q4_K_M.gguf"
)
declare -A SIZE=([qwen]=4683074240 [llama]=4920739232 [gemma]=2489758112)
declare -A PORT=([qwen]=8091 [llama]=8092 [gemma]=8093)
declare -A ALIAS=([qwen]=qwen2.5-7b [llama]=llama3.1-8b [gemma]=gemma3-4b)

wait_for_downloads() {
  # Ready when SHA256SUMS exists, or every file has reached its expected size.
  while true; do
    [[ -s "$MODELS/SHA256SUMS" ]] && return 0
    local ok=1
    for k in qwen llama gemma; do
      local f="$MODELS/${FILE[$k]}"
      [[ -f "$f" && "$(stat -c %s "$f")" == "${SIZE[$k]}" ]] || ok=0
    done
    [[ $ok == 1 ]] && return 0
    echo "waiting for model downloads..." >&2; sleep 15
  done
}

start_one() {
  local k="$1" name="aacv-$1"
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" --gpus all \
    -v "$MODELS:/models:ro" -p "${PORT[$k]}:8080" \
    "$IMAGE" \
    -m "/models/${FILE[$k]}" --alias "${ALIAS[$k]}" \
    --host 0.0.0.0 --port 8080 \
    -ngl 99 --jinja --parallel "$PARALLEL" -c $((PARALLEL * CTX_PER_SLOT)) \
    -fa on -ctk q8_0 -ctv q8_0 --no-warmup >/dev/null
  # wait for /health == ok
  for _ in $(seq 1 120); do
    if curl -sf "http://127.0.0.1:${PORT[$k]}/health" | grep -q '"ok"'; then
      echo "$name ready on :${PORT[$k]}"; return 0
    fi
    if ! docker ps -q -f "name=^${name}$" | grep -q .; then
      echo "$name exited:" >&2; docker logs --tail 30 "$name" >&2; return 1
    fi
    sleep 2
  done
  echo "$name did not become healthy" >&2; return 1
}

wait_for_downloads
targets=("${@:-qwen llama gemma}")
# shellcheck disable=SC2206
targets=(${targets[*]})
for k in "${targets[@]}"; do start_one "$k"; done
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
