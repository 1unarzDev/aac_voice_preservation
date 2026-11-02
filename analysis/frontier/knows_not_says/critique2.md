# critique2 (adversarial: methods/statistics + novelty), knows_not_says, round 2

## What exists (checked 2026-11-02 ~17:00)
- Stage 0 pilot: done (pilot_notes.md, pilot_mechanics.json). round2.md does NOT exist.
- Stage 1 qwen2.5-7b: still generating (qwen.log: 12,000/26,469 requests, 0 errors; gens.jsonl 13.1k lines incl. resume). llama3.1-8b not started. src/frontier_knows_not_says_analyze.py has never been run: no analysis/frontier/knows_not_says/stage1/ directory, no r1/r2/pol CSVs, no summary.json. pairs_raw.json (pair-scoring arm) not run for any Stage 1 run.
- Unit tests (src/frontier_knows_not_says_test.py): 7/7 pass (I re-ran them). They test the library on synthetic data, not analyze.py (untested end to end; it asserts full coverage of inputs, so it cannot be smoke-tested on partial data).
- So there are no R1/R2/R3 results to validate, again. Only mechanics are verifiable.

## Fatal
1. No Stage 1 outcome evidence and no round2.md: nothing reportable as "recovers / calibrated / knows". Any statement of results today would be unsupported. (Not a refutation of the design.)

## Major
1. A10 re-defines a failed Stage 0 criterion after seeing the failure (A1c, 68% vs required 95%). It is disclosed and pre-Stage-1, but the replacement is tuned to pass with zero margin: forced 68% vs repeat 78%, threshold "no more than 10 points below" (it is 10). The comparison is also apples to oranges: 78% = 36/46 conditional on identical text; over all 50 sequences the repeat rate is 36/50 = 72%, and without prompt cache 29/46 = 63%. Treat the forced scorer as "noisy, not validated". Pair-scoring conclusions need the noise floor as an explicit tolerance, and top-1000 imputation (an upper bound on the rare negated-token logprob) biases log-odds toward 0, i.e. toward a spurious "indifferent" reading.
2. Detector asymmetry in R1. Numerator = layer0 detector on MODEL OUTPUTS; target = layer0 detector on HUMAN SOURCE sentences. A shared detector does not cancel differing sensitivity on the two text distributions (model outputs are formulaic: "I can't...", "I don't want..."; human sources are not). The detector-vs-judge agreement check was not run (A17), so ratio r and the R1 class (calibrated/overconfident) are not interpretable beyond "detector-share ratio". Any "calibrated-but-hidden" headline would be circular-ish until Part 21 and the judge check exist (both folders empty).
3. Marginal calibration is not distributional calibration. Matching mean sampled-negation share to P(source negated | no-cue) can hold while the model negates the wrong inputs. R1 alone cannot support "A: calibrated but hidden"; A14/R2 is the guard, and with ~68 raw cap4 positives (and ~16 human) from 2 models on identical items R2 is underpowered/exploratory-ish. Hold the claim to "same-item consistency, not replication" as A5 says; also do not call tied-score AUROC (sampled share is 0 for most units; ties give 0.5) a clean comparison against a continuous lexical OOF probability: tie handling alone advantages the continuous score. Report tie share.
4. Policies/baselines (R3):
   - Chip and plain word are modelled as an ORACLE-triggered user (taps = true positives, no false triggers) with residual reversals = commit reversals x (1-h). This is a best-case strawman in favour of the cue interventions and is not a like-for-like comparison with learned ask policies; in analyze.py the chip row's d_cost_vs_commit / caught_minus_random / recall_of_reversals are computed from the oracle ask vector (residual ignored) while weighted_cost uses the residual: internally inconsistent columns in one row. Do not tabulate those columns for chip/word.
   - G1 check is by construction (G1 only enforces cues supplied in the input; bare keywords supply none). That is a verification that G1 is inapplicable, not a benchmark of G1. Do not present "G1: no improvement" as a result; say "not applicable to the bare-keyword condition".
   - Asking is assumed to resolve to the source label (oracle). All taps/reversal gains are upper bounds; label every table so.
   - Cost-optimal ask hard-codes w_spur=1; the weight-sensitivity table only recomputes cost of fixed asks, it does not refit policies under w_spur=1/8, 1/36. Say so.
5. Undeclared deviations from the declared 10,000-resample plan: reliability ECE/Brier use the first 3,000 resamples, policies use 4,000 (analyze.py). Report as such or run 10,000. Holm over 2 models is not applied anywhere in the code (A12 says it will be).
6. Pilot-exclusion is by message for units, but stage1.py generates ALL pair inputs including the 20 pilot E-pairs families (harmless) and pairs.py excludes them; keep the exclusion consistent in the pair analysis (analyze.pair_summary reads pairs_raw which excludes them, but `sampled_neg_share_bare` joins on inputs in G, fine).

## Checks I ran (cheap)
- gens.jsonl: 0 duplicate (input,k) keys; all 12,368 sampled completions finish=stop (no length truncation); first-token draws with p<0.05: 102 observed vs ~97 expected from the greedy top-20 (a lower bound) => the chat-completions endpoint DOES use the untruncated sampler (the pilot verified /completion; this closes that gap). Good.
- Unit tests 7/7.
- Not done: no GPU use (lock held by the running Stage 1); analyze.py not executable until qwen finishes.

## Novelty (WebSearch, snippet level; 1 query this round plus PLAN section 1)
- The new query (LLM sampling distribution vs human base rate of an omitted negation, AAC keyword expansion) returned only generic LLM-vs-human distribution calibration papers (e.g. emotion-label uncertainty calibration arXiv 2604.27345; semantic calibration from sampling, ICLR 2026) and nothing on AAC keyword expansion. Consistent with the gap claimed, but not proof; the semantic-calibration and "calibrate before use" literature is the real competition for the "calibration of sampling vs base rate" framing, and arXiv 2605.25284 for "knows but does not say". The contribution must be stated as AAC-grounded omitted-cue base rate + priced silent reversals, not "LLMs are calibrated/uncalibrated".
- A reviewer will ask for an instruction-tuned vs base comparison (Q4 instruct logprobs are not base logprobs); not available here.

## Next steps
1. Let qwen finish, then llama; run pairs.py once per model under the lock; run analyze.py with --boot 10000 (fix to 10,000 everywhere).
2. Smoke-test analyze.py end to end on a tiny synthetic gens.jsonl before the real run.
3. Fix chip/word row columns; add Holm; add tie-share for AUROC; report detector-vs-judge agreement (150-output subset via arbiter, output text only) before any R1 class is named in text.
4. Write round2.md stating exactly what was and was not run.
