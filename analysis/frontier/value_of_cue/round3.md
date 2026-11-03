# value_of_cue, round 3 (PROVISIONAL: detector source labels, machine-arbitrated output labels, simulated q = 0.9 and rho; 20 writers x 600 messages; HT-weighted)
Rules: PLAN.md A5 (written before outcomes; all items post-pilot). Script src/frontier_value_of_cue_round3.py, figure src/frontier_value_of_cue_fig3.py. Outputs: round3/ (r3_*.csv, summary_round3.json, curves_r3.json, fig_round3.png); copy of the summary at summary_round3.json. Fixed-prediction CIs = widest of writer/message/joint cluster bootstrap (300 resamples each); refit CIs = 200 joint resamples with every policy refit end to end. No CRC-guarantee language. Only Angelopoulos et al. (arXiv 2208.02814) is verified-opened; B6 is inspired-by, not a reproduction.

## Headline (primary scope: polarity, speech act, politeness-lost; one prompt per message; q = 0.9; T = 100 taps per 1,000 messages)
Status quo B0 = 178.2 SLP-weighted (235.3 raw) silent errors per 1,000 messages. Strict S1 (drops please, MOD, WH, "?", CERT and the NEG/POL/ACT flags) is used for all learned policies. All policies are listed (no best-of selection).
| policy | % of B0 averted [95% CI, fixed] | weighted averted /1,000 | raw errors averted /1,000 | taps per error averted |
|---|---|---|---|---|
| oracle (upper bound) | 42.7 [32.8, 53.9] | 76.1 | 90.0 | 1.1 |
| P-I (strict S1 + model internals, qwen+llama) | 13.8 [9.6, 19.3] | 24.6 | 30.7 | 3.3 |
| P-O (strict S1 + stored arbiter labels of the committed text) | 11.4 [7.5, 17.8] | 20.2 | 25.3 | 4.0 |
| B6-sup (entropy / minority-frequency features, same learner and folds) | 11.9 [7.8, 16.1] | 21.3 | 26.6 | 3.8 |
| P-K (keyword-only, strict S1) | 8.9 [5.6, 12.7] | 15.9 | 19.8 | 5.0 |
| B5 (best fixed prompt by prior) | 6.5 [5.9, 7.1] | 11.7 | 14.6 | 6.9 |
| B6 unsupervised entropy gate (inspired-by) | 4.4 [1.6, 8.3] | 7.8 | 10.1 | 9.9 |
| B1 random ask | 3.0 | 5.3 | 7.1 | 14.2 |
Residual after P-I: 153.6 weighted (204.6 raw) per 1,000; the policy touches 10% of messages. Gains are small in absolute AAC terms: about 31 raw silent reversals avoided per 1,000 messages for 100 taps, 87% of the status-quo burden remains.

## Paired contrasts at T = 100 (fixed predictions [refit-bootstrap CI in brackets, 200 resamples])
| contrast | pp of B0 | fixed CI | refit CI |
|---|---|---|---|
| P-K minus B5 | +2.4 | [-1.0, 6.2] | +1.0 [-3.4, 6.0] |
| P-O minus B5 | +4.8 | [1.2, 10.9] | +5.4 [0.0, 11.7] |
| P-I minus B5 | +7.2 | [3.2, 12.4] | +6.5 [1.1, 13.0] |
| P-I minus P-O (beyond committed output) | +2.4 | [-3.4, 6.7] | +1.2 [-5.1, 7.9] |
| P-I minus P-K | +4.9 | [-0.3, 11.3] | +5.5 [-0.2, 12.4] |
| P-K minus B1 | +5.9 | [2.6, 9.7] | +4.6 [0.4, 9.5] |
| P-I minus B6 (unsupervised) | +9.4 | [4.2, 15.1] | |
| P-I minus B6-sup | +1.9 | [-3.0, 7.4] | |
| P-K minus P-K-noLex (strict vs round-2 S1) | +0.7 | [-2.7, 2.9] | |
- **Verdicts on pre-declared claims.** (i) "Signals beyond the committed output": P-I minus P-O CI includes 0 at T = 50 (+2.3 [-1.5, 6.4]), 100 and 200 (refit and fixed) and for both single models (qwen +4.3 [-3.0, 10.4], llama +4.6 [-1.4, 8.7] at T = 100). NOT demonstrated. Most of the gain over B5 is "ask when the model's own output lacks the cue" (P-O minus B5 +4.8 [1.2, 10.9]); P-O stored vs regenerated labels differ by +0.7 pp [-0.6, 3.7], so the comparator is not sensitive to that choice. (ii) Keyword-only P-K does not reliably beat the prior-only B5 (CI includes 0 at T = 50, 100 and, under refit, 200). It beats random B1. (iii) Learned P-I beats B5 with the CI excluding 0 under both bootstraps at T = 100 and 200. (iv) Supervised B6 features (B6-sup) match P-I within noise (P-I minus B6-sup +1.9 [-3.0, 7.4]): the entropy signal is the main content of the internal-signal gain, so the novelty over an entropy-gated asker rests on learning the gate, not on new features. Unsupervised B6 is no better than random (B6 minus B1 +1.4 [-1.4, 5.3]) and below B5.
- **Refit bootstrap is wider than fixed-prediction CIs** (for example P-K at T = 100: fixed [5.6, 12.7], refit [3.4, 12.5]); the refit interval is the headline whenever they differ. Refit means are slightly lower than the point estimates (P-K 7.6 vs 8.9), a sign of mild optimism in the single cross-fit.
- **Two S1 variants.** AUROC, no-lexicon (round 2) vs strict: speech act .733 -> .635 [.57, .69], politeness .708 -> .607 [.49, .70], polarity .564 -> .618 [.45, .76]. Dropping the question/modal/please lexicon removes about 0.1 AUROC from keyword-only features on speech act and politeness, so round-2 keyword AUROCs were partly lexical leakage. The frontier changes little (P-K strict 8.9% vs noLex 8.2% at T = 100; P-I strict 13.8% vs noLex 14.6%), because the ladder gain is dominated by the prior and the speech-act base rate. With model signals added AUROC recovers: speech act P-I .783 [.73, .83], P-O .758 [.69, .81], P-IO .793; politeness P-I .685 [.59, .77]; polarity P-I .575 [.39, .74] (CI includes .5 for every polarity model).
- **Per-model H2 under strict S1 (post-pilot re-evaluation).** T = 50, P-I minus P-K: qwen +4.9 pp [0.4, 9.7], llama +3.9 [0.1, 8.2] (both exclude 0; in round 2 llama's CI included 0). Speech-act AUROC gain >= .03 met. H2 is still reported as NOT MET as declared: gemma3-4b is missing (2 of 3 models), the external-detector comparison (P-X, round 2: "internal beats external" 1 of 2 models) was not re-run, and the pooled T = 50 pooled P-I minus P-K CI includes 0 (+3.0 [-1.3, 7.2]).

## Polarity failure and what the policy actually does
At T = 100 every prompt of P-K, P-O and P-I (100%) is a SHOW-TWO on speech act; polarity (B0 share 23.9 weighted, the clinically heaviest per event) and politeness (24.7) are never prompted, and ASK-ONE-CUE is never chosen (r3_decomp.csv). Polarity AUROC CIs include 0.5 for all feature sets; B6-sup polarity AUROC is .329 [.22, .46] (below chance). The policy is a "which messages likely lost a question/request act" detector, not a general cue-risk detector.

## q sensitivity (0.3 to 1.0, T = 100, % of B0; r3_qsweep.csv)
| q | P-K | P-O | P-I | B5 | B1 | P-K minus B5 [CI] | P-I minus B5 [CI] | P-I minus P-O [CI] |
|---|---|---|---|---|---|---|---|---|
| 0.3 | 3.8 | 4.4 | 6.5 | 2.9 | 1.0 | +0.9 [-0.8, 3.7] | +3.7 [0.9, 6.8] | +2.1 [-1.2, 5.8] |
| 0.5 | 5.0 | 6.5 | 7.6 | 3.6 | 1.7 | +1.3 [-0.6, 3.5] | +4.0 [1.7, 6.8] | +1.2 [-2.0, 3.7] |
| 0.7 | 6.9 | 9.1 | 10.7 | 5.1 | 2.3 | +1.8 [-0.8, 4.9] | +5.6 [2.5, 9.6] | +1.6 [-2.8, 5.1] |
| 0.9 | 8.9 | 11.4 | 13.8 | 6.5 | 3.0 | +2.4 [-1.0, 6.2] | +7.2 [3.2, 12.4] | +2.4 [-3.4, 6.7] |
| 1.0 | 9.6 | 13.4 | 15.7 | 7.3 | 3.3 | +2.3 [-1.2, 7.1] | +8.4 [3.3, 13.9] | +2.3 [-4.5, 7.4] |
Ordering is the same at every q; there is no break-even inside [0.3, 1.0] (point estimates P-K >= B5 and P-I >= B5 at every q; grid floor 0.3). P-I minus B5 excludes 0 at every q; P-K minus B5 never does. The size of every gain scales with q (P-I 6.5% at q = 0.3 vs 15.7% at q = 1.0); q is unmeasured, annotation request pending.

## Cost model at T = 100 (false alarm a tap-equivalents per prompt on a message that did not need it; mis-pick m; r3_cost.csv; policies not re-tuned)
- a = 0, m = 0 (primary): P-K 8.9, P-O 11.4, P-I 13.8, B5 6.5, B1 3.0.
- a = 0.5, m = 0.05: P-K 5.3 [2.3, 8.4], P-O 6.9, P-I 9.2 [5.2, 14.2], B5 3.3, B1 0.7; P-I minus B5 +5.9 [2.2, 10.9], P-K minus B5 +2.1 [-1.0, 5.0].
- a = 1, m = 0.10 (harshest): P-K 3.2 [0.5, 6.5], P-O 4.2, P-I 7.7 [3.2, 12.1], B5 1.5, B1 0.0; P-I minus B5 +6.2 [2.2, 10.5].
False alarms and mis-picks hurt the broad baselines (B5, B1) more than the learned policies, so the P-I advantage over B5 is preserved or grows (+7.2 -> +6.2 to +8.0 pp) while the absolute gain falls by up to 45%. P-I stays positive in every cell; P-K minus B5 never excludes 0.
- **Spurious-addition sensitivity** (spurious additions counted as errors fixable at efficacy e x q; policies trained on lost cues only): e = 0.5: P-K 8.1, P-O 9.3, P-I 11.5, B5 6.3 (P-I minus B5 +5.3 [2.1, 9.3]); e = 1: P-K 7.6, P-O 7.9, P-I 10.0, B5 6.1 (P-I minus B5 +3.9 [1.2, 7.2]; P-O minus B5 +1.8 [-0.4, 5.1]). Shares fall because B0 grows from 178 to 267; weighted errors averted per 1,000 rise (P-I 24.6 -> 26.7).

## Primary vs full five-dimension scope (lost cues only; five-dim B0 = 354.1; exploratory, r3_scope.csv)
| T = 100 | P-K | P-O | P-I | B5 | B1 |
|---|---|---|---|---|---|
| primary (3-dim), % of B0 | 8.9 | 11.4 | 13.8 | 6.5 | 3.0 |
| five-dim, % of B0 | 3.3 [1.8, 5.6] | 5.6 [3.9, 8.5] | 6.6 [4.3, 8.8] | 4.0 [3.5, 4.6] | 1.8 |
Five-dim: P-K minus B5 -0.7 pp [-2.4, 1.5] (no gain over prior), P-O minus B5 +1.5 [-0.3, 4.5], P-I minus B5 +2.5 [0.1, 4.8], P-I minus P-O +1.0 [-2.0, 2.9]; at T = 200 P-I (11.9%) falls below P-O (13.4%). Certainty and agent AUROC (P-K/P-O/P-I): certainty .39/.54/.57, agent .54/.57/.64 (exploratory; certainty is below chance for keywords alone). Including them roughly halves the share averted because agent and certainty are detector-vs-judge disagreement and are not helped by the signals.

## G1-after-ask and the ASK action (transfer estimate with the stored 52.5% G1 repair; r3_frontier.csv)
G1 alone averts 0 (no chip in keyword-only input). ASK actions cost 2 taps, so under a tap budget they lose to SHOW-TWO: P-I ASK+G1 6.5 / 13.3 weighted averted per 1,000 (3.6% / 7.5% of B0) at T = 50 / 100 vs P-I SHOW 13.3 / 24.6 (P-I ASK+G1 minus P-I -11.2 [-18, -6] weighted at T = 100). Entropy-gated B6 ASK+G1: 3.0 (1.7%). P-I ASK+G1 minus B6 ASK+G1 +10.4 [4.1, 17.1] weighted. ASK with G1 is the better action only when taps are not the constraint (fixed baselines in round2/fixed_baselines.csv: ask-all with G1 leaves 14.6 weighted at 6,000 taps).

## Per-writer heterogeneity (pooled T = 100; r3_per_writer.csv, fig_round3.png panel C)
P-K beats B5 for 7 of 20 writers (median writer gain 2.5% of own B0 vs B5 5.5%); P-O 8 of 20; P-I 16 of 20 (median 11.8% vs B5 6.0%). Several writers get 0 prompts from P-K/P-O (their keyword style does not look like it drops a request) while three writers (P01 to P03) carry most of the aggregate gain. P-K's gain is concentrated in a minority of writers.

## Gemma and the GPU
gemma3-4b Stage 1 was NOT run: the owner SIGSTOPped the queued AAC GPU jobs (GPU-PAUSE-NOTE.md, D-084, for the D-15 Unity job; my queued job is pid 1229407/1512740, still stopped) and I started no new lock jobs. All round-3 numbers use qwen2.5-7b + llama3.1-8b features (2 of 3 models), recorded as a deviation. Re-run when it finishes: `python src/frontier_value_of_cue_features.py gemma3-4b S2`, then `VOC_LOCALS=qwen2.5-7b,llama3.1-8b,gemma3-4b python src/frontier_value_of_cue_round3.py 300 200` (delete round3/P_r3.npz first).

## Where it does NOT help
Polarity (never prompted, AUROC CI includes .5); certainty and agent; keyword-only P-K versus the prior-only B5 (CI includes 0 at every budget up to 200 under refit, and in the five-dimension scope it is below B5); signals beyond the committed output (P-I minus P-O CI includes 0 everywhere); unsupervised entropy gating (no better than random); ASK-ONE-CUE (2 taps, never chosen); the five-dimension scope (P-I 6.6% vs B5 4.0%); about half of writers (P-K gain at 0 for many). Absolute burden remains: 87% of weighted silent errors persist at 100 taps per 1,000.

## Deviations and status
K = 8 samples (round 2), gemma missing, B6 inspired-by, outcome labels machine-arbitrated, q and rho simulated, penalty models not re-tuned, refit bootstrap uses fixed 5x5 cross-fit blocks (200 resamples). H3 (round 2 amended targets) was not re-run. All AAC-unit numbers are PROVISIONAL until q is measured (ANNOTATION_REQUEST.md, not sent).
