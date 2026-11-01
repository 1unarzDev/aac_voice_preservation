# Loss, Violation, or Assumption? Meaning and stance preservation in LLM keyword expansion for AAC

Research code, data and analysis for an audit of LLM keyword-to-sentence expansion in augmentative and alternative
communication (AAC). Controlled input channels attribute changes in meaning/stance (polarity, roles, certainty,
speech act, politeness, time/quantity) to information **lost** in compression, **violations** of cues the model
received, or **assumptions** made under ambiguous input; and evaluate commitment "chips" and suggestion sets.

Work in progress (Nov 2026). Start with `orchestration/PLAN.md`, `orchestration/SPEC.md`, `orchestration/decision_log.md`.
- `src/` pipeline (see `src/README.md`, `src/README_judge.md`), `data/items/` probe families, `runs/` generations + judgments,
  `analysis/` tables and figures, `annotation/` codebook + human annotation tool, `paper/` drafts, `lit/` literature reviews.
- Third-party data licences: `data/raw/LICENSES.md`. Model weights are not included (see `src/models.py` for sources and hashes).
