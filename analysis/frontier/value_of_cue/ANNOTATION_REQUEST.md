# Annotation request (value_of_cue) -- NOT SENT; items are built after Stage 3 freezes the policy (so the draw can be applied to real policy decisions)

**Purpose.** Validate the outcome metric behind the frontier: is a unit scored "silent reversal" (source had the cue, keywords dropped it, output lacks it) really a reversal of what the writer meant?
Without this the frontier rests on detector source labels and arbiter-labelled outputs. Part 21 (source-label check) covers source labels; this check covers the unit-level verdict and policy-flagged units.
**Items.** 160 units drawn by hash rank (seed string `voc-2026-11-02`, sha256(seed|stratum|unit id)): 4 strata x 40: (a) committed and scored reversal, (b) committed and scored fine,
(c) policy asks (risk high) and scored reversal, (d) policy commits (risk low) and scored reversal (the policy's misses). One unit per message, stratified over dimensions polarity/speech act/politeness.
**Question shown per item.** Source message, keywords the writer typed, and the sentence the model produced. Q1: "Does the sentence say the same thing as the original message about <dimension>?" (same / different / cannot tell).
Q2: "Could you tell from the keywords alone that this part was meant?" (yes / no / unsure). No arm, policy or judge labels shown.
**Who.** ~20 adult non-author annotators (never the writer of that keyword set), 2 per item, 16 items each, ~8 minutes per person. No SLPs needed, no AAC users, no IRB.
**Feeds.** Metric validity (Q1 agreement with the arbiter verdict; kappa with CI), re-weighting of the frontier by validated precision per stratum, and the statement of whether keyword-only recoverability (Q2) explains where the policy cannot help.
**Files to build later:** annotation/frontier_value_of_cue_key.csv, annotation/frontier_value_of_cue_sample.json (annotate.html / check_pairs-style). Until then all numbers are labelled PROVISIONAL.
