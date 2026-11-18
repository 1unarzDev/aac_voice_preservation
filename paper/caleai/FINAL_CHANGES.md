# CALE-AI final writer, round 1 (Nov 17)

Folded in (every number is a macro in make_macros.py reading the stored summary files; hx_, tc_, src_, dp_, vq, cv_ prefixes):
- hw1+hw2 speech-act result (analysis/hw12): +37.5 [33.8, 41.2], 10 writers, 1,016 rows; wild and sign-flip checks, all writers positive, leave-one-out, hw2 alone, Can-you / I-want-please recodes; where it does not help (Llama +16.9, 6/127 families, 17% of cue outputs miss). P2/P3 unchanged and still reported as direction only. New "Held-out writers" paragraph (Sec 6.4), abstract, contributions, conclusion.
- Part 20: judge critical label vs human consensus 115/115 on treated outputs (Scoring paragraph, Sec 3), added content stated as the weak field; the "validated on untreated outputs only" sentence and the Limitations clause were revised.
- Part 21 / corrected T2: 2.7% [1.8, 3.7] unchanged, stated as largely by construction (Defaults paragraph).
- Part 22 (source labels validated, human-label always-commit reversals, Q3/Q4 gate not validated, kappa about 0) and Part 24 (measured q 73.6% [59.7, 86.1] vs assumed 90%) as a "Human labels on the frontier inputs" paragraph in Sec 6.6. The P-I/value_of_cue refit numbers are not in the paper (it carries none of them); the refit bootstrap did not finish, so none is cited.
- Stage 6 coverage as a bounded "Draft sets against one cue tap" paragraph (one cue tap vs draft sets; sets do not replace the tap; contrast selection not better than prompted diversity; adult annotators, not AAC users).

Page budget (body <= 8 pp): to make room, cut the audit's per-pool and per-model sentences, the estimator Table (now one sentence), part of the estimand, related-work and consultant text, trimmed the MRT table rows, scaled Fig. 2 to 0.82 width. No result was removed except those details.
Compliance: no names, university, URLs or repo names in the text (the phrase "authors' university peers" became "authors' peers"); no undefined refs or missing macros (build log clean); body ends on p. 8, references on pp. 9-10; artifact placeholder is \pending{anonymized artifact URL} in the last sentence of the Conclusion. Tone rule applied (limits stated once, briefly, in the body).
Deviation: none from the frozen analysis rules; the machine-round coverage proxy is mentioned nowhere (human results only).

# Round 2 (reviewer feedback)
- Anonymity/history: removed "earlier cue-value analysis", "now measures", and "shares data with this paper" (companion paper cited as described elsewhere); artifact placeholder replaced by "An anonymized artifact rebuilds every number."
- Headline scope: abstract and conclusion now carry the per-model range (+0.85 to +19.02) and say the 78 families are the guard's weakest dimension (upper-leaning slice); the 0-of-26 is stated with its construction caveat in the abstract.
- Usability: abstract states the audit once as a bounded result (gap, CI, detectable gap); intro "Yes" replaced by "What does it show?"; conclusion no longer repeats the cost caveat (Sec 6.2 holds it once); abstract ends on the cue/default finding.
- Statistics: sign-flip p marked one-sided (two-sided floor twice); 0/26 bound marked exact upper 97.5%; Table 2 development "Pass line" now "development criteria met (not a confirmatory test)", confirmation labelled the only confirmatory verdict.
- Thesis shown: one sentence of what a gain-only report would say vs what the ledger adds. Contributions trimmed 5 to 3. Related work: +2 sentences and 2 refs (Maynez 2020, Ji 2023; marked VERIFY in refs.bib). Fig. 1 caption leads with the chip legend; "row" references replaced. Defaults paragraph split into short sentences with one p (src_t2) and the others listed once.
- Not done: Table 3 is already in Sec 7; Sec 6.4-6.6 numeric density only partly reduced; the model-pooled intervals' fixed-model note remains in Scoring ("the models are fixed, not sampled").
- Build: body ends p. 8, refs pp. 9-10, no undefined macros. No new numbers typed; all via existing macros.

# Round 3 (final writer, error-fix pass)
- Fig. 1 caption: second example is the politeness row (polite option 26/40 to 12/40); sets with both readings (polarity and certainty) rose 15/80 to 78/80 (macros sc_pz_*, sc_pc_*).
- Abstract and Sec. 6.1: 0 of 26 is measured by the same strict predicate the monitor uses (partly by construction); the 120-text human audit is named the non-circular safety evidence. Frozen verdict reported with the significantly negative stricter endpoints (meaning preserved -13.6 [-26.2, -1.0]; usable and preserving -20.0 [-34.8, -3.9]) beside the paired original-failed result (meaning kept +30.0 [9.1, 46.8]; usable and preserving +10.0 [-9.4, 29.1]).
- Within-pair contrasts marked exploratory (secondary, fixed before returns, outside the frozen rule, uncorrected); 20 vs 19 pairs explained (one original had no decided stance rating; new macro p17_stance_unk).
- Cue failed clause (73.8% of typed vs the 80% line) now in the abstract, contribution (3) and Sec. 6.3 (conclusion no longer claims the cue gain alone).
- p range 2.0% to 11.4% and break-even ratio 36 to 8 beside the break-even argument (macros t2_post_h_bayes, t2_post_c, t2_ratio_h, new t2_ratio_c).
- Abstract and conclusion: +9.83 is on the guard's weakest development dimension (upper-leaning slice), spread +0.85 to +19.02 by model.
- Stage 6: one bounded paragraph (cue tap main lever +30 pp; draft sets add +13 on top of a cue, not instead; prompted diversity does as well); measured q=0.74 (new macro vq_q) where the 90% assumed supply rate appears.
- hw1+hw2 speech-act +37.5 [33.8, 41.2], ten writers, in the abstract. Artifact placeholder restored: \pending{anonymized artifact URL} in the last sentence.
- Space cuts (to keep body at 8 pp): the abstract's judge-agreement sentence, AUROC clause, chen2023say duplicate sentence, "other estimates of p" list, two MRT rows, minor wording. No result other than these details removed.
- Build clean (no undefined macros); body ends p. 8, refs p. 9-10 (10 pages total). No names, URLs or university. Not committed.

# Round 4 (final fixer, verifier errors)
- Abstract rewritten (~200 words): leads with the cue (+37.5, ten writers, all positive), then the guard (+9.83 on its weakest development dimension, 52.51% repaired, 0 of 26 by the strict check itself), one-sentence lead claim "repairs half of strict failures but the repairs cost meaning" with audit endpoints; cue failed 80% clause (73.8%) and "same-item regeneration with machine labels, supply rate q=0.74 (vq_q)" stated. Audit named once as the 120-text primary audit (p17_prim); contribution (2) now says "primary". Exploratory paired contrast and 18-point detectability stay in the body only.
- Conclusion and contribution (3): failed 80% clause, same-item/machine-label qualifier and q added; [PENDING] artifact placeholder removed from the text.
- Part 23 whole-message result in the intro (A2 vs A0 acceptability 0.0 [-13.9, +16.7], 36 inputs; added-content flag kappa .23, sensitivity .31, not a validated detector); new macros wm23_* parsed from analysis/frontier/whole_message/human.md in make_macros.py.
- Sec 3: validation split into a "Label validation" paragraph that opens with the weak added-content field (kappa .59).
- P3 labelled: first seven writers' pairs, percent of committed answers (analysis files give the same as points above 50).
- Table 2 example-row overlap fixed (scriptsize mono, noalign skip; generator figs/make_caleai_figs.py updated). Cut the Can-you/I-want recode sentence for space. Build clean, body ends p. 8, refs pp. 9-10.
- Not done: Part 25 (C73) not reported; abstract wording on 98.4% dropped rather than reworded; design constants (90%, 80%, 20+20, +-5) still typed; Fig. 2 text small; no real artifact URL exists (sentence says anonymized artifact rebuilds every number).
