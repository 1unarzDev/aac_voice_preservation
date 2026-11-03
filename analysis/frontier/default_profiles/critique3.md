# default_profiles: adversarial critique, round 3 (methods/statistics + novelty)

Verdict: valid = true (no fatal issue). Round 3 withdraws the round-2 G1 claim, reports B = 300 as primary, resamples rho inside the bootstrap, and presents a measurement framework plus a null. Remaining problems are overclaim risks and an unmet benchmark requirement, listed below.

Checks done: read round3.md, DEVIATIONS.md, PLAN sections 9-10, critique2.md; inspected contrasts_r3.csv (primary rows, Holm p_adj = 1.0 as stated), mde_r3.csv, rho_draws.csv, g1_spec_check.json; light literature search. I did not re-run the pipeline (no GPU or API needed for the reading checks).

## FATAL
None.

## MAJOR
1. **Closest-published-method benchmark is still unmet.** No CLAM-style ambiguity classifier was implemented; the "entropy" policy is a stand-in. The task's "benchmarked against prior methods" requirement is therefore not met. The paper must not claim superiority or parity with published clarification methods, and the Limitations section should be near the front.
2. **Chip, plain-word and every-message rows are arithmetic, not outcomes.** They equal always-commit minus rho x ranking reduction, with rho transported from hw1 pairs and with the assumption that asking supplies the cue. "Chip on every message: 0.1 left" is (1 - 0.995) x 23.9. Rho uncertainty is now in the CIs, but not the hw1-to-elicitation transport gap or user non-response. The headline benefit (taps to remove reversals) is conditional and must be worded that way everywhere, including abstract and figures. The G1 same-items comparison does not exist, so the study's own intervention is not benchmarked.
3. **G1 spec check leaks by design and is recall-only.** The spec contains the source message (oracle intent), and check() flags 41% of outputs with none of the three reversals. Detection shares of 87%, 98% and 99% are therefore recall at a very high false-flag rate. Do not present them as G1 performance. Precision for the three dimensions is not reported, and repair was not run.
4. **Primary contrasts are null and underpowered, and the point estimates are off-centre.** The negation prior-vs-random point estimate is -4.2, but the bootstrap mean is -1.5. The BC interval [-15.0, -0.5] excludes 0 while the percentile interval [-8.5, 2.2] does not. Reporting both is honest. Do not cite the BC interval or the point estimate as support for the prior. The MDE is computed from the observed SE (post hoc power), so it supports "cannot detect" and nothing stronger.
5. **Exploratory confidence signal.** The negation confidence-vs-random contrast (BH q = 0.119) and the valid-cell mean (15.4) are selected using the same exposure units, and the event is defined by the same models that supply the probes (circularity). Keep them out of the abstract. The 21 of 236 BH hits at q < .05 mostly come from near-duplicate variants.
6. **Provisional labels carry the headline.** Question/request (162 per 1,000) and politeness (49) rest on detector-proxy source labels; the annotation request is not sent. The headline 24 / 49 / 162 mixes one validated and two provisional dimensions. The abstract must either lead with negation or tag the others. SLP-weighted sums across unlike events (weights from 2 raters) are descriptive.
7. **Plan section 10 was written after the 22-second r3 run.** DEVIATIONS item 6 discloses this, and the choices restate the director's instructions. Reviewers may still see it as a post-hoc protocol, so keep the disclosure in the paper.

## MINOR
- Acceptability table: arms are not comparable (selected judge-failed items, 2 raters, 20-40 items). The caption says so; keep it out of any figure that implies a ranking. The guard_original lower CI prints as "-0".
- Output-level G1 rates (24.2 / 35.0 / 194.3) and unit-level rates (23.9 / 49.4 / 161.9) differ in denominator. This is stated; keep them in separate tables.
- "Silent reversals per 1,000 messages" is a model-visible count over 1,800 keyword units (strata random/enriched, HT-weighted). State that these are not deployment rates.
- H1 belief-scale gaps (+35 to +46 pp) are acquiescence-confounded. BSS < 0 is the usable content. 3 of 5 probe models were run.

## Novelty (search 2026-11-02)
- Cai et al., NAACL 2022 (context-aware abbreviation expansion with LLMs for AAC) is the nearest AAC work. It shows candidate options to the user, with no negation or speech-act reversal pricing: https://aclanthology.org/2022.naacl-main.91.pdf
- Chen et al., ACL 2023 ("Say What You Mean!", LLMs speak too positively) documents negation dropping in keyword-to-sentence generation, already cited: https://aclanthology.org/2023.acl-long.550.pdf
- Ask-when-Needed (EMNLP 2025) and a NAACL 2025 Findings clarification paper cover when to ask; these were seen as search snippets only and are not opened: https://aclanthology.org/2025.emnlp-main.1104.pdf, https://aclanthology.org/2025.findings-naacl.306.pdf
- I found no AAC-specific work pricing silent meaning reversals per 1,000 messages with human keyword base rates. Novelty lies in the measurement framework, not in the ask policy, which is a null.

## Strongest true claim
On 1,800 human keyword units, always-commit leaves roughly 24 (negation) silent meaning reversals per 1,000 messages, 95% CI [16.0, 32.5] (politeness 49 and question/request 162 provisional). No tested ask policy is distinguishable from gated-random at a 10% ask budget after Holm, with MDE 8.5 per 1,000 for negation. Probe-model beliefs are poorly calibrated to human base rates (BSS < 0).

## Next steps
1. Send the ANNOTATION_REQUEST (speech act and politeness source labels), then re-run r3 with human labels.
2. Implement the CLAM-style classifier when the GPU pause lifts, or drop the "closest published method" claim.
3. Measure chip and word cue-honouring on the elicitation units, or keep every intervention row labelled conditional.
4. Run G1 with regeneration on cue-supplied items for precision and repair; keep it out of same-items tables until then.
5. Frame the paper as a measurement and null-result paper and lead with negation.
