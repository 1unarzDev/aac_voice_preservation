# Part 28 stimuli notes (2026-11-17)

Built by src/make_listener_study.py (draw, guard, build) under analysis/listener/PLAN.md (sha256 221321be61bcdc92baa3843a7781f4b7d644685afaccfab4d12909c736bad8f7 at draw time).
Seed 20261117. 120 items: 30 per dimension (polarity, speech_act, agent, time_quantity), 15 default / 15 non-default intended each. Model per item: gemma3-4b 29, llama3.1-8b 31, qwen2.5-7b 29, gpt-6.1-terra 31.
Stimulus rows: bare 120, chip1 120, nlcue 102, G1 120, reference 120 = 582. Unique judge units (identical text within an item merged, reference never merged): 423.
Gaps: nlcue absent for the 18 items drawn from hw2 (runs/hw2 has no plain-word channel); nlcue contrasts restricted to the 102 hw1 items. No other gap.
Guard: G1 unchanged (src/interventions.guard_one, retries 2, temp 0, 96 tokens, seed 1000 local). 120/120 ran, 0 errors. The bare input supplies no cue, so only unsupplied politeness is checked: 16 of 120 first-pass outputs were flagged (politeness:added, all "Please ..."), 16 regenerated to unflagged text, 104 unchanged. Local models were run (qwen 3 calls, gemma 9 calls, terra 4 calls) under flock /tmp/aacv_gpu.lock, GPU idle; no fallback to terra-only was needed.
Context: item files have no context text; the topic label is the context line ("Topic: <topic>").
Private key (not in repo): orchestration/listener_key_private.json (gitignored).
