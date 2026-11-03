# partner_context, round 1: E0 pilot (feasibility; descriptive numbers are PROVISIONAL)

Scope: polarity only, 26 of 40 drawn families (14 dropped by the pre-stated checker rule), turns 0/N/D/X/Q, channels bare and chip, qwen2.5-7b (local) and gpt-6.1-terra.
Per cell n = 26 families, so intervals are wide. No human check of turns or labels yet (R9). Nothing here is used to pick conditions; E1 has NOT been run, so R1-R7 are not applied.

## What was done
1. PLAN amendment A1 (draw, authoring, checker details) written before any turn existed. Draw: `random.Random(20261102).sample(sorted polarity ids, 40)`.
2. Stage 0 v1 (`v1_failed_gate/`): checker pass 80% after retry, gate is >= 85%, so it FAILED. N passed 40%, X 82.5%, D 100%, Q 97.5%.
   Cause, from checker votes only (no model-under-test output existed): template N "What happened with X?" presupposes an event (voted affirmative), and the reading descriptions were ambiguous for noun-phrase topics.
3. Amendment A2: N -> "What about {topic}?"; reading wording changed to be about the user's sentence; D/X/Q and all pass rules unchanged. Stage 0 rerun in full (v2).
   v2: pass after retry 90.0% overall (N 70%, D 100%, X 90%, Q 100%); first try N 55%, D 100%, X 87.5%, Q 97.5%. Gate MET. 14 families with a failing turn dropped (never hand-edited): 26 kept.
   N is still the weakest type: the 12 remaining N failures were voted "affirmative" by the checker (a bare "What about X?" still invites an affirmative reply).
4. Requests (`src/frontier_partner_context_build.py`): P0c = P0 text with `The conversation partner just said: "<turn>"` in the context slot; turn 0 = plain P0, identical cache key to hw1 (78 of 390 requests per model were stored hw1 outputs). 780 unique requests, greedy, one draw.
5. Generation: terra at concurrency 4; qwen under the blocking GPU lock (390 requests in 17 s). Judge J1/J2 (gpt-6.1-sol, concurrency 3), 675 units; 15 disputed units arbitrated blind (output text only, `arbiter_tool.py`), no J1 fallback.
   Arbiter rule (declared when viewing): questions/fragments with no assertion, and sentences with an embedded negation under an affirmative main predicate -> unclear/mixed. All 15 were questions/fragments or the "I guess not X worked out" copies.

## Feasibility gate (not effect based)
| gate | result | pass |
|---|---|---|
| checker pass >= 85% after one retry | 90.0% (v2); v1 80% | yes, after A2 |
| valid labels >= 95% (judge+arbiter) | 100% (1040/1040 rows, 0 unresolved) | yes |
| parse failures < 3% | 0 / 1040 | yes |
Judge J1/J2 polarity agreement 98.5% (kappa 0.97); layer0 vs J1 99.3%.

## Results (share of 26 families; bootstrap over families, 10,000, seed 20261102, 95% CI)
Bare channel (outputs do not depend on intent, so one output per family x turn):
| model | turn | affirmative | negated | unclear/mixed |
|---|---|---|---|---|
| qwen2.5-7b | 0 | 1.00 | 0.00 | 0.00 |
| | N | 0.77 | 0.00 | 0.23 |
| | D | 1.00 | 0.00 | 0.00 |
| | X | 0.19 | 0.77 | 0.04 |
| | Q | 0.96 | 0.00 | 0.04 |
| terra | 0 | 1.00 | 0.00 | 0.00 |
| | N | 0.77 | 0.00 | 0.23 |
| | D | 0.96 | 0.00 | 0.04 |
| | X | 0.54 | 0.42 | 0.04 |
| | Q | 0.92 | 0.00 | 0.08 |

Chip channel, cue SUPPLIED (override = output polarity opposite to the cue):
| model | cue | 0 | N | D | X | Q |
|---|---|---|---|---|---|---|
| qwen | [YES] (affirmative) | 0 | 0 | 0 | 0.12 | 0 |
| qwen | [NOT] (negated) | 0 | 0 | 0.08 (+0.15 uncommitted) | 0 | 0 |
| terra | [YES] | 0 | 0 | 0 | 0.54 | 0 |
| terra | [NOT] | 0 | 0 | 0 | 0 | 0 |

Planned contrasts (vs N, as pre-declared), pilot only, no rule applied:
| contrast | qwen | terra |
|---|---|---|
| C1 override, incongruent (A+X, B+D) minus N, chip | +9.6 pp [1.9, 19.2] | +26.9 pp [17.3, 36.5] |
| C2 bare, X minus N, share negated | +76.9 pp [61.5, 92.3] | +42.3 pp [23.1, 61.5] |
| C3 bare, Q minus N, share affirmative | +19.2 pp [0.0, 38.5] | +15.4 pp [-3.8, 34.6] |
| C4 bare, X minus N, negated exact-match (= C2 by construction on bare) | +76.9 [61.5, 92.3] | +42.3 [23.1, 61.5] |

Same contrasts vs the no-turn baseline 0 (added because N is not a clean baseline, see caveat 1; `e0_extra_contrasts.csv`):
bare Q minus 0, share affirmative: qwen -3.8 pp [-11.5, 0.0], terra -7.7 pp [-19.2, 0.0]; bare D minus 0: qwen 0.0, terra -3.8 [-11.5, 0.0]; C1 pooled vs 0: qwen +9.6 [1.9, 19.2], terra +26.9 [17.3, 36.5]
(vs 0 and vs N coincide for chip because overrides are 0 under both).

## What this says (and does not)
- Headline (provisional): a partner turn that states the opposite of a supplied affirmative cue flips the output polarity in 12% (qwen) to 54% (terra) of the 26 chip cells, while neutral, question and affirmative-leaning turns do not (0-8%). So "put the partner's turn in the prompt" (the Cai-style context baseline we test) is not free: the chip, the app's strongest commitment, is overridden by context for the stronger API model.
- Bare input: X turns move qwen to negated in 77% of families and terra in 42%. That is the Cai-type benefit when the user intends the negated reading (the turn tells the model) and a NEW silent-reversal class when the user intends the affirmative one. Because bare output is intent-independent, the trade-off is symmetric: break-even rate of frame-incongruent intent among X-frame messages is q* = 0.5 (both models, bare). The real quantity is q, which we do not measure.
- AAC terms (sensitivity, no prevalence claim): among X-frame messages with an affirmative cue, 120 (qwen) to 540 (terra) silent polarity reversals per 1,000 messages; with SLP negation weight 5/5 that is 600-2,700 weighted units per 1,000. Negation 2.7%-prevalence baseline (23.9/1,000 reversals) is dwarfed in that subset, but only in messages whose partner turn actually contradicts the intent.
- H3 (question frame raises default reading): NOT supported; vs no turn the Q effect is slightly negative (-4 to -8 pp, CIs touching 0). The apparent +15-19 pp vs N is an artifact: N lowers commitment (23% unclear/mixed, the model writes a question back to "What about X?"), so N is a poor baseline. This should be fixed before E1 (use 0 as the primary baseline or a content-light N; the plan's C3/C4 definitions vs N inherit the problem). Not changed by me; flagged for the director.
- D (affirmative lead) has ~0 effect on both channels, as the ceiling predicts.

## Caveats and problems (honest)
1. N baseline defect as above; also N is the weakest checker type (70% pass).
2. Many chip overrides read as replies to the partner ("Yes, using cream at breakfast did not work out."; qwen: "I heard ... didn't work out."). So some of C1 is [YES] being read as "yes, I agree with your remark", and qwen's overrides often echo the turn. Both are real failures for an AAC user saying an intended sentence, but the mechanism is reply-to-turn / echo, not a pure polarity confusion; the judge scores polarity only.
3. Only 26 families after drop, polarity only, one draw, two models; terra at T=0 is not exactly reproducible (API ignores seed). Cell n is small and CIs wide; no multiplicity adjustment.
4. Turns are model-authored templates; naturalness unknown until the annotation returns; the checker (gpt-6.1-sol) differs from the judge only in prompt, not model family.
5. Benchmarks (word cue, guard G1, background-only instruction, context-ablation, random/always-ask, taps and acceptability) were NOT run: they belong to E2, which per R6 triggers only after E1. The pilot's pooled C1 and C2 point estimates both exceed the 5 pp trigger, so E2 would trigger if E1 replicates; this is a statement about the pilot, not a decision.
6. Two plan amendments (A1, A2) were needed; A2 is a design change made after the checker gate failed, before any model output existed.

## Artifacts
- analysis/frontier/partner_context/{PLAN.md (A1, A2), turns.jsonl, checker.jsonl, turns_meta.json, v1_failed_gate/, items_e0.jsonl, e0_results.csv, e0_extra_contrasts.csv, e0_gate_inputs.json, e0_examples.json, summary.json, round1.md, ANNOTATION_REQUEST.md}
- annotation/frontier_partner_context_items.json, annotation/frontier_partner_context_key.csv (built, not sent)
- runs/frontier_partner_context_e0 (generations, judgments, arbiter, scored.parquet), _qwen, _api, requests in runs/frontier_partner_context_req/e0.jsonl
- src/frontier_partner_context_{templates,stage0,build,analyze_e0}.py, src/frontier_partner_context_run_e0.sh
Examples (real stored outputs, rule: first two by family id with a negated label on X-turn cells per model/channel): see e0_examples.json.
