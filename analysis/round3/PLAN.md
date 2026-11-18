# Round 3 (hw3): independent confirmatory writer round for the speech-act cue effect (problem #8)

Written 2026-11-18. FROZEN before any round-3 sentence is written, checked, generated or judged. Not committed. Nothing below
changes after the first round-3 pair is returned; any later change is logged in analysis/round3/DEVIATIONS.md, never edited here.
Status of earlier numbers: hw1+hw2 pooling (P1 +37.5 pp, 10 writers) was a post hoc decision (D-058..D-079; ledger C63: "exploratory,
not preregistered"). This round replaces that pooled estimate, as the confirmatory claim, with a test on new writers alone.

## 1. Question and role of people
Does supplying the speech-act cue (a chip such as [?] or [PLEASE]) raise critical speech-act match relative to a noncritical
word, for sentences written by writers who have never written speech-act pairs? Twenty adult non-author classmates (P01-P20),
consented and paid, annotate/write study materials; nothing is collected about them. No AAC users, no study of people as system
users. Writers release their sentences CC BY 4.0 (tick-box in write_pairs.html; otherwise annotation/written/hw3/consent_confirmed.csv
with the user's confirmation, as D-079).

## 2. Batch tag and paths (all new; hw1/hw2 untouched)
Batch `hw3`. Family ids `hw3-act-NNN`, `hw3-plt-NNN`. Returns: annotation/returns_written_hw3/, annotation/returns_hwcheck_hw3/.
Candidates/dedup: annotation/written/hw3/. Items: data/items/hw3.jsonl. Checks: analysis/hw3_checks/. Run: runs/hw3. Analysis: analysis/round3/.

## 3. Writers (declared rule, applied to the files on disk on 2026-11-18; roster fixed here)
Speech-act writers: every person in P01-P20 with NO speech_act file in annotation/returns_written/ or returns_written_hw2/.
Prior speech-act writers: P01 P03 P04 P05 P06 P08 P14 P15 P16 P17 P18. Roster = **P02 P07 P09 P10 P11 P12 P13 P19 P20 (G = 9)**.
Each writes **15 speech-act pairs** (135 pairs; same topic-rotation/fragment scheme as Part 15: `write_pairs.html#dim=speech_act&rot=<r>&id=<ID>`,
rot assigned in roster order 0..8 mod 12 over the topic list).
Replacement: none. A writer who does not return or does not consent is dropped (no substitute, since every other person has
written speech act); the achieved G is reported. Rule for the confirmatory claim at achieved G: G >= 6 (section 8), else descriptive only.
Optional politeness arm (supporting only, does not gate anything): 6 writers who never wrote politeness, are not in the speech-act roster,
lowest prior Part 7/15 file count, ties by ID. Never wrote politeness: P01 P03 P05 P06 P07 P08 P09 P10 P13 P14 P15 P17 P19 P20; minus roster
leaves P01 P03 P05 P06 P08 P14 P15 P17 with load 2,2,3,2,2,2,2,3 -> **P01 P03 P06 P08 P14 P15 (G = 6)**, 15 politeness pairs each (90 pairs).
Politeness is skipped entirely if the speech-act wave is not complete by the due date.

## 4. Writing rules (unchanged from Parts 7/15)
Same write_pairs.html (no edits to the page, rules or examples; hash of annotation_package/write_pairs.html recorded in the hash deposit),
src/hw_rules.check_pair Fix-rules, 15 pairs, 3 practice pairs first, 4-12 words, keywords 2-4 not revealing the difference, one shared
non-keyword word, no copying of any sentence seen earlier in any part. Writers get the Part 15 instruction text verbatim.
Dedup (mandatory, before any check is planned) = src/collect_written_pairs.py --batch hw3 rules against ALL earlier pairs: every accepted
candidate in hw1, hw2 (including pairs later dropped by checks), annotation/written/rejected.csv and hw2/rejected.csv, and earlier hw3
pairs: exact pair, one sentence equal (token-normalised), or token Jaccard >= .75. A rejected pair may be replaced once by its writer
within the same due date (to reach 15); the replacement goes through the same dedup.
Quarantine rule as W-C/hw1: speech-act families whose critical values are refusal/acceptance are excluded from analysis (analyze_hw1.build).

## 5. Blind checks (wave 2)
3 independent blind checks per accepted pair via check_pairs.html (same 4 questions), never the pair's writer, pool = P01-P20 minus the writer;
assignment by src/make_check_batches.py (seeded, balanced, max load 36 pairs per person; files of 30). A person is not assigned a pair
whose dimension-mate sentence they wrote. Total 405 checks (+270 if politeness) = about 1.1 files each, about 25 min. A pair is KEPT if
>= 2 of 3 checkers pass all four questions (min_pass 2, planned 3), as hw1/hw2. 3-of-3-only is a sensitivity. Checks are scored by
src/score_pair_checks.py --batch hw3. The kept set (data/items/hw3.jsonl) is frozen and its sha256 written to analysis/round3/FROZEN.sha256
BEFORE any generation. Generation runs on the kept set only (no pre-generation, unlike hw2), so outcomes cannot influence which pairs are kept.

## 6. Generation and labelling (identical protocol to hw1/hw2)
Prompt P0 (greedy, same system prompts, chip_legend as in runs/hw1/hw2), 5 channels (src/build_requests.py CHANNELS: bare, noncrit,
chip1, chipall, full), 4 primary models: qwen2.5-7b, llama3.1-8b, gemma3-4b (local, one server at a time) and
gpt-6.1-terra (codex-lb, <= 4 concurrent). Local generation via `~/research-cluster/bin/research submit aac-llm` (HANDOFF-AAC.md);
fallback blocking flock /tmp/aacv_gpu.lock; Unity has GPU priority. Judge: src/judge.py J1/J2, concurrency <= 3. Blind arbiter
src/arbiter_tool.py (sees output text only, not condition/model/writer). attribute.py WITHOUT fallback. Judge/arbiter model, rubric
and precedents (D-057 etc.) are the committed versions; no new precedents are introduced after seeing round-3 outputs: any unlisted
case is coded unclear/mixed. Scale: about 4,300 generations for 135 speech-act families (hw2: 1,896 for 60); 1,080 P1 rows for the full 135 families
(135 families x 2 variants x 4 models); politeness adds roughly 2,800 generations if run.

## 7. Estimand and exact analysis (confirmatory)
Frame: src/analyze_hw1.frames P1 on round-3 families only: per (family, variant, model) value = critical_match(chip1) - critical_match(noncrit),
channels at P0, speech_act dimension, after the quarantine exclusion. Writer = cluster.
**Primary estimator**: theta = unweighted mean over writers of the writer mean of value (pp). Writer mean = mean of the writer's rows.
**Primary test**: one-sided t test with G-1 df on the G writer means, H0: theta <= 10 pp (a margin below every earlier subset: hw1 alone +35.3,
llama3.1 +16.9, rule-of-thumb "meaningful"), alpha = .025 (equivalently the lower bound of the 95% two-sided writer-mean t interval > +10 pp).
**Co-primary condition** (both required): exact sign-flip randomisation test over writer means against 0, one-sided p <= .025 (needs G >= 6;
with G = 9 min p = 1/512). Confirmed = both hold. Not confirmed = reported plainly as "not confirmed in new writers", whatever the pooled estimate.
No other contrast is confirmatory; no multiplicity adjustment is therefore needed.
Secondary (descriptive, labelled as such): (a) CR1 row-weighted pooled estimate with t(G-1) CI, wild-Rademacher exact 2^G and Webb CIs
(src/robust_t6_small_cluster.py --items data/items/hw3.jsonl --runs runs/hw3 --name hw3; seed 20261118); (b) per-model P1 and chip/no-chip rates;
(c) leave-one-writer-out range; (d) the proportion of writers with positive mean; (e) conventions sensitivity: "Can you" coded question, "I want X,
please" coded statement (src/hw12_speech_act_sensitivity.py patterns); (f) 3-of-3 kept set; (g) Claude-relabel critical labels (src/relabel_nongpt_*).
**Pooled estimate (secondary, explicitly post hoc in origin)**: hw1+hw2+hw3, G_total = 10 + achieved G (writers are all distinct people),
same estimators; report next to the round-3-alone estimate, plus heterogeneity: Welch t between the 10 earlier writer means and the new writer means
(two-sided, no decision rule). The headline in both papers is the round-3-alone confirmatory result; pooled only as "pooled across rounds".
**Supporting politeness (P2)** if run: frame analyze_hw1.frames P2 (plain minus polite switch, full channel), G=6; supports if one-sided t
lower bound > 0 and sign-flip p <= .0156 (all six positive); reported as supporting, no claim depends on it.
Excluded rows and writers: none by outcome. A writer with < 8 kept pairs is retained (rows weight equally within writer in theta); if < 3 kept
pairs of a writer, the writer is dropped and reported.

## 8. Power (declared inputs: hw1+hw2 P1, ledger C63, analysis/hw12/summary.json)
Writer-mean effect 37.2 (row-weighted +37.5); SD across 10 writer means = 5.4 pp (range +29.2 to +45.5); weakest model gain +16.9 (llama).
Simulation by noncentral t, one-sided alpha .025, df G-1, same test as section 7:
| G | SD across writers | true theta | power vs H0 theta <= 10 |
|---|---|---|---|
| 9 | 5.4 | 37.5 | 1.00 |
| 9 | 10 (about 2x observed) | 30 | 1.00 (vs 0: 1.00) |
| 9 | 8 | 30 vs H0 <= 20 | .91 |
| 9 | 10 | 25 | .975 |
| 6 | 10 | 25 | .83 |
| 6 | 5.4 | 25 | 1.00 |
Even a true effect of half the observed (18.7) is detected vs 0 with power >= .95 at G = 6 and SD = 10. Hence G = 9 is chosen as the
maximum available independent writers (there are no more people who have not written speech act), not for marginal power; the sign-flip
floor requires G >= 6. If achieved G is 6-8 the rule is unchanged; if G < 6 the claim is descriptive. Pairs per writer (15) follow the
protocol; with 8 rows per pair, a writer mean has ~120 rows.
Politeness (P2): earlier +7.6 pp, SD across writers 3.7; G = 6: power .99 at SD 3.5 and .84 at SD 5 for theta = 7.6; at theta = 5, .80 / .51:
supporting only for this reason.

## 9. Items / stimuli / tools to build
1. annotation/returns_written_hw3/ and annotation/written/hw3/; write_pairs fragments and sheets for 9 (+6) writers: extend make_assignments.py with
   `--stage 8` (hw3; Part 30 write, Part 31 check) parameterising the hard-coded hw2 constants (S4_WRITTEN, S4_BATCH, `*_check_hw2.json`);
   collect_written_pairs.py --batch regex to accept hw3 (family-id codes act/plt); score_pair_checks.py --batch hw3.
2. Sheets `assignments/<ID>_stage8.md` with the CC BY note, due dates, and the instruction not to copy any earlier sentence; fragments rot 0..8.
3. Dedup reports (dedup_report.csv, rejected.csv) vs all hw1/hw2 pairs (including hw2 rejected).
4. Check files `stage8/<ID>_check_hw3.json` (3 checks per pair, never the writer; 30-pair files) and private check key.
5. data/items/hw3.jsonl (kept pairs) + analysis/hw3_checks/; FROZEN.sha256 of items + this PLAN + write_pairs.html + build_requests config.
6. runs/requests/hw3.jsonl via build_requests.py --items data/items/hw3.jsonl --split hw --prompts P0; sequential local run (research submit);
   API run for terra (<= 4); judge; arbiter inventory/decisions; attribute.py without fallback.
7. Analysis: src/analyze_round3.py (new, thin wrapper over analyze_hw1.frames/robust_t6_small_cluster; computes section 7 exactly, writes
   analysis/round3/{confirmatory.json,report.md,contrasts.csv,pooled.json}); a simulated-data self-check run before data exist.
8. Hash deposit (GitHub release + OTS, as protocol-hash-2026-11-18f pattern) of this PLAN and the tooling hashes before sheets are sent; second deposit
   of FROZEN.sha256 before generation.
9. Tests: pytest for the stage-8 roster rule (asserts roster == P02 P07 P09 P10 P11 P12 P13 P19 P20), hw3 id/dedup, analyze_round3 on synthetic data
   (known effect recovered; sign-flip p at G=9 is 1/512).

## 10. Order of operations (no step reads outcomes before the next freeze)
write (due T+3 days) -> collect + dedup -> assign + wave-2 checks (T+5) -> score, freeze hw3.jsonl, hash -> generate -> judge -> arbiter ->
attribute -> run analyze_round3.py once -> report. Round-3 outputs are not inspected before the analysis script is run.
Scratch only in ~/aac-voice-preservation/tmp/ (deleted afterwards). Papers are updated only after the report (confirmatory result stated first,
pooled estimate labelled as pooled/secondary).
