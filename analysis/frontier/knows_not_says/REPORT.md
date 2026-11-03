# Frontier report: knows_not_says. Calibration of negation restoration on bare keywords (two 7-8B models)

Director report, 2026-11-02, after round 3 of 3. Status: PROVISIONAL, a bounded negative/qualified result. Detector labels are checked only against a machine reference (judges J1+J2 plus a blind arbiter). No human has checked anything. All "asking" gains are simulations that assume asking resolves the cue to the source label. Sources: round3.md, critique1-3.md, PLAN.md (amendments A1-A25), stage1/tables.md, summary.json.

## 1. Question
When a person types a sentence that contains a negation and AAC keyword compression drops it, the model expands bare keywords to an affirmative sentence (a silent reversal). Is that default (A) a decoding problem, with a roughly calibrated sampling distribution hidden by greedy decoding, (B) a miscalibrated model distribution, or (C) calibrated on average but carrying no per-input signal about which inputs lost the cue? And can sampling, prior-shift or probes recover it cheaply, relative to simply asking the user?

Title note: the working title "Knows but does not say" was dropped because of arXiv 2605.25284 ("Knowing but Not Showing", behavioural ambiguity recognition in QA). The finding does not support "knows" anyway. Working title: "Which reading does the model drop? Calibration of negation restoration for AAC keyword expansion". The frontier id is only a file name.

## 2. Pre-declared rules (PLAN.md, written before any generation)
- R1 (calibration, recast by A4 as an equivalence test): calibrated if the 90% CI of (sampled negated share / target) lies in [0.67, 1.5]. Overconfident if wholly outside [0.5, 2] and below. Otherwise inconclusive. A headline needs R1 and R2 together, and a dataset disagreement means no headline.
- R2 (per-input knowledge): pooled AUROC lower CI > 0.55 AND beats a lexical baseline by >= 0.03 with paired CI excluding 0. Otherwise scenario C.
- R3 (recovery): a policy must lower weighted reversals vs always-commit AND beat random-ask at the same ask rate (paired item-bootstrap CI excluding 0).
- R4 (probes) was gated on H3 AUROC >= 0.60 in >= 2 models.
- Unit is the message (10,000 resamples, seed 20261102, HT-weighted, stratified). Holm correction across models. Detector-based labels are flagged.
- Post-failure amendment, disclosed: Stage 0 check A1(c) (forced-decoding scorer within 0.05 nats on >= 95% of sequences) FAILED at 68%. A10 replaced it with a lenient rule that passes at the boundary (10 points below the 78% same-server repeat rate). It is treated as "noisy, not validated". One dry run on qwen (A24, B = 200) was used only for crash detection, and no rule changed after it.

## 3. What was run (and what was not)
- Run: qwen2.5-7b and llama3.1-8b (Q4_K_M, chat template), prompt P0n only. Per input, 1 greedy (top-20 logprobs) plus K = 16 untruncated T=1 samples (top_k 0, top_p 1, min_p 0). Inputs: E-cap4 (540 messages, POS-cap4 keywords, negation dropped in all units, 107 source-negated no-cue units, confirmatory) and E-human (1,367 no-cue units from 3 human keyword sets, 68 negated, exploratory). Plus a pair-scoring arm on 164 hw1/W-C polarity pairs with placebo contrasts. Detector validity: 834 sentences judged by J1+J2 (agreement 827/834, kappa 0.977) with 7 arbiter disputes.
- NOT run: hidden-state probes and steering (Stage 4), 14B/Nemo/Gemma, temperature sweep, legend arm, GPT/Gemini sampling arm, verbalised-confidence baseline, Stage 3 scale-up, the embedding arm (server returned 501). The "probes" half of the frontier title was never executed. This is a scope gap, not a finding.
- Two models on identical items are consistency, not independent replication. No "k of 5 models" claim exists.

## 4. Results (95% CI unless stated; detector-relative)
**Scale of the problem (always-commit, greedy, E-cap4).** 104.2 silent negation reversals per 1,000 messages [81.2, 128.9] for qwen, and 104.9 [81.8, 129.7] for llama. Greedy restores the negation in about 3% of source-negated units. On E-human it is about 23 per 1,000. SLP weight for polarity reversal is 5.0/5. Greedy run-to-run text change (about 8% of repeats) is not in these CIs.

**R1, is the distribution calibrated? No for qwen, mixed for llama.**
| model | set | target | sampled share | ratio [90%] | class |
|---|---|---|---|---|---|
| qwen2.5-7b | E-cap4 | 10.8% [8.5, 13.3] | 0.49% [0.22, 0.81] | 0.05 [0.02, 0.07] | overconfident |
| qwen2.5-7b | E-human | 2.6% [1.7, 3.8] | 0.36% [0.13, 0.66] | 0.14 [0.06, 0.27] | overconfident |
| llama3.1-8b | E-cap4 | 10.8% | 1.57% [1.03, 2.23] | 0.15 [0.10, 0.21] | overconfident |
| llama3.1-8b | E-human | 2.6% | 1.87% [1.27, 2.57] | 0.71 [0.46, 1.12] | inconclusive |
Hypothesis (A), "calibrated but hidden by decoding", is rejected. The server's default top-k/top-p/min-p truncation does hide the tail (0 tail draws vs 14.1 expected), but with the untruncated sampler the tail is still 7-20 times too thin on E-cap4. Headline only for qwen (both sets). Llama is overconfident on cap4 only, so the datasets disagree and the rule forbids a headline for it. Caveat from critique 3: the E-cap4 10.8% is the corpus rate of negated messages after POS-cap4 stripping, not a human omission rate, and marginal calibration is not the Bayes-correct test for a per-input predictor. E-cap4 is a stress test. E-human (2.6%, human omission) is the realistic target. Predictive-value correction for detector error leaves every class unchanged. Politeness and speech act are unvalidated and kept out of claims.

**R2, does the sampled share rank at-risk inputs? Not at K = 16, and the test is resolution-limited.** E-cap4 tie-aware HT-weighted AUROC:
| score | qwen | llama | pooled |
|---|---|---|---|
| sampled share, K = 16 | 0.53 [0.51, 0.55] | 0.59 [0.54, 0.65] | 0.56 [0.53, 0.59] |
| greedy first-token entropy | 0.49 [0.42, 0.57] | 0.48 [0.40, 0.56] | 0.49 [0.42, 0.56] |
| greedy mean-token entropy (top-20 approx.) | 0.59 [0.51, 0.67] | 0.63 [0.57, 0.70] | 0.61 [0.54, 0.67] |
| keyword-only lexical logistic (model-free, cross-fitted) | 0.64 [0.58, 0.71] | 0.64 [0.58, 0.71] | 0.64 [0.58, 0.71] |
The R2 rule fails (pooled lower CI 0.53 < 0.55, and sampled minus lexical is -0.08 [-0.16, -0.01] pooled). Because 97% (qwen) and 87% (llama) of units have a sampled share of exactly 0, this is a measurement-resolution limit. The honest statement is "K = 16 sampled share does not discriminate", not "the model has no per-input knowledge". Not done, and the obvious next step: a continuous score (early-position negation-token logprob mass from stored top-20 logprobs, or K >= 256 on the positives plus a matched negative draw). Holm tests reject AUROC = 0.5 for both models (adjusted p 0.003, 0.0008), which is statistically real but practically tiny. The Stage 4 gate (AUROC >= 0.60 in >= 2 models) was not met (0.53, 0.59).

**R3 and the AAC benchmark (E-cap4, per 1,000 messages, simulated, same items).** Cost reduction comes from asking, not from the model's uncertainty.
| arm | qwen reversals / taps | llama reversals / taps |
|---|---|---|
| always-commit (status quo) | 104.2 / 0 | 104.9 / 0 |
| always-ask | 0 / 1,000 | 0 / 1,000 |
| random-ask at 10/100 | 93.8 / 100 | 94.4 / 100 |
| negated-fraction ask at 10/100 (our scalar version of the semantic-entropy idea) | 91.6 / 100 | 80.8 / 102 |
| greedy mean-token-entropy ask at 10/100 | 81.4 / 101 | 92.5 / 104 |
| lexical logistic ask at 10/100 (no model, needs labelled data) | 80.6 / 102 | 81.3 / 102 |
| lexical logistic ask at 25/100 | 63.1 / 250 | 63.8 / 250 |
| cue chip, ORACLE-triggered | 0.5 / 108 | 1.0 / 108 |
| plain word, ORACLE-triggered | 1.5 / 108 | 0.5 / 108 |
| guard G1 | not applicable | not applicable |
- Caught minus matched random-ask at 10/100 (per 1,000): negated-fraction ask qwen +2.2 [-0.5, 5.4] (no), llama +13.4 [4.7, 23.2] (yes). Lexical ask +12.9 and +12.8 (both CIs exclude 0). Mean-token entropy qwen +12.2 [3.0, 22.6], llama +1.4 [-5.0, 9.0]. First-token entropy never beats random.
- Closest implementable prior methods: contextual calibration (Zhao et al., ICML 2021) is degenerate for llama (its content-free input already yields negation in 6/16 samples) and does not beat random-ask. A Platt cost-optimal rule collapses to "ask all or ask none" because the 10% base rate exceeds the 0.03 tap price (c = 0.03), and at c = 0.1 does not beat random. Rows that "recover" by asking 998 of 1,000 are artefacts. The SpeakFaster-style ranker and any probe-based estimator were not implemented.
- G1 acts only on supplied cues. On bare keywords it raised 0 polarity flags.
- **Improvement in AAC terms, honestly.** Realistic, non-oracle: model-side or lexical asking removes about 20-40% of the 104 reversals (to 63-92 per 1,000) at 100-250 taps per 1,000. Upper bound only: an oracle-triggered cue brings it to about 1 per 1,000 at 108 taps. That is largely by construction (taps equal the positives). It ignores the cost of the user knowing when to cue, and it assumes the cue is honoured. It is not a deployable result. No acceptability data exist, because there are no participants.

**Pair scoring (provisional, noise-limited).** The affirmative variant is preferred in 94% (qwen) and 91% (llama) of 164 polarity pairs under the full-sum scorer, but only 68% and 51% under the length-normalised scorer. 29-37% of pairs exceed the placebo 95th percentile. This supports "the affirmative reading is far more probable", not any claim about indifference.

## 5. Critic issues and resolution
| round | issue | resolution |
|---|---|---|
| 1 | No outputs (pilot never got the GPU lock) | Not a design flaw. Lock-wait fixed, pre-outcome amendments A1-A9. |
| 1 | R3 queries-per-catch bar vacuous, no HT weighting, power, replicate unit | A2-A5 (weighted metrics, per-dataset random-ask comparator, models as consistency, power stated). |
| 2 | A1(c) redefined after failure at zero margin | Disclosed in full as a failure. Scorer treated as noisy. |
| 2 | Detector asymmetry between outputs and sources | Machine-referenced validity run (J1+J2+arbiter). Predictive-value correction is inside the bootstrap. Class unchanged. |
| 3 | R2 score cannot resolve a 0.5-1.6% event (ties) | Conceded in this report. R2 reworded as resolution-limited. Continuous negation-mass score not run (open). |
| 3 | "Semantic-entropy" benchmark mislabelled | Renamed "negated-fraction ask". Clustering-based semantic entropy not implemented. |
| 3 | R1 target is an artefact of cap4 construction, and the llama disagreement was headlined | Headline restricted to qwen. cap4 labelled a stress test. |
| 3 | PPV depends on codebook, "sensitivity 1.00" overstated, 3 vs 7 arbiter disputes | PPV 0.74/0.85/0.73 reported as codebook-dependent. NPV 300/300 with a one-sided FN bound of about 1.3% rather than "sensitivity 1.00". ANNOTATION_REQUEST.md corrected to 7 disputes. |
| 3 | Oracle chip/word headline is a tautology | Labelled an upper bound. Realistic 20-40% reported first. |
| 3 | Stop-rule wording, R3-a relabelled post hoc, probes never ran | Disclosed. The R3-a relabel ("necessary but not discriminating") is post hoc relative to A22(c), where it was a declared test that both models pass. Only R3-b counts. Stages 3-4 were cancelled under the stop-rule spirit and round cap, and this is a scope gap. |
| 3 | Not fixed (needs new compute or humans) | Verbalised-confidence baseline, temperature curve, other model families, 14B, negation-mass score, codebook-sensitivity re-labelling. |

## 6. Strongest true claim
On POS-cap4 bare keywords (negation removed in every unit), qwen2.5-7b and llama3.1-8b greedy decoding restores the negation in under 1% of the roughly 10% of messages whose source was negated. That is about 104 silent reversals per 1,000 messages [81, 129], detector-relative. Their untruncated K = 16 sampled negation share is 0.5-1.6%, so default decoding is not hiding a calibrated tail, at least for qwen on both datasets. The K = 16 sampled share ranks at-risk inputs only slightly above chance (AUROC 0.53-0.59) and no better than a model-free keyword classifier (0.64). Model-side asking removes at most a fifth to two fifths of reversals at 100-250 taps per 1,000.

Not claimable: "the model knows but does not say" (R2 fails and is resolution-limited), any probe/steering result, any real-user or acceptability benefit, calibration of politeness or speech act, any claim for llama on E-human, or "k of 5 models".

## 7. Novelty and closest prior work
Verified at snippet or abstract level only, none read in full text:
- arXiv 2605.25284 (Knowing but Not Showing): behavioural ambiguity recognition vs clarifying questions in QA. Adjacent, not the same: it has no logprob or sampling calibration, no negation dimension and no human base rate.
- arXiv 2511.04869 (Trained on Tokens, Calibrated on Concepts): the nearest frame for semantic-level calibration via sampling. Novelty must be argued against it.
- Zhao et al. 2021 (contextual calibration), implemented as a baseline.
- Semantic entropy (Kuhn et al. ICLR 2023, Farquhar et al. Nature 2024): only a scalar proxy implemented.
- Hou et al. 2024 (clarification ensembling): seen only in a survey snippet, not implemented.
- Probing-for-ambiguity papers (EMNLP 2025, COLING 2025 and others): not run here.
- SpeakFaster (Cai et al.): not implemented.
Novelty is medium-low and confined to the AAC keyword-omission setting: an independently measured human omission rate set against the model's sampling distribution, tied to a measured silent-reversal cost with SLP weights and a model-free lexical comparator. The result is negative, which limits novelty value. Run the three re-check queries listed in PLAN section 1 before any paper.

## 8. Limitations
- Detector labels throughout. Machine-reference PPV is 0.73-0.85 with a codebook choice that counts uncertainty wording and some clause negations as not negated. No human check (534-item request written, not sent).
- Two Q4 instruct models, one prompt, same items. Chat-template logprobs are not base-model logprobs.
- The lexical baseline is trained on the same source labels, so it needs labelled data in deployment.
- The pair-scoring arm is noise-limited (forced vs generation logprobs agree within 0.05 nats on only 68% of sequences).
- SLP weights come from n = 2 raters.
- Nothing human checks the premise that asking resolves the cue.

## 9. Recommended use
- **CALE-AI lift by Nov 16: yes, narrowly.** Use it as a short, honest negative-result section or a figure. Claims: (i) the scale, about 104 silent reversals per 1,000 on cap4 stress keywords and about 23 on human keywords; (ii) default and untruncated sampling are both overconfident for qwen; (iii) K = 16 sampling does not rescue it; (iv) the only large recovery is a user-supplied cue (upper bound), and model or lexical triggers recover 20-40%. Use stage1/figs/fig1-fig4. Label it provisional and detector-relative. Do not mention probes.
- **Journal: not as is.** It needs, at minimum, the continuous negation-mass score and K >= 256 on the positives, a verbalised-confidence baseline, 14B and one more family, human confirmation of labels, and a non-oracle cue-user model.
- **New paper: no**, unless the continuous-score rerun flips R2. If the model carries a continuous per-input signal, that would be a more interesting paper (a probe study).
- **Drop: no.** The silent-reversal benchmark and the "asking beats model uncertainty" result feed the main study. The remaining compute is small (one offline logprob analysis, one GPU day). Hold the 534-item annotation request for the orchestrator's batch.

## 10. Artifacts
Code: src/frontier_knows_not_says_*.py (tests 8/8 pass). Results: analysis/frontier/knows_not_says/{stage1/,summary.json,round3.md,critique1-3.md,PLAN.md,ANNOTATION_REQUEST.md}. Figures: stage1/figs/fig1_r1_shares.png, fig2_r2_auroc.png, fig3_pareto.png, fig4_reliability.png. Raw runs: runs/frontier_knows_not_says_stage1/, runs/frontier_knows_not_says_judge/. Annotation build: annotation/frontier_knows_not_says_*.
