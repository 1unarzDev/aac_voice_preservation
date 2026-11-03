#!/usr/bin/env bash
# G1 local models under the blocking GPU lock (reads outputs from runs/cache), terra afterwards via API
set -u
cd ~/aac-voice-preservation; . .venv/bin/activate
until grep -q "requests in" runs/frontier_partner_context_chain2.log 2>/dev/null && [ $(grep -c "requests in" runs/frontier_partner_context_chain2.log) -ge 3 ]; do sleep 20; done
exec 9>/tmp/aacv_gpu.lock; flock 9
bash src/stop_local.sh >/dev/null 2>&1
declare -A K=([qwen2.5-7b]=qwen [llama3.1-8b]=llama [gemma3-4b]=gemma)
for m in qwen2.5-7b llama3.1-8b gemma3-4b; do
  PARALLEL=4 CTX_PER_SLOT=1024 bash src/serve_local.sh ${K[$m]} || continue
  python src/frontier_partner_context_guard.py --models $m
  bash src/stop_local.sh >/dev/null 2>&1
done
flock -u 9
echo GUARDLOCALDONE
