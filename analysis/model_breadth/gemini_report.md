# Gemini as a third model family: legend test and cue restoration

Plan and priority order: `analysis/model_breadth/GEMINI_PLAN.md` (written before any request). Daily queue: `src/gemini_daily.py` (state `runs/gemini_daily_state.json`, log `runs/gemini_daily.log`). Judging: existing gpt judge (J1/J2), blind arbiter on disputed critical labels, attribution WITHOUT fallback: rows without an agreed or arbitrated label are missing, counted below, never imputed. Same estimators and seeds as `analysis/legend_test` and `analysis/chip_controls` (10,000 bootstrap resamples, seed 20261031).

## Progress (requests cached / planned, per run; unresolved valid rows after judging)

| model | legend (tier 1) | hw run: tiers 2+3 | hwctl (tier 2) | unresolved legend rows | unresolved cue rows |
|---|---|---|---|---|---|
| gemini-3.5-flash | 12/356 | 0/2752 | 0/483 | 0 | 0 |
| gemini-3.1-flash-lite | 356/356 | 71/2752 | 59/483 | 0 | 0 |

(`cached` = generated; the tables below use only generated AND judged AND label-resolved rows; arbiter pending rows are missing.)

## Tier 1: legend test, bare polarity inputs (draw d1; affirmative share among committed outputs)

Reading rule (E1, arm b not scheduled for Gemini): default is NOT a legend artifact if both arms a and c >= 90%; reframe if either < 70%; else partly induced. Arm c reduces commitment (more `unclear/mixed`) when it is instructable; see commitment column.

| model | source | arm | n outputs | n families | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | WC | a_legend | 80 (of 80) | 80 | 96.2 [91.2, 100.0] | 96.2 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | WC | c_markers_missing | 80 (of 80) | 80 | 97.5 [93.8, 100.0] | 97.5 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | hw1 | a_legend | 104 (of 104) | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | hw1 | c_markers_missing | 104 (of 104) | 104 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | pooled | a_legend | 184 (of 184) | 184 | 97.8 [95.7, 99.5] | 97.8 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | pooled | c_markers_missing | 184 (of 184) | 184 | 98.9 [97.3, 100.0] | 98.9 | 100.0 | 0.0 |
| gemini-3.5-flash | hw1 | a_legend | 6 (of 6) | 6 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemini-3.5-flash | hw1 | c_markers_missing | 6 (of 6) | 6 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemini-3.5-flash | pooled | a_legend | 6 (of 6) | 6 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemini-3.5-flash | pooled | c_markers_missing | 6 (of 6) | 6 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |

**gemini-3.5-flash (pooled sources): default NOT a legend artifact (a and c >= 90%).** a 100.0% (n=6), c 100.0% (n=6); commitment a 100.0%, c 100.0%.

**gemini-3.1-flash-lite (pooled sources): default NOT a legend artifact (a and c >= 90%).** a 97.8% (n=184), c 98.9% (n=184); commitment a 100.0%, c 100.0%.

### Side by side: existing models, same arms, draw d1, pooled sources (`analysis/legend_test/arm_share.csv`)

| model | arm | n | affirmative share [95% CI] | commitment rate |
|---|---|---|---|---|
| ALL | a_legend | 731 | 99.5 [98.9, 99.9] | 99.3 |
| ALL | c_markers_missing | 731 | 99.9 [99.6, 100.0] | 99.3 |
| gemma3-4b | a_legend | 183 | 99.5 [98.4, 100.0] | 99.5 |
| gemma3-4b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 |
| gpt-6.1-terra | a_legend | 182 | 99.5 [98.3, 100.0] | 98.9 |
| gpt-6.1-terra | c_markers_missing | 181 | 99.4 [98.3, 100.0] | 98.4 |
| llama3.1-8b | a_legend | 184 | 99.5 [98.4, 100.0] | 100.0 |
| llama3.1-8b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 |
| qwen2.5-7b | a_legend | 182 | 99.5 [98.3, 100.0] | 98.9 |
| qwen2.5-7b | c_markers_missing | 182 | 100.0 [100.0, 100.0] | 98.9 |

## Tier 2: cue restoration on hw1 polarity and speech_act (critical match; paired by family x variant)

### Critical-match rate by channel (writer-cluster 95% CI; n = scored family x variant pairs with that channel)

| model | dimension | noncrit | chip1 | irrel | nlcue |
|---|---|---|---|---|---|
| gemini-3.1-flash-lite | polarity | NA [NA, NA] (n=0) | NA [NA, NA] (n=0) | 50.0 [50.0, 50.0] (n=24) | 100.0 [100.0, 100.0] (n=23) |
| gemini-3.1-flash-lite | speech_act | 50.0 [50.0, 50.0] (n=2) | NA [NA, NA] (n=0) | 44.4 [31.2, 50.0] (n=18) | 83.3 [57.1, 100.0] (n=18) |

### Gains and control contrasts (pp; writer-cluster CI primary, family-cluster alongside)

| model | dimension | contrast | estimate | writer-cluster 95% CI | family-cluster 95% CI | n pairs | writers | families |
|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | polarity | G_chip (chip1-noncrit) | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | polarity | G_irrel (irrel-noncrit) | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | polarity | G_nl (nlcue-noncrit) | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | polarity | chip1-irrel [primary] | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | polarity | chip1-nlcue [primary] | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | speech_act | G_chip (chip1-noncrit) | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | speech_act | G_irrel (irrel-noncrit) | +0.0 | [+0.0, +0.0] | [+0.0, +0.0] | 2 | 1 | 1 |
| gemini-3.1-flash-lite | speech_act | G_nl (nlcue-noncrit) | +50.0 | [+50.0, +50.0] | [+50.0, +50.0] | 2 | 1 | 1 |
| gemini-3.1-flash-lite | speech_act | chip1-irrel [primary] | NA (no paired rows yet) | | | 0 | | |
| gemini-3.1-flash-lite | speech_act | chip1-nlcue [primary] | NA (no paired rows yet) | | | 0 | | |

### Pre-declared reading (analysis/chip_controls/PLAN.md rules, per dimension, writer-cluster CI)

| model | dimension | chip1 - irrel | vs any-chip | chip1 - nlcue | vs natural language |
|---|---|---|---|---|---|
| gemini-3.1-flash-lite | polarity | incomplete | | incomplete | |
| gemini-3.1-flash-lite | speech_act | incomplete | | incomplete | |

### Side by side: existing models, pooled over the 4 models and per model (`analysis/chip_controls/chip_controls.csv`, writer-cluster CI)

| model | dimension | G_chip | chip1 - irrel | chip1 - nlcue |
|---|---|---|---|---|
| ALL | polarity | +49.5 [+49.0, +49.9] | +49.5 [+49.0, +49.9] | +0.8 [+0.1, +1.4] |
| ALL | speech_act | +35.3 [+31.2, +40.3] | +30.0 [+24.6, +33.9] | -8.2 [-12.1, -5.3] |
| gemma3-4b | polarity | +49.5 [+48.6, +50.0] | +49.5 [+48.6, +50.0] | +1.0 [+0.0, +2.0] |
| gemma3-4b | speech_act | +36.6 [+28.7, +45.1] | +29.9 [+23.0, +35.7] | -13.4 [-16.1, -11.1] |
| gpt-6.1-terra | polarity | +50.0 [+50.0, +50.0] | +50.0 [+50.0, +50.0] | +1.9 [+0.0, +3.9] |
| gpt-6.1-terra | speech_act | +50.7 [+43.0, +60.0] | +44.8 [+41.1, +48.4] | +4.5 [+0.8, +7.9] |
| llama3.1-8b | polarity | +49.0 [+48.0, +50.0] | +49.0 [+48.0, +50.0] | -0.5 [-2.0, +1.0] |
| llama3.1-8b | speech_act | +18.7 [+7.1, +25.9] | +11.9 [+0.8, +18.4] | -14.9 [-23.7, -8.6] |
| qwen2.5-7b | polarity | +49.5 [+48.5, +50.0] | +49.5 [+48.5, +50.0] | +1.0 [+0.0, +2.4] |
| qwen2.5-7b | speech_act | +35.1 [+30.1, +41.0] | +33.6 [+27.6, +39.7] | -9.0 [-16.7, -0.8] |

### Literalization: share of valid outputs containing a bracketed chip

| model | channel | bracket share | n |
|---|---|---|---|
| gemini-3.1-flash-lite | irrel | 0.0% | 42 |
| gemini-3.1-flash-lite | nlcue | 4.9% | 41 |
| gemini-3.1-flash-lite | noncrit | 0.0% | 2 |

## Tier 3: hw1 P0, critical-match by dimension and channel (writer-cluster 95% CI, n per cell)

| model | dimension | channel | critical match [95% CI] | n |  terra (hw1) |
|---|---|---|---|---|---|

## Caveats
- One decoding configuration (T=0, thinking budget 0, no seed); free-tier model snapshots can change (model id in each cache entry).
- Partial tiers are family-ordered prefixes (request-file order), so early n is a sample of families in file order, not random.
- Machine-panel judging plus a blind Claude arbiter is not human validation.

