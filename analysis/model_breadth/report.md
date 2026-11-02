# Model breadth: larger local open models next to the four original models

New models: qwen2.5-14b, mistral-nemo-12b (Q4_K_M GGUF, llama.cpp, same prompts/inputs/greedy decoding/request files as the original models; only the model id differs). Original: qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra. Labels: J1==J2 else blind arbiter, no fallback (unresolved valid rows: hw 0, controls 0, legend 0). hw1 population: 546 analysed families (547 kept minus the speech-act refusal/acceptance quarantine and writer P06's speech-act pair), 20 writers; writer-cluster 95% bootstrap CIs (10,000 resamples) unless stated.

## 1. Bare default: affirmative share among committed polarity outputs (hw1, bare channel, polarity families)

| model | share [writer 95% CI] | family-cluster CI | n |
|---|---|---|---|
| qwen2.5-7b | 100.0 [100.0, 100.0] | [100.0, 100.0] | 102 |
| llama3.1-8b | 99.0 [97.1, 100.0] | [97.1, 100.0] | 104 |
| gemma3-4b | 100.0 [100.0, 100.0] | [100.0, 100.0] | 104 |
| gpt-6.1-terra | 100.0 [100.0, 100.0] | [100.0, 100.0] | 104 |
| qwen2.5-14b (new) | 100.0 [100.0, 100.0] | [100.0, 100.0] | 104 |
| mistral-nemo-12b (new) | 99.0 [97.1, 100.0] | [97.1, 100.0] | 104 |

## 2. Legend test (draw d1; affirmative share among committed outputs; 184 families = hw1 104 + W-C 80; family-cluster CI)

| model | (a) legend | (b) no legend | (c) markers may be missing | commitment rate a/b/c | hw1-only a/b/c (writer CI upper bounds) |
|---|---|---|---|---|---|
| qwen2.5-7b | 99.5 [98.3, 100.0] | 98.9 [97.3, 100.0] | 100.0 [100.0, 100.0] | 98.9 / 100.0 / 98.9 | 100.0 (hi 100.0) / 99.0 (hi 100.0) / 100.0 (hi 100.0) |
| llama3.1-8b | 99.5 [98.4, 100.0] | 98.4 [96.2, 100.0] | 100.0 [100.0, 100.0] | 100.0 / 100.0 / 100.0 | 99.0 (hi 100.0) / 99.0 (hi 100.0) / 100.0 (hi 100.0) |
| gemma3-4b | 99.5 [98.4, 100.0] | 98.9 [97.3, 100.0] | 100.0 [100.0, 100.0] | 99.5 / 100.0 / 100.0 | 99.0 (hi 100.0) / 100.0 (hi 100.0) / 100.0 (hi 100.0) |
| gpt-6.1-terra | 99.5 [98.3, 100.0] | 97.3 [94.6, 99.5] | 99.4 [98.3, 100.0] | 98.9 / 100.0 / 98.4 | 100.0 (hi 100.0) / 100.0 (hi 100.0) / 100.0 (hi 100.0) |
| qwen2.5-14b (new) | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 / 100.0 / 98.9 | 100.0 (hi 100.0) / 100.0 (hi 100.0) / 100.0 (hi 100.0) |
| mistral-nemo-12b (new) | 97.3 [94.6, 99.5] | 99.5 [98.4, 100.0] | 97.8 [95.7, 99.5] | 100.0 / 99.5 / 100.0 | 99.0 (hi 100.0) / 100.0 (hi 100.0) / 99.0 (hi 100.0) |

Replication draw d2 (a / b / c):

| model | a | b | c |
|---|---|---|---|
| qwen2.5-7b | 99.5 | 98.9 | 100.0 |
| llama3.1-8b | 99.5 | 97.8 | 100.0 |
| gemma3-4b | 100.0 | 99.5 | 100.0 |
| gpt-6.1-terra | 98.4 | 98.4 | 99.5 |
| qwen2.5-14b | 100.0 | 100.0 | 100.0 |
| mistral-nemo-12b | 97.3 | 100.0 | 97.8 |

## 3. Speech-act chip contrast (P1: chip1 - noncritical word, speech-act families) and politeness addition (P2)

| contrast | model | estimate pp | writer CI | family CI | n | writers |
|---|---|---|---|---|---|---|
| P1 | qwen2.5-7b | +35.1 | [+30.1, +41.0] | [+28.4, +41.0] | 134 | 6 |
| P1 | llama3.1-8b | +18.7 | [+7.1, +25.9] | [+10.4, +26.9] | 134 | 6 |
| P1 | gemma3-4b | +36.6 | [+28.7, +45.1] | [+29.9, +43.3] | 134 | 6 |
| P1 | gpt-6.1-terra | +50.7 | [+43.0, +60.0] | [+44.8, +56.0] | 134 | 6 |
| P1 | qwen2.5-14b (new) | +35.1 | [+31.6, +38.7] | [+27.6, +41.8] | 134 | 6 |
| P1 | mistral-nemo-12b (new) | +37.3 | [+23.8, +46.4] | [+29.9, +44.8] | 134 | 6 |
| P2 | qwen2.5-7b | +0.0 | [+0.0, +0.0] | [+0.0, +0.0] | 89 | 6 |
| P2 | llama3.1-8b | +1.1 | [+0.0, +3.4] | [+0.0, +3.4] | 89 | 6 |
| P2 | gemma3-4b | +22.5 | [+15.6, +29.9] | [+13.5, +32.6] | 89 | 6 |
| P2 | gpt-6.1-terra | +6.7 | [+3.4, +10.0] | [+2.2, +12.4] | 89 | 6 |
| P2 | qwen2.5-14b (new) | +7.9 | [+0.0, +16.7] | [+0.0, +16.9] | 89 | 6 |
| P2 | mistral-nemo-12b (new) | -1.1 | [-6.7, +3.4] | [-5.6, +2.2] | 89 | 6 |

## 4. Chip gain per dimension (pp, writer-cluster 95% CI)

chip1 - noncrit = gain over the noncritical word; chip1 - irrel = gain over an irrelevant chip from another dimension (cue content, not any chip); chip1 - word = chip versus the same meaning as a plain word (0 = the plain word does as well as the chip).

| dimension | model | chip1 - noncrit | chip1 - irrel | irrel - noncrit | chip1 - plain word | writers |
|---|---|---|---|---|---|---|
| polarity | qwen2.5-7b | +49.5 [+48.5, +50.0] | +49.5 [+48.5, +50.0] | +0.0 [+0.0, +0.0] | +1.0 [+0.0, +2.4] | 7 |
| polarity | llama3.1-8b | +49.0 [+48.0, +50.0] | +49.0 [+48.0, +50.0] | +0.0 [+0.0, +0.0] | -0.5 [-2.0, +1.0] | 7 |
| polarity | gemma3-4b | +49.5 [+48.6, +50.0] | +49.5 [+48.6, +50.0] | +0.0 [+0.0, +0.0] | +1.0 [+0.0, +2.0] | 7 |
| polarity | gpt-6.1-terra | +50.0 [+50.0, +50.0] | +50.0 [+50.0, +50.0] | +0.0 [+0.0, +0.0] | +1.9 [+0.0, +3.9] | 7 |
| polarity | qwen2.5-14b (new) | +50.0 [+50.0, +50.0] | +50.0 [+50.0, +50.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | 7 |
| polarity | mistral-nemo-12b (new) | +50.0 [+50.0, +50.0] | +50.0 [+50.0, +50.0] | +0.0 [+0.0, +0.0] | +0.5 [+0.0, +1.4] | 7 |
| speech_act | qwen2.5-7b | +35.1 [+30.1, +41.0] | +33.6 [+27.6, +39.7] | +1.5 [-1.9, +7.8] | -9.0 [-16.7, -0.8] | 6 |
| speech_act | llama3.1-8b | +18.7 [+7.1, +25.9] | +11.9 [+0.8, +18.4] | +6.7 [+4.5, +9.8] | -14.9 [-23.7, -8.6] | 6 |
| speech_act | gemma3-4b | +36.6 [+28.7, +45.1] | +29.9 [+23.0, +35.7] | +6.7 [+0.0, +16.4] | -13.4 [-16.1, -11.1] | 6 |
| speech_act | gpt-6.1-terra | +50.7 [+43.0, +60.0] | +44.8 [+41.1, +48.4] | +6.0 [+0.7, +12.5] | +4.5 [+0.8, +7.9] | 6 |
| speech_act | qwen2.5-14b (new) | +35.1 [+31.6, +38.7] | +32.8 [+29.0, +37.1] | +2.2 [+0.0, +5.8] | -3.0 [-8.0, +3.4] | 6 |
| speech_act | mistral-nemo-12b (new) | +37.3 [+23.8, +46.4] | +31.3 [+14.2, +40.6] | +6.0 [+2.8, +10.8] | +3.7 [-4.3, +9.7] | 6 |
| politeness | qwen2.5-7b | +45.5 [+42.5, +47.8] | +45.5 [+42.5, +47.8] | +0.0 [+0.0, +0.0] | +0.6 [-1.7, +2.8] | 6 |
| politeness | llama3.1-8b | +41.0 [+37.5, +43.9] | +41.0 [+37.5, +43.9] | +0.0 [+0.0, +0.0] | +1.7 [-2.8, +7.2] | 6 |
| politeness | gemma3-4b | +16.9 [+12.9, +20.8] | +16.9 [+12.9, +20.8] | +0.0 [+0.0, +0.0] | -12.9 [-19.1, -6.7] | 6 |
| politeness | gpt-6.1-terra | +49.4 [+48.3, +50.0] | +49.4 [+48.3, +50.0] | +0.0 [+0.0, +0.0] | +2.2 [+0.6, +4.4] | 6 |
| politeness | qwen2.5-14b (new) | +50.0 [+50.0, +50.0] | +50.0 [+50.0, +50.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | 6 |
| politeness | mistral-nemo-12b (new) | +49.4 [+48.3, +50.0] | +49.4 [+48.3, +50.0] | +0.0 [+0.0, +0.0] | +1.7 [-1.1, +4.5] | 6 |
| agent | qwen2.5-7b | +65.2 [+60.5, +69.4] | +68.1 [+64.8, +71.7] | -2.9 [-5.3, -0.5] | +0.0 [+0.0, +0.0] | 7 |
| agent | llama3.1-8b | +71.6 [+67.8, +76.2] | +74.0 [+70.8, +77.0] | -2.5 [-6.6, +1.9] | +0.0 [+0.0, +0.0] | 7 |
| agent | gemma3-4b | +62.7 [+59.5, +65.8] | +64.2 [+61.3, +67.0] | -1.5 [-4.5, +2.9] | +0.0 [+0.0, +0.0] | 7 |
| agent | gpt-6.1-terra | +69.6 [+66.7, +72.7] | +65.2 [+61.9, +69.1] | +4.4 [+1.4, +7.9] | +0.5 [+0.0, +1.5] | 7 |
| agent | qwen2.5-14b (new) | +63.7 [+60.2, +67.2] | +62.7 [+59.1, +65.8] | +1.0 [-1.9, +3.9] | +0.0 [+0.0, +0.0] | 7 |
| agent | mistral-nemo-12b (new) | +64.7 [+60.0, +68.8] | +66.2 [+61.9, +71.0] | -1.5 [-6.4, +2.9] | +0.0 [+0.0, +0.0] | 7 |
| time_quantity | qwen2.5-7b | +78.4 [+73.5, +83.7] | +82.5 [+78.3, +87.3] | -4.1 [-6.2, -2.0] | +0.0 [-1.5, +1.5] | 7 |
| time_quantity | llama3.1-8b | +83.0 [+77.3, +88.1] | +82.5 [+77.6, +87.3] | +0.5 [-5.0, +7.2] | +2.6 [+0.5, +5.1] | 7 |
| time_quantity | gemma3-4b | +88.1 [+86.0, +90.4] | +84.5 [+79.7, +89.4] | +3.6 [-1.0, +8.6] | -0.5 [-2.1, +1.1] | 7 |
| time_quantity | gpt-6.1-terra | +81.4 [+76.5, +86.9] | +74.2 [+69.0, +80.3] | +7.2 [+3.2, +12.8] | +0.0 [+0.0, +0.0] | 7 |
| time_quantity | qwen2.5-14b (new) | +83.0 [+81.2, +84.8] | +89.2 [+85.8, +92.5] | -6.2 [-10.6, -1.6] | -1.0 [-2.2, +0.0] | 7 |
| time_quantity | mistral-nemo-12b (new) | +83.0 [+79.4, +85.6] | +73.7 [+70.2, +77.6] | +9.3 [+4.4, +14.2] | -1.5 [-2.9, -0.5] | 7 |
| certainty | qwen2.5-7b | +51.7 [+48.9, +54.4] | +50.6 [+47.1, +52.9] | +1.1 [-1.1, +3.1] | +0.6 [-1.7, +3.3] | 6 |
| certainty | llama3.1-8b | +54.6 [+51.7, +57.5] | +50.6 [+50.0, +51.7] | +4.0 [+1.7, +6.1] | -1.1 [-2.3, +0.0] | 6 |
| certainty | gemma3-4b | +46.0 [+42.3, +50.6] | +36.2 [+32.1, +40.2] | +9.8 [+6.9, +12.1] | +0.6 [-2.3, +4.6] | 6 |
| certainty | gpt-6.1-terra | +63.8 [+60.9, +67.8] | +52.9 [+50.6, +56.2] | +10.9 [+6.2, +15.5] | +0.6 [+0.0, +1.7] | 6 |
| certainty | qwen2.5-14b (new) | +52.9 [+51.1, +54.8] | +50.0 [+50.0, +50.0] | +2.9 [+1.1, +4.8] | +0.6 [+0.0, +1.7] | 6 |
| certainty | mistral-nemo-12b (new) | +54.0 [+51.7, +56.7] | +50.0 [+50.0, +50.0] | +4.0 [+1.7, +6.7] | +0.0 [+0.0, +0.0] | 6 |

## 5. Critical match on the `full` channel (typed sentence; % of valid outputs honouring the item's critical value; writer CI)

| dimension | qwen2.5-7b | llama3.1-8b | gemma3-4b | gpt-6.1-terra | qwen2.5-14b | mistral-nemo-12b |
|---|---|---|---|---|---|---|
| polarity | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 99.5 [98.6, 100.0] |
| speech_act | 100.0 [100.0, 100.0] | 97.8 [96.2, 99.2] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 97.0 [94.9, 99.2] |
| politeness | 100.0 [100.0, 100.0] | 99.4 [98.3, 100.0] | 87.6 [84.5, 90.6] | 96.6 [95.0, 98.3] | 91.6 [88.3, 94.9] | 98.3 [96.1, 100.0] |
| agent | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] |
| time_quantity | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 99.0 [96.9, 100.0] | 100.0 [100.0, 100.0] |
| certainty | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 98.9 [96.3, 100.0] |

## 6. Pattern checks (computed)

| model | bare default >= 90% | legend b and c >= 90% | P1 writer CI > 0 | chip1 - irrel CI > 0 in all 6 dims | chip1 - plain word within +/-5 pp (dims) |
|---|---|---|---|---|---|
| qwen2.5-7b | True | True | True | True (6/6) | 5/6 |
| llama3.1-8b | True | True | True | True (6/6) | 3/6 |
| gemma3-4b | True | True | True | True (6/6) | 4/6 |
| gpt-6.1-terra | True | True | True | True (6/6) | 5/6 |
| qwen2.5-14b | True | True | True | True (6/6) | 5/6 |
| mistral-nemo-12b | True | True | True | True (6/6) | 5/6 |

## 7. Reading (generated from the tables above)

- Bare default and legend test: both new models stay at or above 97.3% affirmative among committed outputs in every legend arm (decision rule: >= 90% in arms b and c = not a legend artifact), and 99.0% or more on the bare hw1 channel. Pattern holds for both.
- Speech-act chip contrast (P1): new models +35.1 to +37.3 pp (writer CI lower bounds +23.8 and above), original four +18.7 to +50.7 pp. Same sign, inside the original range.
- Irrelevant chip: the gain over an irrelevant chip stays positive in all 6 dimensions for both new models; the irrelevant chip alone moves critical match by a few points at most (column `irrel - noncrit`), so the chip gain is cue content, as for the original models.
- Plain word vs chip: for polarity, politeness, agent, time and certainty the plain-word cue equals the chip within +/-5 pp for both new models; speech act is the dimension where the plain word and the chip differ, as in the original models (see section 4), so the 'plain word matches chips' reading is not uniform across dimensions.
- Full channel: lowest cell per new model: qwen2.5-14b politeness 91.6%; mistral-nemo-12b speech_act 97.0% (original models' lowest: qwen2.5-7b polarity 100.0%; llama3.1-8b speech_act 97.8%; gemma3-4b politeness 87.6%; gpt-6.1-terra politeness 96.6%). Model size does not monotonically improve politeness on the full channel (compare qwen2.5-7b vs qwen2.5-14b).
- Caveats: Q4_K_M quantisation (as for the original local models), greedy decoding, one draw for hw1 and chip controls (two draws for the legend test), 6-7 writers per dimension; 12-14B open models are larger than the original local models but not frontier-scale.
