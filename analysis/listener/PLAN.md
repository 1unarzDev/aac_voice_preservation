# Part 28 Listener Communication Study: frozen analysis plan

Written 2026-11-17, before the stimulus draw, before the guard run, and before any stored output for the 120 drawn messages was read.
Nothing below may change after listener data are collected. Any later deviation is reported as a deviation, not folded in.
Status: not committed; to be hash-deposited before the sheets are sent (see COORDINATOR_STEPS section 7, written by the assignment task).

## 1. Question and role of the people
Twenty adult non-author volunteers act as annotators of study materials. A listener sees a context line and one sentence and says what the person is saying.
No data about the listeners themselves are collected. Listeners are not AAC communication partners; comprehension is not a real-world consequence.

## 2. Stimuli (frozen rules)
Source: data/items/hw.jsonl (547 families) and data/items/hw2.jsonl (60 speech-act families); every family is a kept pair (3 of 3 human checks pass).
Draw script: src/make_listener_study.py, seed 20261117 (python random.Random(seed), explicit sort of family ids before every draw).

* Dimensions: polarity, speech_act, agent, time_quantity. certainty and politeness are excluded (lower SLP severity, 3 to 3.5 against 4 to 5).
* 30 messages per dimension, 120 total. hw and hw2 families are pooled before the speech-act draw (hw2 is not oversampled). No family is used twice.
* An "intended message" is one variant (A or B) of a family: its source sentence is the writer's own sentence and the reference condition.
* Default vs non-default intended value, declared a priori (not from any model output). Value rank, default first:
  polarity: affirmative > negated;
  speech_act: statement > question > request/command;
  agent: speaker > addressee > third party;
  time_quantity: now > past > later.
  In each family the variant with the higher-ranked critical value is the default variant, the other is non-default.
  Each dimension: 15 messages with the default variant intended, 15 with the non-default variant intended (50% non-default overall, balanced within dimension).
* Model: each item is assigned one of the four primary models (qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra) by seeded round-robin over a seeded permutation of the items within each dimension x default stratum. The same model supplies every model-made condition of that item.
* Context line: the item files hold no context text (all null). The neutral topic label of the pair (e.g. "plans", "transport") is shown as the context line, "Topic: <topic>". If the topic is missing the context line is omitted.
* Conditions per item: bare (P0 greedy, channel bare, runs/hw1 or runs/hw2); chip1 (channel chip1, the intended variant's cue, same model); nlcue (plain-word cue, runs/hwctl1 channel nlcue; hw2 has no nlcue, so nlcue exists only for hw1 items; the condition gap is documented and the nlcue contrasts are restricted to hw1 items); G1 (the unchanged guard of runs/guard_wc, src/interventions.guard_one with max_retries 2, temperature 0, 96 output tokens, tag I1-guard-v1, seed 1000 for local models, run on the bare input of the same model); reference (the writer's own sentence).
* G1 reads only cues the user supplied. The bare input supplies none, so G1 is expected to be inert except for removing/regenerating unsupplied politeness. This is a property of the frozen guard and is reported, not tuned. The guard policy is not modified.
* Identical-text rule: within an item, model-made conditions whose output text is identical after normalisation (lowercase, collapse whitespace, strip trailing punctuation) are one sentence. It is judged once per listener pair, and every condition inherits that sentence's judgments. The reference is never merged. The stimulus table keeps one row per (item, condition) with a judge_unit id.
* Items whose chosen model returned an empty or unparsed output for bare or chip1 are not replaced; they are reported as a gap and excluded from every contrast involving that condition.

## 3. Listener task and codes
Q1 (primary): "What is the person saying?" Options: reading A, reading B (order randomised per stimulus), "something else / unclear". Readings are the two writer sentences of the pair.
Q2: "How would you respond?" Four fixed options per item: the action implied by the intended reading (correct), the action implied by the opposite reading (opposite), "ask them to say it again / confirm" (clarify), and one dimension-specific third action (other). Option order is randomised.
Q3: confidence 1 to 3.

## 4. Outcomes (per judgment)
* Success = Q1 equals the intended reading.
* Received reversal = Q1 equals the opposite reading of the pair. "Something else / unclear" is neither success nor reversal and is reported separately as unclear.
* Consequential error = Q2 equals the opposite action. Sensitivity: Q2 is not the correct action and not clarify.
* Reversal per 1,000 = 1000 x mean(reversal). SLP-weighted reversal per 1,000 = 1000 x mean(w_d x reversal) with w_d = mean SLP severity of the dimension / 5, from expert_package/returns_slp task 1: polarity (NEG 5,5) 1.0; speech_act (ACT 4,4) 0.8; agent (AGT 4,4) 0.8; time_quantity (TIM 4,4) 0.8. Weights are descriptive, from two raters.
* Ceiling: the reference condition's success rate; it is reported next to every contrast.

## 5. Estimation, primary contrasts, clustering, equivalence
Unit of analysis: the judgment. Condition means are item-balanced: mean over items of the item's mean over its judgments in that condition.
Primary contrasts on success (each paired by item, same items in both arms):
1. chip1 - bare
2. G1 - bare
3. nlcue - chip1, restricted to items that have nlcue (hw1 items), with an equivalence margin of +/-5 percentage points.
Uncertainty: two-way cluster bootstrap, 10,000 resamples, seed 20261117, resampling items and listeners independently with replacement (judgments kept if both their item and listener are drawn, with multiplicity). Percentile 95% CIs. Holm correction over the three primary contrasts for the 95% intervals reported as adjusted intervals (the unadjusted ones are also given).
Equivalence for contrast 3: declared only if the 90% bootstrap interval lies inside [-5, +5] pp (TOST). Otherwise "not shown equivalent"; absence of a difference is never claimed from a non-significant interval.
Secondary (descriptive, same bootstrap): reversal per 1,000 and SLP-weighted per 1,000 per condition, overall and in the non-default-intended stratum; consequential error; unclear share; by dimension; Q3 confidence; bare - reference.
Sensitivity (reported, not primary): logistic mixed model with crossed random intercepts for item and listener (if it fails to converge, the bootstrap stands alone).
The headline is only stated if the data agree: "listeners received the opposite of the intended meaning in X of 1,000 messages without the cue and Y with it", with the 50% non-default design mix stated beside it.

## 6. Exclusions
* Listener: a listener whose reference-condition Q1 success is below 75% (their attention check) is excluded from all analyses; the count is reported and results with them retained are given as a sensitivity.
* Listener: a listener with fewer than 80% of assigned judgments completed is excluded.
* Judgment: missing Q1 is dropped. No outlier-time trimming (time is not collected).
* Item: an item missing a condition's output is dropped from contrasts involving that condition only.
* Nobody judges their own pair or a pair they checked (logic of src/make_frontier_parts.py, src/make_assignments.py --stage 5).
* No exclusion is made on the basis of outcomes. Exclusions are applied identically to all conditions.

## 7. Fallbacks
* Local-model access for the guard run is blocked by Unity or GPU: the guard only needs a call when it flags a candidate; items whose assigned model is local and which need a call are reassigned, before any listener data, to the terra output set (terra-only items); this is documented in analysis/listener/STIMULI_NOTES.md.
* nlcue missing for hw2 items: nlcue restricted to hw1 items (section 2).
* Fewer than 16 usable listeners after exclusions: all results are descriptive and the primary contrasts are labelled underpowered.
* Guard gives identical outputs (expected): guard - bare is reported as exactly the same sentences, with the share of changed items.
