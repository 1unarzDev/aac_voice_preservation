# S1 detector development check

The uniform random sample is fixed by seed 20261031 over train, dev, then test
source lines. All 150 messages were read by the executing LLM before its initial
detector predictions were inspected. The compact source-only labels are stored
in `manual_labels_compact.txt`; they have not been rewritten to match predictions.
The full CSV expands all seven labels, including empty time/quantity lists.

This is a same-LLM, unblinded development check. It is neither independent human
validation nor an unbiased estimate of performance after tuning. The random
sample has no positive quantity labels. Generated numeric diagnostics only check
code behavior and do not establish natural-text precision or recall.

One initial-to-final detector revision addressed:

- Question/request precedence: wh-time questions with “will you” stay questions;
  direct interrogative wh dependents survive discourse preambles; “I would like”
  is a conventional request, allowing an intervening intensifier.
- Main-clause selection: prefer the first grammatical matrix subject/predicate
  when spaCy promotes a later paratactic clause; respect initial imperatives and
  avoid conditional subordinate subjects. Handle contracted wh copulas and the
  narrow spelling patterns “ill be” and “Its ...ing”.
- Tense: use finite forms rather than the Present feature of VBG participles;
  do-support in imperatives is not a present-time commitment.
- Refusal: negative inability (“I won't be able”) and protective commitments
  (“I won't let you suffer”) are not automatically declining; an initial
  “No, I can't” is a refusal.
- Imperatives: base-form “read” is allowed despite past-tense parser tagging;
  “need some water” remains an underspecified statement fragment. Formulaic
  “Have a good/great ...” greetings are statements. This is a pilot convention,
  not a claim that all fragmentary uses have one intended speech act.
- Politeness: permit “I would really like” as a softened request.

The detector retains the original lexicon's longest-first, non-overlapping
matches as routing features. Interpreted epistemic certainty excludes obvious
physical “feel”, directional “about/around”, ability “can”, deontic “should”,
habitual adverbs, apologies, and bare downtoners. “Would like” is a request
softener, not epistemic uncertainty. Certainty is n/a for questions/requests.
Boosters inside a matched longer hedge, e.g. “I'm not sure”, are suppressed.
The inherited lexicon's bibliographic comments were not reverified in S1 and
must not be treated as independently checked references.

Residual differences are intentionally preserved in `detector_disagreements.csv`:

- In “i need you to stay with me tonight, i was scared last night”, the detector
  includes past from explicit “last night”; the original LLM label included only
  main-clause present and “tonight” future. The detector's extra past follows
  the across-message time-word rule. The frozen LLM label likely omitted this.
- Three “thank you” formulas receive finite present-tense cues from spaCy;
  the LLM treated the formulas as lacking explicit time. This remains a known
  pragmatic false positive rather than another tuning iteration.

Additional limitations: negation scope is unresolved, and lexical negation in a
softener (“if you don't mind”) still counts as an explicit negation cue. Main
agent labels are grammatical roles rather than resolution of the eventual
action's agent in every embedding. Time categories are coarse: “today” and
“tonight” are conventionally mapped to present and future, and exact dates or
temporal referents are not encoded by chips. A retained token does not guarantee
that its original scope, syntax, role, or sense can be recovered from keywords.
Each hedge phrase requires all its matched carrier tokens, so results depend on
the operational definition of cue survival.

Reproduce with `python -m src.s1_analyze --initial`, then
`python -m src.s1_analyze`, then `python -m src.s1_verify`, after activating the
project venv. Revision 0 remains implemented for auditing the initial predictions.
