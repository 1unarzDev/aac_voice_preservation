# Codebook: labelling what a sentence says (v0.2, D-007 + CB-1..CB-5)

You will see one **sentence** at a time. It was written by a computer from a few words a
person typed. You answer questions about **what the sentence itself says**.

You do **not** see what the person meant, and you do not need to guess it. There are no
trick items. "Unsure" (key **S**) is always allowed and is useful information, not a failure.

The same rules are given to the LLM judge (`src/judge.py`, prompts J1 and J2). If you change
a rule here, change it there too and log it in `orchestration/decision_log.md`.

## How to work

1. Read the sentence.
2. Answer the **main question** (it changes from item to item), then the five general
   questions. Each has a fixed list of answers.
3. Answer the **added content** question last. Only for this question you also see the
   words the person typed. They stay hidden until questions 1–6 are answered, so they
   cannot change your other answers.
4. If two rules seem to clash, or no option fits, press **S**. Do not force an answer.

General rules:
- Label the **words on the page**. Ignore tone of voice, what the writer probably meant, and
  whether the sentence is a good one.
- If a sentence has two parts that disagree (one negated, one not), use the **mixed/unclear**
  option when it exists.
- An exclamation mark (!) alone changes nothing.

## 1. Main question (the item's critical dimension)

The question and its options are shown on screen. Choose `unclear/mixed` if the sentence
does not commit to one option, or commits to two.

| Dimension | Options | Rule |
|---|---|---|
| polarity | negated, affirmative, unclear/mixed | Is the main thing said negated? Same rules as general polarity below. |
| agent | speaker, addressee, we/joint, third party, unclear/mixed | Who does the main content action? Same rules as general agent below. No doer = unclear/mixed. |
| certainty | plain assertion, hedged/uncertain, strongly certain/emphatic, unclear/mixed | Same as general certainty. A question or request makes no claim, so it is unclear/mixed. |
| speech_act | statement, question, request/command, refusal, acceptance, offer/suggestion, unclear/mixed | Same as general speech act. **acceptance** = agreeing to something ("Yes, I'll cover your shift."). |
| politeness | polite, plain, unclear/mixed | **polite** = contains please, could you, would you, would you mind, thank you/thanks or sorry. **plain** = none of these. "Can you …?" alone is plain. |
| time_quantity (time) | past, now, later, unclear/mixed | When does the main event happen? Use tense and time words. past = already happened, now = happening now, later = in the future. |
| time_quantity (number) | the listed numbers, unclear/mixed | Which exact number does it state? No number, "some" or "a few" = unclear/mixed. |

Examples:
- time, **past**: "I paid the phone bill already." / "I saw the doctor yesterday."
- time, **now**: "I'm leaving right now." / "The water is running now."
- time, **later**: "I'll pay the bill later." / "Let's go to the park tomorrow."
- time, **unclear/mixed**: "I want to go to the park." (no time is said) / "I went yesterday and I'll go again tomorrow."
- number, a number: "We need five pizzas." (five) / "I took 2 painkillers." (two)
- number, **unclear/mixed**: "We need some pizzas." / "I took a few painkillers."
- politeness, **polite**: "Please turn the TV down." / "Would you mind sending me the notes?"
- politeness, **plain**: "Turn the TV down." / "Can you send me the notes?"
- acceptance: "Yes, I'll come." / "Sure, I can do that."

## 2. General questions (every item)

### Polarity: is the main statement or request negated?
- **affirmative**: no negation of the main clause.
  - "I want to go to the party." / "Yes, the window is open."
- **negated**: the main clause, or what it directly embeds, is negated (not, n't, never, no, nothing). A reply that starts with "No," is negated.
  - "I don't want to go to the party." / "No, I won't cover your shift."
- **mixed/unclear**: one part negated and one not, or the negation only shows uncertainty.
  - "I want to go but I can't." / "I'm not sure about going."

### Speech act: what does the sentence do?
- **statement**: tells something. Includes "I want X" and "I need X", and declaratives with a "you" subject (CB-1).
  - "Dinner is ready." / "You need to call grandma."
- **question**: asks for information or for permission. "Can I …?" and "May I …?" are questions (D-007).
  - "Is dinner ready?" / "Can I leave the meeting early?"
- **request/command**: asks the listener to do something. Imperatives, "Can/could/would/will you …?", and any ask containing "please".
  - "Open the window." / "Can you pick me up after work?"
- **refusal**: an explicit way of declining ("no thanks", "I'll pass", "I'd rather not", "I won't").
  - "No thanks, I already ate." / "No, I won't cover your shift."
- **offer/suggestion**: proposes something. "Let's", "how about", "we should/could", "shall we", "do you want to …?", "would you like …?"
  - "Let's watch a movie." / "Do you want to go to the party?"
- **other**: only a greeting or thanks.
  - "Thank you so much!" / "Hi!"

### Agent: who does the main action?
The doer of the **content verb**, not of the speech act (CB-5).
- **speaker**: I/me. This includes the speaker's own body part, such as "my back" or "my cut" (CB-4). In "I want/need to X", the doer of X. "I want/need X" with no second verb ("I want the window open", "I need help") → speaker (CB-6).
  - "I need to call grandma." / "My ankle hurts."
- **addressee**: you. This includes imperatives and "can you …?".
  - "You need to call grandma." / "Pass me the water."
  - "No, you can't borrow my car." (CB-5: you would be doing the borrowing)
- **we/joint**: we, let's, you and I.
  - "Let's go home." / "We should call grandma."
- **third party**: other people, and inanimate things such as the bus, the lift, the sauce or dinner (CB-4).
  - "Mom is picking me up." / "The lift is broken."
- **unspecified**: no doer is named, e.g. dummy "it/there", or a passive with no doer.
  - "It's raining." / "The window was opened."
- In hedged sentences ("I think X", "Maybe X"), label the doer of **X**, never the "I" of "I think" (CB-3).
  - "I think the bus is late." → third party

### Certainty: how sure does it sound?
- **n/a (question/request)**: always for questions and requests/commands.
  - "Is the bus late?" / "Open the window."
- **hedged/uncertain**: maybe, might, may, probably, perhaps, I think, I guess, not sure.
  - "The bus might be late." / "I think I failed the exam."
- **strongly certain/emphatic**: definitely, really, for sure, of course, absolutely, I'm sure.
  - "The bus is definitely late." / "I really want to go."
- **plain assertion**: none of the above.
  - "The bus is late." / "I failed the exam."

### Politeness: explicit polite words only
Pick the **highest** marker present: please > softened request > thanks/apology > none.
- **please**: "Please open the window." / "Can you call grandma, please?"
- **softened request (could you/would you mind)**: could you, would you, would you mind, may I, if possible, when you get a chance.
  - "Could you open the window?" / "Would you mind sending the notes?"
- **thanks/apology**: thank you, thanks, sorry, excuse me.
  - "Thanks, I already ate." / "Sorry, I can't come."
- **none**: no marker. "Can you …?" or "Can I …?" alone is none (CB-2).
  - "Open the window." / "Can you pick me up?"

## 3. Added content (you see the typed input)

Does the sentence state a **fact, reason, person, place or time** that is **not** in the
typed input?

- Chips are bracketed words like `[NOT]`, `[?]` or `[I]`. A chip's meaning counts as being in the input.
- These do **not** count as added content:
  - grammar words, word endings and pronouns;
  - negation, hedges, boosters and politeness words, and question form. These are coded in the questions above.
- **yes**:
  - "I need to call grandma today." from `need call grandma` (today)
  - "Open the window, it's hot in here." from `open window` (a reason)
  - "They fixed the lift." from `[THEY] lift fixed`. The chip says *someone else*, but a human "they" doing the fixing is new (CB-4 note).
- **no**:
  - "I want to go to the party." from `want go party`
  - "I don't want to go to the party." from `[NOT] want go party`

## 4. Open questions for autistic reviewers

We would like your view on where a change in the sentence **counts as changing what the
person said**. Your answers can change these rules. We log every change, and we do not ask
about your personal preferences.

1. **Added politeness.** The person typed `open window`, and the sentence says "Please open
   the window" or "Could you open the window?". Is that a change to their message, or just
   normal wording? Does "please" differ from "could you"? Does it matter who the listener is?
2. **"Can you …?"** We code "Can you …?" as a plain request with no politeness marker
   (CB-2). Is that how it reads to you? Is "Can you" more or less direct than an imperative
   ("Pick me up")?
3. **Added certainty.** The person typed `bus late`, and the sentence says "The bus is
   definitely late" or "The bus is late!". Should "definitely" count as a change? Should an
   exclamation mark? Right now "!" alone counts as nothing.
4. **Added uncertainty.** The sentence says "I think the bus might be late". Is adding a
   hedge to a plain message as much of a change as removing one?
5. **Directness.** Is turning a statement ("You need to call grandma") into a command
   ("Call grandma") a change of speech act, a change of directness, or both? Is softening a
   refusal ("No" → "I'd rather not") a change?
6. **Who does it.** Under rule CB-3, "I think the bus is late" has the bus as agent. Does
   the added "I think" also add something about the speaker that should be coded?
7. **Fillers and reasons.** Should invented reasons ("…, it's hot in here") be treated as
   more serious than invented times ("today")?
8. **Unsure.** Are there kinds of sentences where you would want an option that is not on
   the list?

## Change log
- v0.2: D-007. Time is coarse (past/now/later). "Can I …?" is a question and "Can you …?"
  is a request. Politeness critical options are polite/plain/unclear. A certainty
  "plain assertion" target is matched by plain or emphatic, and emphatic is logged as a
  stance addition. Added CB-1 to CB-5 (annotation/CB_rules.md).
- v0.1: initial schema (SPEC v0.1).
