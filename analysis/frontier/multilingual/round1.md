# Frontier multilingual, round 1 (Stage 0 pilot): register and polarity defaults in German, Spanish, French

Status: PILOT / AUDIT. Translated stimuli (not native keyword behaviour), 20 polarity + 20 register families per language, 3 models, greedy decoding, machine labels only (no human check yet; see ANNOTATION_REQUEST.md). Plan: PLAN.md (frozen before outputs). Deviations: DEVIATIONS.md (10 items, including one detector revision). Nothing here is a human-subjects result.

## What was run
- Items: hw1 CC BY families; 20 POL by sha256("ml1|id") order, 20 REG by sha256("ml1reg|id") order. Forward translation gpt-6.1-terra, blind back-translation gpt-6.1-sol, gates (a) polarity preserved, (b) no negation/register word in keywords, (c) keyword overlap >= 0.5. Survival: DE 40/40, FR 40/40, ES 39/40 (POL pol-059 dropped, overlap). Drop rate under 3%, far above the 70% gate, but this is only the machine back-translation gate (human check pending).
- Prompts: P0-L (P0 template and legend unchanged + "Write the sentence in X."), P0-LL (whole template and legend translated, bare only). 716 requests per model (200 DE, 197 ES, 200 FR for P0-L plus 119 P0-LL). Models: gemma3-4b and mistral-nemo-12b (local, one server at a time under the blocking GPU lock), gpt-6.1-terra via codex-lb. Greedy, max_tokens 96. 2,148 generations, 0 failures.
- Arms. POL: bare, restored ([YES]/[NOT]). REG: bare, chip ([FORMAL]/[INFORMAL], legend extended for those arms only), plain word (formell/formal/formel and informal), context ("Gespraech mit dem Arzt" vs "... dem besten Freund", neutral noun phrases).
- Labels. Register: deterministic detector (src/frontier_multilingual_register.py) + blind arbiter (the engineer agent reading shuffled output text only) for detector-ambiguous outputs. Polarity: blind gpt-6.1-sol, direct target-language route and translate-then-English route, disagreements to the arbiter (3 texts of 700 unique, all "affirmative"). Family-cluster bootstrap, 10,000 resamples, seed 20261102 (3,000 for arm tables). Note: when every output is the same label the bootstrap CI collapses to [1,1]; exact Clopper-Pearson intervals are given for H1.

## Gates (Stage 0 go/no-go)
| gate | DE | ES | FR | verdict |
|---|---|---|---|---|
| translation survival (>=70%) | 100% | 97.5% | 100% | pass |
| polarity route kappa (>=0.85), direct vs translate-then-English, n unique texts 174/172/177 | 0.986 | 0.973 | 1.000 | pass |
| register detector v1 vs blind arbiter, 40 random non-ambiguous | 87.5% | 67.5% | 82.5% | FAIL (all errors: pronoun-less imperatives and 2sg verb forms returned "none") |
| register detector v2 (single revision), FRESH 40 per language | 100% | 90% | 100% | DE and FR pass; ES FAIL (misses future 2sg "Enviaras" and misspelled imperative "Envia") |

Go/No-go: GO (translation and polarity gates pass in all 3, detector gate passes in 2 of 3). Spanish register results are EXPLORATORY and flagged. The 120-per-language validation size in the plan was reduced to 40 (DEVIATIONS 5); the 90% for Spanish therefore has a wide interval (36/40).

## Results

### H1: register commitment with no register cue (bare, P0-L, three models pooled)
| language | outputs | with an address form | committed T | committed V | mixed | no address form | commit share (exact 95% CI) |
|---|---|---|---|---|---|---|---|
| DE | 60 | 35 | 24 | 11 | 0 | 25 (42%) | 35/35 = 100% (90-100) |
| ES (exploratory) | 60 | 26 | 26 | 0 | 0 | 34 (57%) | 26/26 = 100% (87-100) |
| FR | 60 | 33 | 14 | 19 | 0 | 27 (45%) | 33/33 = 100% (89-100) |
Across all three: 94/94 address-bearing outputs commit to exactly one register, none mixed (exact lower bound 96%). H1 holds at the pooled level (>=95%) in DE and FR (confirmatory) and ES (exploratory). Cell-level (model x language) point estimates are all 100% but cells have only 1-14 address-bearing outputs, so the 90% cell criterion cannot be demonstrated (lower bounds 70-93%); report as consistent, not proven, at cell level. IMPORTANT qualifier: 42-57% of bare outputs contain no second-person form at all (impersonal "Ich bringe ein Paket", infinitives "Traer un paquete, por favor", or first-person). These outputs avoid the register question and are not errors; the REG keyword strings do not force address, and the Spanish "none" share is likely inflated because Spanish unmarked 2sg forms are partly undetected (gate failure).

### H2: the default direction differs by language and by model (V-share among address-bearing bare outputs)
| model | DE | ES (expl.) | FR |
|---|---|---|---|
| gemma3-4b | 5/10 = 50% | 0/1 | 11/12 = 92% |
| mistral-nemo-12b | 5/11 = 45% | 0/12 = 0% | 7/9 = 78% |
| gpt-6.1-terra | 1/14 = 7% | 0/13 = 0% | 1/12 = 8% |
| pooled | 31% (n=35) | 0% (n=26) | 58% (n=33) |
Language effect (V share DE minus FR, cluster bootstrap 95% CI): gemma3-4b -41.7 pp [-75, -3], nemo -32.3 pp [-67, 0], terra -1 pp [-23, 19], pooled -26.1 pp [-44, -10]. H2 criterion (>= 30 pp in at least one model with CI excluding 0, using the two languages that passed validation) is MET for gemma3-4b only; nemo is borderline (CI touches 0) and terra shows no language effect. Model effect within a language is as large: in French gemma V 92% vs terra V 8% (84 pp), in German nemo 45% vs terra 7%. So "the default" is not a language fact; it is model-dependent. The same model can also flip between languages (gemma: DE 50% V, FR 92% V). Small n: each cell 1-14.
Exploratory side observation (not a generation result): terra as TRANSLATOR rendered the 20 "you" source sentences with T in DE 19/20, FR 5/20 T (15 V), ES 13 T and 7 no-pronoun forms; a hint that the translated stimuli themselves carry the translator's register default (this is why the translated A sources were not used as generation prompts).

### H3: polarity default replication (bare keywords, B families, pooled over models)
| language | affirmative share of committed bare outputs | English, same families and models | difference | negated outputs |
|---|---|---|---|---|
| DE | 60/60 = 100% | 48/48 = 100% | 0.0 pp (CI approx [0, 0]) | 0 |
| ES | 57/57 = 100% | 45/45 = 100% | 0.0 pp | 0 |
| FR | 59/60 = 98.3% (CI 95-100) | 48/48 = 100% | -1.7 pp (CI approx [-5, 0]) | 1 (nemo) |
The English default replicates in all three languages; the non-inferiority margin of 5 pp holds for DE and ES, and for FR the lower CI bound sits at -5 pp (borderline). "Unclear" outputs: 0. P0-LL (fully translated prompt) gives 60/60, 57/57, and the same all-affirmative pattern, so the result is not an artefact of the English prompt wrapper. English comparison n is smaller (some English judge rows are missing; only agreeing J1/J2 labels used). No language effect on polarity was found (no claim of a language difference).

### H4: cue restoration transfers
Polarity ([NOT] on B families, same items): negated rate 98.3% (DE), 98.2% (ES), 98.3% (FR) vs bare 0%; paired gain 98.3 / 98.2 / 96.7 pp, CI lower bounds 95 / 94.7 / 91.7 pp. Per model gain lower CI bound: gemma 85 / 84 / 85 pp, nemo and terra 85-100 pp. H4 (>= 50 pp lower bound) holds in every one of the 3 models x 3 languages tested (the plan's 6-model criterion is not tested, only 3 models). [YES] on A families: 100% affirmative except nemo ES 94.7%.
Register (match to requested register among outputs with an address form; address-bearing rate in parentheses; pooled over 3 models):
| arm | DE | ES (expl.) | FR |
|---|---|---|---|
| chip FORMAL | 100% (90%) | 100% (90%) | 100% (92%) |
| chip INFORMAL | 98% (82%) | 100% (82%) | 79% (80%) |
| plain word formal | 97% (63%) | 80% (33%) | 100% (65%) |
| plain word informal | 90% (70%) | 100% (55%) | 61% (63%) |
| context formal | 97% (55%) | 61% (60%) | 98% (67%) |
| context informal | 100% (70%) | 100% (62%) | 86% (73%) |
Chips restore the formal register in all languages and models (100% when an address form is produced) and the informal register in DE and ES; they FAIL for informal French in the two local models (gemma 64%, nemo 69%; terra 100%), which keep writing "s'il vous plait" with [INFORMAL]. Plain word and context cues are weaker than the chip (lower address rate, e.g. ES plain formal 33% of outputs carry an address form; ES context formal only 15% matched in nemo). H4's register clause (>= 90% requested register) holds for chips in DE and ES, not FR-informal; plain/context not in all cells. Even with the chip, 8-20% of outputs contain no address form at all (cue restored but nothing to apply it to).

## Improvement in AAC terms and benchmarks (same items; policies.csv)
Polarity, pi_neg = 2.7% (sensitivity 0.5%, 10% in policies.csv), SLP weight NEG = 1.0 (both SLP raters severity 5; the weight table is in slp_weights_and_translator.json; POL weight 0.5):
| policy (pooled, per 1,000 messages) | silent reversals DE / ES / FR | taps |
|---|---|---|
| always-commit (bare, = what the app does without a cue) | 27.0 / 27.0 / 26.6 | 0 |
| G1 guard without a written cue | same as always-commit (cannot fire; not run, declared in plan) | 0 |
| random-ask p = 0.25 / 0.5 / 0.75 (expected) | about 20 / 13.7 / 7.1 | 250 / 500 / 750 |
| always-ask = cue chip | 0.45 / 0.47 / 0.45 | 1000 |
So the cue chip removes about 98% of silent polarity reversals in each language (27 down to under 0.5 per 1,000), the same size as in English, but needs one tap per message; random asking only buys reversals down linearly. Same as English: the benefit comes from the chip and costs taps; no language is spared.
Register has no ground truth, so no single error number is claimed. Mismatch per 1,000 messages is shown as a grid over the prior pi_V = P(listener needs V) (policies.csv). Example pi_V = 0.5 (DE / FR): always-commit mismatch 292 / 275 per 1,000, always-ask chip 8 / 83, ask-only-when-an-address-form-appears 6 / 57 with 583 / 550 taps per 1,000; random-ask p = 0.5 gives 150 / 179 (taps 500). The rule "ask only when the output addresses the listener" is the best trade here (as it asks about 55-58% of messages, not 100%), but it needs the model to show the address form first (implementable by detecting the form in the generated sentence). Break-even: for any committed default the default beats the opposite constant register iff pi_V is on the same side of 0.5 as its default (e.g. T default is better only if the listener needs V with probability < 50%); since pi_V is unknown for real AAC use, committing silently is not defensible. Weighted by the POL weight (0.5) as an approximation, no SLP rating on register exists.

## Where it does NOT help or is not shown
- Polarity: nothing differs from English; no language-specific hazard found. The pilot cannot rule out small differences (items 20, n per cell small).
- Register: bare outputs often avoid address, the per-cell n is 1-14, the Spanish register labels failed validation, informal French is not restored by chip, plain word or context (local models), and plain/context cues are weaker than the chip. Chip vs plain word are NOT equal here (chip better), unlike the English D-070 result: Spanish plain formal 33% vs chip 90% address rate.
- Always-ask costs 1,000 taps per 1,000 messages.

## Not done (so not claimed)
Stage 1 (50 families, 6 models, d2 replication), PLT/H5 politeness markers, CS/H6 code-switching, the "full" (typed sentence) arm, G1 with a written cue as an upper bound, entropy-ask (INTENT-SIM style) baseline, acceptability/fluency judging (only the annotation request covers it), and the formality-controlled-MT literature (IWSLT) reading TODO from PLAN Sec. 0. The "closest published method" benchmark is the explicit-attribute control arm (chip/plain word, formality-controlled MT style); the ask-when-uncertain method is NOT implemented, so that comparison is open.

## Verdict against PLAN Sec. 7
Pilot-level SUCCESS for promotion to Stage 1: H1 holds in DE and FR (and ES exploratory); H2 shown for one model (gemma3-4b DE vs FR, CI excludes 0) and model-dependence is large; H3 shows no language effect (the polarity default replicates); H4 holds for polarity in all 3 languages and for register chips in 2 of 3 languages (FR informal fails). Machine labels only: not human-checked; Spanish register exploratory; 3 of 6 models.

## Problems and caveats
- GPU lock was held by other jobs for about 50 min before the local run; the run itself took about 5 min per model. API: no failures. Terra is not exactly reproducible at T=0 (HANDOFF); outputs are the cached ones used.
- Detector revision after seeing validation failures (logged, DEVIATIONS 10); v2 in-sample 120/120 is NOT a validation; the fresh-sample result is.
- The arbiter is the engineer agent (a Claude model) reading text only, not an independent panel; the detector v2 lexicon was written after reading that arbiter's v1 labels, so v2 is tuned to my labelling conventions (for instance "Podria" questions to the listener = V); human annotators may disagree (ES especially).
- Labelling stimuli only machine-checked: translations may have unnatural keyword strings; register keywords are infinitives as instructed.
- Examples (real outputs; first three REG families in hash order, bare, then chip FORMAL):
  - hw-act-052 "bringen Paket": gemma "Ich bringe ein Paket." (none) / chip "Sie bringen ein Paket."; nemo "Bitte bringen Sie das Paket." (V) ; terra "Bringst du das Paket?" (T) / chip "Bringen Sie das Paket."
  - hw-act-052 "apporter colis" FR: gemma "Apportez le colis, s'il vous plait." (V); terra "Apporte le colis." (T); with [INFORMAL] nemo still "Apportez le colis, s'il vous plait." (V).
  - hw-plt-006 "traer gafas" ES: gemma "Traer las gafas, por favor." (none), nemo "Trae mis gafas, por favor." (T), terra "Trae las gafas." (T); chip FORMAL terra "Podria traerme las gafas?" (V).
