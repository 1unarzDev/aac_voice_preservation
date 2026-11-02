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


---
## Amendment 1 (2026-11-02 05:50 UTC, after the first test calls, before any result was inspected): the planned models do not exist for this key

Empirical limits (AI Studio free tier, this key; probes and the first tier-1 sends, `runs/gemini_429.jsonl` has every 429):
- `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`: HTTP 404 "no longer available to new users". They cannot be used.
- `gemini-3.1-pro-preview` / `gemini-pro-latest`: HTTP 429 with `generate_content_free_tier_input_token_count limit: 0`. No free-tier Pro at all.
  So tier 4 (Pro) and tier 5 (Pro as arbiter) are blocked unless the allowance changes; they stay in the plan with the model id replaced
  by `gemini-3.1-pro-preview` and are re-tested at every daily relaunch only if someone sets a non-zero limit in `runs/gemini_limits.json`.
- `gemini-3.5-flash` (thinkingBudget 0 accepted): **5 requests/min, 20 requests/day** (`GenerateRequestsPerMinutePerProjectPerModel-FreeTier` = 5,
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier` = 20). `gemini-3.6-flash` and `gemini-3.7-flash` also hit a 20/day cap (3.7 was returning 503 high demand);
  `gemini-3.8-flash` timed out (overloaded). They are not queued: a 20/day model can not finish any tier in a useful time, and mixing flash snapshots inside one tier would
  confound the model identity.
- `gemini-3.1-flash-lite` (thinkingBudget 0 accepted): >= 14 requests/min, daily cap recorded in the discovered-limits section of the report below.

Consequence, fixed before inspecting any Gemini output:
- Model identity of the "Gemini family" arms: **gemini-3.5-flash** (the named flash; budget 0) gets its 20/day on tier 1 first (priority list unchanged, tier 1 then 2 then 3);
  **gemini-3.1-flash-lite** (budget 0) runs the same tiers 1, 2, 3 in the same order concurrently, since its quota is independent (using it costs the flash arm nothing).
  They are reported as two separate models, never pooled.
- Inside a tier the order is now family-hash order (sha256("20261101"+family_id)), a family's requests adjacent (the a/c arms and the chip/noncrit/irrel/nlcue channels stay paired).
  With a 20/day quota every prefix is then a random sample of families, not an alphabetical block. (Amends the "family-ordered prefix" sentence above; request keys are unchanged.
  Flash-lite's first 262 tier-1 requests were sent in the old order, hw1 families first, before this change; they are kept and the rest completes the tier.)
- The Pro subset rule is moot (Pro unavailable). The report states n per cell for every number.

## Discovered limits and projections (measured 2026-11-02 UTC, free tier, this key; every 429 is in `runs/gemini_429.jsonl`)
| model | RPM | RPD | notes |
|---|---|---|---|
| gemini-3.5-flash | 5 | 20 | runner sends at 4.5/min |
| gemini-3.1-flash-lite | >= 14 measured, runner uses 12/min | 500 | exhausted after 500 requests (quota value 500 in the 429) |
| gemini-3.6-flash, gemini-3.7-flash | not measured | 20 | not queued |
| gemini-3.1-pro-preview / gemini-pro-latest | n/a | 0 | free-tier limit 0 (input-token metric) |
| gemini-2.5-* | n/a | n/a | 404, not available to new users |
Quota resets at midnight Pacific (08:00 UTC while PST). The reset instant was confirmed only from the 429 `retryDelay` (about 2 h 20 min at 05:37 UTC).

Requests completed on the first day (up to 06:16 UTC): flash-lite 486 (tier 1 complete 356/356, tier 2 130/1030), flash 12 (tier 1, 6 family pairs).
Projection (one daily batch each, after the reset at 08:00 UTC; judging adds a few hours of latency, no Gemini quota):
- gemini-3.1-flash-lite: tier 2 completes with the 2nd daily batch from now (900 left: 500 + 400), tier 3 (2,205) with the 7th (5 more full batches after tier 2 ends, ~Nov 8 PT). Whole queue: about 7 more daily batches.
- gemini-3.5-flash: tier 1 has 344 left = 18 daily batches (about Nov 19), tier 2 1,030 = 52 more batches, tier 3 2,205 = 111 more. At 20/day only tier 1 is realistic; tier 2 for this model would need a quota change or a different model.
