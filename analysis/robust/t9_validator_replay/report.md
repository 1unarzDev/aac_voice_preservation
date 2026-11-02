# T9: R5 validator replay on W-C, W-D and hw1 rendered cue inputs

Script `src/robust_t9_validator_replay.py`; per-input rows in `replay_rows.csv`; `summary.json`. The validator (`src/validate_cue_inputs.py`, unit tests in `tests/test_validate_cue_inputs.py`) is imported unchanged. 0 generation / 0 judge calls. Inputs: unique (family, variant, channel, rendered input) from the stored scored tables, each also present in the stored request files (inputs whose request_key is absent from, or renders differently in, the request files: {'W-C r2c1': 0, 'hw1': 0, 'W-D r2d1': 0}). Critical-dimension cues are validated against the authored variant value; bare/noncrit channels are checked for cue leaks; bare/noncrit inputs identical between A and B: {'W-C r2c1': {'bare': {'family_channels': 240, 'differing_between_A_and_B': 0}, 'noncrit': {'family_channels': 240, 'differing_between_A_and_B': 15}}, 'hw1': {'bare': {'family_channels': 574, 'differing_between_A_and_B': 0}, 'noncrit': {'family_channels': 574, 'differing_between_A_and_B': 13}}}.

W-C and hw1 `chipall`/`chip1` and W-D pol/actor/both cells are the 'cue' channels; `full` (free text) is out of validator scope.

## Validator as shipped (long chip aliases such as [STATEMENT] are unsupported chips -> unknown)

| run | cue_inputs | compatible | compatible_but_coarser | conflicting | unknown | unchanged_noop | no_cue_inputs | leaks |
|---|---|---|---|---|---|---|---|---|
| W-C r2c1 | 960 | 960 | 0 | 0 | 0 | 0 | 960 | 0 |
| W-D r2d1 | 10240 | 7680 | 0 | 0 | 2560 | 0 | 2560 | 0 |
| hw1 | 2296 | 1888 | 0 | 0 | 408 | 0 | 2296 | 0 |

**Conflicts, W-C r2c1: 0**

**Conflicts, W-D r2d1: 0**

**Conflicts, hw1: 0**


## With the legend's long chip aliases normalised to the short chips

| run | cue_inputs | compatible | compatible_but_coarser | conflicting | unknown | unchanged_noop | no_cue_inputs | leaks |
|---|---|---|---|---|---|---|---|---|
| W-C r2c1 | 960 | 960 | 0 | 0 | 0 | 0 | 960 | 0 |
| W-D r2d1 | 10240 | 10240 | 0 | 0 | 0 | 0 | 2560 | 0 |
| hw1 | 2296 | 1888 | 0 | 0 | 408 | 0 | 2296 | 0 |

**Conflicts, W-C r2c1: 0**

**Conflicts, W-D r2d1: 0**

**Conflicts, hw1: 0**

## Non-certified cue inputs after alias normalisation (by run, channel, dimension, verdict)

| run | channel | dimension | verdict | n |
|---|---|---|---|---|
| hw1 | chip1 | time_quantity | unknown | 204 |
| hw1 | chipall | time_quantity | unknown | 204 |

Example reasons: no decodable time_quantity cue in the rendered input (unsupported chip(s) [LATER]); no decodable time_quantity cue in the rendered input (unsupported chip(s) [NOW]); no decodable time_quantity cue in the rendered input (unsupported chip(s) [PAST])

## Notes and caveats

* `unknown` for time_quantity is a scope gap of the validator ([PAST]/[NOW]/[LATER] are not in `CHIP_TO_GENERAL`), not a defect in the inputs.
* `compatible_but_coarser` is the `[SURE]` granularity case (accepts plain or emphatic); `unchanged_noop` flags a chip input byte-identical to its bare baseline.
* bare is identical for A and B in every family; noncrit differs between A and B in the word order of the keywords for the families listed above (the SPEC rule 'words keep source order'), a documented design property, not a cue leak.
* In W-D the `[STATEMENT]` encoding is an unsupported chip for the shipped validator (the speech-act check is `unknown` raw and `compatible` once the legend alias is normalised); the polarity/agent cells are unaffected.
* 'conflicting' is the only blocking class. A clean result here is a statement about the rendered cue vs the authored critical value, not about whether the model honours it, and says nothing on the free-text `full` channel.
* hw1 includes all 574 candidate families (547 kept); family-level exclusions do not change the conflict count (see rows).
