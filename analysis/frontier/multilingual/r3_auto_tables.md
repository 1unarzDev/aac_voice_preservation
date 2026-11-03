## A. Non-ceiling polarity test, arm family ctxq (yes/no question context); models with data: ['gpt-6.1-terra']
| scope | lang | n bare (committed) | P(negated bare) % [CI] | diff vs EN pp [CI] | P(negated, [NOT]) % | P(affirmative, [YES]) % | bare reversals/1000 @pi=2.7% | @pi=50% | cued reversals/1000 @2.7% | @50% |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | en | 20 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| pooled | de | 20 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| pooled | es | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| pooled | fr | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | en | 20 | 0.0 [0.0, 0.0] | - | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | de | 20 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | es | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |
| gpt-6.1-terra | fr | 19 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 100.0 | 100.0 | 27 | 500 | 0.0 | 0.0 |

## A. Non-ceiling polarity test, arm family ctxn (question context + refusal prior); models with data: ['gpt-6.1-terra']
| scope | lang | n bare (committed) | P(negated bare) % [CI] | diff vs EN pp [CI] | P(negated, [NOT]) % | P(affirmative, [YES]) % | bare reversals/1000 @pi=2.7% | @pi=50% | cued reversals/1000 @2.7% | @50% |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | en | 19 | 100.0 [100.0, 100.0] | - | n/a | 80.0 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | de | 20 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 43.8 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 35.3 (cue beats context) | n/a | n/a | n/a | n/a |
| pooled | fr | 18 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 40.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | en | 19 | 100.0 [100.0, 100.0] | - | n/a | 80.0 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | de | 20 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 43.8 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | es | 19 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 35.3 (cue beats context) | n/a | n/a | n/a | n/a |
| gpt-6.1-terra | fr | 18 | 100.0 [100.0, 100.0] | 0.0 [0.0, 0.0] | n/a | 40.0 (cue beats context) | n/a | n/a | n/a | n/a |


## B. Polarity, fair-cost comparison (B messages; reversal = output not negated; pi_neg = 2.7%; per 1,000 messages)
Chip every message = 1 tap on all messages; chip cued-only = 1 tap on the pi_neg share; plain word 'not' = 1 tap (single core word) or 3 keystroke-equivalents, on cued messages only or on all messages (round-2 convention).
| lang | policy | taps/1000 | silent reversals/1000 [CI] | SLP-weighted/1000 |
|---|---|---|---|---|
| en | always-commit (bare) | 0 | 27.0 [27.0, 27.0] | 27.0 |
| en | chip, every message | 1000 | 1.4 [0.0, 3.4] | 1.4 |
| en | chip, cued messages only | 27 | 1.4 [0.0, 3.4] | 1.4 |
| en | plain word 'not', 1 tap, cued only | 27 | 2.0 [0.0, 4.1] | 2.0 |
| en | plain word 'not', 3 keystrokes, cued only | 81 | 2.0 [0.0, 4.1] | 2.0 |
| en | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 2.0 [0.0, 4.1] | 2.0 |
| en | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 2.5 [-5.0, 10.0] | indistinguishable |
| de | always-commit (bare) | 0 | 27.0 [27.0, 27.0] | 27.0 |
| de | chip, every message | 1000 | 0.0 [0.0, 0.0] | 0.0 |
| de | chip, cued messages only | 27 | 0.0 [0.0, 0.0] | 0.0 |
| de | plain word 'not', 1 tap, cued only | 27 | 0.7 [0.0, 2.0] | 0.7 |
| de | plain word 'not', 3 keystrokes, cued only | 81 | 0.7 [0.0, 2.0] | 0.7 |
| de | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 0.7 [0.0, 2.0] | 0.7 |
| de | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 2.5 [-0.0, 7.5] | indistinguishable |
| es | always-commit (bare) | 0 | 27.0 [27.0, 27.0] | 27.0 |
| es | chip, every message | 1000 | 0.0 [0.0, 0.0] | 0.0 |
| es | chip, cued messages only | 27 | 0.0 [0.0, 0.0] | 0.0 |
| es | plain word 'not', 1 tap, cued only | 27 | 2.1 [0.0, 4.7] | 2.1 |
| es | plain word 'not', 3 keystrokes, cued only | 81 | 2.1 [0.0, 4.7] | 2.1 |
| es | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 2.1 [0.0, 4.7] | 2.1 |
| es | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 7.9 [-0.0, 17.5] | indistinguishable |
| fr | always-commit (bare) | 0 | 26.3 [25.0, 27.0] | 26.3 |
| fr | chip, every message | 1000 | 0.0 [0.0, 0.0] | 0.0 |
| fr | chip, cued messages only | 27 | 0.0 [0.0, 0.0] | 0.0 |
| fr | plain word 'not', 1 tap, cued only | 27 | 0.7 [0.0, 2.0] | 0.7 |
| fr | plain word 'not', 3 keystrokes, cued only | 81 | 0.7 [0.0, 2.0] | 0.7 |
| fr | plain word 'not', 3 keystrokes, every message (r2 convention) | 3000 | 0.7 [0.0, 2.0] | 0.7 |
| fr | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | 2.5 [-0.0, 7.5] | indistinguishable |

## C. Register policies = MECHANISM ILLUSTRATION (pi_V assumed, chip treated as ground truth for the requested register, borrowed 0.5 SLP weight)
Mismatch per 1,000 messages; 'harmless' = no-address output not counted (declared, flatters bare and ask-if-address); 'cost' = no-address output counted as a failure to realise the register. taps/1000 per message when every message is cued.
| lang | policy | taps/1000 | mismatch/1000 harmless pi_V=.5 | mismatch/1000 no-address=cost pi_V=.5 | no-address=cost, pi_V=.1 | pi_V=.9 |
|---|---|---|---|---|---|---|
| de | commit | 0 | 312 [212, 400] | 688 [600, 788] | 558 | 818 |
| de | chip | 1000 | 0 [0, 0] | 88 [0, 212] | 98 | 78 |
| de | plain_x | 1000 | 25 [0, 62] | 162 [62, 288] | 152 | 173 |
| de | plain_x_leakfilter | 1075 | 100 [38, 162] | 188 [88, 312] | 157 | 217 |
| de | ctx_x | 1000 | 0 [0, 0] | 375 [212, 550] | 335 | 415 |
| de | ask_if_address | 625 | 0 [0, 0] | 375 [200, 575] | 375 | 375 |
| es (expl.) | commit | 0 | 312 [225, 400] | 688 [600, 775] | 438 | 938 |
| es (expl.) | chip | 1000 | 0 [0, 0] | 100 [38, 162] | 120 | 80 |
| es (expl.) | plain_x | 1000 | 12 [0, 38] | 275 [138, 425] | 195 | 355 |
| es (expl.) | plain_x_leakfilter | 1150 | 162 [62, 288] | 312 [162, 475] | 242 | 382 |
| es (expl.) | ctx_x | 1000 | 138 [88, 188] | 488 [375, 612] | 337 | 638 |
| es (expl.) | ask_if_address | 625 | 0 [0, 0] | 388 [212, 575] | 378 | 398 |
| fr | commit | 0 | 262 [162, 362] | 738 [638, 838] | 688 | 788 |
| fr | chip | 1000 | 62 [12, 112] | 175 [100, 262] | 255 | 95 |
| fr | plain_x | 1000 | 125 [75, 175] | 312 [212, 412] | 363 | 262 |
| fr | plain_x_leakfilter | 1125 | 238 [162, 312] | 350 [238, 475] | 370 | 330 |
| fr | ctx_x | 1000 | 62 [25, 112] | 462 [325, 600] | 472 | 452 |
| fr | ask_if_address | 525 | 38 [0, 75] | 512 [325, 700] | 543 | 482 |

Break-even tap cost c* (mismatches avoided per tap vs always-commit; the policy pays off only if one tap is cheaper than c* mismatches), pi_V = .5, no-address counted as cost:
| lang | chip | ask-if-address | plain word (1 tap) |
|---|---|---|---|
| de | 0.60 [0.50, 0.70] | 0.50 [0.50, 0.50] | 0.53 [0.41, 0.62] |
| es | 0.59 [0.53, 0.66] | 0.48 [0.43, 0.50] | 0.41 [0.33, 0.50] |
| fr | 0.56 [0.46, 0.66] | 0.43 [0.36, 0.50] | 0.42 [0.33, 0.54] |

### C2. Equal-cost register comparison (every cue = 1 tap on cued messages; no-address = cost; pi_V = .5): chip vs plain word, legend-equalised; with the leak filter; and on the keyword-lexicon-filtered family subset
| lang | subset | n msgs | chip | plain | plain + output leak filter | chip - plain pp [CI] | chip - plain-leakfilter pp [CI] | plain outputs echoing the cue word % |
|---|---|---|---|---|---|---|---|---|
| de | all (20 fam.) | 40 | 8.8 | 16.2 | 18.8 | 7.5 [-2.5, 17.5] | 10.0 [0.0, 20.0] | 7.5 |
| de | lexicon-filtered keywords (20 fam.) | 40 | 8.8 | 16.2 | 18.8 | 7.5 [-2.5, 17.5] | 10.0 [0.0, 20.0] | 7.5 |
| es | all (20 fam.) | 40 | 10.0 | 27.5 | 31.2 | 17.5 [7.5, 28.7] | 21.2 [10.0, 33.8] | 15.0 |
| es | lexicon-filtered keywords (20 fam.) | 40 | 10.0 | 27.5 | 31.2 | 17.5 [7.5, 28.7] | 21.2 [10.0, 33.8] | 15.0 |
| fr | all (20 fam.) | 40 | 17.5 | 31.2 | 35.0 | 13.8 [5.0, 22.5] | 17.5 [7.5, 28.7] | 12.5 |
| fr | lexicon-filtered keywords (20 fam.) | 40 | 17.5 | 31.2 | 35.0 | 13.8 [5.0, 22.5] | 17.5 [7.5, 28.7] | 12.5 |
(values are failure rates: share of outputs not in the requested register; positive 'chip - plain' columns here are plain minus chip, i.e. positive = chip better)

## D. E6 keyword-condition controls on E8 meaning-check survivors only (sol and terra back-translation overlap >= 0.5 under both)
| lang | condition | survivors/total | V share pooled (n T/V) | same families, bare | address rate | per-model V (n) |
|---|---|---|---|---|---|---|
| de | bare_nom | 18/20 | 20.0 [0.0, 66.7] (n=5) | 19.0 (n=21) | 13.9 | mistral-nemo-12b: 100.0 (n=1); gpt-6.1-terra: 0.0 (n=4) |
| es | bare_nom | 17/20 | 0.0 [0.0, 0.0] (n=5) | 0.0 (n=19) | 14.7 | mistral-nemo-12b: 0.0 (n=3); gpt-6.1-terra: 0.0 (n=2) |
| fr | bare_nom | 15/20 | 75.0 [0.0, 100.0] (n=4) | 41.7 (n=12) | 13.3 | mistral-nemo-12b: 100.0 (n=1); gpt-6.1-terra: 66.7 (n=3) |
| de | bare_sep | 16/16 | 16.7 [0.0, 36.4] (n=24) | 26.1 (n=23) | 75.0 | mistral-nemo-12b: 16.7 (n=12); gpt-6.1-terra: 16.7 (n=12) |
| de | bare_kw2 | 20/20 | 17.6 [0.0, 33.3] (n=17) | 24.0 (n=25) | 42.5 | mistral-nemo-12b: 37.5 (n=8); gpt-6.1-terra: 0.0 (n=9) |
| es | bare_kw2 | 20/20 | 0.0 [0.0, 0.0] (n=21) | 0.0 (n=25) | 52.5 | mistral-nemo-12b: 0.0 (n=12); gpt-6.1-terra: 0.0 (n=9) |
| fr | bare_kw2 | 19/19 | 42.1 [23.1, 61.1] (n=19) | 38.1 (n=21) | 50.0 | mistral-nemo-12b: 77.8 (n=9); gpt-6.1-terra: 10.0 (n=10) |

## E. Inference bookkeeping
Holm family actually used (ES contrasts excluded because the ES detector failed the 95% gate, 94.2%): DE-FR for each model with data = 2 tests (mistral-nemo-12b|de-fr, gpt-6.1-terra|de-fr). The declared family would have been up to 18 tests (3 contrasts x 6 models); it was not reached.
| test | est pp [CI] | n DE | n FR | Holm p | language effect confirmed (Holm<.05 and |d|>=30pp) |
|---|---|---|---|---|---|
| mistral-nemo-12b|de-fr | -32.3 [-66.7, 0.0] | 11 | 9 | 0.113 | False |
| gpt-6.1-terra|de-fr | -1.2 [-23.3, 18.8] | 14 | 12 | 1.000 | False |
| V-share cells (bare, per model; n = outputs with a T or V form) | DE | FR | ES (exploratory, excluded from headline) |
|---|---|---|---|
| mistral-nemo-12b | 45.5% (5/11), CP [16.7, 76.6] | 77.8% (7/9), CP [40.0, 97.2] | 0.0% (0/12), CP [0.0, 26.5] |
| gpt-6.1-terra | 7.1% (1/14), CP [0.2, 33.9] | 8.3% (1/12), CP [0.2, 38.5] | 0.0% (0/13), CP [0.0, 24.7] |

E1 single register given an address form, with n and Clopper-Pearson 95% interval:
- de: 25/25 single-register, CP [86.3, 100.0]; no address form in 37.5% of 40 outputs
- es: 25/25 single-register, CP [86.3, 100.0]; no address form in 37.5% of 40 outputs
- fr: 21/21 single-register, CP [83.9, 100.0]; no address form in 47.5% of 40 outputs

E3b declared rule (pronoun-address share vs English 'you', pooled; |d| >= 15 pp and CI excluding 0) and the post-hoc clean pronoun-only sensitivity:
- de: declared 15.0 [0.0, 30.0] pp, meets declared rule = False; clean pronoun-only (post-hoc) 15.0 [0.0, 30.0] pp
- es: declared 20.0 [2.5, 37.5] pp, meets declared rule = True; clean pronoun-only (post-hoc) -7.5 [-15.0, 0.0] pp
- fr: declared 17.5 [0.0, 35.0] pp, meets declared rule = False; clean pronoun-only (post-hoc) 17.5 [0.0, 35.0] pp

## F. Six-model criteria (2 of 6 models have data: ['mistral-nemo-12b', 'gpt-6.1-terra'])
- Fewer than 6 models: this is a 2-model pilot. No 6-model claim; E2 range, E4 5-of-6 and R2.9 stop rule are NOT evaluated. E4 per-model lower bound >= 50 pp: {'en': ['mistral-nemo-12b', 'gpt-6.1-terra'], 'de': ['mistral-nemo-12b', 'gpt-6.1-terra'], 'es': ['mistral-nemo-12b', 'gpt-6.1-terra'], 'fr': ['mistral-nemo-12b', 'gpt-6.1-terra']}
- Model-range of V share (bare, within language): de: 38.3 pp CI [4.3, 75.0]; es: 0.0 pp CI [0.0, 0.0]; fr: 69.4 pp CI [33.3, 100.0]
