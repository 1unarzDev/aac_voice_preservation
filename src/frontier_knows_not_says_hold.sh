#!/usr/bin/env bash
# usage: hold.sh <model-key> <port-tag> <release-file> <max-seconds>
# Takes the GPU lock (BLOCKING), serves the model, then waits for the release file (or timeout), stops server, releases.
set -u
cd ~/aac-voice-preservation
M=$1; REL=$2; MAXS=${3:-5400}
echo "waiting for lock $(date -Is)"
exec 9>/tmp/aacv_gpu.lock
flock 9
echo "lock acquired $(date -Is)"
PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh $M || { echo serve failed; exit 1; }
rm -f "$REL"; t0=$(date +%s)
while [ ! -e "$REL" ] && [ $(( $(date +%s) - t0 )) -lt $MAXS ]; do sleep 10; done
docker rm -f aacv-$M >/dev/null 2>&1
echo "released $(date -Is)"
