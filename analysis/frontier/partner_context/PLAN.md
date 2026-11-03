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

### Amendment A2 (2026-11-02, after the first Stage 0 checker run, BEFORE any model-under-test output was generated or seen)
- Stage 0 v1 FAILED the feasibility gate: checker pass 80% after retry (gate >= 85%); N passed only 40%, X 82.5%, D 100%, Q 97.5% (files kept in `v1_failed_gate/`).
  Diagnosis from the checker votes only: (a) template N "What happened with {topic}?" presupposes that something happened and was voted "affirmative" in 45/50 attempts that failed; (b) the reading descriptions
  ("the thing happened / is so") were ambiguous for noun-phrase topics, so X turns such as "...did not work out" were voted affirmative for some topics.
- Changes (design defects, not outcome based): N template -> "What about {topic}?"; checker readings reworded to be about the sentence the user will say: "the user's sentence will say that <kw> is so / happened (an affirmative sentence)" vs
  "... will say that <kw> is not so / did not happen (a negated sentence)". D, X, Q templates and all pass rules unchanged. The whole Stage 0 is rerun (same 40 families, same draw); v1 is reported as a failed first attempt, not hidden.
- If v2 still misses the gate, E0 proceeds only on passing families (the pre-stated drop rule) and the gate failure is reported.

## Decisions

### Decision D-R1 (2026-11-02, director, after round 1 of 3; post-pilot, outcome-informed, labelled as such)
Verdict: CONTINUE, but the headline is withdrawn. E0 supports feasibility only (1040 rows, 0 parse failures, J1/J2 98.5%). The "override" claim and the AAC conversion (120-540 per 1,000) are NOT reportable: the critic showed most terra/qwen "negations" are echoes of the template phrase "did not work out" (12/14 terra chip overrides, 3/3 qwen; qwen bare 18/20), only about 2/26 are propositional negations. Stop condition for later rounds: if echo-corrected effects are indistinguishable from zero in round 2, report a null/feasibility paper section and stop.

Round 2 instructions (post-pilot amendments A3+, each dated before any new outputs are generated; E0 families do NOT enter confirmatory E1):
1. Fix measurement first. Add an echo/copy label to the judge pipeline, declared before generation: a negated output is "echo" if it reuses the turn's negated phrase (lexical overlap of the negation-bearing span) and "propositional" otherwise. Primary outcome = propositional negation only; echo is reported separately. Rewrite X turns with N varied paraphrases (at least 3 negation surface forms per family, none a fixed phrase) so echo cannot be a single template token.
2. Declare chip semantics and an agreement-reply rule BEFORE E1: with a [YES]/[NOT] cue, a reply that agrees with the partner's remark while remaining consistent with the cue's intent is not an override. Override is defined only against a cue-contradicting intended proposition, and cells where "Yes, X did not work out" is a licensed agreement (X/[YES], D/[NOT]) are labelled partner-licensed and excluded from harm counts. Do not convert to silent reversals per 1,000 unless a stated prevalence q is supplied; present only a sensitivity curve over q, with the same denominator as the baseline.
3. Baseline: replace N with the no-turn arm (0) as the reference, with a dated post-pilot amendment; drop C4 as redundant with C2 on bare and adjust Holm to the true number of independent contrasts. Q turns must be topic-locked (checker rule: same topic noun phrase, no new entities), so C3 is not confounded by topic drift. Report Q against 0 only.
4. Authoring/judging independence: author turns with a different model family than the checker/judge (not terra author with sol checker/judge on the same family), and include at least one local model (qwen2.5-7b or gemma3-4b) as author for a robustness subset. Re-draw families with a new seed; keep N-turn failures reported, and analyse all families (not the survivor subset) by dropping N as a baseline.
5. Power: pilot n=26 gives CIs of one-family granularity (3.8 pp) and degenerate bootstraps. Use at least 120 families, cluster bootstrap with BCa or exact paired tests, and a >=5 pp equivalence margin; do not claim equivalence below that.
6. Benchmarks required in E1 on the same items: always-commit, random-ask at matched taps, always-ask, plain-word, G1, and the closest implementable published approach (instruction-conflict/context-copying mitigation, e.g. an explicit "ignore the partner's wording" prompt as M4/M5). Report weighted reversals (SLP negation weight 5), taps per 1,000, and where the method does not help.
7. Novelty: re-run a literature search on echo/copy-from-context and instruction-vs-context conflict before any novelty claim; cite only opened sources.
8. Annotation: send nothing now; the ANNOTATION_REQUEST.md should be revised to cover a human check of echo vs propositional labels (about 150 stratified outputs) and chip-semantics agreement-reply judgments, to be batched by the orchestrator.

### Amendment A3 (2026-11-02, round 2, post-pilot and outcome-informed by round 1/critic; written BEFORE any round-2 turn was authored or generated)
Reason: D-R1. The round-1 headline was dominated by echo of the template phrase "did not work out". Round 2 is a clean re-run (E0 families excluded) with a measurement fix. Round-1 numbers are not reused.
1. Echo vs propositional (primary outcome change). For every output generated in a turn cell, two blind-to-intent judge prompts (EJ1/EJ2, gpt-6.1-sol, effort low, reversed option order) see ONLY the partner turn and the output (not channel, cue, model, intent) and answer:
   (a) ECHO = yes if the output re-uses the turn's value-bearing wording (the negation-bearing or "worked out/failed/..." span, verbatim or near-verbatim paraphrase) instead of expressing the user's own statement about the keywords' event;
   (b) REPLY = yes if the output answers or acknowledges the partner (starts with yes/yeah/oh/right/I heard/I know/that is..., or is phrased as a response to the remark) rather than being the user's own message.
   Two-judge disagreement on either flag is resolved conservatively against the headline: unresolved = echo/reply "yes" (so PROPOSITIONAL requires both judges to agree on no/no). If fewer than ~60 disagreements per flag, I additionally arbitrate them blind (output + turn text only) as a sensitivity.
   PROPOSITIONAL negation (primary) = polarity label negated (J1/J2/arbiter; no J1 fallback) AND echo=no AND reply=no. Echo-negation and reply-negation are reported as separate columns. A lexical sensitivity rule is also computed: echo_lex = negated and (shares a contiguous word 3-gram with the turn or any turn-specific content token, i.e. not a keyword stem and not a stop word/hearsay verb); reply_lex = output starts with yes/yeah/oh/right/ah/really/i heard/i know or contains "heard". Judge-vs-lexical agreement is reported.
2. X turns: three negation surface forms per family, none a fixed phrase, authored per family: Xa explicit negation word (not/n't/never/no) in any syntax; Xb implicit lexical negative with NO negation token (failed, fell through, was cancelled, collapsed, ...); Xc quantifier/existential negation ("nobody", "nothing came of", "no sign of"). The phrase "work out" is forbidden. X contrast pools Xa,Xb,Xc (family-level mean of the three) so one family is one cluster; forms are reported separately.
3. Chip semantics (declared). [YES] cue = the user's intended message states the keywords' proposition affirmatively; [NOT] = states it negated. The cue is the user's intent. OVERRIDE/HARM in the chip channel = output polarity opposite to the cue AND propositional (echo=no, reply=no). A negated output after an X turn with [YES] that is an echo or an agreement reply ("Yes, X did not work out") is PARTNER-LICENSED: the cue-vs-partner conflict cells are X/[YES] and D/[NOT] (incongruent); they are labelled licensable at cell level, and harm counts only output-level propositional contradictions. Licensed outputs are reported separately and NOT counted as harm. Because every incongruent cell is licensable, the chip harm is identifiable only through the echo/reply labels; this is stated as a limit, and the human check (ANNOTATION_REQUEST.md, Part B) validates those labels. "Upper bound" harm (counting licensed outputs) is reported next to it.
4. No per-1,000 conversion without a stated prevalence. AAC conversion only as a sensitivity curve over q = P(turn frame disagrees with intent), q in {0.05, 0.10, 0.20, 0.30, 0.50}, same denominator for all policies (1,000 messages carrying a turn of that frame), plus the no-turn row (prevalence of negated intent 2.7%, declared in section 4).

### Amendment A4 (2026-11-02, before generation): baseline, contrasts, topic-lock
- The baseline is the NO-TURN arm 0 (plain P0, same family, same cue channel). N turns are dropped. Q is compared to 0 only. C4 is dropped (identical to C2 on bare).
- Confirmatory contrasts (3, Holm over 3): C1 chip harm: X-incongruent cells ([YES] cue, X turn) minus the same cue with no turn, propositional-contradiction rate; C2 bare: X minus 0, share PROPOSITIONAL negation; C3 bare: Q minus 0, share affirmative (default-reading), expected null. D-turn and [NOT]/D cells are exploratory.
- Q turn rule: polar question, no negation token, topic-locked: every content word of the question must come from the keyword list (any inflection) plus function words; an additional gpt-6.1-sol topic-lock check ("does the question mention any entity, place, person or topic not in the keyword list: yes/no", pass = no). Fail -> one retry -> kept in the ITT analysis flagged as failing the lock.
- Turn checker (gpt-6.1-sol, 3 votes, same reading wording as A2): D must favor affirmative, each X form must favor negated in >=2/3 votes, Q must be "neither" in >=2/3 votes plus the lock; plus lexical rules: D, Q contain no negation token; Xa contains one; Xb and Xc: Xb contains none of the negation tokens, Xc must contain no/nobody/nothing/none/never. One retry. Failing turns are NOT used to drop families: ITT analysis uses the final turn regardless (primary); per-protocol (only passing turns) is a sensitivity analysis. The failure rate per type is reported.

### Amendment A5 (2026-11-02, before generation): authoring independence, families, seeds
- Authoring model: mistral-nemo-12b (local, GPU lock; Mistral family: different from the checker/judge family (gpt) and not one of the models under test). Robustness subset: qwen2.5-14b authors turns for the first 40 families of the draw (by sorted id); reported as a separate column (note: Qwen family overlaps with qwen2.5-7b under test; read that column as author-independent of checker/judge only).
- Families: pool = polarity families of data/items/hw.jsonl NOT in the E0 draw (64) + data/items/r2_c1.jsonl polarity families (80) = 144; draw 130 with `random.Random(20261103).sample(sorted(pool_ids), 130)`. E0 families (40) excluded. Every drawn family is analysed.
- Models under test: qwen2.5-7b, llama3.1-8b, gemma3-4b (local, one server at a time under a blocking flock), gpt-6.1-terra (API, concurrency 4). Greedy, one draw (terra not exactly reproducible).
- Prompts: P0 (no turn), P0c (turn in context), P0cb (turn + "background only, do not take your reading from them" instruction = M4, our implementation of the instruction-conflict mitigation; there is no published AAC baseline for this exact mitigation, see literature section in round2.md).
- Channels per family and variant: bare (no cue), chip (the critical chip), word (the plain word "yes"/"not" from analysis/chip_controls/mapping.json). Turn types: 0, D, Xa, Xb, Xc, Q.

### Amendment A6 (2026-11-02, before generation): statistics
- Unit/cluster = family. Intervals: percentile cluster bootstrap over families (5,000 resamples, seed 20261103) on the pooled mean over the 4 models (model-level estimates computed on the same resampled families), model-specific CIs likewise; plus exact paired sign-flip permutation p-values (family-level mean difference, 20,000 flips; exact where feasible is infeasible at n=130 so the Monte-Carlo permutation with the stated seed is used) for Holm. Writer-cluster robustness for the hw families only if time.
- Equivalence margin +-5 pp (D-R1). Rules: CONFIRMED if Holm-adjusted p < 0.05, pooled point >= +5 pp (material) and the point estimate is positive in >= 3 of 4 models; EQUIVALENT/NULL if the whole 95% CI lies in [-5,+5] pp; else INCONCLUSIVE. Equivalence is never claimed from a CI wider than +-5.
- STOP RULE (D-R1): if the echo-corrected C1 and C2 are both not confirmed (CI contains 0 and point < 5 pp), round 2 is written as a null/feasibility section.

### Amendment A7 (2026-11-02, before generation): benchmarks and AAC metrics
Policies on identical cells (family x intended variant x turn x model), evaluated for each frame (X-frame: Xa/Xb/Xc pooled; D-frame; Q-frame):
 P0ctx always-commit = bare input + turn (P0c); Pnoctx = bare, turn dropped (arm 0; no context benefit, no harm); M1 plain word (word channel, 1 tap); M2 chip = always-ask (chip channel, 1 tap); M3 guard G1 (chip channel; interventions.py check/feedback/supplied, <=2 retries, extra model calls reported; blind on bare); M4 background-only instruction on bare (0 taps) and on chip (1 tap); M5a context-ablation consistency: if label(bare|turn) differs from label(bare|0) use the arm-0 output; M5b: if they differ, ask (cue supplied output chip|turn, 1 tap); random-ask matched to M5b's tap rate per model and frame (expected value, exact); always-ask (= M2).
Metrics per policy: committed-wrong-polarity rate by intent (two versions: all, and propositional-only i.e. excluding echo/reply outputs), uncommitted rate, taps; silent polarity reversals per 1,000 messages and SLP-weighted (negation weight 5; both reversal directions weighted 5 as polarity) as a function of q for the X-frame (intent affirmative with prob q) and the D-frame (intent negated with prob q); no-turn row at p(negated)=0.027. Acceptability: fluency/added-content is NOT judged here; human acceptability only via annotation. A policy is credited only if it beats random-ask at matched taps (paired family-bootstrap CI excluding 0) and always-commit on weighted reversals; reported "where it does not help" explicitly. The cost of silence about uncommitted outputs: the abstention rate is reported next to every headline.

### Amendment A8 (2026-11-02, before generation): echo-judge scope and execution details
- To bound API load the echo/reply judges (A3.1) are applied to every output in a turn cell (turn != 0) whose resolved polarity label is "negated", plus every output in D-turn cells and every output whose cue is [NOT] (the cells where an affirmative output can be the wrong one). Outputs outside that scope are not echo-judged and are never counted as harm or as propositional negation. Units are (turn text, output text); judge calls are batched 10 units per call.
- M4 (P0cb) is generated for bare and chip cells of every turn type; the word channel only with P0c. The author-subset (qwen2.5-14b turns, "q14Xa/Xb/Xc") is generated for bare and chip only with P0c.
- G1 is run on the chip|turn P0c outputs with a local reimplementation using interventions.supplied/check/feedback (the stock guard driver re-renders P0 prompts and cannot reproduce P0c keys); retries <= 2; the retry conversation includes the partner turn (it is part of the prompt).
- Generation concurrency: terra API_CONC=4; judge --concurrency 3. Polarity labels: J1/J2/blind arbiter (Claude, output text only); no J1 fallback.

### Amendment A9 (2026-11-03, written after outcomes were seen; deviations log, not a design change)
- Execution: the stock run_sequential.sh terra branch was killed (shared-endpoint slowness) and terra was re-run from the shared request cache in two files (core: P0/P0c; then M4 P0cb); results are identical in kind (requests keyed by prompt hash). Judge ran on one assembled run (frontier_partner_context_r2); G1 outputs were judged in frontier_partner_context_r2g.
- Arbiter: 143 A-units (r2) and 22 (r2g) were labelled by me (Claude) blind (output text only). Decision rules were written when viewing (same as round 1), stored in the arbiter_decisions.tsv rationale: questions/fragments/leaked chips -> unclear/mixed; mental-state frames with embedded negation (understand/respect/read/know) and "I don't know" -> unclear/mixed; communicative frames (tell/want to tell) take the content polarity; corrective "X, not Y" -> affirmative. The 22 r2g items used the same rule except that I three times labelled "I don't know"-type items differently before the rule was written down (only r2 uses the final rule; 3 r2g items were not re-labelled). No outcome was consulted.
- Turn checker: Xb passed only 39% after retry because its lexical rule (no negation token) rejects "didn't materialize"; ITT analysis includes all families (A4), PP is a sensitivity.
- Bootstrap B=5000 and Monte-Carlo sign-flip permutation (20,000) as in A6; writer-cluster robustness not run. The pooled estimate is the mean of the four model-level estimates.
- Policy analysis uses committed-wrong-polarity (wrong_all; unclear/mixed = abstention reported separately) and wrong_prop (excludes echo/reply). For arms 0 the echo flag is undefined so wrong_prop = wrong_all.
- C1/C2 verdict labels come from the declared code: C1 pooled is flagged "EQUIVALENT within +-5 pp" although its CI excludes 0 (Holm p = 0.017); read as "detectable but negligible".

### Decision D-R2 (2026-11-03, director, after round 2 of 3; post-pilot, outcome-informed, labelled as such)
**CONTINUE to round 3 (final), narrowly scoped. No new generation sweeps; machine-only re-analysis plus the human check. The result is already publishable as a "bounded, mostly negative/benchmarking" finding, so round 3 is about claim hygiene, not new effects.**

Round-3 instructions (fix major issues first):
1. C1 restatement. Report the UNFILTERED echo/agreement-as-harm estimate (+7.1 pp [5.2, 9.0]) as the primary C1 number and the filtered +1.2 [0.2, 2.2] as a lower bound. Remove the word "equivalent/negligible" from all text and from the code-emitted verdict label (A9 flagged label); state that the margin was widened from +-2 to +-5 post-pilot and that the filtered CI fails the original +-2 margin. Apply the same echo filter symmetrically to arm 0 (run the echo/reply judge on arm-0 outputs in the same scope) and report C1 both ways; if arm 0 filtering is not feasible, say so and treat the filtered number as unvalidated.
2. C2 decomposition. Re-label the 142 propositional X negations (and a matched random sample of 60 affirmative-cell outputs as control) into paraphrase-of-partner / fabrication / partner-independent using the existing machine judge, report counts by turn type (Xa/Xb/Xc), and show the Xb-vs-lexical-form confound (re-run C2 restricted to checker-passing Xa/Xc). Headline C2 as a range: +8.7 propositional, +36.7 including echo; state that licensed agreement vs harm awaits the human check.
3. Author dependence. Report C2 as author-specific (+9.8 mistral-authored vs +4.8 qwen14-authored on the 40 shared families); add a writer-cluster sensitivity (resample families within author and model weights equal vs by n) and give the pooled CI as conservative (min over author subsets). No new turns authored.
4. Benchmark honesty. Relabel chip, word, M4+chip and chip+G1 as cue-supplied oracle upper bounds, not mitigations of the partner effect; state the X-frame benchmark is near-definitional at q=0.1 and extend the q grid to 0.9 (analysis only). Add two cheap stronger selective-ask baselines computed from existing outputs, with no new generation: (a) negation-frame gate (ask iff turn contains negation/contrast cue), (b) logprob/entropy gate on the local qwen/llama runs only if logprobs already stored; credit only if it beats matched-tap random-ask. Note G1 shares the gpt family with the judges and report the arbiter-only (Claude) subset G1 vs chip contrast on the labelled units.
5. C3. Reword: the Q frame lowers the affirmative share via abstention (unclear 13% qwen); H3 is "unsupported", not "reversed". Report the non-abstained affirmative share alongside.
6. Human check: finalize ANNOTATION_REQUEST.md Part A (paraphrase/fabrication/licensed-agreement for ~150 X-negation outputs + 50 controls) and Part B (echo/reply filter validity, ~100 units stratified by judge decision, both arms). ~20 non-author annotators, ~15 min each. Do not send; the orchestrator batches. All numbers stay PROVISIONAL.
7. Write REPORT.md in journal style: strongest true claim only (large partner-wording echo; +8.7 propositional; cue channel largely removes it; zero-tap mitigations do not beat random-ask at matched taps; polarity labels robust to J1/J2/arbiter 36.8-38.4), with a figure per claim and an explicit "where it does not help" section. No GPU needed; keep API use at zero unless item 1 requires arm-0 echo judging (<=3 judge concurrency).

Stop rule for round 3: this is the last round regardless of outcome; items 1-3 are mandatory, 4-7 best effort.

### Amendment A10 (2026-11-03, round 3; written BEFORE any round-3 number was computed; machine-only re-analysis of stored outputs, no new generation sweeps)
Scope: D-R2 items 1-7. All round-3 numbers stay PROVISIONAL until the human check (ANNOTATION_REQUEST.md, round-3 section) returns. Everything here is post-pilot and outcome-informed by round 2 (labelled as such).
1. C1 restatement. Primary C1 = UNFILTERED: chip, [YES] cue, X turns (Xa/Xb/Xc, family mean) minus arm 0 (no turn), outcome = committed output with polarity opposite to the cue (wrong_all, echoes and agreement replies counted as harm), pooled mean of 4 models, family cluster bootstrap (B=5000, seed 20261103). The echo/reply-filtered version (wrong_prop) is a LOWER BOUND. The +-5 pp margin was widened from +-2 pp after the pilot (D-R1 item 5); the filtered CI is also reported against the original +-2 margin, and no text or code label may say "equivalent/negligible". Symmetric filter: the arm-0 outputs in scope (every arm-0 output labelled negated, all channels) are paired with the family's Xa, Xb and Xc turn texts (the counterfactual turn the partner would have said) and sent through the same two echo/reply judge prompts (EJ1/EJ2, gpt-6.1-sol, concurrency 3, same disagreement rule); filtered arm-0 harm per family = mean over the three forms of (negated and not licensed). C1-filtered-symmetric = wrong_prop(X) - wrong_prop(arm 0, counterfactual turn).
2. C2 decomposition. Units: the 142 bare-channel, intended-affirmative, X-turn outputs labelled negated and not licensed by the echo/reply judges (137 unique (turn,output) pairs), plus a control of 60 outputs sampled (random.Random(20261104)) from bare, intended-affirmative, X-turn outputs labelled affirmative, drawn to match the 142 by model x turn form proportions. A new gpt-6.1-sol judge (two prompt variants, reversed option order; judge sees keywords, partner turn, output; not intent/model/channel) assigns one class by the claim the output makes: PARAPHRASE (restates the partner's claim in different words), FABRICATION (adds a specific negative claim, reason or entity found neither in the keywords nor in the turn), INDEPENDENT (the claim follows from the keywords alone, not tied to the turn). Disagreement between variants -> reported as "unresolved" and counted as PARAPHRASE (conservative for harm attribution to the partner). Counts by Xa/Xb/Xc and model; the control shows the judge's false-positive rate (affirmative outputs should not be PARAPHRASE of a negation). Lexical-form confound: C2 re-run on checker-passing Xa/Xc turns only (per-protocol, forms Xa and Xc), next to ITT Xa/Xc and Xb alone. Headline C2 = range "+8.7 propositional to +36.7 with echoes".
3. Author dependence. Reported as author-specific on the 40 shared families (mistral-authored vs qwen14-authored). Writer-cluster sensitivity: clusters = writer_id (hw families; r2_c1 families are their own cluster); resample writer clusters. Author-weighted pooling: (a) equal weights across the two authors on the 40 shared families, (b) weights by n (130 mistral + 40 qwen14 family-vectors). Conservative CI = the author subset with the smaller effect (qwen14) and its own CI; the cross-author "min over subsets" is quoted as the conservative bound. Model weights: equal (mean of 4 models) vs by n cells (identical counts, so equal; stated).
4. Benchmarks. (i) chip, word, M4+chip, chip+G1 are relabelled "cue-supplied ORACLE upper bounds" (the intended polarity is handed to the system; they do not mitigate the partner effect on bare input). (ii) Q grid extended to {0.05,0.10,0.20,0.30,0.50,0.70,0.90}; X-frame comparison is near-definitional (stated). (iii) Negation-frame gate G_neg: ask (chip output, 1 tap) iff the partner turn text contains a negation/contrast cue (declared lexicon: not, n't, no, nobody, nothing, none, never, nor, neither, without, fail*, fell through, fall through, cancel*, call* off, collaps*, drop*, abandon*, scrap*, but, however, although, unfortunately, sadly, instead), else commit with the turn in context (bare|turn). Applied per (family, turn). Matched random-ask = ask with probability equal to G_neg's frame-level ask rate. Credited only if its paired family-bootstrap CI vs matched random-ask excludes 0 in the right direction. Reported per frame (X, D, Q) and on a mixed stream (X, D, Q equal weight, q=0.1 for X and D). (iv) Logprob gate: generations.jsonl was checked and does not store logprobs; NOT computed, no generation. (v) Arbiter-only contrast G1 vs chip: for X-turn chip outputs (both intents) where G1 changed the text (182 of 3120 pairs; unchanged pairs have identical labels and cancel in the contrast), the polarity of every distinct changed text (chip arm and G1 arm) is labelled by me (Claude) blind, output text only, shuffled, arm and judge labels hidden; decision rules as in A9 (questions/fragments/leaked chips/mental-state frames -> unclear/mixed; corrective "X, not Y" -> affirmative). Contrast = weighted wrong polarity per 1,000 X messages, G1 minus chip, under (a) final labels, (b) J1 only, (c) J2 only, (d) Claude-arbiter labels on the changed units (final labels elsewhere; identical text so identical).
5. C3 reworded: "H3 unsupported; the Q frame lowers the affirmative share through abstention". Also report the non-abstained affirmative share = aff / (aff + negated) and per-model abstention (unclear/mixed) shares.
6. Label robustness: C2 all-negation recomputed with critical_J1 only, critical_J2 only, and final label (strongest-claim range).
7. Human check items/keys built, not sent (round-3 section of ANNOTATION_REQUEST.md).

### Amendment A10b (2026-11-03, round 3, before any round-3 outcome was computed; efficiency deviation)
The arm-0 echo judge scope in A10.1 ("every arm-0 output labelled negated, all channels") was narrowed to arm-0 outputs labelled negated in intent-AFFIRMATIVE cells (all channels), because only those cells enter C1/C2 and the intent-negated negations are correct outputs under the cue (about 1,000 extra units x 3 turn forms would only burn shared API quota). The estimands are unchanged. Cache from the first (aborted) launch is reused.

### Decision D-R3 (2026-11-03, after round 3 of 3): STOP
Round cap reached (3 of 3); no further compute. All numbers remain PROVISIONAL (machine labels only) until the human check returns. Critic issues not resolved are carried as stated limits, not fixed by new runs (post-round-3 labelling).

What is supported (strongest true claim): in the bare channel a negative partner remark raises negated output in all 4 models (+36.7 pp all negation; propositional excess +8.7 [6.9, 10.6], author- and form-dependent; Xa+Xc only +6.8 [4.9, 8.9]). With a supplied [YES] cue the leakage is +7.05 pp [5.26, 9.04] unfiltered (filtered lower bound +1.2 to +1.5 pp, inside +-5 pp but NOT inside the original +-2 pp; do not call it equivalent/negligible). Cue-supplied chip/word/M4+chip/chip+G1 are oracle upper bounds, not mitigations of the bare-input effect. Zero-tap fixes (M5b, M4) do not beat matched random asking at low q; the negation-frame gate gives no gain over frame-aware random ask (+2.8 [-1.4, 7.5]).

Limits to state in any write-up (the critic's major issues, unfixed):
1. Policy rankings are functions of the assumed q; the M4 zero-tap vs random-ask comparison uses different tap rates, so only same-tap comparisons (or tap-vs-error frontiers per q) may be quoted. "Where it matters" claims are removed.
2. Decomposition is a machine-judge result: control rates (13/18/68 vs 50/19/31) show fabrication is indistinguishable from the control false-positive rate (19% vs 18%) and 15 unresolved are counted as PARAPHRASE; no pp attribution by class and no weighted x5 columns are quoted. Echo vs propositional split is unvalidated until human Part A/B return.
3. Author dependence is unresolved: second author on only 40 of 130 families; always quote the subset with its denominator (+9.2 mistral, +4.2 qwen14, writer-cluster conservative lower end +2.8). Limit goes in the abstract.
4. Drift: the shared code gives +9.2/+4.2 (earlier quoted +9.8/+4.8) and pooled 36.67 (earlier 37.1); cause not traced, so the current shared-code values are the reported ones and the earlier ones are labelled superseded. The "director range" wording is retired (it was round-2 flip-sensitivity bounds).
5. G1 gain rests on one author-aware rater at 75% agreement over 182 changed pairs; logprob/entropy-gated ask NOT run (generations.jsonl stores no logprobs); listed as future work, not claimed.

Next steps that need human input, not compute: send the round-3 ANNOTATION_REQUEST.md Parts A/B (non-author annotators; 350 G1/chip texts for non-author labels), and a second turn author on all 130 families if the paper is to claim author-robustness. Cite COMPA as motivation only. Orchestrator should treat the frontier as write-up ready with the above hedges.
