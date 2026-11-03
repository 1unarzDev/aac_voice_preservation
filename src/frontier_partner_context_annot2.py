"""Round-2 annotation items (NOT sent): Part A echo vs propositional (150 outputs), Part B chip-semantics agreement-reply (60), Part C turn check (100 turns).
Seed 20261103. Writes annotation/frontier_partner_context_r2_items.json and annotation/frontier_partner_context_r2_key.csv."""
import json, random, sys, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "analysis/frontier/partner_context"; rnd = random.Random(20261103)
items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
echo = {}
for l in open(OUT / "echo_labels.jsonl"):
    j = json.loads(l); echo[(j["turn"], j["text"])] = j
df = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); p = df.channel.str.split("|", expand=True); df["kind"], df["turn"] = p[0], p[1]; df["cb"] = p[2].eq("cb")
df = df[(df.turn.isin(["Xa", "Xb", "Xc"])) & (~df.cb) & (df.critical == "negated") & (df.variant_value == "affirmative")].copy()
df["turn_text"] = [items[f]["partner_turns"][t] for f, t in zip(df.family_id, df.turn)]
def lic(r):
    j = echo[(r.turn_text, r.text)]; return any(j[k] == "yes" or j[k] is None for k in ("EJ1_echo", "EJ2_echo", "EJ1_reply", "EJ2_reply"))
df["lic"] = df.apply(lic, axis=1)
out, key = [], []
# Part A: bare cells, stratified model x form x judge class, 6 each (fewer if scarce), unique (turn,text)
A = df[df.kind == "bare"].drop_duplicates(["turn_text", "text"])
picked = []
for (m, t, l), g in A.groupby(["model", "turn", "lic"]):
    ids = sorted(g.index); rnd.shuffle(ids); picked += ids[:6]
rnd.shuffle(picked); picked = picked[:150]
for i, ix in enumerate(picked):
    r = df.loc[ix]; out.append(dict(id=f"pcA{i:03d}", part="A", turn=r.turn_text, sentence=r.text,
        q="Which best describes the sentence? (a) it repeats or restates what the partner said; (b) it is a reply addressed to the partner (e.g. Yes..., I heard...); (c) it is the person's own statement that the thing did not happen, in their own words; (d) other / unclear",
        options=["a", "b", "c", "d"]))
    key.append(dict(id=f"pcA{i:03d}", part="A", family_id=r.family_id, model=r.model, turn_type=r.turn, judge_licensed=bool(r.lic), channel=r.channel))
# Part B: chip cells with [YES] cue, negated outputs
Bd = df[df.kind == "chip"].drop_duplicates(["turn_text", "text"]); pick = []
for (m, l), g in Bd.groupby(["model", "lic"]):
    ids = sorted(g.index); rnd.shuffle(ids); pick += ids[:8]
rnd.shuffle(pick); pick = pick[:60]
for i, ix in enumerate(pick):
    r = df.loc[ix]; kw = items[r.family_id]["bare"]
    out.append(dict(id=f"pcB{i:03d}", part="B", keywords=kw, turn=r.turn_text, sentence=r.text,
        context="The person pressed the YES button with the keywords, meaning: they want to say that the keywords' event happened / is so (an affirmative message).",
        q="Compared with what the person wanted, the sentence: (a) says what they wanted; (b) contradicts what they wanted (silently reverses it); (c) acknowledges or agrees with the partner's remark in a way that is still consistent with what they wanted; (d) unclear",
        options=["a", "b", "c", "d"]))
    key.append(dict(id=f"pcB{i:03d}", part="B", family_id=r.family_id, model=r.model, turn_type=r.turn, judge_licensed=bool(r.lic), channel=r.channel))
# Part C: round-2 turn check, 20 per type, with checker verdict hidden
T = [json.loads(l) for l in open(OUT / "turns2.jsonl")]
for ty in ["D", "Xa", "Xb", "Xc", "Q"]:
    g = sorted([t for t in T if t["type"] == ty], key=lambda t: t["family_id"]); rnd.shuffle(g)
    for t in g[:20]:
        f = items[t["family_id"]]; kw = f["bare"]; flip = rnd.random() < 0.5
        r = ['the person\'s sentence will say that "%s" is so / happened (affirmative)' % kw, 'the person\'s sentence will say that "%s" did not happen / is not so (negated)' % kw]
        if flip: r = r[::-1]
        i = len(key); out.append(dict(id=f"pcC{i:03d}", part="C", keywords=kw, turn=t["turn"], reading1=r[0], reading2=r[1],
            q="Which reply does the remark make more likely? (reading 1 / reading 2 / neither) and how natural is the remark (1-5)?", options=["1", "2", "neither"]))
        key.append(dict(id=f"pcC{i:03d}", part="C", family_id=t["family_id"], model="", turn_type=ty, judge_licensed="", channel="", checker_pass=t["pass"], reading1_kind="neg" if flip else "aff"))
json.dump(out, open(ROOT / "annotation/frontier_partner_context_r2_items.json", "w"), indent=1, ensure_ascii=False)
pd.DataFrame(key).to_csv(ROOT / "annotation/frontier_partner_context_r2_key.csv", index=False)
print(pd.DataFrame(key).groupby("part").size().to_dict(), "A judge_licensed share", pd.DataFrame(key).query("part=='A'").judge_licensed.mean())
