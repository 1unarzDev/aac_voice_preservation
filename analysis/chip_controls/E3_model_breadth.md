# E3 (T8 model breadth): not run

Checked 2026-11-02. `GET /v1/models` on codex-lb (needs a browser-like User-Agent; the default urllib agent gets 403) lists:
`codex-auto-review`, `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-6-astra`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-reserve`.
One-request probes of P0 on `Keywords: not want go party` (T=0, max_tokens 96): gpt-6-astra, gpt-5.6-sol, gpt-6-luna, gpt-5.6-luna, gpt-5.6-terra answered normally
(0 reasoning tokens); gpt-6-sol timed out at 120 s once.

Decision: **skipped.** Every available model is a tier or generation of the same GPT family already represented by gpt-6.1-terra; `gpt-6.1-sol`
is the judge (using it as a subject would add a judge-equals-subject confound). No non-GPT family and no larger open model is on the endpoint, and the
tier sizes are not documented, so "larger" cannot be verified. Adding another GPT tier would not answer the T8 "different families" objection and would
cost about 5,100 API generations per model (hw1 bare + chip1 + full) plus judging, with usage-limit risk. The one-family limit stays an explicit limitation.
If a different tier is wanted anyway, the cheapest defensible choice is gpt-5.6-terra (older generation, same tier name) and gpt-6-astra, registered as `role=under_test`.
