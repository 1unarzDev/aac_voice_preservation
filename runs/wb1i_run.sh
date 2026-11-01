#!/usr/bin/env bash
# W-B interim (all base + terra restored; local restored pending GPU lock). All generations cached.
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/generate.py --requests runs/requests/wb1i.jsonl --run-id wb1i --local-concurrency 1 > runs/wb1i_gen.log 2>&1
python src/explode.py --run runs/wb1i && python src/explode.py --run runs/wb1i --by-input
python src/judge.py --run wb1i --items data/items/wb.jsonl --concurrency 8 > runs/wb1i_judge.log 2>&1
python src/attribute.py --run wb1i --items data/items/wb.jsonl --fallback J1 > runs/wb1i_attr.log 2>&1 && cp runs/wb1i/scored.parquet runs/wb1i/scored_fallbackJ1.parquet
python src/attribute.py --run wb1i --items data/items/wb.jsonl >> runs/wb1i_attr.log 2>&1
python src/wb_report.py wb1i > runs/wb1i_report.log 2>&1
echo WBIDONE >> runs/wb1i_attr.log
