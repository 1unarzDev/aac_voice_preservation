# Critique 1 (methods/statistics + novelty), frontier multilingual, round 1

Verdict: valid = true (no fatal issue; every number I re-derived from the stored tables and labels matches round1.md). The "pilot-level SUCCESS" verdict in round1.md is overclaimed, and several major issues below must be fixed or stated before anything is promoted.

## Major issues

1. H1 is nearly tautological and conditioned on the outcome. The denominator is outputs that already contain a T or V form, and each output is a single sentence. A single sentence rarely mixes registers, so 94/94 "commit" says little. The unconditional rate is the informative number. Only 58% (DE), 43% (ES) and 55% (FR) of bare outputs address the listener at all. The rest avoid the choice, which is the opposite of "always commits". The "approaches 100%" headline should be reframed as "when a model addresses the listener it picks one form, and a large share dodge". The exact Clopper-Pearson interval also assumes independence. The 94 outputs are 20 families x 3 models at greedy T=0, so the effective n is much smaller.

2. Success verdict versus PLAN Sec. 7. H2 is met only by gemma3-4b, DE vs FR. That is n=10 vs n=12 address-bearing outputs. The CI is [-75,-3], one of three models, uncorrected, though the plan promised Holm. Nemo is borderline and terra shows no effect. H3 shows no language effect. H4's register clause fails for French informal and for plain/context arms. "Promotion to Stage 1" is reasonable. Calling it "SUCCESS" is not. The honest label is "Partial, with H2 weakly supported on one model".

3. Stimulus confound: infinitive keywords. REG keywords are infinitives by instruction. In German the infinitive is identical to the formal imperative ("bringen Sie"), and in French the infinitive resembles the polite "veuillez/apportez" pattern. The keyword form therefore pushes toward some registers, and this differs by language. The DE-vs-FR "language flip" may come from the stimulus format, not from model defaults. Spanish "Traer X, por favor" gives impersonal outputs. No arm uses non-infinitive (e.g. noun-only) keywords. The terra-as-translator register skew (DE 19/20 T, FR 15/20 V) shows the translation step injects register, and that is not controlled either.

4. Detector validation is weaker than reported.
   - The sample was "non-ambiguous" outputs only. About 15% of bare outputs (the ambiguous ones, 49 of 180) were labelled by the same arbiter and never validated.
   - The arbiter is a Claude agent, not independent of the author. The v2 lexicon was written after reading its v1 labels, and v2 includes the inflected forms of the fixed REG verbs. That lexicon is tuned to these 20 families and will not generalise to the 50 Stage 1 families without a fresh check.
   - Spanish fails the gate (36/40). Spanish "none" (57%) and "0% V" are therefore unreliable.
   - The validation size was cut from 120 to 40, so a 95% gate cannot be tested with any power. 38/40 is the minimum pass, and the CI is wide.

5. H3 English comparator is not "same families and models". english_baseline.jsonl has 99 rows. These cover 16 families and 5 models, and include qwen2.5-7b and llama3.1-8b, which were not run in the pilot. English n is 45-48 against 57-60. Rows were kept only when J1 and J2 agreed. English is at 100% too, so non-inferiority at a ceiling is trivially met and has no power to detect a language difference. The "CI approx [-5,0]" for FR is an approximation, not a computed bootstrap. The result is also close to degenerate: bare A and B share one keyword string, so there are 20 distinct inputs per language, repeated across 3 models. Rerun English on exactly the 20 families and 3 models.

6. Policy benchmarks.
   - Random-ask is compared at the wrong operating point for register. "Ask only when the output addresses the listener" (583/550 taps) is compared with random-ask at p=0.5 (500 taps). It should be compared at matched taps. The address trigger also assumes a generate-then-regenerate loop, which costs latency and a second generation that is not counted.
   - Policy mismatch counts only address-bearing outputs, and chip arms change the address rate (58% to 90%). The accounting is inconsistent across policies.
   - The always-ask chip value (0.45 per 1,000) assumes the user always supplies the correct cue.
   - G1 with a written cue and entropy-ask (INTENT-SIM style) were not run. The "closest published method" comparison is therefore open, as the report says.
   - SLP weights give NEG = 1.0, so the "weighted" polarity number equals the raw one. Register uses the POL weight 0.5 with no SLP rating behind it.

7. Chip vs plain/context comparison is confounded. The chip arm uses an extended legend that defines [FORMAL] and [INFORMAL]. The plain and context arms use the original legend. "Chip better than plain word" (unlike English D-070) may reflect the legend text and the instruction-like framing, not the chip form.

8. Polarity route: the judge is a single model family (gpt-6.1-sol), and all three arbiter-resolved texts went to the same Claude arbiter. A kappa of 0.97-1.0 is expected when every label is "affirmative". Kappa is degenerate at that prevalence, so report raw agreement and the count of negated items instead. With 1 negated output in 180, the polarity default result cannot distinguish "no language effect" from "no variance".

9. Translation gate is lenient. A 100% survival rate with a 3-letter-prefix overlap and a one-word polarity classifier is a weak filter. The human check is pending, so "far above the 70% gate" says little. A single back-translator was used and the Claude 20% subsample was dropped (DEVIATIONS 3).

## Minor issues
- Terra is not reproducible at T=0, so the terra results are one draw. The d2 replication was not run.
- 3 of 6 models were run, and all conclusions are per-model with n=1-14 per cell.
- Cell lists use "pooled" rows. The pooled V share (DE 31% vs FR 58%) mixes models whose defaults point in opposite directions, so it reflects the model mix, not a language fact.
- The English V/T comparison is absent. English has no register distinction, so a "language flip" cannot be tested against English.

## Novelty
- A web search (2026-11-02) found no paper that benchmarks the T-V default of LLMs under an underspecified task. Searching again for "LLM formality bias German French evaluation" and the formality-controlled MT work (IWSLT 2022/23, CoCoA-MT) is still needed.
- The nearest prior art found:
  - Faruqui and Padó (EACL 2012), T/V as an NLP label.
  - SYSTRAN's politeness-mode token (arXiv 1610.05540), which is explicit attribute control and is the direct ancestor of the chip arm.
  - A Frontiers in Public Health 2021 study of chatbot T/V in French and German.
  - Wang and Suresh (arXiv 2606.00333) on jurisdictional defaults, already cited in PLAN.
- The explicit attribute control (chip) is not novel. It is a tag-based formality control in the style of SYSTRAN and IWSLT, and should be described as a replication in an AAC setting, not a new method. Ershadi et al. (2302.12299) and the IWSLT papers still have to be opened before any "first" claim. The polarity-default-outside-English claim is also weak if the result is a non-finding at ceiling.

## Next steps
1. Reframe H1 as an unconditional "address vs dodge vs commit" split and report the dodge rate in the abstract.
2. Add a keyword-form control (non-infinitive or noun-only) for REG, and run the v2 detector on a fresh Stage 1 validation sample that includes the ambiguous outputs.
3. Rerun the English baseline on the exact 20 families and 3 models, with a computed CI.
4. Compare policies at matched taps, include G1 with a written cue and the entropy-ask baseline, and apply Holm across models.
5. Give plain/context arms the same legend extension as the chip arm.
6. Run the human annotation (Spanish register first) before promoting, and read the IWSLT formality and Ershadi et al. papers before claiming novelty.

Sources: [Faruqui and Padó 2012](https://aclanthology.org/E12-1064.pdf), [SYSTRAN pure NMT politeness mode](https://arxiv.org/pdf/1610.05540), [Frontiers in Public Health 2021, T/V chatbot study](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2021.691595/full).
