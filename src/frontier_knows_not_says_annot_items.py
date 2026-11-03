"""Builds the (NOT sent) human-confirmation request items for knows_not_says: annotation/frontier_knows_not_says_items.json (annotate.html-style,
single polarity question, blind: sentence only), a randomised key, and an assignment table (3 raters per item, 20 annotators P01..P20 as placeholders).
Items: every detector-negated model output in the validity sample + 150 random detector-not-negated outputs per model + the 100 source sentences."""
import json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent; rng = np.random.default_rng(20261102)
K = pd.read_csv(ROOT / "annotation/frontier_knows_not_says_key.csv"); sel = []
for s, g in K.groupby("set"):
    if s == "source": sel.append(g)
    else:
        sel.append(g[g.detector_neg == 1]); o = g[g.detector_neg == 0]; sel.append(o.iloc[rng.permutation(len(o))[:150]])
S = pd.concat(sel).drop_duplicates("family_id"); S = S.iloc[rng.permutation(len(S))].reset_index(drop=True)
Q = "Is the main thing the sentence says negated (not/never/no/don't) or affirmative? Uncertainty wording like 'not sure' is unclear/mixed."
items = []; key = []
for i, r in S.iterrows():
    iid = "kv-" + hashlib.sha256(f"{r.family_id}|{r.text}".encode()).hexdigest()[:8]
    items.append(dict(item_id=iid, text=r.text, critical=dict(dimension="polarity", question=Q, options=["negated", "affirmative", "unclear/mixed"]), input_text=""))
    key.append(dict(item_id=iid, family_id=r.family_id, set=r.set, detector=r.detector, detector_neg=r.detector_neg))
json.dump(dict(run="knows_not_says_validity", codebook_version="polarity only", seed=20261102, general_dims=[], practice=[], items=items), open(ROOT / "annotation/frontier_knows_not_says_items.json", "w"), indent=1)
pd.DataFrame(key).to_csv(ROOT / "annotation/frontier_knows_not_says_items_key.csv", index=False)
P = [f"P{j:02d}" for j in range(1, 21)]; rows = []
for n, it in enumerate(items):
    for k in range(3): rows.append(dict(item_id=it["item_id"], annotator=P[(n * 3 + k) % 20]))
A = pd.DataFrame(rows); A.to_csv(ROOT / "annotation/frontier_knows_not_says_assignment.csv", index=False)
print(len(items), "items;", pd.DataFrame(key).groupby("set").size().to_dict(), "; items per annotator:", A.groupby("annotator").size().min(), "-", A.groupby("annotator").size().max())
