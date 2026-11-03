# GPU pause (2026-11-02 20:25 CST)

Owner chose to give the GPU to the crane D-15 Unity video first. Your queued GPU runs are SIGSTOPped
(process groups in /home/lunarz/.cache/aac-paused-pids.txt: whole_message_r2 gens 1471532, default_profiles_probe
1108235 (next: qwen14), value_of_cue_s1gpu 1229407 (gemma), /tmp/aacv_ml_r2_driver.sh 1263175 (gemma multilingual_r2_gen)).
Nothing was interrupted: the lock holder at the time, run_sequential.sh for frontier_partner_context_r2 (chain2, pgid 1262069),
was left to finish its llama and gemma passes; the chain then continues with judge.py (API only).
They resume automatically (SIGCONT) when D-15 is done: the systemd --user unit aac-gpu-resume
(log ~/.cache/aac-gpu-resume.log; at most 8 h). Please don't start new /tmp/aacv_gpu.lock jobs until then.
Manual resume: `grep -v '^#' ~/.cache/aac-paused-pids.txt | cut -f1 | xargs -I{} kill -CONT -- -{}`
