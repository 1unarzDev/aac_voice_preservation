# default_profiles: claims README (round 3, final)

**Paper framing: a measurement framework + a null result + where it does not help.** Details and tables: `round3.md`. Plan and amendments: `PLAN.md`; deviations: `DEVIATIONS.md`.

## Claims we make
1. **Always-commit silent reversals** (model-visible, 4-model mean, per 1,000 messages): negation 24 [16, 33], politeness 49 [38, 64], question/request 162 [134, 188]. Politeness and question/request are provisional (detector-proxy labels).
2. **No tested ask policy is distinguishable from gated-random at a 10% ask budget.** 0 of 4 pre-named primary contrasts significant after Holm (B = 300). Negation MDE is 8.5 per 1,000, so this is a null of limited power, not equivalence.
3. **Probe beliefs are poorly calibrated** against human base rates (BSS < 0 on negation and politeness for all three probe models; acquiescence-confounded, not an AAC profile gap).
4. **Framework:** exposure vs model-visible reversals, SLP-weighted, with ask budgets and taps, a gated random baseline, and a no-model-call prior.

## Claims we do NOT make
- No G1 comparison: G1 needs a spec, and the round-2 'G1 harmful for politeness' claim is withdrawn (flags were by construction). A spec-based check shows detection only, with oracle intent; repair was not run.
- No benefit of chip or plain word is measured on these units: those rows use transported rho from hw1 pairs and assume asking supplies the cue.
- No CLAM benchmark (entropy stand-in only); the closest-published-method benchmark is unmet.
- No claim that the keyword prior beats confidence or random; no 'avoided reversals' claim from policy ranking; no model is singled out; the confidence signal on negation is suggestive only (exploratory, BH).
- No acceptability comparison between arms (not comparable; 2 raters, 20 to 40 rater-items).
- Speech-act and politeness numbers are provisional until the annotation request (not sent) returns.
