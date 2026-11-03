"""Build (not send) annotation items + key for the multilingual pilot."""
import sys, json, csv, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
tr = [r for r in jl(OUT / "translations.jsonl") if r["accepted"]]
items, key = [], []
for lang in LANGS:
    ts = sorted([r for r in tr if r["lang"] == lang], key=lambda r: h("ml1chk", lang, r["family_id"]))[:40]
    for r in ts:
        iid = "T-" + h("T", lang, r["family_id"])[:8]
        if r["kind"] == "POL":
            items.append({"id": iid, "lang": lang, "type": "T", "A": r["t"]["A"], "B": r["t"]["B"], "keywords": r["t"]["keywords"], "english_keywords": r["bare"],
                          "questions": ["Q1 differ only affirmative vs negated (yes/no)", "Q2 keywords contain negation or formal/informal marker (yes/no)", "Q3 keywords stand for same core as English (yes/partly/no)"]})
        else:
            items.append({"id": iid, "lang": lang, "type": "T", "A": r["t"]["A"], "keywords": r["t"]["keywords"], "english_keywords": r["bare"],
                          "questions": ["Q2 keywords contain negation or formal/informal marker (yes/no)", "Q3 keywords stand for same core as English (yes/partly/no)"]})
        key.append({"id": iid, "lang": lang, "type": "T", "family_id": r["family_id"], "kind": r["kind"]})
    pol = [r for m in ("gemma3-4b", "mistral-nemo-12b", "gpt-6.1-terra") for r in jl(OUT / f"pol_final.jsonl") if r["lang"] == lang and r["pset"] == "L"]
    reg = [r for r in jl(OUT / "register_labels.jsonl") if r["lang"] == lang and r["pset"] == "L"]
    seen = set(); sel = []
    for r in sorted(pol, key=lambda r: h("ml1chkP", r["id"], r["model"])):
        if r["text"] not in seen and len([x for x in sel if x["kind"] == "POL"]) < 30:
            seen.add(r["text"]); sel.append(r)
    for r in sorted(reg, key=lambda r: h("ml1chkR", r["id"], r["model"])):
        if r["text"] not in seen and len([x for x in sel if x["kind"] == "REG"]) < 30:
            seen.add(r["text"]); sel.append(r)
    for r in sel:
        iid = "L-" + h("L", lang, r["id"], r["model"])[:8]
        qs = ["Q4 main message affirmative / negated / unclear"] if r["kind"] == "POL" else ["Q5 address form informal / formal / none / mixed"]
        items.append({"id": iid, "lang": lang, "type": "L", "text": r["text"], "questions": qs + ["Q6 natural in this language 1-5"]})
        key.append({"id": iid, "lang": lang, "type": "L", "kind": r["kind"], "model": r["model"], "arm": r["arm"], "machine_label": r["label"]})
random.Random("ml1order").shuffle(items)
json.dump(items, open(ROOT / "annotation/frontier_multilingual_items.json", "w"), ensure_ascii=False, indent=1)
cols = sorted({c for k in key for c in k})
with open(ROOT / "annotation/frontier_multilingual_key.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(key)
print(len(items), len(key))
