# Deviations from PLAN.md (log only after outcomes; never edit the plan)

(none)

## 2026-11-18 Part B build (before any annotation/judge/score)
- Gemini daily quota (HTTP 429 PerDay) hit during the scope family walk: 146 of the 150 allowed calls returned a quota error and counted against the cap (cap 150 set by the run task, plan cap 220). Scope mutants: 4 of 20 built (all gemini); other four families 20/20 by template. Shortfall 16 scope mutants is NOT repaired (FREEZE_B written; no source replaced). Planned synthetic top-up (codex-lb) not run; any later top-up needs a new labelled round.
- Template-only families therefore have method=template for all 80 of their mutants; the plan's LLM-family stratum is only 4 scope items.
- Controls were drawn before mutants in the build (so control quotas are not starved by mutant templates); controls and mutants share no source family.
- Part A: FB05 failed the validate step (importing the module as a script requires argv) and was replaced by reserve R01 (logged in faults_table.json swaps); F5 sites existed only in analyze.py (and 1 in score_listener_study), so 4 F5 faults moved to AN per plan (moved_from recorded); module counts therefore differ from the plan quota (AN 10, RA/MA/ML/MF 4 each).
