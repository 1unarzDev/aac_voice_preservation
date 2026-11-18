# B2: Claude (non-GPT) re-label of judge units

Disclosure: Claude (Sonnet) is a second-family extractor here, not an independent human check. Claude also served as the arbiter in the production labelling and assisted analysis and writing of this project, so these agreement numbers are not independent of Claude-side choices. Pre-declared rules: `analysis/relabel_nongpt/PLAN.md`; labelling instruction `INSTRUCTION.md` (verbatim in every subagent prompt); script `src/relabel_nongpt_aggregate.py` (stored data, 0 API calls).

## Coverage

* Units: 1575 in 40 batches; labelled 1574; with all values valid 1574; missing 1; problems 0; batches without label file: none.
* Gaps and invalid entries: ; unlabelled units: u591993ab0b (b03, hw12). Unlabelled units are excluded from every analysis below (the affected rows keep the GPT label in the P1 Claude re-run).

## Claude vs human consensus, Part 13 (152 outputs, plurality of 3 coders)

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 150 | 89.3% [83.4, 93.3] | 0.885 [0.83, 0.94] |
| polarity | 152 | 100.0% [97.5, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 149 | 98.7% [95.2, 99.6] | 0.972 [0.93, 1.00] |
| agent | 152 | 98.7% [95.3, 99.6] | 0.981 [0.95, 1.00] |
| certainty | 151 | 94.7% [89.9, 97.3] | 0.898 [0.82, 0.96] |
| politeness | 152 | 100.0% [97.5, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 906 | 96.9% [95.6, 97.9] | 0.966 [0.95, 0.98] |

## Claude vs human consensus, Part 20 (120 outputs, strict two-coder consensus; items without consensus excluded per field)

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 115 | 100.0% [96.8, 100.0] | 1.000 [1.00, 1.00] |
| polarity | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 111 | 100.0% [96.7, 100.0] | 1.000 [1.00, 1.00] |
| agent | 110 | 100.0% [96.6, 100.0] | 1.000 [1.00, 1.00] |
| certainty | 119 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| politeness | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 695 | 100.0% [99.5, 100.0] | 1.000 [1.00, 1.00] |

## Claude vs human consensus, Parts 13+20 pooled

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 265 | 94.0% [90.4, 96.2] | 0.935 [0.90, 0.96] |
| polarity | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 260 | 99.2% [97.2, 99.8] | 0.985 [0.96, 1.00] |
| agent | 262 | 99.2% [97.3, 99.8] | 0.989 [0.97, 1.00] |
| certainty | 270 | 97.0% [94.3, 98.5] | 0.946 [0.91, 0.98] |
| politeness | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 1601 | 98.2% [97.5, 98.8] | 0.981 [0.97, 0.99] |

## Claude vs GPT judge (production label), Part 13

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 152 | 87.5% [81.3, 91.8] | 0.866 [0.81, 0.92] |
| polarity | 152 | 100.0% [97.5, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 152 | 98.7% [95.3, 99.6] | 0.973 [0.93, 1.00] |
| agent | 152 | 98.0% [94.4, 99.3] | 0.972 [0.94, 1.00] |
| certainty | 152 | 96.7% [92.5, 98.6] | 0.936 [0.88, 0.99] |
| politeness | 152 | 100.0% [97.5, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 912 | 96.8% [95.5, 97.8] | 0.965 [0.95, 0.98] |

## Claude vs GPT judge, Part 20

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| polarity | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| agent | 120 | 98.3% [94.1, 99.5] | 0.975 [0.94, 1.00] |
| certainty | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| politeness | 120 | 100.0% [96.9, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 720 | 99.7% [99.0, 99.9] | 0.997 [0.99, 1.00] |

## Claude vs GPT judge, Parts 13+20

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 272 | 93.0% [89.3, 95.5] | 0.925 [0.89, 0.96] |
| polarity | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 272 | 99.3% [97.4, 99.8] | 0.986 [0.96, 1.00] |
| agent | 272 | 98.2% [95.8, 99.2] | 0.973 [0.95, 0.99] |
| certainty | 272 | 98.2% [95.8, 99.2] | 0.967 [0.94, 0.99] |
| politeness | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 1632 | 98.1% [97.3, 98.7] | 0.979 [0.97, 0.99] |

## Reference: GPT judge vs human consensus on the same items (Parts 13+20)

| field | n | accuracy [Wilson 95%] | Cohen kappa [boot 95%] |
|---|---|---|---|
| critical | 265 | 96.6% [93.7, 98.2] | 0.964 [0.94, 0.98] |
| polarity | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| speech_act | 260 | 100.0% [98.5, 100.0] | 1.000 [1.00, 1.00] |
| agent | 262 | 99.6% [97.9, 99.9] | 0.995 [0.98, 1.00] |
| certainty | 270 | 98.9% [96.8, 99.6] | 0.980 [0.95, 1.00] |
| politeness | 272 | 100.0% [98.6, 100.0] | 1.000 [1.00, 1.00] |
| all_fields_pooled | 1601 | 99.2% [98.6, 99.5] | 0.991 [0.99, 1.00] |

## hw12 speech-act critical label: Claude vs GPT production label (no human reference)

| subset | n | accuracy [Wilson 95%] | kappa |
|---|---|---|---|
| all rows (hw1+hw2, P0, chip1+noncrit) | 2070 | 98.5% [97.8, 98.9] | 0.974 [0.96, 0.98] |
| distinct texts | 1323 | 99.6% [99.1, 99.8] | 0.994 [0.99, 1.00] |
| chip1 | 1024 | 99.4% [98.7, 99.7] | 0.991 [0.98, 1.00] |
| noncrit | 1046 | 97.5% [96.4, 98.3] | 0.936 [0.91, 0.96] |

Critical field, all three unit sets vs GPT (rows): 2342 | 97.8% [97.1, 98.3] | 0.967 [0.96, 0.97].

## P1 re-run (hw1+hw2 speech-act chip1 minus noncrit critical-match gain)

Estimator: `src/robust_t6_small_cluster.py` `analyse` (pooled row-weighted ratio over writers, CR1 SE, t CI with writers-1 df), after `analyze_hw1.build/frames` (same exclusions). Claude's critical label replaced the GPT critical label on 2046 scored rows (8 changed); all other rows unchanged.

| labels | writers | rows | chip1 match | noncrit match | P1 estimate (pp) | t 95% CI | wild-Webb CI | sign-flip p (1-sided) | all writers positive | leave-one-out |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt | 10 | 1016 | 82.9 | 45.4 | +37.5 | [33.8, 41.2] | [33.9, 41.2] | 0.0010 | True | +36.7 to +38.3 |
| claude | 10 | 1016 | 83.4 | 45.5 | +37.9 | [34.5, 41.3] | [34.5, 41.4] | 0.0010 | True | +37.2 to +38.7 |

Claude writer means (pp): P01 +33.0, P03 +31.9, P04 +40.9, P05 +40.0, P08 +31.2, P14 +34.4, P15 +45.5, P16 +43.3, P17 +38.3, P18 +38.3

## Items where Claude's critical label differs from human consensus

| set | item | text | Claude | human | GPT |
|---|---|---|---|---|---|
| p13 | g-1fae0e2f8e | Sure, the game starts now. | plain assertion | strongly certain/emphatic | plain assertion |
| p13 | g-5c87aa7c39 | I want to go to the train platform. | later | unclear/mixed | now |
| p13 | g-b2f66aac11 | I need to collect my prescription. | later | unclear/mixed | now |
| p13 | g-6260ca665e | I want to lock the gate. | later | unclear/mixed | unclear/mixed |
| p13 | g-d474d61a7f | I want to practice playing a tune on the guitar. | later | unclear/mixed | unclear/mixed |
| p13 | g-e82edac42f | Please turn up the music. | later | unclear/mixed | unclear/mixed |
| p13 | g-386be5253e | I want to cook pasta for dinner. | later | unclear/mixed | unclear/mixed |
| p13 | g-36f6bbdfad | Let's start the game. | unclear/mixed | plain assertion | unclear/mixed |
| p13 | g-ad647fbc98 | The guard checks the gate. | now | unclear/mixed | unclear/mixed |
| p13 | g-08e2339681 | Call the clinic. | later | unclear/mixed | unclear/mixed |
| p13 | g-d518ebc3f4 | I want to file an access request. | later | unclear/mixed | unclear/mixed |
| p13 | g-40de00bf9e | Check the gate. | later | unclear/mixed | unclear/mixed |
| p13 | g-6f8ad41b2e | Maybe I want a taxi to the hotel? | hedged/uncertain | unclear/mixed | unclear/mixed |
| p13 | g-497e8c1c48 | I must tell the landlord about the past bill. | later | unclear/mixed | unclear/mixed |
| p13 | g-8f78f777fe | The bus must arrive at the station. | later | unclear/mixed | unclear/mixed |
| p13 | g-26bf286f76 | Maybe I should wait for a taxi at the library? | hedged/uncertain | unclear/mixed | hedged/uncertain |

## Caveats

* added_content was not labelled (it needs the input, which would unblind).
* Claude saw only the output sentence; the GPT judge also saw only the output for these fields (J1 pass A), so the contrast is extractor family, not information.
* The hw12 comparison has no human reference; agreement there is Claude-vs-GPT only.
* Part 20 consensus is the strict two-coder rule; Part 13 is the stored plurality of three coders. GPT labels are the production labels (arbiter-resolved critical).
