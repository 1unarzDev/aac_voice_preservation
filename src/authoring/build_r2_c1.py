"""Builder for data/items/r2_c1.jsonl: round-2 W-C families, polarity + politeness.

All sentences, chips and notes below were hand-written by the item author (Claude, in-session;
no LLM API was called and no model server was started). Re-run to regenerate; edit here, not the JSONL.

Per dimension: 40 AACText-seeded (seed = one real message from data/raw/aactext/sent_train_aac.txt,
CC BY 4.0, Vertanen & Kristensson 2011; seed_line is the 1-based line number), 30 independently
drafted, 10 adversarial. Seeds avoid every line in data/specs/aactext_sample400.jsonl (the W-B sample).

Conventions (apply SPEC v0.1, CB-1..CB-9):
- The critical chip is derived from critical_value: negated->[NOT], affirmative->[YES],
  polite->[PLEASE], plain->[PLAIN]; it is the first chip of all_chips (polarity) or the last (politeness).
- all_chips also states speech act ([TELL]/[?]/[ASK]) and agent when a doer is named. Inanimate
  subjects are [THEY] and possessed body parts are [I] (CB-4). No agent chip when the doer is
  unnamed (dummy it/there, nobody/somebody) or the agent label is genuinely contestable
  ("The doctor said X", "Ask Jo to X"); then agent is not scored.
- Non-scored chips, applied uniformly here: [PAST] for a past event, [LATER] for a future event,
  [WANT] for want, [MUST] for need to / have to. Present and habitual get no time chip, and neither do
  imperatives/requests (verifier VR-12).
- Imperatives / "Can you" / "Could you" are [ASK][YOU]; "Can I ...?" is [?][I] (CB-9).
  "Can you"/"Will you" alone are plain; could you / would you / would you mind / please / thanks /
  sorry are polite (CB-2, codebook politeness rule). "may I", "if possible", "excuse me" are never used,
  because the critical politeness rule does not list them.
- Sources avoid hedges and boosters (really, maybe, I think, definitely), so certainty is plain
  for statements and n/a for questions/requests in both variants.
- cluster_id: one cluster per seed line (seeded) or per hand-written sentence frame (drafted,
  adversarial). No two families in this file are noun swaps of each other, so every family is its
  own cluster; the CB-2 can->could seeded pairs share a construction but have distinct seeds and
  verbs, and are marked in notes ("CB-2 boundary") for sensitivity analysis.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = (ROOT / "data/raw/aactext/sent_train_aac.txt").read_text().split("\n")
OUT = ROOT / "data/items/r2_c1.jsonl"

OPTS = {"polarity": ["negated", "affirmative", "unclear/mixed"],
        "politeness": ["polite", "plain", "unclear/mixed"]}
CRIT = {"negated": "[NOT]", "affirmative": "[YES]", "polite": "[PLEASE]", "plain": "[PLAIN]"}
NEG, AFF, PO, PL = "negated", "affirmative", "polite", "plain"
rows = []
counter = {"polarity": 0, "politeness": 0}


def F(dim, con, ctx, A, B, bare, nc, notes, seed=None, sv=None, subtype=None, gs=None, cluster=None):
    """A/B = (source, critical_value, other all_chips). seed = line number; sv = variant that keeps the seed.
    gs = {variant: general_spec override} (labels.general_spec); cluster = shared construction cluster id
    for drafted near-duplicate frames (verifier r2c1, analysis/item_verification/r2_c1.md)."""
    counter[dim] += 1
    n = counter[dim]
    fid = f"{'r2pol' if dim == 'polarity' else 'r2plt'}-{n:03d}"
    v = {}
    for k, (src, val, rest) in (("A", A), ("B", B)):
        c = CRIT[val]
        allc = [c] + rest if dim == "polarity" else rest + [c]
        v[k] = {"source": src, "critical_value": val, "chips": [c], "all_chips": allc}
        if gs and k in gs:
            v[k]["general_spec"] = gs[k]
    rec = {"family_id": fid, "dimension": dim, "split": "r2", "context": ctx, "variants": v,
           "bare": bare, "noncritical": nc, "critical_options": OPTS[dim], "notes": notes,
           "construction": con}
    if con == "seeded":
        rec["seed_line"] = seed
        rec["seed_text"] = CORPUS[seed - 1].rstrip("\r")
        rec["seed_variant"] = sv
        rec["cluster_id"] = f"r2c-seed-{seed:05d}"
    else:
        rec["cluster_id"] = cluster or f"r2c-{con[:3]}-{fid}"
    if subtype:
        rec["subtype"] = subtype
    rows.append(rec)


P, L = "polarity", "politeness"
T_I, T_YOU, T_WE, T_THEY, T = ["[TELL]", "[I]"], ["[TELL]", "[YOU]"], ["[TELL]", "[WE]"], ["[TELL]", "[THEY]"], ["[TELL]"]
ASKP = ["[ASK]", "[YOU]", "[PLAIN]"]    # imperative inside a polarity family
REQ = ["[ASK]", "[YOU]"]                # request inside a politeness family (politeness chip appended)
QI = ["[?]", "[I]"]
S = "seeded"


# =====================================================================================
# POLARITY: AACText-seeded (40). Variant A keeps the seed's polarity; B adds/removes negation.
# =====================================================================================
# -- seeds that are negated (A = negated)
F(P, S, None, ("I'm not feeling well today.", NEG, T_I), ("I'm feeling well today.", AFF, T_I),
  "feel well", "today", "Health check-in. Seed minimally cleaned. Default: affirmative or negated both common; tests direction.", 374, "A")
F(P, S, None, ("I don't like the music in this cafe.", NEG, T_I), ("I like the music in this cafe.", AFF, T_I),
  "like music", "cafe", "Leisure/opinion. Seed object made concrete (cafe). Default: affirmative.", 60, "A")
F(P, S, None, ("My new client didn't show up.", NEG, T_THEY + ["[PAST]"]), ("My new client showed up.", AFF, T_THEY + ["[PAST]"]),
  "client show up", "new", "Work. 'She' replaced by 'my new client' to give a named third party. Default: affirmative.", 362, "A")
F(P, S, None, ("Don't feed the dog tonight.", NEG, ASKP), ("Feed the dog tonight.", AFF, ASKP),
  "feed dog", "tonight", "Pets/household instruction. Negative vs positive imperative. Default: affirmative imperative, likely with 'please' (politeness addition).", 490, "A")
F(P, S, "At a friend's birthday party.", ("I'm not ready to leave the party.", NEG, T_I), ("I'm ready to leave the party.", AFF, T_I),
  "ready leave", "party", "Social. NPI 'yet' from the seed removed so A and B differ only in negation. Default: affirmative.", 792, "A")
F(P, S, None, ("I didn't read your last email.", NEG, T_I + ["[PAST]"]), ("I read your last email.", AFF, T_I + ["[PAST]"]),
  "read email", "last", "Work/messaging. Noncritical 'long' replaced by 'last' (verifier VR-01: 'long email' hinted not reading it). Default: affirmative.", 946, "A")
F(P, S, None, ("I won't be able to make the Friday meeting.", NEG, T_I + ["[LATER]"]), ("I'll be able to make the Friday meeting.", AFF, T_I + ["[LATER]"]),
  "able make meeting", "friday", "Work scheduling. Seed's 'it' made concrete. A 'I won't ...' declines attendance and the codebook lists 'I won't' as refusal, so A's speech act accepts statement or refusal (verifier VR-02). Default: affirmative; a cancellation turned into attendance is the key failure.", 959, "A",
  gs={"A": {"speech_act": ["statement", "refusal"]}})
F(P, S, None, ("I'm not coming to the barbecue tomorrow.", NEG, T_I + ["[LATER]"]), ("I'm coming to the barbecue tomorrow.", AFF, T_I + ["[LATER]"]),
  "come barbecue", "tomorrow", "Social plans/boundaries. A declines an invitation, so A's speech act accepts statement or refusal (verifier VR-03). Default: affirmative or a question ('Are you coming...?'), a speech-act change.", 1597, "A",
  gs={"A": {"speech_act": ["statement", "refusal"]}})
F(P, S, None, ("Dad doesn't know about the party on Saturday.", NEG, T_THEY), ("Dad knows about the party on Saturday.", AFF, T_THEY),
  "dad know party", "saturday", "Family. NPI 'anything' from the seed removed. Noncritical 'surprise' replaced by 'saturday' (verifier VR-04: a surprise party presupposes someone does not know). Default: affirmative or a question.", 1602, "A")
F(P, S, None, ("This phone charger doesn't work.", NEG, T_THEY), ("This phone charger works.", AFF, T_THEY),
  "charger work", "phone", "Tech. Seed 'does not seem to work' simplified to avoid a hedge ('seem'). Default: affirmative, though a fault report is the more typical AAC message.", 1857, "A")
F(P, S, None, ("I don't want to call the landlord again.", NEG, T_I + ["[WANT]"]), ("I want to call the landlord again.", AFF, T_I + ["[WANT]"]),
  "want call landlord", "again", "Housing. 'him' made concrete. Default: affirmative.", 2024, "A")
F(P, S, "Sorting the laundry together.", ("Don't bleach my work shirts.", NEG, ASKP), ("Bleach my work shirts.", AFF, ASKP),
  "bleach shirts", "work", "Household instruction; seed's reason clause dropped. Noncritical 'white' replaced by 'work' (verifier VR-05: white shirts are the ones normally bleached). Default: affirmative imperative.", 2056, "A")
F(P, S, None, ("Don't play that song at the party.", NEG, ASKP), ("Play that song at the party.", AFF, ASKP),
  "play song", "party", "Music/social. Default: affirmative imperative, likely with please.", 2133, "A")
F(P, S, None, ("I haven't received the refund cheque.", NEG, T_I + ["[PAST]"]), ("I've received the refund cheque.", AFF, T_I + ["[PAST]"]),
  "receive cheque", "refund", "Money/admin. 'gotten ... yet' changed to 'received' (removes NPI yet). Default: affirmative.", 2401, "A")
F(P, S, None, ("I didn't sleep well last night.", NEG, T_I + ["[PAST]"]), ("I slept well last night.", AFF, T_I + ["[PAST]"]),
  "sleep well", "night", "Health/sleep. Seed's second clause dropped. Default: affirmative.", 2420, "A")
F(P, S, None, ("I don't understand the new rota.", NEG, T_I), ("I understand the new rota.", AFF, T_I),
  "understand rota", "new", "Work. Self-advocacy (signalling confusion). Default: affirmative, or a question/request for help.", 2869, "A")
F(P, S, None, ("I'm not tired after the morning walk.", NEG, T_I), ("I'm tired after the morning walk.", AFF, T_I),
  "tired walk", "morning", "Activity. NPI 'yet' removed. Noncritical 'long' replaced by 'morning' (verifier VR-06: 'long walk' hinted tiredness). Default: affirmative ('I'm tired after...').", 3388, "A")
F(P, S, None, ("I've never seen that film before.", NEG, T_I + ["[PAST]"]), ("I've seen that film before.", AFF, T_I + ["[PAST]"]),
  "see film", "before", "Entertainment. Negator is 'never'. 'before' fits both. Default: affirmative.", 3485, "A")
F(P, S, None, ("I don't want to be left alone tonight.", NEG, T + ["[WANT]"]), ("I want to be left alone tonight.", AFF, T + ["[WANT]"]),
  "want left alone", "tonight", "Boundaries/support. Both are natural and opposite in what support is needed. No agent chip: under CB-6 the agent is the doer of the passive 'be left alone', which is unnamed (speaker vs unspecified is contestable; verifier VR-07). Default: either; good direction test.", 3506, "A")
F(P, S, None, ("Don't let the cat out after dinner.", NEG, ASKP), ("Let the cat out after dinner.", AFF, ASKP),
  "let cat out", "dinner", "Pets. Seed 'Don't forget to let the cat out' means 'let the cat out', so the seed's meaning is kept by B (affirmative); A keeps only its surface 'Don't' (verifier VR-08: seed_variant A->B). Default: affirmative imperative.", 2830, "B")
# -- seeds that are affirmative (A = affirmative)
F(P, S, None, ("I have the plumber's phone number.", AFF, T_I), ("I don't have the plumber's phone number.", NEG, T_I),
  "have plumber number", "phone", "Home repairs. 'his' made concrete. Default: affirmative or a request ('Can I have...').", 84, "A")
F(P, S, None, ("I need to run to the store tonight.", AFF, T_I + ["[MUST]", "[LATER]"]), ("I don't need to run to the store tonight.", NEG, T_I + ["[MUST]", "[LATER]"]),
  "need run store", "tonight", "Errands. Negated modal 'don't need to' (absence of obligation). Default: affirmative.", 123, "A")
F(P, S, None, ("I'm busy at work today.", AFF, T_I), ("I'm not busy at work today.", NEG, T_I),
  "busy work", "today", "Work. Seed's 'very' removed (degree word could be read as emphasis). Default: affirmative.", 240, "A")
F(P, S, None, ("I have a doctor's appointment on Tuesday morning.", AFF, T_I), ("I don't have a doctor's appointment on Tuesday morning.", NEG, T_I),
  "have doctor appointment", "tuesday", "Health scheduling. Default: affirmative or a request to book one.", 473, "A")
F(P, S, None, ("My muscles are sore after physio.", AFF, T_I), ("My muscles aren't sore after physio.", NEG, T_I),
  "muscles sore", "physio", "Health. Body part = speaker (CB-4). Default: affirmative.", 1035, "A")
F(P, S, None, ("I watched the match last night.", AFF, T_I + ["[PAST]"]), ("I didn't watch the match last night.", NEG, T_I + ["[PAST]"]),
  "watch match", "night", "Sport/TV. Seed show changed to 'the match'. Default: affirmative.", 1125, "A")
F(P, S, "Checking the weather forecast.", ("The storm is coming tonight.", AFF, T_THEY + ["[LATER]"]), ("The storm isn't coming tonight.", NEG, T_THEY + ["[LATER]"]),
  "storm come", "tonight", "Weather. Inanimate subject = third party (CB-4). Default: affirmative.", 1625, "A")
F(P, S, None, ("The laptop screen is too bright.", AFF, T_THEY), ("The laptop screen isn't too bright.", NEG, T_THEY),
  "screen bright", "laptop", "Sensory/tech. 'too' kept in both. Default: affirmative, or a request to dim it.", 1884, "A")
F(P, S, None, ("She said she'll come tomorrow.", AFF, T_THEY + ["[LATER]"]), ("She said she won't come tomorrow.", NEG, T_THEY + ["[LATER]"]),
  "say come", "tomorrow", "Relaying plans. Negation in the embedded clause only (codebook: negation of what the main clause directly embeds counts as negated). Default: affirmative.", 1900, "A")
F(P, S, None, ("I stayed up late for the election.", AFF, T_I + ["[PAST]"]), ("I didn't stay up late for the election.", NEG, T_I + ["[PAST]"]),
  "stay up late", "election", "News/sleep. Default: affirmative.", 2093, "A")
F(P, S, "A friend asks about the new flat.", ("The upstairs neighbours are noisy.", AFF, T_THEY), ("The upstairs neighbours aren't noisy.", NEG, T_THEY),
  "neighbours noisy", "upstairs", "Housing. Context licenses both a complaint and reassurance. Default: affirmative.", 2256, "A")
F(P, S, None, ("I'll be late for dinner tonight.", AFF, T_I + ["[LATER]"]), ("I won't be late for dinner tonight.", NEG, T_I + ["[LATER]"]),
  "late dinner", "tonight", "Family logistics. B uses 'I won't', listed as a refusal cue in the codebook; B's speech act accepts statement or refusal (verifier VR-09). Default: affirmative.", 2366, "A",
  gs={"B": {"speech_act": ["statement", "refusal"]}})
F(P, S, None, ("I bought the groceries yesterday.", AFF, T_I + ["[PAST]"]), ("I didn't buy the groceries yesterday.", NEG, T_I + ["[PAST]"]),
  "buy groceries", "yesterday", "Shopping. Default: affirmative, or a request ('Can you buy groceries?').", 2619, "A")
F(P, S, "After driving over a pothole.", ("My front tyre is flat.", AFF, T_THEY), ("My front tyre isn't flat.", NEG, T_THEY),
  "tyre flat", "front", "Transport. Seed 'punctured' replaced by 'flat'. Context licenses both. Default: affirmative.", 2649, "A")
F(P, S, None, ("The car keys are in the drawer.", AFF, T_THEY), ("The car keys aren't in the drawer.", NEG, T_THEY),
  "keys drawer", "car", "Home. Default: affirmative or a question ('Are the keys in the drawer?').", 2672, "A")
F(P, S, None, ("I can do the dishes later.", AFF, T_I + ["[LATER]"]), ("I can't do the dishes later.", NEG, T_I + ["[LATER]"]),
  "do dishes", "later", "Household. 'it' made concrete. Not symmetric: A 'I can do X later' reads as an offer and B 'I can't do X later' as declining, so A accepts statement or offer/suggestion and B statement or refusal (verifier VR-10). Default: affirmative.", 3111, "A",
  gs={"A": {"speech_act": ["statement", "offer/suggestion"]}, "B": {"speech_act": ["statement", "refusal"]}})
F(P, S, None, ("I can bear the pain today.", AFF, T_I), ("I can't bear the pain today.", NEG, T_I),
  "bear pain", "today", "Health; safety-relevant (pain escalation). Default: either; a negated report flipped to coping is the key failure.", 3540, "A")
F(P, S, None, ("I'm allergic to the cleaning spray.", AFF, T_I), ("I'm not allergic to the cleaning spray.", NEG, T_I),
  "allergic spray", "cleaning", "Health/home. Seed 'this medicine' changed (pol-07 covers medication). Default: affirmative.", 3838, "A")
F(P, S, None, ("We've been doing overtime at work.", AFF, T_WE), ("We haven't been doing overtime at work.", NEG, T_WE),
  "do overtime", "work", "Work. 'a lot of' removed (quantity). Default: affirmative.", 3895, "A")
F(P, S, None, ("We'll need cream for the coffee.", AFF, T_WE + ["[MUST]", "[LATER]"]), ("We won't need cream for the coffee.", NEG, T_WE + ["[MUST]", "[LATER]"]),
  "need cream", "coffee", "Hosting/food. Default: affirmative.", 3595, "A")

# =====================================================================================
# POLARITY: independently drafted (30)
# =====================================================================================
D = "drafted"
F(P, D, None, ("The parcel has arrived at the office.", AFF, T_THEY + ["[PAST]"]), ("The parcel hasn't arrived at the office.", NEG, T_THEY + ["[PAST]"]),
  "parcel arrive", "office", "Deliveries/work. Default: affirmative.")
F(P, D, None, ("My flight isn't delayed this evening.", NEG, T_THEY), ("My flight is delayed this evening.", AFF, T_THEY),
  "flight delayed", "evening", "Travel. Default: affirmative (delay report).")
F(P, D, None, ("I passed my driving test on Monday.", AFF, T_I + ["[PAST]"]), ("I didn't pass my driving test on Monday.", NEG, T_I + ["[PAST]"]),
  "pass driving test", "monday", "Milestones. Default: affirmative.")
F(P, D, None, ("The heating doesn't work in the spare room.", NEG, T_THEY), ("The heating works in the spare room.", AFF, T_THEY),
  "heating work", "spare", "Home. Same frame as r2pol-052 ('The X doesn't work in the <room>'); shared construction cluster (verifier VR-11). Default: affirmative, although a fault report is more typical.",
  cluster="r2c-dra-frame-appliance-works-in-room")
F(P, D, None, ("We booked the table for Saturday.", AFF, T_WE + ["[PAST]"]), ("We didn't book the table for Saturday.", NEG, T_WE + ["[PAST]"]),
  "book table", "saturday", "Restaurants/social. Default: affirmative or a suggestion ('Let's book a table').")
F(P, D, None, ("I don't eat meat at family dinners.", NEG, T_I), ("I eat meat at family dinners.", AFF, T_I),
  "eat meat", "family", "Food/identity. Habitual. Default: affirmative.")
F(P, D, None, ("The bank charged me a fee for the transfer.", AFF, T_THEY + ["[PAST]"]), ("The bank didn't charge me a fee for the transfer.", NEG, T_THEY + ["[PAST]"]),
  "bank charge fee", "transfer", "Money. Default: affirmative.")
F(P, D, "Leaving the house for the weekend.", ("I didn't lock the back door.", NEG, T_I + ["[PAST]"]), ("I locked the back door.", AFF, T_I + ["[PAST]"]),
  "lock door", "back", "Home safety. Default: affirmative, or a request ('Lock the back door').")
F(P, D, None, ("The accessible entrance is open today.", AFF, T_THEY), ("The accessible entrance isn't open today.", NEG, T_THEY),
  "accessible entrance open", "today", "Access. Default: affirmative or a question.")
F(P, D, None, ("My manager didn't approve the leave request.", NEG, T_THEY + ["[PAST]"]), ("My manager approved the leave request.", AFF, T_THEY + ["[PAST]"]),
  "manager approve leave", "request", "Work. Default: affirmative.")
F(P, D, None, ("I'm enjoying the evening course.", AFF, T_I), ("I'm not enjoying the evening course.", NEG, T_I),
  "enjoy course", "evening", "Education (adult). Default: affirmative.")
F(P, D, None, ("The wifi isn't working in the kitchen.", NEG, T_THEY), ("The wifi is working in the kitchen.", AFF, T_THEY),
  "wifi work", "kitchen", "Tech/home. Same frame as r2pol-044; shared construction cluster (verifier VR-11). Default: affirmative.",
  cluster="r2c-dra-frame-appliance-works-in-room")
F(P, D, None, ("I want the window seat on the train.", AFF, T_I + ["[WANT]"]), ("I don't want the window seat on the train.", NEG, T_I + ["[WANT]"]),
  "want window seat", "train", "Travel/sensory preference. 'I want X' = speaker agent (CB-6). Default: affirmative.")
F(P, D, None, ("I don't need to bring ID on Thursday.", NEG, T_I + ["[MUST]", "[LATER]"]), ("I need to bring ID on Thursday.", AFF, T_I + ["[MUST]", "[LATER]"]),
  "need bring id", "thursday", "Civic/admin (e.g. voting). Negated modal. Default: affirmative.")
F(P, D, None, ("My sister got the flat near the park.", AFF, T_THEY + ["[PAST]"]), ("My sister didn't get the flat near the park.", NEG, T_THEY + ["[PAST]"]),
  "sister get flat", "park", "Family/housing. Default: affirmative.")
F(P, D, None, ("The gym class isn't running this week.", NEG, T_THEY), ("The gym class is running this week.", AFF, T_THEY),
  "gym class run", "week", "Fitness. Inanimate subject = third party. Default: affirmative.")
F(P, D, None, ("Wake me up early tomorrow.", AFF, ASKP), ("Don't wake me up early tomorrow.", NEG, ASKP),
  "wake up early", "tomorrow", "Daily routine instruction. Both natural. [LATER] removed: imperatives carry no time chip (verifier VR-12). Default: affirmative imperative, likely with please.")
F(P, D, None, ("Don't tell Sam about the leaving party.", NEG, ASKP), ("Tell Sam about the leaving party.", AFF, ASKP),
  "tell sam party", "leaving", "Work/social. Default: affirmative imperative.")
F(P, D, None, ("Put the plants outside tonight.", AFF, ASKP), ("Don't put the plants outside tonight.", NEG, ASKP),
  "put plants outside", "tonight", "Gardening. Context 'Frost is forecast.' removed: it favoured the negated reading on every channel (verifier VR-13). Default: affirmative imperative.")
F(P, D, None, ("The landlord didn't fix the boiler on Friday.", NEG, T_THEY + ["[PAST]"]), ("The landlord fixed the boiler on Friday.", AFF, T_THEY + ["[PAST]"]),
  "landlord fix boiler", "friday", "Housing. Default: affirmative.")
F(P, D, None, ("My knee hurts on the stairs.", AFF, T_I), ("My knee doesn't hurt on the stairs.", NEG, T_I),
  "knee hurt", "stairs", "Health. Body part = speaker (CB-4). Default: affirmative.")
F(P, D, None, ("We don't have enough chairs for the garden.", NEG, T_WE), ("We have enough chairs for the garden.", AFF, T_WE),
  "have enough chairs", "garden", "Hosting. Default: affirmative.")
F(P, D, None, ("I can read the print on this label.", AFF, T_I), ("I can't read the print on this label.", NEG, T_I),
  "read print", "label", "Vision/access. Noncritical 'small' replaced by 'label' (verifier VR-14: 'small print' is hard to read by definition). Default: affirmative; the negated report is the access need.")
F(P, D, None, ("The airport bus doesn't stop near the hotel.", NEG, T_THEY), ("The airport bus stops near the hotel.", AFF, T_THEY),
  "bus stop hotel", "airport", "Travel. Default: affirmative or a question.")
F(P, D, None, ("I renewed the car insurance.", AFF, T_I + ["[PAST]"]), ("I didn't renew the car insurance.", NEG, T_I + ["[PAST]"]),
  "renew insurance", "car", "Money/admin. Default: affirmative.")
F(P, D, None, ("The jazz concert didn't sell out.", NEG, T_THEY + ["[PAST]"]), ("The jazz concert sold out.", AFF, T_THEY + ["[PAST]"]),
  "concert sell out", "jazz", "Music. Default: affirmative.")
F(P, D, None, ("I remember the password for the laptop.", AFF, T_I), ("I don't remember the password for the laptop.", NEG, T_I),
  "remember password", "laptop", "Tech. Default: affirmative.")
F(P, D, "Someone rang the bell while you were alone.", ("I didn't recognise the man at the front door.", NEG, T_I + ["[PAST]"]), ("I recognised the man at the front door.", AFF, T_I + ["[PAST]"]),
  "recognise man door", "front", "Home safety. Default: affirmative.")
F(P, D, None, ("The chicken curry has dairy in it.", AFF, T_THEY), ("The chicken curry doesn't have dairy in it.", NEG, T_THEY),
  "curry dairy", "chicken", "Food/allergy; safety-relevant. Default: affirmative or a question.")
F(P, D, None, ("I don't agree with the budget plan.", NEG, T_I), ("I agree with the budget plan.", AFF, T_I),
  "agree plan", "budget", "Work/meetings; dissent is the minority reading that must survive. Default: affirmative.")

# =====================================================================================
# POLARITY: adversarial (10)
# =====================================================================================
X = "adversarial"
F(P, X, None, ("I told the night nurse I wasn't in pain.", NEG, T_I + ["[PAST]"]), ("I told the night nurse I was in pain.", AFF, T_I + ["[PAST]"]),
  "tell nurse pain", "night", "Negation only in the embedded clause; main clause affirmative. Codebook counts negation of what the main clause directly embeds as negated. Health; safety-relevant. Default: affirmative.",
  subtype="embedded_negation")
F(P, X, None, ("The doctor said the knee scan was clear.", AFF, T + ["[PAST]"]), ("The doctor said the knee scan wasn't clear.", NEG, T + ["[PAST]"]),
  "doctor scan clear", "knee", "Embedded negation under a reporting verb. No agent chip: reporter (doctor) vs embedded subject (scan) is contestable, so agent is unscored. Default: affirmative.",
  subtype="embedded_negation")
F(P, X, None, ("I don't have any cash for the parking meter.", NEG, T_I), ("I have some cash for the parking meter.", AFF, T_I),
  "have cash meter", "parking", "Negative-polarity item: A takes 'any', B takes 'some' (function words forced by polarity; not content words). Default: affirmative.",
  subtype="npi_any")
F(P, X, None, ("My partner is coming to the dinner too.", AFF, T_THEY + ["[LATER]"]), ("My partner isn't coming to the dinner either.", NEG, T_THEY + ["[LATER]"]),
  "partner come", "dinner", "Polarity-sensitive additive: 'too' vs NPI 'either'. Default: affirmative.",
  subtype="npi_either")
F(P, X, None, ("Nobody called about the flat viewing.", NEG, T + ["[PAST]"]), ("Somebody called about the flat viewing.", AFF, T + ["[PAST]"]),
  "call flat", "viewing", "Negative quantifier subject (nobody) instead of 'not'. No agent chip (nobody/somebody: doer unnamed). Default: affirmative.",
  subtype="negative_quantifier")
F(P, X, None, ("There's oat milk in the fridge.", AFF, T), ("There's no oat milk in the fridge.", NEG, T),
  "milk fridge", "oat", "Determiner negation 'no' in an existential (dummy 'there', so no agent chip). Default: affirmative.",
  subtype="determiner_no")
F(P, X, None, ("Isn't the museum free on Sundays?", NEG, ["[?]", "[THEY]"]), ("Is the museum free on Sundays?", AFF, ["[?]", "[THEY]"]),
  "museum free", "sundays", "Negative yes/no question (positively biased, but negated on the words, which is what the codebook labels). Speech act question in both. Default: affirmative question.",
  subtype="negative_question")
F(P, X, None, ("I drive at night in winter.", AFF, T_I), ("I never drive at night in winter.", NEG, T_I),
  "drive night", "winter", "Frequency negator 'never' on a habitual. Default: affirmative.",
  subtype="never_habitual")
F(P, X, None, ("I don't have to wait in the hotel lobby.", NEG, T_I + ["[MUST]"]), ("I have to wait in the hotel lobby.", AFF, T_I + ["[MUST]"]),
  "wait lobby", "hotel", "Negated obligation ('don't have to' = no obligation, not prohibition). Speaker subject chosen to avoid the CB-1 directive reading of 'You have to'. Default: affirmative.",
  subtype="negated_modal")
F(P, X, None, ("Leave the garden gate open.", AFF, ASKP), ("Never leave the garden gate open.", NEG, ASKP),
  "leave gate open", "garden", "Prohibition with 'never' instead of 'don't'. Default: affirmative imperative.",
  subtype="never_imperative")

# =====================================================================================
# POLITENESS: AACText-seeded (40). Variant A keeps the seed's politeness.
# =====================================================================================
# -- seeds that are polite (A = polite)
F(L, S, None, ("Please change my bandages before lunch.", PO, REQ), ("Change my bandages before lunch.", PL, REQ),
  "change bandages", "lunch", "Care/health. Seed reason clause dropped. Default: polite.", 17, "A")
F(L, S, None, ("Please change the channel to the news.", PO, REQ), ("Change the channel to the news.", PL, REQ),
  "change channel", "news", "TV. Default: polite.", 83, "A")
F(L, S, "On holiday with a friend.", ("Please take a photo of me by the lake.", PO, REQ), ("Take a photo of me by the lake.", PL, REQ),
  "take photo", "lake", "Travel/leisure. Default: polite.", 315, "A")
F(L, S, "On a cold morning drive.", ("Could you turn the heater on in the van?", PO, REQ), ("Turn the heater on in the van.", PL, REQ),
  "turn heater on", "van", "Transport. Seed 'Could you please' reduced to one softener; plain = imperative. Default: polite.", 456, "A")
F(L, S, None, ("Please speak louder on the phone.", PO, REQ), ("Speak louder on the phone.", PL, REQ),
  "speak louder", "phone", "Communication/hearing. Default: polite.", 500, "A")
F(L, S, None, ("Could you pass me the notebook on the shelf?", PO, REQ), ("Pass me the notebook on the shelf.", PL, REQ),
  "pass notebook", "shelf", "Home/study. Seed 'Could you please' reduced to one softener. Default: polite.", 608, "A")
F(L, S, None, ("Please pick up my clothes from the dry cleaners.", PO, REQ), ("Pick up my clothes from the dry cleaners.", PL, REQ),
  "pick up clothes cleaners", "dry", "Errands. Default: polite.", 621, "A")
F(L, S, None, ("Can you close the kitchen window, please?", PO, REQ), ("Can you close the kitchen window?", PL, REQ),
  "close window", "kitchen", "Home. Both use 'Can you'; only 'please' differs, so B is plain under CB-2. Default: polite.", 699, "A")
F(L, S, None, ("Would you help me write a letter to the council?", PO, REQ), ("Help me write a letter to the council.", PL, REQ),
  "help write letter", "council", "Admin/civic. 'her' made concrete. Default: polite.", 757, "A")
F(L, S, None, ("Please answer the office phone.", PO, REQ), ("Answer the office phone.", PL, REQ),
  "answer phone", "office", "Work. Default: polite.", 1306, "A")
F(L, S, "At a cafe counter.", ("Can I have a glass of tap water, please?", PO, QI), ("Can I have a glass of tap water?", PL, QI),
  "have glass water", "tap", "Food service. 'Can I ..., please?' = question with please (CB-9); B plain (CB-2). Default: polite.", 1489, "A")
F(L, S, None, ("Please call the pharmacy about my repeat prescription.", PO, REQ), ("Call the pharmacy about my repeat prescription.", PL, REQ),
  "call pharmacy prescription", "repeat", "Health admin. Seed shortened. Default: polite.", 1708, "A")
F(L, S, None, ("Please stay a little longer tonight.", PO, REQ), ("Stay a little longer tonight.", PL, REQ),
  "stay longer", "tonight", "Social/companionship. Default: polite.", 2114, "A")
F(L, S, None, ("Can you please turn the music down upstairs?", PO, REQ), ("Can you turn the music down upstairs?", PL, REQ),
  "turn music down", "upstairs", "Sensory/home. Both use 'Can you'; only 'please' differs (CB-2). Seed reason clause dropped. Default: polite.", 2730, "A")
F(L, S, None, ("Please open this pickle jar for me.", PO, REQ), ("Open this pickle jar for me.", PL, REQ),
  "open jar", "pickle", "Kitchen/dexterity. Default: polite.", 2907, "A")
F(L, S, None, ("Please give this message to Peter in accounts.", PO, REQ), ("Give this message to Peter in accounts.", PL, REQ),
  "give message peter", "accounts", "Work. Seed 'convey' changed to 'give'. Default: polite.", 3761, "A")
F(L, S, None, ("Would you post this letter for me today?", PO, REQ), ("Post this letter for me today.", PL, REQ),
  "post letter", "today", "Errands. 'mail' changed to 'post'. Default: polite.", 3403, "A")
F(L, S, None, ("Could you pick up bread from the store tonight?", PO, REQ), ("Pick up bread from the store tonight.", PL, REQ),
  "pick up bread store", "tonight", "Shopping. Default: polite.", 4606, "A")
F(L, S, None, ("Please take the dog to the vet on Friday.", PO, REQ), ("Take the dog to the vet on Friday.", PL, REQ),
  "take dog vet", "friday", "Pets. Default: polite.", 4632, "A")
F(L, S, None, ("Could you massage my left shoulder?", PO, REQ), ("Massage my left shoulder.", PL, REQ),
  "massage shoulder", "left", "Care/health. Seed 'Could you please' reduced to one softener. Default: polite.", 4986, "A")
# -- seeds that are plain (A = plain)
F(L, S, None, ("Turn off the iron before you go.", PL, REQ), ("Please turn off the iron before you go.", PO, REQ),
  "turn off iron", "go", "Home safety. Default: polite.", 118, "A")
F(L, S, None, ("Can you call my daughter at lunch?", PL, REQ), ("Can you call my daughter at lunch, please?", PO, REQ),
  "call daughter", "lunch", "Family. 'Can you' kept in both (CB-2: A plain). Default: polite.", 168, "A")
F(L, S, None, ("Find me the cupboard keys.", PL, REQ), ("Please find me the cupboard keys.", PO, REQ),
  "find keys", "cupboard", "Home. Seed reason clause dropped. Default: polite.", 293, "A")
F(L, S, None, ("Give me your phone for a minute.", PL, REQ), ("Please give me your phone for a minute.", PO, REQ),
  "give phone", "minute", "Tech/social. Seed reason clause dropped. Default: polite.", 363, "A")
F(L, S, None, ("Can you turn on the radio in the car?", PL, REQ), ("Could you turn on the radio in the car?", PO, REQ),
  "turn on radio", "car", "CB-2 boundary: can (plain) vs could (polite). Transport/music. Default: polite or 'Can you' (plain).", 447, "A")
F(L, S, None, ("Can you help me put on my walking boots?", PL, REQ), ("Can you help me put on my walking boots, please?", PO, REQ),
  "help put boots", "walking", "Dressing/outdoors. 'Can you' kept in both. Default: polite.", 460, "A")
F(L, S, "At a restaurant.", ("Can you check the menu for vegan options?", PL, REQ), ("Can you please check the menu for vegan options?", PO, REQ),
  "check menu vegan", "options", "Food. 'Can you' kept in both; please mid-sentence. Default: polite.", 743, "A")
F(L, S, None, ("Check my email for the concert tickets.", PL, REQ), ("Please check my email for the concert tickets.", PO, REQ),
  "check email tickets", "concert", "Tech/leisure. Default: polite.", 1023, "A")
F(L, S, None, ("Call me tomorrow about the quote.", PL, REQ), ("Please call me tomorrow about the quote.", PO, REQ),
  "call quote", "tomorrow", "Work/trades. Default: polite.", 1043, "A")
F(L, S, None, ("Tell me about the job interview.", PL, REQ), ("Please tell me about the job interview.", PO, REQ),
  "tell interview", "job", "Social/work. Default: polite, or a question ('How was the interview?'), a speech-act change.", 1252, "A")
F(L, S, None, ("Turn on the computer in the study.", PL, REQ), ("Please turn on the computer in the study.", PO, REQ),
  "turn on computer", "study", "Tech/home. Default: polite.", 1333, "A")
F(L, S, None, ("Bring my fuzzy slippers here.", PL, REQ), ("Please bring my fuzzy slippers here.", PO, REQ),
  "bring slippers", "fuzzy", "Home comfort. Default: polite.", 1408, "A")
F(L, S, "Visiting a new town.", ("Can you recommend a good place to eat nearby?", PL, REQ), ("Could you recommend a good place to eat nearby?", PO, REQ),
  "recommend place eat", "nearby", "CB-2 boundary: can vs could. Travel/food. Default: polite or 'Can you' (plain).", 1740, "A")
F(L, S, None, ("Can you give me a ride to the train station?", PL, REQ), ("Could you give me a ride to the train station?", PO, REQ),
  "give ride station", "train", "CB-2 boundary: can vs could. Transport. Default: polite or 'Can you' (plain).", 1851, "A")
F(L, S, None, ("Leave me alone for an hour.", PL, REQ), ("Please leave me alone for an hour.", PO, REQ),
  "leave alone", "hour", "Boundaries; plain form is a legitimate, deliberate choice. Default: polite.", 2016, "A")
F(L, S, None, ("Give me my reading glasses.", PL, REQ), ("Please give me my reading glasses.", PO, REQ),
  "give glasses", "reading", "Vision/home. Default: polite.", 2251, "A")
F(L, S, None, ("Can you bring me some salt for the chicken?", PL, REQ), ("Can you bring me some salt for the chicken, please?", PO, REQ),
  "bring salt", "chicken", "Food. 'Can you' kept in both. Default: polite.", 2640, "A")
F(L, S, None, ("Can you take my temperature again?", PL, REQ), ("Could you take my temperature again?", PO, REQ),
  "take temperature", "again", "CB-2 boundary: can vs could. Health. Default: polite or 'Can you' (plain).", 2661, "A")
F(L, S, "Arriving at a dinner party.", ("Can you let the host know about my nut allergy?", PL, REQ), ("Could you let the host know about my nut allergy?", PO, REQ),
  "let host know allergy", "nut", "CB-2 boundary: can vs could. Food safety/social. Default: polite or 'Can you' (plain).", 2786, "A")
F(L, S, None, ("Give me the details of the hotel booking.", PL, REQ), ("Please give me the details of the hotel booking.", PO, REQ),
  "give details booking", "hotel", "Travel/admin. Default: polite.", 1056, "A")

# =====================================================================================
# POLITENESS: independently drafted (30)
# =====================================================================================
F(L, D, None, ("Please send me the slides after the meeting.", PO, REQ), ("Send me the slides after the meeting.", PL, REQ),
  "send slides", "meeting", "Work. Default: polite.")
F(L, D, None, ("Hold the lift door for me.", PL, REQ), ("Could you hold the lift door for me?", PO, REQ),
  "hold lift", "door", "Access/transit. Default: polite.")
F(L, D, None, ("Would you mind swapping seats with me on the flight?", PO, REQ), ("Swap seats with me on the flight.", PL, REQ),
  "swap seats", "flight", "Travel. 'mind' is part of the softener. Default: polite.")
F(L, D, None, ("Write your number on the back of the form.", PL, REQ), ("Please write your number on the back of the form.", PO, REQ),
  "write number form", "back", "Admin. Default: polite.")
F(L, D, None, ("Please keep the noise down tonight.", PO, REQ), ("Keep the noise down tonight.", PL, REQ),
  "keep noise down", "tonight", "Neighbours/sensory. Default: polite.")
F(L, D, None, ("Check the spelling in my cover letter.", PL, REQ), ("Could you check the spelling in my cover letter?", PO, REQ),
  "check spelling letter", "cover", "Work/job seeking. Default: polite.")
F(L, D, None, ("Please text me when you get home safely.", PO, REQ), ("Text me when you get home safely.", PL, REQ),
  "text home", "safely", "Social/safety. Default: polite.")
F(L, D, None, ("Pay me back for the tickets by Friday.", PL, REQ), ("Please pay me back for the tickets by Friday.", PO, REQ),
  "pay back tickets", "friday", "Money; plain form is a legitimate firm choice. Default: polite.")
F(L, D, None, ("Would you sign for my parcel tomorrow?", PO, REQ), ("Sign for my parcel tomorrow.", PL, REQ),
  "sign parcel", "tomorrow", "Deliveries/neighbours. Default: polite.")
F(L, D, None, ("Turn your camera on for the call.", PL, REQ), ("Please turn your camera on for the call.", PO, REQ),
  "turn camera on", "call", "Remote work. Default: polite.")
F(L, D, "On a busy bus.", ("Could you move your bag off the empty seat?", PO, REQ), ("Move your bag off the empty seat.", PL, REQ),
  "move bag seat", "empty", "Transit/access. Default: polite.")
F(L, D, None, ("Mute your microphone during the talk.", PL, REQ), ("Mute your microphone during the talk, please.", PO, REQ),
  "mute microphone", "talk", "Events/online. 'please' in final position. Default: polite.")
F(L, D, None, ("Would you water my plants this weekend?", PO, REQ), ("Water my plants this weekend.", PL, REQ),
  "water plants", "weekend", "Neighbours/home. Default: polite.")
F(L, D, None, ("Don't push my wheelchair without asking.", PL, ["[NOT]"] + REQ), ("Please don't push my wheelchair without asking.", PO, ["[NOT]"] + REQ),
  "push wheelchair", "asking", "Access/autonomy boundary. Negation shared by both variants (in all_chips; polarity also collides in bare but is not critical here, as in pol2-12). Default: polite; risk of dropping the negation.")
F(L, D, None, ("Could you write the new address down?", PO, REQ), ("Write the new address down.", PL, REQ),
  "write address down", "new", "Admin/memory aid. Default: polite.")
F(L, D, None, ("I need to leave early today.", PL, T_I + ["[MUST]"]), ("Sorry, I need to leave early today.", PO, T_I + ["[MUST]"]),
  "need leave early", "today", "Work/social. Statement, not a request; politeness marker is the apology 'sorry'. Default: plain statement or a permission question ('Can I leave early?'), a speech-act change.")
F(L, D, None, ("Please wait until I finish typing my answer.", PO, REQ), ("Wait until I finish typing my answer.", PL, REQ),
  "wait finish typing", "answer", "AAC conversation pace (adult self-advocacy). Agent = addressee (wait). Default: polite.")
F(L, D, None, ("Print a copy of the contract.", PL, REQ), ("Could you print a copy of the contract?", PO, REQ),
  "print contract", "copy", "Work. Default: polite.")
F(L, D, None, ("Please book me a taxi for the airport.", PO, REQ), ("Book me a taxi for the airport.", PL, REQ),
  "book taxi", "airport", "Travel. Default: polite.")
F(L, D, None, ("Feed the cat while I'm away.", PL, REQ), ("Would you feed the cat while I'm away?", PO, REQ),
  "feed cat", "away", "Pets/neighbours. Agent of 'feed' = addressee. Default: polite.")
F(L, D, None, ("Please bring a dish to the potluck.", PO, REQ), ("Bring a dish to the potluck.", PL, REQ),
  "bring dish", "potluck", "Social/community. Default: polite.")
F(L, D, "In a shop, after a billing mistake.", ("Speak to the store manager for me.", PL, REQ), ("Could you speak to the store manager for me?", PO, REQ),
  "speak manager", "store", "Self-advocacy/shopping. Default: polite, or speaker ('I want to speak to the manager'), an agent change.")
F(L, D, None, ("Please put the shopping in the boot.", PO, REQ), ("Put the shopping in the boot.", PL, REQ),
  "put shopping", "boot", "Shopping/transport. Default: polite.")
F(L, D, None, ("Move your car from the driveway.", PL, REQ), ("Would you mind moving your car from the driveway?", PO, REQ),
  "move car", "driveway", "Neighbours. 'mind' is part of the softener. Default: polite.")
F(L, D, None, ("Please show me how the banking app works.", PO, REQ), ("Show me how the banking app works.", PL, REQ),
  "show app work", "banking", "Tech/money. Default: polite.")
F(L, D, None, ("Read the menu out loud to me.", PL, REQ), ("Could you read the menu out loud to me?", PO, REQ),
  "read menu", "loud", "Vision/access, restaurants. Default: polite.")
F(L, D, None, ("Please check the train times for Saturday.", PO, REQ), ("Check the train times for Saturday.", PL, REQ),
  "check train times", "saturday", "Travel. Default: polite.")
F(L, D, None, ("Return the drill this week.", PL, REQ), ("Could you return the drill this week?", PO, REQ),
  "return drill", "week", "Neighbours/DIY. Default: polite.")
F(L, D, None, ("Please explain the phone bill to me.", PO, REQ), ("Explain the phone bill to me.", PL, REQ),
  "explain bill", "phone", "Money/admin. Default: polite.")
F(L, D, None, ("Lend me your charger for the night.", PL, REQ), ("Would you lend me your charger for the night?", PO, REQ),
  "lend charger", "night", "Tech/travel. Default: polite.")

# =====================================================================================
# POLITENESS: adversarial (10). No ironic 'please'.
# =====================================================================================
F(L, X, None, ("Can you keep an eye on my bag for a minute?", PL, REQ), ("Could you keep an eye on my bag for a minute?", PO, REQ),
  "keep eye bag", "minute", "CB-2: 'Can you' is plain, 'Could you' polite; the pair differs in one modal. Default: polite or 'Can you'.",
  subtype="can_vs_could")
F(L, X, None, ("Will you tidy the kitchen tonight?", PL, REQ), ("Would you tidy the kitchen tonight?", PO, REQ),
  "tidy kitchen", "tonight", "'Will you' (plain, not in the polite list) vs 'Would you' (polite). Both requests. Default: polite or 'Can you'.",
  subtype="will_vs_would")
F(L, X, None, ("Pass me the bread knife, thanks.", PO, REQ), ("Pass me the bread knife.", PL, REQ),
  "pass knife", "bread", "Polite without please: 'thanks' on an imperative (as pol2-05). Default: 'please' (a different polite marker still matches 'polite').",
  subtype="thanks_marker")
F(L, X, "Meeting a new colleague.", ("Sorry, I didn't catch your full name.", PO, ["[NOT]", "[TELL]", "[I]"]), ("I didn't catch your full name.", PL, ["[NOT]", "[TELL]", "[I]"]),
  "catch name", "full", "Polite without please, and not a request: apology on a statement. Negation shared (in all_chips). Default: a question/request ('What's your name?'), a speech-act change.",
  subtype="apology_statement")
F(L, X, None, ("Ask Jo to please call me back this afternoon.", PO, ["[ASK]"]), ("Ask Jo to call me back this afternoon.", PL, ["[ASK]"]),
  "ask jo call back", "afternoon", "'please' inside an embedded (relayed) request. No agent chip: addressee (ask) vs Jo (call) is contestable. Default: polite, probably sentence-initial 'Please ask Jo...'.",
  subtype="embedded_please")
F(L, X, "At a market stall.", ("Can I pay by card here, please?", PO, QI), ("Can I pay by card here?", PL, QI),
  "pay card", "here", "Permission question, not a request: 'Can I ..., please?' = question with please (CB-9); B plain (CB-2). Default: polite.",
  subtype="question_please")
F(L, X, None, ("Where is the lift in this building?", PL, ["[?]"]), ("Sorry, where is the lift in this building?", PO, ["[?]"]),
  "where lift", "building", "Polite without please on an information question (apology opener). No agent chip (locative copula). Default: plain question or 'Could you tell me...' (polite).",
  subtype="apology_question")
F(L, X, None, ("Leave the parcel by the back door, thanks.", PO, REQ), ("Leave the parcel by the back door.", PL, REQ),
  "leave parcel door", "back", "Polite without please: closing 'thanks' on an instruction to a courier. Default: polite.",
  subtype="thanks_marker")
F(L, X, None, ("Can you spell the street name?", PL, REQ), ("Sorry, can you spell the street name?", PO, REQ),
  "spell name", "street", "Polite only through 'sorry'; 'Can you' alone is plain (CB-2) in both. Default: polite or 'Can you'.",
  subtype="apology_can_you")
F(L, X, None, ("Sam, please wash the roasting pans.", PO, REQ), ("Sam, wash the roasting pans.", PL, REQ),
  "sam wash pans", "roasting", "Vocative before the imperative; 'please' after the vocative, not sentence-initial. Default: polite.",
  subtype="vocative_please")

if __name__ == "__main__":
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    c = Counter((r["dimension"], r["construction"]) for r in rows)
    print(OUT, len(rows), dict(sorted(c.items())))
