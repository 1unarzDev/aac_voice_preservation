# Seeded-fault sweep of the harness: plan (written before any mutant was run)

Task B1 of the SE4All plan. Question: if the harness code were wrong in a specific way, would the
existing self-tests notice? This replaces the inventory of two self-found defects with a seeded-fault
sweep. Everything is CPU only; no API calls, no GPU, no generation, no judging.

## Subject and isolation
* Mutated code: `src/attribute.py`, `src/labels.py`, `src/judge.py`, `src/build_requests.py`, `src/prompts.py`,
  `src/oracle_wa.py`, `src/validate_cue_inputs.py`, `src/layer0.py`, `src/runio.py`, `src/explode.py`, `src/analyze.py`.
* Each mutant lives in its own temp copy `tmp/sf/<mutant>/` (copy of `src/`, `tests/`, `prompts/`; data directories are
  symlinked read-only, `runs/fixture` and `analysis/robust` are private real directories because tests write there).
  The real `src/` is never modified; the real tree is checked for changes (git status) before and after the sweep.
* Mutations are exact, single-site (one or two literal substitutions) source edits applied by `src/seeded_faults.py`.
  A mutation must change the file, must match its target text exactly once, and must `py_compile`. A mutant that fails
  these generator checks is a bug in the generator, is fixed, and is never swapped out for outcome reasons.
  No mutant is added, dropped or replaced after test outcomes are seen.

## Mutation classes (declared from the code structure, not from the defect history)
Each class is one structural role in the harness; each operator is applied at several sites of that role.
Operators: negate a condition (drop `not`, flip `==`/`!=`, `and`<->`or`), swap two constants or keys, drop a clause or
branch, widen/narrow a set, swap argument order, replace a key/field by its sibling.

| class | structural role | files | n |
|---|---|---|---|
| K1 verdict rules | Violation/Assumption/commit/chose/constraint-preserving, stance additions, arbiter precedence | attribute.py | 10 |
| K2 channel-to-commitment mapping | which dimensions a channel gives; cue vs ambiguous channel sets; chip -> general-dimension table; spec defaults | attribute.py, labels.py | 10 |
| K3 judge post-processing | J1/J2 agreement rule, arbiter routing, layer0 tiebreak, general-dimension and added-content assembly | judge.py | 6 |
| K4 input builder | chip set per channel, chip order, typed-sentence channel, noncritical insertion, request key, dedupe of identical renders | build_requests.py, prompts.py | 8 |
| K5 oracle acceptance | critical_match relaxations (plain~emphatic, acceptance~statement), final equality, the oracle's own contract verdict | labels.py, oracle_wa.py | 7 |
| K6 cue validator | accepted/required sets, relation rules, verdict assignment, politeness word rules | validate_cue_inputs.py | 8 |
| K7 deterministic labeler | layer0 certainty/polarity/speech-act rules used for the tiebreak and stance reference | layer0.py | 3 |
| K8 data plumbing and aggregation | occurrence validity, text normalisation, rate/duplicate/quarantine handling, bootstrap estimate, paired difference direction | runio.py, explode.py, attribute.py, analyze.py | 6 |

Total 58 mutants (inside the 40-60 target). The concrete site list is the `MUTATIONS` table in `src/seeded_faults.py`
(its sha256 is recorded in `summary.json`).

## Tests run on every mutant (all existing self-tests, nothing written for the sweep except the harness glue)
Columns of the kill matrix:
1. `pytest tests/` (74 tests, 16 files). Reported per test file and pooled (`pytest_all`). The `tests/*.js` HTML-front-end
   tests are not run: they exercise `annotation_package/*.html`, which no mutant touches.
2. `oracle_identity`: re-score `runs/oracle_inject` with the production `attribute.score` (+ label resolution) and compare the
   120 identity rows (critical, critical_source, critical_match, raw_match, violation, constraint_preserving, contradicted dims,
   general dims, added_content) with the frozen `analysis/oracle/injection_results.csv`.
3. `oracle_injection`: the same for the 120 scoped-mutation rows (detection = Violation).
4. `oracle_challenge`: re-score the 72 keyed challenge sentences (frozen keys, sha256 check of the key files, production
   critical_match, raw rule, label/general agreement, gate verdict) against frozen `analysis/oracle/challenge_results.csv`.
5. `validator_r5_replay`: `validate_cue_inputs.replay()` (its internal assertions: 139/139 audit agreement, 7/7 known conflicts
   rejected, 8 SURE-coarse flagged, 0 coarse certified) plus equality of `replay.csv`/`replay.json` with the frozen
   `analysis/r5_validator/`.
6. `validator_t9_replay`: `robust_t9_validator_replay.main()` over W-C, W-D and hw1 rendered inputs vs stored request files,
   `summary.json` equal to the frozen `analysis/robust/t9_validator_replay/summary.json`.
7. `rescore_frozen_endpoints`: re-score stored runs with `attribute.score` + `attribute.endpoints` and require exact equality
   with each frozen `runs/<run>/endpoints.json`. The run list and the per-run option (none / fallback / resolution) are fixed
   from the clean baseline, which must reproduce every frozen file.
Supplementary column (not an existing self-test, added by this sweep and reported separately, never in the headline):
8. `request_rebuild`: rebuild stored request files (`runs/requests/*`) from the item files with `build_requests` and require the
   same request keys, rendered inputs and target lists. It exists to show what an input-builder replay would add.

## Kill criterion
A test kills a mutant iff the test FAILS (assertion, mismatch with frozen output, exception, timeout, collection error) on the
mutant AND PASSES on the clean code. Clean baseline is run first through the identical pipeline; every column must pass,
otherwise the sweep stops. Kills by crash/exception are recorded and reported separately from kills by a failing comparison
or assertion (a crash is detection, but a weaker form).

## Scores
* mutation score per test = mutants killed by that test / all mutants (58); pooled score = mutants killed by at least one
  existing test (columns 1-7) / 58. Per-test-file pytest columns are subsets of `pytest_all`.
* Survivors count against the score. After the run every survivor gets an individual explanation. A survivor is called
  *equivalent* only with positive evidence (the mutated line is not reachable from any stored data or code path any test
  exercises, or it changes nothing observable); the report gives the score both with all survivors counted and with
  demonstrated equivalents removed, and labels which is which. The headline is the strict one.
* 95% Wilson intervals for the pooled score.
