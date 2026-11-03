"""default_profiles round 2 (R2-7): build annotation items + key (NOT sent). Draw: sha256("dp2|"+unit) order within stratum, seeded, from exposure units of the human keyword sets.
    . .venv/bin/activate && python src/frontier_default_profiles_annot.py"""
import hashlib, json, re, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.argv = ["x", "--boot", "1"]; sys.path.insert(0, str(ROOT / "src"))
import importlib.util
spec = importlib.util.spec_from_file_location("r2", ROOT / "src/frontier_default_profiles_r2.py"); r2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r2)
U = r2.U.merge(r2.msg[["item_id", "text", "inclusion_prob"]], on="item_id"); h = lambda u: hashlib.sha256(("dp2|" + u).encode()).hexdigest()
def draw(mask, k, used):
    d = U[mask & ~U.item_id.isin(used)].copy(); d["h"] = d.unit.map(h); d = d.sort_values("h").drop_duplicates("item_id").head(k); used |= set(d.item_id); return d
used = set(); S = []
S.append(("E_speech_act", draw(U.E_speech_act > 0, 120, used))); S.append(("E_politeness", draw(U.E_politeness > 0, 60, used)))
S.append(("control", draw((~U.nonstmt) & (~U.polite) & ~U.kw_act & ~U.kw_pol, 60, used)))
items = []; key = []
for st, d in S:
    for r in d.itertuples(): items.append(dict(item_id="dp-" + h(r.unit)[:8], text=r.text, keywords=r.kw)); key.append(dict(item_id="dp-" + h(r.unit)[:8], stratum=st, unit=r.unit, item=r.item_id, detector_nonstmt=bool(r.nonstmt), detector_polite=bool(r.polite), w=1 / r.inclusion_prob))
import random; random.Random("dp2order").shuffle(items)
Qs = [dict(id="q1", question="What does the SENTENCE do?", options=["statement", "question", "request/command", "other"]),
      dict(id="q2", question="Is the SENTENCE polite (please, thank you, sorry, softened wording like 'could you')?", options=["polite", "not polite"]),
      dict(id="q3", question="Look ONLY at the KEYWORDS. Do the keywords by themselves already show that the sentence is a question or a request (not a plain statement)?", options=["yes", "no"]),
      dict(id="q4", question="Look ONLY at the KEYWORDS. Do the keywords by themselves already show politeness?", options=["yes", "no"])]
json.dump(dict(run="frontier_default_profiles", seed="dp2", questions=Qs, items=items), open(ROOT / "annotation/frontier_default_profiles_items.json", "w"), indent=1)
pd.DataFrame(key).to_csv(ROOT / "annotation/frontier_default_profiles_key.csv", index=False); print(len(items), pd.DataFrame(key).stratum.value_counts().to_dict())
