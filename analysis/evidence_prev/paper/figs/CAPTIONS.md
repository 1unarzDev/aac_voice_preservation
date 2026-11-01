# Figure captions (draft)

Source: `runs/main1/scored.parquet` + `data/items/*.jsonl`, built by `paper/figs/make_figs.py`.
Every number below is in `fig_numbers.json`, which the script regenerates; re-check these captions after any rerun.
60 families (test split), 4 models (GPT-6.1-terra, Qwen2.5-7B, Llama-3.1-8B, Gemma-3-4B).
Every CI is a 95% percentile interval from 2,000 whole-family bootstrap resamples (seed 20261031).
`time_quantity` is shown as two rows, **Time** (5 families, past/now/later) and **Quantity** (5 families, two numbers), because the two kinds of pair have different value sets.

Sizes: single-column figures are 3.2–3.3 in wide and double-column figures 6.0–6.9 in, with 7 pt text (6–6.5 pt for ticks and annotations). Include them at `\columnwidth` / `\textwidth`. This works for both AAAI (3.3/7.0 in) and IEEE (3.5/7.16 in).

---

## fig_pipeline (double column)

**Method.** Each family is a minimal pair of source messages that differ on one critical dimension (here polarity, family pol-07). Each variant is compressed into five visible input channels. *bare* is the content words, which are identical for both variants. *+noncritical* adds one content word that leaves the critical dimension open (a length control). *+chip* adds the critical chip. *+all chips* adds every commitment chip. *full* is the typed source sentence. Blue channels contain the critical cue. An LLM (4 models; prompts P0, P2, S3) writes the output. A blind judge extracts values from the output alone; it never sees the source, model or channel. Loss, Violation and Assumption are then computed deterministically by comparing the extracted value with the item specification and the channel. The three have different denominators and are not exclusive shares of one total. The output shown is GPT-6.1-terra's stored P0 response to the bare input "like medication": "I like the medication." (affirmative, speaker, statement).

## fig_defaults (double column)

**What the model says when the keywords don't decide.** Bare channel, generic prompt P0, one output per family × model; variants A and B send an identical request, so it is counted once. n = 240 outputs from 60 families (40 per dimension; 20 each for Time and Quantity). Bars show the pooled share of outputs expressing each value, with family-bootstrap 95% CIs. Open markers show each model. The dashed line at 50% is what a balanced minimal pair implies. Polarity: 100% affirmative [100, 100] and 0% negated, in all four models. Certainty: 90% plain [80, 100], 0% hedged. Agent: 68% speaker [42, 88]. Speech act: 68% statement [50, 85]. Politeness is the only dimension near balance (55% plain / 45% polite). Quantity: 0 of 20 outputs state either number of the pair (100% unclear). Time is split between now (30%), later (30%), unclear (30%) and past (10%).

## fig_channel_ladder (double column)

**A cue restores the meaning; extra length does not.** Critical-match rate by visible input channel, P0, n = 2,400 outputs (60 families × 2 variants × 5 channels × 4 models). The blue line is pooled over models, with a family-bootstrap 95% band; grey markers show each model. The shaded region marks channels where the critical cue is visible. Under bare and +word, one output serves both variants, so match cannot exceed 50% (dashed line). Below that line, match is not accuracy; it reflects which reading the model chose. Pooled over dimensions: bare 38% [33, 43], +word 41% [37, 45], +chip 94% [91, 97], +all chips 95% [92, 97], full 97% [95, 99]. Adding the noncritical word leaves match essentially unchanged; this is an aggregate claim, and individual outputs do change. A single chip brings polarity, agent, certainty and time to ≥ 99%. Speech act (81% [68, 92] with +chip) and politeness (86% [76, 95] even under full) remain below ceiling.

## fig_cost_asymmetry (single column)

**The non-default meaning costs an extra action.** Mean extra input actions the user needs before the system shows the target reading, starting from the bare input. A family's *default reading* is the pair value produced most often by P0 under bare across the 4 models. P0 ties are broken by the bare P2/S3 outputs. Eight families have no default because their P0 outputs never committed to either pair value (all 5 Quantity families, 1 Time, 1 Agent) or stayed tied (1 Politeness); they are excluded, leaving 52 families and 208 targets per prompt. P0 cost: 0 if the single suggestion has the target value, otherwise the target's chip count. P2 cost: 0 if the first suggestion matches, 1 if the target appears among the 3 suggestions, otherwise the chip count. Pooled P0: default 0.21 [0.14, 0.28] vs non-default 0.93 [0.88, 0.97] actions. Pooled P2: 0.25 [0.16, 0.34] vs 0.86 [0.79, 0.92]. For polarity the gap is total (0 vs 1.0) under both prompts. P2 narrows the gap only for politeness (0.44 vs 0.56). The cost model counts selections only; it omits the time spent reading and checking suggestions.

## fig_politeness_ratchet (single column)

**When the user types the whole sentence, politeness is added but not removed.** Full channel (the source sentence typed verbatim), P0. Left panel: the 10 politeness families; share of outputs that add a politeness marker to a plain source (n = 40) vs drop it from a polite source (n = 40). Right panel: the 10 certainty families; hedges added to plain sources (n = 40) vs removed from hedged sources (n = 40). Pooled, politeness is added to 22% [10, 38] of plain sources and removed from 5% [0, 12] of polite ones. Gemma-3-4B adds politeness to 60% [30, 90] of plain commands, GPT-6.1-terra to 20% [0, 50]. Hedging is preserved exactly in both directions (0/40, 0/40). Over all 440 plain-politeness sources in the 60 families, the addition rate is 2.3% (Gemma 6.4%), so the effect is concentrated in bare commands. Per-model CIs rest on 10 families each.

## fig_sets (single column)

**Asking for three different meanings helps only some dimensions.** Coverage@3 is the share of suggestion sets that contain *both* readings of the minimal pair. Bare channel, one set per family × model (n = 40 sets per dimension; 20 for Time and Quantity; 240 sets per prompt). P2 is one request for 3 suggestions covering different meanings. S3 is 3 independent P0 samples at T = 0.7. Points show pooled estimates with family-bootstrap 95% CIs; the columns on the right give the point estimates. Pooled coverage is 32% [25, 40] for P2 and 4% [1, 7] for S3. P2 coverage is highest for politeness (65% [52, 78]) and agent (50% [32, 68]). It stays low for polarity (22% [10, 38]), certainty (12%) and time (10%), and is 0% for quantity. Sampling (S3) almost never covers both readings (0–12%).

---

### Notes for the authors
- **STYLE.md conflict:** STYLE.md (from the pilot, D-013) says "P2 does not cover negation". In main1, polarity P2 coverage is 22% [10, 38]; by model, GPT-6.1-terra 4/10, Gemma 3/10, Llama 1/10, Qwen 1/10. The pilot's "0/16" should not be quoted as the main result. The correct framing is "low, and lower than politeness/agent", not "zero".
- Politeness under full (86%) is *below* +chip (90%). This is consistent with fig_politeness_ratchet: politeness is added to typed plain commands. It is a hypothesis that an explicit [PLAIN] chip suppresses that addition; the difference is not tested.
