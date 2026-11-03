# whole_message Follow-up F1 (2026-11-03): leave-one-writer-out for M1-free and word count

Label: POST-PILOT follow-up, CPU only, stored scores only (no model calls). Rule pre-declared in PLAN.md ("Follow-up F1 pre-declared rule") before the script ran. Script: `src/frontier_whole_message_followup_lowo.py`. Outputs: `followup_lowo.csv`, `followup_summary.json`. Source of SYNTHESIS.md section 5 item 5.

## What was computed
Data: `r2_validity_features.csv`. Primary subset chip1 (n = 97 outputs, 20 writers); secondary all200 (n = 195, 20 writers). Outcome: writer rejection (L1). Scores: M1free_gpt and T1_wordcount.
(a) drop each writer in turn and recompute both AUROCs and the paired delta (M1-free minus word count);
(b) delete-one writer jackknife SE and normal 95% CI of the delta;
(c) writer-stratified AUROC (within-writer pairs only), which removes between-writer base-rate differences.

## Result
| subset | AUROC M1-free | AUROC word count | delta | LOWO range of M1-free | LOWO range of delta | jackknife 95% CI of delta | stratified AUROC (M1-free / word count) |
|---|---|---|---|---|---|---|---|
| chip1 (n = 97) | .766 | .724 | +.042 | .751 to .784 | +.015 to +.068 | [-.076, +.159] (SE .060) | .744 / .641 (78 pairs) |
| all200 (n = 195) | .766 | .704 | +.063 | .751 to .782 | +.042 to +.083 | [-.035, +.161] (SE .050) | .779 / .670 (315 pairs) |

Most influential writers: P20, P03, P10 (chip1); P16, P10, P12 (all200).

## Verdict under the declared rule
- "M1-free beats word count" needs the jackknife CI of the delta to exclude 0 AND min LOWO delta > 0. The LOWO condition holds (every dropped-writer delta is positive), but the jackknife CI includes 0 in both subsets. NOT SUPPORTED.
- "Parity with word count" is reported when the CI includes 0 and |delta| < .10 in all LOWO fits. Both hold. Verdict: PARITY (consistent with a small M1-free advantage of .02 to .08 that this 20-writer sample cannot resolve).
- M1-free against the .75 threshold: the LOWO minimum is .751 (chip1) and .751 (all200), so the point threshold is met in every leave-one-out fit. The margin is .001, and no CI for the AUROC itself was part of the declared rule; treat the threshold as marginally met, not comfortably met.
- Within-writer stratified AUROCs favour M1-free by .10 (both subsets), the only analysis that leans toward M1-free. It is secondary and has no declared threshold.

## Does it change the frontier's verdict?
No. The frontier verdict (the whole-message metric is a null result; the prompt effect is judge-defined) stands, because SUPPORTED was not reached. The honest wording moves from "M1-free does not beat length" to "M1-free is at parity with length; the best estimate favours M1-free by .04 to .06 AUROC with a CI that includes 0, and no single writer drives it". This is a small softening of the "length beats it" reading in REPORT.md section 8, not a flip. The first limitation in REPORT.md section 7 ("No leave-one-writer-out analysis") is now closed.
