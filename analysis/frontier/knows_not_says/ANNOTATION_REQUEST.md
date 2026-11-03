# Annotation request (NOT SENT): does the polarity detector agree with human readers on model outputs and on typed sentences?

Frontier knows_not_says, round 3. Status: items and key built, nothing sent; the orchestrator batches requests.

## Purpose
R1 (does the model's sampled distribution match the human rate of omitting a negation?) rests on one regex/rule detector (`src/layer0.py`) applied to BOTH the model outputs and the typed sentences. A machine check (judge.py J1+J2, gpt-6.1-sol, blind arbiter on 7 disputes) already estimates its predictive values (see round3.md, T7), but a machine reference is not human truth. This request asks humans to confirm that reference on exactly the sentences the machine check used, so the R1 correction (predictive-value form, PLAN A19b) can be reported as human-validated. Part 21 (`annotation/returns_source_check`, 200 typed sentences) is the human check of source labels and has 0 returned files today; the 100 source sentences here are a fallback and should be dropped if Part 21 returns first.

## Items and draw rule
534 sentences, seed 20261102 (`src/frontier_knows_not_says_validity.py draw`, `src/frontier_knows_not_says_annot_items.py`): per model (qwen2.5-7b, llama3.1-8b) every detector-negated output in the validity sample (34 and 100) plus 150 random detector-not-negated outputs (of the 300 drawn); 100 typed source sentences (50 detector-negated, 50 not) from the no-cue messages. Sentences are shown alone, in random order, with no model, input, detector label or condition.
Files: `annotation/frontier_knows_not_says_items.json` (for `annotation/frontier_knows_not_says_annotate.html`, a copy of annotate.html that hides the added-content question), key `annotation/frontier_knows_not_says_key.csv` and `annotation/frontier_knows_not_says_items_key.csv` (item -> set, detector label; never shown), assignment `annotation/frontier_knows_not_says_assignment.csv` (3 raters per item, 80-81 items per annotator).

## Question and options (one question per sentence)
"Is the main thing the sentence says negated (not/never/no/don't) or affirmative? Uncertainty wording like 'not sure' is unclear/mixed." Options: negated, affirmative, unclear/mixed (plus the tool's "unsure" key).

## Who and time
About 20 adult non-author annotators (the same pool as the other parts; P01-P20 in the assignment file are placeholders). No SLPs needed. No AAC users, no IRB. About 80 sentences per person at roughly 8 s each: 10-12 minutes.

## Analysis it feeds
Human majority label (3 raters, ties to unclear/mixed) replaces the machine reference: PPV = P(human negated | detector negated), NPV = P(human not negated | detector not negated), separately for model outputs per model and for typed sentences, Wilson CIs; Fleiss kappa among raters; agreement of the machine reference with the human majority. These feed `corrected_r1` in `src/frontier_knows_not_says_analyze.py` (predictive-value correction, Beta posteriors inside the bootstrap), turning "detector-relative, validated by a machine reference" into "human-validated" or showing that the R1 class changes.
