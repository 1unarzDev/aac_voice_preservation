# partner_context, round 2: echo-corrected re-run (130 fresh families, 4 models)
All numbers are machine-only and PROVISIONAL (R9) until the human check in ANNOTATION_REQUEST.md (round-2 revision) returns. Plan: PLAN.md A3-A9 (amendments A3-A8 written before any turn/output existed; A9 is a post-hoc deviations log).

## What was done
- 130 polarity families, E0 families excluded: pool = 64 unused hw polarity + 80 r2_c1 polarity = 144 (the pool cannot supply more), `random.Random(20261103).sample`. All analysed (ITT).
- Turns authored by mistral-nemo-12b (local; not the checker/judge family, not under test): D, three X negation forms (Xa explicit negation word, Xb implicit "failed/fell through", Xc quantifier "no sign/nobody"), topic-locked Q. Checker gpt-6.1-sol. Robustness: qwen2.5-14b authored X turns for 40 families. Checker pass after retry: D 88%, Xa 84%, Xb 39%, Xc 80%, Q 72% (Xb fails mostly because the authoring model writes "didn't"; ITT keeps them). N turns dropped; baseline = no-turn arm 0.
- Models: qwen2.5-7b, llama3.1-8b, gemma3-4b (local, greedy), gpt-6.1-terra. 29,940 requests (7,485 per model), channels bare / chip / plain-word, prompts P0, P0c (turn in context), P0cb (M4 "background only" instruction). G1 guard re-run on chip outputs (6,152 outputs, ~0.03-0.13 extra calls per message).
- Labels: polarity by J1/J2 (agreement 99.1%, kappa 0.982, 16,033 units) plus blind arbiter on 145 disputed units (+22 for G1 outputs); 0 unresolved, no J1 fallback. Echo/reply: two sol prompt variants on 10,778 (turn, output) units; agreement 97.6% (echo), 99.1% (reply); disagreement counted as echo/reply (conservative).
- Nothing was sent to annotators; items and key built (288 items).

## Confirmatory contrasts (family cluster bootstrap 95% CI, 5,000 resamples; Holm over 3; pooled = mean of 4 models)
| contrast | pooled (pp) | per model qwen / llama / gemma / terra | rule verdict |
|---|---|---|---|
| C2 bare, X minus no-turn, share PROPOSITIONAL negation | **+8.7 [7.0, 10.6]**, Holm p<0.001 | +8.7 / +13.1 / +9.2 / +3.9 (all CIs exclude 0) | CONFIRMED, material (>=5 pp, 4/4 models) |
| C1 chip, [YES] cue, X minus no-turn, PROPOSITIONAL contradiction of the cue | **+1.2 [0.2, 2.2]**, Holm p=0.017 | +1.5 / +0.3 / +3.1 [1.3, 4.9] / 0.0 | detectable but negligible: whole CI inside +-5 pp (equivalent at the declared margin); not material |
| C3 bare, Q minus no-turn, share affirmative | **-6.0 [-8.3, -3.7]** | -10.8 / -6.2 / -5.4 / -1.5 | INCONCLUSIVE by the rule; direction is opposite to H3 (a question frame does not raise the default reading; it lowers it, mostly by induced abstention: unclear/mixed 13% qwen, 5% gemma, 2% terra; llama writes a negation 7%) |
Stop rule (C1 and C2 both null) NOT triggered because C2 is confirmed. The effect is much smaller than round 1 claimed.

## The key measurement finding: most "negation" after an X turn is echo
Bare input, all families, X turns (mean of 3 forms), intended-affirmative cells: ALL negated outputs vs PROPOSITIONAL ones (C2 all-negation pooled **+36.7 pp [32.6, 40.9]**, vs **+8.7** propositional). Per model negated outputs by kind (r2_decomp.csv): qwen 44% total of which echo 35% / propositional 8.7%; llama 45% / 31% echo / 14%; gemma 40% / 30% / 9%; terra 19% / 14% / 4%. By form, propositional share: Xa +4.6 pp, Xb +12.5, Xc +9.0 pooled (r2_contrasts.csv); Xa (explicit "not") is mostly echo, Xb (implicit "failed") is more often re-expressed. With the cue supplied the chip breaks echo almost completely: negated outputs 2-14% of cells, of which propositional 0-4%; counting echo/reply as harm gives an upper bound of **+7.1 pp [5.2, 9.0]** (round 1 reported 12-54% on a fixed template). Lexical re-implementation of the echo rule agrees on the verdicts (C2 +9.7 [7.8, 11.7]; C1 +1.0 [-0.1, 1.9]); judge vs lexical licensed-flag agreement 72-93% per model/channel (r2_lex_sens.csv).
Robustness: author-independence: on the 40 shared families, C2 propositional is +9.8 [6.7, 13.3] with mistral-authored turns and +4.8 [2.9, 6.9] with qwen14-authored turns (same sign, smaller); C1 +1.25 in both. Per-protocol (checker-passing turns only): C2 +6.6 [4.5, 8.8], C1 +1.2 [-0.1, 2.3]. D turns: no effect on bare (-0.6 [-1.7, 0.6]) or against a [NOT] cue (+0.4 [-1.4, 2.1]).
Mitigation M4 (background-only instruction): C2 falls from +8.7 to +4.3 [3.1, 5.6] (terra -0.5); C1 under M4 +0.3 [-0.5, 0.9].

## Benchmarks on the same items (r2_policies.csv, r2_policy_contrasts.csv; reversals per 1,000 = committed wrong polarity; SLP weighted = x5; q = share of X-frame messages whose intent contradicts the remark; no prevalence claim)
X-frame messages, q = 0.10 (pooled 4 models; "wrong_all" counts echoes, because the user would receive them):
| policy | taps / 1,000 | wrong polarity / 1,000 [95% CI] | weighted (x5) | wrong, excl. echo/reply |
|---|---|---|---|---|
| ignore partner (no-turn bare) | 0 | 892 [884, 898] | 4,459 | 892 |
| always commit with context (M0, Cai-style) | 0 | 575 [541, 607] | 2,874 | 495 |
| M4 instruction, bare | 0 | 777 [757, 797] | 3,886 | 745 |
| M5a fall back to no-turn output | 0 | 892 | 4,459 | 840 |
| M5b ask when turn changes the output | 402 | 544 [506, 581] | 2,718 | 486 |
| random-ask at matched taps (402) | 402 | 362 [343, 382] | 1,812 | 310 |
| plain word cue (M1) | 1,000 | 19 [13, 26] | 96 | 4 |
| chip = always-ask (M2) | 1,000 | 21 [14, 28] | 104 | 10 |
| M4 + chip | 1,000 | 13 [8, 20] | 66 | 10 |
| chip + guard G1 | 1,000 | **5 [3, 8]** | **26** | 2 |
Read carefully: (i) For users who supply NO cue, the high "wrong" counts are mostly the cost of the default itself (intent is negated in 90% of these messages at q=0.1 and bare output cannot know it). Always-commit with context beats ignoring the partner by -317 [-348, -285] per 1,000, and still beats it at q=0.5 (-13 [-19, -7]); this reproduces the Cai-type benefit and is a near-identity (bare output is intent-independent), not a discovery. (ii) The mitigations that keep zero taps do NOT help: M4-bare and M5a are worse than plain context (they remove the benefit; M4-bare +202 [179, 225] vs M0), and M5b does not beat random-ask at matched taps (+181 [164, 199] worse). (iii) Supplying the cue is what removes the reversals (-554 [-589, -520] vs commit; weighted -2,770), at 1 tap per message, and the guard adds a further -15 [-22, -10] per 1,000 (weighted -77) over the plain chip for about 0.1 extra model call per message; plain word is statistically indistinguishable from the chip (-1.5 [-8.5, 5.1]). M4 + chip: -7 [-14, -1] vs chip. The same ordering holds at q=0.3 and 0.5 (G1 vs chip -25 and -34 per 1,000). (iv) In the D-frame partner remarks change almost nothing (all policies within noise), and in the Q-frame (p(negated)=2.7%) always-commit context adds +13 [3, 24] wrong per 1,000 vs ignoring context (weighted +67) with 50 per 1,000 uncommitted (question-like outputs).
Per-model table: r2_policies_by_model_X_q10.csv (terra is the least echo-prone: chip+commit 8 wrong per 1,000, M4+chip 0).

## Where this does not help / limits
- The contamination of a SUPPLIED cue is small (about 1 pp propositional; 7 pp if echoes and agreement replies are counted). The strong round-1 headline (12-54% override) is withdrawn. Whether echoes/agreement replies are harm is a human-validity question (Part A/B of the request).
- The bare-channel effect (+8.7 pp propositional) is real but partly one-sided by construction: it is a benefit when the user intended the negation. No prevalence q is measured; q* (always-commit vs ignore) is above 0.5 in this metric.
- Zero-tap fixes (M4, M5a, M5b) are not credited: M5b fails to beat random-ask. Only cue supply (chip/word) and G1 help, and G1 is blind on bare input.
- Echo-vs-propositional is a machine label (two sol prompts, conservative union); judge-vs-lexical agreement only 72-93%. Xb turns largely failed their own lexical rule (ITT keeps them). Turns are model-authored templates, not natural dialogue; polarity only; one draw (terra not exactly reproducible); arbiter rules written at viewing; no writer-cluster check.

- Example check (r2_examples.json, rule: first by family id per model, bare|Xa, negated, one per machine class): the machine "propositional" class includes paraphrases that still carry the partner's claim (e.g. partner "Not the best fit for travel, are they?" -> "These headphones aren't good for travel."), and the echo class can include near-copies the user might plausibly intend. So "propositional" means "not a wording echo", not "independent of the partner"; C2 propositional (+8.7 pp) is therefore best read as partner-driven negation that is not verbatim copying, and may still be an upper bound on genuinely independent errors. The human Part A check is needed before any harm claim.

## Literature (opened pages only; claims limited to what was read)
- Cai et al., NAACL 2022 (arXiv 2205.03767): one prior conversation turn more than doubles abbreviation-expansion accuracy; aggregate accuracy only, no commitment attribution. M0 here is that context-in-prompt condition.
- Camassa & Shiller, arXiv 2605.20382 (May 2026): instruction vs pattern-in-context conflict; models drift toward the context pattern, onset varies by model. Zhou et al., arXiv 2407.13048: instruction > context > parametric knowledge hierarchy; vanilla instruction-tuned models prefer context over instruction. Farahani et al., arXiv 2601.12075 (EMNLP 2026): copying from context is easier to induce than recall. Braun, arXiv 2509.08480 (from round 1): LLMs lean to "no".
- Search for "copy from context / instruction-context conflict" found general-LLM work; none of the opened papers is on AAC partner turns, commitment attribution or echo vs propositional. The M4 instruction is our implementation of an instruction-conflict mitigation, not a published AAC method. Novelty: still "not found", not proven.

## Artifacts
analysis/frontier/partner_context/: round2.md, r2_summary.json, r2_contrasts.csv, r2_decomp.csv, r2_policies.csv, r2_policy_contrasts.csv, r2_policies_by_model_X_q10.csv, r2_author_subset.csv, r2_lex_sens.csv, r2_fig_echo_and_frontier.png, turns2*.jsonl, checker2_*.jsonl, turns2_meta_*.json, items_r2.jsonl, echo_labels.jsonl, echo_cache.jsonl, ANNOTATION_REQUEST.md (revised), PLAN.md (A3-A9). annotation/frontier_partner_context_r2_{items.json,key.csv}. runs/frontier_partner_context_r2, _r2g, _req/r2.jsonl. src/frontier_partner_context_{templates2,stage0b,build2,echo,guard,analyze2,annot2}.py and the .sh drivers.
Examples (rule: first by family id with a negated label, bare|Xa, per model): see r2_examples.json.
