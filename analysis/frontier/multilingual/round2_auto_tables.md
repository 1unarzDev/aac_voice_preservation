# Round-2 auto tables (models with data: gemma3-4b, mistral-nemo-12b, qwen2.5-7b, llama3.1-8b, qwen2.5-14b, gpt-6.1-terra; rows 14914)

## E1 register commitment, bare, unconditional (P(no address) | P(single register | address) | n address / n outputs | V share among T/V)

| scope | DE | ES | FR |
|---|---|---|---|
| pooled | none 55% / single 100% / 54of120 / V 35% (n=54) | none 75% / single 100% / 30of120 / V 7% (n=30) | none 67% / single 100% / 40of120 / V 60% (n=40) |
| gemma3-4b | none 50% / single 100% / 10of20 / V 50% (n=10) | none 95% / single 100% / 1of20 / V 0% (n=1) | none 40% / single 100% / 12of20 / V 92% (n=12) |
| mistral-nemo-12b | none 45% / single 100% / 11of20 / V 45% (n=11) | none 40% / single 100% / 12of20 / V 0% (n=12) | none 55% / single 100% / 9of20 / V 78% (n=9) |
| qwen2.5-7b | none 45% / single 100% / 11of20 / V 45% (n=11) | none 100% / single nan% / 0of20 / V nan% (n=0) | none 80% / single 100% / 4of20 / V 75% (n=4) |
| llama3.1-8b | none 80% / single 100% / 4of20 / V 50% (n=4) | none 90% / single 100% / 2of20 / V 100% (n=2) | none 95% / single 100% / 1of20 / V 100% (n=1) |
| qwen2.5-14b | none 80% / single 100% / 4of20 / V 25% (n=4) | none 90% / single 100% / 2of20 / V 0% (n=2) | none 90% / single 100% / 2of20 / V 50% (n=2) |
| gpt-6.1-terra | none 30% / single 100% / 14of20 / V 7% (n=14) | none 35% / single 100% / 13of20 / V 0% (n=13) | none 40% / single 100% / 12of20 / V 8% (n=12) |

## E2 language contrasts (V-share difference, cluster bootstrap CI, Holm p)
| test | diff | 95% CI | p_holm | confirmed (Holm<.05 and >=30pp) |
|---|---|---|---|---|
| gemma3-4b|de-fr | -41.7 pp | -75 to -5 | 0.182 | False |
| mistral-nemo-12b|de-fr | -32.3 pp | -67 to 0 | 0.283 | False |
| qwen2.5-7b|de-fr | -29.5 pp | -75 to 33 | 1.000 | False |
| llama3.1-8b|de-fr | -50.0 pp | -100 to 0 | 1.000 | False |
| qwen2.5-14b|de-fr | -25.0 pp | -100 to 50 | 1.000 | False |
| gpt-6.1-terra|de-fr | -1.2 pp | -23 to 19 | 1.000 | False |

Model range of V-share within language: de: 43 pp (CI 41-100); es: 100 pp (CI 0-100); fr: 92 pp (CI 71-100)

## E3 polarity default vs matched English (P(affirmative | committed) / P(negated | all) / diff vs EN [CI])
| draw | scope | EN | DE | ES | FR |
|---|---|---|---|---|---|
| greedy | pooled | 100.0% / neg 0.0% n=120 | 99.2% / neg 0.8% / d -0.8 [-2.5,0.0] n=120 | 99.1% / neg 0.9% / d -0.9 [-2.8,0.0] n=114 | 99.2% / neg 0.8% / d -0.8 [-2.5,0.0] n=119 |
| greedy | gemma3-4b | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 |
| greedy | mistral-nemo-12b | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 95.0% / neg 5.0% / d -5.0 [-15.0,0.0] n=20 |
| greedy | qwen2.5-7b | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 |
| greedy | llama3.1-8b | 100.0% / neg 0.0% n=20 | 95.0% / neg 5.0% / d -5.0 [-15.0,0.0] n=20 | 94.7% / neg 5.3% / d -5.3 [-16.7,0.0] n=19 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 |
| greedy | qwen2.5-14b | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 |
| greedy | gpt-6.1-terra | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 |
| sampled | pooled | 100.0% / neg 0.0% n=600 | 99.3% / neg 0.7% / d -0.7 [-1.8,0.0] n=596 | 99.3% / neg 0.7% / d -0.7 [-1.6,0.0] n=568 | 98.8% / neg 1.2% / d -1.2 [-2.5,-0.2] n=593 |
| sampled | gemma3-4b | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=95 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 |
| sampled | mistral-nemo-12b | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 97.9% / neg 2.1% / d -2.1 [-6.7,0.0] n=95 | 94.9% / neg 5.1% / d -5.1 [-12.2,0.0] n=98 |
| sampled | qwen2.5-7b | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=95 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 |
| sampled | llama3.1-8b | 100.0% / neg 0.0% n=100 | 96.0% / neg 4.0% / d -4.0 [-11.1,0.0] n=100 | 97.9% / neg 2.1% / d -2.1 [-5.3,0.0] n=95 | 98.0% / neg 2.0% / d -2.0 [-6.0,0.0] n=100 |
| sampled | qwen2.5-14b | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=93 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=97 |
| sampled | gpt-6.1-terra | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=96 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=95 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=98 |

## E3b pronoun-address vs English (P(you) EN; target pronoun-address; diff [CI])
| scope | DE | ES | FR |
|---|---|---|---|
| pooled | EN 5% / DE 22% / d 17 [7,27] | EN 5% / ES 13% / d 8 [2,15] | EN 5% / FR 18% / d 12 [4,21] |
| gemma3-4b | EN 0% / DE 30% / d 30 [10,50] | EN 0% / ES 0% / d 0 [0,0] | EN 0% / FR 45% / d 45 [25,65] |
| mistral-nemo-12b | EN 20% / DE 30% / d 10 [-15,35] | EN 20% / ES 40% / d 20 [-5,45] | EN 20% / FR 45% / d 25 [-5,50] |
| qwen2.5-7b | EN 5% / DE 30% / d 25 [10,45] | EN 5% / ES 0% / d -5 [-15,0] | EN 5% / FR 0% / d -5 [-15,0] |
| llama3.1-8b | EN 5% / DE 15% / d 10 [-10,30] | EN 5% / ES 10% / d 5 [-10,20] | EN 5% / FR 5% / d 0 [-15,15] |
| qwen2.5-14b | EN 0% / DE 5% / d 5 [0,15] | EN 0% / ES 10% / d 10 [0,25] | EN 0% / FR 0% / d 0 [0,0] |
| gpt-6.1-terra | EN 0% / DE 20% / d 20 [5,40] | EN 0% / ES 20% / d 20 [5,40] | EN 0% / FR 10% / d 10 [0,25] |

## E4 cue restoration (B families): negated rate restored / bare / plain word; gain CI lower bound
| scope | EN | DE | ES | FR |
|---|---|---|---|---|
| pooled | 97% / 0% / plain 93%; gain lo 93 pp | 99% / 1% / plain 95%; gain lo 96 pp | 99% / 1% / plain 96%; gain lo 94 pp | 99% / 1% / plain 95%; gain lo 96 pp |
| gemma3-4b | 95% / 0% / plain 100%; gain lo 85 pp | 95% / 0% / plain 90%; gain lo 85 pp | 95% / 0% / plain 95%; gain lo 83 pp | 95% / 0% / plain 72%; gain lo 85 pp |
| mistral-nemo-12b | 95% / 0% / plain 85%; gain lo 85 pp | 100% / 0% / plain 95%; gain lo 100 pp | 100% / 0% / plain 84%; gain lo 100 pp | 100% / 5% / plain 95%; gain lo 85 pp |
| qwen2.5-7b | 100% / 0% / plain 95%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp |
| llama3.1-8b | 95% / 0% / plain 80%; gain lo 85 pp | 100% / 5% / plain 85%; gain lo 85 pp | 100% / 5% / plain 100%; gain lo 83 pp | 100% / 0% / plain 100%; gain lo 100 pp |
| qwen2.5-14b | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp |
| gpt-6.1-terra | 95% / 0% / plain 100%; gain lo 85 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp |

Models meeting the >=50 pp lower-bound criterion: en: 6/6; de: 6/6; es: 6/6; fr: 6/6

Instrument agreement (direct vs translate-then-English), positive agreement on the NEGATED class (restored B) and the affirmative class (restored A):
- DE: negated PA 1.000 (direct 119, route 119, both 119, n=120); affirmative PA 1.000 (n=120)
- ES: negated PA 1.000 (direct 113, route 113, both 113, n=114); affirmative PA 1.000 (n=114)
- FR: negated PA 1.000 (direct 119, route 119, both 119, n=120); affirmative PA 1.000 (n=120)

## E5 register cues, pooled (match among address / address rate / match of all)
| lang, requested | chip | plain | ctx | plain_x (legend-eq.) | ctx_x |
|---|---|---|---|---|---|
| DE formal | 100% / 87% / 87% | 95% / 54% / 52% | 91% / 47% / 42% | 94% / 73% / 69% | 93% / 48% / 44% |
| DE informal | 99% / 72% / 72% | 91% / 53% / 48% | 98% / 52% / 52% | 94% / 64% / 60% | 100% / 57% / 57% |
| ES formal | 95% / 72% / 69% | 80% / 25% / 20% | 59% / 34% / 20% | 95% / 53% / 51% | 61% / 38% / 23% |
| ES informal | 100% / 70% / 70% | 100% / 38% / 38% | 98% / 39% / 38% | 100% / 60% / 60% | 96% / 44% / 42% |
| FR formal | 100% / 86% / 86% | 100% / 42% / 42% | 98% / 49% / 48% | 100% / 62% / 62% | 97% / 49% / 48% |
| FR informal | 88% / 78% / 68% | 59% / 41% / 24% | 82% / 51% / 42% | 64% / 61% / 39% | 76% / 55% / 42% |

Chip minus legend-equalised cues, match of all outputs (paired, pooled):
- DE formal: chip-plain_x 18 pp [9,26]; chip-ctx_x 43 pp [31,54]
- DE informal: chip-plain_x 12 pp [4,20]; chip-ctx_x 14 pp [6,23]
- ES formal: chip-plain_x 18 pp [6,31]; chip-ctx_x 46 pp [37,55]
- ES informal: chip-plain_x 10 pp [2,18]; chip-ctx_x 27 pp [18,38]
- FR formal: chip-plain_x 24 pp [13,35]; chip-ctx_x 38 pp [29,47]
- FR informal: chip-plain_x 29 pp [18,41]; chip-ctx_x 27 pp [18,34]

FR-informal chip outputs by model: {"gemma3-4b": {"labels": {"none": 6, "V": 5, "T": 9}, "V_trigger_tokens": {"s'il vous pla": 5, "vous": 5}, "examples_V": ["Éteindre la lumière, s'il vous plaît.", "Éteindre la lampe, s'il vous plaît.", "Coupez le sandwich, s'il vous plaît."], "n": 20}, "mistral-nemo-12b": {"labels": {"V": 5, "T": 11, "none": 4}, "V_trigger_tokens": {"s'il vous pla": 3, "vous": 3}, "examples_V": ["Apportez le colis, s'il vous plaît.", "Laissez le colis ici.", "Apportez le dossier, s'il vous plaît."], "n": 20}, "qwen2.5-7b": {"labels": {"T": 17, "V": 1, "none": 2}, "V_trigger_tokens": {}, "examples_V": ["Coupez le sandwich."], "n": 20}, "llama3.1-8b": {"labels": {"T": 9, "none": 11}, "V_trigger_tokens": {}, "examples_V": [], "n": 20}, "qwen2.5-14b": {"labels": {"T": 18, "none": 2}, "V_trigger_tokens": {}, "examples_V": [], "n": 20}, "gpt-6.1-terra": {"labels": {"T": 18, "none": 2}, "V_trigger_tokens": {}, "examples_V": [], "n": 20}}

## E6 keyword-condition controls (V share among T/V; n in parentheses; pooled address rate)
| lang | condition | pooled V | address rate | gemma3-4b | mistral-nemo-12b | qwen2.5-7b | llama3.1-8b | qwen2.5-14b | gpt-6.1-terra | model range |
|---|---|---|---|---|---|---|---|---|---|---|
| de | bare | 35% (22-48) | 45% | 50% (n=10) | 45% (n=11) | 45% (n=11) | 50% (n=4) | 25% (n=4) | 7% (n=14) | 43 pp (41-100) |
| de | bare_nom | 57% (25-86) | 12% | 75% (n=4) | 100% (n=1) | 67% (n=3) | 100% (n=2) | NA (n=0) | 0% (n=4) | 100 pp (60-100) |
| de | bare_sep | 25% (14-38) | 53% | 44% (n=9) | 17% (n=12) | 14% (n=7) | 67% (n=6) | 0% (n=5) | 17% (n=12) | 67 pp (40-100) |
| de | bare_kw2 | 36% (22-54) | 28% | 43% (n=7) | 38% (n=8) | 75% (n=8) | NA (n=0) | 0% (n=1) | 0% (n=9) | 75 pp (44-100) |
| de | bare_x | 30% (18-41) | 44% | 33% (n=9) | 58% (n=12) | 30% (n=10) | 75% (n=4) | 0% (n=4) | 0% (n=14) | 75 pp (50-100) |
| es | bare | 7% (0-18) | 25% | 0% (n=1) | 0% (n=12) | NA (n=0) | 100% (n=2) | 0% (n=2) | 0% (n=13) | 100 pp (0-100) |
| es | bare_nom | 11% (0-29) | 15% | 0% (n=6) | 0% (n=3) | 50% (n=2) | 25% (n=4) | 0% (n=1) | 0% (n=2) | 50 pp (0-100) |
| es | bare_kw2 | 7% (0-21) | 22% | 0% (n=3) | 0% (n=12) | NA (n=0) | 67% (n=3) | NA (n=0) | 0% (n=9) | 67 pp (0-100) |
| es | bare_x | 8% (0-18) | 31% | 0% (n=3) | 0% (n=15) | NA (n=0) | 100% (n=3) | 0% (n=5) | 0% (n=11) | 100 pp (0-100) |
| fr | bare | 60% (51-69) | 33% | 92% (n=12) | 78% (n=9) | 75% (n=4) | 100% (n=1) | 50% (n=2) | 8% (n=12) | 92 pp (71-100) |
| fr | bare_nom | 76% (64-90) | 28% | 78% (n=9) | 100% (n=2) | 71% (n=7) | 86% (n=7) | 100% (n=1) | 57% (n=7) | 43 pp (20-83) |
| fr | bare_kw2 | 62% (51-75) | 35% | 92% (n=12) | 78% (n=9) | 75% (n=4) | 100% (n=2) | 33% (n=3) | 10% (n=10) | 90 pp (71-100) |
| fr | bare_x | 73% (60-88) | 37% | 89% (n=9) | 75% (n=12) | 67% (n=3) | 83% (n=6) | 50% (n=2) | 58% (n=12) | 39 pp (25-100) |

## E9 policies. Polarity at pi_neg=2.7% (silent reversals per 1,000; taps per 1,000)

| policy | EN | DE | ES | FR |
|---|---|---|---|---|
| G1_written_cue | 0.0 [0.0,0.0] ; taps 1000 | 0.9 [0.0,2.0] ; taps 1000 | 0.2 [0.0,0.8] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 |
| always_ask_chip | 0.7 [0.0,1.4] ; taps 1000 | 0.2 [0.0,0.7] ; taps 1000 | 0.2 [0.0,0.8] ; taps 1000 | 0.2 [0.0,0.7] ; taps 1000 |
| always_commit(bare) | 26.5 [25.9,27.0] ; taps 0 | 26.8 [26.3,27.0] ; taps 0 | 26.8 [26.2,27.0] ; taps 0 | 26.8 [26.3,27.0] ; taps 0 |
| entropy_ask | 26.5 [25.9,27.0] ; taps 0 | 26.5 [25.9,27.0] ; taps 17 | 26.3 [25.4,27.0] ; taps 26 | 26.1 [25.2,26.8] ; taps 34 |
| plain_word | 1.6 [0.7,2.5] ; taps 3000 | 1.4 [0.5,2.2] ; taps 3000 | 0.9 [0.0,2.1] ; taps 3000 | 0.7 [0.0,1.4] ; taps 3000 |

Entropy-ask rate (polarity): en: 0.0%, de: 1.7%, es: 2.6%, fr: 3.4%

## E9 register at pi_V=0.5 (mismatch per 1,000 [CI]; taps per 1,000)
| policy | DE | ES (expl.) | FR |
|---|---|---|---|
| always_commit(bare) | 225 [158,292] ; taps 0 | 125 [88,158] ; taps 0 | 167 [108,225] ; taps 0 |
| always_ask_chip | 4 [0,12] ; taps 1000 | 17 [4,33] ; taps 1000 | 46 [25,67] ; taps 1000 |
| plain_word | 38 [21,54] ; taps 3000 | 25 [4,50] ; taps 3000 | 83 [54,112] ; taps 3000 |
| plain_word_x(legend-equalised) | 42 [21,62] ; taps 3000 | 12 [0,25] ; taps 3000 | 108 [75,142] ; taps 3000 |
| ctx_cue | 25 [8,46] ; taps 1000 | 75 [50,100] ; taps 1000 | 50 [25,79] ; taps 1000 |
| ctx_cue_x(legend-equalised) | 17 [4,33] ; taps 1000 | 83 [54,117] ; taps 1000 | 75 [46,104] ; taps 1000 |
| ask_if_address | 4 [0,12] ; taps 450 | 0 [0,0] ; taps 250 | 38 [17,58] ; taps 333 |
| entropy_ask(T/V split) | 138 [96,179] ; taps 192 | 121 [88,154] ; taps 8 | 121 [67,175] ; taps 142 |
| entropy_ask(any disagreement) | 100 [67,138] ; taps 358 | 67 [38,96] ; taps 308 | 112 [62,162] ; taps 292 |
| G1_written_cue | 4 [0,12] ; taps 1000 | 0 [0,0] ; taps 1000 | 21 [4,38] ; taps 1000 |
| random_ask_matched_to_ask_if_address | 126 [87,164] ; taps 450 | 98 [71,124] ; taps 250 | 126 [82,169] ; taps 333 |
| random_ask_matched_to_1000 | 4 [0,12] ; taps 1000 | 17 [4,33] ; taps 1000 | 46 [25,67] ; taps 1000 |

Ask-if-address minus random-ask at matched taps (mismatch fraction, paired CI): de: -12.1 pp [-15.6,-8.5]; es: -9.8 pp [-12.4,-7.1]; fr: -8.9 pp [-12.1,-5.7]

G1 written cue: {"en|neg": {"n": 120, "monitor_fired": 120, "still_bad_after_retries": 0}, "de|T": {"n": 120, "monitor_fired": 18, "still_bad_after_retries": 0}, "de|V": {"n": 120, "monitor_fired": 35, "still_bad_after_retries": 0}, "de|neg": {"n": 120, "monitor_fired": 119, "still_bad_after_retries": 4}, "es|T": {"n": 120, "monitor_fired": 2, "still_bad_after_retries": 0}, "es|V": {"n": 120, "monitor_fired": 28, "still_bad_after_retries": 0}, "es|neg": {"n": 114, "monitor_fired": 113, "still_bad_after_retries": 1}, "fr|T": {"n": 120, "monitor_fired": 24, "still_bad_after_retries": 5}, "fr|V": {"n": 120, "monitor_fired": 16, "still_bad_after_retries": 0}, "fr|neg": {"n": 120, "monitor_fired": 119, "still_bad_after_retries": 1}}

## E7 detector validation
```
{
 "de": {
  "n": 120,
  "n_ambig": 0,
  "n_non_ambig": 120,
  "primary_agree": 0.975,
  "primary_k": 117,
  "primary_wilson": [
   0.9290687625956524,
   0.9914619799012145
  ],
  "overall_agree_ambig_as_error": 0.975,
  "none_subset_n": 38,
  "none_missed_address_forms": 3,
  "arb1_vs_arb2_agree": 1.0,
  "arb_label_dist": {
   "T": 52,
   "V": 33,
   "none": 35,
   "mixed": 0
  },
  "ambig_arbiter_dist": {
   "T": 0,
   "V": 0,
   "none": 0,
   "mixed": 0
  },
  "pass": true
 },
 "es": {
  "n": 120,
  "n_ambig": 0,
  "n_non_ambig": 120,
  "primary_agree": 0.9416666666666667,
  "primary_k": 113,
  "primary_wilson": [
   0.8844727405319686,
   0.9714593533686271
  ],
  "overall_agree_ambig_as_error": 0.9416666666666667,
  "none_subset_n": 67,
  "none_missed_address_forms": 7,
  "arb1_vs_arb2_agree": 0.9916666666666667,
  "arb_label_dist": {
   "T": 50,
   "V": 10,
   "none": 60,
   "mixed": 0
  },
  "ambig_arbiter_dist": {
   "T": 0,
   "V": 0,
   "none": 0,
   "mixed": 0
  },
  "pass": false
 },
 "fr": {
  "n": 120,
  "n_ambig": 0,
  "n_non_ambig": 120,
  "primary_agree": 1.0,
  "primary_k": 120,
  "primary_wilson": [
   0.9689797289440706,
   1.0
  ],
  "overall_agree_ambig_as_error": 1.0,
  "none_subset_n": 43,
  "none_missed_address_forms": 0,
  "arb1_vs_arb2_agree": 1.0,
  "arb_label_dist": {
   "T": 25,
   "V": 52,
   "none": 43,
   "mixed": 0
  },
  "ambig_arbiter_dist": {
   "T": 0,
   "V": 0,
   "none": 0,
   "mixed": 0
  },
  "pass": true
 }
}
```

## E10 naturalness
```
{
 "means": {
  "en|POL|bare": {
   "mean": 4.316666666666666,
   "n": 120
  },
  "en|POL|restored": {
   "mean": 4.133333333333334,
   "n": 120
  },
  "en|POL|plain_neg": {
   "mean": 4.116666666666666,
   "n": 120
  },
  "en|REG|bare": {
   "mean": 4.633333333333334,
   "n": 120
  },
  "de|POL|bare": {
   "mean": 3.8333333333333335,
   "n": 120
  },
  "de|POL|restored": {
   "mean": 3.65,
   "n": 120
  },
  "de|POL|plain_neg": {
   "mean": 3.525,
   "n": 120
  },
  "de|REG|bare": {
   "mean": 4.491666666666666,
   "n": 120
  },
  "de|REG|chip_formal": {
   "mean": 4.225,
   "n": 120
  },
  "de|REG|chip_informal": {
   "mean": 4.466666666666667,
   "n": 120
  },
  "de|REG|plain_formal": {
   "mean": 3.2583333333333333,
   "n": 120
  },
  "de|REG|plain_informal": {
   "mean": 3.966666666666667,
   "n": 120
  },
  "es|POL|bare": {
   "mean": 4.2368421052631575,
   "n": 114
  },
  "es|POL|restored": {
   "mean": 3.8157894736842106,
   "n": 114
  },
  "es|POL|plain_neg": {
   "mean": 4.219298245614035,
   "n": 114
  },
  "es|REG|bare": {
   "mean": 4.466666666666667,
   "n": 120
  },
  "es|REG|chip_formal": {
   "mean": 4.383333333333334,
   "n": 120
  },
  "es|REG|chip_informal": {
   "mean": 4.758333333333334,
   "n": 120
  },
  "es|REG|plain_formal": {
   "mean": 3.0416666666666665,
   "n": 120
  },
  "es|REG|plain_informal": {
   "mean": 3.775,
   "n": 120
  },
  "fr|POL|bare": {
   "mean": 4.133333333333334,
   "n": 120
  },
  "fr|POL|restored": {
   "mean": 4.066666666666666,
   "n": 120
  },
  "fr|POL|plain_neg": {
   "mean": 4.058333333333334,
   "n": 120
  },
  "fr|REG|bare": {
   "mean": 4.383333333333334,
   "n": 120
  },
  "fr|REG|chip_formal": {
   "mean": 4.141666666666667,
   "n": 120
  },
  "fr|REG|chip_informal": {
   "mean": 4.525,
   "n": 120
  },
  "fr|REG|plain_formal": {
   "mean": 3.35,
   "n": 120
  },
  "fr|REG|plain_informal": {
   "mean": 3.2666666666666666,
   "n": 120
  }
 },
 "paired": {
  "en|POL|restored-bare": {
   "diff": -0.18333333333333335,
   "ci": [
    -0.5166666666666665,
    0.14999999999999997
   ],
   "n_fam": 20
  },
  "en|POL|plain_neg-bare": {
   "diff": -0.1999999999999999,
   "ci": [
    -0.5416666666666665,
    0.13333333333333347
   ],
   "n_fam": 20
  },
  "de|POL|restored-bare": {
   "diff": -0.1833333333333334,
   "ci": [
    -0.43333333333333346,
    0.0833333333333333
   ],
   "n_fam": 20
  },
  "de|POL|plain_neg-bare": {
   "diff": -0.3083333333333334,
   "ci": [
    -0.6083333333333333,
    0.00833333333333317
   ],
   "n_fam": 20
  },
  "de|REG|chip_formal-bare": {
   "diff": -0.2666666666666666,
   "ci": [
    -0.5083333333333334,
    -0.04999999999999991
   ],
   "n_fam": 20
  },
  "de|REG|chip_informal-bare": {
   "diff": -0.025,
   "ci": [
    -0.21666666666666662,
    0.16666666666666663
   ],
   "n_fam": 20
  },
  "de|REG|plain_formal-bare": {
   "diff": -1.2333333333333334,
   "ci": [
    -1.6,
    -0.8833333333333334
   ],
   "n_fam": 20
  },
  "es|POL|restored-bare": {
   "diff": -0.42105263157894735,
   "ci": [
    -0.6929824561403509,
    -0.1929824561403508
   ],
   "n_fam": 19
  },
  "es|POL|plain_neg-bare": {
   "diff": -0.017543859649122837,
   "ci": [
    -0.18421052631578955,
    0.1491228070175438
   ],
   "n_fam": 19
  },
  "es|REG|chip_formal-bare": {
   "diff": -0.08333333333333334,
   "ci": [
    -0.375,
    0.15833333333333335
   ],
   "n_fam": 20
  },
  "es|REG|chip_informal-bare": {
   "diff": 0.2916666666666667,
   "ci": [
    0.06666666666666662,
    0.4916666666666668
   ],
   "n_fam": 20
  },
  "es|REG|plain_formal-bare": {
   "diff": -1.4249999999999998,
   "ci": [
    -1.7002083333333335,
    -1.125
   ],
   "n_fam": 20
  },
  "fr|POL|restored-bare": {
   "diff": -0.06666666666666661,
   "ci": [
    -0.40020833333333333,
    0.2583333333333334
   ],
   "n_fam": 20
  },
  "fr|POL|plain_neg-bare": {
   "diff": -0.07499999999999998,
   "ci": [
    -0.4583333333333332,
    0.2666666666666667
   ],
   "n_fam": 20
  },
  "fr|REG|chip_formal-bare": {
   "diff": -0.2416666666666666,
   "ci": [
    -0.5166666666666666,
    -0.008333333333333238
   ],
   "n_fam": 20
  },
  "fr|REG|chip_informal-bare": {
   "diff": 0.14166666666666675,
   "ci": [
    -0.07499999999999993,
    0.35
   ],
   "n_fam": 20
  },
  "fr|REG|plain_formal-bare": {
   "diff": -1.0333333333333334,
   "ci": [
    -1.366875,
    -0.7166666666666668
   ],
   "n_fam": 20
  }
 }
}
```

## E8 strict gate (second back-translator: qwen2.5-14b)
- de|POL: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- de|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- de|all: {'n': 40, 'pilot_gate': 40, 'strict_gate': 40, 'strict_rate': 1.0}
- es|POL: {'n': 20, 'pilot_gate': 19, 'strict_gate': 19}
- es|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- es|all: {'n': 40, 'pilot_gate': 39, 'strict_gate': 39, 'strict_rate': 0.975}
- fr|POL: {'n': 20, 'pilot_gate': 20, 'strict_gate': 19}
- fr|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- fr|all: {'n': 40, 'pilot_gate': 40, 'strict_gate': 39, 'strict_rate': 0.975}
