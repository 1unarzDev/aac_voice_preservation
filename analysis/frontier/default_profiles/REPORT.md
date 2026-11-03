# REPORT: Default-elicitation profiles and interventional estimands (frontier `default_profiles`)

Director's final report, 2026-11-02. Sources: `PLAN.md` (sections 1-4 and 8 written before outcomes; 9 and 10 are labelled post-pilot amendments), `round1.md`, `round2.md`, `round3.md`, `critique1-3.md`, `DEVIATIONS.md`, `summary.json`, `README.md`. All evidence is machine-only (stored outputs plus a local logprob probe): no human labels, no new generation, no J1 fallback. Nothing was sent for annotation.

**Verdict in one line: a measurement framework plus a null result. The proposed ask policy did not help detectably, the study's own interventions are not benchmarked on the same items, and the closest-published-method benchmark was not delivered.**

## 1. Question
Do LLM keyword-to-sentence expanders have a default reading (for example "no negation", "statement", "not polite") that differs from the human base rate when the keywords drop a meaning cue? If so:
1. What does that default cost in silent meaning reversals per 1,000 messages, weighted by SLP severity?
2. Can a cheap ask policy (a no-model-call keyword prior, or model confidence) spend a small ask budget better than random?
3. How do chip, plain word and G1 compare on the same items?

## 2. Pre-declared rules (and what was amended)
- **H1 (profile gap):** the calibration gap differs by dimension. **H2:** SLP weighting changes the dimension ranking. **H3:** assumption effect credited only if the placebo channel passes. **H4:** prior beats confidence by at least 25% fewer reversals at a 10% ask budget with CI excluding 0 (polarity); otherwise claim only parity, and "no policy helps" where nothing beats random.
- **Round-2 amendments (post-pilot, written before round-2 numbers):** the CV prior is refit in every bootstrap replicate; message-cluster bootstrap at B = 300; four named primary contrasts (P1 negation prior vs gated random, P2 negation prior vs confidence mean, P3 and P4 the same for politeness), Holm over 4; every other contrast exploratory (BH); TOST margins 5 / 10 / 25 per 1,000 (negation / politeness / speech act), wording "not distinguishable" unless met.
- **Deviations (see `DEVIATIONS.md`):** round 2 ran B = 1000 against the declared 300 without recording it (round 3 reports B = 300 as primary); the plan section 10 was appended after the 22-second round-3 run (it restates the director's earlier instructions, and no method was chosen after seeing outcomes); the valid-cell probe mean is a post-hoc comparator; H1's sign convention was inconsistent in the plan and was fixed in round 1; B = 300 BC intervals are noisy.

## 3. What was run
- 1,800 human keyword units (600 messages x 3 human keyword sets; strata random and enriched; HT-weighted); stored elic1 outputs for 4 generators (qwen2.5-7b, llama3.1-8b, gemma3-4b, a gpt-family model), 7,200 outputs.
- Local forced-choice logprob probe on 3 of 5 planned models (gemma3-4b, llama3.1-8b, qwen2.5-7b), under the GPU lock.
- Policies at a 10% ask budget (100 asks per 1,000 messages), all on the same units: keyword prior (CV, refit in the bootstrap), gated random (primary baseline), ungated random, confidence (probe mean, valid-cell mean, per-model), an entropy stand-in (NOT CLAM), shortest-keywords-first. Interventions: chip, plain word, every-message prompting, G1.
- Exposure = cue in the source but dropped from the keywords (model-independent upper bound). Model-visible reversal = exposure and the model output actually lost the cue.
- "Reversals per 1,000" are rates over these sampled units (HT-weighted). They are not deployment rates.

## 4. Results (95% CI; message-cluster percentile bootstrap, B = 300)

### 4.1 What always-commit costs (measured)
| dimension | model-visible reversals per 1,000 | exposure per 1,000 | label status |
|---|---|---|---|
| negation | 23.9 [16.0, 32.5] | 24.4 | detector validated elsewhere |
| politeness | 49.4 [38.5, 63.8] | 56.4 | **provisional** (detector proxy) |
| question/request | 161.9 [134.1, 187.8] | 277.5 | **provisional** (detector proxy) |

SLP weights (2 raters, descriptive): negation 1.0, question/request 0.8, politeness 0.5. Weighting does not change the dimension ranking (H2 not met; Kendall tau = 1; with one rater's weights politeness falls below negation, so that order is within rater disagreement). Summing unlike events is descriptive.

### 4.2 Ask policies at 10% asks (null)
Primary contrasts, Holm over 4:

| contrast | point diff per 1,000 | percentile CI | bootstrap mean | Holm p |
|---|---|---|---|---|
| P1 negation: prior - gated random | -4.2 | [-8.5, 2.2] | -1.5 | 1.00 |
| P2 negation: prior - confidence mean | -0.4 | [-4.4, 8.0] | +2.3 | 1.00 |
| P3 politeness: prior - gated random | -5.6 | [-16.4, 2.7] | -4.6 | 1.00 |
| P4 politeness: prior - confidence mean | -6.7 | [-18.4, 4.2] | -5.3 | 1.00 |

**0 of 4 significant. H4 not met.** Negation levels at 10% asks: always-commit 23.9, gated random 21.3 [14.2, 28.9], prior 17.1 [10.0, 28.8], confidence mean 17.4 [11.4, 24.4], entropy stand-in 19.3. The minimum detectable effect for the negation primary contrast is 8.5 per 1,000 (36% of the always-commit rate), so this is a null of limited power, not equivalence (no TOST margin met). Point estimates are off-centre (the full-sample prior looks better than its bootstrap mean), so the point estimate and the BC interval ([-15.0, -0.5] for P1) are not cited as support. The only suggestive signal (probe-mean confidence vs gated random on negation, -3.8 [-7.7, -0.8], BH q = 0.119) is exploratory and circular (events defined by the same models that supply the probes).

### 4.3 Same-items interventions (conditional, arithmetic on a transported rate)
Reversals left = always-commit minus rho x (ranked reduction), with rho (cue-honouring rate) transported from hw1 discriminating pairs and an assumption that an ask supplies the cue. rho is resampled in the bootstrap; hw1-to-elicitation transport mismatch and user non-response are NOT covered.

| strategy | taps per 1,000 | negation reversals per 1,000 | politeness |
|---|---|---|---|
| always-commit (measured) | 0 | 23.9 [16.0, 32.5] | 49.4 [38.5, 63.8] |
| chip on 10%, prior-ranked | 100 | 17.1 [10.1, 28.9] | 39.5 [28.1, 54.1] |
| chip on 10%, gated random | 100 | 21.3 [14.2, 28.9] | 44.4 [34.6, 57.3] |
| plain word on 10%, prior-ranked | 100 | 17.1 [10.1, 28.9] | 39.2 [27.9, 54.0] |
| chip on every message | 1000 | 0.1 [0.0, 0.3] | 5.8 [4.3, 7.8] |
| plain word on every message | 1000 | 0.3 [0.2, 0.5] | 4.8 [3.4, 6.5] |

Question/request (provisional), every message: chip 34.4 [25.7, 47.3], plain word 21.1 [15.1, 30.1] (rho 0.79 and 0.87; 52 of 417 exposure units are unreachable by any gated policy). Chip and plain word are interchangeable in reversal terms at these rho values (no test). In AAC terms: prompting every message would, if every prompt were answered, remove almost all negation reversals at the cost of 1,000 taps per 1,000 messages; spending 100 taps at any tested ranking changes little beyond the null above.

### 4.4 G1: not benchmarked
The round-2 claim "G1 is harmful for politeness (measured)" was a construction artefact (bare keywords give an empty spec, so `check()` flags polite outputs by design). It is **withdrawn**. A spec-based check on stored outputs (oracle-intent spec) shows detection shares of 87% (negation), 98% (politeness) and 99% (question/request), but this is recall only, `check()` also flags 41% of outputs containing none of the three reversals, and repair was not run. No G1 rate appears in any same-items table.

### 4.5 Probe calibration (H1, reframed)
Forced-choice probe beliefs minus human base rate, among units whose keywords lack the cue: negation +35 to +46 pp (base rate 2.7%), Brier skill score below 0 for every probe model on negation and politeness (for example gemma3-4b negation -10.2 [-15.9, -7.1]). This is acquiescence-confounded and **not** an AAC profile gap. The round-1 "polarity +2.5 pp overconfidence" claim stays retracted (greedy-output rate is not a calibration measure). Only 4 of 9 model x dimension cells have a valid confidence signal (AUROC lower CI above 0.5); no politeness cell does.

### 4.6 Acceptability
Descriptive only and not comparable across arms (selected items, 2 SLP raters, 20 to 40 rater-items): chip 13/20, word 10/20, guard_repair 13/40, guard_original 0/20 (selected judge-failed items). No ranking implied.

## 5. Critic issues and resolution
| round | issue | resolution |
|---|---|---|
| 1 | greedy-vs-posterior H1, ungated random, misreported contrast | fixed in round 2 (posterior probe, gated random, named contrasts) |
| 2 (fatal) | "G1 harmful (measured)" is by construction | withdrawn; spec-check as recall only; hypothetical worst case separated and labelled |
| 2 | chip/word rows presented as outcomes | relabelled "transported rho"; rho resampled in bootstrap; every-message rows called conditional |
| 2 | prior estimate off-centre; B undeclared | B = 300 primary, percentile + BC + bootstrap mean shown; logged in DEVIATIONS |
| 2 | invalid probe comparators, circularity, post hoc qwen highlight | valid-cell mean flagged post hoc; no model singled out; circularity stated |
| 2 | acceptability confounded | caption states not comparable |
| 3 (no fatal) | CLAM benchmark unmet | **unresolved**; stated as unmet, entropy is a stand-in |
| 3 | intervention rows are arithmetic; G1 not same-items | **unresolved**; labelled conditional everywhere |
| 3 | spec check leaks (oracle intent), recall only | labelled upper-bound detection, not G1 performance |
| 3 | MDE is post hoc power; exploratory hits circular | wording limited to "cannot detect"; kept out of headline |
| 3 | provisional labels carry headline; plan section 10 written after run | labels tagged; lead with negation; disclosure kept |

Final critic verdict (round 3): valid, no fatal issue; majors are overclaim risks and the unmet benchmark.

## 6. Strongest TRUE claim
On 1,800 human keyword units, always-commit leaves about 24 silent negation reversals per 1,000 messages (95% CI 16.0 to 32.5; politeness 49 and question/request 162 are provisional on detector-proxy labels). No tested ask policy (keyword prior, model confidence, entropy stand-in, shortest-first) is distinguishable from gated random at a 10% ask budget after Holm correction (0 of 4 primary contrasts; negation minimum detectable effect 8.5 per 1,000, so this is a null of limited power, not equivalence). Probe-model beliefs are poorly calibrated against human base rates (Brier skill score below 0 on negation and politeness).

What we do **not** claim: that the prior beats confidence or random; that chip or plain word reduces reversals on these units (transported, conditional); anything about G1 versus chip or word; parity or superiority to CLAM or other published clarification methods; any acceptability ranking; any per-model finding.

## 7. Novelty and closest prior work
- Cai et al., NAACL 2022 (context-aware abbreviation expansion for AAC): nearest AAC work; shows candidates to the user, with no meaning-reversal pricing. Chen et al., ACL 2023 ("Say What You Mean!"): documents negation dropping in keyword-to-sentence generation (cited). Kuhn et al. (CLAM) and 2025 ask-when-needed and clarification papers (EMNLP 2025, NAACL Findings 2025; seen as search snippets only, not opened): the closest ask-policy methods, **not implemented here**. Wang and Suresh (arXiv 2606.00333): defaults as a measured object in legal prompts, without a human base rate or cost. Judge-error correction and PPI literature motivated, but were not run (S3 out of scope).
- Searches (2026-11-02) found no AAC work that prices silent meaning reversals per 1,000 messages against human keyword base rates. Novelty is therefore the measurement framework (exposure vs model-visible reversal, SLP weighting, ask budgets and taps, gated-random baseline, no-model-call prior), not the ask policy, which is a null.

## 8. Limitations
- Closest-published-method benchmark unmet (CLAM-style needs about 10,800 local calls; not run because of the owner's GPU pause note).
- Low power: 76 negation exposure units; MDE about a third of the baseline rate.
- Chip, plain word and every-message rows assume asking supplies the cue and use rho from other units; no user-response model; no study of people (no IRB).
- G1 has no same-items measure; spec check is oracle-intent recall only.
- Speech-act and politeness labels are detector proxies; the headline mixes one validated and two provisional dimensions.
- Probe models 3 of 5; verbal-confidence arm below its coverage floor and unused; human keyword sets only; probe is acquiescence-confounded.
- Event definition and probes share the same models (circularity for confidence policies); rates are not deployment rates; SLP weights come from 2 raters.

## 9. Human annotation request (drafted, NOT sent)
`ANNOTATION_REQUEST.md`: 223 source messages (120 speech-act exposure, 43 politeness exposure, 60 controls); four questions (speech act, politeness, keywords already show question/request, keywords already show politeness); about 20 adult non-author annotators, 2 ratings per item, about 8 minutes each; no AAC users, no SLPs, no IRB. Items and key are built (`annotation/frontier_default_profiles_items.json`, `annotation/frontier_default_profiles_key.csv`). It feeds a re-run of `src/frontier_default_profiles_r3.py` with human labels and removes the "provisional" tag from speech act and politeness.

## 10. Recommended use
**Primary: CALE-AI lift by Nov 16, as a short measurement-and-null contribution, led by negation.** Content to lift: the measured always-commit cost (24 per 1,000 negation, 95% CI 16 to 32), the framework (exposure vs model-visible, ask budget and taps, gated-random baseline), the pre-declared null on ask policies with MDE stated, the withdrawn G1 claim as a methods caution, and the poor probe calibration. Speech act and politeness only with the "provisional" tag unless the annotation batch returns first. Do not put chip or plain-word reductions in the abstract; if shown, label as conditional on cue-honouring.
**Journal: not yet.** It becomes viable only after (i) the annotation batch returns, (ii) a CLAM-style comparator is run, (iii) chip, plain word and G1 are measured with regeneration on the same elicitation units, and (iv) a larger negation sample (the MDE is too large). **New standalone paper: no. Drop: no**, because the framework and the null are reportable, but the "ask policy helps" story should be dropped.

## 11. Files
`round1.md`, `round2.md`, `round3.md` (tables), `summary.json`, `claims.json`, `contrasts_r3.csv`, `policy_budgets_r3.csv`, `intervention_same_items_r3.csv`, `mde_r3.csv`, `h1_belief_scale_r3.csv`, `g1_spec_check.*`, `rho_draws.csv`, `fig_reversals_vs_asks_r3.png/.pdf`, `fig_primary_contrasts_r3.png`, `fig_h1_belief_r3.png`, `ANNOTATION_REQUEST.md`, `DEVIATIONS.md`. Scripts: `src/frontier_default_profiles_*.py`.
