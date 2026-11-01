# W-C guard transfer: formal acceptance audit (cycle 3)

Date: **2026-11-01**. Auditor: cycle-3 Action 3 worker (Claude). The audit is read-only. It makes **0 generation, 0 judge and 0 network calls**. Reproduce it with `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/acceptance_check.py`, which writes [`acceptance_check.json`](acceptance_check.json). The designated verifier `verify_results.py` (including its closure-comparator checks) was also re-run and passes ([`verification.json`](verification.json)).

## Verdict: **ACCEPT WITH QUALIFICATIONS**

The frozen transfer result in [`report.md`](report.md) / [`headline.json`](headline.json) is accepted as **PASS on the scored partial-predicate endpoint**. Its ledger ID is **C37**: this row was the second one labelled C36, and D-045 renumbers it, leaving C36 as the first-output diagnostic. Every frozen budget, concurrency and wall-clock limit in [`FREEZE.md`](FREEZE.md) was met. All 18 result hashes match. Every headline count was recomputed from `paired_G1.parquet` / `paired_G1s.parquet`. The baseline-parity failure was a false alarm caused by dtype alone, and no baseline value differs. The qualifications below concern provenance statements and operating guidance. None of them changes a number or a criterion.

| Check | Frozen limit | Observed (source) | Status |
|---|---|---|---|
| Retry-generation HTTP calls | ≤2,000 (and ≤2F = 1,016) | **766** = 726 HTTP 200 + 40 failed (20×429, 15×502, 5×524); 766 logical guard attempts = Σ G1 `extra_calls` = `logical_calls.jsonl` rows. G1s used 0 calls. `actual_calls.csv` ≡ `budget.sqlite` row for row | within |
| Judge-batch HTTP calls | ≤400 | **207** = 34 successful + 173 failed (165×429, 5×503, 3×524) | within |
| Wall clock | ≤4 h from launch 18:31:49 UTC | last instrumented call ended **1.00 h** after launch (19:31:53 UTC); all calls inside the window | within |
| API generation concurrency | 8 (ceiling 12) | gpt-6.1-terra peak **8** | within |
| Judge concurrency | 12 (ceiling 12) | gpt-6.1-sol peak **12**, both before the resume (12:34 local) and during it (13:29 local) | within frozen; **above the later ≤8 operating limit** |
| Local inference | 4 slots, one server at a time | peak 4 per model; non-overlapping windows qwen 5–17 s, llama 23–41 s, gemma 47–68 s | within |
| Baseline parity (1,872 P0 rows × text, crit, 5 general dims, constraint_preserving) | frozen W-C labels unchanged | **0 value differences** before and after the resume | holds |
| Transfer criteria | repair ≥30%; changed-correct ≤10%; joint-gain lower bound >0 | 251/478 = 52.51% [48.36, 56.70]; 26/1,394 = 1.87% [1.16, 2.64]; +9.83 pp [8.39, 11.32] | all pass |

## Qualifications (append-only corrections)

1. **The "937 calls" figure is wrong as a generation count.** D-042 and decision memo Action 1 quote it, but no stored artifact equals 937. Generation used **766** retry HTTP calls. Before the 13:28 resume, the instrumented calls were 766 generation + 170 judge batches, all of which failed (165×429, 5×503), for **936**. 937 is most plausibly that all-call total off by one. Treat it as unsupported. The correct totals are 766 generation / 207 judge / 973 instrumented HTTP calls.
2. **Concurrency.** The run stayed within its frozen limits (API generation 8, judge 12). The judge ran at 12 in both windows, which exceeds the ≤8 codex-lb concurrency later requested for cycle-3 workers. Disclose this as an operating deviation, not a protocol violation.
3. **One uninstrumented API request.** The resume script `orchestration/guard_wc_resume.sh` sent a readiness probe (`"hi"` to gpt-6.1-sol) outside the budget ledger. The first resumed judge batch began 61 s after the 13:28 gate, and a failed probe would have added a 120 s sleep, so exactly one probe ran. It is not a judge batch, and even counted against the judge cap the total is 208 ≤ 400.
4. **Why the baseline-parity assertion failed earlier.** The first runner ended with `J2/B: … 240 still missing` (165 of its 170 judge batches got HTTP 429), yet still printed `GUARD_WC_COMPLETE`. At that point **164 G1 and 82 G1s rows** lacked `constraint_preserving`. The whole-frame column therefore held `None` and became dtype `object`, and the P0 slice inherited that dtype. `pandas.Series.equals` checks dtype, so `AssertionError: constraint_preserving` fired even though **no P0 value differed**. After the resumed judging filled every label, the column is all-known `bool` and the original, unmodified assertion holds. D-044 ("missing judgments") and `closure_audit.json` ("dtype-only bool versus object") describe the same event from two sides. The completion marker alone was insufficient evidence of a completed evaluation.
5. **Label residue.** 10 critical J units (26 target rows) remain unresolved. None is a selected critical unknown, so every planned target is known and all denominators are 1,872/1,872. There were 0 new arbiter calls. 49 general-label disagreement fields keep the frozen agreement/L0 rule, and 0 joint outcomes change under agreement-only scoring.
6. **Scope.** This PASS is machine-scored partial-predicate transfer on 78 W-C speech-act families. Repaired-text completeness, fluency and usefulness are unvalidated (`usable_repair_validated=false`), and H7 does not cover new repairs. The strip-only comparator gives G1−G1s joint **+6.36 pp [5.29, 7.48]** (123 G1-only vs 4 G1s-only passes). That is exploratory and supports no causal feedback claim. The early-cache and post-outcome-arbitration qualifications of the frozen W-C baseline carry over.

The ledger corrections are appended as **C37** in `orchestration/claims_ledger.md`, and the decision-log correction as **D-045** in `orchestration/decision_log.md`. The earlier rows remain unedited.
