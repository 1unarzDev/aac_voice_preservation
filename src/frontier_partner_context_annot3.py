"""Round-3 annotation items (NOT sent). Part A (paraphrase/reply/fabrication/own-statement, ~150 X-negation outputs + 50 affirmative controls)
and Part B (echo/reply filter validity, ~100 units stratified by judge decision, both arms). Seed 20261106.
Writes annotation/frontier_partner_context_r3_items.json and annotation/frontier_partner_context_r3_key.csv."""
import json, random, sys, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/partner_context"; rnd = random.Random(20261106)
items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
D = [json.loads(l) for l in open(OUT / "r3_decomp_labels.jsonl")]
echo = {}
for l in open(OUT / "echo_labels.jsonl"): j = json.loads(l); echo[(j["turn"], j["text"])] = j
a0 = {}
for l in open(OUT / "r3_arm0_echo_labels.jsonl"): j = json.loads(l); a0[(j["turn"], j["text"])] = j
def dec(j):
    e = any(j[k] in ("yes", None) for k in ("EJ1_echo", "EJ2_echo")); r = any(j[k] in ("yes", None) for k in ("EJ1_reply", "EJ2_reply"))
    return "reply" if r else ("echo" if e else "none")
out, key = [], []
def seen(lst): s = set(); return [x for x in lst if not ((x["turn"], x["text"]) in s or s.add((x["turn"], x["text"])))]
neg = seen([x for x in D if x["group"] == "propositional_negation"]); ctl = seen([x for x in D if x["group"] == "affirmative_control"])
rnd.shuffle(ctl); ctl = ctl[:50]
# ~10 machine-licensed (echo/reply) negations as anchors from the round-2 key population
df = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); p = df.channel.str.split("|", expand=True); df["kind"], df["turn"] = p[0], p[1]; df["cb"] = p[2].eq("cb")
df = df[df.turn.isin(["Xa", "Xb", "Xc"]) & ~df.cb & (df.kind == "bare") & (df.variant_value == "affirmative") & (df.critical == "negated")].copy()
df["tt"] = [items[f]["partner_turns"][t] for f, t in zip(df.family_id, df.turn)]; df["jd"] = [dec(echo[(a, b)]) for a, b in zip(df.tt, df.text)]
lic = df[df.jd != "none"].drop_duplicates(["tt", "text"]); ids = sorted(lic.index); rnd.shuffle(ids)
anch = [dict(uid=f"L{i:03d}", group="machine_licensed_anchor", family_id=r.family_id, model=r.model, turn_type=r.turn, kw=items[r.family_id]["bare"], turn=r.tt, text=r.text) for i, r in enumerate(df.loc[ids[:10]].itertuples())]
A = neg + anch + ctl; rnd.shuffle(A)
for i, x in enumerate(A):
    iid = f"pc3A{i:03d}"
    out.append(dict(id=iid, part="A", keywords=x["kw"], turn=x["turn"], sentence=x["text"],
        q="Compared with the partner's remark, which best describes the sentence? (a) it restates the partner's remark in other words; (b) it is a reply to the partner (agrees with or acknowledges the remark); (c) it adds something negative that neither the keywords nor the remark support (invented); (d) it is a plain statement about the keywords' event that the person could say without the remark; (e) other / unclear",
        options=["a", "b", "c", "d", "e"]))
    key.append(dict(id=iid, part="A", group=x["group"], family_id=x["family_id"], model=x["model"], turn_type=x["turn_type"], machine_class=x.get("D1", ""), machine_class2=x.get("D2", "")))
# Part B: echo/reply filter validity, 100 units stratified by judge decision, both arms
Bx = df.drop_duplicates(["tt", "text"]).copy(); Bx["arm"] = "turn_present"
rows = []
for jd in ("echo", "reply", "none"):
    g = Bx[Bx.jd == jd]; ids = sorted(g.index); rnd.shuffle(ids); rows += [dict(arm="turn_present", jd=jd, turn=g.loc[i].tt, text=g.loc[i].text, family_id=g.loc[i].family_id, model=g.loc[i].model, turn_type=g.loc[i].turn) for i in ids[:25]]
z = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); zp = z.channel.str.split("|", expand=True); z["turn"] = zp[1]
z = z[(z.turn == "0") & (z.critical == "negated")].drop_duplicates(["family_id", "text"])
arm0 = []
for r in z.itertuples():
    t = items[r.family_id]["partner_turns"]["Xa"]; j = a0.get((t, r.text))
    if j: arm0.append(dict(arm="no_turn_counterfactual", jd=dec(j), turn=t, text=r.text, family_id=r.family_id, model=r.model, turn_type="Xa(counterfactual)"))
arm0 = seen(arm0); byd = {}
for r in arm0: byd.setdefault(r["jd"], []).append(r)
for jd, lst in byd.items(): rnd.shuffle(lst); rows += lst[:max(8, 25 if jd == "none" else 25)][:25]
rows = rows[:100] if len(rows) > 100 else rows; rnd.shuffle(rows)
for i, r in enumerate(rows):
    iid = f"pc3B{i:03d}"
    out.append(dict(id=iid, part="B", turn=r["turn"], sentence=r["text"],
        q="Question 1: Does the sentence re-use the partner's own wording about the outcome (same negative phrase, verbatim or nearly)? yes / no.  Question 2: Is the sentence phrased as a reply to the partner (starts with yes/oh/I heard/I know, or acknowledges what they said)? yes / no.",
        options=["echo:yes|no", "reply:yes|no"]))
    key.append(dict(id=iid, part="B", group=r["arm"], family_id=r["family_id"], model=r["model"], turn_type=r["turn_type"], machine_class=r["jd"], machine_class2=""))
# rater assignment: 20 annotator slots, each item rated by 3 distinct slots, round robin over a shuffled order
order = list(range(len(out))); rnd.shuffle(order); slots = {i: [] for i in range(len(out))}; k = 0
for i in order:
    for _ in range(3): slots[i].append(k % 20 + 1); k += 1
kd = pd.DataFrame(key); kd["raters"] = [";".join(map(str, slots[i])) for i in range(len(out))]
json.dump(out, open(ROOT / "annotation/frontier_partner_context_r3_items.json", "w"), indent=1, ensure_ascii=False); kd.to_csv(ROOT / "annotation/frontier_partner_context_r3_key.csv", index=False)
per = pd.Series([s for v in slots.values() for s in v]).value_counts()
print(kd.groupby(["part", "group"]).size().to_dict(), "items per annotator min/max", per.min(), per.max())
print(kd[kd.part == "B"].groupby(["group", "machine_class"]).size().to_dict())
