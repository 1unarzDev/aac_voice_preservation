# W-C guard transfer: prospective Action 6 freeze

Written 2026-11-01T18:28:32.106254+00:00, before any Action 6 retry or judge call. The read-only feasibility
preview used the stored first passes only. D-040 and the user's November 1 instruction
authorize an early launch; the memo's November 11–15 window is superseded for timing.
Core W-B/W-C/W-D evidence and the partial repair endpoint are reviewable. CALE-AI only;
do not change paper/ or the SE4All evidence. No policy tuning, additional arms or items.

## Inventory and policy

W-C r2c1 P0 speech-act families, excluding D-018 r2act-078/079: **78 families × 2 targets
× 4 fixed models × chip1/chipall/full = 1,872 target occurrences** before missing-label
exclusions. All occurrences remain in the planned denominator. Deduplicate generation
by original request_key; clip each request's targets to this inventory, even when its
representative family belongs to another stratum. Re-render and assert the original
request key. Reuse the exact stored first sentence and its raw conversation response.

**UNCHANGED G1** from frozen src/interventions.py: supplied() and check() (layer0 plus
number/time add-on), unsupplied-politeness rule, feedback(), guard_one(), temperature 0,
96 output tokens, seed 1000 for local models (API has no seed), tag I1-guard-v1.
Up to two monitor-triggered regeneration calls. Return the first unflagged candidate,
otherwise fewest flags, earliest on ties (original wins a tie). Empty originals remain
missing/failed without generation. **G1s** uses the unchanged strip_please() rule only
when initial politeness:added and please/pls/plz are present; zero generation calls.
No I2 run. A wrapper may restrict inventory, instrument costs and enforce caps; it
must not alter these functions, prompts, monitor thresholds, or return logic.

## Endpoint and missingness

Primary = **joint supplied-predicate pass**, src/analyze.normalize_table's
constraint_preserving: valid completion, focal match, and no contradicted supplied
general predicate. Known failures dominate missingness; otherwise a needed missing
label yields unknown. Source specifications, not the monitor's source interpretation,
define evaluation. This is a partial contract, not fluency or full semantics. Secondary
strict pass additionally requires no added politeness; this is the previous guard's
repair/changed-correct endpoint. Report both, without switching after outcomes.

Reuse cached J1/J2 evaluation and existing r2c1 arbiter decisions by their production
unit (normalized text, critical question/options, with input where needed). Never
substitute J1. **New critical J1/J2 disagreements are recorded as unresolved**, with
zero new arbiter calls. General labels retain the frozen production agreement/L0
tie-break rule, disclosed with counts and agreement-only sensitivity. No new labels
may replace a frozen baseline label. First-pass baseline retains the completed W-C
arbitration and its chronology qualifications. Preserve missing/error outcomes and
report observed/planned denominators, paired known units and worst/best missingness
bounds. New missing general labels may not silently count as passes.

Compare P0/G1/G1s on identical target occurrences, with paired gains, repair rates,
changed-correct, pass→fail, residual failures and flags, per-model and per-channel.
Primary uncertainty: **10,000 whole-family percentile bootstrap resamples**, seed
20261101, retaining every model/target/channel/arm of a sampled family jointly.
Companion recorded seed/construction-cluster bootstrap (55 clusters) handles shared
W-C templates/seeds; report it alongside the required 78-family bootstrap. Fixed
roster, row-weighted means, pointwise 95% intervals; no population/model inference.

## Audit and examples (selection frozen before retries)

If audit capacity becomes available, select 20 distinct G1 changed texts and 20
unchanged baseline-strict-correct controls by ascending SHA256 of normalized text,
breaking ties by model, family, variant, channel; first collapse exact normalized
texts, retaining all memberships and inclusion counts. Repairs cannot be selected
by judged success. Freeze the resulting sample before any human labels; provide
sentence-only blind completeness and separately paired supplied-constraint review.
No new human time is allocated and no usable-repair claim without new independent
quality evidence. Do not reuse main1 H7 as repair validation.

Examples, if shown: first SHA256(base_request_key, family, variant, channel) in each
predeclared category: strict fail→pass, residual strict failure, correct-text-changed,
pass→fail, G1s fail→pass (one per category, absent categories reported). Quote actual
stored outputs verbatim, output IDs, selection key, and the category's full rate.
These are selected illustrations, never typicality claims.

## Fixed budget, admission, and kill rules

**Across all models: ≤2,000 actual retry-generation HTTP calls; ≤400 actual judge
batch HTTP calls including network/invalid-batch retries; ≤4 h wall clock from the
recorded launch timestamp (including GPU-lock wait).** No automatic HTTP retries
for generation; a failed call consumes its allocated guard attempt and returns the
earliest best available output. Judge transport retries are disabled; any explicit
batch retry consumes the shared cap. Cache hits consume no HTTP calls. Count logical
guard attempts, cache hits, actual requests, failures and latency separately.

Compute F over flagged unique stored first-pass requests with the frozen monitor.
If **2F > 2,000, defer the entire experiment**, without selecting failures/models.
The conservative four-pass judge plan is 4 ceil(2F/25), with actual G1s/cache needs
inventoried before judging and ≤400 enforced for all traffic. If that fixed full
evaluation exceeds budget, report incompleteness; no favorable subset substitution.
Launch long work with setsid nohup. GPU mutex: flock /tmp/aacv_gpu.lock; **one local
server at a time** through src/run_interventions.sh; local 4 slots, CTX 1024, full GPU
layers where available. API concurrency 8 (≤12), judge concurrency 12 (≤12).

Transfer success requires ALL: **≥30% strict failures repaired; ≤10% initially
strict-correct texts changed; positive paired joint-pass gain with lower 95% family
bootstrap bound >0**. Also report joint failure repair and joint-correct edits.
Insufficient evidence/unfinished evaluation cannot earn success. Failure is negative
transfer evidence, never an invitation to tune. Even a pass licenses only scored
predicate transfer; usable-repair requires independent quality evidence on new repairs.

## Hashes and immutable evidence

input_hashes.json records SHA256 for every frozen source/data file, copied byte-for-byte
under frozen/. Its SHA256 is `9a4514c388edecc3e303c94eec9428f22485ab7cb3647d3d00db2c52231bdb2a`.
The machine-readable request/target inventory, monitor replay and admission decision
are written next, before retry launch, and separately hashed in inventory_hashes.json.
An additional launch_manifest.json freezes the completed wrapper/runner/analysis code
before any retries. This file is not regenerated after observing repairs.
