# Critique, round 3 (value_of_cue) -- adversarial methods/statistics + novelty

Verdict: valid = true (no fatal issue). The round-3 write-up is unusually candid. The remaining problems are framing and baseline strength, listed below. None invalidates a result, but several must be fixed before any journal claim.

## Major
1. Headline CI contradicts the stated rule. round3.md says the refit CI is the headline whenever it differs from the fixed CI. The headline table still shows fixed CIs. For P-I at T=100, fixed is [9.6, 19.3] and refit is [7.0, 19.9]. P-I minus B5 at T=50 under refit is [-0.9, 9.1], which includes 0. P-I minus B5 at T=100 under refit is [1.1, 13.0], barely excluding 0. The refit B5 interval is narrow only because B5 depends on the prior alone. Use refit CIs in the table and say that P-I beats B5 reliably only at T>=100. The refit interval uses 200 resamples, so its tails are noisy.
2. "Lexical leakage" is a mislabel, and strict S1 handicaps every learned policy. The outcome r is defined as "source has the cue AND the keywords LACK it AND the output lacks it". Features such as "?", WH, MOD and "please" in the keywords therefore mark units that are deterministically not lost. They are available at deployment and are legitimate conditioning information. They are not label leakage. Removing them lowers speech-act P-K AUROC from .733 to .635.
   - The strict headline therefore understates what a hand-written rule achieves.
   - It also leaves a natural baseline out: B5 restricted to messages whose keywords do not already contain a question or request cue, which is a zero-learning lexicon gate.
   - B5 is applied to a random fraction of all messages, so it is a weak straw baseline. P-K minus B5 is not significant, and this leaves P-K's value understated.
   - Strict is a valid ablation. Report the noLex or full S1 frontier and the lexicon-gated B5 as a co-primary comparison, and drop the "round-2 AUROCs were partly leakage" wording.
   - Odd detail: a 0.1 AUROC drop produces nearly the same frontier (8.9 vs 8.2). Explain it, for example top-10% ranking versus overall ranking.
3. q = 0.9 exceeds the measured restoration of the same action. The SHOW-TWO alternative is the cue-flipped sentence. The only prompt ever chosen is a speech-act SHOW-TWO, and the chip-restoration rate for speech act measured in this study is rho = .787. So the effective q for the headline action is bounded near .79 times the pick probability, not .9. At q = .7 P-I is 10.7%, not 13.8%. The q = .9 headline is optimistic. Headline at q = rho_speech_act or at the lower end of the sweep, and state that every AAC-unit figure scales with q.
4. P-O stored is near-definitional and not a zero-cost comparator. r contains "stored output lacks the cue", and P-O feeds that same arbiter label in as a feature. The tests "P-I minus P-O" and "P-IO minus P-O" are under-powered (P-I minus P-O +2.4 [-3.4, 6.7]). Writing "NOT demonstrated" is correct, but the CI is also compatible with a gain of several pp, so do not conclude "no signal beyond output". Also, labelling the output needs a labeller (an L0 lexicon or a judge call), so it is not free. The practical finding is that "label the committed sentence, ask when the cue is absent" gets about 80% of the gain without logprobs. Frame it that way.
5. Outcome and feature models are mismatched. The outcome is the mean over four models (including gemma and gpt-6.1-terra). P-I and P-O features come from only qwen and llama, averaged. A deployed policy reads its own model's internals and output. The per-model analysis is the faithful test and is given only at T=50/100 with 150 resamples. The pooled headline describes a hypothetical blend. Lead with per-model results or restrict the outcome to the feature models.
6. The scope was chosen post-pilot and the favourable scope is the headline. Primary scope drops agent and certainty. The five-dimension scope gives P-I 6.6% vs B5 4.0%, and P-K is below B5. Present both side by side in the abstract, not only in an "exploratory" section.
7. Absolute impact is small and one-dimensional. 13.8% of B0 means about 31 raw reversals avoided per 1,000 messages, with 87% remaining. The policy never prompts polarity, the clinically heaviest dimension; its AUROC CI includes .5 and B6-sup is .33. "Calibrated ask-or-assume policy" overclaims. It is a speech-act question/request-loss detector.
8. Novelty is thin. A search in this review finds general work on when to ask: Clarify When Necessary (Zhang and Choi, NAACL Findings 2025, entropy gate with a budget on the top b%), AskBench and Learning to Ask. No AAC work turned up in that search, but it was a single query.
   - B6-sup matches P-I (+1.9 [-3.0, 7.4]).
   - The learned logistic gate over entropy features is the substance, and that is close to selective prediction with a coverage budget.
   - Before submission, search again for AAC-specific work (SpeakFaster, KWickChat, Cai et al.) and open the sources.

## Minor
- Title says "20 writers x 600 messages". The data are 1,800 units with 74-114 units per writer, and each message has 3 writers. Fix the label.
- The tap budget T is read off the ladder using the evaluation data's realised taps. This is standard but is budget-matching on test data, and the same applies to all policies.
- Feature z-scoring uses all units (a transductive step, negligible).
- Stored-label construction (rawS) uses `.eq()` on possibly missing labels, so the `isfinite` assert is vacuous. Missing labels are 2 for qwen polarity, 1 for qwen speech act and 1 for llama polarity. The effect is negligible, but fix it.
- B1 and B5 CIs are analytic or near-degenerate. B1 has no CI in the table.
- Gemma was not run (2 of 3 models), and H2 is correctly reported as NOT MET.
- Only Angelopoulos et al. was opened and verified; keep the other citations marked unverified.
- The figure and diagram requirement for journal readiness is unchecked here (fig_round3.png not visually reviewed).

## Not found
No leakage of outcome labels into S1-strict or B6-sup features. The cross-fit is writer-group and message-group disjoint, and there is no hw2 peeking. All policies are reported without best-of selection, and the deviations are logged. The claims actually made are conservative.

Sources searched: [Clarify When Necessary](https://openreview.net/pdf?id=XgdNdoZ1Hc), [Knowing but Not Showing](https://arxiv.org/html/2605.25284v1), [AskBench](https://arxiv.org/html/2602.11199v1).
