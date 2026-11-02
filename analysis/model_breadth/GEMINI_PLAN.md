# Gemini third model family: plan and priority order (written 2026-11-01 BEFORE any generation request was sent)

Goal: add Google Gemini (AI Studio, free daily allowance) beside Qwen/Llama/Gemma/terra, spending the daily quota on the
highest-value requests first. Nothing here changes any existing request key, prompt, or analysis: Gemini rows are
retargeted copies of the gpt-6.1-terra requests (same prompt bytes, input, targets, namespace, T=0, max_tokens=96),
with `model` swapped and `request_key` recomputed by `build_requests.request_key`.

## Backend settings (fixed now)
- Whole rendered prompt as ONE user message (no system message), exactly as for terra. temperature 0. maxOutputTokens 96.
- gemini-2.5-flash: `thinkingBudget` 0 (thinking off, saves quota and tokens). gemini-2.5-pro: thinking cannot be disabled, so
  `thinkingBudget` 128 (the minimum) and maxOutputTokens raised by 256 so thinking cannot starve the sentence.
  Both are written into every cache entry. No seed (the API has none that is honoured; same caveat as terra).
- Judging: existing gpt-6.1-sol judge via codex-lb (J1/J2, concurrency <= 8). No Gemini quota is spent on judging.
  Blind arbiter as usual (`src/arbiter_tool.py`, output text only); attribution WITHOUT fallback; unresolved rows stay missing.

## Priority tiers (highest value per request first; counts from `src/build_gemini_requests.py`)
| tier | model | content | requests | why |
|---|---|---|---|---|
| 1 | flash | legend test: polarity bare, arm a (P0 + legend) and arm c (P0 + legend + "markers may be missing"), draw d1, hw1 + W-C (184 families; 178 distinct bare inputs) | 356 | the default claim (affirmative default is not a legend artifact) on a third family |
| 2 | flash | cue restoration on hw1 polarity + speech_act: chip1, noncrit, irrel (irrelevant chip), nlcue (plain word) | 1,030 | the cue claim (chip gain is cue content; plain word matches chip) |
| 3 | flash | rest of hw1 P0: bare, chip1, full, all 6 dimensions (minus tier 2) | 2,205 | full hw1 six-dimension side-by-side |
| 4 | pro | same tiers 1 and 2 (subset rule below if the daily cap is small) | see limits section | flagship model on the two headline claims |
| 5 | pro (optional) | second-family arbiter on the arbitrated units (`runs/*/arbiter.jsonl`), agreement with the Claude arbiter | n/a | judge-independence threat T5; only after tiers 1-4 |

Ordering inside the daily queue is strictly tier 1, 2, 3 for flash, then pro tier 1, 2. A tier is finished before the next
starts; the runner is resumable (cached requests skipped), so a daily quota stop simply resumes the next day.
Within a tier the order is the request-file order (family order), so a half-finished tier is a family-ordered prefix.
This is deterministic, chosen before any output was seen, and makes n per cell visible in the report.

## Pro subset rule (applies only if pro's discovered daily cap cannot cover the tier within about 3 days)
Stratified deterministic subset: strata = (run, dimension, channel, prompt id, draw); strata sorted, rows in each stratum
ordered by sha256(20261101 + request_key); strata take turns (round robin) until the cap N is reached. The cap and the
resulting counts are stated in the report. The rule is fixed before any pro output is seen. (Filled in below after the
limits are known.)

## Not claimed
Single decoding configuration (T=0, thinking off for flash, minimum for pro), unseeded API, free-tier model snapshots can change
(model_reported is stored per request). Model-breadth evidence only; agreement with Claude arbiter is not human validation.

