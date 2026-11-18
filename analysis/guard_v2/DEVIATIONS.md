# DEVIATIONS / clarifications for Problem 7 (guard v2)

All entries below were made before any G2 generation outcome or any rating existed unless stated. PLAN.md is unchanged (sha256 in FREEZE.md).

1. Frame/exclusion ambiguity (2026-11-18, before G2 generation). PLAN section 3 states N = 301 (gemma 147, llama 115, terra 22, qwen 17) and also
   "Excluded: any normalised text that appeared in Parts 4, 11, 17". The two cannot both hold: 61 of the 301 frame items (gemma 25, llama 25, terra 6, qwen 5)
   have a first-pass or G1 text whose normalised form appeared in a prior audit. The frame and draw were built as the numbers in the plan say (301; 22+17+90+71),
   with NO exclusion, because the counts are explicit and the draw rule names exact numbers. The overlap is a property of the frame, not a selection choice; the
   report will state it and show the headline contrast with and without those 61 items (descriptive, not a new primary).
2. Duplicate output rows. 24 of 1,848 W-C G1 requests expose the same output_id under two channels (chip1 and chipall) with identical text. The frame keeps one row per
   output_id (the first in file order); N stays 301.
3. Pre-use check fixtures (before any W-C G2 run). The first fixture for "clean pair" prepended "Please" to a statement, which makes layer0 label the sentence a request, so A correctly
   rejected 81 percent: a fixture artifact, not a property of A. Replaced by (a) clean_same (first == cand) and (b) a label-preserving contraction rewrite. Result in analysis/guard_v2/preuse_check.json:
   recall collateral 0.98, fragment 1.0, echo 1.0; false-reject 0.0 (rewrite) and 0.02 (clean_same). A was not changed (the one allowed code fix was not used).
   Limit: src/seeded_faults.py mutates repository code (not sentences), so sentence fixtures were built with the independent-mutant style templates and deterministic plants in guard_v2.py.
4. Echo rule "chip prompt text": implemented as 4-grams of prompts/chip_legend.txt plus, for chip inputs, the visible chip line with brackets removed.
5. Retries: the first retry message equals G1's (cache key reused, tag I1-guard-v1); a retry with an appended acceptance reason uses tag I1-guard-v2.
6. Local generation: `research submit aac-llm` takes generate.py request files, whereas the guard is a multi-turn loop (calls are chat messages built at run time), so local models run via the
   blocking flock /tmp/aacv_gpu.lock (same transport as the W-C guard run); terra via codex-lb with concurrency 4.
7. Catch items use independent-mutant candidates (analysis/oracle_indep: neg_fail_to, neg_refuse_to, neg_nobody, role_passive as planted-bad; ctl_paraphrase / ctl_contraction as known-good), shown with the original sentence as typed input.
   Catch is judged correct when planted-bad gets meaning not "yes" and known-good gets usable "yes" and meaning "yes".
