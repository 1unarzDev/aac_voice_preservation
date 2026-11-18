# Part 28 scoring deviations (2026-11-18)
1. Output location: the frozen scorer writes to analysis/listener_human/ (its default); human.md and summary.json (merged summary) were written to analysis/listener/ as requested. No analysis choice changed.
2. Mixed-model sensitivity (PLAN section 5) not run: statsmodels is not installed; plan says the bootstrap then stands alone.
3. contrasts.csv shows p_boot = 2.0 for G1 - bare: all bootstrap differences are exactly 0, so the scorer's two-sided formula exceeds 1. It is not a p-value; interpreted as "no change". Scorer unchanged.
4. The plan's headline sentence is not stated as a finding: the Q1 reversal difference interval includes zero (see human.md).
No exclusions were made; no listener, item or condition was dropped; nothing imputed.
