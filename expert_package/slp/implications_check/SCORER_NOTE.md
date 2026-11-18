# Scorer note: design implications check (authors only; do not send)

Returns go to `annotation/returns_slp_implications/` as `implications_check_SLP1.csv` and `implications_check_SLP2.csv`
(columns `reviewer_id,item,sound,comment`; items S1 to S8 plus a `FREE` row; `sound` is `yes`, `caveat`, `no` or blank).
Build: `src/build_implications_check.py` (figures in S6 to S8 are read from `src/score_slp_panel.py` output at build time).

## What this is
An anonymous expert review of eight design statements drawn from the materials, by the same two SLPs (SLP1, SLP2). It checks whether
the papers' design implications are clinically sound. It is not a study of the reviewers and not a population estimate.

## Scoring: no statistics
- No kappa, no tests, no intervals, no scores. n = 2.
- Per statement report the two answers as a count, for example "both yes", "one yes and one with a caveat", "one no".
- Report **every caveat and every "no"** by paraphrase that stays close to the reviewer's words. Do not average, drop or soften one.
  Short anonymous quotes are allowed by `AGREEMENT.md` section 4; never attach an ID to a quote in the paper.
- The free box is reported the same way: list each point that is clinically important and was missing, as a paraphrase.
- Blank answers are reported as blank, not as yes.

## How the result may be used
- A statement with two "yes" may be described as "both reviewers judged it clinically sound".
- A statement with a caveat or "no" is **not** reported as agreement. State the caveat, and change the paper's wording or limitation
  to match, or say plainly that we keep the statement and why. Do not keep wording a reviewer rejected without saying so.
- S1 (selection burden under scanning and eye gaze) concerns something the studies did not measure. A "yes" supports the design
  reasoning only; it is not evidence about selection time. Say so.
- S6 to S8 restate the reviewers' own earlier ratings and the weighted figures. A "yes" there confirms the interpretation, not the
  measurements.
- Wording: "expert review", "two speech-language pathologists", "clinically sound as a design implication". Never "validated",
  "clinically validated", "approved", or any AAC-user benefit claim.

## Rules
- Do not collect or report anything about the reviewers. If a note contains personal, client or workplace details, remove them
  before storing the file in the repo, and record that the text was redacted.
- CALE-AI stays anonymous: no reviewer identity, no repository URL, no project history.
- Macros only in the papers. If a count from this check is used, add a macro reading a derived file, for example
  `analysis/slp_implications/summary.json`, created from the returned CSVs; do not type counts by hand.
- Stage 7 slots (`\slotListener*`, `\oracleindep`, `% LISTENER`, `% ORACLE_INDEP`) are not touched by this check.
