# CALE-AI cycle 2 changes

Build (docker latexmk): 9 pages total; body ends 2 lines onto page 8, so about 0.9 page of slack remains (limit 8 excluding references). No undefined macros, no red macro placeholders.

## Consistency fixes (verified against analysis files)
- Table 4 caption: the echo count was over all unusable repairs but the caption said "of the three". `make_macros.py` now exports `*_ex_echo` over the three shown (1 and 1) and `*_echo_all` (3 and 1). "Tell you" is described as a pattern, not as shown.
- Fig. 2 (ledger) chip row: `miss_persists` used the bare-keyword baseline (284 misses) while `lost_with_chip` used the length-matched word (194 kept). `caleai_evidence.py` line 217 now conditions on the same comparator: 7/194 lost, 17/270 still missed; 194 + 270 = 464, and 7 + 17 = 24 = 464 - 440. `evidence.json` regenerated; only `miss_persists` changed.
- Rounding: Table 3 caption states that differences are computed from unrounded rates (2.44 vs 96.70 - 94.25).
- Inputs vs targets: defined in the Table 3 caption with macros (1,392 cue targets + `g_amb_req` = 464 no-cue requests = 1,856 inputs; 1,872 targets share 1,848 distinct requests).
- Held-out: now "development set"; guard numbers there are labelled development results. "Every miss is attributed by construction" now says it holds only as far as the extractor and conditions are right. The deployment clause is stated once (Table 2 and 6.2). The abstract names the chip failure and the 12.13% residue, and reports the pooled pilot gap with its CI (post hoc, descriptive, new macros `pp_*`: -15.2 [-33.8, 4.5], includes 0 and -10).
- Human-vs-scorer check inside the pilot (macros `ra_pres`, `rt_pres`): raters judged meaning kept in 14/16 and 16/19 scored-passing repairs, so the usability problem is mostly form, not lost meaning.

## Jargon
Part 17/18, W-C, W-D, hw1, I1/I2, P0/P2/S3/G1/G1s, chip1/chipall removed from the text, tables, figures and generated example rows. Plain names: development set, confirmation set, human-written pairs, keyword study, first pass, strip-only, guard, menu, cue, 120-text audit, writer-intent check. "Kill" replaced by "pass line". Glossary cut to 10 rows.

## Lay rewrites, examples, venue fit
- Abstract rewritten (lay R1-R3 adapted): one-line answer under "Does it work?", hedges stated once. Intro opens with the plain failure example.
- Fig. 1 (page 1, new): three real stored outputs ("Is [I] bring a friend?", "Don't knock...", "Ask you to wear headphones."), strings via macros `bx*` from `analysis/guard_wc/examples.json` and `evidence.json`. Selection rule (first in hash order within category) and each category's rate are in the caption; labelled "illustrative failures found by the audit". "Is it okay if I bring a friend?" is the first of 26/1,394 changed-correct texts; the "knock" row is the first of the menu's politeness losses (26/40 -> 12/40 sets).
- Fig. 2 (ledger) redone: fonts 7-9 pt (were 5.8-7.6), one-line labels, pass line and pp defined in the caption, plain names, cost/test column no longer clipped.
- Section 7 is now a pre-specified human-effect study: estimand (causal excursion effect), per-flagged-message randomization among three arms, proximal and longitudinal outcomes, sample-size reasoning, H1-H3. Sample-size numbers are macros. Typed assumptions are in `make_macros.py` and flagged as assumptions: ICC 0.2, d 0.2, T 40, rho 0.3, 80% power. The writer count (20) is read from `data/items/hw.jsonl`.
- Baseline: Section 4 and Limitations say strip-only covers one failure type and that the increment is an upper bound on the feedback's contribution. A `% BASELINE` comment marks where a no-feedback resample baseline would go. None is claimed.
- Concurrent paper: scoring, attribution, extractor, arbiter and populations are defined in-paper; the one citation is for provenance only.
- Bib: "per author record" and BiAlign venue notes removed (the lit/ notes confirm the arXiv records, not the venues). The concurrent-paper note is now "Anonymized for review". The artifact placeholder became a sentence plus `% VERIFY`.

## Slots for tomorrow
Preamble macros `\slotAuditAbs`, `\slotAuditBody` (marked `% PART17`) and `\slotIntent` (`% PART18`) have printing defaults. The header comment has one sentence pattern per frozen-rule outcome (killed, uncertain, none) and for H1 (supported, demoted).

## Notes for the orchestrator
- Not committed. The ledger figure and guard-example rows were regenerated; `results_macros.tex` and `evidence.json` changed.
- The abstract is longer (about 230 words). Cut the "Two other add-ons" sentence first if needed.
- The pooled pilot gap is post hoc. The frozen rule applies to the 120-text audit, and the text says so.
- Whether the 120-text audit includes the original-failed and strip-only arms is still unconfirmed (carried over from cycle 1).
