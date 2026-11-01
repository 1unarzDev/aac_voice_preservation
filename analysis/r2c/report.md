# W-C: registered contrasts and discovery replication

**3/3 registered directions pass Holm α=.05 in the protocol-aligned analysis. Confirmation is qualified:** 48 cached requests predate the final item freeze (20 also predate the PREREG mtime), and 259 J1/J2 critical-disagreement rows are resolved by the post-outcome cross-family arbiter record (runs/r2c1/arbiter.jsonl; [arbitration.md](arbitration.md)); the earlier unknown-masked snapshot is retained in [snapshot_unknown_masked](snapshot_unknown_masked/README.md) and as a sensitivity below. An unqualified wholly fresh sample is not claimed. See [FREEZE.md](FREEZE.md), [primary.json](primary.json), and sensitivities below.

## Population, chronology and scoring

All generation records contributing to a registered primary contrast postdate the PREREG mtime. Twelve distinct primary requests predate the final item mtimes: eight P1 noncrit requests and four P3 bare requests; P2 has none. Thus primary prereg-before-generation ordering is supported locally, while final-item-freeze-before-every-primary-generation ordering is not. [Primary timestamp audit](primary_pre_freeze_cache.csv).

Fixed 240 approved families: 80 polarity, 80 speech act, 80 politeness; 40 seeded/30 drafted/10 adversarial per dimension. No resizing or new calls. D-018 excludes r2act-078/079 from primary speech act (78 families). They remain in the inclusive scored input and [diagnostic](excluded_d018_diagnostic.csv). Other descriptive tables exclude these families consistently. Inclusive recorded clusters: 211; analyzed clusters: 210. Cross-file shared seeds and the r2pol-044/052 construction cluster are kept intact. Four models are a fixed roster.

Input contains 67,166 target rows; analyzed 66,610; P0 has all 9,600 planned inclusive target rows. All five channels are present for P0/P2/S3. PREREG called for P2/S3 bare; D-022 describes bare/noncrit, but the stored manifest actually generated all five channels for all three prompt regimes. Extra generated channels do not enlarge the primary test family. 38,300 unique generation records map to 48,000 request targets and 67,166 exploded/scored suggestions. The cache audit found 48 early requests across 6 families: r2act-007, r2act-029, r2act-030, r2act-032, r2plt-002, r2pol-004. All 48,000 request input targets match current source specs exactly. The fixed primary sample is retained; family-exclusion sensitivity is supplementary. Hash/timestamp evidence cannot prove these cache outputs followed the final freeze.

Supplied critical_source counts: {'agree': 66907, 'arbiter': 259}. runs/r2c1/arbiter.jsonl resolves 259 rows (no J1/J2 fallback remains); see arbitration.md. General dimensions retain the supplied production labels, including its existing general-label resolution. Scored invalid completions: 0; critical unknown after masking: 0. General missingness: {'polarity': 19, 'speech_act': 5, 'agent': 27, 'certainty': 7, 'politeness': 0}. Critical unknowns are excluded; invalid completions count as match failures. The available human-gold report contains human validation on the earlier validation inventory; this is not a W-C human spot-check or proof of every new boundary label.

## PRIMARY registered contrasts

Estimate and pointwise 95% percentile CI; differences in percentage points. n is observed/total analysis units (paired targets for P1; paired family×model directional switches for P2; unique family×model bare outputs with affirmative/negated readings for P3). Each P2 pair comprises two outputs. Cluster counts are observed/available, with Kish effective clusters from cluster row denominators. Holm tests the three pooled contrasts only; per-model/construction entries are descriptive. P1/P2 contrast names are not prompt IDs; all three use prompt P0.

| contrast | estimand | estimate [95% CI], n, clusters | p one-sided | Holm p | reject .05 |
| --- | --- | --- | --- | --- | --- |
| P1 | speech-act chip1−noncrit match | 31.41 pp [25.00, 37.94]; n=624/624, clusters=55/55, eff=33.1 | 0.0001 | 0.0003 | True |
| P2 | full politeness addition−removal | 6.25 pp [2.50, 10.00]; n=320/320, clusters=80/80, eff=80.0 | 0.0009 | 0.0009 | True |
| P3 | bare affirmative share−0.5 | 49.37 pp [48.42, 50.00]; n=319/320, clusters=79/79, eff=78.0 | 0.0001 | 0.0003 | True |

P3 affirmative share: 99.37% [98.42, 100.00]; n=319/320, clusters=79/79, eff=78.0. The denominator is 317 affirmative + 2 negated; one observed unclear reading is outside the directional denominator (not an unknown judge label). The all-known-output sensitivity is 317/320 = 99.06%. Full politeness addition: 8.12% [5.31, 11.25]; n=320/320, clusters=80/80, eff=80.0; removal: 1.88% [0.62, 3.44]; n=320/320, clusters=80/80, eff=80.0.

Bootstrap: 10,000 whole recorded seed/construction-cluster multinomial resamples, seed 20261031, row-weighted means, paired comparisons retained jointly. Helpers from src/analyze.py are reused with cluster_id as the resampling group. No independent model bootstrap or independence assumption across outputs within a cluster. Unadjusted 95% CIs are not simultaneous Holm intervals. PREREG did not specify test tails or a p-value algorithm: the analysis freeze declares null-centered one-sided bootstrap tests in the expected positive direction; two-sided centered-bootstrap Holm sensitivity is included in primary.json. The Monte Carlo p floor is 1/10001. Boundary bootstrap intervals may collapse and do not establish zero population risk.

### Descriptive per-model and construction estimates

| contrast | stratum | estimate [95% CI], n, clusters |
| --- | --- | --- |
| P1 | gemma3-4b | 35.26 pp [25.56, 45.59]; n=156/156, clusters=55/55, eff=33.1 |
| P1 | gpt-6.1-terra | 41.67 pp [35.00, 48.03]; n=156/156, clusters=55/55, eff=33.1 |
| P1 | llama3.1-8b | 20.51 pp [12.19, 28.87]; n=156/156, clusters=55/55, eff=33.1 |
| P1 | qwen2.5-7b | 28.21 pp [18.05, 38.24]; n=156/156, clusters=55/55, eff=33.1 |
| P2 | gemma3-4b | 23.75 pp [13.75, 33.75]; n=80/80, clusters=80/80, eff=80.0 |
| P2 | gpt-6.1-terra | 6.25 pp [1.25, 12.50]; n=80/80, clusters=80/80, eff=80.0 |
| P2 | llama3.1-8b | -1.25 pp [-6.25, 2.50]; n=80/80, clusters=80/80, eff=80.0 |
| P2 | qwen2.5-7b | -3.75 pp [-8.75, 0.00]; n=80/80, clusters=80/80, eff=80.0 |
| P3 | gemma3-4b | 50.00 pp [50.00, 50.00]; n=80/80, clusters=79/79, eff=78.0 |
| P3 | gpt-6.1-terra | 47.50 pp [43.67, 50.00]; n=80/80, clusters=79/79, eff=78.0 |
| P3 | llama3.1-8b | 50.00 pp [50.00, 50.00]; n=80/80, clusters=79/79, eff=78.0 |
| P3 | qwen2.5-7b | 50.00 pp [50.00, 50.00]; n=79/80, clusters=78/79, eff=77.0 |

| contrast | stratum | estimate [95% CI], n, clusters |
| --- | --- | --- |
| P1 | adversarial | 21.88 pp [8.75, 45.83]; n=64/64, clusters=6/6, eff=4.6 |
| P1 | drafted | 35.83 pp [26.19, 47.83]; n=240/240, clusters=9/9, eff=6.9 |
| P1 | seeded | 30.00 pp [20.94, 38.75]; n=320/320, clusters=40/40, eff=40.0 |
| P2 | adversarial | 0.00 pp [-10.00, 10.00]; n=40/40, clusters=10/10, eff=10.0 |
| P2 | drafted | 11.67 pp [5.00, 19.17]; n=120/120, clusters=30/30, eff=30.0 |
| P2 | seeded | 3.75 pp [0.00, 7.50]; n=160/160, clusters=40/40, eff=40.0 |
| P3 | adversarial | 50.00 pp [50.00, 50.00]; n=40/40, clusters=10/10, eff=10.0 |
| P3 | drafted | 49.16 pp [47.39, 50.00]; n=119/120, clusters=29/29, eff=28.0 |
| P3 | seeded | 49.38 pp [48.12, 50.00]; n=160/160, clusters=40/40, eff=40.0 |

### Primary sensitivity (descriptive; no sample substitution)

| sensitivity | contrast | estimate [95% CI], n, clusters |
| --- | --- | --- |
| exclude_any_pre_freeze_cache_family | P1 | 29.56 pp [23.06, 36.27]; n=592/592, clusters=51/51, eff=30.4 |
| exclude_any_pre_freeze_cache_family | P2 | 6.33 pp [2.85, 10.13]; n=316/316, clusters=79/79, eff=79.0 |
| exclude_any_pre_freeze_cache_family | P3 | 49.37 pp [48.40, 50.00]; n=315/316, clusters=78/78, eff=77.0 |
| exclude_negative_question_r2pol077 | P1 | 31.41 pp [25.00, 37.94]; n=624/624, clusters=55/55, eff=33.1 |
| exclude_negative_question_r2pol077 | P2 | 6.25 pp [2.50, 10.00]; n=320/320, clusters=80/80, eff=80.0 |
| exclude_negative_question_r2pol077 | P3 | 49.37 pp [48.40, 50.00]; n=315/316, clusters=78/78, eff=77.0 |
| supplied_J1_fallback | P1 | 31.41 pp [24.85, 38.04]; n=624/624, clusters=55/55, eff=33.1 |
| supplied_J1_fallback | P2 | 6.25 pp [2.50, 10.00]; n=320/320, clusters=80/80, eff=80.0 |
| supplied_J1_fallback | P3 | 49.37 pp [48.42, 50.00]; n=319/320, clusters=79/79, eff=78.0 |
| unknown_masked_pre_arbitration | P1 | 31.65 pp [25.22, 38.19]; n=613/624, clusters=55/55, eff=32.9 |
| unknown_masked_pre_arbitration | P2 | 6.25 pp [2.50, 10.00]; n=320/320, clusters=80/80, eff=80.0 |
| unknown_masked_pre_arbitration | P3 | 49.37 pp [48.42, 50.00]; n=319/320, clusters=79/79, eff=78.0 |
| P3_all_known_outputs | P3 | 49.06 pp [47.81, 50.00]; n=320/320, clusters=79/79, eff=78.0 |

## Secondary/descriptive endpoints

The descriptive results refine several discovery claims: C2 does not establish equivalence of a noncritical word and bare input; C3 does not hold at full-input fidelity for speech act; C4’s “not polarity” clause does not repeat (P2−S3 polarity coverage is +7.19 pp); C7 repeats as a pooled direction, with Qwen and Llama having more removals than additions. C11 speech-act chips are weakest among the three tested dimensions, and statements are weaker than question/request targets here. C5 and C9 cannot be tested by this design; C10’s encoding-comparison clause cannot be tested.

### Full channel ladder

P0 critical match is reference agreement for bare/noncrit, supplied-critical preservation for chip1/chipall/full. Ambiguous agreement is not accuracy. Joint supplied predicates are a partial contract; fluency and complete semantic equivalence are not evaluated.

| dimension | channel | estimate [95% CI], n, clusters |
| --- | --- | --- |
| polarity | bare | 49.84% [49.53, 50.00]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | chip1 | 99.22% [98.28, 99.85]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | chipall | 96.25% [94.60, 97.78]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | full | 99.84% [99.53, 100.00]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | noncrit | 49.84% [49.53, 50.00]; n=640/640, clusters=79/79, eff=78.0 |
| politeness | bare | 50.00% [50.00, 50.00]; n=640/640, clusters=80/80, eff=80.0 |
| politeness | chip1 | 89.53% [87.66, 91.41]; n=640/640, clusters=80/80, eff=80.0 |
| politeness | chipall | 87.19% [86.25, 88.12]; n=640/640, clusters=80/80, eff=80.0 |
| politeness | full | 95.00% [93.28, 96.56]; n=640/640, clusters=80/80, eff=80.0 |
| politeness | noncrit | 50.00% [50.00, 50.00]; n=640/640, clusters=80/80, eff=80.0 |
| speech_act | bare | 39.26% [34.38, 43.52]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | chip1 | 73.24% [68.97, 77.56]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | chipall | 74.84% [69.88, 80.11]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | full | 99.20% [98.44, 99.83]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | noncrit | 41.83% [36.99, 46.19]; n=624/624, clusters=55/55, eff=33.1 |

### Coverage@3: P2 versus S3

Both pair values among the first three suggestions; shared A/B targets deduplicated. P2 uses one greedy three-suggestion request; S3 uses three T=.7 draws. Unknown labels yield unknown coverage unless both values are already observed. Noncrit sometimes renders words in different source order across variants: those distinct inputs remain distinct set occurrences; shared inputs are deduplicated. P2−S3 comparisons pair by target and actual input text before deduplicating shared inputs. Incomplete sets are retained and flagged; no fabricated third output.

| dimension | channel | prompt_id | estimate [95% CI], n, clusters |
| --- | --- | --- | --- |
| polarity | bare | P2 | 7.81% [4.43, 11.39]; n=320/320, clusters=79/79, eff=78.0 |
| polarity | bare | S3 | 0.62% [0.00, 1.54]; n=320/320, clusters=79/79, eff=78.0 |
| polarity | noncrit | P2 | 6.71% [3.61, 10.17]; n=328/328, clusters=79/79, eff=76.4 |
| polarity | noncrit | S3 | 0.91% [0.00, 2.11]; n=328/328, clusters=79/79, eff=76.4 |
| politeness | bare | P2 | 69.38% [64.06, 74.69]; n=320/320, clusters=80/80, eff=80.0 |
| politeness | bare | S3 | 12.81% [9.38, 16.56]; n=320/320, clusters=80/80, eff=80.0 |
| politeness | noncrit | P2 | 63.12% [57.19, 69.06]; n=320/320, clusters=80/80, eff=80.0 |
| politeness | noncrit | S3 | 12.81% [9.38, 16.25]; n=320/320, clusters=80/80, eff=80.0 |
| speech_act | bare | P2 | 53.21% [44.48, 61.71]; n=312/312, clusters=55/55, eff=33.1 |
| speech_act | bare | S3 | 3.85% [1.97, 5.77]; n=312/312, clusters=55/55, eff=33.1 |
| speech_act | noncrit | P2 | 59.07% [50.32, 66.98]; n=364/364, clusters=55/55, eff=33.3 |
| speech_act | noncrit | S3 | 4.12% [2.16, 6.36]; n=364/364, clusters=55/55, eff=33.3 |

| dimension | channel | estimate [95% CI], n, clusters |
| --- | --- | --- |
| polarity | bare | 7.19 pp [4.11, 10.49]; n=320/320, clusters=79/79, eff=78.0 |
| polarity | noncrit | 5.79 pp [2.71, 9.26]; n=328/328, clusters=79/79, eff=76.4 |
| politeness | bare | 56.56 pp [51.25, 61.88]; n=320/320, clusters=80/80, eff=80.0 |
| politeness | noncrit | 50.31 pp [44.06, 56.88]; n=320/320, clusters=80/80, eff=80.0 |
| speech_act | bare | 49.36 pp [41.39, 57.28]; n=312/312, clusters=55/55, eff=33.1 |
| speech_act | noncrit | 54.95 pp [46.55, 62.79]; n=364/364, clusters=55/55, eff=33.3 |

### Stance additions

Target-reference-relative additions under ambiguous input, not errors against unknowable private intent. General speech act/agent mismatch and politeness addition use source all_chips/general_spec. Certainty n/a is excluded; certainty_raised follows analyze.py, and added_content remains judge-defined. All dimensions/prompts/channels are in [stance_additions.csv](stance_additions.csv) and per-model rates in [stance_by_model.csv](stance_by_model.csv).

| dimension | metric | rate [95% CI], n, clusters |
| --- | --- | --- |
| polarity | addition_speech_act | 17.19% [12.03, 22.84]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | addition_agent | 30.26% [22.70, 38.18]; n=608/640, clusters=75/79, eff=74.1 |
| polarity | politeness_added | 5.62% [2.85, 8.86]; n=640/640, clusters=79/79, eff=78.0 |
| polarity | certainty_raised | 0.40% [0.00, 1.26]; n=502/640, clusters=70/79, eff=67.0 |
| politeness | addition_speech_act | 40.00% [33.12, 46.88]; n=640/640, clusters=80/80, eff=80.0 |
| politeness | addition_agent | 37.18% [30.13, 44.08]; n=624/640, clusters=78/80, eff=78.0 |
| politeness | politeness_added | 32.81% [27.19, 38.75]; n=320/640, clusters=80/80, eff=80.0 |
| politeness | certainty_raised | 0.00% [0.00, 0.00]; n=12/640, clusters=2/80, eff=1.8 |
| speech_act | addition_speech_act | 60.74% [56.48, 65.62]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | addition_agent | 53.67% [46.04, 61.49]; n=600/624, clusters=52/55, eff=31.1 |
| speech_act | politeness_added | 13.14% [8.75, 17.86]; n=624/624, clusters=55/55, eff=33.1 |
| speech_act | certainty_raised | 0.00% [0.00, 0.00]; n=161/624, clusters=36/55, eff=22.1 |

### Nominal action cost, default versus non-default

Default is each output/set top-1 A/B reading. Unclear/other top-1 is unidentified and separately retained. A target costs 0 extra selections if top-1 matches, 1 if another of three matches, otherwise the number of target critical chips. Fallback is a nominal input cost with no guarantee of preservation; it excludes typing time, motor effort and retry cost. Not a user study. Both channel definitions, all prompts and unidentified rates are in [nominal_action_cost.csv](nominal_action_cost.csv). Figure cost defines the family modal default instead and labels that descriptive rule explicitly.

| dimension | prompt | reading | mean actions [95% CI] | n | clusters |
| --- | --- | --- | --- | --- | --- |
| polarity | P0 | default | 0.000 [0.000, 0.000] | 319 | 79 |
| polarity | P0 | non-default | 1.000 [1.000, 1.000] | 319 | 79 |
| polarity | P0 | unidentified | 1.000 [1.000, 1.000] | 2 | 1 |
| polarity | P2 | default | 0.000 [0.000, 0.000] | 319 | 79 |
| polarity | P2 | non-default | 1.000 [1.000, 1.000] | 319 | 79 |
| polarity | P2 | unidentified | 1.000 [1.000, 1.000] | 2 | 1 |
| polarity | S3 | default | 0.000 [0.000, 0.000] | 320 | 79 |
| polarity | S3 | non-default | 1.000 [1.000, 1.000] | 320 | 79 |
| politeness | P0 | default | 0.000 [0.000, 0.000] | 320 | 80 |
| politeness | P0 | non-default | 1.000 [1.000, 1.000] | 320 | 80 |
| politeness | P2 | default | 0.000 [0.000, 0.000] | 320 | 80 |
| politeness | P2 | non-default | 1.000 [1.000, 1.000] | 320 | 80 |
| politeness | S3 | default | 0.000 [0.000, 0.000] | 320 | 80 |
| politeness | S3 | non-default | 1.000 [1.000, 1.000] | 320 | 80 |
| speech_act | P0 | default | 0.000 [0.000, 0.000] | 245 | 52 |
| speech_act | P0 | non-default | 1.000 [1.000, 1.000] | 245 | 52 |
| speech_act | P0 | unidentified | 1.000 [1.000, 1.000] | 134 | 24 |
| speech_act | P2 | default | 0.000 [0.000, 0.000] | 237 | 50 |
| speech_act | P2 | non-default | 1.000 [1.000, 1.000] | 237 | 50 |
| speech_act | P2 | unidentified | 1.000 [1.000, 1.000] | 150 | 21 |
| speech_act | S3 | default | 0.000 [0.000, 0.000] | 243 | 51 |
| speech_act | S3 | non-default | 1.000 [1.000, 1.000] | 243 | 51 |
| speech_act | S3 | unidentified | 1.000 [1.000, 1.000] | 138 | 23 |

## Discovery-claim replication (secondary unless explicitly PRIMARY above)

Original C1–C11 and C17 are discovery claims. Fresh matching endpoints test transfer of the pattern, not confirm every clause of the original claim. Only registered P1/P2/P3 have confirmatory multiplicity control. An absence of difference is not equivalence.

| claim | status | W-C evidence / scope |
| --- | --- | --- |
| C1 | PRIMARY P3 counterpart | 99.37% [98.42, 100.00]; n=319/320, clusters=79/79, eff=78.0 |
| C2 | Descriptive length-control check | polarity: 0.00 pp [0.00, 0.00]; n=640/640, clusters=79/79, eff=78.0; speech_act: 2.56 pp [0.60, 4.58]; n=624/624, clusters=55/55, eff=33.1; politeness: 0.00 pp [0.00, 0.00]; n=640/640, clusters=80/80, eff=80.0; no equivalence margin was registered. |
| C3 | Descriptive chip1 versus full | polarity: -0.62 pp [-1.58, 0.16]; n=640/640, clusters=79/79, eff=78.0; speech_act: -25.96 pp [-30.36, -21.53]; n=624/624, clusters=55/55, eff=33.1; politeness: -5.47 pp [-7.97, -2.81]; n=640/640, clusters=80/80, eff=80.0; no noninferiority margin, so “full-level” is not formally established. |
| C4 | Descriptive P2−S3 coverage | polarity: 7.19 pp [4.11, 10.49]; n=320/320, clusters=79/79, eff=78.0; politeness: 56.56 pp [51.25, 61.88]; n=320/320, clusters=80/80, eff=80.0; speech_act: 49.36 pp [41.39, 57.28]; n=312/312, clusters=55/55, eff=33.1 |
| C5 | Not testable in W-C | AACText natural-corpus POS-cap4 cue prevalence requires S1/W-B; authored balanced pairs cannot estimate corpus prevalence. |
| C6 | PRIMARY P2 related endpoint | Full politeness addition 8.12% [5.31, 11.25]; n=320/320, clusters=80/80, eff=80.0; literal please-only counts are reported below. |
| C7 | PRIMARY P2 counterpart | Addition−removal 6.25 pp [2.50, 10.00]; n=320/320, clusters=80/80, eff=80.0; model directions may differ from discovery. |
| C8 | Partial replication | Polarity 99.37% [98.42, 100.00]; n=319/320, clusters=79/79, eff=78.0; certainty/agent-critical strata absent, so their discovery default rates are not retested. |
| C9 | Not testable in W-C | No controlled factorial YES/NOT × I/YOU composition/repeats; use W-D. |
| C10 | Partial descriptive diagnostic | PLAIN/ASK behavior in W-C is observable, but Exp B alias/NL factor and constant-content perturbation design are absent; no encoding superiority replication. |
| C11 | Descriptive + registered P1 | Speech-act chip1 value-specific matches and transitions below; “weakest” is scoped to three W-C dimensions, not all discovery dimensions. |
| C17 | Frozen-eligibility secondary replication | H1: 74 eligible / 6 ineligible families; model/channel retention contrasts and thresholds below. |

| dimension | source target | chip1 match [95% CI], n, clusters |
| --- | --- | --- |
| polarity | affirmative | 100.00% [100.00, 100.00]; n=320/320, clusters=79/79, eff=78.0 |
| polarity | negated | 98.44% [96.56, 99.69]; n=320/320, clusters=79/79, eff=78.0 |
| politeness | plain | 79.06% [75.31, 82.81]; n=320/320, clusters=80/80, eff=80.0 |
| politeness | polite | 100.00% [100.00, 100.00]; n=320/320, clusters=80/80, eff=80.0 |
| speech_act | question | 72.12% [62.50, 81.14]; n=208/208, clusters=37/37, eff=24.6 |
| speech_act | request/command | 89.00% [84.87, 92.55]; n=200/200, clusters=36/36, eff=21.2 |
| speech_act | statement | 59.72% [50.49, 69.55]; n=216/216, clusters=37/37, eff=20.8 |

C6 literal please-only extraction: 8.12% [5.31, 11.25]; n=320/320, clusters=80/80, eff=80.0. This category is narrower than any-polite addition.

### H1 / C17: paired request retention

Eligibility was written from source specs before loading scored outcomes: [h1_eligibility.csv](h1_eligibility.csv). Six excluded families: r2plt-011, r2plt-056, r2plt-074, r2plt-075, r2plt-076, r2plt-077. Both source variants must be explicit requests with the same expressible actor. Llama is the focal secondary replication; other models descriptive. Success threshold is plain−polite ≤−20 pp and upper 95% bound <0. A chip-only effect remains encoding-specific.

| model | channel | plain−polite [95% CI], n, clusters | threshold met |
| --- | --- | --- | --- |
| gemma3-4b | chipall | 0.00 pp [0.00, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |
| gpt-6.1-terra | chipall | 0.00 pp [0.00, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |
| llama3.1-8b | chipall | -87.84 pp [-94.59, -79.73]; n=74/74, clusters=74/74, eff=74.0 | True |
| qwen2.5-7b | chipall | 0.00 pp [0.00, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |
| gemma3-4b | full | -1.35 pp [-4.05, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |
| gpt-6.1-terra | full | 0.00 pp [0.00, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |
| llama3.1-8b | full | -13.51 pp [-22.97, -5.41]; n=74/74, clusters=74/74, eff=74.0 | False |
| qwen2.5-7b | full | 0.00 pp [0.00, 0.00]; n=74/74, clusters=74/74, eff=74.0 | False |

C17 replicates the large Llama request-retention gap under chipall, with the cache-provenance qualification. It does not replicate perfect plain-register match: Llama matches plain register on 69/74 chipall targets; request retention is 9/74 plain versus 74/74 polite. Full request retention is 62/74 versus 72/74. The full-input gap is below the registered magnitude threshold, so the promoted replication is encoding-specific.

Llama chipall: meets the frozen replication threshold.

Llama full: does not meet the frozen replication threshold.

Plain/polite arm retention, register match and joint preservation are in [h1_arms.csv](h1_arms.csv); raw per-judge retention differences are in [h1_judge_sensitivity.csv](h1_judge_sensitivity.csv). General-label judge sensitivity does not replace the production endpoint.

### H2: question construction coding (descriptive)

53 question sources were coded before scored inspection: action/event, state/evaluation, unresolved. D-018 leaves 52 analyzed question sources. [h2_construction.csv](h2_construction.csv) retains all 53 and their exclusions. A single analyst coded predicates/source syntax; independent coding audit is not available, so the construction headline is not promoted.

| channel | construction | question loss [95% CI], n, clusters |
| --- | --- | --- |
| chip1 | action/event | 38.24% [28.91, 46.95]; n=136/136, clusters=26/26, eff=19.3 |
| chip1 | state/evaluation | 9.38% [1.92, 21.15]; n=64/64, clusters=13/13, eff=9.1 |
| chip1 | unresolved | 0.00% [0.00, 0.00]; n=8/8, clusters=1/1, eff=1.0 |
| chipall | action/event | 38.97% [26.47, 50.66]; n=136/136, clusters=26/26, eff=19.3 |
| chipall | state/evaluation | 9.38% [4.55, 15.38]; n=64/64, clusters=13/13, eff=9.1 |
| chipall | unresolved | 12.50% [12.50, 12.50]; n=8/8, clusters=1/1, eff=1.0 |
| full | action/event | 0.00% [0.00, 0.00]; n=136/136, clusters=26/26, eff=19.3 |
| full | state/evaluation | 0.00% [0.00, 0.00]; n=64/64, clusters=13/13, eff=9.1 |
| full | unresolved | 0.00% [0.00, 0.00]; n=8/8, clusters=1/1, eff=1.0 |

Action-minus-state question-loss differences (joint seed/construction-cluster resampling, not independent resampling of overlapping construction strata):

| channel | gap pp [95% CI] | n | action/state clusters | numeric threshold met | independent audit |
| --- | --- | --- | --- | --- | --- |
| chip1 | 28.86 [14.26, 41.41] | 200 | 26/13 | True | False |
| chipall | 29.60 [15.28, 42.65] | 200 | 26/13 | True | False |
| full | 0.00 [0.00, 0.00] | 200 | 26/13 | False | False |

## Limitations and reproducibility

Items/source hashes and actual timestamp ordering are in FREEZE.md; that file was written during analysis, not before generation. Caches include earlier generations; exclusion sensitivity cannot establish prospective registration retroactively. The request builder deduplicated identical visible inputs and reuses them as multiple target occurrences where applicable; recorded cluster_id preserves known seed/construction dependence, but distinct authored families can still share a model request. Sensitivity excluding early-cache families does not repair every possible content overlap. New item human spot-check completion is not established here. Automated labels and a partial contract cannot certify full meaning, fluency, communicative usefulness or population-wide model behavior.

J1 fallback was a deviation in orchestration/r2c_judge.sh. The fallback rows were later resolved by a single post-outcome Claude arbiter (blind to reference, model, arm and J1/J2; see arbitration.md); this is not a prospective resolution, and the unknown-masked and supplied-J1 analyses are retained as sensitivities. Complete-case analysis can be biased by outcome-related missingness; supplied-J1 sensitivity is not adjudication. General labels follow the stored production resolution. Per-model and construction intervals are pointwise descriptive with small adversarial construction inventories.

Reproduce with `.venv/bin/python analysis/r2c/analyze_confirmatory.py` (set OPENBLAS_NUM_THREADS=1 for predictable local performance). Do not rerun freeze_analysis.py after outcomes: FREEZE.md is an audit record, not regenerated output. All analysis is CPU/local files; no API, judge or GPU server calls. [metadata.json](metadata.json) hashes the inputs, source eligibility and analysis helpers. [headline.json](headline.json) is flat numeric unit-scale estimates (multiply by 100 for percentages/pp); `<key>_ci_low`, `_ci_high`, `_n`, `_n_clusters` accompany each estimate. Top-level n counts analyzed target/suggestion rows, while endpoint-specific n is authoritative. [report.json](report.json) supplies the CALE readiness compatibility artifact.

Figure reproduction: `.venv/bin/python paper/figs/make_figs.py --table runs/r2c1/scored.parquet --items 'data/items/r2_c[12].jsonl' --out paper/figs/r2c --n-boot 10000 --seed 20261031 --cluster-by-items --strict-critical --exclude-primary`. Publication figures and their numeric manifest: [paper/figs/r2c](../../paper/figs/r2c/). Examples: [examples.md](examples.md), with [machine-readable provenance](examples.json). Complete table index:

- [primary_strata.csv](primary_strata.csv)
- [primary_arms.csv](primary_arms.csv)
- [politeness_direction_by_model.csv](politeness_direction_by_model.csv)
- [primary_sensitivity.csv](primary_sensitivity.csv)
- [channel_ladder.csv](channel_ladder.csv)
- [channel_ladder_by_model.csv](channel_ladder_by_model.csv)
- [channel_differences.csv](channel_differences.csv)
- [commitment.csv](commitment.csv)
- [coverage.csv](coverage.csv)
- [coverage_by_model.csv](coverage_by_model.csv)
- [coverage_difference.csv](coverage_difference.csv)
- [stance_additions.csv](stance_additions.csv)
- [stance_by_model.csv](stance_by_model.csv)
- [nominal_action_cost.csv](nominal_action_cost.csv)
- [h1_arms.csv](h1_arms.csv)
- [h1_difference.csv](h1_difference.csv)
- [h1_judge_sensitivity.csv](h1_judge_sensitivity.csv)
- [h2_question_loss.csv](h2_question_loss.csv)
- [h2_action_minus_state.csv](h2_action_minus_state.csv)
- [cue_value_match_by_model.csv](cue_value_match_by_model.csv)
- [cue_value_match.csv](cue_value_match.csv)
- [speech_act_transitions.csv](speech_act_transitions.csv)
- [excluded_d018_diagnostic.csv](excluded_d018_diagnostic.csv)
- [primary_pre_freeze_cache.csv](primary_pre_freeze_cache.csv)