# Oracle mutation analysis on real outputs, with baseline oracles

Seed 20261102. 200 mutants, 100 controls from real hw1 outputs the production oracle scored as preserving the critical commitment (cue-bearing channels, one per family). Plan: `PLAN.md`. Intervals are Wilson 95%.
W-A had no mutation code (its mutants were hand-written), so the same operator families were re-implemented in `src/oracle_real_ops.py`.

Definitions. Mutation score = share of meaning-changing mutants an oracle rejects (says the commitment is not preserved). False alarm = share of meaning-preserving controls an oracle rejects. Judge = production J1+J2 judge with arbiter; 0 rows were unresolved (J1 != J2, no arbiter).

## Headline (booster mutants excluded, see below)

| oracle | mutation score | false alarm (controls) |
|---|---|---|
| judge | 193/196 (98.5%) [96, 99] | 0/100 (0.0%) [0, 4] |
| surface | 190/196 (96.9%) [93, 99] | 4/100 (4.0%) [2, 10] |
| overlap | 138/196 (70.4%) [64, 76] | 16/100 (16.0%) [10, 24] |

Judge mutation score if unresolved rows are counted as caught: 193/196 (98.5%) [96, 99]. Judge returns exactly the expected new label on 186/196 (94.9%) [91, 97] of mutants.
Booster mutants (plain -> 'Definitely, ...') are tolerated by the production contract (plain is honoured by emphatic) and are excluded: judge 0/4 (0.0%) [0, 49], surface 0/4 (0.0%) [0, 49], overlap 0/4 (0.0%) [0, 49].

## By dimension (mutation score; false alarm on that dimension's controls)

| dimension | n mut | judge | surface | overlap | n ctl | judge FA | surface FA | overlap FA |
|---|---|---|---|---|---|---|---|---|
| agent | 34 | 34/34 (100.0%) [90, 100] | 34/34 (100.0%) [90, 100] | 30/34 (88.2%) [73, 95] | 17 | 0/17 (0.0%) [0, 18] | 4/17 (23.5%) [10, 47] | 6/17 (35.3%) [17, 59] |
| certainty | 30 | 30/30 (100.0%) [89, 100] | 27/30 (90.0%) [74, 97] | 21/30 (70.0%) [52, 83] | 17 | 0/17 (0.0%) [0, 18] | 0/17 (0.0%) [0, 18] | 4/17 (23.5%) [10, 47] |
| polarity | 33 | 33/33 (100.0%) [90, 100] | 33/33 (100.0%) [90, 100] | 25/33 (75.8%) [59, 87] | 16 | 0/16 (0.0%) [0, 19] | 0/16 (0.0%) [0, 19] | 0/16 (0.0%) [0, 19] |
| politeness | 33 | 33/33 (100.0%) [90, 100] | 33/33 (100.0%) [90, 100] | 12/33 (36.4%) [22, 53] | 16 | 0/16 (0.0%) [0, 19] | 0/16 (0.0%) [0, 19] | 1/16 (6.2%) [1, 28] |
| speech_act | 33 | 32/33 (97.0%) [85, 99] | 32/33 (97.0%) [85, 99] | 22/33 (66.7%) [50, 80] | 17 | 0/17 (0.0%) [0, 18] | 0/17 (0.0%) [0, 18] | 1/17 (5.9%) [1, 27] |
| time_quantity | 33 | 31/33 (93.9%) [80, 98] | 31/33 (93.9%) [80, 98] | 28/33 (84.9%) [69, 93] | 17 | 0/17 (0.0%) [0, 18] | 0/17 (0.0%) [0, 18] | 4/17 (23.5%) [10, 47] |

## By operator (mutation score)

| operator | n | judge | surface | overlap |
|---|---|---|---|---|
| agent_swap | 34 | 34/34 (100.0%) [90, 100] | 34/34 (100.0%) [90, 100] | 30/34 (88.2%) [73, 95] |
| booster_insert | 4 | 0/4 (0.0%) [0, 49] | 0/4 (0.0%) [0, 49] | 0/4 (0.0%) [0, 49] |
| hedge_insert | 9 | 9/9 (100.0%) [70, 100] | 6/9 (66.7%) [35, 88] | 2/9 (22.2%) [6, 55] |
| hedge_remove | 21 | 21/21 (100.0%) [85, 100] | 21/21 (100.0%) [85, 100] | 19/21 (90.5%) [71, 97] |
| negation_insert | 21 | 21/21 (100.0%) [85, 100] | 21/21 (100.0%) [85, 100] | 21/21 (100.0%) [85, 100] |
| negation_remove | 12 | 12/12 (100.0%) [76, 100] | 12/12 (100.0%) [76, 100] | 4/12 (33.3%) [14, 61] |
| politeness_add | 24 | 24/24 (100.0%) [86, 100] | 24/24 (100.0%) [86, 100] | 3/24 (12.5%) [4, 31] |
| politeness_remove | 9 | 9/9 (100.0%) [70, 100] | 9/9 (100.0%) [70, 100] | 9/9 (100.0%) [70, 100] |
| speech_act_to_question | 23 | 22/23 (95.7%) [79, 99] | 22/23 (95.7%) [79, 99] | 15/23 (65.2%) [45, 81] |
| speech_act_to_statement | 10 | 10/10 (100.0%) [72, 100] | 10/10 (100.0%) [72, 100] | 7/10 (70.0%) [40, 89] |
| time_shift | 33 | 31/33 (93.9%) [80, 98] | 31/33 (93.9%) [80, 98] | 28/33 (84.9%) [69, 93] |

## Control edit types (false alarm)

| edit | n | judge | surface | overlap |
|---|---|---|---|---|
| case_initial | 37 | 0/37 (0.0%) [0, 9] | 3/37 (8.1%) [3, 21] | 5/37 (13.5%) [6, 28] |
| contraction | 21 | 0/21 (0.0%) [0, 15] | 0/21 (0.0%) [0, 15] | 0/21 (0.0%) [0, 15] |
| punctuation_commas | 1 | 0/1 (0.0%) [0, 79] | 0/1 (0.0%) [0, 79] | 0/1 (0.0%) [0, 79] |
| punctuation_period | 39 | 0/39 (0.0%) [0, 9] | 1/39 (2.6%) [0, 13] | 11/39 (28.2%) [17, 44] |
| synonym | 2 | 0/2 (0.0%) [0, 66] | 0/2 (0.0%) [0, 66] | 0/2 (0.0%) [0, 66] |

## Baselines on the unmutated originals

On the 300 unmutated source outputs (which the judge scored as preserving by construction): surface false alarm 6/300 (2.0%) [1, 4], overlap 45/300 (15.0%) [11, 19]. A baseline's false alarm on controls therefore partly reflects its failure on the original sentence.

| dimension | n | surface FA | overlap FA |
|---|---|---|---|
| agent | 51 | 4/51 (7.8%) [3, 18] | 10/51 (19.6%) [11, 32] |
| certainty | 51 | 0/51 (0.0%) [0, 7] | 15/51 (29.4%) [19, 43] |
| polarity | 49 | 0/49 (0.0%) [0, 7] | 1/49 (2.0%) [0, 11] |
| politeness | 49 | 0/49 (0.0%) [0, 7] | 3/49 (6.1%) [2, 17] |
| speech_act | 50 | 2/50 (4.0%) [1, 13] | 2/50 (4.0%) [1, 13] |
| time_quantity | 50 | 0/50 (0.0%) [0, 7] | 14/50 (28.0%) [17, 42] |

Agreement with the judge on all judged real rows: surface 293/300 (97.7%) [95, 99], overlap 225/300 (75.0%) [70, 80].

## Comparison with W-A authored sentences

| set / group | n mut | n ctl | judge mut | surface mut | overlap mut | judge FA | surface FA | overlap FA |
|---|---|---|---|---|---|---|---|---|
| W-A injection / all | 120 | 120 | 120/120 (100.0%) [97, 100] | 115/120 (95.8%) [91, 98] | 87/120 (72.5%) [64, 80] | 0/120 (0.0%) [0, 3] | 4/120 (3.3%) [1, 8] | 0/120 (0.0%) [0, 3] |
| W-A injection / agent | 20 | 20 | 20/20 (100.0%) [84, 100] | 16/20 (80.0%) [58, 92] | 19/20 (95.0%) [76, 99] | 0/20 (0.0%) [0, 16] | 2/20 (10.0%) [3, 30] | 0/20 (0.0%) [0, 16] |
| W-A injection / certainty | 20 | 20 | 20/20 (100.0%) [84, 100] | 20/20 (100.0%) [84, 100] | 8/20 (40.0%) [22, 61] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] |
| W-A injection / polarity | 20 | 20 | 20/20 (100.0%) [84, 100] | 20/20 (100.0%) [84, 100] | 17/20 (85.0%) [64, 95] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] |
| W-A injection / politeness | 20 | 20 | 20/20 (100.0%) [84, 100] | 20/20 (100.0%) [84, 100] | 10/20 (50.0%) [30, 70] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] |
| W-A injection / speech_act | 20 | 20 | 20/20 (100.0%) [84, 100] | 19/20 (95.0%) [76, 99] | 13/20 (65.0%) [43, 82] | 0/20 (0.0%) [0, 16] | 2/20 (10.0%) [3, 30] | 0/20 (0.0%) [0, 16] |
| W-A injection / time_quantity | 20 | 20 | 20/20 (100.0%) [84, 100] | 20/20 (100.0%) [84, 100] | 20/20 (100.0%) [84, 100] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] | 0/20 (0.0%) [0, 16] |
| W-A challenge / all | 24 | 24 | 22/24 (91.7%) [74, 98] | 20/24 (83.3%) [64, 93] | 24/24 (100.0%) [86, 100] | 0/24 (0.0%) [0, 14] | 5/24 (20.8%) [9, 40] | 0/24 (0.0%) [0, 14] |
| W-A challenge / acceptance | 6 | 6 | 4/6 (66.7%) [30, 90] | 3/6 (50.0%) [19, 81] | 6/6 (100.0%) [61, 100] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] |
| W-A challenge / embedded_actor | 6 | 6 | 6/6 (100.0%) [61, 100] | 5/6 (83.3%) [44, 97] | 6/6 (100.0%) [61, 100] | 0/6 (0.0%) [0, 39] | 5/6 (83.3%) [44, 97] | 0/6 (0.0%) [0, 39] |
| W-A challenge / mitigation | 6 | 6 | 6/6 (100.0%) [61, 100] | 6/6 (100.0%) [61, 100] | 6/6 (100.0%) [61, 100] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] |
| W-A challenge / question_request | 6 | 6 | 6/6 (100.0%) [61, 100] | 6/6 (100.0%) [61, 100] | 6/6 (100.0%) [61, 100] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] | 0/6 (0.0%) [0, 39] |

Real-output rows above use the same judge, the same contract and the same production critical_match. The W-A challenge set is scored as in `analysis/oracle/report.md` (production rule). Overlap on W-A challenge uses the paired control/mutant text as the minimal pair.

## Judge misses and false alarms

- missed mutant R034 (certainty/booster_insert): `I want a taxi to the hotel.` -> `Definitely, I want a taxi to the hotel.`; expected strongly certain/emphatic, judge strongly certain/emphatic
- missed mutant R037 (certainty/booster_insert): `The ramp is clear by the entrance.` -> `Definitely, the ramp is clear by the entrance.`; expected strongly certain/emphatic, judge strongly certain/emphatic
- missed mutant R051 (certainty/booster_insert): `The headphones will block the traffic noise.` -> `Definitely, the headphones will block the traffic noise.`; expected strongly certain/emphatic, judge strongly certain/emphatic
- missed mutant R067 (certainty/booster_insert): `The family meets at the park tonight.` -> `Definitely, the family meets at the park tonight.`; expected strongly certain/emphatic, judge strongly certain/emphatic
- missed mutant R134 (speech_act/speech_act_to_question): `Does the dog sleep beside the sofa at night.` -> `Is it true that does the dog sleep beside the sofa at night?`; expected question, judge question
- missed mutant R173 (time_quantity/time_shift): `They told the dog was on the sofa.` -> `They told the dog is on the sofa.`; expected now, judge past
- missed mutant R187 (time_quantity/time_shift): `They told me the music was loud in the past.` -> `They told me the music is loud in the past.`; expected now, judge past

## Caveats

- Circularity of the surface baseline: its lexicons (not/n't, maybe, please/thanks/sorry, tense and time words, '?') are the very cues the operators insert or delete, so its high mutation score shows that these operators are lexically shallow, not that a lexicon oracle is adequate. The judge's edge over it is small here (mutation score) and shows up on controls (surface false alarms on agent, case-initial and the W-A embedded-actor group) and on cases where meaning is not lexically marked. An independent surface baseline would need a second author.
- One equivalent mutant: R134's source output is a question written without '?', so the operator's statement-to-question edit did not change the value; excluding it the judge's score is 193/195. Headline numbers keep it. Two time-shift misses (R173, R187) keep an explicit 'in the past' / past-tense word beside the shifted verb, so the mutant is mixed-signal and the judge followed the explicit phrase.
- Mutants are rule-generated and some are unnatural (e.g. 'I did call you yesterday'); the judge sees only the output, so naturalness does not leak the key, but it limits realism.
- Draw rule: first N sentences in a seeded shuffle that the operator can mutate; applicability by dimension is in `draw.json`.
- The overlap baseline uses key information (minimal-pair source difference) and is generous; the surface baseline was written before seeing scores and not tuned.
- NLI baseline (iii) skipped: no NLI model or transformers install is available locally and no download was made.
- Controls are mostly punctuation, case and contraction edits because model outputs are short plain sentences; the synonym lexicon rarely applies.
- Judge false-alarm rate here is on surface-edited controls only; it is not a false-alarm rate on unedited outputs (those are scored by the human gate).
