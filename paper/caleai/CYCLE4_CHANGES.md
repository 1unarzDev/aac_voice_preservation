# CALE-AI cycle 4 changes

Build (docker latexmk): 10 pages; body ends at the bottom of page 8, references follow on 9-10. No undefined macros or citations. All pages viewed at 70 dpi. Abstract about 231 words in the PDF (was about 270). Not committed.

## New macros (make_macros.py, block "cycle 4"; no typed numbers)
- `bd_*` / `bw_*` (development / confirmation) from `analysis/guard_baseline/summary.json`: joint and strict pass for G1, G1s, G1r, G1t (`_jp_`, `_sp_`), strict repair `_rep_`, contrasts `_gr` (G1-G1r), `_tr` (G1t-G1r, matched decoding), `_rs` (G1r-G1s), `_ptf_all` (strict pass to fail summed over arms), `_same` (retry reproduced the original text, 111/170 and 351/508). Asserts: G1-G1r lower bound above 0 on both sets; G1r-G1s not positive.
- `lg_*` from `analysis/legend_test/summary.json`: `lg_a/b/c` (legend, no legend, markers may be missing; with `_lo/_hi`, `_d2` replication draw, `_commit`), `lg_unclear_max`, `lg_n_models`. Asserts: no unresolved rows, every model class "not_artifact", arms b and c at least 90%.

## Slots filled
- `% BASELINE`: `\slotBaseline` (Section 4 description of G1r and G1t) and new `\slotBaselineRes` (Section 6.1: G1r repair rates, G1-G1r and G1t-G1r increments on both sets, retries reproducing the first text, 0 pass-to-fail). Table 3 gains a "Free baseline 2" block (joint pass resample / guard at T=0.7; repaired; the two contrasts). The strip-only floor sentence now says the second free baseline is plain retrying. "This compares stored configurations and does not isolate the feedback message" now points to the baseline. Limitations: the "no resample baseline exists" sentence is replaced by the caveats (one seed per attempt, T=0.7 vs the guard's 0, exploratory).
- `% LEGEND_TEST`: `\slotLegend` (cue probe): default survives removing the legend and the explicit "do not assume" instruction, replicated by a second draw, "unclear" at most a fraction of a percent; "you cannot prompt the default away, so the ledger must measure it". Same point added to the end of the defaults paragraph.

## Orchestrator directive: lead with what works
- Abstract rewritten: guard gain (+joint, with interval) and repair rate, no correct sentence broken, feedback beats plain retrying at matched decoding, then what the ledger adds (residual failures, strip-please share, unusable passing sentence), the pilot as a usability warning, the default (affirmative commitment even when told not to assume, silent reversals), stored-text scope. "Does it work?" dropped; the development-to-confirmation drop and the pilot's control-selection detail now sit in the body only (Section 6.1, 6.2, Limitations). The elicitation sentence was cut.
- Intro contribution (2) and (3), Section 6.1 title ("about half of failures repaired, and feedback beats plain retrying") and the conclusion opening now lead with the result.
- Abstract uses the joint pass for the gain (+9.83 is the frozen confirmation criterion); strict figures are labelled strict.

## Layout
- Table 3 float placement changed to `[!t]` (it was deferred past the conclusion and pushed the body to 9 pages). `\slotAuditAbs` default shortened.

## For the orchestrator
- The abstract no longer states the 78.8 to 52.5 development-to-confirmation drop (cycle-3 review item); it is in 6.1. Re-add one clause if a reviewer wants it up front.
- The G1-G1r contrast is not a clean feedback effect (T=0 vs T=0.7); the paper says so and gives G1t-G1r as the isolating contrast.
- The slot header comments in main.tex (C) and (D) are now historical.
