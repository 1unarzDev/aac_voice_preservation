#!/usr/bin/env bash
# usage: frontier_multilingual_local.sh <gemma|nemo> <served-alias>; run under blocking flock by the caller
set -u
cd "$(dirname "$0")/.."
. .venv/bin/activate
PARALLEL=4 CTX_PER_SLOT=1024 src/serve_local.sh "$1" || { docker rm -f "aacv-$1" >/dev/null 2>&1; exit 1; }
python src/frontier_multilingual_gen.py "$2" 4
docker rm -f "aacv-$1" >/dev/null 2>&1
