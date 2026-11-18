# partner_context: human labels (Stage 5, Part 25)

Status: scored 2026-11-17 under the frozen rules (`annotation/COORDINATOR_STEPS.md` section 5, Part 25; request `ANNOTATION_REQUEST.md` round-3 revision; PLAN R8/R9). Script `src/frontier_stage5_p25_partner_context.py`; every table is a `human_*.csv` in this directory; summary `human_summary.json`. Human labels sit next to the machine results as validity checks and replace no headline estimate ("No re-labelling" rule).

**Data.** 20 annotators, 774/774 ratings (258 items x 3), returns match the private assignment exactly (no missing, no extra, no duplicated answer set). Consensus = 2 of 3; three different answers = no consensus (1 of 197 Part A items, shown as a count). Part A = 197 items (137 propositional negations, 10 machine-licensed anchors, 50 affirmative controls); Part B = 61 units (56 with a partner turn, 5 arm-0 counterfactuals). Intervals are family-cluster bootstrap (Part A, 10,000 resamples) or Wilson (Part B, which has no repeated families).

## Headline
1. **The raters are reliable and the controls behave.** Part A Fleiss kappa .87 [.82, .92] (87% unanimous). Affirmative controls are called "plain statement" 78% [64, 91] (39/50) and never "invented" (0/50); machine-licensed anchors are called "restates the partner" 80% (8/10). Part B: echo kappa .80 [.67, .91], reply kappa .89 [.61, 1.00].
2. **The machine echo/reply filter is validated.** On the 56 turn-present units, the filter (echo or reply) against the human echo-or-reply call has sensitivity .96 [.81, .99], specificity .80 [.63, .91], kappa .75. Units the filter calls "neither" are human-echo in 1 of 25 (4% [0.7, 19.5]), below the pre-declared 20% line, so **the filtered numbers (+1.2 to +1.5 pp lower bound; filtered propositional C2) are not marked unvalidated.** The filter over-flags (6 false positives in 30 human-negative units), which makes the filtered lower bounds conservative.
3. **The machine decomposition over-credited partner re-wording.** Of the 137 propositional negations, humans call 29% [20, 40] a restatement of (or reply to) the partner's remark; the machine judge said 43% PARAPHRASE (agreement on partner-linked vs not: kappa .72 [.56, .85] first prompt, .81 [.68, .92] second prompt). 16 of the 59 machine-PARAPHRASE outputs are human "invented".
4. **Most propositional negations are negations the remark does not supply: 61% [50, 71] "invented" (83/137), 3.6% plain statement (5/137).** This is a descriptive reading of the same outputs, not a causal split: the keywords were intended-affirmative, so a negation that is not a restatement is by construction unsupported by the keywords, and the +8.7 pp is still an X-turn minus no-turn increment.

## 1. Part A: what the propositional negations are (family-cluster 95% CI)
| group | n | restates partner (a) | reply (b) | invented (c) | plain statement (d) | other (e) | no consensus |
|---|---|---|---|---|---|---|---|
| propositional negations (machine: neither echo nor reply) | 137 | 28.5% [19.1, 38.8] (39) | 0.7% (1) | **60.6% [50.0, 70.6]** (83) | 3.6% [0, 8.6] (5) | 5.8% [1.5, 11.3] (8) | 0.7% (1) |
| partner-linked (a or b) | 137 | **29.2% [19.6, 39.6]** (40) | | | | | |
| affirmative controls | 50 | 10.0% [2.0, 19.6] (5) | 0 | 0 | **78.0% [63.6, 90.9]** (39) | 12.0% [2.0, 25.0] (6) | 0 |
| machine-licensed anchors | 10 | **80.0% [50, 100]** (8) | 0 | 10% (1) | 0 | 10% (1) | 0 |
| all Part A | 197 | 26.4% [18.8, 34.9] | 0.5% | 42.6% [34.3, 51.0] | 22.3% [16.1, 29.0] | 7.6% | 0.5% |

By turn form (propositional, n = 25 / 64 / 48 for Xa / Xb / Xc, 137 unique turn-output pairs): restates 4 / 23 / 12 (Xb 36%, Xa 16%, Xc 25%), invented 18 / 33 / 32. By model: restates qwen 10, llama 11, gemma 11, terra 7; invented 17, 36, 22, 8 (`human_partA_by_*.csv`). Cell sizes are small; no model contrast is claimed.

**Machine versus human (172 items where both give a class and humans chose a, b, c or d).** Three-class kappa .43 [.31, .56] (first prompt) and .47 [.35, .59] (second prompt); the disagreement is almost all one cell: machine INDEPENDENT is human "invented" (38 of 46 propositional) because the two schemes cut the "not a restatement" side differently (the machine asks whether the output depends on the turn; the human asks whether the keywords or the remark support it). On the question that carries the claim, partner-linked or not, agreement is good (kappa .72 to .81) and the machine over-states partner-linkage by about 10 to 14 pp.

## 2. Re-split of the +8.7 pp (propositional C2, pooled, bare channel, X minus no-turn; +8.72 [6.92, 10.58])
Class shares of the 137 propositional negations times the headline increment. The interval is the share interval only (the C2 interval is not propagated); the class mix of the increment is assumed equal to the class mix of the X-turn negations (arm 0 has only 5 negated outputs, so it cannot be checked).
| component | human share | pp of +8.7 [share-only CI] | machine rough attribution (round 3) |
|---|---|---|---|
| restates or replies to the partner | 29.2% [19.6, 39.6] | **2.5** [1.7, 3.4] | paraphrase about 4.4 |
| invented (neither keywords nor remark supply it) | 60.6% [50.0, 70.6] | **5.3** [4.4, 6.2] | fabrication about 1.7 |
| plain statement | 3.6% [0, 8.6] | 0.3 [0, 0.8] | independent about 2.7 |
| other / no consensus | 6.5% | 0.6 | |
Reading: the increment is not mainly the model parroting the partner; it is mainly the model writing a negation the keywords do not carry after a negative remark. The headline is unchanged; its interpretation moves from "half is partner re-wording" to "about a third is partner re-wording, about three fifths is an unsupported negation".

## 3. Part B: filter validity (human consensus, 2 of 3)
| machine decision | n | human echo | human reply | human echo or reply |
|---|---|---|---|---|
| echo-only (turn present) | 25 | 80% [61, 91] (20) | 0% [0, 13] | 80% [61, 91] |
| neither (turn present) | 25 | **4% [0.7, 19.5] (1)** | 0% [0, 13] | 4% [0.7, 19.5] |
| reply (turn present; all that exist) | 6 | 50% [19, 81] (3) | 67% [30, 90] (4) | 83% [44, 97] (5) |
| arm-0 counterfactual: echo / neither / reply | 1 / 2 / 2 | 0 / 0 / 0 | 0 / 0 / 2 of 2 | |
| Filter vs human (turn present, n = 56) | TP / FN / TN / FP | sensitivity [Wilson] | specificity [Wilson] | kappa |
| echo flag vs human echo | 20 / 4 / 27 / 5 | .83 [.64, .93] | .84 [.68, .93] | .67 |
| filter (echo or reply) vs human echo-or-reply | 25 / 1 / 24 / 6 | .96 [.81, .99] | .80 [.63, .91] | .75 |
| reply flag vs human reply | 4 / 0 / 50 / 2 | 1.0 [.51, 1.0] | .96 [.87, .99] | .78 |
Arm-0: the five arm-0 outputs were judged against the family's Xa remark as a counterfactual; humans did call the two machine-"reply" ones replies, but five units cannot validate the symmetric filter and nothing is claimed beyond that.

## 4. Does the verdict change?
- **Unchanged:** every headline estimate (C1 +7.05 [5.26, 9.04] unfiltered; filtered lower bounds +1.22 / +1.54; C2 +8.7 propositional, up to +36.7 counting echoes; the author-dependence, Xb-confound and benchmark conclusions). Part A and B do not touch them.
- **Strengthened:** the echo/reply machine filter, so "echo and agreement replies" are a validated part of the +36.7 range and the filtered rows are usable as lower bounds.
- **Changed:** the interpretation of the propositional residue (29%, not about half, restates the partner; 61% are unsupported negations); the PROVISIONAL (R9) label on the decomposition is lifted only in this corrected form.
- **Not settled:** whether an echo or agreement reply under a [YES] cue is harm to a person (no human outcome measure); whether the pattern holds for turn authors other than the two models used; the 5-output arm-0 symmetry check.

## Where it does not help
Humans do not settle causation: the +8.7 pp is still a difference between conditions, and the class shares are of the X-turn outputs. Reply is rare (4 of 56 units), so the reply half of the filter is thin. Raters are non-authors reading text; they are not AAC users or SLPs. One keyword-to-sentence prompt and two turn authors.
