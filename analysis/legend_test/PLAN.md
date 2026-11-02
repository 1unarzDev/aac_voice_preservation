# E1 plan: three-arm prompt-legend test (threat T1), written BEFORE any generation or any look at outputs

Written 2026-11-02 before `runs/legend1` was generated. Source: `ideas/review_j1/SYNTHESIS.md` T1, `methods_review.md` 1.1.

## Question
Is the ~99% affirmative reading of a bare (keywords-only) polarity input an LLM default, or an inference induced by the
chip legend that every P0 prompt carries (the legend lists `[NOT]`, so "no `[NOT]`" can read as "affirmative")?

## Arms (bare channel only, P0 wording, one sentence output, greedy)
| arm | prompt id | text | sha256 (prompt = template + legend, as `prompts.template_sha`) |
|---|---|---|---|
| a | `P0` (unchanged) | existing P0 with the chip legend | ad8e7920bfeba2badf6d831b7923170cabb5fa1841f44b583088c3167481bcf7 |
| b | `P0n` | P0 wording with NO legend and no mention of chips (`prompts/P0_nolegend.txt`) | 33a2971bd34448a2abef26bd03f18fa995a9587535e166ba75a9f8c300a0f5fe |
| c | `P0m` | P0 + legend + one line (`prompts/chip_legend_m.txt`) | 86899fd454efed2368d052563932d70614a96672dc3d515f91c2c4522b4d2d47 |

Arm c line, verbatim, fixed now: "Markers may be missing; if the keywords do not say whether the message is negative or affirmative, do not assume either reading."
File sha256: `P0_nolegend.txt` 53da659e..., `chip_legend_m.txt` df38103f..., `chip_legend_none.txt` (empty) e3b0c442....
P0's sha and all existing request keys are unchanged (new prompt ids in `src/prompts.py`; D-012 precedent for `P0x`).

## Items and models
hw1 polarity families (`data/items/hw.jsonl`, 104, 7 writers) and W-C polarity families (`data/items/r2_c1.jsonl`, 80). Copies are in
`data/items_ext/legend_items.jsonl` (sha256 in the report). Bare input is identical for A and B, so one request per family x model.
Models: qwen2.5-7b, llama3.1-8b, gemma3-4b (local, GPU lock, `src/run_sequential.sh`) and gpt-6.1-terra.
Draws: namespaces `d1`, `d2` for all three arms (fresh cache keys, same seed, so the draws measure greedy/batching instability, not sampling).
Arm a additionally has the original un-salted draw (`d0`, cached from hw1 / r2c1, free). Requests: `runs/requests/legend1.jsonl`.
Judge: `src/judge.py --concurrency 8` (J1/J2, `gpt-6.1-sol`), blind arbiter on disputed critical labels from output text only
(`runs/hw1/arbiter.jsonl` precedent), `attribute.py` WITHOUT fallback. Unresolved rows stay missing, not imputed.

## Primary metric (fixed now)
Affirmative share = among valid outputs whose critical label is `affirmative` or `negated`, the fraction `affirmative`
(the P3 frame of W-C and hw1 that produced the 99.4% / 99.8% headline). Unit = one (request, suggestion), A/B shared requests counted once.
Primary draw = `d1`; `d2` is a replication; `d0` (arm a only) is a check against the earlier published number.
CI = percentile bootstrap resampling FAMILIES (10,000, seed 20261031); hw1 is additionally reported with writer clusters.
Reported cells: arm x model x source set (hw1, WC) and pooled over models and sources. Secondary metrics:
commitment rate (share of valid outputs that are not `unclear/mixed`), affirmative share among ALL valid outputs
(unclear counted in the denominator), negated share, unclear share. Arm differences (b - a, c - a, c - b) are paired by
family x model, family-cluster bootstrap.

## Decision rule (fixed now, applied to the pooled primary metric of arms b and c; draw d1)
- **Default is not a legend artifact:** arms b AND c both have pooled affirmative share >= 90%.
- **Default claim must be reframed:** arm b OR arm c has pooled affirmative share < 70% (the legend, or an instruction about it, produces the default).
- **Partly induced:** otherwise (an arm between 70% and 90%): report as a legend-sensitive default, with the size of the drop.
- Per-model classification uses the same thresholds on each model's pooled-over-sources share; a model with a different
  classification than the pooled one is reported as model-specific, and does not override the pooled verdict.
- Pre-written reading of arm c: if arm c reduces the commitment rate (more `unclear/mixed` outputs) while the committed
  outputs stay >= 90% affirmative, the verdict is "instructable abstention, direction of residual error unchanged": the default
  survives for direction and the paper must say the unmarked reading is suppressible by an instruction. The
  all-valid affirmative share and the commitment rate are reported next to the primary number so a reader sees both.
- No arm, model or draw is dropped after outputs are seen. `d2` and `d0` cannot rescue or overturn the d1 verdict, but disagreements are reported.

## Not claimed
This isolates one confounder (the chip legend text and the "markers may be missing" instruction) under one wording. It does
not show that models would behave this way on real AAC input, nor that "affirmative" is wrong: how rational a default is
(T2) is a separate analysis.
