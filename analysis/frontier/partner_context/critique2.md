# partner_context, critique round 2 (methods/statistics + novelty)

Verdict: valid = true (no fatal issue). The round-1 fatal problems are fixed: echo is measured and the no-turn baseline is used. Several headline readings are still too strong and need re-wording before journal use.
Checks I re-ran on runs/frontier_partner_context_r2/scored.parquet and echo_labels.jsonl:
- Polarity-label sensitivity. Pooled bare X-turn negation, intended-affirmative cells, is 37.1% with the final labels, 36.9% with J1 only, 37.2% with J2 only, 36.8% if all arbiter units are set to "not negated", and 38.4% if all are set to "negated". The 25 arbiter units in these cells (243 over the whole file) do not drive the result.
- A random draw of "propositional" negated bare outputs (read by me, 14 shown).

## Major
M1. The C1 "equivalent / negligible" verdict depends on a filter that is not validated and is asymmetric.
- C1 counts only outputs with echo=no and reply=no (+1.2 [0.2, 2.2]). With a [YES] cue, any negated output reaches the partner as a reversed message, whether or not it echoes or agrees. In AAC terms that is harm.
- The same file reports the unfiltered version as +7.1 [5.2, 9.0]. Its upper CI is above the +-5 margin, and the whole interval is above 0.
- So the supportable statement is "somewhere between 1 and 7 pp, depending on an unvalidated machine label". "Equivalent within +-5" is not supported.
- Under the original +-2 margin (PLAN section 4), the filtered CI [0.2, 2.2] fails equivalence as well.
- The filter is also applied asymmetrically. Turn cells use wrong_prop (echo/reply removed). Arm 0 uses wrong_all because the echo flag is undefined there (A9).
- The +-5 margin was widened from +-2 after the pilot (D-R1). It is about twice the 2.4 pp baseline of 24 per 1,000, with no clinical justification.
- Fix: lead with the upper bound. Call the filtered number a lower bound. Report equivalence only after the human Part B check.

M2. "Propositional" is not independence from the partner.
- In my sample of 14, most "propositional" negations carry the partner's claim in new words:
  - "Your plan to visit your sister didn't materialize" -> "I didn't get to visit my sister."
  - "No prescriptions were delivered today" -> "Pharmacy did not deliver."
  - "Not meeting at the park today" -> "I don't plan to meet you now."
- Others are fabrications: "Your login attempt didn't pan out" -> "I don't remember my password"; "Your request didn't go through" -> "The clerk doesn't understand."
- Xb makes up 67 of 142 such outputs and Xc 49, against Xa 26. The echo/propositional split therefore partly measures the lexical form of the turn.
- The +8.7 pp C2 contains paraphrase-of-partner (arguably licensed), fabrication (harm) and partner-independent errors, all in one number. Report the three classes separately after the human check.
- Xa turns themselves are defective in places (e.g. "No visitors ever closed this place"). Only 39% of Xb turns pass the checker, and ITT keeps them.

M3. The C2 estimate is author-specific, and the CIs ignore author and turn variance.
- Resampling is over families only. Turns are one realisation per family from one authoring model.
- On the 40 shared families the effect is +9.8 with mistral-authored turns and +4.8 with qwen14-authored turns, about half. That spread is larger than the CI width.
- Treat turn-authoring as a random factor. Use at least two authors on all families, or widen the CI and say so.
- Pooling is the unweighted mean of 4 models, three of them 4-8B. Per-model values range from +3.9 to +13.1 (terra at +3.9, llama at +13.1). Present the per-model values as the result.

M4. The policy benchmark mostly restates its own assumptions.
- The X-frame table assumes intent is negated for 90% of messages (q = 0.1). "Ignore partner" is then 892 wrong per 1,000 by construction.
  - The q grid stops at 0.5. The case where the partner's remark is usually wrong (q about 0.9) is missing.
  - That case is the interesting one for contamination, and bare context-following would be worst there.
- The chip and word arms hand over the answer: a cue on every message, 1,000 taps per 1,000. They beat no-cue policies because the cue is the intent.
  - They are an oracle-style upper bound, not an AAC mitigation, and should not be presented as the mitigation result.
  - The only real zero-tap or low-tap candidates (M4 bare, M5a, M5b) all fail.
- The selective-ask baseline is weak. M5b asks when the turn changes the output. At q = 0.1 that is exactly when the output (negated) is already mostly right, so M5b is worse than random-ask by design.
  - A fair strong baseline is "ask iff the turn contains a negation frame", or ask iff the committed polarity disagrees with the arm-0 default and the partner turn is a statement.
  - Add it, along with an entropy or logprob ask rule, which the repo already has elsewhere.
- Weighted figures are the unweighted figures times 5, so they add no information. "SLP weighted" for a single dimension with one weight is cosmetic.
- G1 vs chip is -15 per 1,000 [-22, -10]. G1's checker and the polarity judges are the same gpt family, so this gain is partly self-agreement. G1 also sees only supplied cues.
- Echo/reply flags are used for wrong_prop in turn cells only (see M1). Say which version each table column uses.

M5. C3 is not interpretable as stated.
- The effect is -6 pp. Abstention (13% for qwen) drives it, with a topic-locked Q that only 72% of turns pass the checker.
- The verdict "INCONCLUSIVE" is correct, but the text calls the direction "opposite to H3". That is over-read. The metric is the share of outputs labelled affirmative, and abstention counts as non-affirmative.
- Report committed-affirmative among committed outputs next to it.

## Minor
- Arbiter (Claude, in the session that wrote the analysis) rules were written while viewing items (A9). My check shows they do not move C2. Three r2g items were labelled inconsistently before the rule existed.
- Terra is non-reproducible at T=0 and has no replicate. The writer-cluster check was not run.
- Examples: the rule is declared, but the chosen cell (bare|Xa, negated) is the echo-heavy one. Add a propositional-class example by the same rule. Include fabricated-content examples, since they are real harm.
- Holm covers 3 contrasts, but the report also runs about 20 forms, models and sensitivity contrasts. Label all of those exploratory.
- A9 documents execution deviations honestly (terra rerun from cache, judge assembled runs). I found no hidden outcome-based drop.

## Novelty
- Search 2026-11-03 (CHI 2023 "The less I type, the better", COMPA CHI 2024, Predictive Anchoring arXiv 2408.11140, Google TDCommons) turned up partner-turn-as-context for AAC. None of them measures echo, partner-driven wrong commitment, or polarity reversal.
- That agrees with "not found". It is still not a proof of absence. Also check SpeakFaster / Cai et al. 2023-24 follow-ups and KWickChat before claiming novelty.
- The echo vs instruction-context-conflict literature (Zhou 2407.13048, Camassa and Shiller 2605.20382, Farahani 2601.12075) is general LLM work. The AAC-specific contribution would be the commitment attribution plus the cue-supplied result. The cue-supplied result itself is the trivial part.

## What stands
- Bare, X turn: the share of outputs that take the partner's negation is large (+36.7 all, +8.7 narrowly) and appears in 4 of 4 models.
- With a cue supplied, the harm is small: 1.2 filtered, 7.1 unfiltered.
- Zero-tap mitigations do not help.
- The round-1 headline is correctly withdrawn.

## Requested before journal use
1. Re-state C1 with the unfiltered number as primary and no "equivalent" label until the human check.
2. Split "propositional" into paraphrase-of-partner, fabrication and independent classes, using the human Part A labels.
3. Add a second turn author on all families, or add author as a random effect.
4. Extend the q grid to q = 0.7, 0.9. Add a negation-frame-gated ask baseline and a logprob-gated ask baseline at matched taps. Describe chip and word as oracle upper bounds.
5. Check G1 with a non-gpt checker, or drop the G1 gain claim.
