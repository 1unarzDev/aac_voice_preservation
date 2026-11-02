# Resample-without-feedback baseline (G1r) vs the commitment guard (G1)

Plan: [PLAN.md](PLAN.md) (written before any generation). Script: `src/guard_baseline.py`; runner `src/run_guard_baseline.sh`. Machine-scored partial predicates only; no usable-repair claim. 10,000 whole-family percentile bootstrap, seed 20261101, all arms resampled jointly; cue channels (chip1/chipall/full). Discovery excludes the quarantined act-10/act-16; W-C excludes r2act-078/079.

**Arms.** P0 first pass; G1 (feedback, T=0); G1s (strip-only); **G1r** (same monitor, trigger and 2-retry budget; retry = original prompt, no feedback, **T=0.7**, new seed per retry); **G1t** (G1's feedback conversation at G1r's T=0.7; isolates feedback). A T=0 no-feedback retry is the identical request and would just reproduce the first pass, so T=0.7 is the minimal change. It confounds G1-G1r with temperature, so the isolating contrast is G1t-G1r.

## Discovery set (guard1; 58 families x 4 models; 170 flagged requests)

1392 cue-channel targets. Levels in %, family-cluster 95% CI.

| arm | joint pass | strict pass | strict failures repaired | correct-text changed | pass->fail | residual strict failures |
|---|---|---|---|---|---|---|
| P0 | 94.68 [92.39, 96.70] | 94.25 [91.88, 96.41] | | | | |
| G1 | 98.85 [98.13, 99.50] | 98.78 [97.99, 99.50] | 63/80 = 78.75 [67.57, 89.13] | 14/1312 | 0 | 17 |
| G1s | 96.77 [95.26, 97.99] | 96.70 [95.19, 97.99] | 34/80 = 42.50 [29.17, 54.65] | 0/1312 | 0 | 46 |
| G1r | 95.62 [93.68, 97.34] | 95.33 [93.25, 97.20] | 15/80 = 18.75 [10.00, 30.12] | 3/1312 | 0 | 65 |
| G1t | 98.56 [97.77, 99.28] | 98.56 [97.77, 99.28] | 60/80 = 75.00 [64.58, 84.71] | 16/1312 | 0 | 20 |

Paired contrasts in percentage points (all targets; unflagged targets contribute 0), with counts of targets where only X / only Y passes:

| contrast (X-Y) | joint, pp [95% CI] | X-only / Y-only | strict, pp [95% CI] | X-only / Y-only |
|---|---|---|---|---|
| G1-G1r **(primary)** | +3.23 [1.87, 4.81] | 45 / 0 | +3.45 [2.01, 5.10] | 48 / 0 |
| G1t-G1r (isolates feedback) | +2.95 [1.65, 4.38] | 43 / 2 | +3.23 [1.80, 4.81] | 47 / 2 |
| G1-G1t | +0.29 [0.07, 0.57] | 4 / 0 | +0.22 [-0.07, 0.50] | 4 / 1 |
| G1-G1s | +2.08 [1.15, 3.16] | 30 / 1 | +2.08 [1.15, 3.16] | 31 / 2 |
| G1r-G1s | -1.15 [-2.08, -0.29] | 8 / 24 | -1.36 [-2.37, -0.43] | 8 / 27 |
| G1t-G1s | +1.80 [0.93, 2.73] | 26 / 1 | +1.87 [1.01, 2.87] | 27 / 1 |

On targets whose first pass the monitor flagged (n=96): joint pass P0 26.0% -> G1 86.5%, G1s 56.2%, G1r 39.6%, G1t 82.3%.
Ambiguous channels, politeness added (%): P0 10.1, G1 0.0, G1s 0.4, G1r 7.3, G1t 0.0.

Requests (flagged unique requests; retries stop at the first unflagged output):

| arm | generation calls | unflagged after guard | first retry already unflagged | a retry reproduced the original text | final text changed |
|---|---|---|---|---|---|
| G1 | 215 | 143/170 | 125 |  | 145 |
| G1s | 0 | 92/170 |  |  |  |
| G1r | 309 | 34/170 | 31 | 111 | 37 |
| G1t | 213 | 142/170 | 127 | 18 | 144 |

## W-C transfer set (78 families x 4 models; 508 flagged requests)

1872 cue-channel targets. Levels in %, family-cluster 95% CI.

| arm | joint pass | strict pass | strict failures repaired | correct-text changed | pass->fail | residual strict failures |
|---|---|---|---|---|---|---|
| P0 | 78.79 [76.23, 81.41] | 74.47 [71.26, 77.78] | | | | |
| G1 | 88.62 [86.91, 90.38] | 87.87 [86.00, 89.80] | 251/478 = 52.51 [48.36, 56.70] | 26/1394 | 0 | 227 |
| G1s | 82.26 [80.29, 84.35] | 81.73 [79.59, 83.92] | 136/478 = 28.45 [25.49, 31.15] | 0/1394 | 0 | 342 |
| G1r | 82.43 [80.02, 84.83] | 79.11 [76.18, 82.05] | 87/478 = 18.20 [14.74, 21.84] | 12/1394 | 0 | 391 |
| G1t | 89.37 [87.71, 91.03] | 89.05 [87.34, 90.81] | 273/478 = 57.11 [53.03, 61.36] | 26/1394 | 0 | 205 |

Paired contrasts in percentage points (all targets; unflagged targets contribute 0), with counts of targets where only X / only Y passes:

| contrast (X-Y) | joint, pp [95% CI] | X-only / Y-only | strict, pp [95% CI] | X-only / Y-only |
|---|---|---|---|---|
| G1-G1r **(primary)** | +6.20 [4.75, 7.64] | 157 / 41 | +8.76 [6.94, 10.58] | 209 / 45 |
| G1t-G1r (isolates feedback) | +6.94 [5.34, 8.60] | 171 / 41 | +9.94 [7.96, 11.91] | 229 / 43 |
| G1-G1t | -0.75 [-1.55, 0.05] | 27 / 41 | -1.18 [-2.14, -0.27] | 28 / 50 |
| G1-G1s | +6.36 [5.29, 7.48] | 123 / 4 | +6.14 [4.91, 7.43] | 128 / 13 |
| G1r-G1s | +0.16 [-0.85, 1.18] | 66 / 63 | -2.62 [-4.06, -1.28] | 66 / 115 |
| G1t-G1s | +7.10 [5.98, 8.28] | 136 / 3 | +7.32 [6.09, 8.60] | 145 / 8 |

On targets whose first pass the monitor flagged (n=511): joint pass P0 22.9% -> G1 58.9%, G1s 35.6%, G1r 36.2%, G1t 61.6%.

Requests (flagged unique requests; retries stop at the first unflagged output):

| arm | generation calls | unflagged after guard | first retry already unflagged | a retry reproduced the original text | final text changed |
|---|---|---|---|---|---|
| G1 | 766 | 282/508 | 225 |  | 301 |
| G1s | 0 | 129/508 |  |  |  |
| G1r | 952 | 99/508 | 64 | 351 | 107 |
| G1t | 782 | 302/508 | 234 | 128 | 321 |

## Reading

1. Resampling without feedback (G1r) gives about the strip-only gain on W-C and no more: joint +3.63 pp vs G1s +3.47, and it repairs 18.2% of strict failures (G1s 28.5%, G1 52.5%). On the discovery set G1r is +0.93 pp, below G1s (+2.08). G1r leaves added-politeness failures in place (strict pass is well below joint pass) because a fresh sample often adds 'please' again.
2. Feedback adds value beyond resampling on both sets. G1-G1r joint is +3.23 pp [1.87, 4.81] (discovery) and +6.20 pp [4.75, 7.64] (W-C). Under matched decoding G1t-G1r is +2.95 [1.65, 4.38] and +6.94 [5.34, 8.60]. The lower bounds are above 0 on both sets and both endpoints, so the PLAN.md decision rule is met.
3. Temperature is not what separates G1 from G1r: G1t (feedback at T=0.7) is about as good as G1 (G1-G1t joint +0.29 [0.07, 0.57] discovery, -0.75 [-1.55, 0.05] W-C).
4. Strict pass->fail is 0 in every arm on both sets (joint: 2 for G1s on W-C). Correct-text changes: 14/1,312 (G1), 3 (G1r), 16 (G1t) on discovery; 26, 12, 26 of 1,394 on W-C.
5. Many G1r retries just reproduce the original text (111 of 170 and 351 of 508 flagged requests had a retry identical to the original), so the small models are nearly deterministic even at T=0.7. A higher temperature or more retries might help G1r; that was not tried, for budget parity with G1.

## Caveats

- G1 and G1s outputs and labels are the existing ones (the script reproduces the published W-C +9.83 pp, 251/478 repairs and 26/1,394 changed-correct). G1r/G1t outputs were scored with the same judge pipeline; unchanged texts inherit baseline labels.
- 2 (discovery) and 7 (W-C) new A-units had no existing critical resolution. They were arbitrated blind from the output text and the production question only (Claude, procedure of runs/hw1/arbiter.jsonl). The W-C 'Will you ...?' calls (question) are judgment calls; decisions are in runs/guard_baseline_*/arbiter_new.jsonl. No label fell back to J1/J2.
- Exploratory: one retry seed per attempt, a single run, and the API is not reproducible. The flagged set is defined by G1's first-pass trigger. Repaired-text completeness, fluency and usefulness are not validated. The retry decoding differs from G1 (T=0.7 vs 0); see PLAN.md. No arm was tuned after seeing outcomes.

## Resources

Generation calls (logical; all fresh, 0 errors, 0 cache hits): discovery 522 (G1r 309, G1t 213), W-C 1,734 (G1r 952, G1t 782); total 2,256 of the 2,712 upper bound. By model across both sets: terra 274, qwen 412, llama 785, gemma 785. Judge batch calls: 22 (4 discovery, 18 W-C; concurrency 8; 0 failed). New arbiter API calls: 0 (9 A-units decided by Claude, blind). Local models ran one server at a time under flock /tmp/aacv_gpu.lock after legend1 SEQDONE; terra ran at concurrency 4.

Files: `summary.json`, `arm_metrics.csv`, `contrasts.csv`, `cost.csv`, `scored_{disc,wc}.parquet`, `paired_{disc,wc}_{G1,G1s,G1r,G1t}.parquet`, `inventory.json`. Reproduce: `python src/guard_baseline.py analyze` after the runs in `runs/guard_baseline_{disc,wc}`.
