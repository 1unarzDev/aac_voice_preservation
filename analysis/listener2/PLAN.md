# Part 30 Listener Study v2 (confirmatory, text and spoken): frozen analysis plan

Written 2026-11-18, BEFORE the item draw, any generation, any TTS rendering, any listener data. Nothing below changes after outcomes; deviations go to analysis/listener2/DEVIATIONS.md.
Status: not committed; hash-deposit PLAN.md, the draw file and the private key before sheets are sent (as COORDINATOR_STEPS section 7).

## 1. Question, role of people
Part 28 (exploratory, N=120 items) found, on the non-default-intended stratum (60 items, 120 judgments), received reversal bare 66.7 vs chip 0.0 per 1,000, but the interval included zero (chip - bare -41.7 per 1,000 overall [-98.9, +6.9]). Q1: is the reduction confirmed on fresh items? Q2: does it hold when the sentence is HEARD (the realistic AAC channel: speech output), not only read?
~20 adult non-author classmates annotate study materials (consented, paid, nothing collected about them). Not AAC partners, no AAC users, no real-world consequence.

## 2. Stimuli (frozen rules)
* Pool: kept pairs (3 of 3 human checks pass) of data/items/hw.jsonl and hw2.jsonl, MINUS every family used in Part 28 (analysis/listener/draw.json) and Part 29. Non-default-intended variants only (default ranking as Part 28: polarity affirmative>negated; speech_act statement>question>request; agent speaker>addressee>third party; time now>past>later; the variant with the lower-ranked critical value is intended). Reversals only occur here, so default-intended items are not run (the cost: no estimate of harm to default items; stated as limit, Part 28 gave bare 33.3 / chip 16.7 per 1,000 there).
* Draw: src/make_listener_study.py extended with `draw2` (seed 20261118, random.Random, sorted family ids before each draw), 30 items per dimension, N = 120 items (hw and hw2 pooled for speech_act; no family twice). If a dimension has < 30 fresh eligible families, take all and report; the shortfall is not refilled from other dimensions.
* Models: as Part 28 (qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra), seeded round-robin within dimension; same model supplies both conditions of an item. Generation: the existing frozen P0 bare run and chip1 run (same prompts, greedy, same channel code as runs/hw1, runs/hw2); no tuning. An item whose model returns empty/unparsed for either condition is dropped as a pair (reported), not replaced.
* Conditions: bare (P0, no cue) and chip (chip1, the intended variant's cue). No G1, nlcue or reference arms (reference is kept only as 1 attention sentence per listener, see 6).
* Identical-text rule: if bare and chip outputs are identical after normalisation (lowercase, whitespace, trailing punctuation), they are one sentence per modality; every listener-pair judgment is inherited by both conditions (Part 28 rule) and the item contributes a zero difference.
* Modality: text (context line plus sentence on screen) vs audio (context line on screen, sentence only heard). TTS: one fixed neutral voice (Piper en_US-lessac-medium, or Kokoro af_heart if Piper is unavailable; chosen once before rendering, recorded with model hash), 22.05 kHz mono wav, default speed, no SSML or emphasis, rendered from the exact output string including punctuation, loudness-normalised to -23 LUFS. Rendered files are stored in tmp/, deposited with hashes, never hand-edited. Listener may replay once (the replay count is logged by the page; a second replay is disabled). Audio is played on the annotator's own headphones; a headphone/volume check item precedes (a fixed spoken digit sentence, not scored).
* 4 cells per item: {bare, chip} x {text, audio}. Unit = cell.

## 3. Task and codes (as Part 28 Q1 to Q3)
Q1 reading A / reading B (order randomised per stimulus) / something else-unclear; Q2 four fixed responses (correct, opposite, clarify, other); Q3 confidence 1 to 3. Readings are shown as text in both modalities (the audio condition tests how the sentence is heard, not how the choices are read). Tool: annotation_package/rate_items.html with an audio element for the audio cells (new field `audio`, replay cap 1).
Outcomes per judgment: success (Q1 = intended); received reversal (Q1 = opposite reading); unclear; opposite action (Q2 = opposite); sensitivity Q2 neither correct nor clarify.

## 4. Design: Latin square, listeners, load
* 3 listeners per cell, 12 judgments per item, 1,440 judgments. 20 listeners x 72 judgments (~30 s average; ~36 min plus practice 4 items).
* Each listener sees each item AT MOST once (one of the 4 cells). Assignment (src/make_listener_study.py `package2`, balanced by construction): for each item the 12 listener slots are 3 replicates of the 4 cells; listeners are split into 4 groups of 5; within a replicate the group-to-cell map is a seeded cyclic shift of the Latin square so every group sees each cell equally often over items; 12 distinct listeners per item; each listener gets 72 items; each listener's cells balanced 18/18/18/18 within one unit (checked in the balance report, a failed balance blocks the send).
* Exclusions of people: nobody judges a pair they wrote or checked (hw_blocks logic); where this removes a listener from an item the slot goes to the next listener in the seeded order; if impossible, the item is dropped before sending, counted.
* Practice: 4 unscored items (2 text, 2 audio), dropped.
* Attention: 6 reference-sentence items per listener (writer's own sentence, from default items not in the draw; 3 text 3 audio).

## 5. Primary endpoint and exact analysis
PRIMARY: received reversal per 1,000, chip - bare, pooled over modality, over the 120 non-default items. Item-balanced: mean over items of (mean reversal over the item's chip judgments - mean over its bare judgments) x 1000 (6 judgments each side per item).
Test: item-level paired sign-flip permutation test on item differences, 100,000 flips, seed 20261118, two-sided alpha .05; success = p < .05 AND point estimate < 0 (chip lower). Interval: two-way cluster bootstrap (items and listeners independently, B=10,000, seed 20261118, percentile 95%). Both reported; decision rests on the permutation test, the CI is reported with it. Primary confirmed only if both p < .05 and the 95% CI upper bound < 0; if p < .05 but CI includes 0 -> "supported, not confirmed". Non-confirmation is reported as such (a null on fresh items is a result, Part 28's headline is then stated as exploratory).
SECONDARY (one family, Holm over the 5, same permutation/bootstrap, reported with unadjusted and adjusted intervals): (1) success pp chip - bare; (2) opposite action (Q2) per 1,000, chip - bare; (3) unclear share chip - bare; (4) reversal chip - bare separately in text and in audio (reported with each modality's own item-paired test); (5) modality x condition interaction on reversal: (chip-bare)_audio - (chip-bare)_text, item-paired, same bootstrap. Interaction is estimated and not declared absent from a non-significant result; no equivalence claim.
Descriptive: bare/chip by dimension; audio-minus-text for bare (does hearing raise reversal); Q3 confidence; SLP-weighted reversal (weights 1.0 polarity, 0.8 others as Part 28); replay rate; per-model.
Sensitivity (not primary): logistic mixed model with crossed random item and listener intercepts (statsmodels/R if installable; else not run and stated); sensitivity with excluded listeners retained; analysis restricted to items where bare and chip differ in text; analysis with item-level chip true rate not assumed zero.

## 6. Exclusions
Listener: attention success on the 6 reference items < 5 of 6 (<83%); or < 80% of judgments completed; or audio never played on > 25% of audio cells (page log). Excluded listeners removed identically from all cells; results with them retained as sensitivity. Judgment: missing Q1 dropped, practice dropped. Item: missing output in either condition drops the item pair. No exclusion on outcomes, no outlier trimming. If fewer than 16 listeners remain, every result is descriptive and labelled underpowered.
Clustering: dependence from item and listener handled by the item-level test and the two-way bootstrap; judgments never treated as independent.

## 7. Power (from Part 28)
Part 28 non-default: bare 8 reversals in 120 judgments (66.7 per 1,000), chip 0/120. Reversals are concentrated in few items, so power was simulated at the item level: fraction vulnerable items v, bare rate pb, chip rate pc, 6 judgments per item per arm, the exact primary test above (sign-flip permutation, 600 sims per cell, seed 1).
Power, N items = 60 / 80 / 96 / 120:
* pb .067, pc .005, v .15: .84 / .98 / 1.00 / 1.00
* pb .067, pc .010, v .15: .84 / .97 / .99 / 1.00
* pb .050 (shrunk toward zero), pc .010, v .15: .67 / .89 / .95 / .98
* pb .040, pc .005, v .10 (pessimistic): .43 / .70 / .86 / .95
* pb .067, pc .010, v .50 (diffuse): .98 / 1.0 / 1.0 / 1.0
N = 120 gives >= .95 under every planned scenario including the shrunk and pessimistic ones (>= 90% target met). Smallest effect with 90% power at N=120, v .15: about 3.5 reversal per 1,000 net. If the true bare rate is below ~3 per 1,000 the study is underpowered; this is the stated risk (the pilot effect is itself a small count).

## 8. Fallbacks
* GPU/Unity blocked: terra-only (API) generation for items whose assigned model is local; reassign before any listener data and log.
* TTS fails to install: sentence is read aloud-only by a second TTS (Kokoro); if neither, the modality factor is dropped and N rises to 120 x 2 cells (3 listeners each = 720 judgments, same primary).
* Fewer than 30 fresh items in a dimension: take all, N shrinks; power at N >= 96 still >= .86.
* Fewer listeners than 20: items per listener rise to a cap of 90; else cut N by whole dimension blocks (never cherry-picked).

## 9. Build list
1. src/make_listener_study.py: `draw2` (fresh non-default draw, 120 items, seed 20261118, exclude Part 28/29 families), `build2` (stimuli.jsonl from existing runs; run bare+chip1 generation for any model/item lacking an output through ~/research-cluster/bin/research submit aac-llm or the flock lock; API <=4), `tts` (render 240 wavs of unique sentences max, loudness-normalise, hash manifest), `package2` (Latin square, attention, practice, balance report, private key + sha256).
2. 120 items x 2 conditions = 240 sentences (fewer if identical) + 6 x 20 attention sentences (reuse ~30 default items) + 4 practice + 1 headphone check: ~290 wav files in analysis/listener2/audio/ (deposit hashes).
3. rate_items.html: audio field, replay cap 1, play/replay logging.
4. src/score_listener2.py (derived from src/score_listener_study.py): section 5, section 6, the permutation test, bootstrap, power report; written and unit-tested on synthetic data BEFORE sheets return.
5. Judging and assignment: src/make_assignments.py stage 8 sheets; coordinator steps appended to annotation/COORDINATOR_STEPS.md; DEVIATIONS.md created empty.
