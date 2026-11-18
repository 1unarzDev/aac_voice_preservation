# whole_message: human labels (Stage 5, Part 23, R-WM-1)

Status: scored 2026-11-17 under the frozen rules (`annotation/COORDINATOR_STEPS.md` section 5, Part 23; `ANNOTATION_REQUEST.md`; PLAN section 5). Script `src/frontier_stage5_p23_whole_message.py`; tables `human_*.csv`; summary `human_summary.json`. Descriptive, no new threshold; human labels sit next to the machine results as validity checks.

**Data.** 13 annotators, 360/360 ratings (120 items x 3; no missing, none extra, the returns match the private assignment exactly), 108 output items (36 inputs x arms A0 plain, A1 preservation, A2 minimal-expansion, generator gpt-6.1-terra, chip1, greedy; 82 distinct input-output pairs, so some identical sentences were rated under two arms by different people) and 12 verbatim keyword copies. Consensus = 2 of 3 on each question (Q1 had no split item; Q2 had 6 three-way splits, kept as "not added"). **Every interval is a family-cluster bootstrap over the 36 inputs (4,000 resamples); with 36 inputs the intervals are wide and are meant to be read that way.** Rater agreement: Q1 (which version) Fleiss kappa .85 [.77, .91]; Q3 (accept) .68 [.58, .76]; Q2 (added / left out) .44 [.35, .52], so the added-content call is the noisiest human label.

## Headline
1. **The reference-free "unrequested content" flag points the right way but undercounts what people see.** Against the 3-rater majority for "added content", the gpt UC flag has kappa .23 [.07, .39], sensitivity .31 [.17, .46], specificity .94 [.86, 1.0], AUROC .62 [.54, .71]. Humans call 67% of plain-prompt (A0) outputs "added", the flag 36%.
2. **The preservation and minimal-expansion prompts reduce human-seen added content, by about half the flagged amount, and do not change acceptability.** A2 minus A0 on the same 36 inputs: added content **-16.7 pp [-33.3, 0.0]** (judge flag: -27.8 pp); acceptable **0.0 pp [-13.9, +16.7]**; Q1 = intended version **+16.7 pp [0.0, +33.3]**. A1 minus A0: added -13.9 [-30.6, +2.8]; acceptable -2.8 [-13.9, +8.3]; match +8.3 [-8.3, +25.0].
3. **Critical-only checking does not predict human rejection, and length does about as well as a reference-free judge.** AUROC for human rejection (Q3 "no", 25 of 108): critical-reversal flag .45 [.38, .50]; gpt UC flag .65 [.53, .80]; reference-free score .65 [.52, .79]; output length / keyword words .81 [.67, .91]; output words .83 [.70, .92]; the score that sees the writer's sentence (upper bound) .89 [.80, .96]. Length minus reference-free score +.16 [-.00, +.31].
4. **Verbatim copies add nothing, and are not sentences.** 0 of 12 copies "say something beyond the keywords" (0% [0, 24]); 0 of 12 are "a complete sentence you could say as it is" (0% [0, 24]). The UC flag (0/12) agrees with the first; it is silent on the second.

## 1. Per-arm human rates (consensus 2 of 3; 36 inputs per arm; family-cluster 95% CI)
| measure | A0 plain | A1 preservation | A2 minimal-expansion | all 108 |
|---|---|---|---|---|
| acceptable (Q3 yes or small edit) | 77.8% [63.9, 91.7] | 75.0% [61.1, 88.9] | 77.8% [63.9, 91.7] | 76.9% [64.8, 88.0] |
| acceptable as-is (Q3 yes) | 27.8% [13.9, 41.7] | 38.9% [22.2, 55.6] | 38.9% [22.2, 52.8] | 35.2% [23.1, 48.1] |
| Q1 = the intended version | 47.2% [30.6, 63.9] | 55.6% [38.9, 72.2] | 63.9% [47.2, 77.8] | 55.6% [42.6, 68.5] |
| Q1 = "something else" | 52.8% | 44.4% | 36.1% | 44.4% |
| added content (Q2 added or both) | 66.7% [50.0, 80.6] | 52.8% [36.1, 69.4] | 50.0% [33.3, 66.7] | 56.5% [43.5, 69.4] |
| left out (Q2 left out or both) | 55.6% [38.9, 72.2] | 66.7% [50.0, 80.6] | 58.3% [41.7, 75.0] | 60.2% [47.2, 72.2] |
| gpt UC flag (key) | 36.1% | 16.7% | 8.3% | |
Per-rater-judgment rates (not majority) agree to within 2 pp (`human_arm_rates_judgment_level.csv`).

## 2. Paired contrasts (same input, family x variant; 36 pairs; discordant counts = inputs better under the first arm / under the second)
| measure | A2 - A0 | A1 - A0 | A2 - A1 |
|---|---|---|---|
| acceptable | 0.0 [-13.9, +16.7] (4 / 4) | -2.8 [-13.9, +8.3] (2 / 3) | +2.8 [-8.3, +13.9] |
| acceptable as-is | +11.1 [-2.8, +27.8] (6 / 2) | +11.1 [-5.6, +27.8] (7 / 3) | 0.0 [-16.7, +16.7] |
| Q1 = intended | **+16.7 [0.0, +33.3]** (8 / 2) | +8.3 [-8.3, +25.0] | +8.3 [-2.8, +22.2] |
| added content | **-16.7 [-33.3, 0.0]** (2 / 8) | -13.9 [-30.6, +2.8] | -2.8 [-19.4, +13.9] |
| left out | +2.8 [-13.9, +19.4] | +11.1 [-5.6, +27.8] | -8.3 [-25.0, +8.3] |

## 3. Metric validity against human labels
AUROC (family-cluster CI; 108 outputs; positives: reject 25, added 61, Q1 not intended 48).
| score | human rejection | human added | Q1 not intended |
|---|---|---|---|
| critical-only reversal flag | .45 [.38, .50] | .50 [.44, .56] | .44 [.37, .50] |
| gpt UC flag | .65 [.53, .80] | .62 [.54, .71] | .60 [.51, .70] |
| reference-free score (1-5) | .65 [.52, .79] | .66 [.58, .74] | .62 [.52, .72] |
| output / keyword length | .81 [.67, .91] | .70 [.56, .83] | .64 [.48, .77] |
| output words | .83 [.70, .92] | .65 [.51, .78] | .61 [.45, .75] |
| score that sees the writer sentence | .89 [.80, .96] | .73 [.65, .80] | .79 [.70, .88] |
Critical commitment kept (CK = 1, 99 outputs): 74.7% accepted; critical reversal flagged (CK = 0, 9 outputs): 9 of 9 accepted, 89% Q1-intended: the critical flag does not mark what third-party raters reject (n = 9, a small cell). Within CK = 1, accepted when the UC flag is off 82.1% (78) and on 47.6% (21): the added-content flag does carry information about acceptability.

## 4. Verbatim copies (12 Part 18 gate inputs)
Q4 "adds something": 0 of 12 majority-yes (Wilson 0 to 24%); Q5 "complete, sayable as is": 0 of 12 (0 to 24%); judgments 0/36 on both. The gate copies are what the reference-free judge says (nothing added) and they are fragments by human reading. The earlier machine finding "the binary flag fails 39% of copies for dropped glue words" is consistent with the human "not sayable as is", not with "adds something".

## 5. Does the verdict change?
- **Confirmed (now with human labels):** critical-only fidelity does not predict rejection (.45); the flagged-content prompt effect has the right sign (A2 minus A0 added content -16.7 pp [-33.3, 0.0]).
- **Tempered:** the machine flag shrinks by 28 pp A0 to A2; people see a 17 pp change with an interval that touches 0, because the flag misses most of what they call added (sensitivity .31).
- **Not shown:** "removing unrequested content makes outputs more acceptable to people". Acceptability is flat (A2 - A0 0.0 [-13.9, +16.7]); the only gains are in Q1 match (borderline) and added-content perception. The claim stays limited to "the judge flags less and people see somewhat less added content; acceptance does not move".
- **Reference-free metric validity:** a reference-free whole-message judge does not beat output length for predicting human rejection (delta +.16 [-.00, +.31] in favour of length); only the reference-aware score is strong (.89), which needs the writer's sentence.

## Where it does not help
36 inputs, one generator (terra), greedy outputs, one prompt per arm; intervals touch 0 for the A2 effect. Raters are third parties (13 non-authors), not the writers: they accepted 77% (Q3) whereas Part 18 writers accepted 1 of 200 as-is, so rater acceptance is a looser standard than the writer's own and is not a replacement for it. Q2 agreement is moderate (kappa .44). The critical-flag cell has 9 items.
