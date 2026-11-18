# Fresh validation (problem #10: mutation and fault results partly circular) - plan, frozen before any generation, run or outcome

Status: written 2026-11-18. Nothing below has been generated, run or scored. Any later change goes to DEVIATIONS.md, never into this file.
Problem: (i) the 58 seeded faults were designed with the code and its tests in view, and round 2 added tests AFTER seeing which survived
(analysis/seeded_faults/round2_report.md), so the round-2 kill rate is tuned to that set. (ii) the independent mutants (analysis/oracle_indep) fixed the
lexicon circularity but covered 6 operators, two of which (role_passive, q_embed) failed human confirmation, and the non-circular stratum is dominated by 3 templates.
Two fresh, single-shot validations answer this. Each set is built blind to the thing it is tested against, frozen by hash, run ONCE.
No human subjects: part B is annotation of study materials by ~20 adult non-author classmates (consented, paid, nothing collected about them).

# PART A. Fresh seeded-fault set (40 mutations + 10 reserve), run once against the current, frozen test suite

## A1 Blindness rules
- The builder (a person/agent who has NOT opened tests/ and has not read analysis/seeded_faults/*_report.md survivor sections for this build) writes
  `src/fresh_faults.py` (mutation table) and `analysis/fresh_validation/faults_table.json` from this taxonomy and the source only.
  Allowed reads: src/*.py of the target modules, this PLAN, analysis/seeded_faults/PLAN.md + mutant ids/lines of the old table (to exclude them).
  Not read: tests/, tests/fixtures, kill matrices, round-2 report.
- Validate step (apply + `python -m py_compile` + import of the module, NO pytest, no stored-run replay) may be run before freezing. It is the only execution allowed before the sweep.
- Freeze: sha256 of faults_table.json and of the tests/ tree (`git ls-files tests | xargs sha256sum | sha256sum`) and the HEAD commit are written to
  analysis/fresh_validation/FREEZE.json BEFORE the sweep. The sweep refuses to run if the tests/ hash differs. NO test is added, edited or removed after FREEZE
  (and none between the plan and FREEZE for the purpose of this set); a failure of the sweep infrastructure is re-run unchanged and logged, results of a mutant are never re-run.
- Tests are NOT touched once outcomes are seen. If survivors reveal test gaps, that is reported as the finding; fixing them is a later, separately labelled round with a new set.

## A2 Written taxonomy (operators distinct from the 58)
The 58 were organised by structural role (K1-K8) and mostly use boolean/pattern flips (drop `not`, and<->or, negate, string-pattern relaxations) in
attribute, labels, judge, build_requests, oracle_wa, validate_cue_inputs, layer0, runio/explode/analyze. The fresh set is organised by FAULT TYPE, applied
mostly to modules the 58 barely touched (study-code that produces the papers' human-study numbers). 8 fault types x 5 = 40:

| type | fault | typical operators (examples, not exhaustive) |
|---|---|---|
| F1 boundary | off-by-one / comparison edge | `<`<->`<=`, `>=`->`>`, range(n)->range(n-1), slice end +-1, `>= 0.8`->`> 0.8` on exclusion thresholds |
| F2 constant | wrong constant/default/threshold | numeric literal x2 or +-1, z=1.96->1.64, default arg flipped, seed constant altered, n_boot/min_n changed |
| F3 wrong operand | wrong variable / swapped args / swapped axes | a<->b in a difference, rows<->cols, kwargs order, A/B condition labels swapped in one branch, wrong loop variable |
| F4 aggregation | denominator/estimator/rounding | divide by n vs valid n, mean<->median, sum<->max, ddof 0<->1, floor<->round, percent x100 dropped, pooled vs per-unit |
| F5 identity/key | dedupe, join, grouping | drop_duplicates subset narrowed, merge how inner<->left, groupby key dropped, dict key collision, set vs list loss of repeats |
| F6 allocation | assignment/ordering/balance (human-study code) | Latin-square shift by 1, shuffle seed unused, self-annotation exclusion skipped for one role, per-annotator cap off by one, order coin reversed |
| F7 silent failure | missing branch / swallowed error / early return | `except: pass`, quarantine filter not applied on one path, empty-input early return value, default instead of raise, a continue inserted |
| F8 normalisation | sign / encoding / label map | sign flip of a paired difference, label-map entry swapped, strip()/casefold dropped, unicode form not normalised, "same"/"different" mapping inverted on one branch |

Module quota (40; every type has exactly 5 sites over the modules; module quotas are fixed so the set is not concentrated where tests are known to be good):
score_listener_study.py 6; score_repair_audit.py 5; score_oracle_indep.py 4; make_assignments.py 5; make_listener_study.py 5; make_frontier_parts.py 5;
guard code behind runs/guard_wc (guard_baseline.py + its scorer) 4; analyze.py / arbiter_tool.py statistics and aggregation 6.
If a module lacks an applicable site for a type, the site goes to the next module in the order above, recorded in the table (`moved_from`).

## A3 Site selection (seeded, mechanical where possible)
- `src/fresh_faults.py enumerate` walks the AST of the target modules and lists every site each operator can apply to (F1,F2,F3,F4,F8 mostly; F5 where pandas/dict
  calls exist). Output analysis/fresh_validation/sites.json (written before any pick). Pick = seeded sample: `random.Random("fresh|<type>|<module>")`, seed 20261118,
  first applicable site(s) in shuffled order. F6 and F7 are written by hand from the module's docstring/spec (what the function must guarantee), not from tests.
- Exclusions: a site is ineligible if it is the same file:line, or the same replaced text on the same line, as any of the 58 mutants (SF01-SF58) in the old table.
  A site is ineligible if the mutated module cannot be imported by any entry point (dead code by import graph).
- Each mutation = a single textual replacement in a single file, applied to a copy (same isolation as src/seeded_faults.py: tmp/fv/<id>/, data symlinked read-only,
  real tree unchanged; reuse the harness: `src/seeded_faults.py run` machinery, importing its columns via `--table analysis/fresh_validation/faults_table.json --prefix fresh_`).
- No equivalence screening before the run. Reserve: 10 extra sites (R01-R10) drawn by the same procedure. A primary mutation that fails apply/compile/import at VALIDATE
  is replaced by the lowest-numbered unused reserve of the same fault type (else same module, else any); the swap is logged. After FREEZE no replacement is possible.
- Table fields: id FB01-FB40, type F1-F8, file, line, original, mutated, one-line description of the intended fault, moved_from, enumerated site index.

## A4 Run and kill rule (identical to round 1/2 so numbers are comparable)
- Clean baseline first through the same pipeline; every column must pass, else stop and fix infrastructure (not tests).
- Columns: pytest per file and pooled (all current tests, including tests/test_replay_regression.py and tests/test_survivor_classes.py), oracle_identity, oracle_injection,
  oracle_challenge, validator_r5_replay, validator_t9_replay, rescore_frozen_endpoints. Supplementary, reported separately: request_rebuild; and one more "stage7 replays"
  column made only of existing scorer self-checks already in the repo (score_listener_study / score_repair_audit / score_oracle_indep `--selfcheck` if they exist at FREEZE; recorded in FREEZE.json, not added to the headline unless it existed as a test).
- A mutant is KILLED iff some column fails on the mutant AND passes on clean code (assertion, mismatch, exception, timeout, collection error). Crash-only kills reported separately.
- Headline = pooled existing-test kill rate, strict (survivors count against, no equivalence removal). A second line removes survivors proven equivalent
  (positive evidence: unreachable from stored data and every code path any entry point exercises, or provably no observable change); each equivalence claim is written with its evidence
  and checked by a second reader before it enters the second line.
- Secondary tests columns on the same single run (no extra mutant runs beyond subsetting): kill rate of "round-1-era" tests only (all pytest files except the two replay/survivor files), to
  show how much the tests written after seeing survivors generalise.

## A5 Analysis (exact, fixed) and power
- Primary: k/40 with Wilson 95% interval. Declared expectation (from 58-set round-1 67% [54,78]): interval half-width about +-13 pp at 70%.
- Comparison to the tuned set: Fisher exact two-sided, fresh k/40 vs round-2 pooled on the 58, alpha 0.05; descriptive, not a gate. Power by simulation: 55% to detect 80% vs 60%, 87% vs 50%.
  Because power is modest, the claim is stated as an interval, and a drop is described as "consistent with / larger than" the interval, never as "no difference".
- By fault type (n=5 each) and by module: counts only, no tests of significance, no intervals claimed to be informative.
- Reading rule fixed now: if the fresh rate is below the lower Wilson bound of the round-2 pooled score, the papers say the round-2 rate was tuned to the 58 and report fresh as the generalisation figure; otherwise
  they report both. The paper's headline mutation claim uses the fresh figure either way.
- Survivor reporting: each survivor gets a one-line explanation (missing test / equivalent / unreachable by stored data), by fault type.

## A6 Items to build (Part A)
1. src/fresh_faults.py (enumerate / validate / freeze / run wrapper around the seeded_faults machinery). 2. sites.json. 3. faults_table.json (FB01-FB40 + R01-R10).
4. FREEZE.json (table sha, tests/ sha, HEAD, column list). 5. Outputs: kill_matrix.csv, mutant_results.json, summary.json, report.md under analysis/fresh_validation/faults/.
CPU only; no GPU, no API.

# PART B. Fresh lexicon-blind meaning-change set: 100 mutants + 50 controls, human-confirmed, scored once

## B1 New operator families (none used in analysis/oracle_real or oracle_indep)
Prior families were negation insertion/"fail to"/"refuse to"/"hardly"/"nobody", agent passive/embedding, question embedding, implied time. New families, 20 mutants each:

| family | target dim (primary) | meaning change | minimal pair examples |
|---|---|---|---|
| scope | polarity | scope of negation/quantifier flips | "not all of them came" -> "all of them did not come"; "I don't want everything" -> "I want nothing"; "not every" -> "every ... not" |
| counterfactual | certainty / time_quantity | real event or plan <-> counterfactual | "I will go" -> "I would have gone"; "I took it" -> "I would have taken it"; "If I had gone" vs "As I went" |
| obligation | speech_act / certainty (modality) | permission/obligation/necessity swaps | "you must not go" <-> "you need not go"; "I must call" <-> "I may call"; "you can't" <-> "you shouldn't" |
| possessive_agent | agent | implicit agent carried by a possessive/relational noun changes | "my nurse gave it" -> "your nurse gave it"; "her mother will drive" -> "my mother will drive"; "their ride is here" -> "your ride is here" |
| aspect | time_quantity | tense/aspect shift without an explicit time word | "I was eating" -> "I have eaten"; "I eat" -> "I am about to eat"; "I used to take it" -> "I take it"; "I am leaving" -> "I have left" |

Construction is lexicon-blind: the builder does not read src/oracle_baselines.py (NEG/HEDGE/PAST/LATER regexes) or src/oracle_real_ops.py before the build. After the build `lex_visible`
(the mutant newly matches a baseline NEG/PAST/LATER lexicon) is computed mechanically and stored in the private key; it is reported as a stratum and never used to filter.
Because the baselines were not consulted, the non-circular stratum is expected to be the majority; the headline is the lex_visible False stratum.

## B2 Source pool and applicability
- Pool = the oracle-pass filter of analysis/oracle_indep/PLAN.md (runs/hw1/scored.parquet, valid, channel chip1/chipall/full, critical_match True, critical_source agree/arbiter, no
  quarantine, one output per family and per distinct text), 3-22 words, one sentence, EXCLUDING every text used in oracle_real/sample.jsonl and oracle_indep/candidates.jsonl.
- Per family an applicability pattern (fixed, written here, deliberately NOT the baseline lexicon): scope: contains any of {all, every, everyone, everything, both, any, anyone, never} or "n't"/"not";
  counterfactual: contains a finite verb in simple past or "will"/"am going to" with a first/second/third person subject; obligation: contains {can, can't, cannot, must, need, should, have to, may, will you, could};
  possessive_agent: contains {my, your, his, her, their, our} + a role/relational noun (a closed list of 40 roles written in src/fresh_mutants.py before build: mother, nurse, friend, doctor, ride, teacher, ...); aspect: contains a verb in simple present/past/progressive.
- Seed 20261118, per-family `random.Random(f"{SEED}|fresh|{family}")`, shuffled pool, walk until 20 successful mutants. A text is used at most once across the whole set.
- If a family has fewer than 20 applicable pool sentences, the shortfall is filled with SYNTHETIC sources: sentences written by codex-lb (<=4 concurrent) in the pool's AAC register that contain the construction;
  flagged `source=synthetic`, reported as a stratum, and the counted number of synthetic items per family is capped at 10. No source is replaced after build.

## B3 Mutant construction (fixed before any call)
- Template ops where a regex rewrite exists (scope: "not all X" <-> "all X not"; possessive swaps my<->your/his<->my; obligation swaps by lookup; aspect rewrites by verb-form table) - the table is in src/fresh_mutants.py, frozen at plan sha.
- Otherwise one LLM call per item (Gemini via src/gemini_backend.py, temperature 0, thinking off, max_tokens 96, one retry) with a FIXED family-specific prompt that states the intended minimal change, committed in
  src/fresh_mutants.py before the first call. Call cap 220 (100 mutants + 50 controls + retries). Mechanical validity: one sentence, differs from original, length 0.5x-2.5x, no unrelated change
  detectable by token-set difference > 6 tokens. Failures after retry are dropped and replaced by the next shuffled item (counted in the call cap).
- Controls (50, 10 per family, meaning-preserving within the SAME family so control and mutant surface forms match): scope "not all" <-> "some do not"/"not every"; counterfactual "I would have" <-> "I would've"/"I'd have";
  obligation "must not" <-> "mustn't"/"are not allowed to"/"cannot", "need not" <-> "don't need to"; possessive: "my nurse" <-> "the nurse of mine" only where unambiguous, plus contraction/determiner-neutral edits; aspect: "was eating" <-> "were eating" (number agreement)/"am eating" <-> "'m eating".
  Sources are separate families from the mutants (as in oracle_indep). Quotas fixed: 10 per family.
- Outputs (before any annotator or judge): analysis/fresh_validation/mutants/candidates.jsonl {id, original, mutant, dimension_hint}, key.private.jsonl {id, kind, family, expected, source text_id/family/model, ref labels, lex_visible, source type},
  draw.json (seed, pool sizes, counts, call counts), FREEZE_B.json (sha256 of candidates + key + src/fresh_mutants.py). The judge and baselines are NOT run before human returns.

## B4 Human confirmation (2 annotators per item) - frozen rules
- Packet via src/make_listener_study.py (same machinery as oracle_indep Part 29): all 150 items mixed, each to 2 different annotators, 20 annotators x 15 items = 300 judgments. Part id assigned by the coordinator (next after 29).
  Nobody annotates an item whose source family they wrote or checked (hw_blocks logic of src/make_frontier_parts.py). Sentence 1/2 order is a seeded coin per item (stored in the private key). Annotators never see kind, family or source.
- Tool: annotation_package/rate_items.html (same/different/unsure). Fixed dimension-neutral question exactly as in oracle_indep Amendment 2.
- Confirmed CHANGED: both annotators "different" (mutant). Confirmed SAME: both "same" (control). Any other pair (disagreement, "unsure", missing) = unresolved, excluded from every score, counted by family.
  Mutant both "same" or control both "different" = construction failure, reported by family, never scored. An annotator below 80% answered is dropped (items become unresolved). Agreement: raw and Cohen kappa (same/different only, and 3-way).
- Attrition is NOT repaired: no item is replaced or re-annotated after returns. Expected attrition from oracle_indep: 75% mutants confirmed (templates ~100%, free-form LLM families 0-50%); per-family confirmed n is reported;
  a family with <8 confirmed mutants is listed as "not estimable" and kept in the pooled number but given no per-family estimate.

## B5 Scoring (once, after returns and after the key is merged)
- Judge: production src/judge.py (J1+J2, concurrency <=3), on BOTH texts of every one of the 150 pairs (mutant/control text and its original), blind arbiter src/arbiter_tool.py for J1/J2 disputes (disputes
  list sent blind: text and label options only, no kind). Baselines: surface and overlap oracles (src/oracle_baselines.py) applied the same way. Judge/baseline results are produced by src/score_fresh_validation.py (adapt score_oracle_indep.py; self-check on synthetic keys before returns).
- Because many originals here are not drawn from a reference-labelled pool for these families' attributes, an oracle CATCHES a pair when its label vector changes between original and variant (pairwise rule, same for mutants and controls):
  primary = ANY of the six dimension labels (critical + five general) differs; secondary = the family's target dimension label differs. Pairwise rule is symmetric and does not trust any outside reference label.
  Unresolved judge label counts as not caught, upper bound where counted as caught reported beside.
- Sensitivity = caught / human-confirmed mutants; false-alarm rate = caught / human-confirmed controls; Wilson 95%; pooled, by family, by lex_visible stratum, by source type. Headline = pooled primary sensitivity in the lex_visible False stratum.
- Judge vs each baseline on the same confirmed mutants: exact McNemar on discordant pairs, alpha 0.05, both strata; the same on controls for false alarms. Operator-balanced mean (mean of per-family rates over estimable families) is reported beside the pooled rate.
- Comparison with oracle_indep: descriptive only (70.7% pooled; 58.5% non-circular). No pass/fail threshold; no exclusion on any oracle output.
- Run once; no prompt, regex, template or rule is changed afterwards. Infrastructure failure -> rerun unchanged and log.

## B6 Power (expected 75-90 confirmed mutants of 100, 40-50 controls of 50)
- Pooled sensitivity with 70 confirmed: Wilson half-width about +-11 pp at 65%; in the non-circular stratum (~50) about +-13 pp; per family (~14) about +-24 pp, so per-family numbers are descriptive.
- Judge vs baseline McNemar on 70 confirmed, true judge 60% vs baseline 30%, within-item correlation 0.3: power about 0.78; 60 confirmed: 0.74; baseline at 45%: 0.23 (not powered for a 15 pp gap; reported as an interval and counts only).
- False alarms with 45 confirmed controls: Wilson half-width +-8 pp at 9%.

## B7 Items/stimuli to build (Part B)
1. src/fresh_mutants.py: applicability patterns, role list, templates, family prompts, control edits, seed (frozen). 2. candidates.jsonl (150), key.private.jsonl, draw.json, FREEZE_B.json.
3. Human packet: annotation_package/<stage>/<ID>_partNN.json for 20 annotators (15 items each), annotation/fresh_validation_key.csv (private), coordinator steps entry modelled on COORDINATOR_STEPS.md section 7.
4. src/score_fresh_validation.py + self-check; judge run dir runs/fresh_validation/; analysis outputs summary.json, scores.csv, confirmation.csv, report.md.
5. DEVIATIONS.md (empty at start) in analysis/fresh_validation/.

## Order of work (so nothing is seen early)
A: enumerate -> pick -> validate -> FREEZE -> sweep once -> report.  B: build -> FREEZE_B -> packet -> returns -> confirmation -> judge/baselines once -> report. Part A and Part B are independent; neither's results feed the other.
Resources: A is CPU only (about the round-1 sweep, --jobs 6). B needs <=220 Gemini/codex-lb calls (<=4 concurrent) and ~600 judge calls (concurrency <=3) plus arbiter; no GPU. Scratch in tmp/, delete after.
