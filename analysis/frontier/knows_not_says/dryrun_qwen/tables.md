## T1. R1, polarity (detector-relative share of no-cue units whose output is negated; HT-weighted; 10,000 item resamples)
| model | set | no-cue units | raw pos. | source posterior % [95%] | greedy share % [95%] | sampled share % [95%] | ratio sampled/posterior [90%] | class (detector) | corrected ratio [90%] | class (corrected) | power |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | 1367 | 68 | 2.62 [1.68, 3.84] | 0.28 [0.00, 0.64] | 0.36 [0.14, 0.69] | 0.14 [0.07, 0.27] | overconfident (default too strong) |  |  | confirmatory-eligible |
| qwen2.5-7b | cap4 | 540 | 107 | 10.77 [8.70, 13.29] | 0.39 [0.11, 0.73] | 0.49 [0.21, 0.79] | 0.05 [0.02, 0.07] | overconfident (default too strong) |  |  | confirmatory-eligible |

## T1b. other dimensions (descriptive only; detector labels, no validity check)
| model | set | dimension | no-cue units | raw pos. | source posterior | greedy share | sampled share | ratio | class |
|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | politeness | 1327 | 124 | 6.55% | 2.96% | 3.70% | 0.56 | inconclusive |
| qwen2.5-7b | human | speech_act | 978 | 388 | 48.23% | 16.43% | 16.70% | 0.35 | overconfident (default too strong) |
| qwen2.5-7b | cap4 | politeness | 441 | 21 | 3.71% | 1.17% | 2.11% | 0.57 | inconclusive |
| qwen2.5-7b | cap4 | speech_act | 372 | 151 | 53.11% | 8.51% | 9.22% | 0.17 | overconfident (default too strong) |

## T2. R2, per-input AUROC on no-cue units (tie-aware, HT-weighted; E-human EXPLORATORY)
| model | set | score | AUROC [95%] | raw pos. | power | tied-at-0 (all/pos/neg) | sampled minus lexical [95%] |
|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | sampled_share(K=16) | 0.50 [0.49, 0.52] | 68 | confirmatory-eligible | 0.99 / 0.97 / 0.99 | -0.25 [-0.33, -0.14] |
| qwen2.5-7b | human | greedy_first_token_entropy | 0.49 [0.36, 0.60] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | greedy_mean_token_entropy | 0.64 [0.53, 0.76] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | lexical_cv_logistic | 0.75 [0.65, 0.82] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | greedy_output_negated | 0.50 [0.50, 0.51] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | sampled_share(K=16) | 0.53 [0.51, 0.55] | 107 | confirmatory-eligible | 0.97 / 0.90 / 0.99 | -0.11 [-0.18, -0.04] |
| qwen2.5-7b | cap4 | greedy_first_token_entropy | 0.49 [0.41, 0.57] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | greedy_mean_token_entropy | 0.59 [0.51, 0.67] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | lexical_cv_logistic | 0.64 [0.57, 0.70] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | greedy_output_negated | 0.52 [0.50, 0.53] | 107 | confirmatory-eligible |  |  |

## T3. Holm family (E-cap4 confirmatory; one-sided bootstrap p)
| model | test | p raw | p Holm | reject at 0.05 |
|---|---|---|---|---|
| qwen2.5-7b | R2-a sampled-share AUROC > 0.5 | 0.0050 | 0.0199 | yes |
| qwen2.5-7b | R2-b sampled-share AUROC > lexical (paired) | 1.0000 | 1.0000 | no |
| qwen2.5-7b | R3-a tap-priced (0.03) weighted cost of sampled-share-ask @10/100 < always-commit | 0.0050 | 0.0199 | yes |
| qwen2.5-7b | R3-b caught_minus_random > 0 for sampled-share-ask @10/100 | 0.0746 | 0.1493 | no |

## T4. Benchmark, E-cap4: silent polarity reversals, spurious negations and taps per 1,000 units (SLP weights w_rev = w_spur = 1 unless stated; simulated, assumes asking resolves the cue)
**qwen2.5-7b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 104.2 [82.2, 129.5] | 0.4 [0.0, 1.6] | 0.0 [0.0, 0.0] |  | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 1000.0 [1000.0, 1000.0] |  | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 104.9 [83.6, 129.5] | 0.4 [0.0, 1.6] | 0.0 [0.0, 0.0] |  | -0.7 [-2.7, 0.0] | -0.01 [-0.03, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 99.0 [78.1, 123.0] | 0.4 [0.0, 1.5] | 50.0 [50.0, 50.0] |  | -0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 93.8 [74.0, 116.6] | 0.4 [0.0, 1.5] | 100.0 [100.0, 100.0] |  | 0.0 [-0.0, 0.0] | 0.10 [0.10, 0.10] |  |  |
| random-ask @ 25/100 (expectation) | 78.2 [61.7, 97.1] | 0.3 [0.0, 1.2] | 250.0 [250.0, 250.0] |  | 0.0 [-0.0, 0.0] | 0.25 [0.25, 0.25] |  |  |
| disagreement-ask (share>=1/16) | 100.0 [78.7, 123.8] | 0.0 [0.0, 0.0] | 17.3 [8.2, 30.6] |  | 2.2 [-0.8, 6.3] | 0.04 [0.01, 0.07] | no |  |
| disagreement-ask (share>=2/16) | 101.4 [80.1, 126.6] | 0.0 [0.0, 0.0] | 6.8 [2.8, 11.1] |  | 2.1 [0.1, 4.9] | 0.03 [0.01, 0.06] | YES |  |
| disagreement-ask (share>=4/16) | 102.8 [81.5, 127.4] | 0.0 [0.0, 0.0] | 5.4 [2.1, 9.0] |  | 0.8 [-0.5, 3.2] | 0.01 [0.00, 0.04] | no |  |
| disagreement-ask (share>=8/16) | 104.2 [82.2, 129.5] | 0.0 [0.0, 0.0] | 3.2 [0.7, 5.8] |  | -0.3 [-0.7, -0.1] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 96.7 [76.1, 119.7] | 0.0 [0.0, 0.0] | 49.9 [41.0, 62.8] |  | 2.2 [-0.8, 6.1] | 0.07 [0.04, 0.10] | no |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 91.6 [72.1, 113.4] | 0.0 [0.0, 0.0] | 99.9 [91.5, 112.1] |  | 2.1 [-0.7, 5.8] | 0.12 [0.09, 0.15] | no |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 76.3 [60.1, 94.5] | 0.0 [0.0, 0.0] | 249.9 [242.9, 260.1] |  | 1.7 [-0.6, 4.8] | 0.27 [0.25, 0.29] | no |  |
| greedy first-token entropy @ 5/100 | 98.3 [76.6, 123.3] | 0.4 [0.0, 1.6] | 52.4 [33.7, 78.8] |  | 0.3 [-4.7, 7.3] | 0.06 [0.01, 0.12] | no |  |
| greedy first-token entropy @ 10/100 | 95.7 [74.1, 119.0] | 0.4 [0.0, 1.6] | 100.4 [76.8, 132.8] |  | -2.2 [-8.8, 6.0] | 0.08 [0.03, 0.16] | no |  |
| greedy first-token entropy @ 25/100 | 77.1 [59.0, 99.3] | 0.3 [0.0, 1.1] | 250.5 [210.8, 293.4] |  | 0.8 [-8.8, 13.2] | 0.26 [0.17, 0.38] | no |  |
| greedy mean token entropy @ 5/100 | 94.8 [73.8, 116.9] | 0.4 [0.0, 1.6] | 52.8 [33.2, 77.6] |  | 4.0 [-2.5, 12.8] | 0.09 [0.03, 0.19] | no |  |
| greedy mean token entropy @ 10/100 | 81.4 [63.4, 104.6] | 0.4 [0.0, 1.6] | 101.0 [71.3, 132.3] |  | 12.3 [2.4, 22.8] | 0.22 [0.12, 0.32] | YES |  |
| greedy mean token entropy @ 25/100 | 66.5 [51.1, 85.1] | 0.4 [0.0, 1.5] | 249.0 [213.4, 291.0] |  | 11.4 [-0.4, 21.4] | 0.36 [0.26, 0.46] | no |  |
| lexical logistic (cross-fitted) @ 5/100 | 87.0 [65.7, 107.0] | 0.4 [0.0, 1.6] | 49.0 [33.7, 67.7] |  | 12.4 [4.0, 21.5] | 0.17 [0.08, 0.26] | YES |  |
| lexical logistic (cross-fitted) @ 10/100 | 80.6 [61.9, 102.6] | 0.4 [0.0, 1.6] | 102.0 [76.0, 127.9] |  | 13.2 [4.1, 25.3] | 0.23 [0.13, 0.35] | YES |  |
| lexical logistic (cross-fitted) @ 25/100 | 63.1 [44.7, 83.2] | 0.4 [0.0, 1.6] | 250.4 [212.8, 297.9] |  | 15.4 [4.0, 26.9] | 0.40 [0.29, 0.52] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 107.7 [87.0, 132.9] |  | 93.3 [75.0, 112.5] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 0.5 [0.4, 0.6] | 0.4 [0.0, 1.6] | 107.7 [87.0, 132.9] |  | 92.8 [74.6, 111.8] | 1.00 [1.00, 1.00] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 1.5 [1.2, 1.9] | 0.4 [0.0, 1.6] | 107.7 [87.0, 132.9] |  | 91.8 [73.8, 110.6] | 0.99 [0.99, 0.99] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 388} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 998.0 [996.4, 999.6] |  | 0.2 [0.0, 0.4] | 1.00 [1.00, 1.00] | YES |  |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/8 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 996.4 [993.5, 999.0] |  | 0.4 [0.1, 0.7] | 1.00 [1.00, 1.00] | YES |  |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/36 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 996.1 [992.7, 998.9] |  | 0.4 [0.1, 0.8] | 1.00 [1.00, 1.00] | YES |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 996.8 [994.2, 999.3] |  | 0.3 [0.1, 0.7] | 1.00 [1.00, 1.00] | YES |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/8 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 996.6 [993.9, 999.3] |  | 0.4 [0.1, 0.7] | 1.00 [1.00, 1.00] | YES |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/36 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.6] | 996.1 [992.7, 998.9] |  | 0.4 [0.1, 0.8] | 1.00 [1.00, 1.00] | YES |  |

## T4. Benchmark, E-human: silent polarity reversals, spurious negations and taps per 1,000 units (SLP weights w_rev = w_spur = 1 unless stated; simulated, assumes asking resolves the cue) EXPLORATORY
**qwen2.5-7b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 23.8 [15.0, 34.8] | 2.3 [0.0, 5.7] | 0.0 [0.0, 0.0] |  | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 916.3 [894.8, 933.4] |  | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 23.8 [15.0, 34.8] | 2.3 [0.0, 5.7] | 0.0 [0.0, 0.0] |  | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 22.5 [14.2, 32.9] | 2.2 [0.0, 5.4] | 50.0 [48.8, 50.9] |  | 0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 21.2 [13.4, 31.0] | 2.1 [0.0, 5.1] | 100.0 [97.7, 101.9] |  | -0.0 [-0.0, 0.0] | 0.11 [0.11, 0.11] |  |  |
| random-ask @ 25/100 (expectation) | 17.3 [10.9, 25.3] | 1.7 [0.0, 4.2] | 250.0 [244.1, 254.7] |  | 0.0 [-0.0, 0.0] | 0.27 [0.27, 0.27] |  |  |
| disagreement-ask (share>=1/16) | 23.6 [15.0, 34.8] | 0.0 [0.0, 0.0] | 12.6 [5.3, 22.6] |  | -0.1 [-0.5, 0.4] | 0.01 [0.00, 0.03] | no |  |
| disagreement-ask (share>=2/16) | 23.6 [15.0, 34.8] | 0.0 [0.0, 0.0] | 6.6 [2.4, 11.7] |  | 0.1 [-0.3, 0.6] | 0.01 [0.00, 0.03] | no |  |
| disagreement-ask (share>=4/16) | 23.6 [15.0, 34.8] | 0.0 [0.0, 0.0] | 4.3 [1.5, 8.5] |  | 0.1 [-0.2, 0.6] | 0.01 [0.00, 0.03] | no |  |
| disagreement-ask (share>=8/16) | 23.8 [15.0, 34.8] | 0.0 [0.0, 0.0] | 2.6 [0.0, 5.8] |  | -0.1 [-0.2, 0.0] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 22.6 [14.4, 33.4] | 0.0 [0.0, 0.0] | 50.0 [42.9, 59.8] |  | -0.1 [-0.5, 0.4] | 0.05 [0.04, 0.07] | no |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 21.3 [13.6, 31.4] | 0.0 [0.0, 0.0] | 100.0 [93.4, 109.6] |  | -0.1 [-0.5, 0.4] | 0.11 [0.10, 0.13] | no |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 17.4 [11.1, 25.7] | 0.0 [0.0, 0.0] | 250.0 [241.8, 259.3] |  | -0.1 [-0.4, 0.3] | 0.27 [0.26, 0.29] | no |  |
| greedy first-token entropy @ 5/100 | 22.8 [13.9, 33.9] | 2.3 [0.0, 5.7] | 50.8 [37.0, 68.8] |  | -0.3 [-1.6, 1.6] | 0.04 [0.00, 0.15] | no |  |
| greedy first-token entropy @ 10/100 | 21.9 [13.4, 32.9] | 1.2 [0.0, 3.3] | 101.2 [79.0, 126.8] |  | -0.7 [-2.7, 1.7] | 0.08 [0.01, 0.18] | no |  |
| greedy first-token entropy @ 25/100 | 17.4 [9.6, 26.9] | 1.2 [0.0, 3.3] | 252.0 [219.7, 283.7] |  | -0.3 [-3.5, 2.7] | 0.26 [0.15, 0.40] | no |  |
| greedy mean token entropy @ 5/100 | 18.0 [10.9, 27.6] | 2.3 [0.0, 5.7] | 54.2 [40.5, 74.3] |  | 4.2 [0.5, 9.6] | 0.23 [0.09, 0.44] | no |  |
| greedy mean token entropy @ 10/100 | 16.6 [9.8, 25.7] | 2.3 [0.0, 5.7] | 99.3 [78.8, 121.5] |  | 4.3 [0.5, 9.8] | 0.29 [0.13, 0.50] | no |  |
| greedy mean token entropy @ 25/100 | 13.9 [7.4, 23.4] | 1.2 [0.0, 3.3] | 249.1 [219.2, 282.4] |  | 3.1 [-1.7, 8.1] | 0.41 [0.21, 0.61] | no |  |
| lexical logistic (cross-fitted) @ 5/100 | 19.8 [13.0, 27.6] | 2.0 [0.0, 4.8] | 51.4 [37.9, 69.5] |  | 2.9 [-0.1, 6.8] | 0.17 [0.05, 0.31] | no |  |
| lexical logistic (cross-fitted) @ 10/100 | 17.8 [11.4, 24.5] | 1.4 [0.0, 4.5] | 99.5 [77.6, 125.8] |  | 3.6 [0.5, 7.9] | 0.26 [0.13, 0.39] | YES |  |
| lexical logistic (cross-fitted) @ 25/100 | 8.0 [4.6, 11.7] | 1.1 [0.0, 4.5] | 249.0 [212.3, 283.0] |  | 9.4 [3.3, 16.8] | 0.66 [0.45, 0.81] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 2.3 [0.0, 5.7] | 24.0 [15.5, 35.0] |  | 23.0 [14.8, 33.4] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 0.1 [0.1, 0.2] | 2.3 [0.0, 5.7] | 24.0 [15.5, 35.0] |  | 22.9 [14.7, 33.3] | 1.00 [1.00, 1.00] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 0.3 [0.2, 0.5] | 2.3 [0.0, 5.7] | 24.0 [15.5, 35.0] |  | 22.7 [14.5, 32.9] | 0.99 [0.99, 0.99] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 388} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 19.6 [12.2, 29.0] | 0.0 [0.0, 0.0] | 236.3 [226.2, 246.0] |  | -2.0 [-3.3, -0.8] | 0.18 [0.15, 0.21] | no |  |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/8 | 18.7 [11.4, 27.7] | 0.1 [0.0, 0.3] | 255.8 [244.9, 265.7] |  | -1.5 [-2.9, -0.4] | 0.22 [0.18, 0.26] | no |  |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/36 | 19.1 [11.8, 28.7] | 2.3 [0.0, 5.7] | 255.1 [246.7, 263.7] |  | -1.9 [-3.7, -0.6] | 0.20 [0.16, 0.25] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 18.0 [11.4, 27.1] | 0.0 [0.0, 0.0] | 312.2 [300.4, 322.7] |  | -2.3 [-4.3, -0.9] | 0.24 [0.20, 0.30] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/8 | 19.6 [12.3, 28.8] | 1.3 [0.0, 4.0] | 218.5 [207.9, 229.5] |  | -1.5 [-2.7, -0.6] | 0.18 [0.15, 0.21] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/36 | 19.2 [12.2, 28.8] | 2.3 [0.0, 5.7] | 239.3 [228.6, 250.1] |  | -1.6 [-3.1, -0.3] | 0.19 [0.15, 0.24] | no |  |

## T5. Reliability (HT-weighted ECE and Brier, no-cue units; constant base-rate Brier for reference)
| model | set | ECE [95%] | Brier [95%] | Brier of a constant base-rate predictor |
|---|---|---|---|---|
| qwen2.5-7b | human | 0.0289 [0.0191, 0.0409] | 0.0277 [0.0179, 0.0400] | 0.0256 |
| qwen2.5-7b | cap4 | 0.1035 [0.0827, 0.1295] | 0.1035 [0.0821, 0.1291] | 0.0961 |

## T6. Mechanics
- qwen2.5-7b: inputs 1733, missing requests 0, mean unique texts per 16 samples 2.88, finish=length 0, content-free 'Keywords: N/A' sampled negated share 0.0; G1 check on 2160 greedy outputs: {'politeness:added': 388}