# Design review packet

*Reading level: plain language. Print this page, or use the web page `review.html`. There is no time limit. You can skip any question, take breaks, and answer over several days. A support person may write what you say, word for word.*

## What this is

We are building a tool that helps a person say a full sentence from a few words. A computer writes the sentence. Sometimes the computer changes the meaning by mistake. We have written five rules (R1 to R5) that say what the tool must do. We would like your help to check the rules.

You are being asked as a paid design consultant. You are looking at our rules and at examples that we made. The examples are tests made by researchers and a computer. They are not real messages from anyone.

## What we are asking

Please tell us what you think about the rules, the button idea and the examples.

We are asking about the tool and these pages only. You do not need to tell us about yourself, your health, how you talk, or your own life. Please do not write your name or personal stories in the answers. If you want to say something personal, you do not have to.

We do not collect your age, your diagnosis or anything about your own communication. We do not record you.

## How to answer

There is no time limit. Take as long as you like. Take breaks. You can stop at any time and still be paid for the time you spent.

You can answer in any way that works for you. You can type. You can use your AAC device. You can ask a support person to type or write what you say, word for word, while you are in charge of the answers. You can answer on more than one day. You can skip any question.

The page can show bigger text. You can also print this packet and write on it, or use the .md copy.

## The five rules

For each rule: a plain statement, why it matters, real examples, and then questions for you.

### R1. Keep the button's meaning

**Rule:** If I pick a meaning button, the sentence must keep that meaning. The system must not silently turn “not” into a yes, or a question into a statement.

**Why:** A button is extra work. If the system ignores it, the work was wasted and the message can be wrong.

**A good case.** You picked these words and buttons: `[?] brother call`
- The system wrote: “Did my brother call?”
- The person picked the question button. The sentence is a question.

**A bad case.** You picked these words and buttons: `[NOT] guest respect`
- The system wrote: “We must respect the guest.”
- The person picked the NOT button. The sentence has no “not” and turns into a different message.

**Question A.** How important is R1? Important / Somewhat important / Not important / Skip

**Question B.** Is anything wrong with R1, or missing from it?

> Your answer: ______________________________________________

### R2. Do not change a typed sentence

**Rule:** If I type a whole sentence, the system must not change it. No added “please”, no added words, no new tone.

**Why:** It is my sentence. This rule is a choice we made to protect the person's own words. Some people may want the system to rewrite for them. We want to know what you think.

**A good case.** You typed the whole sentence: `The dog waits outside the kitchen door.`
- The system wrote: “The dog waits outside the kitchen door.”
- The person typed a sentence. The system kept it as it was.

**A bad case.** You picked these words and buttons: `[PLAIN] check receipt`
- The system wrote: “Please check the receipt.”
- The person picked the PLAIN button (no polite words). The system added “Please”.

**Question A.** How important is R2? Important / Somewhat important / Not important / Skip

**Question B.** Is anything wrong with R2, or missing from it?

> Your answer: ______________________________________________

### R3. Do not quietly guess when the words are unclear

**Rule:** If my words could mean more than one thing, the system must not quietly pick one. It should show me the choices, or ask.

**Why:** Two words like “shop close” can mean “The shop closes”, “Is the shop closed?” or “Close the shop”. A silent guess can say the wrong thing.

**A case where the system guessed.** You picked these words and buttons: `band play`
- The system wrote: “The band plays now.”
- The words did not say when. The system chose “now”.

**Another case where the system guessed.** You picked these words and buttons: `shop close`
- The system wrote: “The shop is closed.”
- The words did not say if it is a question or a statement. The system chose a statement.

**Question A.** How important is R3? Important / Somewhat important / Not important / Skip

**Question B.** Is anything wrong with R3, or missing from it?

> Your answer: ______________________________________________

### R4. Adding a button must not break something that was right

**Rule:** If I add another button, the parts of the message that were already right must stay right.

**Why:** People often pick more than one button. A second button should help, not damage the first.

**Same words, more buttons.** Here the person picked one button:
- Picked: `[NOT] supervisor read`
- The system wrote: “The supervisor will not read.”

With more buttons on the same words:
- Picked: `[NOT] [TELL] [THEY] supervisor read`
- The system wrote: “They will not tell the supervisor to read.”

The more-buttons sentence changed the meaning that the one-button sentence kept.

**Question A.** How important is R4? Important / Somewhat important / Not important / Skip

**Question B.** Is anything wrong with R4, or missing from it?

> Your answer: ______________________________________________

### R5. The test screen must be honest (this one is for the people who test the system)

**Rule:** When researchers test the system, the screen they show it must carry the meaning they say it carries. If the test screen is wrong, the system gets blamed for the test's mistake.

**Why:** We found this mistake in our own test tool. A button said “maybe” for a sentence that was not unsure. The system followed the button, and the test counted it as a system error.

**Real case 1.**
- The message the test was about: “An extra pillow would be nice.”
- What the test screen showed the system: `[MAYBE] extra pillow nice`
- What the system wrote: “Maybe I want an extra pillow.”

**Real case 2.**
- The message the test was about: “i will tell you as soon as possible”
- What the test screen showed the system: `[MAYBE] tell possible`
- What the system wrote: “Maybe I told you something.”

**Question A.** How important is R5? Important / Somewhat important / Not important / Skip

**Question B.** Is anything wrong with R5, or missing from it?

> Your answer: ______________________________________________

### Anything missing

Is there a rule we forgot? What would you add?

> Your answer: ______________________________________________

## What a system should never change without asking

What should a system never change without asking? You can list things, for example words, tone, who does the action, or anything else.

> Your answer: ______________________________________________

## A button or a plain word

Here is the idea in words. A person picks a few words from a list. There are two ways to say the extra meaning (for example “not”).

**Version 1, buttons (chips).** Under the word box is a row of small buttons: `[NOT]` (not), `[?]` (this is a question), `[ASK]` (this is a request), `[TELL]` (this is a statement), `[I]` (I do it), `[YOU]` (you do it), `[MAYBE]` (I am not sure), `[PLEASE]` (polite), `[PAST]` (it already happened), `[LATER]` (it will happen later). The person picks words, and may tap one or more buttons.
- Example, picked: `[TELL] shop close`. The system wrote: “The shop closes.”

**Version 2, plain words.** There are no buttons. The extra meaning is a plain word in the same list (for example the word `not`).
- Example, picked: `statement shop close`. The system wrote: “The shop is closed now.”

These are descriptions, not a finished design. We are not saying one is better. A button may take more steps for some ways of using a device. A word may be easier to find. You tell us.

Think about the design only. Which is easier to imagine using: a button (chip) or a plain word?

- The button (chip) is easier to imagine
- The plain word is easier to imagine
- Both are fine
- Neither is good
- It depends (please say on what)

Why?

> Your answer: ______________________________________________

## Ten example sentences

Each one was made by the computer from the words shown. For each one: would it be acceptable to send as the person's message? Fine to send / Not acceptable to send / Not sure. If not, tell us why.

### Example E01

You picked these words and buttons: `[ASK] leave light`

- The computer's first try: “Please leave the light on.”
- After the system fixed it: “Leave the light on.”

Please answer about the fixed sentence. You can comment on the first try too.

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E02

You picked these words and buttons: `[TELL] [YOU] send note`

- The system wrote: “Tell you to send a note.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E03

You picked these words and buttons: `later guitar music`

- The system wrote: “I will play guitar music later.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E04

You picked these words and buttons: `[YES] [TELL] [THEY] club offer`

- The system wrote: “They will tell you about the club offer.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E05

You picked these words and buttons: `[NOT] [TELL] [WE] schedule training`

- The system wrote: “We tell schedule training.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E06

You picked these words and buttons: `[ASK] [YOU] [PLAIN] get chair`

- The computer's first try: “You get the chair.”
- After the system fixed it: “Get the chair.”

Please answer about the fixed sentence. You can comment on the first try too.

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E07

You picked these words and buttons: `[ASK] ring council permit`

- The computer's first try: “Please ring the council about the permit.”
- After the system fixed it: “Ring the council about the permit.”

Please answer about the fixed sentence. You can comment on the first try too.

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E08

You picked these words and buttons: `[TELL] [I] [PAST] adjust lamp`

- The system wrote: “I adjusted the lamp.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E09

You picked these words and buttons: `[TELL] [THEY] practice guitar`

- The system wrote: “They tell me they practice guitar.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

### Example E10

You picked these words and buttons: `[ASK] [YOU] [PLAIN] show receptionist pass`

- The system wrote: “Please show the receptionist my pass.”

Fine to send / Not acceptable to send / Not sure

Why?

> Your answer: ______________________________________________

## Free comments

Anything else you want the authors to know about the design or these pages.

> Your answer: ______________________________________________

## Thank you

Please return your answers as described in the agreement. You do not need to give your name with them.
