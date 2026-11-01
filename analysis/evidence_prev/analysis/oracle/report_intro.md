# W-A oracle validation report (PREREG_R2)

Date: 2026-11-01. Author: W-A oracle validation engineer (Claude). No GPU servers were started. The judge ran at
concurrency 8: 30 API calls, 1 transient failure that was retried. The production judge (gpt-6.1-sol, J1+J2,
effort low), the layer0 tiebreak, the arbiter rule and src/attribute.py are unchanged.

Reproduce:
```
python src/oracle_wa.py prepare && python src/oracle_wa.py judge && python src/oracle_wa.py arbiter-todo
python src/score_gold.py --run main1 --panel 'annotation/returns_codex/*.csv' --challenge-judgments runs/oracle_challenges
python src/score_gold.py --run main1 --panel 'annotation/returns_codex/*.csv' --challenge-judgments runs/oracle_challenges \
    --panel-members C-gpt-5.6-sol,C-gpt-6-astra --tag _sens_sol_astra
PYTHONPATH=src python src/analyze.py --table runs/main1/scored.parquet --tag main1
python src/oracle_report.py
```

## Headline results

| check | result | gate |
|---|---|---|
| Identity: 120 verbatim sources scored as `full` outputs | 0/120 contract false alarms [0.00, 0.03]; 0 added content | none set; necessary condition met |
| Scoped mutation: 120 hand-written single-value flips | 120/120 detected as Violation [0.97, 1.00] | none set |
| New challenges: mutants detected (production rule) | 22/24 [0.74, 0.98] | >= 22/24: **pass, with no slack** |
| New challenges: control false alarms | 0/24 [0.00, 0.14] | <= 1/24: pass |
| New challenges, acceptance group | 4/6 mutants detected; both misses are statement substitutions passed by the D-015 relaxation | per-group: **not met** |
| Same, raw rule (no D-015 relaxation) | 24/24 detected, 0/24 false alarms | pass |
| Round-1 challenges, critical label = key | 22/24 [0.74, 0.98] | none set |
| Judge vs codex-panel majority, kappa (sampled, unweighted / design-weighted) | critical .97/.98; polarity 1.0/1.0; speech_act .95/.97; agent .96/.97; certainty .91/.97; politeness .96/.97; added_content .76/.80 | kappa >= .6 vs **human** gold: **not evaluable, 0 human returns** |
| Contract verdicts recomputed from panel labels | Violation flips in 2/105 units (1.3% weighted); constraint_preserving 4/105 (2.7%); Assumption 1/58 (0.4%) | none set |

Four findings matter most:

1. **The oracle is strong on clean single-cue contrasts.** Identity, mutation, embedded actor, question vs request
   and mitigation all came out perfect. Both identity and mutation on act-16 B, however, depend on the arbiter. On
   "Yes, you can borrow my car this weekend." J1 said *statement*. On the mutant "Sorry, you can't borrow my car
   this weekend." J1 also said *statement*. Under the production acceptance~statement relaxation, J1's label would
   have **passed the refusal mutant as an honoured acceptance**. Only the arbiter's *refusal* label caught it.
2. **The D-015 acceptance repair destroys sensitivity to statement substitution.** "You borrowed my car this
   weekend." and "Of course, I helped you move on Saturday." were both correctly labelled *statement*, and both
   satisfy an *acceptance* contract under the production rule. This is the reviewers' "arbitrary statements satisfy
   acceptance" concern, now shown on keyed items. The quarantine (section 6) is therefore required, not optional.
3. **Panel agreement does not validate shared errors.** On round-1 challenges the judge is wrong against the key
   on ch-08 ("I can't wait..." -> negated) and ch-22 ("a couple of" -> two). The 3-model panel majority makes the
   same two errors, so judge-vs-panel challenge accuracy is 24/24. gpt-5.6-sol and gpt-6-astra agree with each other
   and with the judge at kappa ~.95-1.0 on most dims. This is consistent with correlated GPT-family errors as much
   as with correctness.
4. **added_content is the weakest dimension.** The panel's own alpha is .41, and judge-vs-majority kappa is .76.
   18/163 sampled units have no production added_content label, because J1 != J2 and there is no tiebreak. On the
   new challenges the judge called three keyword-complete sentences added content ("after work" from `pick up
   work`, "check if" from `pharmacy open sunday`).

Data-quality note on the panel: in C_gpt-6-luna_core.csv, 28/100 critical answers are not options of the item
(for example "past" for an agent question). They are dropped as invalid. Luna's general-dim agreement in that one
file is also low (0.61-0.90 raw agreement with sol, against 0.86-1.0 in its extra files). The file looks partly
misaligned or degraded, but it is not a simple row shift. A sol+astra-only sensitivity is reported throughout.

## 1. Challenge-set construction (task 1)

annotation/challenge_items_r2.jsonl has 48 hand-authored sentences in 4 groups. Each group has 6 valid controls
and 6 single-feature mutants, and each mutant has a `pair` (its control), a `mutated_feature` and a
`contract_value` (the control's critical value). The format is the round-1 format (cid, text, dimension, key,
probe) plus `group`, `role`, `pair`, `mutated_feature`, `critical_options` and `input_text` (keywords for the
added-content pass). Keys and the 120 source mutations were hashed before the first judge call
(analysis/oracle/challenge_keys_frozen.sha256).

- acceptance (speech_act). Controls: yes/sure/okay/of course/fine plus a commitment, including the D-015 sentence.
  Mutants: 2 refusals, 1 question, 1 let's-suggestion, and 2 statement substitutions that report, rather than
  accept (the D-015 probes).
- embedded_actor (agent). Controls: want-you-to, X-wants-me-to, asked-Dad-to (CB-7 generalised), I-think-you-should
  (CB-3), maybe-the-nurse (CB-3), told-you-to (CB-7). Mutants change only the embedded doer, or swap the roles.
- question_request (speech_act). 3 question controls (can-I, information, did-you) and 3 request controls
  (can-you, could-you, would-you). Each mutant crosses to the other class by a one-word subject or auxiliary
  change, or a mood change.
- mitigation (politeness). 3 polite controls (could you, please, sorry) whose mutants remove the marker; 3 plain
  controls (imperative, CB-2 can-you, statement) whose mutants add please / would you mind / thanks.
