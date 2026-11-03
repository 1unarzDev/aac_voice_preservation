# Annotation request R-WM-1 (updated round 2, 2026-11-02): does removing unrequested content change judged acceptability?

STATUS: items, key and assignment BUILT, NOT SENT. Every machine-only result of this frontier is PROVISIONAL until this returns.
Files: `annotation/frontier_whole_message_items.json` (items for an annotate.html / check_pairs.html style tool), `annotation/frontier_whole_message_key.csv`
(PRIVATE: arm, generator, family, judge flags), `annotation/frontier_whole_message_assignment.csv` (item x annotator). Builder: `src/frontier_whole_message_r2_annot_items.py`
(deterministic, seed string `wm-r2h`).

## Purpose
1. Does the plain prompt's unrequested content (A0: 35% of chip1 outputs flagged by the gpt reference-free judge) make the output less acceptable to
   a person than the preservation prompt (A1) or the minimal-expansion prompt (A2), which flag 6 to 13%? The round-2 machine evidence says the judge flag moves a lot but the
   judge's match-to-the-writer's-sentence score barely moves, so only people can say whether the change matters.
2. Verbatim-copy false-flag check: when the output is just the keywords copied back, does a person see "nothing added" (the gpt UC flag says nothing added for 100/100
   gate copies, but the binary whole-message flag fails 39% of them for dropped glue words or frame). This sets how much to trust the flags near the copy end.

## Items and draw rule (120 items)
- 108 output items = 36 chip1 inputs x 3 arms (A0 plain P0 prompt, A1 preservation P1, A2 minimal-expansion), generator gpt-6.1-terra, greedy d0 outputs, stored in
  `analysis/frontier/whole_message/r2_outputs.csv`. Inputs: 6 families per dimension (polarity, speech_act, agent, certainty, politeness, time_quantity) ranked by
  `sha256("wm-r2h|fam|family_id")` ascending, one variant per family by `sha256("wm-r2h|var|family_id|variant")`. (82 distinct input/output pairs: where two arms produced the
  same sentence the same text appears under two item ids to different annotators.)
- 12 verbatim-copy items: the Part 18 gate-set inputs (analysis/frontier/whole_message PLAN freeze record), the output being the keywords with chips removed, ranked by
  `sha256("wm-r2h|vc|item_id")` ascending.
- Arm labels, judge flags and family ids are not in the items file.

## Who, time
About 20 adult non-author annotators (anonymous ids R01 to R20). No AAC users as participants, no IRB claim, no demographics. Each item is rated by 3 annotators; each annotator
gets 18 items (never two arms of the same input), about 10 minutes (about 30 s per item). Order shuffled per annotator.

## Questions (exact)
Output items (108): the annotator sees the keywords with chips, the two candidate messages the writer meant (version A, version B) and the output.
 Q1. Which version does the output say? A / B / something else / cannot tell.
 Q2. Does the output add anything you did not ask for or leave out something you meant? added / left out / both / neither.
 Q3. Would you accept it as the message? yes / yes with a small edit / no.
Verbatim items (12): the annotator sees the keywords with chips and the output.
 Q4. Does the output say anything beyond the keywords and chips? yes / no.
 Q5. Is it a complete sentence you could say as it is? yes / no.

## Analysis it feeds (declared)
- Acceptability (Q3 yes or small edit) and Q1-match per arm with item-cluster (family) bootstrap CI; paired A2 - A0 and A1 - A0 on the same inputs. Added-content rate (Q2 added or both)
  per arm versus the gpt UC flag (kappa and AUROC of the flag against the majority of 3).
- Verbatim stratum: share of copies a majority call "adds something" (Q4) and "complete" (Q5), against the gpt flags.
- This is the only way to claim that removing unrequested content helps people; without it the claim is limited to "the judge flags less".
- Optional R-WM-2 (2 anonymous SLPs, expert rating of materials only; not built): 30 cards of CK-true outputs with unrequested content, acceptable to speak yes / with edit / no, about 15 minutes each.
