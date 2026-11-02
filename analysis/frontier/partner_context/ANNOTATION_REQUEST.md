# Annotation request (DRAFT, not sent): partner-turn neutrality and naturalness
Purpose: validate the machine neutrality/manipulation checker and naturalness of the model-authored partner turns (feeds R9: removes the PROVISIONAL label).
Items: 120 turns = 30 per type (N, D, X, Q), seeded draw (seed 20261102) stratified over polarity/speech_act/certainty, taken from turns.jsonl after Stage 0. Items JSON + key (annotation/frontier_partner_context_key.csv) are built after Stage 0 (not yet built).
Question 1: "Which meaning does the partner's remark make more likely for the reply?" options: reading 1 / reading 2 / neither (reading order shuffled; readings shown as neutral descriptions).
Question 2: "How natural is this as something a conversation partner might say?" 1-5.
Who: ~20 adult non-author annotators, each 30 items, 2 raters per item. No AAC users, no SLPs, no IRB. About 10 minutes per person.
Analysis: agreement with the checker (kappa); N/Q pass if >=70% "neither" by humans, D/X pass if >=70% favor declared direction; naturalness median >= 3. Failing turn types are reported, not re-run post hoc.
