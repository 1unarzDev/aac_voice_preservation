# Whole-message fidelity: why a preserved critical commitment is not enough

Scope: Part 18 (200 writer-rated outputs, 20 writers), SLP panel (50 outputs, 2 raters), exploratory, post hoc, no new model calls. Classifier and hand coding are described in `src/analyze_whole_message.py`. The 'writer's sentence' is the writer's own A or B sentence for the intended variant; it often contains details (places, times, objects) that the keywords do not carry. Writer-intent agreement is not validation by AAC users.

## 1. Part 18: why writers reject the output

Rejection definitions: R1 writer does not say it is the intended version 146/195 = 74.9% [68, 80]; R2 acceptance = no 120/200 = 60.0% [53, 67]; R3 not accepted as-is 199/200 = 99.5% [97, 100].

### 1a. Classifier validation (40 hand-coded items)

Diff classifier vs hand coding (primary reason): agreement 80% (32/40), Cohen kappa 0.71. Note-regex-only: 92%. Hand-coded distribution: {'dropped': 17, 'substitution': 11, 'critical': 10, 'added': 1, 'fluency': 1}. **Caveat: the hand coder is an LLM, the classifier rules were written after seeing these 40, so this is optimistic, not held out.**

Confusion (rows hand, cols classifier):

```
prim          critical  dropped  fluency  substitution
hand                                                  
added                0        0        0             1
critical            10        0        0             0
dropped              0       12        2             3
fluency              0        0        1             0
substitution         0        2        0             9
```

### 1b. Reason distribution (primary reason, all 199 non-accepted items)

| group | n | critical | fluency | substitution | added | dropped | reword |
|---|---|---|---|---|---|---|---|
| all not accepted | 199 | 70 (35%) | 6 (3%) | 63 (32%) | 0 (0%) | 59 (30%) | 1 (1%) |
| all, note-regex classifier instead | 199 | 70 (35%) | 1 (1%) | 50 (25%) | 0 (0%) | 47 (24%) | 31 (16%) |
| channel bare | 99 | 66 (67%) | 1 (1%) | 17 (17%) | 0 (0%) | 15 (15%) | 0 (0%) |
| channel chip1 | 100 | 4 (4%) | 5 (5%) | 46 (46%) | 0 (0%) | 44 (44%) | 1 (1%) |
| model gemma3-4b | 50 | 22 (44%) | 1 (2%) | 13 (26%) | 0 (0%) | 13 (26%) | 1 (2%) |
| model gpt-6.1-terra | 51 | 19 (37%) | 1 (2%) | 7 (14%) | 0 (0%) | 24 (47%) | 0 (0%) |
| model llama3.1-8b | 46 | 13 (28%) | 2 (4%) | 20 (43%) | 0 (0%) | 11 (24%) | 0 (0%) |
| model qwen2.5-7b | 52 | 16 (31%) | 2 (4%) | 23 (44%) | 0 (0%) | 11 (21%) | 0 (0%) |

Multi-label flags (share of non-accepted items; flags overlap):

| group | n | critical | fluency | substitution | added | dropped | dropped_unrecoverable | dropped_keyword |
|---|---|---|---|---|---|---|---|---|
| all | 199 | 35% | 4% | 59% | 28% | 98% | 98% | 11% |
| bare | 99 | 67% | 2% | 71% | 39% | 99% | 99% | 7% |
| chip1 | 100 | 4% | 6% | 48% | 16% | 98% | 98% | 15% |

`dropped_unrecoverable` = a content word of the writer's sentence that is neither in the input keywords nor a chip realisation (the model could not have known it). `dropped_keyword` = the model left out a keyword it was given.

### 1c. Key question: judge says the critical value is right

| subset | n | writer: not the intended version (R1) | acceptance = no (R2) | not accepted as-is (R3) |
|---|---|---|---|---|
| judge critical RIGHT | 130 | 77/126 = 61.1% [52, 69] | 69/130 = 53.1% [45, 61] | 129/130 = 99.2% [96, 100] |
| judge critical WRONG | 70 | 69/69 = 100.0% [95, 100] | 51/70 = 72.9% [61, 82] | 70/70 = 100.0% [95, 100] |
| RIGHT, chip1 | 96 | 55/93 = 59.1% [49, 69] | 48/96 = 50.0% [40, 60] | 96/96 = 100.0% [96, 100] |
| RIGHT, bare | 34 | 22/33 = 66.7% [50, 80] | 21/34 = 61.8% [45, 76] | 33/34 = 97.1% [85, 99] |

Why, among the 129 judge-RIGHT items not accepted as-is (primary reason):

| judge RIGHT, not accepted | 129 | 0 (0%) | 6 (5%) | 63 (49%) | 0 (0%) | 59 (46%) | 1 (1%) |
| judge RIGHT, R1 (not intended version) | 77 | 0 (0%) | 1 (1%) | 56 (73%) | 0 (0%) | 19 (25%) | 1 (1%) |
| judge RIGHT, R2 (acceptance=no) | 69 | 0 (0%) | 2 (3%) | 53 (77%) | 0 (0%) | 13 (19%) | 1 (1%) |
| judge RIGHT, writer-matched but small edit | 48 | 0 (0%) | 3 (6%) | 6 (12%) | 0 (0%) | 39 (81%) | 0 (0%) |

A writer-matched item (writer says it is the intended version) was usually still edited: the typical edit is adding the writer's own detail.

Among judge-RIGHT not-accepted items: unrecoverable content dropped 98%, role/event substitution 49%, model added new content words 22%, judge `added_content` = yes 22% (of judged), fragment 5%.

## 2. SLP panel (50 outputs, 2 raters)

Rater-item pairs: 100. SLP 'says what the selected words mean' != yes (partly/no): 64/100 = 64.0% [54, 73]; acceptable != yes: 64/100 = 64.0% [54, 73].

| subset | rater-items | says partly/no | acceptable != yes | acceptable = no |
|---|---|---|---|---|
| judge PASS (meaning_fail=0) | 80 | 44/80 = 55.0% [44, 65] | 44/80 = 55.0% [44, 65] | 20/80 = 25.0% [17, 35] |
| judge PASS and no added_content | 58 | 24/58 = 41.4% [30, 54] | 24/58 = 41.4% [30, 54] | 11/58 = 19.0% [11, 31] |
| judge FAIL | 20 | 20/20 = 100.0% [84, 100] | 20/20 = 100.0% [84, 100] | 10/20 = 50.0% [30, 70] |

Why, for the 44 rater-items the judge passes but the SLP marks partly/no (primary reason from the SLP's note and a diff against the input; no writer sentence exists for these items; note regexes, so approximate):

| group | n | critical | fluency | substitution | added | dropped | reword |
|---|---|---|---|---|---|---|---|
| judge PASS, SLP partly/no | 44 | 0 (0%) | 3 (7%) | 11 (25%) | 19 (43%) | 6 (14%) | 5 (11%) |
|   arm chip | 7 | 0 (0%) | 1 (14%) | 0 (0%) | 3 (43%) | 1 (14%) | 2 (29%) |
|   arm guard_original | 0 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
|   arm guard_repair | 27 | 0 (0%) | 2 (7%) | 11 (41%) | 10 (37%) | 2 (7%) | 2 (7%) |
|   arm word | 10 | 0 (0%) | 0 (0%) | 0 (0%) | 6 (60%) | 3 (30%) | 1 (10%) |

Of these, SLP note mentions adding/assuming content: 30%; model produced a content word not in the input: 64%; judge `added_content`=yes: 45%.

- SLP1: judge pass vs SLP 'yes': kappa 0.19, SLP says yes 15/50 = 30.0% [19, 44], judge pass 40/50 = 80.0% [67, 89]
- SLP2: judge pass vs SLP 'yes': kappa 0.31, SLP says yes 21/50 = 42.0% [29, 56], judge pass 40/50 = 80.0% [67, 89]

## 3. Bridge metric: what predicts rejection beyond the critical label?

Deployable predictors need only the input and the output (judge `added_content`, length ratio output words / keyword count, number of output content lemmas not in input or chip realisation). Oracle-ish predictors need the writer's own sentence (lexical overlap) and are not available in use. No local embedding model: similarity is lexical (content-lemma Jaccard and token F1 with the writer's sentence). AUROC > .5 means higher value goes with rejection (similarity is sign-flipped so higher = more likely rejected). 95% CIs: item bootstrap (writer-cluster CI in the second CI column).

**Part 18, judge-RIGHT items, outcome R1 (writer: not the intended version)** (n=126, rejected 77)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| judge added_content (deployable) | 0.635 | [0.578, 0.695] | [0.580, 0.688] |
| length ratio to keywords (deployable) | 0.764 | [0.677, 0.843] | [0.679, 0.843] |
| novel content words vs input (deployable) | 0.675 | [0.616, 0.735] | [0.626, 0.727] |
| 1 - Jaccard with writer sentence (oracle) | 0.642 | [0.548, 0.734] | [0.548, 0.734] |
| 1 - token F1 with writer sentence (oracle) | 0.641 | [0.541, 0.731] | [0.549, 0.729] |

**Part 18, judge-RIGHT items, outcome R2 (acceptance = no)** (n=130, rejected 69)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| judge added_content (deployable) | 0.627 | [0.563, 0.688] | [0.576, 0.675] |
| length ratio to keywords (deployable) | 0.780 | [0.693, 0.857] | [0.710, 0.850] |
| novel content words vs input (deployable) | 0.702 | [0.641, 0.760] | [0.653, 0.750] |
| 1 - Jaccard with writer sentence (oracle) | 0.656 | [0.571, 0.744] | [0.579, 0.738] |
| 1 - token F1 with writer sentence (oracle) | 0.656 | [0.570, 0.740] | [0.584, 0.734] |

**Part 18, all items, outcome R1** (n=195, rejected 146)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| critical label wrong (judge) | 0.736 | [0.695, 0.776] | [0.707, 0.769] |
| judge added_content (deployable) | 0.644 | [0.596, 0.689] | [0.606, 0.676] |
| length ratio to keywords (deployable) | 0.709 | [0.626, 0.785] | [0.627, 0.787] |
| novel content words vs input (deployable) | 0.676 | [0.630, 0.723] | [0.637, 0.713] |
| 1 - Jaccard with writer sentence (oracle) | 0.626 | [0.542, 0.702] | [0.524, 0.721] |
| 1 - token F1 with writer sentence (oracle) | 0.626 | [0.543, 0.706] | [0.531, 0.723] |

**Incremental value over the critical label, Part 18 all items, outcome R1** (n=195; 5-fold CV ridge-logit scores, mean AUROC over 10 CV seeds; bootstrap resamples items and refits)

| model | AUROC | item CI | delta vs critical alone | delta CI |
|---|---|---|---|---|
| critical (binary, raw AUROC) | 0.736 | [0.699, 0.777] | +0.000 | [+0.000, +0.000] |
| critical + judge added | 0.769 | [0.727, 0.819] | +0.033 | [-0.010, +0.068] |
| critical + length ratio | 0.865 | [0.819, 0.911] | +0.129 | [+0.077, +0.175] |
| critical + novel words | 0.798 | [0.746, 0.839] | +0.062 | [+0.012, +0.094] |
| critical + all 3 deployable | 0.875 | [0.828, 0.924] | +0.139 | [+0.086, +0.190] |
| critical + all 3 + Jaccard (oracle) | 0.873 | [0.825, 0.924] | +0.137 | [+0.084, +0.192] |

(300 bootstrap resamples for the incremental table, so those intervals are rougher.)

**SLP, judge-PASS rater-items, outcome says partly/no (bootstrap over the 50 items; both raters kept together)** (n=80, rejected 44)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| judge added_content (deployable) | 0.699 | [0.620, 0.783] | [0.596, 0.803] |
| length ratio to keywords (deployable) | 0.705 | [0.584, 0.809] | [0.552, 0.847] |
| novel content words vs input (deployable) | 0.765 | [0.674, 0.851] | [0.650, 0.863] |

**SLP, judge-PASS rater-items, outcome acceptable != yes** (n=80, rejected 44)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| judge added_content (deployable) | 0.699 | [0.617, 0.783] | [0.599, 0.798] |
| length ratio to keywords (deployable) | 0.705 | [0.582, 0.813] | [0.559, 0.844] |
| novel content words vs input (deployable) | 0.765 | [0.669, 0.848] | [0.652, 0.876] |

**SLP, all rater-items, outcome says partly/no** (n=100, rejected 64)

| predictor | AUROC | item CI | cluster CI |
|---|---|---|---|
| judge meaning_fail | 0.656 | [0.600, 0.714] | [0.578, 0.735] |
| judge added_content (deployable) | 0.675 | [0.604, 0.740] | [0.589, 0.763] |
| length ratio to keywords (deployable) | 0.734 | [0.629, 0.830] | [0.611, 0.853] |
| novel content words vs input (deployable) | 0.731 | [0.653, 0.810] | [0.632, 0.826] |

## 4. Representative examples (declared rule)

Rule: among judge-RIGHT items, writer rejected (R1), take for each primary reason the item with the smallest sha256(`20261102|whole|<reason>|<item id>`); for SLP, among judge-PASS items with SLP says partly/no, one per primary reason by the same hash. No cherry-picking beyond that; every reason with at least one item is shown.

- Part 18, **fluency** (1 such items). Input `Keywords: [YES] quiet music`; writer meant: "I ask for quiet in the music room."; output: "Yes, quiet music."; writer note: "Quiet music is not a request for quiet in the music room."; critical value correct per judge.
- Part 18, **substitution** (56 such items). Input `Keywords: [SURE] taxi wait`; writer meant: "The taxi waits outside the main gate."; output: "I am sure I need to wait for the taxi."; writer note: "I wait for the taxi rather than the taxi waiting at the gate."; critical value correct per judge.
- Part 18, **dropped** (19 such items). Input `Keywords: [SURE] soup warm`; writer meant: "The soup is warm in the kitchen."; output: "The soup is definitely warm."; writer note: "Adds definite certainty and omits the kitchen."; critical value correct per judge.
- Part 18, **reword** (1 such items). Input `Keywords: [?] cousin enter room`; writer meant: "Can your cousin enter my room now?"; output: "Does my cousin enter the room?"; writer note: "Changes your cousin to my cousin and permission to usual action."; critical value correct per judge.
- SLP, **fluency** (3 rater-items). Input `Keywords: [ASK] [YOU] [PLAIN] mail documents`; output: "Ask you for mail documents."; SLP says "partly", acceptable "edit"; note: "Use Mail the documents rather than the incomplete reporting phrase.".
- SLP, **substitution** (11 rater-items). Input `Keywords: [TELL] bus stop hospital`; output: "I need to go to the hospital from the bus stop."; SLP says "no", acceptable "no"; note: "Invents the speaker needing hospital travel instead of stating something about the bus stopping at the hospital.".
- SLP, **added** (19 rater-items). Input `Keywords: please put soup bowl`; output: "Please put the soup bowl on the table."; SLP says "partly", acceptable "edit"; note: "Remove the invented table; confirm soup into a bowl versus moving a soup bowl.".
- SLP, **dropped** (6 rater-items). Input `Keywords: [NOT] fan make`; output: "The fan doesn't make."; SLP says "partly", acceptable "no"; note: "Negation survives but make is missing its complement; the message cannot be recovered safely.".
- SLP, **reword** (5 rater-items). Input `Keywords: you check forms`; output: "Can you check the forms?"; SLP says "partly", acceptable "edit"; note: "A request is plausible, but these words can also state what the listener does. Confirm the intended speech act.".
## 5. Draft paragraph (for the authors; papers not edited)

A metric that checks one critical commitment (negation, speech act, agent, certainty, politeness or time) is necessary but not sufficient evidence that a message "said what the user meant". In our writer-intent check, the judge found the critical value correct for 130 outputs, yet writers said 77 of 126 (61%) were not the version they meant and accepted only 1 of 130 as written. Classifying the writers' notes against their own sentences, the main reasons were not paraphrase (about 1%) but a different event or role than intended (e.g. "I wait for the taxi" for "the taxi waits at the gate", 32% of all non-accepted outputs by our diff rule) and details the writer meant but the keywords do not carry (place, time, object; the writer's sentence contained such a word in 98% of cases). Added content that the user did not request is a real but smaller share: the model introduced content words absent from the input in 22% of judge-correct, non-accepted outputs, and the judge's own added-content flag was set for 45% of the outputs on which SLPs marked "partly" or "no" despite a judge pass. Expert SLPs showed the same gap: the judge passed 40 of 50 outputs (80 rater-items) but the SLPs marked 44 of those 80 partly or no. A cheap signal that needs no human label, the ratio of output length to the number of keywords given, ranks writer rejection among judge-correct outputs with AUROC 0.76 (95% item-bootstrap CI 0.68 to 0.84), and adding it with two other deployable features to the critical label raises cross-validated AUROC from 0.74 to 0.88. We therefore recommend reporting an "unrequested content" column beside critical-commitment preservation, and we read the headline preservation rates as an upper bound on whole-message fidelity. Limits: writers rated 10 outputs each of their own pairs, whose sentences are richer than keyword input by construction; two SLPs; one prompt and four models; a rule-based, partly LLM-validated reason classifier (agreement with hand coding 80%, optimistic because the rules were tuned on that sample).

Note on examples: the single `reword` Part 18 example is a classifier miss on inspection (the note says the agent and speech act changed), shown because the rule was fixed in advance.
