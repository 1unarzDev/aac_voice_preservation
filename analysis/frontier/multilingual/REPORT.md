# Report: cross-lingual register and polarity defaults (pilot), frontier "multilingual"

Director's final report, 2026-11-02. Status: **PILOT, machine labels only, translated stimuli, 2 of 6 planned models.** Companion files: PLAN.md (rules, written before outputs), DEVIATIONS.md (26 items), round1.md, round2.md, round3.md, critique1-3.md, ANNOTATION_REQUEST.md (built, NOT sent), r3_auto_tables.md and summary_r3.json (numbers).

## 1. Question
When an AAC user sends a bare keyword string to an LLM that expands it into a sentence, what does the model silently decide that the keywords do not say, and does that change across languages?
- Register: German du/Sie, French tu/vous, Spanish tu/usted.
- Polarity: affirmative versus negated.
- Does a one-tap cue (chip "[NOT]", "[FORMAL]") fix it, and does it beat a plain typed word at equal cost?

Scope: a pilot that tests whether the English finding (silent default, chip repairs it) transfers to DE/ES/FR. It is not a study of real multilingual AAC users (no participants, no IRB).

## 2. Pre-declared rules (PLAN.md, frozen before outputs)
- Hypotheses H1 to H6 and decision rules were written before any translation or generation. H1 is register commitment (at least 90% single-register given an address form). H2 is a register direction difference of at least 30 pp between languages, cluster-bootstrap CI excluding 0. H3 is a polarity default within 5 pp of matched English. H4 is cue restoration of at least 50 pp. H5 (politeness) and H6 (code-switching) were never run.
- Cluster bootstrap over 20 families per task, 10,000 resamples, seed 20261102, Clopper-Pearson where the bootstrap collapses. Holm correction for the language contrasts.
- Register detector gate: at least 95% agreement with a blind arbiter on a fresh sample. One revision was allowed.
- No J1 fallback, and arbiters are non-Claude (gpt-6.1-sol primary, terra secondary).
- Round-2 and round-3 plans were written before those rounds' outputs. All of them are post-pilot amendments to the original plan.
- Post-hoc and labelled as such: the clean pronoun-only E3b variant, the ctxn refusal-prior arm (added after ctxq gave 0%), and the E3b wording correction.

## 3. What was run
- Stimuli: 20 polarity minimal-pair families and 20 register keyword families, translated to DE/ES/FR (ES has 19 accepted polarity pairs). Gates were back-translation overlap and a one-word polarity classifier. No native speaker has checked anything.
- Models with data: gpt-6.1-terra and mistral-nemo-12b. gemma3-4b, qwen2.5-7b, llama3.1-8b and qwen2.5-14b are queued and were not run because the owner's GPU pause (D-084) was still in force. Every number is therefore a 2-model result (n = 40 outputs per cell, 20 families times 2 models).
- Arms:
  - bare keywords;
  - cue chip (restores the negation or register cue);
  - plain typed word ("not", "formell", legend-equalised);
  - context cue;
  - G1 guard with a written cue;
  - entropy and sampled-vote ask;
  - random-ask;
  - ask-if-address;
  - matched English comparator;
  - keyword controls (nominal, German separable-prefix, second translator).
- Labels: polarity by blind sol, direct route and translate-then-English route. Register by detector v2 plus an arbiter for ambiguous outputs.
- Detector validation on a fresh 120 outputs per language: DE 97.5% (pass), FR 100% (pass), **ES 94.2% (FAIL, 7 of 67 "none" outputs were address forms)**. Spanish register results are exploratory.
- AAC-unit endpoints at pi_neg = 2.7%. This is an English, non-AAC prior transferred to DE/ES/FR. SLP negation weight is 1.0. The register weight 0.5 is borrowed. Chip charged every message or cued-only.

## 4. Results (2-model pilot, with CIs)

### 4.1 Polarity: bare default and chip restoration (mechanism check)
| language | bare negated (B families) | chip negated | reversals per 1,000, always-commit | chip |
|---|---|---|---|---|
| DE | 0% | 100% | 27.0 | 0.0 |
| ES | 0% | 100% | 27.0 | 0.0 |
| FR | 2% (1 output) | 100% | 26.3 | 0.0 |
| EN (matched) | 0% | 95% | 27.0 | 1.4 pooled |

- Gain lower CI bound is at least 88 pp in all four languages and both models. This meets H4 for 2 of 2 models.
- Honest framing: the always-commit figure equals pi_neg x 1,000 by construction. Its CI has no sampling meaning and the number is assumption-driven.
- Chip 0/40 has a degenerate bootstrap CI. Exact Clopper-Pearson gives an upper bound of 8.8% negation failure, which is at most about 2.4 reversals per 1,000.
- Matched English H3: P(affirmative | committed) is 100 / 100 / 98.9 / 97.4% for EN / DE / ES / FR. This is a ceiling result and uninformative about a language effect. Sampling at T = 0.7 created no variance.
- Interpretation: this is the known keyword-to-sentence positivity bias (Chen et al., ACL 2023, arXiv 2305.05976, abstract opened). It holds in DE/ES/FR at the same size. It is a mechanism check, not a discovery.

### 4.2 Polarity: chip versus plain word "not"
Negated-rate difference, chip minus plain, cued messages: EN 2.5 pp (CI -5 to 10), DE 2.5 (0 to 7.5), ES 7.9 (0 to 17.5), FR 2.5 (0 to 7.5). Silent reversals per 1,000: chip 0.0 to 1.4, plain 0.7 to 2.1. Taps cued-only are 27 per 1,000 for both.
- **This is not resolved at n = 20 families x 2 models.** The critic correctly rejected "statistically indistinguishable", because the upper bound of 17.5 pp is about 4.7 reversals per 1,000.
- What is supported: the difference is at most a few reversals per 1,000 in the observed outputs, and the plain word works.
- Cost caveat: "cued-only" taps assume the user already knows which messages need the cue. That is the unsolved problem, and no false-negative-cueing cost is modelled. The every-message chip (1,000 taps) is the honest chip cost.

### 4.3 Register default (model-dependent, language effect not supported)
French V share among address-bearing bare outputs: nemo 77.8% (7/9, CP 40.0 to 97.2) versus terra 8.3% (1/12, CP 0.2 to 38.5). German: nemo 45.5% (5/11) versus terra 7.1% (1/14).
- Cross-model range: DE 38.3 pp (CI 4.3 to 75.0), FR 69.4 pp (CI 33.3 to 100).
- Language contrasts do not survive Holm. DE-FR for nemo is -32.3 pp (CI -66.7 to 0.0), Holm p = 0.113. For terra, p = 1.0.
- Spanish (0 of 25 V) is excluded because the detector failed its gate.
- Round 1 (5 models, earlier pilot) saw the same direction: FR V share 8% terra versus 92% gemma, with H2 met for one model pair only (uncorrected).
- Honest reading: the default is not a property of the language. It differs by model.
- The comparison is confounded by vendor, size, API versus llama.cpp templating, and by conditioning on the output containing an address form.
- E1 commitment: given an address form, every bare output is single-register (DE 25/25, ES 25/25, FR 21/21; CP lower bound 84 to 86%). But 37.5% (DE, ES) and 47.5% (FR) of bare outputs contain no address form at all. "Always commits" is conditional and near-tautological for one-sentence outputs.
- E3b, commitment versus English "you": the declared rule is formally met in ES only (+20 pp, CI 2.5 to 37.5), but the clean pronoun-only variant flips ES to -7.5 pp (-15 to 0). That is unstable, on a detector that failed its gate, so no commitment claim is made and the frontier was not promoted on it.

### 4.4 Register chip versus plain word (equal cost, legend-equalised)
Failure rate (output not in requested register, no-address counted as failure, pi_V = .5):
- Chip: DE 8.8%, ES 10.0%, FR 17.5%.
- Plain word: DE 16.2%, ES 27.5%, FR 31.2%.
- Plain minus chip: DE 7.5 pp (CI -2.5 to 17.5, unresolved), ES 17.5 (7.5 to 28.7, exploratory, failed-gate detector), FR 13.8 (5.0 to 22.5).
- Leak: 7.5 / 15 / 12.5% of plain-word outputs echo the cue word. With the output filter, the gap is 10.0 / 21.2 / 17.5 pp. This is a lower bound, because rejected outputs were not regenerated.
- Policy table per 1,000 messages (a mechanism illustration, with pi_V assumed and the chip treated as ground truth):
  - DE: commit 688, chip 88, plain 162, context 375, ask-if-address 375.
  - FR: commit 738, chip 175, plain 312, context 462, ask-if-address 512.
- Break-even tap value c* is about 0.56 to 0.60 mismatches avoided per tap for the chip, versus 0.41 to 0.53 for the plain word.
- Ask-if-address looks cheap only because it asks less. Once a no-address output counts as a cost, it leaves 375 to 512 mismatches per 1,000.
- Where it does not help: French-informal chip failures remain (17.5% overall; 79% in round 1), and the DE advantage is not resolved.
- This is formality-attribute control in the CoCoA-MT / IWSLT 2022 sense. It is not novel and was not re-implemented.

### 4.5 Non-ceiling polarity test (weak, one model)
- ctxq (yes/no question context): 0% negated in all languages. The model often echoes the question, so this is a failed attempt to leave the ceiling.
- ctxn (refusal prior, added post-hoc): bare is 100% negated, which is vacuous because the prompt states the refusal. The [YES] chip is honoured 80% (EN), 44% (DE), 35% (ES), 40% (FR).
- The critic flags this as probably a labelling artefact. Hybrids such as "Ja, aber ich moechte nicht ..." exist in the stored outputs, and no hand check was done. **ctxn compliance is not a headline and is unsupported until hand-checked.** It shows only that the default moves under a prior.

### 4.6 Controls and benchmarks
- Keyword controls (nominal, separable-prefix, second translator):
  - Nominal keywords produce few address forms (13 to 15%), so there is no power.
  - French second-translator V share is 42.1% versus 38.1% bare, which argues against a translator artefact for French.
  - German is unresolved (separable-prefix 16.7% versus 26.1%, n = 12 per model). No claim is made.
- Back-translation overlap gate passed 59 of 59 second-translator strings, so it filters nothing. "Survivor" does not mean verified correct.
- G1 guard with a written cue repaired every output. It needs the cue written first, so it is effectively the chip plus verification.
- Sampled-vote ask removes 0 to 1.3 of 27 reversals. The model is confidently wrong, so all 5 draws agree.
- The leak-filter keyword lexicon removed 0 of 20 families.
- Not done: no implemented published method (the closest, CoCoA-MT, is cited from abstracts only) and no acceptability or SLP-rated outcome. The SLP-weighted column equals the raw count at weight 1.0, so it adds nothing.

## 5. Critic issues and resolution
| issue (critique1-3) | resolution |
|---|---|
| English comparator unmatched, H3 at ceiling | Matched English added (round 2). It is still a ceiling and is reported as uninformative. |
| ES detector failed gate | One revision made (DE 87.5 / ES 67.5 / FR 82.5% to v2, in-sample). Fresh validation DE 97.5 / ES 94.2 / FR 100%. ES stays exploratory and is excluded from the headline V-share. Human check requested (not sent). |
| "Statistically indistinguishable" (chip vs plain) | Withdrawn. Reported as unresolved, with CIs and the 4.7-per-1,000 bound. |
| Reversal metric is pi x 1,000 by construction | Stated here. The CI has no sampling meaning. Exact CP bound for the chip. |
| Cost accounting favours cued arms | Both cued-only and every-message costs reported. False-negative cueing not modelled (open). |
| ctxn compliance may be a labelling artefact | Demoted to non-headline. A hand check is requested. |
| Model-dependent default is a 2-model contrast, conditioned on address-bearing outputs | Worded as a contrast. Confounds listed. |
| E3b sign flip | Reported both. No promotion. |
| Label independence (terra is tested and an arbiter) | Disclosed. Sol is the primary arbiter. Human labels pending. |
| Novelty positioning | Done in section 7. 2603.26236 is unread. |
| Benchmark gaps | Open (see section 8). |

## 6. Strongest true claim
In a 2-model, machine-labelled, translated-stimulus pilot, a bare keyword string is expanded into an affirmative sentence in German, Spanish and French essentially always (0 to 1 of 40 outputs negated), as in English. Restoring an explicit negation cue removes it (0 to 1 of 40 failures, at most about 2 reversals per 1,000 at pi_neg = 2.7%, versus 27 for always-commit). The register default of the same models differs strongly between a gpt model and a 12B local model (formal-address share in French 8% versus 78%). So "the" default is not a language fact, and a [FORMAL]/[INFORMAL] chip beats a typed plain word by roughly 14 to 18 pp in FR and ES (DE unresolved), at equal tap cost.

Not claimed: any language effect on polarity or register, 6-model replication, chip equivalence to the plain word, the ctxn result, any real-user benefit.

## 7. Novelty and closest prior work
- Polarity: low novelty. Chen et al. 2023 (arXiv 2305.05976) already show LLMs generate positively from keywords. The multilingual extension and the AAC-unit conversion are incremental.
- Register default: partly covered by Ersoy/Ershadi et al., "In What Languages are Generative Language Models the Most Formal?" (arXiv 2302.12299; XGLM and BLOOM, neutral prompts, formal-leaning defaults). Only the abstract was opened.
  - The difference: chat models, an underspecified keyword-expansion task, and an AAC framing.
  - Model dependence of the default, together with the missing-address rate of 37 to 47%, is the modest new observation.
- Chip as a formality control: CoCoA-MT and IWSLT 2022 formality control (from abstracts only). Not novel.
- Conceptual precedent: Wang and Suresh, arXiv 2606.00333 (default as measured object).
- Check before any novelty claim: arXiv 2603.26236 (language-agnostic informal register), which is unread. No search found negation default plus AAC, but the search was shallow.

## 8. Limitations
- 2 of 6 models. No 6-model criterion (E2 range, H4 in 5 of 6, stop rule) was evaluated. Cells have n = 1 to 14. CIs are conditional on the two models.
- Translated stimuli with no native check. Machine labels only, from gpt-family arbiters, with terra both tested and arbiter. The ES detector failed its gate.
- pi_neg and pi_V are assumed. The register SLP weight is borrowed. No acceptability outcome. No real AAC keyword data.
- No implemented published baseline. The leak-filtered plain word has no regeneration arm. A cueing false-negative or false-cue cost was not modelled.
- H5 (politeness) and H6 (code-switching) were not run. Round 2 and 3 are post-pilot plans (pre-output, but amendments).
- No figures or diagrams were produced. The writing passes must supply them: a bare/chip/plain failure-rate panel by language, and a register-default-by-model dot plot with CP intervals.

## 9. Recommended use
1. **CALE-AI (lift by Nov 16): lift a small piece only.**
   - One limitations or "does it transfer?" paragraph plus one small table. Content: the [NOT] chip's gain in DE/ES/FR with the exact bounds, and the French and German register default being model-dependent, with the contrast figure.
   - Label it "pilot, translated stimuli, 2 models, machine labels".
   - Do not include the chip-versus-plain equivalence, ctxn, or Spanish register claims.
   - Cost: one afternoon, with no new data needed.
2. **Journal / new paper: not on this evidence.** The polarity part is a replication of a known bias, and the register part is a 2-model contrast with a prior paper covering the question. It becomes a short paper (register default of chat models for keyword-to-sentence in AAC, with a chip repair) only if three things hold:
   - the 4 queued models run after the GPU resumes (gemma, qwen2.5-7b, llama3.1-8b, qwen2.5-14b), and the model-dependence survives;
   - the human annotation batch (ANNOTATION_REQUEST.md, 271 items, about 20 non-author annotators, 15 to 25 minutes each) validates the translations and the ES labels;
   - a real baseline (a formality-controlled generation prompt) and an acceptability outcome are added.
3. **Do not drop.** The 4-model run is already queued and the finalisers exist (src/frontier_multilingual_r3_finalize.sh and src/frontier_multilingual_r2_finish.sh). If the extra models show the register default is stable across models, the "model-dependent" claim reverses and the frontier shrinks to the CALE-AI paragraph.

Human annotation: requested, not sent (ANNOTATION_REQUEST.md; items in annotation/frontier_multilingual_r3_items.json, key in annotation/frontier_multilingual_r3_key.csv). Spanish annotators go first for the S items. Until labels return, every result is "machine-checked, provisional".

## 10. Follow-up: six-model run (2026-11-03, POST-PILOT; details in `followup.md`)
The four queued models (gemma3-4b, qwen2.5-7b, llama3.1-8b, qwen2.5-14b) were run by the resumed GPU waiter and labelled and analysed by `frontier_multilingual_r2_finish.sh`; Sections 4 to 9 above remain the earlier 2-model text. Six-model criteria applied literally: H4 met (6 of 6 models in EN, DE, ES, FR; restored 97 to 99% vs bare 0 to 1%; chip minus plain word +2.6 to +4.3 pp), E2 model range met (DE 43 pp CI [41, 100]; FR 92 pp CI [71, 100]), no language effect on the default (DE-FR in 0 of 6 models after Holm), R2.9 stop rule met, not promoted.
Does "model-dependent register default" survive? Yes, as "differs by model, not a language property": FR V share ranges from 8% (terra) to 92% (gemma), DE from 7% to 50%. Limits: it is largely terra against five open-weight models (Fisher DE p = .011, FR p < .001, unclustered; among the five alone the DE range is 25 pp), cells have 1 to 14 address-bearing outputs, and many models give no address form at all. Polarity default off the ceiling (ctxq) is also model-dependent (ES negated 18.4% vs EN 1.8%, driven by llama and nemo). No verdict change: stop, no promotion, human labels still needed.
