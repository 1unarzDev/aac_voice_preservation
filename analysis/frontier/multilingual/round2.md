# Frontier multilingual, round 2: matched English, controls, instruments, policies (PARTIAL: 2 of 6 models)

[Superseded in parts by round3.md: E3b wording, INTENT-SIM label, separable-prefix inference, cost accounting, Chen et al. citation.]

Status: machine labels only, translated stimuli, 20 POL + 20 REG families (pilot items frozen). **Round-2 generation exists for gpt-6.1-terra and mistral-nemo-12b only.** The owner paused all AAC GPU waiters (D-084, SIGSTOP, up to 8 h, "Unity first") at 20:23; gemma3-4b, qwen2.5-7b, llama3.1-8b and qwen2.5-14b are queued (stopped inside the flock) and a finish script (src/frontier_multilingual_r2_finish.sh) will label, analyse and re-render `round2_auto_tables.md` and `summary_r2.json` when they complete. Every number below is a TWO-model result (n = 20 families x 2 models = 40 outputs per cell); the 6-model criteria (cross-model range, H4 in 5 of 6 models, the stop rule) are **not evaluated**. Plan: PLAN.md "ROUND-2 ANALYSIS PLAN" (frozen before outputs). Deviations 11-20 in DEVIATIONS.md. Full tables: `round2_auto_tables.md`, `summary_r2.json`, `r2_*.csv`.

## Headline (what can be said now)
1. **The register default is model-dependent, not a language fact.** In French, bare outputs that address the listener are formal in 78% (nemo, 7/9) and 8% (terra, 1/12). In German 45% (5/11) vs 7% (1/14). Spanish is T in 25 of 25 address-bearing outputs for both models, but Spanish is exploratory (detector 94.2% < 95% gate). Single-model language contrasts did not survive Holm correction (nemo DE-FR -32 pp, CI -67 to 0, Holm p = 0.11; terra -1 pp).
2. **Restoring the [NOT] cue removes the silent reversals, in every language and in English.** Bare B outputs are negated 0% (DE, ES), 2% (FR, one output), 0% (EN) of the time; with the chip 100% (DE, ES, FR) and 95% (EN, one family fails for both models). At pi_neg = 2.7%: 27.0 silent reversals per 1,000 messages (always-commit, DE/ES/EN; 26.3 FR) down to 0.0 (DE, ES, FR) and 0.7 (EN) with the chip, at 1 tap per message. Gain lower CI bound >= 88 pp in all four languages, in both models.
3. **Matched English shows no language effect on the polarity default.** Same 20 families, same 2 models, same template, greedy and 5 draws at T=0.7 (sampled n = 200 / 200 / 185 / 196 for EN / DE / ES / FR): P(affirmative | committed) 100 / 100 / 98.9 / 97.4%; difference to English 0.0, -1.1, -2.6 pp, all CIs touching 0, far inside the 10 pp rule. The default is at ceiling in every language; sampling at T=0.7 did not create variance (0 to 5% negated, only nemo in FR and ES).
4. **A plain word cue works for polarity but costs more and leaks; the chip is the better benchmark for register.** Details and benchmarks below.
Not claimed: any language effect; the 6-model replication; a "success" verdict.

## What was done
- Matched English comparator (same families, template P0 with no "write in X" line, greedy + T=0.7 x 5 draws on bare POL and REG), new arms for DE/ES/FR/EN (plain-word negation, legend-equalised register arms), keyword-condition controls (nominal, German separable-prefix verbs, second translator nemo-12b), G1 with a written cue, entropy-ask from the sampled draws. 2,105 requests per model, 0 failures; 199 G1 jobs per model.
- Labels: polarity gpt-6.1-sol blind, direct and translate-then-English route (disagreements excluded, 15 rows); register detector v2 (frozen) + sol arbiter (non-Claude) for ambiguous outputs (1 output). Cluster bootstrap over the 20 families (10,000, seed 20261102). Source reading: see Literature.

## Instruments
**Detector validation E7 (fresh 120 per language, drawn by hash, not tuned, includes no-address outputs; arbiter 1 = gpt-6.1-sol, arbiter 2 = gpt-6.1-terra, text only):**
| language | detector vs arbiter-1 | Wilson 95% | detector "none" that arbiter calls an address form | arbiter-1 vs arbiter-2 | gate (>=95%) |
|---|---|---|---|---|---|
| DE | 117/120 = 97.5% | 92.9-99.1 | 3 of 38 | 100% | pass |
| ES | 113/120 = 94.2% | 88.4-97.1 | 7 of 67 | 99.2% | FAIL (stays exploratory) |
| FR | 120/120 = 100% | 96.9-100 | 0 | 100% | pass |
All disagreements are the detector missing a T or V address form (returns "none"); detector ambiguity was almost never triggered in this sample (0 of 360), so the "ambiguous outputs included" requirement is met only for no-address outputs (38 to 67 per language). The sample comes from 2 models. Human labels: not returned.
**Polarity instrument agreement on the negated class (restored B outputs):** positive agreement 1.000 in DE (n=40), ES (38), FR (40); affirmative class on restored A 1.000. Perfect agreement here means the two routes cannot be separated on these outputs; it does not show the instruments are unbiased.
**Strict translation gate E8:** full-word overlap (>=0.5) under both back-translators and polarity preserved under both: survival DE 40/40, ES 39/40, FR 40/40 (second back-translator was terra not qwen2.5-14b, DEVIATIONS 18; the qwen pass is queued). One drop (ES, overlap). The strict gate does not change the picture; headline numbers were not recomputed on a subset because no family was dropped except the one already dropped.

## H1, unconditional (bare, pooled over terra and nemo, n = 40 outputs per language)
| language | no address form | single register given address | mixed | V share (T/V outputs) |
|---|---|---|---|---|
| DE | 38% (15/40) | 25/25 = 100% | 0 | 24% (6/25) |
| ES (expl.) | 38% | 25/25 = 100% | 0 | 0% (0/25) |
| FR | 48% (19/40) | 21/21 = 100% | 0 | 38% (8/21) |
Commitment given an address form is complete, but 38-48% of bare outputs avoid the question altogether (impersonal, infinitive, first person, pronoun-less forms the detector reads as none), so "the model always commits" is only conditionally true.

## H2, language and model
| model | DE V share | ES (expl.) | FR V share | DE-FR diff [CI], Holm p |
|---|---|---|---|---|
| mistral-nemo-12b | 45% (5/11) | 0% (0/12) | 78% (7/9) | -32 pp [-67, 0], 0.11 |
| gpt-6.1-terra | 7% (1/14) | 0% (0/13) | 8% (1/12) | -1 pp [-23, 19], 1.0 |
Model range within language (2 models): DE 38 pp (CI 4-75), FR 69 pp (CI 33-100). With only 2 models this is a contrast, not a heterogeneity estimate. The matched English comparator has no T/V contrast, so it cannot test the register default; it tests address commitment only (next).
**Register commitment vs English (E3b, declared rule, pronoun-address share):** EN "you" 10% vs DE 25% (+15 pp, CI 0 to 30), ES 30% (+20 pp, CI 2 to 38), FR 28% (+18, CI 0 to 35). By the declared rule the ES difference meets "|diff| >= 15 pp with CI excluding 0", but the v1 lexicons count a few imperative/verb tokens (trae, dame, bist ...) so this is not a pronoun-only measure. The clean pronoun-only variant (added after seeing this, DEVIATIONS 15): DE +15 pp (0 to 30), ES -7.5 pp (-15 to 0), FR +17.5 pp (0 to 35). Verdict (round-3 correction): by the DECLARED rule the ES difference MEETS the rule (+20 pp, CI 2 to 38) and DE/FR do not; the formal PROMOTE trigger is therefore acknowledged, but it rests on an unstable measure (the clean pronoun-only post-hoc variant flips sign for ES: -7.5 pp). No robust commitment claim. Spanish pro-drop makes explicit pronouns rare.

## Register confound control (E6; V share among T/V outputs, pooled address rate)
| language | condition | pooled V share | address rate | nemo | terra |
|---|---|---|---|---|---|
| DE | infinitive (pilot) | 24% | 62% | 45% (n=11) | 7% (n=14) |
| DE | nominal | 20% (n=5) | 12% | 100% (n=1) | 0% (n=4) |
| DE | separable-prefix (infinitive != formal imperative) | 17% | 75% | 17% (n=12) | 17% (n=12) |
| DE | second translator (nemo) | 18% | 42% | 38% (n=8) | 0% (n=9) |
| FR | infinitive (pilot) | 38% | 52% | 78% (n=9) | 8% (n=12) |
| FR | nominal | 67% | 22% | 100% (n=2) | 57% (n=7) |
| FR | second translator | 42% | 50% | 78% (n=9) | 10% (n=10) |
Reading: (i) German separable-prefix keywords gave 17% vs 17% at n=12/12 (description only; round 3 withdraws the inference that this removes the DE gap, the cell is tiny and the keywords were not meaning-checked); (ii) French is unchanged under a second translator (78% vs 10%): the French model dependence is not a translator effect; (iii) nominal keywords nearly eliminate address forms (12-22%), so that condition has no power (n = 1-7). The nemo-translated Spanish strings contain meaning errors (DEVIATIONS 19). The 6-model "survives the control" rule is not evaluable.

## Cue benchmarks (E5, pooled over 2 models; share of requested register among all outputs; paired CI)
| language, request | chip | plain word (legend-equalised) | context (legend-equalised) | chip - plain_x | chip - ctx_x |
|---|---|---|---|---|---|
| DE formal | 92% | 82% | 57% | +10 [-3, 25] | +35 [20, 50] |
| ES formal | 92% | 62% | 32% | +30 [12, 48] | +60 [45, 75] |
| FR formal | 92% | 75% | 55% | +18 [5, 30] | +38 [25, 50] |
| DE informal | 90% | 85% | 68% | +5 [-7, 17] | +22 [10, 38] |
| ES informal | 88% | 82% | 70% | +5 [0, 12] | +18 [7, 30] |
| FR informal | 72% | 62% | 52% | +10 [-3, 22] | +20 [10, 30] |
Equalising the legend (the plain and context arms now see the same extended legend as the chip arm) shrinks the chip's lead over the plain word (the pilot's confound was real: chip - plain was larger before equalising, e.g. ES formal address rate 35% -> 65%), but the chip still wins in ES-formal and FR-formal and the context cue is clearly weaker. Plain-word leakage: the cue word itself appears in the output sentence in 15-50% of plain-word outputs (DE 15-18%, ES 25-50%, FR 28-30%, pooled over both models; e.g. nemo "Bitte bringen Sie das Paket formal.", "Traeré gafas formales."), a defect the chip does not have. Machine naturalness (sol 1-5, E10) is 0.8-1.1 lower for plain formal than bare (CI excluding 0) and unchanged for chips (|diff| <= 0.1, CIs include 0).
**FR-informal chip failure (79% pilot; 72% here):** nemo writes V in 5 of 20 outputs and none in 4, with "s'il vous plait" (3) and "Apportez/Laissez" imperatives; terra writes T in 18 of 20. The failure is a politeness-phrase habit ("s'il vous plait" paired with [INFORMAL]) and formal imperative defaults in the weaker local model; the 6-model split (gemma, qwen, llama) is pending.

## AAC units and policy benchmarks (same items, 2 models pooled; SLP NEG weight 1.0 for polarity; register weight is BORROWED from politeness 0.5 and is an approximation)
Polarity, silent reversals per 1,000 messages at pi_neg = 2.7% (sensitivity 0.5% and 10% in `r2_policies.csv`, scales linearly), taps per 1,000 messages:
| policy | EN | DE | ES | FR |
|---|---|---|---|---|
| always-commit (bare) | 27.0 | 27.0 | 27.0 | 26.3 |
| entropy-ask (5 draws split) | 27.0 (0 taps) | 27.0 (0) | 26.3 (27 taps) | 25.0 (75) |
| random-ask matched to entropy rate | about the same | about the same | 26.3 | 24.4 |
| plain word "not" (3 keystroke-equivalents) | 1.4 (3,000 taps) | 0.7 | 2.2 | 0.7 |
| chip, always-ask | 0.7 (1,000 taps) | 0.0 | 0.0 | 0.0 |
| G1 with a written cue (upper bound, 1 tap for the cue) | 0.0 | 0.0 | 0.0 | 0.0 |
Entropy-ask (a sampled-vote ask baseline, own implementation; the earlier 'INTENT-SIM' label was unverified and is dropped) asks almost never because the model is confidently wrong: all 5 draws are affirmative, so it removes 0 to 1.3 of 27 reversals. That is a method result: self-consistency cannot detect a default bias. G1 with a written cue repaired every output (monitor fired on 38 to 40 of 40 B outputs per language, 0 left bad after at most 2 retries) but needs the cue to be written first, i.e. it is the chip with a verification step.
Register mismatch per 1,000 messages at pi_V = 0.5 (a mismatch is an address form of the wrong register; no ground-truth prior is available, `r2_policies.csv` has the grid 0.1-0.9), taps per 1,000:
| policy | DE | ES (expl.) | FR |
|---|---|---|---|
| always-commit (bare) | 312 | 312 | 262 |
| ask-if-address-form | 0 (625 taps) | 0 (625) | 38 (525) |
| random-ask matched to that rate | 117 | 117 | 158 |
| always-ask chip | 0 (1,000) | 0 (1,000) | 62 (1,000) |
| plain word, legend-equalised (3,000 taps-equiv.) | 25 | 12 | 125 |
| context cue, legend-equalised | 0 | 138 | 62 |
| entropy-ask, T/V split | 200 (225 taps) | 312 (0) | 162 (275) |
| G1 with a written cue (1,000 taps) | 0 | 0 | 0 |
Ask-if-address beats random-ask at the same ask rate by 11.7 pp (DE), 11.7 pp (ES) and 12.0 pp (FR) of mismatches (paired CI excluding 0 in all three), and reaches the chip's error level with 38-48% fewer taps; this holds because the policy asks exactly when an address form exists. Entropy-ask is the weakest ask policy. Where it does NOT help: chip and ask-if-address still leave 38-62 mismatches per 1,000 in French (the FR-informal failure); mismatch counts treat no-address outputs as harmless, which flatters ask-if-address; the 0 values are at a ceiling with n = 40 per cell, so CIs on 0 are [0,0] and these are floor results, not proof of zero.

## Literature (verified reading, 2026-11-02)
- Chen, Shi, Fu, Cheng, Li, Xiao, "Say What You Mean! Large Language Models Speak Too Positively about Negative Commonsense Knowledge", ACL 2023 (arXiv 2305.05976; abstract opened): keyword-to-sentence generation shows a positivity bias (models fail to produce valid negative-knowledge sentences) while the same models answer yes/no questions correctly. Our polarity default (bare keywords -> affirmative) is an instance of this known bias in an AAC unit setting and in DE/ES/FR; it is not a new discovery.
- Ersoy, Vizcarra, Mayeesha, Muller, "In What Languages are Generative Language Models the Most Formal? Analyzing Formality Distribution across Languages", arXiv 2302.12299 (2023), abstract opened (the director's brief spelled the name "Ershadi"; the verified authors are Ersoy et al.). XGLM and BLOOM, five languages, 1,200 labelled outputs per language; "highly biased toward the formal style when prompted neutrally"; behaviour differs strongly between models and languages. This supports our finding that the default is model- and language-specific, but it measures formality of free continuations in base models, not chat-model commitments in a keyword-to-sentence task; its language list was not fully visible in the abstract page, so we cite only the model, language-count and bias statements.
- Nadejde, Currey, Hsu, Niu, Federico, Dinu, "CoCoA-MT: A Dataset and Benchmark for Contrastive Controlled MT with Application to Formality", Findings of NAACL 2022, pp. 616-632 (abstract opened): formal/informal controlled translation into six languages, accuracy 82% in-domain and 73% out-of-domain with small supervised data.
- IWSLT 2022 formality track (findings paper, section 7; read via search results and the task page, not the full paper): EN to DE, ES, HI, JA (constrained), IT, RU (zero-shot), systems control formality with high automatic accuracy (average 92.9 to 99.4 across languages), Japanese hardest, "a clear bias toward one formality level" noted in some results; human evaluation agreed with the automatic metric.
Positioning: the chip is an explicit attribute control in the sense of this line of work (a formality tag) applied to AAC keyword expansion; it is not a methodological novelty. What is specific here is the audit design (assume vs violate vs lose), the unconditional commitment split, the legend-equalised comparison with a plain word, and scoring ask/assume policies in AAC units. The entropy-ask and G1 baselines are our own implementations.

## Stop rule (director's) and status
Not evaluable: H4 holds in 2 of 2 models (>= 88 pp lower bound, every language and English), but the criterion is 5 of 6; H2 model dependence is shown for 2 models (FR 69 pp) but not for the 6-model range. Matched English shows no language effect on polarity (measured at ceiling and under T=0.7 sampling) and no robust effect on commitment, so the promotion trigger is not met so far. Current reading if the remaining models do not change it: robustness/null result for the polarity default plus the model-dependent register default, with the chip benchmarked against the plain word, the context cue, entropy-ask and G1.

## Human annotation (built, not sent)
`ANNOTATION_REQUEST.md` (pilot items) is unchanged; round-2 items are built: annotation/frontier_multilingual_r2_items.json (375 items: 60 register outputs per language from the E7 sample, 20 polarity outputs per language, 135 keyword strings of the nominal, separable and second-translator conditions) and annotation/frontier_multilingual_r2_key.csv (key, never shown). Questions: address form (informal/formal/none/mixed), natural 1-5, same message core yes/partly/no, contains negation or register marker, polarity. About 20 adult non-author annotators across DE/ES/FR (6-9 per language; Spanish first because the ES detector failed), about 20 minutes each; no AAC users, no SLPs, no IRB. Feeds: kappa(human, detector/judge) per language, the ES gate, translation acceptance of the control keywords.

## Not done / problems
- 4 of 6 models missing (GPU paused by the owner; see top). Single-model contrasts at n of 9 to 14 per cell are underpowered; Holm over 2 tests only.
- No second Claude/human arbiter; arbiters are gpt-6.1-sol and terra (the labelling family is also a tested model family: terra is both a tested model and an arbiter of the other arbiter), so label independence is limited. Human check pending.
- Spanish stays exploratory (94.2%); ES "V = 0%" may partly be detector misses (7 of 67 "none" outputs were address forms).
- The plain-word naturalness drop partly reflects the word leaking into the sentence; naturalness is a machine judge only (no human acceptability yet).
- No figures produced yet (diagrams are for the writing passes). English REG has only the bare arm; "formality" in English is not a T/V contrast.
- Examples (real outputs): FR family "la lumière gêne": bare "La lumière me gêne." / restored [NOT] "Il n'y a pas de lumière qui gêne." (nemo; a negated output with a shifted meaning) / plain word "La lumière ne me gêne pas." Register: nemo with plain word formal, DE: "Bitte bringen Sie das Paket formal." (word leaks); terra ES plain formal: "Podría traer los formularios, por favor?".
