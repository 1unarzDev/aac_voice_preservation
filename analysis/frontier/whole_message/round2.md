# Whole-message fidelity and unrequested content: round 2 results (PROVISIONAL, machine-only)

Run 2026-11-02. Plan and freeze record: `PLAN.md` ("ROUND 2 FREEZE RECORD" written before any round-2 outcome; "Round 2 deviation log" appended after outcomes were seen). Scripts: `src/frontier_whole_message_r2_{gen,assemble,local,validity,analyze,figs,annot_items}.py`, `src/frontier_whole_message_r2_gpu.sh`. Everything here is judged by LLMs (gpt-6.1-sol; local Qwen2.5-14B and Mistral-Nemo-12B as independent-family judges) and the existing J1/J2 critical judge with a blind arbiter (output text only). **No human has checked any treated output** (R-WM-1 is built, not sent). Not validation by AAC users; no IRB claim.

## Verdict (stop rule applies: no round 3)
1. **The reference-free whole-message score does not beat a trivial length baseline.** On chip1 (97 outputs, 59 rejected by writers): M1-free AUROC .77 [.69,.84] vs output word count .72 [.61,.83]; paired delta +.04 [-.07,+.16], CI includes 0. On the holdout half (P11-20) M1-free is .82 [.71,.91] vs word count .72 [.52,.89], delta +.11 [-.05,+.28]. Round-1 "validated" was against a strawman. The declared pass rule needed (i) a CI excluding 0 against the best trivial baseline: **it fails**. The only trivial model M1-free clearly beats is the cross-validated length+lexical logistic (+.12 [+.01,+.24]), which is worse than word count alone.
2. **Insufficiency of critical-only checking is confirmed with a graded comparator.** The graded critical-only score (Qwen14B option probability) has AUROC .45 [.31,.61] on chip1 (Nemo12B .55 [.44,.65]); the binary round-1 M0 was .53. M1-free beats both graded comparators (+.31 [+.13,+.49] and +.22 [+.11,+.33]). So "keeps the commitment" does not predict writer rejection; "is longer or more elaborate" predicts it about as well as any whole-message judge.
3. **The independent-family judges reproduce the ranking but not tightly.** Qwen14B whole-message score AUROC .76 [.66,.85] on chip1 (point above word count .72, delta vs word count +.04 [-.06,+.13]); Nemo12B .72 [.58,.84]. Spearman with gpt M1-free graded score on chip1: Qwen .48, Nemo .29 (all-200: .53, .25). Declared criterion (iii) needed >= .50 on the claim subset: **Qwen misses by .02, Nemo fails**. The local UC flags are uncalibrated (Qwen flags 7%, Nemo 65%, gpt 21% of outputs), so only their ranking is used.
4. **Holdout threshold.** The declared rule asked for holdout AUROC >= .75; the point estimate (.82) meets it, the CI lower bound (.71) does not. As directed, this is recorded as a miss and the threshold is not re-declared.
5. **Prompt-side result (3 generators, 36 families, chip1 and bare): minimal-expansion removes flagged unrequested content, with no loss of the critical commitment and no gain in intent match.** Pooled over generators, A2 (minimal expansion) vs A0 (plain prompt), chip1: flagged unrequested content -287 per 1,000 messages [-384,-199]; silent reversals -37 per 1,000 [-69,-9]; SLP-weighted harm -230 weight-points per 1,000 [-307,-156]; match to the writer's sentence (M1-ref score, max .6; terra only, the one generator with full M1-ref coverage) +.031 [+.008,+.056] chip1 and +.022 [-.014,+.058] bare, i.e. at most 0.15 of one rating point. This is judge-defined. It is not new (A2 is minimal-expansion prompting; round 1 already showed P1 does the same for terra), and with llama3.1-8b A2 beats P1 clearly (see below), which reverses the round-1 reading "A2 is no better than P1" for that model.
6. **Two-candidate output (the "offer an alternative" arm) does not pass.** Declared match criterion (M1-ref >= .8) is degenerate (0 matches in every arm, because M1-ref never scores above .6). Post hoc match (>= .6): chip1 best-of-two +4.2 pp [0,+9.7] over the single A2 output and only +2.8 pp [-2.8,+8.3] over an equal-budget second sample; bare +11.1 pp [+2.8,+20.8] and +5.6 pp [-5.6,+16.7]. The second distinct reading matches the writer in only 17% (chip1) and 11% (bare) of cases. Round 3 gate: **fails** (needs a CI excluding 0 over the equal-budget baseline).
7. **Go/no-go for round 3: NO-GO.** Metric fails (i); two-candidate fails the equal-budget comparison. What survives: the critical-retention-vs-rejection finding, the prompt-side UC/reversal effect (judge-defined), and an AAC-terms table. R-WM-1 is the only route to claim that removing unrequested content helps people.

## What was done
- R2-A metric validity on the 195 Part 18 items (writer-cluster bootstrap B=5,000, seed 20261102): trivial baselines T1-T6 (word count, length ratio, lexical F1, novel lemmas, edit distance to the keywords, cross-validated length+lexical logistic grouped by writer), graded critical comparator M0g, two independent-family judges (single-token logprob readout of UC and a 1-5 score), M1-ref as an upper bound only. 4,444 local queries per model, 0 failures. Files `r2_validity_auroc.csv`, `r2_validity_paired.csv`, `r2_validity_features.csv`, `r2_validity_summary.json`.
- R2-B mechanism of rejections from existing labels (`r2_mechanism.csv`).
- R2-C generation experiment: 36 families (6 per dimension, one per near-duplicate component, 16 writers), both variants, chip1 and bare = 144 inputs; generators gpt-6.1-terra, gpt-5.6-luna, llama3.1-8b; arms A0 (plain P0), A1 (P1), A2 (minimal expansion), A6 second reading (terra); 3,600 generated rows (terra 1,440 including 144 A6 second readings, luna 432, llama 1,728; `r2_outputs.csv`). Critical judge J1/J2 on all d0 outputs and A0 d1-d3 (708 unique texts, 11 blind arbiter units, 0 unresolved); gpt M1-free on every unique d0 output; gpt M1-ref on terra A0/A1/A2/A6 d0 and A2 d1; local judges on every output. Files `r2_outputs.csv`, `r2_rates.csv`, `r2_contrasts.csv`, `r2_noise.csv`, `r2_g1sim.csv`, `r2_twocand*.csv`, `r2_policies*.csv`, `r2_selfcheck*.csv`, `r2_stored_a0_check.csv`, `r2_examples.md`, figures in `figs/`.
- Annotation request updated and items built, not sent (`ANNOTATION_REQUEST.md`, `annotation/frontier_whole_message_{items.json,key.csv,assignment.csv}`; 120 items, 360 ratings, 18 per annotator).

## R2-A. Metric validity, chip1 (n=97, 59 rejected), AUROC [writer-cluster 95% CI]

| score | chip1 all | holdout P11-20 | all 200 | bare |
|---|---|---|---|---|
| critical-only, binary (round-1 M0) | .53 [.51,.57] | .52 | .74 | .87 |
| critical-only, graded (Qwen14B) | .45 [.31,.61] | .37 | .69 | .87 |
| critical-only, graded (Nemo12B) | .55 [.44,.65] | .60 | .79 | .95 |
| T1 word count | .72 [.61,.83] | .71 [.52,.89] | .70 | .69 |
| T2 length ratio | .68 [.56,.79] | .65 | .71 | .81 |
| T3 lexical F1 to writer sentence | .60 [.48,.70] | .49 | .63 | .76 |
| T4 novel lemmas | .62 [.55,.68] | .60 | .68 | .73 |
| T5 edit distance to keywords | .65 [.52,.77] | .62 | .68 | .77 |
| T6 CV logistic (length+lexical) | .65 [.52,.76] | .61 | .69 | .72 |
| **M1-free, gpt-6.1-sol (graded)** | **.77 [.69,.84]** | **.82 [.71,.91]** | .77 | .68 |
| M1-free UC flag only (gpt) | .71 [.63,.78] | .73 | .75 | .69 |
| independent whole-message score, Qwen14B | .76 [.66,.85] | .75 | .79 | .78 |
| independent whole-message score, Nemo12B | .72 [.58,.84] | .64 | .66 | .56 |
| M1-ref, sees writer sentence (UPPER BOUND, circular) | .88 [.84,.93] | .89 | .92 | .94 |

Paired deltas, chip1, same bootstrap draws: M1-free vs best trivial (word count) +.04 [-.07,+.16] (fails rule i); vs CV logistic +.12 [+.01,+.24]; vs graded critical Qwen +.31 [+.13,+.49]; vs graded critical Nemo +.22 [+.11,+.33]; vs binary M0 +.23 [+.15,+.31]. On bare M1-free is worse than the length ratio (-.14 [-.32,+.04]) and than the graded critical score (a bare input cannot match the intended variant by construction, so rejection tracks the critical label); on all 200, M1-free vs best trivial is +.06 [-.03,+.14]. Figure: `figs/fig1_metric_vs_baselines.png`.

Status labels: graded-score primary is **post hoc** (chosen after the binary M1-ref fail flag proved degenerate, `dropped` non-empty for 100% of outputs). M1-ref is reported only as an upper bound. The deployable claim rests on M1-free alone, and it is not supported beyond length.

**Verbatim-copy false flags.** Keyword copies (gate stratum, n=100): `unrequested` flagged 0/100, but the binary whole-message flag fails 39% (dropped glue words 39%, frame changed 24%). Handling: no deployable statement uses the binary flag; claims use the UC flag and the graded score. In Part 18 the stratum of outputs with zero novel content lemmas (n=140) is still flagged for unrequested content in 44%, so the UC flag also fires on added sentence frames ("I want to ...") that the lemma count does not see. Restricting chip1 to outputs with novel lemmas leaves only 19 outputs (17 rejected), too few for a stable AUROC (M1-free .65 [.55,.75]); this exclusion test is uninformative and is not used.

## R2-B. Why writers reject outputs that keep the commitment (chip1 CK-true outputs: 93, rejected 55 = 59%)
- Reference-free UC flag yes (n=39): writer rejects 82% (chip1) ; flag no (n=54): rejects 43%. All channels: 81% vs 41%.
- UC flag no and the writer-sentence judge reports no frame change (n=34): rejects 15% (5/34). So most rejections without added content are cases where the output carries a different sentence frame or drops detail the keywords never contained. This conditioning uses M1-ref, which sees the writer's sentence, so it is partly circular.
- The declared decomposition (critical misresolution OR M1-ref frame change; added content; dropped detail; residual) is uninformative here: 134 of 146 rejections fall in the first class because M1-ref flags a frame change in 67% of all outputs and dropped detail in 100%. Not re-declared.
- Reading: rejection is mainly compression loss (details no keyword can carry); added content is a strong marker but removing it (Stage 2 and below) leaves the match score flat.

## R2-C. Generation: arms, three generators (greedy d0; gpt M1-free UC; critical judge; family-cluster bootstrap)

Flagged unrequested content per 1,000 outputs (events/N in brackets; 72 inputs per cell):

| generator | channel | A0 plain | A1 P1 | A2 minimal |
|---|---|---|---|---|
| terra | chip1 | 347 [222,486] (25/72) | 125 [42,222] (9/72) | 56 [14,111] (4/72, events < 10) |
| luna | chip1 | 361 [222,500] (26/72) | 56 [14,111] (4/72, < 10) | 56 [0,125] (4/72, < 10) |
| llama3.1-8b | chip1 | 431 [292,569] (31/72) | 389 [250,528] (28/72) | 167 [69,278] (12/72) |
| terra | bare | 694 [528,833] (50/72) | 56 [0,139] (4/72, < 10) | 0 (0/72) |
| luna | bare | 639 [472,778] (46/72) | 56 [0,139] (4/72, < 10) | 111 [28,222] (8/72, < 10) |
| llama3.1-8b | bare | 694 [528,833] (50/72) | 694 [528,833] (50/72) | 278 [139,417] (20/72) |

Pooled over the three generators (equal weight; paired by input; family-cluster CI), differences per 1,000 messages, chip1 | bare:

| contrast | unrequested content | silent reversals | SLP-weighted harm (points) | fragments | composite (reversal, UC or fragment) | word edits to writer sentence (per message) |
|---|---|---|---|---|---|---|
| A2 - A0 | -287 [-384,-199] \| -546 [-667,-417] | -37 [-69,-9] \| -9 [-46,+28] | -230 [-307,-156] \| -292 [-372,-216] | +9 [0,+23] \| -9 [-37,+19] | -278 [-375,-185] \| -352 [-444,-264] | -0.22 [-0.43,-0.01] \| -0.29 [-0.59,+0.02] |
| A1 - A0 | -190 [-287,-97] \| -407 [-500,-315] | -32 [-65,-9] \| -32 [-65,0] | -148 [-222,-74] \| -247 [-304,-189] | +42 [+14,+74] \| +148 [+83,+222] | -153 [-250,-56] \| -167 [-227,-106] | +0.20 [-0.03,+0.44] \| -0.06 [-0.33,+0.20] |
| A2 - A1 | -97 [-157,-42] \| -139 [-222,-65] | -5 [-14,0] \| +23 [-14,+65] | -81 [-130,-37] \| -45 [-98,+8] | -32 [-60,-5] \| -157 [-231,-93] | -125 [-190,-65] \| -185 [-278,-106] | -0.42 [-0.67,-0.19] \| -0.23 [-0.44,-0.03] |

Critical commitment kept (CK), pooled A2 - A0 chip1 +7.4 pp [+4.2,+11.1]; bare -0.9 pp [-4.6,+2.8] (bare CK is about 38% in every arm and generator: with no cue the model guesses). Silent-reversal and weighted-harm columns on bare are dominated by this guess rate, not by the prompt. Match to the writer's sentence (M1-ref mean score; complete only for terra, where it was run on all A0/A1/A2 outputs; luna and llama have partial coverage from cache hits and are not pooled): terra chip1 A0 .506, A1 .528, A2 .536 (A2 - A0 +.031 [+.008,+.056]); bare .408, .433, .431 (A2 - A0 +.022 [-.014,+.058]).

Per-generator contrasts and per-dimension cells are in `r2_contrasts.csv` and `r2_rates.csv`. Notable: A2 beats A1 on flagged content only through llama (A1 barely changes llama: 431 to 389; A2: 167) and through bare; for terra and luna A1 and A2 are equal on content (A2 - A1 terra chip1 -6.9 pp [-16.7,+1.4]; luna 0.0 pp [-6.9,+8.3]). A1's fluency cost is real: fragments (no finite verb) A1 - A0 +42 per 1,000 chip1 and +148 bare pooled; terra bare 24/72 fragments under A1 vs 0/72 under A2. After netting fragments into the composite, A2 beats A1 in both channels (-125 [-190,-65] chip1; -185 [-278,-106] bare per 1,000). This is a prompt-wording choice, not a new method.

Examples are real stored outputs chosen by the declared rule in `r2_examples.md` (terra chip1: A0 "I want to call the clinic." vs A1/A2 "I call the clinic." for `[I] call clinic`; certainty `[MAYBE] manager report` stays flagged under all three arms, a case where no arm helps).

## Noise floor and A0 stability
- Terra, local Qwen14B UC rate across the three T=0.7 draws: A0 chip1 .139/.097/.083 (sd .029), A2 chip1 .097/.042/.056 (sd .029); bare A0 sd .042, A2 sd .016. Llama (all arms): sd .000 to .032. The share of inputs whose UC flag flips between T=0.7 draws is 6 to 17% (up to 36% for llama A0 bare).
- Paired A2 - A0 on the Qwen UC flag has the same sign in all 4 draws for every generator-channel (terra chip1 -.028 to -.056; terra bare -.056 to -.139; llama chip1 -.028 to -.097; llama bare -.083 to -.167), so the A2 effect is larger than the draw-to-draw wobble. A1 - A0 is not stable for llama bare (+.028 to -.056, around zero).
- Stored hw1 A0 (terra greedy) vs fresh A0 d0 on the same inputs: only 69% (chip1) and 61% (bare) of texts are identical; critical retention on chip1 is 98.6% stored vs 90.3% fresh (different generations and judge runs); llama 86% identical text, CK 86.1% vs 83.3%. An 8-pp gap in CK between two A0 runs for terra is the endpoint's run-to-run noise on 72 inputs; effects smaller than that should not be trusted.

## Baselines and policies (terra, chip1 and bare, 72 inputs per channel)
- G1-sim (the guard's role simulated by the critical judge as a perfect monitor, picking the first of d0-d3 with the right critical value; an UPPER BOUND on the real G1 monitor, which was not run): terra chip1 reversals 14 to 0 per 1,000, CK .903 to .917, UC unchanged (.111 to .111 on the Qwen flag); llama chip1 reversals 97 to 83, CK .833 to .875. It never touches UC because it targets the critical value. On bare it cannot help (CK .403 to .444). A2 gets the same or more critical retention without any resampling (llama chip1 CK .931).
- Always-commit / always-ask / random-ask / flag-ask (cand1 = A2 greedy; ask = show a second reading, costs 1 tap; post hoc match >= .6; `r2_policies_posthoc60.csv`): chip1 always-commit .778 [.667,.889]; always-ask with the A6 reading .819 [.708,.917] at 1,000 taps per 1,000; always-ask with an equal-budget resample .792; at the matched ask rate of the gpt UC flag (5.6%, 56 taps per 1,000) random-ask gives .780 and every flag gives .778. At 25% and 50% ask rates the SelfCheck-style flag (.784, .797) and the length flag (.778, .778) do not beat random-ask (.788, .800). On bare: always-commit .472, always-ask A6 .583 [.444,.708], resample .528; flags at 50%: gpt UC .552, SelfCheck .527, random .527.
- Closest published detector actually run: SelfCheckGPT-style sampling consistency (SelfCheck-Unigram adaptation: mean share of the first output's content lemmas absent from each of three T=0.7 samples). Its AUROC for the gpt UC flag on terra A2 chip1 is .58 (4 flagged outputs of 72) and for "output does not match the writer" .55, against .79 and .69 for plain output word count. SHARS-style detect-then-resample, A3+, A4 variants and A5 were not run.

## AAC terms (pooled over three generators, chip1, per 1,000 messages; A2 instead of A0; machine-judged)
| quantity | change | CI |
|---|---|---|
| messages with flagged unrequested content | -287 | [-384,-199] |
| silent critical reversals | -37 | [-69,-9] |
| SLP-weighted harm points (largest weight among flagged types: polarity 1.0, speech_act .8, agent .8, certainty .7, politeness .5, time .8, added content .8; fragments excluded because the SLPs did not rate them) | -230 | [-307,-156] |
| fragments (no finite verb) | +9 | [0,+23] |
| composite failure (reversal, unrequested content or fragment) | -278 | [-375,-185] |
| extra taps | 0 | by construction |
| word edits to the writer's sentence, per message | -0.22 | [-0.43,-0.01] |
| match to the writer's sentence (terra only) | +.031 (M1-ref score, scale max .6) | [+.008,+.056] |
| judged acceptability to people | pending R-WM-1 | n/a |

For bare input the composite falls by -352 per 1,000 [-444,-264] but the critical commitment is retained in only about 38% of outputs in every arm; these gains are about added content, not about getting the message right. Asking for a second reading costs 1 tap per ask and buys +4 pp (chip1) to +11 pp (bare) match at the always-ask rate on terra.

## Where it does not help
- Intent match: A0 to A2 changes the terra match score by .031 (chip1) and .022 (bare, CI includes 0) on a scale capped at .6; the best-of-two reading adds .014 (chip1) and .039 (bare) of a .6-capped scale, and not more than an equal-budget second sample.
- Bare channel: critical retention about 38% in every arm and generator; the whole-message flag is worse than the length ratio there.
- Certainty items stay flagged under every arm in the shown example; polarity, speech_act and agent are where the prompts help (see `r2_rates.csv`; per-dimension cells have 12 outputs, descriptive only).
- Detectors (UC flag, SelfCheck-style, length) do not beat random asking at matched ask rates on this sample.
- Llama3.1-8b: A1 (P1) is nearly inert on flagged content; only A2 helps. Luna: A2 is not different from A1.

## Limits and honest caveats
- Everything is machine-judged; the UC flag (gpt) and the writer labels are different things, and Stage 2 and this round show the flag moves much more than writer-match. R-WM-1 (not sent) is required before claiming any benefit to people.
- The same vendor family generates (terra, luna) and judges (sol); llama and the two local judges are the independence check, and the local judges only partly agree (Spearman .29 to .54).
- Declared match criterion (M1-ref >= .8) is degenerate; the post hoc >= .6 threshold is labelled post hoc. M1-ref for A0/A1/A2 exists for terra only; luna and llama have critical, UC and fragment outcomes but no match score.
- Budget cuts (luna d0 only and default decoding because temperature hangs the endpoint; terra A1 d1-d3 skipped), 72 inputs per cell, 36 families and 16 writers; many cells have fewer than 10 events and are flagged. The `harm_w` and bare-channel reversal columns are dominated by the bare guess rate.
- The arbiter view prints one dimension header over units of other dimensions (as in round 1); this round I took each unit's dimension from the frozen inventory before deciding. 11 arbiter units, decisions in `runs/frontier_whole_message_r2/arbiter_decisions.tsv`. Fragments and no-explicit-time statements were labelled unclear/mixed, in line with the round-1 arbiter practice.
- Novelty: no prior work was opened this round, so no novelty claim is made. The contribution that can be defended is (a) critical-commitment retention does not predict writer rejection (reproduced with a graded comparator and two independent judges), (b) a reference-free whole-message flag that is not distinguishable from length, and (c) the AAC-terms translation. Minimal-expansion prompting is not claimed as new.
