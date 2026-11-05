# Intent-coverage pilot, round 1 (machine proxy only)

Date 2026-11-05. Executes PLAN.md sections 2, 3, 5, 5b on the 200 main items (20 writers). Descriptive only: no human ratings exist yet. Figures below are copied from `coverage_by_arm.csv`, `contrasts.csv`, `selector_recall.csv`, `sensitivity.csv`, `summary.json` (all in this folder).

## Status and deviations (log in DEVIATIONS.md)
- **Proxy gate FAILED** (`proxy_validity.json`): holdout AUROC .829 (cluster CI .772-.886), kappa .556 (CI .367-.688), gate (c) fails: AUROC gain over word count .120, CI -.015 to .258 includes 0. Per PLAN sec 3, machine coverage is descriptive; no machine-only claim about arms; S1-S4 are decided by the human stage.
- **Models differ from plan**: gpt-6.1-terra / gpt-6.1-sol returned 503 (no plan). Used `gpt-5.6-terra` (generation) and `gpt-6-luna` (judge, effort low) per `models_used.json`. Judge was not the planned one; log as a deviation.
- Generation: 8069 gen calls (11 errors), 5089 judge calls (5 errors), 5099 unique drafts, 368 label-faithfulness regenerations. Fill after regeneration 83.6% of 1959 edit slots (above the 80% stop-rule threshold), needed-regen rate 18.8%.
- Independent-family judges (Qwen/Mistral on terra drafts): not run.

## Local replication (Qwen2.5-14B, Llama-3.1-8B)
Plain generation is COMPLETE for both (3645/3645 requests each; `runs/coverage_local-qwen14`, `runs/coverage_local-llama`; G1, W1, 8 samples per bare/chip input). Nothing is queued on the cluster. **Proxy judging of these outputs is blocked**: codex-lb returns 429 "Rate limit exceeded, try again in 300s" repeatedly (probe 05:27). `src/coverage_local_eval.py` is ready and resumable (judge cache); it only covers G1/W1/D3s/D5s (contrast/prompted-diversity arms need terra edit calls). S7 (arm ordering on local models) is therefore unevaluated.

## Machine coverage per arm (proxy; writer-cluster 95% CI; n=200)
| arm | k | bare | chip |
|---|---|---|---|
| G1 | 1 | .145 (.080-.215) | .580 (.475-.680) |
| W1 (word cue) | 1 | | .565 (.450-.675) |
| D3s | 3 | .200 (.125-.280) | .685 (.575-.790) |
| D3p | 3 | .245 (.160-.340) | .695 (.590-.795) |
| C3 | 3 | .315 (.215-.420) | .675 (.565-.780) |
| E3 | 3 | .250 (.155-.345) | .690 (.585-.790) |
| R3 | 3 | .255 (.175-.345) | .635 (.530-.740) |
| C3f | 3 | .265 (.175-.360) | .650 (.540-.765) |
| C3o (oracle, ceiling) | 3 | .420 (.310-.530) | |
| D5s | 5 | .205 (.130-.290) | .690 (.580-.790) |
| D5p | 5 | .390 (.290-.490) | .800 (.715-.880) |
| C5 | 5 | .420 (.315-.525) | .690 (.575-.795) |
| E5 | 5 | .340 (.240-.445) | .735 (.630-.830) |

Ceiling (any draft of any arm covers): bare .595, chip .840, word .565. Loose rule (`partly`=yes) raises all values (e.g. G1 bare .23, E3 chip .94).
Short sets (fewer than k drafts after filtering): D3s 65.5% / D5s 88.5% of bare items (sampling collapses to few distinct drafts); C3 25.5%, E3 11.5% bare.

## Pre-declared contrasts (paired, percentage points, cluster CI, sign-flip p)
- Cue tap: G1 chip - G1 bare = +43.5 (34.5 to 53.0). W1 word - G1 chip = -1.5 (-8.0 to 5.0).
- S1 (targeting vs diversity, bare, k=3): E3 - D3p +0.5 (-7.5 to 9.0); C3 - D3p +7.0 (0.0 to 14.5, p .026); R3 - D3p +1.0; C3f - D3p +2.0; oracle C3o - D3p +17.5 (8.0 to 27.0). By the plan's own selection rule (larger on proxy, C3), the proxy difference is below the +10 pp bar; unresolved. At k=5: C5 - D5p +3.0 (-5.5 to 12.0); E5 - D5p -5.0 (-13.0 to 3.0).
- S2 (set vs one cue tap): best bare set vs G1 chip: C3 -26.5 (-38.0 to -14.5), E3 -33.0. Far from non-inferior. Cost per covered message (r=.5): bare E3 29.4, C3 22.6 vs G1 chip 8.4. S2 fails on the proxy.
- S3 (set adds to a cue, chip): E3 - G1 +11.0 (4.5 to 18.5); C3 +9.5; D3p +11.5 (5.0 to 19.0); E5 +15.5; C5 +11.0; D5p +22.0 (13.5 to 31.0). Plain prompted diversity matches or beats contrast sets: E3 - D3p chip -0.5 (-6.0 to 5.0); E5 - D5p -6.5 (-12.5 to -1.0).
- Over G1 in bare: C3 +17.0, E3 +10.5, D3p +10.0, D3s +5.5.
- Sensitivity (no Part 18 repeats n=188; no hw2; no short sets): same signs and magnitudes (e.g. E3 chip - G1 +10.6 / +11.2 / +12.7).

## Selector and safety
- Selector recall of the pair's true dimension: @1 .24 (static .16, random .17); @2 .41 (static .37, random .33). H3 criterion (>= static + .05 at @2) NOT met (+.04). Per-dimension @2 is near 1 for speech_act (.98) and agent (.94) and near 0 for certainty (0), politeness (.04), polarity (.09), time_quantity (.10): the selector mostly names two dimensions. Selector C3 beats static C3f by +5.0 in bare coverage only descriptively (.315 vs .265).
- Wrong-first (G1 reads the other variant): bare .365, chip .020; identical across arms because slot 1 = G1.
- Cue violations: raw chip edit drafts contradict the cue 29.1% (event 12%, samples 18.8%, prompted diversity 15.2%); shown after the hard filter: C/E/R arms 0%, but D3p 53.8% of non-G1 drafts (D5p 15.3%, D3s 17.1%, D5s 18.8%) contradict the cue because diversity arms are unfiltered. Filtered contrast sets therefore carry a safety advantage that coverage does not show.
- Both-sides coverage (bare, covers_both): C3 .12, C5 .24, D5p .22, E5 .125, C3o .29, D3p .06, G1 0 (minimal-pair property is only partly reached; C-arms are best at k=3).
- Median drafts read to first covering draft among covered E3 items: 1.0 (chip and bare), meaning most coverage comes from slot 1.

## Break-even (cost grid, `breakeven.csv`)
In chip, sets beat G1-with-chip only for small read cost: C3/C5 up to r=.60, E3 1.2, E5 1.45, D3p 1.45, D5p 2.5. In bare no set beats chip G1 at any r tested.

## Reading against outcome rules (provisional, machine only)
Proxy suggests: a cue tap dominates every bare draft set (+43.5 pp for one tap); in chip, extra drafts add about 10 pp but prompted diversity does as well as contrast sets; targeting adds a modest gain over diversity only with the oracle dimension. This looks closer to C-C / partial C-B than C-A, but the gate failed and the sign cannot be turned into a claim until human results. Moves that this round supports: build the Stage 6 package with D3p and C3 as the diversity and targeting arms (E3 did not beat D3p); keep D5p in the audit pool.

## Caveats
Single judge (gpt-6-luna), failed gate, drafts from gpt-5.6-terra, bug in contrasts.csv last row (wrong-first duplicate of the S3 E3 numbers; use the `wrong_first` column), writers' items are minimal pairs written to a dimension quota. No AAC-user claim; writer-intent agreement by adult annotators.
