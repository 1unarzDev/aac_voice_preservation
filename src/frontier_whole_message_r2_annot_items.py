"""Build (NOT send) the R-WM-1 annotation items, key and assignment for round 2. Draw rule in ANNOTATION_REQUEST.md.
Outputs: annotation/frontier_whole_message_items.json, annotation/frontier_whole_message_key.csv, annotation/frontier_whole_message_assignment.csv"""
import hashlib, json, sys, re
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
import frontier_whole_message_stage1_jobs as J1
R = ROOT / "runs/frontier_whole_message_r2"; SEED = "wm-r2h"
h = lambda *a: hashlib.sha256("|".join(map(str, a)).encode()).hexdigest()
inp = pd.read_csv(R / "inputs.csv", keep_default_na=False)
g = pd.read_csv(R / "gens_gpt-6.1-terra.csv", keep_default_na=False); g = g[(g.draw == 0) & g.arm.isin(["A0", "A1", "A2"]) & (g.channel == "chip1")]
fams = {}
for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
    o = json.loads(l); fams[o["family_id"]] = o
cache = m1.load()
# 36 chip1 inputs: per dimension, 6 families by hash, one variant by hash
sel = []
for dim, s in inp[inp.channel == "chip1"].groupby("dimension"):
    for f in sorted(s.family_id.unique(), key=lambda f: h(SEED, "fam", f))[:6]:
        v = sorted(["A", "B"], key=lambda v: h(SEED, "var", f, v))[0]; sel.append((f, v))
items, key = [], []
for f, v in sel:
    for arm in ["A0", "A1", "A2"]:
        r = g[(g.family_id == f) & (g.variant == v) & (g.arm == arm)].iloc[0]
        it = fams[f]; iid = "wm-" + h(SEED, "item", arm, f, v)[:8]
        fv = cache.get(m1.key("free", r.input_text, r.text, None))
        items.append(dict(id=iid, type="O", input_text=r.input_text, output=r.text, version_A=it["variants"]["A"]["source"], version_B=it["variants"]["B"]["source"],
                          questions=["Q1 which version does the output say: A / B / something else / cannot tell", "Q2 does it add anything you did not ask for or leave out something you meant: added / left out / both / neither",
                                     "Q3 would you accept it as the message: yes / yes with a small edit / no"]))
        key.append(dict(id=iid, kind="output", arm=arm, generator="gpt-6.1-terra", family_id=f, variant=v, dimension=r.dimension, intended_variant=v, text=r.text,
                        gpt_UC=int(bool(fv["unrequested"])) if fv else "", gpt_score=fv["score_1to5"] if fv else ""))
# 12 verbatim keyword copies: Part 18 gate-set inputs, copy = keywords with chips and 'Keywords:' stripped, by hash
gate = J1.gate.assign(_k=J1.gate.item_id.map(lambda i: h(SEED, "vc", i))).sort_values("_k").head(12)
for _, r in gate.iterrows():
    cp = J1.kw(r.input_text); iid = "wm-" + h(SEED, "vc", r.item_id)[:8]
    fv = cache.get(m1.key("free", r.input_text, cp, None))
    items.append(dict(id=iid, type="V", input_text=r.input_text, output=cp, questions=["Q4 does the output say anything beyond the keywords and chips: yes / no", "Q5 is it a complete sentence you could say as it is: yes / no"]))
    key.append(dict(id=iid, kind="verbatim_copy", arm="keyword_copy", generator="none", family_id=r.family_id, variant="", dimension=r.dimension, intended_variant="", text=cp,
                    gpt_UC=int(bool(fv["unrequested"])) if fv else "", gpt_score=fv["score_1to5"] if fv else ""))
# assignment: 20 annotators, each item 3 annotators, at most one output per input per annotator, load balanced
ann = [f"R{i:02d}" for i in range(1, 21)]; load = {a: 0 for a in ann}; hold = {a: set() for a in ann}; asg = []
kd = {k["id"]: k for k in key}
for it in sorted(items, key=lambda i: h(SEED, "order", i["id"])):
    k = kd[it["id"]]; grp = (k["family_id"], k["variant"]) if k["kind"] == "output" else (k["id"],)
    cand = sorted([a for a in ann if grp not in hold[a]], key=lambda a: (load[a], h(SEED, "a", a, it["id"])))[:3]
    for a in cand: load[a] += 1; hold[a].add(grp); asg.append((it["id"], a))
json.dump(dict(run="whole_message_r2", seed=SEED, n_items=len(items), items=items), open(ROOT / "annotation/frontier_whole_message_items.json", "w"), indent=1)
pd.DataFrame(key).to_csv(ROOT / "annotation/frontier_whole_message_key.csv", index=False)
pd.DataFrame(asg, columns=["item_id", "annotator"]).to_csv(ROOT / "annotation/frontier_whole_message_assignment.csv", index=False)
print(len(items), "items;", len(asg), "ratings; load", min(load.values()), "-", max(load.values()), "; unique (input,output) among arms:", len({(i["input_text"], i["output"]) for i in items if i["type"] == "O"}))
