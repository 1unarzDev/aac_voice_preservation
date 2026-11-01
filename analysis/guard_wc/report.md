# W-C speech-act guard transfer (cycle-2 Action 6)

**PASS: frozen guard transfers on the scored partial predicate endpoint.**

This is the single optional CALE-AI guard-transfer experiment, launched early under D-040 and the user instruction. No guard/prompt tuning, new models, extra families or I2 generation. The prior discovery guard result is a separate population.

## Prospective freeze, inventory and endpoint

FREEZE.md and its SHA256 `987f464b0432119986b60f1b49c38c0e6b5f4423b888ca80a9e6bd812a873cd8` precede all retry requests; launch_manifest.json freezes the adapter/analysis code. Frozen inputs, first passes and labels are byte-preserved under frozen/. 78 speech-act families, two variants, four fixed models, three cue channels (chip1/chipall/full): **1,872 target occurrences / 1,848 unique requests**. D-018 excludes r2act-078/079. **F=508; 2F=1,016 ≤2,000**, so the full design was admitted; the memo judge formula gives 164 initial batches before cache reuse.

G1 and G1s call the unchanged src/interventions.py policy functions. G1 uses at most two monitor-triggered retries; first unflagged else fewest flags, earliest on ties. G1s only strips unsupplied please/pls/plz. The monitor never sees evaluation labels. Generation uses temperature 0, local seed 1000, 96 tokens; local serving is one llama.cpp server at a time under flock /tmp/aacv_gpu.lock, 4 slots × 1024 context, NGL=99; API concurrency 8 and judge concurrency 12. All long work launched with setsid nohup.

Primary joint pass is the existing analyze.normalize_table constraint-preserving endpoint: focal value and all other scored supplied predicates, with missing needed labels unknown unless a known failure dominates. Strict pass also prohibits politeness addition and supplies the earlier guard's repair/changed-correct criteria. Numbers below are machine-scored partial predicates. Neither sentence completeness nor full meaning nor communicative usefulness is certified.

## Paired P0 / G1 / G1s

Rates and pointwise 95% percentile intervals in percent; n=observed/planned eligible target occurrences. 10,000 whole-family resamples, seed 20261101, paired arms/models/channels retained jointly. No resampling of models and no multiplicity claim.

| arm | joint supplied-predicate pass | strict pass | focal match | politeness added |
|---|---|---|---|---|
| P0 | 78.79 [76.23, 81.41] (n=1872/1872) | 74.47 [71.26, 77.78] (n=1872/1872) | 82.43 [80.45, 84.51] (n=1872/1872) | 9.08 [7.43, 10.79] (n=1872/1872) |
| G1 | 88.62 [86.91, 90.38] (n=1872/1872) | 87.87 [86.00, 89.80] (n=1872/1872) | 88.89 [87.23, 90.60] (n=1872/1872) | 0.96 [0.53, 1.50] (n=1872/1872) |
| G1s | 82.26 [80.29, 84.35] (n=1872/1872) | 81.73 [79.59, 83.92] (n=1872/1872) | 82.32 [80.34, 84.40] (n=1872/1872) | 0.64 [0.32, 1.01] (n=1872/1872) |

Paired differences in percentage points. Repair rates condition on initial strict failures; changed-correct and pass→fail condition on initial strict passes. Unknown returned labels remain unknown. The conservative repair criterion counts only known returned passes over **all** known initial failures, including unresolved returned outcomes in its denominator.

| arm | joint-pass gain, pp | strict failures repaired | correct-text changed | pass→fail | residual strict failures |
|---|---|---|---|---|---|
| G1 | 9.83 [8.39, 11.32] (n=1872/1872) | 251/478; 52.51 [48.36, 56.70] (n=478/478) | 26/1394; 1.87 [1.16, 2.64] (n=1394/1394) | 0/1394; 0.00 [0.00, 0.00] (n=1394/1394) | 227/1872; 12.13 [10.20, 14.00] (n=1872/1872) |
| G1s | 3.47 [2.78, 4.22] (n=1872/1872) | 136/478; 28.45 [25.49, 31.15] (n=478/478) | 0/1394; 0.00 [0.00, 0.00] (n=1394/1394) | 0/1394; 0.00 [0.00, 0.00] (n=1394/1394) | 342/1872; 18.27 [16.08, 20.41] (n=1872/1872) |

## Transfer criteria

| fixed criterion | result | passes |
|---|---|---|
| strict repairs ≥30% (conservative full initial-failure denominator) | 52.51 [48.36, 56.70] (n=478/478) | True |
| initially strict-correct text changed ≤10% | 1.87 [1.16, 2.64] (n=1394/1394) | True |
| paired joint-pass gain lower 95% bound >0 | 9.83 [8.39, 11.32] (n=1872/1872) pp | True |
| completed fixed design / resource cap | True / True | True |

Failure of any criterion is negative transfer, not a tuning invitation. The old human extraction gate H7 passed on the main1 inventory; it does not independently validate new repairs. No usable-repair rate is claimed.

## Per-model and channel effects

| model | P0 joint | G1 joint | G1s joint | G1−P0 joint, pp | G1 strict repair | G1 correct-text changed | G1 pass→fail |
|---|---|---|---|---|---|---|---|
| gemma3-4b | 70.94 [66.03, 75.64] (n=468/468) | 89.96 [87.39, 92.52] (n=468/468) | 84.40 [81.62, 87.18] (n=468/468) | 19.02 [15.38, 22.86] (n=468/468) | 128/177; 72.32 [67.22, 77.46] (n=177/177) | 3/291 | 0/291 |
| gpt-6.1-terra | 93.38 [90.60, 95.94] (n=468/468) | 94.23 [91.45, 96.79] (n=468/468) | 93.59 [91.03, 95.94] (n=468/468) | 0.85 [0.21, 1.71] (n=468/468) | 21/59; 35.59 [23.81, 49.06] (n=59/59) | 1/409 | 0/409 |
| llama3.1-8b | 68.16 [64.32, 72.01] (n=468/468) | 84.40 [80.98, 87.82] (n=468/468) | 68.38 [64.53, 72.22] (n=468/468) | 16.24 [13.25, 19.44] (n=468/468) | 87/161; 54.04 [46.33, 61.94] (n=161/161) | 20/307 | 0/307 |
| qwen2.5-7b | 82.69 [79.06, 86.32] (n=468/468) | 85.90 [82.69, 89.10] (n=468/468) | 82.69 [79.06, 86.32] (n=468/468) | 3.21 [1.92, 4.70] (n=468/468) | 15/81; 18.52 [11.39, 25.88] (n=81/81) | 2/387 | 0/387 |

| channel | P0 joint | G1 joint | G1s joint | G1−P0 joint, pp |
|---|---|---|---|---|
| chip1 | 73.24 [69.39, 76.92] (n=624/624) | 81.41 [78.04, 84.62] (n=624/624) | 72.92 [69.07, 76.76] (n=624/624) | 8.17 [5.93, 10.58] (n=624/624) |
| chipall | 66.51 [61.86, 71.15] (n=624/624) | 85.10 [81.89, 88.14] (n=624/624) | 74.68 [71.15, 78.21] (n=624/624) | 18.59 [15.71, 21.63] (n=624/624) |
| full | 96.63 [94.87, 98.08] (n=624/624) | 99.36 [98.72, 99.84] (n=624/624) | 99.20 [98.40, 99.84] (n=624/624) | 2.72 [1.60, 4.01] (n=624/624) |

Full per-model/channel endpoint, harm and missingness estimates: stratified_effects.csv and headline.json.

## Unknowns, scoring and cluster sensitivity

Frozen P0 labels are retained exactly. An unchanged output reuses its baseline labels. Existing W-C arbitration may be reused only on the same production A-unit (text ID, critical dimension and options). All new critical J1/J2 disagreements are recorded in unresolved.jsonl and receive no J1 fallback or new arbitration. General labels retain production J1/J2 agreement, otherwise the existing layer0 tie-break; agreement-only sensitivity below removes this source of dependence. Known contradictions dominate missingness; unknowns are never silently promoted to passes.

New unresolved critical J-units: **10**; distinct A-units: **10**. The target counts below may repeat an extraction decision.

- P0: critical unknown 0; joint unknown 0; strict unknown 0; invalid 0.
- G1: critical unknown 0; joint unknown 0; strict unknown 0; invalid 0.
- G1s: critical unknown 0; joint unknown 0; strict unknown 0; invalid 0.
- G1−P0 joint gain over all planned targets: identification bound [9.83, 9.83] pp (not a CI). Recorded seed/construction-cluster bootstrap: 9.83 [8.03, 11.63] (n=1872/1872) pp, 55 clusters. Initial strict failures with unknown returned labels: 0; initial passes with unknown returned labels: 0.
- G1s−P0 joint gain over all planned targets: identification bound [3.47, 3.47] pp (not a CI). Recorded seed/construction-cluster bootstrap: 3.47 [2.53, 4.43] (n=1872/1872) pp, 55 clusters. Initial strict failures with unknown returned labels: 0; initial passes with unknown returned labels: 0.
- General-label agreement-only sensitivity, G1 joint gain: 9.83 [8.39, 11.32] (n=1872/1872) pp. New critical disagreements remain unresolved in this sensitivity.
- General-label agreement-only sensitivity, G1s joint gain: 3.47 [2.78, 4.22] (n=1872/1872) pp. New critical disagreements remain unresolved in this sensitivity.

W-C's early-cache and post-outcome baseline arbitration qualifications travel with this transfer. The new retry freeze is prospective, but cannot repair the original baseline chronology. Family bootstrap is the requested primary uncertainty; shared recorded clusters are reported as a companion. No independent quality audit or W-C-specific human source validation is created here.

## Monitor, residual flags and resource use

G1 residual flags: **226/1,848 unique returned requests**. Among 227 known residual strict target failures, **215** remain flagged; 226/1,872 returned target occurrences carry any flag. Flags are monitor diagnostics, not measured warning benefit.

Actual HTTP calls: **766 generation** / 2,000; **207 judge batches** / 400 (all failures/retries included); **0 new arbitration**. Logical guard attempts 766, cache hits 0, logical errors 40. Actual extra calls/input 0.4145, /flagged input 1.5079. Elapsed through analysis 3605.3 s / 14,400 s.

| model | inputs | initially flagged | logical attempts / actual calls | residual flagged unique | extra stored latency s/input | flagged median s | monitor median ms |
|---|---|---|---|---|---|---|---|
| gemma3-4b | 462 | 177 | 234 / 234 | 40 | 0.175 | 0.322 | 2.24 |
| gpt-6.1-terra | 462 | 62 | 77 / 77 | 40 | 0.354 | 1.421 | 2.39 |
| llama3.1-8b | 462 | 185 | 293 / 293 | 78 | 0.155 | 0.350 | 2.23 |
| qwen2.5-7b | 462 | 84 | 162 / 162 | 68 | 0.096 | 0.405 | 2.26 |

Latency is the sum of per-call generation service times, not total elapsed wall time; concurrent calls overlap. Stored latency includes the original cost of cached retry responses; actual HTTP duration and cache counts are separate in headline.json and actual_calls.csv. First-pass historical latency is excluded. G1s uses zero model calls. Hardware-specific latency is not an AAC deployment prediction.

## Declared-rule examples (selected, not typical)

Each row below is the first SHA256([base_request_key, family, variant, channel]) in its pre-frozen event category. Exact output/input strings are joined to stored run outputs; category rates accompany them. No quality-based filtering.

- **strict fail→pass** (251/478 target occurrences), llama3.1-8b, r2act-069/B, chipall. Input: `Keywords: [ASK] [YOU] [PLAIN] send photos`. P0: "You send photos." → G1: "Send photos.". IDs `d9b35be4ca0120bc` → `6cdacfa409328293`.
- **residual strict failure** (227/1872 target occurrences), gemma3-4b, r2act-063/A, chipall. Input: `Keywords: [?] [YOU] email manager`. P0: "Can you send me an email?" → G1: "Can you send me an email?". IDs `06000cc0bbdbb0ab` → `f76cb85386066cf2`.
- **correct-text-changed** (26/1394 target occurrences), qwen2.5-7b, r2act-073/A, chipall. Input: `Keywords: [?] [I] bring friend`. P0: "Is it okay if I bring a friend?" → G1: "Is [I] bring a friend?". IDs `9caa8acf1f9a3671` → `2e6854997dd20399`.
- **pass→fail**: absent (0/1394).
- **G1s strict fail→pass** (136/478 target occurrences), llama3.1-8b, r2act-022/B, chip1. Input: `Keywords: [ASK] put dishes`. P0: "Can you please put the dishes?" → G1s: "Can you put the dishes?". IDs `1526ba270dc60f5c` → `786648e106163a97`.

## Audit and reproducibility

audit_sample.csv applies the pre-frozen text-hash selection to 20 distinct changed G1 texts and 20 unchanged baseline-correct controls (all eligible counts and memberships in audit_manifest.json). HUMAN fields are empty; selection is deterministic, not a probability sample, and no representative usable-repair percentage follows. No human time was allocated or consumed by this run.

Reproduce locally: `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/analyze.py --exit-code 0`. Do not rerun prepare.py or launch to manufacture a retrospective freeze. Frozen inputs and wrapper code hashes are recorded before launch; final output hashes are in result_hashes.json. paired_G1/G1s.parquet retain all target transitions; scored.parquet retains all three arms; residual flags and attempt traces are in runs/guard_wc/generations.jsonl. Resource records include every HTTP attempt without secrets.

