# default_profiles Follow-up F1 (2026-11-03): same-items chip / plain-word / G1 restoration and a CLAM-style comparator

Label: POST-PILOT follow-up. Rule: PLAN.md section 11, written before any F1 generation, judging or probe output existed. Source: SYNTHESIS.md section 5 item 6. Scripts: `src/frontier_default_profiles_f1_{build,gpu.sh,guard,judge.sh,clam,clam_analyze,analyze}.py`. Outputs: `followup/` and `followup_summary.json`. No human labels; machine-judged (gpt-6.1-sol J1/J2).

## What was run
- 332 exposure units from the elicitation set (cue in the source, dropped from the human keyword set): polarity 76, politeness 136, speech act 120 (random 120 of 414, seed 20261103, question or request only). Arms: bare (the stored elic1 P0 output), chip ([NOT], [PLEASE], [?] or [ASK]), plain word ("not", "please", "question", "request"), chip + G1 (guard, up to 2 retries, spec = supplied chip). Models: gpt-6.1-terra, qwen2.5-7b, llama3.1-8b, T = 0. Pooled with equal model weight; message-cluster bootstrap B = 2,000, seed 20261103, stratified by sample type.
- Judging: 2,071 + 665 unique outputs, J1 vs J2 critical agreement 99.3% / 99.5%. 15 + 3 disputes (J1 != J2). Resolved by the blind arbiter (`src/arbiter_tool.py`, output text only, Claude Sonnet 5.5, per the follow-up instruction; arbiter agreed with J1 on 11 and J2 on 7). No J1 fallback. PLAN.md section 11 also allows "exclude and bound"; both are reported as sensitivities (excluded; all-fail; all-pass) and change no decision except one noted below. Deviation to note: the plan names gpt-6.1-sol as the arbiter and the output-text-only Claude arbiter replaces it by instruction; Claude is not judging its own outputs here (outputs are from terra, qwen, llama).
- G1 ran on 285 unique chip prompts per model (duplicate keyword strings share a prompt); initially flagged 68 (terra), 54 (qwen), 44 (llama); extra calls 97, 84, 69.

## Result 1: restoration r (share of exposure units whose output honours the dropped cue), pooled, 95% CI
| dimension | bare | chip | plain word | chip + G1 |
|---|---|---|---|---|
| polarity (n 76) | .024 [.003, .056] | .934 [.890, .973] | .895 [.842, .944] | .950 [.909, .986] |
| politeness (n 136) | .081 [.041, .133] | .988 [.974, .998] | .979 [.961, .994] | 1.000 [1.000, 1.000] |
| speech act (n 120) | .299 [.219, .386] | .756 [.698, .817] | .792 [.722, .860] | .904 [.856, .949] |

Per model (arbiter-resolved): polarity chip terra .867, qwen .995, llama .940; word .855, .864, .965. Politeness chip .984, 1.000, .979; word .991, 1.000, .946. Speech act chip .747, .701, .820; word .774, .838, .764. Full table: `followup/f1_restoration.csv`; per-unit outcomes `followup/f1_unit_outcomes.csv`.

## Result 2: derived price, reversals per 1,000 messages when the arm is applied to every message
Exposure per 1,000 messages from round 3 (24.4 / 56.4 / 277.5) x (1 - r).
| dimension | always-commit (this sample) | r3 model-visible always-commit | chip | plain word | chip + G1 |
|---|---|---|---|---|---|
| polarity | 23.8 [23.0, 24.3] | 23.9 | 1.6 [0.7, 2.7] | 2.6 [1.4, 3.9] | 1.2 [0.3, 2.2] |
| politeness | 51.8 [48.9, 54.1] | 49.4 | 0.7 [0.1, 1.4] | 1.2 [0.3, 2.2] | 0.0 [0.0, 0.0] |
| speech act | 194.5 [170.4, 216.8] | not computed in r3 | 67.7 [50.7, 83.8] | 57.7 [38.9, 77.2] | 26.7 [14.1, 39.9] |
The bare arm of this sample reproduces the r3 always-commit numbers (23.8 vs 23.9; 51.8 vs 49.4), so the unit construction matches. The price assumes a cue is given on every message (1 tap or 1 word each); it does not model asking on messages without a cue, so these are the best case for the cue arms. Intervals exclude exposure-rate uncertainty (the round-3 exposure is taken as fixed).

## Decisions (declared rules)
- D1 chip vs plain word (pooled): polarity chip - word +3.9 pp, 90% CI [+0.3, +7.8], 95% CI [-0.5, +8.6]: not distinguishable (not equivalent within +-5 pp). Politeness +0.8 pp, 90% CI [-0.5, +2.3]: equivalent. Speech act -3.6 pp, 95% CI [-8.7, +1.7]: not distinguishable (under the all-fail dispute bound the 95% CI is [-10.4, -0.7], "word better"; this is the only decision a dispute treatment changes).
- D2 guard on chip (paired, pooled): polarity +1.6 pp [+0.3, +3.3], politeness +1.2 pp [+0.2, +2.6], speech act +14.8 pp [+9.8, +20.1]: the guard helps in all three. This is "chip plus guard", not G1 against chip in the field: the spec is the supplied chip, so it only repairs dropped chips, and it costs extra generation calls (about 0.2 to 0.3 per chip prompt).
- D3 transport of the r3 rho (chip1 / nlcue discriminating pairs from hw1): polarity DID NOT TRANSPORT (transported chip .995, word .987; measured .934 and .895; both outside +-5 pp and outside the CI); politeness DID NOT TRANSPORT in the other direction (transported .882 and .903; measured .988 and .979); speech act: chip held (.787 vs .756) but word did not (.868 vs .792), so the dimension is "did not transport". The r3 chip and word rows are superseded by the measured rows above. Direction: r3 was too optimistic for polarity (about 1.6 vs 0.1 per 1,000 for chip, still small) and too pessimistic for politeness (r3 chip/word rows overstated remaining reversals).

## Result 3: CLAM-style generic clarification trigger (D4)
Generic few-shot yes/no "does this keyword string need a clarifying question?", score = P(yes) from first-token logprobs, mean of qwen2.5-7b, llama3.1-8b and gemma3-4b, all 1,800 human keyword units, ask the top 10% (gated like the prior). Silent reversals per 1,000 messages (model-visible), same units and weights as r3, B = 1,000.
| dimension | CLAM mean gated | gated random | r3 probe confidence mean | always-commit |
|---|---|---|---|---|
| polarity | 21.2 [13.6, 30.8] | 21.3 [14.3, 30.0] | 17.4 [11.1, 24.2] | 23.9 |
| politeness | 45.5 [33.3, 58.8] | 43.7 [32.0, 56.3] | 44.8 [32.5, 57.5] | 49.4 |
Named contrasts (Holm over 4): CLAM - gated random, polarity -0.0 [-3.0, +2.2], p_Holm 1.00 (MDE 3.8 per 1,000); politeness +1.8 [-1.1, +4.3], p_Holm .59 (MDE 3.8). CLAM - probe confidence mean: polarity +3.8 [+0.1, +8.8], raw p .049, p_Holm .20; politeness +0.7 [-2.5, +5.2], p_Holm 1.00. AUROC of the CLAM score for exposure among gated no-cue units: polarity .563, politeness .487 (probe confidence .672 and .549). Per-model CLAM and ungated variants are in `followup/clam_contrasts.csv` (exploratory; none beats gated random).
Verdict: the "benchmark unmet" gap is closed (comparator computed on the same units). H4 is NOT revised: a CLAM-style generic clarification trigger also fails to beat gated random, with an MDE of about 3.8 reversals per 1,000. The existing probe confidence mean is nominally the better ranker for polarity but only at uncorrected p = .049.

## What this changes
- The cue arms are now measured, not transported. Giving the model the cue (chip or word) restores it in 93 / 99 / 76% (chip) of exposure units; the chip is not shown to beat the plain word. Chip + G1 is the best arm on every dimension, and it is the first same-items measurement of G1 (previously unbenchmarked).
- The ask-policy null stands. The remaining uncertainty is not the trigger, it is that the cue still has to be elicited.
- Limits: 76 polarity units (wide CIs); three models and one prompt (P0); machine judging only (no human check of the restored outputs); speech-act units are a 120-unit subsample; the price ignores the cost of cueing messages that need no cue.
