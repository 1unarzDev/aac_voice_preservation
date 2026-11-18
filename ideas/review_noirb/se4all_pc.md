# No-IRB action plan: SE4All program-committee reviewer (2026-11-18)

Basis: se4all/caleai/journal PDFs, OUTLINE.md, claims ledger C44-C81, D-096..D-107, review_j5. Current rating by me: SE4All 6.5 (weak accept), CALE-AI 6, journal-draft not yet reviewable as a TACCESS paper. Target: SE4All 7.5, CALE-AI 7, TACCESS minor-revision-able.

Timescales: (a) before Nov 20 AoE, about 2 days, so only cheap/machine items; (b) camera-ready/rebuttal; (c) journal mid-Dec and revision.

## Where my score is actually lost (no-IRB view)
1. Density: ~150 numbers, 7 tables, abstract that spends its words on secondary stats (clarity 5/10 in J5). Biggest cheap gain.
2. SE claim rests on the authors' own exercise: 58/58 kill is on a list that informed the tests (stated as coverage, so it is not evidence of fault detection); 2 self-found defects; no outsider ever extended the harness.
3. Oracle independence: 70.7% overall and 58.5% lexicon-blind on independent mutants, with role_passive 0/14 and q_embed 1/12 unusable or missed; no NLI/entailment baseline; extractor and generator share a family.
4. Human-outcome gap: listener study is annotators reading materials; guard = bare for listeners; reversal difference includes 0; writers reject 61% of judge-correct outputs.
5. Generalisation: 6 models, 5 families, all <=14B 4-bit except one API model; one prompt; constructed text.

## The 10 actions, ranked by (rating gain x feasibility)

### 1. One-headline restructure and readability cut (gain +0.5 SE4All, +0.5 CALE-AI; feasibility very high)
- Do: each abstract states one result per sentence, <=4 numbers, no tokens a stranger must decode (chip, pp, J1/J2, mutants defined by one clause). Pick a single spine for SE4All: "the checker is software; here is how we tested it; here is what it caught that a text-similarity score cannot." Rank evidence into three tiers in the intro: (A) independent of authors/GPT (human-confirmed: 115/115 judge, 200/200 detector, 47/50 style items, independent mutants, Claude re-label 94.0%); (B) author-built (kill matrix, defect trace); (C) exploratory (hw1/hw2). Merge Tables V and VI (J5); move composition study to artifact; keep Fig. 1 with the "I want coffee / I don't want coffee" example. Secondary stats to tables.
- Why: clarity was the lowest J5 score and the evidence is strong enough that tiering it converts density into credibility.
- Effort: 1 person, 6-8 h per paper, plus the macro rebuild; page count re-check via pdftotext (References heading). Timescale (a).
- Risk: dropping a number that a reviewer wanted. NOT: add new results to the abstract; do not delete the honesty elements (n=2 defects, coverage-not-rate, scope of listener study) to save space; compress them.

### 2. Fresh blind seeded faults (gain +0.4 SE4All; feasibility high)
- Do: have 3-5 Claude subagents that have never seen src/tests write 60+ plausible single-site faults for the same 8 component classes (spec: "a bug a maintainer might introduce"), applied to temp copies exactly as in src/seeded_faults.py; run the post-sweep suite once, frozen plan first (git-timestamp). Report killed/total with Wilson CI, by class, with survivors listed as findings and one survivor fixed by a new regression test.
- Why: converts the weakest SE sentence ("coverage of a fixed list that informed the tests") into a genuine detection estimate on faults not used to design tests. A 45/60 result is still publishable; 100% would look suspect.
- Effort: ~4 h orchestration, API/subagent only, no GPU. Timescale (a) if scoped to 30 mutants, full set (b).
- Risk: low kill rate; frame as the point of the method. NOT: re-tune tests and re-run until it is high; do not call it independent of the authors (the agents share a model family with the authors' assistant: say "written by agents blind to the tests").

### 3. Second oracle and NLI baseline on the mutant sets (gain +0.35; feasibility high)
- Do: on the 196+100 rule-mutants and the 100+50 independent mutants run (i) Claude Sonnet as oracle with the same acceptance rule, (ii) an off-the-shelf NLI model (DeBERTa-MNLI, fits 16 GB, minutes) as bidirectional-entailment oracle, (iii) existing lexicon baseline. Report catch rate and false-alarm on the lexicon-blind stratum in one table.
- Why: closes the J5 "no NLI baseline" point and tests whether the 58.5% is a GPT-family artefact. Either outcome is informative (NLI missing negation changes would be a nice SE finding).
- Effort: ~3 h, GPU under flock for minutes (behind Unity priority), Claude API for (i). Timescale (a) for the NLI row, (b) for Claude.
- Risk: Claude oracle better than production judge; then say so and report as option, no claim of superiority. NOT: choose the oracle after seeing results; pre-declare in a PLAN.md before running.

### 4. Turn the oracle's own misses into the defect trace (gain +0.3; feasibility high)
- Do: role_passive 0/14 and q_embed 1/12 were "not usable"/missed; the 31/53 miss structure is a defect list. Write 2 more traces beside the relaxed-acceptance and input-builder defects: miss class -> requirement (R1 scope, event/role) -> failing test -> status (fixed, or declared out of scope in R1 with the test marked expected-fail). Re-run only the affected mutants, labelled as post-hoc.
- Why: raises "defects found by the process" from n=2 to 4 and shows the harness reports its own blind spots, the point of the title.
- Effort: 4-6 h, mostly CPU/API. Timescale (a) text, (b) re-run.
- Risk: appears as scope creep; keep to half a column. NOT: patch the lexicon and quote the improved rate as the oracle's rate.

### 5. Cross-family and frontier-size generator replication, targeted (gain +0.3 SE4All/+0.4 CALE-AI/+0.4 journal; feasibility medium)
- Do: take the speech-act contrast (127 families, hw1+hw2; bare / chip / plain word) and polarity bare-default (104+80 legend families); generate with Claude subagents (Sonnet, Haiku-class) and limited Gemini, same prompt text and request keys; label with GPT judge J1/J2 and Claude blind labeller; report P1 chip-minus-word and affirmative share by model, cluster by writer. Frozen PLAN first.
- Why: the only plain external-validity upgrade available without people: shows the effect is not a <=14B-quantised or GPT-family property, and the harness ports to a new generator without code change (also an SE point: R5 replay, 0 conflicts).
- Effort: ~2 days for the full set, ~6 h for the speech-act subset; no GPU; Claude subagent throughput is the limit. Timescale (a) subset as one sentence, (b)/(c) full.
- Risk: frontier models may not show the default (then report that: it prices the problem by model size). NOT: sample families post hoc, or say "all LLMs".

### 6. Agent-developer extension test (gain +0.3 SE4All; feasibility medium)
- Do: replace the missing "outside developer" with a machine proxy: 5 fresh coding agents, each given only the README and told to add one new dimension or chip (e.g., modality "can/must", quantity) plus its oracle test; record wall time, files touched, tests added, whether the full suite and R5 replay still pass, and failures. Pre-declare success criteria.
- Why: the "cheap to extend" claim becomes evidence of a type SE reviewers recognise (extension effort, regression safety), without human participants.
- Effort: ~5 h, API only. Timescale (b) (can be a 1-paragraph in camera-ready), (c) journal.
- Risk: agent results are not developer-usability evidence. State it as "agent proxy; no human developer has yet used it". NOT: report it as a user study or as human developer time.

### 7. Public-corpus base rates to price the failure (gain +0.25; feasibility medium)
- Do: estimate how often real short AAC-like utterances contain negation, a question/request form, politeness markers, using public corpora (e.g., the AAC-like and communication-partner collections released by Vertanen and colleagues, DailyDialog, Switchboard-style short turns), with the existing detector; recompute the "2.7% default" and reversals per 1,000 under those priors. Cite the corpora and licence; verify availability first (mark `% VERIFY`).
- Why: answers "constructed, crowd-written" with data about real AAC-like text and makes the per-1,000 price transparent to a prior.
- Effort: 1-2 days, CPU. Timescale (b)/(c).
- Risk: AAC-like corpora are simulated by crowd workers, not AAC users; say so. NOT: claim the rates are AAC-user rates.

### 8. Consultant and SLP member-check, bounded (gain +0.25 CALE-AI, +0.4 journal; feasibility medium)
- Do: (a) chase the unreplied consultant member-check and SLP implications replies; send each consultant the one-page "what you told us -> what we changed" table with a yes/needs-change per row; accept corrections as design feedback only. (b) With the 2 SLPs, a 30-min second rating round: severity of the 7 change types for the three that listeners confused (polarity, speech act, agent), plus "would you block this" on 20 listener-study outputs. All are expert raters/design feedback inside the stated permission.
- Why: removes "n=2, paraphrased, unconfirmed" and gives a pre-specified expert-weighted outcome for the listener result (consequence severity), the nearest no-IRB proxy for a harm claim.
- Effort: <=30 min per person; batch via coordinator. Timescale (b)/(c); (a) only the chase.
- Risk: no reply before camera-ready: keep paraphrases and no quotes (current rule). NOT: quote or acknowledge anyone without written permission; do not describe them as a sample or as evidence of user benefit.

### 9. Listener round 2 designed for the open question (gain +0.3 journal, +0.15 CALE-AI; feasibility medium, effort high)
- Do: 20 annotators again (judging materials), pre-specified: oversample negation/agent items (>=60) so the received-reversal difference is estimable (round 1: 50 vs 8 per 1,000, CI [-99,7] including 0); add chip+word and a bare-vs-guard-feedback arm; item-cluster bootstrap; declare in advance that listener != AAC partner.
- Why: round 1 left the headline harm outcome unconfirmed; a powered round turns it into a result or an honest null for the journal.
- Effort: ~25 min/annotator, ~2 days orchestration, scoring scripts exist. Timescale (c) only.
- Risk: another null. Fine: the SLP-weighted consequence and "unclear" rate remain. NOT: re-analyse round 1 with new rules, add post hoc endpoints, or pool rounds without declaring it.

### 10. Artifact and ethics-wording hygiene (gain +0.2 SE4All; +journal desk-reject risk down; feasibility very high)
- Do: Zenodo (or GitHub release) archive with DOI of code, stored outputs, macros and the one-command replay; a "reviewer quick start" (<=10 min, CPU only: self-tests, kill matrix, R5 replay). Check single-blind compliance for SE4All, anonymity for CALE-AI (no repo URL). Keep the ethics paragraph as canonical (annotators non-authors, reimbursed, no personal data, no institutional determination sought). For TACCESS, read the ACM policy on human-subjects statements and write the cover letter paragraph before submission (see "cannot fix" below).
- Effort: 3-4 h. Timescale (a).
- Risk: link in CALE-AI breaks anonymity. NOT: write "exempt", "approved", or "not human-subjects research" unless a body says so.

## Weaknesses that cannot be fixed without IRB, and the cheapest framing
| Weakness | Framing that costs least |
|---|---|
| No data from AAC users on benefit, taps, cost, approval behaviour, or whether the cue is usable | State once in the body: "materials-level evaluation; no participant study"; present consultants as design review that changed requirements (table), never as evidence; state predictions as falsifiable hypotheses (CALE-AI Sec. 7) for those who can run the study. |
| Real AAC messages and access-method cost (dwell, grid, scanning) | "Constructed and crowd-written; cost is per tap, not time"; give the sensitivity of the price to the prior (action 7). |
| Whether writers would accept drafts in use (writers here judged post hoc) | Report the 61% rejection as a finding about the metric ("necessary not sufficient") and as why the paper evaluates commitments, not usefulness. |
| Listener study with real partners, longitudinal or consequence | Listeners are non-AAC adults judging text; claim comprehension of materials only (as now). Round 2 narrows, does not close. |
| TACCESS expectation of human-subject statement | Be factual: annotators and expert raters judged study materials; some chose keywords and wrote pairs under CC BY 4.0; no personal data; no institutional determination sought. Offer the editor the evidence and expect possible desk-risk; a journal with a human-subject focus may prefer a technical/methods article type. Do not substitute a made-up exemption. |
| hw1 writers (6-7 per contrast) cannot be widened | Claim direction and consistency (all writer means positive), exact sign-flip p floor; do not run further writer-generation sessions: that would be closer to participant research. |

## Do-not list (across all actions)
- No new tasks where people supply their own behaviour, opinions or experiences (surveys, think-alouds, preference ratings of the system by annotators about themselves).
- No claim of AAC-user benefit, IRB approval/exemption, "pre-registered", or machine agreement as human validation.
- No hand-typed numbers; every new result gets a PLAN.md written and git-timestamped before the run, and a macro.
- No retrying until a favourable rate appears; report every run.

## Expected movement
SE4All: 6.5 -> about 7.5 if actions 1-4 land by Nov 20 (readability, blind faults, NLI baseline, defect traces); 5-6 add credibility at camera-ready. CALE-AI: 6 -> 6.5-7 mostly from 1, 5, 8. Journal: items 5, 7, 8, 9 are the load-bearing ones; without people it is a strong measurement paper, not an intervention paper, and should be scoped as such.
