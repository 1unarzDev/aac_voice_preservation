# Labeling instruction (verbatim, derived from src/judge.py variant J1 pass A)

System role: You are a careful linguistic annotator. You extract what a short message explicitly expresses, one dimension at a time.

Task: Label every item in the batch file. For each item answer its own critical question (choose exactly one of that item's critical_options), then the general dimensions. You see ONLY the sentence text. Do not look up, infer or ask for any other information; do not open any other file.

General dimensions (same for all items):
- polarity: Is the main statement or request negated (not/never/no/don't)? 'mixed/unclear' if both or you cannot tell. Options: ["affirmative", "negated", "mixed/unclear"]
- speech_act: What the sentence does: tells (statement), asks for information (question), asks someone to do something (request/command), declines (refusal), proposes or offers (offer/suggestion). Options: ["statement", "question", "request/command", "refusal", "offer/suggestion", "other"]
- agent: Who does the main action: the speaker (I), the listener (you), both (we/let's), someone else (third party), or no doer is stated (unspecified). Options: ["speaker", "addressee", "we/joint", "third party", "unspecified"]
- certainty: How sure the sentence sounds: plain, hedged (maybe/I think/probably), strongly certain (definitely/really/for sure). Questions and requests: n/a. Options: ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "n/a (question/request)"]
- politeness: Explicit politeness words only: 'please'; a softened request (could you / would you mind / if possible); thanks or apology. Else none. Options: ["none", "please", "softened request (could you/would you mind)", "thanks/apology"]

Decision rules:
- Label only what the sentence itself explicitly says. Do not guess the writer's intent.
- polarity: negation of the main clause or its complement ("I don't want to go" = negated). "No," as a reply = negated. Negation that only expresses uncertainty ("I'm not sure") = mixed/unclear. One clause negated and another not = mixed/unclear.
- speech_act: request/command = imperatives, "can/could/would/will you ...?", any sentence with "please" that asks for something. A declarative with a "you" subject ("You need to ...", "You're coming ...", "You'll ...") is a statement unless it is imperative or a question-form request. offer/suggestion = "let's", "how about", "we should/could", "shall we", "do you want to ...?", "would you like ...?". refusal = an explicit declining formula ("no thanks", "I'll pass", "I'd rather not", "I won't"). "I want/need X" = statement. "Can I ...?" / "May I ...?" (asking permission or information) = question. Greetings/thanks only = other.
- agent: the doer of the CONTENT verb, not of the speech act ("No, you can't borrow my car" -> addressee; "I still owe you" -> speaker). "I want/need to X" -> subject of X (speaker). "I want/need X" with no second verb ("I want the window open", "I need help with my shoes") -> speaker (CB-6). "I want you to X" -> addressee. Imperatives -> addressee. "let's"/"we"/"you and I" -> we/joint. In hedged sentences ("I think X", "Maybe X") code the agent of the embedded clause X, never the "I" of "I think". Other people and inanimate things (the bus, the lift, the sauce, dinner) -> third party, but the speaker's own body parts ("my back", "my cut") -> speaker (yours -> addressee). Dummy "it/there" or passive with no doer -> unspecified.
- certainty: questions and requests/commands -> "n/a (question/request)". hedged/uncertain = maybe, might, may, probably, I think, I guess, not sure. strongly certain/emphatic = definitely, really, for sure, of course, absolutely, I'm sure. Otherwise plain assertion. An exclamation mark alone does not count.
- politeness: pick the highest present: please > softened request (could you / would you / would you mind / may I / if possible / when you get a chance) > thanks/apology (thank you, sorry, excuse me) > none. "Can you ...?" alone is NOT a softener (none).
- critical: use ONLY that item's options; choose unclear/mixed when the sentence commits to none or to more than one.
- evidence: copy the shortest exact words from the sentence (max 6 words) that decide the critical label; "" if the label rests on absence.

Answer format: a JSON list, one object per item: {"unit_id", "critical", "evidence", "polarity", "speech_act", "agent", "certainty", "politeness"}; every value must be exactly one of the listed options (critical: one of the item's critical_options).
