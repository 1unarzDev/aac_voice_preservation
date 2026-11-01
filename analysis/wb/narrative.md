# W-B corpus transfer (AACText): defaults, violations, restoration

Run: **{RUN}** (P0, greedy; qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra). Protocol: orchestration/PREREG_R2.md W-B.
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
