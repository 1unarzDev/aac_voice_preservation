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

# Round 5 (Plan section C: ledger as method, human outcomes, listener slot)
- Structure: abstract, contributions and conclusion restructured so the ledger is the method, cue restoration is the cleanest finding and the guard is the worked case of hidden costs. Cue stated at the measured q (vq_q = 0.74, analysis/frontier/value_of_cue/human_q.json), with Part 20 (judge agrees with two people on 115/115 treated outputs, 20/20 each for chip and plain-word cue; existing tc_* macros), the Claude re-label and Stage 6. Intro "no AAC users" sentence reworded (stored text plus adult-annotator judgments).
- New Sec. 6.5 "Cue restoration judged by people": (a) Listeners (Part 28) slot; (b) writers' own intent (Stage 6, analysis/coverage_human; cue tap +30 pp, exploratory, draft sets +13 on top of a cue; paragraph moved out of Sec. 6.7, wording unchanged in substance); (c) second-family re-label (Claude Sonnet; P1 +37.9 [34.5, 41.3] vs +37.5; 8 of 2,046 labels changed; agreement with human consensus 94.0% of 265, with the judge 93.0% of 272; disclosure that Claude also arbitrated and assisted analysis and writing).
- LISTENER SLOT (to fill Nov 19): \slotListenerAbs (abstract), \slotListenerBody (Sec. 6.5), \slotListenerConc (conclusion) in main.tex; defaults print an orange PENDING marker. Sentence patterns for each frozen-rule outcome of analysis/listener/PLAN.md (headline, chip-bare CI excludes/includes 0, guard-bare inert-by-construction, plain word vs chip equivalent/not shown, fewer than 16 listeners, attention-check exclusions, fallback) are in the header comment, slot (E). Design counts are macros (ls_items 120, ls_g1_chg 16, ls_listeners 20; ls_listeners is a typed design constant). Result macros ls_* still to be added to make_macros.py once the scorer output exists. Tested with dummy fill text of expected length: body still ends on p. 8.
- Ethics paragraph: now the plan's wording (twenty adult non-author volunteers from the authors' university classmates, consented, paid, judged study materials as annotators; no data about them; no one used or was evaluated on a system; no AAC users; no institutional review determination sought) plus the CC BY 4.0 sentence. Limitations first item now says human outcomes are annotator judgments, listeners are not AAC communication partners, comprehension is not a real-world consequence.
- New macros (make_macros.py): rl_* (relabel_nongpt/summary.json), tc_chipc/tc_nlc, ls_*. results_macros.tex regenerated; no existing macro changed.
- Space cuts to stay at 8 pp: the "price the default" closing sentence, the "accounting conditioned" sentence, the faithfulness/hallucination related-work sentence (this removes the only citations of maynez2020faithfulness and ji2023hallucination, so both leave the printed bibliography; restore the sentence if space allows), the always-commit and coder-agreement sentences in Sec. 6.7, the lexical chip-token sentence, the writer-intent decomposition sentence, the "Can you" coding clause, the Estimand paragraph (folded), menu and cue paragraphs merged, consultants and community sentences shortened.
- Build clean, no undefined macros, 10 pages (body ends p. 8, refs pp. 9-10). All pages viewed. Anonymous: no names, URLs or project history. Not committed.

# Round 6 (human-consequence framing; five improvements)
- 1 Human consequence: abstract and intro now open with authorship (a spoken message is heard as the person's own; a silent reversal puts words in their mouth) and carry the SLP severity (negation \RES{slp_neg_sev} of 5, both would block; macros). Listener slot (\slotListener*, % LISTENER) untouched, still in abstract, Sec. 6.5 and conclusion for Nov 19.
- 2 Consultants: new Table 4 "What AAC-user consultants told us and what we changed" (R6 approval, R1 NOT-to-action, R2 exact-copy default, R3 differing drafts highlighted, flagged flaws -> fixed items and regression tests); paraphrase only; "% QUOTE-PENDING: C01/C02 permission" comment in Sec. 7; framed as a design review of requirements, not a study.
- 3 What people wanted: Sec. 6.6 writer-intent paragraph adds rejection reasons from existing macros (p18_right_dropped 98% compression, p18_right_subst 49% event/role, overlapping diff-classifier flags) and "the person, not the model, owns the message"; abstract carries 1/200 as-written.
- 4 Costs: Sec. 7 paragraph, labelled design reasoning (taps cost effort, more under scanning/gaze; reading drafts costs attention; neither measured): one cue tap +30 pp cheapest route, drafts +13 more at reading cost.
- 5 Framing: positionality statement replaces "Community involvement" in Limitations (authors independent LLM-evaluation researchers without a clinical or AAC-community partner institution; no AAC users as participants; claims limited accordingly). CONFIRM that author description is acceptable. No new numbers typed; no new macros.
- Space: cut resample/standardize sentence and paired-usable sentence in audit slot, estimators and ask-policy sentences in 6.7, Sec. 6.3 default-detail sentences, MRT table rows, misc. Build clean, body ends p. 8, refs pp. 9-10. Not committed.
- Ethics: 'university classmates' changed to 'recruited by the authors' (anonymity).

# Round 7 (respectful-framing fixes from verifiers)
- "AAC-user design consultants" -> "paid design consultants" in Sec. 7, Table 4 caption, Positionality (re-identification risk, n=2). Sec. 7 says: written agreement, paraphrase only, no data about them, they did not review the paper or outcome measure, did not always agree (button vs plain word; rewrite and confirmation), neither speaks for AAC users. Table 4 rows R2 and R3 starred (put differently by the two; footnote gives C02's optional-Rewrite/Undo view).
- Burden claim: "least burden for the most protection" -> "smallest added step among the options compared, as design reasoning; burden and benefit untested"; "protection" -> "stored-text coverage"; abstract "costs the person" -> "costs in text and in design terms"; "cheapest route ... among those compared".
- Positionality: "n=2 each" -> "two people per role"; consultants/SLPs described as paid reviewers; H3's "said what I meant" outcome stated as our proposal to be checked with AAC users; authors' own AAC use/clinical training not reported (stated); no acknowledgement without permission.
- Space: trimmed other limitation/ethics wording (dropped "untreated and treated outputs" detail from Labels sentence). Stage 7 slots intact. Build clean, body ends p. 8, refs pp. 9-10; pages viewed (1, 8, 9).
- Not fixed: member-check not reported (not returned; paper does not claim one); intro line 135 "often compose" is cited, unchanged; consultant consent/compensation wording kept brief; QUOTE-PENDING comment kept; Table 2 "per distinct request" tweak skipped.

## Page-limit trim (body back on page 8, about 19 free lines)
Cut or compressed (no numbers or macros removed except noted):
- MRT table (Sec. 7): shortened estimand, arms, outcomes and sample-size rows; same macros.
- Frontier limits: dropped model names, the chip/word elaboration, and the cue-value restatement; kept the 3 claims, q, and CIs.
- Consultants paragraph: shortened; Table 4 untouched; "paid design consultants who use AAC" kept.
- Limitations: removed caveats already in the body (strip-only, menu not run on confirmation set, duplicate "no AAC user was evaluated", "no acknowledgement without permission"); positionality and ethics kept.
- Sec. 6.x: removed duplicate "listeners are not AAC partners" sentence, "necessary, not sufficient" line, "The cue has to come from the user", chip-vs-word polarity/time sentence, honour-rate pair (hx_chip_rate, hx_non_rate), rl_gpt agreement clause, "analysis files give same figure" parenthetical.
- Macros no longer printed in main.tex: cc_nl (polarity/time sentence had no macro), hx_chip_rate, hx_non_rate, rl_gpt, rl_gpt_n (none used by abstract or conclusion).

## Stage 7 listener fold (Part 28, scored as frozen)
- make_macros.py: ls_* macros now read analysis/listener/summary.json (success, reversal, unclear, conseq, contrasts, Holm, plain-word 90% interval).
- Filled \slotListenerAbs, \slotListenerBody, \slotListenerConc; all PENDING markers removed (none in PDF text).
- Abstract: one sentence, reversals per 1,000 bare vs cue (50 vs 8) marked descriptive (interval includes zero) plus intended-reading 8% vs 28% (+20 [9, 31]). No reversal headline claimed (frozen rule: not confirmed).
- Body (Sec. 6.x Listeners): success + Holm + reference 100%; consequence 22.5% vs 1.3% (non-default 33% vs 0%); reversal descriptive; mostly unclear (87%/71%); guard changed 16/120, success 0.0; plain word not shown equivalent (-0.5, 90% [-7.2, 6.3]); limits stated once (two listeners per unit, 50% non-default design mix, unclear partly lost information, low absolute success, mixed model not run, not AAC partners).
- Conclusion: one clause (8% to 28%). Cue's failed 80% clause, Part 17 endpoints, anonymity, consultants-who-use-AAC wording unchanged.
- Space: shortened own listener text to fit; build 10 pp, body ends p. 8, References starts p. 9 (pdftotext). Pages 1 and 8 viewed.

## Final fixer (verifier round)
- Abstract: cue headline now labelled a machine-label gain checked against people, with the 80% shortfall (wc_act_ratio) stated immediately after; q and "removes nearly all silent reversals" dropped from abstract, contributions and conclusion; guard sentence gives usable gap and meaning-preservation point estimates first, notes underpowered and secondary/uncorrected.
- Fig. 1 caption: 0-of-26 marked "by construction, scored by the same predicate". Table glossary: G1r defined as resample-without-feedback. H3 text: states it is the workshop-theme contribution and that a null demotes the offline proxies. Conclusion guard sentence shortened. QUOTE-PENDING comment removed.
- Build: docker pdflatex, 10 pp, References starts p9 (pdftotext), body ends p8; pages 1 and 8 rendered. No undefined refs.
- Not fixed: full ~150-word abstract rewrite, confirmatory/exploratory marker in Table 2, Table 2 overfull and font enlargement, independent-mutant numbers in CALE-AI (SE4All-only), ls_cq_chip rounding nudge, GenAI placeholder, 0-of-26 still in body, no claims-ledger row added.

## Readability pass (Nov 18)
- Abstract rewritten: 149 words, 4 headline numbers (+37.5 cue, 73.8% vs 80% target, 28% vs 8% listeners); problem, method, findings, limitation clause. Kept: failed 80% clause, "machine-scored", reversal cut not confirmed, guard audit underpowered with stricter endpoints, no AAC users. Fixed double-negative ("-13.3 points less often") by removing the number from the abstract.
- Sec. 6.4/6.5 prose: moved wild interval, sign-flip p, writer-mean range, new-vs-first writers, Llama split, contrast-selected set, bare-3-draft range, kappa to new Table "Secondary results" (tab:secondary); primary CIs kept in text. Added plain topic openers to two paragraphs.
- Build clean, no undefined refs; 10 pp, body ends p8 (References heading on p8). Pages 1, 2, 8 viewed.
- Not done: per-paragraph opener rewrite of Sec. 3-5, sentence-length pass of Setting/Interventions.

## Fixer (numbers/limits check, Nov 18)
- No numeric errors found by checker (about 45 figures verified). Listener limits: "adult classmates" -> "adult peers of the authors" (matches Ethics). Table 4 sample-size row: flag rate now "computed at the unrounded 8.46%-rate" wording so 473 messages reproduces.
- Table 2 overfull (144 pt) viewed on p5: nothing clipped (multicolumn rows only); 4 pt overfull left. Ethics paragraph already states no institutional review determination was sought.
- Not done: macro-backed derivation of "about 18 points" audit MDE (text uses dz_mde macro); structural readability items (abstract/thesis paragraph, Sec. 6.2, 6.7 density) left to the readability pass.
- Build: 10 pp, References heading on p8 (pdftotext), body within 8 pp, no PENDING, no undefined refs.

## A1 one-headline rewrite + A4 fold (Nov 18)
- Title, abstract (about 125 words) and Introduction now lead with ONE headline: the cue restores intended meaning for adult listeners (+20 pp success; opposite-action 22.5% -> 1.3%); machine gain (+37.5, 73.8% vs 80%) as supporting; ledger/guard as a gain-and-cost sentence. Abstract no longer ends on a limitation; "none an AAC user" is in the listener clause. Conclusion reordered the same way.
- Thesis/Contributions paragraphs replaced by "Headline" and "The ledger" paragraphs plus new Table 1 (evidence status + estimand: claim, estimand/unit, evidence type human-judged / machine / projection, estimate; 8 rows, all macros). Chain row labelled projection (central +14.7).
- A4 fold: listener body adds crossed-model robustness (GLMM +19.5 [14.7, 24.5]; two-way cluster linear +20.0 [11.8, 28.1]) and "0 of 846 judgments by a listener who wrote or checked the pair"; "mixed-model check not run" removed from limits. New macros hd_* in make_macros.py (read analysis/hardening/summary.json). Frozen estimate stays the headline. Reversal row stays "not confirmed".
- Space cuts to keep body on p8: duplicate intro sentences, audit-rule clause, per-model gain list, "offline failure indicators and cost" paragraph, wc_early sentence, unfixed-failure sentence, two secondary-table rows, one consultant row, frontier politeness clause and dp_* human-label sentence, p19 arbiter-agreement sentence (macros still generated), consultants-paragraph trims. All honesty items kept (80% shortfall, audit underpowered, not AAC partners, Claude not independent, no IRB determination, anonymity).
- Build: docker pdflatex, 10 pp, body ends p8, References starts p9 (pdftotext). Pages 1, 2, 8 viewed. Not committed.

## Fixer (checker round 3, Nov 18)
- Abstract, "Headline" paragraph, conclusion: "restores intended meaning" -> "improves the reading listeners choose"; states absolute 28% with "most cue outputs still miss it", "no AAC users or partners tested", frozen primary (received reversals, -42 per 1,000 [-99, +7]) not confirmed, guard usability gap with interval and "deployment clause unresolved". Intro now says cue is lead contribution, guard the worked ledger case. All numbers via macros.
- Not done: worked example/mini-glossary on p1, Table 1 split, Table 3 overfull (nothing clipped), pooled ~34-pt note, ledger rows for gt_jgain_g1/gt_rep_g1 provenance, GenAI comment wording (no space; body held on p8).
- Build: docker latexmk, 10 pp, Conclusion on p8, References heading p9 (pdftotext), no undefined refs. Not committed.
