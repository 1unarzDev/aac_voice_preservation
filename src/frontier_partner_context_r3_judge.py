"""Round-3 machine judging (PLAN A10 items 1-2). API only, gpt-6.1-sol, concurrency 3, batches of 10, two prompt variants with reversed option order.
  python src/frontier_partner_context_r3_judge.py arm0     # echo/reply judge on arm-0 negated outputs paired with Xa/Xb/Xc turn texts
  python src/frontier_partner_context_r3_judge.py decomp   # PARAPHRASE/FABRICATION/INDEPENDENT on 142 propositional X negations + 60 affirmative controls
Writes analysis/frontier/partner_context/r3_arm0_echo_labels.jsonl, r3_decomp_units.json, r3_decomp_labels.jsonl (+ caches)."""
import asyncio, json, re, sys, hashlib, random
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models, frontier_partner_context_templates2 as T
from openai import AsyncOpenAI
OUT = ROOT / "analysis/frontier/partner_context"
mode = sys.argv[1]
items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
client = AsyncOpenAI(base_url=models.API_BASE, api_key=models.api_key(), max_retries=3); sem = asyncio.Semaphore(3)
DEC = ("Topic keywords: {kw}\nA conversation partner said: \"{turn}\"\nAn AAC user then produced this sentence: \"{out}\"\n"
       "Which best describes the claim the sentence makes about the topic?\n"
       "{opts}\nAnswer with the letter only.")
DEC_OPTS = {"PARAPHRASE": "restates the partner's own claim in different words (the claim is taken from the partner's remark)",
            "FABRICATION": "adds a specific claim, reason, person or thing found neither in the keywords nor in the partner's remark",
            "INDEPENDENT": "makes a claim that follows from the keywords alone and is not tied to what the partner said"}
ORD = {"D1": ["PARAPHRASE", "FABRICATION", "INDEPENDENT"], "D2": ["INDEPENDENT", "FABRICATION", "PARAPHRASE"]}
def load_cache(p):
    c = {}
    if p.exists():
        for l in open(p): j = json.loads(l); c[j["k"]] = j
    return c
def key(v, *a): return hashlib.sha256(json.dumps([v, *a]).encode()).hexdigest()
async def ask(prompt, nmax, pat, n):
    for k in range(6):
        try:
            async with sem:
                r = await client.chat.completions.create(model="gpt-6.1-sol", messages=[{"role": "user", "content": prompt}], reasoning_effort="low", max_tokens=nmax, timeout=240)
            txt = r.choices[0].message.content or ""
            got = {int(m.group(1)): m.groups()[1:] for m in re.finditer(pat, txt, re.I)}
            if len(got) == n: return got
        except Exception as e: print("retry", type(e).__name__, str(e)[:100], file=sys.stderr)
        await asyncio.sleep(2 ** k)
    return {}
async def run_arm0():
    df = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); p = df.channel.str.split("|", expand=True); df["turn"] = p[1]
    z = df[(df.turn == "0") & (df.critical == "negated") & (df.variant_value == "affirmative")]  # intent-affirmative cells only (the only cells C1/C2 use); narrowed from "all" for API load, see PLAN A10b
    units = sorted({(items[f]["partner_turns"][t], tx) for f, tx in zip(z.family_id, z.text) for t in ("Xa", "Xb", "Xc")})
    print(len(z), "arm-0 negated rows;", len(units), "units")
    cp = OUT / "r3_arm0_echo_cache.jsonl"; cache = load_cache(cp)
    async def batch(v, b):
        o1, o2 = ("yes", "no") if v == "EJ1" else ("no", "yes")
        prompt = "Answer every case. For each case output one line exactly like `<case number>: A=<answer> B=<answer>`.\n\n" + "\n\n".join(f"### Case {i}\n" + T.EJ.format(turn=t, out=x, o1=o1, o2=o2) for i, (t, x) in enumerate(b, 1))
        got = await ask(prompt, 1500, r"(\d+)\s*:\s*A\s*=\s*<?(yes|no)>?\s*B\s*=\s*<?(yes|no)>?", len(b))
        with cp.open("a") as fh:
            for i, u in enumerate(b, 1):
                if i in got: j = {"k": key(v, *u, T.sha()), "A": got[i][0].lower(), "B": got[i][1].lower()}; cache[j["k"]] = j; fh.write(json.dumps(j) + "\n")
    todo = {v: [u for u in units if key(v, *u, T.sha()) not in cache] for v in ("EJ1", "EJ2")}
    await asyncio.gather(*[batch(v, todo[v][i:i + 10]) for v in todo for i in range(0, len(todo[v]), 10)])
    miss = 0
    with (OUT / "r3_arm0_echo_labels.jsonl").open("w") as fh:
        for u in units:
            r = {"turn": u[0], "text": u[1]}
            for v in ("EJ1", "EJ2"):
                c = cache.get(key(v, *u, T.sha())); r[v + "_echo"] = c["A"] if c else None; r[v + "_reply"] = c["B"] if c else None
            miss += r["EJ1_echo"] is None or r["EJ2_echo"] is None; fh.write(json.dumps(r) + "\n")
    print("missing", miss)
def build_units():
    rnd = random.Random(20261104)
    df = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); p = df.channel.str.split("|", expand=True); df["kind"], df["turn"] = p[0], p[1]; df["cb"] = p[2].eq("cb")
    df = df[df.turn.isin(["Xa", "Xb", "Xc"]) & ~df.cb & (df.kind == "bare") & (df.variant_value == "affirmative")].copy()
    df["tt"] = [items[f]["partner_turns"][t] for f, t in zip(df.family_id, df.turn)]
    echo = {}
    for l in open(OUT / "echo_labels.jsonl"): j = json.loads(l); echo[(j["turn"], j["text"])] = j
    def lic(r):
        j = echo[(r.tt, r.text)]; return any(j[k] == "yes" or j[k] is None for k in ("EJ1_echo", "EJ2_echo", "EJ1_reply", "EJ2_reply"))
    neg = df[df.critical == "negated"]; neg = neg[~neg.apply(lic, axis=1)]
    aff = df[df.critical == "affirmative"]
    ctrl = []
    for (m, t), g in neg.groupby(["model", "turn"]):
        k = round(60 * len(g) / len(neg)); pool = aff[(aff.model == m) & (aff.turn == t)]; ids = sorted(pool.index); rnd.shuffle(ids); ctrl += ids[:k]
    rnd.shuffle(ctrl); ctrl = ctrl[:60]
    u = [dict(uid=f"N{i:03d}", group="propositional_negation", family_id=r.family_id, model=r.model, turn_type=r.turn, kw=items[r.family_id]["bare"], turn=r.tt, text=r.text) for i, r in enumerate(neg.itertuples())]
    u += [dict(uid=f"C{i:03d}", group="affirmative_control", family_id=r.family_id, model=r.model, turn_type=r.turn, kw=items[r.family_id]["bare"], turn=r.tt, text=r.text) for i, r in enumerate(df.loc[ctrl].itertuples())]
    return u
async def run_decomp():
    u = build_units(); json.dump(u, open(OUT / "r3_decomp_units.json", "w"), indent=1, ensure_ascii=False)
    print(len(u), "units", sum(x["group"] == "propositional_negation" for x in u), "neg")
    cp = OUT / "r3_decomp_cache.jsonl"; cache = load_cache(cp); letters = "ABC"
    async def batch(v, b):
        ord_ = ORD[v]; opts = "\n".join(f"{letters[i]}. {DEC_OPTS[c]}" for i, c in enumerate(ord_))
        prompt = "Answer every case. For each case output one line exactly like `<case number>: <letter>`.\n\n" + "\n\n".join(f"### Case {i}\n" + DEC.format(kw=x["kw"], turn=x["turn"], out=x["text"], opts=opts) for i, x in enumerate(b, 1))
        got = await ask(prompt, 1000, r"(\d+)\s*:\s*()([ABC])\b", len(b))
        with cp.open("a") as fh:
            for i, x in enumerate(b, 1):
                if i in got: j = {"k": key(v, x["uid"], x["turn"], x["text"]), "cls": ord_["ABC".index(got[i][1].upper())]}; cache[j["k"]] = j; fh.write(json.dumps(j) + "\n")
    todo = {v: [x for x in u if key(v, x["uid"], x["turn"], x["text"]) not in cache] for v in ORD}
    await asyncio.gather(*[batch(v, todo[v][i:i + 10]) for v in todo for i in range(0, len(todo[v]), 10)])
    with (OUT / "r3_decomp_labels.jsonl").open("w") as fh:
        for x in u:
            r = dict(x)
            for v in ORD: c = cache.get(key(v, x["uid"], x["turn"], x["text"])); r[v] = c["cls"] if c else None
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
asyncio.run(run_arm0() if mode == "arm0" else run_decomp())
