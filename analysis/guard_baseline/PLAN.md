# Resample-without-feedback baseline for the commitment guard (G1r) -- PLAN

Written 2026-11-01, before any G1r/G1t generation or judge call. Nothing in `src/interventions.py`, the frozen G1/G1s
outputs, the frozen W-C inventory or any paper is changed.

## Question
Reviewers: the only comparator to G1 is strip-only G1s. Does the *feedback text* help, or does *trying again* help?

## Arms (all share the unchanged monitor `supplied()` / `check()`, trigger, retry budget and selection rule)
- **G1** (existing, T=0, feedback turn "Your sentence must keep: ..."), **G1s** (existing strip-only), **P0** (existing first pass).
- **G1r (new)**: same trigger (the first pass is flagged by the monitor). Retry = the *original single-turn prompt*,
  **no feedback text, no conversation history**, up to 2 retries, return the first unflagged candidate else fewest flags,
  earliest on ties (original wins ties) -- exactly G1's return rule.
- **G1t (new, matched)**: G1's conversation and feedback text exactly, but with G1r's retry decoding. It isolates the feedback effect.

## Decoding of the retry (the one deliberate change)
G1 retried at **T=0** (96 tokens, local seed 1000, the feedback turn appended to the conversation). A T=0 retry of the
original prompt without feedback is the identical request, so it would only reproduce the first pass (local models
are deterministic at T=0; the cache key would be identical). The minimal change that yields a fresh sample is **temperature 0.7**
(the repo's existing S3 sampling temperature), 96 tokens, **local seed 3000+k for retry k** (k=1,2; distinct per retry and from
the S3 seeds 1000-1002; the API ignores seed and relies on T>0). Retries are distinct cache entries (tag `G1r-v1-a<k>` / `G1t-v1-a<k>`).
Consequence: G1 vs G1r differs in feedback AND temperature. The clean feedback contrast is **G1t - G1r** (identical decoding,
only the feedback differs). Both are reported; G1 - G1r is the contrast the reviewers asked for and is labelled
as decoding-confounded; G1t - G1r is the isolating one. G1 - G1t is the pure temperature effect on the guard.

## Inputs (exactly where G1 fired, both sets, same models, same max retries = 2)
Unique stored first-pass requests whose monitor replay flags the output (non-empty `flags_initial`, non-empty text).
- Discovery set `runs/guard1`: 170 flagged unique requests (gemma3-4b 69, llama3.1-8b 46, qwen2.5-7b 28, gpt-6.1-terra 27); G1 used 215 calls.
- W-C transfer `runs/guard_wc` (78 families, `analysis/guard_wc/items.jsonl`): 508 flagged (gemma 177, llama 185, qwen 84, terra 62); G1 used 766 calls.
Unflagged inputs receive no retry in any arm, so every arm equals P0 there; all target occurrences stay in the denominators.
Upper bound on new generation calls: 2 arms x 2 retries x 678 = 2,712 (terra 356); actual is lower because retries stop at the first unflagged output.

## Endpoints (reuse the guard analysis; `analysis/guard_wc/analyze.py` metric/pair_metrics, 10,000 whole-family percentile bootstrap, seed 20261101)
Cue channels (chip1/chipall/full): joint supplied-predicate pass (primary), strict pass (also no added politeness), repair of
initial strict failures (and conservative lower bound), changed-correct, **pass->fail**, **residual failures**; plus unflagged-after,
calls and the ambiguous-channel politeness rate (secondary). Discovery excludes the D-024 quarantined families (act-10/act-16) as in the
guard analysis; the W-C set already excludes r2act-078/079. Paired on identical targets; every arm/model/channel of a sampled family
resamples jointly (the 55 W-C construction-cluster companion is also in summary.json for wc).
**Primary contrast: G1 - G1r (joint-pass gain, pp).** Isolating contrast: G1t - G1r. Secondary: G1 - G1s, G1r - G1s.
Decision rule written now: "feedback adds value beyond resampling" only if G1t - G1r joint gain has a lower 95% bound > 0 on a set;
if the interval contains 0 it is reported as not distinguishable. No arm or decoding is tuned after seeing outcomes.

## Evaluation
New output texts (changed from the original) go through `src/judge.py --concurrency 8` (gpt-6.1-sol, J1/J2); cached judgments
are reused. P0, G1, G1s labels are the existing ones (unchanged outputs inherit baseline labels). Critical J1/J2 disagreements:
reuse existing resolutions (annotation/label_resolution.jsonl; W-C frozen r2c1 arbiter, same A-unit); otherwise a **blind arbiter**
from output text + production critical question/options only (procedure of runs/hw1/arbiter.jsonl; no input, arm, model, channel, J1/J2 shown).
Attribution never falls back to J1/J2; unresolved stays unknown (`attribute.score` with run arbiter.jsonl).

## Scheduling and resources
- API (gpt-6.1-terra) part may run now at concurrency <=4. Local models only after `runs/legend1_seq.log` shows SEQDONE and no legend1
  `generate.py` is running; one llama.cpp server at a time under `flock /tmp/aacv_gpu.lock`, 4 slots, CTX 1024, NGL 99 (src/run_guard_baseline.sh).
  The robotics Unity job also uses the lock; we wait.
- Judge concurrency 8. Launch long jobs with `setsid nohup`; never `pkill -f`.
- Caveat to disclose: the flagged set is chosen by G1's first-pass trigger, selected on the same data as in the original analyses; the sets are
  small (170/508 flagged requests), and API runs are not reproducible at T=0 either. No human validation of repaired text is created;
  machine-scored partial predicates only.
