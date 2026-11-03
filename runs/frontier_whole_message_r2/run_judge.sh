#!/bin/bash
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/judge.py --run frontier_whole_message_r2 --items annotation/written/hw_candidates.jsonl --concurrency 3 >> runs/frontier_whole_message_r2/judge.log 2>&1
echo JUDGEDONE >> runs/frontier_whole_message_r2/judge.log
