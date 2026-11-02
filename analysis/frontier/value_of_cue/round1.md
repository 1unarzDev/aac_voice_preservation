# value_of_cue, round 1 (Stage 0 pilot: CPU only, 0 model calls, 0 judge calls) -- PROVISIONAL

Plan: `PLAN.md` (+ Amendment A1, written after the unit table and T2 gate but before any policy or frontier outcome was computed).
Scripts: `src/frontier_value_of_cue_units.py`, `src/frontier_value_of_cue_stage0.py`, `src/frontier_value_of_cue_fig.py`. Seed 20261102, 2,000 bootstrap resamples per mode. Log: `runs/frontier_value_of_cue_stage0.log` (empty: results are in the CSVs).
Data: 1,800 units (600 messages x 3 human keyword sets, 20 writers), HT-weighted exactly as in T2; outcomes from the 4 stored P0 models (arbitrated labels, no J1 fallback), averaged over models.
Labels are detector source labels and machine-arbitrated output labels. NOT human validation. Provisional until Part 21 (source check) and the frontier annotation check are scored.

## 0. What was run and what was NOT
Run: Stage 0 (unit table, T2 consistency gate, keyword-feature policy P-K with nested writer-and-message-disjoint CV, frontier vs baselines, cluster bootstrap, sensitivity, per-dimension, CRC on 500 writer x message splits).
NOT run (needs GPU, API or other data; deferred): Stage 1 internal signals (P-I), Stage 2 external detector (P-X), B6 entropy-gated baseline (closest published method), hw1 shift test, hw2 confirmation, any human annotation. Therefore **H2 and H4 are OPEN**, and no claim about internal vs external signals can be made from this round. The ANNOTATION_REQUEST.md items were not built (the plan builds them after Stage 3 freezes the policy; they would use this P-K policy if kept).

## 1. Consistency gate (T2): PASSED
Polarity 23.9 / 1,000 (T2 23.9), speech act 162.0 (161.9), politeness 49.4 (49.4); spurious 0.8 / 62.5 / 75.2 match; per-model polarity 23.9 / 23.5 / 24.2 / 23.9 identical to the T2 table.
New dimensions (same construction, not in T2): certainty 24.4 reversals + 13.5 spurious per 1,000; agent 198.5 reversals (spurious undefined, set 0). Agent and certainty "reversals" include detector-vs-judge label disagreement and are the least trustworthy; headline numbers are given with and without them.
Commit-error burden under the status quo (B0): **451.9 SLP-weighted errors per 1,000 messages** (610 raw error events per 1,000; weights NEG 1.0, ACT .8, AGT .8, CRT .7, POL .5). Per dimension weighted: polarity 24.7, speech act 179.6, politeness 62.3, certainty 26.5, agent 158.8.

## 2. Can keywords alone predict where a cue was dropped? (AUROC, held-out blocks, writer-and-message-disjoint)
| dimension | prior (HT) | AUROC S1 [95% CI] | ECE |
|---|---|---|---|
| polarity | 2.5% | 0.60 [0.43, 0.75] | 0.009 |
| speech act | 22.5% | 0.71 [0.66, 0.76] | 0.036 |
| politeness | 12.5% | 0.65 [0.59, 0.71] | 0.031 |
| certainty | 3.8% | 0.59 [0.45, 0.71] | 0.011 |
| agent | 19.8% | 0.59 [0.53, 0.66] | 0.040 |
Gate G0 (S1 AUROC <= 0.55 on ALL dimensions and no gain over B1) is NOT triggered: speech act, politeness and agent have CIs above 0.5. For polarity (the highest-severity, rarest error) and certainty the CI includes 0.5: keyword features do not reliably flag negation loss.

## 3. Frontier on held-out blocks (one prompt per message at most; SHOW-TWO = 1 tap, ASK-ONE-CUE = 2 taps)
SLP-weighted errors averted, as a share of the B0 burden (451.9 / 1,000). 95% CI = widest of writers-x-messages, writers-only, messages-only bootstrap. B1 has no CI (its relative value is a fixed fraction of B0 by construction).
| taps / 1,000 messages | P-K | B5 prior-only | B1 random | oracle (upper bound) | P-K minus B1 [CI] | P-K minus B5 [CI] |
|---|---|---|---|---|---|---|
| 20 | 1.6% [0.6, 2.4] | 0.7% | 0.4% | 4.0% | +1.2 pp [0.3, 2.0] | +0.9 pp [-0.1, 1.6] |
| 50 | 3.1% [2.0, 4.6] | 1.8% | 0.9% | 8.9% | +2.2 pp [1.1, 3.7] | +1.3 pp [0.2, 2.8] |
| 100 | 5.6% [4.0, 7.5] | 3.6% | 1.8% | 16.8% | +3.8 pp [2.2, 5.7] | +2.0 pp [0.4, 3.8] |
| 200 | 11.0% [8.3, 13.5] | 7.2% | 3.6% | 32.8% | +7.4 pp [4.7, 9.9] | +3.8 pp [1.3, 6.1] |
| 400 | 21.0% [17.4, 24.5] | 14.3% | 7.2% | 56.3% | +13.8 pp [10.2, 17.3] | +6.7 pp [3.6, 9.5] |
In AAC terms at 100 taps per 1,000 messages (about one prompt per 20 messages): P-K averts 25.3 weighted errors (31.7 raw error events) per 1,000 messages; B5 averts 16.2; B1 8.1. Taps per error event averted: P-K 3.2, B5 4.9, B1 9.1, oracle 1.1.
Fixed baselines (all 5 dimensions, no one-action cap): B2 always-ask: 10,000 taps / 1,000 messages, residual 47.0 weighted errors (floor from rho < 1); B4 always-show-two: 5,000 taps, residual 45.2; B3 always-ask polarity only: 2,000 taps, averts only 24.5 of 451.9 (polarity is 5% of the burden).
**H1 verdict: PARTIAL.** The policy beats random-ask (CI excludes 0 at every budget) and prior-only (CI excludes 0 at T = 50, 100, 200, 400; at T = 20 it includes 0), but the reduction at T = 100 is 5.6% [4.0, 7.5], far below the 25% SUCCESS line. Per-message keyword signal is real but modest; most of the value at low budgets comes from the prior (B5 is already 2x B1), and the oracle shows that a perfect risk signal would avert 3x more. Figure: `fig_frontier.png`.
Honest reading: at a realistic 50-100 taps / 1,000 messages a keyword-only policy removes roughly 3-6% of the SLP-weighted silent errors. Large reductions require far more prompts (21% at 400 taps) or a better signal (Stage 1/2, not yet run).

## 4. Where it does NOT help (H5, descriptive; per-dimension runs, point estimates, no per-dimension CIs)
Weighted errors averted per 1,000 at T = 50 (P-K vs random B1 vs oracle; dimension burden): polarity 1.9 vs 0.2 vs 24.4 (24.7); speech act 16.0 vs 1.6 vs 36.0 (179.6); politeness 1.7 vs 0.6 vs 22.5 (62.3); certainty 2.3 vs 0.2 vs 23.9 (26.5); agent 5.6 vs 1.4 vs 36.0 (158.8).
* Polarity: the single-dimension oracle could remove almost all 24.7 per 1,000 with 50 taps, but S1 AUROC is 0.60 with CI including 0.5, so P-K captures only 8% of it at T = 50 and 18% at T = 100. Keywords do not tell us which dropped negations to ask about; blanket polarity asking (B3, 2,000 taps) removes 24.5.
* Politeness: at T = 20 P-K (0.12) is below random B1 (0.22): not helped at very low budgets.
* Speech act: largest absolute gain (16.0 at T = 50) but 179.6 burden and a coin-flip prior: unresolved even at 400 taps.
* Agent and certainty: weak/noisy labels (see section 1); treat as exploratory.
* Excluding certainty and agent (weight 0): P-K reaches 10.1% at T = 100 (P-K minus B1 [5.5, 11.4] pp); still below 25%.

## 5. Sensitivity (P-K relative reduction at T = 100; P-K minus B1 CI excludes 0 in every setting at T = 100)
SLP1 weights 5.4%, SLP2 5.8%, uniform 4.9%; q = 0.7: 4.3%, q = 1.0: 6.1%; rho = 1: 5.6%; spurious weight x0.5: 4.6%, x2: 7.0%; per-model outcomes qwen 6.3%, llama 4.2%, gemma 5.6%, terra 6.4% (llama at T = 50: P-K minus B1 [0.0, 2.6] pp, includes 0 marginally). 300 random SLP weight vectors in [0.2, 1]: P-K > B1 in 99.3%, P-K > B5 in 74.7%, P-K relative reduction median 4.9% (min 1.7%). Conclusion (P-K beats random; modest size) is stable across SLP1, SLP2, uniform and random weights. P-K vs prior-only B5 is the less stable comparison (75% of random weight vectors).
Spurious-loss sensitivities re-score the outcome on the same fitted P (no refit).

## 6. Distribution-free guarantee (CRC; 500 random splits, 10 writers x half of messages calibrate, the other 10 writers x other half test; independent per-dimension decisions at one lambda, up to 5 prompts per message)
H3 original targets alpha = 5, 10, 20 per 1,000: **INFEASIBLE** (always-ask floor is 47.0; CRC returns the most conservative lambda, risk 25.5 on the test blocks because asks are confined to the policy's own action set, violating every target). Amended targets (A1):
| alpha | policy | mean test risk | split violation rate | taps / 1,000 | 
|---|---|---|---|---|
| 100 | P-K | 92.7 | 35% | 2,763 |
| 100 | B5 prior-only | 81.3 | 20% | 3,462 |
| 100 | B1 random show-two | 91.9 | 27% | 4,431 |
| 150 | P-K | 142.1 | 36% | 1,982 |
| 150 | B5 | 115.0 | 28% | 2,606 |
| 150 | B1 random show-two | 142.6 | 35% | 3,811 |
| 250 | P-K | 241.4 | 39% | 1,059 |
| 250 | B5 | 150.1 | 1% | 1,988 |
| 250 | B1 random show-two | 244.2 | 42% | 2,569 |
**H3 verdict on amended targets: SUCCESS as pre-declared** (mean test risk <= alpha for all three; P-K needs fewer taps than B1 and than B5 at the same alpha, ~38% fewer than B1 at alpha = 100). Caveats: CRC controls the mean, not each split (35-39% of splits exceed alpha, as expected near the boundary); the cost is 1-3 prompts per message, i.e. these risk levels are NOT reachable with a handful of taps; B5's discrete dimension ladder overshoots at alpha = 250 (risk 150), so the tap comparison there favours P-K partly through B5's granularity; calibration units are HT-weighted and the exchangeability across 20 writers is thin. B2 always-ask (10,000 taps) is dominated. Shift to hw1 (3c) not run.

## 7. Zero-tap alternative (B7, from stored results, not re-run)
Guard G1 converts failures to passes at no tap cost (D-068); not re-estimated on these units and not comparable here (different population). Stage 3 should show the combination "G1 then policy" on hw1.

## 8. Problems / caveats
1. Outcome labels are machine/detector labels; agent/certainty are noisy; polarity prevalence in the HT frame (2.5% of units are polarity errors) leaves only 75 positive units so polarity AUROC CI is wide.
2. rho and q are simulated, not measured on users; taps are a proxy for motor effort, not time.
3. The prior B5 and the HT base rates were computed on all 1,800 units (a mild optimism for B5, not for P-K whose predictions are out-of-block).
4. Held-out frontier uses a single global lambda grid on pooled out-of-block predictions; the CRC section calibrates lambda properly.
5. First launch of the script with default BLAS threading thrashed on the loaded machine; relaunched with OMP_NUM_THREADS=1 (no change in results; the 100-resample test and the 2,000-resample run agree to the third decimal).
6. B6 (the closest published method) is missing, so no claim of beating published approaches.
Next round: Stage 1 on qwen2.5-7b (greedy logprobs + K samples + yes/no probes) under the GPU lock, Stage 2 gpt-6.1-sol keywords-only detector, B6, H2/H4.

Files: units.parquet, stage0_frontier_budgets.csv, stage0_fixed_baselines.csv, stage0_calibration_auroc.csv, stage0_perdim.csv, stage0_sensitivity.csv, stage0_crc.csv, stage0_curves.json, stage0_summary.json, P_K_oof.npy, fig_frontier.png.
