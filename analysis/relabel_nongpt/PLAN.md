# Claude re-label (plan section B2) - pre-declared before any labels exist

Purpose: a second-family (non-GPT) extractor labels the same outputs the production judge (src/judge.py, J1 wording) labelled, blind, so we can report agreement with human consensus and with the GPT judge, and re-run P1 (hw1+hw2 speech-act chip1-minus-noncrit gain) with Claude labels.

Labeller: Claude (Sonnet) subagents, batches of <=40 units, one fixed instruction (INSTRUCTION.md, copied verbatim into every subagent prompt). Disclosure: Claude is also arbiter and assisted analysis/writing; this is a second-family extractor, not an independent human check.

## Units (declared before generation)
1. Part 13: annotation/gold_key_hw.csv (152 outputs; output text; critical options from data/items family).
2. Part 20: annotation/treated_check_key.csv (120 outputs; options from the key's critical_options).
3. hw12 speech-act: runs/hw1 and runs/hw2 scored.parquet, prompt P0, dimension speech_act, channels chip1 and noncrit only, kept families only (data/items/hw.jsonl, hw2.jsonl) minus the analysis exclusions (refusal/acceptance-critical families, writer P06), valid outputs with text. Deduplicated by output text.
Units are deduplicated across all three sets by (text, critical question, options); one unit_id per distinct tuple.

## What a unit contains
unit_id (opaque, sha1 of text+question prefix, shuffled order), output text, critical question + options exactly as src/judge.py critical_question() gives them, the five general field questions/options (judge's GENERAL dims). Nothing else: no input, reference, condition, model, family, GPT label. added_content is NOT labelled (it needs the input, which would unblind).
The unit->source mapping is stored separately in unit_map.json (never shown to labellers).

## Batching / order
Units sorted by sha1(seed|unit_id) (seed 20261117), split sequentially into batches of <=40 (equal-sized as possible). Batch files: batches/bNN.json.

## Output format from labeller
JSON list of {unit_id, critical, polarity, speech_act, agent, certainty, politeness, evidence}; critical must be one of the unit's options.

## Analysis (declared)
Agreement of Claude critical label vs human consensus (Part 13/20) and vs GPT judge production label: accuracy and Cohen kappa, Wilson 95% CI. P1 re-run: replace the critical label for the hw12 chip1/noncrit outputs with Claude's, same estimator (writer-clustered ratio, t CI), reported next to the GPT-label estimate. No rule changes after seeing labels.
Units: 1575 distinct (152 p13 + 120 p20 + 2032 hw12 rows, deduped); 40 batches of <=40. Built by a one-off script (deleted).
