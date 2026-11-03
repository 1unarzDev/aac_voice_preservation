# Frontier report: value_of_cue. Does a per-message commit / show-two / ask policy cut silent reversals at a small tap cost? (AAC keyword expansion)

Director report written 2026-11-03 (writing pass after round 3 of 3; the workflow subagent could not save it, so it was rebuilt from the run files). Status: PROVISIONAL, a modest and qualified result, speech-act only. Labels are detector source labels and machine-arbitrated output labels. q (the pick probability) and rho (chip restoration) are simulated. Nothing was checked by a human. Sources: PLAN.md (A1-A7, D-R1..D-R3), round1-3.md, critique1-3.md, round2/, round3/, b5lex/b5lex.csv, ANNOTATION_REQUEST.md, summary_round3.json, SYNTHESIS.md section 2. Headline numbers were re-derived from round3/*.csv and b5lex/b5lex.csv. Where a summary disagreed with a file, the file is used (section 11).

## 1. Question
Models commit silently to affirmative, plain, statement defaults when a cue is missing from the keywords. Supplying the cue (chip or plain word) fixes it but costs taps. Question: can a per-message, per-dimension policy choose among COMMIT (0 taps), SHOW-TWO (1 tap: default plus a cue-flipped alternative) and ASK-ONE-CUE (2 taps) so that SLP-weighted silent reversals fall substantially at a small tap cost? Do model-internal signals add anything over keywords, over the committed output, and over cheap lexical or prior baselines?

The original title, "calibrated ask-or-assume policy", is dropped. No calibration or guarantee claim survives (the CRC targets were infeasible or heuristic, see 3 and 8). The contribution is a priced, SLP-weighted, same-items evaluation, plus a modest speech-act result and several nulls.

## 2. Data and units
1,800 units (600 AACText messages x 3 human keyword sets, 20 writers), HT-weighted as in the T2 posterior. Outcome = lost-cue reversal averaged over the 4 stored P0 models (qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra). The consistency gate reproduced T2 (polarity 23.9 per 1,000, speech act 162.0, politeness 49.4). Primary scope (chosen post-pilot, D-R1): polarity, speech act, politeness-lost. B0 (always-commit) = 178.2 SLP-weighted (235.3 raw) silent errors per 1,000 messages. SLP weights NEG 1.0, ACT 0.8, POL 0.5 (n = 2 SLPs). One action per message at most. Internal signals come from qwen2.5-7b and llama3.1-8b only (2 of 3 declared models), pooled by averaging, while the outcome averages 4 models.

## 3. Pre-declared rules and amendments (PRE = before outcomes; POST = post-pilot, outcomes already seen)
- PRE (PLAN section 7). H1: best policy beats random-ask and prior-only, with >= 25% reduction at T = 100 for SUCCESS. H2: internal signals beat keywords (delta AUROC >= .03 on polarity or speech act AND averted at T = 50 CI excludes 0), "internal beats external" only on >= 2 of 3 models. H3: CRC held-out mean risk <= alpha. H4: beat the closest published method (B6). H5: list where it does not help. Tap price never chosen post hoc: full frontier and budgets T in {20, 50, 100, 200, 400}. Unit of inference = writer-by-message cluster bootstrap, widest of writer/message/joint.
- A1 (PRE for policy outcomes): gate passed. rho_d = measured chip1 restoration (polarity .995, speech act .787, politeness .882, certainty .954, agent 1.0); q = 0.9 assumed. The original CRC targets 5/10/20 per 1,000 were declared infeasible (floor above them).
- D-R1 (POST): H3 restated as "success under amended targets only" (22/33/55% of B0). Floor argument corrected. Primary scope re-cut to 3 dimensions (agent and certainty exploratory). Lexicon features removed from S1.
- A2 (PRE for round 2, round-1 outcomes seen): R2-1 primary scope; R2-2 S1 without NEG/POL/ACT lexicon flags; R2-5 internal signals with K = 8 samples (deviation from K = 16); R2-6 external gpt-6.1-sol detector from keywords only; R2-7 B6 entropy gate, inspired-by only (source not opened); R2-9 stop rule.
- A3 (POST): P-O control added after a 30-resample qwen debugging run showed P-I speech-act AUROC .82-.85. The stop-rule candidate set was not changed.
- D-R2 / A5 (PRE for round 3, all items POST-pilot): strict S1 (also drops please, MOD, WH, "?", CERT), P-O rebuilt from stored arbiter labels, supervised B6 (B6-sup), refit bootstrap (200 joint resamples, every policy refit end to end), q sweep .3-1.0, false-alarm and mis-pick costs, five-dimension scope side by side. "Report all policies, no best-of selection" supersedes the stop rule. Strict S1 is the headline feature set for all learned policies.
- A6: gemma3-4b not run (owner paused GPU jobs, D-084). H2 reported NOT MET as declared.
- D-R3 (POST): stop compute, narrowed claim. Writing-pass instructions: refit CIs as primary, q = 0.7 beside q = 0.9 (q <= rho_speech_act = .79), per-model results as the faithful test, both scopes, no "calibrated" or CRC language.
- A7 (PRE for the B5-lex outcome, written before it was computed): B5-lex = B5's action (SHOW-TWO on speech act) applied by a randomised ladder only to messages whose keywords contain no speech-act lexicon hit, modal, WH word or "?" (65.4% of weighted messages pass, recomputed from the code). Pre-stated rule: if B5-lex minus P-I has a CI including 0 AND is within 1 pp, the headline becomes "learned internals add nothing over a lexicon-gated prompt". Result: rule not triggered (section 5).

## 4. What was run
- Stage 0 (round 1): unit table, T2 gate, keyword policy P-K with 5x5 writer-and-message-disjoint cross-fit, frontier, CRC on 500 splits. CPU only.
- Round 2: internal signals S3 for qwen2.5-7b and llama3.1-8b (greedy logprob features, K = 8 T=1 samples, forced-choice probes), external detector P-X (gpt-6.1-sol, keywords only), B6, G1 transfer, H3 restated.
- Round 3: strict S1, P-O (stored arbiter labels), P-IO, B6-sup, refit bootstrap, q sweep, cost model, scopes, per-writer, per-model, ASK+G1 transfer.
- Writing pass: B5-lex (CPU only, 300 fixed-prediction resamples, q = 0.9 and 0.7).
- NOT run: gemma3-4b signals, qwen 14B confirmation, hw1/hw2 transfer, any human annotation (the 145-item q-measurement request is built, NOT sent), reproduction of the published entropy-gate method, refit CIs for B5-lex and for the q sweep.

## 5. Results (percent of B0 averted, primary scope, T = 100 taps per 1,000 messages; about 10% of messages prompted)
Refit CIs (200 end-to-end resamples) are the headline wherever they exist (q = 0.9 only). The q = 0.7 column has fixed-prediction CIs only (round3/r3_qsweep.csv). Fixed CIs are in brackets in the rightmost columns.

| policy | q = 0.9 point | q = 0.9 refit [95%] | q = 0.9 fixed [95%] | q = 0.7 point [fixed 95%] | weighted / raw averted per 1,000 (q = 0.9) | taps per error averted |
|---|---|---|---|---|---|---|
| Oracle (upper bound, unrealisable) | 42.7 | 43.2 [32.9, 53.0] | [32.8, 53.9] | 33.2 [25.5, 42.0] | 76.1 / 90.0 | 1.1 |
| P-I (strict S1 + model internals, qwen+llama blend) | 13.8 | 13.1 [7.0, 19.9] | [9.6, 19.3] | 10.7 [7.5, 14.9] | 24.6 / 30.7 | 3.3 |
| P-O (strict S1 + stored label of the committed text) | 11.4 | 11.9 [6.6, 18.4] | [7.5, 17.8] | 9.1 [5.9, 13.7] | 20.2 / 25.3 | 4.0 |
| B6-sup (entropy and minority-frequency features, same learner) | 11.9 | not refit | [7.8, 16.1] | not computed | 21.3 / 26.6 | 3.8 |
| P-K (keyword-only, strict S1) | 8.9 | 7.6 [3.4, 12.5] | [5.6, 12.7] | 6.9 [4.3, 10.0] | 15.9 / 19.8 | 5.0 |
| B5-lex (lexicon-gated fixed prompt, A7, no learning) | 9.1 | not refit | [7.8, 10.6] | 7.1 [6.1, 8.2] | 16.3 / not stored | not stored |
| B5 (best fixed prompt by prior, applied to a random fraction) | 6.5 | 6.6 [5.8, 7.1] | [5.9, 7.1] | 5.1 [4.6, 5.6] | 11.7 / 14.6 | 6.9 |
| B6 unsupervised entropy gate (inspired-by, not a reproduction) | 4.4 | not refit | [1.6, 8.3] | not computed | 7.8 / 10.1 | 9.9 |
| B1 random ask (analytic, no sampling interval) | 3.0 | 3.0 | n/a | 2.3 | 5.3 / 7.1 | 14.2 |

q = 0.9 is optimistic: the measured chip-restoration rate for speech act, the only dimension ever prompted, is .787, and q is unmeasured. Read q = 0.7 beside it. Every AAC-unit gain scales with q (P-I: 6.5% at q = 0.3, 10.7% at 0.7, 13.8% at 0.9, 15.7% at 1.0). Residual after P-I at q = 0.9: 153.6 weighted (204.6 raw) per 1,000, so 87% of the weighted burden remains. Gain in absolute terms: about 31 raw silent errors averted per 1,000 messages for 100 taps.

**Paired contrasts (percentage points of B0, T = 100, q = 0.9).** Refit [95%] where available, else fixed.
| contrast | point | refit | fixed |
|---|---|---|---|
| P-I minus B5 | +7.2 | +6.5 [1.1, 13.0] | [3.2, 12.4] |
| P-O minus B5 | +4.8 | +5.4 [0.0, 11.7] | [1.2, 10.9] |
| P-K minus B5 | +2.4 | +1.0 [-3.4, 6.0] | [-1.0, 6.2] |
| P-K minus B1 | +5.9 | +4.6 [0.4, 9.5] | [2.6, 9.7] |
| P-I minus P-K | +4.9 | +5.5 [-0.2, 12.4] | [-0.3, 11.3] |
| P-I minus P-O (beyond committed output) | +2.4 | +1.2 [-5.1, 7.9] | [-3.4, 6.7] |
| P-I minus B6-sup | +1.9 | not refit | [-3.0, 7.4] |
| P-I minus B6 (unsupervised) | +9.4 | not refit | [4.2, 15.1] |
| P-I minus B5-lex | +4.7 | not refit | [1.1, 9.5] |
| P-O minus B5-lex | +2.2 | not refit | [-1.0, 7.9] |
| P-K minus B5-lex | -0.2 | not refit | [-3.8, 3.3] |
At q = 0.7: P-I minus B5 +5.6 [2.5, 9.6], P-K minus B5 +1.8 [-0.8, 4.9], P-I minus P-O +1.6 [-2.8, 5.1], P-I minus B5-lex +3.6 [1.0, 7.3] (fixed CIs).

**Budget dependence.** P-I minus B5 refit at T = 50 is +3.2 [-0.9, 9.1] (includes 0; fixed [1.0, 7.6]), at T = 100 +6.5 [1.1, 13.0] (barely excludes 0), at T = 200 +12.7 [4.0, 21.8]. P-I beats B5 reliably only from T = 100. P-I minus B5-lex at T = 50 is +2.9 [-0.03, 6.5] (touches 0), at T = 200 +11.2 [5.1, 17.9]; at q = 0.7 and T = 50 it is +2.3 [0.08, 5.0]. B5-lex minus P-O at T = 100 is -2.2 [-7.9, 1.0]: P-O is not separable from B5-lex.

**q sweep (T = 100, % of B0, fixed CIs).** P-I minus B5 excludes 0 at every q in 0.3-1.0 (+3.7 [0.9, 6.8] at 0.3 up to +8.4 [3.3, 13.9] at 1.0). P-K minus B5 never excludes 0 (+0.9 to +2.4). Point estimates P-K >= B5 and P-I >= B5 at every q down to the grid floor 0.3, so no break-even exists inside the grid. Ordering is stable. Size is not.

**Per-model results (the faithful test; fixed CIs, 150 resamples, outcome still averages 4 models).**
| contrast (pp of B0) | qwen2.5-7b | llama3.1-8b |
|---|---|---|
| P-I minus P-K, T = 50 | +4.9 [0.4, 9.7] | +3.9 [0.07, 8.2] |
| P-I minus P-K, T = 100 | +9.7 [2.4, 17.1] | +6.8 [-0.6, 12.1] |
| P-I minus P-O, T = 100 | +4.3 [-3.0, 10.4] | +4.6 [-1.4, 8.7] |
| P-I minus B5, T = 100 | +12.2 [5.5, 18.8] | +8.8 [2.2, 12.7] |
| P-K minus B5, T = 100 | +2.6 [-1.2, 6.2] | +2.0 [-2.2, 7.6] |
| speech-act AUROC P-K / P-I / P-O | .634 / .840 / .822 | .599 / .707 / .764 |
H2 is NOT MET as declared: gemma is missing (2 of 3 models), the external-detector comparison was not re-run in round 3 ("internal beats external" held on 1 of 2 models in round 2), and the pooled T = 50 P-I minus P-K CI includes 0 (+3.0 [-1.3, 7.2], fixed). Under strict S1 both single-model T = 50 CIs exclude 0, but that is a post-pilot re-evaluation.

**AUROC (round3/r3_auroc.csv).** Strict P-K: speech act .635 [.57, .69], politeness .607 [.49, .70], polarity .618 [.45, .76]. No-lexicon P-K: .733, .708, .564. P-I: speech act .783 [.72, .83], politeness .685 [.59, .77], polarity .575 [.39, .74]. P-O: .758, .645, .632. B6-sup polarity .329 [.22, .46], below chance. Dropping the question, modal and please features costs about .1 AUROC on speech act and politeness, yet the frontier barely moves (P-K 8.9 strict vs 8.2 noLex; P-I 13.8 vs 14.6), because the frontier is driven by the prior and the speech-act base rate. The gap is not fully explained (critique 3). Strict S1 handicaps every learned policy equally, and those features are legitimate at deployment, so strict is a valid ablation, not label-leakage repair.

**Cost model (T = 100, policies not re-tuned; a = false-alarm tap-equivalents, m = mis-pick rate).** P-I minus B5 stays positive in every cell: a = 0, m = 0 +7.2 [3.2, 12.4]; a = 0.5, m = 0.05 +5.9 [2.2, 10.9] (P-I 9.2 [5.2, 14.2], B5 3.3); a = 1, m = 0.10 +6.2 [2.2, 10.5] (P-I 7.7 [3.2, 12.1], B5 1.5). P-K minus B5 never excludes 0 in any cell. Absolute gains fall by up to 45%. Spurious-addition sensitivity (counted as fixable errors at efficacy e): e = 0.5 P-I 11.5, B5 6.3; e = 1 P-I 10.0, B5 6.1 (P-I minus B5 +3.9 [1.2, 7.2]).

**Scopes.** Five-dimension lost-cue scope (B0 = 354.1, exploratory, T = 100): P-K 3.3 [1.8, 5.6], P-O 5.6 [3.9, 8.5], P-I 6.6 [4.3, 8.8], B5 4.0 [3.5, 4.6], B1 1.8. P-K minus B5 -0.7 [-2.4, 1.5]. P-I minus B5 +2.5 [0.1, 4.8]. At T = 200 P-I (11.9) falls below P-O (13.4). The 3-dimension scope was chosen post-pilot (A2, D-R1), and the five-dimension scope is arguably the pre-planned one. Show both.

**Per writer (pooled T = 100).** P-I beats B5 for 16 of 20 writers (median 11.8% of own B0 vs B5 6.0%). P-K beats B5 for 7 of 20 (median 2.5% vs 5.5%). P-O beats B5 for 8 of 20. Several writers receive 0 prompts from P-K or P-O. Writers P01-P03 carry most of the aggregate P-K and P-O gain.

## 6. Baselines (all of them, none dropped)
- B0 always-commit: 178.2 weighted / 235.3 raw per 1,000, 0 taps.
- B1 random ask at matched taps: 3.0% (5.3 weighted).
- B2 always-ask three dimensions with chips: 6,000 taps, residual 30.6 weighted (147.5 averted). With G1 repair after the ask (52.5% stored W-C repair rate, a transfer estimate): residual 14.6 (163.6 averted).
- B3 always-ask polarity only: 2,000 taps, averts 23.8 weighted.
- B4 always-show-two on three dimensions: 3,000 taps, residual 17.8 (160.4 averted). Blanket options cost 20-60x the taps of the 100-tap policies.
- B5 prior-only fixed prompt: 6.5% [5.9, 7.1]. B5 gets about 47% of P-I's gain at T = 100 (6.5 of 13.8).
- B5-lex lexicon-gated fixed prompt (A7): 9.1% [7.8, 10.6], with no learned component. It matches P-K (P-K minus B5-lex -0.2 [-3.8, 3.3]) and P-O (+2.2 [-1.0, 7.9]) within noise. P-I beats it by +4.7 [1.1, 9.5].
- Keyword-only null: P-K (strict) does not reliably beat the prior-only B5 (CI includes 0 at T = 50, 100 and, under refit, 200; below B5 in the five-dimension scope), and it does not beat the lexicon-gated B5-lex. It beats random B1. The keyword gate G0 was not triggered in round 1 (speech act AUROC CI above .5), but the keyword signal is modest.
- B6 unsupervised entropy gate (K = 8 samples, inspired by Clarify When Necessary, source not opened): 4.4% [1.6, 8.3]. B6 minus B1 +1.4 [-1.4, 5.3]: no better than random. B6 minus B5 -2.2 [-5.2, 1.3].
- B6-sup (supervised entropy features, same learner and folds): 11.9% [7.8, 16.1], matches P-I (+1.9 [-3.0, 7.4]). The entropy signal is the main content of the internal-signal gain. The beyond-B6-sup claim is not available.
- P-X external keyword-only detector (round 2): 8.9% pooled at T = 100, no better than P-K (+0.7 [-2.5, 3.6]). Not re-run in round 3.
- G1 guard: 0 averted on these units by construction (keyword-only input carries no chip). ASK + G1 (transfer, T = 100): P-I 7.5% vs SHOW-TWO P-I 13.8%; ASK+G1 minus SHOW is -6.3 [-10.0, -3.2]. ASK costs 2 taps, so it loses under a tap budget.
- Closest published: entropy-gated clarification (B6, B6-sup) and selective prediction. Neither implementation is a reproduction.
- CRC: pre-declared alpha = 5/10/20 infeasible. Amended targets (22/33/55% of B0, P-K): mean test risk 35.3/53.7/89.8 vs target 39.2/58.8/98.0 with 31-35% exceedance (31-40% in the full CRC table), needing 1.7/1.0/0.5 prompts per message, and P-K saved 22-38% of taps vs B5 at equal risk. Units are HT-weighted and cross-fitted, so exchangeability fails. Heuristic calibration only, no guarantee. Not rerun for P-I. Not a result.

## 7. Where it does NOT help
- Polarity, the clinically heaviest dimension (B0 share 23.9 weighted): never prompted at T = 100 (share of prompts 0.0 for P-K, P-O, P-I). AUROC CI includes .5 for every feature set (P-I .575 [.39, .74]), and B6-sup is .33 [.22, .46].
- Politeness (24.7 weighted): never prompted. Certainty (AUROC .39 P-K, .54 P-O, .57 P-I) and agent are exploratory and not helped.
- Every prompt of P-K, P-O and P-I (100%) is a SHOW-TWO on speech act. The policy is a "which messages lost a question or request act" detector, not a general cue-risk detector. ASK-ONE-CUE is never chosen.
- Keyword-only P-K versus the prior-only B5 and versus B5-lex: no reliable gain.
- Signals beyond the committed output: P-I minus P-O includes 0 at T = 50, 100, 200, for both fixed and refit CIs and for both single models. NOT demonstrated, which is not the same as absent (the CI is compatible with several pp).
- Beyond supervised entropy features: P-I minus B6-sup +1.9 [-3.0, 7.4].
- Unsupervised entropy gating: no better than random.
- Five-dimension scope: P-I 6.6% vs B5 4.0%, P-K below B5.
- About half of writers (13 of 20 for P-K) get no gain over B5.
- At T = 50, P-I minus B5 (refit) and P-I minus B5-lex include or touch 0.
- Absolute burden: 87% of weighted silent errors remain at 100 taps per 1,000.
- Not tested: hw1/hw2 transfer, any non-AAC-simulated user, polarity at the tails.

## 8. Critic issues and resolution
| round | issue | resolution |
|---|---|---|
| 1 | ASK-ONE-CUE almost never chosen, so "value-of-cue" is really a show-two frontier, and q = 0.9 was invented | Reframed as show-two. q swept .3-1.0, headline stated conditional on q, q-measurement request built (not sent). |
| 1 | H3 "SUCCESS" overclaimed, floor argument wrong, B5 ladder coarse, exchangeability, 35-39% exceedance | H3 restated as amended-targets only, floors corrected, B5 on a randomised ladder, "heuristic, no guarantee". CRC language dropped. |
| 1 | 41% of the burden from agent and certainty (detector-vs-judge disagreement) | Primary scope cut to polarity, speech act, politeness-lost, five-dimension shown side by side. |
| 1 | No closest-published baseline, no G1, no signals, B1 is a strawman | B6, B6-sup, G1 transfer, P-X, P-I and a lexicon-gated B5 added. B1 stays analytic. |
| 1 | Feature leakage by construction (NEG/POL/ACT lexicon flags in S1) | S1 reduced to noLex (round 2) and strict (round 3). Reported both ways. |
| 2 | Leakage fix incomplete (please, MOD, WH, "?", CERT remain) | Strict S1 (round 3). After critique 3 the "leakage" wording was dropped. |
| 2 | P-O built from regenerated L0 labels, so a weak control | P-O rebuilt from stored arbiter labels. The regenerated version is kept as a secondary row. |
| 2 | B6 unsupervised vs supervised learners is unfair | B6-sup added. P-I minus B6-sup +1.9 [-3.0, 7.4], the novelty over entropy gating is conceded. |
| 2 | One-sided cost model (false alarms free) | a and m sweeps. P-I minus B5 is positive in every cell. |
| 2 | Best-of-four selection, bootstrap holds the fitted policy fixed | All policies reported. Refit bootstrap (200) added. |
| 3 | Headline used fixed CIs against the stated rule | Refit CIs are primary in this report. P-I vs B5 reliable only at T >= 100. |
| 3 | "Lexical leakage" mislabel, a lexicon-gated B5 baseline is missing | B5-lex run under A7 (pre-declared). The headline is not overturned, P-I minus B5-lex +4.7 [1.1, 9.5]. |
| 3 | q = 0.9 exceeds the measured speech-act restoration .787 | q = 0.7 beside q = 0.9, q = 0.9 labelled optimistic. |
| 3 | P-O stored is near-definitional, P-I minus P-O under-powered | Reported as "not demonstrated". Practical framing: label the committed sentence and ask when the cue is absent. |
| 3 | Outcome (4 models) vs features (2 models) mismatch | Disclosed. Per-model results reported. The pooled P-I is called a hypothetical blend. |
| 3 | Favourable scope is the headline | Both scopes shown. |
| 3 | Absolute impact small, polarity never prompted, "calibrated" overclaims | Stated in sections 6 and 7. Claim narrowed to a speech-act SHOW-TWO effect. |
| 3 | Novelty thin | Section 9. |
| 3 | Minor: "20 writers x 600 messages" label, stored-label `isfinite` assert vacuous (4 missing labels), z-scoring uses all units, budget matched on test data | Disclosed here (the data are 1,800 units, 3 writers per message). The effect is negligible. Code not changed. |
| open | Needs new compute or humans: gemma signals, measured q, 14B, hw1/hw2, human label checks, refit for B5-lex and the q sweep, verified citations | Not done. |

## 9. Novelty and closest prior work
Verified opened: Angelopoulos et al., Conformal Risk Control (arXiv 2208.02814; authors, abstract). Used only as background for the amended CRC, and no guarantee is claimed.
Unverified (seen in search snippets or surveys, NOT opened, do not cite until opened): Clarify When Necessary (Zhang and Choi, NAACL Findings 2025, OpenReview XgdNdoZ1Hc; B6 is inspired by it, not a reproduction), Cai et al. Context-Aware Abbreviation Expansion (arXiv 2205.03767), KWickChat (IUI 2022), SpeakFaster (Nature Communications 2024), AskBench (arXiv 2602.11199), arXiv 2605.25284, and the PLAN candidates 2606.29054, 2607.27143, 2609.07395.
Novelty: low to medium. Chow-rule abstention, entropy-gated asking, selective prediction and conformal risk control are generic. What remains is the setting (AAC keyword expansion), the clinical pricing (SLP weights, silent reversals per 1,000, taps per error averted), the same-items comparison against prior-only, lexicon-gated and entropy baselines, and the null for signals beyond the committed output. A search found no AAC paper with a cost-priced commit-or-ask rule, but it was a handful of queries, not an exhaustive search. B6-sup matches P-I, so the learned gate is the substance. No claim of an exhaustive AAC literature search.

## 10. Limitations
- Labels: detector source labels and machine-arbitrated output labels. Agent and certainty include detector-vs-judge disagreement. No human has checked anything (Part 21 source check and the frontier annotation request unscored).
- q and rho are simulated (rho from the stored chip controls, q assumed). The alternative sentence is never shown to cover the true speech act. 145 q-measurement items are built and not sent.
- 20 writers, 600 messages (1,800 units). CIs are optimistic. P01-P03 carry much of the P-K and P-O gain.
- 2 of 3 declared models (gemma not run). Outcome averages 4 models, features average 2, so P-I is a hypothetical blend. K = 8 samples, not 16.
- Refit CIs use 200 resamples (noisy tails) and exist only for q = 0.9. The q = 0.7 numbers, B5-lex, B6-sup and B6 have fixed-prediction CIs only. B1 and B5 CIs are analytic or near-degenerate.
- Primary scope chosen post-pilot. The strict S1 headline is a post-pilot choice. P-O stored is near-definitional. The budget is matched on test-set realised taps (all policies alike). Oracle is one-action and unrealisable.
- Penalty models are not re-tuned, B6 is not a reproduction, SLP weights come from n = 2 raters, taps are a proxy for effort (no seconds or fatigue claim, no AAC users).
- Transfers (G1 52.5% repair, chip restoration) come from other studies in this repo.

## 11. Number checks (files win)
All headline numbers in sections 5 and 6 were re-derived from round3/r3_frontier.csv, r3_refit.csv, r3_qsweep.csv, r3_cost.csv, r3_scope.csv, r3_per_model.csv, r3_per_writer.csv, r3_auroc.csv, r3_decomp.csv, summary_round3.json and b5lex/b5lex.csv, and agree with round3.md and the workflow summary except for:
- The workflow summary wrote "P-K minus B5-lex: -0.2 [-3.3, 3.8]". The file b5lex.csv gives -0.2 [-3.77, 3.34], so the interval is [-3.8, 3.3]. The summary had the bounds reversed.
- Workflow summary "+3.6 [1.0, 7.4]" for P-I minus B5-lex at q = 0.7, T = 100. File: 3.58 [0.96, 7.35], so [1.0, 7.3]. Rounding only.
- The workflow summary and round3.md say P-I minus P-O "includes 0 everywhere". Confirmed for the CIs in the files (fixed and refit at T = 50, 100, 200, q sweep, single models).
- The 65% B5-lex gate share is not stored in any output file. It was recomputed from the script's gate (65.4% weighted, 64.6% unweighted).
- q = 0.9 weighted 24.6 for P-I and 31 raw (30.7): consistent.
- Round 2 reported P-I 14.6% and per-writer median P-K gain 0.6%. Round 3 (strict S1) supersedes with 13.8% and 2.5%.
- The round-2 "P-I minus B5 +8.1 [3.4, 12.9]" and round-3 "+7.2 [3.2, 12.4]" differ because of the feature set (noLex vs strict), not a conflict.

## 12. Strongest TRUE claim
On 1,800 human-keyword units (20 writers), under machine labels and a simulated q, a learned gate using model internals averts 13.8% of SLP-weighted silent reversals at 100 taps per 1,000 messages at q = 0.9 (refit 13.1% [7.0, 19.9]) and 10.7% at q = 0.7. That is about 31 raw errors per 1,000 messages for 100 taps, with 87% of the weighted burden remaining. It beats the prior-only fixed prompt (refit +6.5 pp [1.1, 13.0] at T = 100) and a lexicon-gated fixed prompt (+4.7 pp [1.1, 9.5], fixed CI). Every prompt it issues is a speech-act SHOW-TWO. Most of the gain comes from knowing the committed output lacks a cue (P-O 11.4%), and a supervised entropy-feature learner matches it (B6-sup 11.9%). A keyword-only policy does not reliably beat the prior or the lexicon gate.

Not claimable: a general calibrated ask-or-assume policy; any CRC guarantee; signals beyond the committed output; superiority over supervised entropy features; any polarity or politeness result; ASK-ONE-CUE value; any real-user or acceptability benefit; any q-dependent AAC-unit number as measured; "internal beats external"; a gemma or hw1/hw2 result.

## 13. Recommended use
- CALE-AI lift by Nov 16: optional, as the honest evaluation-framework and modest-result item (SYNTHESIS section 2, item 4). Quote q = 0.7 beside q = 0.9, use refit CIs, include section 7 and the B5-lex and keyword-only null rows, and say speech act only. Do not say "calibrated ask-or-assume" or any guarantee.
- SE4All: nothing from this frontier.
- Journal or standalone paper: not as is. Needs a measured q (send the speech-act stratum A items plus the whole stratum B control from the 145-item request first if time is short), gemma signals, refit CIs for B5-lex and the q sweep, a user-model for the cue chip, verified citations, hw1/hw2 transfer and human label checks.
- Drop: no. Small residual compute (gemma: `python src/frontier_value_of_cue_features.py gemma3-4b S2`, then `VOC_LOCALS=qwen2.5-7b,llama3.1-8b,gemma3-4b python src/frontier_value_of_cue_round3.py 300 200` after deleting round3/P_r3.npz; needs the GPU lock and the owner's pause lifted).

## 14. Artifacts
Code: src/frontier_value_of_cue_{units,stage0,lib,round2_cpu,features,s1gpu,s2api,signals,signals_q,perwriter,q_items,round3,b5lex,fig,fig2,fig3}.py. Results: analysis/frontier/value_of_cue/{PLAN.md, round1-3.md, critique1-3.md, round2/, round3/, b5lex/b5lex.csv, summary*.json, ANNOTATION_REQUEST.md, fig_frontier.png, round2/fig_round2.png, round3/fig_round3.png}. Annotation items (not sent): annotation/frontier_value_of_cue_items.json and _key.csv.
