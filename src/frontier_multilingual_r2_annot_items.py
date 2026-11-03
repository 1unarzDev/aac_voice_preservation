"""Build round-2 human-annotation items (NOT sent). Items: the E7 fresh validation sample (register outputs), 20 polarity outputs per language, and the control keyword strings."""
import json, csv, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
items, key = [], []
rnd = random.Random("ml2order")
def add(t, lang, payload, keyrow):
    i = f"ml2-{len(items):04d}"
    items.append({"id": i, "lang": lang, "type": t, **payload}); key.append({"id": i, "lang": lang, "type": t, **keyrow})
for lang in LANGS:
    for r in jl(OUT / f"r2_validation_items_{lang}.jsonl")[:60]:
        add("R", lang, {"text": r["text"], "questions": ["Q5 address form: informal (du/tu/tú) / formal (Sie/vous/usted) / none / mixed", "Q6 natural? 1-5"]}, {"detector": r["det"], "arb_sol": r["arb1"], "arb_terra": r["arb2"]})
    kc = json.load(open(OUT / "r2_keyword_conditions.json"))
    pol = [json.loads(l) for l in open(OUT / "translations.jsonl")]
    rs = [r for r in pol if r["lang"] == lang and r["kind"] == "REG" and r["accepted"]]
    for r in rs[:20]:
        fid = r["family_id"]
        for cond, d in (("nom", kc["nominal"]), ("kw2", kc["kw2"]), ("sep", kc["sep_de"])):
            k = d.get(f"{lang}|{fid}")
            if k:
                add("K", lang, {"english": r["bare"], "keywords": k, "questions": ["Q7 same message core as the English? yes/partly/no", "Q2 contains a negation or formal/informal marker? yes/no"]}, {"condition": cond, "family": fid})
    pr = [x for x in json.load(open(OUT / "r2_pol_labels.json")).items() if x[0].startswith(lang + "|")]
    pr = sorted(pr, key=lambda x: h("ml2pol", x[0]))[:20]
    for k, v in pr:
        add("P", lang, {"text": k.split("|", 1)[1], "questions": ["Q4 polarity: affirmative / negated / unclear"]}, {"direct": v["direct"], "route": v["route"]})
order = list(range(len(items))); rnd.shuffle(order)
items = [items[i] for i in order]
json.dump(items, open(ROOT / "annotation/frontier_multilingual_r2_items.json", "w"), ensure_ascii=False, indent=1)
with open(ROOT / "annotation/frontier_multilingual_r2_key.csv", "w", newline="") as f:
    cols = sorted({c for r in key for c in r}); w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(key)
import collections
print(len(items), collections.Counter((i["lang"], i["type"]) for i in items))
