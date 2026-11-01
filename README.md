# Loss, Violation, or Assumption? Meaning and stance preservation in LLM keyword expansion for AAC

Research code, data and analyses for an audit of LLM keyword-to-sentence expansion in augmentative and alternative
communication (AAC). Controlled input channels attribute changes in meaning and stance (polarity, roles, certainty,
speech act, politeness, time/quantity) to information **lost** in compression, **violations** of cues the model
received, or **assumptions** made under ambiguous input. The repository also evaluates commitment "chips",
suggestion sets and two interventions (a guard and span-aware sets).

Two papers are built from this repository: `paper/se4all/` (SE4All @ ICSE 2027) and `paper/caleai/` (CALE-AI @ AAAI-27).
`paper/humane/` is an unsubmitted draft.

## Repository map

| Path | Contents |
|---|---|
| `src/` | Pipeline: request building, generation, extraction (judge), attribution, analysis, oracle checks, interventions. See `src/README.md` and `src/README_judge.md`. |
| `src/authoring/` | Builders for the round-2 item files (`data/items/r2_*.jsonl`). |
| `data/items/` | Probe families (minimal pairs) for every study split. |
| `data/specs/`, `data/raw/` | Corpus samples and third-party source data (see licences below). |
| `prompts/` | Prompt templates and the chip legend. |
| `runs/<run>/` | Stored generations, judgments, scored tables and run configs. |
| `analysis/` | Analysis outputs: per-study reports, tables, frozen evidence snapshots and manifests. `analysis/EVIDENCE_MAP.md` is the current routing table from each claim to its source files. |
| `analysis/examples/` | Selected-example manifests (`story_evidence.v2.json` is the current gallery source) and the archived selector scripts. |
| `analysis/derived/` | Derived exploratory checks (hypothesis screens, guard-increment check, W-B cue-source audit). |
| `analysis/item_verification/` | Independent item-verification tables for the probe families. |
| `annotation/` | Codebook, decision rules, gold keys, human returns and validation results. |
| `annotation_package/` | Self-contained, offline package handed to human annotators (also `annotation_package.zip`). |
| `paper/` | LaTeX sources, generated macros/tables and figure scripts. |
| `tests/` | Unit and integration tests. |

Some frozen manifests record file hashes under the working paths the files had when the hashes were taken.
`src/provenance_paths.py` maps every such recorded path to its published, byte-identical copy, so all recorded
hashes still verify.

## Reproducing the papers

Requirements: Python 3.12 with pandas, numpy, pyarrow, scipy, matplotlib (spaCy only for the corpus analysis in
`src/s1_analyze.py`), and Docker for LaTeX. Rebuilding the papers needs no model, GPU or network access: every
number is read from stored tables under `runs/` and `analysis/`.

```bash
export OPENBLAS_NUM_THREADS=1
PY=.venv/bin/python            # any Python 3.12 environment with the packages above

# Evidence map, example manifests and captions (offline, idempotent)
$PY src/validate_cue_inputs.py replay
$PY analysis/guard_wc/acceptance_check.py
$PY src/c3_evidence.py
$PY src/refresh_captions.py
$PY src/c3_evidence.py          # re-verifies captions and manifests

# SE4All
$PY paper/se4all/make_macros.py
$PY paper/figs/make_ratchet_column.py
$PY paper/figs/make_r2d_column.py

# CALE-AI
$PY paper/caleai/caleai_evidence.py
$PY paper/caleai/make_macros.py
$PY paper/caleai/figs/make_caleai_figs.py

# PDFs
for p in se4all caleai; do
  docker run --rm -v "$PWD":/w -w /w/paper/$p texlive/texlive:latest-full latexmk -pdf main.tex
done
```

Tests: `for t in tests/test_*.py; do $PY "$t"; done`. The HTML annotation tools have jsdom tests
(`NODE_PATH=<dir with jsdom> node tests/test_repair_audit_html.js annotation_package/repair_audit.html`, and likewise
for `wb_corpus_check.html` and `wc_source_check.html`).

Regenerating model outputs or judgments is a separate, GPU/API-dependent step; see `src/README.md`. Model weights
are not included; `models/SHA256SUMS` and `src/models.py` list the sources and hashes. Judge calls are cached under
`cache/judge/`, which is created on demand and not tracked.

## Data licences

Third-party data and their licences are listed in `data/raw/LICENSES.md`:

- AACText (Vertanen & Kristensson 2011, "The Imagination of Crowds", EMNLP): CC BY 4.0. Only
  `sent_{train,dev,test}_aac.txt` are used. These are fictional, crowdsourced AAC-like messages.
- HANS (McCoy, Pavlick & Linzen 2019): MIT License.
- ScoNe (She et al. 2023): CC0 1.0.

All probe families in `data/items/` are constructed test items, not messages from AAC users.

## Annotation package

`annotation_package/` (zipped as `annotation_package.zip`) is what human annotators receive. It works offline in a
desktop browser and contains the annotation tool (`annotate.html`), the codebook (`CODEBOOK.md`, `CB_rules.md`), the
item parts (`part1_core.json` to `part3_extraB.json`) and three optional audits (`repair_audit.html`,
`wc_source_check.html`, `wb_corpus_check.html`). Instructions are in `annotation_package/README.md`. Answer keys and
model labels live in `annotation/` and are deliberately left out of the package. Returned files go to
`annotation/returns*/`. `src/score_gold.py` scores them.
