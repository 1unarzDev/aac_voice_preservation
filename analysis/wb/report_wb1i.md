# W-B corpus transfer (AACText): defaults, violations, restoration

Run: **wb1i** (P0, greedy; qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra). Protocol: orchestration/PREREG_R2.md W-B.
Code: src/wb_sample.py, src/wb_items.py, src/wb_admissibility.py, src/wb_report.py. Status/resume notes: analysis/wb/STATUS.md.

**Run status.** `wb1` is the full design. `wb1i` is an interim run with every POS-cap4 and full output from all 4 models, plus the restored channel for gpt-6.1-terra only. The local models' restored channel was waiting on the GPU lock (D-019), which r2c1 held during its API phase. Sections A and B (POS-cap4/full) are identical in both runs. In the wb1i interim, the section C restoration effect and the "restored" column of B are terra-only. In wb1 they cover 4 models.

## Headline results (numbers from the tables below; 95% message-cluster bootstrap CIs)

**A. Defaults on confirmed-ambiguous dimensions (POS-cap4).** Under the primary panel, both coders marked 82-99% of (message, dimension) cells ambiguous.
- **Models almost always commit.** The commitment rate is 99.3% (random) and 98.1% (enriched).
- **They usually commit to the unmarked default.** The default share is 84.4% [80.6, 88.2] in the random sample and 77.4% [72.1, 82.1] in the enriched sample.
- **Polarity is the extreme case.** Polarity is affirmative in 98.7% / 99.0% of outputs. When the source was negated, POS-cap4 outputs honoured it in **0/36 (random) and 2/84 (enriched)** cases.
- **Non-default meanings are lost.** Overall, outputs honour a non-default source value only 25.7% [17.3, 34.7] (random) and 31.3% [21.2, 41.9] (enriched) of the time. "Honours source" looks high (70% / 64%) only because most sources carry the default value.
- **Outputs stay within admissible readings.** Values outside both coders' admissible sets are rare: 0.1% random, 1.2% enriched. So the models pick an admissible reading, but systematically the default one.

**B. Violations of supplied commitments.**
- **POS-cap4, primary panel.** Almost nothing counts as "supplied" (40 output rows from 7 random messages; 84 rows from 16 enriched messages, mostly retained "please"). The POS-cap4 violation estimates are therefore uninformative: 17.5% [0, 43] random, 3.6% [0, 12.5] enriched.
- **POS-cap4, strict sensitivity.** Under the strict panel (only "likely" readings count), the supplied-commitment violation rate is 9.3% [4.5, 14.7] random and 6.8% [3.0, 11.8] enriched.
- **Full source.** Violation rates are 4.9% [2.3, 8.0] (random) and 5.7% [3.3, 8.5] (enriched). They are concentrated in agent, speech act and certainty, e.g. a question rewritten as a statement, a plain statement as n/a, or speaker swapped with addressee. Part of this is codebook disagreement between the panel's source coding and the judge's output coding (see caveats).

**C. Focal-cue restoration.** Restoration adds the source's focal cue to POS-cap4, as a chip where the vocabulary allows (131 messages) or as the cue word (8 messages).
- **Interim (wb1i, terra only).** Focal-dimension match rises by **+40.4 pp [+26.3, +54.4] (random, 57 messages)** and **+38.0 pp [+24.1, +51.9] (enriched, 79 messages)**. Restored match is 91.4% (random) and 80.0% (enriched), versus 94.8% / 91.8% for the full source.
- **Polarity gains most.** POS-cap4 polarity match is 2.5-9.1% (pooled models); terra with restored [NOT] reaches 70-73%. A residual gap to full text remains for enriched polarity and certainty.
- **Ineligible.** 21 random messages have no lost focal cue (focal_dim = none) and are excluded. See the table for 4-model results when the run is wb1.

## Caveats
1. **The panel is near-ceiling liberal.** Even with the instruction to list only natural readings, the checklist ("consider each option value") made both codex coders admit almost any value. Ambiguity kappas are low or undefined (-0.01 to 0.79) because prevalence is near 100%, not because the coders disagree (raw agreement 0.86-0.95). The graded strict pass (`p1g`, likely-only) is a sensitivity analysis declared after seeing the primary panel rates but before inspecting any judged output. Under it, polarity is "supplied" (affirmative only) for 97/160 messages. Its A/B estimates are reported separately, and its conclusions match the primary ones (default share 82% / 80%; honours source 56% / 50%).
2. **Source commitments come from the codex panel's pass 2,** where the two coders agree (kappa 0.90-1.00). Output values come from the gpt-6.1-sol J1/J2 judge (general dimensions: J1/J2 agreement, then the layer0 tiebreak). The two use similar but not identical codebooks (e.g. imperatives: agent addressee vs unspecified; "I'd like" counted as a request). Some full-channel "violations" are codebook mismatches, not model errors. The CB rules were not re-checked for this corpus.
3. **Admissibility has no human validation yet.** annotation/wb_audit.json (20 random messages) is prepared and not yet returned. The detector-based enriched strata are not human-validated either.
4. **Inclusion probabilities.** Random sample: SRS of the frame (pi = 80/4831). Enriched pools are disjoint by rarest-first priority after removing the random 80 (pi = 20/|pool|, conditional on the random draw). Estimates are unweighted within sample type. The enriched sample is not prevalence-representative and must not be pooled with the random sample.
5. **Frame exclusions.** The frame excludes messages under 3 words (766), messages with empty POS-cap4 (126) and exact-duplicate texts (419; the first occurrence is kept). The empty-POS-cap4 exclusion is an addition to the brief, made because those messages have no input to expand.
6. **Overlap with sample400.** 20 W-B ids (10 random, 10 enriched) are also in sample400. The ids are in analysis/wb/sample_manifest.json and data/specs/wb_sample.jsonl (`in_sample400`). W-C was not told anything. W-C seed disjointness from W-B should be verified by an id check against data/specs/wb_sample.jsonl when W-C freezes.
7. **Restoration details.** The restored chip is the panel source value's chip when it differs from the detector cue. For politeness, a retained "please" makes restoration nearly redundant (+10 pp). Messages with focal_dim = none (21 random) have no restored channel. They are counted as ineligible.
8. **Generation and judging.** Greedy, one draw, P0 only. Unresolved focal critical labels (J1 != J2) are excluded from the primary table and included in the J1-fallback sensitivity table. Their counts are given below.


---

Generated by `python src/wb_report.py` (run wb1i, P0, 4 models). Protocol: orchestration/PREREG_R2.md W-B. All intervals: 95% percentile bootstrap over messages (2000 reps). Random (SRS, pi = 0.0166) and enriched (disjoint cue pools, pi in certainty 0.084, polarity 0.049, politeness 0.038, speech_act 0.011) samples are never pooled.

## Sample and denominators

Frame: 6142 nonempty AACText lines -> exclusions {'lt3_words': 766, 'empty_pos_cap4': 126, 'duplicate_text': 419} -> N = 4831 unique messages. Drawn: {'random': 80, 'enriched_certainty': 20, 'enriched_polarity': 20, 'enriched_politeness': 20, 'enriched_speech_act': 20}. Overlap with sample400: 20 ids ({'random': 10, 'enriched': 10}); ids listed in analysis/wb/sample_manifest.json.

Outputs per sample x channel (one per message x model; invalid = empty/failed generation; critical_resolved = J1==J2 on the focal critical question):

| sample | channel | outputs | valid | critical_resolved |
|---|---|---|---|---|
| enriched | full | 320 | 320 | 317 |
| enriched | pos_cap4 | 308 | 308 | 303 |
| enriched | restored | 80 | 80 | 80 |
| random | full | 320 | 320 | 314 |
| random | pos_cap4 | 320 | 320 | 318 |
| random | restored | 59 | 59 | 58 |

Panel status of every (message, dimension), POS-cap4 input (both coders): confirmed_ambiguous = both list >=2 values; supplied = both list exactly the source value; coder_disagree = the coders differ; unambiguous_wrong = both unambiguous but not equal to their source value (or source value disputed). Only the first two are eligible for A/B.

| sample | dim | coder_disagree | confirmed_ambiguous | supplied | unambiguous_wrong |
|---|---|---|---|---|---|
| enriched | agent | 11 | 67 | 2 | 0 |
| enriched | certainty | 10 | 64 | 5 | 1 |
| enriched | polarity | 3 | 77 | 0 | 0 |
| enriched | politeness | 4 | 62 | 14 | 0 |
| enriched | speech_act | 7 | 73 | 0 | 0 |
| random | agent | 13 | 65 | 2 | 0 |
| random | certainty | 3 | 74 | 3 | 0 |
| random | polarity | 5 | 75 | 0 | 0 |
| random | politeness | 4 | 72 | 4 | 0 |
| random | speech_act | 7 | 72 | 1 | 0 |

## Codex panel agreement (source-blind pass 1, source-revealed pass 2)

Coders: gpt-5.6-sol, gpt-6-astra, effort medium, batches of 20, separate sessions per pass.

| dim | ambiguous rate c1 / c2 | ambiguous agree (kappa) | confirmed amb n | supplied agree (kappa) | supplied n | source value agree (kappa) |
|---|---|---|---|---|---|---|
| polarity | 0.96 / 0.99 | 0.95 (-0.011) | 152 | 0.95 (-0.011) | 0 | 0.97 (0.93) |
| speech_act | 0.91 / 0.99 | 0.91 (0.115) | 145 | 0.93 (0.144) | 1 | 0.98 (0.971) |
| agent | 0.82 / 0.96 | 0.86 (0.31) | 132 | 0.89 (0.279) | 4 | 0.93 (0.899) |
| certainty | 0.86 / 0.94 | 0.92 (0.544) | 138 | 0.93 (0.562) | 8 | 0.97 (0.959) |
| politeness | 0.84 / 0.89 | 0.95 (0.79) | 134 | 0.95 (0.79) | 18 | 1.00 (1.0) |

Human audit of 20 random messages: annotation/wb_audit.json (not yet returned).

## A. Default commitments on confirmed-ambiguous dimensions (POS-cap4)

Rows = POS-cap4 outputs (message x model) on (message, dim) that BOTH coders marked ambiguous. committed = definite value (not mixed/unclear, unspecified, other); default = the unmarked value (affirmative / statement / speaker / plain assertion / none); honours source = matches the panel-consensus source value (rows with disputed source value are dropped from that column only); outside admissible = a value neither coder listed.

### random

| dim | eligible msgs | committed | takes default | honours source | honours NON-default source | outside admissible |
|---|---|---|---|---|---|---|
| polarity | 75 | 299/300 = 99.7% [99.0, 100.0] (75 msgs) | 296/300 = 98.7% [97.3, 99.7] (75 msgs) | 254/300 = 84.7% [76.7, 92.3] (75 msgs) | 0/36 = 0.0% [0.0, 0.0] (9 msgs) | 0/300 = 0.0% [0.0, 0.0] (75 msgs) |
| speech_act | 72 | 287/288 = 99.7% [99.0, 100.0] (72 msgs) | 230/288 = 79.9% [73.3, 86.1] (72 msgs) | 178/288 = 61.8% [51.7, 71.2] (72 msgs) | 33/124 = 26.6% [16.1, 37.9] (31 msgs) | 0/288 = 0.0% [0.0, 0.0] (72 msgs) |
| agent | 65 | 252/260 = 96.9% [94.2, 99.2] (65 msgs) | 168/260 = 64.6% [56.5, 73.1] (65 msgs) | 120/259 = 46.3% [36.4, 56.4] (65 msgs) | 41/140 = 29.3% [19.3, 39.3] (35 msgs) | 2/260 = 0.8% [0.0, 1.9] (65 msgs) |
| certainty | 74 | 296/296 = 100.0% [100.0, 100.0] (74 msgs) | 237/296 = 80.1% [73.6, 86.5] (74 msgs) | 174/296 = 58.8% [49.7, 68.2] (74 msgs) | 37/132 = 28.0% [18.2, 38.6] (33 msgs) | 0/296 = 0.0% [0.0, 0.0] (74 msgs) |
| politeness | 72 | 288/288 = 100.0% [100.0, 100.0] (72 msgs) | 278/288 = 96.5% [93.8, 98.6] (72 msgs) | 278/288 = 96.5% [93.4, 99.0] (72 msgs) | n/a (0) | 0/288 = 0.0% [0.0, 0.0] (72 msgs) |
| ALL | 76 | 1422/1432 = 99.3% [98.8, 99.7] (76 msgs) | 1209/1432 = 84.4% [80.6, 88.2] (76 msgs) | 1004/1431 = 70.2% [65.1, 75.3] (76 msgs) | 111/432 = 25.7% [17.3, 34.7] (48 msgs) | 2/1432 = 0.1% [0.0, 0.4] (76 msgs) |

Direction (output value distribution) on confirmed-ambiguous dims, random:

| dim | out | n | share |
|---|---|---|---|
| agent | addressee | 54 | 0.208 |
| agent | speaker | 168 | 0.649 |
| agent | third party | 22 | 0.085 |
| agent | unspecified | 8 | 0.031 |
| agent | we/joint | 7 | 0.027 |
| certainty | hedged/uncertain | 8 | 0.027 |
| certainty | n/a (question/request) | 49 | 0.166 |
| certainty | plain assertion | 237 | 0.801 |
| certainty | strongly certain/emphatic | 2 | 0.007 |
| polarity | affirmative | 296 | 0.987 |
| polarity | mixed/unclear | 1 | 0.003 |
| polarity | negated | 3 | 0.01 |
| politeness | none | 278 | 0.965 |
| politeness | please | 9 | 0.031 |
| politeness | softened request (could you/would you mind) | 1 | 0.003 |
| speech_act | offer/suggestion | 5 | 0.017 |
| speech_act | other | 1 | 0.003 |
| speech_act | question | 18 | 0.062 |
| speech_act | refusal | 4 | 0.014 |
| speech_act | request/command | 30 | 0.104 |
| speech_act | statement | 230 | 0.799 |

By model (random, all dims):

| model | takes_default | honours_source |
|---|---|---|
| gemma3-4b | 294/358 = 82.1% [75.8, 88.2] (76 msgs) | 252/358 = 70.4% [64.5, 76.5] (76 msgs) |
| gpt-6.1-terra | 280/358 = 78.2% [72.2, 84.5] (76 msgs) | 257/357 = 72.0% [65.6, 77.9] (76 msgs) |
| llama3.1-8b | 323/358 = 90.2% [85.9, 94.1] (76 msgs) | 251/358 = 70.1% [63.8, 76.5] (76 msgs) |
| qwen2.5-7b | 312/358 = 87.2% [82.2, 91.8] (76 msgs) | 244/358 = 68.2% [62.3, 74.6] (76 msgs) |

### enriched

| dim | eligible msgs | committed | takes default | honours source | honours NON-default source | outside admissible |
|---|---|---|---|---|---|---|
| polarity | 77 | 298/299 = 99.7% [99.0, 100.0] (77 msgs) | 296/299 = 99.0% [97.7, 100.0] (77 msgs) | 209/299 = 69.9% [59.3, 79.7] (77 msgs) | 2/84 = 2.4% [0.0, 6.0] (21 msgs) | 1/299 = 0.3% [0.0, 1.0] (77 msgs) |
| speech_act | 73 | 281/283 = 99.3% [98.2, 100.0] (73 msgs) | 193/283 = 68.2% [58.8, 77.4] (73 msgs) | 172/283 = 60.8% [50.5, 71.3] (73 msgs) | 60/146 = 41.1% [27.0, 55.5] (38 msgs) | 1/283 = 0.4% [0.0, 1.1] (73 msgs) |
| agent | 67 | 239/259 = 92.3% [87.0, 96.9] (67 msgs) | 133/259 = 51.4% [41.0, 61.5] (67 msgs) | 138/257 = 53.7% [43.6, 63.7] (67 msgs) | 65/144 = 45.1% [31.2, 59.0] (36 msgs) | 13/259 = 5.0% [1.5, 10.0] (67 msgs) |
| certainty | 64 | 247/247 = 100.0% [100.0, 100.0] (64 msgs) | 179/247 = 72.5% [63.2, 81.2] (64 msgs) | 104/247 = 42.1% [31.2, 52.9] (64 msgs) | 37/156 = 23.7% [12.8, 35.3] (39 msgs) | 0/247 = 0.0% [0.0, 0.0] (64 msgs) |
| politeness | 62 | 239/239 = 100.0% [100.0, 100.0] (62 msgs) | 226/239 = 94.6% [91.3, 97.5] (62 msgs) | 220/239 = 92.1% [86.4, 96.7] (62 msgs) | 4/14 = 28.6% [5.9, 75.0] (5 msgs) | 0/239 = 0.0% [0.0, 0.0] (62 msgs) |
| ALL | 77 | 1304/1327 = 98.3% [97.1, 99.3] (77 msgs) | 1027/1327 = 77.4% [71.9, 82.2] (77 msgs) | 843/1325 = 63.6% [58.1, 68.5] (77 msgs) | 168/544 = 30.9% [20.7, 41.5] (69 msgs) | 15/1327 = 1.1% [0.3, 2.1] (77 msgs) |

Direction (output value distribution) on confirmed-ambiguous dims, enriched:

| dim | out | n | share |
|---|---|---|---|
| agent | addressee | 82 | 0.319 |
| agent | speaker | 133 | 0.518 |
| agent | third party | 15 | 0.058 |
| agent | unspecified | 20 | 0.078 |
| agent | we/joint | 7 | 0.027 |
| certainty | hedged/uncertain | 20 | 0.081 |
| certainty | n/a (question/request) | 48 | 0.194 |
| certainty | plain assertion | 179 | 0.725 |
| polarity | affirmative | 296 | 0.99 |
| polarity | mixed/unclear | 1 | 0.003 |
| polarity | negated | 2 | 0.007 |
| politeness | none | 226 | 0.946 |
| politeness | please | 10 | 0.042 |
| politeness | thanks/apology | 3 | 0.013 |
| speech_act | offer/suggestion | 7 | 0.025 |
| speech_act | other | 2 | 0.007 |
| speech_act | question | 12 | 0.042 |
| speech_act | request/command | 69 | 0.244 |
| speech_act | statement | 193 | 0.682 |

By model (enriched, all dims):

| model | takes_default | honours_source |
|---|---|---|
| gemma3-4b | 249/328 = 75.9% [69.2, 82.1] (74 msgs) | 204/327 = 62.4% [56.9, 67.9] (74 msgs) |
| gpt-6.1-terra | 256/343 = 74.6% [67.8, 81.1] (77 msgs) | 227/343 = 66.2% [60.1, 72.1] (77 msgs) |
| llama3.1-8b | 268/328 = 81.7% [76.1, 86.8] (74 msgs) | 205/328 = 62.5% [56.9, 68.4] (74 msgs) |
| qwen2.5-7b | 254/328 = 77.4% [71.0, 83.3] (74 msgs) | 207/327 = 63.3% [57.9, 68.8] (74 msgs) |

## B. Violations of supplied, expressible commitments

POS-cap4: (message, dim) supplied per both coders and source value consensus & expressible. restored: the focal dimension (supplied by the chip/cue word). full: every dim with an expressible consensus source value (the source supplies all). violation = output does not honour the source value. Ineligible rows are counted in the status table above.

### random

| dim | POS-cap4 (supplied) | restored (focal) | full |
|---|---|---|---|
| polarity | n/a (0) | 1/9 = 11.1% [0.0, 33.3] (9 msgs) | 0/308 = 0.0% [0.0, 0.0] (77 msgs) |
| speech_act | 3/4 = 75.0% [75.0, 75.0] (1 msgs) | 2/20 = 10.0% [0.0, 25.0] (20 msgs) | 20/318 = 6.3% [2.2, 11.0] (80 msgs) |
| agent | 1/8 = 12.5% [0.0, 25.0] (2 msgs) | 0/24 = 0.0% [0.0, 0.0] (24 msgs) | 26/280 = 9.3% [3.6, 16.1] (70 msgs) |
| certainty | 3/12 = 25.0% [0.0, 75.0] (3 msgs) | 0/1 = 0.0% [0.0, 0.0] (1 msgs) | 23/312 = 7.4% [3.2, 12.8] (78 msgs) |
| politeness | 0/16 = 0.0% [0.0, 0.0] (4 msgs) | 0/1 = 0.0% [0.0, 0.0] (1 msgs) | 6/320 = 1.9% [0.3, 3.8] (80 msgs) |
| ALL | 7/40 = 17.5% [0.0, 43.2] (7 msgs) | 3/55 = 5.5% [0.0, 12.7] (55 msgs) | 75/1538 = 4.9% [2.3, 8.1] (80 msgs) |

By model (random, all dims):

| model | pos_cap4 | restored | full |
|---|---|---|---|
| gemma3-4b | 2/10 = 20.0% [0.0, 54.5] (7 msgs) | n/a (0) | 18/384 = 4.7% [1.8, 8.2] (80 msgs) |
| gpt-6.1-terra | 0/10 = 0.0% [0.0, 0.0] (7 msgs) | 3/55 = 5.5% [0.0, 12.7] (55 msgs) | 15/385 = 3.9% [1.0, 7.2] (80 msgs) |
| llama3.1-8b | 2/10 = 20.0% [0.0, 54.5] (7 msgs) | n/a (0) | 28/385 = 7.3% [3.7, 11.5] (80 msgs) |
| qwen2.5-7b | 3/10 = 30.0% [0.0, 66.7] (7 msgs) | n/a (0) | 14/384 = 3.6% [1.0, 6.8] (80 msgs) |

Most frequent violation patterns (random):

| channel | dim | src | out | n |
|---|---|---|---|---|
| full | certainty | plain assertion | n/a (question/request) | 10 |
| full | certainty | n/a (question/request) | plain assertion | 9 |
| full | agent | addressee | speaker | 9 |
| full | agent | speaker | addressee | 8 |
| full | speech_act | request/command | statement | 7 |
| full | speech_act | statement | request/command | 7 |
| full | agent | addressee | unspecified | 5 |
| full | politeness | none | please | 5 |
| full | certainty | hedged/uncertain | plain assertion | 4 |
| full | speech_act | statement | question | 3 |
| pos_cap4 | speech_act | question | statement | 3 |
| pos_cap4 | certainty | n/a (question/request) | plain assertion | 3 |

### enriched

| dim | POS-cap4 (supplied) | restored (focal) | full |
|---|---|---|---|
| polarity | n/a (0) | 0/11 = 0.0% [0.0, 0.0] (11 msgs) | 2/276 = 0.7% [0.0, 1.8] (69 msgs) |
| speech_act | n/a (0) | 4/20 = 20.0% [5.0, 40.0] (20 msgs) | 23/296 = 7.8% [3.0, 13.2] (74 msgs) |
| agent | 3/8 = 37.5% [0.0, 75.0] (2 msgs) | n/a (0) | 30/280 = 10.7% [4.6, 18.2] (70 msgs) |
| certainty | 0/20 = 0.0% [0.0, 0.0] (5 msgs) | 5/18 = 27.8% [11.1, 50.0] (18 msgs) | 23/312 = 7.4% [2.6, 12.8] (78 msgs) |
| politeness | 0/56 = 0.0% [0.0, 0.0] (14 msgs) | 1/20 = 5.0% [0.0, 15.0] (20 msgs) | 7/320 = 2.2% [0.3, 5.3] (80 msgs) |
| ALL | 3/84 = 3.6% [0.0, 12.5] (16 msgs) | 10/69 = 14.5% [7.2, 23.2] (69 msgs) | 85/1484 = 5.7% [3.3, 8.6] (80 msgs) |

By model (enriched, all dims):

| model | pos_cap4 | restored | full |
|---|---|---|---|
| gemma3-4b | 1/21 = 4.8% [0.0, 16.7] (16 msgs) | n/a (0) | 17/371 = 4.6% [2.2, 7.5] (80 msgs) |
| gpt-6.1-terra | 0/21 = 0.0% [0.0, 0.0] (16 msgs) | 10/69 = 14.5% [7.2, 23.2] (69 msgs) | 16/371 = 4.3% [1.9, 7.1] (80 msgs) |
| llama3.1-8b | 1/21 = 4.8% [0.0, 15.8] (16 msgs) | n/a (0) | 34/371 = 9.2% [5.1, 13.3] (80 msgs) |
| qwen2.5-7b | 1/21 = 4.8% [0.0, 15.8] (16 msgs) | n/a (0) | 18/371 = 4.9% [2.4, 8.0] (80 msgs) |

Most frequent violation patterns (enriched):

| channel | dim | src | out | n |
|---|---|---|---|---|
| full | agent | speaker | addressee | 11 |
| full | agent | speaker | unspecified | 8 |
| full | certainty | plain assertion | n/a (question/request) | 8 |
| full | speech_act | statement | request/command | 8 |
| full | certainty | strongly certain/emphatic | plain assertion | 6 |
| restored | certainty | plain assertion | hedged/uncertain | 5 |
| full | agent | third party | unspecified | 4 |
| full | agent | speaker | third party | 4 |
| full | speech_act | request/command | statement | 4 |
| full | politeness | none | thanks/apology | 4 |
| full | certainty | hedged/uncertain | plain assertion | 4 |
| full | speech_act | refusal | statement | 4 |

## Sensitivity: strict admissibility (graded pass p1g, only 'likely' readings count)

Same estimands as A and B(POS-cap4) with the panel status recomputed from a separate graded source-blind pass in which each reading is tagged likely/possible (declared after the primary pass showed near-ceiling ambiguity, before any judged output was inspected).

| sample | dim | coder_disagree | confirmed_ambiguous | supplied | unambiguous_wrong |
|---|---|---|---|---|---|
| enriched | agent | 29 | 24 | 24 | 3 |
| enriched | certainty | 23 | 28 | 25 | 4 |
| enriched | polarity | 14 | 12 | 43 | 11 |
| enriched | politeness | 20 | 10 | 49 | 1 |
| enriched | speech_act | 18 | 35 | 25 | 2 |
| random | agent | 19 | 35 | 18 | 8 |
| random | certainty | 18 | 43 | 17 | 2 |
| random | polarity | 11 | 13 | 54 | 2 |
| random | politeness | 20 | 12 | 48 | 0 |
| random | speech_act | 15 | 43 | 18 | 4 |

| sample | dim | A: eligible msgs | A: takes default | A: honours source | B: POS-cap4 supplied violation |
|---|---|---|---|---|---|
| random | polarity | 13 | 51/52 = 98.1% [94.2, 100.0] (13 msgs) | 27/52 = 51.9% [26.9, 80.8] (13 msgs) | 0/216 = 0.0% [0.0, 0.0] (54 msgs) |
| random | speech_act | 43 | 142/172 = 82.6% [74.4, 89.5] (43 msgs) | 99/172 = 57.6% [44.8, 70.9] (43 msgs) | 16/72 = 22.2% [8.3, 37.5] (18 msgs) |
| random | agent | 35 | 100/140 = 71.4% [60.0, 82.1] (35 msgs) | 67/140 = 47.9% [34.3, 61.4] (35 msgs) | 17/68 = 25.0% [10.3, 41.2] (17 msgs) |
| random | certainty | 43 | 148/172 = 86.0% [79.1, 91.9] (43 msgs) | 93/172 = 54.1% [40.7, 67.4] (43 msgs) | 23/68 = 33.8% [19.1, 50.0] (17 msgs) |
| random | politeness | 12 | 39/48 = 81.2% [68.8, 93.8] (12 msgs) | 39/48 = 81.2% [68.8, 91.7] (12 msgs) | 1/192 = 0.5% [0.0, 1.6] (48 msgs) |
| random | ALL | 56 | 480/584 = 82.2% [76.1, 87.8] (56 msgs) | 325/584 = 55.7% [44.7, 65.5] (56 msgs) | 57/616 = 9.3% [4.5, 14.6] (69 msgs) |
| enriched | polarity | 12 | 48/48 = 100.0% [100.0, 100.0] (12 msgs) | 28/48 = 58.3% [33.3, 83.3] (12 msgs) | 7/163 = 4.3% [0.0, 10.8] (43 msgs) |
| enriched | speech_act | 35 | 112/140 = 80.0% [69.3, 90.0] (35 msgs) | 63/140 = 45.0% [30.7, 60.7] (35 msgs) | 8/92 = 8.7% [1.1, 19.6] (23 msgs) |
| enriched | agent | 24 | 61/96 = 63.5% [47.9, 78.2] (24 msgs) | 46/96 = 47.9% [31.2, 63.5] (24 msgs) | 11/89 = 12.4% [2.4, 24.7] (23 msgs) |
| enriched | certainty | 28 | 89/112 = 79.5% [68.8, 89.3] (28 msgs) | 45/112 = 40.2% [24.1, 56.2] (28 msgs) | 10/90 = 11.1% [2.2, 22.6] (24 msgs) |
| enriched | politeness | 10 | 38/40 = 95.0% [87.5, 100.0] (10 msgs) | 34/40 = 85.0% [62.5, 100.0] (10 msgs) | 2/184 = 1.1% [0.0, 2.8] (49 msgs) |
| enriched | ALL | 45 | 348/436 = 79.8% [71.3, 87.2] (45 msgs) | 216/436 = 49.5% [39.5, 59.0] (45 msgs) | 38/618 = 6.1% [2.4, 10.9] (64 msgs) |

## C. Focal-cue restoration effect (critical question = focal dimension)

Per (message, model): critical_match of the focal critical label (judge J1==J2; disagreements excluded and counted) for POS-cap4, restored and full. Effect = restored - POS-cap4, paired. Messages with focal_dim = none (random sample, no lost focal-type cue) have no restored channel and are ineligible. 'focal ambiguous' restricts to messages whose focal dim is confirmed ambiguous at POS-cap4.

### critical labels: J1==J2 only

| sample | subset | focal msgs (ineligible) | POS-cap4 match | restored match | full match | restored - POS-cap4 | full - restored |
|---|---|---|---|---|---|---|---|
| random | all focal | 59 (21) | 102/234 = 43.6% [33.3, 53.9] (59 msgs) | 53/58 = 91.4% [82.8, 98.3] (58 msgs) | 218/230 = 94.8% [89.5, 99.1] (58 msgs) | +40.4 pp [+26.3, +54.4] (n=57 pairs, 57 msgs) | +3.6 pp [-3.6, +12.5] (n=56 pairs, 56 msgs) |
| random | focal ambiguous | 53 (-) | 87/211 = 41.2% [29.9, 51.9] (53 msgs) | 48/53 = 90.6% [83.0, 98.1] (53 msgs) | 194/206 = 94.2% [88.2, 99.0] (52 msgs) | +44.2 pp [+30.8, +57.7] (n=52 pairs, 52 msgs) | +3.9 pp [-5.9, +13.7] (n=51 pairs, 51 msgs) |
| random | focal=polarity | 11 (-) | 4/44 = 9.1% [0.0, 27.3] (11 msgs) | 8/11 = 72.7% [45.5, 100.0] (11 msgs) | 42/44 = 95.5% [86.4, 100.0] (11 msgs) | +63.6 pp [+36.4, +90.9] (n=11 pairs, 11 msgs) | +27.3 pp [+0.0, +54.5] (n=11 pairs, 11 msgs) |
| random | focal=speech_act | 20 (-) | 21/80 = 26.2% [12.5, 42.5] (20 msgs) | 18/20 = 90.0% [75.0, 100.0] (20 msgs) | 72/79 = 91.1% [77.9, 100.0] (20 msgs) | +45.0 pp [+20.0, +70.0] (n=20 pairs, 20 msgs) | +0.0 pp [-15.8, +15.8] (n=19 pairs, 19 msgs) |
| random | focal=agent | 26 (-) | 72/102 = 70.6% [57.8, 82.5] (26 msgs) | 25/25 = 100.0% [100.0, 100.0] (25 msgs) | 96/99 = 97.0% [90.7, 100.0] (25 msgs) | +25.0 pp [+8.3, +41.8] (n=24 pairs, 24 msgs) | -4.2 pp [-12.5, +0.0] (n=24 pairs, 24 msgs) |
| random | focal=certainty | 1 (-) | 1/4 = 25.0% [25.0, 25.0] (1 msgs) | 1/1 = 100.0% [100.0, 100.0] (1 msgs) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | +100.0 pp [+100.0, +100.0] (n=1 pairs, 1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) |
| random | focal=politeness | 1 (-) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | 1/1 = 100.0% [100.0, 100.0] (1 msgs) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) |
| enriched | all focal | 80 (0) | 110/303 = 36.3% [26.9, 46.7] (79 msgs) | 64/80 = 80.0% [71.2, 87.5] (80 msgs) | 291/317 = 91.8% [86.1, 96.2] (80 msgs) | +38.0 pp [+24.1, +51.9] (n=79 pairs, 79 msgs) | +15.2 pp [+6.3, +24.1] (n=79 pairs, 79 msgs) |
| enriched | focal ambiguous | 66 (-) | 57/250 = 22.8% [14.3, 32.0] (65 msgs) | 50/66 = 75.8% [65.2, 86.4] (66 msgs) | 237/261 = 90.8% [84.6, 96.2] (66 msgs) | +46.2 pp [+30.7, +60.0] (n=65 pairs, 65 msgs) | +18.5 pp [+7.7, +29.2] (n=65 pairs, 65 msgs) |
| enriched | focal=polarity | 20 (-) | 2/80 = 2.5% [0.0, 6.2] (20 msgs) | 14/20 = 70.0% [50.0, 90.0] (20 msgs) | 73/80 = 91.2% [80.0, 98.8] (20 msgs) | +60.0 pp [+40.0, +80.0] (n=20 pairs, 20 msgs) | +25.0 pp [+0.0, +45.0] (n=20 pairs, 20 msgs) |
| enriched | focal=speech_act | 20 (-) | 19/80 = 23.8% [8.8, 40.0] (20 msgs) | 16/20 = 80.0% [60.0, 95.0] (20 msgs) | 74/80 = 92.5% [81.2, 100.0] (20 msgs) | +45.0 pp [+20.0, +70.0] (n=20 pairs, 20 msgs) | +15.0 pp [+0.0, +30.0] (n=20 pairs, 20 msgs) |
| enriched | focal=certainty | 20 (-) | 32/75 = 42.7% [22.7, 64.9] (19 msgs) | 15/20 = 75.0% [55.0, 90.0] (20 msgs) | 70/77 = 90.9% [77.3, 100.0] (20 msgs) | +36.8 pp [+0.0, +73.7] (n=19 pairs, 19 msgs) | +21.1 pp [+0.0, +42.2] (n=19 pairs, 19 msgs) |
| enriched | focal=politeness | 20 (-) | 57/68 = 83.8% [66.2, 98.5] (20 msgs) | 19/20 = 95.0% [85.0, 100.0] (20 msgs) | 74/80 = 92.5% [81.2, 100.0] (20 msgs) | +10.0 pp [+0.0, +25.0] (n=20 pairs, 20 msgs) | +0.0 pp [+0.0, +0.0] (n=20 pairs, 20 msgs) |

By model:

| sample | model | pos_cap4 | restored | effect |
|---|---|---|---|---|
| enriched | gemma3-4b | 27/75 = 36.0% [24.0, 46.7] (75 msgs) | n/a (0) | n/a (0) |
| enriched | gpt-6.1-terra | 33/79 = 41.8% [30.4, 51.9] (79 msgs) | 64/80 = 80.0% [70.0, 88.8] (80 msgs) | +38.0 pp [+24.1, +50.6] (n=79 pairs, 79 msgs) |
| enriched | llama3.1-8b | 25/75 = 33.3% [22.7, 44.0] (75 msgs) | n/a (0) | n/a (0) |
| enriched | qwen2.5-7b | 25/74 = 33.8% [24.3, 44.6] (74 msgs) | n/a (0) | n/a (0) |
| random | gemma3-4b | 27/59 = 45.8% [33.9, 59.3] (59 msgs) | n/a (0) | n/a (0) |
| random | gpt-6.1-terra | 29/57 = 50.9% [38.6, 63.2] (57 msgs) | 53/58 = 91.4% [82.8, 98.3] (58 msgs) | +40.4 pp [+26.3, +54.4] (n=57 pairs, 57 msgs) |
| random | llama3.1-8b | 25/59 = 42.4% [30.5, 54.2] (59 msgs) | n/a (0) | n/a (0) |
| random | qwen2.5-7b | 21/59 = 35.6% [23.7, 47.5] (59 msgs) | n/a (0) | n/a (0) |

### critical labels: J1 fallback on disagreement (sensitivity)

| sample | subset | focal msgs (ineligible) | POS-cap4 match | restored match | full match | restored - POS-cap4 | full - restored |
|---|---|---|---|---|---|---|---|
| random | all focal | 59 (21) | 102/236 = 43.2% [32.6, 53.8] (59 msgs) | 54/59 = 91.5% [84.7, 98.3] (59 msgs) | 223/236 = 94.5% [89.0, 99.2] (59 msgs) | +42.4 pp [+28.8, +55.9] (n=59 pairs, 59 msgs) | +5.1 pp [-3.4, +13.6] (n=59 pairs, 59 msgs) |
| random | focal ambiguous | 53 (-) | 87/212 = 41.0% [30.2, 52.4] (53 msgs) | 48/53 = 90.6% [81.1, 98.1] (53 msgs) | 199/212 = 93.9% [87.3, 99.1] (53 msgs) | +45.3 pp [+30.2, +58.5] (n=53 pairs, 53 msgs) | +5.7 pp [-3.8, +15.1] (n=53 pairs, 53 msgs) |
| random | focal=polarity | 11 (-) | 4/44 = 9.1% [0.0, 27.3] (11 msgs) | 8/11 = 72.7% [45.5, 100.0] (11 msgs) | 42/44 = 95.5% [86.4, 100.0] (11 msgs) | +63.6 pp [+36.4, +90.9] (n=11 pairs, 11 msgs) | +27.3 pp [+0.0, +54.5] (n=11 pairs, 11 msgs) |
| random | focal=speech_act | 20 (-) | 21/80 = 26.2% [12.5, 41.2] (20 msgs) | 18/20 = 90.0% [75.0, 100.0] (20 msgs) | 73/80 = 91.2% [77.5, 100.0] (20 msgs) | +45.0 pp [+19.9, +70.0] (n=20 pairs, 20 msgs) | +5.0 pp [-10.0, +25.0] (n=20 pairs, 20 msgs) |
| random | focal=agent | 26 (-) | 72/104 = 69.2% [56.7, 81.7] (26 msgs) | 26/26 = 100.0% [100.0, 100.0] (26 msgs) | 100/104 = 96.2% [88.5, 100.0] (26 msgs) | +30.8 pp [+15.4, +50.0] (n=26 pairs, 26 msgs) | -3.8 pp [-11.5, +0.0] (n=26 pairs, 26 msgs) |
| random | focal=certainty | 1 (-) | 1/4 = 25.0% [25.0, 25.0] (1 msgs) | 1/1 = 100.0% [100.0, 100.0] (1 msgs) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | +100.0 pp [+100.0, +100.0] (n=1 pairs, 1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) |
| random | focal=politeness | 1 (-) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | 1/1 = 100.0% [100.0, 100.0] (1 msgs) | 4/4 = 100.0% [100.0, 100.0] (1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) | +0.0 pp [+0.0, +0.0] (n=1 pairs, 1 msgs) |
| enriched | all focal | 80 (0) | 110/308 = 35.7% [26.1, 45.9] (80 msgs) | 64/80 = 80.0% [70.0, 88.8] (80 msgs) | 292/320 = 91.2% [85.6, 96.2] (80 msgs) | +38.8 pp [+25.0, +52.5] (n=80 pairs, 80 msgs) | +13.8 pp [+3.8, +23.8] (n=80 pairs, 80 msgs) |
| enriched | focal ambiguous | 66 (-) | 57/255 = 22.4% [14.3, 31.4] (66 msgs) | 50/66 = 75.8% [65.2, 86.4] (66 msgs) | 238/264 = 90.2% [83.3, 96.2] (66 msgs) | +47.0 pp [+31.8, +62.1] (n=66 pairs, 66 msgs) | +16.7 pp [+6.1, +28.8] (n=66 pairs, 66 msgs) |
| enriched | focal=polarity | 20 (-) | 2/80 = 2.5% [0.0, 6.2] (20 msgs) | 14/20 = 70.0% [50.0, 90.0] (20 msgs) | 73/80 = 91.2% [80.0, 98.8] (20 msgs) | +60.0 pp [+40.0, +80.0] (n=20 pairs, 20 msgs) | +25.0 pp [+0.0, +50.0] (n=20 pairs, 20 msgs) |
| enriched | focal=speech_act | 20 (-) | 19/80 = 23.8% [10.0, 40.0] (20 msgs) | 16/20 = 80.0% [60.0, 95.0] (20 msgs) | 74/80 = 92.5% [81.2, 100.0] (20 msgs) | +45.0 pp [+20.0, +70.0] (n=20 pairs, 20 msgs) | +15.0 pp [+0.0, +30.0] (n=20 pairs, 20 msgs) |
| enriched | focal=certainty | 20 (-) | 32/80 = 40.0% [20.0, 61.3] (20 msgs) | 15/20 = 75.0% [55.0, 90.0] (20 msgs) | 71/80 = 88.8% [73.8, 100.0] (20 msgs) | +40.0 pp [+5.0, +75.0] (n=20 pairs, 20 msgs) | +15.0 pp [-10.0, +40.0] (n=20 pairs, 20 msgs) |
| enriched | focal=politeness | 20 (-) | 57/68 = 83.8% [67.6, 98.2] (20 msgs) | 19/20 = 95.0% [85.0, 100.0] (20 msgs) | 74/80 = 92.5% [81.2, 100.0] (20 msgs) | +10.0 pp [+0.0, +25.0] (n=20 pairs, 20 msgs) | +0.0 pp [+0.0, +0.0] (n=20 pairs, 20 msgs) |

Unresolved focal critical labels (J1 != J2): 17 of 1407 valid output rows.

