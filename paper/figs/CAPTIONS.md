# Figure captions (refreshed ACTION 2)

Generated from `runs/main1/scored.parquet` with `annotation/label_resolution.jsonl` by `paper/figs/make_figs.py` and `src/refresh_captions.py`. Original captions and numbers remain in `analysis/evidence_prev/paper/figs/`. The generated figure numbers, macros and example manifest share this scoring version. The design contains 60 test families; primary estimates use **58 families**, excluding act-10 and act-16. Four fixed models. Quarantine-inclusive figures and numbers are in `quarantine_inclusive/`. All automated rates are provisional; human oracle validation remains pending.

CIs are pointwise 95% percentile intervals from 2,000 whole-family bootstrap resamples, seed 20261031. Families are resampled jointly over models, targets and paired arms. Exact counts and denominators are retained in `fig_numbers.json` and `example_manifest.json`. Primary exclusions apply to every figure. Time and quantity each contain five families and are displayed separately.

## fig_pipeline

**Channel-controlled attribution.** Minimal-pair family pol-07, with stored gpt-6.1-terra P0 bare output "I like the medication.". Noncritical input uses the stored order `like new medication`. Bare/noncritical reference match measures a model's chosen reading; the added word is a length control and default-sensitivity diagnostic. Supplied-cue correctness is assessed in chip1/chipall/full. Full means source visible to the generator; extraction remains blind to source, model and channel. Loss, Violation and Assumption have different denominators. This is a selected example, not a typicality claim.

## fig_defaults

**Choices under ambiguous keywords.** P0 bare, 232 distinct family/model outputs from 58 primary families. A/B duplicate requests count once. polarity affirmative: 100.00% [100.00, 100.00] (n=40); certainty plain assertion: 90.00% [80.00, 100.00] (n=40); agent speaker: 67.50% [42.50, 87.50] (n=40); speech_act statement: 75.00% [53.12, 93.75] (n=32). The 50% line follows from balanced authored pairs, not a population preference or fairness target.

## fig_channel_ladder

**Reference match and supplied-predicate preservation.** P0, 2320 target occurrences (58 families × two targets × five channels × four models). bare: 38.79% [33.84, 43.32]; noncrit: 41.81% [37.07, 45.91]; chip1: 94.83% [91.38, 97.63]; chipall: 95.91% [94.18, 97.41]; full: 97.41% [95.04, 99.14]. Bare/noncritical values are ambiguous reference match; chip1/chipall/full assess supplied cues. The orange dashed line adds joint preservation of scored supplied predicates. joint chip1: 94.83% [91.38, 97.63] (n=464); joint chipall: 92.46% [89.44, 95.26] (n=464); joint full: 96.77% [93.97, 99.14] (n=464). Two refusal/acceptance families are quarantined rather than counted as primary passes.

## fig_cost_asymmetry

**Nominal extra selections.** 50 primary families have an identified default; 8 primary families lack one and are excluded. Default is the modal bare P0 pair value across four models; ties use cached P2/S3 outputs. Cost is zero for a matching first suggestion, one when the target occurs later in the three-suggestion set, otherwise the critical chip count. P0_default: 0.195 [0.130, 0.265] (n=200); P0_non-default: 0.925 [0.880, 0.965] (n=200); P2_default: 0.230 [0.145, 0.330] (n=200); P2_non-default: 0.855 [0.780, 0.920] (n=200). This counts nominal selections, omits reading/navigation time, and does not guarantee the chip repair succeeds.

## fig_politeness_ratchet

**Full-mode politeness additions and removals.** P0, ten politeness families: plain→polite 22.50% [10.00, 37.50] (9/40), polite→plain 5.00% [0.00, 12.50] (2/40). Per-model addition counts are Qwen 0/10, Llama 1/10, Gemma 6/10, Terra 2/10; these are ten-family intervals. Hedging controls show 0/40 additions and 0/40 removals. Across primary families whose source spec is plain, 10/424 full-mode outputs add politeness. Cached P1 sensitivity remains separate from the primary prompts: 4/40 additions, 6/40 removals.

## fig_sets

**Coverage of both authored readings among three suggestions.** Bare, one set per family/model/arm. P2: 33.62% [25.86, 41.38] (78/232 sets); S3: 3.88% [1.29, 6.90] (9/232 sets). P2 requests three different meanings; S3 samples three P0 outputs at temperature 0.7. Polarity P2 is 25.00% [12.50, 40.00] (10/40), after propagating the arbiter to span1. This is authored-pair coverage under machine labels, not coverage of all admissible meanings.

