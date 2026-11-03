#!/usr/bin/env bash
cd ~/aac-voice-preservation; . .venv/bin/activate
python src/judge.py --run frontier_default_profiles_f1all --items analysis/frontier/default_profiles/followup/items_f1.jsonl --concurrency 3 > runs/frontier_default_profiles_f1_judge.log 2>&1
python src/judge.py --run frontier_default_profiles_f1g --items analysis/frontier/default_profiles/followup/items_f1.jsonl --concurrency 3 > runs/frontier_default_profiles_f1g_judge.log 2>&1
echo JUDGEDONE >> runs/frontier_default_profiles_f1g_judge.log
