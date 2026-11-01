#!/usr/bin/env bash
# Stop and remove all aacv-* llama.cpp server containers.
set -euo pipefail
ids=$(docker ps -aq -f name=aacv-)
[[ -n "$ids" ]] && docker rm -f $ids >/dev/null && echo "stopped: $(echo $ids | wc -w) container(s)" || echo "nothing running"
