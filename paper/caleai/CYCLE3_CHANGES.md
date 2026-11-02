
# CALE-AI cycle 3 changes

Build (docker latexmk): 10 pages total; the body, conclusion included, ends on page 8 and references start at its bottom right (limit 8 excluding references). No undefined macros or citations. All 8 body pages viewed at 70 dpi.

## New macros (make_macros.py, block "cycle 3"; all read analysis/robust/*/summary.json)
`ra_unk_*`, `ra_effn`, `ra_rho`, `ra_usable_patterns`, `ra_repfail_*`, `ra_ctl_passed_n`, `ra_dim_*` (repair_audit_confounds); `t2_*` (t2_posterior); `t4_*` (t4_codebook); `t6_*` (t6_small_cluster); `t7_*` (t7_human_gate; the script asserts added_content is lowest or within 0.02 of lowest in every gate); `mrt_q`, `mrt_Teff`, `mrt_users_q`. Typed assumption, labelled in code: the outcome collection probability `_q` = 0.5.

## Folded in
- Part 4 pilot: unknown-as-unusable gap, about 1.1 effective independent raters (redundant answers), outcome-selected controls (20/20 passed; 12/20 repaired items known first-pass failures), politeness-heavy repaired arm (permutation p). Framed as a warning sign from 40 items; the 120-text audit decides. Abstract carries the short version.
- T2 default reframing: new Results paragraph "Defaults: a good guess with an asymmetric cost" (human 2.7% and compressor 11.4% posterior, 24 vs 0.8 per 1,000, politeness matches, speech act over-commits); thesis paragraph, ledger failure indicators (intro, card row for the cue) and one abstract clause now carry it. The line "average-accuracy metrics reward exactly the behavior that silently reverses meaning" is in the abstract, the paragraph and the conclusion.
- T4: both codings of "Can you...?" wherever the act-chip gain appears (cue probe; human-written pairs: 31.4 to 18.6 [10.0, 26.9]; 35.3 to 32.5).
- T6: the bootstrap-floor intervals/p are replaced by t intervals over writers, all-writer-sign agreement and the exact sign-flip randomization p with Holm values.
- T7: ties-as-disagreement kappa for critical dimension and added_content (weakest) in Setting.

## Cycle-3 review
- "Gain-only is the norm" softened to "commonly reports accuracy- or similarity-style gains", with 3 cited examples verified against lit/lit_aac_llm.md (Cai 2022 exact-expansion accuracy, KWickChat consistency rating and keystroke saving, SpeakFaster entry rate); the text says we did not survey the field. New bib entry `cai2022abbrev` (fields from lit note A04).
- Abstract uses the strict pass throughout (pass, gain, residual, repair rate) and says so; the frozen confirmation criterion is still the joint pass, reported in the body. "Typed input" is defined as the full channel in the glossary and where used.
- Development to confirmation repair-rate drop (78.8% to 52.5%; joint-pass repair also given) stated in abstract and Section 6.1, with the population-versus-tuning ambiguity.
- Elicitation: says the 20.8% is on cue-enriched messages with a set-level interval; also gives the message-level reweighted rate (21.4% [15.4, 27.8]).
- MRT: outcome collected on a random subset of sends is now in the power paragraph (users needed for that outcome versus every-send); the flag rate is said to come from constructed items.
- Kappa sample reconciliation: per-field n is smaller because ties and unsure items are excluded.
- Conclusion softened on human-written pairs and keywords.

## Slots (macros with defaults, patterns in the header comment)
`\slotBaseline` (`% BASELINE`, Section 4 and Section 6.1; default is the old upper-bound sentence), `\slotLegend` (`% LEGEND_TEST`, cue probe; default says the three-arm test is not in). Existing `% PART17` and `% PART18` slots unchanged.

## For the orchestrator
- Not committed. `results_macros.tex`, `main.tex`, `make_macros.py` and `refs.bib` changed.
- The abstract is about 270 words (was 230); cut the elicitation sentence first if needed.
- The T7 "weakest" claim: added_content is the lowest in the human-written-pairs gate and within 0.02 of the lowest in the other two (agent ties it), so the text says "weakest" without the margin; reword if a reviewer pushes.
