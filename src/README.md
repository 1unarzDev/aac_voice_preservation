# Generation harness (SPEC v0.1)

families (`data/items/*.jsonl`) → `build_requests.py` → requests → `generate.py` (cached, async) →
`runs/<run_id>/generations.jsonl` → `explode.py` → `outputs.jsonl` + `unique_outputs.jsonl` (judge input)

All commands run from the repo root with the venv active: `cd ~/aac-voice-preservation && . .venv/bin/activate`.

## 1. Local servers
```bash
src/serve_local.sh          # all three at once (fits: ~15.1 / 16.4 GB incl. ~1 GB desktop)
src/serve_local.sh gemma    # or just one/some (qwen | llama | gemma), e.g. sequential mode
src/stop_local.sh           # removes all aacv-* containers
python src/models.py        # health of every registry endpoint (add --verify-sha to hash GGUFs)
```
| container | model | port | alias (= request `model`) |
|---|---|---|---|
| aacv-qwen | Qwen2.5-7B-Instruct Q4_K_M | 8091 | qwen2.5-7b |
| aacv-llama | Llama-3.1-8B-Instruct Q4_K_M | 8092 | llama3.1-8b |
| aacv-gemma | gemma-3-4b-it Q4_K_M | 8093 | gemma3-4b |

Image `ghcr.io/ggml-org/llama.cpp:server-cuda`, models mounted read-only, `--gpus all -ngl 99 --jinja
--parallel 8 -c 8*CTX_PER_SLOT` (CTX_PER_SLOT default 1536), `-fa on -ctk q8_0 -ctv q8_0` (q8 KV cache
is what makes all three fit). The script waits for `models/SHA256SUMS` or for the final file sizes.
If VRAM gets tighter (e.g. desktop apps grow), use `CTX_PER_SLOT=1024 src/serve_local.sh`, or run
the models one at a time: `src/serve_local.sh qwen`, generate with `--models qwen2.5-7b`, then stop and
start the next. Prompts are 183–330 tokens and outputs at most 128, so 1024 per slot is enough.

## 2. Registry (`models.py`)
Local: the three above. API (`https://codex.lunarz.dev/v1`, OpenAI chat/completions): `gpt-6.1-terra`
(under test) and `gpt-6.1-sol` (judge). The key comes from env `CODEX_LB_API_KEY`, or is parsed from
`~/.config/caelestia/.env.secrets`. That file is fish syntax (`set -gx`), so it can't be `source`d from
bash; models.py reads it itself. The key is never printed or written.
**The API rejects `seed`** (HTTP 400 "Unsupported parameter: seed"), so it is never sent to API models.
Local requests use `seed = 1000 + sample_idx`. `gpt-6.1-sol` uses hidden reasoning tokens, so give
it a generous `max_tokens` when judging.

## 3. Prompts (`prompts.py`, `prompts/*.txt`)
| id | template | T | k samples | suggestions per response |
|---|---|---|---|---|
| P0 | `P0.txt` (old expand.txt wording) | 0 | 1 | 1 |
| S3 | `P0.txt` (same text) | 0.7 | 3 | 1 |
| P1 | `P1.txt` preservation | 0 | 1 | 1 |
| P2 | `P2.txt` spanning, JSON list of 3 | 0 | 1 | 3 |

Every template includes `prompts/chip_legend.txt`. A family's `context` (if any) is rendered as
`Situation: ...`. `prompt_sha` = sha256(template + legend) is stored in every row and in config.json.
Changing a template changes the sha, the request_key, and therefore the cache entry.

## 4. Requests
```bash
python src/build_requests.py --items 'data/items/*.jsonl' --out runs/requests/pilot.jsonl \
    --split pilot [--models qwen2.5-7b,gpt-6.1-terra] [--prompts P0,P1,P2,S3] [--channels bare,noncrit,chip1,chipall,full]
```
Default models are the 4 under test. Channel inputs:
`Keywords: <bare>`, `Keywords: <bare+noncritical, in source order>`, `Keywords: <chips> <bare>`,
`Keywords: <all_chips> <bare>`, `The user typed: <source>`. Chips are sorted in legend order.
`request_key = sha1([model, prompt_id, rendered_prompt, temperature, sample_idx])`. Identical renders
are merged into one request, and `targets` lists every `(family_id, variant, channel)` that uses it
(bare/noncrit are shared by A and B; chip1 and chipall can coincide).
Numeric chips like `[2]` (used by pilot time_quantity items) are accepted provisionally with a
warning and placed after the time chips. **They are not in the SPEC legend, so this needs a decision.**
Families with `split: smoke` are skipped unless `--split smoke` is given.
Validation: every variant needs at least 1 chip, all chips must be in the vocabulary, and
`critical_value` must be one of `critical_options`.

### Follow-up experiments (D-012)
`python src/make_followup_items.py` writes `data/items/expB.jsonl` / `expC.jsonl` (splits `expB`/`expC`,
opt-in like `smoke`). Such families carry `custom_channels` = `{variant: {channel_id: input_text |
{"input", "commitments", "prompts"}}}`, rendered instead of the 5 standard channels; `commitments` tell
attribute.py which dimensions the input specifies (cue_in_input = critical chips among them), and
`prompts` restricts a channel (alias / `[·]` padding channels need `P0x` = P0 + `prompts/chip_legend_x.txt`).
`--namespace d1,d2` builds one request set per salt (separate cache entries; no salt = old keys).
```bash
python src/build_requests.py --items data/items/expB.jsonl --split expB --prompts P0,P0x --namespace d1,d2 --out runs/requests/expB1.jsonl
python src/build_requests.py --items data/items/expC.jsonl --split expC --prompts P0 --namespace d1,d2 --out runs/requests/expC1.jsonl
```

## 5. Generate
```bash
python src/generate.py --requests runs/requests/pilot.jsonl --run-id pilot1 \
    [--models gemma3-4b] [--local-concurrency 8] [--api-concurrency 16] [--retries 5]
```
- The cache `runs/cache/<request_key>.json` is written once, after a successful call. Re-runs and
  resumes are free. Failed calls are not cached: the run exits 1, and re-running retries only those.
- **Never delete the cache for production runs.** Greedy output is not bit-reproducible: two fresh
  smoke runs agreed on 81–88% of local greedy outputs (llama.cpp continuous batching) and on 69%
  for the API at T=0. The cache freezes the first draw. Use `--cache-dir /tmp/x` only to benchmark.
- Each row records `raw_text`, `finish_reason`, `latency_s`, `usage`, `model_reported`, `seed`,
  `attempts`, `suggestions`, `parse_ok`, `parse_method` (json | lines | single | first_line | empty),
  and `targets`. Parsing strips code fences, bullets/numbering, `Suggestion 1:` style labels, quotes
  and `**`. P2 accepts a JSON list (also `{"k":[...]}` and `["a"], ["b"]` shapes) and falls back to
  lines. `parse_ok` = exactly the expected number of suggestions via the expected route.
- `config.json` stores the models (no secrets), prompt specs and shas, the requests-file sha,
  `code_sha256` (src/*.py + *.sh), throughput, parse failures and finish reasons.
  `throughput.jsonl` gets one line appended per invocation.

## 6. Explode
```bash
python src/explode.py --run runs/pilot1 [--by-input]
```
`outputs.jsonl`: one row per (generation × suggestion × target), with
`output_id = sha1([request_key, suggestion_idx, text])[:16]`.
`unique_outputs.jsonl`: one row per normalised text (`text_id`) with its `output_ids` and
`input_texts`. Use `--by-input` to dedupe on (text, input_text) for judge passes that show the
visible input (Pass A `added_content`).

## Smoke test (2 toy families, `data/items/smoke.jsonl`, split `smoke`)
```bash
python src/build_requests.py --items data/items/smoke.jsonl --split smoke --out runs/requests/smoke.jsonl
python src/generate.py --requests runs/requests/smoke.jsonl --run-id smoke1
python src/explode.py --run runs/smoke1
```
2 families × 2 variants × 5 channels × (P0+P1+P2+3×S3) × 4 models gives 480 cells, which collapse
to 384 unique requests, 512 outputs and 180 unique texts.
Throughput measured on 2026-10-31 (all four running at once, fresh cache, 3 servers sharing the GPU):

| model | req/min | outputs/min | completion tok/s |
|---|---|---|---|
| qwen2.5-7b | 443–535 | 590–713 | 97–117 |
| llama3.1-8b | 451–484 | 601–645 | 97–106 |
| gemma3-4b | 366–392 | 480–522 | 99–105 |
| gpt-6.1-terra (conc 16) | 169–179 | 226–238 | 58–67 |

## 7. Interventions (CALE-AI): `interventions.py`, `run_interventions.sh`
Two runtime interventions, both evaluated with the standard judge/attribute pipeline. They
reuse a base run's cached first pass (P0 for I1; P2 + S3 bare for I2) and write a standard run
(`generations.jsonl` with `targets` → explode → judge → `attribute --fallback J1`).
| arm (`prompt_id`) | what |
|---|---|
| `P0` | first pass, copied from the base run (same request_key, judge cache hits) |
| `G1` | **I1 commitment guard**: layer0 (+ a small number/tense add-on) checks the P0 output against the commitments the user *supplied* (chips parsed from the visible input; for `full`, layer0 labels of the typed source), plus unsupplied politeness (polite marker without `[PLEASE]` / without politeness in the source). On a flag: same conversation + one feedback turn ("Your sentence must keep: negated (...); no added politeness (...)"), up to `--max-retries 2`. Returns the first unflagged attempt, else the fewest-flag attempt (ties → original). |
| `G1s` | strip-only variant: deterministic removal of an unsupplied "please"; 0 calls |
| `P2`, `S3` | bare-channel first pass, copied |
| `I2` | **ambiguity-complete set**: keep P2's s1; for polarity then certainty, if layer0 finds no slot with the alternative reading of s1, replace slot 3 (then 2) with an LLM rewrite of s1 ("make it NEGATED ..."), layer0-verified, one feedback retry |
Extra keys on G1/G1s/I2 generation rows: `base_request_key`, `guard_spec`, `flags_initial`,
`flags_final`, `attempts`, `chosen_attempt`, `changed`, `extra_calls`, `extra_latency_s`,
`extra_completion_tokens`, `check_ms`; I2: `base_suggestions`, `span_plan`. Calls are cached in
`runs/cache/` (key = sha1(model, tag `I1-guard-v1`/`I2-span-v1`, messages, T=0, seed)).
`attribute.py` includes `I2` in coverage@3 (no change for older runs).
```bash
src/run_interventions.sh dev0 guardpilot spanpilot         # flock /tmp/aacv_gpu.lock (D-019), one server at a time + terra
python src/judge.py --run guardpilot --concurrency 8 && python src/attribute.py --run guardpilot --fallback J1
python src/judge.py --run spanpilot  --concurrency 8 && python src/attribute.py --run spanpilot --fallback J1
python src/interventions.py report --guard guardpilot --span spanpilot --out analysis/interventions/pilot.md
# main: base = runs/main1 (test split, cached first pass) -> guard1 / span1 -> analysis/interventions/report.md
```
`dev0` = P0/P2/S3 first pass on `data/items/dev.jsonl` (`build_requests --split dev --prompts P0,P2,S3`).
VRAM shared with an external process: `NGL_QWEN=14 NGL_LLAMA=14 NGL_GEMMA=20 src/run_interventions.sh ...`
serves with partial CPU offload (`serve_local.sh` honours `NGL`, default 99 = unchanged). This was used
for the guard/span calls on 2026-10-31 (the cached first passes were served fully on GPU).
`judge.py --concurrency N` (default 16, unchanged) caps in-flight judge calls; use <= 8 (D-019).
