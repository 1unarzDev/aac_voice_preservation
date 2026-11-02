# Frontier: calibrated ask-or-assume (value-of-cue) policy -- PLAN

Written 2026-11-02 BEFORE any outcome for this frontier was computed or inspected. The only stored numbers used to design it are those already in the repo
(analysis/robust/t2_posterior/report.md, SLP severity returns, D-066..D-079). Everything here is frozen once committed to the hash deposit; changes go
in a dated "Amendments" section at the bottom, never by editing above.

## 1. Question and claim to test
Models commit silently to affirmative / plain / statement defaults (>99% on polarity); supplying the missing cue fixes it (chip or plain word, D-070), but every
cue costs the user taps. Question: **can a per-message, per-dimension policy choose among COMMIT / SHOW-TWO / ASK-ONE-CUE so that clinically weighted silent
reversals fall substantially at a small tap cost, and does a distribution-free guarantee (conformal risk control, CRC) hold on held-out writers?**
Honest framing: we do NOT claim "first to use VOI / conformal / MBR". We claim the first cost-priced, per-dimension, SLP-weighted evaluation of the
commit-vs-ask decision for AAC keyword expansion on human-typed keywords, with model-internal vs external signals compared on the same items.

## 2. Literature check (WebSearch 2026-11-02; [S] = seen in search results, not opened; [F] = opened by an earlier ideator, see ideas/frontier/uncertainty_decoding.md)
Nothing found that combines AAC + commit/ask decision + clinical costs + risk control. Closest, and how we differ:
- Cai et al., *Context-Aware Abbreviation Expansion Using LLMs*, arXiv 2205.03767 [S]: AAC (eye-gaze); names expansion errors and keystroke cost as the tension; proposes
  options/confirmation but no decision rule, no cost model, no guarantee. -> we supply the decision rule and evaluate it.
- Shen et al. KWickChat (cited in arXiv 2501.10582, *Adapting LLMs for character-based AAC*) [S]: keyword->utterance LLM AAC; no ask/commit policy.
- *Clarify When Necessary: Resolving Ambiguity Through Interaction with LMs* (OpenReview XgdNdoZ1Hc; NAACL 2025 Findings version; authors not verified) [S]:
  entropy over simulated intents, ask on top-b% uncertain, cost = interaction. **Implemented as the "closest published method" baseline** (entropy-gated asking,
  budgeted); it has no per-dimension error weights and is not on AAC.
- Deng et al. (EIG-reward clarification), Zhang & Choi, QuestBench, Su & Cardie [F in ideas file]: question choice by information gain about task intent; no asymmetric
  clinical cost, no motor cost.
- Angelopoulos, Bates, Fisch, Lei, Schuster, *Conformal Risk Control*, ICLR 2024 (arXiv 2208.02814) [S, venue confirmed]: the guarantee we use (monotone loss).
  Quach et al. *Conformal Language Modeling* ICLR 2024 [F]: sets of generations; not commit/ask.
- *When Can CRC Certify LLM Outputs?* arXiv 2606.29054 [S]: alpha* = c_abstain/c_error cost-aware rule; used as the "break-even Chow rule" baseline.
  *Cost-sensitive conformal prediction and HITL abstention* arXiv 2607.27143 [S]; *Uncertainty Quantification for LLM Agents* arXiv 2609.07395 [S] (survey: ask when
  EIG > interaction cost). A search found no work calibrating a three-way answer / ask / defer choice with CRC under asymmetric costs.
- Tomov et al. arXiv 2601.21500 [F] (MBR in task latent space), Daheim & Gurevych arXiv 2606.30578 [F] (Bayesian decisions under ambiguity): decision-theoretic templates.
Novelty verdict: MEDIUM. Components are known; the setting, cost source (SLP weights), tap pricing and the same-items comparison of internal vs external signals are new.
Before any paper claim, re-run: "AAC clarification policy", "keyword expansion ask vs assume", "SpeakFaster / KWickChat confirmation" and verify the [S] items by opening them.

## 3. Data (all stored or cheap; no human participants, no IRB)
- **Unit** u = (message i, writer w, dimension d). Source: elicitation, 600 AACText messages x 3 human keyword sets = 1,800 sets from 20 adult annotators
  (analysis/elicitation/messages.csv, ratings.csv; HT inclusion probabilities kept: all population estimates are HT-weighted exactly as in robust_t2_posterior.py).
- **Outcome (commit loss)** for model m (the 4 P0 models in runs/elic1: qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra) on unit u:
  r_{u,d,m} = 1 if source has cue d AND keywords lack it (lenient human "lost" flag; lexicon fallback as in T2) AND the P0 output (arbitrated labels, no J1 fallback) lacks the cue value.
  s_{u,d,m} = spurious: output asserts cue d the source lacks. Dimensions: polarity, speech_act, politeness, certainty, agent (judge labels exist for these five; time and quantity have
  no output labels and are EXCLUDED, stated as a limitation).
- **Clinical weights** (expert_package/returns_slp, Task 1; mean severity/5): NEG 1.00, ACT 0.80, AGT 0.80, CRT 0.70, POL 0.50 (TIM 0.80, ADD 0.80 unused here). n=2 SLPs: sensitivity over
  (a) each SLP's own weights, (b) uniform weights, (c) 1,000 random weight vectors in [0.2,1]; conclusions must survive (a)-(b), ranking stability under (c) is reported.
- **Source-label caveat**: source cue flags are detector labels (polarity 150/150 vs LLM; others weaker). Part 21 human source check (annotation/returns_source_check) is used ONLY to
  re-weight / report sensitivity when its returns are scored; headline stays provisional until then.
- hw1 (546 human-written minimal families, gold critical values) is a SECOND population (prevalence ~50%, designed) used for transfer / shift tests, never for base rates.
- hw2 (60 pairs from Part 15) is held back as a final untouched test if checks are accepted (see 6.4).

## 4. Actions, costs, simulated user (frozen)
Per unit and dimension the policy picks one of: COMMIT (0 taps; loss = w_d * r); SHOW-TWO (1 tap: the default sentence plus the cue-flipped alternative; user picks right one with prob q,
primary q = 0.9, sweep 0.7/0.9/1.0; alternative covers the true meaning only for the flagged dimension); ASK-ONE-CUE (2 taps: open cue row + choose value; resolves dimension d with the measured
chip-restoration rate rho_d from hw1 chip1 vs bare [stored], sweep rho=1). At most ONE action per message in the primary analysis (argmax over d of expected benefit); two-ask variant is secondary.
Spurious loss uses the same w_d (primary); a x0.5 and x2 spurious weight is a sensitivity analysis.
Tap price lambda is never chosen post hoc: we report the full frontier (weighted reversals per 1,000 vs taps per 1,000) and fixed budget points T in {20, 50, 100, 200, 400} taps/1,000 messages.
Taps are a proxy for motor effort; we do NOT claim seconds or fatigue (no AAC-user data).

## 5. Policies compared (all on the same 1,800 units, same folds)
B0 always-commit (the status quo, = 100% of reversals). B1 random-ask at matched taps (1,000 draws). B2 always-ask all 5 dimensions (chip row; max taps). B3 always-ask polarity only.
B4 always-show-two. B5 prior-only rule (ask the dimension with the largest population prior x w; no per-message signal = Chow/break-even with base rates, alpha* = c_ask/c_err style).
B6 **closest published**: entropy-gated asking (Clarify-When-Necessary style): entropy of commitment value over K=16 T=1 samples, ask if above the budgeted quantile.
B7 guard G1 (monitor + regenerate, 0 taps): not re-run on elicitation (no cue-bearing loop here); its measured fail->pass conversion on W-C speech act (D-068) and hw1 is reported next
to the frontier as a zero-tap alternative, labelled a TRANSFER estimate, and also shown as the combination "G1 then policy" on hw1 only if time allows.
B8 cue chip / plain word = the ASK action itself (D-070); the policy decides when to spend it.
P-K keyword-feature policy (signals S1). P-X external-signal policy (S1+S2). P-I internal-signal policy (S1+S3, per model). P-ALL (S1+S2+S3).
Policy form for all P-*: calibrated risk estimate p_d(u) = P(r_d=1 | signals) from a regularised logistic model (primary) or gradient boosting (secondary), then expected-benefit rule
benefit(a,d) = w_d * p_d * (1 - residual(a)) - lambda * taps(a); choose the best action. (Chow-type Bayes rule.)

## 6. Experiments (staged; each <= ~1 day compute)
### Stage 0 -- cheap pilot, CPU only, ~3 h, 0 model calls
Build the unit table; reproduce T2 numbers (consistency gate: polarity silent reversals 23.9 per 1,000 within +-1.0, speech-act 161.9 within +-3, per-model identical). Fit S1 keyword-feature
policy (features: n keywords, cue-lexicon hits per dimension in keywords, keyword POS pattern, writer-free text features, whether keywords contain a question/modal/negation word, content-word count)
with nested writer-and-message-disjoint CV (5 writer groups x 5 message groups, train on off-diagonal, test the diagonal block). Report AUROC per dimension, frontier vs B0/B1/B2/B5.
**Gate G0 (pre-declared):** proceed to Stage 1 regardless (internal signals are the scientific point); but if S1 AUROC <= 0.55 on ALL dimensions and P-K does not beat B1 at T=50, the paper states
"keywords alone carry no usable risk signal" and the claim narrows to H2/H3.
### Stage 1 -- model-internal signals, local GPU, ~8 h, one server at a time under blocking `flock /tmp/aacv_gpu.lock`
Models: qwen2.5-7b, llama3.1-8b, gemma3-4b (those with stored P0 labels) via src/serve_local.sh; confirmation on qwen2.5-14b for the headline model only. Per unit (1,800) and model:
(a) P0 greedy regeneration with n_probs=10 -> mean/min token logprob, first-token entropy, margin; identical-text rate vs stored output is reported; units whose regenerated text differs use
the stored output's label and the logprob features are flagged (primary analysis = identical-text units, sensitivity = all).
(b) K=16 samples at T=1 -> sampling frequency of each cue value per dimension and commitment-vector entropy, labelled by the deterministic L0 lexicon labeller (src/layer0.py) -- if L0 does not
cover a dimension, that dimension's sampling signal is dropped and reported as such (no extra judge spend).
(c) Verbalised/forced-choice probe: after the P0 prompt, "Could the writer have meant <cue value>? Answer Yes or No." -> P(Yes) from logprobs, per dimension (prefill-only, ~9,000 calls/model).
Output: runs/frontier_value_of_cue_*; features table analysis/frontier/value_of_cue/features_internal.parquet. Compare calibration of p-hat to the HT base rate (reliability curve, ECE) -- Idea A
as a by-product (the "calibrated but argmax'd" question).
### Stage 2 -- external detector, API, ~2 h, concurrency <=3
gpt-6.1-sol (effort low; the judge model family, but a SEPARATE zero-shot prompt that sees only the keywords, never the source or output): for each of 1,800 keyword sets give 0-100 probability that the
writer dropped each of the five cues. 1,800 calls, cached. Plus S2-lex: dimension-specific lexicon detector. Circularity guard: this prompt never uses the judge/arbiter labels; the
outcome labels come from the unchanged arbiter pipeline. No Gemini.
### Stage 3 -- policies, frontier, CRC, CPU, ~4 h
(3a) Frontier on held-out writer-and-message blocks for all policies/baselines/models; paired comparisons on identical units.
(3b) CRC: loss L(lambda) = SLP-weighted silent-reversal loss per message under the policy at threshold lambda (monotone: lower lambda -> more asks). Calibrate lambda-hat on writer-disjoint calibration
blocks to target alpha in {5, 10, 20} weighted reversals per 1,000; evaluate on held-out writers x held-out messages over 500 random block splits (10 writers cal / 10 test; message halves).
(3c) Shift: calibrate on elicitation, evaluate on hw1 (prevalence 50%); report violation, then prevalence-reweighted (covariate-shift) CRC as exploratory.
(3d) Sensitivity: SLP weights, q, rho, spurious weight, two-ask, per-model, logistic vs boosted, excluding agent/certainty.
### Stage 4 -- optional confirmation / human validation (see ANNOTATION_REQUEST.md)
Freeze policy and lambda from Stage 3, then evaluate once on hw2 (60 pairs, 4 models, stored P0 + judged) for polarity/speech-act where applicable and on the pooled hw1 families; report as a
single pre-declared confirmatory test, not tuned.

## 7. Hypotheses and PRE-DECLARED decision rules
Unit of inference: writer-and-message cluster bootstrap (2,000 resamples, resampling writers and messages jointly by block), 95% percentile CI, on the held-out blocks only. With 20 writers CIs are
optimistic; state direction and the wider of the writer-cluster and message-cluster intervals.
- **H1 (value of a per-message policy).** At T=50 taps/1,000 the best P-* policy averts more SLP-weighted silent reversals than B1 random-ask at matched taps and than B5 prior-only.
  SUCCESS: paired difference vs B1 CI excludes 0 AND relative reduction of weighted reversals vs B0 >= 25% at T=100. PARTIAL: beats B1 but < 25% -> report as modest. FAIL: CI includes 0 vs B1 -> "no
  usable per-message signal; blanket cue prompts are as good" (published as a negative result; the cost-surface and base-rate analysis stand).
- **H2 (internal vs external signals).** Internal signals add predictive value beyond keyword features: delta AUROC (P-I minus P-K) >= 0.03 for polarity or speech act, AND weighted reversals averted at T=50
  (P-I vs P-K) CI excludes 0. External (P-X) vs internal compared by the same two statistics; "internal beats external" is claimed only if P-I > P-X with CI excluding 0 on >= 2 of 3 local models;
  otherwise "no detectable difference" (and cost: internal is free at inference, external needs an extra call). Any single-model win is reported as model-specific.
- **H3 (guarantee).** CRC held-out mean weighted risk <= alpha (point estimate) for alpha = 10 and 20 across the 500 splits, and its violation rate (split risk > alpha) reported (CRC controls the
  mean, not each split). SUCCESS: mean test risk <= alpha and CRC needs fewer taps than B2 always-ask at the same alpha. If target alpha is below the residual floor from imperfect cue restoration (rho<1), declared INFEASIBLE.
  Shift (3c) is expected to fail without reweighting; we report it, no spin.
- **H4 (closest published method).** P-* beats B6 entropy-gated asking at matched taps (CI excludes 0). If B6 is equal, say so; the contribution is then the cost/weights/guarantee framework, not the signal.
- **H5 (where it does NOT help; descriptive).** Speech act: posterior ~48% so single-dimension default is a coin flip; expect little risk concentration. Report per-dimension frontiers; any dimension where
  P-* does not beat B1 is listed as not helped. Politeness added (spurious) channel reported separately.
- **Headline AAC numbers reported** (per 1,000 messages, HT-weighted): silent reversals (raw), SLP-weighted reversal cost, taps, spurious additions, plus "taps per reversal averted" and share of messages
  shown any prompt. Acceptability of repairs/outputs (SLP rating, guard, chip vs word) is cited from the SLP panel, not re-estimated.
- **Claims allowed in papers:** only the rows whose rule above is met; everything else "exploratory". Machine labels are never called human validation; provisional until Part 21 source check and the
  frontier annotation check (below) are scored.
- **Stopping/ordering rules:** Stage 0 -> 1 -> 2 -> 3 in order; no peeking at hw2 before freeze; model/feature set fixed after Stage 3a CV; all hyperparameters chosen by inner CV on training blocks only;
  no result is dropped for being negative; every run logged with seed. Any deviation goes in Amendments.

## 8. Compute / people summary
Stage 0: CPU 3 h. Stage 1: ~8 h GPU under lock (3 models x (1,800 greedy + 28,800 T=1 samples + ~9,000 probe calls); 14B confirm ~3 h). Stage 2: 1,800 gpt calls (~1 h at concurrency 3). Stage 3: CPU.
No new people required for the machine-only evidence. Optional human check: ANNOTATION_REQUEST.md (~20 adult non-author annotators, ~8 min each; no SLP need; no AAC users).

## 9. Risks (known before outcomes)
1. Source-cue labels are detector-derived. 2. Only 20 writers: CRC exchangeability across writers is thin. 3. Chip restoration rate rho and q are simulated, not user-measured. 4. Four P0 models are
near-identical in output (99.9% default), so between-model comparisons of signals have little outcome variation for polarity. 5. gpt-6.1-terra has no logprobs: internal signals only for the 3 local models.
6. Greedy regeneration may differ from stored text (reported). 7. Possible circularity if the external detector shares priors with the judge: the detector sees keywords only.

## Amendments
### A1 (2026-11-02, written after the unit table and the T2 consistency gate were computed, BEFORE any policy/frontier/CRC outcome was computed or inspected)
- Gate result: unit table reproduces T2 (polarity 23.9 /1,000, speech act 162.0, politeness 49.4; per-model identical to the T2 table). Gate PASSED.
- Outcome definition used (frozen): polarity / politeness / speech act exactly as in robust_t2_posterior.py (source cue present AND keywords lack it [lexicon for polarity and politeness, lenient lost flag for speech act] AND P0 output lacks the cue-bearing value); certainty and agent: source cue present (key `present`) AND lenient lost flag = 1 AND output label differs from the detector source label. Spurious s: output asserts the cue the source lacks (agent: undefined, set 0). Commit-error event per (unit, dimension) y = r + s, averaged over the 4 models (outcome = fraction of models that err). Agent and certainty "reversals" include detector-vs-judge label disagreement and are the least trustworthy dimensions; headline numbers are given with and without them.
- rho_d (ASK restoration) = chip1 restoration rate from analysis/chip_controls/channel_rates.csv (ALL models): polarity .995, speech act .787, politeness .882, certainty .954, agent 1.000. q = 0.9 (sweep .7/.9/1).
- SLP weights (Task 1, mean severity/5): NEG 1.0, ACT .8, AGT .8, CRT .7, POL .5 (SLP1: CRT .8, POL .6; SLP2: CRT .6, POL .4).
- FEASIBILITY, computed from stored quantities only: B0 SLP-weighted commit error = 451 per 1,000 messages; the "ask every dimension" floor (rho < 1) = 46.8 per 1,000; the one-action-per-message oracle floor = 145. Therefore the pre-declared CRC targets alpha = 5, 10, 20 per 1,000 are INFEASIBLE (below the always-ask floor) and are declared so (H3 rule). Added CRC targets (declared before CRC is run): alpha in {100, 150, 250} weighted per 1,000 (22%, 33%, 55% of B0), with the CRC policy deciding per dimension independently (one shared lambda, up to 5 actions per message) because the one-action cap cannot reach them. The one-action-per-message frontier stays the primary frontier analysis. H3 SUCCESS rule otherwise unchanged (mean test risk <= alpha and fewer taps than B1 random-ask and B5 prior-only calibrated to the same alpha; B2 always-ask has 10,000 taps).
- Stage-0 policy fitting: L2 logistic on S1 features, C chosen by inner 3-fold CV (grouped by message group) on training blocks only; held-out predictions from 25 (writer-group x message-group) blocks, each unit predicted once by a model trained with its writer group AND message group excluded.
- Frontier points: lambda grid (300 log-spaced values) applied to pooled held-out predictions; budgets T in {20, 50, 100, 200, 400} read off by linear interpolation. Bootstrap: 2,000 resamples each of (writers x messages jointly), writers only, messages only; reported CI is the widest of the three. B1 = expected value of random action on a random dimension at matched taps (analytic, better of ASK and SHOW-TWO). B5 = the single best (action, dimension) under population prior only, applied to a random fraction of messages. "Oracle" = same machinery with p = realised y (upper bound).
- NOT run in this pilot (Stage 1/2/3c/4 need GPU/API/hw1 and are deferred): B6 entropy-gated baseline (needs samples), internal-signal and external-detector policies (H2, H4), hw1 shift (3c), hw2. H2/H4 remain OPEN.
