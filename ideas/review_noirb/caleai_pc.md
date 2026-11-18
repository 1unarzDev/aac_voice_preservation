# CALE-AI PC reviewer: no-IRB improvement plan (2026-11-18)

Role: program-committee reviewer, causal / longitudinal human-effect evaluation of AI. Read: CALE-AI and SE4All PDFs, journal OUTLINE, ledger C44-C81, D-103..D-107.
Current rating from this seat: 6 (weak accept at best). It is a careful ledger paper whose human-effect claims are explicitly absent (no estimand on people), whose lead guard shows a human-judged cost and zero listener benefit, and whose cleanest result (cue) misses its own pre-set 80% line. With the actions below I would go to 7, and to 8 if actions 1-3 land.

Calibration of what a causal/longitudinal reviewer wants: (i) an explicit estimand and identification argument for each contrast, (ii) human-outcome evidence, not only machine labels, (iii) honest handling of heterogeneity and transport, (iv) a credible path to longitudinal evidence. Without IRB, (ii) is limited to materials-judging, so (i), (iii), (iv) must carry more weight.

## Ranked actions (rating gain x feasibility)

### 1. Estimand, identification and chain-of-effects table (replaces prose caveats)
- Do: one half-page table in CALE-AI (and one sentence in SE4All). Rows = each headline contrast (guard joint-pass gain, cue restoration, listener success, listener opposite-action, usability audit). Columns = unit, intervention, comparator, estimand (descriptive stored-text contrast / effect on listener comprehension of materials / excursion effect on people), identification (randomisation-by-construction over items and conditions; listener assignment; what is NOT identified), link to the next row. Add a "chain": cue supply q = 73.6% [59.7, 86.1] x machine restoration x listener success +20.0 = a bounded projection for the person-level effect, using Manski-style worst/best bounds for the unmeasured link (writer-to-AAC-user transfer).
- Why: this is the single thing this seat scores. It converts the "no estimand for people" disclaimer into a stated, bounded structure and shows exactly what a future study must measure. Turns the weakness into a method contribution.
- Effort: 6-8 h writing plus 1-2 h CPU (bounds from stored files, macros via make_macros.py). 0 people-minutes.
- Timescale: (a) fits before Nov 20 if the readability pass frees ~12 lines; otherwise (b) and in the journal (c).
- Risks: reads as over-formal if long; keep to 10 rows maximum. Bounds must be labelled projection, not evidence.
- NOT: do not write "causal effect on AAC users" or multiply to a single headline person-level number; do not present the projection with a point CI.

### 2. Re-analyse the listener study with crossed random effects and show the reversal result honestly (CPU only)
- Do: items x listeners crossed mixed model (or two-way cluster bootstrap / cluster-robust), for Q1 success, Q2 opposite action and received reversal; report the minimum detectable difference for reversal (it includes zero: -42 [-99, +7] per 1,000). State Q2 (opposite action 22.5% to 1.3%, -21.3 [-31.3, -11.6]) as the consequence outcome and reversal as the frozen primary that was not confirmed. Add the "unclear 87% to 71%" finding as what bare inputs actually do to a listener (not reversal, uncertainty), which is the more accurate lead.
- Why: the listener study is the only human-effect evidence; a PC member will test its clustering and multiplicity. A correct dependence model preempts the main attack and the plan said mixed model "not run".
- Effort: 3-5 h CPU, no new data. Timescale (a).
- Risks: the mixed model may widen intervals; report whichever it gives, labelled post hoc vs frozen. Never swap the primary after the fact.
- NOT: do not drop the unconfirmed reversal row; do not call listeners AAC partners.

### 3. Second listener round, new items, same frozen analysis (confirmatory)
- Do: draw 120 new intended messages with the Part 28 plan (fresh seed, frozen before draw), 20 annotators x ~25 min, same scoring script. Include guard-changed outputs and plain-word arm on all items (fills the 18-item gap). Declare the reversal difference and Q2 as confirmatory, with the interval needed for a pass.
- Why: turns an exploratory-frozen human result into a replication; the guard=bare finding gets a proper test; most valuable human-evidence upgrade available without IRB.
- Effort: ~1 day to build (materials, key, hashing), 500 annotator-minutes (20 x 25), ~$0 compute beyond generation. Timescale (b)/(c): include in camera-ready if returned, else the TACCESS revision. Not before Nov 20.
- Risks: reuse of the same 20 classmates (learning, fatigue); keep different items and say so. Same ethical framing as Part 28 (judging materials, no personal data).
- NOT: do not recruit outside the class cohort; do not add demographics, comprehension-in-use or "how would you feel" questions; do not describe it as a user or participant study.

### 4. Frame and fix density now (focused readability pass, in progress)
- Do: abstract to about 150-170 words with 4 numbers (cue +37.5 pp; listener +20 pp and opposite action 22.5% to 1.3%; guard +9.83 pp with the usability cost; 73.8% vs 80% line stated once). Secondary stats (kappas, arbiter, coverage, multilingual) to tables. Move the Figure 1 caption's rule text to body. Remove repeated "descriptive / exploratory / post hoc" tags where the table's column already says it.
- Why: as a reviewer I lose the lead finding in the abstract; the paper currently reads as caveat-dense, which hides real strengths. Raises clarity score and the reviewer's trust in the claims that matter.
- Effort: ~4 h for both papers; in the running workflow. Timescale (a).
- Risks: cutting a caveat that an honesty rule requires (listener not AAC partners, not independent Claude relabel, audit underpowered). Keep each once.
- NOT: do not lead with limitations or end the abstract on one (tone rule); do not add new numbers by hand.

### 5. Item-matched, larger repair-usability audit (Part 17 round 2, annotators)
- Do: re-run the usability audit with controls matched to each repaired item (same family and model, never-failed neighbour), 3 raters per text, n of about 100 repairs + 100 matched controls, frozen rule as before. Tests the deployment clause that is currently "unresolved" (-13.3 [-27.6, +1.5]) and removes the item-difficulty confound.
- Why: the guard is the "lead"; its human cost is the paper's central honesty and is underpowered. A matched, larger audit either resolves it or yields a cleaner finding. Power target: detect -10 with 80%.
- Effort: 1 day prep, ~20 annotators x 30 min. Timescale (b)/(c).
- Risks: could confirm a real cost (fine; the paper's thesis is that gains hide costs; this strengthens it). Matching reduces usable pairs.
- NOT: do not pool with the old audit to rescue the interval; do not change the frozen rule.

### 6. Capability-scaling machine experiment (heterogeneity / transport, API compute)
- Do: add the remaining GPT tiers available (luna/sol/terra/astra tiers) plus one larger open model to the speech-act and polarity bare / chip / guard arms; plot gain and reversal rate against a capability proxy (tier, parameters). Current guard gain is +0.85 (API model) to +19.0 (Gemma): pooled gain is mostly weak models.
- Why: a causal reviewer asks whether the effect transports to the next models. A trend (or its flattening) is the cheapest honest answer, and it targets the "will this matter" question.
- Effort: ~1 day pipeline, ~6-10 h API (concurrency 12 generation, 8 judge); no GPU needed except local models (lock). People-minutes 0. Timescale (b).
- Risks: judge is same family (gpt-6.1-sol); label as such; use the Claude re-label on a sample. Tier sizes are undocumented, so use ordinal rank only.
- NOT: do not claim a scaling law; do not pool tiers with the four primary models in the headline.

### 7. Longitudinal design as a deliverable: power-calibrated, registered-report-style protocol plus a simulated exposure model
- Do: replace the prose Section 7 with (a) a protocol for the excursion/longitudinal study (units, schedule, outcomes: silent-reversal exposure per 1,000 messages, repair burden, approval rate), (b) a simulation using the measured rates (reversals 50 vs 8 per 1,000 listener-received; cue supply q 0.74; approval-gate catch rate as an unknown with a sensitivity grid) giving expected reversal exposure over N messages and the sample size a future IRB-approved study needs. Mark as projection; code and seeds in repo.
- Why: the workshop is about longitudinal human effects; the paper cannot supply them, so supplying the credible design and power numbers is what a reviewer rewards. Needs no people.
- Effort: ~1 day CPU/writing. Timescale (a) short form, (c) full in TACCESS.
- Risks: simulation can look like invented evidence; every parameter must be a macro or an explicit sensitivity range, results labelled "projection".
- NOT: do not report simulated outcomes as results; do not imply a study is planned or approved.

### 8. Independent-family judge replication of the guard headline
- Do: extend the Claude re-label (currently P1 only, +37.9 vs GPT +37.5) to the guard confirmation set (strict-check and joint pass, 9.83 pp) and the resample baselines; use Claude subagents blind to condition, with a limited Gemini pass on a stratified subset. Report the delta and the disagreement set.
- Why: the machine-label gains are judged by one family and the extractor shares a family with one generator; this is the standing threat to the "gain" in the ledger.
- Effort: ~1 day, Claude subagent budget for ~3-5k units; 0 annotators. Timescale (b).
- Risks: Claude also arbiter/assisted writing (state: second family, not independent). Disagreements concentrate in time_quantity; keep the stratification.
- NOT: do not call it human validation; do not replace the GPT numbers.

### 9. SLP and design-consultant calibration of what the listener outcomes mean (cheap experts)
- Do: ask the 2 SLPs to rate severity of the listener study's opposite-action outcomes (Q2) and the "unclear" outcome on ~40 items (about 30 min each); use consultants only for design feedback (the member-check replies due Nov 19 18:00; quote nothing that has not been returned).
- Why: gives a severity weighting to the one human-effect outcome (opposite action) and external validity for materials, from the only domain experts available.
- Effort: ~1 h per SLP, 30 min per consultant. Timescale (b).
- Risks: n=2, so report as expert review; consultants' acknowledgement must wait for their reply.
- NOT: do not call consultants a sample or an effect estimate; no new surveys about their own experience.

### 10. Power and sensitivity appendix for every human-judged endpoint (CPU)
- Do: for audit, listener, coverage, SLP, part 21-24 checks, minimum detectable effect at 80% power and what interval the data can exclude; mark each endpoint confirmatory / frozen-exploratory / post hoc in one column.
- Why: replaces scattered "underpowered" sentences with one table; a reviewer can then calibrate each claim; it is also the factual base for action 7.
- Effort: 3 h CPU. Timescale (a)/(b).
- Risks: low. NOT: do not retro-fit "observed power".

## Weaknesses that cannot be fixed without IRB, and how to frame them cheaply
1. No effect on AAC users, no longitudinal use, no real communication consequences. Frame once, in Limitations and the estimand table: "results are changes in stored text and judgments of materials by adult annotators; the person-level effect is a stated, bounded, untested link" and give the protocol and power numbers (actions 1, 7). This costs less than hedging in every section.
2. Listeners are adult classmates, not AAC communication partners; writers are not AAC users, so "intended message" is a non-AAC writer's intent. Say so in the listener paragraph and glossary; do not generalise to partners or to AAC users.
3. Consultants and SLPs are n=2 each: report as expert review and design input, with changes made, not as estimates.
4. Anything about how people actually select cues (cue supply q) beyond the 73.6% annotator-measured proxy. Frame as the pre-declared 80% line missed and as the open parameter in the projection.
5. Ethical exposure: several existing parts (writers rating "is this what you meant", coverage, keyword typing) sit near behavioural / self-report studies. Keep the canonical ethics paragraph exactly; add no new parts of this kind; label them as annotation of materials the annotators authored; accept that a reviewer may still query it and answer in rebuttal with the paragraph and the no-personal-data statement. The user should decide whether any of Parts 18, 26/27 should be cut from the journal if an editor asks.

## Order of work
Before Nov 20: 4 (in progress), 2, 1 (short form), 10, 7 short form. Camera-ready/rebuttal: 3 prepared, 5, 8, 9, 6. TACCESS mid-Dec: 1 and 7 full, 2, 6, 8, plus 3/5 if returns land; revision: 3 and 5 results.
