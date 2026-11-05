# Intent-coverage pilot: PLAN (frozen before any generation)

Written 2026-11-04 by the designer, before any draft set was generated, before any item was drawn, and before any coverage judgment was made. Nothing in this plan has been run. Every number quoted below comes from files already in the repo (Part 18 `analysis/intent_check/`, `analysis/whole_message/`, `analysis/frontier/*`, `orchestration/decision_log.md` D-070..D-092) or is a design constant declared here. No number in this file is a result of this study.
Source of the stage: `ideas/frontier/CRITIC_SYNTHESIS.md` Stage 2 (journal core, C3 + C1 merged). Human stage = "Stage 6" in the annotation program.
Status rule: this file is git-timestamped, then hash-deposited by the orchestrator (as for D-073/D-092) before generation. Any later change goes in `DEVIATIONS.md` in this folder with a date and a reason; the plan text is never edited.

## 0. Question, thesis, and what the pilot may conclude

Part 18 showed that keeping the critical commitment is necessary but far from sufficient: writers accepted 1/200 expansions as-is, 25.1% of outputs matched the intended version (39.2% with the critical chip, 11.2% bare), and 70% were "something else". Consultants (R6) ask that drafts are never spoken without approval and that the system "show differing drafts" and "show the particular unresolved choice". That turns the output into an approval-gated set of drafts. The pilot measures what such sets buy.

Primary question. For the same writer-authored items and the same keywords, how often does a draft set contain a sentence the writer says is what they meant, and at what reading and tap cost, for: a single greedy draft, diverse samples (K = 3, 5), one-dimension-contrast sets, dimension + event/role contrast sets, and a plain-word-cue single draft?

Why this is the journal core. Contrast sets operationalise "show differing drafts" and make the writer-intent coverage of a set, per tap and per draft read, the currency. The pilot gives the first measured coverage-per-burden frontier for AAC keyword expansion against the writer's own intent (not a judge). The analysis is pre-declared so that a null is as reportable as a gain.

Allowed conclusions (declared now, section 9 gives the rules):
- C-A "contrast sets raise coverage beyond diversity and beyond a cue tap";
- C-B "drafts help only when the cue is missing" (gain on bare, none on chip);
- C-C "drafts do not help beyond one cue tap" (bounded null; thesis shifts to the ceiling analysis and the validity study);
- in every case, direction and writer-cluster CI, never "AAC users benefit". Writers rate sets built from their own pairs. This is writer-intent agreement by adult annotators, not validation by AAC users.

## 1. Items

### 1.1 Frame
- Unit: a kept writer pair (family) from `data/items/hw.jsonl` (hw1, 547 kept; analysis exclusions as in `analysis/hw1`: the P06 speech-act pair, any refusal/acceptance speech-act family as in W-C) plus accepted `hw2` speech-act pairs (`annotation/written/hw2/hw_candidates.jsonl`, 60 pairs, P05/P16/P17/P18, dropped pairs after Part 16 removed). Near-duplicate components collapsed to the lowest family_id (Jaccard >= .75 rule of `analysis/hw1/report.md`).
- Each pair has variants A and B that differ in exactly one dimension (polarity, agent, time_quantity, politeness, certainty, speech_act) and identical bare keywords. The writer's own sentence for the intended variant is the target `r`. These are the writers' own pairs; the same writer rates their own items.

### 1.2 Draw (declared, seeded; script `src/coverage_draw.py`, written after this plan is hashed)
- Seed 20261117. N = 200 items = 10 per writer, 20 writers (P01..P20), the same writer load as Part 18 so that all 20 can finish in one sitting.
- Stratification: within each writer, 5 + 5 over the writer's two dimensions (P06: 10 time_quantity; P06 has no speech-act item). The four hw2 writers (P05, P16, P17, P18) give 3 of their 10 items from their accepted hw2 speech-act pairs (replacing the writer's hw1 item from the stratum with more items, ties by seed), so hw2 contributes 12 items and speech act is about 40 in total. Target per-dimension totals are therefore about 30-42, each >= 30. The script prints the realised table, which is frozen in `items_draw.json` with its sha256.
- Exclusion of Part 18 families (200 items in `annotation/intent_check_sample.json`): excluded from the draw so that writers do not re-rate sentences they judged before. Exception: P06 has 15 pairs, 10 used in Part 18, so P06 takes the 5 unused plus 5 Part 18 families chosen by seed, flagged `seen_in_part18`. Sensitivity: all primary contrasts re-estimated without the flagged items.
- Intended variant (A or B) per item: seeded coin, balanced within writer-dimension, same rule as `make_intent_check.py`. Machine analyses additionally score both sides (section 5.3) because bare keywords are identical for A and B.
- Reserve: 20 additional items drawn by the same rule (one per writer, flagged `reserve`) for dry runs and the proxy debugging. They never enter any estimate.

### 1.3 Input conditions (factor within item)
- `bare`: the pair's bare keywords (reference level: a model cannot know the intended side).
- `chip`: bare + the critical chip of the intended variant (as in Part 18 `chip1`).
- `word` (reference arm only): bare + the plain-word cue with equivalent content (D-070 chip controls; same text rule as `src/build_chip_controls.py`).
All three are built from the stored items, never from the writer's sentence. Both `bare` and `chip` are in every comparison; `word` enters only the plain-word reference (section 2, W1).

### 1.4 Power (approximation, not a promise)
Paired item difference in "writer says a draft is what I meant" with SD about .45, 200 items, 20 writer clusters of 10 (design effect about 1 + 9 x .05 = 1.45 if ICC is .05; ICC is re-estimated from Part 18 before the Stage 6 package is built and the table updated in `DEVIATIONS.md` if it is much larger). SE about .038, so the minimum detectable paired difference at 80% power, two-sided .05, is about 11 pp. We therefore only claim a gain of >= 10 pp as meaningful and treat smaller differences as unresolved. Per-dimension results (n about 30-40, 6-7 writers) are direction only (same caution as hw1).

## 2. Draft-set methods (all on the same items and keywords)

Generator. Primary: `gpt-6.1-terra` (API, codex-lb, generation concurrency <= 4). Prompt family P0 = `prompts/P0.txt` for plain generation (as in hw1/Part 18). New prompts are frozen in `prompts/coverage_*.txt` with sha256 in `prompt_shas.json` before generation. Replication (machine proxy only, no human rating): Qwen2.5-14B and Llama-3.1-8B via `~/research-cluster/bin/research submit aac-llm` (plain generation; no logprob probes needed).
The generator never sees: variant labels A/B, the dimension label of the pair, the writer id, the other variant, or the writer's sentence. Contrast values come from the fixed per-dimension menu in the item schema (`critical_options`: e.g. polarity affirmative/negated; speech_act statement/question/request/offer/...; agent speaker/addressee/we/third party; certainty plain/hedged/emphatic; politeness polite/plain; time past/now/later), never from the pair.

Notation. k = number of drafts shown. Slot 1 is always the default draft (G1 output), so every set contains the status-quo draft.

| id | method | k | how the set is made |
|---|---|---|---|
| G1 | single greedy draft | 1 | P0, T = 0. Reference for every contrast. Both `bare` and `chip`. |
| W1 | plain-word-cue single draft | 1 | same as G1, with the cue as a plain word (`word` condition). Reference for "cue as encoding" (D-070: word ~ chip on 5/6 dims, word > chip on speech act). |
| D3s, D5s | diverse sampling | 3, 5 | independent T = 1.0, top_p .95 samples from P0; de-duplicate on normalised text; draw up to 12 samples to reach k distinct; slot 1 = G1. Sets with fewer than k distinct drafts are kept short and counted. |
| D3p, D5p | prompted diversity | 3, 5 | one call: "give k sentences that each say something different the keywords could mean". The strong diversity baseline (no strawman). |
| C3, C5 | one-dimension-contrast set, deployable | 3, 5 | slot 1 = G1; slots 2..k = G1 edited so that exactly one named dimension takes a named alternative value and everything else (wording, other values) is held fixed, for the top-(k-1) dimensions chosen by the selector S (below). Label-faithfulness filter (below). |
| C3o | contrast set with oracle dimension | 3 | as C3, but the contrast dimension is the pair's own dimension (value flip to the other written value plus a second menu value). Ceiling, not deployable, always labelled as such. |
| E3, E5 | dimension + event/role contrast | 3, 5 | k = 3: G1, one top-1 dimension contrast (S), one event/role contrast. k = 5: G1, two dimension contrasts, two event/role contrasts. The event/role contrast is a reading with the same critical values but a different relation (who does what to whom, which verb/predicate, e.g. "Does the cafe serve lunch?" vs "Are we having lunch at the cafe?"). |
| R3 | random-dimension control | 3 | as C3, but the contrast dimensions are drawn at random from the other dimensions (seeded). Tests that targeting, not variety, drives any gain. |
| C3f | static-order contrast set | 3 | as C3, with the dimension order fixed (polarity, speech_act, agent, time_quantity, certainty, politeness; the order of SLP severity weights). Tests whether the LLM selector earns its call. |

Selector S (deployable dimension choice). One frozen prompt sees only the keywords (and the chip, in the `chip` condition) and ranks the six dimensions by how likely the default reading is wrong or underdetermined. In `chip` the cued dimension is removed from the ranking (it is already covered). Diagnostics: recall@1 and recall@2 of the pair's true dimension in `bare` (a number for the paper, not a gate), against static-order and random.
Label-faithfulness hard filter. Each contrast draft is checked by the critical-value judge for the value it was supposed to realise (and, in `chip`, for the cued value: a draft contradicting the given cue is dropped). A failed slot is regenerated once; if it fails again the slot is left empty. Fill rate, regeneration rate, and the unfiltered cue-violation rate are reported. This is the "guard as hard filter": sets never show a draft that contradicts a given cue.
Draft order in a deployed set is deterministic (G1, then contrasts in selector order, then event/role). Human pool order is shuffled (section 4).
Run-to-run noise. The API ignores seeds (D-066 era note: exact T = 0 agreement 44-71% for terra). Stored outputs are the data; we do not regenerate after seeing results. G1 is run twice in the dry run only to report its repeat agreement.

Counts and cost (estimates for budgeting, to be replaced by counts from the run): about 200 items x 2 conditions x about 22 terra generation calls = about 9,000 calls (G1 shared by all arms; contrast and event/role drafts are edit calls); judge calls about 400 item-conditions x about 25 unique drafts = about 10,000 combined critical+match calls (one JSON call per draft) at judge concurrency <= 3, cached under `cache/judge/`. Local replications: the same inputs with the two local models via the research platform, about 18,000 plain generations. Total API on the order of tens of dollars; budget cap USD 60 (stop and report if exceeded). No Gemini.

## 3. The machine coverage proxy (Stage 2 primary, validated before use)

Definition. A draft `d` covers target `r` (the writer's sentence for the intended variant) iff a blind judge says both:
1. critical value of `d` on the pair's dimension equals the intended value (the existing critical-value judge, blind arbiter, no J1 fallback; `src/judge.py`);
2. event/role structure of `d` matches `r` (same predicate and same participants in the same roles: who does what to whom/what; ignoring added or dropped detail such as places, times of day not in the keywords, adjectives, and tense where tense is not the pair's dimension).
One call per (draft, r) returns JSON {critical_value, event_role_match: yes/partly/no, which_variant: A/B/neither}. The call sees the draft, A and B sentences (so it can place the draft) and the pair's dimension; it does not see the arm, the input, the condition, or other drafts. A set covers iff any draft covers. `partly` counts as no in the primary rule (a looser rule is a sensitivity). Detail drop is explicitly tolerated: Part 18/`whole_message` showed 98% of rejected outputs omit detail no keyword carries, so requiring detail overlap would make coverage unreachable.
Judges. Primary: `gpt-6.1-sol` (effort low). Independent-family checks: Qwen2.5-14B and Mistral-Nemo-12B locally (as in `whole_message`), on all drafts of the primary generator; reported, not substituted.

Validity gate (run FIRST, before any new generation, no new people):
- Data: the 195 usable Part 18 outputs with writer labels (variant match: A/B/something else; accept: yes/small edit/no).
- Split: threshold and prompt frozen on writers P01-P10; evaluated on P11-P20 (as in `whole_message`).
- Pass requires all of: (a) AUROC for "writer says it matches the intended version" >= .80 with writer-cluster CI lower bound >= .70 on the holdout; (b) binary Cohen kappa >= .50 vs the writer match label at the frozen threshold on the holdout (the critical-only judge reached kappa .24-.31 in Part 18); (c) paired AUROC gain over word count (best trivial in `whole_message`, .72) with writer-cluster CI excluding 0; (d) sanity checks: the identical sentence covers itself, an unrelated sentence does not.
- If the gate passes: machine coverage is the Stage 2 primary and is reported with a validity statement against writers. If it fails: machine coverage is reported as descriptive only; no machine-only claim about arms is made, human Stage 6 carries the conclusions, and the failure is a finding (instrument validity, C5).
- The proxy is an M1-ref-type score (it sees the writer's sentence offline), so it is a research instrument, never a deployable component. Machine-panel agreement is never called human validation.

## 4. The human measure (Stage 6)

Who. The same 20 writers, each on their own 10 items (adult non-author university classmates, consented, paid with payment and food, as before). No new people. Ethics wording unchanged and canonical: annotators were non-authors and reimbursed; they labelled and audited; some chose keywords and wrote pairs under CC BY 4.0; no personal data; no institutional review determination sought. We make no IRB claim and no AAC-user claim.

Package. One HTML tool in the same style as `rate_items.html` (Parts 20-25), about 50 min per writer (estimate: 10 items x about 5 min; the exact figure comes from a timed dry run on 2 reserve items with 2 non-writers; if the dry run says > 60 min, cut the `chip` pool before cutting the set view). Items are served with the writer's A and B sentences visible and the intended variant marked ("you meant: ...").

Per item, in this order:
1. Set view (deployed form). One randomly assigned (condition, arm) set, shown in its deployed order with no arm label. Condition in {bare, chip}; arm in {G1, D3p, C3, E3}, balanced within writer, so 25 sets per cell over 200 items. Questions: "Is any of these what you meant?" (yes / no); "Which one?" (pick one or none); "How hard was it to find what you meant (1 easy - 5 hard)?"; timestamps are recorded by the tool (reading time per screen).
2. Pool rating. All unique drafts from the primary arms for both input conditions (G1, D3p, C3, E3, plus W1; for items assigned to a 5-arm audit, D5p, C5, E5), shuffled, arm-blind, de-duplicated across arms by normalised text. Per draft, the Part 18 question: "Does it say version A, version B, or something else?" and "Would you accept it as your message? yes / with a small edit / no" and, for rejected drafts, a short free-text "what is wrong" (this adds the free-text field the critic noted was missing in Stage 2). Items served in `bare` and `chip` pools separately, each pool headed with the keywords that produced it. Order: pool follows the set view, so set-view answers are not primed by the pool.
3. Burden check on a quarter of items (2-3 per writer): the set from step 1 vs a second set of another arm for the same condition, side by side in random left-right order: "Which set is easier to find what you meant in?" (left / right / same) and 1-5 burden each. Exploratory.
Counts: about 9 unique drafts per item and condition at k = 3; the five-arm audit adds about 6 on 5 items per writer (k = 5 pools only on those items, so k = 5 results are labelled subset, n about 100).

Human endpoints (all derived from the pool ratings per arm, so every arm is measured on every item):
- H-cov (primary): the arm's set has >= 1 draft rated "version = intended variant" AND accept in {yes, with a small edit}. This is Part 18's match question made usable; "yes or small edit" is the second leg because writers' sentences carry detail no keyword supplies. Strict as-is acceptance is reported but is not a success criterion (Part 18: 1/200).
- H-match (secondary): the arm's set has >= 1 draft rated as the intended version regardless of acceptance (the exact Part 18 definition, comparable with 25.1% / 39.2% / 11.2%).
- H-first (read cost): the position, in deployed order, of the first draft with H-cov; if none, the full k (censored).
- H-burden (secondary): reading burden 1-5 and reading time from the set view; side-by-side preference from step 3.
- H-direct (check): H-cov computed from the set-view question for the arm each item was assigned, against the pool-derived value for the same arm (checks that the pool rating, which is easier, does not overstate coverage).
- H-wrong-first (safety): the share of sets whose first draft is rated as the other variant on the pair's dimension. Contrast sets must not be worse than G1 here by construction (slot 1 = G1); reported as a check and as an unfiltered-cue-violation rate.
Human-machine concordance. Draft-level agreement of the validated proxy with the pool ratings (kappa, AUROC) and arm-level rank concordance (section 7, S5). Writer free text is coded into a small taxonomy (critical, relation, detail dropped, added, fluency) by the hand-coding rule of `whole_message`; the coder is stated.

## 5. Cost model (taps and drafts read)

Constants are assumptions, not device measurements, and are flagged as such everywhere they appear. Consultants asked to test navigation and scanning order on real devices; that test is out of scope here, and the report states the cost as tap-equivalents, with a sweep.
- Keyword taps: identical across arms, excluded from differences.
- Cue tap c = 1 per cue (chip or plain word; D-070: equal cost).
- Read cost r per draft read, default r = 0.5 tap-equivalents; sweep r in {0.25, 0.5, 1, 2}.
- Choose tap s = 1 whenever k > 1 (pick a draft); accept tap a = 1 in every arm.
- Fallback when no draft is usable: edit cost e = 1 tap-equivalent per word edited, using word-level Levenshtein distance from the closest draft to `r` (writer-free, judge-free; `whole_message`), and rewrite cost = number of words in `r` when no draft is usable, sweep e in {0.5, 1, 2}.
Expected cost per message = c x [cue given] + r x (drafts read until the first usable draft, else k) + s x [k > 1] + a + fallback (as above if no usable draft; edit cost to the closest usable-or-not draft otherwise 0).
Outputs: coverage vs expected cost frontier (points = arms x condition), cost per covered message, extra coverage per extra tap-equivalent over G1, and break-even r* at which each arm stops beating G1-with-chip. Machine-side costs use the proxy; human-side costs use H-cov and H-first. Safety stays a hard filter, not part of the price; we additionally report the silent-reversal and SLP-weighted reversal rates of the first-shown draft per arm (stored SLP weights from D-078; n = 2, expert review not a population estimate).

## 5b. Machine analysis extras (cheap, no people)
- 5.1 Dimension recall@1/2 of the selector S vs static-order and random, per pair dimension.
- 5.2 Both-sides coverage in `bare`: for each pair, coverage of A and of B by the same set (the pair is a minimal pair). Reports P(covers intended), P(covers both), and whether contrast sets are the only arms that cover both.
- 5.3 Size/diversity controls: mean pairwise similarity within sets, dedupe-shortfall rate, equal-k comparisons only for any headline claim.
- 5.4 Replication on two local models: arm ordering, not magnitude, is the claim.

## 6. Hypotheses (directional guesses, declared; none is a success criterion by itself)
- H1: in `bare`, targeted contrast sets (C3, E3) cover more than diversity at equal k (D3p), because diversity does not control which dimension varies.
- H2: in `chip`, dimension contrast adds little (the critical dimension is already cued); event/role contrast carries the gain because relation substitution is the main reason chip outputs are rejected (46% vs critical 4%, `whole_message`).
- H3: R3 does not beat G1 by more than D3p does; the selector beats static order only if recall@2 >= static recall@2 + .05.
- H4: reading cost eats part of the gain: at r = 1 contrast sets lose to chip + G1 on cost per covered message; they win at r = 0.25.

## 7. Pre-declared success criteria vs baselines

Inference unit: writer (20 clusters), paired within item. 95% CI = writer-cluster bootstrap (B = 10,000, seed 20261117, resample writers then items within writer), plus the writer sign-flip randomisation test of `robust` T6 (reported next to each p). Holm over the four primary contrasts S1-S4. Everything else is exploratory and labelled so.
Baselines (fixed): B0 = G1 in `bare`; B1 = G1 in `chip` (one cue tap, the strongest single draft); B2 = W1; B3 = D3p, D5p (diversity at matched k).

Primary contrasts on H-cov (human), all paired:
- S1 (targeting beats diversity): `bare`, E3 minus D3p, or C3 minus D3p, whichever is the larger on the machine proxy at the dry-run stage (chosen from the machine proxy only; ties go to E3). Success = difference >= +10 pp and CI lower bound > 0.
- S2 (a set beats a cue tap): `bare`, best contrast set at k = 3 versus B1 (G1 with chip, one tap). Success = non-inferior with margin 5 pp (CI lower bound > -5 pp) AND expected cost per covered message not higher than B1 at r = 0.5. If coverage is non-inferior but cost is higher at r = 0.5, the finding is "equal coverage at higher burden", reported as such.
- S3 (a set adds to a cue): `chip`, E3 minus B1 (G1 with chip). Success = >= +10 pp, CI lower bound > 0.
- S4 (burden acceptable): median drafts read to first usable draft <= 2.0 at k = 3 among covered items, and mean set-view burden of E3/C3 no more than 0.5 points above G1 (CI upper bound for the difference < +1.0).

Secondary criteria: S5 proxy-human concordance: arm-level Spearman between machine and human coverage across the 8 primary arm-conditions >= .80, and draft-level kappa >= .50 on pool ratings. S6 safety: unfiltered cue-violation rate reported; filtered 0 by construction; wrong-first no worse than G1 (difference CI upper bound < +3 pp). S7 machine replication: arm ordering of the primary comparisons holds on both local models.

Outcome rules (decided now):
- S1 and S3 (or S1 and S2) pass: write C-A; Stage 3 (policy and frontier) proceeds with contrast sets as the output type.
- S1 passes only in `bare` and S3 fails: C-B, gain is cue substitution; the design guidance is "cue first, drafts for the missing cue".
- S1 fails and the best set minus B1 < +5 pp in both conditions: C-C. Report coverage ceilings per arm (what share of writer sentences any draft can reach) and shift Stage 3 to the ceiling analysis; the thesis is validity and approval, not drafts.
- Any criterion marked unresolved (CI spans both -5 and +10) is reported as unresolved, not as a pass or a fail.
- If the proxy gate fails (section 3), only human results count toward S1-S4.

## 8. Analysis plan and outputs
- Script `src/coverage_analyze.py` is written and frozen (sha256 deposited) before the human returns; it reads only files in this folder and emits `summary.json`, `coverage_by_arm.csv` (arm x condition x model, machine and human), `contrasts.csv` (S1-S4, with the CI and randomisation p), `frontier.csv` (cost grid), `proxy_validity.json`, `selector_recall.csv`, `free_text_coded.csv`, and figures (coverage vs cost frontier; coverage by k; per-dimension profile).
- Rates carry Wilson intervals where per-item and writer-cluster intervals where compared. Per-dimension and per-writer tables are direction only. Mixed-effects logistic model (writer random intercept, family nested) is a sensitivity for S1-S3.
- Sensitivities (fixed list): without the `seen_in_part18` items; hw2 items out; looser proxy rule (`partly` = yes); strict as-is acceptance; excluding sets with fewer than k drafts; censored vs imputed read counts.
- Paper numbers: every number in a paper is a macro from these files via `make_macros.py` (no hand-typed numbers). Example sets in a paper are real stored sets chosen by a declared rule (e.g. the draw rule: seeded, first 3 per dimension) with the rate shown beside them.
- Claims language fixed in advance: "coverage of the writer's own intended message", "approval-gated draft sets", "writer-intent agreement by adult annotators". Never: IRB approval or exemption, AAC-user benefit, pre-registered (use "pre-specified and git-timestamped, hash-deposited"), that the affirmative default is new (cite Chen et al., ACL 2023), or machine-panel agreement as human validation.

## 9. Sequence, gates and stopping

1. Orchestrator commits this plan and hash-deposits it (no generation before).
2. Draw (`items_draw.json`), prompt freeze (`prompt_shas.json`), analysis-script freeze. Reserve-item dry run (20 items, 2 conditions, all arms) to debug prompts and the timed 2-person pretest. Dry-run items are never used again.
3. Proxy validity gate on Part 18 outputs (no new generation). Stop rule: if it fails, proceed but follow section 3.
4. Full generation (terra, then local models via the platform), label-faithfulness filter, coverage judging. Machine analysis. A machine-only intermediate report lists arm coverage and costs; it cannot change the human arms, the item list or the criteria.
5. Stage 6 package built from the frozen pool; send to the 20 writers; hash-deposit the pool key before sending.
6. Human analysis and the final report; deviations logged.
Stop rules: generation error rate > 2% or fill rate of any contrast arm < 80% after one regeneration -> stop and fix the prompt on reserve items (not on the 200), log a deviation; API spend cap USD 60; GPU only through the platform (`research submit aac-llm`); no logprob probes needed, so no flock jobs.

## 10. Threats, stated once
- Pairs are minimal pairs written to a quota per dimension, so coverage is measured against this intent distribution, not natural use. Coverage of natural messages is a Stage 3 question.
- Writers' sentences carry detail no keyword supplies, so strict as-is acceptance stays near 0; the usable criterion tolerates detail edits and the report shows both.
- The deployable selector may rarely hit the pair's dimension; the oracle-dimension arm bounds this.
- Writers rate their own pairs (no cross-rater reliability for intent); the pool design lets us compare with the proxy but there is no second human rater per item.
- Read and tap costs are assumed constants; they price the comparison, they do not measure a device.
- n = 20 writers, 200 items: moderate precision; only effects of about 10 pp or more are resolved.
- Order effects between set view and pool are bounded by H-direct; one sitting means fatigue, which the tool's timestamps expose.

## 11. Files this study will create
`analysis/coverage/`: `PLAN.md` (this), `DEVIATIONS.md`, `items_draw.json`, `prompt_shas.json`, `proxy_validity.json`, `drafts_*.jsonl`, `judgments_*.jsonl`, `coverage_by_arm.csv`, `contrasts.csv`, `frontier.csv`, `summary.json`, `REPORT.md`; `prompts/coverage_*.txt`; `src/coverage_{draw,gen,judge,analyze,package}.py`; `annotation/` Stage 6 tool and key (key never sent). Scratch in `~/aac-voice-preservation/tmp/` and deleted afterwards.
