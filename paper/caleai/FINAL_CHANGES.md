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
