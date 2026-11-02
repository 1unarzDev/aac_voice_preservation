# Stage 0 pilot notes (mechanics only; no H1-H5 outcome evaluated; pilot items excluded from Stage 1)
Run 2026-11-02 16:44-16:47 CST, qwen2.5-7b Q4_K_M, llama.cpp build b12019, GPU lock held (blocking flock; waited about 5 min behind a robotics job and one other frontier). Script `src/frontier_knows_not_says_pilot.py`, raw `pilot_mechanics.json`, `pilot_generations.jsonl`, `pair_scores_raw.json`, `pilot_items.json` (60 E-human messages, 20 E-pairs). The first attempt (round 1) crashed with KeyError 'logprobs' because `top_logprobs=0` suppresses logprobs in llama-server; fixed by requesting >= 1.

Numeric rule A1 and result
| check | rule | result | verdict |
|---|---|---|---|
| (a) logprob coverage | >= 99% of generated tokens | 7,550 / 7,550 = 100% | pass |
| (b) untruncated sampling | per-token freq within 0.03 of server prob (20 prompts x 200) | mean abs dev 0.0055, max 0.0283; tail draws (p<0.02) 16 observed vs 14.1 expected. Server defaults (top_k 40, top_p .95, min_p .05): 0 tail draws | pass; defaults truncate the tail, explicit top_k=0, top_p=1, min_p=0 is required |
| (c) forced scorer vs generation | within 0.05 nats on >= 95% of 50 sequences | 34/50 = 68% (mean abs diff 0.015, worst 0.45) | FAIL as written |
| (d) /embedding | finite fixed-dim vectors | HTTP 501 (server lacks --embeddings) | not available; arm dropped (A11) |
| (e) throughput | measured | 21.2 req/s, 157 tok/s, 7.4 tokens/request; 0.4-0.5 h per model for the main arm | ok |

Why (c) fails: the server is not run-to-run deterministic. Repeating the same 50 greedy requests (concurrency 4) gave the same text in 46/50 and, among those, logprobs within 0.05 nats in 36/46 (78%) with prompt cache, 29/46 without. So forced decoding agrees with generation about as well as generation agrees with itself (68% vs 78%); a 95% rule cannot be met on this server. Amendment A10 (post-pilot, written before Stage 1) replaces the rule by "no more than 10 points below the generation-vs-generation fraction and mean abs diff <= 0.05" (met: 68 vs 78, 0.015).
Other mechanics: no prompt-logprob endpoint exists (n_predict=0 / echo give no prompt logprobs), so pair scoring uses per-token forced decoding (0.19 s per candidate, top-1000 only: 12 of the pilot pair tokens fell outside and are imputed with the 1000th logprob as an upper bound).
Consequence to carry: single-token probabilities from this server carry noise up to about 0.4 nats at individual positions (batching, q8_0 KV cache); about 8% of greedy repeats change text.
