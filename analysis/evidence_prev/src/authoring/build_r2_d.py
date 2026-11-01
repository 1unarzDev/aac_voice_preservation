"""Builder for data/items/r2_d.jsonl: W-D encoding-controlled composition (PREREG_R2), 80 scenarios r2d-001..080.

All scenarios were hand-written by the item author (Claude); no LLM API was used. Edit here, not the JSONL.
    python3 src/authoring/build_r2_d.py && python3 src/validate_items.py data/items/r2_d.jsonl

Representation is exactly that of data/items/expC.jsonl (src/make_followup_items.py, D-012): each scenario
is a {YES,NOT} x {I,YOU} factorial of plain statements, split into 4 standard A/B records
(polarity at I, polarity at YOU, agent at YES, agent at NOT) with custom channels neither / pol / actor / both.
New in W-D: every channel exists in two encodings of the constant speech-act chip,
  <channel>_TELL       constant [TELL]       (as in Exp C)
  <channel>_STATEMENT  constant [STATEMENT]  (P0x alias of [TELL], already defined in prompts/chip_legend_x.txt)
and all channels run under prompts=['P0x'] only, so both encodings see the same legend. Each encoding has
9 unique inputs per scenario (1 neither + 2 pol + 2 actor + 4 both).
Sources: single predicate, no embedded/nested predicate (no want/need/forget/try to ...), adult everyday
content, past simple ("I locked ..." / "I didn't lock ...") or present perfect ("I've ..." / "I haven't ...")
so the you-subject cells read as reports, not directives (V-01/V-03; avoids "You'll ..."). Objects use
"the" (never my/your) so cells differ only in polarity and actor. Verbs/objects are disjoint from Exp C.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import prompts as P  # noqa: E402

# (bare, noncritical, base verb, past or participle form, object phrase)
PAST = [  # "I {past} {obj}." / "I didn't {base} {obj}."
    ("lock door", "front", "lock", "locked", "the front door"),
    ("book taxi", "airport", "book", "booked", "the airport taxi"),
    ("post letter", "council", "post", "posted", "the letter to the council"),
    ("empty bin", "kitchen", "empty", "emptied", "the kitchen bin"),
    ("return parcel", "damaged", "return", "returned", "the damaged parcel"),
    ("renew prescription", "repeat", "renew", "renewed", "the repeat prescription"),
    ("reply email", "landlord", "reply", "replied", "to the email from the landlord"),
    ("fix shelf", "wobbly", "fix", "fixed", "the wobbly shelf"),
    ("scrub tray", "oven", "scrub", "scrubbed", "the oven tray"),
    ("iron shirt", "white", "iron", "ironed", "the white shirt"),
    ("recycle bottles", "glass", "recycle", "recycled", "the glass bottles"),
    ("sell bike", "old", "sell", "sold", "the old bike"),
    ("buy milk", "oat", "buy", "bought", "the oat milk"),
    ("send invoice", "final", "send", "sent", "the final invoice"),
    ("mow grass", "long", "mow", "mowed", "the long grass"),
    ("defrost freezer", "garage", "defrost", "defrosted", "the garage freezer"),
    ("unplug heater", "fan", "unplug", "unplugged", "the fan heater"),
    ("fold laundry", "clean", "fold", "folded", "the clean laundry"),
    ("vacuum carpet", "hallway", "vacuum", "vacuumed", "the hallway carpet"),
    ("print tickets", "train", "print", "printed", "the train tickets"),
    ("sign form", "consent", "sign", "signed", "the consent form"),
    ("move bins", "wheelie", "move", "moved", "the wheelie bins"),
    ("clear gutters", "blocked", "clear", "cleared", "the blocked gutters"),
    ("cook rice", "brown", "cook", "cooked", "the brown rice"),
    ("thaw chicken", "frozen", "thaw", "thawed", "the frozen chicken"),
    ("test alarm", "smoke", "test", "tested", "the smoke alarm"),
    ("restart router", "wifi", "restart", "restarted", "the wifi router"),   # V2-D1: was reset/reset (past = base form; "You reset ..." reads as present/directive)
    ("tidy shed", "garden", "tidy", "tidied", "the garden shed"),
    ("paint fence", "wooden", "paint", "painted", "the wooden fence"),
    ("wrap present", "birthday", "wrap", "wrapped", "the birthday present"),
    ("measure window", "bedroom", "measure", "measured", "the bedroom window"),
    ("update calendar", "shared", "update", "updated", "the shared calendar"),
    ("scan receipts", "expense", "scan", "scanned", "the expense receipts"),
    ("polish shoes", "work", "polish", "polished", "the work shoes"),
    ("replace bulb", "porch", "replace", "replaced", "the porch bulb"),
    ("collect cleaning", "dry", "collect", "collected", "the dry cleaning"),
    ("inflate tyres", "bike", "inflate", "inflated", "the bike tyres"),
    ("email surgery", "GP", "email", "emailed", "the GP surgery"),
    ("visit neighbour", "elderly", "visit", "visited", "the elderly neighbour"),
    ("unpack boxes", "moving", "unpack", "unpacked", "the moving boxes"),
    ("load van", "removal", "load", "loaded", "the removal van"),
    ("transfer deposit", "rent", "transfer", "transferred", "the rent deposit"),
    ("postpone meeting", "team", "postpone", "postponed", "the team meeting"),
    ("register car", "electric", "register", "registered", "the electric car"),
    ("repair tap", "leaking", "repair", "repaired", "the leaking tap"),
    ("water baskets", "hanging", "water", "watered", "the hanging baskets"),
    ("phone engineer", "gas", "phone", "phoned", "the gas engineer"),
    ("clean tank", "fish", "clean", "cleaned", "the fish tank"),
    ("label jars", "spice", "label", "labelled", "the spice jars"),
    ("close account", "savings", "close", "closed", "the savings account"),
]
PERFECT = [  # "I've {pp} {obj}." / "I haven't {pp} {obj}."
    ("book cottage", "holiday", "book", "booked", "the holiday cottage"),
    ("read contract", "rental", "read", "read", "the rental contract"),
    ("take tablets", "iron", "take", "taken", "the iron tablets"),
    ("write card", "sympathy", "write", "written", "the sympathy card"),
    ("eat curry", "leftover", "eat", "eaten", "the leftover curry"),
    ("find charger", "laptop", "find", "found", "the laptop charger"),
    ("make soup", "lentil", "make", "made", "the lentil soup"),
    ("pay fine", "parking", "pay", "paid", "the parking fine"),
    ("send application", "job", "send", "sent", "the job application"),
    ("meet manager", "new", "meet", "met", "the new manager"),
    ("fill jug", "water", "fill", "filled", "the water jug"),
    ("watch show", "cooking", "watch", "watched", "the cooking show"),
    ("clean mirror", "bathroom", "clean", "cleaned", "the bathroom mirror"),
    ("change sheets", "bed", "change", "changed", "the bed sheets"),
    ("back up photos", "family", "back", "backed", "up the family photos"),
    ("borrow ladder", "step", "borrow", "borrowed", "the step ladder"),
    ("pack bag", "hospital", "pack", "packed", "the hospital bag"),
    ("file tax return", "annual", "file", "filed", "the annual tax return"),
    ("bake bread", "banana", "bake", "baked", "the banana bread"),
    ("plant seeds", "tomato", "plant", "planted", "the tomato seeds"),
    ("copy keys", "house", "copy", "copied", "the house keys"),
    ("download statement", "bank", "download", "downloaded", "the bank statement"),
    ("install curtain", "shower", "install", "installed", "the shower curtain"),
    ("do shopping", "food", "do", "done", "the food shopping"),
    ("brush dog", "muddy", "brush", "brushed", "the muddy dog"),
    ("sharpen knife", "carving", "sharpen", "sharpened", "the carving knife"),
    ("store clothes", "winter", "store", "stored", "the winter clothes"),
    ("confirm table", "restaurant", "confirm", "confirmed", "the restaurant table"),
    ("report streetlight", "broken", "report", "reported", "the broken streetlight"),
    ("shred mail", "junk", "shred", "shredded", "the junk mail"),
]
SUBJ = {"I": "I", "YOU": "You"}
PERF_AUX = {("YES", "I"): "I've", ("YES", "YOU"): "You've", ("NOT", "I"): "I haven't", ("NOT", "YOU"): "You haven't"}
POL = {"YES": ("[YES]", "affirmative"), "NOT": ("[NOT]", "negated")}
ACT = {"I": ("[I]", "speaker"), "YOU": ("[YOU]", "addressee")}
POL_OPTS = ["negated", "affirmative", "unclear/mixed"]
AGT_OPTS = ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"]
ENCODINGS = {"TELL": "[TELL]", "STATEMENT": "[STATEMENT]"}   # [STATEMENT] = P0x alias of [TELL]


def sources(tense: str, base: str, form: str, obj: str) -> dict:
    out = {}
    for p in ("YES", "NOT"):
        for a in ("I", "YOU"):
            if tense == "past":
                out[(p, a)] = f"{SUBJ[a]} {form} {obj}." if p == "YES" else f"{SUBJ[a]} didn't {base} {obj}."
            else:
                out[(p, a)] = f"{PERF_AUX[(p, a)]} {form} {obj}."
    return out


def kw(chips: list[str], bare: str, enc: str) -> str:
    toks = [ENCODINGS[enc] if c == "[TELL]" else c for c in P.sort_chips(chips)]
    return "Keywords: " + " ".join(toks + [bare])


def channels(pc: str, av: str, bare: str) -> dict:
    out = {}
    for enc in ENCODINGS:
        for name, chips in (("neither", ["[TELL]"]), ("pol", [pc, "[TELL]"]), ("actor", ["[TELL]", av]),
                            ("both", [pc, "[TELL]", av])):
            out[f"{name}_{enc}"] = {"input": kw(chips, bare, enc), "commitments": P.sort_chips(chips),
                                    "prompts": ["P0x"]}
    return out


def build() -> list[dict]:
    rows = [("past", *r) for r in PAST] + [("perfect", *r) for r in PERFECT]
    assert len(rows) == 80, len(rows)
    out = []
    for n, (tense, bare, nc, base, form, obj) in enumerate(rows, 1):
        fam = f"r2d-{n:03d}"
        src = sources(tense, base, form, obj)

        def variant(p: str, a: str, crit_dim: str) -> tuple[dict, dict]:
            pc, av = POL[p][0], ACT[a][0]
            v = {"source": src[(p, a)],
                 "critical_value": POL[p][1] if crit_dim == "polarity" else ACT[a][1],
                 "chips": [pc] if crit_dim == "polarity" else [av],
                 "all_chips": P.sort_chips([pc, "[TELL]", av]), "cell": f"{p}|{a}"}
            return v, channels(pc, av, bare)

        for crit_dim, fixed_name, fixed_vals, pairs in [
                ("polarity", "agent", ["I", "YOU"], lambda f: [("YES", f), ("NOT", f)]),
                ("agent", "polarity", ["YES", "NOT"], lambda f: [(f, "I"), (f, "YOU")])]:
            for fv in fixed_vals:
                (pa, aa), (pb, ab) = pairs(fv)
                if n % 2 == 0:   # alternate which value is variant A across scenarios
                    (pa, aa), (pb, ab) = (pb, ab), (pa, aa)
                vA, cA = variant(pa, aa, crit_dim)
                vB, cB = variant(pb, ab, crit_dim)
                short = "pol" if crit_dim == "polarity" else "agt"
                out.append({
                    "family_id": f"{fam}-{short}-{fv.lower()}", "dimension": crit_dim, "split": "r2d",
                    "context": None, "variants": {"A": vA, "B": vB}, "bare": bare, "noncritical": nc,
                    "critical_options": POL_OPTS if crit_dim == "polarity" else AGT_OPTS,
                    "notes": (f"W-D factorial scenario {fam} ({bare}, {tense}); {crit_dim} pair with "
                              f"{fixed_name} held at {fv}. Plain single-predicate statements; constant "
                              "[TELL] vs [STATEMENT] encodings under P0x."),
                    "factorial_family": fam, "held_fixed": {fixed_name: fv}, "tense": tense,
                    "encodings": list(ENCODINGS),
                    "custom_channels": {"A": cA, "B": cB}})
    return out


def main() -> None:
    fams = build()
    p = ROOT / "data/items/r2_d.jsonl"
    p.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in fams), encoding="utf-8")
    print(f"{p}: {len(fams)} records ({len(fams) // 4} scenarios)")


if __name__ == "__main__":
    main()
