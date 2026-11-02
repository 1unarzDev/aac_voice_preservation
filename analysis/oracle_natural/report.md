# Oracle on faults nobody seeded

Judge verdict vs human-consensus verdict on the four human-labelled sets of natural model outputs (counts from `score_gold.py` verdict agreement, scope primary). Wilson 95% CIs.

| set | verdict | n | ref+ | TP | FP | FN | precision [CI] | recall [CI] | F1 |
|---|---|---|---|---|---|---|---|---|---|
| H7 gate (main1) | violation | 99 | 24 | 22 | 1 | 2 | 95.7 [79.0, 99.2] | 91.7 [74.2, 97.7] | 93.6 |
| H7 gate (main1) | preservation_failure | 97 | 30 | 28 | 1 | 2 | 96.6 [82.8, 99.4] | 93.3 [78.7, 98.2] | 94.9 |
| H7 gate (main1) | assumption | 56 | 43 | 42 | 1 | 1 | 97.7 [87.9, 99.6] | 97.7 [87.9, 99.6] | 97.7 |
| Part 10 (gold_new) | violation | 134 | 23 | 22 | 2 | 1 | 91.7 [74.2, 97.7] | 95.7 [79.0, 99.2] | 93.6 |
| Part 10 (gold_new) | preservation_failure | 134 | 31 | 29 | 6 | 2 | 82.9 [67.3, 91.9] | 93.5 [79.3, 98.2] | 87.9 |
| Part 10 (gold_new) | assumption | 42 | 42 | 42 | 0 | 0 | 100.0 [91.6, 100.0] | 100.0 [91.6, 100.0] | 100.0 |
| Part 12 (elicitation) | assumption | 151 | 143 | 143 | 0 | 0 | 100.0 [97.4, 100.0] | 100.0 [97.4, 100.0] | 100.0 |
| Part 13 (human-written) | violation | 83 | 16 | 14 | 3 | 2 | 82.4 [59.0, 93.8] | 87.5 [64.0, 96.5] | 84.8 |
| Part 13 (human-written) | preservation_failure | 82 | 22 | 20 | 3 | 2 | 87.0 [67.9, 95.5] | 90.9 [72.2, 97.5] | 88.9 |
| Part 13 (human-written) | assumption | 75 | 55 | 55 | 4 | 0 | 93.2 [83.8, 97.3] | 100.0 [93.5, 100.0] | 96.5 |
| pooled main1+new+hw | violation |  | 63 | 58 | 6 | 5 | 90.6 [81.0, 95.6] | 92.1 [82.7, 96.6] | 91.3 |
| pooled main1+new+hw | preservation_failure |  | 83 | 77 | 10 | 6 | 88.5 [80.1, 93.6] | 92.8 [85.1, 96.6] | 90.6 |

Notes: few positives in single sets (violation positives are few per set), so intervals are wide; pooled rows sum main1, Part 10 and Part 13 (distinct items). Part 12 supports only the assumption verdict (positive = assumption made; 8 negatives). Reference is human consensus, with ties/unsure excluded.
