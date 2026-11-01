# W-C critical-label arbitration (c2 decision ACTION 2)

Date 2026-11-01. Arbiter: one Claude model (`claude-opus-5-5`), which is cross-family relative to the GPT judge (D-002, D-016). No generator, judge or API calls were made, and no GPU was used. No prompt or codebook was changed. This arbitration took place **after the outcomes were known**. The registered W-C analysis had already been read (report.md, decision memo). It is therefore a post-hoc resolution of a deviation, the J1 fallback in `orchestration/r2c_judge.sh`. It is not a prospective step. `FREEZE.md` and `freeze_analysis.py` were not rerun or edited.

## Inventory (frozen before labelling)

`arbiter_inventory.json`, inventory sha256 `c7261048108b1f195a25e7e84f0b8a33d9aa12147fa672994305c81359dea9ff`. It was written by `arbitration/freeze_inventory.py` from the `needs_arbiter` keys in `runs/r2c1/judgments.jsonl` and the fallback rows of the J1-fallback `scored.parquet`. The script printed no labels.

| level | count |
|---|---|
| fallback scored rows (`critical_source == J1`) | **259** (P0 24, P2 172, S3 63) |
| J-units `(text_id, family_id, input_text)`, the attribute.py key | **177** |
| production extraction units: judge.py A-units `(text_id, dimension, critical_options)` | **177** |
| arbitration decisions made | **177** (one per A-unit; 0 API calls) |

Deduplication did not reduce the count: each A-unit occurs in exactly one J-unit. The 259 rows come from repeated occurrences of the same unit. 142 units have 1 row, 17 have 2, 6 have 3, 9 have 4, 2 have 6 and 1 has 17.

## Procedure and blinding

- `arbitration/blind_view.py` printed only three things for each A-unit: the output text, the production critical question (`judge.critical_question`) and its options. Units were shown in sha256(A-unit) order. The view hid the input, authored reference/variant value, family, model, prompt/arm, channel, J1/J2 labels and evidence.
- All 177 labels and one-line rationales were decided by reading, under CODEBOOK CB-1..CB-9 and the judge rule text. They are recorded in `arbitration/decisions.tsv`. Earlier D-016 arbiter decisions from other runs (`runs/{main1,pilot1,expB1,expC1,...}/arbiter.jsonl`) were consulted as precedent. These include "I want X, please" = request/command, "Will you be V-ing?" = question about plans, and declarative + "please?" = question.
- **Visible input / source disclosure.** Under D-016 the arbiter may see the visible input. In the `full` channel that input is `The user typed: <authored source>`, so it reveals the source and hence the reference. **This arbitration did not display any input**: the critical production extraction is output-only, and all decisions used output-only information. The inventory JSON does store `input_text` as a join key, but it was not printed during labelling.
- `arbitration/write_arbiter.py` wrote `runs/r2c1/arbiter.jsonl` (sha256 `9dd9d4879fb46b488690f960b4c96e91ceb2e33f2e2a009011560b352a96eadc`). It writes one row per J-unit with the keys `text_id, family_id, input_text, critical, rationale, arbiter_model`, plus `text, dimension, a_unit, arbitration_view, inventory_sha256`. Only **after** writing did the script compare the labels with J1/J2.
- **Post-decision exposure.** After the arbiter file was written and hashed, a diagnostic query printed the reference value, model and J1/J2 for the 24 P0 rows. No label was changed afterwards, and the file hash above is unchanged.
- The unknown-masked analysis was snapshotted byte-for-byte in `snapshot_unknown_masked/` (`SHA256SUMS`). The snapshot includes the J1-fallback `runs/r2c1/scored.parquet` and `endpoints.json`. After that, `python src/attribute.py --run r2c1` was rerun **without `--fallback`**. Result: critical_source `{agree: 66907, arbiter: 259}`, 0 unresolved. No agreed label or non-critical column changed. Then `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/r2c/analyze_confirmatory.py > analysis/r2c/analysis_run.log` was run.
- **Analyzer edit (disclosed).** `analyze_confirmatory.py` contained hard-coded prose ("No r2c1 arbiter file exists", "adjudication still outstanding"). It also built its `supplied_J1_fallback` sensitivity from the live parquet. A minimal edit makes the following conditional on `critical_source == 'arbiter'`:
  - the prose;
  - the `primary.json` status;
  - a new `arbiter_resolved_rows` headline field;
  - the J1 sensitivity, which now reads the snapshot J1 parquet;
  - an added `unknown_masked_pre_arbitration` sensitivity.

  The estimators, the masking of J1/J2 fallback and the bootstrap are unchanged. With no arbiter rows, the old behaviour is reproduced.

## Agreement with J1/J2

| | units (177) | scored rows (259) |
|---|---|---|
| arbiter = J1 | 123 (69.5%) | 177 |
| arbiter = J2 | 47 (26.6%) | 75 |
| neither | 7 (4.0%) | 7 |

By dimension (units): speech act 110 (J1 83 / J2 23 / neither 4); polarity 34 (J1 13 / J2 18 / neither 3); politeness 33 (J1 27 / J2 6). The arbiter label differs from the J1 fallback on **82/259 rows**.

### Disagreement types (units; full list in `arbitration/agreement.json`, per unit in `arbitration/unit_comparison.csv`)

| dimension | J1/J2 split | arbiter outcome | units | rule applied |
|---|---|---|---|---|
| speech act | request/command vs statement | request/command | 39 | "I want/need X, please" = an ask containing please; "I tell/I'm telling you to X" = performative directive |
| politeness | plain vs polite | polite (all 33) | 33 | May I / would … if you could / would it be possible / when you have a chance are listed softeners in both judge rule texts; one "Can you kindly" judged please-equivalent (least certain) |
| polarity | negated vs unclear/mixed | negated 25, unclear 1, affirmative 1 | 27 | negation in a directly embedded complement (tell me why … don't, told X I wasn't, I'm surprised … aren't) = negated |
| speech act | question vs request/command | request 17, question 15 | 32 | Will you + task for the speaker / are you able to = request; Will you be V-ing / own plans / Can-Could I …, please (CB-9) / please on information questions = question |
| speech act | offer/suggestion vs question | offer/suggestion | 10 | should we / shall I / could we / would you like |
| speech act | request/command vs unclear/mixed | request 8, unclear 2 | 10 | imperative/please + reason clause = request; fragments = unclear |
| speech act | statement vs unclear/mixed | question 3, unclear 2, statement 1 | 6 | declarative indirect if-question with "?" = question; fragments = unclear |
| speech act | question vs statement | question 5, request 1 | 6 | indirect questions; "I need you to X?" = request |
| polarity | affirmative vs negated / unclear | affirmative 3, negated 3, unclear 1 | 7 | negation only inside a relative clause, or lexical ("failed to", "unavailable") = affirmative; contrastive "X, not Y" / "not X but Y" = unclear/mixed |
| speech act | other (acceptance vs statement, offer vs statement/unclear, question vs unclear) | — | 7 | [YES] + doing it now = acceptance; [YES] + past report = statement |

Seven units match neither judge. In three, an indirect if-question with "?" was labelled statement by J1 and unclear by J2. In two, an embedded negated complement was labelled affirmative by J2 and unclear by J1. One is "I need you to top up my bus pass?", labelled request (J1 statement, J2 question). The last is "Is there any work that doesn't need heating?", labelled affirmative because the negation is only in the relative clause.

## Before/after: registered primary contrasts (all prompt P0)

Before = the snapshot with fallback masked as unknown (protocol-aligned, C28). After = arbiter-resolved. 10,000 cluster resamples, seed 20261031, Holm across the three contrasts.

| contrast | before: estimate [95% CI]; n/total (missing) | after: estimate [95% CI]; n/total (missing) | Holm p before → after | reject .05 |
|---|---|---|---|---|
| **P1** speech-act chip1−noncrit | **31.65 pp [25.22, 38.19]**; 613/624 (11); 194/613; eff. clusters 32.9 | **31.41 pp [25.00, 37.94]**; 624/624 (0); 196/624; eff. 33.1 | .0003 → .0003 | yes → yes |
| **P2** full politeness addition−removal | 6.25 pp [2.50, 10.00]; 320/320 (0) | 6.25 pp [2.50, 10.00]; 320/320 (0) | .0009 → .0009 | yes → yes |
| **P3** bare affirmative share−0.5 | 49.37 pp [48.42, 50.00]; 319/320 (1 unclear reading, not unknown) | identical | .0003 → .0003 | yes → yes |

- **P1** is the only primary contrast that changes. The 11 previously missing pairs (9 Gemma, 2 Llama) now enter. Their paired differences are +1 ×5, 0 ×3 and −1 ×3, so they sum to +2. The two P1 arms change as follows: chip1 match 73.51% (619/624) → **73.24% [68.97, 77.56] (624/624)**; noncrit match 41.75% (618/624) → **41.83% [36.99, 46.19] (624/624)**.
- **P2 and P3 are byte-identical.** None of the 259 arbitrated rows falls in P0 full politeness or P0 bare polarity. P2 additions 8.12% and removals 1.88% are unchanged, as is P3 317 affirmative / 2 negated.
- Per model, only P1 changes:

| P1 model | before | after |
|---|---|---|
| gemma3-4b | 36.73 pp [27.16, 46.94]; 147/156 | **35.26 pp [25.56, 45.59]; 156/156** |
| llama3.1-8b | 20.13 pp [11.11, 28.79]; 154/156 | **20.51 pp [12.19, 28.87]; 156/156** |
| gpt-6.1-terra | 41.67 pp; 156/156 | unchanged |
| qwen2.5-7b | 28.21 pp; 156/156 | unchanged |

  All P2 and P3 per-model estimates are unchanged. The P1 construction strata are now adversarial 21.88 (64/64), drafted 35.83 (240/240) and seeded 30.00 (320/320).
- Sensitivities (`primary_sensitivity.csv`): `supplied_J1_fallback` P1 is still 31.41 [24.85, 38.04] (624/624). It has the same point estimate as the arbitrated result, with a different pair composition. The added `unknown_masked_pre_arbitration` reproduces the "before" column exactly. Excluding early-cache families gives P1 29.56 [23.06, 36.27] (592/592).

### Secondary numbers that move (for ledger/captions; not new tests)

- **C34**: speech-act chip1 is now **73.24% [68.97, 77.56], 624/624**. Chip1−full is now **−25.96 pp [−30.36, −21.53], 624 pairs**. Before, these were 73.51% (619/624) and −25.69 [−30.07, −21.28]. Chipall is now 74.84% (was 75.12%).
- Speech-act noncrit−bare is now +2.56 [0.60, 4.58] (was +2.27). Politeness chip1 is now 89.53% (was 89.67%). Politeness chip1−full is now −5.47 (was −5.32).
- Speech-act coverage@3 is now P2 53.21% (312/312) and S3 3.85% (312/312). Before, these were 53.23% (310/312) and 3.86% (311/312).
- The headline keys changed are listed in `headline.json` against `snapshot_unknown_masked/headline.json`. 19 keys differ, mostly P1, coverage and ladder; `unadjudicated_fallback_rows` 259 → 0.

## Limits

- A single arbiter decided each unit without independent re-arbitration, and arbitration happened after the outcomes were known. Speech-act boundaries carry most of the judgement: "Will you …?" plans versus request, "I want X, please", and indirect questions marked with "?".
- The arbitration removes the missingness. It does not remove the early-cache or chronology qualifications.
- Paper macros and figures (`paper/figs/r2c`, the SE4All/CALE macro scripts) and `verify_artifacts.py` were **not** rerun. The C28/C29/C34 ledger text should receive a versioned update and must not silently replace the protocol-aligned snapshot (decision memo, C28/C29 note).
