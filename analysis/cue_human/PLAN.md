# Problem 6 (cue_human): is the speech-act cue gain (P1) still there when people, not machines, label the outputs? Frozen analysis plan

Written 2026-11-18, before any human label, before the sample draw, and before any stored output was drawn for this check.
Nothing below may change after human labels are collected. Any later deviation goes to analysis/cue_human/DEVIATIONS.md (create it empty now) and is reported as a deviation.
Status: not committed; plan sha256 to be deposited with the key before any sheet is sent (src/make_cue_human.py package prints it).
What was looked at before writing: the stored P1 frame (analysis/hw12, src/analyze_hw1.py frames) for its SIZE and machine-label cell counts only, to set the allocation and the power. No human label of any hw12 output exists.

## 1. Question and role of the people
The headline P1 (speech-act chip gain, +37.5 pp, 10 writers, 1,016 pairs) is chip1 critical match minus noncrit critical match, where "critical" is the J1/J2 LLM label, arbiter-resolved. Both judges and the arbiter are LLMs; the 98.5% Claude-vs-GPT agreement on hw12 (analysis/relabel_nongpt) shows the machines agree with each other, not that they agree with people. This check puts people on the exact contrast.
Annotators are ~20 adult non-author classmates (consented, paid; nothing collected about them) labelling study materials. No AAC users, no studies of people as system users.

## 2. Population and estimand
Population: every (family, variant, model) cell of runs/hw1 + runs/hw2, prompt P0, dimension speech_act, with both a chip1 and a noncrit output, after the stored exclusions of src/analyze_hw1.py build() (refusal/acceptance families and writer P06 removed; D-058). Pair = (family, variant, model). Expected N = 1,016 pairs = 2,032 outputs, 127 families, 10 writers, 4 models (src/cue_human_power.py prints the exact N).
Unit label: match_k = 1 if the label of output k equals the critical value the writer's variant intends (stored `variant_value`), else 0 ("unclear/mixed", "other", and any other value are 0, as for the machine).
D_i = match(chip1 output) - match(noncrit output) in {-1,0,1}. Estimand: P1 = (1/N) sum_i D_i over the population (pair-weighted, same as the stored +37.5). Clusters = writer (G = 10).
Machine value of the estimand D^m_i is the stored `critical_match` difference. Human value D^h_i is defined only on the sample.

## 3. Stimuli (frozen rules; built by src/make_cue_human.py, to be written by the assignment task)
Seed 20261118 (numpy default_rng(seed) after sorting pairs by (family_id, variant, model)).
* Sample of 120 PAIRS = 240 outputs (both the chip1 and noncrit output of each sampled pair, so the paired contrast is observed directly).
* Stratification: stratum = model x machine pattern (chip1 match, noncrit match) in {11,10,01,00}; 15 non-empty strata (gpt-6.1-terra has no 01 pair).
  Allocation (src/cue_human_power.py allocate()): min(N_h, 4) per stratum, remainder proportional to N_h, largest-remainder ties by stratum name. Draw within stratum uniformly without replacement. Inclusion probability pi_i = n_h / N_h is stored in the private key and used by every estimator. The allocation over-samples the machine-discordant cells (00, 01) where machine error most threatens the contrast; weights correct it.
* Writers are not a stratum; the 120 pairs fall on all 10 writers by chance (sampled writers < 10 is reported; any writer with 0 sampled pairs still contributes its machine mass to the PPI).
* No replacement of any item. Items whose output is empty/unparsed are not in the population (valid is True on all rows).
* Judge unit = distinct output text (normalised: lowercase, collapse whitespace, strip trailing punctuation) among the 240; identical texts are labelled once by the same two annotators and every output with that text inherits the label (identical-text rule of analysis/listener/PLAN.md). Expected about 190-215 distinct units.
* What an annotator sees (and all they see): the sentence, and the critical question exactly as src/judge.py asks it: CRITICAL_Q["speech_act"] verbatim, the seven options in the judge's order (statement, question, request/command, refusal, acceptance, offer/suggestion, unclear/mixed), and the speech_act decision rule of RULES_J2 verbatim (the judge's own definition, so a disagreement is not a missing-instruction artefact). The judge sees output text only (src/judge.py pass A: "No input, source, ..."), so no input, keywords, chips, family, writer, model, channel, intended value, machine label, or pair partner is shown. Option order fixed, item order seeded shuffle.
* Tool: annotation_package/rate_items.html with one blind JSON per annotator (format and Latin/assignment logic of src/make_frontier_parts.py and src/make_listener_study.py package; two practice items per file with key shown after).
* Private files: annotation/cue_human_key.csv (unit, output_ids, family, variant, model, channel, stratum, pi, machine label, J1, J2, arbiter) with .sha256 deposited before sending; annotation/assignments/ plan read by src/make_assignments.py.

## 4. Annotators and assignment
* 2 distinct annotators per unit. Nobody labels a unit from a family they wrote or checked (hw_blocks of src/make_frontier_parts.py). Nobody labels both outputs of the same pair (they would see the contrast); where the two outputs are the identical text this is moot because it is one unit. Load balanced to within 30 s as in make_frontier_parts.py.
* Burden: ~410 labels at ~20 s (the Part 22 rate, 21.5 s) is about 2.5 h in total, about 7 to 9 min per annotator over 20 people.
* Tie-break: a unit where the two annotators disagree on the 7-way label goes to one third distinct eligible annotator (second short file, same tool); majority label wins; a three-way split is "unclear/mixed". Expected 8 to 12% of units. The machine labels are never used to resolve.
* Reliability gate, computed before any machine-vs-human comparison is unblinded: human-human 7-way Cohen kappa and raw agreement on the match indicator, on all units with two labels. Declared: if match-indicator raw agreement is below 85% or kappa below 0.60, the human labels are called "ambiguity-limited": results are still reported, with the two-annotator-alone sensitivities (section 7) as the main display, and no sentence says the machine is "wrong".
* Exclusions: an annotator whose 7-way agreement with the other annotators on shared units is below 60% (attention) has all labels dropped and the units re-routed to a replacement annotator before any machine comparison; the count is reported. No exclusion depends on the machine label or on outcomes. Annotators are not told machine labels exist for these items.

## 5. Pre-declared analyses
Let the human-resolved match for output k be h_k (section 3-4 rules). For sampled pair i, D^h_i = h(chip1) - h(noncrit); D^m_i is the stored machine value; R_i = 1 if sampled; pi_i inclusion probability.

(a) Human-labelled P1 (design-weighted, no machine input in the estimate): P1_h = sum_i R_i D^h_i / pi_i / N (Horvitz-Thompson over the 1,016 pairs). Writer-clustered: influence psi_i = R_i D^h_i / pi_i - P1_h, summed within writer, CR1 variance G/(G-1) sum_g (sum psi)^2 / N^2, t interval with df = G-1 = 9. Also reported: chip1 and noncrit human match rates (same weights), and the writer-mean version. Wild-cluster bootstrap-t, Rademacher exact over all 2^10 writer sign patterns, as in src/robust_t6_small_cluster.py, is the check on the interval.

(b) PRIMARY estimator, prediction-powered inference, lambda = 1 (Angelopoulos et al. 2023; stratified-sampling form):
  P1_PPI = (1/N) sum_i D^m_i  +  (1/N) sum_i R_i (D^h_i - D^m_i) / pi_i.
  The second term is the rectifier (Delta, in pp), the human-measured bias of the machine contrast. Cluster-robust variance from writer totals of psi_i = D^m_i + R_i (D^h_i - D^m_i)/pi_i - P1_PPI, CR1, t(9). Same wild-cluster Rademacher check. Rectifier interval from the writer totals of R_i (D^h_i-D^m_i)/pi_i likewise.
  Sensitivity estimators (reported, not primary): (i) ratio / regression-calibrated: mean(D^m) x [sum R D^h/pi] / [sum R D^m/pi]; (ii) PPI++ with the power-tuning lambda estimated on the sample (clipped to [0,1]); (iii) PPI done per arm (chip1 rate and noncrit rate separately) with the contrast formed from them.
  Strata/model: per-model PPI (about 30 pairs per model) is descriptive only, no tests, no heterogeneity claim.

(c) Judge-human agreement on THIS contrast (output level, resolved human label vs the production machine label `critical`, plus J1 and J2 individually), each with and without the 1/pi weights, by arm (chip1, noncrit) and by stratum:
  7-way accuracy and Cohen kappa; match-indicator 2x2 (machine match vs human match) per arm with the false-match rate (machine 1, human 0) and the missed-match rate (machine 0, human 1); the 3x3 table of D^m vs D^h per pair; the arm-difference of false-match rates (this is what moves the rectifier); and the same agreement restricted to arbiter-resolved machine units. Wilson 95% intervals for rates (weighted: Kish effective n). Names of the disagreements (text and both labels) are listed in the report for the Can-you / I-want-please recode families already isolated in analysis/hw12/speech_act_sensitivity.json (descriptive).

## 6. Decision rules (frozen; wording the papers may use)
1. Direction. "The cue gain holds under human labels" only if the 95% t lower limit of P1_PPI is above 0 AND the lower limit of P1_h is above 0.
2. Size. The paper's headline P1 becomes the P1_PPI estimate with its CI (not 37.5) in every case. The sentence "human labels leave the machine contrast unchanged" is allowed only if the 90% interval (TOST) of the rectifier lies inside [-10, +10] pp. Otherwise the report says the machine contrast is biased by Delta pp [CI] and the paper states the PPI figure and the bias.
3. Judge validation. "The judge is validated on this contrast" only if weighted 7-way kappa >= 0.80, the match-indicator 2x2 false-match rates are each <= 10%, and the arm difference of false-match rates has a 95% interval inside [-10, +10] pp. Otherwise "not validated on this contrast" and the discordant cells are listed.
4. No claim of equivalence from a non-significant interval; no outcome-based re-weighting, re-labelling, or subset dropping. Unresolved three-way splits stay "unclear/mixed" (non-match).
5. Sensitivities (reported next to the primary, never swapped in): (i) each annotator alone, averaged over their two labels; (ii) disagreement units forced to non-match; (iii) disagreement units forced to match for the chip1 output and non-match for noncrit (the adverse and favourable bounds); (iv) drop identical-text units; (v) leave-one-writer-out; (vi) drop quarantined hw2 speech-act families.

## 7. Power (src/cue_human_power.py, analysis/cue_human/power.json; machine labels and the declared allocation only, no human data)
Machine P1 = 37.5 pp, G = 10, 120 pairs, 2,000 simulated draws per scenario, human match = machine match with symmetric flip noise e per output or extra chip1 over-credit; t(9) intervals.
| scenario | mean PPI (pp) | SE (pp) | 95% half-width | P(lower > 0) | P(rectifier shows nonzero) | P(rectifier 90% inside +-10) |
|---|---|---|---|---|---|---|
| 5% noise | 33.8 | 3.2 | 7.3 | 1.00 | 0.17 | 0.63 |
| 10% noise | 30.1 | 4.3 | 9.7 | 1.00 | 0.32 | 0.15 |
| 15% noise | 26.4 | 5.2 | 11.7 | 0.99 | 0.47 | 0.03 |
| chip1 over-credited 10 pp | 25.6 | 4.0 | 9.0 | 1.00 | 0.84 | 0.02 |
| chip1 over-credited 20 pp | 15.9 | 4.9 | 11.1 | 0.80 | 1.00 | 0.00 |
Reading: the design reliably decides direction (P1 > 0 under every plausible noise level) and detects a machine bias of about 10 pp or more in the chip1 arm; it cannot certify "unchanged" unless people and machines are close (human-machine disagreement below about 6% per output). Symmetric human noise itself pulls the estimate toward zero, so noise15 shifts the PPI to 26 even though the machine is unbiased relative to a noisy referee; the reliability gate (section 4) and the sensitivity (iii) bound this. Precision with 10 writers is limited by the cluster count, not by the 120 pairs; the sample is not enlarged.
If power is judged short, the only pre-declared extension is a second batch of 60 pairs drawn with the same rules (seed 20261119) BEFORE any human label is read; it cannot be triggered by outcomes.

## 8. Items and files to build (assignment task)
1. src/make_cue_human.py: subcommands draw (seeded; reuses population()/allocate() from src/cue_human_power.py), package (per-annotator blind JSONs + private key + plan + sha256), tiebreak (second-wave files), score (sections 5 and 6, writes analysis/cue_human/{summary.json,p1_human.csv,agreement.csv,report.md}).
2. annotation_package/stage8/<ID>_part30.json (blind rate_items files with one speech_act dimension, the verbatim judge question and J2 rule, two practice items) and <ID>_part30b.json (tie-break wave); one-line addition to annotation/COORDINATOR_STEPS.md (section 8).
3. annotation/cue_human_key.csv(+.sha256), annotation/assignments/stage8_plan.json (read by src/make_assignments.py), sheet text for each annotator.
4. tests/test_cue_human.py: stratum allocation sums to 120 and is reproducible; blindness (no key column in any package file); nobody labels own/checked family nor both outputs of a pair; PPI reduces to the machine P1 when D^h = D^m and to HT when D^m = 0; weights sum to N.
5. analysis/cue_human/DEVIATIONS.md (empty), power.json (done).
6. Generation: none. No GPU, no API call. All 2,032 outputs and machine labels are stored.
