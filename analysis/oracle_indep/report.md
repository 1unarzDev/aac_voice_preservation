# Independent mutation set: Part 29 confirmation and oracle scores

Rules: `PLAN.md` (with Amendment 2) and `annotation/COORDINATOR_STEPS.md` section 7, frozen before any return. Scorer `src/score_oracle_indep.py` (self-check passed). Wilson 95% intervals. Full numbers: `summary.json`, `scores.csv`, `confirmation.csv`.

## Part 29 confirmation
20 annotators returned 15 items each (0 dropped, no duplicated answer sets, no QC rejects). Two annotators per item; raw agreement 95.3% (kappa 0.908 three-way; 96.0% / kappa 0.919 on same/different only).
- Mutants (100): 75 confirmed changed, 20 construction failures (both said same), 5 unresolved.
- Controls (50): 46 confirmed same, 1 construction failure (both said different), 3 unresolved.
- By operator: neg_fail_to 13/13, neg_hardly 12/12, neg_nobody 10/10, neg_refuse_to 13/13, role_embed 12/12, time_implied 14/14 confirmed. role_passive 0/14 (all 14 judged same: the passive/inversion rewrites kept the meaning), q_embed 1/12 (6 same, 5 unresolved). Neither operator can be reported as a sensitivity result (n = 0 and n = 1).

## Judge (production J1+J2, mutant text only, concurrency 3)
150 candidates judged; 17 J1/J2 disputes went to the blind arbiter (it chose the J1 label in all 17); 0 unresolved.

| oracle | sensitivity, all confirmed mutants | lex_visible False (non-circular) | lex_visible True | false alarms, confirmed controls |
|---|---|---|---|---|
| judge | 53/75 = 70.7% [59.6, 79.8] | 31/53 = 58.5% [45.1, 70.7] | 22/22 = 100% [85.1, 100] | 4/46 = 8.7% [3.4, 20.3] |
| surface baseline | 30/75 = 40.0% [29.7, 51.3] | 8/53 = 15.1% [7.9, 27.1] | 22/22 | 11/46 = 23.9% [13.9, 37.9] |
| overlap baseline | 28/75 = 37.3% [27.3, 48.7] | 16/53 = 30.2% [19.5, 43.5] | 12/22 = 54.5% [34.7, 73.1] | 15/46 = 32.6% [20.9, 47.0] |

Counting an unresolved judge label as caught changes nothing (0 unresolved).

By operator (judge caught / confirmed; surface; overlap):
neg_fail_to 6/13 (0; 1), neg_refuse_to 5/13 (0; 2), neg_hardly 12/12 (0; 3), neg_nobody 10/10 (10; 0), role_embed 6/12 (6; 7), time_implied 13/14 (13; 14), q_embed 1/1.
Judge misses are concentrated in "fail to" and "refuse to" (15 of the 22 misses, 11 of 26 caught: the judge reads "They will fail to meet" or "I refuse to carry the inhaler" as affirmative in both passes) and in role_embed (the judge returns the embedded speaker as the agent in 6/12). Neg_nobody and time_implied are lex_visible by construction (the baseline lexicon matches them), so the non-circular stratum is made of neg_fail_to, neg_refuse_to, neg_hardly, role_embed and 2 time items; q_embed contributes 1.

Non-circular stratum, judge versus baselines (exact McNemar, same 53 mutants): judge-only 23 / surface-only 0 (p < 1e-6); judge-only 19 / overlap-only 4 (p = 0.003). On all 75: judge-only 23 vs 0 (surface), 29 vs 4 (overlap), both p < 0.001.

False alarms: 4 of 36 paraphrase controls (politeness: "Kindly ..." versus "Would you mind ...", all four are polite/plain boundary cases); 0 of 10 contraction controls.

## Reading
The earlier circular set (analysis/oracle_real, 98.5%) overstated sensitivity: on mutants built without the checker lexicon and confirmed by two people, the judge catches 71% overall and 59% where the baseline lexicon does not already see the change, with wide intervals. It beats both baselines clearly. The set covers six operator types; sensitivity for passive role swaps and question embedding is not estimated here (humans did not confirm a meaning change). Operators are not equally weighted by count (operator-balanced judge mean 71% over the six estimable operators, 64% in the non-circular stratum).

Caveats: the human question was one fixed same/different judgment, so confirmed mutants are those clear enough for two people; mutants come from one small generator model plus templates; the non-circular stratum is dominated by 3 templates; the placeholder input "(none)" was used for the judge (pass A, which yields the critical label, never sees input); the arbiter agreed with J1 17/17, which is reported rather than interpreted.
