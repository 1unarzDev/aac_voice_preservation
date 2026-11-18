# default_profiles: human labels (Stage 5, Part 22)

Status: scored 2026-11-17 under the frozen rules (`annotation/COORDINATOR_STEPS.md` section 5, Part 22; `ANNOTATION_REQUEST.md`; PLAN sections 1 and 5). Script `src/frontier_stage5_p22_default_profiles.py`; tables `human_*.csv`; the committed machine reference (`round3.md`, `*_r3.csv`) is untouched ("No re-labelling": human labels sit next to the machine numbers).

**Data.** 11 annotators did this part (446/446 ratings, 223 items x 2, returns identical to the private assignment, no missing, no extra, no duplicated answer set). Items: 120 speech-act exposure units (E_speech_act), 43 politeness exposure units (E_politeness), 60 controls (detector says statement, not polite, keywords lack both cues). Consensus = both coders agree; disagreement = no consensus, counted and listed. Primary speech-act label: question or request/command = non-statement, statement = statement, "other" and no-consensus excluded; sensitivity: "other" and no-consensus counted as non-statement. Intervals: Wilson for within-stratum shares, message-cluster bootstrap (2,000 resamples, strata and human sample resampled together) for rates per 1,000 messages. Negation is not in this part.

## Headline
1. **The speech-act and politeness source labels are validated.** Detector non-statement vs human: 91.6% [84.8, 95.5] of the 107 decided exposure units are human question/request (92.5% [86.4, 96.0] with "other" counted); controls are human question/request in 3.4% [1.0, 11.7] (2/58; 6.7% [2.6, 15.9] under the sensitivity rule). Pooled kappa .83 [.75, .91] (HT-weighted .82 [.72, .91], Kish n 159; .79 [.70, .87] under the sensitivity rule). Politeness: 97.7% [87.9, 99.6] of the 43 detector-polite exposure units are human-polite (42/43); controls are human-polite in 0 of 60 (0% [0, 6.0]); kappa .97 [.93, 1.00]. Human-human agreement on the two label questions: Q1 kappa .97 [.95, .99], Q2 .99 [.97, 1.00].
2. **Re-running the exposure estimates with human labels barely moves them.** Always-commit, model-visible, per 1,000 messages: speech act **159.7 [131.2, 189.0]** (detector 161.9; ratio .99 [.91, 1.09]); politeness **48.6 [35.7, 62.6]** (detector 49.4; ratio .98 [.95, 1.00]). Exposure: speech act 268.9 [229.3, 307.5] (detector 277.5), politeness 55.5 [41.0, 71.0] (detector 56.4). The "provisional, detector-proxy" label on the speech-act and politeness source labels can be dropped; the exposure and always-commit numbers stand.
3. **The keyword-lacks-cue half (Q3, Q4) could not be validated.** The two coders agree on Q3 and Q4 at chance (agreement 50% and 48%, kappa -.03 [-.17, .09] and -.07 [-.20, .06]), so there is no human consensus on "do the keywords already show the cue" for about half the items and the consensus that exists is noise-level. The lexical gate and the exposure unit definition (cue in the source, dropped from the keywords) therefore stay machine-defined; nothing here supports or contradicts them.

## 1. Detector versus human consensus
| stratum | n | human non-statement (question or request) | statement | other / no consensus | human polite |
|---|---|---|---|---|---|
| E_speech_act (detector non-statement) | 120 | 98 (91.6% of 107 decided) | 9 | 13 (10 other, 3 split) | 39 of 119 (32.8%) |
| E_politeness (detector polite) | 43 | 31 of 38 decided (81.6% [66.6, 90.8]); detector non-statement in 37 of 43 | 7 | 5 | 42 (97.7% [87.9, 99.6]) |
| control (detector statement, not polite) | 60 | 2 (3.4% [1.0, 11.7]) | 56 | 2 | 0 (0% [0, 6.0]) |
Among E_speech_act units the detector's "polite" call is right 38 of 39 and its "not polite" call wrong in 1 of 80 (1.2% [0.2, 6.7]).

| detector vs human | n | agreement | kappa [95% CI, item bootstrap] | HT kappa [CI] |
|---|---|---|---|---|
| non-statement (primary) | 203 | 92.6% | .83 [.75, .91] | .82 [.72, .91] |
| non-statement ("other" counted) | 223 | 91.0% | .79 [.70, .87] | .80 [.70, .89] |
| polite (primary) | 222 | 98.6% | .97 [.93, 1.00] | .98 [.96, 1.00] |
The pooled kappas mix three targeted strata (positives are over-represented), so they are descriptive of this draw, not population kappas; the per-stratum rates above are the quantities used downstream.

## 2. Q3 and Q4 against the lexical gate (not validated)
Among E_speech_act units with a Q3 consensus (60 of 120), the lexical gate says "keywords lack the cue" for 49 and the human consensus agrees for 36 (73.5% [59.7, 83.8]); 20 consensus items say the keywords already show a question or request. Among E_politeness units with a Q4 consensus (24 of 43) the gate and humans agree on 16 of 24 (66.7% [46.7, 82.0]). Q3 and Q4 are not usable as a gate standard given chance-level coder agreement; the machine-side figure remains "52 of 417 speech-act exposure units the gate cannot reach" (`summary_r3.json`).

## 3. Re-run with human consensus substituted (class-calibrated)
The human draw covers 223 messages, not the 1,800 units, so a literal substitution would relabel 12% of units and mix detector and human labels. Instead each detector class is replaced by its human-measured rate: units the detector marks as exposure get the human PPV (E_speech_act stratum; E_politeness stratum), and the control class (detector statement and not polite, keywords lacking both cues) gets the human miss rate; the model-visible event keeps each unit's stored model output. Units outside both classes keep exposure 0 (not validated; a cue-bearing keyword set with a detector-statement source is untested). Bootstrap resamples messages (random / enriched strata) and the human sample together.
| quantity, per 1,000 messages | detector (committed) | human-calibrated [95% CI] | sensitivity ("other" counted) |
|---|---|---|---|
| speech act, exposure | 277.5 | **268.9 [229.3, 307.5]** | 274.1 [235.1, 313.4] |
| speech act, always-commit model-visible | 161.9 | **159.7 [131.2, 189.0]** | 163.7 [135.5, 193.5] |
| politeness, exposure | 56.4 | **55.5 [41.0, 71.0]** | 55.5 [41.4, 69.7] |
| politeness, always-commit model-visible | 49.4 | **48.6 [35.7, 62.6]** | 48.6 [36.0, 62.3] |
Of the speech-act exposure, 8.9 [0, 26.2] per 1,000 comes from controls (human-found requests the detector called statements); PPV .937, miss rate .033 (HT).

**Price of a cue on every message, with the measured restoration rates (F1, `followup.md`) and the human-calibrated exposure** (reversals per 1,000 messages; the corner interval combines the exposure CI with the restoration CI, so it is wide by construction): speech act bare 188.5, chip 65.6 [41.9, 92.9], plain word 55.9 [32.1, 85.6]; politeness bare 51.0, chip 0.7 [0.1, 1.8], plain word 1.2 [0.2, 2.8]. Detector-based values were 67.7 / 57.7 and 0.7 / 1.2. Ask-policy contrasts (prior vs gated random vs confidence) were not re-run: the calibration rescales exposure inside a class by a constant (PPV .94 and .98), which cannot reorder policies within a class; the null on ask policies is unchanged by construction and is not independently re-tested.

## 4. Does the verdict change?
No. The framework, the null on ask policies, and the cost numbers stand; the speech-act and politeness figures lose their "provisional (detector proxy)" label for the source labels, with the keyword-lacks-cue gate still machine-defined. The speech-act headline (always-commit about 160 per 1,000, about 270 exposed) is now human-checked; the SLP-weighted values change by the same factors (.99 and .98).

## Where it does not help
Q3 and Q4 gave no usable human standard. The human sample is 223 messages; controls (60) bound the miss rate to [0, 9.6] (speech act, bootstrap) rather than pin it. The calibration assumes the E class and control class are the only sources of human-positive exposure. Eleven coders, non-authors, reading text. Polarity and the policy-ranking contrasts are not covered by this part.
