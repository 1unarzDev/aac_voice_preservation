# Gemini as a third model family: legend test and cue restoration

Plan and priority order: `analysis/model_breadth/GEMINI_PLAN.md` (written before any request). Daily queue: `src/gemini_daily.py` (state `runs/gemini_daily_state.json`, log `runs/gemini_daily.log`). Judging: existing gpt judge (J1/J2), blind arbiter on disputed critical labels, attribution WITHOUT fallback: rows without an agreed or arbitrated label are missing, counted below, never imputed. Same estimators and seeds as `analysis/legend_test` and `analysis/chip_controls` (10,000 bootstrap resamples, seed 20261031).

## Progress (requests cached / planned, per run; unresolved valid rows after judging)

| model | legend (tier 1) | hw run: tiers 2+3 | hwctl (tier 2) | unresolved legend rows | unresolved cue rows |
|---|---|---|---|---|---|
| gemini-3.5-flash | 12/356 | 0/2752 | 0/483 | 0 | 0 |
| gemini-3.1-flash-lite | 262/356 | 0/2752 | 0/483 | 0 | 0 |

(`cached` = generated; the tables below use only generated AND judged AND label-resolved rows; arbiter pending rows are missing.)

## Tier 1: legend test, bare polarity inputs (draw d1; affirmative share among committed outputs)

Reading rule (E1, arm b not scheduled for Gemini): default is NOT a legend artifact if both arms a and c >= 90%; reframe if either < 70%; else partly induced. Arm c reduces commitment (more `unclear/mixed`) when it is instructable; see commitment column.

| model | source | arm | n outputs | n families | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | hw1 | a_legend | 104 (of 104) | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | hw1 | c_markers_missing | 103 (of 103) | 103 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | pooled | a_legend | 104 (of 104) | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| gemini-3.1-flash-lite | pooled | c_markers_missing | 103 (of 103) | 103 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |

**gemini-3.1-flash-lite (pooled sources): default NOT a legend artifact (a and c >= 90%).** a 99.0% (n=104), c 100.0% (n=103); commitment a 100.0%, c 100.0%.

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

No judged cue rows yet.


## Tier 3: hw1 P0, critical-match by dimension and channel (writer-cluster 95% CI, n per cell)

Tier 3 not yet judged.


## Caveats
- One decoding configuration (T=0, thinking budget 0, no seed); free-tier model snapshots can change (model id in each cache entry).
- Partial tiers are family-ordered prefixes (request-file order), so early n is a sample of families in file order, not random.
- Machine-panel judging plus a blind Claude arbiter is not human validation.

