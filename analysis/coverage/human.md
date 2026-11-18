# Stage 6 intent coverage: human results (Parts 26 and 27)

Analyst: scoring analyst (coverage). Frozen rules: `annotation/COORDINATOR_STEPS.md` section 6 (hash-deposited, protocol-hash-2026-11-05e). Key `annotation/coverage_key.csv`, sha256 d72aba58...253d, matches `coverage_key.sha256`. Scorer `src/score_coverage.py` (self-check PASSED before and after the two fixes in "Deviations"). Estimand: coverage of the writer's own intended message, judged by the writer (adult annotators, not AAC users). 20 writers, 10 items each (200 items; 100 bare, 100 chip). B = 10,000, seed 20261117, CIs resample writers then items. Every CI below is a writer-cluster bootstrap; p is a writer sign-flip test; Holm over the five primary contrasts.

## QC
Part 26: 240 rows, 40 practice dropped, 200/200 scored, 0 duplicates, 0 incomplete, 0 invalid (after the loader fix). Part 27: 1278 rows, 40 practice dropped, 1238/1238 drafts rated, 0 invalid. Nothing imputed; every arm-item endpoint is defined (n = 100 per arm-condition). 0 inconsistent set answers. 2 sets were shown with fewer than 3 drafts (kept, counted).

## Primary result: H-cov per arm (item has a draft the writer says is what they meant AND would send as is or with a small edit)
| condition | arm (drafts shown) | H-cov [95% CI] | H-strict (as is) | proxy (machine) |
|---|---|---|---|---|
| bare | G1 (1) | 13% [5, 23] | 4% | 17% |
| bare | D3p (3) | 20% [11, 31] | 5% | 26% |
| bare | C3 (3) | 22% [11, 34] | 5% | 35% |
| bare | E3 (3) | 22% [11, 34] | 5% | 29% |
| chip | G1 (1) | 43% [31, 55] | 12% | 57% |
| chip | D3p (2.89) | 65% [52, 77] | 16% | 73% |
| chip | C3 (2.87) | 53% [40, 66] | 15% | 69% |
| chip | E3 (2.95) | 56% [44, 68] | 15% | 71% |
| chip | D3pU (3, unfiltered) | 64% [52, 76] | 15% | 69% |

H-match equals H-cov in every cell: every draft a writer rated "meant" was also accepted (159 small edit, 35 as is, 0 No), so the acceptance step removed nothing. Only 18% of "meant" drafts were accepted as written; the rest needed a small edit. Set-level ceiling (any draft of any arm covers): 28% bare, 71% chip. Part 18 comparison (generator differs, stated): Part 18 overall 25.1%, chip 39.2%, bare 11.2%; here G1 chip 43%, G1 bare 13%.

## Frozen contrasts (n = 100 items per paired contrast; writer-cluster)
| contrast | diff pp [95% CI] | p (Holm) | frozen status |
|---|---|---|---|
| S1 C3 - D3p, bare | +2 [-8, +11] | .78 (1.0) | unresolved |
| S1 E3 - D3p, bare | +2 [-7, +11] | .78 (1.0) | unresolved |
| S2 C3 bare vs G1 chip (unpaired) | -21 [-36, -5] | .004 (.016) | unresolved by the literal rule (upper bound is exactly -5.0); cost also higher |
| S2 E3 bare vs G1 chip (unpaired) | -21 [-36, -5] | .004 (.016) | same |
| S3 E3 - G1, chip | +13 [+5, +22] | .0008 (.004) | PASS |

Exploratory (not Holm-controlled): C3 - G1 chip +10 [+3, +19]; D3p - G1 chip +22 [+12, +33]; cue tap (G1 chip - G1 bare, unpaired) +30 [+15, +44]; filter effect D3pU - D3p -1 [-6, +3]. Per writer in chip: E3 > G1 for 11 writers, tie 9, below 0; D3p > G1 for 15, tie 5, below 0. Bare E3 vs D3p: 6 up, 11 tie, 3 down.

## Where draft sets do NOT help
1. **Bare, sets add little and not reliably.** Three drafts lift coverage from 13% (one draft) to 20-22%, but contrast-selected sets (C3, E3) are indistinguishable from plain prompted diversity (+2 pp, CIs reach +11 and -8). S1 is unresolved, not passed. Bare coverage stays at 22% at best, the 3-draft ceiling over all arms is 28%.
2. **A set does not replace a cue tap.** Bare 3-draft sets reach 22% against 43% for one draft after a cue tap (-21 pp, CI -36 to -5). The cue is the main lever: +30 pp [+15, +44]. Cost per covered message at r = 0.5: bare C3 34.8, E3 34.2 versus chip G1 13.6 (no-fallback 15.1/15.2 vs 5.8). S2 fails on cost whatever the CI status.
3. **Contrast targeting did not beat diversity where it counts.** In chip, prompted diversity D3p (65%) is above E3 (56%) and C3 (53%) (D3p - E3 is not a frozen contrast; direction only). The contrast-selector (C3, E3) is therefore not the best set builder in this data; the earlier machine round's wish to drop E3 was not applied, and the result stands as is.
4. **Per-dimension (direction only, 3-10 items per cell).** Bare coverage is near zero for agent (0-6%) and time_quantity (0-10%); speech_act is the one dimension where chip sets stay low (G1 19%, sets 29-38%). Sets help most on agent, time_quantity and polarity in chip, and not at all on certainty (73% in every arm).
5. **Strict acceptance wipes most of the gain.** On H-strict (as is) the chip differences are +3 [0, 9] (E3), +3 [0, 9] (C3), +4 [0, 11] (D3p) over G1: sets raise the chance of a nearly-right draft, rarely of a ready-to-send one.
6. **Direct set-view answers are lower than the pool-derived ones.** For the arm each set showed, picked-and-sendable direct H-cov vs pool-derived: chip D3p .32 vs .60, C3 .52 vs .64, E3 .48 vs .64, G1 .20 vs .32; bare within 0-8 pp. (n = 25 sets per cell; agreement .72-.96.) The 5 pp rule is about direct above pool; this is the other direction: in the set view writers pick a draft far more often than they then say "send". The direct data (200 sets, 25 per cell) are underpowered; unpaired direct contrasts have intervals of +-25 to 30 pp (E3 - G1 chip +28 [-5, +58]; C3 - G1 chip +32 [+7, +57]) and do not change any status. Pool ratings and direct choices agree on match (picked) within 0-8 pp.
7. **The machine proxy overstates coverage and is only moderately aligned.** Draft level (n = 1029): proxy "intended" rate 31% vs writers 17%, kappa .40, AUROC .76; by origin kappa G1 .55, E3 .44, D3p .33, C3 .30. Set-level agreement 78% (16% proxy yes / writers no; 6% the reverse). Arm-level Spearman over the 8 arm-condition cells .99 (ordering identical except proxy ranks C3/E3 above D3p in bare). The proxy gate had already failed; no machine number decides anything. Spearman .99 is rank agreement of the cell means only.

## Burden (S4) and cost
- Median drafts read to the first covering draft, among covered items: 1.0 for C3 and E3, bare and chip (criterion <= 2.0: met). Caveat: read position is the position within the (arm-ordered) set, G1 draft first by construction.
- Mean Part 26 burden (1-5, unpaired, items differ): C3 - G1 +0.20 [-0.33, +0.80], E3 - G1 +0.20 [-0.40, +0.80] (criterion: <= 0.5 and CI upper < 1.0: met on both). Cell means 1.2-1.8. Read time was not exported by the tool (no `time_ms` column in the returns), so reading time in seconds is unavailable.
- Cost per covered message (tap-equivalents; assumptions, not device measurements; fallback = min(words, edit distance) when no draft is usable), r = 0.5, with fallback [CI] / without fallback:
  chip G1 13.6 [10.9, 17.7] / 5.8 [5.0, 6.9]; chip D3p 8.8 [6.9, 11.6] / 6.0 [5.2, 7.3]; chip E3 11.3 [9.3, 14.2] / 7.1 [6.3, 8.4]; chip C3 12.6 [10.0, 16.4] / 7.5 [6.3, 9.1]; bare G1 50.6 / 11.5; bare D3p 37.5 / 16.8; bare C3 34.8 / 15.1; bare E3 34.2 / 15.2.
  The fallback term favours bigger sets (it is large because most bare items are uncovered). Without it, chip G1 is the cheapest per covered message (5.8) and every 3-draft set costs more (6.0-7.5; the D3p-minus-G1 difference is 0.2 and within noise); with it, chip sets are cheaper (D3p 8.8, E3 11.3 vs 13.6) because a covered item saves the fallback. Break-even (chip, with fallback): C3 loses to G1 chip at r > 1.2, E3 at r > 2.2, D3p never in 0-4. Bare sets never beat chip G1 at any r. The sign of the chip comparison depends on the fallback assumption.

## Outcome rules (PLAN section 7)
S3 passes; S1 unresolved for both sets; S2 unresolved by the literal rule and worse on cost; S4 met. None of C-A (needs S1 and S3, or S1 and S2), C-B (S1 pass in bare) or C-C (S1 fails and best set minus G1 chip < +5 pp in both conditions; here the best set minus G1 chip is +13 to +22 pp, so C-C is not met either) is satisfied; the outcome is reported as unresolved by the frozen rules. The proxy gate failed, so only these human results decide.

## Sensitivities (exploratory; `sensitivity.csv`)
Excluding sets with fewer than 3 drafts: S3 E3 +12.5 [+5.1, +21.6], unchanged. Strict as-is: S1 0 [-4, +4], S3 E3 +3 [0, +9]. Not run: seen_in_part18 exclusion, hw2 exclusion, `partly` proxy variant, mixed-effects model (not needed for decisions; the proxy variants are machine-only).

## Free text
1032 notes on No ratings (992 "something else", 40 "my other version"). Coded by keyword rule (the analyst, not by hand): meaning changed (actor, time, polarity, speech act, replacement) 693, detail dropped 89, added 9, fluency 2, uncoded 239. Notes repeat within an item (200 items, median 4 distinct notes per item; 707 distinct strings), so they describe items more than independent draft errors. Counts are descriptive.

## Safety
Share of shown drafts rated "my other version" (the reverse reading): bare 9-12% in every arm; chip 0.3% (filtered arms) and 1.3% (D3pU, 3 of 300). Draft 1 (G1) wrong-first is 12% bare, 1% chip by construction. The unfiltered/filtered difference in coverage is -1 pp [-6, +3].

## Deviations (not edits of the frozen rules)
1. `read_returns` did not fill missing columns when concatenating per-person files with different pick columns (pick1/pick2/pick3 present only for the set size that person saw): NaN was counted as an invalid option, so a first run kept 20 of 200 set-view items. Fixed with `.fillna("")` before scoring; no rule changed. Pool results were unaffected (identical before and after).
2. The tool did not export `time_ms`; `set_view` now reads it with a default (0). Read-time outputs are absent. Burden uses the 1-5 `hard` answer only.
3. Extras (cost CIs, break-even, sensitivity, direct contrasts, draft safety) are in `extra_analyses.py`; they are exploratory and are not frozen.
4. S2 status follows the literal rule (fail only if upper bound < -5). The upper bound is exactly -5.0 pp (rounded to the resolution 1/100 items); calling it "fail" would be a reading beyond the rule.
5. Free-text coding is a keyword rule, not a manual pass.
6. Costs use the tap-equivalent assumptions of PLAN section 5; none is measured. Set-view burden is not per-draft read time.

Files: `by_arm.csv, contrasts.csv, direct_vs_pool.csv, concordance.json, qc.json, free_text_to_code.csv, sensitivity.csv, cost_ci.csv, breakeven.csv, direct_contrasts.csv, draft_safety.csv, extra_analyses.py, summary.json`.
