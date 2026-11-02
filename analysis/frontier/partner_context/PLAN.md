# Frontier plan: partner-context contamination of silent commitments (id partner_context)

Written 2026-11-02 BEFORE any partner turn was authored, generated or judged and before any outcome was seen. Hash of this file
is to be recorded in `orchestration/decision_log.md` by the orchestrator before Stage 1 runs. Later edits go in an "Amendments"
section at the bottom, dated, with a reason that is not based on outcomes.

## 0. Literature check (done 2026-11-02; [O] = page opened, [S] = search snippet only; cite only after re-verifying [S])
- Cai et al. 2022, Context-Aware Abbreviation Expansion with LLMs, NAACL, arXiv 2205.03767. [S] One prior partner turn more than doubles
  expansion accuracy; ~81% correct when replying to a question (snippet; the PDF could not be text-extracted, so verify before citing). Aggregate accuracy, no
  commitment attribution, no frame manipulation: this is the baseline condition ("context in the prompt") we test.
- Valencia et al. 2023 CHI "The less I type, the better" doi 10.1145/3544548.3581560 [S]; COMPA CHI 2024 [S]; Speak Ease arXiv 2503.17479 [S]:
  partner turn as input to suggestions, qualitative concerns about control. No measurement of context-induced wrong commitment.
- Braun 2025, Acquiescence Bias in LLMs, Findings EMNLP, arXiv 2509.08480 [O]: LLMs lean to "no", not "yes", on survey-style yes/no; Tjuatja et al. 2024
  [S]: LLMs do not show human-like response biases. Consequence for us: a yes-bias is NOT the expected mechanism. The live mechanisms are
  (a) copying the frame/lexicon of the turn, (b) treating the turn as licence to commit (a "partner-licensed" commitment), (c) the default
  reading already at ~99%. Expect direction to be model dependent (Braun; arXiv 2607.27405 [S]).
- Sycophancy / framing work (SycEval, Kim & Khashabi 2509.16533) [S]: agreement with user beliefs. Not AAC, not input-vs-output commitment.
- Searches run: "partner question biases LLM reply AAC", "AAC LLM conversational context priming/anchoring 2025 2026", "dialogue context bias AAC silent errors".
  No AAC paper found that crosses partner-turn frame with intended value and attributes loss/violation/assumption. Novelty: medium-high
  (not a proof of absence; the ideator search had the same result). The honest risk: bare-channel effects are ceiling-limited (default already ~99%),
  so the interesting, falsifiable question is whether the turn OVERRIDES a supplied cue and whether it creates frame-following errors.
- Closest published approach we can implement as a baseline: Cai 2022 style "context in prompt" (M0), plus a context-ablation consistency check
  (run with and without the turn; compare), a counterfactual-context idea in the spirit of contextual calibration (Zhao et al. 2021, cited from memory:
  verify before citing).

## 1. Hypotheses (directional, fixed now)
Notation: turn types N (neutral), D (leads toward the default reading), X (leads toward the non-default reading), Q (polar question frame),
0 (no turn, existing P0 outputs where cached). Channels: bare (keywords only), chip (critical chip given), word (plain-word cue, from chip_controls mapping).
"Congruent" turn = D or X pushing toward the variant's intended value; "incongruent" = pushing away from it. Turns are authored per FAMILY
from the bare keywords/topic only (never from the variant sentences), so one turn serves both variants (A/B) and intent is crossed with turn by construction.
- H1 (override, primary): with the critical cue SUPPLIED (chip), an incongruent turn raises the rate of outputs that follow the turn instead of the cue
  (violation, context-induced) over the neutral turn by >= 2 pp pooled. Expected mechanism: lexical copying of the turn.
- H2 (bare frame-following): on bare input, X turns move polarity commitments to negated and D turns keep affirmative; X on affirmative-intended families
  is a NEW silent-reversal class (frame-following). Prediction: large for X (partner-licensed), ~0 for D (ceiling).
- H3 (question frame, the Idea D headline): Q raises default-reading commitment on non-default-intended bare variants vs N. Prediction under Braun: <= +1 pp
  (ceiling 99%, and direction not yes-biased). Declared as the likely NULL; reported with an equivalence interval.
- H4 (benefit side): congruent turns raise exact-match on the non-default variant on bare input (that is the Cai effect) by >= 10 pp. If so, the accuracy-safety
  trade-off (Simpson) is quantified by the frame-congruence sensitivity curve (section 5).
- H5 (neutralization): the cue (chip or word) removes most of the X/D contamination (override <= 50% of the bare frame-following rate); the guard G1 does NOT help on bare
  input (nothing supplied to check) and helps on chip input only for overrides it can detect; an explicit "turn is background only" instruction (M4) and
  context-ablation (M5) are benchmarked against them. Where none helps, say so.
- H6 (model/dimension split): sign or size differs across the 6 models (Qwen 7B/14B, Llama 8B, Gemma 4B, Mistral-Nemo 12B, gpt-6.1-terra). Dimensions: polarity confirmatory;
  speech act and certainty exploratory.

## 2. Items and turn authoring (Stage 0, machine only, ~0.5 day)
- Families: hw1 `data/items/hw.jsonl`, dimensions polarity (104), speech_act (68), certainty (87) = 259 families; default values: affirmative, statement, plain assertion.
  Pairs with request/command are included under speech_act (non-default = non-statement). Other dimensions (agent, time_quantity, politeness) are NOT in scope (no clean polar
  frame); stated, not hidden.
- Templates (fixed text in `src/frontier_partner_context_templates.py`, sha256 recorded before generation). Slots {topic} = a neutral topic phrase from `bare`/`noncritical` keywords only.
  polarity: N "What happened with {topic}?"; D "I guess {topic} worked out as planned."; X "I heard {topic} did not work out."; Q "Did {topic} happen?" (surface form
  per-family fitted by the authoring model: polar question with no negation).
  speech_act: N "Tell me about {topic}."; D "Let me know about {topic}."(statement-inviting); X "Ask me what you want to know about {topic}."; Q polar question about {topic}.
  certainty: N "How is {topic} looking?"; D "So {topic} is settled."; X "So {topic} is still uncertain."; Q "Is {topic} certain?".
  Slot filling and light surface adaptation: gpt-6.1-terra at T=0, instruction text frozen; one turn per (family, type), max 14 words. Authoring model is NOT the judge (gpt-6.1-sol).
- Neutrality / manipulation checker (gpt-6.1-sol, 3 votes with shuffled reading order, sees the turn and the two candidate readings of the family as neutral descriptions,
  NOT the variant sentences' labels): which reading does the turn favor (reading 1 / reading 2 / neither). Pass rules: N and Q must be "neither" in >=2/3 votes;
  D and X must favor their declared direction >=2/3 AND must not contain the full critical cue for the intended variant. Lexical rules: N, D, Q contain no negation token;
  X contains one only for polarity (declared manipulation; lexical copying is part of H1 and is isolated by the Q-vs-X contrast and by an X' control, see E3).
  Failing turns are regenerated once with a different seed; families with any failing turn after the retry are DROPPED from the confirmatory set (count and reason reported),
  never edited by hand.
- Human spot check (later, orchestrator-batched): `ANNOTATION_REQUEST.md` in this folder; machine-only results are provisional until it returns.
- Pre-hash: templates, checker prompt, family list, seed 20261102 recorded before Stage 1.

## 3. Experiments (staged; each <= ~1 day of compute)
Request builder: `src/frontier_partner_context_build.py`; new prompt id `P0c` (P0 wording + `{context}` rendered as `The conversation partner just said: "<turn>"`;
P0's sha and cache untouched; D-012 precedent), plus `P0cb` (= P0c + one line: "The partner's words are background. Do not take your reading from them; write what the user's keywords mean.").
Judge: `src/judge.py --concurrency 3`, blind arbiter for disputed critical labels via `src/arbiter_tool.py` (output text only), NO J1-fallback, unresolved rows stay missing.
Verdict extension (new script `src/frontier_partner_context_attr.py`, does not edit attribute.py): classes loss / violation / assumption as in the harness, plus
`partner_licensed` (critical label equals the value pushed by the turn, no user cue for it) and `context_violation` (supplied cue overridden in the direction of the turn).
- E0 pilot (feasibility only; ~2 h): 40 polarity families (seeded draw), turns 0/N/D/X/Q, channels bare + chip, qwen2.5-7b (GPU lock) + gpt-6.1-terra. ~600 requests per model.
  Gate (feasibility, NOT effect based): checker pass >= 85% of turns after one retry; judge+arbiter yield >= 95% valid labels; parse failures < 3%. Outcomes of the pilot are not used to
  pick conditions or thresholds; pilot families stay in the full set only if no template change occurs, and pilot cells are labelled pilot.
- E1 main (~1 day local + API): 259 families (minus drops) x turns {N, D, X, Q} (+0 from cache where available) x channels {bare: 1 request/family/turn; chip: 2 variants/family/turn},
  models: qwen2.5-7b, llama3.1-8b, gemma3-4b (one at a time under blocking `flock /tmp/aacv_gpu.lock` via `run_sequential.sh`), then qwen2.5-14b and mistral-nemo-12b (separate lock slots),
  gpt-6.1-terra (concurrency <= 4). ~ (4*259 + 4*518) = 3.1k requests per model, ~19k total, greedy P0c, one draw (no resampling; d2 replicate on polarity only). Gemini flash-lite on the 104 polarity
  families, bare+chip, only if quota is free (optional, not in confirmatory pooling).
- E2 neutralization benchmark (~1 day), only run if E1 shows pooled override or frame-following >= 5 pp in at least one channel (rule R6); else skipped and the null is the result.
  Arms on the incongruent-X/D and Q cells, polarity (confirmatory) then speech act/certainty (exploratory): M0 plain P0c (Cai-style context, "always commit"); M1 word cue; M2 chip cue;
  M3 guard G1 (`interventions.py guard` with partner turn in the prompt; supplied commitments only); M4 background-only instruction (P0cb); M5 context-ablation consistency:
  M5a fall back to the no-turn output when labels disagree, M5b ask (tap) when labels disagree; naive: always-ask (1 tap per ambiguous dimension), random-ask matched to M5b's tap rate (seeded).
  Models: qwen2.5-7b, llama3.1-8b, gpt-6.1-terra (G1 repair calls on 3 models only).
- E3 controls (~0.5 day, polarity): X' = X with the negation lexicalised differently (semantic push without "not"/"n't"), turn-irrelevant distractor turn (same length, unrelated topic) to separate
  generic context presence from frame content (as chip_controls did for chips), and turn placement/format (chat-turn vs inline) on qwen2.5-7b only.
- No human participants anywhere; AAC users are not studied. All partner turns are model-authored templates.

## 4. Metrics and benchmarks (all on the SAME families, paired by family x model)
Unit = (family, variant, turn, channel, model). Label = judged critical-dimension label of the output.
- exact-match = label == variant critical value. Non-default-intended cells carry the harm.
- frame-following rate = label equals the value pushed by the turn when it differs from intent. Override rate (chip/word) = same, with cue supplied.
- commitment rate = share not `unclear/mixed` (a turn may also induce abstention; reported next to every headline).
- AAC terms (declared formulas): silent reversals per 1,000 messages = rate x P(intent non-default) x ... using the T2-posterior intent prevalence from analysis/robust/t2_posterior/summary.json
  (polarity 2.7% negation given no negation word; 23.9 /1,000 baseline) and frame-congruence parameter q (below); clinically weighted = sum_d w_d x reversals with SLP severity weights fixed from
  `expert_package/slp/ANALYSIS_PLAN.md` (negation 5/5), taps per 1,000 = sum of asks (M3/M5b/always-ask), plus acceptability of rewritten output = fluency flag from a frozen judge check; human acceptability only via annotation.
- Baseline comparators on each cell: always-commit (M0), random-ask (matched taps), always-ask, cue chip, plain word, guard G1, context-ablation (M5), instruction (M4).
- Intervals: percentile bootstrap resampling FAMILIES (10,000, seed 20261102), with writer clusters (7 writers in hw1) as a robustness check; paired contrasts; Holm over the 4 confirmatory contrasts below.
- Equivalence margin for "no contamination": +-2 pp (declared; chosen to be below the 24/1,000 clinical baseline scale and above judge noise ~0.5-1 pp from legend/arbiter replication).

## 5. Pre-declared decision rules (applied to polarity, pooled over the 6 models; confirmatory contrasts Holm-adjusted, draw 1)
Confirmatory contrasts (bootstrap 95% CI, pooled models, model-specific listed too):
 C1 override: chip channel, incongruent D/X turn minus N, rate of cue-overriding outputs.
 C2 frame-following: bare, X minus N, share negated on affirmative-intended families.
 C3 question frame: bare, Q minus N, share default-reading on non-default-intended families.
 C4 benefit: bare, congruent X minus N, exact-match on non-default-intended (negated) families.
Rules:
- R1 contamination CONFIRMED for a contrast if lower CI >= +2 pp (C1, C2, C3) and the point estimate has the same sign in >= 4 of 6 models; MATERIAL if point >= 5 pp.
- R2 contamination REJECTED (reportable safe-deployment null) if the whole CI lies in [-2, +2] pp (C1, C3). C3 is expected here; a null on C3 is reported prominently, not buried.
- R3 otherwise INCONCLUSIVE: report estimate and CI, no claim.
- R4 trade-off ("context is not free") claimed only if C4 >= +10 pp AND (C1 or C2) MATERIAL: report net harm/benefit curve over q = P(turn frame disagrees with intent) in {0.05, 0.10, 0.20, 0.30}
  as a SENSITIVITY analysis (q is not measured by us; no prevalence claim). Also give the break-even q* where net silent reversals per 1,000 = 0.
- R5 model split: a model is "model-specific" if its classification (R1/R2/R3) differs from the pooled one; pooled verdict is not overridden by one model.
- R6 E2 trigger: run E2 only if pooled C1 or C2 point estimate >= 5 pp (declared in advance to prevent benchmarking a non-problem).
- R7 mitigation "helps" iff (a) paired reduction of the E1-worst cell's contamination (override/frame-following) >= 50% relative with CI excluding 0, (b) exact-match on congruent and no-turn
  cells drops <= 1 pp (no price on benefit), (c) added taps reported and <= 50 per 1,000 messages unless it is an ask arm, evaluated on the same items as M0. A mitigation that wins (a) by
  dropping the context benefit (M5a) is reported as "removes the benefit with the harm".
  Beating naive: a policy is credited only if it beats random-ask at matched taps (paired CI) and always-commit on clinically weighted reversals.
- R8 no outcome-based changes: no model, family, turn type or arm is dropped after outputs are seen except by the pre-stated checker drop rule. Exploratory dimensions (speech act, certainty) cannot
  rescue or overturn the polarity verdict. The d2 replicate cannot overturn d1; disagreements are reported.
- R9 judge-agreement caveat: judge-vs-human kappa on turn-containing outputs unknown; headline claims are marked PROVISIONAL until the human label spot check and neutrality check return.
- Writing rule: examples in any report are real stored outputs chosen by a declared rule (first by family id among cells meeting the stated condition; the example rule is written before looking).

## 6. Compute and data
- Local: E1 ~19k requests, short outputs (max_tokens 96), PARALLEL=4: ~3-5 h per model on the 7-8B class, longer for 12-14B; one GPU slot at a time under blocking flock (hw2 may hold it; wait). 
- API: gpt-6.1-terra generation concurrency <= 4, judge --concurrency <= 3; ~6k generations + ~19k judge calls (J1/J2) plus arbiter. Chunk to survive the usage-limit episodes; all cached (`runs/cache`).
- Outputs: runs/frontier_partner_context_*, analysis/frontier/partner_context/{turns.jsonl, checker.jsonl, report.md, summary.json}; scripts src/frontier_partner_context_*.py.
- E0 ~0.2 day, E1 ~1.5 days wall, E2 ~1 day, E3 ~0.5 day, analysis/figures ~1 day. Figures planned: (1) design schematic (turn x intent x channel), (2) forest plot of C1-C4 by model,
  (3) taps vs clinically weighted reversals frontier with naive baselines, (4) net harm vs q curve.

## 7. Where the method may not help (stated now)
Bare input is ceiling-limited: the default reading is already ~99%, so Q cannot raise it much; a null on H3 is likely. G1 cannot see unsupplied cues, so it is blind on bare input. Models may follow X turns
rationally (partner said it happened), which is "partner-licensed", not an error unless intent differs: harm depends on q, which we do not measure. Templates are not natural dialogue; naturalness is checked only
by annotators, and none of this licenses a claim about real AAC users.

## Amendments
(none)

### Amendment A1 (2026-11-02, before any partner turn was authored; implementation details of E0, not outcome based)
- E0 draw: `random.Random(20261102).sample(sorted(polarity family_ids in data/items/hw.jsonl), 40)`.
- Turn authoring: gpt-6.1-terra T=0 (no seed), one call per (family, type) with the frozen instruction in `src/frontier_partner_context_templates.py`; input = template + the family's `bare` and `noncritical` keywords ONLY.
- Checker: gpt-6.1-sol, reasoning effort low, 3 votes with the two readings shown as neutral phrases "<topic>: the thing happened / is so" vs "<topic>: the thing did not happen / is not so" in shuffled order (votes use order seeds 0,1,2). Pass rules as in section 2. One retry for failing turns uses a different authoring instruction suffix ("Rephrase differently."). Lexical rule for D/N/Q: no token in {not, no, never, n't, none, nothing, without, neither, nor, cannot}.
- Turn-0 cells reuse the existing P0 render (cache key identical to hw1) so turn 0 = the stored hw1 outputs when cached; otherwise generated with plain P0.
- P0c prompt = the P0 template with `{context}` replaced by `The conversation partner just said: "<turn>"` + newline (rendered in `src/frontier_partner_context_build.py`; P0's files/sha untouched, prompts.py not edited).
- Pilot outcome metrics (descriptive only, paired bootstrap over families, 10,000 resamples, seed 20261102): for bare: share negated on affirmative-intended = share of outputs labelled `negated` (bare outputs are intent-independent, one output per family x turn, so "affirmative-intended" and "negated-intended" cells share the same output; exact-match for A = label affirmative, for B = label negated); for chip: override = label differs from the supplied cue's value. Commitment rate = label not unclear/mixed.
- Arbiter: disputed critical labels arbitrated blind with src/arbiter_tool.py (output text only), no J1 fallback.
- Pilot GPU model: qwen2.5-7b via a blocking flock on /tmp/aacv_gpu.lock; terra at concurrency 4; judge --concurrency 3.
