# Part 4 repair audit: confound analysis (stored ratings; 0 generation / 0 judge calls)

Script `src/robust_repair_audit_confounds.py`; files `summary.json`, `per_rater_gap.csv`, `usable_by_stratum.csv`. Source: `annotation/returns_repair/*.csv` (14 raters x 40 items = 560 ratings; every rater rated every item), `annotation/repair_audit_key.csv`. Parser, endpoint rules, Wilson and Newcombe intervals are those of `src/score_repair_audit.py`; the stored item consensus is reproduced exactly.

## 1. Item-level n

The unit is the ITEM: 20 repaired + 20 control = 40 items, rated by the same 14 people. The 560 ratings are not 560 observations (see section 3). Known items per endpoint (unknown = tie or all raters unsure/cannot judge):

| endpoint | repaired known/20 | control known/20 | stored gap [Newcombe] |
|---|---|---|---|
| usable | 17 | 19 | -30.7 pp [-54.7, -2.0] |
| usable_or_minor | 20 | 20 | -25.0 pp [-47.3, -0.8] |
| preserving | 16 | 17 | -6.6 pp [-30.6, +16.3] |
| usable_and_preserving | 16 | 16 | -25.0 pp [-51.1, +6.9] |
| added_stance | 19 | 18 | -12.0 pp [-37.3, +14.6] |

## 2. Unknowns counted as unusable (upper-end sensitivity) or as usable

Item-level consensus; the 'unknown' rows are ties or items nobody could judge. 'Unknown = unusable/failing' treats every unknown item as a failure in BOTH arms (the upper-end reading of the repair cost, because repaired items have more unknowns); 'unknown = usable' is the reverse. Bounds = repaired unknowns fail while control unknowns pass, and the opposite.

| endpoint | stored: repaired / control | gap | unknown=unusable: repaired / control | gap [Newcombe] | unknown=usable: gap | bounds on the gap (pp) | Fisher p (unknown=unusable) |
|---|---|---|---|---|---|---|---|
| usable | 10/17 = 58.8% [36.0, 78.4]; 3 unknown / 17/19 = 89.5% [68.6, 97.1]; 1 unknown | -30.7 | 10/20 = 50.0% [29.9, 70.1] / 17/20 = 85.0% [64.0, 94.8] | -35.0 [-57.4, -5.9] | -25.0 | -40.0 to -20.0 | 0.041 |
| usable_or_minor | 14/20 = 70.0% [48.1, 85.5] / 19/20 = 95.0% [76.4, 99.1] | -25.0 | 14/20 = 70.0% [48.1, 85.5] / 19/20 = 95.0% [76.4, 99.1] | -25.0 [-47.3, -0.8] | -25.0 | -25.0 to -25.0 | 0.091 |
| preserving | 14/16 = 87.5% [64.0, 96.5]; 4 unknown / 16/17 = 94.1% [73.0, 99.0]; 3 unknown | -6.6 | 14/20 = 70.0% [48.1, 85.5] / 16/20 = 80.0% [58.4, 91.9] | -10.0 [-34.9, +16.6] | -5.0 | -25.0 to +10.0 | 0.716 |
| usable_and_preserving | 9/16 = 56.2% [33.2, 76.9]; 4 unknown / 13/16 = 81.2% [57.0, 93.4]; 4 unknown | -25.0 | 9/20 = 45.0% [25.8, 65.8] / 13/20 = 65.0% [43.3, 81.9] | -20.0 [-45.6, +10.1] | -20.0 | -40.0 to +0.0 | 0.341 |
| added_stance | 3/19 = 15.8% [5.5, 37.6]; 1 unknown / 5/18 = 27.8% [12.5, 50.9]; 2 unknown | -12.0 | 3/20 = 15.0% [5.2, 36.0] / 5/20 = 25.0% [11.2, 46.9] | -10.0 [-34.0, +15.1] | -15.0 | -20.0 to -5.0 | 0.695 |

Unknown items (repaired / control): usable 3/1; usable_or_minor 0/0; preserving 4/3; usable_and_preserving 4/4; added_stance 1/2. Added stance is a rate where 'yes' is the undesirable outcome, so for that row 'unusable' means 'added stance = yes' only through the same fill; ignore the added-stance fills.

## 3. Rater non-independence

* Distinct full answer patterns (quality + contract + added over the 40 items, 120 answers each): **7 of 14 raters**; sizes [6, 3, 1, 1, 1, 1, 1].
* Distinct quality-answer patterns: 4 (sizes [6, 4, 3, 1]); distinct usable yes/no patterns: 2 (sizes [7, 7]).
* Pairwise answer disagreements out of 120: median 27, max 38, share of rater pairs with identical patterns 20%.
* Rater groups by maximum number of differing answers (single-linkage): <= 0: sizes [6, 3, 1, 1, 1, 1, 1]; <= 2: sizes [7, 3, 2, 1, 1]; <= 5: sizes [7, 4, 3]; <= 10: sizes [7, 4, 3]; <= 20: sizes [7, 4, 3].
* Mean pairwise correlation of usable answers rho = 0.87; design-effect effective number of independent raters = 14 / (1 + 13 rho) = **1.1**.
* Identical-pattern groups: P01,P05,P06,P08,P12,P13; P03; P04,P15,P16; P17; P18; P19; P20.
* Gap in usable (repaired - control, Newcombe), one rater at a time: range -30.0 to -30.0 pp; distinct values [-30.0]. Leave-one-pattern-group-out gap: drop P01,P05,P06,P08,P12,P13: -30.0 pp; drop P03: -30.0 pp; drop P04,P15,P16: -30.0 pp; drop P17: -30.0 pp; drop P18: -30.0 pp; drop P19: -30.0 pp; drop P20: -30.0 pp.

Statement for the paper: the 14 raters are not 14 independent judgements. Their usable answers collapse to 2 distinct yes/no patterns (7 + 7), their full answers to 7 patterns, and the correlation-based effective number of raters is about 1.1; every single rater alone reproduces the same usable gap. The 40 items, not the 560 ratings, limit precision, and the item-level intervals of Part 4 are the honest ones.

## 4. Do controls differ from repaired items in difficulty?

By construction controls are P0 outputs that PASSED the strict machine check (`p0_strict_fail` = False for all 20) and are not repaired; repaired items are P0 FAILURES that G1 fixed (`p0_strict_fail`: {'True': 12, 'False': 4, 'False|True': 4}). The two arms are therefore selected on the outcome the audit is about, so 'repaired - control' compares hard cases that were fixed with easy cases that never failed: it is an upper bound on the usability cost of repair relative to what a cue-compliant output costs, not a matched causal contrast. Matching on model and channel group was designed in; the rest differs:

| factor | repaired | control | permutation p |
|---|---|---|---|
| channel group (cue / ambiguous) | ambiguous 5, cue 15 | ambiguous 5, cue 15 | 1.000 |
| model | gemma3-4b 5, gpt-6.1-terra 5, llama3.1-8b 5, qwen2.5-7b 5 | gemma3-4b 5, gpt-6.1-terra 5, llama3.1-8b 5, qwen2.5-7b 5 | 1.000 |
| dimension | agent 0, certainty 1, polarity 1, politeness 10, speech_act 4, time_quantity 4 | agent 1, certainty 3, polarity 6, politeness 2, speech_act 5, time_quantity 3 | 0.031 |
| words in output (mean) | 5.35 | 6.15 | 0.138 |
| chips in input (mean) | 1.45 | 1.20 | 0.539 |
| keyword count (mean) | 3.00 | 3.75 | 0.639 |
| occurrences of the output text (mean) | 1.40 | 2.40 | 0.013 |
| inclusion prob. pi_mc (a sampling-design artefact: repaired items come from a small pool; not a difficulty measure) (mean) | 0.21 | 0.02 | 0.000 |

Usable (consensus, unknown excluded) within strata:

| stratum | rep | ctl | diff |
|---|---|---|---|
| channel_group=ambiguous | 3/4 = 75.0% [30.1, 95.4]; 1 unknown | 5/5 = 100.0% [56.6, 100.0] | -0.250 |
| channel_group=cue | 7/13 = 53.8% [29.1, 76.8]; 2 unknown | 12/14 = 85.7% [60.1, 96.0]; 1 unknown | -0.319 |
| assigned_model=gemma3-4b | 1/4 = 25.0% [4.6, 69.9]; 1 unknown | 4/5 = 80.0% [37.6, 96.4] | -0.550 |
| assigned_model=gpt-6.1-terra | 5/5 = 100.0% [56.6, 100.0] | 5/5 = 100.0% [56.6, 100.0] | 0.000 |
| assigned_model=llama3.1-8b | 2/4 = 50.0% [15.0, 85.0]; 1 unknown | 5/5 = 100.0% [56.6, 100.0] | -0.500 |
| assigned_model=qwen2.5-7b | 2/4 = 50.0% [15.0, 85.0]; 1 unknown | 3/4 = 75.0% [30.1, 95.4]; 1 unknown | -0.250 |
| dim=agent | n/a (0 known) | 1/1 = 100.0% [20.7, 100.0] | NA |
| dim=certainty | 1/1 = 100.0% [20.7, 100.0] | 3/3 = 100.0% [43.9, 100.0] | 0.000 |
| dim=polarity | 1/1 = 100.0% [20.7, 100.0] | 5/6 = 83.3% [43.6, 97.0] | 0.167 |
| dim=politeness | 6/9 = 66.7% [35.4, 87.9]; 1 unknown | 1/1 = 100.0% [20.7, 100.0]; 1 unknown | -0.333 |
| dim=speech_act | 2/4 = 50.0% [15.0, 85.0] | 4/5 = 80.0% [37.6, 96.4] | -0.300 |
| dim=time_quantity | 0/2 = 0.0% [0.0, 65.8]; 2 unknown | 3/3 = 100.0% [43.9, 100.0] | -1.000 |

Stratified gap in usable (Mantel-Haenszel risk difference; within-stratum permutation p, 5,000 draws):

| stratification | MH risk difference | permutation p (two-sided) |
|---|---|---|
| channel_group | -30.2 pp | 0.036 |
| model | -31.7 pp | 0.025 |
| channel_group x model | -30.6 pp | 0.048 |
| dimension | -34.1 pp | 0.057 |
| unadjusted | -30.7 pp | nan |

## Caveats

* n = 20 + 20 items, 14 raters with nearly identical answers: Part 4 is a pilot. Part 17 (three independent raters per item) is the evidence for any usable-repair claim.
* Dimension mix differs (repaired items are mostly politeness, controls mostly polarity/speech act); with 20 items per arm no model-based adjustment is credible, and the stratified estimates above are descriptive.
* Controls never failed the strict machine check; a failing-but-unrepaired arm (the pre-repair outputs, or strip-only G1s outputs) is the right comparator and is only available through Part 17 if those arms were added.
* Unknown handling is a sensitivity analysis, not a re-estimation: the stored consensus (strict majority of known answers) is unchanged.
