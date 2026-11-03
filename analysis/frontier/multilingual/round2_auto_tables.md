# Round-2 auto tables (models with data: mistral-nemo-12b, gpt-6.1-terra; rows 4195)

## E1 register commitment, bare, unconditional (P(no address) | P(single register | address) | n address / n outputs | V share among T/V)

| scope | DE | ES | FR |
|---|---|---|---|
| pooled | none 38% / single 100% / 25of40 / V 24% (n=25) | none 38% / single 100% / 25of40 / V 0% (n=25) | none 48% / single 100% / 21of40 / V 38% (n=21) |
| mistral-nemo-12b | none 45% / single 100% / 11of20 / V 45% (n=11) | none 40% / single 100% / 12of20 / V 0% (n=12) | none 55% / single 100% / 9of20 / V 78% (n=9) |
| gpt-6.1-terra | none 30% / single 100% / 14of20 / V 7% (n=14) | none 35% / single 100% / 13of20 / V 0% (n=13) | none 40% / single 100% / 12of20 / V 8% (n=12) |

## E2 language contrasts (V-share difference, cluster bootstrap CI, Holm p)
| test | diff | 95% CI | p_holm | confirmed (Holm<.05 and >=30pp) |
|---|---|---|---|---|
| mistral-nemo-12b|de-fr | -32.3 pp | -67 to 0 | 0.113 | False |
| gpt-6.1-terra|de-fr | -1.2 pp | -23 to 19 | 1.000 | False |

Model range of V-share within language: de: 38 pp (CI 4-75); es: 0 pp (CI 0-0); fr: 69 pp (CI 33-100)

## E3 polarity default vs matched English (P(affirmative | committed) / P(negated | all) / diff vs EN [CI])
| draw | scope | EN | DE | ES | FR |
|---|---|---|---|---|---|
| greedy | pooled | 100.0% / neg 0.0% n=40 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=40 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=37 | 97.5% / neg 2.5% / d -2.5 [-7.5,0.0] n=40 |
| greedy | mistral-nemo-12b | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=19 | 95.0% / neg 5.0% / d -5.0 [-15.0,0.0] n=20 |
| greedy | gpt-6.1-terra | 100.0% / neg 0.0% n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=18 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=20 |
| sampled | pooled | 100.0% / neg 0.0% n=200 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=200 | 98.9% / neg 1.1% / d -1.1 [-3.4,0.0] n=185 | 97.4% / neg 2.6% / d -2.6 [-6.1,0.0] n=196 |
| sampled | mistral-nemo-12b | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 97.8% / neg 2.2% / d -2.2 [-6.8,0.0] n=93 | 94.9% / neg 5.1% / d -5.1 [-12.2,0.0] n=98 |
| sampled | gpt-6.1-terra | 100.0% / neg 0.0% n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=100 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=92 | 100.0% / neg 0.0% / d 0.0 [0.0,0.0] n=98 |

## E3b pronoun-address vs English (P(you) EN; target pronoun-address; diff [CI])
| scope | DE | ES | FR |
|---|---|---|---|
| pooled | EN 10% / DE 25% / d 15 [0,30] | EN 10% / ES 30% / d 20 [2,38] | EN 10% / FR 28% / d 18 [0,35] |
| mistral-nemo-12b | EN 20% / DE 30% / d 10 [-15,35] | EN 20% / ES 40% / d 20 [-5,45] | EN 20% / FR 45% / d 25 [-5,50] |
| gpt-6.1-terra | EN 0% / DE 20% / d 20 [5,40] | EN 0% / ES 20% / d 20 [5,40] | EN 0% / FR 10% / d 10 [0,25] |

## E4 cue restoration (B families): negated rate restored / bare / plain word; gain CI lower bound
| scope | EN | DE | ES | FR |
|---|---|---|---|---|
| pooled | 95% / 0% / plain 95%; gain lo 88 pp | 100% / 0% / plain 97%; gain lo 100 pp | 100% / 0% / plain 92%; gain lo 100 pp | 100% / 2% / plain 98%; gain lo 92 pp |
| mistral-nemo-12b | 95% / 0% / plain 90%; gain lo 85 pp | 100% / 0% / plain 95%; gain lo 100 pp | 100% / 0% / plain 84%; gain lo 100 pp | 100% / 5% / plain 95%; gain lo 85 pp |
| gpt-6.1-terra | 95% / 0% / plain 100%; gain lo 85 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp | 100% / 0% / plain 100%; gain lo 100 pp |

Models meeting the >=50 pp lower-bound criterion: en: 2/2; de: 2/2; es: 2/2; fr: 2/2

Instrument agreement (direct vs translate-then-English), positive agreement on the NEGATED class (restored B) and the affirmative class (restored A):
- DE: negated PA 1.000 (direct 40, route 40, both 40, n=40); affirmative PA 1.000 (n=40)
- ES: negated PA 1.000 (direct 38, route 38, both 38, n=38); affirmative PA 1.000 (n=38)
- FR: negated PA 1.000 (direct 40, route 40, both 40, n=40); affirmative PA 1.000 (n=40)

## E5 register cues, pooled (match among address / address rate / match of all)
| lang, requested | chip | plain | ctx | plain_x (legend-eq.) | ctx_x |
|---|---|---|---|---|---|
| DE formal | 100% / 92% / 92% | 100% / 70% / 70% | 100% / 60% / 60% | 100% / 82% / 82% | 100% / 57% / 57% |
| DE informal | 100% / 90% / 90% | 94% / 78% / 72% | 100% / 68% / 68% | 94% / 90% / 85% | 100% / 68% / 68% |
| ES formal | 100% / 92% / 92% | 86% / 35% / 30% | 52% / 57% / 30% | 96% / 65% / 62% | 54% / 60% / 32% |
| ES informal | 100% / 88% / 88% | 100% / 62% / 62% | 100% / 62% / 62% | 100% / 82% / 82% | 100% / 70% / 70% |
| FR formal | 100% / 92% / 92% | 100% / 68% / 68% | 95% / 52% / 50% | 100% / 75% / 75% | 100% / 55% / 55% |
| FR informal | 85% / 85% / 72% | 75% / 70% / 52% | 81% / 65% / 52% | 71% / 88% / 62% | 81% / 65% / 52% |

Chip minus legend-equalised cues, match of all outputs (paired, pooled):
- DE formal: chip-plain_x 10 pp [-3,25]; chip-ctx_x 35 pp [20,50]
- DE informal: chip-plain_x 5 pp [-7,17]; chip-ctx_x 22 pp [10,38]
- ES formal: chip-plain_x 30 pp [12,48]; chip-ctx_x 60 pp [45,75]
- ES informal: chip-plain_x 5 pp [0,12]; chip-ctx_x 18 pp [7,30]
- FR formal: chip-plain_x 18 pp [5,30]; chip-ctx_x 38 pp [25,50]
- FR informal: chip-plain_x 10 pp [-3,22]; chip-ctx_x 20 pp [10,30]

FR-informal chip outputs by model: {"mistral-nemo-12b": {"labels": {"V": 5, "T": 11, "none": 4}, "V_trigger_tokens": {"s'il vous pla": 3, "vous": 3}, "examples_V": ["Apportez le colis, s'il vous plaît.", "Laissez le colis ici.", "Apportez le dossier, s'il vous plaît."], "n": 20}, "gpt-6.1-terra": {"labels": {"T": 18, "none": 2}, "V_trigger_tokens": {}, "examples_V": [], "n": 20}}

## E6 keyword-condition controls (V share among T/V; n in parentheses; pooled address rate)
| lang | condition | pooled V | address rate | mistral-nemo-12b | gpt-6.1-terra | model range |
|---|---|---|---|---|---|---|
| de | bare | 24% (10-38) | 62% | 45% (n=11) | 7% (n=14) | 38 pp (4-75) |
| de | bare_nom | 20% (0-67) | 12% | 100% (n=1) | 0% (n=4) | 100 pp (0-100) |
| de | bare_sep | 17% (0-36) | 75% | 17% (n=12) | 17% (n=12) | 0 pp (0-29) |
| de | bare_kw2 | 18% (0-33) | 42% | 38% (n=8) | 0% (n=9) | 38 pp (0-75) |
| de | bare_x | 27% (13-39) | 65% | 58% (n=12) | 0% (n=14) | 58 pp (29-86) |
| es | bare | 0% (0-0) | 62% | 0% (n=12) | 0% (n=13) | 0 pp (0-0) |
| es | bare_nom | 0% (0-0) | 12% | 0% (n=3) | 0% (n=2) | 0 pp (0-0) |
| es | bare_kw2 | 0% (0-0) | 52% | 0% (n=12) | 0% (n=9) | 0 pp (0-0) |
| es | bare_x | 0% (0-0) | 65% | 0% (n=15) | 0% (n=11) | 0 pp (0-0) |
| fr | bare | 38% (23-52) | 52% | 78% (n=9) | 8% (n=12) | 69 pp (33-100) |
| fr | bare_nom | 67% (38-100) | 22% | 100% (n=2) | 57% (n=7) | 43 pp (0-83) |
| fr | bare_kw2 | 42% (23-61) | 50% | 78% (n=9) | 10% (n=10) | 68 pp (35-100) |
| fr | bare_x | 67% (45-86) | 60% | 75% (n=12) | 58% (n=12) | 17 pp (1-50) |

## E9 policies. Polarity at pi_neg=2.7% (silent reversals per 1,000; taps per 1,000)

| policy | EN | DE | ES | FR |
|---|---|---|---|---|
| G1_written_cue | 0.0 [0.0,0.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 |
| always_ask_chip | 0.7 [0.0,2.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 | 0.0 [0.0,0.0] ; taps 1000 |
| always_commit(bare) | 27.0 [27.0,27.0] ; taps 0 | 27.0 [27.0,27.0] ; taps 0 | 27.0 [27.0,27.0] ; taps 0 | 26.3 [25.0,27.0] ; taps 0 |
| entropy_ask | 27.0 [27.0,27.0] ; taps 0 | 27.0 [27.0,27.0] ; taps 0 | 26.3 [24.7,27.0] ; taps 27 | 25.0 [22.3,27.0] ; taps 75 |
| plain_word | 1.4 [0.0,3.4] ; taps 3000 | 0.7 [0.0,2.1] ; taps 3000 | 2.2 [0.0,4.9] ; taps 3000 | 0.7 [0.0,2.0] ; taps 3000 |

Entropy-ask rate (polarity): en: 0.0%, de: 0.0%, es: 2.7%, fr: 7.5%

## E9 register at pi_V=0.5 (mismatch per 1,000 [CI]; taps per 1,000)
| policy | DE | ES (expl.) | FR |
|---|---|---|---|
| always_commit(bare) | 312 [212,400] ; taps 0 | 312 [225,400] ; taps 0 | 262 [162,362] ; taps 0 |
| always_ask_chip | 0 [0,0] ; taps 1000 | 0 [0,0] ; taps 1000 | 62 [12,112] ; taps 1000 |
| plain_word | 25 [0,62] ; taps 3000 | 25 [0,62] ; taps 3000 | 88 [38,138] ; taps 3000 |
| plain_word_x(legend-equalised) | 25 [0,62] ; taps 3000 | 12 [0,38] ; taps 3000 | 125 [75,175] ; taps 3000 |
| ctx_cue | 0 [0,0] ; taps 1000 | 138 [88,188] ; taps 1000 | 75 [25,125] ; taps 1000 |
| ctx_cue_x(legend-equalised) | 0 [0,0] ; taps 1000 | 138 [88,188] ; taps 1000 | 62 [25,112] ; taps 1000 |
| ask_if_address | 0 [0,0] ; taps 625 | 0 [0,0] ; taps 625 | 38 [0,75] ; taps 525 |
| entropy_ask(T/V split) | 200 [138,262] ; taps 225 | 312 [225,400] ; taps 0 | 162 [88,238] ; taps 275 |
| entropy_ask(any disagreement) | 162 [100,225] ; taps 450 | 150 [75,225] ; taps 450 | 150 [75,225] ; taps 525 |
| G1_written_cue | 0 [0,0] ; taps 1000 | 0 [0,0] ; taps 1000 | 0 [0,0] ; taps 1000 |
| random_ask_matched_to_ask_if_address | 117 [80,150] ; taps 625 | 117 [84,150] ; taps 625 | 158 [96,218] ; taps 525 |
| random_ask_matched_to_1000 | 0 [0,0] ; taps 1000 | 0 [0,0] ; taps 1000 | 62 [12,112] ; taps 1000 |

Ask-if-address minus random-ask at matched taps (mismatch fraction, paired CI): de: -11.7 pp [-15.0,-8.0]; es: -11.7 pp [-15.0,-8.4]; fr: -12.0 pp [-16.8,-7.2]

G1 written cue: {"en|neg": {"n": 40, "monitor_fired": 40, "still_bad_after_retries": 0}, "de|T": {"n": 40, "monitor_fired": 6, "still_bad_after_retries": 0}, "de|V": {"n": 40, "monitor_fired": 19, "still_bad_after_retries": 0}, "de|neg": {"n": 40, "monitor_fired": 40, "still_bad_after_retries": 0}, "es|T": {"n": 40, "monitor_fired": 0, "still_bad_after_retries": 0}, "es|V": {"n": 40, "monitor_fired": 25, "still_bad_after_retries": 0}, "es|neg": {"n": 38, "monitor_fired": 38, "still_bad_after_retries": 0}, "fr|T": {"n": 40, "monitor_fired": 8, "still_bad_after_retries": 0}, "fr|V": {"n": 40, "monitor_fired": 13, "still_bad_after_retries": 0}, "fr|neg": {"n": 40, "monitor_fired": 39, "still_bad_after_retries": 0}}

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
   "mean": 4.775,
   "n": 40
  },
  "en|POL|restored": {
   "mean": 4.275,
   "n": 40
  },
  "en|POL|plain_neg": {
   "mean": 4.6,
   "n": 40
  },
  "en|REG|bare": {
   "mean": 4.85,
   "n": 40
  },
  "de|POL|bare": {
   "mean": 4.525,
   "n": 40
  },
  "de|POL|restored": {
   "mean": 4.5,
   "n": 40
  },
  "de|POL|plain_neg": {
   "mean": 4.525,
   "n": 40
  },
  "de|REG|bare": {
   "mean": 4.775,
   "n": 40
  },
  "de|REG|chip_formal": {
   "mean": 4.675,
   "n": 40
  },
  "de|REG|chip_informal": {
   "mean": 4.85,
   "n": 40
  },
  "de|REG|plain_formal": {
   "mean": 4.0,
   "n": 40
  },
  "de|REG|plain_informal": {
   "mean": 4.625,
   "n": 40
  },
  "es|POL|bare": {
   "mean": 4.473684210526316,
   "n": 38
  },
  "es|POL|restored": {
   "mean": 4.342105263157895,
   "n": 38
  },
  "es|POL|plain_neg": {
   "mean": 4.473684210526316,
   "n": 38
  },
  "es|REG|bare": {
   "mean": 4.9,
   "n": 40
  },
  "es|REG|chip_formal": {
   "mean": 4.875,
   "n": 40
  },
  "es|REG|chip_informal": {
   "mean": 4.875,
   "n": 40
  },
  "es|REG|plain_formal": {
   "mean": 3.85,
   "n": 40
  },
  "es|REG|plain_informal": {
   "mean": 4.675,
   "n": 40
  },
  "fr|POL|bare": {
   "mean": 4.575,
   "n": 40
  },
  "fr|POL|restored": {
   "mean": 4.2,
   "n": 40
  },
  "fr|POL|plain_neg": {
   "mean": 4.575,
   "n": 40
  },
  "fr|REG|bare": {
   "mean": 4.675,
   "n": 40
  },
  "fr|REG|chip_formal": {
   "mean": 4.65,
   "n": 40
  },
  "fr|REG|chip_informal": {
   "mean": 4.65,
   "n": 40
  },
  "fr|REG|plain_formal": {
   "mean": 3.875,
   "n": 40
  },
  "fr|REG|plain_informal": {
   "mean": 3.9,
   "n": 40
  }
 },
 "paired": {
  "en|POL|restored-bare": {
   "diff": -0.5,
   "ci": [
    -0.9,
    -0.125
   ],
   "n_fam": 20
  },
  "en|POL|plain_neg-bare": {
   "diff": -0.175,
   "ci": [
    -0.375,
    0.0
   ],
   "n_fam": 20
  },
  "de|POL|restored-bare": {
   "diff": -0.025,
   "ci": [
    -0.3,
    0.275
   ],
   "n_fam": 20
  },
  "de|POL|plain_neg-bare": {
   "diff": 0.0,
   "ci": [
    -0.35,
    0.425
   ],
   "n_fam": 20
  },
  "de|REG|chip_formal-bare": {
   "diff": -0.1,
   "ci": [
    -0.35,
    0.15
   ],
   "n_fam": 20
  },
  "de|REG|chip_informal-bare": {
   "diff": 0.075,
   "ci": [
    -0.1,
    0.325
   ],
   "n_fam": 20
  },
  "de|REG|plain_formal-bare": {
   "diff": -0.775,
   "ci": [
    -1.15,
    -0.425
   ],
   "n_fam": 20
  },
  "es|POL|restored-bare": {
   "diff": -0.13157894736842105,
   "ci": [
    -0.47368421052631576,
    0.18421052631578946
   ],
   "n_fam": 19
  },
  "es|POL|plain_neg-bare": {
   "diff": 0.0,
   "ci": [
    -0.2894736842105263,
    0.2631578947368421
   ],
   "n_fam": 19
  },
  "es|REG|chip_formal-bare": {
   "diff": -0.025,
   "ci": [
    -0.2,
    0.15
   ],
   "n_fam": 20
  },
  "es|REG|chip_informal-bare": {
   "diff": -0.025,
   "ci": [
    -0.3,
    0.175
   ],
   "n_fam": 20
  },
  "es|REG|plain_formal-bare": {
   "diff": -1.05,
   "ci": [
    -1.4,
    -0.725
   ],
   "n_fam": 20
  },
  "fr|POL|restored-bare": {
   "diff": -0.375,
   "ci": [
    -1.0,
    0.25
   ],
   "n_fam": 20
  },
  "fr|POL|plain_neg-bare": {
   "diff": 0.0,
   "ci": [
    -0.4,
    0.4
   ],
   "n_fam": 20
  },
  "fr|REG|chip_formal-bare": {
   "diff": -0.025,
   "ci": [
    -0.275,
    0.2
   ],
   "n_fam": 20
  },
  "fr|REG|chip_informal-bare": {
   "diff": -0.025,
   "ci": [
    -0.175,
    0.1
   ],
   "n_fam": 20
  },
  "fr|REG|plain_formal-bare": {
   "diff": -0.8,
   "ci": [
    -1.225,
    -0.4
   ],
   "n_fam": 20
  }
 }
}
```

## E8 strict gate (second back-translator: gpt-6.1-terra)
- de|POL: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- de|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- de|all: {'n': 40, 'pilot_gate': 40, 'strict_gate': 40, 'strict_rate': 1.0}
- es|POL: {'n': 20, 'pilot_gate': 19, 'strict_gate': 19}
- es|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- es|all: {'n': 40, 'pilot_gate': 39, 'strict_gate': 39, 'strict_rate': 0.975}
- fr|POL: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- fr|REG: {'n': 20, 'pilot_gate': 20, 'strict_gate': 20}
- fr|all: {'n': 40, 'pilot_gate': 40, 'strict_gate': 40, 'strict_rate': 1.0}
