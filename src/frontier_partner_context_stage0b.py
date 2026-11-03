"""Round-2 Stage 0: draw 130 polarity families (E0 excluded), author turns 0/D/Xa/Xb/Xc/Q with a LOCAL non-gpt author, check with gpt-6.1-sol.
  python src/frontier_partner_context_stage0b.py --author mistral-nemo-12b --out turns2.jsonl [--n-fam 40]
Local server must be up (the wrapper shell takes the GPU lock). Writes analysis/frontier/partner_context/<out>, checker2_<tag>.jsonl."""
import asyncio, json, random, re, sys, argparse, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models, frontier_partner_context_templates2 as T
from openai import AsyncOpenAI
OUT = ROOT / "analysis/frontier/partner_context"
ap = argparse.ArgumentParser(); ap.add_argument("--author", required=True); ap.add_argument("--out", required=True); ap.add_argument("--n-fam", type=int, default=0)
a = ap.parse_args()

def families():
    e0 = set(json.load(open(OUT / "turns_meta.json"))["draw"])
    hw = [json.loads(l) for l in open(ROOT / "data/items/hw.jsonl")]
    r2 = [json.loads(l) for l in open(ROOT / "data/items/r2_c1.jsonl")]
    pool = [f for f in hw if f["dimension"] == "polarity" and f["family_id"] not in e0] + [f for f in r2 if f["dimension"] == "polarity"]
    byid = {f["family_id"]: f for f in pool}
    draw = random.Random(T.SEED).sample(sorted(byid), 130)
    return draw, byid
draw, byid = families()
if a.n_fam: draw = sorted(draw)[:a.n_fam]
spec = models.get(a.author)
local = AsyncOpenAI(base_url=spec.base_url, api_key="x", max_retries=2)
api = AsyncOpenAI(base_url=models.API_BASE, api_key=models.api_key(), max_retries=3)
lsem, asem = asyncio.Semaphore(4), asyncio.Semaphore(4)
NEG = re.compile(r"\b(" + "|".join(re.escape(t) for t in T.NEG_TOKENS if t != "n't") + r")\b|n't|n’t", re.I)
XC = re.compile(r"\b(no|nobody|nothing|none|never|no one)\b", re.I)
STOP = set("a an the of to in on at for with by is are was were be been it its this that these those do does did have has had will would can could should may might and or but if so as from about up out there their they them he she his her we you i my your our me us what who which when where how why not yes any some more than then just very also too into over after before again".split())

def stem(w): return re.sub(r"[^a-z]", "", w.lower())[:4]

async def chat(client, sem, model, content, **kw):
    for k in range(6):
        try:
            async with sem:
                r = await client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}], timeout=180, **kw)
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            print("retry", type(e).__name__, str(e)[:100], file=sys.stderr); await asyncio.sleep(2 ** k)
    return ""

async def author(f, typ, retry):
    ins = T.INSTRUCTION.format(bare=f["bare"], noncritical=f.get("noncritical") or "-", spec=T.SPEC[typ])
    if retry: ins += T.RETRY_SUFFIX
    kw = dict(temperature=0.8, seed=7) if retry else dict(temperature=0.0)
    t = await chat(local, lsem, spec.model, ins, max_tokens=60, **kw)
    t = t.strip().split("\n")[0].strip().strip('"').strip("“”")
    return t

async def vote(f, turn, order):
    kw = f["bare"]; rd = [T.READINGS["aff"].format(kw=kw), T.READINGS["neg"].format(kw=kw)]
    if order == 1: rd = rd[::-1]
    out = (await chat(api, asem, "gpt-6.1-sol", T.CHECKER.format(kw=kw, turn=turn, r1=rd[0], r2=rd[1]), reasoning_effort="low", max_tokens=400)).lower()
    m = re.search(r"\b(1|2|neither)\b", out)
    if not m: return None
    if m.group(1) == "neither": return "neither"
    return "aff" if (int(m.group(1)) - 1 == 0) == (order == 0) else "neg"

async def lock(f, turn):
    kw = f["bare"] + "; " + (f.get("noncritical") or "")
    out = (await chat(api, asem, "gpt-6.1-sol", T.LOCK.format(kw=kw, turn=turn), reasoning_effort="low", max_tokens=300)).lower()
    m = re.search(r"\b(yes|no)\b", out); return None if not m else m.group(1)

def lexlock(f, turn):
    ok = {stem(w) for w in re.findall(r"[A-Za-z']+", f["bare"] + " " + (f.get("noncritical") or ""))}
    bad = [w for w in re.findall(r"[A-Za-z']+", turn) if w.lower() not in STOP and stem(w) not in ok]
    return bad

def passes(typ, votes, turn, lk, bad):
    n = lambda lab: sum(v == lab for v in votes) >= 2
    hasneg = bool(NEG.search(turn))
    if len(turn.split()) > 14 or re.search(r"work(ed)? out", turn, re.I): return False
    if typ == "D": return n("aff") and not hasneg
    if typ == "Q": return n("neither") and not hasneg and lk == "no" and len(bad) <= 1
    if typ == "Xa": return n("neg") and hasneg
    if typ == "Xb": return n("neg") and not hasneg
    if typ == "Xc": return n("neg") and bool(XC.search(turn))
    return False

async def one(f, typ):
    rec = {"family_id": f["family_id"], "type": typ, "attempts": []}
    for retry in (False, True):
        turn = await author(f, typ, retry)
        votes = await asyncio.gather(*[vote(f, turn, o) for o in (0, 1, 0)])
        lk = await lock(f, turn) if typ == "Q" else None
        bad = lexlock(f, turn) if typ == "Q" else []
        ok = passes(typ, votes, turn, lk, bad)
        rec["attempts"].append({"turn": turn, "votes": votes, "lock": lk, "lex_offtopic": bad, "pass": ok, "retry": retry})
        if ok: break
    rec["turn"] = rec["attempts"][-1]["turn"]; rec["pass"] = rec["attempts"][-1]["pass"]
    return rec

async def main():
    types = ["Xa", "Xb", "Xc"] if a.n_fam else ["D", "Xa", "Xb", "Xc", "Q"]
    res = await asyncio.gather(*[one(byid[i], t) for i in draw for t in types])
    with (OUT / a.out).open("w") as fh:
        for r in res: fh.write(json.dumps({"family_id": r["family_id"], "type": r["type"], "turn": r["turn"], "pass": r["pass"], "author": a.author}, ensure_ascii=False) + "\n")
    with (OUT / ("checker2_" + a.out)).open("w") as fh:
        for r in res: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = collections.Counter((r["type"], r["pass"]) for r in res); f1 = collections.Counter((r["type"], r["attempts"][0]["pass"]) for r in res)
    meta = {"author": a.author, "n_families": len(draw), "draw_all130": sorted(families()[0]), "templates2_sha256": T.sha(),
            "pass_after_retry": {t: c[(t, True)] / max(1, c[(t, True)] + c[(t, False)]) for t in types},
            "pass_first_try": {t: f1[(t, True)] / max(1, f1[(t, True)] + f1[(t, False)]) for t in types}}
    (OUT / ("turns2_meta_" + a.author + ".json")).write_text(json.dumps(meta, indent=1)); print(json.dumps(meta, indent=1))
asyncio.run(main())
