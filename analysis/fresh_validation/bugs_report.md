# Fresh seeded-fault sweep (PLAN.md part A), run once, tests frozen

Clean baseline passed all columns. Pooled existing-test kill rate (strict, survivors count against): 16/40 = 40.0%, Wilson 95% [26.3, 55.4]. Killed by assertion/mismatch 15, crash-only 1. Real tree unchanged: True.
All 16 kills come from pytest (test_stage7 12, test_stage23 3, test_analyze/stage4/stage5 1 each); no oracle/validator/rescore column killed any fresh mutant (those columns do not exercise these modules). request_rebuild adds none.
No test was changed after FREEZE (tests sha in FREEZE.json). Survivors are test gaps or equivalents; equivalence claims NOT yet reviewed (second line pending).

## By fault type (killed/5)

- F1: 1/5
- F2: 3/5
- F3: 2/5
- F4: 2/5
- F5: 0/5
- F6: 5/5
- F7: 2/5
- F8: 1/5

## Per mutant (id, type, module:line, description, result)

- FB01 F1 LS:158 comparison edge > -> >= -> pytest_all
- FB02 F1 RA:219 comparison edge < -> <= -> SURVIVED (explanation pending)
- FB03 F1 OI:306 slice end -1 -> SURVIVED (explanation pending)
- FB04 F1 MF:335 range(n) -> range(n - 1) -> SURVIVED (explanation pending)
- FB05 F1 LS:320 comparison edge < -> <= -> SURVIVED (explanation pending)
- FB06 F2 LS:303 constant 0.55 -> 1.1 -> pytest_all
- FB07 F2 OI:259 constant 150 -> 151 -> pytest_all
- FB08 F2 MA:147 constant 35 -> 36 -> pytest_all
- FB09 F2 GD:75 constant 3 -> 4 -> SURVIVED (explanation pending)
- FB10 F2 AN:541 default/flag index=False flipped -> SURVIVED (explanation pending)
- FB11 F3 LS:240 first two positional arguments swapped -> pytest_all
- FB12 F3 RA:150 operands of a difference swapped -> SURVIVED (explanation pending)
- FB13 F3 ML:239 first two positional arguments swapped -> pytest_all
- FB14 F3 MF:375 first two positional arguments swapped -> SURVIVED (explanation pending)
- FB15 F3 AN:524 first two positional arguments swapped -> SURVIVED (explanation pending)
- FB16 F4 LS:305 true division -> floor division -> pytest_all
- FB17 F4 RA:295 true division -> floor division -> SURVIVED (explanation pending)
- FB18 F4 OI:165 int() -> round() -> SURVIVED (explanation pending)
- FB19 F4 GD:453 sum() -> max() -> SURVIVED (explanation pending)
- FB20 F4 AN:197 float() -> int() -> pytest_all
- FB21 F5 AN:213 sort_values: last key column dropped -> SURVIVED (explanation pending)
- FB22 F5 AN:304 groupby: last key column dropped -> SURVIVED (explanation pending)
- FB23 F5 AN:403 drop_duplicates: last key column dropped -> SURVIVED (explanation pending)
- FB24 F5 AN:264 sort_values: last key column dropped -> SURVIVED (explanation pending)
- FB25 F5 AN:500 drop_duplicates: last key column dropped -> SURVIVED (explanation pending)
- FB26 F6 MA:254 elicitation tie-break order reversed (hord rank sign) -> pytest_all
- FB27 F6 MA:1060 tie-break routing no longer excludes the pair writer -> pytest_all
- FB28 F6 ML:316 Part 29 sentence-order coin reversed -> pytest_all
- FB29 F6 ML:306 Part 28 self-annotation exclusion skipped (nobody blocked) -> pytest_all
- FB30 F6 MF:312 allocator may give the same item to the same person twice (no duplicate-annotator check) -> pytest_all
- FB31 F7 LS:236 listener exclusions computed but not applied on the main path -> pytest_all
- FB32 F7 RA:73 practice rows flagged practice=1 no longer skipped -> SURVIVED (explanation pending)
- FB33 F7 OI:154 empty-input default: judge reported scored when no items -> SURVIVED (explanation pending)
- FB34 F7 MF:347 balance(): new-part opening not prevented when allow_new is False -> pytest_all
- FB35 F7 GD:369 quarantine filter not applied on the disc path -> SURVIVED (explanation pending)
- FB36 F8 LS:269 label/form map 'A' -> 'B' -> pytest_all
- FB37 F8 MA:994 label/form map 'A' -> 'B' -> SURVIVED (explanation pending)
- FB38 F8 ML:463 label/form map 'B' -> 'A' -> SURVIVED (explanation pending)
- FB39 F8 GD:421 sign flip of a difference (- -> +) -> SURVIVED (explanation pending)
- FB40 F8 AN:508 label/form map 'B' -> 'A' -> SURVIVED (explanation pending)

Deviations: FB05 replaced by reserve R01 at validate; F5 sites mostly only in analyze.py so 4 F5 faults moved (see DEVIATIONS.md). Round-2 comparison (Fisher) and per-survivor explanations to be added by a separate analysis step.