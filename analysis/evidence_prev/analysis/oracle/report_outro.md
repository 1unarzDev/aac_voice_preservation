
## 7. What this licenses us to claim

Licensed now (machine evidence; describe it as such):
- The production oracle (J1+J2, arbiter, contract code) **satisfies the identity relation on all 120 authored
  test sources**: 0/120 contract false alarms, upper 95% bound 3%. It **flags 120/120 scoped single-value
  mutations** of those sources (lower bound 97%) on polarity, agent, certainty, politeness, speech act and
  time/quantity. This is minimum-functionality evidence on clean authored sentences. It is not an error rate on
  model outputs.
- On new balanced challenges, the oracle separates embedded actors, question vs request, and presence vs absence of
  explicit politeness markers without error (6/6 and 0/6 in each group). The pooled PREREG challenge gate passes
  at 22/24 and 0/24, with no slack.
- Against a 3-model codex panel majority on the 163 probability-sampled main1 units, judge labels agree at
  kappa >= .90 (design-weighted >= .97) on every extraction dimension. Recomputing the contract verdicts from panel
  labels changes Violation for about 1% of the weighted output population and constraint_preserving for about 3%.
  This bounds how much the reported verdicts *could* move under this alternative labeller. It does not show that
  either labeller is right.

Not licensed:
- **"Validated against human gold" or "passes the kappa >= .6 gate."** There are zero human returns. Every panel
  number is machine-machine agreement among GPT-family models, which share the codebook and probably some errors
  (finding 3). Per PREREG, headline automated claims stay provisional until the human double-coding of gold_core
  arrives. Then run `score_gold.py --human annotation/returns/*.csv --panel ...`. The gate is evaluated only in the
  human section.
- **Any primary speech-act claim that uses the refusal/acceptance families**, including the "5/8 refusals survive"
  result. The relaxed acceptance predicate misses 2/2 statement substitutions on keyed items. The raw predicate
  instead fails the D-015 sentence when J1 is used alone. Report act-10/act-16 only as sensitivity, both raw and
  relaxed: P0 full critical match is 13/16 relaxed against 7/16 raw. On the 8 remaining speech-act families, P0
  full critical match is .984 and chipall is .906, against .950 and .850 with the quarantined families included.
- **Added-content headlines.** Panel alpha is .41, judge kappa .76, 11% of sampled units are unlabelled, and there
  are false positives on keyword-complete challenges.
- **Fine certainty-degree claims** (plain vs emphatic). Panel-vs-judge disagreements concentrate there
  (plain/hedged -> emphatic), and the contract treats emphatic as honouring plain by design.
- **Idiomatic negation and vague quantity.** On ch-08 ("can't wait") and ch-22 ("a couple of") both the judge and
  the panel disagree with the key. Treat them as known oracle blind spots.

Remaining W-A work: human double-coding of gold_core (100 items) with `score_gold.py --human`; a symmetric
acceptance/refusal predicate, or a separate response-particle feature, that passes both the statement-substitution
mutants and the identity relation using J1 or J2 alone; and an added-content tiebreak policy.

## Files

- annotation/challenge_items_r2.jsonl: 48 new keyed challenges. analysis/oracle/source_mutations.jsonl: 120 keyed
  mutations. analysis/oracle/challenge_keys_frozen.sha256: hashes and freeze time.
- runs/oracle_inject/, runs/oracle_challenges/: synthetic runs (outputs, judgments, arbiter.jsonl with the 3
  arbiter rows from a fresh blind Claude subagent that saw only the codebook, the text and the J1/J2 labels).
- analysis/oracle/injection_results.csv, challenge_results.csv, verdict_validation{,_sens_sol_astra}.csv.
- annotation/judge_validation_main1{,_sens_sol_astra}.json/.csv (sections `human` and `panel`, kept separate),
  annotation/panel_majority_main1{,_sens_sol_astra}.csv (provenance = machine).
- Code: src/oracle_wa.py, src/oracle_report.py (new); src/score_gold.py (`--human`/`--panel`, arbiter fill,
  weighted metrics, invalid-option handling); src/attribute.py (quarantine flag and endpoints);
  src/analyze.py (quarantine sensitivity table).
