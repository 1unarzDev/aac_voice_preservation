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

# SE4All kill-matrix pass (seeded-fault sweep, Claude re-label)
- Replaced the old inventory fault-by-test table (tab:matrix) with ONE fault-to-test kill-matrix table (Table IV, generated as `kill_table.tex` by make_macros.py from `analysis/seeded_faults/{kill_matrix,round2_kill_matrix}.csv`): per class K1-K8, mutants killed by unit tests (round 1 and 2), oracle tests, validator replay, frozen rescore, and pooled all-test score round 1 vs round 2.
- New paragraph "Seeded faults, two untested components, new regression tests": 58 mutants, round 1 killed 39/58, sweep exposed judge post-processing (0/6) and input builder (1/8) as untested, two test files added, round 2 kills 58/58 on the same mutants (same table hash). Stated as a coverage score of a fixed list that informed the tests, not a detection rate; replay uses stored J1/J2 fields and layer-0 labels, not recorded API payloads. Abstract, contributions, Threats (Oracle bullet) and Conclusion updated to the same story.
- New paragraph "A second judge family": Claude re-label of 1,574 units; critical label vs human 94.0% (kappa .935, n=265) vs GPT 96.6% (kappa .964); act-chip gain with Claude labels +37.9 [34.5, 41.3] vs +37.5 (8 of 2,046 labels change). Discloses that the same model family also arbitrated and assisted, so it is a second opinion, not independent. Threats bullet no longer says "no non-OpenAI re-label".
- Slots: `% ORACLE_INDEP` (macro \oracleindep, default sentence says the independent mutant set is pending; uses RES@oi_text when make_macros defines it; sentence pattern in a comment in main.tex preamble) and `% LISTENER` (macro \listenerslot, empty by default; pattern in comment). Both sit in the "Seeded faults" paragraph.
- All new numbers are macros sf_* and rl_* (make_macros.py). Unused-now macros left in place (sf_pytest_n etc.).
- Cuts to stay at 8 pages (no result dropped): composition subsection condensed, legend three-arm sentence, model-breadth/corpus-transfer sentences, per-writer means, Defect B and R5 agreement details, surface-baseline false alarms, mutant-source-count sentence, development-item in-sample numbers, T1 per-model rates, writer-judge kappa, R-SPEAK related-work sentence (its bib entry is now uncited), Fig. 1 caption, a few arbiter/elicitation clauses.
- Build: 8 pages incl. references, no overfull/undefined (only scit font substitution); all 8 pages viewed. Not committed.
- Not done: ORACLE_INDEP and LISTENER results (arrive later); abstract is long (~330 words) and should be tightened by the orchestrator if the venue enforces a limit.

# SE4All five-improvements pass
- (1) Abstract and intro now open with authorship: a message is spoken as the person's own, so a silent reversal puts words in their mouth; SLP severity (macros slp_neg = 5 of 5, new slp_neg_block = 100%, both would block). The \listenerslot macro moved from the Seeded-faults paragraph to the intro (comment % LISTENER, still empty until Nov 19); an abstract-sentence placeholder comment added. \oracleindep untouched.
- (2) Section V rewritten as "What Consultants Who Use AAC Told Us" with one compact Table VI (8 paraphrased design points -> R6, R1 scope, R2 exact copy, R3 draft/difference, R4/T1, Defect B tests, chip-as-probe, cue-as-choice). "Two paid consultants ... design review, not a study; no data about them." % QUOTE-PENDING: C01/C02 permission comments placed in the table and section; no quotes used.
- (3) "Necessary, not sufficient": person owns the message; implications (cue the person controls, R6, exact typed words, R2). (4) New "Costs to the person" paragraph: effort/scanning/gaze/reading as design reasoning only (no motor-cost numbers); Stage 6 cue tap +30 pp, extra drafts +13 on top (new macros cv_s3*, make_macros.py) -> least burden for most protection.
- (5) "AAC users" -> "people who use AAC" throughout; precise Positionality sentences added to Ethics (two independent researchers, no lived AAC experience reported, no AAC participants/co-authors, annotators not recruited as people who use AAC, why this limits claims). NOTE for author: verify the "no lived AAC experience" wording is true of you both.
- Cuts to hold 8 pages (no result dropped): cost-of-extension and model-breadth paragraphs, one strict-rule table row, keyed-challenge bullet, elicited-keywords precision sentence, T9/R5 detail, some human-gate/arbiter/related-work wording. Build: 8 pages incl. refs, no overfull/undefined; all pages viewed. Not committed.

# SE4All verifier-fix pass 2 (respectful framing)
- Disability statements removed: consultants are now "paid design consultants" (abstract, contributions, Sec II, Sec V title "What Our Design Consultants Told Us", conclusion, ethics); "(not a sample)" hedge added to abstract, contribution (4), Sec V; "required" -> "asked for".
- Member check: Ethics now states the Table VI paraphrases are not member-checked (packet in expert_package/consultant/member_check/ pending). Positionality: "none of us reports using AAC". Inactive anonymous-acknowledgement comment added (permission needed, agreement section 6).
- Roles: "SLP consultants" -> "SLP raters"; R4 relations request attributed to the SLP raters. "information the person paid for" -> "selection effort the person spent".
- Numbers: "six types" -> macro slp_ntypes (7); slp_acc_rep now exact k/n (32.5, was half-even 32). Stage 7 slots untouched. 8 pages, no overfull/undefined. Not committed.
- Unfixed: p=.0003 still hand-typed; "protects authorship" wording in R2 row/Sec IV left; consultant_log.csv still has C1/C2 split (internal file).

## 2026-11-18 fold: independent mutants + listener sentence
- make_macros.py now emits oi_* (analysis/oracle_indep/summary.json: judge sensitivity 31/53 = 58.5% non-circular stratum, 53/75 = 70.7% overall, surface/overlap baselines in the stratum, agreement, controls) and ls_* (analysis/listener/summary.json: bare 8.3%, chip 28.3%, +20.0 pp [9.1, 31.2], 20 listeners). results_macros.tex regenerated (run from repo root).
- \oracleindep and \listenerslot are now defined as sentences over those macros (default "not yet in" text removed); the %-comment placeholders deleted. Listener sentence carries the not-AAC-partners / materials-not-consequences caveat; mutant sentence states weakness on fail-to/refuse-to/embedded roles and that passive and embedded-question mutants were unconfirmed.
- Compression to hold 8 pp: cut the Claude-relabel sentence from the abstract, the strict-rule clause, the arbiter side-of-prompt sentence, item-level arbiter agreement clause, a "taught the codebook" sentence, and one mutation-misses sentence. Build: 8 pages, no missing macros.
- Not added (space): reversal-per-1,000, consequence and guard listener results; abstract has no listener sentence.

## 2026-11-18 FINAL FIXER
- \oracleindep: literal 75 -> macro oi_all_n; adds k/n 53/75, judge false alarms on confirmed controls (oi_fa 4/46, politeness), and states the rule-seeded figure overstates sensitivity. Abstract now calls 193/196 a circular measure and gives 70.7% on lexicon-blind mutants.
- \listenerslot: CI labelled unadjusted 95% bootstrap; adds bare "unclear" 86.7% (new macro ls_un_bare) and reversal difference -42 per 1,000 [-99, 7] includes zero (new macros ls_rd*, make_macros.py; regenerated from repo root).
- Cuts for 8 pp: abstract "two defects/keyed gate zero margin" sentence, "released" sentence, equivalent-mutant parenthetical. Build: 8 pages incl. refs, no undefined; pages 1 and 8 viewed.
- Unfixed (needs new analyses/venue choice): second non-GPT/non-Claude extractor, pre-specified pooling for 37.5 pp (abstract still gives it), third defect trace, R6 test, member check, density of Tables II-V, p=.0003 hand-typed.

## 2026-11-18 readability pass
- Abstract cut from ~330 to ~165 words: problem, method, circular-vs-lexicon-blind mutant caveat (70.7%), cue effect (99.8% affirmative default; +37.5 pp, exploratory), listener result with reversal difference not confirmed, necessary-not-sufficient (61.1% rejected) and consultants-who-use-AAC (not a sample). Four result numbers.
- Secondary statistics (leave-one-out, sign-flip p, per-model splits, robustness shift, chip-control gaps) moved from prose into new Table "Secondary results" (tab:secondary); primary paragraph and controls paragraph shortened and open with their point; Costs paragraph reordered to lead with the finding. Fixed a broken paragraph break.
- Honesty elements retained (Stage 7 listener sentence, mutant circularity, human-vs-machine labels, ethics/positionality). Original saved at tmp/se4all_main_before_readability.tex. Not committed.

## 2026-11-18 FIXER (post-check)
- Fig. 1 caption: 99.3% chip figure now stated as conditional (of the 414 outputs wrong bare, right with chip), not an overall chip rate.
- Abstract: removed cryptic "(a coverage score)". Not changed: Wilson 96.8% vs rounded 97 (consistent); email trailing underscore and IEEE AI disclosure left for author.
- Build: page count and References position rechecked.

## 2026-11-18 A1 one-headline rewrite + A2/A4 fold (SE4All)
- Abstract rewritten: headline = testing the oracle like software (independent mutants 70.7% / 58.5% lexicon-blind, Claude 90.7% and NLI 73.3% as alternative oracles, seeded faults) then the cue as the application (99.8% affirmative default, +37.5 pp exploratory, listener opposite action 22.5% -> 1.3%). Intro opens with the problem, then states the one headline; contributions list replaced by one paragraph.
- New Table I (evidence status: claim -> Human / Machine / Author-built / Not measured -> estimate), 10 rows. Listener sentence moved from the intro to a new "Listener check" subsection, with one sentence on the A4 sensitivities (crossed models, leakage audit: effects unchanged; reversal difference still not confirmed, item-clustered test does not reject).
- Table (Oracle evidence): near-circular baseline rows merged into one; three rows added for the 75 confirmed independent mutants (judge, NLI primary rule, Claude label-change: all / lexicon-blind / false alarms). \oracleindep gained one sentence (NLI rule declared before scoring; Claude is a second family, not independent; NLI misses role/implied-time; sensitivity only). No new paragraph.
- New macros in make_macros.py: oi2_* (analysis/oracle_indep2), ls_cq_bare/chip (new half-up rounding fmt "pcth" so 1.25 prints 1.3 as frozen), oi2_extra. results_macros.tex regenerated.
- Cuts to hold 8 pp (nothing dropped from results): contribution list, interval-convention sentence, family-count sentence, composition/consultant-table rows (2), 4 oracle-table agreement rows, 4 secondary-table rows, p19_cy sentence, Costs closing sentence, conclusion and related-work wording. Not changed: honesty elements, Ethics.
- Build: docker pdflatex, 8 pages incl. refs, no overfull/undefined; pages 1, 2, 8 viewed. Backup tmp/se4all_main_before_A1.tex. Not committed.

## 2026-11-18 FIXER (checks round: nits)
- Abstract: NLI/Claude catch rates now stated "of all 75 mutants" (macro oi_all_n), resolving the strata-mixing nit vs Table I; listener sentence now says "no AAC users were tested".
- Listener check: reversal difference "stays not confirmed, at best borderline". No number changed; no mismatches were found by the checkers.
- Build (docker pdflatex): 8 pages incl. references (References on p. 8), no overfull/undefined refs. Not changed: scit font warning, email underscore, AI disclosure, artifact URL (author items).

# Round 7 (2026-11-19, framing and readability pass)
- Abstract rewritten: stakes -> oracle problem -> harness + four testing methods -> "tests changed what the oracle can be trusted for" (rule-seeded 193/196 vs independent 70.7%, seeded-fault sweep) -> 115/115 treated -> application (99.8%, +37.5 exploratory, listener 22.5% -> 1.3%) -> necessary not sufficient. NLI/Claude moved to Table I and the body.
- Intro: research question restored from the Nov 17 draft; four numbered contributions; one evidence-tier sentence.
- Section order: II Harness, III Testing the Oracle (moved up), IV Applying the Tested Oracle (was III). Independent-mutant paragraph now follows the rule-seeded real-output result it qualifies, with its own heading.
- Removed internal artefacts: the repo path in the Table VI caption, the consultant_log.csv path, "Stage 6"; Fig. 1 caption statistics shortened.
- Ethics and positionality tightened, every required statement kept.
- Trims for 8 pages: machine-agreement anecdote, composition setup, booster clause, per-set kappa list (now "at or above .925").
- Checks: 8 pages including references, 0 overfull boxes, no undefined references; no new numbers vs the previous PDF.
- Fresh-reviewer fixes (score 5/10, clarity 3): the abstract gives both 70.7% overall and 58.5% lexicon-blind, "four models (six in breadth checks)", 115/115 "that had a consensus", and the listener 8.3 -> 28.3 beside the opposite-action result; IV-C explains opposite action vs reversal; Table I says the seeded-fault tests were written for those faults; the conclusion's listener claim is softened. 8 pages.

# Round 8 (2026-11-19, outsider rewrite)
- Blind A/B baseline: Round 7 7/10 (clarity 6) vs the Nov 18 draft 6/10 (clarity 5).
- Body rewritten in plain language (tmp/framing/r8/se_body.tex; assembler tmp/framing/r8/se_assemble.py; Round 7 backup tmp/se4all_main_r7.tex).
  - Terms defined once (input conditions, cue chip, identity test, mutant, control, human gate, tie-breaker); J1/J2, "keyed" and "arbiter" jargon removed from the prose.
  - Testing the Oracle split into five subsections; the "rule-seeded mutants overstated sensitivity" story is the centre.
  - Table I gives all / lexicon-blind mutant results for each checker.
  - Listener measures defined.
  - Secondary-results table removed (key items kept in the text); confirmation-set table kept with a plain caption; composition folded into IV-D.
- 7 pages including references, 0 overfull boxes, no undefined references, no new numbers.
- Layout pass (user feedback): run-in italic headings in Sec. II and Related Work became lettered subsections; new Fig. 1 table (one stored Gemma output per input condition, verbatim from runs/hw1/outputs.jsonl, hw-pol-075 variant B); all table captions shortened to titles, notes moved to a short line under each table; Tables I, IV and V rebuilt with plain labels (Table V as two row groups); Tables III and VI full-width and centred; Table II requirements rewritten without C(x)/L_d(y) notation; Fig. 2 node labels updated; abstract tightened; Defect A/B and IV-D paragraphs split; stale references fixed. 7 pages, 0 overfull.
