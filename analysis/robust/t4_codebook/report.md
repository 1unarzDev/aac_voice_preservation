# T4: codebook sensitivity re-scoring (stored labels only; 0 generation / 0 judge calls)

Script `src/robust_t4_codebook.py`. Tables: `primary_contrasts_by_variant.csv`, `chip_gain_by_variant.csv` (all six dimensions for hw1, three for W-C), `elic1_by_variant.csv`. Estimators reproduce analysis/r2c and analysis/hw1 (cluster bootstrap, 10,000 resamples, seed 20261031; clusters: W-C `cluster_id`, hw1 `writer_id`).

Variants: (a) 'Can you / Could you ...?' coded question (a2: only without 'please'); (b) 'I want/need X, please' coded statement; (c) drop the arbitrated units of one precedent class at a time (tags assigned from the stored arbiter rationale, output text and dimension; D-016/D-055/D-057 and the W-C arbitration); (d) drop all arbitrated units. A remapped row keeps every other column; a masked row leaves the denominator.

Baseline reproduction (stored vs recomputed): {"W-C_P1_stored": [0.3141025641025641, 0.24996565934065937, 0.3794130777310924], "W-C_P1_here": [[0.3141025641025641, 0.24996565934065937, 0.3794130777310924]], "hw1_P1_stored": [0.35261194029850745, 0.3125, 0.4027829601990049], "hw1_P1_here": [[0.35261194029850745, 0.3125, 0.4027829601990049]], "W-C_P2_stored": [0.0625, 0.025, 0.1], "W-C_P2_here": [[0.0625, 0.025, 0.1]], "hw1_P2_stored": [0.07584269662921349, 0.05, 0.10393258426966293], "hw1_P2_here": [[0.07584269662921349, 0.05, 0.10393258426966293]]}

## W-C r2c1

Arbiter units: 177; tags: {"negation_scope_embedded_or_contrastive": 34, "please_ask_request": 33, "polite_softener(May I/would...if you could/would it be possible)": 33, "will_you_request_or_plans": 18, "indirect_or_info_question": 17, "performative_I_tell_you_to_X": 12, "should_we_let_us_offer": 12, "speech_act_other": 8, "fragment_unclear": 5, "cb9_Can_I_please_question": 5}

| variant | rows changed | P1 chip1-noncrit pp [CI] | P2 pp [CI] | P3 bare affirmative share % [CI] | Holm P1/P2/P3 | flags |
|---|---|---|---|---|---|---|
| base | 0 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| a_can_you_question | 3003 | +18.6 [+10.0, +26.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y | shift -12.8 pp |
| a2_can_you_no_please | 2447 | +21.3 [+13.2, +29.2] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y | shift -10.1 pp |
| b_want_please_statement | 68 | +31.6 [+25.2, +38.0] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| ab | 3071 | +18.8 [+10.2, +27.0] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y | shift -12.7 pp |
| mask_tag:cb9_Can_I_please_question | 7 | +31.6 [+25.2, +38.2] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:fragment_unclear | 13 | +31.3 [+24.8, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:indirect_or_info_question | 25 | +31.3 [+24.7, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:negation_scope_embedded_or_contrastive | 52 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:performative_I_tell_you_to_X | 17 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:please_ask_request | 63 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:polite_softener(May I/would...if you could/would it be possible) | 37 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:should_we_let_us_offer | 13 | +31.4 [+25.0, +37.9] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:speech_act_other | 11 | +31.6 [+25.2, +38.2] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_tag:will_you_request_or_plans | 21 | +31.5 [+25.0, +38.0] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |
| mask_all_arbitrated | 259 | +31.6 [+25.2, +38.2] | +6.2 [+2.5, +10.0] | 99.37 [98.42, 100.00] | Y/Y/Y |  |

### W-C r2c1: chip gain (chip1 - noncrit critical match), pp, by dimension; speech act = P1

| variant | polarity | politeness | speech_act |
|---|---|---|---|
| base | +49.4 | +39.5 | +31.4 |
| a_can_you_question | +49.4 | +39.5 | +18.6 |
| a2_can_you_no_please | +49.4 | +39.5 | +21.3 |
| b_want_please_statement | +49.4 | +39.5 | +31.6 |
| ab | +49.4 | +39.5 | +18.8 |
| mask_tag:cb9_Can_I_please_question | +49.4 | +39.5 | +31.6 |
| mask_tag:fragment_unclear | +49.4 | +39.5 | +31.3 |
| mask_tag:indirect_or_info_question | +49.4 | +39.5 | +31.3 |
| mask_tag:negation_scope_embedded_or_contrastive | +49.4 | +39.5 | +31.4 |
| mask_tag:performative_I_tell_you_to_X | +49.4 | +39.5 | +31.4 |
| mask_tag:please_ask_request | +49.4 | +39.5 | +31.4 |
| mask_tag:polite_softener(May I/would...if you could/would it be possible) | +49.4 | +39.6 | +31.4 |
| mask_tag:should_we_let_us_offer | +49.4 | +39.5 | +31.4 |
| mask_tag:speech_act_other | +49.4 | +39.5 | +31.6 |
| mask_tag:will_you_request_or_plans | +49.4 | +39.5 | +31.5 |
| mask_all_arbitrated | +49.4 | +39.6 | +31.6 |

## hw1

Arbiter units: 170; tags: {"time_no_time_word_unclear(~118)": 113, "certainty_sure_emphatic(D-057)": 11, "agent_other(CB-5/7)": 10, "time_will_now": 9, "certainty_request_question_unclear": 6, "time_vague_word_unclear(D-057 judgment call)": 5, "time_will_later": 4, "please_ask_request": 3, "performative_I_tell_you_to_X": 3, "fragment_unclear": 2, "certainty_hedge_other": 2, "negation_scope_embedded_or_contrastive": 1, "time_other": 1}

| variant | rows changed | P1 chip1-noncrit pp [CI] | P2 pp [CI] | P3 bare affirmative share % [CI] | Holm P1/P2/P3 | flags |
|---|---|---|---|---|---|---|
| base | 0 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| a_can_you_question | 124 | +32.5 [+25.8, +40.5] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| a2_can_you_no_please | 107 | +33.6 [+27.2, +41.2] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| b_want_please_statement | 3 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| ab | 127 | +32.5 [+25.8, +40.5] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:agent_other(CB-5/7) | 14 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:certainty_hedge_other | 2 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:certainty_request_question_unclear | 9 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:certainty_sure_emphatic(D-057) | 11 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:fragment_unclear | 2 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:negation_scope_embedded_or_contrastive | 1 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:performative_I_tell_you_to_X | 4 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:please_ask_request | 5 | +35.2 [+31.1, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:time_no_time_word_unclear(~118) | 272 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:time_other | 1 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:time_vague_word_unclear(D-057 judgment call) | 12 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:time_will_later | 7 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_tag:time_will_now | 14 | +35.3 [+31.2, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |
| mask_all_arbitrated | 354 | +35.2 [+31.1, +40.3] | +7.6 [+5.0, +10.4] | 99.76 [99.26, 100.00] | Y/Y/Y |  |

### hw1: chip gain (chip1 - noncrit critical match), pp, by dimension; speech act = P1

| variant | agent | certainty | polarity | politeness | speech_act | time_quantity |
|---|---|---|---|---|---|---|
| base | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| a_can_you_question | +67.3 | +54.0 | +49.5 | +38.2 | +32.5 | +82.7 |
| a2_can_you_no_please | +67.3 | +54.0 | +49.5 | +38.2 | +33.6 | +82.7 |
| b_want_please_statement | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| ab | +67.3 | +54.0 | +49.5 | +38.2 | +32.5 | +82.7 |
| mask_tag:agent_other(CB-5/7) | +67.1 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:certainty_hedge_other | +67.3 | +53.9 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:certainty_request_question_unclear | +67.3 | +54.1 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:certainty_sure_emphatic(D-057) | +67.3 | +54.3 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:fragment_unclear | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:negation_scope_embedded_or_contrastive | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:performative_I_tell_you_to_X | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:please_ask_request | +67.3 | +54.0 | +49.5 | +38.2 | +35.2 | +82.7 |
| mask_tag:time_no_time_word_unclear(~118) | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +80.3 |
| mask_tag:time_other | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_tag:time_vague_word_unclear(D-057 judgment call) | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.6 |
| mask_tag:time_will_later | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.8 |
| mask_tag:time_will_now | +67.3 | +54.0 | +49.5 | +38.2 | +35.3 | +82.7 |
| mask_all_arbitrated | +67.1 | +54.3 | +49.5 | +38.2 | +35.2 | +80.3 |

## elic1 (descriptive: share of P0 outputs whose focal critical label matches the source; no designed contrast exists)

Match rate by dimension and keyword source; a coding change that moves a request/question label moves these. Message-cluster bootstrap, 2,000 resamples.

| variant | rows_changed | dimension | keywords | match | ci_low | ci_high | n | families |
|---|---|---|---|---|---|---|---|---|
| base | 0 | speech_act | POS-cap4 | 0.214 | 0.173 | 0.258 | 724 | 181 |
| base | 0 | speech_act | human keywords | 0.517 | 0.466 | 0.567 | 2172 | 181 |
| base | 0 | speech_act[question] | all | 0.433 | NA | NA | 1648 | 103 |
| base | 0 | speech_act[request/command] | all | 0.454 | NA | NA | 1248 | 78 |
| a_can_you_question | 83 | speech_act | POS-cap4 | 0.203 | 0.164 | 0.244 | 724 | 181 |
| a_can_you_question | 83 | speech_act | human keywords | 0.511 | 0.461 | 0.559 | 2172 | 181 |
| a_can_you_question | 83 | speech_act[question] | all | 0.451 | NA | NA | 1648 | 103 |
| a_can_you_question | 83 | speech_act[request/command] | all | 0.411 | NA | NA | 1248 | 78 |
| b_want_please_statement | 7 | speech_act | POS-cap4 | 0.213 | 0.173 | 0.257 | 724 | 181 |
| b_want_please_statement | 7 | speech_act | human keywords | 0.516 | 0.463 | 0.565 | 2172 | 181 |
| b_want_please_statement | 7 | speech_act[question] | all | 0.433 | NA | NA | 1648 | 103 |
| b_want_please_statement | 7 | speech_act[request/command] | all | 0.450 | NA | NA | 1248 | 78 |
| ab | 90 | speech_act | POS-cap4 | 0.202 | 0.163 | 0.243 | 724 | 181 |
| ab | 90 | speech_act | human keywords | 0.509 | 0.459 | 0.558 | 2172 | 181 |
| ab | 90 | speech_act[question] | all | 0.451 | NA | NA | 1648 | 103 |
| ab | 90 | speech_act[request/command] | all | 0.407 | NA | NA | 1248 | 78 |
| mask_all_arbitrated | 180 | speech_act | POS-cap4 | 0.211 | 0.170 | 0.255 | 715 | 181 |
| mask_all_arbitrated | 180 | speech_act | human keywords | 0.515 | 0.463 | 0.565 | 2144 | 181 |
| mask_all_arbitrated | 180 | speech_act[question] | all | 0.432 | NA | NA | 1636 | 103 |
| mask_all_arbitrated | 180 | speech_act[request/command] | all | 0.449 | NA | NA | 1223 | 78 |

elic1 arbiter units: 142, tags {"agent_inanimate_CB4": 26, "agent_other(CB-5/7)": 18, "certainty_plain_or_other": 15, "certainty_hope_wonder_could_hedge": 15, "please_ask_request": 14, "negation_only_shows_uncertainty": 12, "negation_scope_embedded_or_contrastive": 11, "certainty_request_question_unclear": 7, "cb9_Can_I_please_question": 6, "certainty_hedge_other": 3, "polite_softener(May I/would...if you could/would it be possible)": 3, "speech_act_other": 3, "indirect_or_info_question": 3, "will_you_request_or_plans": 2, "should_we_let_us_offer": 2, "fragment_unclear": 2}. Per-tag masks are in `elic1_by_variant.csv`.

## Holm decisions and maximum shifts

Decision changes: []
Max absolute shift of any estimate over all variants (pp): {"P1": 12.82051282051282, "P2": 0.0, "P3": 0.0}

## Caveats

* Remapping is by output-text pattern on the final stored label; it cannot tell whether an annotator trained on the alternative rule would label differently in other respects (e.g. 'Can you ... please?').
* Tags are assigned by rule from rationale text (declared in `tag_unit`); 'other' classes are small and heterogeneous.
* Masking an arbitrated unit removes every occurrence of that output text (same text_id), so the denominator shrinks; this is the same operation as the W-C 'unknown_masked' sensitivity.
* 'rows changed' counts stored rows of every prompt and channel (P0, P2, S3), not only the P0 rows entering P1-P3.
* Reading: (a) is the only variant that moves a registered contrast materially (W-C P1 falls by about 13 pp, hw1 P1 by about 3 pp; both stay Holm-significant). Under (a) a chip-ASK request that the model words 'Can you ...?' stops counting as honoured, so the chip gain shrinks.
* P2 (politeness) and P3 (polarity) do not depend on speech-act coding, so (a), (b) leave them unchanged by construction; the stored politeness 'Can you = plain' rule is not varied here.
