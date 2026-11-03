Declared rule: per dimension, the first (family, variant) by sha256('wm-r2ex|family_id|variant') ascending where terra A0 has CK=1 and gpt UC=1; terra chip1 greedy d0 outputs of A0/A1/A2 shown regardless of whether they improve. Dimensions with no qualifying item are listed as none.

**polarity** (hw-pol-040 B) input `Keywords: [NOT] take medicine`; writer sentence: I don't take medicine with breakfast.
- A0: I don’t want to take my medicine.  [CK=1, UC=1.0, match score=0.2]
- A1: Not taking medicine.  [CK=1, UC=0.0, match score=0.6]
- A2: I do not take medicine.  [CK=1, UC=0.0, match score=0.6]

**speech_act** (hw-act-083 B) input `Keywords: [ASK] pack sandwiches`; writer sentence: Pack the sandwiches in the basket.
- A0: Please pack the sandwiches.  [CK=1, UC=1.0, match score=0.6]
- A1: Pack the sandwiches.  [CK=1, UC=0.0, match score=0.6]
- A2: Pack the sandwiches.  [CK=1, UC=0.0, match score=0.6]

**agent** (hw-agt-037 A) input `Keywords: [I] call clinic`; writer sentence: I call the clinic from the garden.
- A0: I want to call the clinic.  [CK=1, UC=1.0, match score=0.6]
- A1: I call the clinic.  [CK=1, UC=0.0, match score=0.6]
- A2: I call the clinic.  [CK=1, UC=0.0, match score=0.6]

**certainty** (hw-cer-012 A) input `Keywords: [MAYBE] manager report`; writer sentence: The manager perhaps saw the report yesterday.
- A0: Maybe the manager has the report.  [CK=1, UC=1.0, match score=0.4]
- A1: Maybe the manager has the report.  [CK=1, UC=1.0, match score=0.4]
- A2: Maybe the manager has a report.  [CK=1, UC=1.0, match score=0.4]

**politeness** (hw-plt-018 B) input `Keywords: [PLEASE] keep office door`; writer sentence: Please keep the office door closed during lunch.
- A0: Please keep the office door closed.  [CK=1, UC=1.0, match score=0.6]
- A1: Please leave the office door as it is.  [CK=1, UC=1.0, match score=0.6]
- A2: Please keep the office door.  [CK=1, UC=0.0, match score=0.6]

**time_quantity** (hw-tim-061 A) input `Keywords: [PAST] nurse report`; writer sentence: The nurse sent the report by email yesterday.
- A0: The nurse gave the report.  [CK=1, UC=1.0, match score=0.6]
- A1: There was a nurse report.  [CK=1, UC=0.0, match score=0.4]
- A2: The nurse reported.  [CK=1, UC=0.0, match score=0.6]
