"""W-B corpus items: one single-variant 'family' per sampled AACText message (corpus_item=true).

Channels (custom_channels, rendered by build_requests; P0 only):
  pos_cap4   "Keywords: <POS-cap4 words>"                          commitments []
  restored   focal-cue-restored: POS-cap4 + the source's focal cue, as a chip when the SPEC
             vocabulary can express it ([NOT] [MAYBE] [SURE] [?] [ASK] [REFUSE] [PLEASE]
             [I] [YOU] [WE] [THEY]); otherwise (softened request, thanks/apology, offer) the
             source cue word(s) inserted in source order.  Omitted when focal_dim == none.
  full       "The user typed: <source>"                            commitments = all_chips
Critical dimension = focal_dim (focal none -> polarity, flagged focal_none).
Critical value / general_spec = codex-panel pass-2 consensus (annotation/wb_admissibility/
panel.jsonl) when available and the two coders agree, else the s1 detector label
(value_source records which). Request keys depend only on the rendered input, so rebuilding
this file after the panel does not change generations.

  python src/wb_items.py          # -> data/items/wb.jsonl (split 'wb', opt-in)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompts as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data/specs/wb_sample.jsonl"
PANEL = ROOT / "annotation/wb_admissibility/panel.jsonl"
OUT = ROOT / "data/items/wb.jsonl"
DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness"]
CRIT_OPTIONS = {
    "polarity": ["negated", "affirmative", "unclear/mixed"],
    "agent": ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"],
    "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
    "politeness": ["polite", "plain", "unclear/mixed"],
    "speech_act": ["statement", "question", "request/command", "refusal", "acceptance",
                   "offer/suggestion", "unclear/mixed"],
}
VALUE_CHIP = {
    "polarity": {"negated": "[NOT]", "affirmative": "[YES]"},
    "speech_act": {"question": "[?]", "request/command": "[ASK]", "refusal": "[REFUSE]", "statement": "[TELL]"},
    "agent": {"speaker": "[I]", "addressee": "[YOU]", "we/joint": "[WE]", "third party": "[THEY]"},
    "certainty": {"hedged/uncertain": "[MAYBE]", "strongly certain/emphatic": "[SURE]", "plain assertion": "[SURE]"},
    "politeness": {"please": "[PLEASE]", "none": "[PLAIN]"},
}


def crit_value(dim: str, general_value: str) -> str:
    if dim == "politeness":
        return "plain" if general_value == "none" else "polite"
    if general_value in CRIT_OPTIONS[dim]:
        return general_value
    return "unclear/mixed"


def focal_cue(r: dict, dim: str) -> dict | None:
    cues = [c for c in r["detector_cues"] if c["dimension"] == dim]
    if not cues:
        return None
    kept = set(r["pos_cap4_token_ids"])
    lost = [c for c in cues if not set(c["carrier_ids"]) <= kept]
    return (lost or cues)[0]


def words_with_cue(r: dict, cue: dict, nlp) -> str:
    doc = nlp(r["text"])
    pos = list(zip(r["pos_cap4_token_ids"], r["pos_cap4"]))
    have = {i for i, _ in pos}
    pos += [(i, doc[i].text.lower().replace("’", "'")) for i in cue["carrier_ids"] if i not in have]
    return " ".join(w for _, w in sorted(pos))


def main() -> None:
    rows = [json.loads(l) for l in SAMPLE.open()]
    panel = {}
    if PANEL.exists():
        panel = {p["id"]: p for p in map(json.loads, PANEL.open())}
    nlp = None
    out = []
    for r in rows:
        pr = panel.get(r["id"])
        gen, srcs = {}, {}
        for d in DIMS:
            pv = pr["dims"][d]["source_value"] if pr else None
            gen[d] = pv if pv is not None else r["detector_labels"][d]
            srcs[d] = "panel" if pv is not None else "detector"
        focal = r["focal_dim"]
        dim = "polarity" if focal == "none" else focal
        cval = crit_value(dim, gen[dim])
        all_chips = [VALUE_CHIP[d][gen[d]] for d in DIMS if gen[d] in VALUE_CHIP[d]]
        all_chips = P.sort_chips(sorted(set(all_chips)))
        kw = " ".join(r["pos_cap4"])
        chans = {"pos_cap4": {"input": f"Keywords: {kw}", "commitments": []},
                 "full": {"input": f"The user typed: {r['text']}", "commitments": all_chips}}
        restore = None
        if focal != "none":
            cue = focal_cue(r, focal)
            chip = cue["chip"] if cue else None
            # restore the SOURCE value (panel consensus); detector cue gives the word/chip
            vchip = VALUE_CHIP[focal].get(gen[focal])
            if focal == "certainty" and gen[focal] == "plain assertion":
                vchip = None
            if chip and (vchip is None or chip == vchip):
                restore = {"mode": "chip", "cue": chip, "detector_value": cue["value"]}
                inp = f"Keywords: {chip} {kw}"
                commit = [chip]
            elif vchip and vchip not in ("[YES]", "[TELL]", "[PLAIN]"):
                restore = {"mode": "chip", "cue": vchip, "detector_value": cue["value"] if cue else None,
                           "note": "chip from panel source value (detector cue differs/absent)"}
                inp = f"Keywords: {vchip} {kw}"
                commit = [vchip]
            elif cue:
                if nlp is None:
                    import spacy
                    nlp = spacy.load("en_core_web_sm", disable=["ner"])
                words = words_with_cue(r, cue, nlp)
                restore = {"mode": "word", "cue": cue["evidence"], "detector_value": cue["value"]}
                inp = f"Keywords: {words}"
                commit = ["[PLEASE]"] if focal == "politeness" else []
            if restore:
                chans["restored"] = {"input": inp, "commitments": commit}
        chips = [VALUE_CHIP[dim].get(gen[dim])] if VALUE_CHIP[dim].get(gen[dim]) else []
        if dim == "politeness" and cval == "polite":
            chips = ["[PLEASE]"]
        if not chips:
            chips = ["[TELL]"] if dim == "speech_act" else ["[YES]"]
        spec = dict(gen)
        if spec["certainty"] == "n/a (question/request)":
            spec["certainty"] = "n/a (question/request)"
        out.append({
            "family_id": f"wb-{r['id']}", "dimension": dim, "split": "wb", "corpus_item": True,
            "context": None, "source_id": r["id"], "sample": r["sample"], "stratum": r["stratum"],
            "focal_dim": focal, "focal_none": focal == "none", "inclusion_prob": r["inclusion_prob"],
            "restoration": restore, "value_source": srcs,
            "variants": {"A": {"source": r["text"], "critical_value": cval, "chips": chips,
                               "all_chips": all_chips, "general_spec": spec}},
            "bare": kw, "noncritical": None, "critical_options": CRIT_OPTIONS[dim],
            "custom_channels": {"A": chans}})
    with OUT.open("w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    n_rest = sum("restored" in o["custom_channels"]["A"] for o in out)
    modes = {}
    for o in out:
        m = (o["restoration"] or {}).get("mode", "none")
        modes[m] = modes.get(m, 0) + 1
    print(f"wrote {OUT}: {len(out)} items, restored channel on {n_rest}; modes {modes}; panel used: {bool(panel)}")


if __name__ == "__main__":
    main()
