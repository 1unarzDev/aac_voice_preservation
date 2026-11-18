# Independent mutation set (plan section B3) - pre-declared before any generation

Purpose: a non-circular sensitivity set. Mutants are built WITHOUT the checker lexicon (the NEG/HEDGE/PAST/LATER regexes
in src/oracle_baselines.py and the operators in src/oracle_real_ops.py). Part 29: 2 human annotators confirm each item
changes or keeps meaning; ONLY human-confirmed items count. This step builds candidates only; the judge and baselines are NOT scored here.

## Source draw (declared, seeded)
- Same oracle-pass filter as src/oracle_real.py build: runs/hw1/scored.parquet, valid, channel in {chip1, chipall, full},
  critical_match True, critical_source in {agree, arbiter}, no refusal/acceptance quarantine; one output per family, one per
  distinct text. Texts already used in analysis/oracle_real/sample.jsonl are excluded (no overlap with the earlier set).
- Seed 20261117; per-operator RNG random.Random(f"{SEED}|{op}"); each text is used at most once across the whole set.
- Applicability pre-filter (before any outcome is seen): length 3-22 words, single sentence, not an empty/degenerate text.

## Operators and quotas (100 mutants)
| op | n | source pool (dimension) | construction |
|---|---|---|---|
| neg_fail_to | 13 | polarity, ref affirmative | template: "I <verb>..." -> "I fail to <verb>..." / "X <verb>s" -> "X fails to <verb>" |
| neg_refuse_to | 13 | polarity, ref affirmative | template: same slot -> "refuse(s) to <verb>" |
| neg_hardly | 12 | polarity, ref affirmative | template: "can" -> "can hardly"; "am/is/are" -> "... hardly"; "I <verb>" -> "I hardly <verb>" |
| neg_nobody | 10 | polarity, ref affirmative | Gemini: rewrite with a quantifier subject like nobody/no one ("Nobody ...") |
| role_passive | 14 | agent | Gemini: swap who does what to whom (passivise or invert roles) |
| role_embed | 12 | agent | Gemini: embed the claim as attributed to someone else so the original speaker is no longer the agent |
| q_embed | 12 | speech_act, ref question | Gemini: turn the question into an embedded statement ("I wonder whether ...") |
| time_implied | 14 | time_quantity | Gemini: shift the time reference by implication only (no explicit time words from the checker list) |

Item operator assignment is by seeded shuffle of the dimension pool in this order of ops; template ops walk the shuffled pool
until the template applies. Gemini ops take the next shuffled items, one call per item (one retry on invalid output).

## Controls (50, meaning-preserving)
- ctl_contraction (10): template toggle of contraction (I am <-> I'm, do not <-> don't excluded where negation present: only non-negated forms).
- ctl_paraphrase (40): Gemini paraphrase that keeps polarity, speech act, agent/roles, certainty, politeness, time and quantity; drawn across all six dimensions (seeded, pool minus mutant sources).

## Gemini
- Model gemini-3.1-flash-lite via src/gemini_backend.py, temperature 0, thinking off, max_tokens 96, concurrency 1.
- Hard cap 150 calls in total (62 mutant + 40 control planned, remainder for single retries). Prompts are fixed in src/independent_mutants.py
  (ops PROMPTS dict) and the raw responses cached in tmp/ then logged to runs/oracle_indep/gemini_calls.jsonl.
- Validation of a Gemini output (fixed, mechanical): non-empty, one sentence, differs from original (case/punct-insensitive),
  length 0.5x-2.5x, and for mutants must not contain the words "yesterday|tomorrow|tonight|ago" (time lexicon) unless op is time_implied
  (where it is forbidden too). Failures after retry are dropped and replaced by the next shuffled item (counted in the call budget).

## Outputs
- analysis/oracle_indep/candidates.jsonl: {id, original, mutant, dimension_hint} in a seeded shuffled order, no labels.
- analysis/oracle_indep/key.private.jsonl: id -> kind (mutant|control), op, expected, source text_id/family/model/variant, ref value,
  lex_visible flag (mutant newly matches the baseline NEG/PAST/LATER regexes; reported as a stratum, "nobody" is NEG-visible by construction).
- analysis/oracle_indep/draw.json: seed, pool sizes, counts by operator, call counts.
- Not done here: judge scoring, baseline scoring, human confirmation (Part 29). Mutants are candidates until two annotators confirm.

## Amendment 1 (made after the first build, which showed template ops under-filled: neg_refuse_to 6/13, neg_hardly 0/12; no outcome/judge info involved)
- Template negation ops walk the polarity pool first, then (seeded order) non-negated, non-question texts from the other five dimension pools; the
  template regex is the only applicability criterion. Their dimension_hint is the source dimension.
- First-build Gemini responses (temperature 0, same op+sentence) are reused from runs/oracle_indep/gemini_calls.jsonl rather than re-called;
  the 150-call cap counts only distinct calls actually made (first build used 106).
- Known limitation, kept on purpose: role_passive/q_embed/paraphrase outputs from a small model can fail to change (or fail to keep) meaning;
  that is exactly what the 2-annotator Part 29 confirmation filters, and only confirmed items count.

## Amendment 2 (Part 29 packet and scoring rules; written 2026-11-17 after candidates.jsonl was built, before any Part 29 return, before any judge or baseline score on these items)
Packet (src/make_listener_study.py, shared with Part 28; per-person files annotation_package/stage7/<ID>_part29.json; private key annotation/oracle_indep_key.csv):
- All 150 candidates (100 mutants, 50 controls) are shown, mixed, each to 2 different annotators. Nobody annotates an item whose source family they wrote or checked
  (src/make_frontier_parts.py logic: hw_blocks). Annotators never see kind, operator, dimension, source or which sentence is the original.
- Which sentence is "Sentence 1" and which is "Sentence 2" is a seeded coin per item (stored in the private key); the two annotators of an item see the same order.
- One fixed, dimension-neutral question for every item: "Do the two sentences tell the listener the same thing: who does what to whom, whether it is so or not, when it
  happens, how sure the speaker is, and whether it is a statement, a question or a request? Small differences in wording or style do not count."
  Answers: same / different / unsure. (The wording names every dimension, so it does not hint at the one that was changed.)
Confirmation rule (the only items that count):
- A mutant is human-confirmed CHANGED if both annotators answer different. A control is human-confirmed SAME if both answer same.
- Any other pair (a disagreement, or either annotator unsure, or a missing answer) is unresolved: excluded from every score and counted by operator.
- A mutant both annotators call same, or a control both call different, is a construction failure: reported by operator, never scored.
- An annotator with fewer than 80% of their assigned Part 29 items answered is dropped; the items then have one annotator and are unresolved.
Scoring (src/score_oracle_indep.py; the judge run is made after returns, by the unchanged production judge, on the mutant text only):
- Target dimension of a mutant: neg_* -> polarity (reference value affirmative); role_passive and role_embed -> agent; q_embed -> speech_act (reference question);
  time_implied -> time_quantity. Reference values are those in the private key. A control is scored on its own source dimension and reference value.
- An oracle "catches" an item when its label does not match the reference (production critical_match). Sensitivity = caught / confirmed mutants, false-alarm rate =
  caught / confirmed controls, both with Wilson 95% intervals; by operator, by target dimension, and by the lex_visible stratum (lex_visible False is the
  non-circular headline: the mutation does not newly match the baseline NEG/PAST/LATER lexicon). Oracles: production judge, surface baseline, overlap baseline
  (src/oracle_baselines.py, applied to the mutant text; overlap uses the source family's two sentences).
- Judge versus each baseline on the same confirmed mutants: exact McNemar test on the discordant pairs. Annotator agreement is reported (raw agreement and Cohen kappa on
  same/different over items where both answered, unsure counted as its own category in a second line).
- An unresolved judge label counts as not caught (conservative) with the upper bound where it counts as caught reported beside it. No exclusion is made on the basis of any oracle output.
