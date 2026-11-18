# Seeded-fault sweep, round 2 (same 58 mutants, new regression tests)

Round 1 (`report.md`, `summary.json`, `kill_matrix.csv`, `mutant_results.json`) is unchanged. Round 2 outputs: `round2_summary.json`, `round2_kill_matrix.csv`, `round2_mutant_results.json`. Mutation table sha256 `05d7f93114222e4f` is identical in both rounds; the clean baseline passes every column; the real tree was unchanged by the sweep. Run: `python src/seeded_faults.py run --jobs 6 --round2`.

## What changed in the code and tests

* `src/judge.py`: the row-assembly loop of `judge_run` (raw pass-A/pass-B responses to J*/L0 fields and final labels) moved verbatim into `assemble_rows(junits, res, variants, l0)` so that it can run without the API. Behaviour is unchanged (replay on 3 stored runs reproduces all stored labels). The mutation patch texts for SF24-SF26 still match.
* `tests/test_replay_regression.py` (new, 14 tests): (1) judge post-processing replay over stored judgments of hw1, hw2, r2c1 (about 41,000 rows): raw responses rebuilt from stored J1/J2 fields, stored L0 labels, compared on critical, needs_arbiter, the five general dims, general_disagree, added_content; plus `_final` truth table. (2) builder golden: runs/requests/{hw (run hw1), r2c (run r2c1), hw2}.jsonl rebuilt from their item files, compared on request_key set, input_text, prompt, targets, model/prompt/sample/temperature; asserts all 5 channels occur.
* `tests/test_survivor_classes.py` (new, 6 tests): synthetic hand-derived cases for non-completion on a cue channel and cue-channel scoring via `attribute.score`, `oracle_wa.verdict`, two layer0 tie rules, `runio._norm` validity.
* `src/seeded_faults.py`: only added the `--round2` output prefix; the mutation list is untouched.
* Full pytest on clean code: 97 passed.

## Before / after

| | round 1 | round 2 |
|---|---|---|
| pooled existing tests | 39/58 (67.2%, Wilson [54, 78]) | 58/58 (100%, Wilson [94, 100]) |
| incl. supplementary request_rebuild | 46/58 (79.3%) | 58/58 |
| kills by crash or timeout only | 0 | 0 |

| class | role | round 1 | round 2 |
|---|---|---|---|
| K1 | verdict rules | 9/10 | 10/10 (SF06, test_survivor_classes) |
| K2 | channel mapping | 10/10 | 10/10 |
| K3 | judge post-processing | 0/6 | 6/6 (SF21-26, replay) |
| K4 | input builder | 1/8 | 8/8 (SF27-34, builder golden) |
| K5 | oracle acceptance | 5/7 | 7/7 (SF40, SF41, survivor_classes) |
| K6 | cue validator | 8/8 | 8/8 |
| K7 | layer0 | 1/3 | 3/3 (SF51, SF52, survivor_classes) |
| K8 | plumbing | 5/6 | 6/6 (SF53, survivor_classes) |

New kills (19): SF06; SF21-SF26; SF27-SF33; SF40, SF41; SF51, SF52; SF53. Two mutants already killed in round 1 are now also caught by pytest (SF01, SF05, via test_survivor_classes). SF34 and SF39 were already pytest kills.

## Surviving mutants

None. Caveats, stated plainly:

* The 19 new kills come from tests written after seeing which mutants survived and what they change. They are genuine regression tests (stored-data replay, golden rebuild, hand-derived expectations on clean behaviour; all pass on clean code), but the round-2 score is not an independent estimate of fault detection: it measures coverage of a fixed list that informed the tests. A fresh mutant set would be needed for that.
* The judge replay uses the stored J1/J2 fields as the "raw responses" (the per-pass API cache was not replayed), and stored L0 labels. SF26 is killed because pass-A reconstruction carries no added_content, which is a property of the reconstruction, not of recorded API payloads.
* Three of the new kills depend on synthetic cases (SF06, SF40/SF41, SF51/SF52, SF53), not on stored data; stored data still cannot distinguish SF06 and SF53.
