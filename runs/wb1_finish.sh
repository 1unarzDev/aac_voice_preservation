#!/usr/bin/env bash
# W-B downstream after generation: assemble, explode, judge (conc 8), attribute (fallback copy + primary), report
cd ~/aac-voice-preservation; . .venv/bin/activate
until grep -q GENDONE runs/wb1_seq2.log; do sleep 20; done
python src/generate.py --requests runs/requests/wb1.jsonl --run-id wb1 --local-concurrency 1 > runs/wb1_assemble.log 2>&1
python src/explode.py --run runs/wb1 && python src/explode.py --run runs/wb1 --by-input
python src/judge.py --run wb1 --items data/items/wb.jsonl --concurrency 8 > runs/wb1_judge.log 2>&1
python src/attribute.py --run wb1 --items data/items/wb.jsonl --fallback J1 > runs/wb1_attr.log 2>&1 && cp runs/wb1/scored.parquet runs/wb1/scored_fallbackJ1.parquet
python src/attribute.py --run wb1 --items data/items/wb.jsonl >> runs/wb1_attr.log 2>&1
python src/wb_report.py > runs/wb1_report.log 2>&1
echo WBFINISHED >> runs/wb1_attr.log
