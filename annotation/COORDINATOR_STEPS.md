# Coordinator steps between stages (private: never send this file to annotators)

Commands only, in order. Run from the repo root after `cd ~/aac-voice-preservation && . .venv/bin/activate`.
Generation and judging use the GPU lock (`src/run_sequential.sh` takes `/tmp/aacv_gpu.lock`) and codex-lb.
Everything else is CPU-only and takes seconds. The plan is frozen in `annotation/assignments/plan.json`; do not
rerun `make_assignments.py --stage 1`.

## 0. While Stage 1 runs (Nov 2-4)

Save each returned CSV unchanged into the `return_folder` listed in `annotation/assignments/stage1.csv`.
List what is still missing:

```bash
python - <<'EOF'
import csv, os
for r in csv.DictReader(open("annotation/assignments/stage1.csv")):
    for f in filter(None, (x.strip() for x in r["return_file"].split(","))):
        if not os.path.exists(r["return_folder"] + f):
            print("MISSING", r["annotator"], r["return_folder"] + f)
EOF
```

## 1. Stage 1 -> Stage 2 (night of Nov 4 -> morning of Nov 5)

```bash
# 1a. writer returns -> candidate pairs (format checks, chips, validator); no make_check_batches here
python src/collect_written_pairs.py --no-batches
# 1b. fill the FIXED Stage 2 files from the precomputed checker graph
#     (--absent: people who will not do Stage 2; --still-checking: non-returning writers who will still check)
python src/make_assignments.py --stage 2            # [--absent P07] [--still-checking P09]
cat annotation/assignments/stage2_fill.json | head -40      # check: pairs_by_n_checkers should be {"3": N}
# 1c. elicitation scoring + generation requests (reduced design: P0 and S3; human channels + POS-cap4 baseline)
python src/score_elicitation.py --prompts P0,S3
# 1d. generation (local models one at a time under the GPU lock; terra on codex-lb in parallel)
bash src/run_sequential.sh runs/requests/elic.jsonl elic1 > runs/elic1_seq.log 2>&1     # ends with SEQDONE
# 1e. judging and attribution
python src/judge.py --run elic1 --items data/items/elic.jsonl --concurrency 12 > runs/elic1_judge.log 2>&1
python src/attribute.py --run elic1 --items data/items/elic.jsonl --fallback J1 > runs/elic1_attr.log 2>&1
# 1f. Part 12 gold file (excludes sets s01-s04 and keyword sets of the Part 12 coders P03, P08, P13, P19)
python src/make_gold_elic.py
# 1g. rebuild the package and publish
rm -f annotation_package.zip && (cd annotation_package && zip -qr -X ../annotation_package.zip . -x '*.DS_Store')
git add annotation/returns* annotation/written annotation/assignments annotation_package annotation_package.zip \
        annotation/gold_key_elic.csv annotation/gold_sample_elic.json data/items/elic.jsonl analysis/elicitation
git commit -m "Stage 2 files: check files, Part 12" && git pull --rebase origin main && git push origin main
```

Then send each annotator `annotation_package/assignments/<ID>_stage2.md` and tell everyone to re-download the zip.
If generation is not done by the morning of Nov 5, send the Part 8 files anyway. Part 12 is the last step on those
four sheets, so it can arrive later the same day.

Fallback rules (built into `make_assignments.py --stage 2`):
- **A writer returns fewer pairs.** The chunks shrink, so the files shrink. Checker sets never change.
- **A writer returns nothing.** That writer's 18 checkers each lose one chunk. If the person is also out for
  Stage 2, their own 18 check chunks go one-to-one to those freed checkers (a deterministic matching in ring
  order). A checker never gets their own pairs or a chunk they already check. Only those checkers' files change.
- **Leftover chunks.** Any chunk that still has no checker goes to the present person with the lowest pair load.

## 2. Stage 2 -> Stage 3 (night of Nov 7 -> Nov 8)

```bash
# 2a. score the blind checks (>= 2 of 3 and majority) -> analysis/hw_checks/items.csv, data/items/hw.jsonl
python src/score_pair_checks.py
# 2b. Part 14 routing to the six fixed tie-breakers (stage3/<ID>_tiebreak.json, possibly empty)
python src/make_assignments.py --stage 3            # [--absent P17]
# 2c. generation on the checked pairs (reduced design: P0 on all 5 channels)
python src/build_requests.py --items data/items/hw.jsonl --split hw --prompts P0 --out runs/requests/hw.jsonl
bash src/run_sequential.sh runs/requests/hw.jsonl hw1 > runs/hw1_seq.log 2>&1
python src/judge.py --run hw1 --items data/items/hw.jsonl --concurrency 12 > runs/hw1_judge.log 2>&1
python src/attribute.py --run hw1 --items data/items/hw.jsonl --fallback J1 > runs/hw1_attr.log 2>&1
# 2d. Part 13 gold file (excludes pairs written or checked by the Part 13 coders)
python src/make_gold_hw.py
# 2e. Part 12 scoring (once its returns are in)
python src/score_gold.py --run elic --human 'annotation/returns_gold_elic/*.csv'
# 2f. rebuild the package and publish (as in 1g, adding annotation/gold_key_hw.csv, annotation/gold_sample_hw.json,
#     data/items/hw.jsonl, analysis/hw_checks)
```

Then send `annotation_package/assignments/<ID>_stage3.md` to the 9 Stage 3 people (Part 13: P04, P15, P20; Part 14:
P01, P06, P12, P16, P17, P18). If someone declines, ask the reserves in the order of
`annotation/assignments/stage3_people.json`:
- **A Part 13 reserve** gets `assignments/<old ID>_stage3.md` with the ID replaced. Rerun `make_gold_hw.py`
  first only if the reserve wrote or checked many of the sampled pairs.
- **A declining tie-breaker** is handled by rerunning `make_assignments.py --stage 3 --absent <ID>`. Their pairs
  go to the other five tie-breakers.

## 3. After Stage 3 (Nov 9-10)

```bash
python src/score_pair_checks.py                       # tie-break checks are read with the other checks (same folder)
python src/score_gold.py --run hw --human 'annotation/returns_gold_hw/*.csv'
```

A 4th check settles a 2-1 split by majority: 3/4 keeps the pair, 2/4 drops it. 1-2 splits are never routed, because
a 4th check cannot change them. If a pair is dropped after hw1 has run, drop its outputs at analysis time, not by
regenerating.

## 4. Stage 4 (proposed Nov 1; build after the user confirms who is available)

Rationale and decisions: D-058. Tools to build (Sonnet subagent): stage-4 fill in `make_assignments.py --stage 4`,
`make_repair_audit_v2.py` (Part 17 sample), `intent_check.html` + `make_intent_check.py` + `score_intent_check.py`
(Part 18). Parts 15/16 reuse `write_pairs.html` / `check_pairs.html` and `collect_written_pairs.py` /
`score_pair_checks.py` with a new batch tag `hw2` (ids must not collide with hw1).

```bash
# 4a. Part 18 (start at once): 10 outputs per writer from their own KEPT pairs, hw1, P0, channels bare + chip1
#     (5 + 5; declared, seeded draw), labels A / B / something else / unclear; key private
python src/make_intent_check.py --run hw1 --per-writer 10 --seed 20261102
# 4b. Part 17: 60 repaired + 60 controls, frozen hash order, EXCLUDING every text in Parts 4/11;
#     3 raters per item, raters = people who did not do Parts 4 / 11 (P02 P07 P09 P10 P11 P14).
#     Added 2026-11-01 before any return: + 20 original_failed + 20 strip_only (10 per pool), 80 items per rater.
#     The 120 base rows, ids and raters are asserted identical to the committed key; --no-arms draws only the 120.
python src/make_repair_audit_v2.py --n 60 --raters P02,P07,P09,P10,P11,P14 --per-item 3
# 4b2. Part 19 (added 2026-11-01 before any return): human check of the arbiter's labels + "Can you" requests.
#      130 items x 2 coders over all 20 people (13 each); seeded draw (20261101); key annotation/arbiter_check_key.csv
python src/make_arbiter_check.py                    # -> stage4/<ID>_part19.json; returns -> annotation/returns_arbiter_check/
python src/score_arbiter_check.py                   # (python src/score_arbiter_check.py --self-check on simulated returns)
# 4c. (roster chosen Nov 1: P05 P16 P17 P18; `make_assignments.py --stage 4` rebuilds sheets/stage4.csv/placeholders;
#     annotation/assignments/stage4_plan.json is kept unless --rebuild or --writers/--raters/--checkers is given)
#     Part 15: 4 writers x 15 speech-act pairs; writers = people who never wrote speech_act; dedup against ALL
#     prior pairs (exact + Jaccard >= .75) is mandatory before checks
python src/make_assignments.py --stage 4            # [--writers <4 IDs>]; returns -> annotation/returns_written_hw2/
# 4d. after Part 15 returns: collect (batch hw2), fill Part 16 checks (3 per pair, never the writer)
python src/collect_written_pairs.py --batch hw2 --no-batches     # -> annotation/written/hw2/ (see dedup_report.csv, rejected.csv)
python src/make_assignments.py --stage 4 --fill-checks           # [--absent <ID>]; returns -> annotation/returns_hwcheck_hw2/
# 4e. after Part 16: score, generate (P0, 5 channels, 4 models; ~1,000 requests), judge, arbiter, attribute
python src/score_pair_checks.py --batch hw2        # -> data/items/hw2.jsonl, analysis/hw2_checks/ (hw1 untouched)
python src/build_requests.py --items data/items/hw2.jsonl --split hw --prompts P0 --out runs/requests/hw2.jsonl
bash src/run_sequential.sh runs/requests/hw2.jsonl hw2 > runs/hw2_seq.log 2>&1
python src/judge.py --run hw2 --items data/items/hw2.jsonl --concurrency 8 > runs/hw2_judge.log 2>&1
# then blind arbiter -> runs/hw2/arbiter.jsonl; attribute.py WITHOUT fallback
```

Analysis rules fixed now (before any Stage 4 data): hw1 + hw2 are analysed together, clustered by writer;
hw1-only results are reported as a sensitivity. P06's remaining speech-act pair is excluded (D-058); P06's 15
time pairs stay, with an exclude-P06 sensitivity. Part 17 is the primary repair-usability estimate; Part 4 is
reported as the pilot. Part 18 is reported as writer-intent agreement, never as AAC-user validation.

### Part 17 decision rule (frozen 2026-11-01 before any Part 17 return; D-062)
Primary endpoint: item-level consensus "usable" (strict majority of 3 raters; ties/unsure = unknown, and a
sensitivity check counts unknown as unusable). Estimate: repaired − control, Newcombe 95% CI, pooled over both pools, plus per pool.
- If the pooled CI lies entirely below −10 pp: the guard fails a new deployment clause ("usable ≥ control − 10 pp").
  It is reported as "killed for deployment, kept as a detector".
- If the CI includes −10 pp but excludes 0: report it as a usability cost of uncertain size.
- If the CI includes 0: report no detectable cost, pooled with Part 4 as a sensitivity check.

Part 4 is reported as the pilot (n = 20 + 20, raters not independent), never combined selectively. Neither audit is
chosen because it is more favourable.

#### Secondary comparisons (added 2026-11-01 before any return)
Added to address the confound "controls never failed, so repaired hard cases are compared with easy ones". The
primary repaired − control rule above is unchanged and stays the only deployment rule. 20 items per arm, 10 per pool,
same 6 raters, 3 per item (key arms `original_failed`, `strip_only`; `paired_source_id` = the repaired item's source id):
- **original_failed:** the pre-repair first-pass output that the guard flagged and then repaired, for the first 10 per
  pool of the already-drawn repaired items in their frozen hash order (all 20 paired with their repaired item).
- **strip_only:** the deterministic "please"-strip output (G1s) for an input where the strip changed the first pass and
  differs from the repair (a sentence cannot be shown twice; G1s often equals the first pass or the repair itself:
  of the 60 repaired items, 20 have a strip-only output identical to the repair and 33 are left unchanged by the
  strip, see `annotation/repair_audit_v2_sample.json`). Paired-first, then the remaining eligible repaired units of the
  pool in hash order (8 of 20 paired).
- **Reported endpoints** (item-level consensus as above; `score_repair_audit.py`):
  repaired − original_failed (did the repair make the sentence usable?) and repaired − strip_only, each as independent
  arms (Newcombe 95% CI, pooled and per pool) and paired by `paired_source_id` where both items have a consensus
  (paired difference, Newcombe method 10 CI, exact sign test, n pairs). No decision threshold is attached; the
  results are read as context for the primary rule and never replace it. "Usable" on original_failed shows how bad
  the unrepaired sentences were; "repaired − original_failed" > 0 means the repair helped. The strip-only contrast is
  limited to inputs where the strip and the repair differ, and the scorer says so.

#### Part 19 (added 2026-11-01 before any return)
Human check of the arbiter's labels (`runs/r2c1`, `hw1`, `elic1` `arbiter.jsonl`) and of the "Can you ...?" request
rule. Reported descriptively (agreement with Wilson CIs per coding and per item, per precedent tag, per run and
dimension; human vs arbiter, J1 and J2; human-human; the share of "Can you" outputs coded as request or question, by
coders with and without earlier labelling work). No pass/fail threshold is set; tags with few items are shown with
their counts. The 38 arbiter units already labelled by people in Parts 10/12/13 are not re-drawn (their gold labels
can be compared with the arbiter separately).

### Stage 5: Parts 20 and 21 (added 2026-11-02 before any return)
Built after Stage 4 had been returned, so they are a separate Stage 5 (files in `annotation_package/stage5/`, sheets
`assignments/<ID>_stage5.md`, `annotation/assignments/stage5.csv`, `make_assignments.py --stage 5`); every Stage 4 item, key and
assignment is unchanged. All 20 people do both parts (10 + 8 min). Returns: `labels_part20_<ID>.csv` ->
`annotation/returns_treated_check/`, `labels_part21_<ID>.csv` -> `annotation/returns_source_check/`.
```bash
python src/make_treated_check.py        # Part 20: 120 outputs (6 classes x 20), seed 20261102, 2 coders each, 12 per person; frozen (--force to redraw)
python src/score_treated_check.py       # (python src/score_treated_check.py --self-check)
python src/make_source_check.py         # Part 21: 200 messages (negated 55 / polite 55 / question-request 45 / plain 45), 2 coders, 20 per person
python src/score_source_check.py        # writes analysis/source_check/ and runs src/robust_t2_posterior.py --human-labels (1.5 min; --no-t2 skips)
python src/make_assignments.py --stage 5
```

#### Part 20 analysis rules (added 2026-11-02 before any return)
Question: does the automatic judge agree with people on real treated outputs, where the headline claims rest?
- **Items.** One item is one real output occurrence. Classes (20 each): G1 guard repairs (outputs the guard changed; `runs/guard1`,
  `runs/guard_wc`), G1r no-feedback retries that changed the sentence (`runs/guard_baseline_disc`, `_wc`), chip1 (`runs/hw1`, channel
  chip1; hwctl1 holds only the irrelevant-chip and plain-word channels, so chip1 comes from hw1, whose arm hwctl1 is contrasted
  with), nlcue plain-word (`runs/hwctl1`), newmodel (Qwen2.5-14B and Mistral-Nemo-12B, 10 each, channels chip1 and bare, so the
  default and the chip arm are both covered), gemini (gemini-3.1-flash-lite, irrelevant-chip control rows left out). Spread equally over the
  dimensions present; the key stores frame size and draw size per class x dimension (weight). The Gemini and guard-baseline runs were
  still growing when the frame was drawn; the key stores the text, so the draw is frozen.
- **Exclusions.** Sentences already labelled or shown to people (Parts 1-3/10/12/13, Part 19, the Part 4/11/17 sentence audits, Part
  18), arm-revealing text (square brackets, "keywords", chip/guard/feedback wording, model or vendor names, assistant boilerplate),
  quarantined families, rows without a production critical label (unresolved judge disagreement). A coder never gets a pair they
  wrote or checked.
- **Reference.** Primary = both coders gave the same label for that field; split or single-coder items have no consensus for that
  field (counted, listed). Sensitivity = plurality (a single labelled coder counts). Judge = production label.
- **Endpoints (descriptive, no pass/fail).** Judge vs human consensus accuracy (Wilson) and Cohen kappa (item bootstrap) per field
  (critical, polarity, speech_act, agent, certainty, politeness, added_content), pooled and per class, critical first; per class the
  accuracy re-weighted over dimensions; critical by class x dimension; J1 and J2 alone; human-human agreement as the ceiling;
  verdict agreement per class (Violation / constraint_preserving on cue channels, Assumption on bare/noncrit), recomputed from labels
  with the production rules. The H7 gate (kappa >= 0.6) is printed for reference only. With about 20 items per class the intervals
  are wide: results are stated as "no detectable judge failure in class X" or "disagreement concentrated in ...", never as a
  per-class threshold pass. A class with a visibly lower critical agreement is reported with its items, not tuned away.
- **No re-labelling.** Human labels never replace production labels in any headline estimate; Part 20 is reported as judge validity
  on the treated arms, next to the Part 10/12/13 gold results.

#### Part 21 analysis rules (added 2026-11-02 before any return)
Question: how accurate are the detector labels (negated, polite, question/request) of the source messages behind the T2 posterior,
and how much does a human-corrected label change P(negated | no negation word in the keywords)?
- **Items.** 200 messages of the 600-message elicitation sample (the T2 sample; W-B has no keyword sets). Strata by detector label
  (disjoint, first match): negated 55 of 122, polite 55 of 115, question_request 45 of 181, plain_other 45 of 182. Weights in the key:
  w_stratum = stratum size / drawn; w_total = w_stratum / elicitation inclusion probability. A person never codes a message whose
  keywords they typed in Part 9 (blocked = annotators of the message's set).
- **Human label.** Primary = both coders equal (question and request count as one answer for "question or request vs statement"); unsure
  is missing. For the T2 correction a yes/no split is p = 0.5, a single labelled coder counts, a message nobody labelled (and every
  message outside the 200) gets the human-negated rate of its detector stratum among labelled messages. Sensitivity: splits ->
  stratum rate.
- **Agreement endpoints (descriptive).** Per label: detector vs human kappa (item bootstrap CI), accuracy, sensitivity, specificity,
  PPV (Wilson; unweighted and w_total-reweighted with Kish effective n), human-human agreement, human rate per detector stratum, the
  list of negation disagreements. No pass/fail threshold.
- **Corrected T2.** `src/robust_t2_posterior.py --human-labels` on the same code path as the committed T2 (HT over the elicitation
  frame, 1,000 message bootstraps); only the polarity of the source changes. Reported next to the detector-based 2.7% (human keywords)
  for both keyword channels, with the silent-reversal rate per 1,000, and the splits -> stratum-rate sensitivity. The T2 headline in
  the papers is restated with the corrected number whichever way it moves; the detector-based number stays as the committed
  reference. The T2 bootstrap does not carry the sampling error of the Part 21 labels (stated in the report).

### Stage 5 wave 2: Parts 22-25 (added 2026-11-03 before any return; Stage 5 opens Wed Nov 4, due Thu Nov 5, 23:59)
Parts 20 and 21 are unchanged (12 and 20 items per person). Four more parts use one new tool, `annotation_package/rate_items.html`
(blind per-person files `stage5/<ID>_part22..25.json`, 2 practice items each, tests `tests/test_rate_items_html.js`, run for every file
with `NODE_PATH=/tmp/jsd/node_modules`). Items and keys are the ones each frontier request already built; nothing is redrawn.
```bash
python src/make_frontier_parts.py          # frozen (seeded, --force redraws): 53 part files, annotation/assignments/stage5_frontier{,_assignment}.{json,csv}
python src/make_assignments.py --stage 5   # sheets <ID>_stage5.md (neutral names), stage5.csv, HANDOUT.md block
```
Returns: `labels_part22_<ID>.csv` ... `labels_part25_<ID>.csv` -> `annotation/returns_part22/` ... `returns_part25/` (columns `item_id, annotator,
check_id, practice, order, <one column per question>, note, time_ms, ...`; `practice=1` rows are dropped; an item's unasked questions are empty).
The private item-by-person list is `annotation/assignments/stage5_frontier_assignment.csv`; join item ids to the `annotation/frontier_*_key.csv`
files only after all returns are in.
- **Items and coder counts (all at the required count).** Part 22 default_profiles 223 items x 2 coders. Part 23 whole_message R-WM-1 120
  (108 output + 12 verbatim) x 3. Part 24 value_of_cue 73 x 2: speech-act stratum A (36) plus the whole control stratum B (37; the key holds 37,
  the request text says 31). Part 25 partner_context round 3, 258 (197 Part A + 61 Part B) x 3. Stratum A polarity (40) and politeness (32)
  items of value_of_cue are NOT in this wave.
- **Exclusions (checked by `tests/test_stage5_frontier.py` from the raw files).** Parts 23 and 25 (families `hw-*`): never the writer in
  `hw_candidates.jsonl` (hw and hw2) nor any checker in `check_key.csv`, incl. Part 14 tie-breakers. Parts 22 and 24: never any annotator of the
  message's elicitation set. Part 25 families `r2pol-*` exclude no one. Part 23: nobody gets two outputs made from the same input (family + variant).
- **Missing and split answers.** No answer is imputed and none is re-requested after labels are seen. Consensus needs the full required count:
  2 coders must agree; for 3 coders the majority (2 of 3) is the label, three different answers = no consensus (counted and listed). A field with no
  consensus is dropped from that field's accuracy and shown as a count. `other` / `cannot tell` / `neither` are answers, not missing.

Analysis rules (each also stated in the request named; those requests and the plan sections cited are the pre-registered frame):
- **Part 22 default_profiles** (`analysis/frontier/default_profiles/ANNOTATION_REQUEST.md`; plan: `PLAN.md` sections 1 and 5; key `annotation/frontier_default_profiles_key.csv`
  with HT weight `w`). Human speech act = Q1 consensus; non-statement = question or request/command, statement = statement, `other` = no consensus
  (sensitivity: other counted as non-statement). Human polite = Q2 consensus. Detector labels (`detector_nonstmt`, `detector_polite`) vs human consensus per stratum
  (E_speech_act, politeness exposure, controls): Cohen kappa, precision and recall (Wilson), HT-reweighted with Kish effective n, human-human agreement. Q3 and Q4
  consensus vs the lexical gate "keywords lack the cue": agreement and the share of exposure the gate cannot reach. Then re-run `src/frontier_default_profiles_r3.py` with
  human consensus substituted for the detector proxies and regenerate `round3.md` with `src/frontier_default_profiles_r3report.py`; the detector-based numbers stay as the
  committed reference and the speech-act and politeness results keep the label provisional until this is scored. Negation is not in this part.
- **Part 23 whole_message R-WM-1** (`analysis/frontier/whole_message/ANNOTATION_REQUEST.md`; plan: `PLAN.md` section 5; key `annotation/frontier_whole_message_key.csv`).
  Output items: acceptability = Q3 yes or yes with a small edit (consensus by 2-of-3); Q1 match = consensus equals the key's intended variant; added content = Q2 added or
  both. Per arm A0, A1, A2 with family-cluster bootstrap CIs; paired A2 - A0 and A1 - A0 on the same inputs (family x variant); judge flag (`gpt_UC`) vs human added
  content: kappa and AUROC against the 3-coder majority. Verbatim items (12): share of copies a majority call "adds something" (Q4 yes) and "complete" (Q5 yes) against the
  flags. Descriptive, no new threshold; with 36 inputs the intervals are wide and are stated as such. Machine-only results stay provisional until this is scored.
- **Part 24 value_of_cue** (`analysis/frontier/value_of_cue/ANNOTATION_REQUEST.md` Part B and round-3 addendum; plan: `PLAN.md` sections 6 (Stage 4) and 7; key
  `annotation/frontier_value_of_cue_key.csv`, `alternative_is`). q-hat (speech act) = share of stratum A speech-act judgments with Q2 = the alternative sentence, every
  judgment counted (2 per item), message-cluster bootstrap CI; Q1 = alternative as the cross-check. Wrong-pick rate m = stratum B judgments with Q2 = alternative (all 37
  items, per dimension descriptive, pooled with a cluster bootstrap); share of Q1 "both equally" or "neither" = adequacy of the offered alternative; inter-annotator kappa
  with CI. q-hat replaces the assumed q = 0.9 only for speech act; polarity and politeness keep the assumed q (not annotated in this wave) and the frontier says so.
  The result is reported whichever way it moves; SHOW-TWO numbers stay conditional on q for the other dimensions.
- **Part 25 partner_context round 3** (`analysis/frontier/partner_context/ANNOTATION_REQUEST.md` round-3 revision; plan: `PLAN.md` sections 4 and 5, rules R8 and R9; key
  `annotation/frontier_partner_context_r3_key.csv`). Part A: the 3-coder consensus category (a restates, b reply, c invented, d plain statement, e other) per group
  (propositional_negation, licensed anchors, controls); shares with a family-cluster bootstrap; confusion with `machine_class` and `machine_class2`; the +8.7 pp is
  re-split by the human shares. Part B: human echo (yes/no) and reply (yes/no) consensus vs the machine filter stratified by judge decision (echo-only, neither, reply,
  arm-0): sensitivity and specificity with Wilson CIs. If the human echo rate on machine-"none" units is above 20%, the filtered numbers (the +1.2 to +1.5 pp lower bound
  and the filtered propositional C2) are reported as unvalidated. Failing
  or odd categories are reported, not re-run. Machine results stay PROVISIONAL (R9) until this is scored.
- **No re-labelling.** Human labels never replace production labels in any headline estimate; they are reported next to the machine results as validity checks.

## 6. Stage 6: intent-coverage draft sets (Parts 26 and 27; added 2026-11-05 before any return)
Human measure of `analysis/coverage/PLAN.md` section 4: does a draft set contain a sentence the writer says is what they meant, at what reading
cost? The same 20 writers, each on their own 10 items (the writer's own kept pair; 200 items, `analysis/coverage/items_draw.json`, 20 reserve
items never used). Nothing is generated or judged by the package builder: it reads the frozen `analysis/coverage/{drafts_main,selector_main}.jsonl`.
Same tool as Parts 22-25 (`annotation_package/rate_items.html`, blind per-person files `stage6/<ID>_part26.json` and `_part27.json`, 2 practice items each).
```bash
python src/make_coverage_stage6.py          # frozen (seeded; --force redraws): 40 part files, annotation/coverage_key.csv (PRIVATE), coverage_key.sha256, assignments/stage6_coverage.json
python src/score_coverage.py --self-check   # key invariants, blind package, planted-writer recovery; must print SELF-CHECK PASSED before the zip is built
python src/make_assignments.py --stage 6    # sheets <ID>_stage6.md, assignments/stage6.csv, HANDOUT.md block (dates are placeholders in DATES: set them first)
uv run --with pytest python -m pytest -q tests/
```
**Before sending (not yet done): hash-deposit `annotation/coverage_key.sha256` (and `analysis/coverage/items_draw.sha256`, `prompt_shas.json`) as for D-073/D-092;
rebuild the zip (not done by these scripts); never put `coverage_key.csv` or `stage6_coverage.json` in the package.**
Returns: `labels_part26_<ID>.csv` -> `annotation/returns_part26/`, `labels_part27_<ID>.csv` -> `annotation/returns_part27/` (columns `item_id, annotator,
check_id, practice, order, <one column per question>, note, time_ms, ...`). Score with `python src/score_coverage.py` -> `analysis/coverage_human/`
(`qc.json, by_arm.csv, contrasts.csv, direct_vs_pool.csv, concordance.json, summary.json, free_text_to_code.csv`).

#### Design as built (differences from PLAN section 4; log each in `analysis/coverage/DEVIATIONS.md` when that file is created)
- **Part 26 (set view).** Per item one (condition, arm) set, condition bare or chip, arm G1 (1 draft), D3p, C3 or E3 (3 drafts), no arm label, drafts in deployed order
  (G1 first). 8 cells x 25 sets; per writer 5 bare + 5 chip (condition balanced within each of the writer's dimensions), every arm once per condition plus one extra arm rotated
  over writers. Questions: pick a draft or none (`pick1/2/3`), send (`as_is/small_edit/no`), hard (1-5); the tool stores time per item.
- **Part 27 (draft check).** For the same item, all distinct drafts of the four arms in the item's own condition (normalised-text de-duplication, tool-shuffled, arm-blind),
  plus the unfiltered D3p drafts (tag `D3pU`, chip only). Questions: `ver` (meant / my other version / something else), `acc` (as it is / small edit / no); the note box carries
  "what is wrong" for No. About 56-65 drafts per person. Part 27 comes after Part 26 so the set answers are not primed.
- **Fits about 30 minutes** (29-31 per person incl. 2 min per part for opening and downloading; seconds per item are assumptions in `stage6_coverage.json`, to be replaced by the
  timed two-person pretest of PLAN section 9 step 2 before sending). Cut to fit: one condition per item (not both), W1 plain-word arm, the k = 5 audit arms (D5p, C5, E5) and the
  side-by-side burden check (PLAN 4 step 3) are NOT in the human package; their human endpoints do not exist.
- **Equal size (critique1 B6).** k = 3 sets are topped up to exactly 3 drafts from the arm's own next candidates (C3: next-ranked dimensions; E3: remaining dimension/event
  candidates in alternation; D3p: next diverse drafts). Sets still short are shown short and counted (`short_sets` in the scorer; the plan-time set size is in the key as `plan_n`).
- **Same cue filter for every arm (critique1 B5).** In chip, D3p drafts that the machine judge reads as contradicting the cue are replaced from the arm's own next diverse drafts, exactly as
  C3/E3 are filtered; the original unfiltered D3p drafts are in the pool as `D3pU`, so both variants are computable from the same human ratings. The filter uses the same judge as the
  proxy; the human pool ratings are the check on it.
- **Contrast arms are the pre-declared ones** (G1, D3p, C3, E3); the round-1 machine suggestion to drop E3 (critique1 B3) was NOT applied. S1 is reported for both C3 and E3 (the plan
  picks one from the machine proxy at the dry-run stage; that choice is not made here).

#### Part 26 and 27 analysis rules (frozen 2026-11-05 before any return; implemented in `src/score_coverage.py`)
- **Unit and inference.** Writer (20 clusters), items within writer. 95% CI = writer-cluster bootstrap (B = 10,000, seed 20261117: resample writers, then items within writer);
  p = writer sign-flip randomisation (20,000 flips) next to each CI; Holm over the five primary contrasts below. Everything else is exploratory and labelled so. Per-dimension and
  per-writer tables are direction only. Language: "coverage of the writer's own intended message", "approval-gated draft sets", "writer-intent agreement by adult annotators". Never AAC-user
  benefit, IRB approval, machine-panel agreement as human validation, or "pre-registered" (use pre-specified, git-timestamped, hash-deposited, and only once the deposit exists).
- **QC, no imputation.** Practice rows dropped; rows for unknown ids or another person's id dropped; a repeated item keeps the last export; incomplete rows and invalid options dropped
  (all counts in `qc.json`). Nothing is imputed and nothing is re-requested after labels are seen. A set answer "none" with a send answer other than No is flagged `inconsistent` and
  counted as none/no.
- **Pool endpoints per (item, arm), derived from Part 27 ratings (the arm's shown drafts).** H-cov (primary) = at least one draft rated `meant` AND accepted `yes` or `small_edit`.
  H-match = at least one `meant` (Part 18's exact definition; compare with Part 18's 25.1% overall, 39.2% chip, 11.2% bare only with the generator difference stated). H-strict = `meant` and `yes`.
  An endpoint is 1 if any rated draft covers, 0 only if every draft of the set was rated and none covers, otherwise undefined (excluded, counted).
  H-first = position of the first covering draft, else the set size (censored). H-wrong-first = draft 1 (G1) rated `other`; it is identical across arms by construction and is a
  check, not a result; the real safety numbers are the D3pU vs D3p difference and the rate of drafts rated `other` per arm.
- **H-direct (check).** From Part 26: picked = a draft chosen; direct H-cov = picked and send in {as it is, small edit}. Compared with the pool-derived value for the same item and arm
  (`direct_vs_pool.csv`: rates and agreement); a direct rate above the pool-derived one by more than 5 pp for any arm is reported as a limitation of the pool rating.
- **Primary contrasts on H-cov (paired within item for the same condition).** S1_C3 and S1_E3: bare, C3 - D3p and E3 - D3p; success = difference >= +10 pp and CI lower bound > 0.
  S2_C3 and S2_E3: best set vs one cue tap, bare C3 (or E3) vs G1 in chip; these are different items for the same writers, so the CI is an unpaired writer-cluster difference; success =
  CI lower bound > -5 pp AND cost per covered message at r = 0.5 not above chip G1's (otherwise "equal coverage at higher cost"). S3_E3: chip, E3 - G1; success = >= +10 pp and CI lower bound > 0.
  Status per contrast: pass / fail (CI upper bound below the threshold) / unresolved. Exploratory: S3x C3 and D3p minus G1 in chip, the cue tap (G1 chip - G1 bare), the filter effect (D3pU - D3p).
- **S4 (burden).** Median drafts read to the first usable draft among covered items at k = 3 (<= 2.0), and mean Part 26 burden of C3/E3 minus G1 (<= 0.5, CI upper < 1.0; unpaired, items differ).
- **Cost.** PLAN section 5, tap-equivalents with the sweep r in {0.25, 0.5, 1, 2}: cue tap, r x drafts read, choose tap when k > 1, accept tap, fallback = min(words of the sentence, e x word
  edit distance to the closest shown draft) when no draft is usable. Assumptions, flagged as such; reported WITH and WITHOUT the fallback term (the fallback favours bigger sets).
- **Outcome rules.** As PLAN section 7 (C-A / C-B / C-C; unresolved stays unresolved). The proxy gate failed (`analysis/coverage/proxy_validity.json`), so only these human results decide S1-S4.
- **Proxy vs writers.** Draft-level kappa and AUROC of the proxy `intended` flag against H-match and H-cov (all drafts, and by origin G1, D3p, D3pU, C3, E3), arm-level Spearman (8 arm-condition
  cells), reported next to the machine tables; set-level agreement is the arm-item comparison of `proxy_cov` and `h_cov`. A conservative proxy variant is not defined here.
- **Free text.** Notes on No ratings are in `free_text_to_code.csv`; coded by hand into critical / relation / detail dropped / added / fluency (the rule of `whole_message`); the coder is named in the report.
- **Not decided here (open).** The ICC re-estimate and power table (PLAN 1.4), the S1 arm choice on the reserve dry run, and the timed pretest. If a deviation changes an arm, a draft or a criterion after a return, it is logged with date and reason; this section is never edited.


## 7. Stage 7: Part 28 listener communication study and Part 29 independent-mutant confirmation (added 2026-11-17 before any return; opens Wed Nov 18, due Thu Nov 19, 12:00)
Human outcome measure (plan section A) and non-circular mutation set (plan section B3). Same 20 people as Stages 1-6, annotators of study materials only: no data about
the people are collected, nobody uses or is evaluated on a system, no AAC users take part. Never write "exempt" or "IRB approved".
Same tool as Parts 22-27 (`annotation_package/rate_items.html`), extended with optional per-item answer options (`qopts`; backwards compatible, tested in `tests/test_rate_items_html.js`).
Blind per-person files `stage7/<ID>_part28.json` and `_part29.json` carry only opaque ids, the topic line and the sentence (Part 28) or the two sentences (Part 29);
never keywords, the intended message, the condition, the model, the operator or the dimension.
```bash
python src/make_listener_study.py package        # frozen (seeded; --force redraws): 40 part files, annotation/listener_key.csv + oracle_indep_key.csv (PRIVATE) + .sha256, assignments/stage7_plan.json
python src/score_listener_study.py --self-check  # key invariants, planted listeners, exclusions; must print SELF-CHECK PASSED before the zip is built
python src/score_oracle_indep.py --self-check    # key invariants, confirmation rule, planted judge; must print SELF-CHECK PASSED
python src/make_assignments.py --stage 7         # sheets <ID>_stage7.md, assignments/stage7.csv, README sections, HANDOUT.md block (dates in DATES: open Wed Nov 18, due Thu Nov 19 12:00)
uv run --with pytest python -m pytest -q tests/
```
**Before sending (not yet done, and the zip is NOT rebuilt by these scripts): hash-deposit (gh release, as for deposits 1-5) `annotation/listener_key.sha256`,
`annotation/oracle_indep_key.sha256`, the sha256 of `analysis/listener/PLAN.md` (221321be61bcdc92...), `analysis/oracle_indep/PLAN.md` (0d2897760da44283... at the time of writing; it carries Amendment 2),
`analysis/listener/stimuli.jsonl` and this section. Never put `listener_key.csv`, `oracle_indep_key.csv`, `stage7_plan.json` or `orchestration/` in the package.**
Returns: `labels_part28_<ID>.csv` -> `annotation/returns_part28/`, `labels_part29_<ID>.csv` -> `annotation/returns_part29/`. Run the integrity duplicate check on the returns before scoring.
Score Part 28 with `python src/score_listener_study.py` -> `analysis/listener_human/`. Part 29: confirm first, then run the production judge on the mutant text of the
candidates (target dimension and reference value in the key columns `target_dimension`, `target_ref`) -> `runs/oracle_indep/judge_labels.jsonl` ({"id", "critical"}), then
`python src/score_oracle_indep.py` -> `analysis/oracle_indep_human/`. The judge run happens after the returns, never before.

#### Packet rules as built (frozen 2026-11-17 before any return; they add to, and do not change, the two PLAN files below)
- **Units and listeners (Part 28).** 120 intended messages, 582 (item, condition) stimuli, 423 judge units (identical text within an item merged, reference never merged). Each unit has exactly 2
  different listeners; a listener sees any one intended message in at most one unit (Latin square over conditions); nobody judges a family they wrote or checked (`src/make_frontier_parts.py`
  `hw_blocks`: writer, Part 8 checkers, Part 14 tie-break checkers). Allocation uses `make_frontier_parts.Alloc` (same balancing) per part, seeded (`S7_SALT` in `src/make_listener_study.py`).
- **Load.** 42-43 sentences (Part 28) and 15 pairs (Part 29) per person. Time assumptions: 26 s per Part 28 judgment, 16 s per Part 29 judgment, 2 practice items per part, 2 min per part to open and download:
  28-29 min per person (limit 30). These are assumptions until the pilot gives real times; if the pilot is slower the reading order stays and the second sitting is allowed.
- **Part 28 screen.** Topic line ("Topic: <topic>" in PLAN section 2; shown as `Topic` with the label text) and the sentence. Q1 readings in a seeded per-listener order, plus "Something else, or I cannot tell"; Q2 four fixed
  responses in a seeded per-listener order; Q3 confidence 1-3. Option values are positional (`reading 1/2/unclear`, `action 1-4`); the private key maps them (`reading1`, `q2_roles`).
- **Practice.** Two invented practice items per part (not from the study), with feedback; practice rows are dropped by the scorers.
- **Part 29 screen.** Fixed, dimension-neutral question (wording in `analysis/oracle_indep/PLAN.md` Amendment 2); same / different / unsure; sentence order seeded per item.
- **QC at scoring.** Practice rows, unknown ids, another listener's id, repeated items (last export wins), missing or invalid Q1 (Part 28) / answer (Part 29) are dropped and counted; nothing is imputed
  and nothing is re-requested after labels are seen.
- **Late or thin returns.** Fewer than 16 usable listeners: Part 28 results are descriptive and labelled underpowered (PLAN section 7). Fallback of the plan: CALE-AI leads with Stage 6 and Part 28 goes to the journal.

#### Frozen rules, copied verbatim from `analysis/listener/PLAN.md` (sha256 221321be61bcdc92baa3843a7781f4b7d644685afaccfab4d12909c736bad8f7)
> # Part 28 Listener Communication Study: frozen analysis plan
>
> Written 2026-11-17, before the stimulus draw, before the guard run, and before any stored output for the 120 drawn messages was read.
> Nothing below may change after listener data are collected. Any later deviation is reported as a deviation, not folded in.
> Status: not committed; to be hash-deposited before the sheets are sent (see COORDINATOR_STEPS section 7, written by the assignment task).
>
> ## 1. Question and role of the people
> Twenty adult non-author volunteers act as annotators of study materials. A listener sees a context line and one sentence and says what the person is saying.
> No data about the listeners themselves are collected. Listeners are not AAC communication partners; comprehension is not a real-world consequence.
>
> ## 2. Stimuli (frozen rules)
> Source: data/items/hw.jsonl (547 families) and data/items/hw2.jsonl (60 speech-act families); every family is a kept pair (3 of 3 human checks pass).
> Draw script: src/make_listener_study.py, seed 20261117 (python random.Random(seed), explicit sort of family ids before every draw).
>
> * Dimensions: polarity, speech_act, agent, time_quantity. certainty and politeness are excluded (lower SLP severity, 3 to 3.5 against 4 to 5).
> * 30 messages per dimension, 120 total. hw and hw2 families are pooled before the speech-act draw (hw2 is not oversampled). No family is used twice.
> * An "intended message" is one variant (A or B) of a family: its source sentence is the writer's own sentence and the reference condition.
> * Default vs non-default intended value, declared a priori (not from any model output). Value rank, default first:
>   polarity: affirmative > negated;
>   speech_act: statement > question > request/command;
>   agent: speaker > addressee > third party;
>   time_quantity: now > past > later.
>   In each family the variant with the higher-ranked critical value is the default variant, the other is non-default.
>   Each dimension: 15 messages with the default variant intended, 15 with the non-default variant intended (50% non-default overall, balanced within dimension).
> * Model: each item is assigned one of the four primary models (qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra) by seeded round-robin over a seeded permutation of the items within each dimension x default stratum. The same model supplies every model-made condition of that item.
> * Context line: the item files hold no context text (all null). The neutral topic label of the pair (e.g. "plans", "transport") is shown as the context line, "Topic: <topic>". If the topic is missing the context line is omitted.
> * Conditions per item: bare (P0 greedy, channel bare, runs/hw1 or runs/hw2); chip1 (channel chip1, the intended variant's cue, same model); nlcue (plain-word cue, runs/hwctl1 channel nlcue; hw2 has no nlcue, so nlcue exists only for hw1 items; the condition gap is documented and the nlcue contrasts are restricted to hw1 items); G1 (the unchanged guard of runs/guard_wc, src/interventions.guard_one with max_retries 2, temperature 0, 96 output tokens, tag I1-guard-v1, seed 1000 for local models, run on the bare input of the same model); reference (the writer's own sentence).
> * G1 reads only cues the user supplied. The bare input supplies none, so G1 is expected to be inert except for removing/regenerating unsupplied politeness. This is a property of the frozen guard and is reported, not tuned. The guard policy is not modified.
> * Identical-text rule: within an item, model-made conditions whose output text is identical after normalisation (lowercase, collapse whitespace, strip trailing punctuation) are one sentence. It is judged once per listener pair, and every condition inherits that sentence's judgments. The reference is never merged. The stimulus table keeps one row per (item, condition) with a judge_unit id.
> * Items whose chosen model returned an empty or unparsed output for bare or chip1 are not replaced; they are reported as a gap and excluded from every contrast involving that condition.
>
> ## 3. Listener task and codes
> Q1 (primary): "What is the person saying?" Options: reading A, reading B (order randomised per stimulus), "something else / unclear". Readings are the two writer sentences of the pair.
> Q2: "How would you respond?" Four fixed options per item: the action implied by the intended reading (correct), the action implied by the opposite reading (opposite), "ask them to say it again / confirm" (clarify), and one dimension-specific third action (other). Option order is randomised.
> Q3: confidence 1 to 3.
>
> ## 4. Outcomes (per judgment)
> * Success = Q1 equals the intended reading.
> * Received reversal = Q1 equals the opposite reading of the pair. "Something else / unclear" is neither success nor reversal and is reported separately as unclear.
> * Consequential error = Q2 equals the opposite action. Sensitivity: Q2 is not the correct action and not clarify.
> * Reversal per 1,000 = 1000 x mean(reversal). SLP-weighted reversal per 1,000 = 1000 x mean(w_d x reversal) with w_d = mean SLP severity of the dimension / 5, from expert_package/returns_slp task 1: polarity (NEG 5,5) 1.0; speech_act (ACT 4,4) 0.8; agent (AGT 4,4) 0.8; time_quantity (TIM 4,4) 0.8. Weights are descriptive, from two raters.
> * Ceiling: the reference condition's success rate; it is reported next to every contrast.
>
> ## 5. Estimation, primary contrasts, clustering, equivalence
> Unit of analysis: the judgment. Condition means are item-balanced: mean over items of the item's mean over its judgments in that condition.
> Primary contrasts on success (each paired by item, same items in both arms):
> 1. chip1 - bare
> 2. G1 - bare
> 3. nlcue - chip1, restricted to items that have nlcue (hw1 items), with an equivalence margin of +/-5 percentage points.
> Uncertainty: two-way cluster bootstrap, 10,000 resamples, seed 20261117, resampling items and listeners independently with replacement (judgments kept if both their item and listener are drawn, with multiplicity). Percentile 95% CIs. Holm correction over the three primary contrasts for the 95% intervals reported as adjusted intervals (the unadjusted ones are also given).
> Equivalence for contrast 3: declared only if the 90% bootstrap interval lies inside [-5, +5] pp (TOST). Otherwise "not shown equivalent"; absence of a difference is never claimed from a non-significant interval.
> Secondary (descriptive, same bootstrap): reversal per 1,000 and SLP-weighted per 1,000 per condition, overall and in the non-default-intended stratum; consequential error; unclear share; by dimension; Q3 confidence; bare - reference.
> Sensitivity (reported, not primary): logistic mixed model with crossed random intercepts for item and listener (if it fails to converge, the bootstrap stands alone).
> The headline is only stated if the data agree: "listeners received the opposite of the intended meaning in X of 1,000 messages without the cue and Y with it", with the 50% non-default design mix stated beside it.
>
> ## 6. Exclusions
> * Listener: a listener whose reference-condition Q1 success is below 75% (their attention check) is excluded from all analyses; the count is reported and results with them retained are given as a sensitivity.
> * Listener: a listener with fewer than 80% of assigned judgments completed is excluded.
> * Judgment: missing Q1 is dropped. No outlier-time trimming (time is not collected).
> * Item: an item missing a condition's output is dropped from contrasts involving that condition only.
> * Nobody judges their own pair or a pair they checked (logic of src/make_frontier_parts.py, src/make_assignments.py --stage 5).
> * No exclusion is made on the basis of outcomes. Exclusions are applied identically to all conditions.
>
> ## 7. Fallbacks
> * Local-model access for the guard run is blocked by Unity or GPU: the guard only needs a call when it flags a candidate; items whose assigned model is local and which need a call are reassigned, before any listener data, to the terra output set (terra-only items); this is documented in analysis/listener/STIMULI_NOTES.md.
> * nlcue missing for hw2 items: nlcue restricted to hw1 items (section 2).
> * Fewer than 16 usable listeners after exclusions: all results are descriptive and the primary contrasts are labelled underpowered.
> * Guard gives identical outputs (expected): guard - bare is reported as exactly the same sentences, with the share of changed items.

#### Frozen rules, copied verbatim from `analysis/oracle_indep/PLAN.md` (sha256 0d2897760da4428364b95aa1dd453a43df5c12cb11a638e2f7ca31619651a985 at the time of writing)
> # Independent mutation set (plan section B3) - pre-declared before any generation
>
> Purpose: a non-circular sensitivity set. Mutants are built WITHOUT the checker lexicon (the NEG/HEDGE/PAST/LATER regexes
> in src/oracle_baselines.py and the operators in src/oracle_real_ops.py). Part 29: 2 human annotators confirm each item
> changes or keeps meaning; ONLY human-confirmed items count. This step builds candidates only; the judge and baselines are NOT scored here.
>
> ## Source draw (declared, seeded)
> - Same oracle-pass filter as src/oracle_real.py build: runs/hw1/scored.parquet, valid, channel in {chip1, chipall, full},
>   critical_match True, critical_source in {agree, arbiter}, no refusal/acceptance quarantine; one output per family, one per
>   distinct text. Texts already used in analysis/oracle_real/sample.jsonl are excluded (no overlap with the earlier set).
> - Seed 20261117; per-operator RNG random.Random(f"{SEED}|{op}"); each text is used at most once across the whole set.
> - Applicability pre-filter (before any outcome is seen): length 3-22 words, single sentence, not an empty/degenerate text.
>
> ## Operators and quotas (100 mutants)
> | op | n | source pool (dimension) | construction |
> |---|---|---|---|
> | neg_fail_to | 13 | polarity, ref affirmative | template: "I <verb>..." -> "I fail to <verb>..." / "X <verb>s" -> "X fails to <verb>" |
> | neg_refuse_to | 13 | polarity, ref affirmative | template: same slot -> "refuse(s) to <verb>" |
> | neg_hardly | 12 | polarity, ref affirmative | template: "can" -> "can hardly"; "am/is/are" -> "... hardly"; "I <verb>" -> "I hardly <verb>" |
> | neg_nobody | 10 | polarity, ref affirmative | Gemini: rewrite with a quantifier subject like nobody/no one ("Nobody ...") |
> | role_passive | 14 | agent | Gemini: swap who does what to whom (passivise or invert roles) |
> | role_embed | 12 | agent | Gemini: embed the claim as attributed to someone else so the original speaker is no longer the agent |
> | q_embed | 12 | speech_act, ref question | Gemini: turn the question into an embedded statement ("I wonder whether ...") |
> | time_implied | 14 | time_quantity | Gemini: shift the time reference by implication only (no explicit time words from the checker list) |
>
> Item operator assignment is by seeded shuffle of the dimension pool in this order of ops; template ops walk the shuffled pool
> until the template applies. Gemini ops take the next shuffled items, one call per item (one retry on invalid output).
>
> ## Controls (50, meaning-preserving)
> - ctl_contraction (10): template toggle of contraction (I am <-> I'm, do not <-> don't excluded where negation present: only non-negated forms).
> - ctl_paraphrase (40): Gemini paraphrase that keeps polarity, speech act, agent/roles, certainty, politeness, time and quantity; drawn across all six dimensions (seeded, pool minus mutant sources).
>
> ## Gemini
> - Model gemini-3.1-flash-lite via src/gemini_backend.py, temperature 0, thinking off, max_tokens 96, concurrency 1.
> - Hard cap 150 calls in total (62 mutant + 40 control planned, remainder for single retries). Prompts are fixed in src/independent_mutants.py
>   (ops PROMPTS dict) and the raw responses cached in tmp/ then logged to runs/oracle_indep/gemini_calls.jsonl.
> - Validation of a Gemini output (fixed, mechanical): non-empty, one sentence, differs from original (case/punct-insensitive),
>   length 0.5x-2.5x, and for mutants must not contain the words "yesterday|tomorrow|tonight|ago" (time lexicon) unless op is time_implied
>   (where it is forbidden too). Failures after retry are dropped and replaced by the next shuffled item (counted in the call budget).
>
> ## Outputs
> - analysis/oracle_indep/candidates.jsonl: {id, original, mutant, dimension_hint} in a seeded shuffled order, no labels.
> - analysis/oracle_indep/key.private.jsonl: id -> kind (mutant|control), op, expected, source text_id/family/model/variant, ref value,
>   lex_visible flag (mutant newly matches the baseline NEG/PAST/LATER regexes; reported as a stratum, "nobody" is NEG-visible by construction).
> - analysis/oracle_indep/draw.json: seed, pool sizes, counts by operator, call counts.
> - Not done here: judge scoring, baseline scoring, human confirmation (Part 29). Mutants are candidates until two annotators confirm.
>
> ## Amendment 1 (made after the first build, which showed template ops under-filled: neg_refuse_to 6/13, neg_hardly 0/12; no outcome/judge info involved)
> - Template negation ops walk the polarity pool first, then (seeded order) non-negated, non-question texts from the other five dimension pools; the
>   template regex is the only applicability criterion. Their dimension_hint is the source dimension.
> - First-build Gemini responses (temperature 0, same op+sentence) are reused from runs/oracle_indep/gemini_calls.jsonl rather than re-called;
>   the 150-call cap counts only distinct calls actually made (first build used 106).
> - Known limitation, kept on purpose: role_passive/q_embed/paraphrase outputs from a small model can fail to change (or fail to keep) meaning;
>   that is exactly what the 2-annotator Part 29 confirmation filters, and only confirmed items count.
>
> ## Amendment 2 (Part 29 packet and scoring rules; written 2026-11-17 after candidates.jsonl was built, before any Part 29 return, before any judge or baseline score on these items)
> Packet (src/make_listener_study.py, shared with Part 28; per-person files annotation_package/stage7/<ID>_part29.json; private key annotation/oracle_indep_key.csv):
> - All 150 candidates (100 mutants, 50 controls) are shown, mixed, each to 2 different annotators. Nobody annotates an item whose source family they wrote or checked
>   (src/make_frontier_parts.py logic: hw_blocks). Annotators never see kind, operator, dimension, source or which sentence is the original.
> - Which sentence is "Sentence 1" and which is "Sentence 2" is a seeded coin per item (stored in the private key); the two annotators of an item see the same order.
> - One fixed, dimension-neutral question for every item: "Do the two sentences tell the listener the same thing: who does what to whom, whether it is so or not, when it
>   happens, how sure the speaker is, and whether it is a statement, a question or a request? Small differences in wording or style do not count."
>   Answers: same / different / unsure. (The wording names every dimension, so it does not hint at the one that was changed.)
> Confirmation rule (the only items that count):
> - A mutant is human-confirmed CHANGED if both annotators answer different. A control is human-confirmed SAME if both answer same.
> - Any other pair (a disagreement, or either annotator unsure, or a missing answer) is unresolved: excluded from every score and counted by operator.
> - A mutant both annotators call same, or a control both call different, is a construction failure: reported by operator, never scored.
> - An annotator with fewer than 80% of their assigned Part 29 items answered is dropped; the items then have one annotator and are unresolved.
> Scoring (src/score_oracle_indep.py; the judge run is made after returns, by the unchanged production judge, on the mutant text only):
> - Target dimension of a mutant: neg_* -> polarity (reference value affirmative); role_passive and role_embed -> agent; q_embed -> speech_act (reference question);
>   time_implied -> time_quantity. Reference values are those in the private key. A control is scored on its own source dimension and reference value.
> - An oracle "catches" an item when its label does not match the reference (production critical_match). Sensitivity = caught / confirmed mutants, false-alarm rate =
>   caught / confirmed controls, both with Wilson 95% intervals; by operator, by target dimension, and by the lex_visible stratum (lex_visible False is the
>   non-circular headline: the mutation does not newly match the baseline NEG/PAST/LATER lexicon). Oracles: production judge, surface baseline, overlap baseline
>   (src/oracle_baselines.py, applied to the mutant text; overlap uses the source family's two sentences).
> - Judge versus each baseline on the same confirmed mutants: exact McNemar test on the discordant pairs. Annotator agreement is reported (raw agreement and Cohen kappa on
>   same/different over items where both answered, unsure counted as its own category in a second line).
> - An unresolved judge label counts as not caught (conservative) with the upper bound where it counts as caught reported beside it. No exclusion is made on the basis of any oracle output.
