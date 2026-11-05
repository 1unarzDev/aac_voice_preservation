# Critique 1 of the intent-coverage pilot (PLAN.md, round1.md)

Date 2026-11-05. Adversarial review of pre-declaration compliance, leakage, fairness, and proxy validity. Checked against the code (`src/coverage_{gen,judge,gate,analyze,lib}.py`), prompts, `prompt_shas.json`, `models_used.json`, `proxy_validity.json`, `gate_final.csv`, `summary.json`, git history and file mtimes. Nothing was re-run and nothing outside this file was edited.

Verdict. The machine round is a usable debugging run. It is not yet a pre-specified result, and several of its readings go beyond what PLAN section 3 allows after a failed gate. Six fixes are blocking (B1-B6), the rest are required before the Stage 6 package is built.

## 1. Pre-declaration compliance

- **B1. The plan was not git-timestamped or hash-deposited before generation.** PLAN says the file is "git-timestamped, then hash-deposited ... before generation" and sequence step 1 says "no generation before". Commit 247c2fd (the first commit containing PLAN.md) is dated 2026-11-05 05:17. The draw ran 2026-11-04 23:13, the main generation finished 2026-11-05 02:49, and the contrasts and round1 were written 05:18-05:29. The newest tag is `protocol-hash-2026-11-03d`, which predates the plan. All `src/coverage_*.py` and `prompts/coverage_*.txt` are still untracked, so the prompt hashes in `prompt_shas.json` and the analysis script are not independently timestamped. The only evidence that the plan predates the data is a filesystem mtime (23:07), which is not git-timestamped. Fix: say so plainly in DEVIATIONS.md. Deposit a hash of PLAN.md, the prompts, `src/coverage_*.py`, `items_draw.json` and `prompt_shas.json` now, and do not call the machine round "pre-specified and git-timestamped" in any paper. Claim at most "plan file written before generation (file mtime); committed after the machine run". The human stage can still be pre-specified if the hash is deposited before the package is sent.
- **B2. DEVIATIONS.md does not exist**, although PLAN section "Status rule" and round1.md both say deviations are logged there. Deviations that are already known and must be logged with dates and reasons:
  - generator gpt-6.1-terra became gpt-5.6-terra, and judge gpt-6.1-sol became gpt-6-luna, after 503 responses;
  - the independent-family judges (Qwen, Mistral) were not run;
  - local-model proxy judging was not run (rate limit);
  - `coverage_gen.py` (23:45), `coverage_analyze.py` (23:51) and `coverage_lib.py` (Nov 5 00:06) were edited after the prompt and draw freeze and some after the reserve dry run. State what each edit changed. The lib edit overlaps the main run window, so confirm the main run used the final code;
  - the judge output schema differs from PLAN section 3 (`value` + `event_A` + `event_B` instead of `critical_value` + `event_role_match` + `which_variant`);
  - the contrasts.csv last-row bug.
- **B3. Round 1 breaks the plan's stop-and-freeze rules.**
  - PLAN section 9 step 4: "A machine-only intermediate report ... cannot change the human arms, the item list or the criteria." round1.md ("Moves that this round supports") recommends building the package with D3p and C3 and dropping E3 on the strength of full-200 machine numbers. The plan fixes the human arms as G1, D3p, C3, E3 (25 per cell). Remove the recommendation, or log it as a proposed deviation that is decided by the user and is not driven by this machine round.
  - PLAN section 3: if the gate fails, "machine coverage is reported as descriptive only; no machine-only claim about arms is made". round1.md still gives arm-level cluster CIs and sign-flip p-values, and states directional readings ("looks closer to C-C / partial C-B", "targeting adds a modest gain over diversity only with the oracle dimension", "prompted diversity matches or beats contrast sets"). Strip the p-values and the outcome-rule reading, or label every such line "descriptive, gate failed, not evidence about arms". The same applies to break-even r* and cost-per-covered, which are arm claims.
  - S1 arm choice. The plan chooses E3 or C3 "from the machine proxy only at the dry-run stage". round1.md makes the choice on the main 200 ("by the plan's own selection rule, C3"). The dry run on the 20 reserve items exists (`dry_run_reserve/`). Apply the rule there and report which arm it selects. If it differs from C3, log that.
- **B4. Gate (c) fails and the gate is not "run once" cleanly.** `coverage_gate.py final` was run, and gate_train.csv (23:14) and gate_final.csv (23:15) are minutes apart. That is acceptable. But the paper must report the gate as a failure: AUROC gain over words .120, CI -.015 to .258. Report the gate (b) kappa CI (.37-.69) honestly: the point estimate passes .50 while the lower bound does not. Also, the cutoff was chosen as the best of three values {1.0, 1.5, 2.0} on only 99 train items. Say so.
- Allowed conclusions C-A, C-B and C-C were declared. round1 should not say anything resembling C-C yet, because the human endpoint is the declared primary and the proxy is not validated.
- Power note. PLAN section 1.4 plans ICC re-estimation from Part 18 before the package is built; no DEVIATIONS or ICC table exists. Do it.

## 2. Leakage

Credit first. The coverage judge prompt (`prompts/coverage_judge.txt`) names no arm, condition, input, or other drafts, and does not say which variant is intended. It sees A, B, the draft and the pair dimension only. The generators never see A/B labels or the writer sentence. The oracle arm C3o is correctly flagged as ceiling. Remaining problems:

- **B5. Judge-in-the-loop filtering (circularity).** The label-faithfulness filter uses the same judge (gpt-6-luna) and the same value read-out as the coverage metric. For contrast, event and random arms in `chip`, a draft whose judged value differs from `intended_value` is dropped and regenerated once. In `bare`, an edit on the pair's own dimension is regenerated until the judge reads the claimed new value. Diversity arms (D3s, D3p, D5s, D5p) get no filter and no second attempt. This selects drafts for agreement with the scoring judge, so judge noise is optimised in the filtered arms only. Fix, all three:
  1. apply an identical filter and one regeneration to the diversity arms (draw replacements from the same pool until k cue-consistent drafts, or report all arms both filtered and unfiltered);
  2. score coverage with a judge that did not filter (the independent-family judges, or at least a second prompt), and report the filter pass rate by arm;
  3. report the "unfiltered" and "filtered" columns side by side in the main table, since round1's own data show D3p has 53.8% cue-violating non-G1 drafts in chip (D5p 15.3%) while C/E/R arms are 0% by construction.
- **Judge prompt differs by draft origin (method label leak).** For drafts that were edits on a dimension other than the pair's, the judge call includes an "extra_value" block naming a second aspect. 1,825 of 5,099 drafts (36%) carry judgments made under that different prompt, and `pairj()` takes the "" key first, otherwise the first extra-dim key. So the prompt a draft is judged under depends on how it was made. That leaks the method to the judge and makes the pair-dimension read-out depend on an unrelated extra instruction. Fix: judge every draft with the identical pair-dimension prompt (the "" call), and run the extra-value call separately for the filter only.
- **Selector sees the cue.** In chip the selector removes the cued dimension, using the pair's dimension. This is legitimate only because the chip states it; say so and note that C3 and E3 in `chip` therefore never target the pair's dimension. This is by design, but it means the S3 comparison against a diversity arm is a test of "other dimensions", not of targeting.
- C3o uses the pair's true dimension. It is declared as a ceiling but sits in `contrasts.csv` under "S1" with p = .00012. Rename the row or remove it from S1.
- Part 18 families: P06 takes 5 flagged seen items. The sensitivity (no_seen) is reported and unchanged. No concern beyond logging.

## 3. Fairness of the comparison (equal reading budget)

- **B6. Nominal k is not the budget shown.** From `summary.json` `mean_shown`, bare / chip mean drafts shown: D3p 3.00 / 3.00, E3 2.89 / 2.72, C3 2.74 / 2.54, R3 2.74 / 2.55, D3s 2.06 / 1.94; at k = 5: D5p 5.00 / 5.00, E5 4.69 / 4.26, C5 4.57 / 4.03, D5s 2.40 / 2.23. D3p is read about 0.3 drafts longer than C3 and D5p about 0.5 longer than C5 in chip. The plan's claim "equal-k comparisons only for any headline claim" (section 5b item 5.3) is not met. Fix, each:
  - headline contrasts restricted to items where both arms reached full k (the `no_short_sets` sensitivity does this only for the sensitivity table), or
  - top up short contrast sets from the arm's own reserve candidates (the selector's next dimensions) so that fill = k, and report the fill rate, or
  - compare at matched mean drafts read, not nominal k.
  The cost model already prices reading, but coverage-only contrasts (S1, S3) do not.
- **Unequal generation effort.** Contrast arms use up to two edit calls per slot plus judge calls; diversity arms use one call. State calls and tokens per arm in the report, and give D3p/D5p a matched retry budget (see B5).
- **D3p is not a strawman, but E-arm and C-arm drafts are minimal edits of G1 by instruction ("keep wording, event, other aspects unchanged")**, so within-set similarity is high by design. `mean_sim` is computed but not reported in round1. Report it. It explains why diversity-by-prompt can beat edits, and it is what the "targeting vs variety" question needs.
- **Ceiling is not comparable.** "Any draft of any arm covers" (bare .595, chip .840) takes the union of about 25 drafts per item, a far larger reading budget than any arm. Label it a generation ceiling, not an arm comparison, and give a matched-k ceiling (best-of-k over random k-subsets) if it is used in the paper.
- Cost model. `cost()` charges `min(r_words, e * min_lev)` as the fallback for uncovered items using the closest draft by Levenshtein, which is judge-free but is computed over all shown drafts. A set with more drafts has a lower expected minimum distance for free (order statistic), so the edit-cost term favours bigger sets independently of coverage. Report with and without the fallback term.
- Single generator (gpt-5.6-terra) for all arms; the local replication was generated but not judged, so S7 is untested. Do not describe the arm ordering as replicated.

## 4. Can the proxy stand in for writer intent?

- **It failed its own gate**, so by the plan it cannot. Beyond that:
- **Calibration and level.** Part 18 reports 25.1% overall, 39.2% chip and 11.2% bare writer-matched. The proxy gives G1 .580 chip and .145 bare on the new items. If the same generator regime applies, chip is about 19 pp above the writer number. On the gate data itself, at the frozen cutoff the proxy flags 32.8% of outputs against a 25.1% writer match rate (FPR .178, TPR .776 over all 195; holdout FPR .147, TPR .714). It over-covers, and the bias is not constant across conditions. Absolute coverage and "cost per covered message" must not be quoted as writer-intent rates. The comparison to Part 18 must be shown (with the generator difference stated) and not left implicit.
- **Set-level validity is untested.** The gate validates single-draft judgments. Coverage of a set is an OR over k drafts, so a per-draft FPR of about .15 compounds: at k = 5 the chance that at least one of five non-matching drafts is wrongly flagged is large (about .55 if independent). Larger sets are therefore favoured by judge error alone, which is one candidate explanation for the D5p chip result (.800 vs ceiling .840). Required: a validation at set level, e.g. judge-vs-writer agreement on set-level coverage from the Stage 6 pool ratings (H-cov vs proxy for the same arm and item), reported before any arm claim; and an FPR-corrected or conservative variant (require `yes` from two prompts or two judges for any draft beyond slot 1).
- **Distribution shift.** The gate used older single-sentence outputs from Part 18 with writers rating against their own A/B text. Edit drafts that flip one dimension while keeping wording ("minimal edits of G1") are exactly the cases where a judge compares against A and B by surface similarity. Include contrast-edit and prompted-diversity drafts in the human pool for validation, which Stage 6 already does; make draft-level kappa by origin (g1, sample, diverse, edit, event) a required output.
- **The target is the writer's sentence, not the writer's intent.** The writer's stored sentence is a lower bound on what they meant (detail no keyword supplies). The `event=yes` requirement penalises valid readings that the writer would accept with a small edit, and tolerates mismatched ones. The H-cov rule (match + accept yes/small edit) handles this on the human side; the proxy does not use the accept leg. Report proxy vs H-cov, not only vs H-match. In the gate, AUROC against accept-ok is .754, below the .80 gate for the match label.
- **Single judge.** Primary judge is a different model than the one in the plan, with no independent-family check. The cross-family judges are listed in the plan as a reported check, and not running them means the proxy has no robustness evidence.
- Language: "writer-intent agreement by adult annotators". The proxy is a research instrument that sees the writer's sentence offline, and agreement between machine judges is never human validation.

## 5. Smaller issues

- contrasts.csv last row is a duplicate of the S3 E3 numbers. The fix is cheap: regenerate it rather than documenting the bug.
- round1.md: "S1 ... unresolved" is correct; keep. "S2 fails on the proxy" and "S3 passes" language implies tests on a failed gate; replace with descriptive wording.
- Wrong-first is identical across arms by construction (slot 1 = G1); present it as a check, not a result. A real safety measure is the share of sets that show an unfiltered cue-contradicting draft anywhere, which round1 gives for D3p (53.8% of non-G1 drafts).
- The selector result is a clean null on the H3 criterion (+.04 at recall@2 vs the +.05 bar). Report it as declared, not as "mostly names two dimensions" alone; the per-dimension recall pattern (speech_act .98, agent .94, others near 0) is interesting and must be shown with the denominator per dimension.
- Per-dimension tables are direction only (n of about 30-40, 6-7 writers). Keep that wording.
- Scratch: confirm `~/aac-voice-preservation/tmp/` is clean and that cache files under `analysis/coverage/cache` (3 MB) are intended to be committed.

## Required fixes (checklist)

Blocking before any number leaves this folder:
1. B1: deposit hashes now; state in DEVIATIONS.md that the plan was committed after generation and that only mtimes show the plan came first. No "git-timestamped before generation" claim for the machine round.
2. B2: create DEVIATIONS.md with every item listed in section 1.
3. B3: remove the arm-dropping recommendation and the p-values and outcome-rule reading from round1.md; keep the machine tables as descriptive. Re-apply the S1 arm-selection rule on the reserve dry run.
4. B4: report the failed gate in full (including the kappa CI and the three-value cutoff search).
5. B5: filter diversity arms identically (or show filtered/unfiltered for all); score with a judge that did not filter; unify the judge prompt across draft origins.
6. B6: equal-reading-budget analysis (full-k only, top-up, or matched mean drafts read), and report `mean_shown` and `mean_sim` in the main table.

Required before the Stage 6 package is built:
7. Set-level proxy validation plan and an FPR-conservative variant; report proxy calibration vs Part 18 writer rates.
8. Run the independent-family judges on a fixed subsample of drafts (stratified by origin) once rate limits allow, and judge the local-model drafts so S7 can be evaluated; until then, S7 stays "not evaluated".
9. ICC re-estimate and power table; fix contrasts.csv; rename the C3o row.
10. Report both with- and without-fallback cost, and a matched-k ceiling.
