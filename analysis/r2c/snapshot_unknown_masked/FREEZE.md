# W-C freeze and analysis plan

Recorded UTC: 2026-11-01T17:44:32.452382+00:00

This is a retrospective provenance audit plus a prospective analysis implementation freeze, not a claim that this file existed before generation. No scored outcomes have been loaded by this analyst before writing it.

| path | sha256 | mtime_utc |
| --- | --- | --- |
| data/items/r2_c1.jsonl | 3ca2e1a6109abd423981ca15263d47165d4648fe12b42adf1a3402cc911f6061 | 2026-11-01T02:51:25.239824+00:00 |
| data/items/r2_c2.jsonl | 457eea54566154bc33f1fbab88245d704cbb4693d6ba887691a1a4dd32578821 | 2026-11-01T02:50:21.220901+00:00 |
| orchestration/PREREG_R2.md | fcc6a9c368650a6eb20e23355f1e462de61e723eca9f14001d221bf34a821717 | 2026-11-01T02:34:13.791404+00:00 |
| runs/requests/r2c.jsonl | bf14ad6997903f47342634d5b57eacc654a0cac885ff9005b36ce38170595994 | 2026-11-01T02:55:10.332038+00:00 |
| runs/r2c1/config.json | 2643416de879b2fe81bfe91145152703ea8f55824b03cfd465a15e7938e88955 | 2026-11-01T06:45:45.139389+00:00 |

## Original generation timestamps (not final collection time)

| model | first_created_utc | last_created_utc | requests |
| --- | --- | --- | --- |
| gemma3-4b | 2026-11-01T01:14:35+00:00 | 2026-11-01T03:50:00+00:00 | 9575 |
| gpt-6.1-terra | 2026-11-01T01:09:31+00:00 | 2026-11-01T06:45:44+00:00 | 9575 |
| llama3.1-8b | 2026-11-01T01:09:18+00:00 | 2026-11-01T03:36:35+00:00 | 9575 |
| qwen2.5-7b | 2026-11-01T01:09:18+00:00 | 2026-11-01T03:27:26+00:00 | 9575 |

38,300 generation records; 48,000 request targets were reconstructed against the current source specs with exact input equality. 48 cached generation records predate the final item mtimes; see pre_freeze_cache.json. Thus a blanket freeze-before-generation claim is NOT established. Most requests follow the frozen request file, but earlier cache reuse must remain disclosed. Registered primary estimates keep the fixed sample; sensitivity excludes any family touched by earlier cached requests. Request SHA256 matches config. Item hash prefixes match the independently recorded D-022 freeze. The config created_utc (2026-11-01T06:45:45+00:00) is a final cached collection snapshot and does not date the first generation.

This establishes recorded ordering for fresh requests but NOT for the reused cache entries (timestamps are not an external trusted timestamp). Primary results are registered contrasts with a cache-provenance qualification, not an unqualified fully fresh confirmation. PREREG title uses November 1 although its actual mtime is October 31 local; ordering uses UTC metadata, not the title. Config lacks item/codebook hashes required by PREREG; source reconstruction and D-022 hashes supply supporting evidence, with that manifest deficiency disclosed.

## Analysis plan unchanged from PREREG

The three W-C PRIMARY estimands remain exactly PREREG_R2: P1 speech-act chip1 minus noncrit critical match, excluding primary_exclude (r2act-078/079, D-018) and refusal/acceptance; P2 full-input politeness plain→polite addition rate minus polite→plain removal rate; P3 bare polarity affirmative share minus 0.5. All primary outputs use P0 (contrast IDs P1/P2 are not prompt IDs). Fixed 240 approved families, four fixed models, no resizing or extension. Other estimates are descriptive, including per-model and construction breakdowns and discovery-claim replication. Models are fixed; no inference to a population of models.

Resample the recorded cluster_id, retaining all variants/models/channels/suggestions of a seed/construction jointly: 10,000 multinomial cluster resamples, seed 20261031; row-weighted estimates; paired within family/variant/model for P1 and within family/model for P2, with subtraction after joint resampling. P3 deduplicates shared A/B requests and conditions on affirmative/negated readings, with all-output affirmative share sensitivity. Report missingness, families, observed clusters, and Kish effective clusters from observed cluster denominators. Percentile 95% CIs. Holm step-down alpha=.05 across exactly the three pooled primary tests, with expected positive direction. No Holm for descriptive strata.

PREREG specifies bootstrap and expected direction, but not a test-statistic/p-value algorithm, denominator details, or CI type. Operationalization declared here before reading scored outcomes: one-sided null-centered cluster bootstrap p=(1+#(bootstrap_estimate−estimate >= estimate))/(10001), capped at 1; Holm monotone adjusted p; also report two-sided centered-bootstrap p sensitivity. At boundary zero variance, report empirical degeneracy; no zero population-risk inference. Unknown required labels are excluded, never replaced by a favorable label; invalid completion is critical-match failure. P2 directional rates use known critical plain/polite extraction (invalid/unclear are not directional switches), complete paired targets for primary difference, arm-specific rates and missingness also reported. No claim that these implementation choices were specified verbatim in the preregistration.

H1 secondary replication eligibility: politeness pairs only; both source specs must explicitly encode request/command ([ASK]) and an expressible main actor (same explicit [YOU]/[I]/[WE]/[THEY] in both all_chips). Exactly one variant plain and one polite. Freeze family list now, source specs only; do not filter on outcomes. Compare plain−polite request retention on P0 chipall and full, Llama focal, others descriptive. Promotion criterion: difference <= −.20 and upper 95% CI <0; chip-only result is encoding-specific.

H2 secondary construction coding: source-blind to generated outcomes, use bare predicate plus source syntax to label question targets action/event, state/evaluation, or unresolved; preserve all exclusions. No independent second coder is available in this analysis, so the independently-audited construction headline remains unearned; results are descriptive regardless of thresholds. No new generation, judging, or GPU servers.

Secondary: full five-channel P0 ladder by dimension, bare/noncrit P2 versus S3 coverage@3, stance additions, nominal action costs default/nondefault using analyze.py semantics, r2pol-077 exclusion sensitivity and C1–C11/C17 replication scope. C5 requires W-B/S1, C9/C10 encoding manipulations absent here; mark untestable rather than manufacture replication. Deterministic examples use seeded SHA256-ranked eligible stored occurrences with explicit outcome-conditioned rules and stratum rates, not manual selection. Publication figures use make_figs.py with r2c1 and the same cluster/seed/bootstrap/exclusion rules. Flat headline.json exports proportions/differences in unit scale with CI/n/n_clusters; primary.json preserves full inference details.
