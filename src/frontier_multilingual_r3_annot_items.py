"""Build round-3 human-annotation items (NOT sent): (S) all ES detector-'none' outputs from the E7 sample plus 25 detector-T/V controls; (X) native-speaker translation check of ALL
frozen pilot translations (POL pairs A/B/keywords, REG keyword strings) in DE/ES/FR; (Q) the generated question-context strings. Key never shown to annotators."""
import json, csv, random, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
items, key = [], []
rnd = random.Random("ml3order")
def add(t, lang, payload, keyrow):
    i = f"ml3-{len(items):04d}"
    items.append({"id": i, "lang": lang, "type": t, **payload}); key.append({"id": i, "lang": lang, "type": t, **keyrow})
es = jl(OUT / "r2_validation_items_es.jsonl")
none = [r for r in es if r["det"] == "none"]; tv = sorted([r for r in es if r["det"] in ("T", "V")], key=lambda r: h("ml3ctl", r["text"]))[:25]
for r in none + tv:
    add("S", "es", {"text": r["text"], "questions": ["Q5 address form: informal (tú) / formal (usted) / none / mixed"]}, {"detector": r["det"], "arb_sol": r["arb1"], "arb_terra": r["arb2"]})
for r in jl(OUT / "translations.jsonl"):
    if not r.get("t"):
        continue
    if r["kind"] == "POL":
        add("X", r["lang"], {"english": {"A": r["A"], "B": r["B"], "keywords": r["bare"]}, "translated": r["t"], "questions": [
            "Q1 Do A and B differ ONLY in affirmative vs negated? yes/no", "Q2 Does the keyword string contain a negation or formal/informal marker? yes/no", "Q3 Does the keyword string stand for the same message core as the English? yes/partly/no", "Q8 Is each sentence correct, natural? yes/no"]},
            {"family": r["family_id"], "kind": "POL", "accepted_machine": r["accepted"]})
    else:
        add("X", r["lang"], {"english": {"keywords": r["bare"]}, "translated": {"keywords": r["t"]["keywords"]}, "questions": [
            "Q2 Does the keyword string contain a negation or formal/informal marker? yes/no", "Q3 Does the keyword string stand for the same message core as the English? yes/partly/no"]},
            {"family": r["family_id"], "kind": "REG", "accepted_machine": r["accepted"]})
for k, v in json.load(open(OUT / "r3_questions.json")).items():
    if v["question"] and not k.startswith("en|"):
        add("Q", k.split("|")[0], {"text": v["question"], "keywords": v["kw"], "questions": ["Q9 Natural yes/no question in this language? yes/no", "Q10 Does it contain a negation? yes/no"]}, {"family": k.split("|")[1]})
order = list(range(len(items))); rnd.shuffle(order); items = [items[i] for i in order]
json.dump(items, open(ROOT / "annotation/frontier_multilingual_r3_items.json", "w"), ensure_ascii=False, indent=1)
with open(ROOT / "annotation/frontier_multilingual_r3_key.csv", "w", newline="") as f:
    cols = sorted({c for r in key for c in r}); w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(key)
print(len(items), collections.Counter((i["lang"], i["type"]) for i in items))
