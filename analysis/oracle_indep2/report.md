# A2 fast: second-family (Claude) and NLI oracles on the independent mutants

Sensitivity analysis on the human-confirmed set (75 mutants, 53 lexicon-blind, 46 controls); the frozen headline is the GPT judge row. Plan: PLAN.md (declared before scoring).
Disclosure: Claude also arbitrated and assisted elsewhere in this pipeline; it is a second model family relative to the GPT judge, not independent of the authors' tooling.

| oracle | mutation score, all | lexicon-blind | false alarms (46 controls) | McNemar vs GPT judge, all (judge-only/oracle-only, p) |
|---|---|---|---|---|
| gpt_judge | 70.7 (53/75; 60-80) | 58.5 (31/53; 45-71) | 8.7 (4/46; 3-20) | - |
| nli_primary | 73.3 (55/75; 62-82) | 77.4 (41/53; 64-87) | 0.0 (0/46; -0-8) | 13/15, p=0.8506 |
| nli_secondary | 90.7 (68/75; 82-95) | 90.6 (48/53; 80-96) | 0.0 (0/46; -0-8) | 6/21, p=0.0059 |
| claude_change | 90.7 (68/75; 82-95) | 86.8 (46/53; 75-93) | 8.7 (4/46; 3-20) | 0/15, p=0.0001 |
| claude_ref | 90.7 (68/75; 82-95) | 86.8 (46/53; 75-93) | 15.2 (7/46; 8-28) | 0/15, p=0.0001 |
| either_nli_primary | 90.7 (68/75; 82-95) | 86.8 (46/53; 75-93) | 8.7 (4/46; 3-20) | 0/15, p=0.0001 |
| both_nli_primary | 53.3 (40/75; 42-64) | 49.1 (26/53; 36-62) | 0.0 (0/46; -0-8) | 13/0, p=0.0002 |
| either_nli_secondary | 98.7 (74/75; 93-100) | 98.1 (52/53; 90-100) | 8.7 (4/46; 3-20) | 0/21, p=0.0 |
| both_nli_secondary | 62.7 (47/75; 51-73) | 50.9 (27/53; 38-64) | 0.0 (0/46; -0-8) | 6/0, p=0.0312 |
| either_claude_change | 90.7 (68/75; 82-95) | 86.8 (46/53; 75-93) | 10.9 (5/46; 5-23) | 0/15, p=0.0001 |
| both_claude_change | 70.7 (53/75; 60-80) | 58.5 (31/53; 45-71) | 6.5 (3/46; 2-18) | 0/0, p=1.0 |
| either_claude_ref | 90.7 (68/75; 82-95) | 86.8 (46/53; 75-93) | 17.4 (8/46; 9-31) | 0/15, p=0.0001 |
| both_claude_ref | 70.7 (53/75; 60-80) | 58.5 (31/53; 45-71) | 6.5 (3/46; 2-18) | 0/0, p=1.0 |

Rates in % (k/n; Wilson 95% CI). claude_change = label(original) != label(mutant) on the confirmed dimension (primary); claude_ref = label(mutant) != reference value (the GPT judge's rule).
nli_primary = contradiction either direction (declared primary); nli_secondary = not mutually entailed. either_/both_ = ensemble with the GPT judge.
Claude out-of-option fallbacks: 0 units.

By operator (confirmed mutants): {"neg_fail_to": {"n": 13, "claude_change": 13, "gpt": 6, "nli": 13}, "neg_hardly": {"n": 12, "claude_change": 12, "gpt": 12, "nli": 12}, "neg_nobody": {"n": 10, "claude_change": 10, "gpt": 10, "nli": 10}, "neg_refuse_to": {"n": 13, "claude_change": 12, "gpt": 5, "nli": 13}, "q_embed": {"n": 1, "claude_change": 1, "gpt": 1, "nli": 0}, "role_embed": {"n": 12, "claude_change": 7, "gpt": 6, "nli": 3}, "time_implied": {"n": 14, "claude_change": 13, "gpt": 13, "nli": 4}}

## Reading (cautions)
- Claude's change-detection flags a strict superset of the GPT judge's catches (0 judge-only discordants); the gain is concentrated in neg_fail_to / neg_refuse_to (judge 6/13 and 5/13, Claude 13/13 and 12/13), role_embed and the one q_embed item.
- The two label-based oracles see the dimension; the NLI model does not. NLI (contradiction rule) has 0/46 false alarms but misses most role_embed (3/12) and time_implied (4/14); the looser no-mutual-entailment rule catches 90.7% with 0/46 false alarms here, but it was declared as a secondary rule, not the primary.
- Claude label-change compares original and mutant (a paired design); the GPT judge saw the mutant only against a reference value. claude_ref applies the judge's own rule and gives the same mutation score with more false alarms (7/46). The comparison is therefore not identical in information and the McNemar p-values are sensitivity, not a replacement for the frozen headline.
- Both Claude and the assistant that built this pipeline are the same vendor family; Claude arbitrated labels elsewhere. n = 75 mutants (53 lexicon-blind), 46 controls; the confirmed set is operator-imbalanced (q_embed 1, role_passive 0).
