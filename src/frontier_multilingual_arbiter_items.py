"""Build blind arbiter item lists (output text only, shuffled by hash). Register: all detector-ambiguous texts + 40 random non-ambiguous per language (validation)."""
import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
from frontier_multilingual_register import label as det

models = [m for m in ("gemma3-4b", "mistral-nemo-12b", "gpt-6.1-terra") if (RUN / f"gen_{m}.jsonl").exists()]
texts = {}
for m in models:
    for r in jl(RUN / f"gen_{m}.jsonl"):
        if r["kind"] == "REG" and r["text"]:
            texts[(r["lang"], r["text"])] = det(r["lang"], r["text"])
items = []
for lang in LANGS:
    amb = sorted(t for (l, t), d in texts.items() if l == lang and d == "ambig")
    ok = sorted(t for (l, t), d in texts.items() if l == lang and d != "ambig")
    rnd = random.Random("ml1val|" + lang)
    val = rnd.sample(ok, min(40, len(ok)))
    items += [{"lang": lang, "text": t, "kind": "ambiguous"} for t in amb] + [{"lang": lang, "text": t, "kind": "validation"} for t in val]
items.sort(key=lambda x: h("arb", x["lang"], x["text"]))
for i, it in enumerate(items):
    it["n"] = i + 1
json.dump(items, open(OUT / "arbiter_register_items.json", "w"), ensure_ascii=False, indent=0)
import collections
print(collections.Counter((i["lang"], i["kind"]) for i in items))
# polarity arbiter items
pol = []
for m in models:
    p = OUT / f"pol_labels_{m}.jsonl"
    if p.exists():
        pol += jl(p)
need = {}
for r in pol:
    d, ro = r.get("direct"), r.get("route")
    if not (d and ro and d == ro):
        need[(r["lang"], r["text"])] = 1
pi = [{"lang": l, "text": t} for (l, t) in need]
pi.sort(key=lambda x: h("arbp", x["lang"], x["text"]))
for i, it in enumerate(pi):
    it["n"] = i + 1
json.dump(pi, open(OUT / "arbiter_polarity_items.json", "w"), ensure_ascii=False, indent=0)
print("pol arbiter items", len(pi))
