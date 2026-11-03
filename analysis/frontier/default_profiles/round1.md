# default_profiles, round 1 (pilot): results

Date 2026-11-02. Plan and decision rules: `PLAN.md` (sections 1-4 written before any outcome; section 8 addendum written before any probe or policy curve). Everything below is machine-only (stored outputs, a local logprob probe, no human labels) and **provisional**. Source labels for speech act and politeness are detector proxies; polarity detector agreed 150/150 with an LLM first pass. No J1 fallback anywhere (this round generated no new judged text).
Scripts: `src/frontier_default_profiles_s0.py` (inventory, placebo), `src/frontier_default_profiles_probe.py/.sh` (GPU probe under blocking flock), `src/frontier_default_profiles_policy.py` (profile, SLP price, policies, probe validity). Raw probe outputs: `runs/frontier_default_profiles_probe/*.jsonl`. Tables: `profile_gap_h1.csv`, `slp_weighted_price_h2.csv`, `placebo_h3.csv`, `policy_budgets.csv`, `policy_auc.csv`, `policy_paired_contrasts.csv`, `logprob_*.csv`, `pilot_inventory.md`, `summary.json`, `s0_summary.json`.

## What was and was not run
Run: S0 inventory (GO); H1/H2 profile and SLP-weighted price on the 4 stored elic1 models (qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra; 1,000 message-bootstrap resamples stratified by sample type, seed 20261101); H3 placebo on 6 models (hw1 + hwctl1 + 14B/Nemo hw/hwctl, 0 new generation); H4 policy comparison on 1,800 human keyword sets (+600 POS-cap4 as secondary); logprob probe on **3 of 5 local models** (qwen2.5-7b, llama3.1-8b, gemma3-4b; 7,200 prompts x 2 framings each).
Not run: qwen2.5-14b and mistral-nemo-12b probes (queued behind other frontiers' GPU jobs for hours; the queued job `runs/frontier_default_profiles_probe.log` may still complete: re-run `python src/frontier_default_profiles_policy.py` afterwards and the tables refresh; the numbers here use 3 probe models); 14B/Nemo bare generation + judging on the human keyword sets (so the profile has 4 models, not 6); S3 judge-error correction (RG/PPI; descriptive gold only); S4 DIF; Gemini; a separate verbalized-uncertainty arm (see probe note).

## S0: GO
Cue-positive human units (600 messages x 3 sets): polarity 366 sets (76 with the cue dropped), speech act 951 (417), politeness 381 (136), certainty 270 (112), quantity 30 (descriptive only). Placebo channel (irrelevant chip, plain word) stored on 6 models. Gate: polarity and speech act both >= 60 units, placebo on >= 4 models: GO. Human gold for judge error rates is small: 25 polarity, 24 politeness, 39 speech-act units, accuracy 1.00 [0.87, 1.00], 1.00 [0.86, 1.00], 0.97 [0.87, 0.995]: the CI half-width for sensitivity exceeds the .07 bar, so **trigger 5.3 (extra human gold) would fire** if S3 is run; no request was written because S3 was not run this round.

## H1: profiles and calibration gap (human keywords, 4 models)
Gap is defined here as P(source has the default reading | keywords lack the cue) minus P(model outputs the default | keywords lack the cue) = posterior of cue minus model cue-assertion rate. Positive = the model commits to the default more strongly than the human base rate supports. (PLAN section 4 H1 wrote the sign inconsistently, "positive" for polarity and "negative" for speech act; with one convention both are positive, so the literal "speech act negative" wording is moot. Reported honestly.)

| dimension | base rate P(cue \| no cue in keywords) | gap, pooled mean of models, pp [95% CI] | random-effects pooled | I^2 across models | per model (gemma, gpt, llama, qwen) |
|---|---|---|---|---|---|
| polarity | 2.7% [1.8, 3.7] | +2.5 [1.6, 3.5] | +2.5 [2.1, 3.0] | 0% | +2.7, +2.6, +2.3, +2.6 |
| speech act | 47.9% [42.8, 53.2] | +19.7 [14.1, 25.3] | +19.6 [14.9, 24.4] | 58% | +18.3, +13.8, +24.8, +21.8 |
| politeness | 6.5% [5.0, 8.4] | -0.2 [-2.3, 2.2] | -0.0 [-3.8, 3.7] | 87% | -6.7, +1.6, +2.8, +1.6 |

H1 verdict: SUPPORTED as pre-specified in spirit. Polarity gap CI excludes 0 and the four models agree almost exactly (I^2 = 0, i.e. the profile is a property of the task, not of a model). Speech act: gap +19.7 pp, CI excludes 0 and is >= 10 pp. Politeness is calibrated on average but heterogeneous (gemma3-4b over-asserts politeness by 6.7 pp). The pooled random-effects interval treats 4 correlated models as exchangeable (they share items), so it is narrower than the message-bootstrap interval; use the latter.

## H2: price and SLP weighting
Silent reversals per 1,000 messages (models mean, human keywords): polarity 23.9 [15.5, 32.5], politeness 49.4 [37.3, 64.3], speech act 161.9 [136.1, 190.6]. SLP severity weights from the two returned panels (descriptive, n = 2 raters): polarity (negation) 5/5 -> 1.0, speech act 4/5 -> 0.8, politeness mean(3,2)/5 = 0.5 (SLP1 0.6, SLP2 0.4). Weighted points per 1,000: speech act 129.5, politeness 24.7, polarity 23.9.
H2 rule (Kendall tau < 1, or polarity share rises >= 10 pp): **not met with mean weights** (tau = 1.0; polarity share of weighted total 13.4% vs 10.2% unweighted, +3.2 pp). Weighting does not change the ranking, a legitimate null. Sensitivity: with SLP2's weights politeness (19.8) drops below polarity (23.9) and tau = 0.33, so the polarity/politeness order is within the raters' disagreement. Clinical price of the bare default is therefore about 71-75% speech act, and 13% negation.

## H3: placebo-validated assumption effect (6 models, stored data, family-cluster bootstrap 2,000)
Criterion: |irrelevant-chip minus noncrit| <= 2 pp with CI inside +-4 pp, and chip1 minus irrelevant >= 10 pp with CI > 0.

| dimension | placebo diff [CI] pp | chip1 - irrelevant [CI] pp | assumption credited |
|---|---|---|---|
| polarity | 0.0 [0.0, 0.0] | +49.7 [49.3, 50.0] | yes (6/6 models) |
| politeness | 0.0 [0.0, 0.0] | +42.0 [40.6, 43.4] | yes |
| agent | -0.5 [-3.6, 2.9] | +66.7 [63.5, 70.3] | yes |
| speech act | +4.8 [2.6, 7.4] | +30.5 [26.6, 34.6] | **no** (0/6 models) |
| certainty | +5.5 [3.5, 7.4] | +48.4 [47.1, 49.6] | no |
| time/quantity | +1.7 [-0.7, 4.3] | +81.1 [78.1, 83.9] | no (CI exceeds +-4) |

Caveat that matters: for polarity and politeness the A/B pair design makes the bare critical-match rate exactly 0.5 whenever a model always commits to one reading, so the placebo difference is zero by construction (the clean result is that an irrelevant chip does not unlock the other reading). The informative failures are speech act, certainty and time/quantity: an irrelevant chip shifts the output by 2-6 pp there, so the assumption/violation split on those dimensions is NOT reported as causal.

## H4: ask-or-assume policies (human keywords, same 1,800 units; exposure event E = cue in source, dropped in keywords)
Reversals left per 1,000 messages at a 10% ask budget (= 100 asks per 1,000 messages), 95% message-bootstrap CI. Always-ask = 0 reversals at 1,000 asks. "Conf (3-model mean)" is the logprob forced-choice probe gated by the same lexical cue test as the other policies; "raw" ungated is in the CSV. Full 2/5/10/20% budgets and AUC in `policy_budgets.csv`, `policy_auc.csv`.

| dimension | always-commit | random ask | shortest-first | confidence (probe, 3-model mean) | PROPOSED prior (no model calls) |
|---|---|---|---|---|---|
| polarity | 24.4 [16.1, 33.1] | 21.9 [14.5, 29.8] | 23.5 [15.4, 32.3] | 17.5 [11.2, 23.5] | **17.7 [11.0, 24.8]** |
| speech act | 277.5 [240.4, 314.4] | 249.7 [216.4, 282.9] | 230.9 [197.6, 265.6] | 224.1 [190.7, 257.5] | 223.7 [190.7, 260.9] |
| politeness | 56.4 [43.0, 72.6] | 50.7 [38.7, 65.3] | 46.7 [35.4, 61.2] | 50.0 [36.9, 64.7] | 40.2 [28.8, 52.3] |

Paired contrasts at 10% (`policy_paired_contrasts.csv`):
- Polarity: prior vs random -4.3 per 1,000 [-9.1, -0.6] (19.5% fewer reversals, CI [3%, 40%]); prior vs confidence (3-model mean) +0.2 [-3.7, 4.5]: indistinguishable. **H4 success criterion (prior >= 25% fewer reversals than confidence, CI excluding 0) is NOT met.** Per the rule's fallback, the claim is only that a no-model-call prior matches model confidence on polarity.
- Speech act: prior -26.0 vs random [-37.3, -13.7] (10.4% fewer) but equal to confidence (-0.4 [-12.4, 13.8]) and to the shortest-first heuristic (-7.2 [-21.5, 8.1], not distinguishable).
- Politeness: prior -10.6 vs random [-19.6, -4.5]; vs confidence not significant.
AAC terms, polarity, prior at 10% budget: 6.7 silent reversals avoided per 1,000 messages (SLP weight 1.0 = 6.7 weighted points) for 100 asks, i.e. **about 15 asks per reversal prevented**, against 41 asks per catch for always-ask (1,000 asks / 24.4) and 41 for random. Speech act, using the model-output event (what models actually get wrong, 161.9 -> 138.9): 23 reversals avoided at 100 asks, about 4.3 asks per catch (random: 16 avoided). The precision gain over random is real but modest on polarity (2.7x), and the absolute reduction is small: polarity reversals per 1,000 for the prior at 2/5/10/20% asks are 20.3 / 18.6 / 17.7 / 14.1 (always-commit 24.4; random 23.9 / 23.2 / 21.9 / 19.5), i.e. 17% / 24% / 28% / 42% fewer than always-commit. POS-cap4 channel (secondary): polarity prior 85.7 [66.6, 108.3] vs random 102.6 vs commit 114.0 reversals per 1,000.
Where no policy helps: speech act, where the best policies remove ~20% of reversals at 10% asks and shortest-first is as good as anything (the human-keyword break-even is 1.1:1, so asking is near-uninformative), and polarity at very small budgets, where the prior gains little over random (20.3 vs 23.9 at 2%; CIs for the 2% contrast are in `policy_paired_contrasts.csv` only at 10%, so the 2% difference is not tested).
Model-output sensitivity (events weighted by the 4 models' actual miss rate) gives the same ordering (polarity prior 17.3 vs commit 23.9, speech act prior 138.9 vs 161.9).
Comparators NOT on the same items: G1 (commitment guard) only checks cues the user supplied (src/interventions.py docstring: bare input gets no check except the politeness rule), so on unaided keyword sets it prevents nothing; the guard was evaluated on hw1/W-C pairs, not here. Cue chip / plain word supply the cue (H3 shows the restoration effect on stored pairs: chip1 minus irrelevant +30 to +67 pp) but need a tap or word on every message that shows them; taps per 1,000 were not computed (no new tap data). A same-items G1/chip comparison needs a decision on what fraction of messages gets a prompt: the policy curves above are exactly that curve for the "when to show a chip" decision.

## Logprob probe validity (stop rule)
Declared stop rule: Spearman(q, judged output asserts cue) < 0.2 -> drop the logprob arm. Observed (human keywords, no cue in keywords): qwen2.5-7b 0.05 / 0.14 / 0.06, llama3.1-8b 0.09 / 0.22 / 0.00, gemma3-4b 0.04 / 0.11 / -0.01 (polarity / speech act / politeness). **Rule triggered** on 8 of 9 cells (llama speech act 0.22 passes): the logprob arm is NOT a primary comparator; its H4 rows are exploratory. Context: the forced-choice probe says "negated" with mean probability 0.37-0.49 on no-negation-word keywords whereas the same models generate a negated sentence on 0.07-0.33% of them (and the base rate is 2.7%), so the readout is not on the generation scale; AUROC of q for predicting exposure among lexically-no-cue units is 0.56-0.70 (polarity), 0.57-0.74 (speech act), 0.51-0.63 (politeness) (`logprob_auroc_exposure.csv`). Because the first-pass probe design (A/B letters, pilot on qwen 1,000 rows, discarded unanalysed) showed an always-'A' position bias and ~65% unparseable tokens, the final probe uses two Yes/No framings; I report the pre-declared mean of both framings AND the non-default-question-only readout (`q0`), which was added after seeing that the second framing diluted polarity (both are in the CSVs; q0 is slightly better on speech act). This is a forking path, disclosed. The probe is a single-token verbalized-style readout, so it is not a separate verbalized-uncertainty arm; the 14B verbalized variant was not run.

## Where the method does not help / limits
- Speech act: policies cut reversals at most ~20% at 10% asks; weighting does not reorder dimensions; assumption effect not placebo-clean.
- No claim that the prior beats model confidence. No claim of user benefit; units are classmate keywords (about 20 non-AAC adults), not AAC users; E for speech act and politeness depends on detector-proxy source labels (Part 21 source-check scoring would bracket this).
- Prior: 76 polarity exposure units; CV scores are computed once, not refit within the bootstrap (CI slightly optimistic); ranks policy by predicted P(cue), so the cost weighting is irrelevant within a dimension.
- Exposure treats every exposed unit as a silent reversal; the model-output event shows this overstates speech act by ~40% (277 vs 162).
- Placebo for polarity/politeness is mechanical (see H3 caveat).
- 3 probe models only; 14B/Nemo and Gemini pending.

## Next (round 2 proposals)
Finish 14B/Nemo probes; generate P0 bare for 14B/Nemo on the 1,800 sets and judge via arbiter; S3 RG/PPI with the (small) gold; a 150-item gold draw for polarity/speech-act outputs of the new models if S3 shows sensitivity CI half-width > .07; run G1 and the chip on the elicitation outputs to get a same-items comparator.
