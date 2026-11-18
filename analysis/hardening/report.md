# A4 CPU hardening: report (2026-11-18)

Plan: `PLAN.md` in this folder, written before any script ran. Code: `run_hardening.py` (seed 20261117), `build_report.py`. Frozen estimates remain the headline; every number below is a sensitivity or an audit. No new human data, no model call, no GPU. Not committed.

## Verdict

- No frozen conclusion changes. Chip raises listener success (+20 pp) and lowers opposite-action responses (about -21 pp) under every dependence model; the received-reversal difference stays 'not confirmed' under the frozen rule (item-cluster randomisation p about 0.06). Details and one nuance in section 1.
- No listener judged a pair they wrote or checked (0 of 846 judgments). Text-level exposure to the same sentence elsewhere in the program touches 89 of 846 listener-item cells (10.5%); dropping them leaves the chip - bare gain at the same size.
- SLP weights: every weighted number moves in level but no ordering or sign changes; the two raters gave identical weights to all four listener-study dimensions, so the listener SLP-weighted reversal is rater-invariant.
- Power: the listener study can detect about 15.8 pp (success) and 14.1 pp (opposite action) at 80% power; it cannot detect the observed reversal difference (MDE 7.6 pp, observed 4.2 pp). Part 17 could not settle a -10 pp margin (non-inferiority power about 0.33 at a true difference of 0).

## 1. Listener study with crossed listener x item dependence

Same 846 unit judgments (20 listeners, 120 items, each listener sees an item at most once; 846 listener-item cells; judgments per item median 6.0). Differences in percentage points. GLMM = logistic, crossed random intercepts for item and listener (statsmodels BinomialBayesMixedGLM, variational Bayes, population-averaged difference; VB intervals are too narrow and are shown as a direction check). LPM-2way = linear probability, two-way cluster-robust (item x listener). LPM-itemFE = item fixed effects, cluster-robust by listener. Frozen = the two-way cluster bootstrap of `analysis/listener_human` (10,000 resamples). p(item), p(listener) = sign-flip randomisation tests with items or listeners as clusters.

| contrast | outcome | ref % | arm % | GLMM | LPM-2way | LPM-itemFE | frozen bootstrap | p(item) | p(listener) |
|---|---|---|---|---|---|---|---|---|---|
| chip1 - bare | success | 8.3 | 28.3 | 19.5 [14.7, 24.5] | 20.0 [11.9, 28.1] | 20.0 [13.6, 26.4] | 20.0 [9.1, 31.2] | 0.000 | 0.000 |
| chip1 - bare | reversal | 5.0 | 0.8 | -4.1 [-6.7, -2.1] | -4.2 [-7.9, -0.4] | -4.2 [-6.6, -1.8] | -4.2 [-9.9, 0.7] | 0.062 | 0.007 |
| chip1 - bare | conseq | 22.5 | 1.2 | -20.2 [-24.8, -15.9] | -21.2 [-28.6, -13.9] | -21.2 [-25.5, -17.0] | -21.2 [-31.3, -11.6] | 0.000 | 0.000 |
| chip1 - bare | unclear | 86.7 | 70.8 | -15.5 [-20.0, -11.4] | -15.8 [-23.0, -8.7] | -15.8 [-22.2, -9.5] |  [, ] | 0.000 | 0.000 |
| nlcue - chip1 | success | 27.0 | 26.5 | -0.6 [-4.5, 3.4] | -0.5 [-6.1, 5.1] | -0.5 [-4.7, 3.7] | -0.5 [-8.7, 7.9] | 1.000 | 0.846 |
| nlcue - chip1 | reversal | 1.0 | 0.0 | -1.1 [-3.0, -0.1] | -1.0 [-2.9, 0.9] | -1.0 [-2.0, 0.1] | -1.0 [-3.9, 0.0] | 1.000 | 0.499 |
| nlcue - chip1 | conseq | 1.5 | 0.0 | -1.6 [-3.7, -0.3] | -1.5 [-3.6, 0.6] | -1.5 [-2.9, -0.0] | -1.5 [-4.8, 0.0] | 0.501 | 0.249 |

G1 - bare is not refit: G1 returned the bare sentence for nearly all items (frozen difference 0.0).

Variance components (logit SD, success, chip - bare model): item 2.73, listener 0.89; item heterogeneity dominates, which is why the paired item-fixed-effect model and the item-clustered tests are the relevant checks.

Reading. Success and opposite action: the sign and size agree in all models, intervals exclude 0, and the model-based intervals are narrower than the frozen bootstrap (the bootstrap is the more conservative and stays the headline). Plain word - chip: no difference in any model, consistent with the frozen 'not shown equivalent' reading (all intervals include 0, widths of about 8 to 10 pp exceed the 5 pp margin). Received reversal: bare 5.0% vs chip 0.8%. The frozen bootstrap interval [-9.9, +0.7] pp includes 0; the crossed models (GLMM, LPM) exclude 0, but they are asymptotic and unreliable with 12 vs 2 events, and the item-cluster randomisation test gives p about 0.06 while the listener-cluster test gives p about 0.01. The honest summary is: the frozen conclusion ('not confirmed') stands as the pre-specified result; the sensitivity analyses point the same direction and are borderline. The paper should keep 'not confirmed' and may add 'sensitivity models agree in direction'.

## 2. Leakage audit

- Direct: listener is the writer of the judged pair in 0 of 846 key rows; listener is one of the three checkers of the judged pair in 0. The same pair id (hc id) appears in the listener's own check packet files for 0 cells and in their returned checks for 0 cells. The drawn families come from 20 writers (all 20 annotators are writers too, so person-level overlap is by design; pair-level overlap is zero).
- Within study: a listener never sees two units of the same item (max 1); each item is judged by 4 to 10 listeners across its units, so a listener cannot compare conditions of one item.
- Cross-stage text exposure (conservative: any listener-item cell where a source sentence of the family or the stimulus sentence appears as text in that listener's own earlier packet files, which includes other writers' near-duplicate sentences): 89 cells (10.5%), 29 of them via a source (writer) sentence; by file {'check_1': 16, 'check_2': 13, 'check_3': 12, 'intent': 4, 'part19': 7, 'part20': 6, 'part23': 14, 'part25': 3, 'part26': 4, 'part27': 6, 'part29': 17}. All are role 'other' (not the writer, not a checker of that pair): the sentence occurs in a different pair or task. Cells in `leakage_exposure_cells.csv`.
- Success among exposed cells 37.9% vs 34.1% unexposed (all conditions pooled, descriptive).

| sample | outcome | bare % | chip % | chip - bare (paired items) | items | judgments |
|---|---|---|---|---|---|---|
| all | success | 8.3 | 28.3 | 20.0 | 120 | 1164 |
| all | reversal | 5.0 | 0.8 | -4.2 | 120 | 1164 |
| all | conseq | 22.5 | 1.2 | -21.2 | 120 | 1164 |
| drop_exposed_cells | success | 7.5 | 27.6 | 20.0 | 110 | 1040 |
| drop_exposed_cells | reversal | 4.8 | 0.9 | -4.1 | 110 | 1040 |
| drop_exposed_cells | conseq | 22.8 | 1.3 | -21.4 | 110 | 1040 |

Reading. No author or checker leakage. Residual exposure is sentence-level and small, and removing it does not move the contrast. The paper can state 'no listener judged a pair they wrote or checked'; cross-stage exposure is a limitation worth one clause only if a reviewer asks.

## 3. SLP weight sensitivity

SLP-weighted numbers in the papers: CALE-AI `slp_wc_base/guard`, `slp_hw_base/chip/word` (weighted failure rate) and the macros `ls_slp_bare/chip` (listener SLP-weighted reversal; defined in the macro file, not cited in the text). SE4All prints no weighted rate (it cites severity 5 of 5 and acceptance counts only). n = 2 raters, so leave-one-out equals each rater alone. Weights: frozen = mean severity/5; uniform = every type 1.0 (the unweighted any-failure rate); rank = rank of mean severity/7; critical-only = types with mean severity >= 4 get 1, others 0.

Weights by type: frozen_mean: NEG 1.00, ACT 0.80, AGT 0.80, CRT 0.70, POL 0.50, TIM 0.80, ADD 0.80; only_SLP1: NEG 1.00, ACT 0.80, AGT 0.80, CRT 0.80, POL 0.60, TIM 0.80, ADD 0.80; only_SLP2: NEG 1.00, ACT 0.80, AGT 0.80, CRT 0.60, POL 0.40, TIM 0.80, ADD 0.80; uniform_1: NEG 1.00, ACT 1.00, AGT 1.00, CRT 1.00, POL 1.00, TIM 1.00, ADD 1.00; rank_based: NEG 1.00, ACT 0.86, AGT 0.86, CRT 0.29, POL 0.14, TIM 0.86, ADD 0.86; critical_only(sev>=4): NEG 1.00, ACT 1.00, AGT 1.00, CRT 0.00, POL 0.00, TIM 1.00, ADD 1.00

| scheme | W-C base | W-C guard | guard rel. reduction % | hw1 bare | hw1 chip | hw1 word | chip rel. reduction % | chip - word (pp) |
|---|---|---|---|---|---|---|---|---|
| critical_only(sev>=4) | 22.9 | 17.8 | 22 | 57.9 | 16.0 | 19.7 | 72 | -3.7 |
| frozen_mean | 22.0 | 14.7 | 33 | 57.4 | 14.9 | 17.8 | 74 | -2.9 |
| only_SLP1 | 22.7 | 14.8 | 35 | 59.0 | 15.2 | 18.1 | 74 | -2.9 |
| only_SLP2 | 21.3 | 14.6 | 31 | 55.8 | 14.5 | 17.4 | 74 | -2.9 |
| rank_based | 20.7 | 15.4 | 25 | 54.2 | 14.4 | 17.5 | 73 | -3.2 |
| uniform_1 | 30.3 | 18.6 | 38 | 73.5 | 19.8 | 23.4 | 73 | -3.6 |

Listener SLP-weighted reversal per 1,000 (item-balanced, two-way bootstrap with 2,000 resamples here; frozen 10,000-resample intervals are in `analysis/listener_human`):

| scheme | w polarity / other | bare | chip | chip - bare |
|---|---|---|---|---|
| frozen_mean | 1.00 / 0.80 | 40.8 [9.1, 82.2] | 6.7 [0.0, 23.5] | -34.2 [-80.3, 4.5] |
| only_SLP1 | 1.00 / 0.80 | 40.8 [9.1, 82.2] | 6.7 [0.0, 23.5] | -34.2 [-80.3, 4.5] |
| only_SLP2 | 1.00 / 0.80 | 40.8 [9.1, 82.2] | 6.7 [0.0, 23.5] | -34.2 [-80.3, 4.5] |
| uniform_1 | 1.00 / 1.00 | 50.0 [10.9, 100.0] | 8.3 [0.0, 29.4] | -41.7 [-97.8, 5.7] |
| rank_based | 1.00 / 0.86 | 43.5 [9.5, 87.1] | 7.1 [0.0, 25.2] | -36.3 [-85.7, 4.8] |
| critical_only(sev>=4) | 1.00 / 1.00 | 50.0 [10.9, 100.0] | 8.3 [0.0, 29.4] | -41.7 [-97.8, 5.7] |

Reading. The frozen weighted values are reproduced (22.0, 14.7, 57.4, 14.9, 17.8; 40.8 and 6.7 per 1,000). Levels move with the scheme (W-C weighted base 20.7 to 30.3) but within each population the ordering is unchanged and every guard or cue arm stays below its baseline. The size of the W-C guard gain depends on the weights: relative reduction runs from about 22% (critical-only) to 38% (uniform) against 33% frozen; the hw1 chip reduction is stable near 73 to 74%. Report the guard's weighted gain as 'about a quarter to two fifths depending on weights' if the sentence is kept. Chip vs word on hw1 is 2.9 to 3.7 pp under every scheme. The listener weights are identical for both raters (polarity 1.0, other three dimensions 0.8), so leave-one-SLP-out changes nothing there; uniform weights give the raw reversal rate.

## 4. Power and minimum detectable effect

MDE = 2.80 x the achieved standard error of the frozen design (two-sided alpha 0.05, 80% power), a statement about the design's sensitivity; no observed power is reported. SE for Part 28 and Stage 6 is recovered from the frozen bootstrap interval (half-width / 1.96); Part 17 uses the binomial SE of two 60-item arms (rater variance ignored, so it is optimistic); Part 18 uses a writer-cluster bootstrap recomputed here (frozen CI 14.8 to 42.0 pp). 'Power at effect' is power to detect a true difference of 10 pp (5 pp for received reversal, the whole bare rate).

| study | endpoint | frozen estimate (pp) | SE (pp) | MDE 80% (pp) | power at effect | note |
|---|---|---|---|---|---|---|
| Part 17 repair audit v2 | usable, repaired - control (item consensus) | -13.3 | 7.4 | 20.8 | 0.27 | non-inferiority rule (lower bound > -10 pp): power 0.33 if true diff 0, 0.11 if -5 pp; n per arm for 80% at 0 true diff and -10 pp margin = 201 |
| Part 18 writer intent | match (says = intended version), chip - bare | 28.0 | 6.8 | 19.2 | 0.31 | frozen CI 14.8 to 42.0 pp |
| Part 28 listener | success, chip - bare | 20.0 | 5.6 | 15.8 | 0.43 | item-FE LPM SE 3.26 pp gives MDE 9.1 pp; two-way LPM SE 4.16 pp gives 11.6 pp |
| Part 28 listener | opposite action, chip - bare | -21.2 | 5.0 | 14.1 | 0.51 | item-FE LPM SE 2.16 pp gives MDE 6.0 pp; two-way LPM SE 3.73 pp gives 10.4 pp |
| Part 28 listener | received reversal, chip - bare | -4.2 | 2.7 | 7.6 | 0.46 | power column is at 5 pp (the whole bare rate), not 10 pp; item-FE LPM SE 1.22 pp gives MDE 3.4 pp; two-way LPM SE 1.92 pp gives 5.4 pp |
| Stage 6 (Parts 26/27) | H-cov S1_C3-D3p_bare | 2.0 | 4.8 | 13.6 | 0.54 | gain; frozen status unresolved |
| Stage 6 (Parts 26/27) | H-cov S2_C3_bare_vs_G1_chip | -21.0 | 7.9 | 22.2 | 0.24 | noninf; frozen status unresolved |
| Stage 6 (Parts 26/27) | H-cov S1_E3-D3p_bare | 2.0 | 4.6 | 12.9 | 0.59 | gain; frozen status unresolved |
| Stage 6 (Parts 26/27) | H-cov S2_E3_bare_vs_G1_chip | -21.0 | 7.9 | 22.2 | 0.24 | noninf; frozen status unresolved |
| Stage 6 (Parts 26/27) | H-cov S3_E3-G1_chip | 13.0 | 4.3 | 12.1 | 0.64 | gain; frozen status pass |

Reading. The study sizes detect effects of 12 to 22 pp, which is enough for the large measured effects (cue tap +30, chip success +20, opposite action -21) and not for small ones. Not settled by design: (a) received reversal (frozen difference -4.2 pp against MDE 7.6 pp; the item-FE model SE gives MDE 3.4 pp); (b) the Part 17 deployment margin (60 per arm; 80% power to show 'lower bound above -10 pp' at a true difference of 0 needs about 200 per arm); (c) Stage 6 S1 contrasts (C3 or E3 minus D3p in bare, MDE about 13 pp against the +10 pp threshold) and S2 (MDE about 22 pp against a -5 pp margin). This supports wording 'unresolved' and 'cost of uncertain size' rather than 'no effect'.

## 5. Estimand table (CALE-AI, 10 rows)

Status values: measured (frozen design on stored text), human-judged (adult annotators or writers), machine (judge or NLI labels), projection (arithmetic; no data on people who use AAC). Source for `estimand_table.tex` and `estimand_table.csv`.

| # | claim | estimand | population | design | estimate | status |
|---|---|---|---|---|---|---|
| 1 | The guard repairs supplied-value failures on fresh items | difference in joint-pass rate, guard minus first pass (machine labels) | 1,872 supplied-cue targets, 4 models, fresh confirmation items | same items, pre-specified, family-cluster bootstrap | +9.8 pts [8.4, 11.3] | machine |
| 2 | A supplied cue restores the dropped commitment | share of outputs honouring the dropped cue, chip minus bare (speech act) | 120 elicited speech-act units, 3 models | same-item regeneration, arbiter-resolved labels | 30% -> 76% [70, 82] | machine |
| 3 | People supply the cue when it matters (cue supply q) | share of judgments choosing the cue-restored draft when keywords lost the speech-act cue | 36 items x 2 judgments, 9 adult annotators (not AAC users), speech act only | blind choice between draft pair, item-cluster bootstrap | 73.6% [59.7, 86.1] | human-judged |
| 4 | Listeners pick the intended reading more often with a cue chip | difference in P(intended reading chosen), chip minus bare | 120 messages, 20 adult non-AAC listeners judging stored text | paired by item, crossed listeners, two-way cluster bootstrap (frozen) | +20.0 pts [9.1, 31.2] | measured |
| 5 | The cue lowers the consequential error of a listener | difference in P(response implied by the opposite reading), chip minus bare | as row 4 | as row 4, descriptive secondary | -21.2 pts [-31.3, -11.6] | measured |
| 6 | The cue lowers received reversals | difference in P(opposite reading chosen), chip minus bare | as row 4 | as row 4; frozen primary, not confirmed | -4.2 pts [-9.9, +0.7] (not confirmed) | measured |
| 7 | Guard repairs are about as usable as untouched outputs | difference in usable share, repaired minus control (item consensus) | 60 + 60 outputs, 6 adult annotators (3 per item) | frozen hash-ordered list, Newcombe CI, margin -10 pts | -13.3 pts [-27.6, +1.5] | human-judged |
| 8 | Cue outputs carry what the writer meant | difference in writer-named intended version, chip minus bare | 200 outputs of the writers' own pairs, 20 writers | writer-cluster bootstrap | +28 pts [14.8, 42.0] | human-judged |
| 9 | A cue tap is the cheapest route to stored-text coverage | difference in H-cov, chip G1 minus bare G1 | 100 items, 20 writers judging their own pairs | writer-cluster bootstrap, exploratory | +30 pts [15, 44] | human-judged |
| 10 | A cue helps a person who uses AAC and a listener (chain L1-L4) | s x q x G: gain in listener success per message if the cue is supplied | people who use AAC and their partners (no data) | projection from rows 3-4; AAC link unmeasured | worst 0 (s = 0); central 14.7 pts (s = 1); best 31 pts (s = 1, q = 1, upper end of row 4) | projection |

### Chain: cue supply -> machine restoration -> listener success -> AAC-user link

| link | estimate | interval | status |
|---|---|---|---|
| L1 cue supply (writer supplies the dropped speech-act cue and the restored draft is chosen) | 73.6 | [59.7, 86.1] | human-judged (9 classmate annotators; speech act only; 36 items) |
| L2 machine restoration given the cue (speech act; bare -> chip, 3 models) | 75.6 (bare 29.9) | [69.8, 81.7] | machine (judge labels, arbiter-resolved) |
| L3 listener success given the cue-in-hand chip output (chip - bare, 4 dimensions) | 20.0 | [9.1, 31.2] | measured on 20 adult non-AAC listeners, stored outputs |
| L3s listener success, speech act only (chip - bare) | 18.3 | [-3.8, 40.9] | measured, subset (30 items), descriptive |
| L4 AAC-user link s (a person who uses AAC supplies the needed cue and picks the restored draft, relative to the classmates of L1) | unmeasured | [0.0, 1.0] | unmeasured; bounds only |

L2 is embedded in L3 for the chip arm (listeners judged the stored chip outputs), so it is not multiplied in again.

Projection (not a finding; gain_pp(s) = s x q x G, with G the cue-in-hand listener gain; s unmeasured): the gain per message in intended-reading success if the person supplies the cue is s x q x G. Worst bound: s = 0, gain 0. Central with s = 1 and measured q = 0.736, G = 20.0: 14.7 pp. Product of the measured interval ends (s = 1): 5.4 to 26.8 pp (this combines two intervals end to end, so it is wider than a joint 95% interval). Best bound: s = 1, q = 1, upper end of G: 31.2 pp; the ceiling is 91.7 pp (writer's own sentence 100%, bare 8.3%). Speech act only (q measured there): central 13.5 pp, but the speech-act listener contrast has 30 items and its interval (-3.8 to 40.9) includes 0, so the speech-act-specific chain is descriptive. q was measured with classmate annotators on speech act only; polarity and politeness keep the assumed 0.9 in the cost model. The listeners are not AAC partners and judged stored text; the AAC-user link, the partner link and any benefit to a person are untested, so the label for row 10 is projection.

## Files

`listener_crossed_models.csv`, `leakage_exposure_cells.csv`, `leakage_sensitivity.csv`, `slp_weights_by_scheme.csv`, `slp_weight_sensitivity_papers.csv`, `slp_weight_sensitivity_listener.csv`, `power_mde.csv`, `estimand_table.csv`, `estimand_table.tex`, `summary.json`.

Known limits. The GLMM is a variational-Bayes fit (no exact crossed-effects frequentist GLMM exists in statsmodels); rare-event models are unreliable and are labelled so; the exposure scan matches text, so it over-counts generic short sentences; MDEs inherit the frozen designs' clustering and use 2.80 x SE (normal approximation).
