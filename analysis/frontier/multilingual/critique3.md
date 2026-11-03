# Critique, round 3 (multilingual register and polarity defaults), methods/statistics + novelty

Verdict: valid = true (no fatal issue for the claims as written, because round3.md already scopes itself as a 2-model machine-label pilot). Several headline sentences still overreach; fix before any writing pass.

## Major issues
1. "Statistically indistinguishable" (Headline 2) is absence of evidence. Plain-vs-chip polarity differences are 1 of 40 outputs (DE/FR), with CIs up to +7.5 to +17.5 pp; 17.5 pp is about 4.7 reversals per 1,000, larger than the whole chip effect. The chip CI [0,0] (0/40) is a degenerate bootstrap; use Clopper-Pearson or rule of three (upper about 7%, about 2 per 1,000). Several lower bounds are "-0.0", i.e. the CI touches 0 exactly. Say "not resolved at n=20 families x 2 models", not "equivalent".
2. The reversal metric is pi_neg x 1000 by construction (27.0, CI [27,27]), with pi_neg = 2.7% an English, non-AAC human-keyword prior transferred to DE/ES/FR. PLAN line 62 also says "24 per 1,000" for English while the tables use 27. The "silent reversals per 1,000" are therefore assumption-driven, and the always-commit CI has no sampling meaning.
3. Chip cost accounting favours both cued arms. "Cued only" taps (27/1,000) assume the user already knows which messages need the cue, which is the unsolved problem. No false-negative-cueing or false-cue (chip on affirmative) cost is modelled, so the 1,000-tap every-message row is the honest chip cost.
4. ES register headline (chip beats plain 17.5 pp) relies on a detector that failed its gate (94.2% < 95%; 7/67 "none" outputs were address forms). No-address is counted as failure, so detector misses inflate failure and likely hit the plain-word and bare arms differentially. Labelled exploratory, but it sits in Headline 3 and the E3b "ES meets rule" claim.
5. ctxn_yes compliance (EN 80% vs DE 44 / ES 35 / FR 40%) is probably a labelling artefact. Stored outputs include hybrids: "Ja, aber ich moechte ... nicht", "Ja, das Spiel beginnt ..., aber ich moechte nicht mitspielen". The EN example is also hybrid ("Yes, but I don't want to ..."). Whether hybrids count as non-affirmative depends on the sol labeller and the translate route, and no language test was run. Treat as unsupported until hand-checked. ctxn_bare = 100% negated is vacuous, since the prompt states the refusal outright, and "diff 0 [0,0]" is a meaningless CI. ctxq 0/20 [0,0] is the same degenerate bootstrap.
6. Headline 4 ("register default is model-dependent") compares one API model with one local 12B on n = 7 to 14 address-bearing outputs, conditioning on a post-treatment variable (the output chose to contain an address). Terra has no address form in about 40% of outputs, so "default" is the default among outputs that happen to address. The 2-model range is a contrast and the report says so. The contrast is also confounded with vendor, size and API versus llama.cpp prompt templating.
7. Label independence: terra is both a tested model and an arbiter, sol is the same vendor family, and there are no human labels. Translated stimuli have no native check (E8 overlap gate passed 59/59, so it filters nothing). Control-keyword survivors for nominal conditions have n = 4 to 5.
8. Benchmark gaps for "journal-ready": no implemented published method (CoCoA-MT or formality-controlled generation is cited only from abstracts); no regeneration arm for the leak-filtered plain word (acknowledged lower bound); the G1 guard is mentioned only with a written cue; no acceptability or SLP-rated outcome (register SLP weight borrowed at 0.5). The SLP-weighted column equals the raw count (weight 1.0), so it adds nothing.

## Process and integrity
- R3.2b (ctxn) was added after seeing ctxq. Declared as post-hoc; acceptable, but the ctxn result should not be a headline.
- Clean E3b variant flips ES sign; handled honestly. The declared rule being "met" in ES while the detector gate failed should be stated in one sentence in the headline, not only in the body.
- Same-item paired CIs are cluster bootstraps over 20 families with only 2 models pooled as replicates; model variance is not in the CI, so the CIs are conditional on these two models.
- Greedy bare outputs of the pilot models are cache hits, so replicates are not independent; round3 states n = families, fine.

## Novelty
- Polarity: round3 already cites Chen et al. 2023 (arXiv 2305.05976) as the prior; correct framing as a mechanism check. The multilingual extension is incremental.
- Register: the default-formality-by-language question is directly covered by Ersoy et al. (arXiv 2302.12299, "In What Languages are Generative Language Models the Most Formal?"; confirmed by search: XGLM and BLOOM, neutral prompts, T-V based, formal-leaning default, sensitivity to prompt formality). The present finding (model-dependent default; terra informal, nemo mixed) differs in using chat models and AAC keyword inputs, but the report should position against that paper (it is only mentioned in a benchmark line) and against formality-controlled MT (CoCoA-MT, IWSLT 2022) for the chip. A 2026 arXiv paper on language-agnostic informal register (2603.26236) turned up in search and is unread here; check it before claiming novelty. A search for negation default plus AAC found nothing, and I did not search further.

## Cheap re-checks done
- Recomputed: 0.675 = 27 x 1/40, so the plain-word "reversals" in DE/FR are one output; 2.13 (ES) = 27 x 0.079; consistent with the tables, no arithmetic bug found.
- ctxq/ctxn rows verified in r3_a CSV against the round3.md text; numbers match.

## Strongest true claim
In this 2-model, translated-stimulus pilot, restoring an explicit negation cue removes essentially all bare-output polarity reversals in DE/ES/FR/EN (0 to 1 of 40 outputs per language), as expected from the known keyword-generation positivity bias; the chip versus 1-tap plain-word difference is small and unresolved.

## Next steps
Replace degenerate bootstraps with exact CIs; drop or hand-check ctxn compliance (hybrids); remove "indistinguishable"; state the ES-detector caveat in Headline 3; add Ersoy et al. and CoCoA-MT positioning; run the remaining models after the GPU resume; add a human check of the ES detector and the translations (already requested); model a cueing false-negative cost.
