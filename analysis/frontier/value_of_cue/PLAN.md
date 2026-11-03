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

## Decisions
### D-R1 (2026-11-02, after round 1 of 3, director) -- CONTINUE (round 2), with fixes first
Verdict: Stage 0 is valid (no fatal issues) but the headline is modest (5.6% [4.0, 7.5] at T=100; P-K beats B1 and B5, B5 gets ~64% of it) and benchmarking is incomplete (no B6, no G1, H2/H4 open). Continue, but round 2 must first repair the claims, then add the missing benchmarks. Labels below marked "post-pilot" are amendments made after seeing Stage-0 outcomes.

Round-2 instructions (in order; items 1-4 are CPU-only and must precede any GPU/API work):
1. (post-pilot) Restate H3: do NOT report "SUCCESS as pre-declared". Report it as "success under amended targets 100/150/250", note the "floor 47" justification was wrong (lambda=0 attains ~25.5; state both the rho<1 always-ask floor and the lambda=0 floor), and that operating points need 1-3 prompts per message (impractical). Compare B5 at EQUAL REALISED RISK using randomised/interpolated ladders (same granularity as P-K), not the coarse CRC ladder; state that P-K and B1 reach equal risk at alpha=100. Note CRC exchangeability caveat (HT-weighted cross-fitted units) and report the 35-39% exceedance honestly.
2. (post-pilot) Re-scope the primary analysis to polarity, speech act and politeness-lost (separate denominators). Agent and certainty are exploratory (detector-vs-judge disagreement, ~41% of B0). Report the headline with and without them, primary = without (10.1% at T=100 is the pilot figure; recompute with CIs and on the restricted B0). Spurious-addition politeness errors reported separately from lost-cue errors.
3. Action analysis: report the ASK vs SHOW-TWO split explicitly; reframe as "show-two vs ask" and say ASK-ONE-CUE is rarely chosen. Sweep q in {0.5,0.7,0.9,1.0} and rho (incl. rho=1 differing from primary by forcing ask-only variant, i.e. an ASK-only policy and a SHOW-TWO-only policy as separate benchmarks). Headline must be stated conditional on q, with the break-even q at which P-K stops beating B5/B1.
4. Remove definitional leakage: refit S1 with NEG/POL/ACT lexicon features dropped (or computed on a disjoint lexicon) and report AUROC/frontier both ways; downgrade novelty claims marked [S] unless opened and verified; keep novelty "medium-to-low pending B6". Add per-writer CIs and add CIs plus the 600-tap extension to the frontier figure.
5. Benchmarks (Stage 1/2, rule written to PLAN.md before running): implement B6 (entropy/sampling-disagreement gated asking, closest published approach; cite only opened sources) with local models under blocking flock, add model-internal signals (token logprob entropy/margin on keyword-conditioned generation) for H2, and the external detector for H4 (API, concurrency <=3, keywords only). Add G1 guard comparison on the same units in AAC terms (silent reversals per 1,000, SLP-weighted, taps per 1,000). Add hw1/hw2 transfer only if time allows.
6. Human validation: measure/bound q via ANNOTATION_REQUEST.md (real alternative sentences, ~20 non-author annotators, no AAC participants). Update the request with the item key; do not send. Keep machine-only results labelled PROVISIONAL.
7. Pre-declared stop rule for round 3: if with H2/H4 signals and B6 the primary-scope gain at T=100 is still <= B5 + 1 pp (CI includes 0), conclude "modest, prior-driven; honest negative-leaning result" and stop; if signals beat B5 with CI excluding 0 on the primary scope, run the full test and finalise figures/writing.
Write the report section including where the method does NOT help (polarity/certainty AUROC CIs include 0.5; politeness below random at T=20).

### A2 (2026-11-02, ROUND 2; written BEFORE any round-2 outcome (primary-scope frontier, q sweep, no-lexicon fit, internal/external signal, B6) was computed. Round-1 outcomes were already seen, so items marked "post-pilot" are not blind.)
Items 1-4 (CPU) first, then Stage 1/2 (GPU/API). Everything here is PROVISIONAL (detector source labels, machine-arbitrated output labels, simulated q and rho).

**R2-1 Primary scope (post-pilot).** Dimensions polarity, speech act, politeness-LOST. Outcome = lost-cue reversal r only (mean over the 4 P0 models; per-model r for H2). Spurious additions s are reported separately for ALL dimensions (never in the primary outcome).
Agent and certainty are exploratory and use their own denominators. B0_prim = sum of weighted r over the 3 dims. Weights SLP mean (NEG 1.0, ACT 0.8, POL 0.5). Primary frontier = one action per message, 3 dimensions, T in {20,50,100,200,400,600} taps/1,000 (HT-weighted, same units, same folds as Stage 0).
**R2-2 Leakage.** S1 primary = features WITHOUT the three outcome-defining lexicon flags (NEG/POL/ACT hits; columns 3-5 of the S1 matrix); S1-full (with them) is reported as a comparison. Every later signal set adds to S1-noLex.
**R2-3 Action analysis.** Report share of ASK vs SHOW-TWO among acted messages (P-K), plus ASK-only (action set restricted to 2-tap ASK, rho_d) and SHOW-only (1-tap SHOW-TWO) versions of P-K and B5. q sweep {0.5, 0.7, 0.9, 1.0}, all in the primary scope. Break-even q: the smallest q on a 0.01 grid in [0.3,1] at which P-K minus B5 (point estimate) at T=100 is >= 0 and also the q at which P-K minus B1 >= 0; the paired-bootstrap CI of the difference is reported at the sweep points. The headline is stated conditional on q (no unmeasured q is called "the" result).
**R2-4 H3 restated.** Reported as "success under amended targets only" (alpha = 22%, 33%, 55% of B0_prim, i.e. the round-1 100/150/250 scaled to the primary scope; the original 5/10/20 stay infeasible). Floors: always-ask residual with rho<1; lambda=0 policy residual; both stated. B5 at equal realised risk uses a RANDOMISED ladder (act on each message independently with probability f on a 201-point grid, same granularity as P-K's 301-point lambda ladder), analytic. Mean prompts per message and the exceedance rate are reported; the cross-fitted HT-weighted units are not exchangeable so CRC is labelled "heuristic calibration, no guarantee".
**R2-5 Stage 1 internal signals (S3), local GPU, blocking flock, one server at a time; models qwen2.5-7b, llama3.1-8b, gemma3-4b (stored P0 labels exist).** The prompt is exactly P0 rendered with src/prompts.render on "Keywords: <kw>" (no context). Per unit and model:
 (a) greedy regeneration (T=0, max 96) with logprobs, top_logprobs=5: features = mean and min token logprob, first-token entropy (from the top-5), first-token margin (top1-top2), mean entropy over the first 3 tokens, n tokens; identical-text rate vs the stored output is reported. Outcome labels always come from the stored arbitrated labels (not regenerated text).
 (b) K = 8 samples at T = 1.0 (declared K=8, not 16, to bound compute; deviation from section 6 Stage 1(b)), labelled by L0 (src/layer0.py) for polarity (negated), speech act (non-statement), politeness (!= none); features per dimension = sample frequency of the cue value and binary entropy; message-level = entropy of the joint 3-label vector. This is also the B6 signal.
 (c) forced-choice probe, one call per dimension: "An AAC user typed these keywords: <kw>. Could the sentence they meant <contain a negation | be a question or a request | contain polite wording such as please or thank you>? Answer Yes or No." P(Yes) = softmax over the Yes/No first-token logprobs.
 P-I_m = logistic on S1-noLex + (a)+(b)+(c) for model m, outcome = that model's own r (per-model); P-K_m = S1-noLex on the same per-model outcome. H2 stays as pre-declared (delta AUROC >= 0.03 for polarity or speech act AND averted-at-T=50 paired CI of P-I minus P-K excludes 0; "internal beats external" needs >= 2 of 3 models).
**R2-6 Stage 2 external detector (S2).** gpt-6.1-sol, reasoning effort low, concurrency <= 3, temperature default, input = keywords ONLY (never source, outputs or labels); one call per keyword set returns 0-100 for each of five cues dropped. Features: the three primary probabilities (S2). P-X = S1-noLex + S2; P-ALL = S1-noLex + S2 + S3 (per local model). H4 = best P-* minus B6 at matched taps, paired CI.
**R2-7 B6 (closest published; Clarify When Necessary, OpenReview XgdNdoZ1Hc, opened/verified only as far as its abstract was seen in round 1; implemented as the "entropy-gated ask" idea, NOT a reproduction).** Per message and model: joint-label entropy H over the K=8 samples; gate = the top-fraction of messages by H until the tap budget T is met; the dimension asked = largest minority-value sample frequency among the 3 dims (unweighted: the published idea has no clinical weights); action = SHOW-TWO (1 tap). B6-w (weighted variant: dimension chosen by w_d x minority frequency) also reported. The pooled-outcome comparison uses the mean of the three local models' H (features), per-model comparison uses model m's own H.
**R2-8 G1 comparison (transfer only; no new generation).** G1 monitors chip-vs-output constraints, so with keyword-only inputs (no cue present) it has nothing to check: G1 alone averts 0 on these units (stated, not measured). The combination "ask (chip) then G1" uses the stored W-C strict-failure repair rate 52.5% [48.4, 56.7] (analysis/guard_baseline/report.md, G1) applied to the ASK residual: residual_ASK x (1 - 0.525); labelled TRANSFER estimate. AAC terms: silent reversals/1,000 (raw), SLP-weighted, taps/1,000, prompts per message.
**R2-9 STOP RULE (round 3).** Let g_best = best of {P-K-noLex, P-X, P-I (pooled mean over local models), P-ALL} relative reduction of B0_prim at T=100, and g_B5 the B5 value. If g_best - g_B5 <= 1.0 pp OR its paired cluster-bootstrap CI includes 0 -> conclusion "modest and prior-driven; honest negative-leaning result", stop. Otherwise continue to the full test (finalise figures and writing).
**R2-10 Annotation request.** Updated to measure q (does the offered alternative sentence cover the writer's meaning, and would the user pick it); items built from real model output and a real cue-flipped alternative (generated by the default model with the cue chip), not sent.

### A3 (2026-11-02, POST-PILOT; written after a 30-resample debugging run of the signals pipeline on qwen2.5-7b alone showed that P-I raised speech-act AUROC from about .73 to .82-.85. The stop-rule candidate set in R2-9 is NOT changed.)
Control added because part of an internal-signal gain could simply be knowing what the model committed to: **P-O** = S1-noLex + the three L0 labels (negated / non-statement / politeness != none) of the regenerated greedy sentence (the committed output, available at inference time, no source access);
**P-IO** = S1-noLex + S3 + those L0 labels. Reported alongside P-K/P-X/P-I/P-ALL with the same folds, paired CIs for P-I minus P-O and P-IO minus P-O. The claim "internal signals beyond the committed output" requires P-IO minus P-O (or P-I minus P-O) to exclude 0; the stop rule still uses the pre-declared set, but the writing must name P-O as the honest zero-cost comparator.

### A4 (2026-11-02, end of round 2)
Citation status after round 2: OPENED and verified = Angelopoulos et al., Conformal Risk Control (arXiv 2208.02814; authors, abstract). NOT opened (OpenReview blocked by a browser check; arXiv items only seen in search results) = Clarify When Necessary, Cai et al. 2205.03767, KWickChat, 2606.29054, 2607.27143, 2609.07395 and all other [S] items: they are "candidate related work, unverified" and must not be cited in a paper before being opened. B6 is therefore an entropy-gated asking baseline INSPIRED by the idea, not a reproduction. Novelty stays medium-to-low.
Deviations: K = 8 (not 16) samples; gemma3-4b Stage 1 NOT run (owner SIGSTOPped AAC GPU waiters, D-084; the queued job resumes automatically and signals can be re-run with `python src/frontier_value_of_cue_features.py gemma3-4b S2 ...` then `src/frontier_value_of_cue_signals.py 1000`); H2 evaluated on 2 of 3 local models.

### D-R2 Director decision after round 2 (2026-11-02): CONTINUE to round 3 (full test + final writing). Not a stop.
Stop rule R2-9 (pre-declared): P-ALL minus B5 = +8.9 pp [3.9, 13.4] > 1.0 pp, CI excludes 0 -> not a stop. Honest framing is mandatory: the gain is real but modest, mostly "ask when the committed output lacks the cue" (P-I minus P-O +2.5 [-2.8, 7.8]); polarity not helped; full five-dimension scope P-K 3.9% vs B5 4.0%; P-K vs B5 CI includes 0 at 100 taps. All AAC-unit numbers are conditional simulations until q is measured. No CRC guarantee language.
Round 3 instructions (labelled post-pilot; fix critic majors first):
1. Leakage: add a "strict no-lexicon" S1 (drop please, MOD, WH, "?" and CERT/never-type features that overlap outcome lexicons); report P-K/P-I/B5 frontiers and AUROCs under both S1 variants; headline uses the strict one if it differs.
2. Stronger P-O: build P-O from stored arbiter labels of the stored committed text (not regenerated L0 labels) as the primary P-O comparator; keep regenerated version as secondary. Claim "beyond committed output" only if P-I minus P-O excludes 0.
3. Supervised B6-feature baseline: same logistic learner on B6 features (entropy, minority frequency) with matched folds, plus B6 vs G1-after-ask comparison; report unsupervised B6 as inspired-by only.
4. Selection: nest model selection (choose the best policy inside folds) or report all policies with no best-of selection; bootstrap should refit the policy per resample at least for P-I/P-O/P-K on a reduced B. Report per-writer heterogeneity (P-K beats B5 for 7/20 writers) and polarity failure explicitly.
5. q and cost model: show frontiers over q in {0.3..1.0}, add a false-alarm cost (a prompt on a message needing none costs the tap plus a small acceptability penalty) and a mis-pick cost, and spurious-addition sensitivity; report both primary and full five-dimension scopes side by side.
6. Gemma3-4b: run Stage 1/signals if GPU lock is available (flock, blocking) so H2 is evaluated on 3 models; otherwise state 2-of-3 as a deviation. Report H2 as NOT met as declared.
7. Annotation: finalise ANNOTATION_REQUEST.md and key for q measurement (do not send); mark all AAC-unit results provisional.
8. Writing/figures: REPORT with headline = taps per error averted and weighted errors averted per 1,000 vs B5/B1/oracle/B6, a frontier diagram (averted vs taps, all policies, CIs), q-sensitivity panel, per-writer panel, and a "where it does not help" section; cite only verified sources (A4 list).

### A5 (2026-11-02 evening, ROUND 3; written BEFORE any round-3 outcome was computed. All round-1/2 outcomes were seen, so every item is post-pilot. PROVISIONAL: detector source labels, machine-arbitrated output labels, simulated q/rho.)
Script: src/frontier_value_of_cue_round3.py. Same units, folds, SLP weights, primary scope (polarity, speech act, politeness-lost, one action per message), pooled outcome = mean over the 4 P0 models, pooled features = mean over the available local models.
**R3-1 Strict S1.** S1-strict drops the columns NEG/POL/ACT hit flags, MOD, WH, "?", CERT, and "please" (columns 3-9 and 16 of the 21-column S1 matrix); keeps length, pronoun, stopword-share and person-pronoun features. S1-noLex (round 2) and S1-strict are both reported (frontiers, AUROCs, P-K/P-O/P-I/B5). Headline uses S1-strict for every learned policy (declared now, not conditional on the outcome).
**R3-2 P-O (primary comparator).** P-O = S1-strict + the STORED arbiter-labelled cue state of the stored committed text (columns polarity/speech_act/politeness of runs/elic1/scored.parquet, P0, mean over the pooled local models). Secondary: P-O-regen (round-2 L0 labels of the regenerated text). P-I = S1-strict + S3 (round-2 features); P-IO = S1-strict + S3 + stored labels. Claim "signals beyond the committed output" only if the paired CI of (P-I minus P-O-stored) at T=100 excludes 0 (also reported at T=50). Caveat declared: the outcome r is itself "cue present in source, absent from keywords, absent from stored output", so P-O-stored is close to a definitional comparator (it is "label the model output and ask when it lacks a cue the keywords might imply").
**R3-3 Supervised B6.** B6-sup = same logistic learner, same folds, on B6 features only (joint-label entropy jH and per-dimension minority frequency, entropy and frequency, no S1); B6-sup+S1 = S1-strict + those. Action = SHOW-TWO. Unsupervised B6 (entropy gate, rank by H) stays "inspired-by, not a reproduction". G1-after-ask comparison: ASK action with residual repaired by G1 (rho_g = rho + (1-rho) x 0.525, transfer estimate) for P-I and for the entropy-gated B6 (ask on the max-minority dimension), vs SHOW-TWO versions, all as AAC-unit columns.
**R3-4 Selection and refit.** No best-of selection: all policies are reported in every table; the round-2 stop rule is superseded by "report all". Refit bootstrap: B_refit = 200 joint writer x message cluster-bootstrap resamples; in each, P-K-strict, P-O-stored and P-I are refit end to end (weights = unit weight x resample counts, same 5x5 blocks and inner CV for C) and the frontier at T in {50,100,200} and differences vs B5 and P-I minus P-O are recomputed; CI = percentile. Reported next to the fixed-prediction CIs; if the refit CI is wider, the refit CI is the headline. Per-writer heterogeneity: per-writer P-K-strict vs B5 at the same pooled prompt rate (as round 2); polarity failure: AUROC and its CI and the share of polarity in the gain.
**R3-5 q and cost model.** q in {0.3,0.4,...,1.0}: T=100 relative gain for P-K-strict, P-O, P-I, B5, B1 with paired fixed-prediction CIs (300 resamples), and break-even q. False-alarm cost: every prompt on a message whose cue was NOT lost on the asked dimension (expected 1-y_d) costs a extra tap-equivalents, a in {0, 0.5, 1}. Mis-pick cost: with probability m in {0, 0.05, 0.10} the shown alternative is wrongly picked when the cue was not lost, adding a spurious cue of weight w_d. Policies are not re-tuned for the penalties (conservative for the policies); effective taps = taps + a x false alarms; net averted = gain - mis-pick loss; evaluated at nominal T=100 effective taps. Spurious-addition sensitivity: evaluate on outcome r + e x s with e in {0, 0.5, 1} (spurious additions treated as errors that SHOW-TWO/ASK can fix with the same efficacy times e), policies trained on r and B5 prior re-derived from the evaluated outcome. Scopes side by side: primary (3 dims) and full five-dimension lost-cue scope (P-K-strict, P-O, P-I, B5, B1), the latter exploratory.
**R3-6 Gemma.** Stage 1 for gemma3-4b is queued under blocking flock (SIGSTOPped by the owner for the D-15 Unity job, D-084). If its file is complete when round 3 finishes, signals are re-run on 3 models; otherwise H2 is on 2 of 3 models, recorded as a deviation. H2 is reported as NOT MET as declared (unchanged).
**R3-7 AAC units.** For every operating point: silent reversals per 1,000 (raw), SLP-weighted per 1,000, taps per 1,000, prompts per message share, taps per error averted. All labelled provisional, conditional on q = 0.9 unless a q sweep is shown. No CRC-guarantee language.
**R3-8 Citations.** Only Angelopoulos et al. (arXiv 2208.02814) is verified-opened; everything else candidate/unverified, not cited as support.

### A6 (end of round 3, 2026-11-02): status. Round 3 ran per A5 (outputs round3/). Deviation: gemma3-4b Stage 1 not run (GPU jobs SIGSTOPped by owner, D-084); H2 evaluated on 2 of 3 models and reported NOT MET as declared. "Beyond committed output" (P-I minus P-O) NOT demonstrated; P-K minus B5 not significant; P-I minus B5 significant. No best-of selection reported.

### D-R3 Director decision after round 3 of 3 (2026-11-02): STOP compute; hand off to writing with a narrowed claim. No round 4 (max rounds reached). All numbers PROVISIONAL.
Decision: the question is answered as far as machine-only evidence allows. Remaining compute would not change the headline; the remaining major issues are framing/reporting fixes plus one cheap CPU-only analysis, and human validation is deferred to ANNOTATION_REQUEST.md (orchestrator batches; nothing sent).

Claim to carry forward (strongest true claim): under strict S1 and simulated q = 0.9, a learned gate with model internals (P-I) averts about 13.8% of SLP-weighted silent reversals at T = 100 taps/1,000 (about 31 raw per 1,000; about 87% of weighted burden remains), 7.2 pp over the prior-only B5. This is a speech-act SHOW-TWO effect, conditional on simulated q. NOT claimed: beyond-committed-output signal (P-I minus P-O +2.4 [-3.4, 6.7], under-powered, "not demonstrated" is not "absent"), superiority over supervised entropy features (B6-sup, +1.9 [-3.0, 7.4]), polarity or politeness prompting, a general calibrated ask-or-assume policy, novelty over Clarify-When-Necessary-style entropy gating.

Writing-pass instructions (post-pilot, labelled; do not change any pre-declared rule or the stop-rule candidate set):
1. Headline table: use refit CIs as primary (report fixed-prediction CIs as secondary). State P-I beats B5 reliably only at T >= 100 (T = 50 refit [-0.9, 9.1] includes 0; T = 100 refit [1.1, 13.0] barely excludes 0).
2. Drop "lexical leakage" wording. Report strict S1 and no-lexicon/full S1 as co-primary, with the note that features such as '?', WH, MOD, 'please' are legitimate at deployment and strict S1 handicaps all learned policies equally.
3. Headline q <= rho_speech_act (.79), i.e. report q = 0.7 (P-I 10.7% of B0) beside q = 0.9, and show the full q sweep as a figure. Label q = 0.9 optimistic.
4. Per-model results (qwen, llama separately) are the faithful test; the pooled P-I/P-O blend is secondary and described as a hypothetical blend. Say plainly that the outcome averages 4 models while signals come from 2.
5. Report both scopes: primary 3-dim scope was chosen post-pilot (A2/A5); show five-dim scope (P-I 6.6% vs B5 4.0%, P-K below B5) in the same table as a robustness row, not a footnote.
6. Position honestly: the policy functions as a speech-act detector; polarity AUROC CIs include .5; absolute gain is modest. Frame the contribution as a benchmarked cost-aware evaluation framework (silent reversals per 1,000, SLP-weighted, taps per error averted, cost-model sweep incl. harsh cell where P-I 7.7% vs B5 1.5%) with a null result for beyond-output signal. Cite Clarify When Necessary and state B6-sup is the closest implementable prior; no claim of exhaustive AAC literature search.
7. Where it does not help: show polarity/politeness failure and ASK-ONE-CUE never chosen as a limitations figure.

Allowed final compute (CPU only, no GPU, no API): a lexicon-gated B5 baseline (apply B5 only to messages whose keywords lack the cue per the lexicon gate) on the same items, reported with refit and fixed CIs, plus its paired contrast to P-I and P-K. Pre-declare in an amendment before computing; report whatever results, including if it closes the P-I gap. If it does, the headline becomes "learned internals add nothing over a lexicon-gated prompt".

Human validation (provisional until done): machine labels and simulated q/rho are the main weaknesses; the annotation request (output-label check, measured q via chip restoration) stays queued for the orchestrator. Journal readiness depends on measured q replacing simulated q.

### A7 (2026-11-02, WRITING PASS; written BEFORE the lexicon-gated B5 outcome was computed; CPU only, the one compute step allowed by D-R3)
**B5-lex** = B5's chosen action (the best fixed prompt by prior; SHOW-TWO on speech act at q = 0.9) applied by a randomised ladder (fraction f in a 401-point grid) ONLY to messages whose keywords contain none of the speech-act lexicon cue (ACT lexicon hit), modal, WH word or "?" (columns 5, 6, 7, 8 of the S1 feature matrix; i.e. the keywords do not already signal a question/request). Same units, weights, primary scope, q = 0.9 and q = 0.7. Paired contrasts at T in {50, 100, 200} against B5, P-K (strict), P-O, P-I from the stored round-3 cross-fitted predictions (P_r3.npz), fixed-prediction cluster bootstrap (300 resamples, widest of writer/message/joint). B5-lex has no learned component, so a refit bootstrap equals the fixed one apart from the prior-based dimension choice (negligible; stated). Rule: if B5-lex minus P-I has a CI including 0 AND point estimate within 1 pp, the headline becomes "learned internals add nothing over a lexicon-gated prompt". Whatever the result is reported. Script src/frontier_value_of_cue_b5lex.py; output b5lex/.
