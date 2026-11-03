#!/usr/bin/env bash
# E0 generation: terra via API (conc 4) alongside qwen2.5-7b under a BLOCKING GPU lock.
set -u
cd ~/aac-voice-preservation; . .venv/bin/activate
req=runs/frontier_partner_context_req/e0.jsonl; run=frontier_partner_context_e0
python src/generate.py --requests $req --run-id ${run}_api --models gpt-6.1-terra --api-concurrency 4 > runs/${run}_api.log 2>&1 &
apipid=$!
exec 9>/tmp/aacv_gpu.lock; flock 9
bash src/stop_local.sh >/dev/null 2>&1
PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh qwen || { echo "serve failed"; exit 1; }
python src/generate.py --requests $req --run-id ${run}_qwen --models qwen2.5-7b --local-concurrency 4
bash src/stop_local.sh >/dev/null 2>&1
flock -u 9
wait $apipid
python src/generate.py --requests $req --run-id $run --local-concurrency 1 --no-network >/dev/null 2>&1
python src/explode.py --run runs/$run; python src/explode.py --run runs/$run --by-input
echo GENDONE
