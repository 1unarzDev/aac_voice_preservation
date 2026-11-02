#!/usr/bin/env bash
# E1 (legend test) then E2 (chip controls) generation, sequential so API concurrency stays <=12 and the GPU lock is taken once per run.
cd ~/aac-voice-preservation
src/run_sequential.sh runs/requests/legend1.jsonl legend1 > runs/legend1_seq.log 2>&1
src/run_sequential.sh runs/requests/hwctl.jsonl hwctl1 > runs/hwctl1_seq.log 2>&1
echo CHAINDONE > runs/chip_chain.done
