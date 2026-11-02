# Representative examples (declared rule, no cherry-picking)

Rule: per dimension, order kept & analysed families by SHA256(family_id); take the first family that has, in P0,
a bare-channel output that is committed (not unclear) yet does not match the variant's critical value, while the
chip1 output for the same family/variant/model does match. Within the family: models in alphabetical order, then variant A, then B.
All text below is the stored model output; labels are the stored judge/arbiter labels. The rates show how typical the example is (writer-cluster 95% CI, pooled over models).

## polarity

Family `hw-pol-075` (writer P18); first of 104 qualifying families by hash; model `gemma3-4b`, variant B (target value: **negated**). Source sentence: "The supervisor does not read my schedule."

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: supervisor read` | The supervisor read. | affirmative | agree |
| noncrit | `Keywords: supervisor read schedule` | The supervisor read the schedule. | affirmative | agree |
| chip1 | `Keywords: [NOT] supervisor read` | The supervisor did not read. | negated | agree |
| chipall | `Keywords: [NOT] [TELL] [THEY] supervisor read` | The supervisor did not read. | negated | agree |
| full | `The user typed: The supervisor does not read my schedule.` | The supervisor does not read my schedule. | negated | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 49.8 [49.5, 50.0]% of bare rows (n=832, 7 writers); when they do, the chip1 output matches the target 99.3 [98.6, 99.8]% of the time (n=414). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 49.5 [49.0, 49.9] pp.

## speech_act

Family `hw-act-005` (writer P01); first of 66 qualifying families by hash; model `gemma3-4b`, variant B (target value: **question**). Source sentence: "Does the café serve lunch near the station?"

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: cafe lunch` | I want a lunch at the cafe. | statement | agree |
| noncrit | `Keywords: cafe lunch near` | I want a lunch at a cafe near. | statement | agree |
| chip1 | `Keywords: [?] cafe lunch` | Is the cafe open for lunch? | question | agree |
| chipall | `Keywords: [?] [THEY] cafe lunch` | Do they want to go to the cafe for lunch? | question | agree |
| full | `The user typed: Does the café serve lunch near the station?` | Does the café serve lunch near the station? | question | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 56.0 [52.1, 63.0]% of bare rows (n=536, 6 writers); when they do, the chip1 output matches the target 75.3 [66.0, 83.2]% of the time (n=300). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 35.3 [31.2, 40.3] pp.

## politeness

Family `hw-plt-029` (writer P04); first of 89 qualifying families by hash; model `gpt-6.1-terra`, variant A (target value: **plain**). Source sentence: "Save my seat near the classroom window."

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: save seat window` | Please save me a seat by the window. | polite | agree |
| noncrit | `Keywords: save seat near window` | Save me a seat near the window. | plain | agree |
| chip1 | `Keywords: [PLAIN] save seat window` | Save me a seat by the window. | plain | agree |
| chipall | `Keywords: [ASK] [YOU] [PLAIN] save seat window` | Save me a seat by the window. | plain | agree |
| full | `The user typed: Save my seat near the classroom window.` | Save my seat near the classroom window. | plain | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 50.0 [50.0, 50.0]% of bare rows (n=712, 6 writers); when they do, the chip1 output matches the target 82.0 [79.5, 84.6]% of the time (n=356). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 38.2 [36.8, 39.4] pp.

## agent

Family `hw-agt-102` (writer P20); first of 102 qualifying families by hash; model `gemma3-4b`, variant B (target value: **addressee**). Source sentence: "You called the neighbor about the keys."

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: call neighbor` | I want to call my neighbor. | speaker | agree |
| noncrit | `Keywords: call neighbor keys` | I want to call my neighbor. | speaker | agree |
| chip1 | `Keywords: [YOU] call neighbor` | You call the neighbor. | addressee | agree |
| chipall | `Keywords: [TELL] [YOU] [PAST] call neighbor` | You told your neighbor in the past. | addressee | agree |
| full | `The user typed: You called the neighbor about the keys.` | You called the neighbor about the keys. | addressee | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 66.2 [63.5, 68.9]% of bare rows (n=816, 7 writers); when they do, the chip1 output matches the target 100.0 [100.0, 100.0]% of the time (n=540). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 67.3 [64.8, 69.9] pp.

## time_quantity

Family `hw-tim-041` (writer P08); first of 75 qualifying families by hash; model `llama3.1-8b`, variant A (target value: **past**). Source sentence: "I cooked the vegetables in the kitchen yesterday."

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: cook vegetables` | I will cook the vegetables. | later | agree |
| noncrit | `Keywords: cook vegetables kitchen` | I will cook the vegetables in the kitchen. | later | agree |
| chip1 | `Keywords: [PAST] cook vegetables` | I cooked vegetables in the past. | past | agree |
| chipall | `Keywords: [TELL] [I] [PAST] cook vegetables` | I cooked vegetables. | past | agree |
| full | `The user typed: I cooked the vegetables in the kitchen yesterday.` | I cooked the vegetables in the kitchen yesterday. | past | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 30.8 [26.6, 35.5]% of bare rows (n=776, 7 writers); when they do, the chip1 output matches the target 98.3 [96.6, 99.6]% of the time (n=239). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 82.7 [80.1, 86.0] pp.

## certainty

Family `hw-cer-062` (writer P16); first of 87 qualifying families by hash; model `gemma3-4b`, variant A (target value: **hedged/uncertain**). Source sentence: "The team meeting might finish by four."

| channel | input given to the model | stored output | judged label | label source |
|---|---|---|---|---|
| bare | `Keywords: team meeting` | The team needs to have a meeting now. | plain assertion | agree |
| noncrit | `Keywords: team meeting finish` | The team meeting must finish now. | plain assertion | agree |
| chip1 | `Keywords: [MAYBE] team meeting` | Maybe there will be a team meeting. | hedged/uncertain | agree |
| chipall | `Keywords: [TELL] [MAYBE] [THEY] [LATER] team meeting` | They might have a team meeting later. | hedged/uncertain | agree |
| full | `The user typed: The team meeting might finish by four.` | The team meeting might finish by four. | hedged/uncertain | agree |

Rate the example represents: in this dimension, bare outputs that commit to a wrong value occur at 40.8 [39.0, 42.2]% of bare rows (n=696, 6 writers); when they do, the chip1 output matches the target 95.4 [93.5, 97.2]% of the time (n=284). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): 54.0 [52.4, 55.3] pp.

