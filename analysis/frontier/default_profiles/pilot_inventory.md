# S0 pilot inventory (default_profiles, round 1). Zero generation; stored outputs only.

## (a) Cue-positive human units (elicitation: 600 messages x 3 human keyword sets)

| dimension | messages with cue | human sets with cue | of which cue dropped (lenient flag) |
|---|---|---|---|
| polarity | 122 | 366 | 76 |
| speech_act | 317 | 951 | 417 |
| politeness | 127 | 381 | 136 |
| certainty | 90 | 270 | 112 |
| quantity | 10 | 30 | 19 |

Quantity is descriptive only (not tested), per PLAN. Note the exposure units E (cue in source AND dropped in keywords) are the 'dropped' column; these are the positives every policy comparison rests on.

## (b,c) Stored channel counts (P0, quarantine rows removed) for hw1-family runs

| model | bare | chip1 | chipall | full | irrel | nlcue | noncrit |
|---|---|---|---|---|---|---|---|
| gemma3-4b | 1148 | 1148 | 1148 | 1148 | 1094 | 1094 | 1148 |
| gpt-6.1-terra | 1148 | 1148 | 1148 | 1148 | 1094 | 1094 | 1148 |
| llama3.1-8b | 1148 | 1148 | 1148 | 1148 | 1094 | 1094 | 1148 |
| mistral-nemo-12b | 1094 | 1094 | 1094 | 1094 | 1094 | 1094 | 1094 |
| qwen2.5-14b | 1094 | 1094 | 1094 | 1094 | 1094 | 1094 | 1094 |
| qwen2.5-7b | 1148 | 1148 | 1148 | 1148 | 1094 | 1094 | 1148 |

Gemini flash-lite hw/hwctl runs are partial (2 / 86 rows scored): excluded.

## (d) Human gold for judge error rates (elic1 sample, final labels vs 4-annotator plurality)

| dimension | subset | n | acc | acc_ci | kappa |
|---|---|---|---|---|---|
| critical | sampled@elic1#agent | 38 | 0.974 | [0.865, 0.995] | 0.965 |
| critical | sampled@elic1#certainty | 25 | 0.920 | [0.75, 0.978] | 0.889 |
| critical | sampled@elic1#polarity | 25 | 1.000 | [0.867, 1.0] | 1.000 |
| critical | sampled@elic1#politeness | 24 | 1.000 | [0.862, 1.0] | 1.000 |
| critical | sampled@elic1#speech_act | 39 | 0.974 | [0.868, 0.995] | 0.964 |

## H3 placebo check (stored data, ALL = 6 models pooled, family-cluster bootstrap 2,000, seed 20261101)

Criterion (PLAN s1): |irrel - noncrit| <= 2 pp with CI inside +-4 pp AND chip1 - irrel >= 10 pp with CI > 0.

| dimension | placebo diff [CI] | chip1 - irrel [CI] | placebo ok | gain >= 10 pp | assumption credited |
|---|---|---|---|---|---|
| agent | -0.5 [-3.6, +2.9] | +66.7 [+63.5, +70.3] | True | True | True |
| certainty | +5.5 [+3.5, +7.4] | +48.4 [+47.1, +49.6] | False | True | False |
| polarity | +0.0 [+0.0, +0.0] | +49.7 [+49.3, +50.0] | True | True | True |
| politeness | +0.0 [+0.0, +0.0] | +42.0 [+40.6, +43.4] | True | True | True |
| speech_act | +4.8 [+2.6, +7.4] | +30.5 [+26.6, +34.6] | False | True | False |
| time_quantity | +1.7 [-0.7, +4.3] | +81.1 [+78.1, +83.9] | False | True | False |

Per-model credit count (placebo and gain both pass), polarity 6/6, speech act 0/6 models.

## GO / NO-GO

{"polarity_cue_pos_units_ge60": true, "speech_act_cue_pos_units_ge60": true, "placebo_models": 6, "GO": true}
