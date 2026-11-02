# SLP expert panel: analysis plan

**Authors only. Do not send this file to the reviewers: it names the arms.** Written 2026-11-02, before any SLP rating exists
(`expert_package/returns_slp/` is empty; no returns have been seen). Code: `src/build_expert_package.py` (draw), `src/build_slp_tool.py`
(tool), `src/score_slp_panel.py` (scoring, `--self-check`). The draw is deterministic and re-runs byte-identically.

## Framing
Two practising SLPs act as **expert annotators judging study materials**. This is an **expert review, not a population estimate**: with
two raters nothing generalises to SLPs as a group, and no significance test is reported. Reviewer ratings concern the outputs only.
No IRB. No demographics, no questions about the reviewers' own practice or communication, no recordings, anonymous IDs (SLP1, SLP2).

## Task 1: severity weights
Seven change types (codes shared with the scorer): NEG negation dropped/added; ACT question became a statement or statement became a
command; AGT actor switched; CRT certainty added/removed; POL politeness added/removed; TIM time changed; ADD added content.
Each type is shown with 2 real stored outputs drawn by the rule below. Each reviewer gives one severity (1 trivial, 5 critical, with written anchors)
and one block/flag choice (block / flag / neither / unsure) per type, "if this were spoken as a client's message".
- **Severity of a type** = mean of the two reviewers. **Weight** w_t = mean severity / 5 (range 0.2 to 1.0).
- Secondary weight: share of reviewer answers that are block or flag.
- Per-type disagreement is reported as the two raw values; identical and within-one-point counts are given.

Note on "request becoming a command": the codebook treats a request and a command as one category, so the judge cannot flag it. The ACT
examples are therefore a question becoming a statement and a statement becoming a command.

## Task 2: acceptability of 50 stored outputs
Rule (fixed before any rating; seed string `expert-panel-2026-11-01`; rank = sha256(seed | stratum | unit id), ascending; first qualifying):
1. **Guard repairs (20).** Pool: W-C speech-act targets (analysis/guard_wc, 4 models x 3 cue channels) where the baseline P0 output
   failed the strict endpoint, the frozen guard G1 changed it and the changed output passes strict. 251 units. Two strata of 10 with
   at most one unit per family: units whose input and repaired text also appear in classmate Part 17 (27 in the pool, stratum
   `guard_overlap`, so SLP and classmate ratings can be compared), then the remainder (`guard_other`).
2. **Originals (10).** The baseline P0 outputs of 10 of those 20 inputs, chosen by (original also in Part 17 as `original_failed`
   first, then hash rank). Shown as separate cards.
3. **Chip and plain-word outputs (10 + 10).** Pool: all (family, variant, model) cells of the 546 analysed hw1 families with a valid P0
   output in both the chip1 channel (runs/hw1) and the plain-word channel (runs/hwctl1, `nlcue`): 4,368 pairs. Stratified by dimension
   (allocation 2,2,2,2,1,1 in the dimension order given by hash rank: speech_act 2, agent 2, politeness 2, certainty 2, time 1,
   polarity 1), one pair per family. Outcome (judge pass/fail) is not used in this draw. Both outputs of a pair are shown, as separate cards.
4. Neutral ids S01 to S50 are a hash permutation; arm, pair and judge labels are held only in the private key `expert_package/slp_key.csv`.
   Both reviewers see the same cards in the same order. The tool embeds no arm information.
Task 1 examples: drawn from cue-supplied P0 outputs (runs hw1, hwctl1, main1, r2c1, pilot1) whose two judges agreed, excluding every
Task 2 output and family; per change type the first by hash rank in each direction stratum (families distinct); ADD examples need an
added phrase of at least two words in the judge's evidence. Pool sizes are in `slp_draw.json`.

Per card: (a) says what the selected words mean (yes / partly / no); (b) acceptable to speak as the client's message (yes / with edit /
no); (c) optional note.

## Estimands (all descriptive)
1. **Severity by type** (mean of 2) and block/flag shares.
2. **Clinically weighted failure rate** for four arms: guard (G1), chip (hw1 chip1), plain word (hwctl1 nlcue) and baseline.
   Existing judge labels only, no new model calls. Per output, the judge-flagged failure types are: critical value not kept
   (NEG, ACT, AGT, CRT, POL, TIM by the focal dimension), any contradiction on polarity, speech act, agent, certainty or politeness,
   politeness added, an emphatic or hedge word added where the input carried no certainty cue (CRT), and added content (ADD).
   Weighted failure of an output = the largest weight among its flagged types (0 if none); arm rate = mean over outputs.
   **Primary** includes ADD; **secondary** drops ADD. Reported beside the unweighted any-failure rate. Populations differ and are
   not pooled: W-C speech-act (baseline P0, guard G1; G1s as a secondary comparator) and hw1 six dimensions (baseline noncrit and bare,
   chip, plain word, irrelevant chip). Compare arms only within a population. Sensitivity: the rate recomputed under each reviewer's own
   severities (min to max, reported as a range, not a CI).
3. **SLP acceptability by arm**: counts and percentages for (a) and (b), pooled and per reviewer; paired counts on shared inputs
   (guard repair vs original; chip vs word). No tests.
4. **SLP to SLP agreement** on the same 50: raw percent, Cohen kappa (nominal), linear-weighted kappa, kappa on yes vs not-yes, with an item-only
   bootstrap interval. Task 1: identical and within-one counts. **n = 2 caveat:** kappa describes these two reviewers; low or
   high agreement is not a population property. If the two disagree systematically, both sets of results are reported separately
   rather than averaged away.
5. **SLP vs judge**: judge meaning-pass (no flagged type other than ADD) vs reviewer (a) = yes, per reviewer and where both agree: raw
   agreement, kappa, 2x2 table.
6. **SLP vs classmate Part 17** on overlapping items only (up to 12 items; about 10 repaired plus 2 originals): reviewer (a) vs classmate
   contract majority, reviewer (b) vs classmate quality majority (edit = minor). Computed only if Part 17 returns exist; the
   Part 17 decision rule in annotation/COORDINATOR_STEPS.md is unaffected.

## Not done
No weighting of reviewers, no imputation, no exclusion of a reviewer after seeing data, no tests, no claim about SLPs in general,
no use of notes beyond quoted illustrations. A card left blank is missing for that question. A blank severity removes that type's weight
and the scorer flags the affected rates.

## Wording rule
"Two practising SLPs rated ..." "an expert review". Never "SLPs found" as a population claim; never "validated" for the judge from n = 2.
