# Human annotation program: all components

This document covers every human task in the study. For each task it says what it is for, what it strengthens in the
papers, how many annotators it needs and how long it takes, how blinding works, and what the annotator hands back.
Annotators need only `annotation_package.zip` and the instructions for their task. Coordinators also use the
"Coordinator" sections.

## Two-stage plan for 20 annotators (P01-P20), plus an optional Stage 3

This section replaces the older allocation tables (section C and the per-task "Recommended" lines). Those are kept
below for reference but are **superseded**.

**Sources.**
- The plan comes from `src/make_assignments.py --stage 1 --annotators P01..P20` and is frozen in
  `annotation/assignments/plan.json`.
- Assignment lists are in `annotation/assignments/stage{1,2,3}.csv`; per-person sheets are in
  `annotation_package/assignments/<ID>.md` (Stage 1), `<ID>_stage2.md` and `<ID>_stage3.md`.
- The coordinator hand-out is `HANDOUT.md`. The commands between stages are in `annotation/COORDINATOR_STEPS.md`
  (private).

**Timeline**

| Stage | Dates | What | Person-hours |
|---|---|---|---|
| 1 | Nov 2-4 (all returned Nov 1) | Part 9 keyword choice, then audits (Parts 4, 11, 5, 6; Part 10; Parts 1-3), then Part 7 writing | 65.2 h (165-220 min each) |
| between | Nov 1 | collect pairs, fill check files, elicitation generation + judging, draw Part 12 | compute only |
| 2 | Nov 1 (due Nov 1, 23:59) | Part 8: 3 check files of 30 pairs each; Part 12 (4 people) | 28.0 h (66 min; Part 12 coders 156 min) |
| between | Nov 1 (as Stage 2 returns) | score checks, route tie-breaks, hw1 generation + judging, draw Part 13 | compute only |
| 3 (optional) | Nov 1 (due Nov 1, 23:59) | Part 13 (3 people, ~90 min), Part 14 tie-breaks (6 people, ~30 min) | 7.5 h |
| 4 (optional, proposed) | Nov 2-5 | Part 15 speech-act writing (4), Part 16 checks (6), Part 17 repair audit (6), Part 18 writer intent (20) | ~12 h |

**Deadlines.**
- SE4All @ ICSE'27: evidence freeze Nov 10, submission Nov 13 AoE. Stages 1-2 feed it, and Stage 3 only if it is
  back on Nov 9.
- CALE-AI @ AAAI'27: evidence freeze Nov 16, deadline Nov 20 (internal target Nov 19). It gets all three stages.

**Why this order.**
- **Elicitation comes first.** It must happen while annotators are naive. Before typing keywords, they have not
  seen any model output, test pair, codebook, or the study's dimensions, so nothing primes them to type "not",
  "please" or "?". Annotators who saw the minimal pairs or the codebook first would over-report the very cues
  whose loss Part 9 measures.
- **Audits come in the middle.** They are independent of each other.
- **Writing comes last.** It requires reading the six dimension definitions and writing deliberate minimal
  contrasts. That is the strongest priming, and it is harmless only once elicitation and the label tasks are done.
- **Stage 2 needs Stage 1 data.** It checks and labels what Stage 1 produced.

**Stage 1 design (checked in code).**
- **Part 9:** 48 sessions (16 sets x 3 Latin-square replicates). Each person gets 2-3 sessions and never two
  replicates of one set; every set is done 3 times.
- **Part 12 coders' sessions:** P03, P08, P13 and P19 hold the paired replicates of sets s01-s04. The Part 12
  sample therefore excludes every message they saw and every keyword set they typed.
- **Audits:** Part 10 (P07, P09, P11) and Parts 1-3 (P02, P10, P14) are the only audit for those six people.
- **Audit counts:** Parts 4/11/5/6 reach 14/14/12/12 annotators against 10/10/6/6 required. The extra coders come
  from topping everyone else up to at least 60 audit minutes (40 for the Part 12 coders, whose Stage 2 is longer).
- **Part 7:** 2 sessions x 15 pairs per person in two different dimensions. That is 600 pairs, with 7/7/6/6/7/7
  writers for polarity, speech act, politeness, certainty, agent and time. Topic rotations follow
  `make_writer_links.py`.

**Stage 2 design (fixed now; files filled after Stage 1).**
- **Checker graph.** Each writer's 30 pairs form 6 chunks of 5. Chunk c, replica k goes to the checker at
  ring offset OFF[c][k], where OFF is a partition of 1-18 that spreads co-checker pairs.
- **Result.** Every pair gets 3 distinct checkers and never its writer. Everyone checks 18 chunks = 90 pairs in
  `stage2/<ID>_check_1..3.json`.
- **Fallbacks for short or missing returns** are in COORDINATOR_STEPS.md: short returns shrink files; a writer who
  returns nothing frees 18 slots, and if that person is also out, their own checks move one-to-one into those slots.
- **Part 12.** `stage2/part12_gold_elic.json` comes from `src/make_gold_elic.py`: about 150 outputs on human
  keyword inputs, drawn as for Part 10, with neutral ids and a private key `annotation/gold_key_elic.csv`.

**Stage 3 (optional; people chosen now: lightest Stage 1+2 load, Part 12 coders excluded).**
- **Part 13** (P04, P15, P20). `stage3/part13_gold_hw.json` comes from `src/make_gold_hw.py`: about 150 outputs
  of run hw1 on the checked pairs. It excludes pairs the coders wrote or checked; the key is
  `annotation/gold_key_hw.csv`.
- **Part 14** (P01, P06, P12, P16, P17, P18). `stage3/<ID>_tiebreak.json` holds a 4th independent check for pairs
  missing a check (priority 1) and for 2-1 splits (priority 2). A tie-breaker is never the writer or a planned or
  actual checker. Each tie-breaker gets at most 40 pairs and is chosen by lowest load. A file may be empty.
- **Reserves** are listed in `annotation/assignments/stage3_people.json`.

**Compute between stages** (request counts; ratios measured on r2c1/wb1).
- **Measured ratios:**
  - P0 gives about 0.65-0.71 judged units per request.
  - S3 gives about 0.36, because samples repeat.
  - The judge needs about 0.15 calls per unit (4 calls per batch of 25) plus about 0.6% arbiter units.
  - codex-lb sustained about 46 calls/min for gpt-6.1-terra and 48 for the judge.

| Run | Design | Requests (terra on codex-lb) | Judge calls | codex-lb time |
|---|---|---|---|---|
| elic1 (after Stage 1) | **recommended:** P0 + S3, 3 human channels + POS-cap4, 4 models | <= 38,400 (9,600) | ~2,600 | ~4.5 h |
| elic1 | full P0/P2/S3 | <= 48,000 (12,000) | ~6,600 | ~6.6 h |
| hw1 (after Stage 2) | **recommended:** P0, 5 channels, 4 models, ~450 kept pairs (600 max) | ~14,400 (3,600); max 19,200 (4,800) | ~1,600; max ~2,100 | ~1.8 h |
| hw1 | full P0/P2/S3 | ~72,000 (18,000) | ~7,800 | ~9 h |

- **Recommended design.** P0 on all 5 channels for the human-written pairs. P0 and S3 on bare input (the human
  keyword channels) for the elicited keywords, with the POS-cap4 baseline under the same prompts. Together that is
  about 13,200 terra requests and 4,200 judge calls, roughly 6 h of codex-lb time spread over the two windows.
- **Reading the counts.** Elicitation counts are upper bounds: identical keyword sets are rendered once.
- **Local models.** The local models need about 1 h of GPU time in total, run one model at a time under the lock.
- **If codex-lb is congested,** run S3 only on the local models and keep terra at P0. That cuts elic1 terra
  requests to 2,400.

**Stage 4 (optional top-up; proposed Nov 1, runs Nov 2-5 if annotators are available).** Stages 1-3 left two
gaps that more human work can close before the SE4All freeze (Nov 10):

1. **Part 15: more speech-act pairs (writing).** Speech act has the fewest kept pairs (69 of the 150 target),
   and it carries the study's main test (the speech-act chip). **4 writers who have not written speech-act pairs
   before** each write 15 new pairs in `write_pairs.html` (speech act only, about 25 min). That gives about 60 new
   candidates and about 125 kept in total. Same rules as Part 7: your own sentences, no copying or adapting other
   people's sentences, and no AI tools.
2. **Part 16: blind checks of the new pairs.** Same task and tool as Part 8 (`check_pairs.html`). Every new pair
   gets 3 checkers, never its writer. About 6 people check 30 pairs each (about 22 min).
3. **Part 17: larger repair audit (new sentences).** Same task and tool as Part 4, on new sentences that were not in
   Parts 4 or 11: 60 repaired outputs and 60 unrepaired controls, 3 independent raters per sentence. Raters
   who did **not** do Parts 4 or 11 (P02, P07, P09, P10, P11, P14) rate 60 sentences each (about 35 min).
   Part 4 had 20+20 sentences, so its repaired-vs-control gap has a wide interval. Part 17 triples the items.
4. **Part 18 (optional): did it say what you meant?** Each writer sees 10 model sentences generated from
   their **own** pairs and marks whether each one says what they meant in version A or version B, says something
   else, or is unclear (about 15 min). Writers are the people who know the intended meaning, so this is the
   closest check to an intended-speaker judgment this program can make. It is **not** a study with AAC users.

Order: Part 18 can start at once (outputs exist). Part 17 needs its sample drawn (no new generation). Part 16
follows Part 15 returns; generation and judging of the new pairs follow Part 16. Task sheets will be
`assignments/<ID>_stage4.md` once the coordinator confirms who is available.

**After Stage 4.** No further annotation is needed for the SE4All and CALE-AI papers. The next step is a separate
study with AAC users. It needs its own ethics determination (IRB or equivalent) before anyone is recruited, and it
is outside this program.

---

**Deadlines that shape priorities**
- SE4All evidence freeze: **Nov 10** (submission Nov 13 AoE).
- CALE-AI evidence freeze: **Nov 16** (submission Nov 19).
- Anything returned after a freeze still strengthens later versions, but it won't be in that paper.

---

## 0. Rules for every task

1. **Independence.** Each annotator works alone. Annotators do not discuss items until everyone has submitted, and do not use AI tools or search engines.
2. **Isolation.** Use only the files in the package. The public repository contains model labels and keys, so annotators must not browse it.
3. **IDs.** Each annotator gets a stable ID (e.g. `P01`…`P30`). The same ID is used for every task, and no other identifying data is collected.
4. **Time.** Coordinators record the start and end time of each session per annotator. The tools also record per-item times.
5. **Returns.** Return each CSV unchanged, named `<task>_<ID>.csv`. Coordinators commit them to the folder listed for each task.
6. **Reimbursement and consent.** Annotators are told the purpose (checking how AI writing tools change meaning), that their work is anonymous, and that they may stop at any time. Reimbursement is recorded per task.
7. **Blinding.** Annotators never see which system produced a sentence, which condition it came from, or what the "right" answer is.

---

## A. Tasks on existing data (tools already built)

### A1. Label extraction: Parts 1–3 (`annotate.html` with `part1_core.json`, `part2_extraA.json`, `part3_extraB.json`)

**What:** for each AI-generated sentence, label its polarity, speech act, agent, certainty, politeness, the family's
critical value, and (shown last) whether it adds content beyond the typed keywords.

**Items:**

| Part | Items | Contents | Time |
|---|---|---|---|
| Part 1 | 100 | 76 probability-sampled outputs + 24 challenge sentences | 45–60 min |
| Part 2 | 44 | probability-sampled outputs | 20–30 min |
| Part 3 | 43 | probability-sampled outputs | 20–30 min |

**Status:**
- Two annotators completed Part 1, plus one extra part each.
- Judge-vs-human κ is 0.90–0.98 across all seven fields; human α is 0.95–1.00.

**What more annotators add:**
- **3–5 annotators on every item of Parts 1–3:**
  - majority-vote gold and an adjudication-free reference;
  - reliability estimated from more than two coders;
  - the extra parts become double- or triple-coded instead of single-coded.
- This answers the reviewer point "only two annotators" and removes the plurality-with-ties limitation. It strengthens the judge validation that **both** papers rest on, but only modestly, because agreement is already very high.

**Recommended:** **3 additional annotators** on Parts 1–3. That is about 1.5–2 h each.

**Coordinator:**
- Returns go in `annotation/returns/`.
- Scoring: `src/score_gold.py --run main1 --human annotation/returns/*.csv` (the package uses neutral challenge IDs, which are mapped via `annotation/package_challenge_id_map.csv`).

### A2. Repair audit: Part 4 (`repair_audit.html`, self-contained, 40 sentences)

**What it checks:**
- **Pass A (blind):** is this a complete, natural sentence a person could send as-is?
- **Pass B (shown the user's input):** does it preserve everything the input specified, and does it add meaning, certainty, politeness or a different speaker?

**Sample:** 20 guard-repaired sentences + 20 unchanged controls (discovery run), frozen hash-ordered with known inclusion probabilities.

**Why it matters:**
- This is the single largest remaining gap. Reviewers said the guard's "repairs" are scored by a partial checker, and some passing repairs are not real sentences ("Ask you to wear headphones.").
- A usable-repair rate turns CALE-AI's headline from "scored predicate repair" into "usable repair", or bounds it honestly.

**Recommended:** **≥5 annotators**, each doing all 40 items (15–20 min each).

**Coordinator:**
- Returns go in `annotation/returns_repair/`.
- Scoring: `src/score_repair_audit.py`.

### A3. W-C source check: Part 5 (`wc_source_check.html`, 20 confirmation families)

**What:** for each minimal pair (two source sentences plus their keywords), the annotator answers three questions:
- What is each sentence's value on the tested dimension?
- Could the keywords mean either sentence?
- Do the two sentences differ only on that dimension?

**Why:** independent human validation of the confirmatory items, which so far have been checked only by the authoring pipeline and an automated verifier. It strengthens the "confirmed on 240 families" claim in SE4All.

**Recommended:** **≥3 annotators** (about 15 min each).

**Coordinator:**
- Returns go in `annotation/returns_wc/`.
- Scoring: `src/score_wc_source_check.py`.

### A4. Corpus check: Part 6 (`wb_corpus_check.html`, 20 real AACText messages)

**What:**
- **Pass 1** shows only the compressed keywords. The annotator marks every plausible reading on five dimensions.
- **Pass 2** shows the full message. The annotator labels what it commits to.

**Why:** human confirmation that real messages become ambiguous after keyword compression. Today that rests on machine coders, who are known to be over-liberal.

**Recommended:** **≥3 annotators** (about 15 min each).

**Coordinator:**
- Returns go in `annotation/returns_wb/`.
- Scoring: `src/score_wb_check.py`.

---

## B. New human-generated data (highest value; all four tools built)

### B1. Human-written minimal pairs ("handwritten data"): Parts 7–8 (`write_pairs.html`, `check_pairs.html`). Built.

**Why this matters most:** all 336 current test families were written by the study's authoring pipeline. A reviewer can
reasonably ask whether the effects are artifacts of how the items were written. Families written independently by many
people:
- remove that objection;
- add genuine diversity of topic and phrasing;
- give a **fully human-authored confirmation set**, which is the strongest possible replication of the headline contrasts (defaults under bare keywords, the speech-act cue effect, politeness added to full input).

**Task (writer):** the annotator writes everyday messages an adult might send, then a minimal partner that differs in one
way only. Each writer is assigned one of three dimensions:
- **polarity:** "I want to go" / "I don't want to go";
- **speech act:** statement / question / request;
- **politeness:** plain / with please, could you or thank you.

The writer also gives the 2–4 keywords both sentences share. A form-based tool checks the format and that the keywords
contain no cue words. About 10 pairs take 20–25 minutes.

**Task (checker):** a *different* annotator verifies each pair blind. This is the same check as A3: the value of each
sentence, whether the keywords could mean either, and whether the pair is minimal. Only pairs passing ≥2 of 3
independent checkers are used.

**Scale:** 20 writers × 10 pairs gives about 200 pairs, and after checking about 150 usable families. That is comparable to the
current confirmation set, from independent authors.

**Pipeline after collection (automated, about 1 day):**
1. Freeze the items.
2. Generate (4 models × 5 channels × P0/P2/S3).
3. Judge.
4. Analyze the same three preregistered contrasts, clustered by writer.

**Deadline:** realistic for CALE-AI (Nov 16 freeze) and for a later version of the HUMANE paper. For SE4All only if the
pairs are returned by about Nov 5 (Stage 1 pairs were returned Nov 1).

**As built (scaled up):** six dimensions (polarity, speech act, politeness, certainty, agent, time), 15 pairs per writer
session (about 35 min), with a per-writer topic rotation over 11 domains (health, sensory, boundaries, work/school, plans,
food, transport, money, relationships, self-advocacy, hobbies). Checks come in blind files of 30 pairs, each file
assigned to 3 checkers who never include a writer of any pair in it. Sized for 600–900 pairs (40–60 writers).

**Coordinator:**
1. Writer links: `python src/make_writer_links.py --writers P01,...` writes `annotation/written/writer_assignment.csv`
   (balanced dimensions, spread rotations, link fragments such as `#dim=agent&rot=4&n=15&id=P07`).
2. Writer returns (`write_pairs_<dim>_<ID>.csv`) go in `annotation/returns_written/`. Then
   `python src/collect_written_pairs.py --checkers-file checkers.txt` re-runs the format checks, derives chips by rule,
   validates, writes the private candidates (`annotation/written/hw_candidates.jsonl`, `rejected.csv`), the quota report
   per dimension × writer (`quota_report.md`), and calls `src/make_check_batches.py`: new blind check files
   `annotation/written/check_files/hwcNNN.json` and the sheet `check_assignment.csv` (+ `_by_checker.csv`). Re-running
   later only batches new pairs; files already sent never change.
3. Check returns (`check_pairs_<file>_<ID>.csv`) go in `annotation/returns_hwcheck/`. Scoring and freezing:
   `python src/score_pair_checks.py [--exclude P07,P09:P12]` keeps a pair only if ≥2 of 3 independent checkers agree with
   both writer values, accept the keywords for both sentences, and judge the pair minimal; self-checks are always dropped.
   Kept families go to `data/items/hw.jsonl` (split `hw`, opt-in in `build_requests.py`; cluster = writer).

### B2. Human keyword elicitation (realistic AAC input): Part 9 (`keyword_elicitation.html` + `elicitation_sets/`). Built.

**Why:** the study currently simulates keyword entry with a rule-based compressor (content words, at most 4). Reviewers
can object that real people would type "not" when it matters. Asking people which keywords they would actually
select measures **how much meaning real keyword choices lose**. This is the ecological version of the "Loss" component,
and it directly tests the papers' claim that missing negation, hedges and politeness are a realistic input condition.

**Task:** shown a full message (AACText messages and B1 sentences), the annotator writes the 2–4 words they would
select on a keyword-based communication device to get that message across, under an effort budget (e.g. "as few words
as you can, as if each word takes a long time to select"). The annotator never sees model output. About 40 messages take 20 min.

**Scale:** 3 annotators per message × 300 messages, so about 45 annotator-sessions of 20 minutes.

**Analysis (automated):**
1. For each message, measure which commitments survive in the human keywords: negation, hedges, politeness, speech-act cues.
2. Feed the human keywords to the 4 models and score them with the existing judge.
3. Compare against the rule-based compressor.

Headline question: *when people choose their own keywords, how often does the model still default to the wrong reading?*

**Deadline:** CALE-AI or later. If returned by about Nov 6, a compact version can go in SE4All.

**As built:** 600 AACText messages (150 simple-random + 150 enriched: 38 hedges, 38 negation, 37 politeness, 37
questions/requests; W-B's 160 and the W-C seeds excluded; inclusion probabilities recorded) in 8 sets of 37–38. Each set
is done by 3 annotators in Latin-square block orders: 24 sessions of about 20 minutes (the "45 sessions" above
overcounted: 300 × 3 / 38 ≈ 24). B1 sentences can be added as a later set.

**Coordinator:**
- Sets and design: `python src/make_elicitation_sets.py [--annotators P01,...]` (already run with placeholder slots
  E01–E24; rerun with real IDs to refresh `annotation/elicitation_assignment.csv`; the draw is fixed by its seed).
  Session files: `annotation_package/elicitation_sets/elic_sNN_rK.json` (item id + text only). Private key:
  `annotation/elicitation_key.jsonl`; manifest `annotation/elicitation_sample.json`.
- Returns (`keyword_elicitation_<file>_<ID>.csv`) go in `annotation/returns_elic/`. Scoring:
  `python src/score_elicitation.py` (cue survival with the s1_cues detectors, agreement between people, comparison with
  POS-cap4; `analysis/elicitation/`). It also writes `data/items/elic.jsonl` and the generation requests
  `runs/requests/elic.jsonl` (human keywords + POS-cap4 baseline, 4 models × P0/P2/S3). It does not generate.

### B3. Expanded gold on new outputs: Part 10 (`annotate.html` with `part10_gold_new.json`, 162 sentences). Built.

**Why:** human label validation (A1) covers the discovery outputs. The confirmation (W-C), composition (W-D) and
guard-transfer outputs are scored by the same judge, but no human has labelled any of them.

**Task:** the same tool and task as A1, on a new part file.

**Sample:** a frozen probability sample of 162 outputs, with known inclusion probabilities:
- 58 from W-C;
- 53 from W-D;
- 51 new guard-transfer outputs (repaired or please-stripped).

It is stratified by run × dimension × judge label, and positives and judge disagreements are oversampled.

**Recommended:** **3 annotators**, about 1.5 h each.

**Deadline:** SE4All if returned by Nov 8, CALE-AI otherwise.

**Coordinator:**
- Returns (`labels_gold_new_<ID>.csv`) go in `annotation/returns_gold_new/`.
- Scoring: `src/score_gold.py --run new --human 'annotation/returns_gold_new/*.csv'`. It reports per-run and per-dimension κ and accuracy, plus verdict agreement.
- The private key is `annotation/gold_key_new.csv`, and the design is in `annotation/gold_sample_new.json`.

### B4. Repair audit on the confirmation transfer: Part 11 (`repair_audit_transfer.html`, self-contained, 40 sentences). Built.

**Why:** A2 audits discovery repairs, but the guard's strongest evidence is now its transfer to the W-C confirmation set
(joint pass +9.8 points). A second 40-item audit (20 repairs + 20 controls from that run) would make the transfer
claim a *usable*-repair claim.

**Task:** identical to A2, with its own embedded sample and saved progress. **≥5 annotators**, about 20 min each.

**Sample:** the list prespecified in `analysis/guard_wc/FREEZE.md` (`analysis/guard_wc/audit_sample.csv`): the first
20 distinct changed texts and the first 20 unchanged strict-correct texts, by ascending SHA256.
- There is no model balancing and there are no design weights.
- The model mix is unbalanced (repaired: gemma 10, llama 7, qwen 2, terra 1; controls: gemma 10, terra 7, llama 2,
  qwen 1). It is reported descriptively.

**Deadline:** CALE-AI (Nov 16 freeze).

**Coordinator:**
- Returns (`repair_audit_transfer_<ID>.csv`) go in `annotation/returns_repair_transfer/`.
- Scoring: `src/score_repair_audit.py --key annotation/repair_audit_transfer_key.csv`.

---

## C. Recommended allocation (SUPERSEDED by the two-stage plan at the top)

| Priority | Task | Annotators | Time each | What it adds |
|---|---|---|---|---|
| 1 | A2 repair audit (discovery) | ≥5 | 20 min | CALE-AI's main missing evidence |
| 2 | B1 human-written pairs + blind checks | 20 writers + 3 checkers per pair | 25 min writing, 15 min checking | Fully human-authored confirmation, removing the item-provenance objection |
| 3 | B2 keyword elicitation | ~45 sessions | 20 min | Ecological "Loss": real keyword choices |
| 4 | A3 + A4 source/corpus checks | ≥3 each | 15 min each | Human validation of confirmation items and corpus ambiguity |
| 5 | B3 expanded gold | 3 | 1.5 h | Judge validity on all new outputs |
| 6 | B4 transfer repair audit | ≥5 | 20 min | Usable-repair claim on the confirmatory transfer |
| 7 | A1 extra coders on Parts 1–3 | 3 | 1.5–2 h | Majority gold, more than two coders |

**Practical schedule:**
- Today/tomorrow: A2, A3 and A4 (tools exist), and start B1 writing as soon as its tool ships.
- Nov 3–5: B1 checks, B2 elicitation, and B3/B4 (built: Parts 10 and 11).
- Results flow into SE4All up to Nov 10 and into CALE-AI up to Nov 16.

## D. Reporting in the papers

For every task the papers report:
- the number of annotators;
- the coding design (which items each annotator saw);
- reliability (Krippendorff α, with a bootstrap CI over items);
- agreement with the automated judge;
- reimbursement;
- that annotators were anonymous, not authors, and blind to system and condition.

Writers of handwritten items are reported as item authors, with their consent for the items to be released under CC BY 4.0
with the study data. The writers' consent text should say this explicitly.
