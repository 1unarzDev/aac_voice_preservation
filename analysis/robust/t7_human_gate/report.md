# T7: human-gate recomputation (stored labels; 0 generation / 0 judge calls)

Script `src/robust_t7_human_gate.py`; tables `kappa_by_rule.csv`, `kappa_by_model_channel.csv`; `summary.json`. Internals from `src/score_gold.py`. Judge FINAL label vs human reference, unweighted Cohen kappa; CIs are family-cluster bootstrap (2,000 resamples).

R0 = stored rule (plurality; ties and unsure/blank excluded; reproduces the stored `sampled_test/final` kappa). R1 = ties and items with no usable human label count as disagreement. R2 = R1 and each unsure/blank answer is an UNSURE vote that can win. 'test' = the seeded 25/75 split used for the gate; 'all' = all sampled items.

## main1_H7_A1A2

Annotators ['A1', 'A2']; 163 sampled items (121 in the test split); coders per item {2: 76, 1: 87}.

| dimension | stored test kappa | test R0 (n) | test R1 (n) [CI] | test R2 (n) [CI] | all R1 (n) [CI] | no-consensus refs in test R1 | human-human kappa [CI] | judge-human kappa [CI] | difference [CI] |
|---|---|---|---|---|---|---|---|---|---|
| critical | 0.947 | 0.947 (119) | 0.930 (121) [0.863, 0.982] | 0.930 (121) [0.863, 0.982] | 0.942 (163) [0.887, 0.985] | 2 | 0.972 [0.928, 1.000] | 0.916 [0.832, 0.981] | -0.056 [-0.130, 0.000] |
| polarity | 0.956 | 0.956 (121) | 0.956 (121) [0.815, 1.000] | 0.956 (121) [0.815, 1.000] | 0.967 (163) [0.870, 1.000] | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| speech_act | 0.941 | 0.941 (118) | 0.901 (121) [0.834, 0.960] | 0.901 (121) [0.834, 0.960] | 0.911 (163) [0.857, 0.958] | 3 | 1.000 [1.000, 1.000] | 0.903 [0.816, 0.976] | -0.097 [-0.184, -0.024] |
| agent | 0.913 | 0.913 (117) | 0.880 (120) [0.803, 0.943] | 0.880 (120) [0.803, 0.943] | 0.903 (162) [0.838, 0.957] | 3 | 0.959 [0.891, 1.000] | 0.915 [0.827, 0.979] | -0.044 [-0.130, 0.028] |
| certainty | 0.909 | 0.909 (119) | 0.881 (121) [0.780, 0.965] | 0.881 (121) [0.780, 0.965] | 0.879 (163) [0.794, 0.950] | 2 | 1.000 [1.000, 1.000] | 0.878 [0.766, 0.976] | -0.122 [-0.234, -0.024] |
| politeness | 0.972 | 0.972 (121) | 0.972 (121) [0.908, 1.000] | 0.972 (121) [0.908, 1.000] | 0.977 (163) [0.924, 1.000] | 0 | 1.000 [1.000, 1.000] | 0.950 [0.808, 1.000] | -0.050 [-0.192, 0.000] |
| added_content | 0.906 | 0.906 (107) | 0.890 (108) [0.800, 0.962] | 0.890 (108) [0.800, 0.962] | 0.890 (145) [0.811, 0.954] | 1 | 0.969 [0.898, 1.000] | 0.922 [0.817, 1.000] | -0.047 [-0.155, 0.031] |

## main1_parts1-3_P02P10P14

Annotators ['P02', 'P10', 'P14']; 163 sampled items (121 in the test split); coders per item {3: 163}.

| dimension | stored test kappa | test R0 (n) | test R1 (n) [CI] | test R2 (n) [CI] | all R1 (n) [CI] | no-consensus refs in test R1 | human-human kappa [CI] | judge-human kappa [CI] | difference [CI] |
|---|---|---|---|---|---|---|---|---|---|
| critical | NA | 0.947 (121) | 0.947 (121) [0.907, 0.982] | 0.947 (121) [0.907, 0.982] | 0.942 (163) [0.903, 0.974] | 0 | 0.918 [0.881, 0.950] | 0.926 [0.888, 0.957] | 0.008 [-0.017, 0.029] |
| polarity | NA | 0.956 (121) | 0.956 (121) [0.815, 1.000] | 0.956 (121) [0.815, 1.000] | 0.967 (163) [0.870, 1.000] | 0 | 0.838 [0.677, 0.955] | 0.904 [0.788, 0.976] | 0.066 [0.013, 0.125] |
| speech_act | NA | 0.942 (121) | 0.942 (121) [0.886, 0.987] | 0.942 (121) [0.886, 0.987] | 0.944 (163) [0.881, 0.989] | 0 | 0.954 [0.920, 0.983] | 0.921 [0.858, 0.966] | -0.033 [-0.100, 0.018] |
| agent | NA | 0.855 (120) | 0.855 (120) [0.771, 0.924] | 0.855 (120) [0.771, 0.924] | 0.884 (162) [0.821, 0.937] | 0 | 0.906 [0.860, 0.946] | 0.884 [0.834, 0.927] | -0.022 [-0.071, 0.017] |
| certainty | NA | 0.909 (121) | 0.909 (121) [0.835, 0.974] | 0.909 (121) [0.835, 0.974] | 0.901 (163) [0.828, 0.962] | 0 | 0.897 [0.846, 0.942] | 0.893 [0.828, 0.948] | -0.004 [-0.060, 0.040] |
| politeness | NA | 0.946 (121) | 0.946 (121) [0.864, 1.000] | 0.946 (121) [0.864, 1.000] | 0.955 (163) [0.887, 1.000] | 0 | 0.956 [0.903, 1.000] | 0.962 [0.913, 1.000] | 0.006 [-0.004, 0.023] |
| added_content | NA | 0.794 (108) | 0.794 (108) [0.663, 0.898] | 0.794 (108) [0.663, 0.898] | 0.762 (145) [0.647, 0.865] | 0 | 0.408 [0.304, 0.507] | 0.593 [0.509, 0.677] | 0.185 [0.108, 0.260] |

## part12_elic

Annotators ['P03', 'P08', 'P13', 'P19']; 161 sampled items (115 in the test split); coders per item {4: 161}.

| dimension | stored test kappa | test R0 (n) | test R1 (n) [CI] | test R2 (n) [CI] | all R1 (n) [CI] | no-consensus refs in test R1 | human-human kappa [CI] | judge-human kappa [CI] | difference [CI] |
|---|---|---|---|---|---|---|---|---|---|
| critical | 0.980 | 0.980 (109) | 0.925 (115) [0.874, 0.971] | 0.925 (115) [0.874, 0.971] | 0.907 (161) [0.863, 0.951] | 6 | 0.989 [0.976, 0.999] | 0.968 [0.939, 0.991] | -0.021 [-0.049, 0.002] |
| polarity | 1.000 | 1.000 (115) | 1.000 (115) [1.000, 1.000] | 1.000 (115) [1.000, 1.000] | 1.000 (161) [1.000, 1.000] | 0 | 0.983 [0.942, 1.000] | 0.992 [0.971, 1.000] | 0.009 [0.000, 0.029] |
| speech_act | 0.984 | 0.984 (108) | 0.885 (115) [0.808, 0.952] | 0.885 (115) [0.808, 0.952] | 0.893 (160) [0.831, 0.949] | 7 | 0.989 [0.974, 1.000] | 0.969 [0.930, 0.998] | -0.020 [-0.060, 0.009] |
| agent | 0.893 | 0.893 (112) | 0.872 (114) [0.797, 0.938] | 0.872 (114) [0.797, 0.938] | 0.842 (160) [0.770, 0.908] | 2 | 0.918 [0.875, 0.956] | 0.896 [0.844, 0.943] | -0.022 [-0.054, 0.004] |
| certainty | 0.918 | 0.918 (113) | 0.888 (115) [0.800, 0.962] | 0.888 (115) [0.800, 0.962] | 0.860 (161) [0.777, 0.932] | 2 | 0.930 [0.884, 0.969] | 0.916 [0.862, 0.958] | -0.014 [-0.060, 0.022] |
| politeness | 1.000 | 1.000 (115) | 1.000 (115) [1.000, 1.000] | 1.000 (115) [1.000, 1.000] | 0.975 (161) [0.926, 1.000] | 0 | 0.984 [0.950, 1.000] | 0.988 [0.963, 1.000] | 0.004 [0.000, 0.012] |
| added_content | 0.901 | 0.901 (101) | 0.872 (102) [0.738, 0.969] | 0.872 (102) [0.738, 0.969] | 0.818 (141) [0.687, 0.925] | 1 | 0.873 [0.776, 0.941] | 0.851 [0.736, 0.934] | -0.022 [-0.103, 0.033] |

## part13_hw

Annotators ['P04', 'P15', 'P20']; 152 sampled items (110 in the test split); coders per item {3: 152}.

| dimension | stored test kappa | test R0 (n) | test R1 (n) [CI] | test R2 (n) [CI] | all R1 (n) [CI] | no-consensus refs in test R1 | human-human kappa [CI] | judge-human kappa [CI] | difference [CI] |
|---|---|---|---|---|---|---|---|---|---|
| critical | 0.940 | 0.940 (109) | 0.931 (110) [0.868, 0.981] | 0.931 (110) [0.868, 0.981] | 0.922 (152) [0.865, 0.969] | 1 | 0.995 [0.984, 1.000] | 0.940 [0.893, 0.975] | -0.055 [-0.102, -0.020] |
| polarity | 1.000 | 1.000 (110) | 1.000 (110) [1.000, 1.000] | 1.000 (110) [1.000, 1.000] | 1.000 (152) [1.000, 1.000] | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| speech_act | 1.000 | 1.000 (108) | 0.964 (110) [0.910, 1.000] | 0.964 (110) [0.910, 1.000] | 0.961 (152) [0.912, 1.000] | 2 | 0.990 [0.967, 1.000] | 0.995 [0.983, 1.000] | 0.005 [0.000, 0.016] |
| agent | 1.000 | 1.000 (110) | 1.000 (110) [1.000, 1.000] | 1.000 (110) [1.000, 1.000] | 0.991 (152) [0.970, 1.000] | 0 | 0.987 [0.965, 1.000] | 0.984 [0.959, 1.000] | -0.003 [-0.027, 0.014] |
| certainty | 0.946 | 0.946 (110) | 0.946 (110) [0.880, 1.000] | 0.946 (110) [0.880, 1.000] | 0.949 (152) [0.892, 0.988] | 0 | 0.987 [0.964, 1.000] | 0.962 [0.915, 0.998] | -0.025 [-0.068, 0.004] |
| politeness | 1.000 | 1.000 (110) | 1.000 (110) [1.000, 1.000] | 1.000 (110) [1.000, 1.000] | 1.000 (152) [1.000, 1.000] | 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| added_content | 0.838 | 0.838 (83) | 0.692 (91) [0.541, 0.833] | 0.692 (91) [0.541, 0.833] | 0.735 (125) [0.613, 0.853] | 8 | 0.731 [0.599, 0.845] | 0.815 [0.716, 0.892] | 0.084 [0.000, 0.168] |

## Per-model and per-channel kappa (critical field, R1, all sampled items; other fields in `kappa_by_model_channel.csv`)

| gate | group | value | n | kappa | acc | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|
| main1_H7_A1A2 | model | gemma3-4b | 43 | 0.900 | 0.907 | 0.778 | 1.000 |
| main1_H7_A1A2 | model | gpt-6.1-terra | 41 | 0.974 | 0.976 | 0.917 | 1.000 |
| main1_H7_A1A2 | model | llama3.1-8b | 44 | 0.927 | 0.932 | 0.834 | 1.000 |
| main1_H7_A1A2 | model | qwen2.5-7b | 49 | 0.978 | 0.980 | 0.926 | 1.000 |
| main1_H7_A1A2 | channel | bare | 26 | 0.956 | 0.962 | 0.854 | 1.000 |
| main1_H7_A1A2 | channel | chip1 | 42 | 0.900 | 0.905 | 0.799 | 0.975 |
| main1_H7_A1A2 | channel | chipall | 36 | 0.970 | 0.972 | 0.907 | 1.000 |
| main1_H7_A1A2 | channel | full | 28 | 0.962 | 0.964 | 0.882 | 1.000 |
| main1_H7_A1A2 | channel | noncrit | 32 | 0.929 | 0.938 | 0.823 | 1.000 |
| main1_parts1-3_P02P10P14 | model | gemma3-4b | 43 | 0.925 | 0.930 | 0.826 | 1.000 |
| main1_parts1-3_P02P10P14 | model | gpt-6.1-terra | 41 | 0.921 | 0.927 | 0.814 | 1.000 |
| main1_parts1-3_P02P10P14 | model | llama3.1-8b | 44 | 0.927 | 0.932 | 0.834 | 1.000 |
| main1_parts1-3_P02P10P14 | model | qwen2.5-7b | 49 | 1.000 | 1.000 | 1.000 | 1.000 |
| main1_parts1-3_P02P10P14 | channel | bare | 26 | 1.000 | 1.000 | 1.000 | 1.000 |
| main1_parts1-3_P02P10P14 | channel | chip1 | 42 | 0.925 | 0.929 | 0.826 | 1.000 |
| main1_parts1-3_P02P10P14 | channel | chipall | 36 | 0.970 | 0.972 | 0.904 | 1.000 |
| main1_parts1-3_P02P10P14 | channel | full | 28 | 0.923 | 0.929 | 0.805 | 1.000 |
| main1_parts1-3_P02P10P14 | channel | noncrit | 32 | 0.892 | 0.906 | 0.747 | 1.000 |
| part12_elic | model | gemma3-4b | 50 | 0.913 | 0.920 | 0.827 | 0.979 |
| part12_elic | model | gpt-6.1-terra | 31 | 1.000 | 1.000 | 1.000 | 1.000 |
| part12_elic | model | llama3.1-8b | 44 | 0.950 | 0.955 | 0.874 | 1.000 |
| part12_elic | model | qwen2.5-7b | 36 | 0.761 | 0.778 | 0.637 | 0.889 |
| part12_elic | channel | human | 161 | 0.907 | 0.913 | 0.860 | 0.953 |
| part12_elic | channel | pos_cap4 | 24 | 0.952 | 0.958 | 0.860 | 1.000 |
| part13_hw | model | gemma3-4b | 57 | 0.941 | 0.947 | 0.866 | 1.000 |
| part13_hw | model | gpt-6.1-terra | 29 | 0.960 | 0.966 | 0.867 | 1.000 |
| part13_hw | model | llama3.1-8b | 36 | 0.938 | 0.944 | 0.842 | 1.000 |
| part13_hw | model | qwen2.5-7b | 30 | 0.819 | 0.833 | 0.661 | 0.948 |
| part13_hw | channel | bare | 34 | 0.824 | 0.853 | 0.655 | 0.964 |
| part13_hw | channel | chip1 | 31 | 0.860 | 0.871 | 0.675 | 1.000 |
| part13_hw | channel | chipall | 25 | 0.912 | 0.920 | 0.771 | 1.000 |
| part13_hw | channel | full | 20 | 1.000 | 1.000 | 1.000 | 1.000 |
| part13_hw | channel | noncrit | 42 | 1.000 | 1.000 | 1.000 | 1.000 |

## Notes and caveats

* R1/R2 can only lower kappa relative to R0: they add reference categories the judge cannot match. The size of the drop shows how much of the gate rests on excluded ties/unsure answers.
* For main1 H7 (two annotators, 100 double-coded, 87 single-coded) a tie is any disagreement on a double-coded item; there is no third vote. Human-human kappa on the double-coded items is therefore the natural ceiling for judge-human kappa.
* Human-human kappa pools all annotator pairs per item; judge-human kappa pools the judge against each member of those same pairs (so it is computed on identical items). Both are family-cluster resampled together for the difference.
* main1 channel/model are recovered from `runs/main1/scored.parquet` by text_id (a text can occur in several channels/models and is then counted in each); elic/hw use the key columns (`model`, `channels`; human_* channels pooled as 'human').
* All gates cover untreated outputs of the stored inventories only; annotators were taught the same codebook as the judge (see CODEBOOK.md).
* The machine panel (`main1_sens_sol_astra`) is not a human reference and is not recomputed here.
