# partner_context, critique round 3 (methods/statistics + novelty)

Verdict: valid = true (no fatal issue). Round-2 fatal and major items are mostly addressed: C1 leads with the unfiltered figure, the filter is labelled a lower bound, "equivalent" is gone, the q grid reaches 0.9, and oracle designs are relabelled. Several claims are still too strong for a journal. I did a document-level audit and a web novelty check; I did not re-run the bootstrap.

## Major
M1. The "zero-tap mitigations do not beat matched-tap random ask" claim uses inconsistent comparators.
- At q=0.9, M4-bare (zero taps) is said to beat "matched random ask" (205 vs 255). A matched random ask for a zero-tap policy asks nothing, so it equals always-commit. The comparator there is the random ask at M5b's tap rate, not M4's.
- Every benchmark verdict is a function of the invented q. The REPORT says no prevalence was measured, so the policy ranking (always commit best at q=0.1, ignore best at q=0.9) is a restatement of the assumption. The abstract's "where it matters" has no empirical basis.
- Fix: one tap-vs-error frontier per q, each policy at its own taps. Drop the sentence or define "matters".

M2. The decomposition has weak precision and is over-read.
- The control shows the judge labels 32% (19/60) of affirmative outputs non-INDEPENDENT. Fabrication in the negations is 19% against 18% in the control, so the fabrication class is not distinguishable from judge noise. Paraphrase is 50% against 13%.
- The 15 unresolved units are counted as PARAPHRASE, which inflates the headline share (56 of 142 = 39% without them).
- The "about 4.4 / 1.7 / 2.7 pp" attribution multiplies the class shares by the pooled effect. It does not subtract the control's false-positive rate. Keep it out of the abstract and REPORT until Part A returns.
- The echo and agreement split behind "28 of the 36.7 points are echo" rests on the same unvalidated machine judge (72-93% agreement in round 2).

M3. Author dependence is under-addressed. The round-2 request was a second author on all families. Only 40 families have it (one more author on 40). The conservative +4.2 comes from one weaker author on 40 families. Turn-author generalisation remains unproven, and the abstract line "(6.8 on cleaner forms, 4.2 with a second author)" mixes subsets with different denominators.

M4. Unexplained number drift. Author subsets moved from +9.8/+4.8 to +9.2/+4.2, and the pooled C2 all-negation moved from 37.1 (my round-2 check) to 36.67. The report says the reason was "not traced". Untraced shifts of 0.4 to 0.6 pp in a shared pipeline can be a denominator or row-dropping change (rows with a missing J label are dropped). Trace this before journal use. The REPORT also treats my round-2 sensitivity bounds (36.8 and 38.4, from flipping all arbiter units) as a "director range" to reproduce. They were not a reproduction target.

M5. The G1 gain is weakly supported.
- The arbiter-only contrast is one rater (the same assistant that built the analysis, aware of the study), and agreement with the judge final label is only 75% on chip texts. A 75% agreement rate means label noise of the same size as the -9.7 effect.
- Only changed texts were relabelled. Unchanged pairs keep the original labels, which is correct for the contrast, but the CI comes from 182 changed pairs of 3,120 and bootstrap over families, which is thin.
- The "weighted x5" figures (-77, -49, -508) carry no information beyond the unweighted ones and should be dropped (my round-2 point, not applied).
- G1 gain "survives with non-gpt labels" is overstated. Call it provisional until a non-author human labels the 350 texts.

## Minor
- C1 symmetric filter: 5 arm-0 outputs, a counterfactual-turn echo judgement on no-turn text. The report says so. Do not present it as a validated filter.
- The A10b narrowing (arm-0 judging scoped to intent-affirmative cells) was written before outcomes, so it is declared, not a violation.
- The logprob gate was dropped "because no new generation was allowed". For the three local models a short re-score or rerun under the GPU lock is feasible; the missing entropy-gated baseline is the strongest-baseline gap remaining. Prior art on confidence-gated asking exists (the W19-1706 paper on partner ASR confidence in AAC).
- The gate benchmark's lexicon is the definition of the X frame. Credit against frame-blind random ask is near-definitional (the report already says so). The asked cells use the oracle chip.
- The C1 estimates are against an arm-0 baseline of about 2.4 pp. The "+-5 pp" margin widened after the pilot is retained as a label. The report correctly refuses to call it equivalence.
- Pooling is an unweighted mean of 4 models (one gpt model not exactly reproducible at T=0, no replicate). Per-model values are shown, which is right. Exploratory contrasts (about 20) lack a multiplicity statement beyond Holm on 3.
- Turns are model-authored templates, polarity only. The 130 families are not a sample of AAC traffic, so no per-1,000 clinical figure is supportable, as the report states.

## Novelty (search 2026-11-03)
Searches for partner-turn context in AAC (KWickChat, IUI 2022; Cai et al., NAACL 2022; COMPA, CHI 2024; Partner ASR context, W19-1706) found no measurement of echo, polarity reversal or partner-driven commitment. Absence in this search is not proof. COMPA's finding that the relevant context is often not the partner's last turn is the strongest published motivation for the paper's concern and should be cited. Echo/instruction-context conflict is general-LLM literature (Zhou 2407.13048, Camassa and Shiller 2605.20382, Farahani 2601.12075). The AAC-specific contribution is the commitment attribution under a supplied cue; the cue-supplied result itself is the trivial part.

## What stands
- Bare channel, X turn: a large negation excess in 4 of 4 models (+36.7 all, +8.7 narrow, author- and form-dependent from +4.2 to +9.2).
- With a cue: +7.05 [5.26, 9.04] unfiltered, 1.2-1.5 filtered lower bound.
- Zero-tap fixes do not help relative to random asking at low q.
- Polarity labels are robust to J1/J2 (36.5-36.9).

## Next steps
1. Fix the comparator in the M4/M5 claims; plot tap-vs-error frontiers across q.
2. Trace the 0.4-0.6 pp drift, or report both numbers.
3. Remove weighted x5 columns and the class-share attribution; count unresolved separately from PARAPHRASE.
4. Add a logprob/entropy-gated ask for local models under the GPU lock.
5. Run the human Part A/B and have non-author annotators label the 350 G1/chip texts.
6. Second turn author on all 130 families, or state the limit in the abstract.
