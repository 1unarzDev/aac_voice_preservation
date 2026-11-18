# Part 28 listener communication study: human results (scored 2026-11-18)

Run exactly as frozen (analysis/listener/PLAN.md, hash-deposited protocol-hash-2026-11-18f): `python src/score_listener_study.py` (10,000-resample two-way cluster bootstrap over items and listeners, seed 20261117, percentile 95% CIs). Full tables: analysis/listener_human/{by_condition,contrasts,contrasts_no_exclusion}.csv, qc.json. Machine summary: analysis/listener/summary.json.

## Who and what
20 of 20 listeners returned (886 rows; 40 practice dropped; 0 unknown, duplicate, invalid or missing; integrity check: no duplicated answer sets). 846 unit judgments = 120 intended messages, 582 (item, condition) stimuli, 423 judge units, 2 listeners per unit. Attention check (reference success below 75%): 0 excluded; completion below 80%: 0 excluded; so the no-exclusion sensitivity equals the primary. 20 usable listeners (not underpowered). Mixed-model sensitivity not run (statsmodels absent); the bootstrap stands alone, as the plan allows.
Listeners are adult non-author annotators judging study materials. They are not AAC communication partners; comprehension is not a real-world consequence.

## Merged identical texts (plan section 2)
Identical normalised texts within an item are one judge unit and inherit their judgments. G1 equals bare for 104 of 120 items (the guard changed 16, all removal of unrequested "Please"); chip1 equals bare for 7 items. Consequence: G1 - bare is identified by 16 items only, and chip1 - bare is exactly 0 in 7 items by construction. The guard contrast therefore cannot show more than the guard's very small footprint.

## Primary contrasts (success = Q1 equals the intended reading; item-balanced; percentage points)
| Condition | Success [95% CI] |
|---|---|
| bare | 8.3 [3.2, 14.2] |
| cue chip (chip1) | 28.3 [18.6, 38.5] |
| guard G1 | 8.3 [3.1, 14.4] |
| plain-word cue (nlcue, 102 hw1 items) | 26.5 [16.5, 37.4] |
| reference (writer's own sentence), ceiling | 100.0 [100, 100] |

1. chip1 - bare: +20.0 pp [9.1, 31.2]; Holm-adjusted [6.5, 33.8]; bootstrap p = 0.0006. Excludes zero.
2. G1 - bare: 0.0 pp [0.0, 0.0]: identical success in every item (same sentences for 104 of 120). The reported bootstrap p of 2.0 in contrasts.csv is a degenerate artefact of an all-zero distribution (not a p-value); read as "no change".
3. nlcue - chip1 (102 hw1 items): -0.5 pp [-8.7, 7.9]; 90% interval [-7.2, 6.3] is not inside +/-5 pp: equivalence NOT shown (also not shown different). Holm [-10.0, 9.1].
Bare minus reference: -91.7 pp [-97.2, -85.1]. Most of the gap to the ceiling is "unclear" (below), not reversal.

## Received reversal (Q1 equals the opposite reading), per 1,000 messages
| Condition | Reversal [95% CI] | SLP-weighted (w = 1.0 polarity, 0.8 others) | Non-default intended only |
|---|---|---|---|
| bare | 50.0 [10.3, 98.5] | 40.8 [8.4, 81.0] | 66.7 [0, 150] |
| chip1 | 8.3 [0, 30.0] | 6.7 [0, 24.0] | 0.0 |
| G1 | 45.8 [9.3, 93.4] | 37.5 [7.4, 76.6] | 66.7 |
| nlcue | 0.0 | 0.0 | 0.0 |
| reference | 0.0 | 0.0 | 0.0 |
chip1 - bare: -41.7 per 1,000 [-98.9, +6.9] (SLP-weighted -34.2 [-81.1, 5.4]): the interval includes zero. Design mix: 50% of messages are non-default intended by construction; default-intended only: bare 33.3, chip1 16.7 per 1,000.
The plan's headline ("opposite of the intended meaning in X of 1,000 messages without the cue and Y with it") is therefore only descriptive: 50 versus 8, direction as expected, not a confirmed difference. Reversals are rare in absolute terms because listeners mostly said "unclear".

## "Something else / unclear" (reported separately)
bare 86.7% [79.2, 93.2]; chip1 70.8% [60.5, 80.8]; G1 87.1%; nlcue 73.5%; reference 0%. Model outputs mostly failed to carry the full intended message (the intended readings are the writers' full sentences; the bare inputs are cue-free keywords), and listeners largely said so rather than choosing the wrong reading. The cue moves about 20 points of this into success and removes most wrong-way readings.

## Consequential error (Q2 equals the opposite action), per 100 judgments
bare 22.5 [14.3, 31.2]; chip1 1.25 [0.0, 3.9]; G1 22.5; nlcue 0.0; reference 0.0. chip1 - bare -21.3 pp [-31.3, -11.6]. Non-default intended: bare 33.3, chip1 0.0; default intended: bare 11.7, chip1 2.5. Sensitivity (Q2 neither correct nor clarify): bare 38.8, chip1 7.9. Q2 errors exceed Q1 reversals because listeners who called the sentence unclear still chose an opposite action in a minority of cases; this is the more stable consequence measure here (its interval excludes zero).

## By dimension (point estimates; success pp bare / chip1 / nlcue; reversal per 1,000 bare / chip1)
polarity 10.0 / 21.7 / 21.7; 16.7 / 0.
speech_act 8.3 / 26.7 / 4.2; 116.7 / 33.3 (the plain word is weak for speech acts, hw1 speech-act items only).
agent 15.0 / 36.7 / 40.0; 33.3 / 0.
time_quantity 0.0 / 28.3 / 26.7; 33.3 / 0.
Per-dimension intervals are in by_condition.csv (30 items each; wide, descriptive).

## Confidence (Q3, 1-3, mean)
reference 3.00; bare 2.46; G1 2.45; nlcue 2.32; chip1 2.28. Listeners were least confident on unclear answers (2.4-2.5 mean over them) yet not more confident when right (2.1). Confidence does not separate conditions usefully.

## Limits
Two listeners per unit, 20 adult classmates judging materials; no AAC partners, no AAC users; the intended readings are full sentences so "unclear" is partly an information-loss outcome; 4 models, one per item; success levels are low in absolute terms (28% with the cue). The mixed model was not run.
