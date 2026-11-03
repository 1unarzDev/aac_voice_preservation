# Whole-message fidelity and unrequested content: round 1 results (PROVISIONAL, machine-only)

Run 2026-11-02. Plan: PLAN.md (frozen before outcomes; freeze record and deviation log appended there). Scripts: `src/frontier_whole_message_{m1,stage1_jobs,stage1_analyze,s2_gen,s2_m1jobs,s2_analyze}.py`. Data: `stage1_features.csv`, `stage1_auroc.csv`, `stage1_h2_ck_true.csv`, `stage2_outputs.csv`, `stage2_rates.csv`, `stage2_contrasts.csv`, `stage2_by_dimension.csv`, `stage2_ck_true.csv`, `stage2_examples.md`, `summary.json`.
Everything here uses an LLM judge (gpt-6.1-sol, effort low) as the metric and the existing J1/J2 critical judge with a blind arbiter. Writer labels (Part 18) are the validation target for the metric; the Stage 2 arms have NOT been checked by people (R-WM-1 is not sent). Not validation by AAC users.

## What was done
- Stage 0: froze the M1 rubric prompt (sha256 fe9af5fd...), sanity-gate set and splits; logged in PLAN.md before any call.
- Stage 1 (full): scored the 200 Part 18 outputs and 50 SLP cards with M0 (existing critical judge), M1-ref, M1-free, M2 (lexical), a length-ratio baseline; 741 judge calls, 0 missing.
- Stage 2 (reduced slice, API only): gpt-6.1-terra, chip1, 54 families x 2 variants = 108 inputs, arms A0 (stored P0), A1 (P1, generated now), A2 (minimal-expansion prompt), A3 (deterministic exact-copy template); 432 outputs, 864 M1 calls, J1/J2 critical judge, 5 blind arbitrations (0 unresolved).
- NOT done: M3 (AlignScore/NLI), M4 (local logprob detector), A3+, A4 contrastive drafts, A5 constrained rewrite, B4/B5/G1 baselines, local models, Stages 3 to 5. Reason: round budget and a shared slow endpoint (about 10 judge calls/min); the GPU was not needed for the slice that was run.

## Stage 1: does a whole-message metric predict writer rejection better than the critical-only judge?
Label L1 = writer says the output is not the intended version (195 usable; 146 positive). AUROC, writer-cluster bootstrap B=5,000, seed 20261102, paired delta vs M0 from the same draws.

Sanity gates (100 items): y = writer's sentence under M1-ref passes WMF 97/100 (gate 95%); a different family's sentence fails 100/100 (95%); keyword copy has no unrequested content under M1-free 100/100 (90%). All three pass.

| subset (n, positives) | M0 critical-only | M1-ref (graded) | M1-free (graded) | M2 content-lemma F1 | length ratio |
|---|---|---|---|---|---|
| chip1 all (97, 59) | .53 [.51,.57] | .88 [.84,.93] | .77 [.69,.84] | .60 | .68 |
| chip1 dev P01-10 (50, 35) | .54 | .89 | .69 [.54,.81] | .66 | .67 |
| chip1 holdout P11-20 (47, 24) | .52 | .89 [.81,.96] | .82 [.71,.91] | .49 | .65 |
| all 200 (195, 146) | .74 [.71,.77] | .92 [.89,.94] | .77 [.70,.83] | .63 | .71 |
| bare (98, 87) | .87 | .94 | .68 [.52,.81] | .76 | .81 |

Paired delta vs M0: M1-ref chip1 +.35 [+.29,+.41]; all 200 +.18 [+.15,+.21]. M1-free chip1 +.23 [+.15,+.31]; all 200 +.03 [-.04,+.10]; bare -.20 [-.36,-.05].

Decision rule outcome (as pre-declared, two readings):
- Chip1 reading (bare excluded from the primary, as the plan says): M1-ref validated (holdout .89, delta CI excludes 0); M1-free validated (holdout .82, delta CI excludes 0).
- Literal "full-200" reading: M1-ref validated; M1-free NOT validated (delta CI includes 0), because on the bare channel the critical judge alone already ranks well (a bare input cannot match the intended variant, so rejection tracks the critical label) and M1-free is worse there.
- Headline we can defend: the deployable reference-free M1 is validated for the cue-present (chip1) case only; the reference-based M1 is validated everywhere but needs the writer's sentence, so it is an evaluation tool, not a deployable detector.
- The critical-only judge is near chance for writer rejection on chip1 (AUROC .53): 96% of chip1 outputs keep the critical value, 59% of those are still rejected. This is the insufficiency result (H2): of chip1 outputs with the critical commitment kept, the reference-free judge flags unrequested content in 41% (406 per 1,000), and the writer rejects 59% (591 per 1,000). On bare: 71% flagged, 67% rejected.
- Caveats: binary M1-ref WMF-fail is degenerate (the `dropped` list is non-empty for every CK-true output, because writers' sentences carry details no keyword string can carry), so only the graded score is used. M1-ref sees the same sentence the writer's label is defined against, so its high AUROC partly measures "LLM reproduces the writer's comparison", not an independent signal. Item-level bootstrap CIs are not shown; 5 writers per half have 10 items each.
- SLP cards (L4, n=50 cards x 2 raters = 100 ratings, acceptable != yes, item-cluster bootstrap): M1-free AUROC .84 [.74,.92] versus the critical-only judge .66 [.58,.73]. Descriptive; two raters.

## Stage 2 pilot (gpt-6.1-terra only, chip1, 108 inputs per arm; family-cluster bootstrap B=10,000)
| arm | CK kept | silent reversal / 1,000 | UC flagged / 1,000 | WMF-fail (M1-free) / 1,000 | fragment (no finite verb) | mean word edits to writer sentence | M1-ref score |
|---|---|---|---|---|---|---|---|
| A0 P0 (stored) | .907 | 9 | 259 | 306 | .9% | 4.99 | .489 |
| A1 P1 (existing prompt) | .907 | 0 | 37 | 74 | 10.2% | 5.06 | .496 |
| A2 minimal-expansion | .926 | 0 | 37 | 74 | 3.7% | 4.61 | .500 |
| A3 exact-copy template | .833 | 46 | 83 | 139 | 39.8% | 5.47 | .535 |

Paired contrasts (diff [95% CI], same 54 families):
- UC rate A2 - A0 -22.2 pp [-32.4,-13.0]; A1 - A0 -22.2 pp [-32.4,-13.0]; A2 - A1 0.0 pp [-3.7,+3.7]. A3 - A0 -17.6 pp [-29.6,-6.5].
- CK A2 - A0 +1.9 pp [0,+4.6]; A1 - A0 0.0 [-2.8,+2.8]; A3 - A0 -7.4 pp [-12.0,-2.8].
- Fragments A2 - A1 -6.5 pp [-12.1,-0.9] (A2 is more fluent than P1); A3 - A0 +38.9 pp.
- Edits to writer sentence A2 - A1 -0.44 words [-0.69,-0.24] (small); A2 - A0 -0.38 [-0.59,-0.14].
- M1-ref score (match to what the writer meant): A2 - A0 +.011 [-.015,+.035]; A1 - A0 +.007 [-.024,+.039]. No meaningful gain. A3 +.046 [+.009,+.083] is a metric artifact: it copies the keywords, which the ref scorer counts as less wrong than a wrong guess; its CK and fragment numbers show it is not usable.
- Pilot go/no-go (UC drop >= 5 pp, CK drop <= 3 pp, point estimates, single model): A2 go, A1 go (it is the baseline prompt), A3 no-go.

Reading:
1. Unrequested content in chip1 outputs is real and large under the plain prompt (about 26% of outputs by the deployable judge, 29% among CK-kept) and it is nearly removed (to about 4%) by prompt wording alone.
2. The new minimal-expansion prompt A2 is NOT better than the existing preservation prompt P1 on UC or CK. Its advantage is smaller: fewer fragments (3.7% vs 10.2%) and a slightly closer wording to what the writer wrote. On this slice, "minimal expansion" is not a new strategy; P1 already does it. We would not claim A2 as a contribution.
3. Neither prompt moves the match to the writer's intended sentence (M1-ref .49 to .50). Removing added content does not recover the details the writer meant (e.g. keywords "[MAYBE] guitar music" versus "I think the guitar is in the music room"). Part 18 rejection is mainly about content that cannot be recovered from three keywords; this is where the method does NOT help, and it is the honest limit of any single-output strategy. Whether contrastive drafts (A4) or cue prompts recover it was not tested.
4. The exact-copy default A3 is a poor Pareto point: lowest UC among non-LLM, but 7 pp lower critical-commitment retention (more reversals: 46 vs 9 per 1,000), 40% fragments.

AAC terms (per 1,000 messages, this slice, chip1, one model): P1 or A2 instead of P0 removes about 222 messages with unrequested content and about 9 silent reversals; it costs 0 extra taps by construction, but did not change the expected repair edits (about 5 words per message, driven by compression loss). Clinically weighted and tap-frontier columns are pending (SLP weights not applied; no always-ask/random-ask frontier run).

## Where it does not help / limits
- bare channel: the cue is missing and M1-free is not a validated predictor there; Stage 2 did not include bare.
- by dimension (n=18 outputs per cell, descriptive): UC is high under A0 for polarity (50%), speech_act, time_quantity, politeness (28%); A3 destroys speech_act (CK .56) and time_quantity (fragments 89%). certainty has CK .50 under every arm (no arm fixes certainty on this slice).
- single model; one run per output (the API ignores seeds, so A0 vs fresh generations differ partly by sampling; A0 is stored data from an earlier run); family near-duplicate components not controlled; M1 judge is one LLM family and also the validation instrument is LLM-judged, so Stage 2 effects are provisional until R-WM-1 (human check) returns.
- Goodhart guard not exercised (no in-loop detector used).
- Operational: arbiter view printed one dimension header over items of two dimensions; the first draft of arbiter decisions was rewritten before any analysis (logged in PLAN.md). The Stage 2 pilot's real examples (declared rule: first by hash rank per dimension with A0 CK true and UC true) are in `stage2_examples.md`.

## Recommended next steps
1. Do not spend Stage 3 on A2 as a "new method"; instead use the validated metric to benchmark A4 (contrastive drafts) and A5 against P1 (the strong baseline), since single-output prompting is exhausted on UC and does not move writer match.
2. Run M1-free for the 4-model comparison only on chip1; add the human R-WM-1 check on P1 vs A4 outputs.
3. Local-model arms and M4 detector need the GPU lock (hw2 may hold it).
