# Item verification (independent verifier, 2026-10-31)

Scope: all 96 families in data/items/{pilot,dev,test}.jsonl, read by hand against SPEC v0.1 and D-001..D-008.
No LLM APIs and no GPU servers were used. I checked six things: (1) genuine ambiguity of `bare`; (2) minimality;
(3) chips/all_chips vs source on the general dimensions (polarity, speech_act, agent, certainty, politeness);
(4) the noncritical word; (5) naturalness, adult framing, stereotypes and domain spread; (6) spec values and label clarity.

Edits were applied **only to test** via `src/authoring/build_dev_test.py` (the source of truth). pilot.jsonl was not touched.
dev.jsonl was regenerated and is byte-identical to before.

## Summary stats

| split | n | OK | FIX (applied) | FIX (proposed, not applied) | DROP |
|---|---|---|---|---|---|
| pilot | 24 | 22 | 0 (frozen) | 2 | 0 |
| dev | 12 | 12 | 0 | 0 | 0 |
| test | 60 | 53 | 6 | 1 | 0 |
| **all** | **96** | **87** | **6** | **3** | **0** |

Validator after the changes: `python3 src/validate_items.py data/items/{pilot,dev,test}.jsonl` gives 0 errors and 1 warning.
The warning (act-07: "bare word 'bring' matches one variant's exact form") is a heuristic false positive: `bring` is already the base form, and the check fires because the word ends in "-ing".

Most common problems:
1. **Addressee-subject declaratives that read as directives** ("You'll pay…", "You'll walk…", "You'll call me…", "You're coming…").
   A blind annotator can label a faithful output request/command. In agent families that shows up as a false speech-act stance
   addition; in speech-act families it shows up as a false Violation. Affected: agt-09, agt-15, act-09 (test); act-01, and more weakly agt-01, agt-03 (pilot); agt-11 (test).
2. **Label-clarity risks on general dimensions**, where the all_chips value is defensible but a blind annotator could easily pick another one:
   generic "it's normal to feel" coded [THEY] (act-12), "my team" coded [WE] (cer-14), "You can pick me up" as a statement (act-02),
   "Can you…" as [PLAIN] (act-02).
3. **Codebook-level conventions that need to be stated in the judge prompt** (CB-1..CB-5 below). These affect many families
   and are better solved once than per item.
4. Minor: adult framing (agt-13 teacher/classroom), and an inconsistent use of non-scored chips ([PAST]/[LATER]/[MUST]/[WANT]).

Things that are fine across the set: every family has a genuine two-way collision on `bare`, and none is close to trivial.
I found no extra polarity, certainty or politeness differences beyond the documented refusal/polarity co-variation
(act-03/05/10/16) and the documented shared negation in pol2-12. Noncritical words do not encode the critical dimension.
No item uses a stereotyped "autistic style". Sensory items (fan, TV, perfume, headphones, hearing aid) are framed as ordinary
adult requests or reports. Domain spread is broad. Health is the largest share (15/60 test notes mention health; pilot 5/24),
and school is now small (pol-16, cer-15, pol2-13). Health is heavy but defensible for AAC, so I left it as is.

## Change log (test only, applied in src/authoring/build_dev_test.py)

| id | family | before | after | reason |
|---|---|---|---|---|
| V-01 | agt-09 | "I'll pay for the taxi home." / "You'll pay for the taxi home." ([LATER]) | "I paid for the taxi home." / "You paid for the taxi home." ([PAST]) | "You'll pay…" reads as a directive, which would contradict the [TELL] spec. Past tense makes both variants plain statements; bare `pay taxi` and noncritical `home` are unchanged. |
| V-02 | agt-13 | "I told the teacher about the classroom noise." / "They told the teacher…"; bare `tell teacher noise`, noncritical `classroom` | "I told the manager about the office noise." / "She told the manager about the office noise."; bare `tell manager noise`, noncritical `office` | The old version had child/K-12 framing and a "They" with no antecedent, which made the third-party reading weak. "She" uses the [THEY] convention from agt-02 and agt-08. Domain changes from school to work. |
| V-03 | agt-15 | "I'll walk the dog after lunch." / "You'll walk the dog after lunch." ([LATER]) | "I walked the dog after lunch." / "You walked the dog after lunch." ([PAST]) | The author's own note said B "can be heard as an instruction"; past tense removes that reading. |
| V-04 | cer-14 | "I think my team won the pub quiz." / "My team won the pub quiz."; bare `team win quiz` | "I think we won the pub quiz." / "We won the pub quiz."; bare `win quiz` | A blind annotator could label "my team" as either we/joint or third party, while all_chips says [WE]. "we" pins the agent. |
| V-05 | act-07 | B "I can bring my dog tomorrow." | B "I'm bringing my dog tomorrow." | "I can bring X" is easily labeled offer/suggestion instead of statement, and the critical dimension here is speech act. The fix matches the act-04 and act-13 pattern (plan statement vs permission question). |
| V-06 | act-12 | all_chips ["[TELL]","[THEY]"] / ["[?]","[THEY]"] | ["[TELL]"] / ["[?]"] | In generic "It's normal to feel dizzy…" the agent is unspecified, not third party, and the vocabulary has no chip for unspecified. With [THEY] kept, every faithful output would get a spurious agent stance addition. |

Notes text was updated in the builder for each changed family. Sources still have 4-12 words, and noncritical words are still present.

## Proposed fixes not applied

- **act-09 (test), FIX, needs author decision.** B "You'll call me when the test results come in." is the directive problem again, but this time on
  the *critical* dimension: a faithful output may be extracted as request/command, which is scored as a Violation. No minimal rewrite is
  clean. Options: (a) B = "You always call me when the test results come in." (a habitual statement; the extra word "always" is a
  speech-act cue in the same way "yes"/"no" are); or (b) replace the family with a request vs question pair. Until it is fixed, add a codebook rule (CB-1) and
  report act-09 with a sensitivity analysis.
- **act-01 (pilot, frozen), FIX at analysis time.** A "You're coming to dinner tonight." can be read as insistence (request/command) rather than a
  statement. Apply CB-1 in the judge prompt and report act-01 A Violations with and without request/command counted as statement.
- **act-02 (pilot, frozen), FIX at analysis time.** B "You can pick me up after work today." is likely to be extracted as offer/suggestion (granting permission or proposing).
  Run a sensitivity analysis that treats offer/suggestion as matching statement for act-02 B. Separately, A "Can you…" is coded [PLAIN],
  but the label schema's "softened request (could you/would you mind)" may catch "can you"; see CB-2.

## Codebook rules to add to the judge/annotator instructions (they fix many items at once)

- **CB-1** A declarative with a "you" subject ("You need to…", "You're driving…", "You'll…", "You're coming…") is a *statement* unless it is
  imperative mood or a question-form request. Affects agt-01, agt-03, act-01 (pilot); agt-11, act-09 (test).
- **CB-2** "Can you/Can I…?" alone is a conventional request or question with politeness = none. Only could/would/would you mind/please/thanks
  count as politeness (this matches D-007 and the act-02 notes). Affects act-02 (pilot), pol2 softener items.
- **CB-3** In hedged sentences ("I think X", "Maybe X"), label the agent of the embedded clause, not "I" of "I think". Without this rule,
  every hedged B in cer-02/06/10/12/16 and pilot cer-02 gets a speaker-agent stance addition that its plain partner does not. That is
  an asymmetric artifact correlated with the critical contrast.
- **CB-4** Inanimate subjects (lift, bus, sauce, soap, clinic, refund, taxi ride, hearing aid, inhaler, pool, train, milk) are labeled
  third party, while possessed body parts (back, cut, ankle) are coded speaker ([I]). Tell annotators this. Also watch for outputs where
  [THEY] in `chipall` induces an invented human "they" (e.g. "They fixed the lift"); these should be caught as added_content.
- **CB-5** The agent is the doer of the content verb, not of the speech act: in "No, you can't borrow my car" the agent is the addressee
  (act-16), and in "I still owe you…" the agent is the speaker (tq-09).

Non-scored inconsistency (report only; do not change the frozen pilot): time chips and [MUST]/[WANT] are applied unevenly in all_chips.
For example, act-07/13/16 have future time words but no [LATER]; pol-03 "need help" and tq-02 "We need…" have no [MUST], while agt-01, tq-05 and cer-15 have it;
pol-01 has no [WANT], while pol-11 has it. These are not general label dimensions, so scoring is unaffected, but `chipall` inputs vary in specificity
across families. cer-15 B's chipall "[MAYBE] [MUST]" for "might need" is a slightly odd combination.

## Per-family verdicts

### Pilot (report only; file not edited)

| family | verdict | reason |
|---|---|---|
| pol-01 | OK | Cold vs stuffy room; both readings natural. |
| pol-02 | OK | Nurse check-in licenses both answers; [I] = experiencer (CB-4). |
| pol-03 | OK | Declining vs asking for help; good autonomy item. |
| pol-04 | OK | Clean; [PAST] shared. |
| agt-01 | OK | Needs CB-1 ("You need to call…" = statement). |
| agt-02 | OK | my/her possessive swap is unavoidable for a who-forgot-whose pair; bare uses inflected "forgot" (shared). |
| agt-03 | OK | Needs CB-1 for B "You're driving us…". |
| agt-04 | OK | Clean. |
| cer-01 | OK | B double hedge (think + might) is stronger than A's single plain form; acceptable. Needs CB-3. |
| cer-02 | OK | Same double hedge; needs CB-3. |
| cer-03 | OK | Clean single-adverb hedge. |
| cer-04 | OK | In a cafe a question reading ("Does it have peanuts?") is a strong third reading; still a genuine A/B collision. |
| tq-01 | OK | Clean. |
| tq-02 | OK | Clean number pair. |
| tq-03 | OK | Clean. |
| tq-04 | OK | Safety-relevant; clean. |
| act-01 | FIX | A "You're coming to dinner tonight." can be read as request/command, so the critical label is at risk; CB-1 plus sensitivity analysis. |
| act-02 | FIX | B "You can pick me up…" is likely labeled offer/suggestion; A's "Can you" politeness is ambiguous (CB-2). |
| act-03 | OK | Refusal/polarity co-variation documented. |
| act-04 | OK | Clean; codebook note on permission question already in notes. |
| pol2-01 | OK | Clean. |
| pol2-02 | OK | Clean softener; context does not pick form. |
| pol2-03 | OK | Clean. |
| pol2-04 | OK | Clean. |

### Dev (report only; regenerated file unchanged)

| family | verdict | reason |
|---|---|---|
| pol-05 | OK | Reverse-default direction; natural. |
| pol-06 | OK | Device coded [THEY] while body parts are [I]; covered by CB-4. |
| agt-05 | OK | Complaint vs report; clean. |
| agt-06 | OK | "Permission form" leans school-child, but a parent reading is adult; minor. |
| cer-05 | OK | Clean. |
| cer-06 | OK | Clean; CB-3. |
| tq-05 | OK | Clean. |
| tq-06 | OK | Clean. |
| act-05 | OK | Co-variation documented. |
| act-06 | OK | Clean. |
| pol2-05 | OK | "thanks" as the marker; documented. |
| pol2-06 | OK | Clean. |

### Test (post-fix status in brackets)

| family | verdict | reason |
|---|---|---|
| pol-07 | OK | "would like" request reading is a known confound; documented. |
| pol-08 | OK | "again" fits both; good counter-direction item. |
| pol-09 | OK | Lifted vs new restriction; "now" fits both. |
| pol-10 | OK | Clean. |
| pol-11 | OK | Boundary item; context sets topic only. |
| pol-12 | OK | Clean. |
| pol-13 | OK | Clean. |
| pol-14 | OK | Clean. |
| pol-15 | OK | Context ("two weeks") supports both. |
| pol-16 | OK | Clean; adult student framing. |
| agt-07 | OK | Clean. |
| agt-08 | OK | Autonomy-relevant; [THEY]=she. |
| agt-09 | FIX [applied V-01] | "You'll pay…" directive reading; moved to past. |
| agt-10 | OK | Clean. |
| agt-11 | OK | "You need to finish…" needs CB-1; no clean minimal rewrite (past would drop [MUST]). |
| agt-12 | OK | Clean we vs I. |
| agt-13 | FIX [applied V-02] | Child framing and an antecedent-less "They"; moved to work/manager/she. |
| agt-14 | OK | Clean. |
| agt-15 | FIX [applied V-03] | "You'll walk the dog" instruction reading; moved to past. |
| agt-16 | OK | Context makes "They" (clinic) plausible. |
| cer-07 | OK | Clean. |
| cer-08 | OK | "last" in "last train" is noncritical; fine. |
| cer-09 | OK | Clean. |
| cer-10 | OK | CB-3. |
| cer-11 | OK | Clean. |
| cer-12 | OK | CB-3. |
| cer-13 | OK | Clean; [I] for body part (CB-4). |
| cer-14 | FIX [applied V-04] | "my team" agent ambiguity; now "we". |
| cer-15 | OK | Good accommodation item; [MUST]+[MAYBE] chipall slightly odd (non-scored). |
| cer-16 | OK | CB-3/CB-4. |
| tq-07 | OK | Clean. |
| tq-08 | OK | Clean. |
| tq-09 | OK | CB-5 (creditor is not the agent). |
| tq-10 | OK | Safety-relevant; "evening" is neutral given the context. |
| tq-11 | OK | Clean; CB-4. |
| tq-12 | OK | Clean. |
| tq-13 | OK | Plural "sugars" avoids a number leak. |
| tq-14 | OK | Clean. |
| tq-15 | OK | Clean. |
| tq-16 | OK | Clean. |
| act-07 | FIX [applied V-05] | B "I can bring…" could be labeled offer; now "I'm bringing…". |
| act-08 | OK | Clean. |
| act-09 | FIX [proposed, not applied] | B "You'll call me…" may be extracted as request/command, a false Violation on the critical dimension; see options above. |
| act-10 | OK | Co-variation documented. |
| act-11 | OK | Adult carer instruction; clean. |
| act-12 | FIX [applied V-06] | Generic agent miscoded [THEY]; removed. Statement reading is weaker than the question reading but still plausible (relaying advice). |
| act-13 | OK | Clean boundary vs permission. |
| act-14 | OK | "still" leans slightly toward the question reading ("Are we still…?") but fits both. |
| act-15 | OK | Clean. |
| act-16 | OK | Context blocks the role-reversal reading; needs CB-5 for agent. |
| pol2-07 | OK | Plain form is blunt but a legitimate choice. |
| pol2-08 | OK | Clean. |
| pol2-09 | OK | "to me" is slightly stilted, but it is needed for the 4-word minimum. |
| pol2-10 | OK | Clean. |
| pol2-11 | OK | Clean. |
| pol2-12 | OK | Shared negation documented. |
| pol2-13 | OK | Clean. |
| pol2-14 | OK | Highly AAC-relevant; adult. |
| pol2-15 | OK | Clean. |
| pol2-16 | OK | Clean. |


