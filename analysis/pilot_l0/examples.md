# Deterministically mined examples

Rule: seed=20261031; sort eligible rows by SHA256(seed, family/variant/channel/model/prompt/request/sample/suggestion); take two, preferring different families. No manual curation. Missing labels are ineligible. An assumption-default example expresses the modal A/B choice in that dimension/channel/model/prompt cell (ties choose A) and mismatches the target variant. Chip repairs pair the same sample/suggestion.


## agent


### assumption-default

- `agt-04/A` · llama3.1-8b · S3 · bare · label source layer0
  - Source: "They will email the schedule tonight."
  - Visible input: "Keywords: email schedule"
  - Output: "I will send an email to get the schedule for next week."

- `agt-02/A` · gpt-6.1-terra · P0 · noncrit · label source layer0
  - Source: "She forgot my birthday again."
  - Visible input: "Keywords: forgot birthday again"
  - Output: "I forgot your birthday again."


### violation-with-cue

- `agt-01/A` · llama3.1-8b · P2 · chip1 · label source layer0
  - Source: "I need to call the landlord about the heat today."
  - Visible input: "Keywords: [I] need call landlord heat"
  - Output: "I need to call the landlord, the heat is not working."

- `agt-03/A` · llama3.1-8b · P2 · full · label source layer0
  - Source: "I'm driving us to the airport tomorrow."
  - Visible input: "The user typed: I'm driving us to the airport tomorrow."
  - Output: "We're taking a taxi to the airport tomorrow."


### chip-repair success

- `agt-02/A` · gemma3-4b · S3 · chip1 · label source layer0
  - Source: "She forgot my birthday again."
  - Visible input: "Keywords: [THEY] forgot birthday"
  - Output: "They forgot the birthday."

  - Before: "Keywords: forgot birthday again" → "I forgot the birthday again."

- `agt-03/A` · qwen2.5-7b · P2 · chip1 · label source layer0
  - Source: "I'm driving us to the airport tomorrow."
  - Visible input: "Keywords: [I] driving airport"
  - Output: "I drove to the airport yesterday."

  - Before: "Keywords: driving airport tomorrow" → "Tomorrow, driving to the airport is planned."


### spanning-set miss

- `agt-04/A` · qwen2.5-7b · P2 · bare · label source layer0
  - Source: "They will email the schedule tonight."
  - Visible input: "Keywords: email schedule"
  - Output: ["I will send out the email schedule for next week's shifts.", "Please check the email schedule for next week's shifts.", "The email with next week's shift schedule will be sent out soon."]

- `agt-02/A` · llama3.1-8b · P2 · noncrit · label source layer0
  - Source: "She forgot my birthday again."
  - Visible input: "Keywords: forgot birthday again"
  - Output: ["I forgot your birthday again.", "I'm so sorry, I forgot your birthday again.", "You forgot my birthday again."]


## certainty


### assumption-default

- `cer-04/B` · llama3.1-8b · S3 · bare · label source layer0
  - Source: "The new sauce might have peanuts in it."
  - Visible input: "Keywords: sauce peanuts"
  - Output: "I want the peanuts with sauce."

- `cer-01/B` · qwen2.5-7b · S3 · bare · label source layer0
  - Source: "I think my cut might be infected again."
  - Visible input: "Keywords: cut infected"
  - Output: "I have a cut that is infected."


### violation-with-cue

- `cer-04/B` · gpt-6.1-terra · S3 · chip1 · label source layer0
  - Source: "The new sauce might have peanuts in it."
  - Visible input: "Keywords: [MAYBE] sauce peanuts"
  - Output: "Does the sauce have peanuts in it?"

- `cer-01/A` · gemma3-4b · P2 · chip1 · label source layer0
  - Source: "My cut is infected again."
  - Visible input: "Keywords: [SURE] cut infected"
  - Output: "The wound is definitely infected, please tell someone."


### chip-repair success

- `cer-04/A` · llama3.1-8b · P0 · chip1 · label source layer0
  - Source: "The new sauce has peanuts in it."
  - Visible input: "Keywords: [SURE] sauce peanuts"
  - Output: "I want sauce and peanuts."

  - Before: "Keywords: new sauce peanuts" → "Can I have the new sauce with peanuts?"

- `cer-01/B` · gpt-6.1-terra · P0 · chip1 · label source layer0
  - Source: "I think my cut might be infected again."
  - Visible input: "Keywords: [MAYBE] cut infected"
  - Output: "I think my cut might be infected."

  - Before: "Keywords: cut infected again" → "My cut is infected again."


### spanning-set miss

- `cer-02/B` · gpt-6.1-terra · P2 · bare · label source layer0
  - Source: "I think the bus might be late today."
  - Visible input: "Keywords: bus late"
  - Output: ["The bus is late.", "I am late for the bus.", "Is the bus running late?"]

- `cer-03/B` · gemma3-4b · P2 · bare · label source layer0
  - Source: "I probably failed the chemistry exam."
  - Visible input: "Keywords: failed exam"
  - Output: ["I failed the exam and I'm very disappointed.", "The exam failed, and I need to study harder now.", "Did you hear that I failed my exam?"]


## polarity


### assumption-default

- `pol-04/A` · gemma3-4b · P2 · bare · label source layer0
  - Source: "I didn't get paid for the extra shift."
  - Visible input: "Keywords: get paid shift"
  - Output: "Please tell me when I will get paid for my shift."

- `pol-02/A` · gpt-6.1-terra · P2 · noncrit · label source layer0
  - Source: "My back doesn't hurt this morning."
  - Visible input: "Keywords: back hurt morning"
  - Output: "Did my back start hurting this morning?"


### violation-with-cue

- `pol-02/B` · qwen2.5-7b · P2 · chip1 · label source layer0
  - Source: "My back hurts this morning."
  - Visible input: "Keywords: [YES] back hurt"
  - Output: "Yes, my back hurts, but it's not as bad as yesterday."

- `pol-04/A` · gemma3-4b · P2 · full · label source layer0
  - Source: "I didn't get paid for the extra shift."
  - Visible input: "The user typed: I didn't get paid for the extra shift."
  - Output: "I must ask about the extra shift's pay."


### chip-repair success

- `pol-01/A` · llama3.1-8b · P2 · chip1 · label source layer0
  - Source: "I don't want the window open tonight."
  - Visible input: "Keywords: [NOT] want window open"
  - Output: "I don't want the window to open."

  - Before: "Keywords: want window open tonight" → "I want the window open tonight."

- `pol-02/A` · gemma3-4b · P1 · chip1 · label source layer0
  - Source: "My back doesn't hurt this morning."
  - Visible input: "Keywords: [NOT] back hurt"
  - Output: "You do not back hurt."

  - Before: "Keywords: back hurt morning" → "The back hurts now."


### spanning-set miss

- `pol-03/A` · gemma3-4b · P2 · bare · label source layer0
  - Source: "I don't need help with my shoes now."
  - Visible input: "Keywords: need help shoes"
  - Output: ["I need help finding my shoes.", "Please help me with these shoes.", "I must find help with my shoes now."]

- `pol-02/A` · gpt-6.1-terra · P2 · bare · label source layer0
  - Source: "My back doesn't hurt this morning."
  - Visible input: "Keywords: back hurt"
  - Output: ["My back hurts.", "My back hurt earlier, but it feels better now.", "Could you help me with my back pain?"]


## politeness


### assumption-default

- `pol2-01/A` · gemma3-4b · P2 · bare · label source layer0
  - Source: "Please turn the TV down now."
  - Visible input: "Keywords: turn tv down"
  - Output: "I want you to turn the TV down now."

- `pol2-02/A` · qwen2.5-7b · S3 · bare · label source layer0
  - Source: "Could you text me before you come over Sunday?"
  - Visible input: "Keywords: text come over"
  - Output: "They come over without warning."


### violation-with-cue

- `pol2-01/B` · gemma3-4b · P1 · chip1 · label source layer0
  - Source: "Turn the TV down now."
  - Visible input: "Keywords: [PLAIN] turn tv down"
  - Output: "Please turn the TV down."

- `pol2-04/B` · gemma3-4b · S3 · chip1 · label source layer0
  - Source: "Send me the meeting notes."
  - Visible input: "Keywords: [PLAIN] send notes"
  - Output: "Please send notes."


### chip-repair success

- `pol2-02/A` · llama3.1-8b · P2 · chip1 · label source layer0
  - Source: "Could you text me before you come over Sunday?"
  - Visible input: "Keywords: [PLEASE] text come over"
  - Output: "Please come over and text me when you arrive."

  - Before: "Keywords: text come over sunday" → "They come over every Sunday."

- `pol2-04/B` · llama3.1-8b · P2 · chip1 · label source layer0
  - Source: "Send me the meeting notes."
  - Visible input: "Keywords: [PLAIN] send notes"
  - Output: "You should send notes."

  - Before: "Keywords: send meeting notes" → "Can you send the meeting notes?"


### spanning-set miss

- `pol2-02/A` · llama3.1-8b · P2 · noncrit · label source layer0
  - Source: "Could you text me before you come over Sunday?"
  - Visible input: "Keywords: text come over sunday"
  - Output: ["They come over on Sunday.", "They come over every Sunday.", "They come over on Sundays."]

- `pol2-03/B` · gpt-6.1-terra · P2 · noncrit · label source layer0
  - Source: "Stop asking me about my weight at dinner."
  - Visible input: "Keywords: stop asking weight dinner"
  - Output: ["Please stop asking me about my weight at dinner.", "Please stop asking how much the dinner weighs.", "Please stop asking me to weigh the dinner."]


## speech_act


### assumption-default

- `act-02/B` · llama3.1-8b · P0 · bare · label source layer0
  - Source: "You can pick me up after work today."
  - Visible input: "Keywords: pick up work"
  - Output: "Can you pick me up from work?"

- `act-04/B` · qwen2.5-7b · S3 · bare · label source layer0
  - Source: "Can I leave the meeting early today?"
  - Visible input: "Keywords: leave meeting early"
  - Output: "I want to leave the meeting early."


### violation-with-cue

- `act-03/B` · gpt-6.1-terra · S3 · chipall · label source layer0
  - Source: "Yes, I'll cover your shift on Saturday."
  - Visible input: "Keywords: [YES] [TELL] [I] cover shift"
  - Output: "Yes, I can cover your shift."

- `act-02/B` · llama3.1-8b · S3 · chip1 · label source layer0
  - Source: "You can pick me up after work today."
  - Visible input: "Keywords: [TELL] pick up work"
  - Output: "Tell them to pick you up from work."


### chip-repair success

- `act-01/A` · gpt-6.1-terra · P2 · chip1 · label source layer0
  - Source: "You're coming to dinner tonight."
  - Visible input: "Keywords: [TELL] coming dinner"
  - Output: "Someone is coming over for dinner."

  - Before: "Keywords: coming dinner tonight" → "Who's coming to dinner tonight?"

- `act-02/A` · qwen2.5-7b · S3 · chip1 · label source layer0
  - Source: "Can you pick me up after work today?"
  - Visible input: "Keywords: [ASK] pick up work"
  - Output: "Can you pick me up from work?"

  - Before: "Keywords: pick up work today" → "I will pick you up from work today."


### spanning-set miss

- `act-04/B` · gpt-6.1-terra · P2 · bare · label source layer0
  - Source: "Can I leave the meeting early today?"
  - Visible input: "Keywords: leave meeting early"
  - Output: ["I want to leave the meeting early.", "May I leave the meeting early?", "I need to leave the meeting early."]

- `act-01/B` · llama3.1-8b · P2 · bare · label source layer0
  - Source: "Are you coming to dinner tonight?"
  - Visible input: "Keywords: coming dinner"
  - Output: ["I'm coming for dinner.", "We're having dinner now.", "Can you tell me what's for dinner?"]


## time_quantity


### assumption-default

No eligible examples (missing labels or no qualifying event).


### violation-with-cue

No eligible examples (missing labels or no qualifying event).


### chip-repair success

No eligible examples (missing labels or no qualifying event).


### spanning-set miss

No eligible examples (missing labels or no qualifying event).
