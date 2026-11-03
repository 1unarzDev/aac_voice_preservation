# value_of_cue, round 2 (PROVISIONAL: detector source labels, machine-arbitrated output labels, simulated q and rho; 20 writers x 600 messages; HT-weighted; CIs = widest of writer/message/joint cluster bootstrap, 1,000 resamples)
Rules: PLAN.md A2-A4 (written before outcomes; A3 is post-pilot). Figure: round2/fig_round2.png. All CSVs in round2/. Scripts: src/frontier_value_of_cue_{lib,round2_cpu,s1gpu,s2api,features,signals,signals_q,perwriter,fig2,q_items}.py.

## Primary scope (polarity, speech act, politeness-lost), one prompt per message, q = 0.9 assumed
Status-quo burden B0 = 178.2 SLP-weighted silent errors per 1,000 messages (235 raw). (Round 1's 451.9 included agent, certainty, spurious additions: agent 158.8 and certainty 17.1 weighted lost-cue errors are exploratory; spurious additions listed separately in burden_lost_vs_spurious.csv: speech act 50.0, politeness 37.6, polarity 0.8, certainty 9.4 weighted per 1,000.)

Share of B0 averted (95% CI), keyword-only policy P-K (S1 without lexicon flags) and baselines:
| taps/1,000 | P-K | B5 prior-only | B1 random | oracle |
|---|---|---|---|---|
| 50 | 4.5 [1.7, 7.8] | 3.3 | 1.5 | 22.5 |
| 100 | 8.2 [5.0, 12.9] | 6.5 | 3.0 | 42.7 |
| 400 | 44.4 [36.8, 52.1] | 26.2 | 12.0 | 79.8 |
- P-K minus B5: +1.6 pp [-1.6, 6.5] at 100 taps (CI includes 0); significant only from 200 taps (+8.2 [1.7, 16.9]). P-K minus B1: +5.2 [2.0, 9.9] at 100. B1 has no sampling interval (analytic expectation).
- With the three outcome-defining lexicon flags kept: 9.7% at 100 (AUROC speech act .759 vs .733 without, politeness .722 vs .708, polarity .587 vs .564): leakage inflated slightly; primary is the no-lexicon fit.
- Scope: all five dims, lost cues only: P-K 3.9% [1.9, 6.1] at 100 vs B5 4.0% (difference -0.2 pp [-2.2, 2.1]): no gain over prior in the full scope (scope_comparison.csv).
- AUROC (no-lexicon): polarity .564 [.39, .72], speech act .733 [.67, .78], politeness .708 [.60, .79]; certainty .430 and agent .573 exploratory (certainty below chance, not helped).
- Per-writer (pooled T=100 operating point): P-K beats B5 for only 7 of 20 writers; median writer gain 0.6%. Prompts concentrate on writers whose keyword style drops cues (taps 0 to 308 per 1,000).

## ASK vs SHOW-TWO
ASK-ONE-CUE is never chosen by any policy (share of messages 0.0 at all budgets, P-K, P-I, P-O). The policy is a "show-two" policy. ASK-only P-K averts 4.0% at 100 taps (B5 ASK-only 2.9%), SHOW-only equals P-K (8.2%). q sweep (T=100, P-K / B5 / B1): q=.5 4.5/3.6/1.7; .7 6.6/5.1/2.3; .9 8.2/6.5/3.0; 1.0 9.3/7.3/3.3. Below q about 0.55 P-K (SHOW) falls under ASK-only (flat 4.0%). Break-even q vs B5 and B1: point estimate P-K >= B5 at every q >= 0.3 (grid floor; no break-even found); the P-K minus B5 CI includes 0 at every q at 100 taps. rho=1 changes nothing for SHOW policies.

## Internal and external signals, B6 (pooled local models qwen2.5-7b + llama3.1-8b; gemma3-4b NOT run; K=8)
| T=100 | P-K | P-X (external) | P-O (committed output) | P-I (internal) | P-ALL | B6 | B5 |
|---|---|---|---|---|---|---|---|
| % of B0 averted | 8.2 | 8.9 | 12.1 [6.9, 17.5] | 14.6 [9.9, 19.7] | 15.4 [10.3, 20.0] | 4.4 [1.7, 7.9] | 6.5 |
- Stop rule (R2-9): best = P-ALL, minus B5 = +8.9 pp [3.9, 13.4]; P-I minus B5 +8.1 [3.4, 12.9] (q=.5: +4.6 [1.8, 6.8]; positive CI at every q). Not a stop: signals beat B5 with CI excluding 0 -> round 3 = full test, figures, writing.
- AAC terms at 100 taps/1,000 (pooled): P-I averts 26.1 weighted (32.6 raw) silent errors per 1,000 messages = about 3.1 taps per error averted; B5 11.7 (6.9 taps/error); B1 5.3 (14 taps/error); P-K 14.6 (5.6). Prompts reach about 10% of messages.
- H2 (as pre-declared): speech-act AUROC gain P-I minus P-K +.073 [.028, .119] (>= .03 met) but T=50 averted P-I minus P-K +3.4 pp [-1.4, 7.8] pooled (excludes 0 only for qwen: +5.6 [0.7, 10.6]; llama +3.4 [-1.2, 7.9]); at T=100 +6.5 [0.9, 11.3]. "Internal beats external" (P-I minus P-X at T=50): qwen +4.9 [0.6, 9.6], llama +3.7 [-1.0, 8.4], pooled +4.8 [-0.3, 8.8]: 1 of 2 models, NOT met. H2 therefore NOT met as declared; at T=100 P-I beats P-X (+5.8 [0.4, 11.2]). Polarity: no signal helps (AUROC CIs include .5 for all; llama P-I .637 [.49, .78]). External P-X is no better than P-K (+0.7 [-2.5, 3.6]).
- Honest control (A3): P-O, simply knowing the committed output's cue state, gets 12.1% (P-O minus B5 +5.6 [0.5, 11.1]). P-I minus P-O = +2.5 pp [-2.8, 7.8], P-IO minus P-O +2.4 [-3.1, 7.2]: logprob/sampling/probe signals beyond the committed output are NOT demonstrated. Most of the gain is "ask when the model's own output lacks the cue".
- H4 (B6): P-I minus B6 +10.2 pp [4.4, 15.8] at T=100 (T=50: +6.2 [2.1, 10.2]); P-K minus B6 +3.8 [-0.5, 8.7]. B6 is no better than random (B6 minus B1 +1.4 [-1.3, 4.9]) and below B5 (-2.2 [-4.9, 1.4]). Caveat: B6 is an adaptation of an unverified source and uses only 8 T=1 samples labelled by L0.
- Calibration: ECE <= .04 for all feature sets (speech act P-I .033, P-O .027).
- identical regenerated text vs stored: qwen 91.8%, llama 91.2%.

## G1 comparison (transfer, no new generation)
G1 needs a chip to monitor; keyword-only inputs have none, so G1 alone averts 0 here. Ask-all-3-dims with chips (6,000 taps) leaves 30.6 weighted errors (147.5 averted); with G1 after the ask (W-C strict repair 52.5%, transfer estimate) 14.6 (163.6 averted). Always-show-two (3,000 taps) leaves 17.8; always-ask polarity only (2,000 taps) averts 23.8. These blanket options cost 20-60x more taps than the 100-tap policies and are reported in fixed_baselines.csv.

## H3 restated (success under amended targets only; heuristic calibration, no guarantee)
Original 5/10/20 stay infeasible. The round-1 "floor 47" justification was wrong: always-ask floor (rho<1) is 47.0 for round 1 but lambda=0 attains 25.5; primary scope: always-ask floor 30.6, lambda=0 floor 15.6 (3 prompts per message, 4,000 taps). Targets 22/33/55% residual of B0 (39.2/58.8/98.0), calibrated on writer-disjoint halves, 500 splits (P-K keyword policy):
| residual target | P-K taps (prompts/msg) | B5 randomised ladder at same realised risk | B1 | exceedance |
|---|---|---|---|---|
| 22% | 1,711 (1.7) | 2,206 | 2,681 | 35% |
| 33% | 1,018 (1.0) | 1,417 | 2,337 | 33% |
| 55% | 469 (0.5) | 754 | 1,653 | 31% |
Mean test risk is at or below target (35.3, 53.7, 89.8 vs 39.2, 58.8, 98.0) but exceedance is 31-40% (CRC bounds the mean; units are HT-weighted and cross-fitted, so exchangeability is not met). P-K saves 22-38% of taps vs B5 at equal risk, but operating points need 0.5-1.7 prompts per message (impractical at the low targets). Not rerun for P-I.

## Where it does NOT help
Polarity (AUROC CI includes .5; gains rely on prior and show-two); certainty and agent (exploratory; P-K below B5 at T<=50); external keyword-only detector; B6; the full five-dimension scope with lost cues only; ASK action. Writer-level: gains concentrated.

## Open items
gemma3-4b Stage 1 pending (GPU waiters paused by owner, D-084), H2 on 2 of 3 models. q still assumed: annotation Part B built and NOT sent (annotation/frontier_value_of_cue_items.json, _key.csv, 145 items; ANNOTATION_REQUEST.md). B6 source unverified. hw1/hw2 transfer not done.
