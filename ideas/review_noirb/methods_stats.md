# No-IRB plan: adversarial methods and statistics reviewer

Date 2026-11-18. Read: SE4All and CALE-AI PDFs (text), journal OUTLINE.md, ledger C44-C81, decision_log D-096..D-106, analysis/listener and analysis/oracle_indep summaries. I did not rebuild PDFs and did not re-run any analysis; every "check" below is a proposed step, not a result.

## What my score currently rests on
Strong: frozen rules, macros from analysis files, honest reporting of misses (listener reversal CI includes 0, guard = bare, plain word not shown equivalent, seeded-fault 58/58 labelled as coverage of a list that informed the tests).
What still costs points, from a methods view:
1. All human evidence comes from one pool of about 20 classmates acting as writers, checkers, raters, listeners. Correlated population, non-AAC.
2. Headline human outcomes are small (listener n=20 x 120 items; 6-7 writers for two of three hw1 contrasts) and use unadjusted intervals; the listener reversal contrast is not confirmed; 87% "unclear" invites the reading that bare is merely ambiguous, not wrong.
3. The oracle's lexicon-blind sensitivity is 58.5% and misses are concentrated (fail-to, refuse-to, embedded speaker). The paper reports it honestly but does not close the loop (diagnose -> fix -> test on fresh mutants), which is the SE story.
4. Generators are four small open models plus one GPT tier (plus two 12-14B); judge and one generator share a family. No frontier non-GPT generator. The affirmative-default claim therefore reads as a small-model fact.
5. Guard evidence is the weakest part: repair audit n=20+20, raters not independent, guard = bare on the listener task; Part 17 (3 independent raters) is primary but its status in the papers is a pilot.
6. Forking paths: many post hoc and exploratory rows (pooling hw2, arbiter after outcomes, T4 coding change, Q3/Q4 gate), and an abstract dense with intervals. A reviewer cannot tell which 3 numbers are confirmatory.

## The 10 actions, ranked by (rating gain x feasibility)

### 1. Claude-ensemble oracle ablation on the independent mutants, then a closed-loop fix (SE4All centrepiece)
- Do: (a) have blind Claude subagents label the 75 confirmed mutants + 46 controls (same extractor questions, output text only) and compute sensitivity, lexicon-blind sensitivity, false alarms for Claude alone, GPT alone, and "either flags" / "both flag" ensembles, with McNemar vs GPT. (b) Write a pre-declared extractor-prompt revision aimed at the diagnosed classes (fail to / refuse to, embedded speaker), declare it a v2 oracle BEFORE seeing any fresh data, and evaluate v2 on a FRESH mutant set (60 mutants, new operators written by a Claude subagent that never saw the dev mutants, plus 30 controls). Human confirmation of the fresh set by ~10 annotators (about 10 min each, materials-only task, same ethics paragraph). Report dev (the 75) as dev and fresh as test.
- Why: converts "the oracle is 58.5% lexicon-blind" from a limitation into a find-fix-retest result; Claude-vs-GPT shows whether the weakness is family-specific (answers the shared-family threat directly). Highest value for SE4All's thesis.
- Effort: (a) 1-2 h agent time, about 1.5k Claude calls, no GPU; (b) 3-4 h plus 150 annotator-minutes.
- Timescale: (a) before Nov 20 if run tonight (it is CPU/API only; add one sentence + one table row in SE4All, which has no page slack so replace the Table III row, do not add a paragraph). (b) camera-ready / journal.
- Risks: ensemble raises false alarms (report both); v2 fixes fail-to but breaks something else (report the full kill matrix again, it re-scores for free); Claude labels the mutants differently because it was told what the question is (keep the question identical to production).
- Do NOT: tune v2 on the fresh set; call the dev-set number an estimate after v2 saw those mutants; claim the ensemble "validates" the oracle.

### 2. Frontier-model breadth for the affirmative default and cue restoration (Claude subagents + Gemini + a larger GPT tier)
- Do: bare-polarity, bare-politeness and speech-act arms plus chip arms on hw1+hw2 families (547+127) for 2-3 additional generators: a Claude tier as generator, Gemini (limited quota: polarity and speech-act only, one draw), and the largest available GPT tier other than the judge. Labels by the existing GPT J1/J2 + blind arbiter (the arbiter must NOT be the same Claude tier that generated; use a different tier or the Claude re-label path with outputs mixed and unlabelled by source). Pre-declare the decision rule in analysis/model_breadth_frontier/PLAN.md and commit/hash before generating (a prior hash deposit exists: protocol-hash-*).
- Why: the largest external-validity attack is "small quantized open models plus one GPT". A result that frontier models still silently default, or that they do not, is publishable either way and changes the rating from "interesting harness" to "finding with reach". Either outcome is reported; the cue claim becomes "cue restores in N of 9 models".
- Effort: about 2 days wall clock mostly waiting on API; zero GPU; about 6-10k generations at 1 sentence each.
- Timescale: (a) partial: bare polarity on hw1 104 families x 2 tiers, one hour, enough for one sentence in both papers; full set (b)/(c).
- Risks: Claude as generator and Claude as arbiter is self-preference (use the GPT judges as primary; Claude only as arbiter for GPT-and-Gemini outputs); frontier model refuses or asks a clarifying question for bare keywords (count as uncommitted, report share); Gemini quota stops mid-run (run in paired blocks; drop incomplete blocks, say so).
- Do NOT: change the prompt per model; pick the one tier that reproduces the effect; describe the result as "all LLMs".

### 3. Re-analyse the listener study with crossed random effects and a two-way cluster bootstrap; add item-author leakage audit
- Do: install statsmodels (the summary notes it is missing, PLAN section 5 said the mixed-model sensitivity stands as "not run"), fit logistic GLMM (success ~ condition + (1|listener) + (1|item)) and a two-way (listener x item) cluster bootstrap for chip-bare, bare reversal, opposite-action. Report as sensitivity beside the frozen estimate; the frozen estimate stays the headline. Also check, per listener, whether any listened-to item was written by that listener or a close collaborator (hw1/hw2 writer ids vs listener ids) and re-compute excluding those units.
- Why: a methods reviewer expects the listener x item crossing; the current CI (cluster bootstrap over a unit) may understate variance. If the sensitivity CIs still exclude 0 for chip-bare (+20.0) it removes the attack; if not, better we say it than the reviewer.
- Effort: 2-3 h, CPU, zero annotator time.
- Timescale: (a). Add one clause in CALE-AI limitations or the listener sentence (slack is about 15 lines in CALE-AI; SE4All must swap, not add).
- Risks: the crossed interval is wider and chip-bare no longer separates; leakage check finds shared authorship. In both cases report it; the finding is "direction consistent, width uncertain".
- Do NOT: change the headline to the more favorable estimate; run the sensitivity after choosing which to report.

### 4. Evidence-status table: one page of "confirmatory / frozen-exploratory / post hoc" for every headline number
- Do: add to CALE-AI (an appendix or supplementary file if the review allows; one compact table in the journal) and SE4All (one or two lines) a status ledger with columns claim, rule frozen when (git timestamp), n and cluster unit, multiplicity family, status. Cut abstract numbers to at most 4 per paper (the cue gain +37.5, the listener success pair, the oracle mutants, the guard cost), moving the rest to the body. Declare Holm families explicitly (listener Q1 family, hw1 three contrasts, audit endpoints).
- Why: converts the forking-path worry into transparency; reviewers who see the table mark "confirmatory" rows generously and ignore the post hoc ones. This is also the core of the readability pass.
- Effort: 3-4 h, CPU, all from ledger rows.
- Timescale: (a) for the abstract trims and an SE4All sentence; journal gets the full table.
- Risks: the table exposes that few rows are truly confirmatory (it is true; say it); page pressure.
- Do NOT: relabel anything "pre-registered"; backdate; describe hash deposits as certifying W-C.

### 5. hw3: more writers for politeness and polarity (the contrasts stuck at 6 and 7 writers)
- Do: recruit 10 of the same classmates (writers only, no personal data, CC BY 4.0, consent as before) to write 15 politeness and 15 polarity pairs each, 25 min each, with the same three blind checks (reuse hw2 pipeline). Models: the same 6 + frontier from action 2. Freeze the rules in analysis/hw3/PLAN.md before generation (copy hw1 rules; no changes).
- Why: P2 and P3 are the floors of the permutation tests (1/64, 1/128) and the stated reason the abstract says "direction, not width". With 15-16 writers per contrast the sign-flip floor is about 3e-5 and t-intervals are honest. Raises the primary replication from exploratory-6 to exploratory-16.
- Effort: 250 annotator-minutes, 1 day machine, about half a day analysis.
- Timescale: (c). Not before Nov 20.
- Risks: effect smaller; the same pool writes more (not independent of hw1 writers: some will repeat, so count unique writers and say it); P2 politeness effect is small (+7.6) and could shrink to null; report it.
- Do NOT: pool silently with hw1; stop collecting when significant.

### 6. Fresh pre-hashed machine confirmation set with frozen arbitration (the journal's confirmatory spine)
- Do: generate a new 250-family set across the dimensions with a generator different from the earlier confirmation, write PLAN.md including the judge version (v2 from action 1 if it exists), the arbiter rule (arbiter sees output text only, rules fixed before any labelling), the primary endpoints and the exclusion rules; publish the hash (GitHub release, as before) BEFORE generation. Then run once.
- Why: the existing confirmation set had post-outcome arbitration and an 80% line missed (73.8%); a clean confirmation, hashed first, is what separates confirmatory from exploratory in the journal and answers "arbiter after outcomes".
- Effort: 1 day, machine and API; zero people.
- Timescale: (c). A hash deposit can happen before Nov 20 even if the run is later (zero cost, helps rebuttal).
- Risks: results disagree with the earlier set (report, that is the point); GPU competes with Unity priority (the 16 GB limit allows the 14B only under the lock; use API for the rest).
- Do NOT: reuse families; edit the plan after the first model call; let the arbiter see conditions.

### 7. Part 17 repair audit at adequate size (replaces the n=20+20 pilot as the guard evidence)
- Do: take the 3 independent raters per item design already frozen (COORDINATOR_STEPS section 4), enlarge to 60 repaired + 60 never-failed controls from W-C (stratified by model and dimension), 20 raters x 18 items, paired against own failed originals where the repair came from a failure. Pre-specify a noninferiority margin for usable of -15 pp (state it before scoring, with justification: the Part 4 pilot gap was -35 pp with unknowns counted unusable and -13.3 pp otherwise).
- Why: the guard section currently ends "audit underpowered"; a noninferiority test either supports the guard or retires it, and either result is more useful than another "includes zero". A retired guard is fine under the ledger thesis ("gain-only evaluation hides failures").
- Effort: 360 annotator-minutes (20 x 18 min), 3 h to build the packets from the existing generator, 2 h to score.
- Timescale: (c); a power note (80% power at what difference given n and item ICC) goes in the Nov 20 papers at zero cost.
- Risks: raters fatigue at 18 items; control items are easier (known item-difficulty confound; use matched controls on dimension and length, not random).
- Do NOT: describe the pilot's -13.3 as "no cost"; keep "never claimed AAC-user benefit".

### 8. SLP weight and severity sensitivity, no new data
- Do: with n=2 SLPs, recompute the clinically weighted failure rates (cue gain; guard) under (i) each SLP alone, (ii) rank-order weights only, (iii) uniform weights, (iv) worst-case permutation of the weight order of the five lowest dimensions. Report the range, and Cohen's kappa on severity (with the caveat n=2). Add leave-one-SLP-out to the journal.
- Why: any statistician will say "n=2 severity weights" is the single softest number in the abstract. Showing the cue gain survives all weightings turns the softness into robustness, at zero data cost. If the abstract number does not survive, we learn it before a reviewer does.
- Effort: 1-2 h, CPU. Timescale (a); one clause in the SE4All abstract/body or CALE-AI body (the 2-SLP 5/5 negation claim is already worded as "each rated").
- Risks: ranges are wide; then drop the weighted figure from the abstract and keep the "5 of 5 each, both would block it" sentence only (a true, small claim).
- Do NOT: infer population severity; call these weights "clinical consensus".

### 9. Chase the consultant member-check and the SLP implications check now
- Do: re-send the packets (expert_package/consultant/member_check, slp/implications_check; due Nov 19 18:00 per D-103) with a 10-minute short-form option: three yes/no questions (paraphrases fair; quote permission; acknowledgement preference). Honour no-reply: keep paraphrases only, no quotes.
- Why: a member-checked Table 4 is the one piece of AAC-community grounding available without IRB; it is the response to "no AAC user involvement". People-minutes: 2 consultants x 10 min, 2 SLPs x 10 min.
- Timescale: (a) for the camera-ready sentence "paraphrases member-checked by both consultants" only if both replied; (b) otherwise.
- Risks: a consultant objects to a paraphrase (then change it: that is the point); do not write "member-checked" for a non-reply.
- Do NOT: use quotes or names without permission; describe consultants as a sample or as study participants; imply endorsement of the system.

### 10. Listener round 2 targeted at the unconfirmed reversal and plain-word equivalence (journal only)
- Do: 120 non-default-value items only (where reversals live: bare 66.7 vs chip 0 per 1,000 in round 1), conditions bare / chip / plain word only, 20 listeners x about 18 min, new items not seen in round 1, frozen power note and TOST margin of 10 pp for chip vs plain word (round 1 gave -0.5 [-7.2, 6.3] at 90%: equivalence was within reach but not shown at the margin used). Keep the clear distinction between "unclear" and "opposite".
- Why: resolves the one human endpoint that the papers must now call "not confirmed"; if it confirms, the cue claim changes from "descriptive" to "confirmed in a human task".
- Effort: 360 annotator-minutes, 2 days build and scoring.
- Timescale: (c). Same pool, so independence from round 1 is not claimed; counterbalance, no listener sees an item twice.
- Risks: the same 20 classmates again (practice effects: use new item content and different sentence frames); effect on reversal still includes 0.
- Do NOT: change the endpoint after round 1 data; call listeners AAC partners.

## What cannot be fixed without IRB, and how to frame it at least cost
| Weakness | Frame |
|---|---|
| No AAC-user benefit, preference, burden, speed or error-recovery data | One sentence at the top of Limitations and one clause in the abstract only where a benefit word appears: "developer-facing evaluation of stored text; claims about people who use AAC are predictions (H1-H3), not findings". Make the testable predictions the contribution. |
| Listener comprehension is by non-AAC adults, not partners | Name it "comprehension of materials, not real-world consequence" (already so); do not say "listeners" without the adjective; put the number in a human-outcome table not the first sentence. |
| Messages are authored or crowd-written, not real AAC logs | Say "constructed minimal pairs" everywhere; contrast with AACText fiction; do not claim ecological coverage. Optional (no IRB needed): replicate on a public corpus of short conversational messages (existing crowd-written fiction already used). |
| Single pool of classmates for all human labels | State the pool once with the unique-person count per task; run the author-leakage audit (action 3); say agreement among them is not independence from them. |
| n=2 SLPs, n=2 consultants | "Expert review", "design consultants", never "panel validation"; sensitivity analysis (action 8). |
| Positionality (independent researchers, no AAC-community partner institution) | Already in Limitations; keep it short and specific; add that the consultants reviewed requirements, not outputs of a deployed system. |

## Ranking summary
1 ensemble oracle ablation and closed-loop fix; 2 frontier breadth; 3 crossed-effects listener analysis and leakage audit; 4 evidence-status table and abstract trim; 5 hw3 writers; 6 hashed fresh confirmation; 7 Part 17 at size; 8 SLP weight sensitivity; 9 member-check chase; 10 listener round 2.
Before Nov 20 AoE (zero annotator time): parts of 1(a), 2 (bare polarity only), 3, 4, 8, 9. Camera-ready/rebuttal: 1(b), 5, 6 hash. Journal: 5, 6, 7, 10, 2 in full.

## Notes for the readability pass (my reading as a reviewer)
- The SE4All abstract is a single 330-word paragraph with about 20 intervals; a reviewer cannot find the thesis. Keep: need for an oracle; what we tested (mutants, seeded faults, held-out, relabel); the one human sentence; the result "necessary not sufficient". Move held-out precision/recall and the 31.41/31.65 sensitivity numbers to the body.
- Remove parenthetical stacking: "(first round alone, 6 writers: 35.3 pp; pooling the second round was decided after seeing it)" belongs once in the body, not the abstract.
- Define "chip" and "bare" and "committed" at first use in each abstract.
