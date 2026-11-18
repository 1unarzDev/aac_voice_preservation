# Deviations (Part 29 scoring, 2026-11-18)
1. The judge was run on a purpose-built run directory (runs/oracle_indep_judge, 150 candidates, all items, not only confirmed ones, so no exclusion depended on any oracle output). Critical options are the canonical set for the target dimension (negation ops from non-polarity source pools use the polarity options). The input field is the placeholder "(none)"; pass A does not see it.
2. Arbiter: the blind view (src/arbiter_tool.py) prints one header per dimension, with items from other dimensions listed below it; decisions were made with per-item dimension from the inventory (still blind: text and dimension only). Arbiter model claude-sonnet-5-5 (tool default).
3. Scorer output was written to analysis/oracle_indep/ rather than the default analysis/oracle_indep_human/. Extra stratum-level McNemar and per-operator in-stratum counts computed ad hoc from the same functions (in summary.json).
No change to frozen rules, thresholds or exclusions.
