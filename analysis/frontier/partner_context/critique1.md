# partner_context, critique round 1 (methods/statistics + novelty)

Verdict: valid = false. Two fatal construct problems affect the headline claims. The pilot is still useful as a feasibility check, and the gate numbers are fine.
Re-checks were run on runs/frontier_partner_context_e0/scored.parquet and turns.jsonl. Novelty was not re-searched here, so the literature section is unverified by me.

## Fatal
F1. The headline override rate (terra 54%, qwen 12%) mostly measures echo of the turn's evaluative phrase, not a polarity flip of the user's proposition.
 - Terra chip, X turn, [YES]: 14 of 26 outputs are labelled `negated`. 12 of the 14 contain "did not / didn't work out" ("Yes, using cream at breakfast did not work out.", "Yes, the clinic call didn't work out."), copied from the X template "I heard {topic} did not work out".
 - Only 2 of 14 (hw-pol-003 "couldn't go"; hw-pol-060 "did not accept cash") are propositional negations. If echoes are excluded, the terra override is about 8% (2/26), not 54%.
 - Qwen chip: 3 of 3 overrides are the echo phrase. Qwen bare X: 18 of 20 `negated` outputs contain the echo phrase, and most begin "I heard ...", so they repeat the partner's sentence.
 - "worked out / did not work out" is an outcome evaluation, a different proposition from the user's event. The judge scores polarity of the critical dimension only (caveat 2 admits this but still headlines the number as polarity override).
 - The X template also leaks the lexical negation, so "frame-following" and "lexical copying" are confounded. The planned X' control (E3) is what separates them, and it has not been run.
 - Consequence: the claims "the chip is overridden by context" and the AAC conversion (120-540 reversals per 1,000, 600-2,700 weighted) are not supported as stated.
F2. "[YES]" after a partner remark that says "did not work out" is legitimately ambiguous: it can mean "yes, that is right, it did not work out". Calling "Yes, X did not work out" an override of the cue is therefore partly a design artifact. The same applies to [NOT] after the D turn.
 - Reply-to-turn is a valid reading of the user's intent in these cells, so there is no ground truth for "override" here.
 - This needs either a chip semantics statement shown to the model or a judge rule for "agreement reply", declared in PLAN before E1. Until then C1 is uninterpretable as harm.

## Major
M1. Selection on the baseline. 14 of 40 families (35%) were dropped mainly because the N turn failed the checker. N is the turn the pilot itself then calls a defective baseline.
 - The survivors are non-event topics, which probably differ in susceptibility to X and Q. Drop counts by type per family should be shown, and the drop rule revisited.
 - Q and D turns passed at 97-100%, so the drops came almost entirely from N, not from the manipulation turns.
M2. Outcome-informed redesign is being proposed (use 0 instead of N as the baseline) after the pilot showed N is bad. That is a legitimate fix but it is outcome-informed. It needs a dated amendment that says so, with the pilot labelled as informing the design. The E0 families should not be pooled into confirmatory E1 without re-authoring. PLAN section 2 currently lets pilot families stay in the set "only if no template change occurs", and A2 already changed a template.
M3. C2 and C4 are the same number on the bare channel by construction (round1 says so). Holm over "4 contrasts" is really 3, and presenting C4 as a "benefit" test is circular because the bare output is intent-independent. The "benefit" of a negated-intended family is just C2 read from the other side. The Cai-type accuracy benefit has not been measured on any non-trivial design.
M4. The q* = 0.5 break-even is trivial. The output is intent-independent and the weights are symmetric, so it is a restatement of "the model negated k% of the time". It carries no information about real partner turns, so it should not appear in the summary as a result.
M5. The model under test (gpt-6.1-terra) is also the authoring model of the turns, and the checker (sol) is the same family as the judge. Style or echo leakage between turn text and outputs is plausible. The plan section 2 calls the checker "not the judge", yet the pilot caveat concedes they share a model family.
M6. Q turns are not question frames of the user's proposition. Several rewrite the topic: "Did the receptionist read about access?" for "read access", "Did the guest receive personal respect?", "Did the bank card end up at the flat?". The checker passes them as "neither" because it only judges polarity. C3 therefore tests topic drift plus a question frame. The planned distractor and X' controls do not cover this.
M7. Statistics.
 - n = 26 clusters with events of 1-5 per cell. Percentile bootstrap intervals are degenerate when the count is 0 or 1 (for example Q minus 0 gives [-11.5, 0.0] for a single family, and [0,0] rows).
 - CIs lack small-sample validity, so exact or Bayesian intervals are better. Pooled C1 averages two heterogeneous variant cells (A+X and B+D), and pooled bare C2 resamples the same output twice (variants A and B are duplicates) unless variant A only is used. The code does use A only, which is fine, but the 520 rows per model are really 260 distinct bare outputs.
 - Terra at T=0 is not reproducible (the API ignores seed), so there is no replicate to estimate its noise. The pre-declared R1-R7 were not applied (stated), so there is no cherry-picking, but the "+2 pp equivalence margin" is below the resolution of n = 26 (one family = 3.8 pp).
M8. Weak baselines for "closest published approach": only M0 ("context in prompt") exists in the pilot. No ablation, guard, word cue or ask arm has been run, so the "benchmarked" requirement is not met. The pilot cannot claim anything about interventions, which the round1 text admits in caveat 5.
M9. AAC conversion. "Among X-frame messages ... 120-540 per 1,000" is just the rate times 1,000 in a hypothetical subset. Multiplying by an SLP weight of 5 and comparing it with the 23.9 per 1,000 baseline compares different denominators. This is a rhetorical comparison, not a rate per 1,000 messages. P(X-frame partner turn with affirmative intent) is unmeasured, and the text correctly says so, but the number should not be in the headline.

## Minor
- The "H3 not supported" conclusion is sound (Q minus 0 is slightly negative). The N artifact (+15-19 pp vs N) is honestly disclosed.
- Examples are chosen by a declared rule (first two by family id), which is fine, but the chosen examples are the echo ones, so they do not represent propositional flips.
- The v1 gate failure and the A2 amendment were reported transparently. Amendment A2 was made before model outputs existed, which is good.
- Terra D+[NOT] "0.08 + 0.15 uncommitted" for qwen is qualitatively different: the D template pushes "worked out as planned" onto a negated cue, creating run-ons ("I guess not using cream worked out as planned"). This is judge noise and the label is `unclear/mixed`; the judge handled it consistently.
- Novelty: the literature section is plausible (Cai 2022, Braun 2025) but a search is needed for echo / copy-from-context in LLM generation, prompt-injection-style context override, and instruction conflict research before the "new silent-reversal class" claim.

## Verified OK
- Gate numbers: 1040 rows, 0 invalid, 0 parse failures. Bare variants A/B identical. Only variant A used in bare contrasts.
- The headline 12%/54% match the parquet (3/26 and 14/26).

## Needed before E1 (priority order)
1. Redefine the outcome as propositional polarity of the user's keywords, with a judge rule: copies of the turn's evaluative phrase ("did not work out") are `echo`, not `negated`. Report echo, propositional flip and agreement-reply separately.
2. Add the X' (semantic push without the template phrase) and a distractor-turn control to E1 itself, not E3, and a chip-semantics preamble arm.
3. Make 0 the primary baseline (dated amendment, labelled outcome-informed). Fix the Q template to keep the family predicate verbatim. Re-author N as a non-topic filler or drop N. Do not drop families on N failure.
4. Use a non-terra authoring model for turns, or report terra separately.
5. Report exact or Bayesian intervals, and the one-family resolution (3.8 pp). Drop the q* = 0.5 "result" and the weighted-per-1,000 figure from the summary.
6. Run benchmark arms (M0, M1, M2, M4, M5, random-ask, always-ask) in E1 on a small slice, since E2 gating on a pilot rate that is largely echo would benchmark the wrong problem.
