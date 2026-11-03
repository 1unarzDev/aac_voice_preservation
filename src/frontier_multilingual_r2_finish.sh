#!/usr/bin/env bash
# Run after all local generations exist (runs/frontier_multilingual_r2/driver.done): label -> gate -> analyze -> naturalness -> tables. Idempotent (cached).
cd ~/aac-voice-preservation; . .venv/bin/activate; R=runs/frontier_multilingual_r2
while [ ! -f $R/driver.done ]; do sleep 60; done
python src/frontier_multilingual_r2_label.py > $R/label_final.log 2>&1
python src/frontier_multilingual_r2_gate.py > $R/gate_final.log 2>&1
python src/frontier_multilingual_r2_natural.py > $R/natural_final.log 2>&1
python src/frontier_multilingual_r2_analyze.py > $R/analyze_final.log 2>&1
python src/frontier_multilingual_r2_report.py >> $R/analyze_final.log 2>&1
echo FINISHED > $R/finish.done
