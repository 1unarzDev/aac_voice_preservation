# CALE-AI cycle 1 changes

Build: docker latexmk, 8 pages total, body ends about one fifth of the way down page 7 (limit 8, excluding references). No undefined macros.

## Files changed
- `main.tex` rewritten (comment header trimmed; stale history removed).
- `make_macros.py`: new block reading analysis JSON/CSV. Macros `ra_*` (Part 4 pilot), `rt_*` (Part 11 transfer), `hw_*` (hw1), `el_*` (elicitation), `p17_*`/`p18_*` (typed design constants only). Example outputs are read from `items.csv` by the declared rule "first three consensus-unusable repaired items in hash order, per pool".
- `figs/make_caleai_figs.py`: chip cost label now "+1 selection" with footnote "nominal; dwell, scanning and learning not counted". `fig_ledger.*` regenerated.
- `results_macros.tex` regenerated (additions only in new keys).

## Changes by task item
1. Title, abstract, intro and conclusion reframed as "gain-only evaluation hides failures", with the ledger. The guard is the single lead; I2 and the chip are "bounded" rows. A glossary table (Table 1) was added.
2. The abstract states the guard's +9.83 pp transfer gain next to the pilot gap (58.8% vs 89.5%, -30.7 [-54.7, -2.0], 20+20, raters not independent, controls never failed, "consistent with a cost"), Part 11 (77.8% vs 77.8%), and Part 17 with its frozen rule. New section 6.2 and Table 4 show unusable repairs (real stored outputs). Spots: `% PART17` (abstract and 6.2).
3. The false "each intervention passed" conclusion was replaced. The conclusion, contribution 3, the Fig. 1 caption and the chip paragraph now say the chip failed its >=80%-of-full clause on W-C.
4. New 6.4 "Bridge to realistic input": hw1 (chip gain on all 6 dimensions, P1/P2/P3 replicate in direction; exploratory, 6-7 writers; ~50-pp ceiling caveat) and elicitation (20.8% vs 100%, politeness reversal, alpha .61), all via macros.
5. Section 7 is now falsifiable predictions H1 (writer intent, Part 18; `% PART18` spot), H2 (repair usability, Part 17) and H3 (MRT).
6. Anonymity: removed "earlier version", "critical review retired" and the "No autistic advisers" process phrasing, replaced by a neutral "Community involvement" limitation. No URLs or names; `\pending{anonymized artifact URL}` kept. The ethics paragraph now includes the coordinator-supplied facts: adult non-authors recruited from the authors' university peers, consented, reimbursed with payment and food (university not named).
7. Claim discipline: "pre-specified and git-timestamped"; the 20.8% vs 100% comparison is flagged as against a deliberately crude comparator; the 62.76% vs 2.70% departures are stated to reflect prompt design.
8. AAC wording: "crowd-written AACText (fictional)"; the chip is a probe with costs (access method, dwell/scanning, vocabulary learning, literalization); "spoken as the user's own" became "may speak on the user's behalf, sometimes after review"; authorship-vs-rewriting and word-input-only limitations added.

## Cuts to make room
Gallery figure (I2 menus), applicability table, W-D detail (one sentence kept), related-work and setting trimming, and the transfer-section audit-detail sentences.

## Caveats for the orchestrator
- The abstract and 6.2 mention original-failed and strip-only arms of Part 17 as instructed; confirm these were added to the Part 17 sheets (the synthesis marked them as needing the user's go-ahead).
- The Part 17 sample size (120) is a typed constant in `make_macros.py`.
- The claim that Part 4 raters "are not independent" is stated without a number (no collapse statistic was computed).
- Judge-validation JSONs (Parts 12/13) are not yet cited in the text.
- Not committed.
