#!/usr/bin/env bash
# Holds the GPU lock, serves qwen, runs the given python script, stops the server.
set -u
cd ~/aac-voice-preservation
exec 9>/tmp/aacv_gpu.lock
flock 9
echo "lock acquired $(date -Is)"
PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh qwen || { echo serve failed; exit 1; }
. .venv/bin/activate
python "$@"; rc=$?
docker rm -f aacv-qwen >/dev/null 2>&1
echo "released $(date -Is) rc=$rc"
