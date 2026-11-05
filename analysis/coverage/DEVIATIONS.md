# Intent-coverage pilot: deviations log (written 2026-11-05 by the orchestrator; source: critique1.md)

Status of the machine round: **DRY RUN / debugging, not a pre-specified result.** No machine-round number leaves this folder as a claim. The human Stage 6 task carries the confirmatory questions S1 to S4 (PLAN section 3).

1. **Plan timing.** PLAN.md mtime is 2026-11-04 23:07:21; the first generation is 23:13 (runs/coverage_*, analysis/coverage/drafts_*). The plan was therefore written before generation and has not been modified since, but the only evidence is the filesystem mtime. The first commit (247c2fd, 2026-11-05 05:17) and any hash deposit post-date generation. Stage 6 keys and rules are hash-deposited before any human return (protocol-hash-2026-11-05e).
2. **Model substitution.** gpt-6.1-terra (generation) and gpt-6.1-sol (judge) returned 503. Generation used gpt-5.6-terra and the proxy judge used gpt-6-luna (models_used.json). This changes the system under test relative to the main study.
3. **Not run:** the independent-family judges (Qwen and Mistral on the terra drafts), and the proxy judging of local-model drafts (429 rate limits; src/coverage_local_eval.py is resumable). S7 (arm ordering on local models) is unevaluated.
4. **Code edited after the freeze.** src/coverage_*.py and the prompts were edited during the run and were untracked at run time.
5. **Judge output schema** differs from PLAN section 3.
6. **The proxy failed its validity gate** on criterion (c): the AUROC gain over word count is .120 with CI [-.015, .258]. Per PLAN section 3, all machine numbers are descriptive only.
7. **round1.md breaks plan rules:** it recommends dropping E3 from the human arms (a machine-only report may not change them; the plan stands), reports arm-level p-values after a failed gate, and picks the S1 arm on the main 200 items (the plan says on reserve items). These readings are withdrawn. Stage 6 uses the arms exactly as PLAN.md specifies.
