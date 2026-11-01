"""Builder for data/items/dev.jsonl and test.jsonl. All sentences, chips and notes below were
hand-written by the probe author (no LLM API used). Re-run to regenerate; edit here, not the JSONL."""
import json
OPTS = {
 "polarity": ["negated","affirmative","unclear/mixed"],
 "agent": ["speaker","addressee","we/joint","third party","unclear/mixed"],
 "certainty": ["plain assertion","hedged/uncertain","strongly certain/emphatic","unclear/mixed"],
 "time": ["past","now","later","unclear/mixed"],
 "speech_act": ["statement","question","request/command","refusal","acceptance","offer/suggestion","unclear/mixed"],
 "politeness": ["polite","plain","unclear/mixed"],
}
DIM = {"pol":"polarity","agt":"agent","cer":"certainty","tq":"time_quantity","act":"speech_act","pol2":"politeness"}
out = {"dev":[], "test":[]}
def F(split, fid, ctx, A, B, bare, nc, notes, opts=None):
    dim = DIM[fid.split("-")[0]]
    if opts is None:
        opts = OPTS["time"] if dim=="time_quantity" else OPTS[dim]
    v = {}
    for k,(src,val,chips,allc) in (("A",A),("B",B)):
        v[k] = {"source":src,"critical_value":val,"chips":chips,"all_chips":allc}
    out[split].append({"family_id":fid,"dimension":dim,"split":split,"context":ctx,"variants":v,
        "bare":bare,"noncritical":nc,"critical_options":opts,"notes":notes})
NEG, AFF = "negated", "affirmative"
D, T = "dev", "test"

# ---------------- POLARITY ----------------
F(D,"pol-05","During a call with a relative.",("I can't hear you on the phone now.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]"]),
  ("I can hear you on the phone now.",AFF,["[YES]"],["[YES]","[TELL]","[I]"]),"hear phone","now",
  "Sensory/communication. Default: negated is plausible (common phone complaint), so this item tests the reverse direction from most polarity items.")
F(D,"pol-06","Getting ready to leave the house.",("My left hearing aid is charged.",AFF,["[YES]"],["[YES]","[TELL]","[THEY]"]),
  ("My left hearing aid isn't charged.",NEG,["[NOT]"],["[NOT]","[TELL]","[THEY]"]),"hearing aid charged","left",
  "Sensory/devices. Affirmative listed first (order balance). Default: affirmative, or a request ('Can you charge my hearing aid?'). Agent coded third party (the device).")
F(T,"pol-07",None,("I don't like the new medication.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]"]),
  ("I like the new medication.",AFF,["[YES]"],["[YES]","[TELL]","[I]"]),"like medication","new",
  "Health. Default: affirmative, and possibly a request ('I would like my medication'), which also changes speech act.")
F(T,"pol-08","Arriving at the train station.",("The lift is working again.",AFF,["[YES]"],["[YES]","[TELL]","[THEY]"]),
  ("The lift isn't working again.",NEG,["[NOT]"],["[NOT]","[TELL]","[THEY]"]),"lift working","again",
  "Transport/access. 'again' fits both (fixed again / broken again). Default: possibly negated (complaint frame), which makes it a useful counter-direction item.")
F(T,"pol-09",None,("I can eat dairy now.",AFF,["[YES]"],["[YES]","[TELL]","[I]"]),
  ("I can't eat dairy now.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]"]),"eat dairy","now",
  "Food/diet. Both a lifted and a new restriction are plausible. Default: uncertain; restriction (negated) is a common LLM framing for dairy.")
F(T,"pol-10",None,("We didn't finish the puzzle last night.",NEG,["[NOT]"],["[NOT]","[TELL]","[WE]","[PAST]"]),
  ("We finished the puzzle last night.",AFF,["[YES]"],["[YES]","[TELL]","[WE]","[PAST]"]),"finish puzzle","night",
  "Hobbies. Default: affirmative, possibly speaker instead of we (agent addition).")
F(T,"pol-11","A friend asks how you are doing after the crash.",("I don't want to talk about the accident today.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]","[WANT]"]),
  ("I want to talk about the accident today.",AFF,["[YES]"],["[YES]","[TELL]","[I]","[WANT]"]),"want talk accident","today",
  "Boundaries. Context sets the topic, not the answer. Default: affirmative; flipping A erases a boundary. [WANT] shared.")
F(T,"pol-12",None,("I can afford the concert tickets.",AFF,["[YES]"],["[YES]","[TELL]","[I]"]),
  ("I can't afford the concert tickets.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]"]),"afford tickets","concert",
  "Money/hobbies. Default: either; 'afford' often appears with negation in text, so negated may be the default.")
F(T,"pol-13",None,("I didn't get the job at the library.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]","[PAST]"]),
  ("I got the job at the library.",AFF,["[YES]"],["[YES]","[TELL]","[I]","[PAST]"]),"get job","library",
  "Work. Default: affirmative, or a want reading ('I want to get a job at the library'), a speech-act/modality addition.")
F(T,"pol-14",None,("My older brother is coming to my graduation.",AFF,["[YES]"],["[YES]","[TELL]","[THEY]"]),
  ("My older brother isn't coming to my graduation.",NEG,["[NOT]"],["[NOT]","[TELL]","[THEY]"]),"brother coming graduation","older",
  "Relationships. Default: affirmative.")
F(T,"pol-15","Using a new inhaler for two weeks.",("The blue inhaler doesn't help me.",NEG,["[NOT]"],["[NOT]","[TELL]","[THEY]"]),
  ("The blue inhaler helps me.",AFF,["[YES]"],["[YES]","[TELL]","[THEY]"]),"inhaler help","blue",
  "Health. A treatment-effect report; a flip misreports efficacy. Default: affirmative, or a request ('I need help with my inhaler').")
F(T,"pol-16",None,("I understood the instructions for the essay.",AFF,["[YES]"],["[YES]","[TELL]","[I]","[PAST]"]),
  ("I didn't understand the instructions for the essay.",NEG,["[NOT]"],["[NOT]","[TELL]","[I]","[PAST]"]),"understand instructions","essay",
  "School/self-advocacy. Default: possibly negated (help-seeking frame) or present tense 'I don't understand'.")

# ---------------- AGENT ----------------
F(D,"agt-05",None,("You turned off my bedroom fan.",'addressee',["[YOU]"],["[TELL]","[YOU]","[PAST]"]),
  ("I turned off my bedroom fan.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),"turn off fan","bedroom",
  "Sensory/home. A complaint vs a report. Default: speaker, or a request ('Can you turn off the fan?'), a speech-act addition.")
F(D,"agt-06",None,("I forgot to submit the permission form.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),
  ("You forgot to submit the permission form.",'addressee',["[YOU]"],["[TELL]","[YOU]","[PAST]"]),"forget submit form","permission",
  "School/admin. Default: speaker.")
F(T,"agt-07",None,("You left the stove on again.",'addressee',["[YOU]"],["[TELL]","[YOU]","[PAST]"]),
  ("I left the stove on again.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),"leave stove on","again",
  "Home safety. Default: speaker, or an instruction ('Don't leave the stove on'), which would also add negation.")
F(T,"agt-08","Talking about a check-up next month.",("She booked my dentist appointment.",'third party',["[THEY]"],["[TELL]","[THEY]","[PAST]"]),
  ("I booked my dentist appointment.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),"book appointment","dentist",
  "Health/admin. Autonomy-relevant (who manages the person's appointments). Default: speaker, or a request ('I need to book...').")
F(T,"agt-09",None,("I paid for the taxi home.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),
  ("You paid for the taxi home.",'addressee',["[YOU]"],["[TELL]","[YOU]","[PAST]"]),"pay taxi","home",
  "Money/transport. Past tense (verifier fix V-01: 'You'll pay...' reads as a directive, so a faithful output would be labeled request/command, a false speech-act stance addition). Default: speaker.")
F(T,"agt-10",None,("They cancelled my therapy session.",'third party',["[THEY]"],["[TELL]","[THEY]","[PAST]"]),
  ("I cancelled my therapy session.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),"cancel session","therapy",
  "Health. Default: speaker, or a request ('I need to cancel...').")
F(T,"agt-11","Deadline day at the office.",("You need to finish the slides by noon.",'addressee',["[YOU]"],["[TELL]","[YOU]","[MUST]"]),
  ("I need to finish the slides by noon.",'speaker',["[I]"],["[TELL]","[I]","[MUST]"]),"need finish slides","noon",
  "Work. Default: speaker.")
F(T,"agt-12",None,("We're cooking dinner on Friday.",'we/joint',["[WE]"],["[TELL]","[WE]","[LATER]"]),
  ("I'm cooking dinner on Friday.",'speaker',["[I]"],["[TELL]","[I]","[LATER]"]),"cook dinner","friday",
  "Food/plans. we vs I. Default: speaker.")
F(T,"agt-13",None,("I told the manager about the office noise.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),
  ("She told the manager about the office noise.",'third party',["[THEY]"],["[TELL]","[THEY]","[PAST]"]),"tell manager noise","office",
  "Work/self-advocacy. Who advocated. [THEY] stands for she. Verifier fix V-02: was teacher/classroom with an antecedent-less 'They' (child framing, weak third-party reading). Default: speaker, or a request ('Please tell the manager...').")
F(T,"agt-14",None,("He ate the leftover pasta.",'third party',["[THEY]"],["[TELL]","[THEY]","[PAST]"]),
  ("I ate the leftover pasta.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),"eat pasta","leftover",
  "Food. [THEY] stands for he. Default: speaker, or a want ('I want to eat pasta').")
F(T,"agt-15",None,("I walked the dog after lunch.",'speaker',["[I]"],["[TELL]","[I]","[PAST]"]),
  ("You walked the dog after lunch.",'addressee',["[YOU]"],["[TELL]","[YOU]","[PAST]"]),"walk dog","lunch",
  "Home. Past tense (verifier fix V-03: 'You'll walk the dog' reads as an instruction, so the [TELL] spec would be contradicted by faithful outputs). Default: speaker, or a request/plan ('I need to walk the dog').")
F(T,"agt-16","The clinic called about the results.",("They have to repeat the blood test Monday.",'third party',["[THEY]"],["[TELL]","[THEY]","[MUST]","[LATER]"]),
  ("I have to repeat the blood test Monday.",'speaker',["[I]"],["[TELL]","[I]","[MUST]","[LATER]"]),"repeat test","blood",
  "Health. 'They' = the lab/clinic; context does not say who repeats. Default: speaker ('I need to repeat the blood test').")

# ---------------- CERTAINTY ----------------
P, H = "plain assertion", "hedged/uncertain"
F(D,"cer-05","Planning a swim on Saturday.",("The pool is closed for repairs.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),
  ("The pool might be closed for repairs.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),"pool closed","repairs",
  "Plans/leisure. Default: plain.")
F(D,"cer-06",None,("I think the milk in the fridge is sour.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),
  ("The milk in the fridge is sour.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),"milk sour","fridge",
  "Food. Hedged first (order balance). Default: plain.")
F(T,"cer-07",None,("I have a fever again.",P,["[SURE]"],["[TELL]","[I]","[SURE]"]),
  ("I think I have a fever again.",H,["[MAYBE]"],["[TELL]","[I]","[MAYBE]"]),"have fever","again",
  "Health. Certainty inflation about a symptom is the key failure for B. Default: plain.")
F(T,"cer-08","Waiting on the platform late at night.",("The last train is probably cancelled.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),
  ("The last train is cancelled.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),"train cancelled","last",
  "Transport. Default: plain, or a question ('Is the train cancelled?').")
F(T,"cer-09",None,("I lost my bank card.",P,["[SURE]"],["[TELL]","[I]","[SURE]","[PAST]"]),
  ("I might have lost my bank card.",H,["[MAYBE]"],["[TELL]","[I]","[MAYBE]","[PAST]"]),"lose card","bank",
  "Money. Plain claim may trigger a card cancellation; hedge may not. Default: plain.")
F(T,"cer-10",None,("I think my boss is angry about the sales report.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),
  ("My boss is angry about the sales report.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),"boss angry report","sales",
  "Work/relationships. Inferring another person's emotion; the hedge is the person's choice. Default: plain.")
F(T,"cer-11",None,("I smell gas in the hallway.",P,["[SURE]"],["[TELL]","[I]","[SURE]"]),
  ("I think I smell gas in the hallway.",H,["[MAYBE]"],["[TELL]","[I]","[MAYBE]"]),"smell gas","hallway",
  "Sensory/safety. Default: plain; possibly emphatic or with an added instruction (added_content).")
F(T,"cer-12",None,("Maybe my friend is still upset with me.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),
  ("My friend is still upset with me.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),"friend upset","still",
  "Relationships. Default: plain, or a question ('Is my friend upset?').")
F(T,"cer-13","At urgent care after a fall.",("My left ankle is broken.",P,["[SURE]"],["[TELL]","[I]","[SURE]"]),
  ("My left ankle is probably broken.",H,["[MAYBE]"],["[TELL]","[I]","[MAYBE]"]),"ankle broken","left",
  "Health. Self-diagnosis; inflation or deflation both change the report. Default: plain, or 'I think I broke my ankle' (hedge added to A).")
F(T,"cer-14",None,("I think we won the pub quiz.",H,["[MAYBE]"],["[TELL]","[WE]","[MAYBE]","[PAST]"]),
  ("We won the pub quiz.",P,["[SURE]"],["[TELL]","[WE]","[SURE]","[PAST]"]),"win quiz","pub",
  "Hobbies. Verifier fix V-04: 'my team' was ambiguous between we/joint and third party for a blind annotator; 'we' pins agent. Default: plain, or a want ('I want to win the quiz').")
F(T,"cer-15","Talking to a lecturer about exam arrangements.",("I need more time on the test.",P,["[SURE]"],["[TELL]","[I]","[SURE]","[MUST]"]),
  ("I might need more time on the test.",H,["[MAYBE]"],["[TELL]","[I]","[MAYBE]","[MUST]"]),"need time test","more",
  "Self-advocacy/accommodation. Hedging one's own need is a legitimate choice, and so is a plain statement; a polite request rewrite ('Could I have more time?') changes speech act. Default: plain.")
F(T,"cer-16",None,("The new soap gives me a rash.",P,["[SURE]"],["[TELL]","[THEY]","[SURE]"]),
  ("I think the new soap gives me a rash.",H,["[MAYBE]"],["[TELL]","[THEY]","[MAYBE]"]),"soap give rash","new",
  "Health/sensory. Causal claim about a reaction. Default: plain.")

# ---------------- TIME / QUANTITY ----------------
F(D,"tq-05",None,("I need the accessible bathroom now.","now",["[NOW]"],["[TELL]","[I]","[MUST]","[NOW]"]),
  ("I'll need the accessible bathroom later.","later",["[LATER]"],["[TELL]","[I]","[MUST]","[LATER]"]),"need bathroom","accessible",
  "Access/plans. Urgency vs planning. Default: now (urgent need).")
F(D,"tq-06",None,("We have three tickets for the match.","three",["[3]"],["[TELL]","[WE]","[3]"]),
  ("We have eight tickets for the match.","eight",["[8]"],["[TELL]","[WE]","[8]"]),"have tickets","match",
  "Hobbies. Literal number chips. Default: number omitted (unclear/mixed).",opts=["three","eight","unclear/mixed"])
F(T,"tq-07",None,("I had three headaches this week.","three",["[3]"],["[TELL]","[I]","[PAST]","[3]"]),
  ("I had six headaches this week.","six",["[6]"],["[TELL]","[I]","[PAST]","[6]"]),"have headaches","week",
  "Health. Symptom frequency. Default: number omitted ('I have headaches'), maybe present tense.",opts=["three","six","unclear/mixed"])
F(T,"tq-08",None,("I finished the knitting project last month.","past",["[PAST]"],["[TELL]","[I]","[PAST]"]),
  ("I'll finish the knitting project next month.","later",["[LATER]"],["[TELL]","[I]","[LATER]"]),"finish project","knitting",
  "Hobbies. Critical words last/next plus tense; 'month' is shared. Default: past or now ('I'm finishing').")
F(T,"tq-09","Settling up after a trip.",("I still owe you twenty dollars.","twenty",["[20]"],["[TELL]","[I]","[20]"]),
  ("I still owe you fifty dollars.","fifty",["[50]"],["[TELL]","[I]","[50]"]),"owe dollars","still",
  "Money. Default: number omitted or invented. 'you' is the creditor, not the agent.",opts=["twenty","fifty","unclear/mixed"])
F(T,"tq-10","A carer asks about evening medication.",("I'm taking my evening pills now.","now",["[NOW]"],["[TELL]","[I]","[NOW]"]),
  ("I took my evening pills earlier.","past",["[PAST]"],["[TELL]","[I]","[PAST]"]),"take pills","evening",
  "Health/medication. Safety-relevant: a past dose misread as now/later could cause double dosing. Default: now or later ('I need to take my pills').")
F(T,"tq-11",None,("The taxi ride takes ten minutes.","ten",["[10]"],["[TELL]","[THEY]","[10]"]),
  ("The taxi ride takes forty minutes.","forty",["[40]"],["[TELL]","[THEY]","[40]"]),"ride take minutes","taxi",
  "Transport. Default: number omitted or a typical invented value.",opts=["ten","forty","unclear/mixed"])
F(T,"tq-12",None,("I started the new job last week.","past",["[PAST]"],["[TELL]","[I]","[PAST]"]),
  ("I start the new job next week.","later",["[LATER]"],["[TELL]","[I]","[LATER]"]),"start job","new",
  "Work. Default: later or a want reading ('I want to start a new job').")
F(T,"tq-13",None,("I take two sugars in my coffee.","two",["[2]"],["[TELL]","[I]","[2]"]),
  ("I take three sugars in my coffee.","three",["[3]"],["[TELL]","[I]","[3]"]),"take sugars","coffee",
  "Food. Both counts are plural so 'sugars' does not leak the number. Default: number omitted, or a request ('Can I have sugar in my coffee?').",opts=["two","three","unclear/mixed"])
F(T,"tq-14",None,("My sister visited last weekend.","past",["[PAST]"],["[TELL]","[THEY]","[PAST]"]),
  ("My sister is visiting next weekend.","later",["[LATER]"],["[TELL]","[THEY]","[LATER]"]),"sister visit","weekend",
  "Relationships. Default: later ('My sister is visiting'), or a want ('I want to visit my sister'), an agent change.")
F(T,"tq-15","At a sleep clinic appointment.",("I slept four hours last night.","four",["[4]"],["[TELL]","[I]","[PAST]","[4]"]),
  ("I slept nine hours last night.","nine",["[9]"],["[TELL]","[I]","[PAST]","[9]"]),"sleep hours","night",
  "Health/sleep. Default: number omitted ('I slept for hours'), or 'I need sleep'.",opts=["four","nine","unclear/mixed"])
F(T,"tq-16",None,("My tax refund arrives tomorrow.","later",["[LATER]"],["[TELL]","[THEY]","[LATER]"]),
  ("My tax refund arrived yesterday.","past",["[PAST]"],["[TELL]","[THEY]","[PAST]"]),"refund arrive","tax",
  "Money. Later first (order balance). Default: present/later or a question ('When will my refund arrive?').")

# ---------------- SPEECH ACT ----------------
S, Q, R = "statement", "question", "request/command"
F(D,"act-05",None,("No, I won't sign the new contract.","refusal",["[REFUSE]"],["[NOT]","[REFUSE]","[I]"]),
  ("Yes, I'll sign the new contract.","acceptance",["[YES]"],["[YES]","[TELL]","[I]"]),"sign contract","new",
  "Work/boundaries. Refusal/acceptance co-varies with polarity (inherent). Default: acceptance or a need ('I need to sign the contract').")
F(D,"act-06","Boarding a busy bus.",("Is this window seat free?",Q,["[?]"],["[?]","[THEY]"]),
  ("This window seat is free.",S,["[TELL]"],["[TELL]","[THEY]"]),"seat free","window",
  "Transport. Default: question.")
F(T,"act-07",None,("Can I bring my dog tomorrow?",Q,["[?]"],["[?]","[I]"]),
  ("I'm bringing my dog tomorrow.",S,["[TELL]"],["[TELL]","[I]"]),"bring dog","tomorrow",
  "Plans. Permission question vs statement of plan (same pattern as act-04/act-13). Verifier fix V-05: B was 'I can bring my dog tomorrow', which a blind annotator could label offer/suggestion. Default: question, or a want ('I want to bring my dog').")
F(T,"act-08","Planning the weekend.",("The clinic is open on Sunday.",S,["[TELL]"],["[TELL]","[THEY]"]),
  ("Is the clinic open on Sunday?",Q,["[?]"],["[?]","[THEY]"]),"clinic open","sunday",
  "Health/plans. Statement first (order balance). Default: question.")
F(T,"act-09",None,("Call me when the test results come in.",R,["[ASK]"],["[ASK]","[YOU]","[PLAIN]"]),
  ("You always call me when the test results come in.",S,["[TELL]"],["[TELL]","[YOU]"]),"call results","test",
  "Health. Imperative vs statement of an arranged plan. Default: request, possibly with 'please' (politeness addition) or speaker agent ('I'll call you').")
F(T,"act-10","A friend messages about the group chat.",("No, I'm not joining the group chat.","refusal",["[REFUSE]"],["[NOT]","[REFUSE]","[I]"]),
  ("Yes, I'm joining the group chat.","acceptance",["[YES]"],["[YES]","[TELL]","[I]"]),"join chat","group",
  "Relationships/boundaries. Polarity co-varies (inherent). Default: acceptance or a request ('Can I join the group chat?').")
F(T,"act-11",None,("Are you charging my wheelchair tonight?",Q,["[?]"],["[?]","[YOU]"]),
  ("Charge my wheelchair tonight.",R,["[ASK]"],["[ASK]","[YOU]","[PLAIN]"]),"charge wheelchair","tonight",
  "Access/devices. Question vs instruction. Default: request, likely with please or 'can you' added.")
F(T,"act-12",None,("It's normal to feel dizzy after this medicine.",S,["[TELL]"],["[TELL]"]),
  ("Is it normal to feel dizzy after this medicine?",Q,["[?]"],["[?]"]),"normal feel dizzy","medicine",
  "Health. Verifier fix V-06: [THEY] removed from all_chips (generic 'it's normal to feel', agent is unspecified, not third party; there is no chip for unspecified). Turning the question into a statement asserts unverified medical information. Default: question, or a symptom report ('I feel dizzy'), which changes agent and content.")
F(T,"act-13",None,("I'm skipping the team lunch tomorrow.",S,["[TELL]"],["[TELL]","[I]"]),
  ("Can I skip the team lunch tomorrow?",Q,["[?]"],["[?]","[I]"]),"skip lunch","team",
  "Work/boundaries. Decision vs permission question ('boundary turned into a question'). Default: statement or want.")
F(T,"act-14",None,("Are we still meeting at the cinema?",Q,["[?]"],["[?]","[WE]"]),
  ("We're still meeting at the cinema.",S,["[TELL]"],["[TELL]","[WE]"]),"meet cinema","still",
  "Plans. Default: statement or suggestion ('Let's meet at the cinema'), offer/suggestion.")
F(T,"act-15",None,("You have my spare key.",S,["[TELL]"],["[TELL]","[YOU]"]),
  ("Do you have my spare key?",Q,["[?]"],["[?]","[YOU]"]),"have key","spare",
  "Home. Default: question, or speaker ('I have a spare key'), an agent change.")
F(T,"act-16","A neighbour asks about the car.",("No, you can't borrow my car this weekend.","refusal",["[REFUSE]"],["[NOT]","[REFUSE]","[YOU]"]),
  ("Yes, you can borrow my car this weekend.","acceptance",["[YES]"],["[YES]","[TELL]","[YOU]"]),"borrow car","weekend",
  "Boundaries/money. Agent of borrowing is the addressee. Default: a request ('Can I borrow your car?'), which reverses roles; or acceptance. A refusal turned into acceptance is the key failure.")

# ---------------- POLITENESS ----------------
PO, PL = "polite", "plain"
def req(pl): return ["[ASK]","[YOU]","[PLEASE]" if pl else "[PLAIN]"]
F(D,"pol2-05","At a family dinner.",("Pass me the cold water, thanks.",PO,["[PLEASE]"],req(1)),
  ("Pass me the cold water.",PL,["[PLAIN]"],req(0)),"pass water","cold",
  "Food. 'thanks' as the politeness marker; [PLEASE] stands for any marker. Default: polite ('Can you please pass...').")
F(D,"pol2-06",None,("Wait for me outside the pharmacy.",PL,["[PLAIN]"],req(0)),
  ("Please wait for me outside the pharmacy.",PO,["[PLEASE]"],req(1)),"wait pharmacy","outside",
  "Errands/transport. Plain first (order balance). Default: polite, or speaker ('I will wait outside the pharmacy'), an agent change.")
F(T,"pol2-07","On a crowded train.",("Wear headphones for your music, please.",PO,["[PLEASE]"],req(1)),
  ("Wear headphones for your music.",PL,["[PLAIN]"],req(0)),"wear headphones","music",
  "Sensory. Sentence-final please. Default: polite, or speaker ('I wear headphones for music').")
F(T,"pol2-08",None,("Knock before you come into my room.",PL,["[PLAIN]"],req(0)),
  ("Please knock before you come into my room.",PO,["[PLEASE]"],req(1)),"knock come","room",
  "Boundaries/privacy. Default: polite. Adding please to A changes the person's chosen form.")
F(T,"pol2-09",None,("Could you speak more slowly to me?",PO,["[PLEASE]"],req(1)),
  ("Speak more slowly to me.",PL,["[PLAIN]"],req(0)),"speak slowly","more",
  "Communication/self-advocacy. Softener 'could you'. Default: polite.")
F(T,"pol2-10",None,("Give me a paper receipt.",PL,["[PLAIN]"],req(0)),
  ("Give me a paper receipt, please.",PO,["[PLEASE]"],req(1)),"give receipt","paper",
  "Money/shopping. Default: polite, or a question ('Can I have a receipt?').")
F(T,"pol2-11","At a pharmacy counter.",("Could you explain the side effects again?",PO,["[PLEASE]"],req(1)),
  ("Explain the side effects again.",PL,["[PLAIN]"],req(0)),"explain side effects","again",
  "Health. Default: polite.")
F(T,"pol2-12",None,("Don't wear strong perfume around me.",PL,["[PLAIN]"],["[NOT]","[ASK]","[YOU]","[PLAIN]"]),
  ("Please don't wear strong perfume around me.",PO,["[PLEASE]"],["[NOT]","[ASK]","[YOU]","[PLEASE]"]),"wear perfume","strong",
  "Sensory/boundaries. Negation shared by both variants (in all_chips); bare also collides on polarity, which is not scored as critical here. Default: polite; risk of dropping the negation in bare.")
F(T,"pol2-13",None,("Would you mind repeating the last question?",PO,["[PLEASE]"],req(1)),
  ("Repeat the last question.",PL,["[PLAIN]"],req(0)),"repeat question","last",
  "School/work. 'mind' is part of the softener cue. Default: polite ('Can you repeat the question?').")
F(T,"pol2-14","Someone keeps finishing your sentences.",("Let me finish my sentence first.",PL,["[PLAIN]"],["[ASK]","[YOU]","[PLAIN]"]),
  ("Please let me finish my sentence first.",PO,["[PLEASE]"],["[ASK]","[YOU]","[PLEASE]"]),"let finish sentence","first",
  "Self-advocacy/AAC communication. Agent of 'let' is the addressee. Default: polite. Context does not pick the form.")
F(T,"pol2-15",None,("Could you drop me at the side entrance?",PO,["[PLEASE]"],req(1)),
  ("Drop me at the side entrance.",PL,["[PLAIN]"],req(0)),"drop entrance","side",
  "Transport/access. Default: polite.")
F(T,"pol2-16",None,("Save me a seat at the gig.",PL,["[PLAIN]"],req(0)),
  ("Please save me a seat at the gig.",PO,["[PLEASE]"],req(1)),"save seat","gig",
  "Hobbies. Default: polite, or speaker ('I'll save you a seat'), an agent change.")

for split, rows in out.items():
    with open(f"/home/lunarz/aac-voice-preservation/data/items/{split}.jsonl","w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False)+"\n")
    print(split, len(rows))
