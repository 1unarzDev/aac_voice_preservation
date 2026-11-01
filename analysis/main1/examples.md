# Deterministically mined examples

Rule: seed=20261031; sort eligible rows by SHA256(seed, family/variant/channel/model/prompt/request/sample/suggestion); take two, preferring different families. No manual curation. Missing labels are ineligible. An assumption-default example expresses the modal A/B choice in that dimension/channel/model/prompt cell (ties choose A) and mismatches the target variant. Chip repairs pair the same sample/suggestion.


## agent


### assumption-default

- `agt-11/A` · gemma3-4b · P0 · bare · label source agree
  - Source: "You need to finish the slides by noon."
  - Visible input: "Keywords: need finish slides"
  - Output: "I need to finish the slides."

- `agt-09/A` · gpt-6.1-terra · S3 · bare · label source agree
  - Source: "I paid for the taxi home."
  - Visible input: "Keywords: pay taxi"
  - Output: "Pay for the taxi."


### violation-with-cue

- `agt-08/B` · gemma3-4b · P2 · full · label source agree
  - Source: "I booked my dentist appointment."
  - Visible input: "The user typed: I booked my dentist appointment."
  - Output: "My dentist appointment is scheduled for later this month."

- `agt-14/B` · gemma3-4b · P2 · chip1 · label source agree
  - Source: "I ate the leftover pasta."
  - Visible input: "Keywords: [I] eat pasta"
  - Output: "Could you please pass me some pasta?"


### chip-repair success

- `agt-15/A` · qwen2.5-7b · P1 · chip1 · label source agree
  - Source: "I walked the dog after lunch."
  - Visible input: "Keywords: [I] walk dog"
  - Output: "I will walk the dog."

  - Before: "Keywords: walk dog lunch" → "Do you want to walk the dog before lunch?"

- `agt-08/A` · qwen2.5-7b · S3 · chip1 · label source agree
  - Source: "She booked my dentist appointment."
  - Visible input: "Keywords: [THEY] book appointment"
  - Output: "They will book an appointment next month."

  - Before: "Keywords: book dentist appointment" → "I will book a dentist appointment for next month."


### spanning-set miss

- `agt-16/A` · gpt-6.1-terra · P2 · noncrit · label source agree
  - Source: "They have to repeat the blood test Monday."
  - Visible input: "Keywords: repeat blood test"
  - Output: ["I need to repeat the blood test.", "Do I need to repeat the blood test?", "Please repeat what you said about the blood test."]

- `agt-10/A` · gpt-6.1-terra · P2 · noncrit · label source agree
  - Source: "They cancelled my therapy session."
  - Visible input: "Keywords: cancel therapy session"
  - Output: ["I want to cancel my therapy session.", "Can you cancel my therapy session?", "Has my therapy session been canceled?"]


## certainty


### assumption-default

- `cer-10/A` · gemma3-4b · P2 · noncrit · label source agree
  - Source: "I think my boss is angry about the sales report."
  - Visible input: "Keywords: boss angry sales report"
  - Output: "The boss is angry about the sales report."

- `cer-09/B` · llama3.1-8b · S3 · noncrit · label source agree
  - Source: "I might have lost my bank card."
  - Visible input: "Keywords: lose bank card"
  - Output: "I lost my bank card."


### violation-with-cue

- `cer-11/A` · gemma3-4b · P2 · chip1 · label source agree
  - Source: "I smell gas in the hallway."
  - Visible input: "Keywords: [SURE] smell gas"
  - Output: "Please ask them to investigate the gas smell now?"

- `cer-15/B` · qwen2.5-7b · P1 · chipall · label source agree
  - Source: "I might need more time on the test."
  - Visible input: "Keywords: [TELL] [MAYBE] [MUST] [I] need time test"
  - Output: "I need to take some time for the test."


### chip-repair success

- `cer-10/A` · gemma3-4b · S3 · chip1 · label source agree
  - Source: "I think my boss is angry about the sales report."
  - Visible input: "Keywords: [MAYBE] boss angry report"
  - Output: "Maybe the boss is angry about the report."

  - Before: "Keywords: boss angry sales report" → "The boss is angry about the sales report."

- `cer-15/B` · gemma3-4b · S3 · chip1 · label source agree
  - Source: "I might need more time on the test."
  - Visible input: "Keywords: [MAYBE] need time test"
  - Output: "Maybe I need some more time to take the test."

  - Before: "Keywords: need more time test" → "I need more time for the test, please."


### spanning-set miss

- `cer-10/A` · gemma3-4b · P2 · noncrit · label source agree
  - Source: "I think my boss is angry about the sales report."
  - Visible input: "Keywords: boss angry sales report"
  - Output: ["The boss is angry about the sales report.", "I must tell the boss that the sales report is causing anger.", "Are you asking the boss why they are angry about the sales report?"]

- `cer-15/B` · qwen2.5-7b · P2 · bare · label source agree
  - Source: "I might need more time on the test."
  - Visible input: "Keywords: need time test"
  - Output: ["I need some time to prepare for the test.", "We need to discuss the test time安排.", "They need more time to review for the test."]


## polarity


### assumption-default

- `pol-13/A` · gpt-6.1-terra · P2 · bare · label source agree
  - Source: "I didn't get the job at the library."
  - Visible input: "Keywords: get job"
  - Output: "Did you get the job?"

- `pol-15/A` · gpt-6.1-terra · P2 · bare · label source agree
  - Source: "The blue inhaler doesn't help me."
  - Visible input: "Keywords: inhaler help"
  - Output: "I need help using my new inhaler."


### violation-with-cue

- `pol-14/B` · gemma3-4b · P2 · full · label source agree
  - Source: "My older brother isn't coming to my graduation."
  - Visible input: "The user typed: My older brother isn't coming to my graduation."
  - Output: "My older brother is not attending my graduation, I was hoping he would."

- `pol-16/B` · qwen2.5-7b · P2 · full · label source agree
  - Source: "I didn't understand the instructions for the essay."
  - Visible input: "The user typed: I didn't understand the instructions for the essay."
  - Output: "The instructions for the essay were unclear to me."


### chip-repair success

- `pol-15/A` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "The blue inhaler doesn't help me."
  - Visible input: "Keywords: [NOT] inhaler help"
  - Output: "There is [NOT] any help from using the new inhaler for two weeks."

  - Before: "Keywords: blue inhaler help" → "I have been using the blue inhaler for two weeks and could use some assistance."

- `pol-13/A` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "I didn't get the job at the library."
  - Visible input: "Keywords: [NOT] get job"
  - Output: "I will not get the job."

  - Before: "Keywords: get job library" → "I want to get a job at the library."


### spanning-set miss

- `pol-15/A` · llama3.1-8b · P2 · noncrit · label source agree
  - Source: "The blue inhaler doesn't help me."
  - Visible input: "Keywords: blue inhaler help"
  - Output: ["I need help using the new blue inhaler.", "Can you show me how to use the blue inhaler?", "I'm having trouble with the blue inhaler after two weeks."]

- `pol-14/B` · llama3.1-8b · P2 · bare · label source agree
  - Source: "My older brother isn't coming to my graduation."
  - Visible input: "Keywords: brother coming graduation"
  - Output: ["My brother is graduating now.", "I'm sure my brother will graduate later.", "Can you tell me if my brother is graduating this year?"]


## politeness


### assumption-default

- `pol2-11/A` · llama3.1-8b · P2 · bare · label source agree
  - Source: "Could you explain the side effects again?"
  - Visible input: "Keywords: explain side effects"
  - Output: "I need to know the side effects of the medication."

- `pol2-14/A` · gemma3-4b · S3 · bare · label source agree
  - Source: "Let me finish my sentence first."
  - Visible input: "Keywords: let finish sentence"
  - Output: "You keep finishing my sentences, please."


### violation-with-cue

- `pol2-12/B` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "Please don't wear strong perfume around me."
  - Visible input: "Keywords: [PLEASE] wear perfume"
  - Output: "I would really appreciate it if you wore perfume tomorrow."

- `pol2-14/A` · gemma3-4b · P2 · full · label source agree
  - Source: "Let me finish my sentence first."
  - Visible input: "The user typed: Let me finish my sentence first."
  - Output: "Please allow me to complete my thought."


### chip-repair success

- `pol2-10/A` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "Give me a paper receipt."
  - Visible input: "Keywords: [PLAIN] give receipt"
  - Output: "Can you give me the receipt?"

  - Before: "Keywords: give paper receipt" → "Can you give me a paper receipt, please?"

- `pol2-15/A` · gpt-6.1-terra · P1 · chip1 · label source agree
  - Source: "Could you drop me at the side entrance?"
  - Visible input: "Keywords: [PLEASE] drop entrance"
  - Output: "Please drop me at the entrance."

  - Before: "Keywords: drop side entrance" → "Drop at the side entrance."


### spanning-set miss

- `pol2-11/A` · llama3.1-8b · P2 · bare · label source agree
  - Source: "Could you explain the side effects again?"
  - Visible input: "Keywords: explain side effects"
  - Output: ["I need to know the side effects of the medication.", "Can you explain the side effects of this medication?", "You should tell me about the potential side effects of this prescription."]

- `pol2-10/B` · llama3.1-8b · P2 · bare · label source agree
  - Source: "Give me a paper receipt, please."
  - Visible input: "Keywords: give receipt"
  - Output: ["I need the receipt", "Can you give me the receipt", "You must give me the receipt"]


## speech_act


### assumption-default

- `act-11/A` · qwen2.5-7b · P2 · noncrit · label source agree
  - Source: "Are you charging my wheelchair tonight?"
  - Visible input: "Keywords: charge wheelchair tonight"
  - Output: "Could you charge my wheelchair for me tonight?"

- `act-12/B` · llama3.1-8b · S3 · noncrit · label source agree
  - Source: "Is it normal to feel dizzy after this medicine?"
  - Visible input: "Keywords: normal feel dizzy medicine"
  - Output: "I feel dizzy and need some medicine."


### violation-with-cue

- `act-13/A` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "I'm skipping the team lunch tomorrow."
  - Visible input: "Keywords: [TELL] skip lunch"
  - Output: "Tell me about skipping lunch."

- `act-16/A` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "No, you can't borrow my car this weekend."
  - Visible input: "Keywords: [REFUSE] borrow car"
  - Output: "I'm sorry, but I can't borrow my car right now."


### chip-repair success

- `act-11/B` · qwen2.5-7b · P2 · chip1 · label source agree
  - Source: "Charge my wheelchair tonight."
  - Visible input: "Keywords: [ASK] charge wheelchair"
  - Output: "Could you charge my wheelchair for me?"

  - Before: "Keywords: charge wheelchair tonight" → "Tonight, I will charge my wheelchair."

- `act-15/B` · gpt-6.1-terra · S3 · chip1 · label source agree
  - Source: "Do you have my spare key?"
  - Visible input: "Keywords: [?] have key"
  - Output: "Do you have the key?"

  - Before: "Keywords: have spare key" → "I have a spare key."


### spanning-set miss

- `act-16/A` · llama3.1-8b · P2 · noncrit · label source agree
  - Source: "No, you can't borrow my car this weekend."
  - Visible input: "Keywords: borrow car weekend"
  - Output: ["I want to borrow your car this weekend.", "Can I borrow your car this weekend?", "I must borrow your car this weekend."]

- `act-07/A` · llama3.1-8b · P2 · bare · label source agree
  - Source: "Can I bring my dog tomorrow?"
  - Visible input: "Keywords: bring dog"
  - Output: ["I want to bring the dog.", "Can you bring the dog?", "I must bring the dog."]


## time_quantity


### assumption-default

- `tq-14/A` · gpt-6.1-terra · S3 · noncrit · label source agree
  - Source: "My sister visited last weekend."
  - Visible input: "Keywords: sister visit weekend"
  - Output: "My sister is visiting this weekend."

- `tq-12/A` · llama3.1-8b · S3 · bare · label source agree
  - Source: "I started the new job last week."
  - Visible input: "Keywords: start job"
  - Output: "I will start the job."


### violation-with-cue

- `tq-13/B` · llama3.1-8b · S3 · chip1 · label source agree
  - Source: "I take three sugars in my coffee."
  - Visible input: "Keywords: [3] take sugars"
  - Output: "I will take the sugars."

- `tq-10/A` · gpt-6.1-terra · P2 · chip1 · label source agree
  - Source: "I'm taking my evening pills now."
  - Visible input: "Keywords: [NOW] take pills"
  - Output: "Have I already taken my pills?"


### chip-repair success

- `tq-08/A` · gpt-6.1-terra · P1 · chip1 · label source agree
  - Source: "I finished the knitting project last month."
  - Visible input: "Keywords: [PAST] finish project"
  - Output: "The project was finished."

  - Before: "Keywords: finish knitting project" → "Finish the knitting project."

- `tq-15/B` · llama3.1-8b · P1 · chip1 · label source agree
  - Source: "I slept nine hours last night."
  - Visible input: "Keywords: [9] sleep hours"
  - Output: "They sleep 9 hours."

  - Before: "Keywords: sleep hours night" → "They sleep 7 hours at night."


### spanning-set miss

- `tq-13/B` · llama3.1-8b · P2 · noncrit · label source agree
  - Source: "I take three sugars in my coffee."
  - Visible input: "Keywords: take sugars coffee"
  - Output: ["I want to take two sugars with my coffee.", "Can you please tell me if I can take sugars with coffee?", "I must take sugars with my coffee."]

- `tq-16/B` · qwen2.5-7b · P2 · bare · label source agree
  - Source: "My tax refund arrived yesterday."
  - Visible input: "Keywords: refund arrive"
  - Output: ["I will arrive on time and get a refund if there are any issues.", "They will arrive soon and I will process the refund immediately.", "Please arrive early to ensure you don't miss your refund period."]
