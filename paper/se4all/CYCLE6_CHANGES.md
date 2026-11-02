# SE4All cycle 6 changes (2026-11-01 night)

Build: docker latexmk, 8 pages including references, all pages viewed. Not committed. No model calls.

- **Interval labels**: Sec. III-A says "percentile-bootstrap lower bound above 31.2" and now states that the writer-level t interval for the speech-act chip (Table II) is wider, lower bound 28.9. Evidence-sets paragraph lists the exceptions (t, Wilson, kappa cluster bootstrap); Table II caption labels t vs percentile.
- **Faults nobody seeded**: `src/oracle_natural_pr.py` gained `pooled_heldout_sets` (Part 10 + Part 13 = second gold set + human-written pairs); summary.json/report.md regenerated (unchanged otherwise). New macros `nat_ho_*`, `nat_dev_*`. Held-out violation P 87.8 [74.5, 94.7], R 92.3 [79.7, 97.3] (39 positives); development items reported separately; pooled kept as secondary. Abstract leads with the held-out result and gives the precision interval. "Part 10" replaced by "second gold set".
- **R4**: floor shown from `analysis/r2d/headline.json`: single-chip repeat disagreement 0/160 for Qwen and Llama, so raw = floor-adjusted; both-chip floor (12/320, 5/320) gives 9.38 and 7.03 pp, now given with intervals (macros `wdqa_rep*`, `wdqa_brep*`, `wdqa_db*`). "above the repeat floor" removed; Table I wording changed.
- **Table VI**: "missed" renamed "passed the bad rule".
- **Abstract**: about 150 words; numbers: mutants/false alarms, held-out precision/recall, default share, act-chip range. "Three ways" now "seeded mutants, identity checks and human labels". Legend result and string-overlap number dropped from abstract.
- **References**: Sensei (delara2026sensei) dropped (not in lit/, non-essential). Navneet 2026 marked `% VERIFY` (Crossref only, not in lit/). Lacosse and Al-Tamimi are in lit/. Frisch is arXiv-verified in bib. Channel-ladder file path removed from Table III caption.
- Not done: Table V/VI merge, composition-study move, NLI baseline, outside-developer test (need new evidence or space).
