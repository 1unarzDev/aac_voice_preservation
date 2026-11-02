# Deviations from PLAN.md (Stage 0 pilot, 2026-11-02)
All were decided before looking at generated outputs unless marked.
1. Stage 0 scope: first 20 POL and first 20 REG families by the declared hash order (not 50). Models: gemma3-4b, mistral-nemo-12b, gpt-6.1-terra. P0-LL run on the bare arm only. PLT and CS stimuli not built in Stage 0 (H5, H6 not tested).
2. Keyword overlap check (translation gate c) uses a 3-letter-prefix match between the English bare tokens and the back-translated keyword tokens (the repo's existing convention), not a lemmatiser.
3. Back-translation polarity gate uses a blind gpt-6.1-sol one-word classifier (A must be affirmative, B negated), not the full English judge pipeline. No Claude-subagent 20% back-translation subsample was run (single back-translator, sol).
4. Detector unit tests: 24 hand-written sentences per language instead of 60. Two detector bugs found by these tests BEFORE any model output was labelled were fixed (French "t'" elision and "rendez-vous"; Spanish "es/esta" removed from the weak-formal list). Spanish "ustedes" is sent to the arbiter, not counted as V.
5. Detector validation sample: 40 random non-ambiguous outputs per language (plan: 120), blind arbiter = the Claude engineer agent reading output text only in shuffled order.
6. Polarity judging: gpt-6.1-sol blind, batched 10 sentences per call (text only), direct target-language route and translate-then-English route; disagreements and unclear to the blind Claude arbiter (text only). Not the judge.py J1/J2 pipeline (that pipeline is English-only and keyed to the hw run format).
7. The three "full-sentence" and politeness (PLT) and CS arms, entropy-ask, and guard-with-written-cue arms were NOT run (see round1.md "not done").
8. Chip legend extension for register arms ([FORMAL]/[INFORMAL]) is used only on the chip_formal/chip_informal arms; bare, plain-word and context arms use the original legend.
9. Register context cue text is a neutral noun phrase ("Gespraech mit dem Arzt") so that the cue text itself carries no T/V form.
