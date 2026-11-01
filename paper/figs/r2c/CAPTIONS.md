# W-C publication figures

All six figures are available as vector PDF and 600-dpi PNG. Inputs: runs/r2c1/scored.parquet and data/items/r2_c1.jsonl / r2_c2.jsonl. P0 primary outcomes; 238 families after D-018 exclusions. Bars/lines pool the four fixed models; open markers show individual models where indicated. All intervals are pointwise 95% percentile CIs from 10,000 recorded seed/construction-cluster resamples, seed 20261031. Fallback critical J1/J2 labels are unresolved, not definitive labels.

Provenance qualification: 48 generation requests reuse caches older than the final item freeze, including 12 primary requests. All primary generation timestamps postdate the PREREG mtime; the final item freeze did not precede every cached generation. No claim of an unqualified wholly fresh confirmation. The production scoring fallback has no completed arbiter file. Registered contrasts, missingness, Holm inference and sensitivity analyses are in analysis/r2c/report.md and primary.json.

## fig_defaults

Bare P0 semantic-value shares among valid outputs with known critical extraction, one request occurrence per family×model. Unclear and other values remain in this all-known denominator. Polarity affirmative share is 99.06% (317/320). This descriptive all-output denominator differs from registered P3’s affirmative/negated directional share 99.37% (317/319); the observed unclear output is outside the latter denominator. Balanced source pairs do not make ambiguous inputs informative about private intent.

## fig_channel_ladder

P0 critical match across bare, +noncritical word, +critical chip, +all chips, and full source. Bare/noncrit indicate target-reference agreement, not accuracy. The supplied-cue channels evaluate critical preservation. Orange squares additionally require the joint partial contract for supplied general dimensions. The 78 speech-act families represent 55 recorded construction/seed clusters, not 78 independent constructions. Primary P1 uses complete pairs and therefore can differ slightly from subtraction of independently observed channel means.

## fig_cost_asymmetry

Nominal extra selections for the family’s modal bare reading versus its other target reading. Family default is the most frequent A/B value in P0 across four models, with P2/S3 as a tie-break; absent/tied defaults are excluded. P0 cost is zero for a matching top suggestion, otherwise the critical-chip count. P2 cost is zero for top-1, one for another matching suggestion, otherwise the critical-chip count. The fixed-roster modal default differs from the output-specific top-1 default used in nominal_action_cost.csv. Neither measure estimates typing time or guarantees successful repair.

## fig_politeness_ratchet

P0 full-input plain→polite additions versus polite→plain removals, by model and pooled. Pooled 320 outputs per source register: 26 additions (8.12%) and six removals (1.88%). Registered paired addition−removal contrast is +6.25 pp [2.50,10.00], Holm-adjusted p=0.000900. Pooled asymmetry does not describe every model: Qwen and Llama have more removals than additions. No P1 prompt or certainty-stratum data exist here; those discovery-only sensitivity rows/controls are omitted.

## fig_sets

Bare P2 versus S3 coverage@3: both source-pair values among the first three suggestions. P2 is one greedy request for three different meanings; S3 is three T=.7 draws. Unknown labels produce unknown sets unless both readings are already observed. Incomplete sets remain observed and flagged in the set audit. P2 increases polarity coverage by +7.19 pp [4.11,10.49], so the discovery “not polarity” clause does not repeat, despite low absolute polarity coverage. The figure reports marginal arm rates; paired differences use jointly observed sets and have their own denominator.

## fig_pipeline

Method schematic using the actual stored r2pol-001 P0 bare output from the first model in the fixed plotting order (GPT-6.1-terra): “I feel well.” The source, five rendered channels, output and extracted labels are read from stored specs/table. This is a lexicographically selected method illustration, not an independently selected failure-rate example; outcome-conditioned examples and their complete selection rules/rates are in analysis/r2c/examples.md.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python paper/figs/make_figs.py --table runs/r2c1/scored.parquet --items 'data/items/r2_c[12].jsonl' --out paper/figs/r2c --n-boot 10000 --seed 20261031 --cluster-by-items --strict-critical --exclude-primary
.venv/bin/python analysis/r2c/write_figure_notes.py
```
