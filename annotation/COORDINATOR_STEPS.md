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
