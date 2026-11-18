# Merged no-IRB plan of action (STRATEGIST, 2026-11-18)

Sources: se4all_pc, caleai_pc, aac-ds-reviewer, ae_taccess, methods_stats (this directory). Nothing here was re-run; every number below is a reviewer estimate, not a result. Scores: SE4All and CALE-AI on the 1-10 scale (now about 6.5 and 6), TACCESS on the AE 1-5 scale (now about 2.5, "major revision, leaning reject-and-resubmit"). Realistic no-IRB ceiling: SE4All 7.5, CALE-AI 7 (8 only if the estimand and listener-hardening items land), TACCESS 3.5-4 as a participant-free technical-evaluation and measurement-validity paper; 4.5 needs AAC-user data and is not pursued.

Ranking rule: expected rating gain x feasibility / effort. Conflicts are resolved in section 8.

## 1. The five actions that matter most

| # | Action | SE4All | CALE-AI | TACCESS | Effort | Window |
|---|---|---|---|---|---|---|
| A1 | One-headline rewrite plus evidence-status table (the readability pass, done properly) | +0.5 | +0.5 | +0.2 (full effect via A5) | 6-8 h per paper, 0 people | before Nov 20 |
| A2 | Oracle independence loop: second-family (Claude) and NLI oracle on the independent mutants, fresh blind seeded faults and fresh mutants as a held-out test, oracle misses written up as defect traces | +0.7 combined (blind faults +0.4, NLI/Claude oracle +0.35, traces +0.3, overlap discounted) | 0 | +0.3 | about 10-14 h, API plus minutes of GPU under the lock, 0 people (optional 10 annotators x 10 min to confirm fresh mutants) | NLI row and 30 blind faults before Nov 20; full set at camera-ready |
| A3 | Non-GPT, larger-generator replication of the default and the cue (speech-act and polarity families first) | +0.2 | +0.4 | +0.4 | 6 h subset, about 2 days full, 0 GPU, 0 people | one sentence before Nov 20 if the subset is done; full at camera-ready and journal |
| A4 | CPU inference hardening: crossed listener x item model plus author-leakage audit, SLP weight sensitivity, power/MDE table, estimand and chain-of-effects table (bounds labelled projection) | +0.1 | +0.5 | +0.3 | 12-16 h CPU and writing, 0 people | before Nov 20 for the model, leakage audit, SLP sensitivity and short-form estimand table; full in the journal |
| A5 | Journal restructure to one thesis (about 24-26 pp), participant-free positioning, AAC-literature repositioning, DOI artifact, one claim-evidence-status table | 0 | 0 | +1.0 combined (cut +0.5, literature +0.4, artifact +0.4, discounted for overlap) | 2-3 days one editor | start the artifact link now; restructure mid-Dec |

Why these: clarity was the lowest score in J5 and all five critics put the abstract first; the SE4All thesis (a checker tested like software) is carried by the weakest sentence, "58/58 on a list that informed the tests"; "small quantized open models plus one GPT" is the largest external-validity attack; the listener study is the only human-effect evidence and a methods reviewer will test its dependence structure; the journal cannot be read as one claim at 35 pages.

## 2. Timeline

### Before Nov 20 AoE (about 2 days; machine and CPU only, no new human data)
Order matters because SE4All has no page slack and CALE-AI has about 15 lines: A1 frees the space first.
1. A1 on both papers (frees roughly 12-15 lines for A4's table and one A2/A3 sentence each). Re-measure page limits with pdftotext (References heading); SE4All stays 8 pp, CALE-AI body stays 8 pp.
2. A4 CPU items: crossed-random-effects or two-way cluster bootstrap on the listener study, leakage audit (listener ids vs hw1/hw2 writer ids), SLP leave-one-out and uniform-weight sensitivity, power/MDE table. Install statsmodels first. Frozen estimates stay the headline; sensitivities sit beside them. Write one CALE-AI listener clause and a half-page estimand table (max 10 rows).
3. A2 fast parts: PLAN.md first (git-timestamped, oracle declared before results), then NLI baseline (DeBERTa-MNLI, minutes of GPU under flock) and Claude-as-oracle on the 75 confirmed independent mutants plus 46 controls; 30 fresh blind seeded faults. SE4All: replace a Table III row, do not add a paragraph.
4. A3 subset: speech-act and bare-polarity families with 2 additional generators (one Claude tier, one larger non-OpenAI-judge model); GPT judge primary, Claude only on outputs it did not generate. One sentence per paper, only if the run completes cleanly; otherwise omit and move to camera-ready.
5. Chase the consultant member-check and SLP implications replies (due Nov 19 18:00), short-form option. Write "member-checked" only for replies actually received.
6. Artifact hygiene: Zenodo or GitHub release DOI of code, outputs, macros and replay; reviewer quick start (10 min, CPU); keep the repo URL out of CALE-AI if review is anonymous. Hash deposit of the journal's fresh confirmation PLAN.md (zero cost).

### Rebuttal and camera-ready
Full A2 (v2 oracle declared before fresh data, evaluated once on the fresh set, dev set reported as dev); full A3; Claude re-label of the guard confirmation set (A3 companion); Table V/VI merge and composition study to artifact if not already done; integrate SLP severity tasks and member-check replies; agent-developer extension test as one paragraph if finished (SE4All only).

### Journal (mid-Dec)
A5 restructure first (it decides what everything else is written into); full estimand and projection table plus simulated exposure/power design (section 7 of CALE-AI as protocol, labelled projection); public-corpus base rates; scaling plot by generator; fresh hashed machine confirmation set (generator different from the earlier one); human reason coding replacing the post hoc classifier; participant-free ethics paragraph and cover-letter text.

### Journal revision (Jan onward)
Listener round 2 (new items, oversampled negation/agent, frozen analysis); matched, larger repair-usability audit; results folded in as confirmatory or honest nulls.

## 3. Human-materials tasks (annotation of materials only)

All tasks: annotators or expert raters judge text materials already generated; no demographics, no self-report, no comprehension-in-use, no "how would you feel"; canonical ethics paragraph reused verbatim; no personal data; coordinator batches requests.

| Task | Who | People-minutes | Window | Notes |
|---|---|---|---|---|
| H1 Consultant member-check: one-page "what you told us -> what we changed" table, yes / needs-change per row, plus quote-permission and acknowledgement preference | 2 consultants | 2 x 10 = 20 (short form) | chase now | design feedback only; paraphrases only on no-reply; no quotes or names without written permission; never called a sample |
| H2 SLP implications check | 2 SLPs | 2 x 10 = 20 | chase now | same rules |
| H3 SLP severity round: severity of the three change types listeners confused (polarity, speech act, agent) and "would you block this" on 20 listener-study outputs, plus severity of "opposite action" and "unclear" on about 40 items | 2 SLPs | 2 x 30 = 60 | camera-ready | expert review of materials; n=2 stated; gives consequence weighting to the human outcome; no population severity claims |
| H4 Human confirmation of fresh mutants (A2) | about 10 annotators | 10 x 10 = 100-150 | camera-ready | materials-only judgment; needed so fresh-mutant numbers are human-confirmed, not machine-confirmed |
| H5 Human reason coding replacing the post hoc LLM/diff classifier | 3-4 annotators plus the 2 SLPs adjudicating | about 4 x 30 + 2 x 15 = 150 | journal | coding of outputs, with kappa |
| H6 Listener round 2: 120 new items, bare / chip / plain word (and guard where changed), negation/agent oversampled to at least 60, item-cluster bootstrap, frozen power note and 10 pp equivalence margin for chip vs word | 20 annotators | 20 x 25 = 500 | journal revision | new item content; same pool so independence from round 1 not claimed; declare that listeners are not AAC partners; no pooling with round 1 without declaring |
| H7 Matched repair-usability audit: about 100 repairs plus 100 item-matched never-failed controls, 3 raters per text, noninferiority margin -15 pp declared first | 20 raters | 20 x 30 = 600 | journal revision | frozen rule unchanged; no pooling with the old audit to rescue the interval |

Totals: before Nov 20 about 40 people-minutes (H1, H2 chase); camera-ready about 280-330; journal and revision about 1,250. Anything beyond this list is out of scope (section 7).

## 4. Machine experiments and compute

| Experiment | Compute | Pre-declared | Reports |
|---|---|---|---|
| M1 NLI (DeBERTa-MNLI) bidirectional-entailment oracle on 196+100 rule mutants and 100+50 independent mutants | GPU minutes under flock, behind Unity | PLAN.md before run | catch and false-alarm rates on the lexicon-blind stratum, one table |
| M2 Claude-as-oracle, GPT alone, "either" and "both" ensembles, McNemar vs GPT, on 75 confirmed mutants + 46 controls | about 1.5k Claude calls, no GPU | oracle declared before results | sensitivity, lexicon-blind sensitivity, false alarms; no "validates" claim |
| M3 Fresh blind seeded faults: 3-5 agents that never saw src/tests, 60+ single-site faults over the same 8 component classes, applied to temp copies as in src/seeded_faults.py; run the post-sweep suite once | API only, about 4 h | plan timestamped; 30 faults before Nov 20, full 60+ later | killed/total with Wilson CI by class; survivors listed as findings, one fixed with a regression test; wording "written by agents blind to the tests", not "independent of the authors" |
| M4 v2 oracle (extractor-prompt revision aimed at fail-to / refuse-to and embedded speaker) on 60 fresh mutants + 30 controls written by a subagent that never saw the dev mutants | API, 3-4 h | v2 declared before fresh data | dev vs test reported separately; re-score kill matrix |
| M5 Generator breadth: Claude tier and Gemini (polarity and speech act, one draw) plus the largest non-judge GPT tier, bare / chip / plain word / guard on the 104+80 legend and 127 speech-act families, same prompt text and request keys | API, about 6 h subset, about 2 days full; 6-10k one-sentence generations; no GPU except local models under the lock | decision rule in analysis/model_breadth_frontier/PLAN.md | chip-minus-word and affirmative share by model, writer-clustered; ordinal tier rank only; "N of M models" not "all LLMs"; Claude as labeller only on non-Claude outputs, GPT judge primary |
| M6 Claude re-label of the guard confirmation set (9.83 pp joint pass) and resample baselines | about 3-5k units | before run | delta and disagreement set; not human validation |
| M7 Listener re-analysis: crossed random effects or two-way cluster bootstrap, leakage audit | CPU 3-5 h | as sensitivity beside frozen estimates | reversal minimum detectable difference; unclear 87% -> 71% reported as what bare inputs do to a listener |
| M8 Public-corpus base rates (Vertanen-style AAC-like collections, DailyDialog, short turns) through the existing detector; recompute the 2.7% default and reversals per 1,000 under those priors | CPU, 1-2 days | availability verified first, marked % VERIFY | sensitivity of the price to the prior; "crowd-simulated, not AAC-user rates" |
| M9 Exposure/power simulation from measured rates (q 0.736, reversals 50 vs 8 per 1,000, approval-gate catch rate as an unknown with a sensitivity grid) | CPU, about 1 day | every parameter a macro or sensitivity range | sample size a future approved study would need; labelled projection |
| M10 Agent-developer extension test: 5 fresh coding agents, README only, add one dimension or chip plus oracle test; record time, files, tests, whether suite and R5 replay pass | API, about 5 h | success criteria declared | "agent proxy; no human developer has used it" |
| M11 Fresh 250-family hashed confirmation set with frozen arbitration (journal spine) | machine and API, 1 day; GPU only under the lock | PLAN.md hash published before generation | run once; use v2 judge if M4 exists |
| M12 Capability scaling plot by generator tier | folded into M5 | | trend or flattening, no scaling law |

## 5. Writing and framing changes
1. Abstracts (all three): 150-170 words, one result per sentence, at most 4 numbers each (cue +37.5 pp; listener success pair and opposite action 22.5% -> 1.3%; guard gain with its usability cost and the 73.8% vs 80% line stated once; for SE4All: 193/196 circular, 70.7% independent, 58/58 after tests). Define chip, bare, committed, mutants in one clause at first use. Secondary stats (kappas, arbiter 77.4%, 87.8/92.3, 31.41/31.65, first-round 35.3, multilingual, coverage) go to tables or body. One status sentence replaces repeated "(descriptive / exploratory / post hoc)" parentheticals. Keep each honesty item once, compressed: listener not AAC partners, Claude re-label not independent, audit underpowered, n=2 defects, coverage not rate. Per the Tone rule do not lead with or end on a limitation.
2. Evidence tiers in the SE4All intro: (A) independent of authors and GPT (115/115 judge, 200/200 detector, 47/50 style items, independent mutants, Claude re-label 94.0%); (B) author-built (kill matrix, defect trace); (C) exploratory (hw1/hw2). Spine: "the checker is software; here is how we tested it; here is what it caught that a text-similarity score cannot." Keep the "I want coffee / I don't want coffee" Fig. 1.
3. CALE-AI re-aim at the venue: lead with cue restoration plus listener result; estimand and chain-of-effects table (rows: guard joint-pass gain, cue restoration, listener success, listener opposite action, usability audit; columns: unit, intervention, comparator, estimand type, what is not identified, link to next row); Section 7 stays testable predictions H1-H3 plus protocol and power numbers. Report Q2 (opposite action) as the consequence outcome and reversal as the frozen primary not confirmed; "unclear" as the more accurate lead. Always "adult listeners judging materials", never "people understood".
4. Merge Tables V and VI; move the composition study to the artifact; compact status table (claim, rule frozen when by git timestamp, n and cluster unit, Holm family, status). Do not use the word "pre-registered"; hash deposits are timestamps, not registration.
5. Journal: thesis "passing a meaning-preservation oracle is necessary, not sufficient"; move ask-policy arithmetic, frontier pilots, multilingual, guard detail, F1/F2 follow-ups to the online appendix with one main-text sentence each; keep the ask-policy null and guard cost visible. Reposition the literature in AAC-domain scholarship and the participatory stance. Replace the two-paragraph caveats with one claim-evidence-status table. Lead with what a developer can do; label human-sounding results "proxy".
6. Wording hygiene: "writers" is used for pair writers and raters (separate them); drop two-decimal pp figures; "listeners" always carries "adult, non-AAC" at first use; reading cost is "words shown", not time.
7. Ethics paragraph canonical and unchanged: annotators non-authors and reimbursed; classmates judged study materials; no personal data; some wrote pairs under recorded CC BY consent; no institutional determination sought. Never "exempt", "approved", or "not human-subjects research". For TACCESS, read the ACM human-subjects policy [verify] and prepare the cover-letter paragraph; offer the editor the evidence and say plainly that desk-risk exists.

## 6. Weaknesses unfixable without IRB, and best framing

| Weakness | Best framing | What it costs |
|---|---|---|
| No AAC-user outcome (benefit, preference, burden, trust, speed) | State once at the top of Limitations: "developer-facing evaluation of stored text; claims about people who use AAC are predictions H1-H3, not findings"; the estimand table and protocol with power numbers make the missing link the stated, bounded contribution | a clause in the abstract only where a benefit word appears |
| Writers and listeners are classmates, not AAC users or partners; single pool for all human labels | State the pool once with unique persons per task; leakage audit; "agreement among them is not independence from them"; "comprehension of materials, not real-world consequence" | none beyond the audit |
| Messages constructed or crowd-written, not real logs; cost per tap, not time | "Constructed minimal pairs"; public-corpus base-rate sensitivity; no ecological claim | M8 |
| Writers rejected 61% of judge-correct outputs (post hoc judgments) | A finding about the metric: necessary, not sufficient; the paper evaluates commitments, not usefulness | none |
| n=2 consultants, n=2 SLPs | "Design consultants" and "expert review"; replaced-requirement table with changes made; SLP leave-one-out; never a sample or panel validation | H1-H3 |
| hw1 writers 6-7 per contrast | Claim direction and consistency; exact sign-flip floor; do not widen by recruiting writers | none |
| Reversal difference includes 0; listener chip success 28.3%; oracle 58.5% lexicon-blind; 73.8% below the 80% line | Keep every number; state as "not confirmed", "partial", "diagnosed and tested" with find-fix-retest | A2, H6 |
| Possible ethics query on classmate pair-writing and writer self-rating (Part 18) | Describe as annotation of materials built from the annotator's own text; canonical paragraph and no-personal-data statement in rebuttal; the user decides whether Parts 18 and 26/27 are cut from the journal if an editor asks | residual desk-reject risk accepted |

## 7. What to stop doing
- Stop running new human-behaviour tasks: no new writer-generation sessions (hw3 is cancelled), no surveys, think-alouds, preference ratings, demographics, or "how would you feel" items, no member-check as evidence of benefit.
- Stop adding new results to abstracts and stop adding caveat clauses; stop repeating "descriptive/exploratory/post hoc" tags where a table column says it.
- Stop treating machine agreement (Claude, NLI, Gemini) as human validation, and stop calling Claude "independent"; it is a second family.
- Stop post hoc tuning: no re-tuning tests and re-running until kill rates look high, no choosing the oracle or generator after seeing results, no pooling rounds without declaring, no replacing the frozen primary, no "observed power".
- Stop growing the journal beyond about 26 pages and stop moving null results out of sight; stop hand-typing numbers (every number is a macro, every new run gets a git-timestamped PLAN.md first).
- Stop quoting or naming consultants/SLPs without written permission; do not write "member-checked" for non-replies; do not recruit outside the class cohort.
- Stop chasing TACCESS 4.5 or an AAC-partner listener claim; do not add a repo URL to an anonymous submission; do not commit.

## 8. Conflicts resolved
- hw3 more writers (methods) vs "no further writer sessions" (SE4All PC, AE, causal): cancelled. Writers generating pairs is closest to participant research; keep direction-and-consistency framing and the sign-flip floor.
- Listener round 2 (all five): journal revision only, not before Nov 20, new items, frozen analysis; the matched usability audit goes alongside it. Both stay materials-annotation tasks.
- Frontier breadth: unanimous in direction; scope is a subset before Nov 20 and the full set later. Claude is never both generator and arbiter on the same output.
- Oracle: SE4All PC wanted blind faults and NLI first, methods wanted Claude ensemble plus closed-loop v2, AE wanted second family. Merged into A2: all run, the oracle and v2 declared before data, dev and test kept separate.
- Journal cut: AE and aac-ds agree on one thesis and about 24 pp; SE4All PC adds the artifact; merged into A5.
- Estimand table: only the causal critic ranked it first; kept as a half-page table (A4) because it converts the main weakness into the method contribution, capped at 10 rows and projection-labelled.
- SLP severity: methods wants sensitivity on existing weights (CPU, now), SE4All/aac-ds want a second rating round (camera-ready); both done in that order.
