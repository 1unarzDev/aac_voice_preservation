# E1: prompt-legend test on bare polarity inputs (T1)

Decision rule: `analysis/legend_test/PLAN.md` (written before generation). Run `runs/legend1`; labels J1==J2 else blind arbiter, **no fallback**; 0 valid rows unresolved. Primary draw d1, pooled over 4 models and both source sets (hw1 104 families, W-C 80 families); family-cluster 95% bootstrap CIs (10,000).

## Verdict (pre-declared rule, draw d1): **default is NOT a legend artifact (b and c both >= 90%)**

Pooled affirmative share among committed outputs, d1: a (legend) 99.5%, b (no legend) 98.4%, c (markers may be missing) 99.9%. d2 replication: a_legend 99.3%, b_nolegend 98.6%, c_markers_missing 99.9%; arm a original draw d0 (the published number): 99.6%.

## Per arm x model x source, draw d1 (primary)
### Pooled over sources

| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|
| ALL | a_legend | 731 | 99.5 [98.9, 99.9] | 98.8 | 99.3 | 0.7 |
| ALL | b_nolegend | 736 | 98.4 [97.4, 99.2] | 98.4 | 100.0 | 0.0 |
| ALL | c_markers_missing | 731 | 99.9 [99.6, 100.0] | 99.2 | 99.3 | 0.7 |
| gemma3-4b | a_legend | 183 | 99.5 [98.4, 100.0] | 98.9 | 99.5 | 0.5 |
| gemma3-4b | b_nolegend | 184 | 98.9 [97.3, 100.0] | 98.9 | 100.0 | 0.0 |
| gemma3-4b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | a_legend | 182 | 99.5 [98.3, 100.0] | 98.4 | 98.9 | 1.1 |
| gpt-6.1-terra | b_nolegend | 184 | 97.3 [94.6, 99.5] | 97.3 | 100.0 | 0.0 |
| gpt-6.1-terra | c_markers_missing | 181 | 99.4 [98.3, 100.0] | 97.8 | 98.4 | 1.6 |
| llama3.1-8b | a_legend | 184 | 99.5 [98.4, 100.0] | 99.5 | 100.0 | 0.0 |
| llama3.1-8b | b_nolegend | 184 | 98.4 [96.2, 100.0] | 98.4 | 100.0 | 0.0 |
| llama3.1-8b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| qwen2.5-7b | a_legend | 182 | 99.5 [98.3, 100.0] | 98.4 | 98.9 | 1.1 |
| qwen2.5-7b | b_nolegend | 184 | 98.9 [97.3, 100.0] | 98.9 | 100.0 | 0.0 |
| qwen2.5-7b | c_markers_missing | 182 | 100.0 [100.0, 100.0] | 98.9 | 98.9 | 1.1 |

### hw1 only (human-written; writer-cluster CI in arm_share.csv)

| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|
| ALL | a_legend | 412 | 99.5 [98.8, 100.0] | 98.6 | 99.0 | 1.0 |
| ALL | b_nolegend | 416 | 99.5 [98.8, 100.0] | 99.5 | 100.0 | 0.0 |
| ALL | c_markers_missing | 413 | 100.0 [100.0, 100.0] | 99.3 | 99.3 | 0.7 |
| gemma3-4b | a_legend | 103 | 99.0 [97.1, 100.0] | 98.1 | 99.0 | 1.0 |
| gemma3-4b | b_nolegend | 104 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemma3-4b | c_markers_missing | 104 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | a_legend | 102 | 100.0 [100.0, 100.0] | 98.1 | 98.1 | 1.9 |
| gpt-6.1-terra | b_nolegend | 104 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | c_markers_missing | 102 | 100.0 [100.0, 100.0] | 98.1 | 98.1 | 1.9 |
| llama3.1-8b | a_legend | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| llama3.1-8b | b_nolegend | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| llama3.1-8b | c_markers_missing | 104 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| qwen2.5-7b | a_legend | 103 | 100.0 [100.0, 100.0] | 99.0 | 99.0 | 1.0 |
| qwen2.5-7b | b_nolegend | 104 | 99.0 [97.1, 100.0] | 99.0 | 100.0 | 0.0 |
| qwen2.5-7b | c_markers_missing | 103 | 100.0 [100.0, 100.0] | 99.0 | 99.0 | 1.0 |

### W-C only

| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|
| ALL | a_legend | 319 | 99.4 [98.4, 100.0] | 99.1 | 99.7 | 0.3 |
| ALL | b_nolegend | 320 | 96.9 [94.7, 98.8] | 96.9 | 100.0 | 0.0 |
| ALL | c_markers_missing | 318 | 99.7 [99.1, 100.0] | 99.1 | 99.4 | 0.6 |
| gemma3-4b | a_legend | 80 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gemma3-4b | b_nolegend | 80 | 97.5 [93.8, 100.0] | 97.5 | 100.0 | 0.0 |
| gemma3-4b | c_markers_missing | 80 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | a_legend | 80 | 98.8 [96.2, 100.0] | 98.8 | 100.0 | 0.0 |
| gpt-6.1-terra | b_nolegend | 80 | 93.8 [87.5, 98.8] | 93.8 | 100.0 | 0.0 |
| gpt-6.1-terra | c_markers_missing | 79 | 98.7 [96.2, 100.0] | 97.5 | 98.8 | 1.2 |
| llama3.1-8b | a_legend | 80 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| llama3.1-8b | b_nolegend | 80 | 97.5 [93.8, 100.0] | 97.5 | 100.0 | 0.0 |
| llama3.1-8b | c_markers_missing | 80 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| qwen2.5-7b | a_legend | 79 | 98.7 [96.2, 100.0] | 97.5 | 98.8 | 1.2 |
| qwen2.5-7b | b_nolegend | 80 | 98.8 [96.2, 100.0] | 98.8 | 100.0 | 0.0 |
| qwen2.5-7b | c_markers_missing | 79 | 100.0 [100.0, 100.0] | 98.8 | 98.8 | 1.2 |

## Arm differences (paired by family x model), draw d1, pooled sources, affirmative share among committed

| model | contrast | difference pp [95% CI, family-cluster] | n pairs |
|---|---|---|---|
| ALL | b_nolegend - a_legend | -1.1 [-2.1, -0.3] | 731 |
| ALL | c_markers_missing - a_legend | +0.3 [-0.3, +0.8] | 727 |
| ALL | c_markers_missing - b_nolegend | +1.4 [+0.5, +2.3] | 731 |
| gemma3-4b | b_nolegend - a_legend | -0.5 [-2.7, +1.1] | 183 |
| gemma3-4b | c_markers_missing - a_legend | +0.5 [+0.0, +1.6] | 183 |
| gemma3-4b | c_markers_missing - b_nolegend | +1.1 [+0.0, +2.7] | 184 |
| gpt-6.1-terra | b_nolegend - a_legend | -2.2 [-4.4, -0.5] | 182 |
| gpt-6.1-terra | c_markers_missing - a_legend | +0.0 [-1.7, +1.7] | 179 |
| gpt-6.1-terra | c_markers_missing - b_nolegend | +2.2 [+0.6, +4.4] | 181 |
| llama3.1-8b | b_nolegend - a_legend | -1.1 [-3.3, +1.1] | 184 |
| llama3.1-8b | c_markers_missing - a_legend | +0.5 [+0.0, +1.6] | 184 |
| llama3.1-8b | c_markers_missing - b_nolegend | +1.6 [+0.0, +3.8] | 184 |
| qwen2.5-7b | b_nolegend - a_legend | -0.5 [-1.6, +0.0] | 182 |
| qwen2.5-7b | c_markers_missing - a_legend | +0.0 [+0.0, +0.0] | 181 |
| qwen2.5-7b | c_markers_missing - b_nolegend | +0.5 [+0.0, +1.6] | 182 |

### Commitment rate differences (share of valid outputs with a definite polarity)

| model | contrast | difference pp [95% CI, family-cluster] | n pairs |
|---|---|---|---|
| ALL | b_nolegend - a_legend | +0.7 [+0.1, +1.4] | 736 |
| ALL | c_markers_missing - a_legend | +0.0 [-0.7, +0.8] | 736 |
| ALL | c_markers_missing - b_nolegend | -0.7 [-1.5, -0.1] | 736 |
| gemma3-4b | b_nolegend - a_legend | +0.5 [+0.0, +1.6] | 184 |
| gemma3-4b | c_markers_missing - a_legend | +0.5 [+0.0, +1.6] | 184 |
| gemma3-4b | c_markers_missing - b_nolegend | +0.0 [+0.0, +0.0] | 184 |
| gpt-6.1-terra | b_nolegend - a_legend | +1.1 [+0.0, +2.7] | 184 |
| gpt-6.1-terra | c_markers_missing - a_legend | -0.5 [-2.7, +1.6] | 184 |
| gpt-6.1-terra | c_markers_missing - b_nolegend | -1.6 [-3.8, +0.0] | 184 |
| llama3.1-8b | b_nolegend - a_legend | +0.0 [+0.0, +0.0] | 184 |
| llama3.1-8b | c_markers_missing - a_legend | +0.0 [+0.0, +0.0] | 184 |
| llama3.1-8b | c_markers_missing - b_nolegend | +0.0 [+0.0, +0.0] | 184 |
| qwen2.5-7b | b_nolegend - a_legend | +1.1 [+0.0, +2.7] | 184 |
| qwen2.5-7b | c_markers_missing - a_legend | +0.0 [-1.6, +1.6] | 184 |
| qwen2.5-7b | c_markers_missing - b_nolegend | -1.1 [-2.7, +0.0] | 184 |

## Replication draw d2, pooled sources

| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|
| ALL | a_legend | 733 | 99.3 [98.6, 99.9] | 98.9 | 99.6 | 0.4 |
| ALL | b_nolegend | 736 | 98.6 [97.8, 99.3] | 98.6 | 100.0 | 0.0 |
| ALL | c_markers_missing | 733 | 99.9 [99.6, 100.0] | 99.5 | 99.6 | 0.4 |
| gemma3-4b | a_legend | 183 | 100.0 [100.0, 100.0] | 99.5 | 99.5 | 0.5 |
| gemma3-4b | b_nolegend | 184 | 99.5 [98.4, 100.0] | 99.5 | 100.0 | 0.0 |
| gemma3-4b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | a_legend | 184 | 98.4 [96.2, 100.0] | 98.4 | 100.0 | 0.0 |
| gpt-6.1-terra | b_nolegend | 184 | 98.4 [96.2, 100.0] | 98.4 | 100.0 | 0.0 |
| gpt-6.1-terra | c_markers_missing | 183 | 99.5 [98.4, 100.0] | 98.9 | 99.5 | 0.5 |
| llama3.1-8b | a_legend | 184 | 99.5 [98.4, 100.0] | 99.5 | 100.0 | 0.0 |
| llama3.1-8b | b_nolegend | 184 | 97.8 [95.7, 99.5] | 97.8 | 100.0 | 0.0 |
| llama3.1-8b | c_markers_missing | 184 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| qwen2.5-7b | a_legend | 182 | 99.5 [98.3, 100.0] | 98.4 | 98.9 | 1.1 |
| qwen2.5-7b | b_nolegend | 184 | 98.9 [97.3, 100.0] | 98.9 | 100.0 | 0.0 |
| qwen2.5-7b | c_markers_missing | 182 | 100.0 [100.0, 100.0] | 98.9 | 98.9 | 1.1 |


| model | contrast | difference pp [95% CI, family-cluster] | n pairs |
|---|---|---|---|
| ALL | b_nolegend - a_legend | -0.7 [-1.4, +0.0] | 733 |
| ALL | c_markers_missing - a_legend | +0.4 [+0.0, +1.0] | 731 |
| ALL | c_markers_missing - b_nolegend | +1.1 [+0.4, +1.9] | 733 |
| gemma3-4b | b_nolegend - a_legend | -0.5 [-1.6, +0.0] | 183 |
| gemma3-4b | c_markers_missing - a_legend | +0.0 [+0.0, +0.0] | 183 |
| gemma3-4b | c_markers_missing - b_nolegend | +0.5 [+0.0, +1.6] | 184 |
| gpt-6.1-terra | b_nolegend - a_legend | +0.0 [-1.6, +1.6] | 184 |
| gpt-6.1-terra | c_markers_missing - a_legend | +1.1 [+0.0, +2.7] | 183 |
| gpt-6.1-terra | c_markers_missing - b_nolegend | +1.1 [+0.0, +2.7] | 183 |
| llama3.1-8b | b_nolegend - a_legend | -1.6 [-4.3, +0.5] | 184 |
| llama3.1-8b | c_markers_missing - a_legend | +0.5 [+0.0, +1.6] | 184 |
| llama3.1-8b | c_markers_missing - b_nolegend | +2.2 [+0.5, +4.3] | 184 |
| qwen2.5-7b | b_nolegend - a_legend | -0.5 [-1.6, +0.0] | 182 |
| qwen2.5-7b | c_markers_missing - a_legend | +0.0 [+0.0, +0.0] | 181 |
| qwen2.5-7b | c_markers_missing - b_nolegend | +0.5 [+0.0, +1.6] | 182 |

## Original draw d0 (arm a only; reused cache)

| model | arm | n | affirmative share among committed [95% CI] | aff share of all valid | commitment rate | unclear share |
|---|---|---|---|---|---|---|
| ALL | a_legend | 733 | 99.6 [99.0, 100.0] | 99.2 | 99.6 | 0.4 |
| gemma3-4b | a_legend | 184 | 100.0 [100.0, 100.0] | 100.0 | 100.0 | 0.0 |
| gpt-6.1-terra | a_legend | 184 | 98.9 [97.3, 100.0] | 98.9 | 100.0 | 0.0 |
| llama3.1-8b | a_legend | 184 | 99.5 [98.4, 100.0] | 99.5 | 100.0 | 0.0 |
| qwen2.5-7b | a_legend | 181 | 100.0 [100.0, 100.0] | 98.4 | 98.4 | 1.6 |
