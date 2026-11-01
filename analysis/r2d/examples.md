# W-D stored examples

These are selected counterexamples, not representative utterances. Selection is declared here and implemented in `src/r2d_analyze.py`: within each encoding × protected dimension × transition direction, select the first eligible stored pair ordered by physical scenario ID, fixed model order (Qwen, Llama, Gemma, Terra), encoding, dimension, YES/NOT|I/YOU cell string, and draw. Select one repeat-disagreement pair per cue endpoint × encoding × dimension in the same scenario/model order, then input text. Select one broad-regex literalization example per encoding ordered by scenario, model, input text, draw. No text is rewritten. Empty eligible strata are reported. Full paired encoding controls are shown for every transition example.

Labels: `runs/r2d1/scored.parquet` focal `critical`, agreement else J1 fallback; general `speech_act` uses the stored J1/J2/layer0 resolution. Exact hashes are in `primary.json`. Eligibility rates below use all aligned pairs in that encoding × dimension; selected-model rates are also given.

## TELL / polarity / damage

Eligible: 0/2560 (0.00 [0.00, 0.00]%), across 80 scenarios.

No eligible example.

## TELL / polarity / recovery

Eligible: 0/2560 (0.00 [0.00, 0.00]%), across 80 scenarios.

No eligible example.

## TELL / agent / damage

Eligible: 100/2560 (3.91 [3.01, 4.84]%), across 80 scenarios.

Selected: `r2d-002`, `r2d-002-agt-not`, variant `A`, cell `NOT|YOU`, `qwen2.5-7b`, `d1`. Selected-model stratum: 84/640.

**[STATEMENT]**

- Input: `Keywords: [STATEMENT] [YOU] book taxi`
- Output `11b8b909dbce79ad`: "You will book a taxi."
- Protected label: `addressee`; pass: `True`; J1/J2: `addressee` / `addressee`; source: `agree`; speech_act: `statement`.
- Input: `Keywords: [NOT] [STATEMENT] [YOU] book taxi`
- Output `b614606c22ec3f69`: "You are not booking a taxi."
- Protected label: `addressee`; pass: `True`; J1/J2: `addressee` / `addressee`; source: `agree`; speech_act: `statement`.

**[TELL]**

- Input: `Keywords: [TELL] [YOU] book taxi`
- Output `8568bb2220357144`: "Tell you to book a taxi."
- Protected label: `addressee`; pass: `True`; J1/J2: `addressee` / `addressee`; source: `agree`; speech_act: `request/command`.
- Input: `Keywords: [NOT] [TELL] [YOU] book taxi`
- Output `240d6158fd73e0b3`: "I don't tell you to book a taxi."
- Protected label: `speaker`; pass: `False`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.

## TELL / agent / recovery

Eligible: 22/2560 (0.86 [0.23, 1.56]%), across 80 scenarios.

Selected: `r2d-002`, `r2d-002-agt-not`, variant `B`, cell `NOT|I`, `llama3.1-8b`, `d1`. Selected-model stratum: 8/640.

**[STATEMENT]**

- Input: `Keywords: [STATEMENT] [I] book taxi`
- Output `7785d7cb8bd331d6`: "I book a taxi."
- Protected label: `speaker`; pass: `True`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.
- Input: `Keywords: [NOT] [STATEMENT] [I] book taxi`
- Output `936ac2d23e11461d`: "I don't want to take a taxi."
- Protected label: `speaker`; pass: `True`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.

**[TELL]**

- Input: `Keywords: [TELL] [I] book taxi`
- Output `afb1a4f5bfeaad76`: "I tell you to book a taxi."
- Protected label: `addressee`; pass: `False`; J1/J2: `addressee` / `addressee`; source: `agree`; speech_act: `statement`.
- Input: `Keywords: [NOT] [TELL] [I] book taxi`
- Output `3289cef300b1b168`: "I don't want to tell you to book a taxi."
- Protected label: `speaker`; pass: `True`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.

## STATEMENT / polarity / damage

Eligible: 55/2560 (2.15 [1.56, 2.77]%), across 80 scenarios.

Selected: `r2d-001`, `r2d-001-pol-you`, variant `B`, cell `NOT|YOU`, `llama3.1-8b`, `d1`. Selected-model stratum: 55/640.

**[STATEMENT]**

- Input: `Keywords: [NOT] [STATEMENT] lock door`
- Output `7275441a9c50dd77`: "I will not lock the door."
- Protected label: `negated`; pass: `True`; J1/J2: `negated` / `negated`; source: `agree`; speech_act: `refusal`.
- Input: `Keywords: [NOT] [STATEMENT] [YOU] lock door`
- Output `8b3a5cb35f01d3f7`: "You lock the door."
- Protected label: `affirmative`; pass: `False`; J1/J2: `affirmative` / `affirmative`; source: `agree`; speech_act: `statement`.

**[TELL]**

- Input: `Keywords: [NOT] [TELL] lock door`
- Output `dda8bece0457b1ed`: "I will not lock the door."
- Protected label: `negated`; pass: `True`; J1/J2: `negated` / `negated`; source: `agree`; speech_act: `refusal`.
- Input: `Keywords: [NOT] [TELL] [YOU] lock door`
- Output `7d9c8e0ac0f42f80`: "You should not lock the door."
- Protected label: `negated`; pass: `True`; J1/J2: `negated` / `negated`; source: `agree`; speech_act: `statement`.

## STATEMENT / polarity / recovery

Eligible: 0/2560 (0.00 [0.00, 0.00]%), across 80 scenarios.

No eligible example.

## STATEMENT / agent / damage

Eligible: 4/2560 (0.16 [0.00, 0.47]%), across 80 scenarios.

Selected: `r2d-079`, `r2d-079-agt-not`, variant `A`, cell `NOT|I`, `llama3.1-8b`, `d1`. Selected-model stratum: 4/640.

**[STATEMENT]**

- Input: `Keywords: [STATEMENT] [I] report streetlight`
- Output `42d1b70de746ba0f`: "I report the streetlight."
- Protected label: `speaker`; pass: `True`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.
- Input: `Keywords: [NOT] [STATEMENT] [I] report streetlight`
- Output `263727572feadfaf`: "The streetlight is not on."
- Protected label: `third party`; pass: `False`; J1/J2: `third party` / `third party`; source: `agree`; speech_act: `statement`.

**[TELL]**

- Input: `Keywords: [TELL] [I] report streetlight`
- Output `d427bc98c790a278`: "I report the streetlight."
- Protected label: `speaker`; pass: `True`; J1/J2: `speaker` / `speaker`; source: `agree`; speech_act: `statement`.
- Input: `Keywords: [NOT] [TELL] [I] report streetlight`
- Output `dfb3c7856689d57d`: "The streetlight is not on."
- Protected label: `third party`; pass: `False`; J1/J2: `third party` / `third party`; source: `agree`; speech_act: `statement`.

## STATEMENT / agent / recovery

Eligible: 0/2560 (0.00 [0.00, 0.00]%), across 80 scenarios.

No eligible example.

**CB-7 caveat:** the selected Qwen TELL damage example labels 'I don't tell you to book a taxi.' as agent=speaker in both J1 and J2. CB-7's embedded-doer rule instead points to addressee. This is an observed scoring concern, not an independently adjudicated correction. The stored scores are retained; selected TELL transitions must not be presented as verified semantic damage.

## single / TELL / polarity / repeat disagreement

Eligible unique repeat inputs: 0/640.

No eligible example.

## single / TELL / agent / repeat disagreement

Eligible unique repeat inputs: 0/640.

No eligible example.

## single / STATEMENT / polarity / repeat disagreement

Eligible unique repeat inputs: 0/640.

No eligible example.

## single / STATEMENT / agent / repeat disagreement

Eligible unique repeat inputs: 0/640.

No eligible example.

## both / TELL / polarity / repeat disagreement

Eligible unique repeat inputs: 0/1280.

No eligible example.

## both / TELL / agent / repeat disagreement

Eligible unique repeat inputs: 14/1280.

`r2d-005`, `qwen2.5-7b`. Input: `Keywords: [NOT] [TELL] [YOU] return parcel`.

- d1, `75eb4a06d9cfecc9`: "I don't tell you to return the parcel."; label `speaker`, pass `False`.
- d2, `2f92e47b4d43e167`: "Do not tell me to return the parcel."; label `addressee`, pass `True`.

## both / STATEMENT / polarity / repeat disagreement

Eligible unique repeat inputs: 5/1280.

`r2d-028`, `llama3.1-8b`. Input: `Keywords: [NOT] [STATEMENT] [YOU] tidy shed`.

- d1, `7cfbc3bed63a01ff`: "You tidy the shed."; label `affirmative`, pass `False`.
- d2, `6666de3c1f5af9ef`: "You don't tidy the shed."; label `negated`, pass `True`.

## both / STATEMENT / agent / repeat disagreement

Eligible unique repeat inputs: 0/1280.

No eligible example.

## TELL / lexical literalization

Eligible unique outputs: 1843/5760.

`r2d-001`, `qwen2.5-7b`, `d1`, `both_TELL`; output `1d04cc37fb47420f`.

Input: `Keywords: [NOT] [TELL] [I] lock door`

Output: "I do not tell you to lock the door."

Broad regex: true; tell regex: `True`; judge speech_act: `statement`.

## STATEMENT / lexical literalization

Eligible unique outputs: 76/5760.

`r2d-001`, `gemma3-4b`, `d1`, `pol_STATEMENT`; output `bbc95ac3345c1665`.

Input: `Keywords: [NOT] [STATEMENT] lock door`

Output: "I do not state that the door is locked."

Broad regex: true; tell regex: `False`; judge speech_act: `statement`.
