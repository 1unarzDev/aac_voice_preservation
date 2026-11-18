# REPORT: Whole-message fidelity and unrequested content (frontier whole_message)

Status: PROVISIONAL, machine-only. No human has rated any treated output. R-WM-1 is built and not sent. Written 2026-11-02 by the director from PLAN.md, round1.md, round2.md, summary.json, round2_summary.json, critique1.md and critique2.md. Every number below is copied from those files, or recomputed from `r2_outputs.csv` where marked.

## 1. Question
Part 18 found that writers accepted 1 of 200 outputs as-is. The critical-dimension judge agreed with writers at kappa .24, because it labels one dimension while the writer judges the whole message. Can a whole-message fidelity score (a) predict writer rejection better than critical-only checking and better than trivial baselines, and (b) can a prompt that suppresses unrequested content improve AAC outcomes?

## 2. Pre-declared rules (PLAN.md, frozen before outcomes)
- M1-free metric counts as validated only if its holdout AUROC (writers P11-20) is at least .75 and its paired delta CI excludes 0 against the comparator.
- Round 2 added a stricter rule: the delta against the best trivial baseline must have a CI excluding 0, independent judges must reach Spearman of .50 or more, and the two-candidate arm must beat an equal-budget baseline. Failing these means no round 3.
- Bootstrap was clustered by writer or family (B=5,000, seed 20261102). Blind arbiter for critical labels, with no J1-fallback.
- Deviations were logged in PLAN.md. The graded-score primary and the post hoc match threshold of .6 are labelled post hoc.

## 3. What was run
- Round 1: M0, M1-ref, M1-free, M2 and a length ratio scored on the 195 usable Part 18 items and 50 SLP cards. A reduced API-only generation slice used terra, 108 inputs and arms A0 to A3.
- Round 2, validity: baselines T1-T6, a graded critical comparator, and two independent-family local judges (Qwen2.5-14B, Mistral-Nemo-12B).
- Round 2, generation: 144 inputs (36 families, 16 writers, chip1 and bare). Generators were terra, luna and llama3.1-8b. Arms were A0 (plain), A1 (preservation), A2 (minimal expansion) and A6 (second reading). Policy baselines were always-commit, always-ask, random-ask, flag-ask, G1-sim and a SelfCheckGPT-style detector.

## 4. Results

### 4.1 Metric validity (AUROC for writer rejection, chip1, n=97, 59 rejected)
| score | AUROC [CI] |
|---|---|
| critical-only binary (M0) | .53 [.51,.57] |
| critical-only graded (Qwen14B / Nemo12B) | .45 [.31,.61] / .55 [.44,.65] |
| word count (best trivial) | .72 [.61,.83] |
| M1-free (gpt-6.1-sol) | .77 [.69,.84] (holdout .82 [.71,.91]) |
| independent judges (Qwen14B / Nemo12B) | .76 [.66,.85] / .72 [.58,.84] |
| M1-ref (upper bound, sees the writer's sentence) | .88 [.84,.93] |

Paired deltas for M1-free on chip1:
- Against word count: +.04 [-.07,+.16]. This fails the rule.
- Against graded critical-only: +.31 [+.13,+.49] (Qwen) and +.22 [+.11,+.33] (Nemo).
- Against M0: +.23 [+.15,+.31].

Round 1 called M1-free "validated". That was against a strawman. On bare input, and over all 200 items, M1-free is no better than the trivial or critical baselines. Spearman with the independent judges is Qwen .48 and Nemo .29, so the .50 criterion is missed (Qwen by .02 on SC; the critic notes Qwen UC reaches .54, so the miss depends on which score is read). The holdout point estimate of .82 meets the .75 threshold, but its CI lower bound of .71 does not, which was recorded as a miss.

### 4.2 Why writers reject outputs that keep the commitment
- 55 of 93 outputs that kept the critical commitment (59%) were rejected.
- Flagged unrequested content: rejection 82%. Not flagged: 43%. When the output was also not flagged and the sentence frame was unchanged, rejection was 15% (5/34). That last conditioning uses M1-ref, so it is partly circular.
- Reading: rejection is mostly compression loss (detail that no keyword carries), and added content is a strong marker of it.

### 4.3 Prompt-side effect (A2 minimal-expansion vs A0 plain, chip1, pooled over 3 generators)
| quantity per 1,000 messages | change [CI] | caveat |
|---|---|---|
| flagged unrequested content | -287 [-384,-199] | defined by the gpt judge only (see 4.4) |
| silent reversals | -37 [-69,-9] | about 11 events; within A0 run-to-run noise (see 4.4) |
| SLP-weighted harm (points) | -230 [-307,-156] | driven by the UC flag |
| fragments | +9 [0,+23] | |
| composite failure | -278 [-375,-185] | |
| extra taps | 0 | by construction |
| match to the writer's sentence (terra only) | +.031 [+.008,+.056] on a scale capped at .6 | post hoc, under 0.15 of a rating point |
| acceptability to people | pending R-WM-1 | |

A1 (preservation) is less robust than A2. Pooled A1 - A0 fragments are +42 per 1,000 on chip1 and +148 on bare. Llama is nearly inert under A1 (UC .431 to .389) and moves only under A2 (.167). On bare input the critical commitment is kept in about 38% of outputs in every arm (guessing). The prompt gains there concern added content and say nothing about getting the message right.

### 4.4 Critic issues and their resolution
1. UC effect rests on a same-vendor judge (critic major 1). I recomputed the chip1 UC rate from `r2_outputs.csv` (d0, A0 to A2). The numbers below are recomputed here, not taken from the pre-existing round files.

| generator | gpt judge | Qwen14B | Nemo12B |
|---|---|---|---|
| terra | .347 to .056 | .111 to .056 | .778 to .611 |
| luna | .361 to .056 | .139 to .042 | .764 to .597 |
| llama3.1-8b | .431 to .167 | .208 to .111 | .778 to .681 |

All three judges move in the same direction for every generator. The size of the effect is judge-dependent (the gpt gap is about 29 to 31 pp, Nemo about 10 to 17 pp, Qwen about 6 to 10 pp). **The -287 per 1,000 figure is therefore the gpt-judged rate. It must be quoted as such, and the direction, not the magnitude, is the robust finding.**
2. The reversal gain is inside endpoint noise (critic major 2). Fresh terra A0 critical-commitment retention is .903 against .986 in the stored A0 run on the same inputs. That 8 pp gap is as large as the claimed A2 gain (+7.4 pp pooled). Against the stored A0, terra A2 (.917) shows no gain. The reversal claim is **downgraded to "not distinguishable from run-to-run noise"** and is dropped from the headline.
3. The independent-judge criterion was read post hoc (major 3). Both readings are stated in 4.1. The stop rule stands because criterion (i) fails regardless.
4. Novelty (major 4). Prior work was opened, see section 6.
5. The match endpoint is weak (major 5). It is reported only as "flat". The +.031 figure is not presented as an improvement.
6. Leave-one-writer-out was not run (major 6). The chip1 CIs are probably too narrow. The conclusion that M1-free does not beat length is unaffected, since the point gap is only +.04.
7. A6 UC is NaN for 126 of 144 rows and is filled with 0 in the composite. A6 and the composite are therefore understated, and A6 is used only in the policy tables. Luna was run at d0 only, with default decoding. Bare reversal and harm columns reflect the guess rate and are excluded from the AAC claims.

### 4.5 Baselines and policies (terra, 72 inputs per channel)
- Always-commit with A2 gives match .778 [.667,.889] on chip1. Always-ask with a second reading gives .819 [.708,.917] at 1,000 taps per 1,000. An equal-budget resample gives .792.
- At a matched ask rate (56 taps per 1,000), random-ask gives .780 and every flag gives .778. At 25% and 50% ask rates the SelfCheck-style and length flags do not beat random-ask.
- Two-candidate output: best-of-two is +4.2 pp [0,+9.7] over the single A2 output and +2.8 pp [-2.8,+8.3] over an equal-budget second sample. It fails the gate.
- G1-sim (a perfect-monitor upper bound; the real G1 was not run): terra chip1 reversals fall from 14 to 0 per 1,000 and UC is unchanged. It cannot touch unrequested content, and it cannot help on bare.
- SelfCheck-style sampling consistency has AUROC .58 for the UC flag, against .79 for word count.
- Not run: SHARS-style detect-then-resample, A3+, A4 and A5.

## 5. Strongest TRUE claims
1. **Keeping the critical commitment does not predict writer rejection.** The graded critical-only AUROC is .45 to .55 on chip1, and 59% of commitment-keeping outputs were still rejected. This reproduces with two independent judge families.
2. **A reference-free whole-message judge adds no demonstrable value over output length.** M1-free is .77 [.69,.84] against word count .72 [.61,.83], with a paired delta of +.04 [-.07,+.16]. Detectors also do not beat random-ask at matched ask rates.
3. Minimal-expansion and preservation prompts reduce judge-flagged unrequested content under every generator and every judge, at no cost in taps. Whether that helps people is unknown until R-WM-1 returns.

The metric is a null result. The prompt effect is judge-defined and not new. No "journal-ready AAC improvement" claim is supported by this frontier today.

## 6. Novelty and closest prior work
Opened and verified this session (abstract pages):
- Cai, Venugopalan, Tomanek, Narayanan, Morris, Brenner. "Context-Aware Abbreviation Expansion Using Large Language Models", NAACL 2022, arXiv:2205.03767. It expands abbreviations into several full-phrase options for AAC. Offering several candidates is therefore not novel, and the two-candidate arm is not an AAC contribution.
- Choudhury, Kumar, Martin. "Evaluating Human-LLM Representation Alignment: A Case Study on Affective Sentence Generation for AAC", arXiv:2503.11881. It generates sentences from keywords plus an emotion cue for AAC and evaluates them with human judgment. It is the closest keyword-to-sentence AAC evaluation work, and it concerns the cue representation, not unrequested content.

Not opened here (cited elsewhere in the repo; re-verify before citation): Chen et al. ACL 2023 on positivity bias in keyword-to-sentence generation; KWickChat and three-candidate systems; Ji et al., ACM Computing Surveys 2023, for the intrinsic and extrinsic hallucination taxonomy; SelfCheckGPT.

Defensible novelty is limited to two points. The first is the empirical dissociation: critical-commitment retention, which is what the study's guard checks, does not predict whole-message rejection in AAC keyword expansion. The second is the negative result that an LLM whole-message score does not beat length. I found no prior work that tests either point, but the search was shallow (abstract level and snippets), so this is not a comprehensive novelty claim.

## 7. Limitations
- Machine-only. The labels are the Part 18 writers' rejections, so they come from a small writer pool. The generation sample is 36 families and 16 writers, and many cells have fewer than 10 events.
- The same vendor family generates (terra, luna) and judges (sol). The local judges are uncalibrated (Qwen flags 7%, Nemo 65%, gpt 21%).
- Terra A0 is unstable between runs (CK .986 against .903), so effects under about 8 pp on CK cannot be trusted.
- The M1-ref match score is capped at .6 and covers terra only.
- Luna was run at d0 only. The real G1 monitor was not run.
- No leave-one-writer-out analysis. No human validation. No AAC-user study, and no IRB claim.

## 8. Recommended use
- **Lift into the CALE-AI paper by Nov 16, as a short and honest "limits of critical-only guarding" paragraph or figure.** It should carry two points: (a) the AUROC of critical-only against writer rejection (.45 to .55), and (b) the finding that M1-free does not beat length. It should state that unrequested-content reductions are gpt-judged. Do not include the reversal gain or the -287 figure without the "gpt-judged" label.
- **Journal:** not as a standalone paper in its present form. It becomes a section of the journal paper only if R-WM-1 (120 items, about 20 annotators, about 10 minutes each) returns showing that A2 raises judged acceptability and that the UC flag tracks human "added" calls. If R-WM-1 shows no acceptability gain, report it as a null.
- **New paper:** no. The metric failed, and the prompt is not new.
- **Drop:** drop the metric and the two-candidate arm as contributions.
- **Next steps, in order:** send R-WM-1 in the orchestrator's batch. Run leave-one-writer-out for M1-free and word count. Open Chen 2023, KWickChat and SelfCheckGPT before any novelty sentence.

## 9. Files
Plan: `analysis/frontier/whole_message/PLAN.md`. Results: `round1.md`, `round2.md`, `summary.json`, `round2_summary.json`, `r2_*.csv`. Critiques: `critique1.md`, `critique2.md`. Figures: `figs/fig1_metric_vs_baselines.png`, `fig2_uc_by_arm.png`, `fig3_intent_match.png`. Annotation: `ANNOTATION_REQUEST.md`, `annotation/frontier_whole_message_{items.json,key.csv,assignment.csv}`.

## 10. Follow-up F1 (2026-11-03, POST-PILOT, CPU only; added after the original report, which is unchanged above)
Source: SYNTHESIS.md section 5 item 5. Rule pre-declared in PLAN.md before the run. Details: `followup.md`, `followup_lowo.csv`, `followup_summary.json`.
- Leave-one-writer-out, chip1 (n = 97, 20 writers): M1-free AUROC .766 (LOWO .751 to .784), word count .724 (LOWO .705 to .757), delta +.042 (LOWO +.015 to +.068; every dropped writer leaves it positive). Delete-one writer jackknife 95% CI of the delta [-.076, +.159]. All200 (n = 195): .766 vs .704, delta +.063, LOWO +.042 to +.083, jackknife CI [-.035, +.161].
- Writer-stratified (within-writer pairs only) AUROC: M1-free .744 vs word count .641 (chip1, 78 pairs); .779 vs .670 (all200, 315 pairs).
- Declared verdict: PARITY. "M1-free beats word count" is NOT supported because the jackknife CI includes 0. The .75 threshold is met in every LOWO fit, but only by .001 at the minimum.
- Effect on the frontier verdict: none. The metric stays a null result. The wording in sections 5 (claim 2) and 8 can read "at parity with length, point estimate +.04 to +.06 in favour of M1-free, CI includes 0, no single writer drives it". The limitation "no leave-one-writer-out analysis" (section 7) is closed. Human validation (R-WM-1) is still absent.

## 9. Human labels (Stage 5, Part 23, R-WM-1; added 2026-11-17)
Full tables and rules: `human.md`; script `src/frontier_stage5_p23_whole_message.py`. 13 annotators, 360/360 ratings, 108 outputs (36 inputs x A0/A1/A2, terra, chip1) + 12 verbatim copies, 3 raters each; family-cluster CIs over 36 inputs (wide). Machine results above are unchanged; this section replaces "Human validation (R-WM-1) is still absent".
- **Prompt effect on people.** A2 minus A0 on the same inputs: human-seen added content -16.7 pp [-33.3, 0.0] (the gpt flag moves -27.8 pp); acceptable (Q3 yes or small edit) 0.0 pp [-13.9, +16.7]; Q1 = intended version +16.7 pp [0.0, +33.3]. A1 minus A0: added -13.9 [-30.6, +2.8], acceptable -2.8 [-13.9, +8.3]. Acceptability is flat: 77.8% / 75.0% / 77.8% for A0 / A1 / A2.
- **Flag validity.** gpt UC flag vs the 3-rater "added content" majority: kappa .23 [.07, .39], sensitivity .31, specificity .94, AUROC .62 [.54, .71]. Humans call 67% of A0 outputs "added", the flag 36%.
- **Metric validity vs human rejection (25 of 108).** Critical-only flag AUROC .45 [.38, .50]; gpt UC .65 [.53, .80]; reference-free score .65 [.52, .79]; length ratio .81 [.67, .91]; writer-sentence score .89 [.80, .96]. Length minus reference-free +.16 [-.00, +.31]: parity-or-better for length, as in the machine analysis.
- **Verbatim copies.** 0/12 "adds something" and 0/12 "complete sentence" (Wilson 0 to 24%): the flag is right that nothing is added; the copies are fragments.
- **Verdict.** The dissociation is confirmed with human labels (critical-only fidelity does not predict rejection). The prompt claim narrows: the preservation and minimal-expansion prompts reduce unrequested content people see (borderline, about half the flagged amount) and do not change acceptability; "helps people accept" is not supported.
- **Where it does not help.** 36 inputs, one generator, greedy; raters are third parties who accepted 77% while Part 18 writers accepted 1 of 200 as-is; Q2 agreement is moderate (kappa .44); the critical-reversal cell has 9 items.
