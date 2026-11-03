#!/usr/bin/env bash
# Round-3 finaliser: after the queued local generations (driver.done), the nemo round-3 pass (nemo_r3.done) and the round-2 finish script (finish.done) exist,
# relabel (cached), re-run the control gate and the round-3 analysis. No GPU use. Writes runs/frontier_multilingual_r2/r3_final.done
cd ~/aac-voice-preservation; . .venv/bin/activate; R=runs/frontier_multilingual_r2
while [ ! -f $R/driver.done ] || [ ! -f $R/nemo_r3.done ] || [ ! -f $R/finish.done ]; do sleep 120; done
python src/frontier_multilingual_r2_label.py > $R/label_r3_final.log 2>&1
python src/frontier_multilingual_r2_gate.py > $R/gate_r3_final.log 2>&1
python src/frontier_multilingual_r3_analyze.py > $R/r3_analyze_final.log 2>&1
echo FINAL > $R/r3_final.done
