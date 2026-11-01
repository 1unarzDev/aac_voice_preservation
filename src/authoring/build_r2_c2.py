"""Builder for data/items/r2_c2.jsonl: W-C speech-act stratum, 80 families r2act-001..080.

All sentences were hand-written / hand-edited by the item author (Claude); no LLM API was used.
Edit here, not the JSONL.  Re-run:
    python3 src/authoring/build_r2_c2.py && python3 src/validate_items.py data/items/r2_c2.jsonl

Design (round-2 W-C, speech act; no refusal/acceptance pairs):
  contrasts      statement-question (SQ), request-statement (RS), question-request (QR)
  construction   seeded (40): one variant is a minimally edited real message from
                 data/raw/aactext/sent_train_aac.txt (never a line whose text is in
                 data/specs/aactext_sample400.jsonl); the partner is the speech-act counterfactual.
                 drafted (30): written independently.  adversarial (10): codebook boundary cases
                 ("Can I ...?" = question; you-subject declaratives = statement, CB-1;
                 indirect requests "I need you to ...", keyed request/command, agent per CB-7;
                 "Will you ...?" request vs "Did you ...?" question).
  Agent and polarity are held constant inside every family (affirmative throughout; requests are
  addressee-agent, so their statement partners are you-subject declaratives in the past or present,
  never "You'll ..." except the deliberate CB-1 adversarial item).
  Requests carry [PLAIN]: no please/could/would anywhere (CB-2: "Can you ...?" is plain).
  template: the syntactic construction pair (e.g. can-you~did-you).
  cluster_id: seeded -> r2c-seed-NNNNN (one cluster per seed line, same id as build_r2_c1 so a seed used in
  two strata is one cluster); drafted -> r2c-dra-<order-free template>; adversarial -> r2c-adv-<boundary
  construction> (verifier V2-03, analysis/item_verification/r2_c2.md).
  primary_exclude: "D-018" (exclusion code) on the two "I need you to ..." families (excluded from P1, descriptive only).
  A/B order alternates by family index so neither value is systematically variant A.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import prompts as P  # noqa: E402

OPTS = ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"]
S, Q, R = "statement", "question", "request/command"
CHIP = {S: "[TELL]", Q: "[?]", R: "[ASK]"}
CONTRAST = {frozenset({S, Q}): "statement-question", frozenset({R, S}): "request-statement",
            frozenset({Q, R}): "question-request"}
ACTOR = {"I": "[I]", "YOU": "[YOU]", "WE": "[WE]", "THEY": "[THEY]", None: None}

# seeded(seed_line, construction, (seed-derived source, value), (counterfactual partner, value), actor,
#        bare, noncritical, seed_edit, note).  seed_edit records how the seed variant differs from the raw line.
SEEDED: list[dict] = []


def seeded(line, construction, seed, partner, actor, bare, nc, edit, note):
    SEEDED.append(dict(line=line, construction=construction, seed=seed, partner=partner, actor=actor,
                       bare=bare, nc=nc, edit=edit, note=note))


# ---------------- AACText-seeded: statement vs question (14) ----------------
seeded(607, "be-inversion", ("Is the phone in silent mode?", Q), ("The phone is in silent mode.", S), "THEY",
       "phone silent", "mode", "verbatim", "Device state check vs report. Default: question or a request to silence the phone (speech-act change).")
seeded(3107, "be-inversion(there)", ("Is there Internet access at the library?", Q), ("There is Internet access at the library.", S), None,
       "internet access", "library", "verbatim", "Dummy 'there': agent unspecified, so no actor chip (as act-12). Default: question.")
seeded(221, "do-support", ("My new computer just arrived.", S), ("Did my new computer just arrive?", Q), "THEY",
       "computer arrive", "new", "verbatim", "Inanimate subject = third party (CB-4). Default: statement.")
seeded(1203, "do-support", ("We need more groceries.", S), ("Do we need more groceries?", Q), "WE",
       "need groceries", "more", "verbatim", "Household planning. Default: statement, possibly speaker 'I need' (agent change).")
seeded(2672, "be-inversion", ("The keys are in the dining room.", S), ("Are the keys in the dining room?", Q), "THEY",
       "keys room", "dining", "verbatim", "Locating objects. Keys = inanimate third party (CB-4). Default: statement or 'Where are the keys?' (question with changed content).")
seeded(1050, "be-inversion", ("Are you ready for your new job?", Q), ("You are ready for your new job.", S), "YOU",
       "ready job", "new", "verbatim", "Statement partner is a you-subject declarative = statement (CB-1). Default: question.")
seeded(2291, "be-inversion", ("My cell phone is broken.", S), ("Is my cell phone broken?", Q), "THEY",
       "phone broken", "cell", "verbatim", "Device report vs check. Default: statement.")
seeded(4075, "aux-inversion(passive)", ("The meeting has been moved to tomorrow afternoon.", S),
       ("Has the meeting been moved to tomorrow afternoon?", Q), None,
       "meeting move", "afternoon", "had been -> has been (tense normalised)",
       "Agentless passive: agent unspecified, no actor chip. Default: statement.")
seeded(1739, "be-inversion", ("My new device is working well.", S), ("Is my new device working well?", Q), "THEY",
       "device working", "well", "added final period", "AAC device report. Default: statement.")
seeded(1607, "be-inversion(there)", ("There's a new night club in town.", S), ("Is there a new night club in town?", Q), None,
       "night club", "town", "verbatim", "Dummy 'there': agent unspecified. Default: statement.")
seeded(4295, "be-inversion", ("Mom was here last night.", S), ("Was mom here last night?", Q), "THEY",
       "mom here", "night", "verbatim", "Carer/family visit. Default: statement.")
seeded(3221, "aux-inversion", ("The dog has been scratching at the door.", S), ("Has the dog been scratching at the door?", Q), "THEY",
       "dog scratch", "door", "verbatim", "Pet behaviour. Default: statement; possible request reading ('Let the dog out').")
seeded(2625, "be-inversion", ("You are driving too fast.", S), ("Are you driving too fast?", Q), "YOU",
       "driving fast", "too", "verbatim", "Safety complaint vs check; you-subject declarative = statement (CB-1), risk of a command reading ('Slow down').")
seeded(3595, "aux-inversion", ("We will need cream for the coffee.", S), ("Will we need cream for the coffee?", Q), "WE",
       "need cream", "coffee", "added final period", "Hosting/shopping. Default: statement or 'We need cream' (time loss, unscored).")
# ---------------- AACText-seeded: request vs statement (13) ----------------
seeded(2640, "can-you~you-past", ("Can you bring me some salt for the chicken?", R), ("You brought me some salt for the chicken.", S), "YOU",
       "bring salt", "chicken", "verbatim", "Meal help. Default: request (likely with added please).")
seeded(430, "can-you~you-past", ("Can you get me some orange juice from the fridge?", R), ("You got me some orange juice from the fridge.", S), "YOU",
       "get juice fridge", "orange", "'out the fridge' -> 'from the fridge'; '.' -> '?'", "Drink request. Default: request.")
seeded(3241, "can-you~you-past", ("Can you get me some nail clippers?", R), ("You got me some nail clippers.", S), "YOU",
       "get clippers", "nail", "verbatim", "Personal care. Default: request.")
seeded(4532, "will-you~you-past", ("Will you go to the drug store for me?", R), ("You went to the drug store for me.", S), "YOU",
       "go store", "drug", "verbatim", "Errand. 'Will you ...?' = request (codebook). Default: request.")
seeded(3378, "can-you~you-past", ("Can you get me the new Harry Potter book?", R), ("You got me the new Harry Potter book.", S), "YOU",
       "get potter book", "new", "verbatim", "Leisure. Default: request.")
seeded(1408, "imperative~you-past", ("Bring the fuzzy slippers here.", R), ("You brought the fuzzy slippers here.", S), "YOU",
       "bring slippers", "fuzzy", "verbatim", "Comfort. Default: request.")
seeded(2360, "imperative~you-past", ("Get the details from my address book.", R), ("You got the details from my address book.", S), "YOU",
       "get details book", "address", "verbatim", "Admin help. Default: request.")
seeded(3734, "imperative~you-past", ("Put the dishes away.", R), ("You've put the dishes away.", S), "YOU",
       "put dishes", "away", "verbatim", "Chores. Partner uses the present perfect (verifier V2-01): past 'You put ...' is homographic with a subject-imperative/habitual reading. Default: request.")
seeded(4001, "imperative~you-past", ("Grab my keys off the desk.", R), ("You grabbed my keys off the desk.", S), "YOU",
       "grab keys", "desk", "capitalised, added period", "Daily help. Default: request.")
seeded(1816, "imperative~you-past", ("Bring some bread from the market.", R), ("You brought some bread from the market.", S), "YOU",
       "bring bread", "market", "capitalised, 'the' inserted, added period", "Shopping. Default: request.")
seeded(3464, "imperative~you-past", ("Take my credit card.", R), ("You took my credit card.", S), "YOU",
       "take card", "credit", "verbatim", "Money. Statement reading is a report/complaint; flipping it to an instruction authorises use of the card. Default: request.")
seeded(1454, "imperative~you-past", ("Find the TV remote for me.", R), ("You found the TV remote for me.", S), "YOU",
       "find remote", "tv", "capitalised, 'the' inserted, added period", "Home. Default: request.")
seeded(2926, "imperative~you-past", ("Get the chair from that room.", R), ("You got the chair from that room.", S), "YOU",
       "get chair", "room", "verbatim", "Home/mobility. Default: request.")
# ---------------- AACText-seeded: question vs request (13) ----------------
seeded(1172, "can-you~did-you", ("Can you increase the volume of the TV?", R), ("Did you increase the volume of the TV?", Q), "YOU",
       "increase volume", "tv", "verbatim", "Sensory/TV. Default: request.")
seeded(1861, "did-you~imperative", ("Did you mail the documents to my lawyer?", Q), ("Mail the documents to my lawyer.", R), "YOU",
       "mail documents", "lawyer", "verbatim", "Legal admin. Default: request; a question->request flip turns a check into an instruction.")
seeded(4453, "did-you~can-you", ("Did you pay the power bill?", Q), ("Can you pay the power bill?", R), "YOU",
       "pay bill", "power", "verbatim", "Money. Default: request or speaker statement ('I paid the bill').")
seeded(1613, "can-you~are-you-ing", ("Can you take my dog to the vet?", R), ("Are you taking my dog to the vet?", Q), "YOU",
       "take dog", "vet", "verbatim", "Pets. Default: request.")
seeded(4134, "can-you~did-you", ("Can you get my reports from the lab?", R), ("Did you get my reports from the lab?", Q), "YOU",
       "get reports", "lab", "verbatim", "Health admin. Default: request.")
seeded(4273, "can-you~are-you-ing", ("Can you pick up milk on your way home?", R), ("Are you picking up milk on your way home?", Q), "YOU",
       "pick up milk", "home", "typo 'pick pu' -> 'pick up', capitalised", "Errand. Default: request.")
seeded(4427, "can-you~did-you", ("Can you set my alarm clock?", R), ("Did you set my alarm clock?", Q), "YOU",
       "set alarm", "clock", "verbatim", "Daily routine. Default: request.")
seeded(3166, "can-you~did-you", ("Can you check my eBay account?", R), ("Did you check my eBay account?", Q), "YOU",
       "check account", "ebay", "verbatim", "Online admin. Default: request.")
seeded(3223, "can-you~did-you", ("Can you get some tickets for the match?", R), ("Did you get some tickets for the match?", Q), "YOU",
       "get tickets", "match", "verbatim", "Leisure. Default: request.")
seeded(3430, "can-you~did-you", ("Can you turn on the air conditioner?", R), ("Did you turn on the air conditioner?", Q), "YOU",
       "turn conditioner", "air", "verbatim", "Comfort. Default: request.")
seeded(2843, "did-you~imperative", ("Did you convey my message to the professor?", Q), ("Convey my message to the professor.", R), "YOU",
       "convey message", "professor", "verbatim", "Study/self-advocacy. Default: request.")
seeded(474, "did-you~imperative", ("Did you upload the new pics?", Q), ("Upload the new pics.", R), "YOU",
       "upload pics", "new", "verbatim", "Social media. Default: request.")
seeded(2814, "can-you~did-you", ("Can you open my email inbox for me?", R), ("Did you open my email inbox for me?", Q), "YOU",
       "open inbox", "email", "capitalised", "Online access. Default: request.")

# (construction, A=(source,value), B=(source,value), actor, bare, noncritical, context, note)
DRAFTED = [
    # ---- statement vs question (10) ----
    ("do-support", ("The pharmacy shuts early on Fridays.", S), ("Does the pharmacy shut early on Fridays?", Q), "THEY",
     "pharmacy shut", "fridays", None, "Errands. Inanimate/institution = third party (CB-4). Default: statement."),
    ("be-inversion", ("Is the station accessible by wheelchair?", Q), ("The station is accessible by wheelchair.", S), "THEY",
     "station wheelchair", "accessible", None, "Access/travel. Default: question."),
    ("be-inversion", ("We're out of coffee filters.", S), ("Are we out of coffee filters?", Q), "WE",
     "out filters", "coffee", None, "Household. Default: statement."),
    ("aux-inversion", ("Have you seen the new physio?", Q), ("You've seen the new physio.", S), "YOU",
     "see physio", "new", None, "Health. you-subject declarative = statement (CB-1). Default: question."),
    ("be-inversion", ("I'm on the waiting list for the flat.", S), ("Am I on the waiting list for the flat?", Q), "I",
     "waiting list", "flat", "At the housing office.", "Housing. Context licenses both the report and the check. Default: statement."),
    ("do-support", ("Did the landlord fix the boiler on Monday?", Q), ("The landlord fixed the boiler on Monday.", S), "THEY",
     "landlord fix boiler", "monday", None, "Housing. Default: statement."),
    ("do-support", ("The night bus stops outside the hospital.", S), ("Does the night bus stop outside the hospital?", Q), "THEY",
     "bus stop hospital", "night", None, "Transport. Default: statement or question about location."),
    ("be-inversion", ("Is your sister coming to the wedding reception?", Q), ("Your sister is coming to the wedding reception.", S), "THEY",
     "sister coming wedding", "reception", None, "Family. Default: question or statement."),
    ("do-support", ("The parcel from the bank needs a signature.", S), ("Does the parcel from the bank need a signature?", Q), "THEY",
     "parcel signature", "bank", None, "Post/admin. Default: statement."),
    ("be-inversion", ("Is the lake safe for swimming?", Q), ("The lake is safe for swimming.", S), "THEY",
     "lake safe", "swimming", None, "Leisure/safety. A question turned statement asserts unverified safety information. Default: question."),
    # ---- request vs statement (10) ----
    ("imperative~you-past", ("Text the plumber about the leak.", R), ("You texted the plumber about the leak.", S), "YOU",
     "text plumber", "leak", None, "Home repairs. Default: request."),
    ("imperative~you-past", ("You watered the tomatoes in the greenhouse.", S), ("Water the tomatoes in the greenhouse.", R), "YOU",
     "water tomatoes", "greenhouse", None, "Gardening. Default: request."),
    ("imperative~you-past", ("Put the phone charger in my rucksack.", R), ("You've put the phone charger in my rucksack.", S), "YOU",
     "put charger", "rucksack", None, "Packing. Present perfect statement (verifier V2-02): past 'You put ...' is homographic with a subject-imperative reading. Default: request."),
    ("can-you~you-past", ("You booked a table at the Thai place.", S), ("Can you book a table at the Thai place?", R), "YOU",
     "book table", "thai", None, "Social plans. Default: request."),
    ("imperative~you-past", ("Show the nurse the rash on my arm.", R), ("You showed the nurse the rash on my arm.", S), "YOU",
     "show nurse rash", "arm", None, "Health/self-advocacy. Default: request, or speaker ('I showed the nurse')."),
    ("imperative~you-past", ("You left the porch light on for me.", S), ("Leave the porch light on for me.", R), "YOU",
     "leave light", "porch", None, "Home/safety. Default: request."),
    ("can-you~you-past", ("Can you sort the recycling into the blue bags?", R), ("You sorted the recycling into the blue bags.", S), "YOU",
     "sort recycling", "blue", None, "Chores. Default: request."),
    ("imperative~you-past", ("You paid the window cleaner from the jar.", S), ("Pay the window cleaner from the jar.", R), "YOU",
     "pay window cleaner", "jar", None, "Money/home. Default: request."),
    ("imperative~you-past", ("Move my wheelchair closer to the bed.", R), ("You moved my wheelchair closer to the bed.", S), "YOU",
     "move wheelchair bed", "closer", None, "Access/devices. Default: request."),
    ("can-you~you-past", ("You printed the boarding passes.", S), ("Can you print the boarding passes?", R), "YOU",
     "print passes", "boarding", None, "Travel admin. Default: request."),
    # ---- question vs request (10) ----
    ("did-you~imperative", ("Did you put the bins out for collection?", Q), ("Put the bins out for collection.", R), "YOU",
     "put bins", "collection", None, "Chores. Default: request."),
    ("imperative~are-you-ing", ("Ring the council about the parking permit.", R), ("Are you ringing the council about the parking permit?", Q), "YOU",
     "ring council permit", "parking", None, "Admin/access. Default: request."),
    ("have-you~imperative", ("Have you emailed my manager about the rota?", Q), ("Email my manager about the rota.", R), "YOU",
     "email manager", "rota", None, "Work. Default: request."),
    ("imperative~did-you", ("Renew the car tax.", R), ("Did you renew the car tax?", Q), "YOU",
     "renew tax", "car", None, "Admin/money. Default: request."),
    ("are-you-ing~imperative", ("Are you bringing the folding chairs?", Q), ("Bring the folding chairs.", R), "YOU",
     "bring chairs", "folding", None, "Event planning. Default: request."),
    ("can-you~did-you", ("Can you record the football match?", R), ("Did you record the football match?", Q), "YOU",
     "record match", "football", None, "Leisure/TV. Default: request."),
    ("have-you~imperative", ("Have you cleared the snow from the path?", Q), ("Clear the snow from the path.", R), "YOU",
     "clear snow", "path", None, "Home/access. Default: request."),
    ("imperative~did-you", ("Lower the bed rail.", R), ("Did you lower the bed rail?", Q), "YOU",
     "lower rail", "bed", None, "Care/safety. Default: request."),
    ("are-you-ing~imperative", ("Are you sending the photos to grandma?", Q), ("Send the photos to grandma.", R), "YOU",
     "send photos", "grandma", None, "Family. Default: request."),
    ("imperative~did-you", ("Top up my bus pass.", R), ("Did you top up my bus pass?", Q), "YOU",
     "top up pass", "bus", None, "Transport/money. Default: request."),
]

ADVERSARIAL = [
    # "Can I ...?" = question, not request; partner = speaker plan statement (act-04/07/13 pattern).
    ("adv:can-I~I'm-ing", ("Can I park in the staff car park?", Q), ("I'm parking in the staff car park.", S), "I",
     "park car", "staff", None, "Adversarial (D-007): 'Can I ...?' is a permission question, and a judge may call it a request. Default: question."),
    ("adv:can-I~I'm-ing", ("I'm eating before the blood test.", S), ("Can I eat before the blood test?", Q), "I",
     "eat test", "blood", None, "Adversarial (D-007) health item: a permission question turned into a statement asserts a medical decision. Default: question."),
    ("adv:can-I~I'm-ing", ("Can I bring a friend to the scan?", Q), ("I'm bringing a friend to the scan.", S), "I",
     "bring friend", "scan", None, "Adversarial (D-007): support person at an appointment. Default: question."),
    ("adv:you-habitual~do-you", ("You take sugar in your tea.", S), ("Do you take sugar in your tea?", Q), "YOU",
     "take sugar", "tea", None, "Adversarial (CB-1): a you-subject present-habitual declarative is a statement. Default: question."),
    # you-subject declaratives under CB-1 vs imperatives
    ("adv:you-progressive(CB-1)~imperative", ("You're driving me to the train station.", S), ("Drive me to the train station.", R), "YOU",
     "drive station", "train", None, "Adversarial (CB-1): 'You're driving me...' is a statement although it can be heard as a directive. Default: request."),
    ("adv:you-will(CB-1)~imperative", ("Ring me from the hotel lobby.", R), ("You'll ring me from the hotel lobby.", S), "YOU",
     "ring hotel", "lobby", None, "Adversarial (CB-1): 'You'll ...' is coded statement; this is the directive-reading risk flagged in V-01/V-03, so it is used here on purpose. Default: request."),
    ("adv:you-need-to(CB-1)~imperative", ("You need to sign the lease renewal.", S), ("Sign the lease renewal.", R), "YOU",
     "sign lease", "renewal", None, "Adversarial (CB-1 codebook example 'You need to ...' = statement). [MUST] deliberately omitted from all_chips: 'need to' is the speech-act cue itself here, as 'always' is in act-09."),
    # indirect requests (keyed request/command; agent = doer of X, CB-7)
    ("adv:I-need-you-to~did-you", ("I need you to collect my glasses from the optician.", R), ("Did you collect my glasses from the optician?", Q), "YOU",
     "collect glasses", "optician", None, "Adversarial: indirect request keyed request/command; agent addressee (CB-7). CODEBOOK RISK: the codebook lists 'I need X' as statement, so a literal annotator may code A statement."),
    ("adv:I-need-you-to~you-past", ("You moved your car from the drive.", S), ("I need you to move your car from the drive.", R), "YOU",
     "move car", "drive", None, "Adversarial: indirect request (keyed request/command, agent addressee per CB-7) vs past you-statement. CODEBOOK RISK as in the 'collect glasses' family."),
    # interrogative request vs interrogative question
    ("adv:will-you~did-you", ("Will you pick a film for tonight?", R), ("Did you pick a film for tonight?", Q), "YOU",
     "pick film", "tonight", None, "Adversarial: both variants are interrogatives; 'Will you ...?' is a request (codebook), 'Did you ...?' a question. Default: question or suggestion ('Let's pick a film')."),
]


# Families excluded from the W-C primary contrast P1 (reported descriptively only).
PRIMARY_EXCLUDE = {"I need you to collect my glasses from the optician.": "D-018",
                   "I need you to move your car from the drive.": "D-018"}


def cluster_of(typ: str, cons: str) -> str:
    """Verifier V2-03: drafted -> order-free template (A~B == B~A); adversarial -> the boundary construction
    (left of '~'), so e.g. both 'I need you to ...' families share one cluster."""
    if typ == "adversarial":
        return "r2c-adv-" + cons.split("~")[0].removeprefix("adv:")
    return "r2c-dra-" + "~".join(sorted(cons.split("~")))


def variant(src: str, val: str, actor: str | None) -> dict:
    allc = [CHIP[val]] + ([ACTOR[actor]] if actor else []) + (["[PLAIN]"] if val == R else [])
    return {"source": src, "critical_value": val, "chips": [CHIP[val]], "all_chips": P.sort_chips(allc)}


def check_seed(lines: list[str], sample: set[str], row: dict) -> str:
    text = lines[row["line"] - 1]
    if text.strip().lower() in sample:
        raise SystemExit(f"seed line {row['line']} is in aactext_sample400 (W-B overlap)")
    return text


def main() -> None:
    lines = (ROOT / "data/raw/aactext/sent_train_aac.txt").read_text(encoding="utf-8").split("\n")
    sample = {json.loads(l)["text"].strip().lower()
              for l in (ROOT / "data/specs/aactext_sample400.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = []
    for r in SEEDED:
        rows.append(dict(source_type="aactext_seeded", construction=r["construction"], pair=[r["seed"], r["partner"]],
                         seed_idx=0, actor=r["actor"], bare=r["bare"], nc=r["nc"], ctx=None, note=r["note"],
                         seed_line=r["line"], seed_text=check_seed(lines, sample, r), seed_edit=r["edit"],
                         cluster_id=f"r2c-seed-{r['line']:05d}"))   # same scheme as build_r2_c1 (shared seed lines, V2-03)
    for typ, block in (("drafted", DRAFTED), ("adversarial", ADVERSARIAL)):
        for cons, a, b, actor, bare, nc, ctx, note in block:
            rows.append(dict(source_type=typ, construction=cons, pair=[a, b], seed_idx=None, actor=actor, bare=bare,
                             nc=nc, ctx=ctx, note=note, seed_line=None, seed_text=None, seed_edit=None,
                             cluster_id=cluster_of(typ, cons)))
    assert len(rows) == 80, len(rows)
    out = []
    for i, r in enumerate(rows, 1):
        pair, seed_idx = r["pair"], r["seed_idx"]
        if r["source_type"] == "aactext_seeded" and i % 2 == 0:   # alternate A/B order for seeded rows
            pair, seed_idx = pair[::-1], 1
        (sa, va), (sb, vb) = pair
        contrast = CONTRAST[frozenset({va, vb})]
        fam = {"family_id": f"r2act-{i:03d}", "dimension": "speech_act", "split": "r2", "context": r["ctx"],
               "variants": {"A": variant(sa, va, r["actor"]), "B": variant(sb, vb, r["actor"])},
               "bare": r["bare"], "noncritical": r["nc"], "critical_options": OPTS,
               "notes": f"W-C speech act, {contrast}, {r['source_type'].replace('aactext_', '')}. {r['note']}",
               "stratum": "speech_act", "contrast": contrast,
               "construction": {"aactext_seeded": "seeded"}.get(r["source_type"], r["source_type"]),
               "template": r["construction"], "cluster_id": r["cluster_id"]}
        excl = {PRIMARY_EXCLUDE[s] for s in (sa, sb) if s in PRIMARY_EXCLUDE}
        if excl:
            fam["primary_exclude"] = sorted(excl)[0]
        if r["seed_line"]:   # shared r2 schema: seed fields only on seeded families
            fam.update({"seed_line": r["seed_line"], "seed_text": r["seed_text"],
                        "seed_variant": "AB"[seed_idx], "seed_edit": r["seed_edit"],
                        "seed_file": "data/raw/aactext/sent_train_aac.txt"})
        out.append(fam)
    p = ROOT / "data/items/r2_c2.jsonl"
    p.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in out), encoding="utf-8")
    print(f"{p}: {len(out)} families")


if __name__ == "__main__":
    main()
