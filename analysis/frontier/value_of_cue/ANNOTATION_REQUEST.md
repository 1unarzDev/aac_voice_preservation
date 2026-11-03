# Annotation request (value_of_cue) -- NOT SENT. Items and key are built; the orchestrator batches the send.

## Part B (primary request, round 2): measure q, the chance a writer picks the right sentence when SHOW-TWO offers the default and a cue-restored alternative
**Purpose.** Every gain reported for the SHOW-TWO action (the only action the policy chooses) is conditional on an ASSUMED q = 0.9 (sweep 0.5-1.0 in round2.md). The result's sign depends on q only weakly
(P-K beats B5 and B1 by point estimate at every q >= 0.3) but its size does not (4.5% at q = 0.5 vs 9.3% at q = 1.0 at 100 taps). One measured q with a CI replaces the assumption.
**Items.** 145 items, built (no model outputs were edited): annotation/frontier_value_of_cue_items.json, key annotation/frontier_value_of_cue_key.csv (key hidden from annotators).
Draw rule: sha256(seed "voc2-2026-11-02" | stratum | dimension | message id) rank, one item per message. Stratum A (108 items; polarity 40, speech act 36, politeness 32): the stored qwen2.5-7b P0 sentence
LOST the cue the source message had. Stratum B control (31 items): the source has NO cue on that dimension and the default sentence is right, so the alternative adds an unmeant cue (measures wrong picks).
Default sentence = the real stored P0 output. Alternative = real gpt-6.1-terra output of the same P0 prompt with ONE cue chip added to the writer's keywords ([NOT], [?]/[ASK] from the detector source act, [PLEASE]).
A/B order randomised per item (seeded); which one is the alternative is in the key only.
**Question shown.** The original message, the keywords the writer typed, sentence A, sentence B. Q1: "Which sentence says the same thing as the original message about <the cue>?" (A / B / both equally / neither).
Q2: "If you had typed those keywords, which sentence would you tap to say your message?" (A / B / neither). No arm, policy, model or judge labels shown.
**Who.** About 20 adult non-author annotators, never an elicitation writer of that message; 2 independent annotators per item (290 judgments, about 15 items each), about 12 minutes per person. No SLPs, no AAC users, no IRB.
**Feeds.** q-hat per dimension and pooled with a message-cluster bootstrap CI (stratum A, Q2 = alternative picked; Q1 as a cross-check), the wrong-pick rate from stratum B (the real cost of showing a spurious alternative),
and the "both/neither" share (does the offered alternative actually cover the meaning). q-hat replaces the assumed q in the frontier, the break-even statement and the H3 calibration; inter-annotator kappa with CI is reported.
Until it is scored all SHOW-TWO numbers stay PROVISIONAL and conditional on q.

## Part A (secondary, NOT built): validate the outcome metric
160 units by hash rank (4 strata x 40: committed-and-scored-reversal, committed-and-scored-fine, policy-asks-and-reversal, policy-commits-and-reversal), Q1 same/different/cannot tell about the dimension, Q2 recoverable from keywords. Feeds metric validity and
re-weighting by validated precision. Build only after Part B is scored and the policy is frozen; Part 21 source-label check covers the detector source labels.

## Round-3 addendum (still NOT SENT)
Part B is final as built (145 items, annotation/frontier_value_of_cue_items.json, key annotation/frontier_value_of_cue_key.csv). What the answers replace in round 3: q (q-hat per dimension; round3.md shows P-I minus B5 stays positive for all q in 0.3-1.0 but the share averted moves from 6.5% to 15.7%), the stratum-B wrong-pick rate (the mis-pick probability m in the cost model, assumed 0-0.10), and the share of "both/neither" (alternative adequacy). Because the policy only ever prompts speech-act SHOW-TWO, the speech-act items (36 in stratum A) are the ones that matter most; if annotator time is short, send speech-act stratum A plus the whole stratum B control first.
