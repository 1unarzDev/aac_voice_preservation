#!/usr/bin/env bash
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/generate.py --requests runs/frontier_partner_context_req/r2_terra_core.jsonl --run-id frontier_partner_context_r2_terra_core --models gpt-6.1-terra --api-concurrency 4 > runs/frontier_partner_context_r2_terra_core.log 2>&1
echo COREDONE
python src/generate.py --requests runs/frontier_partner_context_req/r2_terra_cb.jsonl --run-id frontier_partner_context_r2_terra_cb --models gpt-6.1-terra --api-concurrency 4 > runs/frontier_partner_context_r2_terra_cb.log 2>&1
echo CBDONE
