# T6: small-cluster inference for hw1 (writer = cluster; stored data only, 0 generation / 0 judge calls)

Script `src/robust_t6_small_cluster.py` (items ['data/items/hw.jsonl'], runs ['runs/hw1']). Loaders/frames reused from `src/analyze_hw1.py`. Rerun with hw2: `python src/robust_t6_small_cluster.py --items data/items/hw.jsonl data/items/hw2.jsonl --runs runs/hw1 runs/hw2 --name hw12`. Seed 20261101.

Estimates are pooled row-weighted means (as in `analyze_hw1.py`), in percentage points; P3 is the bare affirmative share minus 50 pp. `t` = CR1 cluster-robust SE with t(writers-1); `writer-mean t` = unweighted mean of writer means; `wild` = wild-cluster bootstrap-t (Rademacher exact over all 2^G patterns; Webb 6-point, 19,999 draws); sign-flip = exact writer-level randomization test, one-sided, whose smallest possible p is 1/2^G.

## Intervals (pp)

| contrast | writers | rows | estimate | stored percentile bootstrap | t (CR1) | writer-mean t | wild Rademacher | wild Webb |
|---|---|---|---|---|---|---|---|---|
| P1 | 6 | 536 | +35.3 | [31.2, 40.3] | [28.9, 41.7] | [28.9, 41.8] | [29.0, 41.5] | [27.4, 43.1] |
| P2 | 6 | 356 | +7.6 | [5.0, 10.4] | [3.7, 11.5] | [3.7, 11.5] | [3.5, 11.7] | [3.5, 11.7] |
| P3 | 7 | 414 | +49.8 | [49.3, 50.0] | [49.2, 50.4] | [49.1, 50.4] | [49.3, 50.2] | [49.3, 50.2] |

## p-values

| contrast | t two-sided | Holm(t) | wild Rademacher two-sided (min attainable) | wild Webb two-sided | sign-flip one-sided (min attainable) | Holm(sign-flip) | stored bootstrap Holm |
|---|---|---|---|---|---|---|---|
| P1 | 0.0000 | 0.0001 | 0.0312 (0.0312) | 0.0035 | 0.0156 (0.0156) | 0.0312 | 0.0003 |
| P2 | 0.0042 | 0.0042 | 0.0312 (0.0312) | 0.0120 | 0.0156 (0.0156) | 0.0312 | 0.0003 |
| P3 | 0.0000 | 0.0000 | 0.0156 (0.0156) | 0.0000 | 0.0078 (0.0078) | 0.0234 | 0.0003 |

## Writer-level means (pp) and leave-one-writer-out

**P1**: writer means P01 +32.1 (n=112), P03 +29.2 (n=72), P04 +39.8 (n=88), P08 +31.2 (n=112), P14 +34.4 (n=64), P15 +45.5 (n=88); effective writers 5.76; largest writer 21% of rows; leave-one-out estimates +33.3 to +36.3; t-CI excludes 0 in every leave-one-out: True; all writer signs positive: True.

**P2**: writer means P02 +5.0 (n=60), P04 +6.7 (n=60), P11 +13.3 (n=60), P12 +3.3 (n=60), P16 +6.7 (n=60), P18 +10.7 (n=56); effective writers 6.00; largest writer 17% of rows; leave-one-out estimates +6.4 to +8.4; t-CI excludes 0 in every leave-one-out: True; all writer signs positive: True.

**P3**: writer means P05 +50.0 (n=60), P07 +50.0 (n=59), P09 +48.2 (n=55), P14 +50.0 (n=60), P17 +50.0 (n=60), P18 +50.0 (n=60), P19 +50.0 (n=60); effective writers 6.99; largest writer 14% of rows; leave-one-out estimates +49.7 to +50.0; t-CI excludes 0 in every leave-one-out: True; all writer signs positive: True.

## Per-model estimates (pp, t df = writers-1) and heterogeneity

| contrast | model | estimate | t CI | t p (2-sided) | sign-flip p (1-sided) | all writer means > 0 |
|---|---|---|---|---|---|---|
| P1 | gemma3-4b | +36.6 | [24.3, 48.8] | 0.001 | 0.016 | True |
| P1 | gpt-6.1-terra | +50.7 | [38.6, 62.8] | 0.000 | 0.016 | True |
| P1 | llama3.1-8b | +18.7 | [5.6, 31.7] | 0.014 | 0.031 | False |
| P1 | qwen2.5-7b | +35.1 | [27.3, 42.9] | 0.000 | 0.016 | True |
| P1 | heterogeneity (within-family model-label permutation, 9999 draws) | SS=6.93 | | p=0.0001 | | |
| P2 | gemma3-4b | +22.5 | [12.4, 32.5] | 0.002 | 0.016 | True |
| P2 | gpt-6.1-terra | +6.7 | [2.3, 11.2] | 0.012 | 0.031 | False |
| P2 | llama3.1-8b | +1.1 | [-1.8, 4.0] | 0.362 | 0.500 | False |
| P2 | qwen2.5-7b | +0.0 | [0.0, 0.0] | nan | 1.000 | False |
| P2 | heterogeneity (within-family model-label permutation, 9999 draws) | SS=2.86 | | p=0.0001 | | |
| P3 | gemma3-4b | +50.0 | [50.0, 50.0] | nan | 0.008 | True |
| P3 | gpt-6.1-terra | +50.0 | [50.0, 50.0] | nan | 0.008 | True |
| P3 | llama3.1-8b | +49.0 | [46.7, 51.4] | 0.000 | 0.008 | True |
| P3 | qwen2.5-7b | +50.0 | [50.0, 50.0] | nan | 0.008 | True |
| P3 | heterogeneity (within-family model-label permutation, 9999 draws) | SS=0.01 | | p=1.0000 | | |

## Caveats

* With G = 6-7 writers per contrast, every method here is conditional on very few clusters; the exact sign-flip test cannot return p below 1/2^G (about .016 one-sided for 6 writers), so Holm p = .0003 from the percentile bootstrap is a resampling floor rather than evidence at that level; the number to quote is the smallest attainable p when all writer signs agree.
* Writer-clustering does not remove family or item dependence inside a writer; family counts per writer vary and one writer can dominate rows (see effective writers).
* Writers were volunteers working to a protocol; P06's speech-act pair is excluded as in `analyze_hw1.py`; no hw preregistration exists, so all inference is exploratory.
* The heterogeneity test permutes model labels within family blocks (models see the same inputs) and tests equality of pooled model means, not writer-by-model interactions.
