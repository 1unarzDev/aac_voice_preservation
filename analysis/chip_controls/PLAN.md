# E2 plan: chip-gain controls on hw1 (threat T3), written BEFORE generation / before any look at outputs

Written 2026-11-02. Source: `ideas/review_j1/SYNTHESIS.md` T3, `methods_review.md`.

## Question
hw1's chip gain is `chip1 - noncrit` (critical-dimension chip vs bare plus one noncritical word). That adds a chip AND the
critical cue at once. Two controls separate them:
- **irrel**: noncrit input plus ONE chip from a different dimension (carries no critical information).
- **nlcue**: the critical cue written as a plain word in the position of the chip (no brackets).

## Arms (hw1 `data/items/hw.jsonl`, all 547 kept families, all 6 dimensions, P0 with legend (sha ad8e7920...), 4 models, one draw, greedy)
Comparators already exist in `runs/hw1` (P0 `noncrit`, `chip1`; draw d0, not regenerated). New channels `irrel` and `nlcue` are in
`runs/hwctl1`, request file `runs/requests/hwctl.jsonl` (items `data/items_ext/hwctl_items.jsonl`, split `hwctl`).

### Declared mapping 1: irrelevant chip (one chip, identical input for A and B)
Chip = the first, in this priority order, of the chips that BOTH variants already commit to (intersection of the variants' `all_chips`)
and that belong to a dimension other than the family's critical dimension:
`[I] [YOU] [WE] [THEY] [PAST] [NOW] [LATER] [TELL] [ASK] [?] [WANT] [MUST]`.
Rationale: the chip is true of both sources (no contradiction, SPEC R5 builder rule), is a different dimension, and cannot separate A from B.
Item-level choices: `analysis/chip_controls/mapping.json`. Resulting chips by critical dimension: agent {[TELL] 57, [PAST] 45};
certainty {[THEY] 83, [TELL] 3, [I] 1}; polarity {[THEY] 74, [I] 25, [WE] 4, [TELL] 1}; politeness {[YOU] 81, [TELL] 4, [I] 2, [THEY] 2};
speech_act {[THEY] 47, [YOU] 21}; time_quantity {[I] 50, [THEY] 39, [WE] 6, [TELL] 2}.
Known limit: the chips are mostly agent chips, not the "time chip" of the brief's example, because a time chip is true of only a minority of sources.
The 3 certainty items with `[TELL]` (a plain statement, arguably near certainty) are flagged `borderline` in mapping.json; a sensitivity run drops them.
The irrel input = the noncrit input + the chip, so irrel - noncrit is the effect of the added chip alone.

### Declared mapping 2: natural-language cue (replaces the chip(s), same position, legend still shown)
`[NOT]` not; `[YES]` yes; `[?]` question; `[TELL]` statement; `[ASK]` request; `[I]` I; `[YOU]` you; `[THEY]` they; `[MAYBE]` maybe;
`[SURE]` sure; `[PLEASE]` please; `[PLAIN]` plain; `[PAST]` past; `[NOW]` now; `[LATER]` later.
Example: `Keywords: not want go party`. The noncritical word is NOT added (as in chip1). The words are plain words; the legend only lists bracketed chips.

## Outcome and contrasts (fixed now)
Outcome = `critical_match` of the P0 output (judge labels, J1==J2 else blind arbiter, no fallback), per (family, variant, model).
Paired by (family, variant, model). Per dimension and pooled over models, plus per model:
- G_chip = chip1 - noncrit (hw1 published), G_irrel = irrel - noncrit (what ANY chip adds), G_nl = nlcue - noncrit,
- **primary control contrasts: chip1 - irrel and chip1 - nlcue**.
CIs: writer-cluster bootstrap (the hw1 primary, 7 writers) and family-cluster bootstrap, 10,000 resamples, seed 20261031; exclusions as in `analysis/hw1`
(speech-act refusal/acceptance quarantine, writer P06 speech-act pair). A t-interval over writers is added as small-cluster sensitivity.
Also reported: literalization rate (output contains a bracketed chip, or the words "I tell you"/"tell you"/"statement") by channel and model.

## Decision rules (fixed now, per dimension, writer-cluster CI of the primary contrast)
- **Chip effect is the content of the cue (not "any chip"):** chip1 - irrel > 0 with the CI lower bound > 0. If not, that dimension's chip gain
  must be reported as a manipulation check or generic added-token effect, not as a cue-specific gain.
- **Chip beats natural language:** chip1 - nlcue > 0 with CI lower bound > 0. **NL equals chip:** the whole CI inside +/-5 pp.
  **NL beats chip:** CI upper bound of (chip1 - nlcue) < 0. Else "inconclusive".
- Polarity and politeness are expected to be near-manipulation checks (the cue word is the label); this is reported, not hidden.
- Nothing is dropped after outputs are seen; the borderline-certainty sensitivity is the only declared exclusion variant.
