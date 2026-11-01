# Judge, attribution and annotation (SPEC v0.1, D-007, CB-1..CB-5)

`outputs.jsonl` (explode.py) → `judge.py` → `judgments.jsonl` → `attribute.py` →
`scored.parquet` + `endpoints.json`. Then `make_gold.py` → `annotate.html` → `score_gold.py`.

Run everything from the repo root after `. .venv/bin/activate`. The API key is read by
`models.api_key()` and is never printed or written.

| file | role |
|---|---|
| `src/labels.py` | Option strings (verbatim from SPEC), definitions, chip→spec sets, `critical_match` (D-007). |
| `src/layer0.py` | Deterministic general-dimension labels (spaCy + lexicons). |
| `src/runio.py` | Run-dir adapter. Reads explode's `outputs.jsonl`, or a fixture `exploded.jsonl`. Items come from all `data/items/*.jsonl`. Join key is `text_id`. |
| `src/judge.py` | LLM extraction judge, J1/J2, cache, agreement report. |
| `src/attribute.py` | Violation / Assumption / stance additions / endpoints. |
| `src/agree_stats.py` | κ, confusion, P/R (no sklearn). |
| `src/make_gold.py` | Stratified PPS gold sample + annotator JSON + key. |
| `src/score_gold.py` | Human α (nominal), judge-vs-human per dimension, cal/test split. |
| `annotation/annotate.html` | Static keyboard-only annotation tool. |
| `annotation/CODEBOOK.md` | Annotator rules and open questions for autistic reviewers. |
| `tests/test_layer0.py`, `tests/make_fixture.py` | Unit test; 58-occurrence fixture with hand gold. |

## Commands
```bash
python tests/test_layer0.py                     # layer0 unit test
python tests/make_fixture.py                    # fixture -> runs/fixture + tests/fixtures
python src/judge.py --run fixture --gold tests/fixtures/fixture_gold.jsonl
python src/attribute.py --run fixture
python src/judge.py --run pilot1                # J1+J2, both passes, ~16 concurrent calls
python src/judge.py --run pilot1 --report-only  # agreement report from judgments.jsonl
python src/attribute.py --run pilot1 [--fallback J1]
python src/make_gold.py --run pilot1 --n 160    # annotation/gold_items_pilot1.json + gold_key
python src/score_gold.py --self-check
python src/score_gold.py --run pilot1 --csv 'annotation/returns/*.csv'
```
To annotate, open `annotation/annotate.html` in any browser, enter your ID, load
`gold_items_<run>.json`, and press Download CSV when done. Progress autosaves in the
browser.

## Judge design (`judge.py`)
- **Blind by construction.** There are two calls per batch:
  - **Pass A** sees only the output sentence, the critical question with its options, and the five general dimensions.
  - **Pass B** (added_content) sees the sentence and the visible input string.
  - Neither pass sees the source, model, prompt, channel or family.
- **Units.**
  - A-unit = (text_id, dimension, options).
  - B-unit = (text_id, input_text).
  - Rows in `judgments.jsonl` = (text_id, family_id, input_text).
  - Identical texts from different models or requests are judged once.
- **J1 vs J2.** The two variants use different system and user wording and rule phrasing. J2 reverses every option list and the order of the dimensions, and the item order inside a batch differs.
- **Output format.** JSON is forced with `response_format=json_schema`, strict, using per-batch enums. The endpoint supports this.
  - A critical label outside that item's own option list is rejected.
  - Missing or invalid items are asked again, up to 5 attempts with backoff.
- **Settings.** Batch 25, concurrency 16, model `gpt-6.1-sol`, `reasoning_effort=low`.
- **Cache.** `cache/judge/<variant>.jsonl`, keyed by sha256(variant, template sha, model, text, dimension, options[, input]). Any prompt edit changes the template sha and therefore re-judges.
- **Final labels.**
  - critical = J1 if J1 == J2; otherwise `needs_arbiter=true` and critical=null.
  - General dims use agreement, then layer0 as tiebreaker, then null.
  - added_content uses agreement, else null.
  - An arbiter (a planned cross-family Claude model) writes `runs/<run>/arbiter.jsonl` rows `{text_id, family_id, input_text, critical}`, and attribute.py picks them up.
- **Logs.** `judge_calls.jsonl` (per call: latency, tokens), `judge_perf.json`, `judge_report.json`.

## Attribution (`attribute.py`)
This follows SPEC "Deterministic attribution" literally. The column glossary is in the module docstring. Key choices:
- **Spec sets.** A variant's general spec is a *set* of honouring values built from `all_chips`:
  - `[SURE]` = plain or emphatic (D-007);
  - `[PLEASE]` = any polite marker;
  - unspecified dimensions default to affirmative / statement / plain / none;
  - agent has no default.
- **Which dimensions are "in the input".**
  - `chip1`: the variant's chips.
  - `chipall`: all_chips.
  - `full`: everything.
  - `bare` / `noncrit`: nothing.
  - A mismatch on a dimension in the input is a contradiction (`contra_*`, used in co-primary 1). A mismatch otherwise is a stance addition (`addition_*`).
- **The family's own critical dimension** is excluded from `contra_*` and `addition_*`, since it is already scored as Violation or Assumption.
- **Directed flags.**
  - `politeness_added` = spec none, output has a marker.
  - `hedge_added`.
  - `emphatic_added` = output emphatic while layer0 on the *source* is not emphatic (D-007 logging).
- **Non-completions.** Errored or empty generations come from `generations.jsonl` and count as constraint-preserving = False.
- **Shared requests.** bare/noncrit requests are shared by A and B, so the commitment and direction endpoints count each (request, suggestion) once.
- **Endpoints** are written to `endpoints.json`:
  - cp1 by model × prompt × channel;
  - violation by model × dimension;
  - cp2 commitment and direction (share_A against 50%);
  - coverage@3 for P2 and S3;
  - stance additions.
  - There are no CIs yet. The cluster is family, so analysis should bootstrap by family.

## Layer 0 (`layer0.py`)
- **Hedges.** Hedges come from `old/src/hedges.txt`, matched longest-first and non-overlapping (this fixes the old double count).
- **Contractions.** spaCy splits contractions ("do" + "n't"). Tokens are re-merged into surface words before matching, so "if you don't mind" still matches.
- **Lexicon routing.** hedges.txt is a hedge-*rate* lexicon. Some of its entries are routed away from certainty, with explicit, reviewable sets:
  - can/could/would/should;
  - bare think/feel;
  - frequency adverbs;
  - approximators;
  - softeners, which go to politeness.
- **Rules.** Rules follow the codebook: D-007 "Can I" = question; CB-1 "you need to" = statement; CB-3/4 agent of the embedded clause, statal passives, body parts.
- **Known blind spots.**
  - Sarcasm, ellipsis and fragments.
  - Multi-clause speech acts.
  - "No problem" (lexically negated, pragmatically affirmative).
  - Refusals without a formula ("I don't want to").
  - Polarity of uncertainty negation ("not sure" is mixed/unclear only through the parse).

## Gold sampling (`make_gold.py`)
- **Strata** are dimension × first model × judge critical label (or DISAGREE).
- **Weights.** w = 1 + 3·(J1≠J2 on any dim) + 2·positive, then divided by √(stratum size).
  - positive = Violation, Assumption, stance addition or added content, taken from `scored.parquet`.
- **Sampling** is Poisson PPS with π = min(1, c·w), so Σπ = n. Inclusion probabilities are exact, which allows IPW / Horvitz–Thompson. The realised n is close to the target, not exact.
- **Held-out info.** Annotators get only the sentence, the questions and options, and the input for added_content. `gold_key_<run>.csv` holds the unit, models, stratum, π, and judge and layer0 labels.
- **Split.** The calibration/test split is done in `score_gold.py`: a seeded hash of item_id, 25% calibration. Report the TEST split for H7 (κ ≥ 0.6).
