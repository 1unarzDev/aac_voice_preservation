# SE4All final fold-in (final writer)
- Act-chip gain now pools hw1+hw2: +37.5 [33.8, 41.2], 10 writers, all positive, 127 families, leave-one-out 36.7-38.3, sign-flip p = .0010 (floor); Llama weakest (16.9, writer means not all positive). Abstract, Table II row ("rounds 1+2"), caption, results text, confirmation-set comparison use macros hx_* (analysis/hw12). Politeness/polarity unchanged (6/7 writers).
- New "Treated outputs" paragraph (Part 20): judge critical label = human consensus on 115/115 treated outputs, all 6 classes; added content stays weak (98/109, kappa .59). Abstract and conclusion mention it. Macros tc_* (analysis/treated_check).
- Part 21: detector negation label 200/200 vs human; T2 2.7% / 24 per 1,000 unchanged. Macros src_*.
- Stage 6: one sentence (cue tap main lever: one draft 13% bare vs 43% after cue; three bare drafts 22%). Macros cv_* (analysis/coverage_human). Elaboration left to CALE-AI per overlap rule.
- Trimmed prose elsewhere (cost-of-extension, controls, model breadth, SLP, composition, consultants, limitations "Use") to stay at 8 pages; no content claims dropped. Removed the "labels" arrow label in Fig. 2 (overlapped a node). Caveat that coders were taught the codebook kept.
- IEEE pass: IEEEtran conference 10pt, 8 pages incl. refs, author block intact, no overfull boxes/undefined refs (only a scit font-shape substitution warning), AI-use disclosure comment placeholder kept (no text written), ethics paragraph unchanged. Not committed.

# SE4All verifier-fix pass
- Abstract: "tested its oracle with software-testing methods" (was "the way one tests software"); mutants labelled "a sensitivity measure"; held-out precision/recall now carry Wilson intervals; arbiter figure states chance 50%; act-chip gain gives round-1-only estimate (6 writers) and says pooling round 2 was post hoc; confirmation-set gain shown with post-hoc arbitrated labels masked (wcp1_um); extractor/generator family overlap stated.
- Results: sign-flip p labelled one-sided (two-sided .0020 added, macro hx_sf_p2); floors labelled one-sided; Table II gets a "round 1 only" row (macros hx_r1*, from analysis/hw12/speech_act_sensitivity.json).
- Threats: extractor-family overlap moved to first position as the main limitation. Conclusion: T1 is "a proposed regression test, lexical, awaiting human validation".
- refs.bib: Lacosse entry gets note arXiv:2610.19177 (prints in reference list).
- Cuts to hold 8 pages: cost-of-extension LOC detail, SLP severity weighting, per-dimension gain sentence, manipulation-check sentence, model-breadth sentence.
- Build: 8 pages, no overfull/undefined; all pages viewed.
- Unfixed: Tables IV+V not merged; no non-OpenAI re-label of extractor; rounding stays half-even (96.25 prints 96.2, 13/40 prints 32); mixed interval types only legend-covered; 2026 refs not re-verified beyond REFS_VERIFIED.md.
