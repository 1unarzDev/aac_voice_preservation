"""Build follow-up item files (D-012): data/items/expB.jsonl and data/items/expC.jsonl.

Exp B (cue interaction + encoding): pol2-07..10 and act-07..10 copied from test.jsonl
(sources/specs unchanged, ids prefixed `xb-`), with `custom_channels` per variant:
  interaction (critical chip c fixed; X = second-dimension chip, Y = actor chip)
    i_crit  c                 i_x  c+X           i_y  c+Y           i_xy  c+X+Y
    i_pad   c + [·] [·] in the X/Y slots (P0x only: [·] is defined only in that legend)
      politeness families: X=[ASK], Y=[YOU]  (both in the frozen all_chips)
      speech-act families: X=[PLAIN] (true of every act source: no politeness marker),
                           Y=the actor chip of all_chips ([I]/[YOU]/[THEY])
  encoding of the full spec (all_chips):
    e_chips  original chips   e_alias  transparent aliases (P0x only)   e_nl  "Meaning:" line
Exp C (factorial noninterference): 8 hand-written families x {YES,NOT} x {I,YOU}, all plain
statements; each family is split into 4 standard A/B records (polarity at I, polarity at YOU,
agent at YES, agent at NOT) so attribute.py scores them unchanged. Channels: neither / pol /
actor / both, with [TELL] held constant in all four.

  python src/make_followup_items.py && python src/validate_items.py data/items/expB.jsonl data/items/expC.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompts as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXP_B_IDS = [f"pol2-{i:02d}" for i in range(7, 11)] + [f"act-{i:02d}" for i in range(7, 11)]
ACTOR = ("[I]", "[YOU]", "[WE]", "[THEY]")


def kw(chips: list[str], bare: str) -> str:
    return "Keywords: " + " ".join(chips + [bare])


def ch(text: str, commitments: list[str], prompts: list[str] | None = None) -> dict:
    d = {"input": text, "commitments": P.sort_chips(commitments)}
    if prompts:
        d["prompts"] = prompts
    return d


def exp_b() -> list[dict]:
    test = {json.loads(l)["family_id"]: json.loads(l)
            for l in (ROOT / "data/items/test.jsonl").read_text().splitlines() if l.strip()}
    out = []
    for fid in EXP_B_IDS:
        f = json.loads(json.dumps(test[fid]))
        f["source_family_id"] = fid
        f["family_id"] = f"xb-{fid}"
        f["split"] = "expB"
        f["notes"] = f"Exp B copy of frozen {fid} (sources and specs unchanged). " + f["notes"]
        bare, cc = f["bare"], {}
        for vn, v in f["variants"].items():
            (c,) = v["chips"]
            if f["dimension"] == "politeness":
                x, y = "[ASK]", "[YOU]"
            else:
                x = "[PLAIN]"
                (y,) = [a for a in v["all_chips"] if a in ACTOR]
            both = P.sort_chips([c, x, y])
            pad = [P.PAD if t in (x, y) else t for t in both]
            allc = P.sort_chips(v["all_chips"])
            cc[vn] = {
                "i_crit": ch(kw([c], bare), [c]),
                "i_x": ch(kw(P.sort_chips([c, x]), bare), [c, x]),
                "i_y": ch(kw(P.sort_chips([c, y]), bare), [c, y]),
                "i_xy": ch(kw(both, bare), both),
                "i_pad": ch(kw(pad, bare), [c], ["P0x"]),
                "e_chips": ch(kw(allc, bare), allc),
                "e_alias": ch(kw([P.ALIAS[t] for t in allc], bare), allc, ["P0x"]),
                "e_nl": ch(f"Keywords: {bare}\n{P.nl_meaning(allc)}", allc),
            }
        f["custom_channels"] = cc
        f["design"] = {"exp": "B", "x_chip": "[ASK]" if f["dimension"] == "politeness" else "[PLAIN]",
                       "y_chip": "[YOU]" if f["dimension"] == "politeness" else "actor chip of all_chips"}
        out.append(f)
    return out


# Hand-written Exp C sources: (bare, noncritical, {(polarity, actor): source}).
C_FAMILIES = [
    ("call dentist", "back", {
        ("YES", "I"): "I'll call the dentist back.", ("YES", "YOU"): "You'll call the dentist back.",
        ("NOT", "I"): "I won't call the dentist back.", ("NOT", "YOU"): "You won't call the dentist back."}),
    ("open gate", "side", {
        ("YES", "I"): "I'll open the side gate.", ("YES", "YOU"): "You'll open the side gate.",
        ("NOT", "I"): "I won't open the side gate.", ("NOT", "YOU"): "You won't open the side gate."}),
    ("order lunch", "online", {
        ("YES", "I"): "I'll order lunch online.", ("YES", "YOU"): "You'll order lunch online.",
        ("NOT", "I"): "I won't order lunch online.", ("NOT", "YOU"): "You won't order lunch online."}),
    ("check appointment", "time", {
        ("YES", "I"): "I'll check the appointment time.", ("YES", "YOU"): "You'll check the appointment time.",
        ("NOT", "I"): "I won't check the appointment time.", ("NOT", "YOU"): "You won't check the appointment time."}),
    ("bring coat", "warm", {
        ("YES", "I"): "I'll bring a warm coat.", ("YES", "YOU"): "You'll bring a warm coat.",
        ("NOT", "I"): "I won't bring a warm coat.", ("NOT", "YOU"): "You won't bring a warm coat."}),
    ("charge phone", "spare", {
        ("YES", "I"): "I'll charge the spare phone.", ("YES", "YOU"): "You'll charge the spare phone.",
        ("NOT", "I"): "I won't charge the spare phone.", ("NOT", "YOU"): "You won't charge the spare phone."}),
    ("cancel booking", "hotel", {
        ("YES", "I"): "I'll cancel the hotel booking.", ("YES", "YOU"): "You'll cancel the hotel booking.",
        ("NOT", "I"): "I won't cancel the hotel booking.", ("NOT", "YOU"): "You won't cancel the hotel booking."}),
    ("wash dishes", "dirty", {
        ("YES", "I"): "I'll wash the dirty dishes.", ("YES", "YOU"): "You'll wash the dirty dishes.",
        ("NOT", "I"): "I won't wash the dirty dishes.", ("NOT", "YOU"): "You won't wash the dirty dishes."}),
]
POL = {"YES": ("[YES]", "affirmative"), "NOT": ("[NOT]", "negated")}
ACT = {"I": ("[I]", "speaker"), "YOU": ("[YOU]", "addressee")}
POL_OPTS = ["negated", "affirmative", "unclear/mixed"]
AGT_OPTS = ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"]


def exp_c() -> list[dict]:
    out = []
    for n, (bare, nc, src) in enumerate(C_FAMILIES, 1):
        fam = f"xc-{n:02d}"

        def variant(p: str, a: str, crit_dim: str) -> tuple[dict, dict]:
            pc, av = POL[p][0], ACT[a][0]
            v = {"source": src[(p, a)],
                 "critical_value": POL[p][1] if crit_dim == "polarity" else ACT[a][1],
                 "chips": [pc] if crit_dim == "polarity" else [av],
                 "all_chips": P.sort_chips([pc, "[TELL]", av]), "cell": f"{p}|{a}"}
            chans = {"neither": ch(kw(["[TELL]"], bare), ["[TELL]"]),
                     "pol": ch(kw(P.sort_chips([pc, "[TELL]"]), bare), [pc, "[TELL]"]),
                     "actor": ch(kw(P.sort_chips(["[TELL]", av]), bare), ["[TELL]", av]),
                     "both": ch(kw(P.sort_chips([pc, "[TELL]", av]), bare), [pc, "[TELL]", av])}
            return v, chans

        for crit_dim, fixed_name, fixed_vals, pairs in [
                ("polarity", "agent", ["I", "YOU"], lambda f: [("YES", f), ("NOT", f)]),
                ("agent", "polarity", ["YES", "NOT"], lambda f: [(f, "I"), (f, "YOU")])]:
            for fv in fixed_vals:
                (pa, aa), (pb, ab) = pairs(fv)
                vA, cA = variant(pa, aa, crit_dim)
                vB, cB = variant(pb, ab, crit_dim)
                short = "pol" if crit_dim == "polarity" else "agt"
                out.append({
                    "family_id": f"{fam}-{short}-{fv.lower()}", "dimension": crit_dim, "split": "expC",
                    "context": None, "variants": {"A": vA, "B": vB}, "bare": bare, "noncritical": nc,
                    "critical_options": POL_OPTS if crit_dim == "polarity" else AGT_OPTS,
                    "notes": (f"Exp C factorial family {fam} ({bare}); {crit_dim} pair with "
                              f"{fixed_name} held at {fv}. Plain statements, no nested predicate; "
                              "[TELL] constant in all channels."),
                    "factorial_family": fam, "held_fixed": {fixed_name: fv},
                    "custom_channels": {"A": cA, "B": cB}})
    return out


def main() -> None:
    for name, fams in [("expB", exp_b()), ("expC", exp_c())]:
        p = ROOT / "data/items" / f"{name}.jsonl"
        p.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in fams), encoding="utf-8")
        print(f"{p}: {len(fams)} records")


if __name__ == "__main__":
    main()
