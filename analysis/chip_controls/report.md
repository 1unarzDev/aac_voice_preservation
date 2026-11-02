# E2: chip-gain controls on hw1 (T3)

Decision rules: `analysis/chip_controls/PLAN.md` (written before generation). Outcome = P0 `critical_match`, paired by family x variant x model, pooled over 4 models. Comparators `noncrit`, `chip1` from `runs/hw1` (d0); controls `irrel`, `nlcue` from `runs/hwctl1`. Labels J1==J2 else blind arbiter, no fallback (0 valid control rows unresolved). Writer-cluster CI is primary (7 writers; speech-act n excludes the hw1 quarantine); family-cluster CI and a t interval over writers are alongside.

## Critical-match rate by channel (pooled models; writer-cluster 95% CI)

| dimension | noncrit | chip1 | irrel | nlcue | n |
|---|---|---|---|---|---|
| agent | 32.7 | 100.0 | 32.1 | 99.9 | 816 |
| certainty | 41.4 | 95.4 | 47.8 | 95.3 | 696 |
| polarity | 50.0 | 99.5 | 50.0 | 98.7 | 832 |
| politeness | 50.0 | 88.2 | 50.0 | 90.3 | 712 |
| speech_act | 43.5 | 78.7 | 48.7 | 86.9 | 536 |
| time_quantity | 15.2 | 97.9 | 17.0 | 97.4 | 776 |

## Gains and control contrasts, pooled over models (pp)

| dimension | contrast | estimate | writer-cluster 95% CI | family-cluster 95% CI | t over writers 95% CI | writers | families |
|---|---|---|---|---|---|---|---|
| agent | G_chip (chip1-noncrit) | +67.3 | [+64.8, +69.9] | [+63.8, +70.6] | [+63.9, +70.7] | 7 | 102 |
| agent | G_irrel (irrel-noncrit) | -0.6 | [-1.9, +0.6] | [-3.8, +2.7] | [-2.2, +1.1] | 7 | 102 |
| agent | G_nl (nlcue-noncrit) | +67.2 | [+64.4, +69.9] | [+63.7, +70.6] | [+63.6, +70.8] | 7 | 102 |
| agent | chip1-irrel [primary] | +67.9 | [+66.5, +69.4] | [+64.5, +71.3] | [+66.0, +69.8] | 7 | 102 |
| agent | chip1-nlcue [primary] | +0.1 | [+0.0, +0.4] | [+0.0, +0.4] | [-0.2, +0.4] | 7 | 102 |
| certainty | G_chip (chip1-noncrit) | +54.0 | [+52.4, +55.3] | [+52.0, +56.2] | [+51.9, +56.0] | 6 | 87 |
| certainty | G_irrel (irrel-noncrit) | +6.5 | [+4.9, +7.9] | [+4.2, +8.9] | [+4.1, +8.7] | 6 | 87 |
| certainty | G_nl (nlcue-noncrit) | +53.9 | [+51.4, +55.7] | [+51.4, +56.5] | [+50.7, +57.0] | 6 | 87 |
| certainty | chip1-irrel [primary] | +47.6 | [+46.6, +48.6] | [+45.7, +49.6] | [+46.1, +49.1] | 6 | 87 |
| certainty | chip1-nlcue [primary] | +0.1 | [-0.6, +1.2] | [-1.4, +1.7] | [-1.1, +1.4] | 6 | 87 |
| polarity | G_chip (chip1-noncrit) | +49.5 | [+49.0, +49.9] | [+48.9, +50.0] | [+48.9, +50.1] | 7 | 104 |
| polarity | G_irrel (irrel-noncrit) | +0.0 | [+0.0, +0.0] | [+0.0, +0.0] | [+0.0, +0.0] | 7 | 104 |
| polarity | G_nl (nlcue-noncrit) | +48.7 | [+48.1, +49.3] | [+47.7, +49.5] | [+47.9, +49.4] | 7 | 104 |
| polarity | chip1-irrel [primary] | +49.5 | [+49.0, +49.9] | [+48.9, +50.0] | [+48.9, +50.1] | 7 | 104 |
| polarity | chip1-nlcue [primary] | +0.8 | [+0.1, +1.4] | [+0.0, +1.8] | [-0.1, +1.7] | 7 | 104 |
| politeness | G_chip (chip1-noncrit) | +38.2 | [+36.8, +39.4] | [+36.1, +40.3] | [+36.2, +40.1] | 6 | 89 |
| politeness | G_irrel (irrel-noncrit) | +0.0 | [+0.0, +0.0] | [+0.0, +0.0] | [+0.0, +0.0] | 6 | 89 |
| politeness | G_nl (nlcue-noncrit) | +40.3 | [+38.5, +42.1] | [+38.2, +42.3] | [+37.7, +42.9] | 6 | 89 |
| politeness | chip1-irrel [primary] | +38.2 | [+36.8, +39.4] | [+36.1, +40.3] | [+36.2, +40.1] | 6 | 89 |
| politeness | chip1-nlcue [primary] | -2.1 | [-4.7, +0.3] | [-3.9, -0.3] | [-5.7, +1.5] | 6 | 89 |
| speech_act | G_chip (chip1-noncrit) | +35.3 | [+31.2, +40.3] | [+31.0, +39.4] | [+28.9, +41.8] | 6 | 67 |
| speech_act | G_irrel (irrel-noncrit) | +5.2 | [+1.6, +10.4] | [+2.8, +7.8] | [-1.1, +13.4] | 6 | 67 |
| speech_act | G_nl (nlcue-noncrit) | +43.5 | [+38.7, +48.4] | [+39.9, +47.0] | [+37.1, +51.1] | 6 | 67 |
| speech_act | chip1-irrel [primary] | +30.0 | [+24.6, +33.9] | [+25.6, +34.5] | [+21.3, +37.1] | 6 | 67 |
| speech_act | chip1-nlcue [primary] | -8.2 | [-12.1, -5.3] | [-12.5, -3.9] | [-13.9, -3.6] | 6 | 67 |
| time_quantity | G_chip (chip1-noncrit) | +82.7 | [+80.1, +86.0] | [+79.4, +86.0] | [+78.6, +86.5] | 7 | 97 |
| time_quantity | G_irrel (irrel-noncrit) | +1.8 | [-0.7, +4.8] | [-0.6, +4.3] | [-1.7, +5.6] | 7 | 97 |
| time_quantity | G_nl (nlcue-noncrit) | +82.2 | [+79.8, +85.1] | [+79.0, +85.4] | [+78.6, +85.6] | 7 | 97 |
| time_quantity | chip1-irrel [primary] | +80.9 | [+77.2, +85.4] | [+77.6, +84.1] | [+75.1, +86.1] | 7 | 97 |
| time_quantity | chip1-nlcue [primary] | +0.5 | [+0.1, +1.0] | [-0.5, +1.7] | [-0.1, +1.1] | 7 | 97 |

## Pre-declared reading per dimension

| dimension | chip1 - irrel | vs any-chip | chip1 - nlcue | vs natural language |
|---|---|---|---|---|
| agent | +67.9 [+66.5, +69.4] | chip effect is cue content (chip1-irrel CI > 0) | +0.1 [+0.0, +0.4] | NL equals chip (CI within +/-5 pp) |
| certainty | +47.6 [+46.6, +48.6] | chip effect is cue content (chip1-irrel CI > 0) | +0.1 [-0.6, +1.2] | NL equals chip (CI within +/-5 pp) |
| polarity | +49.5 [+49.0, +49.9] | chip effect is cue content (chip1-irrel CI > 0) | +0.8 [+0.1, +1.4] | chip beats natural language |
| politeness | +38.2 [+36.8, +39.4] | chip effect is cue content (chip1-irrel CI > 0) | -2.1 [-4.7, +0.3] | NL equals chip (CI within +/-5 pp) |
| speech_act | +30.0 [+24.6, +33.9] | chip effect is cue content (chip1-irrel CI > 0) | -8.2 [-12.1, -5.3] | natural language beats chip |
| time_quantity | +80.9 [+77.2, +85.4] | chip effect is cue content (chip1-irrel CI > 0) | +0.5 [+0.1, +1.0] | chip beats natural language |

## Per model: chip1 - irrel and chip1 - nlcue (pp, writer-cluster CI)

| dimension | model | chip1 - irrel | chip1 - nlcue |
|---|---|---|---|
| agent | gemma3-4b | +64.2 [+61.3, +67.0] | +0.0 [+0.0, +0.0] |
| agent | gpt-6.1-terra | +65.2 [+61.9, +69.1] | +0.5 [+0.0, +1.5] |
| agent | llama3.1-8b | +74.0 [+70.8, +77.0] | +0.0 [+0.0, +0.0] |
| agent | qwen2.5-7b | +68.1 [+64.8, +71.7] | +0.0 [+0.0, +0.0] |
| certainty | gemma3-4b | +36.2 [+32.1, +40.2] | +0.6 [-2.3, +4.6] |
| certainty | gpt-6.1-terra | +52.9 [+50.6, +56.2] | +0.6 [+0.0, +1.7] |
| certainty | llama3.1-8b | +50.6 [+50.0, +51.7] | -1.1 [-2.3, +0.0] |
| certainty | qwen2.5-7b | +50.6 [+47.1, +52.9] | +0.6 [-1.7, +3.3] |
| polarity | gemma3-4b | +49.5 [+48.6, +50.0] | +1.0 [+0.0, +2.0] |
| polarity | gpt-6.1-terra | +50.0 [+50.0, +50.0] | +1.9 [+0.0, +3.9] |
| polarity | llama3.1-8b | +49.0 [+48.0, +50.0] | -0.5 [-2.0, +1.0] |
| polarity | qwen2.5-7b | +49.5 [+48.5, +50.0] | +1.0 [+0.0, +2.4] |
| politeness | gemma3-4b | +16.9 [+12.9, +20.8] | -12.9 [-19.1, -6.7] |
| politeness | gpt-6.1-terra | +49.4 [+48.3, +50.0] | +2.2 [+0.6, +4.4] |
| politeness | llama3.1-8b | +41.0 [+37.5, +43.9] | +1.7 [-2.8, +7.2] |
| politeness | qwen2.5-7b | +45.5 [+42.5, +47.8] | +0.6 [-1.7, +2.8] |
| speech_act | gemma3-4b | +29.9 [+23.0, +35.7] | -13.4 [-16.1, -11.1] |
| speech_act | gpt-6.1-terra | +44.8 [+41.1, +48.4] | +4.5 [+0.8, +7.9] |
| speech_act | llama3.1-8b | +11.9 [+0.8, +18.4] | -14.9 [-23.7, -8.6] |
| speech_act | qwen2.5-7b | +33.6 [+27.6, +39.7] | -9.0 [-16.7, -0.8] |
| time_quantity | gemma3-4b | +84.5 [+79.7, +89.4] | -0.5 [-2.1, +1.1] |
| time_quantity | gpt-6.1-terra | +74.2 [+69.0, +80.3] | +0.0 [+0.0, +0.0] |
| time_quantity | llama3.1-8b | +82.5 [+77.6, +87.3] | +2.6 [+0.5, +5.1] |
| time_quantity | qwen2.5-7b | +82.5 [+78.3, +87.3] | +0.0 [-1.5, +1.5] |

## Sensitivity: drop the 3 borderline certainty items with irrelevant chip [TELL] (pooled models)

| dimension | contrast | estimate | writer CI |
|---|---|---|---|
| certainty | G_chip (chip1-noncrit) | +54.0 | [+52.9, +55.1] |
| certainty | G_irrel (irrel-noncrit) | +7.3 | [+5.3, +9.3] |
| certainty | G_nl (nlcue-noncrit) | +53.7 | [+51.2, +55.5] |
| certainty | chip1-irrel [primary] | +46.7 | [+45.4, +48.0] |
| certainty | chip1-nlcue [primary] | +0.3 | [-0.6, +1.7] |

## Literalization (share of valid outputs with a bracket, or 'I tell you' / 'statement' words)

| channel | model | bracket | tell-you/statement words |
|---|---|---|---|
| chip1 | gemma3-4b | 2.0% | 0.3% |
| chip1 | gpt-6.1-terra | 0.0% | 0.2% |
| chip1 | llama3.1-8b | 0.0% | 0.1% |
| chip1 | qwen2.5-7b | 0.1% | 1.2% |
| irrel | gemma3-4b | 1.3% | 0.5% |
| irrel | gpt-6.1-terra | 0.0% | 0.4% |
| irrel | llama3.1-8b | 0.0% | 0.7% |
| irrel | qwen2.5-7b | 0.0% | 1.5% |
| nlcue | gemma3-4b | 3.9% | 0.4% |
| nlcue | gpt-6.1-terra | 0.0% | 0.4% |
| nlcue | llama3.1-8b | 0.0% | 0.5% |
| nlcue | qwen2.5-7b | 5.6% | 0.5% |
| noncrit | gemma3-4b | 0.9% | 0.4% |
| noncrit | gpt-6.1-terra | 0.0% | 0.2% |
| noncrit | llama3.1-8b | 0.0% | 0.2% |
| noncrit | qwen2.5-7b | 0.9% | 0.0% |
