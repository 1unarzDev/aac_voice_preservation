#!/usr/bin/env bash
# waits for stage0b, then build -> generate (GPU lock inside run_sequential.sh, terra at API_CONC=4) -> judge polarity (concurrency 3)
set -u
cd ~/aac-voice-preservation; . .venv/bin/activate
until grep -q STAGE0BDONE runs/frontier_partner_context_stage0b.log 2>/dev/null; do sleep 20; done
python src/frontier_partner_context_build2.py > runs/frontier_partner_context_build2.log 2>&1 || { echo BUILDFAIL; exit 1; }
API_CONC=4 bash src/run_sequential.sh runs/frontier_partner_context_req/r2.jsonl frontier_partner_context_r2 qwen llama gemma
python src/judge.py --run frontier_partner_context_r2 --items analysis/frontier/partner_context/items_r2.jsonl --concurrency 3 > runs/frontier_partner_context_r2_judge.log 2>&1
echo CHAIN2DONE
