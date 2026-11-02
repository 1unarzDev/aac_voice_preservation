# Annotation request R-WM-1: treated-output check for whole-message fidelity

STATUS: specification only. Items and key will be built by `src/frontier_whole_message_build_items.py` after Stage 3 of PLAN.md
(they sample stored arm outputs). Nothing is sent. Machine-only evidence is provisional until this returns.

Purpose: check that the whole-message metric (M1) and the strategy gains are real to people, not only to a model judge, on outputs
produced by the new strategies (minimal-expansion, exact-copy, contrastive drafts, constrained rewrite) versus the baseline prompts.

Who: about 20 adult non-author annotators (the same pool and tool style as Part 18 / Part 20; writers rate pairs written by others
OR their own, as in Part 18, so the writer-intent question is answerable; no AAC users as participants; no IRB; anonymous IDs).

Items and draw rule: 240 outputs = 12 per annotator. Per annotator, from their own kept pairs where possible: 3 baseline P0, 3 P1,
and 6 from the arms that passed Stage 3 (2 each, or 3 each if two arms), stratified by dimension, chip1 channel, seeded
`sha256("wm-h|writer|output_id")` ascending, arm labels hidden, order shuffled. For contrastive drafts the annotator sees all 3
drafts and picks the one that matches (or "none").

Questions (same wording as Part 18, so the results are comparable):
1. Which sentence does this output say, version A / version B / something else / cannot tell?
2. Does it add anything you did not ask for or leave out something you meant? (added / left out / both / neither). Free text optional.
3. Would you accept it as your message? (yes / yes with a small edit / no).

Time: about 12 min per person (about 1 min per item).

Feeds: human WMF-fail rate per arm with writer-cluster CI, agreement of M1 with Q1 and Q2 (kappa, AUROC), and the AAC-terms
table. No SLP is needed here. Optional R-WM-2 (2 anonymous SLPs, expert rating of materials only): 30 cards of CK-true outputs with
unrequested content, 'acceptable to speak' yes / with edit / no, about 15 min each.
