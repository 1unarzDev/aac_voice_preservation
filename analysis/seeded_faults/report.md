# Seeded-fault sweep of the harness (B1)

Plan: `analysis/seeded_faults/PLAN.md` (written before any mutant ran). Code: `src/seeded_faults.py` (mutation table sha256 `05d7f93114222e4f`). Matrix: `kill_matrix.csv`; per-mutant detail incl. the first failing message: `mutant_results.json`; numbers: `summary.json`. CPU only, no API, no GPU, no generation or judging. Temp copies under `tmp/sf/` were deleted afterwards; the real `src/` was never modified (fingerprint of the mutation targets, fixtures and frozen outputs unchanged before and after).

## Headline

* Clean baseline: every column passes (pytest 74/74 in 12 test files, identity, injection, challenge, R5 replay, T9 replay, re-scoring of 21 stored runs vs frozen `endpoints.json`).
* **39/58 seeded faults are caught by at least one existing self-test: mutation score 67.2% (Wilson 95% [54, 78]).** All 39 kills are by a failing assertion or a mismatch with frozen output; none is a crash-only or timeout kill.
* 19 mutants survive the existing tests. Two of them (SF06, SF53) change a line that no stored data exercises (see below), so the score is 39/56 = 69.6% if those two are treated as data-equivalent. The headline stays the strict 67.2%.
* A supplementary replay that rebuilds stored request files from the item files (`request_rebuild`, written for this sweep, not an existing test) adds 7 kills (all input-builder faults), giving 46/58 = 79.3%. It is reported separately and not part of the headline.

## Mutation score per test (kills / 58)

| test | kills | score | kills that no other existing test makes |
|---|---|---|---|
| pytest tests/ (pooled) | 18 | 31.0% | 5 |
|   pytest file test_analyze | 3 | 5.2% | 0 |
|   pytest file test_assignments | 0 | 0.0% | 0 |
|   pytest file test_frontier_multilingual_register | 0 | 0.0% | 0 |
|   pytest file test_hw_elic | 1 | 1.7% | 0 |
|   pytest file test_layer0 | 1 | 1.7% | 0 |
|   pytest file test_parts56_scorers | 0 | 0.0% | 0 |
|   pytest file test_resolution | 0 | 0.0% | 0 |
|   pytest file test_stage23 | 0 | 0.0% | 0 |
|   pytest file test_stage4 | 5 | 8.6% | 0 |
|   pytest file test_stage5_frontier | 0 | 0.0% | 0 |
|   pytest file test_stage6_coverage | 0 | 0.0% | 0 |
|   pytest file test_validate_cue_inputs | 10 | 17.2% | 0 |
| oracle identity (120 sources) | 7 | 12.1% | 0 |
| oracle mutation injection (120 mutants) | 12 | 20.7% | 0 |
| keyed challenge (72 sentences) | 4 | 6.9% | 0 |
| R5 validator replay | 9 | 15.5% | 0 |
| T9 validator replay (W-C, W-D, hw1) | 4 | 6.9% | 0 |
| re-score 21 stored runs vs frozen endpoints.json | 27 | 46.6% | 12 |
| SUPPLEMENTARY request_rebuild (not an existing test) | 8 | 13.8% | - |
| **any existing test (pooled)** | **39** | **67.2%** | |

Per-file pytest rows are subsets of the pooled pytest row. Test files with 0 kills (test_assignments, test_frontier_multilingual_register, test_parts56_scorers, test_resolution, test_stage23, test_stage5_frontier, test_stage6_coverage) test other modules (assignment plans, scorers, HTML packages, coverage gate); none of the 58 mutants is in code they exercise, so a 0 there is not a defect of those tests. Unique kills: 12 mutants are caught only by the re-scoring of stored runs, 5 only by pytest; the other 22 are caught by two or more.

## By class

| class | role | mutants | killed (existing) | with request_rebuild |
|---|---|---|---|---|
| K1 | verdict rules | 10 | 9 | 9 |
| K2 | channel-to-commitment mapping | 10 | 10 | 10 |
| K3 | judge post-processing | 6 | 0 | 0 |
| K4 | input builder | 8 | 1 | 8 |
| K5 | oracle acceptance | 7 | 5 | 5 |
| K6 | cue validator | 8 | 8 | 8 |
| K7 | deterministic labeler (layer0) | 3 | 1 | 1 |
| K8 | plumbing and aggregation | 6 | 5 | 5 |

The weak classes are the ones whose code is only reached through paths with no stored-data replay: judge post-processing (0/6; it runs only inside `judge_run`, which needs the API) and the input builder (1/8 with existing tests).

## Kill matrix (existing tests; X = test fails on the mutant)

| mutant | class | file | fault | pytest | ident | inject | chall | R5 | T9 | rescore | rebuild* |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SF01 | K1 | attribute.py | Violation: drop `not` (violation = critical_match) |  | X | X |  |  |  | X |  |
| SF02 | K1 | attribute.py | Assumption: negate committed |  |  |  |  |  |  | X |  |
| SF03 | K1 | attribute.py | committed: drop `not` (committed = is_unclear) |  |  |  |  |  |  | X |  |
| SF04 | K1 | attribute.py | chose: variant-A value reported as B |  |  |  |  |  |  | X |  |
| SF05 | K1 | attribute.py | constraint_preserving: `and` -> `or` |  |  | X |  |  |  | X |  |
| SF06 | K1 | attribute.py | non-completion on a cue channel counted as constraint-preserving |  |  |  |  |  |  |  |  |
| SF07 | K1 | attribute.py | general-dim comparison also scores the family's own critical dimension |  |  | X |  |  |  | X |  |
| SF08 | K1 | attribute.py | hedge_added inverted |  |  |  |  |  |  | X |  |
| SF09 | K1 | attribute.py | emphatic_added reference test inverted (!= -> ==) |  |  |  |  |  |  | X |  |
| SF10 | K1 | attribute.py | arbiter labels never used when J1 != J2 |  |  |  |  |  |  | X |  |
| SF11 | K2 | attribute.py | contra: counts dimensions NOT given by the channel |  |  | X |  |  |  | X |  |
| SF12 | K2 | attribute.py | stance addition: counts dimensions given by the channel |  |  |  |  |  |  | X |  |
| SF13 | K2 | attribute.py | `full` is no longer a cue channel |  | X | X |  |  |  | X |  |
| SF14 | K2 | attribute.py | `noncrit` is no longer an ambiguous channel |  |  |  |  |  |  | X |  |
| SF15 | K2 | attribute.py | channel_dims: chip1 gives the all_chips dimensions | X |  |  |  |  |  | X |  |
| SF16 | K2 | attribute.py | channel_dims: full channel gives no general dimension |  |  | X |  |  |  | X |  |
| SF17 | K2 | attribute.py | custom channel: cue test reversed subset |  |  |  |  |  |  | X |  |
| SF18 | K2 | labels.py | chip table: [NOT] -> affirmative | X | X | X |  | X | X | X |  |
| SF19 | K2 | labels.py | chip table: [YOU] -> speaker | X | X | X |  | X | X | X |  |
| SF20 | K2 | labels.py | general_spec: requests no longer make certainty n/a |  |  |  |  |  |  | X |  |
| SF21 | K3 | judge.py | _final: agreement is flagged as disagreement |  |  |  |  |  |  |  |  |
| SF22 | K3 | judge.py | _final: tiebreak returns J1 instead of layer0 value |  |  |  |  |  |  |  |  |
| SF23 | K3 | judge.py | _final: unresolved disagreement keeps J1 label |  |  |  |  |  |  |  |  |
| SF24 | K3 | judge.py | general-dim tiebreak uses the polarity layer0 label for every dimension |  |  |  |  |  |  |  |  |
| SF25 | K3 | judge.py | critical label: J2 ignored (J1 compared with itself) |  |  |  |  |  |  |  |  |
| SF26 | K3 | judge.py | added_content read from the extraction pass instead of pass B |  |  |  |  |  |  |  |  |
| SF27 | K4 | build_requests.py | chip1 channel emits all_chips (wrong chip set) |  |  |  |  |  |  |  | X |
| SF28 | K4 | build_requests.py | chipall channel emits only the critical chips |  |  |  |  |  |  |  | X |
| SF29 | K4 | build_requests.py | chipall channel puts keywords before the chips |  |  |  |  |  |  |  | X |
| SF30 | K4 | build_requests.py | full channel types the bare keywords instead of the source sentence |  |  |  |  |  |  |  | X |
| SF31 | K4 | build_requests.py | noncrit channel drops the noncritical word |  |  |  |  |  |  |  | X |
| SF32 | K4 | build_requests.py | noncritical word inserted at the wrong position (> -> <) |  |  |  |  |  |  |  | X |
| SF33 | K4 | build_requests.py | request_key no longer depends on sample_idx |  |  |  |  |  |  |  | X |
| SF34 | K4 | build_requests.py | identical renders no longer merge their targets | X |  |  |  |  |  |  | X |
| SF35 | K5 | labels.py | critical_match: plain no longer honoured by emphatic | X |  |  |  |  |  | X |  |
| SF36 | K5 | labels.py | critical_match: acceptance relaxed to also accept refusal |  |  | X | X |  |  | X |  |
| SF37 | K5 | labels.py | critical_match: plain~emphatic relaxation applied to every certainty value | X | X | X | X |  |  | X |  |
| SF38 | K5 | labels.py | critical_match: acceptance~statement relaxation removed |  |  |  | X |  |  | X |  |
| SF39 | K5 | labels.py | critical_match: final equality inverted | X | X | X | X |  |  | X |  |
| SF40 | K5 | oracle_wa.py | oracle verdict(): violation = critical_match |  |  |  |  |  |  |  |  |
| SF41 | K5 | oracle_wa.py | oracle verdict(): contradiction test inverted |  |  |  |  |  |  |  |  |
| SF42 | K6 | validate_cue_inputs.py | requirement_set: plain no longer honoured by emphatic | X |  |  |  | X | X |  |  |
| SF43 | K6 | validate_cue_inputs.py | requirement_set: polite values no longer a class | X |  |  |  | X | X |  |  |
| SF44 | K6 | validate_cue_inputs.py | decode: several cues for one dimension are unioned instead of intersected | X |  |  |  |  |  |  |  |
| SF45 | K6 | validate_cue_inputs.py | validate: disjoint accepted/required sets no longer conflict | X |  |  |  | X |  |  |  |
| SF46 | K6 | validate_cue_inputs.py | validate: compatible test reversed (req <= accepted) | X |  |  |  | X |  |  |  |
| SF47 | K6 | validate_cue_inputs.py | validate: conflicting verdict only for non-consensus claims | X |  |  |  | X |  |  |  |
| SF48 | K6 | validate_cue_inputs.py | decode: 'would you' no longer a politeness marker | X |  |  |  | X |  |  |  |
| SF49 | K6 | validate_cue_inputs.py | decode: 'feel sorry' no longer treated as ambiguous | X |  |  |  | X |  |  |  |
| SF50 | K7 | layer0.py | layer0: requests no longer certainty n/a | X |  |  |  |  |  |  |  |
| SF51 | K7 | layer0.py | layer0: booster outranks hedge |  |  |  |  |  |  |  |  |
| SF52 | K7 | layer0.py | layer0: polarity negated if ANY main clause is negated |  |  |  |  |  |  |  |  |
| SF53 | K8 | runio.py | occurrence validity: `and` -> `or` |  |  |  |  |  |  |  |  |
| SF54 | K8 | explode.py | text normalisation no longer lower-cases |  | X | X |  |  |  | X |  |
| SF55 | K8 | analyze.py | bootstrap point estimate divides by families, not valid rows | X |  |  |  |  |  |  |  |
| SF56 | K8 | analyze.py | paired difference direction reversed | X |  |  |  |  |  |  |  |
| SF57 | K8 | attribute.py | ambiguous-channel dedupe ignores channel |  |  |  |  |  |  | X |  |
| SF58 | K8 | attribute.py | endpoints: quarantined refusal/acceptance families are KEPT in primary estimates |  |  |  |  |  |  | X |  |

`rebuild*` is the supplementary column. Per-pytest-file columns are in `kill_matrix.csv`.

## Surviving mutants (19), each explained

Classification: **gap** = a real fault no existing test notices and that stored data could expose; **latent** = no stored data or run exercises the mutated line, so the stored-data tests cannot see it (still a real defect if new data arrives); **untested path** = the code runs only outside every test.

| mutant | fault | explanation | class |
|---|---|---|---|
| SF06 | non-completion on a cue channel scored constraint-preserving | Among the 21 re-scored runs there is exactly 1 non-completion target and none on a cue channel, so no stored endpoint depends on the line. The unit tests do not cover an invalid output on a cue channel. | latent (also a missing unit test) |
| SF21-SF23 | `_final` in judge.py: agreement flagged as disagreement; tiebreak returns J1; unresolved keeps J1 | `_final` is exercised only by `judge_run` (API). No test replays it. Post-hoc probe (run after the outcomes, not in the scores): recomputing critical/needs_arbiter/general labels from the stored J1/J2/L0 fields of 13,866 stored judgment rows through the mutated `_final` mismatches on 13,692 (SF21), 199 (SF22) and 208 (SF23) rows and on 0 with the clean code, so a 20-line replay test would kill all three. | gap |
| SF24, SF25, SF26 | judge_run: tiebreak uses the polarity layer0 label; critical ignores J2; added_content read from the wrong pass | These lines are inside `judge_run`, which needs live judge calls (or a stubbed API). The same probe leaves them at 0 mismatches because they are not in `_final`. Stored judgments cannot reveal them; only a stubbed-API unit test could. | untested path |
| SF27-SF33 | builder: chip1 emits all chips; chipall emits critical chips only; chip order; full channel types keywords; noncrit drops word; wrong insertion position; request_key ignores sample_idx | No existing test calls `build_requests.input_text/build` against stored requests: the T9 replay reads rendered inputs from stored tables, not from the builder. The supplementary `request_rebuild` replay (5 stored request files rebuilt from their item files, equal keys, inputs, prompts and target lists) kills all seven. SF34 (no merging of identical renders) is already caught by pytest. | gap (closed by the supplementary replay) |
| SF40, SF41 | oracle_wa.verdict(): violation = critical_match; contradiction test inverted | `verdict()` is used only by the panel/gold sections of `oracle_report.py` (lines 341-347), which are not re-run by any test, and the injection and challenge columns use `attribute.score` and `crit_match`. A re-run of `oracle_report.py` against the frozen `report.md` would cover it. | untested path |
| SF51 | layer0: booster outranks hedge | Witness: `I think it is definitely fine.` is hedged/uncertain in clean code and strongly certain/emphatic in the mutant. The layer0 tests have no hedge+booster sentence, and layer0 labels only break J1/J2 ties and set the emphatic-added reference, so stored endpoints do not move. | gap |
| SF52 | layer0: polarity negated if ANY main clause negated | Witness: `I do not like it but I will go.` is mixed/unclear in clean code and negated in the mutant. No layer0 test has a clause-split negation; same reason stored endpoints do not move. | gap |
| SF53 | runio._norm: occurrence validity `and` -> `or` | In all 232,570 occurrences of the 21 re-scored runs the raw `valid` flag equals `bool(text.strip())` (0 mismatches), so `and` and `or` agree on every stored row. | latent |

None of the 19 is shown to be a true equivalent mutant (the changed code differs in behaviour for some input); SF06 and SF53 are the two where stored data cannot distinguish them.

## What the killing tests cover

* The re-scoring of stored runs against frozen endpoints is the broadest net (27 kills, 12 unique): it covers verdict rules, channel mapping, oracle acceptance and aggregation, because every endpoint is a pure function of the stored labels. It does not cover the judge, the builder or the validator.
* The oracle identity/injection columns kill 7 and 12 mutants (all 7 identity kills are also injection kills). Identity catches false-alarm faults, injection catches missed-flip faults; the challenge set catches the acceptance/plain-certainty relaxations (SF36-SF39).
* The validator is covered by its own unit tests plus both replays: all 8 validator mutants die, 4 of them also in T9.
* Detection by crash: none. Every kill is a failed comparison or assertion.

## Limits

* 58 mutants from 8 structural classes; one-site edits. Scores are conditional on this table and the class quotas fixed in the plan; they are not an estimate over all possible faults. The Wilson interval treats the 58 sites as exchangeable draws, which they are not (they are stratified by class).
* The JS front-end tests (`tests/*.js`) were not run (no mutant touches the HTML packages). `analysis/oracle_report.py` panel sections, `judge_run` and the generation code are not covered by any test column, hence the survivors above.
* Re-score run list and the request-rebuild file list were fixed from the clean baseline (21 of roughly 33 probed runs reproduce frozen endpoints byte-for-byte under a fixed option; 5 request files of 8 tried rebuilt exactly and 3 were dropped before any mutant ran: expC1 request differs, hw2/legend1 key sets differ). Runs that do not reproduce on clean code were excluded, not tuned per mutant.
* The post-hoc `_final` replay probe and the layer0 witnesses for SF51/SF52 were run after seeing the outcomes and are not in any score.
