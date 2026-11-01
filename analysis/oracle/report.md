# W-A oracle validation report (PREREG_R2)

<!-- CURRENT_H7_STATUS -->
**D-031 supersession (cycle-3 Action 3, 2026-11-01).** The earlier main1 human extraction gate H7 **passed**. Two annotators labeled 187 items (100 double-coded core, 87 single-coded extras); held-out `sampled_test/final` κ=0.906–0.972, lowest lower 95% bound 0.813, n=107–121 across seven fields. Violation agreement 96/99 [91.5, 99.0]%, κ=0.916; both positive 22, judge-only 1, human-only 2, both negative 74. Plurality reference, ties/unsure excluded; converted human labels, no per-item times; no adjudication. This supersedes every historical “human pending”, “zero human returns”, and “human gate not evaluable” statement below **only for that earlier extraction inventory**. Historical machine-panel tables remain unchanged. Humans corrected the shared “can’t wait” error; they did not resolve every shared key departure (D-033). H7 does not validate repaired-text completeness, complete meaning, W-B admissibility, or every new W-C/W-D/guard-transfer boundary. Evidence: [human validation JSON](../../annotation/judge_validation_main1.json), [gate log](../oracle/human_gate.log), [current evidence map](../EVIDENCE_MAP.md). Inline “→ D-031” pointers mark each stale prose statement; historical table cells (e.g. “not evaluable, 0 human returns”, “human gate pending”) are kept verbatim as the pre-H7 record.
<!-- END_CURRENT_H7_STATUS -->

Date: 2026-11-01. Author: W-A oracle validation engineer (Claude). No GPU servers were started. The judge ran at
concurrency 8: 30 API calls, 1 transient failure that was retried. The production judge (gpt-6.1-sol, J1+J2,
effort low), the layer0 tiebreak, the extraction calls are historical. ACTION 2 refresh uses shared arbiter > agreement > unknown resolution and primary quarantine exclusions; no new judge calls were made.

Reproduce:
```
python src/oracle_wa.py prepare && python src/oracle_wa.py judge && python src/oracle_wa.py arbiter-todo
python src/score_gold.py --run main1 --panel 'annotation/returns_codex/*.csv' --challenge-judgments runs/oracle_challenges
python src/score_gold.py --run main1 --panel 'annotation/returns_codex/*.csv' --challenge-judgments runs/oracle_challenges \
    --panel-members C-gpt-5.6-sol,C-gpt-6-astra --tag _sens_sol_astra
PYTHONPATH=src python src/analyze.py --table runs/main1/scored.parquet --tag main1
python src/oracle_report.py
```

## Headline results

| check | result | gate |
|---|---|---|
| Identity: 120 verbatim sources scored as `full` outputs | 0/120 contract false alarms [0.00, 0.03]; 0 added content | none set; necessary condition met |
| Scoped mutation: 120 hand-written single-value flips | 120/120 detected as Violation [0.97, 1.00] | none set |
| New challenges: mutants detected (production rule) | 22/24 [0.74, 0.98] | >= 22/24: **pass, with no slack** |
| New challenges: control false alarms | 0/24 [0.00, 0.14] | <= 1/24: pass |
| New challenges, acceptance group | 4/6 mutants detected; both misses are statement substitutions passed by the D-015 relaxation | per-group: **not met** |
| Same, raw rule (no D-015 relaxation) | 24/24 detected, 0/24 false alarms | pass |
| Round-1 challenges, critical label = key | 22/24 [0.74, 0.98] | none set |
| Judge vs codex-panel majority, kappa (sampled, unweighted / design-weighted) | critical .97/.98; polarity 1.0/1.0; speech_act .95/.97; agent .96/.97; certainty .91/.97; politeness .96/.97; added_content .76/.80 | kappa >= .6 vs **human** gold: **not evaluable, 0 human returns** |
| Contract verdicts recomputed from panel labels (primary, excluding quarantine) | violation: 2/99 units (1.37% weighted); constraint_preserving: 4/99 units (2.77% weighted); assumption: 1/57 units (0.41% weighted) | machine agreement only; human gate pending |

Four findings matter most:

1. **The oracle is strong on clean single-cue contrasts.** Identity, mutation, embedded actor, question vs request
   and mitigation all came out perfect. Both identity and mutation on act-16 B, however, depend on the arbiter. On
   "Yes, you can borrow my car this weekend." J1 said *statement*. On the mutant "Sorry, you can't borrow my car
   this weekend." J1 also said *statement*. Under the production acceptance~statement relaxation, J1's label would
   have **passed the refusal mutant as an honoured acceptance**. Only the arbiter's *refusal* label caught it.
2. **The D-015 acceptance repair destroys sensitivity to statement substitution.** "You borrowed my car this
   weekend." and "Of course, I helped you move on Saturday." were both correctly labelled *statement*, and both
   satisfy an *acceptance* contract under the production rule. This is the reviewers' "arbitrary statements satisfy
   acceptance" concern, now shown on keyed items. The quarantine (section 6) is therefore required, not optional.
3. **Panel agreement does not validate shared errors.** On round-1 challenges the judge is wrong against the key
   on ch-08 ("I can't wait..." -> negated) and ch-22 ("a couple of" -> two). The 3-model panel majority makes the
   same two errors, so judge-vs-panel challenge accuracy is 24/24. gpt-5.6-sol and gpt-6-astra agree with each other
   and with the judge at kappa ~.95-1.0 on most dims. This is consistent with correlated GPT-family errors as much
   as with correctness.
4. **added_content is the weakest dimension.** The panel's own alpha is .41, and judge-vs-majority kappa is .76.
   18/163 sampled units have no production added_content label, because J1 != J2 and there is no tiebreak. On the
   new challenges the judge called three keyword-complete sentences added content ("after work" from `pick up
   work`, "check if" from `pharmacy open sunday`).

Data-quality note on the panel: in C_gpt-6-luna_core.csv, 28/100 critical answers are not options of the item
(for example "past" for an agent question). They are dropped as invalid. Luna's general-dim agreement in that one
file is also low (0.61-0.90 raw agreement with sol, against 0.86-1.0 in its extra files). The file looks partly
misaligned or degraded, but it is not a simple row shift. A sol+astra-only sensitivity is reported throughout.

## 1. Challenge-set construction (task 1)

annotation/challenge_items_r2.jsonl has 48 hand-authored sentences in 4 groups. Each group has 6 valid controls
and 6 single-feature mutants, and each mutant has a `pair` (its control), a `mutated_feature` and a
`contract_value` (the control's critical value). The format is the round-1 format (cid, text, dimension, key,
probe) plus `group`, `role`, `pair`, `mutated_feature`, `critical_options` and `input_text` (keywords for the
added-content pass). Keys and the 120 source mutations were hashed before the first judge call
(analysis/oracle/challenge_keys_frozen.sha256).

- acceptance (speech_act). Controls: yes/sure/okay/of course/fine plus a commitment, including the D-015 sentence.
  Mutants: 2 refusals, 1 question, 1 let's-suggestion, and 2 statement substitutions that report, rather than
  accept (the D-015 probes).
- embedded_actor (agent). Controls: want-you-to, X-wants-me-to, asked-Dad-to (CB-7 generalised), I-think-you-should
  (CB-3), maybe-the-nurse (CB-3), told-you-to (CB-7). Mutants change only the embedded doer, or swap the roles.
- question_request (speech_act). 3 question controls (can-I, information, did-you) and 3 request controls
  (can-you, could-you, would-you). Each mutant crosses to the other class by a one-word subject or auxiliary
  change, or a mood change.
- mitigation (politeness). 3 polite controls (could you, please, sorry) whose mutants remove the marker; 3 plain
  controls (imperative, CB-2 can-you, statement) whose mutants add please / would you mind / thanks.
## 2. Identity and scoped-mutation injection (120 test sources)

Every source sentence of data/items/test.jsonl was given to the production judge as if it were the `full`-channel output for its own source (input `The user typed: <source>`), then scored by the unchanged src/attribute.py (J1/J2, layer0 tiebreak for general dims, arbiter for critical J1!=J2). One hand-written, scoped mutation per source (analysis/oracle/source_mutations.jsonl, frozen before judging) flips the critical value and is scored against the *unmutated* source's contract. 17/120 mutations coincide with the family's partner source (minimal pairs admit few other scoped flips); the rest are new wordings.

Critical J1!=J2 disagreements: identity 1/120, mutants 1/120; these went to the arbiter (critical_source=arbiter).

### 2a. Identity relation: every scored commitment of a verbatim source must pass

| dimension | n | critical false alarms (production) | critical false alarms (raw, ORACLE_RAW=1) | contract false alarms (constraint_preserving=False) | added_content=yes | unresolved |
|---|---|---|---|---|---|---|
| agent | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| certainty | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| polarity | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| politeness | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| speech_act | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| time_quantity | 20 | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0/20 [0.00, 0.16] | 0 | 0 |
| ALL | 120 | 0/120 [0.00, 0.03] | 0/120 [0.00, 0.03] | 0/120 [0.00, 0.03] | 0 | 0 |

### 2b. Scoped mutation: the oracle must flag a flipped critical value

| dimension | n | detected: Violation (production) | detected (raw rule) | detected: constraint_preserving=False | misses (production) | label = my expected value |
|---|---|---|---|---|---|---|
| agent | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| certainty | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| polarity | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| politeness | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| speech_act | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| time_quantity | 20 | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 20/20 [0.84, 1.00] | 0 | 20/20 [0.84, 1.00] |
| ALL | 120 | 120/120 [0.97, 1.00] | 120/120 [0.97, 1.00] | 120/120 [0.97, 1.00] | 0 | 120/120 [0.97, 1.00] |

## 3. Challenge items (24 round-1 + 48 new)

The 48 new sentences (annotation/challenge_items_r2.jsonl) were written by hand, without LLM help, with keys frozen before any judge call (sha256 in analysis/oracle/challenge_keys_frozen.sha256). Each control is a valid instance of its contract value. Each mutant changes one feature of its paired control and is scored against the *control's* contract value. A control fails (false alarm) when the production critical_match rejects it. A mutant is detected when critical_match rejects it. `raw` is the same rule without the D-015 acceptance~statement relaxation.

| group | false alarms (prod) | mutants detected (prod) | false alarms (raw) | mutants detected (raw) | critical label = key | keyed general labels correct | J1!=J2 |
|---|---|---|---|---|---|---|---|
| acceptance | 0/6 [0.00, 0.39] | 4/6 [0.30, 0.90] | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 12/12 [0.76, 1.00] | 54/56 [0.88, 0.99] | 1 |
| embedded_actor | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 12/12 [0.76, 1.00] | 61/61 [0.94, 1.00] | 0 |
| mitigation | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 12/12 [0.76, 1.00] | 48/48 [0.93, 1.00] | 0 |
| question_request | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 0/6 [0.00, 0.39] | 6/6 [0.61, 1.00] | 12/12 [0.76, 1.00] | 70/71 [0.92, 1.00] | 0 |
| ALL new (gate) | 0/24 [0.00, 0.14] | 22/24 [0.74, 0.98] | 0/24 [0.00, 0.14] | 24/24 [0.86, 1.00] | 48/48 [0.93, 1.00] | 233/236 [0.96, 1.00] | 1 |

**Gate (PREREG_R2: mutants detected >= 22/24, false alarms <= 1/24):** production oracle 22/24 detected, 0/24 false alarms -> **PASS**. Raw oracle 24/24, 0/24 -> **PASS**. The prereg says '22/24 per new group' but each group has only 6 mutants and 6 controls, so I read the gate as pooled over the 24 new mutants and 24 new controls. Per-group counts are in the table; no group can be certified with n=6 (a 6/6 Wilson lower bound is 0.61).

Per-group strict reading (all 6 mutants detected and 0 false alarms): acceptance 4/6 det, 0/6 FA -> not met, embedded_actor 6/6 det, 0/6 FA -> ok, mitigation 6/6 det, 0/6 FA -> ok, question_request 6/6 det, 0/6 FA -> ok.

Failures (control false alarms and missed mutants):

| cid | role | text | contract | key | judge | J1/J2 |
|---|---|---|---|---|---|---|
| ch2-a10 | mutant | You borrowed my car this weekend. | acceptance | statement | statement (agree) | statement / statement |
| ch2-a11 | mutant | Of course, I helped you move on Saturday. | acceptance | statement | statement (agree) | statement / statement |

Round-1 challenges (24, keyed in round 1, not control/mutant balanced): critical label = key 22/24 [0.74, 0.98]; keyed general labels 42/44 [0.85, 0.99].

| cid | text | key | judge | general errors |
|---|---|---|---|---|
| ch-08 | I can't wait to go to the party. | affirmative | negated (agree) | polarity: key=affirmative judge=negated |
| ch-09 | You should call her tonight. | addressee | addressee (agree) | speech_act: key=offer/suggestion judge=statement |
| ch-22 | I took a couple of painkillers this morning. | unclear/mixed | two (agree) |  |

New challenges, keyed general-dimension disagreements (not part of the gate):

| cid | text | errors |
|---|---|---|
| ch2-a02 | Sure, I can pick you up after work. | added_content: key=no judge=yes |
| ch2-a08 | Sorry, I can't pick you up after work. | added_content: key=no judge=yes |
| ch2-q08 | Check if the pharmacy is open on Sunday. | added_content: key=no judge=yes |

## 4. Codex annotator panel vs the production judge (main1 gold, 163 sampled + 24 round-1 challenges)

Panel: C-gpt-5.6-sol, C-gpt-6-astra, C-gpt-6-luna (machine annotators; none is the judge gpt-6.1-sol or the tested gpt-6.1-terra). **This is machine-machine agreement, not human validation. The PREREG kappa>=0.6 gate applies to human gold only, and no human returns exist yet (annotation/returns/ is absent).** *[→ D-031: superseded for the earlier main1 inventory; H7 passed, see notice at top]* Production labels: J1==J2, else the arbiter (13 sampled critical labels were null in gold_key_main1.csv and are now filled from runs/main1/arbiter.jsonl), general dims use the layer0 tiebreak. Labels the panel member listed in `unsure_dims` are treated as missing, which matches the annotate.html export. Majority means at least 2 of 3 members, and more than half of the non-missing votes. Design weights are 1/pi from gold_key_main1.csv (Horvitz-Thompson); weighted CIs use the Kish effective n. Challenge items have no pi and are scored unweighted, in a separate subset.

Data notes: {"critical_off_option_dropped:C-gpt-6-luna": 28, "out_of_schema:politeness=plain": 2, "out_of_schema:speech_act=acceptance": 3, "rows_with_extra_columns": 43, "unsure:added_content": 10, "unsure:agent": 19, "unsure:certainty": 7, "unsure:critical": 3, "unsure:polarity": 3, "unsure:politeness": 2, "unsure:speech_act": 15}. The 43 rows with an extra column are all of C_gpt-6-luna_extraB.csv, which has one surplus empty field after added_content. The label columns parse correctly. Out-of-schema general labels are kept as given (speech_act=acceptance, politeness=plain) and count as disagreements.

### 4a. Judge (final) vs panel majority, sampled items

| dimension | panel alpha (3 members) | n (majority, judge non-null) | no majority | judge null | acc | kappa | acc_w | kappa_w | n_eff | challenge acc (n) |
|---|---|---|---|---|---|---|---|---|---|---|
| critical | 0.928 [0.895, 0.959] | 163 | 0 | 0 | 0.969 [0.93, 0.987] | 0.968 [0.935, 0.993] | 0.984 [0.936, 0.996] | 0.982 [0.957, 0.997] | 100.3 | 1.0 (24) |
| polarity | 0.772 [0.647, 0.873] | 162 | 2 | 0 | 1.0 [0.977, 1.0] | 1.0 [1.0, 1.0] | 1.0 [0.963, 1.0] | 1.0 [1.0, 1.0] | 99.5 | 1.0 (23) |
| speech_act | 0.853 [0.79, 0.907] | 158 | 6 | 0 | 0.975 [0.937, 0.99] | 0.953 [0.899, 0.989] | 0.986 [0.939, 0.997] | 0.971 [0.91, 0.999] | 98.3 | 1.0 (23) |
| agent | 0.793 [0.733, 0.849] | 154 | 8 | 1 | 0.974 [0.935, 0.99] | 0.962 [0.923, 0.991] | 0.981 [0.93, 0.995] | 0.972 [0.935, 0.999] | 95.7 | 1.0 (24) |
| certainty | 0.829 [0.764, 0.887] | 158 | 5 | 0 | 0.949 [0.903, 0.974] | 0.907 [0.846, 0.965] | 0.981 [0.931, 0.995] | 0.968 [0.918, 0.994] | 97.5 | 1.0 (24) |
| politeness | 0.853 [0.76, 0.931] | 163 | 0 | 0 | 0.988 [0.956, 0.997] | 0.955 [0.884, 1.0] | 0.993 [0.951, 0.999] | 0.974 [0.908, 1.0] | 100.3 | 1.0 (24) |
| added_content | 0.407 [0.304, 0.513] | 142 | 3 | 18 | 0.88 [0.817, 0.924] | 0.757 [0.645, 0.857] | 0.911 [0.835, 0.954] | 0.798 [0.682, 0.885] | 91.3 | 1.0 (24) |

Sensitivity: the reference is gpt-5.6-sol + gpt-6-astra only (both must agree). gpt-6-luna is dropped because its core file gave 28 critical answers that are not options of the item (dropped as invalid above) and has low agreement with every other rater on general dims (core file only, see 4b).

| dimension | 3-member majority: n / kappa / kappa_w | sol+astra agree: n / kappa / kappa_w | sol~astra alpha |
|---|---|---|---|
| critical | 163 / 0.968 / 0.982 | 157 / 0.966 [0.932, 0.993] / 0.982 | 0.983 |
| polarity | 162 / 1.0 / 1.0 | 162 / 1.0 [1.0, 1.0] / 1.0 | 1.0 |
| speech_act | 158 / 0.953 / 0.971 | 151 / 0.987 [0.959, 1.0] / 0.999 | 0.989 |
| agent | 154 / 0.962 / 0.972 | 144 / 0.959 [0.911, 0.99] / 0.97 | 0.965 |
| certainty | 158 / 0.907 / 0.968 | 152 / 0.951 [0.901, 0.989] / 0.991 | 0.959 |
| politeness | 163 / 0.955 / 0.974 | 161 / 1.0 [1.0, 1.0] / 1.0 | 1.0 |
| added_content | 142 / 0.757 / 0.798 | 116 / 0.964 [0.911, 1.0] / 0.975 | 0.653 |

### 4b. Pairwise raw agreement / Cohen kappa (sampled items)

| dimension | 5.6-sol~6-astra | 5.6-sol~6-luna | 5.6-sol~judge | 6-astra~6-luna | 6-astra~judge | 6-luna~judge |
|---|---|---|---|---|---|---|
| critical | 0.98 / 0.98 | 0.88 / 0.873 | 0.95 / 0.948 | 0.90 / 0.893 | 0.97 / 0.967 | 0.90 / 0.896 |
| polarity | 1.00 / 1.0 | 0.94 / 0.686 | 0.99 / 0.967 | 0.94 / 0.71 | 1.00 / 1.0 | 0.94 / 0.711 |
| speech_act | 0.99 / 0.988 | 0.91 / 0.834 | 0.97 / 0.942 | 0.91 / 0.838 | 0.99 / 0.988 | 0.87 / 0.76 |
| agent | 0.97 / 0.961 | 0.83 / 0.757 | 0.95 / 0.925 | 0.85 / 0.779 | 0.97 / 0.952 | 0.83 / 0.756 |
| certainty | 0.97 / 0.953 | 0.89 / 0.801 | 0.94 / 0.9 | 0.89 / 0.805 | 0.95 / 0.918 | 0.85 / 0.737 |
| politeness | 1.00 / 1.0 | 0.95 / 0.822 | 0.99 / 0.955 | 0.95 / 0.807 | 1.00 / 1.0 | 0.94 / 0.769 |
| added_content | 0.82 / 0.621 | 0.63 / 0.209 | 0.84 / 0.68 | 0.68 / 0.316 | 0.94 / 0.884 | 0.62 / 0.226 |

### 4c. Critical label by family dimension (sampled; judge final incl. arbiter vs panel majority)

| critical dimension | n | acc | kappa | kappa_w | disagreements (judge->panel) |
|---|---|---|---|---|---|
| agent | 19 | 18/19 [0.75, 0.99] | 0.918 | 0.892 | speaker->third party |
| certainty | 29 | 27/29 [0.78, 0.98] | 0.901 | 0.967 | plain assertion->strongly certain/emphatic; hedged/uncertain->strongly certain/emphatic |
| polarity | 20 | 20/20 [0.84, 1.00] | 1.0 | 1.0 |  |
| politeness | 22 | 22/22 [0.85, 1.00] | 1.0 | 1.0 |  |
| speech_act | 36 | 36/36 [0.90, 1.00] | 1.0 | 1.0 |  |
| time_quantity | 37 | 35/37 [0.82, 0.98] | 0.937 | 0.961 | now->unclear/mixed; now->unclear/mixed |

Critical confusion matrices by family dimension (rows = panel majority, columns = judge):

**critical / agent**

| panel \ judge | addressee | speaker | third party | unclear/mixed | we/joint |
|---|---|---|---|---|---|
| addressee | 6 | 0 | 0 | 0 | 0 |
| speaker | 0 | 9 | 0 | 0 | 0 |
| third party | 0 | 1 | 1 | 0 | 0 |
| unclear/mixed | 0 | 0 | 0 | 1 | 0 |
| we/joint | 0 | 0 | 0 | 0 | 1 |

**critical / certainty**

| panel \ judge | hedged/uncertain | plain assertion | strongly certain/emphatic | unclear/mixed |
|---|---|---|---|---|
| hedged/uncertain | 7 | 0 | 0 | 0 |
| plain assertion | 0 | 12 | 0 | 0 |
| strongly certain/emphatic | 1 | 1 | 5 | 0 |
| unclear/mixed | 0 | 0 | 0 | 3 |

**critical / polarity**

| panel \ judge | affirmative | negated | unclear/mixed |
|---|---|---|---|
| affirmative | 9 | 0 | 0 |
| negated | 0 | 7 | 0 |
| unclear/mixed | 0 | 0 | 4 |

**critical / politeness**

| panel \ judge | plain | polite |
|---|---|---|
| plain | 11 | 0 |
| polite | 0 | 11 |

**critical / speech_act**

| panel \ judge | acceptance | offer/suggestion | question | refusal | request/command | statement | unclear/mixed |
|---|---|---|---|---|---|---|---|
| acceptance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| offer/suggestion | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| question | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| refusal | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| request/command | 0 | 0 | 0 | 0 | 7 | 0 | 0 |
| statement | 0 | 0 | 0 | 0 | 0 | 9 | 0 |
| unclear/mixed | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

**critical / time_quantity**

| panel \ judge | fifty | forty | four | later | now | past | six | ten | twenty | two | unclear/mixed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fifty | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| forty | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| four | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| later | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| now | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| past | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| six | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| ten | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| twenty | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| two | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| unclear/mixed | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 8 |

### 4d. Per-label precision / recall of the judge, design-weighted (sampled, final)

| dimension | label | n panel | precision | recall | precision_w | recall_w |
|---|---|---|---|---|---|---|
| critical | acceptance | 1 | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] |
| critical | addressee | 6 | 1.0 [0.61, 1.0] | 1.0 [0.61, 1.0] | 1.0 [0.54, 1.0] | 1.0 [0.54, 1.0] |
| critical | affirmative | 9 | 1.0 [0.701, 1.0] | 1.0 [0.701, 1.0] | 1.0 [0.7, 1.0] | 1.0 [0.7, 1.0] |
| critical | fifty | 1 | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] |
| critical | forty | 1 | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] |
| critical | four | 4 | 1.0 [0.51, 1.0] | 1.0 [0.51, 1.0] | 1.0 [0.508, 1.0] | 1.0 [0.508, 1.0] |
| critical | hedged/uncertain | 7 | 0.875 [0.529, 0.978] | 1.0 [0.646, 1.0] | 0.982 [0.526, 1.0] | 1.0 [0.536, 1.0] |
| critical | later | 7 | 1.0 [0.646, 1.0] | 1.0 [0.646, 1.0] | 1.0 [0.518, 1.0] | 1.0 [0.518, 1.0] |
| critical | negated | 7 | 1.0 [0.646, 1.0] | 1.0 [0.646, 1.0] | 1.0 [0.531, 1.0] | 1.0 [0.531, 1.0] |
| critical | now | 3 | 0.6 [0.231, 0.882] | 1.0 [0.439, 1.0] | 0.681 [0.276, 0.923] | 1.0 [0.434, 1.0] |
| critical | offer/suggestion | 2 | 1.0 [0.342, 1.0] | 1.0 [0.342, 1.0] | 1.0 [0.319, 1.0] | 1.0 [0.319, 1.0] |
| critical | past | 3 | 1.0 [0.439, 1.0] | 1.0 [0.439, 1.0] | 1.0 [0.396, 1.0] | 1.0 [0.396, 1.0] |
| critical | plain | 11 | 1.0 [0.741, 1.0] | 1.0 [0.741, 1.0] | 1.0 [0.654, 1.0] | 1.0 [0.654, 1.0] |
| critical | plain assertion | 12 | 0.923 [0.667, 0.986] | 1.0 [0.758, 1.0] | 0.956 [0.693, 0.995] | 1.0 [0.741, 1.0] |
| critical | polite | 11 | 1.0 [0.741, 1.0] | 1.0 [0.741, 1.0] | 1.0 [0.686, 1.0] | 1.0 [0.686, 1.0] |
| critical | question | 9 | 1.0 [0.701, 1.0] | 1.0 [0.701, 1.0] | 1.0 [0.599, 1.0] | 1.0 [0.599, 1.0] |
| critical | refusal | 6 | 1.0 [0.61, 1.0] | 1.0 [0.61, 1.0] | 1.0 [0.501, 1.0] | 1.0 [0.501, 1.0] |
| critical | request/command | 7 | 1.0 [0.646, 1.0] | 1.0 [0.646, 1.0] | 1.0 [0.645, 1.0] | 1.0 [0.645, 1.0] |
| critical | six | 2 | 1.0 [0.342, 1.0] | 1.0 [0.342, 1.0] | 1.0 [0.339, 1.0] | 1.0 [0.339, 1.0] |
| critical | speaker | 9 | 0.9 [0.596, 0.982] | 1.0 [0.701, 1.0] | 0.896 [0.59, 0.981] | 1.0 [0.699, 1.0] |
| critical | statement | 9 | 1.0 [0.701, 1.0] | 1.0 [0.701, 1.0] | 1.0 [0.647, 1.0] | 1.0 [0.647, 1.0] |
| critical | strongly certain/emphatic | 7 | 1.0 [0.566, 1.0] | 0.714 [0.359, 0.918] | 1.0 [0.473, 1.0] | 0.914 [0.431, 0.993] |
| critical | ten | 1 | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] |
| critical | third party | 2 | 1.0 [0.207, 1.0] | 0.5 [0.095, 0.905] | 1.0 [0.207, 1.0] | 0.387 [0.057, 0.868] |
| critical | twenty | 2 | 1.0 [0.342, 1.0] | 1.0 [0.342, 1.0] | 1.0 [0.304, 1.0] | 1.0 [0.304, 1.0] |
| critical | two | 3 | 1.0 [0.439, 1.0] | 1.0 [0.439, 1.0] | 1.0 [0.434, 1.0] | 1.0 [0.434, 1.0] |
| critical | unclear/mixed | 20 | 1.0 [0.824, 1.0] | 0.9 [0.699, 0.972] | 1.0 [0.726, 1.0] | 0.946 [0.67, 0.993] |
| critical | we/joint | 1 | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] | 1.0 [0.207, 1.0] |
| polarity | affirmative | 146 | 1.0 [0.974, 1.0] | 1.0 [0.974, 1.0] | 1.0 [0.959, 1.0] | 1.0 [0.959, 1.0] |
| polarity | mixed/unclear | 5 | 1.0 [0.566, 1.0] | 1.0 [0.566, 1.0] | 1.0 [0.398, 1.0] | 1.0 [0.398, 1.0] |
| polarity | negated | 11 | 1.0 [0.741, 1.0] | 1.0 [0.741, 1.0] | 1.0 [0.637, 1.0] | 1.0 [0.637, 1.0] |
| speech_act | offer/suggestion | 2 | 1.0 [0.342, 1.0] | 1.0 [0.342, 1.0] | 1.0 [0.319, 1.0] | 1.0 [0.319, 1.0] |
| speech_act | question | 19 | 1.0 [0.832, 1.0] | 1.0 [0.832, 1.0] | 1.0 [0.776, 1.0] | 1.0 [0.776, 1.0] |
| speech_act | refusal | 6 | 1.0 [0.61, 1.0] | 1.0 [0.61, 1.0] | 1.0 [0.501, 1.0] | 1.0 [0.501, 1.0] |
| speech_act | request/command | 28 | 0.9 [0.744, 0.965] | 0.964 [0.823, 0.994] | 0.939 [0.731, 0.989] | 0.997 [0.802, 1.0] |
| speech_act | statement | 103 | 0.99 [0.946, 0.998] | 0.971 [0.918, 0.99] | 0.999 [0.944, 1.0] | 0.981 [0.915, 0.996] |
| agent | addressee | 45 | 1.0 [0.916, 1.0] | 0.933 [0.821, 0.977] | 1.0 [0.864, 1.0] | 0.966 [0.816, 0.995] |
| agent | speaker | 66 | 0.943 [0.862, 0.978] | 1.0 [0.945, 1.0] | 0.956 [0.852, 0.988] | 1.0 [0.917, 1.0] |
| agent | third party | 28 | 1.0 [0.875, 1.0] | 0.964 [0.823, 0.994] | 1.0 [0.828, 1.0] | 0.96 [0.775, 0.994] |
| agent | unspecified | 7 | 1.0 [0.646, 1.0] | 1.0 [0.646, 1.0] | 1.0 [0.598, 1.0] | 1.0 [0.598, 1.0] |
| agent | we/joint | 8 | 1.0 [0.676, 1.0] | 1.0 [0.676, 1.0] | 1.0 [0.589, 1.0] | 1.0 [0.589, 1.0] |
| certainty | hedged/uncertain | 10 | 1.0 [0.701, 1.0] | 0.9 [0.596, 0.982] | 1.0 [0.625, 1.0] | 0.986 [0.614, 1.0] |
| certainty | n/a (question/request) | 46 | 0.882 [0.766, 0.945] | 0.978 [0.887, 0.996] | 0.945 [0.796, 0.987] | 0.998 [0.869, 1.0] |
| certainty | plain assertion | 96 | 0.978 [0.925, 0.994] | 0.948 [0.884, 0.978] | 0.997 [0.935, 1.0] | 0.972 [0.897, 0.993] |
| certainty | strongly certain/emphatic | 6 | 1.0 [0.566, 1.0] | 0.833 [0.436, 0.97] | 1.0 [0.492, 1.0] | 0.978 [0.482, 1.0] |
| politeness | none | 136 | 0.986 [0.949, 0.996] | 1.0 [0.973, 1.0] | 0.992 [0.942, 0.999] | 1.0 [0.956, 1.0] |
| politeness | please | 23 | 1.0 [0.857, 1.0] | 1.0 [0.857, 1.0] | 1.0 [0.797, 1.0] | 1.0 [0.797, 1.0] |
| politeness | softened request (could you/would you mind) | 4 | 1.0 [0.342, 1.0] | 0.5 [0.15, 0.85] | 1.0 [0.34, 1.0] | 0.647 [0.204, 0.929] |
| added_content | no | 87 | 0.961 [0.89, 0.986] | 0.839 [0.748, 0.902] | 0.97 [0.881, 0.993] | 0.9 [0.794, 0.955] |
| added_content | yes | 55 | 0.788 [0.675, 0.869] | 0.945 [0.851, 0.981] | 0.801 [0.669, 0.889] | 0.936 [0.817, 0.98] |

### 4e. Confusion matrices (rows = panel majority, columns = judge final; sampled, unweighted counts)

**polarity**

| panel \ judge | affirmative | mixed/unclear | negated |
|---|---|---|---|
| affirmative | 146 | 0 | 0 |
| mixed/unclear | 0 | 5 | 0 |
| negated | 0 | 0 | 11 |

**speech_act**

| panel \ judge | offer/suggestion | question | refusal | request/command | statement |
|---|---|---|---|---|---|
| offer/suggestion | 2 | 0 | 0 | 0 | 0 |
| question | 0 | 19 | 0 | 0 | 0 |
| refusal | 0 | 0 | 6 | 0 | 0 |
| request/command | 0 | 0 | 0 | 27 | 1 |
| statement | 0 | 0 | 0 | 3 | 100 |

**agent**

| panel \ judge | addressee | speaker | third party | unspecified | we/joint |
|---|---|---|---|---|---|
| addressee | 42 | 3 | 0 | 0 | 0 |
| speaker | 0 | 66 | 0 | 0 | 0 |
| third party | 0 | 1 | 27 | 0 | 0 |
| unspecified | 0 | 0 | 0 | 7 | 0 |
| we/joint | 0 | 0 | 0 | 0 | 8 |

**certainty**

| panel \ judge | hedged/uncertain | n/a (question/request) | plain assertion | strongly certain/emphatic |
|---|---|---|---|---|
| hedged/uncertain | 9 | 1 | 0 | 0 |
| n/a (question/request) | 0 | 45 | 1 | 0 |
| plain assertion | 0 | 5 | 91 | 0 |
| strongly certain/emphatic | 0 | 0 | 1 | 5 |

**politeness**

| panel \ judge | none | please | softened request (could you/would you mind) |
|---|---|---|---|
| none | 136 | 0 | 0 |
| please | 0 | 23 | 0 |
| softened request (could you/would you mind) | 2 | 0 | 2 |

**added_content**

| panel \ judge | no | yes |
|---|---|---|
| no | 73 | 14 |
| yes | 3 | 52 |

## 5. Contract-verdict validation (gold items, main1)

### Reference: panel majority (3 members)

Each sampled gold unit (text, family, visible input) maps to one or more scored occurrences in runs/main1/scored.parquet: different variants share bare/noncrit inputs, and models and prompts can produce the same text. For every occurrence I recomputed Violation (cue channels), Assumption (bare/noncrit) and constraint_preserving (cue channels) twice. The first run used the production judge labels; recomputing them reproduces the stored production verdicts exactly ({'ok': 993}). The second run used panel-majority labels for the critical and general dims. A verdict *flips* when the two runs give different non-missing values. When the panel has no majority on a needed label, that verdict is unresolved, not a flip. Production semantics ignore a missing general label; the `strict` columns in the CSV treat it as unresolved instead.

| verdict | occurrences (both defined) | unresolved (no panel majority) | occurrence flips | units with >=1 flip | units flipped, design-weighted | judge T/panel T | judge T/panel F | judge F/panel T | judge F/panel F | judge sens vs panel | judge spec vs panel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| violation | 144 | 0 | 3/144 [0.01, 0.06] | 2/99 [0.01, 0.07] | 0.014 | 25 | 1 | 2 | 116 | 25/27 [0.77, 0.98] | 116/117 [0.95, 1.00] |
| assumption | 187 | 0 | 2/187 [0.00, 0.04] | 1/57 [0.00, 0.09] | 0.004 | 151 | 2 | 0 | 34 | 151/151 [0.97, 1.00] | 34/36 [0.82, 0.98] |
| constraint_preserving | 144 | 0 | 5/144 [0.01, 0.08] | 4/99 [0.02, 0.10] | 0.028 | 105 | 2 | 3 | 34 | 105/108 [0.92, 0.99] | 34/36 [0.82, 0.98] |

Flipped units (5 distinct gold units, 7 occurrences). By family dimension: {'certainty': 3, 'agent': 1, 'time_quantity': 1}.

| item | family | channel | text | judge crit | panel crit | judge V/A/CP | panel V/A/CP |
|---|---|---|---|---|---|---|---|
| g-1888f32ca6 | cer-08 | chipall | We are waiting because the train is cancelled. | plain assertion | plain assertion | False/None/False | False/None/True |
| g-f792e412e3 | cer-09 | full | I lost my bank card now, can you help me? | plain assertion | plain assertion | False/None/False | False/None/True |
| g-1846e404da | agt-13 | chip1 | I tell the manager to stop the noise. | speaker | third party | False/None/True | True/None/False |
| g-5f2523000a | cer-13 | chip1 | I must have broken my ankle because I fell now. | hedged/uncertain | strongly certain/emphatic | True/None/False | False/None/True |
| g-5fbb0137cc | tq-08 | noncrit | I want to finish knitting my project. | now | unclear/mixed | None/True/None | None/False/None |

### Reference: gpt-5.6-sol + gpt-6-astra agreement (sensitivity)

Each sampled gold unit (text, family, visible input) maps to one or more scored occurrences in runs/main1/scored.parquet: different variants share bare/noncrit inputs, and models and prompts can produce the same text. For every occurrence I recomputed Violation (cue channels), Assumption (bare/noncrit) and constraint_preserving (cue channels) twice. The first run used the production judge labels; recomputing them reproduces the stored production verdicts exactly ({'ok': 993}). The second run used panel-majority labels for the critical and general dims. A verdict *flips* when the two runs give different non-missing values. When the panel has no majority on a needed label, that verdict is unresolved, not a flip. Production semantics ignore a missing general label; the `strict` columns in the CSV treat it as unresolved instead.

| verdict | occurrences (both defined) | unresolved (no panel majority) | occurrence flips | units with >=1 flip | units flipped, design-weighted | judge T/panel T | judge T/panel F | judge F/panel T | judge F/panel F | judge sens vs panel | judge spec vs panel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| violation | 141 | 3 | 3/141 [0.01, 0.06] | 2/96 [0.01, 0.07] | 0.014 | 25 | 1 | 2 | 113 | 25/27 [0.77, 0.98] | 113/114 [0.95, 1.00] |
| assumption | 179 | 8 | 2/179 [0.00, 0.04] | 1/54 [0.00, 0.10] | 0.004 | 145 | 2 | 0 | 32 | 145/145 [0.97, 1.00] | 32/34 [0.81, 0.98] |
| constraint_preserving | 141 | 3 | 7/141 [0.02, 0.10] | 6/96 [0.03, 0.13] | 0.038 | 102 | 2 | 5 | 32 | 102/107 [0.90, 0.98] | 32/34 [0.81, 0.98] |

Flipped units (7 distinct gold units, 9 occurrences). By family dimension: {'certainty': 3, 'polarity': 2, 'agent': 1, 'time_quantity': 1}.

| item | family | channel | text | judge crit | panel crit | judge V/A/CP | panel V/A/CP |
|---|---|---|---|---|---|---|---|
| g-1888f32ca6 | cer-08 | chipall | We are waiting because the train is cancelled. | plain assertion | plain assertion | False/None/False | False/None/True |
| g-f792e412e3 | cer-09 | full | I lost my bank card now, can you help me? | plain assertion | plain assertion | False/None/False | False/None/True |
| g-34d17550ef | pol-08 | full | There is no lift available now. | negated | negated | False/None/False | False/None/True |
| g-1846e404da | agt-13 | chip1 | I tell the manager to stop the noise. | speaker | third party | False/None/True | True/None/False |
| g-5f2523000a | cer-13 | chip1 | I must have broken my ankle because I fell now. | hedged/uncertain | strongly certain/emphatic | True/None/False | False/None/True |
| g-5fbb0137cc | tq-08 | noncrit | I want to finish knitting my project. | now | unclear/mixed | None/True/None | None/False/None |
| g-c7324ee764 | pol-14 | full | I'm disappointed that my older brother isn't coming to my graduation. | negated | negated | False/None/False | False/None/True |

### Reference: panel majority, quarantine-inclusive sensitivity

Each sampled gold unit (text, family, visible input) maps to one or more scored occurrences in runs/main1/scored.parquet: different variants share bare/noncrit inputs, and models and prompts can produce the same text. For every occurrence I recomputed Violation (cue channels), Assumption (bare/noncrit) and constraint_preserving (cue channels) twice. The first run used the production judge labels; recomputing them reproduces the stored production verdicts exactly ({'ok': 1041}). The second run used panel-majority labels for the critical and general dims. A verdict *flips* when the two runs give different non-missing values. When the panel has no majority on a needed label, that verdict is unresolved, not a flip. Production semantics ignore a missing general label; the `strict` columns in the CSV treat it as unresolved instead.

| verdict | occurrences (both defined) | unresolved (no panel majority) | occurrence flips | units with >=1 flip | units flipped, design-weighted | judge T/panel T | judge T/panel F | judge F/panel T | judge F/panel F | judge sens vs panel | judge spec vs panel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| violation | 158 | 0 | 3/158 [0.01, 0.05] | 2/105 [0.01, 0.07] | 0.013 | 26 | 1 | 2 | 129 | 26/28 [0.77, 0.98] | 129/130 [0.96, 1.00] |
| assumption | 189 | 0 | 2/189 [0.00, 0.04] | 1/58 [0.00, 0.09] | 0.004 | 153 | 2 | 0 | 34 | 153/153 [0.98, 1.00] | 34/36 [0.82, 0.98] |
| constraint_preserving | 158 | 0 | 5/158 [0.01, 0.07] | 4/105 [0.01, 0.09] | 0.027 | 118 | 2 | 3 | 35 | 118/121 [0.93, 0.99] | 35/37 [0.82, 0.98] |

Flipped units (5 distinct gold units, 7 occurrences). By family dimension: {'certainty': 3, 'agent': 1, 'time_quantity': 1}.

| item | family | channel | text | judge crit | panel crit | judge V/A/CP | panel V/A/CP |
|---|---|---|---|---|---|---|---|
| g-1888f32ca6 | cer-08 | chipall | We are waiting because the train is cancelled. | plain assertion | plain assertion | False/None/False | False/None/True |
| g-f792e412e3 | cer-09 | full | I lost my bank card now, can you help me? | plain assertion | plain assertion | False/None/False | False/None/True |
| g-1846e404da | agt-13 | chip1 | I tell the manager to stop the noise. | speaker | third party | False/None/True | True/None/False |
| g-5f2523000a | cer-13 | chip1 | I must have broken my ankle because I fell now. | hedged/uncertain | strongly certain/emphatic | True/None/False | False/None/True |
| g-5fbb0137cc | tq-08 | noncrit | I want to finish knitting my project. | now | unclear/mixed | None/True/None | None/False/None |

## 6. Refusal/acceptance quarantine

src/attribute.py now writes `quarantine_refusal_acceptance` (True for every row of a speech-act family with a refusal or acceptance variant: act-10, act-16 in main1). runs/main1/scored.parquet was regenerated; critical labels use annotation/label_resolution.jsonl across all refreshed runs. Old tables are preserved as scored_prev.parquet; analysis/reconciliation.md lists changed endpoints. src/analyze.py writes analysis/main1/sensitivity_quarantine_refusal_acceptance.csv; headline analyses now exclude quarantine throughout (58 families, including 8 speech-act families). The full 60-family analysis is retained in analysis/main1_quarantine_inclusive.

P0 speech-act critical match / constraint_preserving (pooled over 4 models; mean of model estimates):

| channel | all_speech_act_families critical_match | all_speech_act_families constraint_preserving | primary_excl_quarantine critical_match | primary_excl_quarantine constraint_preserving | quarantined_only critical_match | quarantined_only constraint_preserving |
|---|---|---|---|---|---|---|
| bare | 0.338 |  | 0.375 |  | 0.188 |  |
| noncrit | 0.375 |  | 0.438 |  | 0.125 |  |
| chip1 | 0.812 | 0.812 | 0.812 | 0.812 | 0.812 | 0.812 |
| chipall | 0.850 | 0.812 | 0.906 | 0.875 | 0.625 | 0.562 |
| full | 0.950 | 0.938 | 0.984 | 0.969 | 0.812 | 0.812 |

Quarantined families, P0 full channel, critical match: production (relaxed) 13/16, raw oracle 7/16. These numbers are sensitivity-only and cannot carry a headline.


## 7. What this licenses us to claim

Licensed now (machine evidence; describe it as such):
- The production oracle (J1+J2, arbiter, contract code) **satisfies the identity relation on all 120 authored
  test sources**: 0/120 contract false alarms, upper 95% bound 3%. It **flags 120/120 scoped single-value
  mutations** of those sources (lower bound 97%) on polarity, agent, certainty, politeness, speech act and
  time/quantity. This is minimum-functionality evidence on clean authored sentences. It is not an error rate on
  model outputs.
- On new balanced challenges, the oracle separates embedded actors, question vs request, and presence vs absence of
  explicit politeness markers without error (6/6 and 0/6 in each group). The pooled PREREG challenge gate passes
  at 22/24 and 0/24, with no slack.
- Against a 3-model codex panel majority on the 163 probability-sampled main1 units, judge labels agree at
  kappa >= .90 (design-weighted >= .97) on every extraction dimension. Recomputing the contract verdicts from panel
  labels changes Violation for about 1% of the weighted output population and constraint_preserving for about 3%.
  This bounds how much the reported verdicts *could* move under this alternative labeller. It does not show that
  either labeller is right.

Not licensed:
- **"Validated against human gold" or "passes the kappa >= .6 gate."** There are zero human returns. *[→ D-031: superseded for the earlier main1 inventory; H7 passed, see notice at top]* Every panel
  number is machine-machine agreement among GPT-family models, which share the codebook and probably some errors
  (finding 3). Per PREREG, headline automated claims stay provisional until the human double-coding of gold_core *[→ D-031: superseded for the earlier main1 inventory; H7 passed, see notice at top]*
  arrives. Then run `score_gold.py --human annotation/returns/*.csv --panel ...`. The gate is evaluated only in the
  human section.
- **Any primary speech-act claim that uses the refusal/acceptance families**, including the "5/8 refusals survive"
  result. The relaxed acceptance predicate misses 2/2 statement substitutions on keyed items. The raw predicate
  instead fails the D-015 sentence when J1 is used alone. Report act-10/act-16 only as sensitivity, both raw and
  relaxed: P0 full critical match is 13/16 relaxed against 7/16 raw. On the 8 remaining speech-act families, P0
  full critical match is .984 and chipall is .906, against .950 and .850 with the quarantined families included.
- **Added-content headlines.** Panel alpha is .41, judge kappa .76, 11% of sampled units are unlabelled, and there
  are false positives on keyword-complete challenges.
- **Fine certainty-degree claims** (plain vs emphatic). Panel-vs-judge disagreements concentrate there
  (plain/hedged -> emphatic), and the contract treats emphatic as honouring plain by design.
- **Idiomatic negation and vague quantity.** On ch-08 ("can't wait") and ch-22 ("a couple of") both the judge and
  the panel disagree with the key. Treat them as known oracle blind spots.

Remaining W-A work: human double-coding of gold_core (100 items) with `score_gold.py --human`; *[→ D-031: superseded for the earlier main1 inventory; H7 passed, see notice at top]* a symmetric
acceptance/refusal predicate, or a separate response-particle feature, that passes both the statement-substitution
mutants and the identity relation using J1 or J2 alone; and an added-content tiebreak policy.

## Files

- annotation/challenge_items_r2.jsonl: 48 new keyed challenges. analysis/oracle/source_mutations.jsonl: 120 keyed
  mutations. analysis/oracle/challenge_keys_frozen.sha256: hashes and freeze time.
- runs/oracle_inject/, runs/oracle_challenges/: synthetic runs (outputs, judgments, arbiter.jsonl with the 3
  arbiter rows from a fresh blind Claude subagent that saw only the codebook, the text and the J1/J2 labels).
- analysis/oracle/injection_results.csv, challenge_results.csv, verdict_validation{,_sens_sol_astra}.csv.
- annotation/judge_validation_main1{,_sens_sol_astra}.json/.csv (sections `human` and `panel`, kept separate),
  annotation/panel_majority_main1{,_sens_sol_astra}.csv (provenance = machine).
- Code: src/oracle_wa.py, src/oracle_report.py (new); src/score_gold.py (`--human`/`--panel`, arbiter fill,
  weighted metrics, invalid-option handling); src/attribute.py (quarantine flag and endpoints);
  src/analyze.py (quarantine sensitivity table).

