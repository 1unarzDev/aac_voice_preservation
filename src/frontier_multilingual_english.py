"""English P0 bare baseline on the SAME POL families (stored outputs + stored J1/J2 labels; agreeing labels only, else arbiter file if present)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
tr = jl(OUT / "translations.jsonl")
fams = {r["family_id"]: r["bare"] for r in tr if r["kind"] == "POL"}
gens = {}
for run in ("hw1", "ext_hw_nemo"):
    for g in jl(ROOT / f"runs/{run}/generations.jsonl"):
        if g["prompt_id"] == "P0" and g["family_id"] in fams and g["input_text"] == "Keywords: " + fams[g["family_id"]]:
            gens[(g["model"], g["family_id"])] = g
out = []
for run in ("hw1", "ext_hw_nemo"):
    for j in jl(ROOT / f"runs/{run}/judgments.jsonl"):
        if j["family_id"] in fams and j["input_text"] == "Keywords: " + fams[j["family_id"]] and j["dimension"] == "polarity":
            out.append({"run": run, "family_id": j["family_id"], "text": j["text"], "J1": j["J1_critical"], "J2": j["J2_critical"], "polarity_J1": j.get("J1_polarity"), "polarity_J2": j.get("J2_polarity")})
# attach model via generation text match
byt = {}
for (m, f), g in gens.items():
    byt.setdefault((f, (g.get("suggestions") or [g["raw_text"]])[0].strip()), []).append(m)
res = []
for o in out:
    ms = byt.get((o["family_id"], o["text"].strip()), [])
    for m in ms:
        res.append({**o, "model": m})
jdump(OUT / "english_baseline.jsonl", res)
import collections
print(collections.Counter((r["model"], r["J1"] == r["J2"], r["J1"]) for r in res))
