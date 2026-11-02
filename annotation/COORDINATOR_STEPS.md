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
