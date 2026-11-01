# W-C deterministic example manifest

Seed 20261031. For each declared phenomenon below, rank eligible stored output occurrences by SHA256(JSON([seed, category, [family, variant, model, prompt, channel, request, sample, suggestion]])). Select the smallest hash; no manual substitution. Outcome-conditioned illustrative selection; rates use the full declared stratum, never the selected example. Exact input/output strings are checked against runs/r2c1/outputs.jsonl.


## Bare affirmative default

Rule: P0 bare polarity; affirmative event; shared A/B target deduplicated. Rate: 99.06% [97.81, 100.00]; n=320/320, clusters=79/79, eff=78.0.

`r2pol-041/A`, qwen2.5-7b, bare, output `5e4759a231df5d70`; label `affirmative`.

Source: "The parcel has arrived at the office."

Input: "Keywords: parcel arrive"

Output: "The parcel has arrived."


## Full-input politeness addition

Rule: P0 full politeness plain targets, known critical label; plain→polite event. Rate: 8.12% [5.31, 11.25]; n=320/320, clusters=80/80, eff=80.0.

`r2plt-015/B`, gemma3-4b, full, output `968b8cae25e89374`; label `polite`.

Source: "Open this pickle jar for me."

Input: "The user typed: Open this pickle jar for me."

Output: "Please open this pickle jar for me."


## Question cue failure

Rule: P0 question chip1 targets with observed match; failure event. Rate: 27.88% [18.86, 37.50]; n=208/208, clusters=37/37, eff=24.6.

`r2act-049/B`, llama3.1-8b, chip1, output `7d7ecf9fb02fd2b8`; label `request/command`.

Source: "Does the parcel from the bank need a signature?"

Input: "Keywords: [?] parcel signature"

Output: "Can you sign for this parcel?"


## H1 Llama plain request loss

Rule: Frozen H1 eligible Llama P0 plain chipall; non-request event. Rate: 87.84% [79.73, 94.59]; n=74/74, clusters=74/74, eff=74.0.

`r2plt-037/A`, llama3.1-8b, chipall, output `2747480bf0fc6292`; label `plain`.

Source: "Can you bring me some salt for the chicken?"

Input: "Keywords: [ASK] [YOU] [PLAIN] bring salt"

Output: "You bring salt."


## P2 coverage miss polarity

Rule: P2 bare sets with known coverage; event=the set misses at least one pair value; complete stored set displayed and first slot identifies the occurrence. Rate: 92.19% [88.61, 95.57]; n=320/320, clusters=79/79, eff=78.0.

Complete stored set: ["I want to be left alone.", "Do you want me to leave you alone?", "I wish they would leave me alone."]

`r2pol-019/A`, gpt-6.1-terra, bare, output `4c0ede18d421991b`; label `affirmative`.

Source: "I don't want to be left alone tonight."

Input: "Keywords: want left alone"

Output: "I want to be left alone."


## P2 coverage miss speech_act

Rule: P2 bare sets with known coverage; event=the set misses at least one pair value; complete stored set displayed and first slot identifies the occurrence. Rate: 46.79% [38.29, 55.52]; n=312/312, clusters=55/55, eff=33.1.

Complete stored set: ["Can you please increase the volume?", "I want to increase the volume", "We need to increase the volume now"]

`r2act-028/A`, llama3.1-8b, bare, output `3eaf2a52c1fbe3c6`; label `request/command`.

Source: "Did you increase the volume of the TV?"

Input: "Keywords: increase volume"

Output: "Can you please increase the volume?"


## P2 coverage miss politeness

Rule: P2 bare sets with known coverage; event=the set misses at least one pair value; complete stored set displayed and first slot identifies the occurrence. Rate: 30.63% [25.31, 35.94]; n=320/320, clusters=80/80, eff=80.0.

Complete stored set: ["I need you to pick up clothes cleaners.", "Can you pick up clothes cleaners for me?", "I want to pick up clothes cleaners myself."]

`r2plt-007/A`, llama3.1-8b, bare, output `2b203d5b57d8ca45`; label `plain`.

Source: "Please pick up my clothes from the dry cleaners."

Input: "Keywords: pick up clothes cleaners"

Output: "I need you to pick up clothes cleaners."
