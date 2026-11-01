# W-D: encoding-controlled composition

## Decision

- **polarity**: [TELL] damage minus repeat 0.00 [0.00, 0.00] pp; [STATEMENT] 2.15 [1.56, 2.77] pp. Literal point-rule verdict: `transparent_encoding_point_gate_passes`.
- **agent**: [TELL] damage minus repeat 3.91 [3.01, 4.84] pp; [STATEMENT] 0.16 [0.00, 0.47] pp. Literal point-rule verdict: `transparent_encoding_point_gate_passes`.
- **pooled**: [TELL] damage minus repeat 1.95 [1.50, 2.42] pp; [STATEMENT] 1.15 [0.84, 1.50] pp. Literal point-rule verdict: `transparent_encoding_point_gate_passes`.

**Interpretation:** the independent transparent-encoding effect is specific to Llama polarity: 55/640 pass→fail transitions across 30/80 scenarios, Δ=8.59 pp [6.25, 11.09], with 0/160 single-cue pass-status repeat disagreements. It survives J2 and agreement-only scoring unchanged. Under [TELL], Qwen agent damage is 84/640 across 44 scenarios (Δ=13.12 pp [10.31, 16.09]); Gemma has 10/640 across six scenarios (1.56 pp [0.47, 2.97]). Those effects are [TELL]-only and therefore encoding defects under the kill rule. Llama's [STATEMENT] agent damage is four transitions from one scenario, with a CI touching zero; Terra has no observed protected-dimension damage. These results support a bounded model/encoding-specific composition failure, not model-general interference or equivalence in the zero-event strata.

The binding kill rule is applied literally to the point difference: damage ≤ repeat disagreement licenses no interference headline; a positive difference confined to [TELL] licenses only an encoding-defect description. Confidence intervals are reported separately: a point-rule pass is not proof of a nonzero effect, and a wide interval containing zero does not establish equivalence. No multiplicity-adjusted significance claim is made. Per-model/dimension outcomes below must not be replaced by the pooled verdict.

## Inventory, freeze, and scoring

All 11,520 planned requests are present: 80 physical scenarios × 9 unique inputs × 2 encodings × 4 models × 2 greedy draws. The 320 A/B records expand to 40,960 scored occurrences; they are not independent scenarios. All outputs are valid, parsed, judged, stop-terminated, and P0x at temperature 0. The two namespace draws d1/d2 use the same greedy configuration; repeat disagreement measures observed run/batching/API instability, not a sampling-temperature effect. Models are a fixed roster; pooled results give them equal weight in this balanced design, without inference to a population of models.

Readiness: the complete run finished November 1, before the November 5 action-6 gate. Git commit `168702e` records the W-D protocol at 2026-11-01 02:34:13 UTC, before the earliest stored generation (2026-11-01T02:52:20+00:00). The item-freeze commit `3f24c80` is at 02:55:11 UTC and says W-D was running, after the first stored outputs (02:52:20 UTC). The assembled run config was created at 16:19:01 UTC and includes prompt/model/code hashes but no frozen item/codebook hashes. Thus protocol-before-generation is supported; a complete prospective item/codebook hash freeze is not independently established by these files. This report is an encoding/repeat sensitivity analysis under the registered design; it does not certify an entirely audited confirmatory freeze. Current input and analysis hashes are recorded in `primary.json`.

Stored critical-label sources over scored occurrences: `{'agree': 40369, 'J1': 591}`. This run has J1 fallback on critical disagreements, with no run-local arbiter file; it must not inherit the main1 pipeline's no-fallback description. General dimensions use J1/J2 agreement, otherwise layer0 tie-breaking as implemented in `judge.py`. Protected correctness uses the dimension's focal `critical` label. Joint polarity/agent fidelity joins the two focal records for each fully specified output; it does not substitute general agent labels, which can disagree with focal extraction. No authored refusal/acceptance families occur here. Generated refusals remain failures of supplied statement cues. CB-7 appears explicitly in `annotation/CODEBOOK.md`; the current J1/J2 rules in `src/judge.py` include the general content-verb agent rule but do not spell out CB-7's tell/to example. The stored judge outputs and codebook are retained as supplied. Human validation elsewhere is not a W-D output-specific audit.

**Observed CB-7 limitation:** the declared-rule Qwen TELL example 'I don't tell you to book a taxi.' has focal agent=speaker in both judge variants, although the embedded-doer rule points to addressee. Thus judge agreement does not certify correct application of CB-7, and the stored TELL agent damage is a machine-scored diagnostic, not independently verified semantic damage. No post-hoc relabeling was performed. The Llama transparent polarity counterexample instead visibly drops negation ('I will not lock the door.' → 'You lock the door.').

## Estimands and uncertainty

The protocol does not specify conditional versus unconditional damage denominators or which repeat inputs to use. The following operational choices are explicit analysis choices, not additional preregistered clauses:

- **Primary damage D** = mean( single-cue protected pass AND both-cue protected fail ) over all four factorial cells and both draws. Protect polarity for pol→both; protect agent for actor→both. Per model × encoding × dimension, n=640 aligned transitions.
- **Primary repeat R** = mean( single-cue d1 protected pass status ≠ d2 protected pass status ) over the exact single-cue inputs used in those transitions. Remove duplicate references to the missing second cue: per model × encoding × dimension, n=160 unique same-input repeat pairs. R is symmetric disagreement, so it is more conservative than one-direction repeat pass→fail counted over all repeat draws. Primary Δ=D−R compares two probabilities on the same protected binary endpoint; paired resampling retains their covariance.
- **Companion denominators**: conditional damage = pass→fail / initial passes; conditional recovery = fail→pass / initial failures. Also report conditional damage minus symmetric R, and conditional damage minus directed conditional repeat breakage (number of discordant repeat pairs / number of passing draws). The latter uses both repeat directions and counts each discordant pair once. Neither companion replaces the primary result after outcomes are known.
- **Other checks**: raw focal-label and exact-text repeat disagreement; net fidelity change = recoveries−damage; joint P/A correctness and joint P/A/statement correctness on unique both-cue outputs. Repeat-endpoint sensitivities also use both-cue inputs and an equal-weight mean of single- and both-cue disagreement. Unsupplied agent/polarity choices are not called preservation failures.
- **Literalization** is a lexical diagnostic, not a causal mechanism: strict tell/tells/telling/told regex; broad regex additionally includes say/state inflections and explicit 'this/my statement' frames. Report broad matches, all nonstatement speech-act labels, and their intersection separately. 'I tell you…' can itself be judged a statement, so requiring a nonstatement label would miss lexical literalization. Regex false positives/negatives are possible; exact regexes and real examples are supplied. Rates use 11,520 unique requests, not repeated A/B occurrences.
- **Bootstrap**: 10,000 draws of 80 physical scenario IDs with replacement, seed 20261031, shared across models, dimensions, encodings, draws, and all contrasts. Recompute numerator/denominator ratios in each resample. Intervals are pointwise 95% percentile intervals. Conditional rates with zero-denominator resamples use finite resamples only; `n_boot_valid` is retained in `primary.json`. Zero-event empirical bootstrap intervals are degenerate and do not imply zero population risk. The two greedy repeats estimate a limited noise floor, not a stable measure of every future source of instability.

## Per-model protected transitions

Rates and intervals are percentages except Δ, which is in percentage points. 'Damage / pass' is conditional; D and recovery use all aligned transitions. All rows have 80 physical clusters. Repeat numerators count unique input pairs.

| Encoding | Protected | Model | Damage k/n; D [CI] | Damage / pass | Recoveries k/n | Repeat k/n; R [CI] | Δ=D−R [CI], pp | Point rule |
|---|---|---|---|---|---|---|---|---|
| TELL | polarity | qwen2.5-7b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | polarity | llama3.1-8b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | polarity | gemma3-4b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | polarity | gpt-6.1-terra | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | polarity | pooled | 0/2560; 0.00 [0.00, 0.00]% | 0/2560; 0.00 [0.00, 0.00]% | 0/2560; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | agent | qwen2.5-7b | 84/640; 13.12 [10.31, 16.09]% | 84/636; 13.21 [10.31, 16.09]% | 2/640; 0.31 [0.00, 0.94]% | 0/160; 0.00 [0.00, 0.00]% | 13.12 [10.31, 16.09] pp | exceeds repeat |
| TELL | agent | llama3.1-8b | 6/640; 0.94 [0.00, 2.50]% | 6/632; 0.95 [0.00, 2.53]% | 8/640; 1.25 [0.00, 3.12]% | 0/160; 0.00 [0.00, 0.00]% | 0.94 [0.00, 2.50] pp | exceeds repeat |
| TELL | agent | gemma3-4b | 10/640; 1.56 [0.47, 2.97]% | 10/628; 1.59 [0.47, 3.01]% | 12/640; 1.88 [0.00, 4.38]% | 0/160; 0.00 [0.00, 0.00]% | 1.56 [0.47, 2.97] pp | exceeds repeat |
| TELL | agent | gpt-6.1-terra | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| TELL | agent | pooled | 100/2560; 3.91 [3.01, 4.84]% | 100/2536; 3.94 [3.03, 4.89]% | 22/2560; 0.86 [0.23, 1.56]% | 0/640; 0.00 [0.00, 0.00]% | 3.91 [3.01, 4.84] pp | exceeds repeat |
| STATEMENT | polarity | qwen2.5-7b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | polarity | llama3.1-8b | 55/640; 8.59 [6.25, 11.09]% | 55/640; 8.59 [6.25, 11.09]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 8.59 [6.25, 11.09] pp | exceeds repeat |
| STATEMENT | polarity | gemma3-4b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | polarity | gpt-6.1-terra | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | polarity | pooled | 55/2560; 2.15 [1.56, 2.77]% | 55/2560; 2.15 [1.56, 2.77]% | 0/2560; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 2.15 [1.56, 2.77] pp | exceeds repeat |
| STATEMENT | agent | qwen2.5-7b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | agent | llama3.1-8b | 4/640; 0.62 [0.00, 1.88]% | 4/640; 0.62 [0.00, 1.88]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.62 [0.00, 1.88] pp | exceeds repeat |
| STATEMENT | agent | gemma3-4b | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | agent | gpt-6.1-terra | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0/160; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | no headline |
| STATEMENT | agent | pooled | 4/2560; 0.16 [0.00, 0.47]% | 4/2560; 0.16 [0.00, 0.47]% | 0/2560; 0.00 [0.00, 0.00]% | 0/640; 0.00 [0.00, 0.00]% | 0.16 [0.00, 0.47] pp | exceeds repeat |

## Fidelity, recoveries, and other noise endpoints

| Encoding | Protected | Model | Single fidelity [CI] | Both fidelity [CI] | Net both−single, pp | Recovery / initial fail | Label-repeat disagreement | Text-repeat disagreement |
|---|---|---|---|---|---|---|---|---|
| TELL | polarity | qwen2.5-7b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 14.37 [9.38, 19.38]% |
| TELL | polarity | llama3.1-8b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 7.50 [3.75, 11.25]% |
| TELL | polarity | gemma3-4b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 14.37 [9.38, 20.00]% |
| TELL | polarity | gpt-6.1-terra | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 53.75 [45.62, 61.88]% |
| TELL | polarity | pooled | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 22.50 [19.69, 25.31]% |
| TELL | agent | qwen2.5-7b | 99.38 [98.12, 100.00]% | 86.56 [83.59, 89.38]% | -12.81 [-15.78, -9.84] pp | 50.00 [50.00, 50.00]% | 0.00 [0.00, 0.00]% | 6.25 [2.50, 10.62]% |
| TELL | agent | llama3.1-8b | 98.75 [96.88, 100.00]% | 99.06 [97.50, 100.00]% | 0.31 [-1.88, 2.50] pp | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00]% | 10.00 [5.62, 15.00]% |
| TELL | agent | gemma3-4b | 98.12 [95.62, 100.00]% | 98.44 [97.03, 99.53]% | 0.31 [-2.03, 2.97] pp | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00]% | 8.75 [5.00, 13.12]% |
| TELL | agent | gpt-6.1-terra | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 18.75 [12.50, 25.62]% |
| TELL | agent | pooled | 99.06 [98.28, 99.69]% | 96.02 [95.04, 96.95]% | -3.05 [-4.10, -1.99] pp | 91.67 [75.00, 100.00]% | 0.00 [0.00, 0.00]% | 10.94 [8.44, 13.75]% |
| STATEMENT | polarity | qwen2.5-7b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 10.62 [6.25, 15.62]% |
| STATEMENT | polarity | llama3.1-8b | 100.00 [100.00, 100.00]% | 91.41 [88.91, 93.75]% | -8.59 [-11.09, -6.25] pp | undefined | 0.00 [0.00, 0.00]% | 15.00 [10.00, 20.62]% |
| STATEMENT | polarity | gemma3-4b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 12.50 [7.50, 18.12]% |
| STATEMENT | polarity | gpt-6.1-terra | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 50.62 [42.50, 58.13]% |
| STATEMENT | polarity | pooled | 100.00 [100.00, 100.00]% | 97.85 [97.23, 98.44]% | -2.15 [-2.77, -1.56] pp | undefined | 0.00 [0.00, 0.00]% | 22.19 [19.38, 25.16]% |
| STATEMENT | agent | qwen2.5-7b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 8.12 [4.38, 12.50]% |
| STATEMENT | agent | llama3.1-8b | 100.00 [100.00, 100.00]% | 99.38 [98.12, 100.00]% | -0.62 [-1.88, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 1.88 [0.00, 4.38]% |
| STATEMENT | agent | gemma3-4b | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 6.88 [3.12, 10.62]% |
| STATEMENT | agent | gpt-6.1-terra | 100.00 [100.00, 100.00]% | 100.00 [100.00, 100.00]% | 0.00 [0.00, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 20.00 [13.75, 26.25]% |
| STATEMENT | agent | pooled | 100.00 [100.00, 100.00]% | 99.84 [99.53, 100.00]% | -0.16 [-0.47, 0.00] pp | undefined | 0.00 [0.00, 0.00]% | 9.22 [6.88, 11.72]% |

### Repeat floor on fully specified inputs

The primary single-cue repeat floor is zero in every stratum despite substantial text variation. Fully specified inputs can be less stable; this secondary check avoids treating the single-cue floor as universal. Both-cue repeat inputs number 320 per model/encoding/dimension. Mean-endpoint R gives equal weight to the two endpoints, rather than letting the four both-cue inputs outweigh the two single-cue inputs. These sensitivities were added to check endpoint dependence; they do not change the declared primary denominator.

| Encoding | Protected | Model | Both repeat k/n [CI] | D−both repeat, pp | D−mean endpoint repeat, pp |
|---|---|---|---|---|---|
| TELL | polarity | qwen2.5-7b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | llama3.1-8b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | gemma3-4b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | gpt-6.1-terra | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | pooled | 0/1280; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | agent | qwen2.5-7b | 12/320; 3.75 [1.88, 5.94]% | 9.38 [6.25, 12.50] pp | 11.25 [8.44, 14.06] pp |
| TELL | agent | llama3.1-8b | 0/320; 0.00 [0.00, 0.00]% | 0.94 [0.00, 2.50] pp | 0.94 [0.00, 2.50] pp |
| TELL | agent | gemma3-4b | 2/320; 0.62 [0.00, 1.56]% | 0.94 [-0.31, 2.34] pp | 1.25 [0.31, 2.50] pp |
| TELL | agent | gpt-6.1-terra | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | agent | pooled | 14/1280; 1.09 [0.55, 1.72]% | 2.81 [1.84, 3.83] pp | 3.36 [2.42, 4.30] pp |
| STATEMENT | polarity | qwen2.5-7b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | llama3.1-8b | 5/320; 1.56 [0.31, 3.12]% | 7.03 [4.38, 9.84] pp | 7.81 [5.31, 10.31] pp |
| STATEMENT | polarity | gemma3-4b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | gpt-6.1-terra | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | pooled | 5/1280; 0.39 [0.08, 0.78]% | 1.76 [1.09, 2.46] pp | 1.95 [1.33, 2.58] pp |
| STATEMENT | agent | qwen2.5-7b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | llama3.1-8b | 0/320; 0.00 [0.00, 0.00]% | 0.62 [0.00, 1.88] pp | 0.62 [0.00, 1.88] pp |
| STATEMENT | agent | gemma3-4b | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | gpt-6.1-terra | 0/320; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | pooled | 0/1280; 0.00 [0.00, 0.00]% | 0.16 [0.00, 0.47] pp | 0.16 [0.00, 0.47] pp |

Llama [STATEMENT] polarity remains above the both-cue noise floor: 5/320 repeat disagreements (1.56%), leaving D−R_both=7.03 pp [4.38, 9.84]. Qwen [TELL] agent likewise remains positive at 9.38 pp [6.25, 12.50]. Gemma [TELL] agent becomes less certain against this endpoint: 0.94 pp [−0.31, 2.34]. Thus the transparent-encoding polarity result survives the repeat-endpoint choice; precision of the smaller [TELL] effect depends on that choice.

## Paired encoding contrast

Difference of primary Δ values, [TELL]−[STATEMENT], preserving all pairing. Positive means more excess damage under [TELL].

| Protected | Model | Difference [95% CI], pp |
|---|---|---|
| polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp |
| polarity | llama3.1-8b | -8.59 [-11.09, -6.25] pp |
| polarity | gemma3-4b | 0.00 [0.00, 0.00] pp |
| polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp |
| polarity | pooled | -2.15 [-2.77, -1.56] pp |
| agent | qwen2.5-7b | 13.12 [10.31, 16.09] pp |
| agent | llama3.1-8b | 0.31 [0.00, 0.94] pp |
| agent | gemma3-4b | 1.56 [0.47, 2.97] pp |
| agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp |
| agent | pooled | 3.75 [2.89, 4.61] pp |
| pooled | qwen2.5-7b | 6.56 [5.16, 8.05] pp |
| pooled | llama3.1-8b | -4.14 [-5.47, -2.89] pp |
| pooled | gemma3-4b | 0.78 [0.23, 1.48] pp |
| pooled | gpt-6.1-terra | 0.00 [0.00, 0.00] pp |
| pooled | pooled | 0.80 [0.25, 1.35] pp |

## Joint fidelity and literalization

Joint P/A and P/A/statement fidelity use 640 unique both-cue outputs per model/encoding; lexical and speech-act rates use 1,440 unique outputs across all nine inputs per model/encoding. 'Lexical ∩ nonstatement' is a corroborated subset of regex hits, not the whole literalization rate.

| Encoding | Model | Joint P/A k/n [CI] | Joint P/A/statement k/n [CI] | Broad lexical k/n [CI] | Tell lexical [CI] | Nonstatement act [CI] | Lexical ∩ nonstatement [CI] |
|---|---|---|---|---|---|---|---|
| TELL | qwen2.5-7b | 554/640; 86.56 [83.59, 89.38]% | 467/640; 72.97 [70.78, 74.84]% | 713/1440; 49.51 [46.25, 52.99]% | 49.51 [46.25, 52.99]% | 24.79 [21.94, 27.78]% | 21.25 [19.10, 23.54]% |
| TELL | llama3.1-8b | 634/640; 99.06 [97.50, 100.00]% | 577/640; 90.16 [87.34, 92.97]% | 215/1440; 14.93 [10.28, 20.14]% | 14.93 [10.28, 20.14]% | 14.03 [11.88, 16.18]% | 2.64 [1.53, 3.89]% |
| TELL | gemma3-4b | 630/640; 98.44 [97.03, 99.53]% | 624/640; 97.50 [95.78, 98.91]% | 915/1440; 63.54 [57.57, 69.51]% | 63.54 [57.57, 69.51]% | 16.94 [13.61, 20.28]% | 12.50 [9.65, 15.42]% |
| TELL | gpt-6.1-terra | 640/640; 100.00 [100.00, 100.00]% | 639/640; 99.84 [99.53, 100.00]% | 0/1440; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00]% | 6.74 [5.00, 8.54]% | 0.00 [0.00, 0.00]% |
| TELL | pooled | 2458/2560; 96.02 [95.04, 96.95]% | 2307/2560; 90.12 [89.10, 91.09]% | 1843/5760; 32.00 [29.36, 34.72]% | 32.00 [29.36, 34.72]% | 15.62 [13.89, 17.43]% | 9.10 [8.14, 10.14]% |
| STATEMENT | qwen2.5-7b | 640/640; 100.00 [100.00, 100.00]% | 630/640; 98.44 [96.88, 99.69]% | 1/1440; 0.07 [0.00, 0.21]% | 0.07 [0.00, 0.21]% | 8.89 [6.94, 10.90]% | 0.00 [0.00, 0.00]% |
| STATEMENT | llama3.1-8b | 581/640; 90.78 [87.97, 93.28]% | 514/640; 80.31 [76.25, 84.22]% | 17/1440; 1.18 [0.21, 2.50]% | 1.18 [0.21, 2.50]% | 11.46 [9.31, 13.54]% | 0.14 [0.00, 0.42]% |
| STATEMENT | gemma3-4b | 640/640; 100.00 [100.00, 100.00]% | 636/640; 99.38 [98.59, 100.00]% | 58/1440; 4.03 [2.43, 5.83]% | 1.11 [0.35, 2.08]% | 7.08 [4.65, 9.72]% | 0.14 [0.00, 0.42]% |
| STATEMENT | gpt-6.1-terra | 640/640; 100.00 [100.00, 100.00]% | 639/640; 99.84 [99.53, 100.00]% | 0/1440; 0.00 [0.00, 0.00]% | 0.00 [0.00, 0.00]% | 7.50 [5.62, 9.51]% | 0.00 [0.00, 0.00]% |
| STATEMENT | pooled | 2501/2560; 97.70 [96.99, 98.32]% | 2419/2560; 94.49 [93.40, 95.59]% | 76/5760; 1.32 [0.75, 2.00]% | 0.59 [0.23, 1.04]% | 8.73 [7.22, 10.33]% | 0.07 [0.00, 0.17]% |

Per-cue literalization and speech-act rates, including literalized statements and literalized requests, are in `primary.json` under `diagnostics`.

## Label and denominator sensitivities

J2 replaces focal labels for every row. Agreement-only removes a transition if either endpoint has focal J1/J2 disagreement, and removes a repeat pair if either draw disagrees; these are selected subsets and retain their own denominators. No scored table is modified. General-label ties and CB-7 remain separate measurement limitations.

| Scoring | Encoding | Protected | Model | Δ=D−R, pp | Paired n | Repeat n |
|---|---|---|---|---|---|---|
| J2 | TELL | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | TELL | polarity | llama3.1-8b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | TELL | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | TELL | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | TELL | polarity | pooled | 0.00 [0.00, 0.00] pp | 2560 | 640 |
| J2 | TELL | agent | qwen2.5-7b | 15.94 [12.50, 19.38] pp | 640 | 160 |
| J2 | TELL | agent | llama3.1-8b | 0.47 [-2.66, 2.81] pp | 640 | 160 |
| J2 | TELL | agent | gemma3-4b | 7.97 [4.69, 11.41] pp | 640 | 160 |
| J2 | TELL | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | TELL | agent | pooled | 6.09 [4.80, 7.38] pp | 2560 | 640 |
| J2 | STATEMENT | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | STATEMENT | polarity | llama3.1-8b | 8.59 [6.25, 11.09] pp | 640 | 160 |
| J2 | STATEMENT | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | STATEMENT | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | STATEMENT | polarity | pooled | 2.15 [1.56, 2.77] pp | 2560 | 640 |
| J2 | STATEMENT | agent | qwen2.5-7b | 0.31 [0.00, 0.94] pp | 640 | 160 |
| J2 | STATEMENT | agent | llama3.1-8b | 0.62 [0.00, 1.88] pp | 640 | 160 |
| J2 | STATEMENT | agent | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | STATEMENT | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| J2 | STATEMENT | agent | pooled | 0.23 [0.00, 0.70] pp | 2560 | 640 |
| agreement_only | TELL | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | TELL | polarity | llama3.1-8b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | TELL | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | TELL | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | TELL | polarity | pooled | 0.00 [0.00, 0.00] pp | 2560 | 640 |
| agreement_only | TELL | agent | qwen2.5-7b | 10.32 [7.53, 13.06] pp | 562 | 158 |
| agreement_only | TELL | agent | llama3.1-8b | 0.96 [0.00, 2.55] pp | 627 | 157 |
| agreement_only | TELL | agent | gemma3-4b | 0.91 [0.00, 2.11] pp | 547 | 150 |
| agreement_only | TELL | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | TELL | agent | pooled | 2.90 [2.05, 3.81] pp | 2376 | 625 |
| agreement_only | STATEMENT | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | STATEMENT | polarity | llama3.1-8b | 8.59 [6.25, 11.09] pp | 640 | 160 |
| agreement_only | STATEMENT | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | STATEMENT | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | STATEMENT | polarity | pooled | 2.15 [1.56, 2.77] pp | 2560 | 640 |
| agreement_only | STATEMENT | agent | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 638 | 160 |
| agreement_only | STATEMENT | agent | llama3.1-8b | 0.62 [0.00, 1.88] pp | 640 | 160 |
| agreement_only | STATEMENT | agent | gemma3-4b | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | STATEMENT | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 640 | 160 |
| agreement_only | STATEMENT | agent | pooled | 0.16 [0.00, 0.47] pp | 2558 | 640 |

| Encoding | Protected | Model | Conditional damage−symmetric repeat, pp | Conditional damage−directed conditional repeat, pp | D−raw-label repeat, pp |
|---|---|---|---|---|---|
| TELL | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | llama3.1-8b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | polarity | pooled | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | agent | qwen2.5-7b | 13.21 [10.31, 16.09] pp | 13.21 [10.31, 16.09] pp | 13.12 [10.31, 16.09] pp |
| TELL | agent | llama3.1-8b | 0.95 [0.00, 2.53] pp | 0.95 [0.00, 2.53] pp | 0.94 [0.00, 2.50] pp |
| TELL | agent | gemma3-4b | 1.59 [0.47, 3.01] pp | 1.59 [0.47, 3.01] pp | 1.56 [0.47, 2.97] pp |
| TELL | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| TELL | agent | pooled | 3.94 [3.03, 4.89] pp | 3.94 [3.03, 4.89] pp | 3.91 [3.01, 4.84] pp |
| STATEMENT | polarity | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | llama3.1-8b | 8.59 [6.25, 11.09] pp | 8.59 [6.25, 11.09] pp | 8.59 [6.25, 11.09] pp |
| STATEMENT | polarity | gemma3-4b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | polarity | pooled | 2.15 [1.56, 2.77] pp | 2.15 [1.56, 2.77] pp | 2.15 [1.56, 2.77] pp |
| STATEMENT | agent | qwen2.5-7b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | llama3.1-8b | 0.62 [0.00, 1.88] pp | 0.62 [0.00, 1.88] pp | 0.62 [0.00, 1.88] pp |
| STATEMENT | agent | gemma3-4b | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | gpt-6.1-terra | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp | 0.00 [0.00, 0.00] pp |
| STATEMENT | agent | pooled | 0.16 [0.00, 0.47] pp | 0.16 [0.00, 0.47] pp | 0.16 [0.00, 0.47] pp |

## Artifacts and reproduction

Run `OPENBLAS_NUM_THREADS=1 .venv/bin/python src/r2d_analyze.py` from the repository root. No GPU or model calls. `primary.json` contains every estimate, CI, denominator, sensitivity, exact input hashes, and literal kill-rule verdict. `headline.json` is flat numeric data in proportion units, with `<key>_ci_low`, `<key>_ci_high`, `<key>_n`, `<key>_n_clusters` and counts where applicable. Global `n=10240` is aligned protected transitions, not independent observations; `n_clusters=80`. SE4All imports it as `wd_<key>`. The identical flat `report.json` supports CALE-AI's existing `wd__<key>` loader after its evidence refresh. `metrics.csv`, `transitions.parquet`, `repeats.parquet`, and `repeats_both.parquet` expose the analysis units; `examples.md` gives deterministically selected real texts and encoding controls. `paper/figs/r2d_composition.pdf` and `.png` show per-model paired dots and 95% scenario-bootstrap CIs for Δ, with a fixed-roster pooled row. The figure's two panels protect polarity and agent, respectively; positive Δ exceeds the repeat baseline. No generic interference claim should be imported solely from artifact readiness or from the exploratory Exp C agent drop. Use the encoding/dimension/model verdicts and their uncertainty above.
