# value_of_cue: human labels (Stage 5, Part 24): measured q

Status: scored 2026-11-17 under the frozen rule (`annotation/COORDINATOR_STEPS.md` section 5, Part 24; `ANNOTATION_REQUEST.md` Part B and round-3 addendum; PLAN sections 6 and 7). Scripts: `src/frontier_stage5_p24_qhat.py` (q, m, kappa), `src/frontier_value_of_cue_round3_human.py` (round-3 frontier refit with q as a per-dimension vector; reproduces `round3/r3_frontier.csv` exactly at q = 0.9, 225 rows, max difference 1e-16), `src/frontier_value_of_cue_b5lex_human.py`. Outputs: `human_q*.csv`, `human_q.json`, `round3_human_human/` (primary), `round3_human_qlo/`, `round3_human_qhi/` (frontier only), `b5lex/b5lex_human.csv`.

**Data.** 9 annotators, 146/146 judgments on 73 items x 2 (36 speech-act stratum-A items, 37 stratum-B controls: polarity 14, politeness 9, speech act 14; the request text said 31 controls, the built key has 37). Assignment matches the private list exactly; no missing or duplicated answers. Stratum A polarity (40) and politeness (32) items were not in this wave, so **q is measured for speech act only; polarity and politeness keep the assumed q = 0.9**. Intervals are item-cluster bootstrap (10,000 resamples; both judgments of an item resampled together).

## Headline
1. **Measured q (speech act): 73.6% [59.7, 86.1]** (53 of 72 judgments pick the cue-restored sentence in Q2; 36 items). The assumed q = 0.9 is above the interval. Q1 cross-check ("which says the same about the cue"): alternative 87.5% [76.4, 97.2], default 11.1%, both/neither 1.4%. Conditional on picking either sentence (Q2 not "neither"): 93.0% [83.6, 100]. The gap between Q2 (73.6%) and Q1 (87.5%) is the 20.8% [9.7, 33.3] of Q2 judgments that say "neither draft is what I would tap" (the alternative fixes the cue but the draft can still be unusable); q-hat uses the Q2 rule as declared, so it is the conservative reading.
2. **Wrong-pick rate m (stratum B, 74 judgments, 37 items): 4.1% [0, 9.5]** pick the unneeded alternative (polarity 1/28, politeness 2/18, speech act 0/28); 60.8% [44.6, 75.7] pick the default; 35.1% [20.3, 50.0] say neither (also a failure of the draft, not of the cue). This sits inside the 0 to 0.10 mis-pick range the cost model assumed; the m = 0.05 cell is the measured one.
3. **Reliability.** Inter-annotator kappa on Q2 .78 [.58, .95] (stratum A speech act, 36 items), .88 [.72, 1.00] (stratum B), .83 [.71, .94] pooled; Q1 .95 [.83, 1.00] (A), .95 (B). Per-annotator q ranges from .38 to .89 on 6 to 10 judgments each (P12 .38, P10 .50; the other seven .71 to .89); both annotators chose the alternative on 25 of 36 items, split on 3, neither chose it on 8. Annotator heterogeneity is part of the interval, not removed from it.
4. **The refit with q = 0.736 shrinks every gain by about a fifth and leaves the ordering unchanged.** At 100 taps per 1,000 messages (fixed-prediction CI, widest of writer, message and joint cluster bootstraps, 300 resamples each): P-I 11.4% [8.0, 15.9] of the SLP-weighted burden B0 = 178.2 (was 13.8% [9.6, 19.3] at q = 0.9), P-O 9.8% [5.9, 14.5], P-K 7.0% [4.4, 10.5], B5 (best fixed prompt by prior) 5.4% [4.8, 5.8], B1 2.6%. That is 20.4 SLP-weighted (25.5 raw) silent reversals averted per 1,000 messages for 100 taps (3.9 taps per raw reversal averted); 89% of the weighted burden remains. P-I minus B5 **+6.1 pp [2.7, 10.2]** (was +7.2 [3.2, 12.4]); P-I minus lexicon-gated B5-lex **+4.0 [0.8, 7.5]** (was +4.7 [1.1, 9.5]); P-K minus B5 +1.7 [-0.9, 5.1] (still includes 0); P-I minus P-O +1.6 [-3.1, 5.5] (still no evidence of signals beyond the committed output).
5. **Refit bootstrap (declared headline interval when it differs from the fixed-prediction one): not completed.** The 200-resample end-to-end refit (`round3_human_human/refit_200.json`) was started with the same code that took 3 minutes in round 3, but the host was at a load average of about 150 and it had not finished after more than two hours. Every CI above is therefore the fixed-prediction interval. In round 3 at q = 0.9 the refit interval was wider (P-I 13.1% [7.0, 19.9] vs fixed [9.6, 19.3]; P-I minus B5 +6.5 [1.1, 13.0] vs fixed [3.2, 12.4]), so read the fixed intervals above as too narrow and expect the P-I minus B5 lower bound to be near 1 pp. This is logged as a deviation.

## 1. Measured q and m
| quantity | set | estimate | 95% CI | n judgments / items |
|---|---|---|---|---|
| q-hat: Q2 = alternative | A, speech act | 73.6% | [59.7, 86.1] | 72 / 36 |
| Q2 = default | A | 5.6% | [0, 12.5] | 72 / 36 |
| Q2 = neither | A | 20.8% | [9.7, 33.3] | 72 / 36 |
| Q1 = alternative (cross-check) | A | 87.5% | [76.4, 97.2] | 72 / 36 |
| q given a pick (Q2 not neither) | A | 93.0% | [83.6, 100] | 57 / 31 |
| m: Q2 = alternative | B all | 4.1% | [0, 9.5] | 74 / 37 |
| m by dimension | B polarity / politeness / speech act | 3.6% / 11.1% / 0% | wide (n 28 / 18 / 28) | |
| Q2 = default | B all | 60.8% | [44.6, 75.7] | 74 / 37 |
| Q2 = neither | B all | 35.1% | [20.3, 50.0] | 74 / 37 |
| Q1 both or neither (adequacy of the offered alternative) | A / B | 1.4% / 1.4% | [0, 4.2] / [0, 4.1] | |
Q1 against Q2 (speech act, A, 72 judgments, labels relative to the alternative): of the 63 judgments where Q1 says the alternative matches the original, 51 pick it in Q2, 10 say neither, 2 pick the default; `human_q_q1_q2_crosstab_speech_act.csv`.

## 2. Frontier refit with measured q (T = 100 taps per 1,000 messages; share of B0 averted; fixed-prediction CI)
| policy | q = 0.9 (committed) | **q-hat = .736** | q = .597 (CI low) | q = .861 (CI high) |
|---|---|---|---|---|
| oracle | 42.7 [32.8, 53.9] | 37.1 [29.0, 46.6] | 32.4 [25.8, 40.8] | 41.4 [31.8, 52.2] |
| P-I (model internals) | 13.8 [9.6, 19.3] | **11.4 [8.0, 15.9]** | 9.2 [6.5, 13.0] | 13.4 [9.4, 18.6] |
| P-O (stored output labels) | 11.4 [7.5, 17.8] | 9.8 [5.9, 14.5] | 7.9 [4.9, 11.6] | 11.5 [7.2, 16.9] |
| P-K (keywords only) | 8.9 [5.6, 12.7] | 7.0 [4.4, 10.5] | 5.9 [3.6, 8.7] | 8.5 [5.2, 12.6] |
| B5 (best fixed prompt) | 6.5 [5.9, 7.1] | 5.4 [4.8, 5.8] | 4.3 [3.9, 4.7] | 6.3 [5.7, 6.8] |
| B1 (random) | 3.0 | 2.6 | 2.3 | 2.9 |
| P-I minus B5 | +7.2 [3.2, 12.4] | **+6.1 [2.7, 10.2]** | +4.8 [2.2, 8.3] | +7.1 [3.2, 12.0] |
| P-K minus B5 | +2.4 [-1.0, 6.2] | +1.7 [-0.9, 5.1] | +1.6 [-0.7, 4.3] | +2.2 [-1.0, 6.4] |
| P-I minus P-O | +2.4 [-3.4, 6.7] | +1.6 [-3.1, 5.5] | +1.3 [-2.5, 4.4] | +1.9 [-3.6, 5.9] |
| P-K minus B1 | +5.9 [2.6, 9.7] | +4.4 [1.8, 8.0] | +3.6 [1.4, 6.4] | +5.6 [2.3, 9.7] |
q-hat only enters speech act, which is the only dimension the policy ever prompts (100% of P-I and P-O prompts, 99.3% for P-K; `r3_decomp.csv`); polarity (23.9 weighted) and politeness (24.7) are still never prompted, so their assumed q does not matter to these rows but remains unmeasured for any future policy that would prompt them. The scalar all-dimension q sweep (0.3 to 1.0) is in `round3_human_human/r3_qsweep.csv`: P-I minus B5 excludes 0 at every q (+3.7 pp at q = 0.3 to +8.4 at 1.0), P-K minus B5 never does, and there is still no break-even q.

Cost model at the measured m (m = 0.05 cell, no false-alarm tap cost): P-I 10.0% [6.2, 14.4], P-O 8.3%, P-K 5.2%, B5 3.5%; P-I minus B5 +6.5 [2.9, 10.8], P-K minus B5 +1.8 [-1.0, 5.7]. With a false alarm costing half a tap as well: P-I 7.4% [4.1, 11.4], B5 2.4%, P-I minus B5 +5.0 [2.0, 9.0]. Spurious-addition sensitivity (e = 0.5 / 1): P-I 9.5% / 8.3%, P-I minus B5 +4.4 [1.6, 7.6] / +3.3 [1.0, 5.8].
Scope: counting certainty and agent as well (five-dimension, lost cues only), P-I is 5.7% [3.5, 7.6] and P-I minus B5 is +1.6 pp [-0.6, 3.8] (was +2.5 [0.1, 4.8]): with q measured the learned policy no longer separates from the fixed prompt there.
Per writer (P-I at T = 100): beats B5 for 17 of 20 writers (median 9.9% of the writer's own burden vs 5.1%); P-K beats B5 for 6 of 20, P-O for 8 of 20 (was 7 and 8; P-I 16).

## 3. Does the verdict change?
- **Sign and ordering: unchanged.** P-I > P-O > P-K > B5 > B1 at every q in [0.6, 0.9]; learned P-I beats the fixed prompt and the lexicon-gated fixed prompt with CIs that exclude 0; keyword-only P-K does not reliably beat B5; signals beyond the committed output are not shown.
- **Size: smaller by about a fifth.** The headline "P-I averts 13.8% of SLP-weighted silent reversals at 100 taps" becomes **11.4% [8.0, 15.9]** at the measured q; the refit interval, which is wider, is pending; the former q = 0.9 was an assumption outside the measured interval.
- **Status:** the PROVISIONAL label on the SHOW-TWO numbers is lifted for the speech-act q (measured) and stays for polarity and politeness q (assumed, unmeasured), the machine arbiter labels of lost cues, the transported rho, and the 2-model signal features.
- **The cost of a spurious alternative is small but not zero** (m = 4.1% [0, 9.5]; one polarity and two politeness wrong picks): the cost-model result P-I minus B5 stays positive (+6.5 at m = 0.05).

## Where it does not help
Polarity and politeness q are not measured; speech-act q rests on 36 items and 9 annotators (two annotators pick the alternative about half the time; the CI [59.7, 86.1] is wide). q is a rate of choosing the restored sentence in a forced two-draft task, not an outcome rate in use by people who rely on AAC. The policy is a "which messages lost a question or request" detector: still no polarity or politeness prompting, five-dimension scope shows no P-I advantage over B5, and 89% of the weighted burden remains at 100 taps. Absolute averted counts are rates over 1,800 sampled units, not deployment rates.
