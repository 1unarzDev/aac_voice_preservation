## A. Non-ceiling polarity test, arm family ctxq (yes/no question context); models with data: ['gemma3-4b', 'mistral-nemo-12b', 'qwen2.5-7b', 'llama3.1-8b', 'qwen2.5-14b', 'gpt-6.1-terra']
| scope | lang | n bare (committed) | P(negated bare) % [CI] | diff vs EN pp [CI] | P(negated, [NOT]) % | P(affirmative, [YES]) % | bare reversals/1000 @pi=2.7% | @pi=50% | cued reversals/1000 @2.7% | @50% |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | en | 111 | 1.8 [0.0, 4.5] | - | 100.0 | 100.0 | 44 | 500 | 0.0 | 0.0 |
| pooled | de | 120 | 5.8 [1.7, 10.8] | 4.0 [-0.2, 8.9] | 100.0 | 100.0 | 82 | 500 | 0.0 | 0.0 |
| pooled | es | 114 | 18.4 [10.8, 26.3] | 16.6 [9.8, 23.6] | 100.0 | 100.0 | 201 | 500 | 0.0 | 0.0 |
| pooled | fr | 111 | 8.1 [3.6, 13.1] | 6.3 [2.7, 10.3] | 100.0 | 100.0 | 104 | 500 | 0.0 | 0.0 |
| gemma3-4b | en | 20 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gemma3-4b | de | 20 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gemma3-4b | es | 19 | 5.3 [0.0, 16.7] | 5.3 [0.0, 16.7] | 100.0 | 100.0 | 77 | 500 | 0.0 | 0.0 |
| gemma3-4b | fr | 18 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| mistral-nemo-12b | en | 20 | 5.0 [0.0, 15.0] | - | 100.0 | 100.0 | 74 | 500 | 0.0 | 0.0 |
| mistral-nemo-12b | de | 20 | 20.0 [5.0, 40.0] | 15.0 [0.0, 30.0] | 100.0 | 100.0 | 216 | 500 | 0.0 | 0.0 |
| mistral-nemo-12b | es | 19 | 31.6 [10.5, 52.6] | 26.6 [6.8, 47.4] | 100.0 | 100.0 | 326 | 500 | 0.0 | 0.0 |
| mistral-nemo-12b | fr | 20 | 30.0 [10.0, 50.0] | 25.0 [0.0, 50.0] | 100.0 | 100.0 | 311 | 500 | 0.0 | 0.0 |
| qwen2.5-7b | en | 18 | 5.6 [0.0, 17.6] | - | 100.0 | 100.0 | 80 | 500 | 0.0 | 0.0 |
| qwen2.5-7b | de | 20 | 10.0 [0.0, 25.0] | 4.4 [-12.5, 20.0] | 100.0 | 100.0 | 122 | 500 | 0.0 | 0.0 |
| qwen2.5-7b | es | 19 | 0.0 [0.0, 0.0] | -5.6 [-17.6, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| qwen2.5-7b | fr | 17 | 0.0 [0.0, 0.0] | -5.6 [-17.6, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| llama3.1-8b | en | 20 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| llama3.1-8b | de | 20 | 5.0 [0.0, 15.0] | 5.0 [0.0, 15.0] | 100.0 | 100.0 | 74 | 500 | 0.0 | 0.0 |
| llama3.1-8b | es | 19 | 57.9 [35.0, 80.0] | 57.9 [35.0, 80.0] | 100.0 | 100.0 | 575 | 500 | 0.0 | 0.0 |
| llama3.1-8b | fr | 20 | 15.0 [0.0, 30.0] | 15.0 [0.0, 30.0] | 100.0 | 100.0 | 169 | 500 | 0.0 | 0.0 |
| qwen2.5-14b | en | 18 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| qwen2.5-14b | de | 20 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| qwen2.5-14b | es | 19 | 15.8 [0.0, 33.3] | 15.8 [0.0, 33.3] | 100.0 | 100.0 | 176 | 500 | 0.0 | 0.0 |
| qwen2.5-14b | fr | 17 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | en | 15 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | de | 20 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | es | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | fr | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |

## A. Non-ceiling polarity test, arm family ctxn (question context + refusal prior); models with data: ['gemma3-4b', 'mistral-nemo-12b', 'qwen2.5-7b', 'llama3.1-8b', 'qwen2.5-14b', 'gpt-6.1-terra']
| scope | lang | n bare (committed) | P(negated bare) % [CI] | diff vs EN pp [CI] | P(negated, [NOT]) % | P(affirmative, [YES]) % | bare reversals/1000 @pi=2.7% | @pi=50% | cued reversals/1000 @2.7% | @50% |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | en | 118 | 100.0 [100.0, 100.0] | - | n/a | 20.0 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | de | 114 | 98.2 [95.6, 100.0] | -1.8 [-4.4, 0.0] | n/a | 13.8 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | es | 114 | 99.1 [97.2, 100.0] | -0.9 [-2.8, 0.0] | n/a | 9.8 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | fr | 98 | 98.0 [93.7, 100.0] | -2.0 [-6.3, 0.0] | n/a | 9.6 (cue beats context) | n/a | n/a | n/a | n/a |
| gemma3-4b | en | 20 | 100.0 [100.0, 100.0] | - | n/a | 25.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gemma3-4b | de | 20 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gemma3-4b | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 5.3 (cue beats context) | n/a | n/a | n/a | n/a |
| gemma3-4b | fr | 20 | 95.0 [85.0, 100.0] | -5.0 [-15.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| mistral-nemo-12b | en | 20 | 100.0 [100.0, 100.0] | - | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| mistral-nemo-12b | de | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| mistral-nemo-12b | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| mistral-nemo-12b | fr | 18 | 94.4 [82.4, 100.0] | -5.6 [-17.6, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-7b | en | 18 | 100.0 [100.0, 100.0] | - | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-7b | de | 17 | 88.2 [70.6, 100.0] | -11.8 [-29.4, 0.0] | n/a | 15.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-7b | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-7b | fr | 14 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 5.3 (cue beats context) | n/a | n/a | n/a | n/a |
| llama3.1-8b | en | 20 | 100.0 [100.0, 100.0] | - | n/a | 10.0 (cue beats context) | n/a | n/a | n/a | n/a |
| llama3.1-8b | de | 20 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 10.5 (cue beats context) | n/a | n/a | n/a | n/a |
| llama3.1-8b | es | 19 | 94.7 [83.3, 100.0] | -5.3 [-16.7, 0.0] | n/a | 5.3 (cue beats context) | n/a | n/a | n/a | n/a |
| llama3.1-8b | fr | 11 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 0.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-14b | en | 20 | 100.0 [100.0, 100.0] | - | n/a | 10.0 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-14b | de | 18 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 23.5 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-14b | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 15.8 (cue beats context) | n/a | n/a | n/a | n/a |
| qwen2.5-14b | fr | 17 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 20.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | en | 20 | 100.0 [100.0, 100.0] | - | n/a | 75.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | de | 20 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 42.9 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 35.3 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | fr | 18 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 27.8 (cue beats context) | n/a | n/a | n/a | n/a |


## B. Polarity, fair-cost comparison (B messages; reversal = output not negated; pi_neg = 2.7%; per 1,000 messages)
Chip every message = 1 tap on all messages; chip cued-only = 1 tap on the pi_neg share; plain word 'not' = 1 tap (single core word) or 3 keystroke-equivalents, on cued messages only or on all messages (round-2 convention).
| lang | policy | taps/1000 | silent reversals/1000 [CI] | SLP-weighted/1000 |
|---|---|---|---|---|
| en | always-commit (bare) | 0 | 27.0 [27.0, 27.0] | 27.0 |
| en | chip, every message | 1000 | 0.9 [0.2, 1.8] | 0.9 |
| en | chip, cued messages only | 27 | 0.9 [0.2, 1.8] | 0.9 |
| en | plain word 'not', 1 tap, cued only | 27 | 1.8 [0.9, 2.7] | 1.8 |
| en | plain word 'not', 3 keystrokes, cued only | 81 | 1.8 [0.9, 2.7] | 1.8 |
| en | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 1.8 [0.9, 2.7] | 1.8 |
| en | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 3.3 [-0.0, 6.7] | indistinguishable |
| de | always-commit (bare) | 0 | 26.8 [26.3, 27.0] | 26.8 |
| de | chip, every message | 1000 | 0.2 [0.0, 0.7] | 0.2 |
| de | chip, cued messages only | 27 | 0.2 [0.0, 0.7] | 0.2 |
| de | plain word 'not', 1 tap, cued only | 27 | 1.4 [0.5, 2.3] | 1.4 |
| de | plain word 'not', 3 keystrokes, cued only | 81 | 1.4 [0.5, 2.3] | 1.4 |
| de | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 1.4 [0.5, 2.3] | 1.4 |
| de | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 4.2 [-0.0, 8.3] | indistinguishable |
| es | always-commit (bare) | 0 | 26.8 [26.2, 27.0] | 26.8 |
| es | chip, every message | 1000 | 0.2 [0.0, 0.8] | 0.2 |
| es | chip, cued messages only | 27 | 0.2 [0.0, 0.8] | 0.2 |
| es | plain word 'not', 1 tap, cued only | 27 | 0.9 [0.0, 2.1] | 0.9 |
| es | plain word 'not', 3 keystrokes, cued only | 81 | 0.9 [0.0, 2.1] | 0.9 |
| es | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 0.9 [0.0, 2.1] | 0.9 |
| es | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 2.6 [-0.0, 5.8] | indistinguishable |
| fr | always-commit (bare) | 0 | 26.8 [26.3, 27.0] | 26.8 |
| fr | chip, every message | 1000 | 0.2 [0.0, 0.7] | 0.2 |
| fr | chip, cued messages only | 27 | 0.2 [0.0, 0.7] | 0.2 |
| fr | plain word 'not', 1 tap, cued only | 27 | 1.4 [0.5, 2.3] | 1.4 |
| fr | plain word 'not', 3 keystrokes, cued only | 81 | 1.4 [0.5, 2.3] | 1.4 |
| fr | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 1.4 [0.5, 2.3] | 1.4 |
| fr | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 4.3 [1.7, 7.6] | chip differs |

## C. Register policies = MECHANISM ILLUSTRATION (pi_V assumed, chip treated as ground truth for the requested register, borrowed 0.5 SLP weight)
Mismatch per 1,000 messages; 'harmless' = no-address output not counted (declared, flatters bare and ask-if-address); 'cost' = no-address output counted as a failure to realise the register. taps/1000 per message when every message is cued.
| lang | policy | taps/1000 | mismatch/1000 harmless pi_V=.5 | mismatch/1000 no-address=cost pi_V=.5 | no-address=cost, pi_V=.1 | pi_V=.9 |
|---|---|---|---|---|---|---|
| de | commit | 0 | 225 [158, 292] | 775 [708, 842] | 722 | 828 |
| de | chip | 1000 | 4 [0, 12] | 208 [146, 288] | 268 | 148 |
| de | plain_x | 1000 | 42 [21, 62] | 354 [271, 446] | 391 | 318 |
| de | plain_x_leakfilter | 1233 | 262 [183, 342] | 442 [362, 529] | 455 | 428 |
| de | ctx_x | 1000 | 17 [4, 33] | 492 [379, 612] | 438 | 545 |
| de | ask_if_address | 450 | 4 [0, 12] | 575 [450, 704] | 588 | 562 |
| es (expl.) | commit | 0 | 125 [88, 158] | 875 [842, 912] | 788 | 962 |
| es (expl.) | chip | 1000 | 17 [4, 33] | 304 [208, 404] | 301 | 308 |
| es (expl.) | plain_x | 1000 | 12 [0, 25] | 446 [362, 533] | 409 | 482 |
| es (expl.) | plain_x_leakfilter | 1312 | 321 [229, 429] | 546 [442, 658] | 496 | 596 |
| es (expl.) | ctx_x | 1000 | 83 [54, 117] | 671 [617, 725] | 594 | 748 |
| es (expl.) | ask_if_address | 250 | 0 [0, 0] | 762 [696, 833] | 759 | 766 |
| fr | commit | 0 | 167 [108, 225] | 833 [775, 892] | 860 | 807 |
| fr | chip | 1000 | 46 [25, 67] | 229 [167, 300] | 299 | 159 |
| fr | plain_x | 1000 | 108 [75, 142] | 496 [417, 571] | 586 | 406 |
| fr | plain_x_leakfilter | 1250 | 325 [242, 412] | 554 [462, 642] | 618 | 491 |
| fr | ctx_x | 1000 | 75 [46, 104] | 554 [462, 642] | 578 | 531 |
| fr | ask_if_address | 333 | 38 [17, 58] | 712 [612, 817] | 749 | 676 |

Break-even tap cost c* (mismatches avoided per tap vs always-commit; the policy pays off only if one tap is cheaper than c* mismatches), pi_V = .5, no-address counted as cost:
| lang | chip | ask-if-address | plain word (1 tap) |
|---|---|---|---|
| de | 0.57 [0.50, 0.63] | 0.44 [0.40, 0.48] | 0.42 [0.36, 0.48] |
| es | 0.57 [0.49, 0.65] | 0.45 [0.40, 0.50] | 0.43 [0.37, 0.49] |
| fr | 0.60 [0.55, 0.65] | 0.36 [0.30, 0.42] | 0.34 [0.28, 0.40] |

### C2. Equal-cost register comparison (every cue = 1 tap on cued messages; no-address = cost; pi_V = .5): chip vs plain word, legend-equalised; with the leak filter; and on the keyword-lexicon-filtered family subset
| lang | subset | n msgs | chip | plain | plain + output leak filter | chip - plain pp [CI] | chip - plain-leakfilter pp [CI] | plain outputs echoing the cue word % |
|---|---|---|---|---|---|---|---|---|
| de | all (20 fam.) | 120 | 20.8 | 35.4 | 44.2 | 14.6 [8.8, 20.8] | 23.3 [15.8, 30.8] | 23.3 |
| de | lexicon-filtered keywords (20 fam.) | 120 | 20.8 | 35.4 | 44.2 | 14.6 [8.8, 20.8] | 23.3 [15.8, 30.8] | 23.3 |
| es | all (20 fam.) | 120 | 30.4 | 44.6 | 54.6 | 14.2 [6.7, 22.1] | 24.2 [15.0, 34.2] | 31.2 |
| es | lexicon-filtered keywords (20 fam.) | 120 | 30.4 | 44.6 | 54.6 | 14.2 [6.7, 22.1] | 24.2 [15.0, 34.2] | 31.2 |
| fr | all (20 fam.) | 120 | 22.9 | 49.6 | 55.4 | 26.7 [17.5, 35.8] | 32.5 [21.7, 42.9] | 25.0 |
| fr | lexicon-filtered keywords (20 fam.) | 120 | 22.9 | 49.6 | 55.4 | 26.7 [17.5, 35.8] | 32.5 [21.7, 42.9] | 25.0 |
(values are failure rates: share of outputs not in the requested register; positive 'chip - plain' columns here are plain minus chip, i.e. positive = chip better)

## D. E6 keyword-condition controls on E8 meaning-check survivors only (sol and terra back-translation overlap >= 0.5 under both)
| lang | condition | survivors/total | V share pooled (n T/V) | same families, bare | address rate | per-model V (n) |
|---|---|---|---|---|---|---|
| de | bare_nom | 18/20 | 57.1 [25.0, 85.7] (n=14) | 34.0 (n=47) | 13.0 | gemma3-4b: 75.0 (n=4); mistral-nemo-12b: 100.0 (n=1); qwen2.5-7b: 66.7 (n=3); llama3.1-8b: 100.0 (n=2); qwen2.5-14b: - (n=0); gpt-6.1-terra: 0.0 (n=4) |
| es | bare_nom | 17/20 | 6.2 [0.0, 20.0] (n=16) | 8.7 (n=23) | 15.7 | gemma3-4b: 0.0 (n=5); mistral-nemo-12b: 0.0 (n=3); qwen2.5-7b: 50.0 (n=2); llama3.1-8b: 0.0 (n=3); qwen2.5-14b: 0.0 (n=1); gpt-6.1-terra: 0.0 (n=2) |
| fr | bare_nom | 15/20 | 77.3 [62.5, 94.4] (n=22) | 58.3 (n=24) | 24.4 | gemma3-4b: 75.0 (n=8); mistral-nemo-12b: 100.0 (n=1); qwen2.5-7b: 60.0 (n=5); llama3.1-8b: 100.0 (n=4); qwen2.5-14b: 100.0 (n=1); gpt-6.1-terra: 66.7 (n=3) |
| de | bare_sep | 16/16 | 25.5 [13.8, 38.5] (n=51) | 34.7 (n=49) | 53.1 | gemma3-4b: 44.4 (n=9); mistral-nemo-12b: 16.7 (n=12); qwen2.5-7b: 14.3 (n=7); llama3.1-8b: 66.7 (n=6); qwen2.5-14b: 0.0 (n=5); gpt-6.1-terra: 16.7 (n=12) |
| de | bare_kw2 | 20/20 | 36.4 [21.6, 54.2] (n=33) | 35.2 (n=54) | 27.5 | gemma3-4b: 42.9 (n=7); mistral-nemo-12b: 37.5 (n=8); qwen2.5-7b: 75.0 (n=8); llama3.1-8b: - (n=0); qwen2.5-14b: 0.0 (n=1); gpt-6.1-terra: 0.0 (n=9) |
| es | bare_kw2 | 20/20 | 7.4 [0.0, 20.8] (n=27) | 6.7 (n=30) | 22.5 | gemma3-4b: 0.0 (n=3); mistral-nemo-12b: 0.0 (n=12); qwen2.5-7b: - (n=0); llama3.1-8b: 66.7 (n=3); qwen2.5-14b: - (n=0); gpt-6.1-terra: 0.0 (n=9) |
| fr | bare_kw2 | 19/19 | 62.5 [51.4, 75.0] (n=40) | 60.0 (n=40) | 35.1 | gemma3-4b: 91.7 (n=12); mistral-nemo-12b: 77.8 (n=9); qwen2.5-7b: 75.0 (n=4); llama3.1-8b: 100.0 (n=2); qwen2.5-14b: 33.3 (n=3); gpt-6.1-terra: 10.0 (n=10) |

## E. Inference bookkeeping
Holm family actually used (ES contrasts excluded because the ES detector failed the 95% gate, 94.2%): DE-FR for each model with data = 6 tests (gemma3-4b|de-fr, mistral-nemo-12b|de-fr, qwen2.5-7b|de-fr, llama3.1-8b|de-fr, qwen2.5-14b|de-fr, gpt-6.1-terra|de-fr). The declared family would have been up to 18 tests (3 contrasts x 6 models); it was not reached.
| test | est pp [CI] | n DE | n FR | Holm p | language effect confirmed (Holm<.05 and |d|>=30pp) |
|---|---|---|---|---|---|
| gemma3-4b|de-fr | -41.7 [-75.0, -5.0] | 10 | 12 | 0.182 | False |
| mistral-nemo-12b|de-fr | -32.3 [-66.7, 0.0] | 11 | 9 | 0.283 | False |
| qwen2.5-7b|de-fr | -29.5 [-75.0, 33.3] | 11 | 4 | 1.000 | False |
| llama3.1-8b|de-fr | -50.0 [-100.0, 0.0] | 4 | 1 | 1.000 | False |
| qwen2.5-14b|de-fr | -25.0 [-100.0, 50.0] | 4 | 2 | 1.000 | False |
| gpt-6.1-terra|de-fr | -1.2 [-23.3, 18.8] | 14 | 12 | 1.000 | False |
| V-share cells (bare, per model; n = outputs with a T or V form) | DE | FR | ES (exploratory, excluded from headline) |
|---|---|---|---|
| gemma3-4b | 50.0% (5/10), CP [18.7, 81.3] | 91.7% (11/12), CP [61.5, 99.8] | 0.0% (0/1), CP [0.0, 97.5] |
| mistral-nemo-12b | 45.5% (5/11), CP [16.7, 76.6] | 77.8% (7/9), CP [40.0, 97.2] | 0.0% (0/12), CP [0.0, 26.5] |
| qwen2.5-7b | 45.5% (5/11), CP [16.7, 76.6] | 75.0% (3/4), CP [19.4, 99.4] | n/a% (0/0), CP [n/a, n/a] |
| llama3.1-8b | 50.0% (2/4), CP [6.8, 93.2] | 100.0% (1/1), CP [2.5, 100.0] | 100.0% (2/2), CP [15.8, 100.0] |
| qwen2.5-14b | 25.0% (1/4), CP [0.6, 80.6] | 50.0% (1/2), CP [1.3, 98.7] | 0.0% (0/2), CP [0.0, 84.2] |
| gpt-6.1-terra | 7.1% (1/14), CP [0.2, 33.9] | 8.3% (1/12), CP [0.2, 38.5] | 0.0% (0/13), CP [0.0, 24.7] |

E1 single register given an address form, with n and Clopper-Pearson 95% interval:
- de: 54/54 single-register, CP [93.4, 100.0]; no address form in 55.0% of 120 outputs
- es: 30/30 single-register, CP [88.4, 100.0]; no address form in 75.0% of 120 outputs
- fr: 40/40 single-register, CP [91.2, 100.0]; no address form in 66.7% of 120 outputs

E3b declared rule (pronoun-address share vs English 'you', pooled; |d| >= 15 pp and CI excluding 0) and the post-hoc clean pronoun-only sensitivity:
- de: declared 16.7 [6.7, 27.5] pp, meets declared rule = True; clean pronoun-only (post-hoc) 16.7 [6.7, 27.5] pp
- es: declared 8.3 [1.7, 15.0] pp, meets declared rule = False; clean pronoun-only (post-hoc) -3.3 [-6.7, -0.8] pp
- fr: declared 12.5 [4.2, 20.8] pp, meets declared rule = False; clean pronoun-only (post-hoc) 12.5 [4.2, 20.8] pp

## F. Six-model criteria (6 of 6 models have data: ['gemma3-4b', 'mistral-nemo-12b', 'qwen2.5-7b', 'llama3.1-8b', 'qwen2.5-14b', 'gpt-6.1-terra'])
- H4 (E4 lower bound >= 50 pp) models meeting per language: {'en': 6, 'de': 6, 'es': 6, 'fr': 6}; replicates in >=5/6 in every language incl. English: True
- E2 model-range criterion (>=30 pp, CI excluding 0, in DE or FR): True
- R2.9 stop rule applied literally: stop iff H4 and H2 criteria hold = True; promote trigger (E3/E3b language effect) = True (the E3b trigger rests on the unstable pronoun measure)
- Model-range of V share (bare, within language): de: 42.9 pp CI [40.9, 100.0]; es: 100.0 pp CI [0.0, 100.0]; fr: 91.7 pp CI [71.4, 100.0]
