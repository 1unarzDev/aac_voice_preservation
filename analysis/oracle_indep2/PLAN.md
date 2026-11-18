# A2 fast part: second-family and NLI oracles on the independent mutants (declared before any scoring)

Status: written 2026-11-18 before any NLI or Claude output on these items. Frozen headline numbers (GPT judge 70.7% overall / 58.5% lexicon-blind,
analysis/oracle_indep/) are NOT changed; everything here is a sensitivity analysis on the same human-confirmed set.

## Items
Scored set exactly as analysis/oracle_indep/confirmation.csv (`scored` True): 75 human-confirmed changed mutants, 46 human-confirmed same controls.
Texts from analysis/oracle_indep/candidates.jsonl (original, mutant). No item is dropped or added after any oracle output.
Claude and the NLI model are run on all 150 candidates (labelling does not depend on confirmation); only the 121 confirmed items are scored.

## Oracle 1: NLI (public MNLI model)
- Model microsoft/deberta-large-mnli (transformers, CPU or GPU under blocking flock /tmp/aacv_gpu.lock), fp32, no fine-tuning, no prompt.
- Input: premise = original, hypothesis = mutant, and the reverse pair. Labels from the model config (CONTRADICTION/NEUTRAL/ENTAILMENT).
- PRIMARY rule (declared now): change detected iff argmax is CONTRADICTION in either direction. Nothing is tuned on these items.
- SECONDARY rule (reported as a sensitivity, declared now): change detected iff NOT (argmax ENTAILMENT in both directions), i.e. no mutual entailment.
- Uses no dimension information (it sees only the two sentences), which is what a generic semantic-equivalence checker would do.

## Oracle 2: Claude as second-family labeller
- Claude Sonnet (claude -p --model sonnet, no tools, fresh process per batch, run from a scratch directory) labels each text blind with the judge's codebook
  prompt (src/judge.py CRITICAL_Q for the item's dimension + RULES_J1 + the item's critical options; time_quantity uses the time question with past/now/later/unclear).
  Output text only (no chips, no original/mutant flag, no op/kind); the original and mutant of a candidate appear as separate units, all units shuffled
  (seed 20261118), batches of about 40. Structured JSON output; unparseable or out-of-option labels are re-asked once, then counted as label "unclear/mixed".
- The dimension given to Claude is the candidate's target dimension (mutants) or source dimension (controls), the same dimension the GPT judge was asked.
- Detection rule: label(original) != label(mutant) on that dimension. Reference-value agreement (the GPT judge's rule, label(mutant) != reference) is reported alongside.
- Disclosure: Claude (same vendor family as the assistant that built this repo) also arbitrated labels elsewhere and assisted the pipeline. This oracle is a
  second family relative to the GPT judge, not independent of the authors' tooling.

## Ensembles with the GPT judge (production, reference-value rule from analysis/oracle_indep)
- "either flags" = judge OR oracle flags; "both flag" = judge AND oracle flag. Applied to NLI-primary and to Claude. Also judge+Claude+NLI majority is NOT run.

## Metrics
Mutation score (flagged / confirmed mutants) overall and in the lex_visible False stratum with Wilson 95% intervals; false-alarm rate on the 46 controls;
exact McNemar (two-sided) of each oracle and ensemble vs the GPT judge on the confirmed mutants (discordant counts reported). Unresolved/missing oracle output
counts as not flagged on mutants and as not flagged on controls, with counts reported.

## Outputs
analysis/oracle_indep2/{report.md, summary.json, scores.csv, nli_raw.csv, claude_labels.jsonl}; scripts src/a2_nli.py, src/a2_claude.py, src/a2_score.py.
