## T1. R1, polarity (detector-relative share of no-cue units whose output is negated; HT-weighted; 10,000 item resamples)
| model | set | no-cue units | raw pos. | source posterior % [95%] | greedy share % [95%] | sampled share % [95%] | ratio sampled/posterior [90%] | class (detector) | corrected ratio [90%] | class (corrected) | power |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | 1367 | 68 | 2.62 [1.66, 3.78] | 0.28 [0.03, 0.63] | 0.36 [0.13, 0.66] | 0.14 [0.06, 0.27] | overconfident (default too strong) | 0.16 [0.05, 0.48] | overconfident (default too strong) | confirmatory-eligible |
| qwen2.5-7b | cap4 | 540 | 107 | 10.77 [8.45, 13.26] | 0.39 [0.11, 0.73] | 0.49 [0.22, 0.81] | 0.05 [0.02, 0.07] | overconfident (default too strong) | 0.07 [0.03, 0.16] | overconfident (default too strong) | confirmatory-eligible |
| llama3.1-8b | human | 1367 | 68 | 2.62 [1.66, 3.78] | 1.36 [0.62, 2.23] | 1.87 [1.27, 2.57] | 0.71 [0.46, 1.12] | inconclusive | 0.49 [0.20, 1.03] | inconclusive | confirmatory-eligible |
| llama3.1-8b | cap4 | 540 | 107 | 10.77 [8.45, 13.26] | 0.98 [0.27, 1.91] | 1.57 [1.03, 2.23] | 0.15 [0.10, 0.21] | overconfident (default too strong) | 0.15 [0.09, 0.26] | overconfident (default too strong) | confirmatory-eligible |

## T1b. other dimensions (descriptive only; detector labels, no validity check)
| model | set | dimension | no-cue units | raw pos. | source posterior | greedy share | sampled share | ratio | class |
|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | politeness | 1327 | 124 | 6.55% | 2.96% | 3.70% | 0.56 | inconclusive |
| qwen2.5-7b | human | speech_act | 978 | 388 | 48.23% | 16.43% | 16.70% | 0.35 | overconfident (default too strong) |
| qwen2.5-7b | cap4 | politeness | 441 | 21 | 3.71% | 1.17% | 2.11% | 0.57 | inconclusive |
| qwen2.5-7b | cap4 | speech_act | 372 | 151 | 53.11% | 8.51% | 9.22% | 0.17 | overconfident (default too strong) |
| llama3.1-8b | human | politeness | 1327 | 124 | 6.55% | 7.04% | 8.02% | 1.22 | inconclusive |
| llama3.1-8b | human | speech_act | 978 | 388 | 48.23% | 21.25% | 20.16% | 0.42 | overconfident (default too strong) |
| llama3.1-8b | cap4 | politeness | 441 | 21 | 3.71% | 4.06% | 5.86% | 1.58 | inconclusive |
| llama3.1-8b | cap4 | speech_act | 372 | 151 | 53.11% | 10.67% | 13.64% | 0.26 | overconfident (default too strong) |

## T2. R2, per-input AUROC on no-cue units (tie-aware, HT-weighted; E-human EXPLORATORY)
| model | set | score | AUROC [95%] | raw pos. | power | tied-at-0 (all/pos/neg) | sampled minus lexical [95%] |
|---|---|---|---|---|---|---|---|
| qwen2.5-7b | human | sampled_share(K=16) | 0.50 [0.49, 0.52] | 68 | confirmatory-eligible | 0.99 / 0.97 / 0.99 | -0.25 [-0.32, -0.15] |
| qwen2.5-7b | human | greedy_first_token_entropy | 0.49 [0.37, 0.61] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | greedy_mean_token_entropy | 0.64 [0.53, 0.76] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | lexical_cv_logistic | 0.75 [0.66, 0.82] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | human | greedy_output_negated | 0.50 [0.50, 0.52] | 68 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | sampled_share(K=16) | 0.53 [0.51, 0.55] | 107 | confirmatory-eligible | 0.97 / 0.90 / 0.99 | -0.11 [-0.18, -0.04] |
| qwen2.5-7b | cap4 | greedy_first_token_entropy | 0.49 [0.42, 0.57] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | greedy_mean_token_entropy | 0.59 [0.51, 0.67] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | lexical_cv_logistic | 0.64 [0.58, 0.71] | 107 | confirmatory-eligible |  |  |
| qwen2.5-7b | cap4 | greedy_output_negated | 0.52 [0.50, 0.53] | 107 | confirmatory-eligible |  |  |
| llama3.1-8b | human | sampled_share(K=16) | 0.63 [0.56, 0.70] | 68 | confirmatory-eligible | 0.91 / 0.72 / 0.92 | -0.12 [-0.24, 0.01] |
| llama3.1-8b | human | greedy_first_token_entropy | 0.45 [0.32, 0.58] | 68 | confirmatory-eligible |  |  |
| llama3.1-8b | human | greedy_mean_token_entropy | 0.61 [0.50, 0.71] | 68 | confirmatory-eligible |  |  |
| llama3.1-8b | human | lexical_cv_logistic | 0.75 [0.66, 0.82] | 68 | confirmatory-eligible |  |  |
| llama3.1-8b | human | greedy_output_negated | 0.51 [0.49, 0.55] | 68 | confirmatory-eligible |  |  |
| llama3.1-8b | cap4 | sampled_share(K=16) | 0.59 [0.54, 0.65] | 107 | confirmatory-eligible | 0.87 / 0.71 / 0.91 | -0.05 [-0.14, 0.03] |
| llama3.1-8b | cap4 | greedy_first_token_entropy | 0.48 [0.40, 0.56] | 107 | confirmatory-eligible |  |  |
| llama3.1-8b | cap4 | greedy_mean_token_entropy | 0.63 [0.57, 0.70] | 107 | confirmatory-eligible |  |  |
| llama3.1-8b | cap4 | lexical_cv_logistic | 0.64 [0.58, 0.71] | 107 | confirmatory-eligible |  |  |
| llama3.1-8b | cap4 | greedy_output_negated | 0.51 [0.50, 0.52] | 107 | confirmatory-eligible |  |  |

## T2b. Model-pooled, item-clustered (same resample for both models)
| set | quantity | models | estimate [95%] | status |
|---|---|---|---|---|
| human | auroc:greedy_first_token_entropy | 2 | 0.47 [0.35, 0.59] | pooled, item-clustered EXPLORATORY |
| human | auroc:greedy_mean_token_entropy | 2 | 0.62 [0.53, 0.72] | pooled, item-clustered EXPLORATORY |
| human | auroc:greedy_output_negated | 2 | 0.51 [0.50, 0.53] | pooled, item-clustered EXPLORATORY |
| human | auroc:lexical_cv_logistic | 2 | 0.75 [0.66, 0.82] | pooled, item-clustered EXPLORATORY |
| human | auroc:sampled_share(K=16) | 2 | 0.56 [0.53, 0.60] | pooled, item-clustered EXPLORATORY |
| human | sampled_share AUROC minus lexical_cv_logistic | 2 | -0.18 [-0.27, -0.07] | pooled, item-clustered EXPLORATORY |
| human | sampled_share AUROC minus greedy_first_token_entropy | 2 | 0.09 [-0.02, 0.21] | pooled, item-clustered EXPLORATORY |
| human | sampled_share AUROC minus greedy_mean_token_entropy | 2 | -0.06 [-0.16, 0.05] | pooled, item-clustered EXPLORATORY |
| human | d_cost vs always-commit (sampled-share-ask @10/100) | 2 | -9.05 [-13.95, -4.69] | pooled, item-clustered EXPLORATORY |
| human | caught minus random (sampled-share-ask @10/100) | 2 | 2.50 [0.89, 4.32] | pooled, item-clustered EXPLORATORY |
| cap4 | auroc:greedy_first_token_entropy | 2 | 0.49 [0.42, 0.56] | pooled, item-clustered |
| cap4 | auroc:greedy_mean_token_entropy | 2 | 0.61 [0.54, 0.67] | pooled, item-clustered |
| cap4 | auroc:greedy_output_negated | 2 | 0.51 [0.50, 0.53] | pooled, item-clustered |
| cap4 | auroc:lexical_cv_logistic | 2 | 0.64 [0.58, 0.71] | pooled, item-clustered |
| cap4 | auroc:sampled_share(K=16) | 2 | 0.56 [0.53, 0.59] | pooled, item-clustered |
| cap4 | sampled_share AUROC minus lexical_cv_logistic | 2 | -0.08 [-0.16, -0.01] | pooled, item-clustered |
| cap4 | sampled_share AUROC minus greedy_first_token_entropy | 2 | 0.07 [-0.00, 0.15] | pooled, item-clustered |
| cap4 | sampled_share AUROC minus greedy_mean_token_entropy | 2 | -0.05 [-0.11, 0.01] | pooled, item-clustered |
| cap4 | d_cost vs always-commit (sampled-share-ask @10/100) | 2 | -19.01 [-26.62, -12.03] | pooled, item-clustered |
| cap4 | caught minus random (sampled-share-ask @10/100) | 2 | 7.79 [2.98, 13.02] | pooled, item-clustered |

## T3. Holm family (E-cap4 confirmatory; one-sided bootstrap p)
| model | test | p raw | p Holm | reject at 0.05 |
|---|---|---|---|---|
| qwen2.5-7b | R2-a sampled-share AUROC > 0.5 | 0.0006 | 0.0030 | yes |
| qwen2.5-7b | R2-b sampled-share AUROC > lexical (paired) | 0.9990 | 1.0000 | no |
| qwen2.5-7b | R3-a tap-priced (0.03) weighted cost of sampled-share-ask @10/100 < always-commit | 0.0001 | 0.0008 | yes |
| qwen2.5-7b | R3-b caught_minus_random > 0 for sampled-share-ask @10/100 | 0.0597 | 0.1791 | no |
| llama3.1-8b | R2-a sampled-share AUROC > 0.5 | 0.0001 | 0.0008 | yes |
| llama3.1-8b | R2-b sampled-share AUROC > lexical (paired) | 0.8977 | 1.0000 | no |
| llama3.1-8b | R3-a tap-priced (0.03) weighted cost of sampled-share-ask @10/100 < always-commit | 0.0001 | 0.0008 | yes |
| llama3.1-8b | R3-b caught_minus_random > 0 for sampled-share-ask @10/100 | 0.0008 | 0.0032 | yes |

## T4. Benchmark, E-cap4: silent polarity reversals, spurious negations and taps per 1,000 units (SLP weights w_rev = w_spur = 1 unless stated; simulated, assumes asking resolves the cue)
**llama3.1-8b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 104.9 [81.8, 129.7] | 7.0 [0.0, 16.1] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 1000.0 [1000.0, 1000.0] | -81.9 [-107.6, -57.4] | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 104.9 [81.8, 129.7] | 2.3 [0.0, 7.2] | 0.0 [0.0, 0.0] | -4.7 [-11.8, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 99.7 [77.7, 123.2] | 6.6 [0.0, 15.3] | 50.0 [50.0, 50.0] | -4.1 [-5.4, -2.9] | -0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 94.4 [73.6, 116.7] | 6.3 [0.0, 14.5] | 100.0 [100.0, 100.0] | -8.2 [-10.8, -5.7] | 0.0 [-0.0, 0.0] | 0.10 [0.10, 0.10] |  |  |
| random-ask @ 25/100 (expectation) | 78.7 [61.4, 97.3] | 5.2 [0.0, 12.1] | 250.0 [250.0, 250.0] | -20.5 [-26.9, -14.3] | 0.0 [-0.0, 0.0] | 0.25 [0.25, 0.25] |  |  |
| disagreement-ask (share>=1/16) | 78.9 [59.0, 100.7] | 0.0 [0.0, 0.0] | 108.3 [80.5, 138.2] | -29.7 [-44.1, -16.7] | 14.6 [5.2, 25.1] | 0.25 [0.15, 0.35] | YES |  |
| disagreement-ask (share>=2/16) | 93.8 [71.9, 117.2] | 0.0 [0.0, 0.0] | 44.4 [27.1, 64.5] | -16.8 [-28.3, -7.2] | 6.5 [0.5, 13.9] | 0.11 [0.05, 0.18] | YES |  |
| disagreement-ask (share>=4/16) | 102.8 [79.7, 127.4] | 2.3 [0.0, 7.1] | 18.1 [7.8, 30.8] | -6.2 [-13.8, -0.5] | 0.2 [-2.1, 2.8] | 0.02 [0.00, 0.05] | no |  |
| disagreement-ask (share>=8/16) | 104.9 [81.8, 129.7] | 4.7 [0.0, 11.8] | 5.1 [0.7, 11.3] | -2.1 [-6.9, 0.2] | -0.5 [-1.2, -0.1] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 92.8 [71.3, 115.8] | 0.0 [0.0, 0.0] | 50.8 [33.8, 70.2] | -17.6 [-28.7, -8.3] | 6.8 [1.2, 13.6] | 0.12 [0.06, 0.18] | YES |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 80.8 [61.0, 102.6] | 0.0 [0.0, 0.0] | 101.9 [76.3, 129.7] | -28.0 [-41.6, -15.7] | 13.4 [4.7, 23.2] | 0.23 [0.14, 0.33] | YES |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 66.5 [49.7, 84.8] | 0.0 [0.0, 0.0] | 249.7 [226.4, 274.9] | -37.9 [-52.6, -24.6] | 12.2 [4.4, 21.1] | 0.37 [0.29, 0.45] | YES |  |
| greedy first-token entropy @ 5/100 | 102.0 [78.9, 126.3] | 7.0 [0.0, 16.1] | 49.6 [31.1, 70.0] | -1.4 [-4.2, 0.8] | -2.3 [-5.5, 0.9] | 0.03 [0.01, 0.06] | no |  |
| greedy first-token entropy @ 10/100 | 95.7 [73.7, 119.5] | 4.5 [0.0, 11.5] | 101.0 [73.5, 130.3] | -8.5 [-17.7, -1.4] | -1.4 [-7.6, 5.8] | 0.09 [0.03, 0.16] | no |  |
| greedy first-token entropy @ 25/100 | 80.2 [59.9, 102.3] | 2.3 [0.0, 7.1] | 249.0 [208.2, 290.6] | -21.9 [-35.8, -10.1] | -1.3 [-10.9, 8.9] | 0.24 [0.15, 0.34] | no |  |
| greedy mean token entropy @ 5/100 | 96.8 [74.5, 120.7] | 7.0 [0.0, 16.1] | 53.9 [34.5, 75.4] | -6.5 [-14.2, -0.8] | 2.5 [-3.1, 9.5] | 0.08 [0.02, 0.15] | no |  |
| greedy mean token entropy @ 10/100 | 92.5 [70.8, 115.9] | 5.0 [0.0, 12.2] | 104.3 [77.4, 132.5] | -11.2 [-20.2, -3.7] | 1.4 [-5.0, 9.0] | 0.12 [0.06, 0.19] | no |  |
| greedy mean token entropy @ 25/100 | 67.0 [49.6, 86.3] | 2.3 [0.0, 7.2] | 250.4 [210.9, 290.5] | -35.0 [-51.0, -20.1] | 11.6 [1.1, 23.0] | 0.36 [0.26, 0.47] | YES |  |
| lexical logistic (cross-fitted) @ 5/100 | 87.7 [67.1, 110.1] | 7.0 [0.0, 16.1] | 49.0 [31.8, 68.5] | -15.7 [-26.4, -7.1] | 12.1 [4.2, 21.5] | 0.16 [0.09, 0.26] | YES |  |
| lexical logistic (cross-fitted) @ 10/100 | 81.3 [61.4, 103.3] | 7.0 [0.0, 16.1] | 102.0 [75.6, 130.2] | -20.5 [-32.4, -10.6] | 12.8 [3.9, 23.2] | 0.22 [0.14, 0.33] | YES |  |
| lexical logistic (cross-fitted) @ 25/100 | 63.8 [45.8, 83.9] | 4.7 [0.0, 11.8] | 250.4 [210.4, 291.6] | -35.9 [-51.9, -21.7] | 14.9 [3.7, 26.8] | 0.39 [0.28, 0.51] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 7.0 [0.0, 16.1] | 107.7 [84.5, 132.6] | -101.7 [-125.7, -79.2] | 93.5 [74.9, 112.5] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 1.0 [0.8, 1.2] | 7.0 [0.0, 16.1] | 107.7 [84.5, 132.6] | -100.7 [-124.5, -78.5] | 92.5 [74.1, 111.2] | 0.99 [0.99, 0.99] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 0.5 [0.4, 0.6] | 7.0 [0.0, 16.1] | 107.7 [84.5, 132.6] | -101.2 [-125.1, -78.9] | 93.0 [74.5, 111.8] | 1.00 [1.00, 1.00] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 431} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 0.0 [0.0, 0.0] | 0.1 [0.0, 0.4] | 999.8 [999.5, 1000.0] | -81.8 [-107.4, -57.3] | 0.0 [0.0, 0.1] | 1.00 [1.00, 1.00] | YES |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/1 | 50.8 [37.7, 65.1] | 0.8 [0.0, 2.5] | 485.8 [467.8, 504.2] | -45.7 [-61.6, -31.1] | 3.1 [-3.0, 9.7] | 0.52 [0.45, 0.58] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/8 | 48.2 [35.5, 62.2] | 6.3 [0.0, 14.4] | 500.7 [482.6, 519.5] | -41.8 [-56.7, -28.3] | 4.2 [-1.9, 10.8] | 0.54 [0.48, 0.61] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/36 | 53.8 [39.8, 69.0] | 7.0 [0.0, 16.1] | 413.6 [394.1, 434.2] | -38.7 [-52.8, -26.1] | 7.7 [1.0, 15.1] | 0.49 [0.42, 0.56] | YES |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 100.0 [77.6, 124.1] | 0.0 [0.0, 0.0] | 31.3 [17.5, 47.7] | -10.9 [-20.0, -3.6] | 1.6 [-1.5, 5.0] | 0.05 [0.02, 0.08] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/1 | 104.4 [81.2, 129.0] | 0.0 [0.0, 0.0] | 12.7 [4.4, 23.0] | -7.1 [-15.8, -0.3] | -0.8 [-2.2, 0.6] | 0.01 [0.00, 0.02] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/8 | 104.4 [81.2, 129.0] | 2.3 [0.0, 7.2] | 9.3 [2.8, 18.0] | -0.8 [-2.3, 0.1] | -0.4 [-1.6, 0.9] | 0.01 [0.00, 0.02] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/36 | 104.4 [81.2, 129.1] | 7.0 [0.0, 16.1] | 2.5 [0.0, 6.7] | -0.4 [-1.5, 0.2] | 0.2 [-0.5, 1.3] | 0.00 [0.00, 0.02] | no |  |

**qwen2.5-7b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 104.2 [81.2, 128.9] | 0.4 [0.0, 1.3] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 1000.0 [1000.0, 1000.0] | -74.7 [-99.1, -51.4] | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 104.9 [81.8, 129.7] | 0.4 [0.0, 1.3] | 0.0 [0.0, 0.0] | 0.7 [0.0, 2.2] | -0.7 [-2.2, 0.0] | -0.01 [-0.02, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 99.0 [77.1, 122.4] | 0.4 [0.0, 1.2] | 50.0 [50.0, 50.0] | -3.7 [-5.0, -2.6] | -0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 93.8 [73.1, 116.0] | 0.4 [0.0, 1.1] | 100.0 [100.0, 100.0] | -7.5 [-9.9, -5.1] | 0.0 [-0.0, 0.0] | 0.10 [0.10, 0.10] |  |  |
| random-ask @ 25/100 (expectation) | 78.2 [60.9, 96.6] | 0.3 [0.0, 0.9] | 250.0 [250.0, 250.0] | -18.7 [-24.8, -12.9] | 0.0 [-0.0, 0.0] | 0.25 [0.25, 0.25] |  |  |
| disagreement-ask (share>=1/16) | 100.0 [77.1, 124.0] | 0.0 [0.0, 0.0] | 17.3 [7.5, 30.0] | -4.1 [-7.7, -1.1] | 2.4 [-0.5, 5.9] | 0.04 [0.01, 0.08] | no |  |
| disagreement-ask (share>=2/16) | 101.4 [78.4, 125.5] | 0.0 [0.0, 0.0] | 6.8 [2.9, 11.2] | -3.0 [-6.1, -0.6] | 2.1 [-0.0, 4.8] | 0.03 [0.01, 0.06] | no |  |
| disagreement-ask (share>=4/16) | 102.8 [79.8, 127.2] | 0.0 [0.0, 0.0] | 5.4 [2.1, 9.3] | -1.7 [-4.0, 0.1] | 0.9 [-0.6, 2.9] | 0.01 [0.00, 0.04] | no |  |
| disagreement-ask (share>=8/16) | 104.2 [81.2, 128.9] | 0.0 [0.0, 0.0] | 3.2 [0.7, 6.3] | -0.3 [-1.2, 0.2] | -0.3 [-0.7, -0.1] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 96.7 [74.6, 119.9] | 0.0 [0.0, 0.0] | 49.9 [40.4, 62.2] | -6.5 [-10.2, -3.3] | 2.3 [-0.5, 5.7] | 0.07 [0.05, 0.11] | no |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 91.6 [70.6, 113.6] | 0.0 [0.0, 0.0] | 99.9 [90.9, 111.5] | -10.1 [-14.2, -6.4] | 2.2 [-0.5, 5.4] | 0.12 [0.10, 0.15] | no |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 76.3 [58.9, 94.7] | 0.0 [0.0, 0.0] | 249.9 [242.4, 259.6] | -20.8 [-27.6, -14.5] | 1.9 [-0.4, 4.5] | 0.27 [0.25, 0.30] | no |  |
| greedy first-token entropy @ 5/100 | 98.3 [76.3, 122.1] | 0.4 [0.0, 1.3] | 52.4 [32.1, 74.0] | -4.2 [-10.9, 0.7] | 0.4 [-4.6, 6.6] | 0.06 [0.01, 0.12] | no |  |
| greedy first-token entropy @ 10/100 | 95.7 [73.9, 119.3] | 0.4 [0.0, 1.3] | 100.4 [73.4, 129.2] | -5.5 [-13.0, 0.4] | -2.0 [-8.1, 5.1] | 0.08 [0.02, 0.15] | no |  |
| greedy first-token entropy @ 25/100 | 77.1 [57.4, 99.1] | 0.3 [0.0, 0.8] | 250.5 [209.9, 291.5] | -19.7 [-32.2, -8.6] | 1.0 [-9.0, 11.5] | 0.26 [0.16, 0.37] | no |  |
| greedy mean token entropy @ 5/100 | 94.8 [73.4, 117.8] | 0.4 [0.0, 1.3] | 52.8 [33.5, 74.2] | -7.7 [-15.8, -1.5] | 3.8 [-2.1, 11.0] | 0.09 [0.03, 0.16] | no |  |
| greedy mean token entropy @ 10/100 | 81.4 [62.0, 103.0] | 0.4 [0.0, 1.3] | 101.0 [74.2, 129.9] | -19.7 [-31.7, -9.3] | 12.2 [3.0, 22.6] | 0.22 [0.13, 0.32] | YES |  |
| greedy mean token entropy @ 25/100 | 66.5 [48.9, 86.1] | 0.4 [0.0, 1.2] | 249.0 [209.1, 290.3] | -30.1 [-45.4, -16.5] | 11.6 [0.6, 23.4] | 0.36 [0.25, 0.47] | YES |  |
| lexical logistic (cross-fitted) @ 5/100 | 87.0 [66.5, 109.3] | 0.4 [0.0, 1.3] | 49.0 [31.8, 68.5] | -15.7 [-26.4, -7.1] | 12.1 [4.2, 21.6] | 0.17 [0.09, 0.26] | YES |  |
| lexical logistic (cross-fitted) @ 10/100 | 80.6 [60.7, 102.6] | 0.4 [0.0, 1.3] | 102.0 [75.6, 130.2] | -20.5 [-32.4, -10.6] | 12.9 [4.0, 23.3] | 0.23 [0.14, 0.33] | YES |  |
| lexical logistic (cross-fitted) @ 25/100 | 63.1 [45.1, 83.1] | 0.4 [0.0, 1.3] | 250.4 [210.4, 291.6] | -33.6 [-48.8, -20.1] | 15.0 [4.0, 26.9] | 0.39 [0.28, 0.51] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.3] | 107.7 [84.5, 132.6] | -101.0 [-124.9, -78.7] | 92.9 [74.3, 111.8] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 0.5 [0.4, 0.6] | 0.4 [0.0, 1.3] | 107.7 [84.5, 132.6] | -100.5 [-124.3, -78.3] | 92.4 [73.9, 111.1] | 1.00 [1.00, 1.00] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 1.5 [1.2, 1.9] | 0.4 [0.0, 1.3] | 107.7 [84.5, 132.6] | -99.5 [-123.0, -77.5] | 91.4 [73.2, 109.9] | 0.99 [0.99, 0.99] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 388} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.3] | 998.0 [996.1, 999.6] | -74.3 [-98.9, -51.2] | 0.2 [0.0, 0.4] | 1.00 [1.00, 1.00] | YES |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/1 | 42.9 [32.6, 54.0] | 0.4 [0.0, 1.3] | 630.1 [620.2, 640.0] | -42.4 [-56.5, -29.2] | -4.3 [-7.4, -1.4] | 0.59 [0.56, 0.62] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/8 | 50.1 [38.2, 62.9] | 0.4 [0.0, 1.3] | 557.8 [546.4, 569.1] | -37.4 [-50.2, -25.5] | -3.9 [-7.4, -0.7] | 0.52 [0.49, 0.55] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/36 | 53.6 [40.9, 67.2] | 0.4 [0.0, 1.3] | 506.3 [494.6, 517.9] | -35.4 [-47.5, -24.2] | -2.1 [-5.8, 1.4] | 0.49 [0.45, 0.52] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 0.0 [0.0, 0.0] | 0.4 [0.0, 1.3] | 996.8 [993.7, 999.3] | -74.3 [-98.9, -51.3] | 0.3 [0.1, 0.7] | 1.00 [1.00, 1.00] | YES |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/1 | 20.3 [15.5, 25.5] | 0.4 [0.0, 1.3] | 827.0 [820.0, 833.8] | -59.1 [-78.8, -40.6] | -2.3 [-3.9, -0.7] | 0.81 [0.79, 0.82] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/8 | 28.0 [21.2, 35.5] | 0.4 [0.0, 1.3] | 753.1 [744.7, 761.4] | -53.6 [-71.2, -37.0] | -2.3 [-4.6, -0.1] | 0.73 [0.71, 0.75] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/36 | 33.4 [25.4, 42.0] | 0.4 [0.0, 1.3] | 703.2 [693.7, 712.4] | -49.8 [-66.2, -34.3] | -2.4 [-4.7, -0.2] | 0.68 [0.66, 0.70] | no |  |

## T4. Benchmark, E-human: silent polarity reversals, spurious negations and taps per 1,000 units (SLP weights w_rev = w_spur = 1 unless stated; simulated, assumes asking resolves the cue) EXPLORATORY
**llama3.1-8b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 23.3 [14.6, 33.5] | 11.7 [5.1, 19.6] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 916.3 [895.4, 935.5] | -7.4 [-20.0, 3.9] | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 23.3 [14.6, 33.5] | 10.1 [4.3, 17.2] | 0.0 [0.0, 0.0] | -1.5 [-5.5, 2.3] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 22.0 [13.8, 31.7] | 11.0 [4.8, 18.5] | 50.0 [48.9, 51.0] | -0.4 [-1.1, 0.2] | 0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 20.7 [13.0, 29.9] | 10.4 [4.6, 17.4] | 100.0 [97.7, 102.1] | -0.8 [-2.2, 0.4] | -0.0 [-0.0, 0.0] | 0.11 [0.11, 0.11] |  |  |
| random-ask @ 25/100 (expectation) | 16.9 [10.6, 24.4] | 8.5 [3.7, 14.2] | 250.0 [244.3, 255.2] | -2.0 [-5.5, 1.1] | 0.0 [-0.0, 0.0] | 0.27 [0.27, 0.27] |  |  |
| disagreement-ask (share>=1/16) | 15.9 [8.9, 24.3] | 0.0 [0.0, 0.0] | 84.3 [62.8, 107.0] | -16.4 [-25.0, -8.9] | 5.2 [2.0, 8.9] | 0.32 [0.19, 0.46] | YES |  |
| disagreement-ask (share>=2/16) | 19.4 [11.6, 28.6] | 0.0 [0.0, 0.0] | 46.2 [31.1, 62.9] | -14.1 [-22.2, -7.2] | 2.7 [0.4, 5.5] | 0.17 [0.07, 0.29] | YES |  |
| disagreement-ask (share>=4/16) | 21.5 [13.5, 30.9] | 0.0 [0.0, 0.0] | 27.1 [16.1, 39.4] | -12.6 [-20.5, -5.9] | 1.1 [-0.6, 3.4] | 0.08 [0.00, 0.17] | no |  |
| disagreement-ask (share>=8/16) | 23.3 [14.6, 33.5] | 2.7 [0.0, 6.1] | 10.9 [4.8, 18.1] | -8.7 [-15.2, -3.3] | -0.3 [-0.5, -0.1] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 19.0 [11.5, 28.0] | 0.0 [0.0, 0.0] | 50.8 [35.8, 67.5] | -14.3 [-22.4, -7.4] | 2.9 [0.7, 5.6] | 0.18 [0.09, 0.30] | YES |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 15.6 [8.8, 23.8] | 0.0 [0.0, 0.0] | 99.9 [78.9, 122.3] | -16.3 [-24.8, -8.7] | 5.1 [1.9, 8.7] | 0.33 [0.20, 0.47] | YES |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 12.7 [7.2, 19.4] | 0.0 [0.0, 0.0] | 249.9 [232.1, 268.7] | -14.6 [-23.5, -6.7] | 4.2 [1.6, 7.1] | 0.45 [0.35, 0.57] | YES |  |
| greedy first-token entropy @ 5/100 | 21.0 [12.9, 30.7] | 8.7 [3.4, 15.1] | 50.6 [37.0, 65.3] | -3.7 [-8.2, -0.1] | 0.9 [-0.8, 3.1] | 0.10 [0.02, 0.19] | no |  |
| greedy first-token entropy @ 10/100 | 20.5 [12.4, 29.9] | 7.8 [2.7, 14.1] | 101.2 [80.5, 123.1] | -3.6 [-9.1, 0.8] | 0.2 [-1.8, 2.6] | 0.12 [0.03, 0.22] | no |  |
| greedy first-token entropy @ 25/100 | 17.1 [10.3, 25.4] | 7.1 [2.1, 13.2] | 248.5 [216.3, 281.3] | -3.3 [-11.2, 2.9] | -0.2 [-3.9, 4.5] | 0.26 [0.10, 0.45] | no |  |
| greedy mean token entropy @ 5/100 | 18.9 [12.2, 26.6] | 9.6 [3.8, 16.6] | 51.3 [36.1, 68.3] | -4.9 [-10.9, -0.2] | 3.1 [-0.5, 7.8] | 0.18 [0.02, 0.33] | no |  |
| greedy mean token entropy @ 10/100 | 18.2 [11.6, 25.7] | 9.3 [3.6, 16.3] | 100.0 [78.9, 122.1] | -4.4 [-10.8, 0.5] | 2.6 [-0.8, 7.0] | 0.21 [0.06, 0.36] | no |  |
| greedy mean token entropy @ 25/100 | 13.1 [7.7, 19.4] | 9.1 [3.4, 15.9] | 247.8 [214.4, 281.3] | -5.3 [-13.3, 0.9] | 3.9 [-0.1, 8.9] | 0.43 [0.27, 0.60] | no |  |
| lexical logistic (cross-fitted) @ 5/100 | 20.0 [12.6, 28.4] | 11.3 [4.9, 19.0] | 51.4 [35.9, 68.3] | -2.1 [-6.4, 0.8] | 2.0 [-0.6, 5.8] | 0.14 [0.02, 0.28] | no |  |
| lexical logistic (cross-fitted) @ 10/100 | 18.1 [11.3, 25.7] | 10.9 [4.5, 18.5] | 99.5 [77.1, 123.6] | -3.0 [-7.9, 0.8] | 2.7 [-0.3, 6.5] | 0.22 [0.10, 0.35] | no |  |
| lexical logistic (cross-fitted) @ 25/100 | 8.2 [4.8, 12.1] | 10.1 [3.9, 17.7] | 249.0 [215.6, 283.8] | -9.2 [-18.7, -1.1] | 8.7 [3.1, 15.5] | 0.64 [0.45, 0.79] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 11.7 [5.1, 19.6] | 24.0 [15.2, 34.4] | -22.6 [-32.5, -14.1] | 22.6 [14.3, 32.3] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 0.2 [0.1, 0.3] | 11.7 [5.1, 19.6] | 24.0 [15.2, 34.4] | -22.3 [-32.2, -14.0] | 22.4 [14.2, 32.0] | 0.99 [0.99, 0.99] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 0.1 [0.1, 0.2] | 11.7 [5.1, 19.6] | 24.0 [15.2, 34.4] | -22.4 [-32.3, -14.0] | 22.5 [14.2, 32.1] | 1.00 [1.00, 1.00] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 431} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 16.9 [9.9, 25.3] | 0.0 [0.0, 0.0] | 174.5 [158.3, 191.7] | -12.8 [-21.1, -5.7] | 1.9 [-0.3, 4.4] | 0.28 [0.18, 0.38] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/1 | 23.0 [14.4, 33.2] | 0.0 [0.0, 0.0] | 16.2 [9.0, 24.5] | -11.4 [-19.1, -5.1] | -0.1 [-0.5, 0.4] | 0.01 [0.00, 0.04] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/8 | 23.0 [14.4, 33.1] | 3.4 [0.8, 6.7] | 13.6 [7.7, 20.3] | -0.9 [-1.6, -0.3] | -0.1 [-0.4, 0.3] | 0.01 [0.00, 0.03] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/36 | 23.1 [14.5, 33.2] | 11.7 [5.1, 19.6] | 3.8 [1.6, 6.5] | -0.1 [-0.3, 0.1] | 0.1 [-0.1, 0.3] | 0.01 [0.00, 0.02] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 23.3 [14.6, 33.5] | 0.0 [0.0, 0.0] | 13.9 [7.0, 22.1] | -11.2 [-18.9, -4.9] | -0.4 [-0.6, -0.2] | 0.00 [0.00, 0.00] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/1 | 23.3 [14.6, 33.5] | 0.0 [0.0, 0.0] | 12.4 [5.6, 20.4] | -11.3 [-18.9, -5.0] | -0.3 [-0.6, -0.1] | 0.00 [0.00, 0.00] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/8 | 23.3 [14.6, 33.5] | 0.2 [0.0, 0.5] | 12.3 [5.6, 20.1] | -1.1 [-1.8, -0.5] | -0.3 [-0.6, -0.1] | 0.00 [0.00, 0.00] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/36 | 23.3 [14.6, 33.5] | 11.7 [5.1, 19.6] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | no |  |

**qwen2.5-7b**

| policy | reversals/1000 | spurious/1000 | taps/1000 | d priced cost vs commit (tap = 0.03) | caught minus matched random-ask | recall of reversals | recovers R3 | note |
|---|---|---|---|---|---|---|---|---|
| always-commit (greedy) | 23.8 [15.0, 34.1] | 2.3 [0.0, 5.5] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] |  |  |
| always-ask (every no-cue unit) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 916.3 [895.4, 935.5] | 1.3 [-9.5, 10.6] | 0.0 [0.0, 0.0] | 1.00 [1.00, 1.00] |  |  |
| sampled-commit (majority of 16) | 23.8 [15.0, 34.1] | 2.3 [0.0, 5.5] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | no |  |
| random-ask @ 5/100 (expectation) | 22.5 [14.1, 32.3] | 2.2 [0.0, 5.2] | 50.0 [48.9, 51.0] | 0.1 [-0.5, 0.6] | 0.0 [-0.0, 0.0] | 0.05 [0.05, 0.05] |  |  |
| random-ask @ 10/100 (expectation) | 21.2 [13.3, 30.4] | 2.1 [0.0, 4.9] | 100.0 [97.7, 102.1] | 0.1 [-1.0, 1.2] | -0.0 [-0.0, 0.0] | 0.11 [0.11, 0.11] |  |  |
| random-ask @ 25/100 (expectation) | 17.3 [10.9, 24.8] | 1.7 [0.0, 4.0] | 250.0 [244.3, 255.2] | 0.4 [-2.6, 2.9] | 0.0 [-0.0, 0.0] | 0.27 [0.27, 0.27] |  |  |
| disagreement-ask (share>=1/16) | 23.6 [14.8, 33.9] | 0.0 [0.0, 0.0] | 12.6 [5.2, 21.9] | -2.2 [-5.3, 0.1] | -0.1 [-0.5, 0.5] | 0.01 [0.00, 0.04] | no |  |
| disagreement-ask (share>=2/16) | 23.6 [14.8, 33.9] | 0.0 [0.0, 0.0] | 6.6 [2.4, 11.7] | -2.4 [-5.4, -0.1] | 0.1 [-0.3, 0.6] | 0.01 [0.00, 0.04] | no |  |
| disagreement-ask (share>=4/16) | 23.6 [14.8, 33.9] | 0.0 [0.0, 0.0] | 4.3 [1.2, 8.3] | -2.4 [-5.5, -0.2] | 0.1 [-0.2, 0.6] | 0.01 [0.00, 0.04] | no |  |
| disagreement-ask (share>=8/16) | 23.8 [15.0, 34.1] | 0.0 [0.0, 0.0] | 2.6 [0.2, 5.8] | -2.2 [-5.3, 0.0] | -0.1 [-0.2, -0.0] | 0.00 [0.00, 0.00] | no |  |
| sampled share (semantic-entropy analogue) @ 5/100 | 22.6 [14.1, 32.5] | 0.0 [0.0, 0.0] | 50.0 [42.8, 59.0] | -2.0 [-5.2, 0.3] | -0.1 [-0.5, 0.5] | 0.05 [0.04, 0.08] | no |  |
| sampled share (semantic-entropy analogue) @ 10/100 | 21.3 [13.3, 30.6] | 0.0 [0.0, 0.0] | 100.0 [92.8, 108.7] | -1.8 [-5.1, 0.7] | -0.1 [-0.5, 0.4] | 0.11 [0.10, 0.13] | no |  |
| sampled share (semantic-entropy analogue) @ 25/100 | 17.4 [10.9, 25.0] | 0.0 [0.0, 0.0] | 250.0 [241.9, 258.7] | -1.2 [-5.3, 2.2] | -0.1 [-0.4, 0.4] | 0.27 [0.26, 0.29] | no |  |
| greedy first-token entropy @ 5/100 | 22.8 [14.0, 33.1] | 2.3 [0.0, 5.5] | 50.8 [34.6, 68.7] | 0.5 [-1.4, 1.7] | -0.3 [-1.6, 1.6] | 0.04 [0.00, 0.13] | no |  |
| greedy first-token entropy @ 10/100 | 21.9 [13.3, 32.2] | 1.2 [0.0, 3.2] | 101.2 [79.1, 123.9] | 0.0 [-3.4, 2.5] | -0.7 [-2.6, 1.4] | 0.08 [0.01, 0.18] | no |  |
| greedy first-token entropy @ 25/100 | 17.4 [9.7, 27.0] | 1.2 [0.0, 3.2] | 252.0 [219.0, 284.9] | 0.0 [-4.4, 3.9] | -0.2 [-3.5, 3.1] | 0.27 [0.15, 0.42] | no |  |
| greedy mean token entropy @ 5/100 | 18.0 [10.7, 26.5] | 2.3 [0.0, 5.5] | 54.2 [38.9, 71.0] | -4.2 [-10.2, 0.0] | 4.4 [0.4, 10.1] | 0.24 [0.08, 0.44] | no |  |
| greedy mean token entropy @ 10/100 | 16.6 [9.6, 25.0] | 2.3 [0.0, 5.5] | 99.3 [78.8, 121.5] | -4.2 [-10.3, 0.3] | 4.6 [0.5, 10.1] | 0.30 [0.13, 0.49] | no |  |
| greedy mean token entropy @ 25/100 | 13.9 [7.3, 22.0] | 1.2 [0.0, 3.2] | 249.1 [218.8, 281.2] | -3.6 [-10.3, 1.8] | 3.4 [-0.7, 8.3] | 0.42 [0.24, 0.61] | no |  |
| lexical logistic (cross-fitted) @ 5/100 | 19.8 [12.4, 28.1] | 2.0 [0.0, 4.9] | 51.4 [35.9, 68.3] | -2.8 [-7.2, 0.4] | 2.7 [-0.2, 6.7] | 0.17 [0.04, 0.31] | no |  |
| lexical logistic (cross-fitted) @ 10/100 | 17.8 [11.1, 25.5] | 1.4 [0.0, 4.1] | 99.5 [77.1, 123.6] | -3.9 [-9.1, 0.1] | 3.4 [0.2, 7.4] | 0.25 [0.12, 0.38] | no |  |
| lexical logistic (cross-fitted) @ 25/100 | 8.0 [4.6, 11.9] | 1.1 [0.0, 3.5] | 249.0 [215.6, 283.8] | -9.6 [-19.1, -1.5] | 9.4 [3.7, 16.2] | 0.66 [0.48, 0.80] | YES |  |
| oracle-ask (upper bound) | 0.0 [0.0, 0.0] | 2.3 [0.0, 5.5] | 24.0 [15.2, 34.4] | -23.1 [-33.1, -14.5] | 23.2 [14.7, 32.9] | 1.00 [1.00, 1.00] |  |  |
| cue chip (ORACLE-triggered user x measured honour rate; upper bound) | 0.1 [0.1, 0.2] | 2.3 [0.0, 5.5] | 24.0 [15.2, 34.4] | -23.0 [-32.9, -14.4] | 23.1 [14.6, 32.7] | 1.00 [1.00, 1.00] | YES |  |
| plain word (ORACLE-triggered user x measured honour rate; upper bound) | 0.3 [0.2, 0.5] | 2.3 [0.0, 5.5] | 24.0 [15.2, 34.4] | -22.8 [-32.6, -14.3] | 22.8 [14.5, 32.4] | 0.99 [0.99, 0.99] | YES |  |
| guard G1 (NOT APPLICABLE to bare keywords) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on 2160 greedy outputs: {'politeness:added': 388} (nei |
| Platt-calibrated cost-optimal ask c=0.03 w_spur=1/1 | 19.6 [12.1, 28.6] | 0.0 [0.0, 0.0] | 236.3 [226.5, 245.9] | 0.6 [-2.8, 3.4] | -2.0 [-3.4, -0.9] | 0.18 [0.15, 0.21] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/1 | 23.8 [15.0, 34.1] | 0.1 [0.0, 0.3] | 2.8 [0.5, 5.9] | -2.1 [-5.0, 0.0] | -0.1 [-0.2, -0.0] | 0.00 [0.00, 0.00] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/8 | 23.8 [14.9, 34.1] | 0.7 [0.0, 1.6] | 2.2 [0.4, 4.6] | -0.2 [-0.4, 0.0] | -0.0 [-0.1, 0.1] | 0.00 [0.00, 0.01] | no |  |
| Platt-calibrated cost-optimal ask c=0.1 w_spur=1/36 | 23.8 [14.9, 34.1] | 2.3 [0.0, 5.5] | 0.5 [0.1, 1.0] | -0.0 [-0.1, 0.0] | 0.0 [-0.0, 0.1] | 0.00 [0.00, 0.01] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.03 w_spur=1/1 | 18.0 [10.9, 26.7] | 0.0 [0.0, 0.0] | 312.2 [300.1, 324.3] | 1.2 [-2.5, 4.4] | -2.3 [-4.3, -0.7] | 0.25 [0.20, 0.30] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/1 | 23.6 [14.8, 33.9] | 0.3 [0.0, 0.8] | 6.2 [2.1, 11.0] | -2.1 [-5.1, 0.0] | 0.1 [-0.3, 0.6] | 0.01 [0.00, 0.04] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/8 | 23.6 [14.8, 33.9] | 2.3 [0.0, 5.5] | 3.6 [0.8, 7.2] | -0.1 [-0.7, 0.2] | 0.1 [-0.2, 0.7] | 0.01 [0.00, 0.04] | no |  |
| contextual-calibration (Zhao 2021) cost-optimal ask c=0.1 w_spur=1/36 | 23.6 [14.8, 33.9] | 2.3 [0.0, 5.5] | 3.8 [0.8, 7.6] | -0.1 [-0.6, 0.2] | 0.1 [-0.2, 0.7] | 0.01 [0.00, 0.04] | no |  |

## T5. Reliability (HT-weighted ECE and Brier, no-cue units; constant base-rate Brier for reference)
| model | set | ECE [95%] | Brier [95%] | Brier of a constant base-rate predictor |
|---|---|---|---|---|
| qwen2.5-7b | human | 0.0289 [0.0191, 0.0407] | 0.0277 [0.0179, 0.0393] | 0.0256 |
| qwen2.5-7b | cap4 | 0.1035 [0.0804, 0.1282] | 0.1035 [0.0804, 0.1277] | 0.0961 |
| llama3.1-8b | human | 0.0307 [0.0210, 0.0423] | 0.0306 [0.0210, 0.0418] | 0.0256 |
| llama3.1-8b | cap4 | 0.0991 [0.0776, 0.1247] | 0.1040 [0.0819, 0.1279] | 0.0961 |

## T7. Detector validity (machine reference: judge J1+J2 + blind arbiter; NOT human truth)
| set | PPV (ref negated | detector negated) [Wilson] | NPV (ref not negated | detector not negated) [Wilson] | ref unclear/mixed among drawn | detector-negated share of domain (HT) | derived sensitivity | derived specificity |
|---|---|---|---|---|---|---|
| model:llama3.1-8b | 73/100 = 0.730 [0.636, 0.807] | 300/300 = 1.000 [0.987, 1.000] | 27 | 0.02 | 1.00 | 1.00 |
| model:qwen2.5-7b | 29/34 = 0.853 [0.699, 0.936] | 300/300 = 1.000 [0.987, 1.000] | 4 | 0.00 | 1.00 | 1.00 |
| source | 37/50 = 0.740 [0.604, 0.841] | 50/50 = 1.000 [0.929, 1.000] | 12 | 0.10 | 1.00 | 0.97 |

## T8. Pair scoring (PROVISIONAL, noise-limited), hw1 + W-C polarity pairs
| model | scorer | pairs | median log-odds aff over neg (nats) | share aff preferred | placebo |logodds| p95 | share of pairs beyond placebo p95 |
|---|---|---|---|---|---|---|
| qwen2.5-7b | full_sum | 164 | 16.86 | 0.94 | 11.03 | 0.70 |
| qwen2.5-7b | len_norm | 164 | 0.85 | 0.68 | 1.49 | 0.37 |
| qwen2.5-7b | span_sum | 164 | 17.10 | 0.98 | 9.45 | 0.80 |
| qwen2.5-7b | span_mean | 164 | 5.18 | 0.72 | 6.38 | 0.53 |
| llama3.1-8b | full_sum | 164 | 5.15 | 0.91 | 3.79 | 0.63 |
| llama3.1-8b | len_norm | 164 | 0.01 | 0.51 | 0.68 | 0.29 |
| llama3.1-8b | span_sum | 164 | 7.04 | 0.97 | 3.42 | 0.86 |
| llama3.1-8b | span_mean | 164 | 1.68 | 0.68 | 2.07 | 0.59 |

| model | scorer | pairs | clean pairs (no imputed token) | imputed in aff-only/neg-only/both | median all | median clean | share aff pref. all | clean | conservative bound | optimistic bound |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-7b | full_sum | 164 | 115 | 13/10/26 | 16.86 | 16.28 | 0.94 | 0.94 | 0.87 | 0.95 |
| qwen2.5-7b | len_norm | 164 | 115 | 13/10/26 | 0.85 | 0.71 | 0.68 | 0.66 | 0.62 | 0.70 |
| qwen2.5-7b | span_sum | 164 | 115 | 13/10/26 | 17.10 | 16.82 | 0.98 | 0.98 | 0.90 | 0.98 |
| qwen2.5-7b | span_mean | 164 | 115 | 13/10/26 | 5.18 | 6.38 | 0.72 | 0.71 | 0.66 | 0.74 |
| llama3.1-8b | full_sum | 164 | 156 | 3/2/3 | 5.15 | 5.19 | 0.91 | 0.91 | 0.89 | 0.91 |
| llama3.1-8b | len_norm | 164 | 156 | 3/2/3 | 0.01 | 0.02 | 0.51 | 0.52 | 0.51 | 0.52 |
| llama3.1-8b | span_sum | 164 | 156 | 3/2/3 | 7.04 | 7.11 | 0.97 | 0.97 | 0.95 | 0.98 |
| llama3.1-8b | span_mean | 164 | 156 | 3/2/3 | 1.68 | 1.83 | 0.68 | 0.69 | 0.66 | 0.68 |

## T6. Mechanics
- qwen2.5-7b: inputs 1733, missing requests 0, mean unique texts per 16 samples 2.88, finish=length 0, content-free 'Keywords: N/A' sampled negated share 0.0; G1 check on 2160 greedy outputs: {'politeness:added': 388}
- llama3.1-8b: inputs 1733, missing requests 0, mean unique texts per 16 samples 8.51, finish=length 1, content-free 'Keywords: N/A' sampled negated share 0.375; G1 check on 2160 greedy outputs: {'politeness:added': 431}