#!/bin/bash
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/judge.py --run frontier_whole_message_s2 --items annotation/written/hw_candidates.jsonl --concurrency 3 > runs/frontier_whole_message_s2/judge.log 2>&1
echo JUDGEDONE >> runs/frontier_whole_message_s2/judge.log
python src/frontier_whole_message_s2_m1jobs.py > runs/frontier_whole_message_s2/m1.log 2>&1
