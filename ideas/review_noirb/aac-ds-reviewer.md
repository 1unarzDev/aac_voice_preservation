# No-IRB plan: AAC / disability-studies reviewer

Read: caleai and se4all PDFs (text), journal OUTLINE.md, LOOP_BRIEF, claims ledger C44-C81, caleai Sections 7-8 and the ethics paragraph. I did not re-run any analysis. Timescales: (a) before Nov 20 AoE, (b) camera-ready/rebuttal, (c) TACCESS by mid-Dec and revision. Rank = rating gain x feasibility.

Standing view of the papers: the evidence is unusually well controlled for a workshop paper (frozen rules, human checks of judge, detector, mutants, listener study). What caps my score is (i) density: the abstracts carry 20+ numbers and 4 nested caveats, so the one finding I should remember is hard to find; (ii) venue fit for CALE-AI (asks for human effects; the human arm is promissory); (iii) "nothing about us without us": two consultants and a positionality limitation are the only AAC-community voice; (iv) one model family as generator, judge and arbiter.

## The 10 actions

### 1. Rewrite the three abstracts and introductions around one headline (a; all papers)
- Do: one headline result per paper, in one sentence, with one number. CALE-AI: cue restoration (+37.5 pp, 10 writers all positive) plus listener +20 pp (8% to 28%). SE4All: "oracle tested like software: 193/196 circular, 70.7% independent, 58/58 after tests, and what it cannot see". Then at most three supporting numbers. Move the rest (arbiter 77.4%, 87.8/92.3 precision/recall, 31.41 vs 31.65, first-round 35.3) into the body or a table. One limitation clause, not four. Cut the "(descriptive; the interval includes zero)" / "(exploratory ...)" parentheticals into one shared status sentence ("pooled round decided after seeing it; exploratory").
- Why: Clarity is my lowest-scoring criterion (6) and the thing that makes a skim reviewer misread the contribution. The Tone rule also asks for this. Numbers already exist as macros, so it is pure editing.
- Effort: 3-4 h per paper, no compute. Re-measure page limit by pdftotext (where References falls).
- Risks: dropping a number a prior reviewer liked; keep every dropped number in the body. Keep -42 [-99, 7] reversal difference labelled as not confirmed.
- NOT: do not add new claims while shortening; do not replace precise status words ("exploratory", "frozen") with vague ones; no new hand-typed numbers.

### 2. Held-out fault injection for the harness (a; SE4All, then journal)
- Do: the 58/58 kill rate is on a list the authors wrote and then fixed for, which the paper calls "a coverage score, not an independent estimate". Get an independent list: give a Claude subagent and a GPT-family model only the source of src/ (not the tests, not the existing 58) and ask each for 30 plausible single-site faults in the same 8 classes; apply, run the unchanged test suite, report kill rate on this unseen list, plus the survivors. Declare the protocol in analysis/seeded_faults/PLAN2.md before running and commit a timestamp.
- Why: this is the SE4All thesis ("testing the test oracle"). An unseen-fault kill rate (even 70-80%) is a more credible result than 58/58 and reviewers in an SE venue will value the surviving mutants as findings.
- Effort: 3-5 h, CPU, about 60 API calls. Timescale a if the run is automated; else b.
- Risks: a low rate looks bad; report it as the honest estimate beside 58/58 (measured-after-fix vs unseen).
- NOT: do not fix survivors and then re-report the same list as clean; fix them after, label the second pass "after fixes".

### 3. Re-aim CALE-AI at what the venue asks, using the human evidence we do have (a)
- Do: make the listener study, writer coverage (+30 pp), and the judge/detector human checks the "human-effect" section; compress the MRT table (Table 3, "about 125 users") to 4 lines inside Section 7 and label it "design a collaborator could run; no data". Say in the abstract "materials judged by adults; AAC-user effects are predicted, not measured". Retitle from the field-level claim ("Gains Hide Failures") to what is shown, e.g. "A Ledger Evaluation of a Commitment Guard ...", as J5 already asked.
- Why: Venue fit was 5. Reviewers there penalise a promised human trial that cannot happen; presenting it as testable predictions (H1-H3) is within the method/negative-result scope and costs little.
- Effort: 3 h. Timescale a.
- Risks: appearing to oversell the listener study; keep "not AAC partners" in the first mention.
- NOT: no sample-size or power calculation that implies the study is planned with this team; no "we will run".

### 4. Non-GPT, larger generator replication of the headline contrasts (a if small, b if full)
- Do: use Claude subagents (and limited Gemini calls) as generators on the 127 hw1+hw2 speech-act families x {bare, chip1, noncrit} (about 380 generations) and on polarity P3 bare (7 writers' pairs). Label with the existing J1 judge plus the blind Claude re-label (C77 protocol, already validated at 94% vs humans). Pre-declare the rule: "replicates if sign matches and chip gain >= +15 pp".
- Why: the four-model, one-family limit (C53) and "extractor shares a family with one generator" are repeated in every limitations paragraph. A frontier non-GPT generator showing the same direction converts a limitation into a result, and raises Soundness and Significance.
- Effort: 4-6 h, no GPU, one-off API cost; Claude subagent calls are the main cost (do concurrency <= 8 judge).
- Risks: Claude may follow the cue almost perfectly (ceiling) or default less affirmatively; both are reportable. Subagent outputs are not temperature controlled; say so.
- NOT: do not call Claude-as-generator and Claude-as-labeler one independent check; use the GPT judge for the Claude generations and the Claude re-label only for the GPT ones.

### 5. Close the lexicon-blind oracle gap with a pre-declared judge combination (a/b; SE4All)
- Do: the independent mutant test shows 58.5% recall when the lexicon cannot see the change. Test, on a split (tune on 50 confirmed mutants, hold out 25 plus controls; or 2-fold), whether a union rule (GPT judge OR a Claude re-label on the same unit) raises lexicon-blind recall without raising false alarms above 46 controls' 4/46. Declare rule and split before looking.
- Why: it turns the main oracle weakness into an improvement with an honest cross-validated number; SE reviewers like "oracle got better and here is the cost".
- Effort: 2-3 h, CPU plus about 200 labelling calls.
- Risks: small n (25 holdout) gives wide intervals; report them. Do not choose the rule after seeing the holdout.
- NOT: do not swap the production oracle and claim all earlier numbers; if the rule changes, state earlier results are with the old oracle.

### 6. Consultant member-check and a small design-feedback round (a for member-check, b/c for mockups)
- Do: send each consultant the exact paragraph and Table 4 (requirements and what changed) and ask: is this a fair paraphrase; anything misrepresented; anything missing. Record yes/changes, paraphrase only. Second, optionally, show 3-4 static mockups of approval-gated draft sets (one tap chip, 3 drafts) and ask design questions only (what would be unsafe, what is missing).
- Why: the biggest disability-studies critique is the missing AAC voice; a member-checked requirements table is the strongest honest answer and it is what TACCESS reviewers look for. It also supports the claim that cues belong to the person.
- Effort: about 45 min per consultant, paid; 2 h of writing.
- Risks: crossing into a study. Keep it as design feedback: no questions about their own experience, preference, burden or benefit; no quotations beyond paraphrase; no counts.
- NOT: do not ask them to rate outputs, rank designs "for them", or say anything "AAC users prefer"; do not describe them as a sample.

### 7. Inference hardening that costs only CPU (a; all papers)
- Do: (a) crossed listener x item bootstrap for the listener study (currently item-level, "unadjusted"); (b) leave-one-annotator-out for every 20-annotator result (listener, Parts 20, 21, 28, 29); (c) report the effect of annotators also being writers (writer-rated own outputs); (d) clean-room rebuild: fresh clone, one command regenerates all macros, record the checksum list in the artifact appendix.
- Why: small-n human results are where reviewers probe first. Doing it ourselves turns "unadjusted CI" into a stated robustness. Reproducibility earns SE4All artifact credit.
- Effort: 4-6 h, CPU only.
- Risks: the -42 [-99, 7] reversal difference may widen; it is already labelled not confirmed.
- NOT: no new multiplicity chasing; do not replace pre-specified intervals with the new ones without saying both.

### 8. Translate per-1,000 prices to realistic exposure using public corpora (b/c; journal)
- Do: for 3-4 public text sources (AACText, DailyDialog, a Switchboard/telephone subset, any AAC-like phrase set already in lit/), use the T2 detector (validated by Part 21, 200/200) to estimate prevalence of negated statements, requests, politeness-bearing messages, then multiply by the measured bare/chip reversal rates to get expected silent reversals per 1,000 realistic messages with a range across corpora.
- Why: it answers "so what?" (Significance) without users and is the honest bridge from stored-text rates to what a deployment would face. T2 already gives 2.7% for one corpus; adding sources shows how corpus-dependent it is.
- Effort: 1-2 days, CPU plus detector runs.
- Risks: public corpora are not AAC users' speech; say "exposure under assumed message mixes", not "rate users experience".
- NOT: never present the result as an incidence in AAC use.

### 9. Restructure and cut the TACCESS draft (c)
- Do: 35 pages and 23.5k words. One thesis spine: (1) harness, (2) the cue works (cross-family, controls), (3) judge-correct is not enough (waterfall, listener), (4) design requirements. Move the guard, repair audit, frontier ask-policy null, multilingual and per-model tables to appendices or supplement; target 24-26 pages. Fill or drop `\slot` boxes; state in one place which numbers are in the workshop papers.
- Why: TACCESS reviewers weigh a clear contribution and readable argument; density currently hides the novelty. This is also where a revision can answer reviewers cheaply.
- Effort: 2-3 days over the window.
- Risks: dropping content reviewers later want; keep a supplement.
- NOT: no new experiments in the draft after the deadline freeze, no concurrent-work placeholders left unverified.

### 10. Two small SLP tasks that give "unclear" and "rejected" clinical meaning (b/c; journal, camera-ready)
- Do: ask the 2 anonymous SLPs (about 40 min each) to rate (i) 30 bare listener outputs labelled "unclear" for how costly the partner repair would be, and (ii) 30 writer-rejected judge-correct outputs for seriousness by rejection reason (compression, changed role, added content). Pre-state the rule; report as expert review (n=2), no inferential statistics beyond agreement.
- Why: the best finding in the listener study is that bare output is mostly unclear, not reversed (86.7%); a clinician's cost rating is the only no-users handle on whether that matters. It also weights the "what failure matters" argument.
- Effort: 2 people x 40 min; 2 h analysis.
- Risks: SLPs may rate unclear as harmless; that is a finding worth reporting and moves effort from rewrite to approval gating.
- NOT: do not ask SLPs about real clients; do not state "clinically validated".

## Weaknesses that cannot be fixed without IRB, and how to frame them
1. AAC-user benefit, agency, effort, trust, abandonment (H3 trial). Frame as predictions with falsifiers; claim only a technical layer plus materials-level comprehension (cite Frisch et al. 2026 for the three-layer evaluation). One sentence in the abstract; one limitations paragraph; no hedging elsewhere.
2. AAC communication partners. Listeners are adult non-partners; say "comprehension of materials" in every mention, never "partner".
3. Real AAC message distributions and use contexts. Say AACText is crowd fiction; use item 8 for sensitivity, label it exposure under assumed mixes.
4. Community voice beyond two consultants. Member-check (item 6), say it is design review not representation, state positionality once and invite a clinical/AAC-community partner as the stated next step.
5. Ethics exposure: "no institutional review determination sought" is the line a reviewer or editor is most likely to act on, and TACCESS or the ACM may consider listener and annotator tasks human-subjects work. Keep the paragraph exactly canonical (non-author adults, reimbursed, no personal data, materials judged); do not use "exempt", "not human subjects research" or "approved". Be ready for an editor query by having the annotation protocol, consent text and data-minimisation facts in one supplement section. If an editor requires a determination, that is a decision for the authors, outside this plan.

## Order of work for Nov 18-20
Items 1 and 3 first (editing only, highest gain per hour), then 7 (CPU, overnight), 2 and 5 only if automation runs before the deadline; 4 and 6 start now and land in (b); 8-10 are (c).
