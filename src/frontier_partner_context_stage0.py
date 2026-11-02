"""Stage 0 (E0 pilot): draw 40 polarity families, author turns N/D/X/Q, run the neutrality/manipulation checker.
  python src/frontier_partner_context_stage0.py
Writes analysis/frontier/partner_context/{turns.jsonl, checker.jsonl, turns_meta.json}."""
import asyncio, json, random, re, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models, frontier_partner_context_templates as T
from openai import AsyncOpenAI
OUT = ROOT / "analysis/frontier/partner_context"
fams = [json.loads(l) for l in open(ROOT / "data/items/hw.jsonl")]
pol = sorted([f for f in fams if f["dimension"] == "polarity"], key=lambda f: f["family_id"])
draw = random.Random(T.SEED).sample([f["family_id"] for f in pol], 40)
byid = {f["family_id"]: f for f in pol}
client = AsyncOpenAI(base_url=models.API_BASE, api_key=models.api_key(), max_retries=3)
sem = asyncio.Semaphore(4)
NEG = re.compile(r"\b(" + "|".join(re.escape(t) for t in T.NEG_TOKENS if t != "n't") + r")\b|n't", re.I)

async def chat(model, content, **kw):
    for a in range(6):
        try:
            async with sem:
                r = await client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}], timeout=120, **kw)
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            print("retry", type(e).__name__, str(e)[:100], file=sys.stderr); await asyncio.sleep(2 ** a)
    return ""

async def author(f, typ, retry=False):
    ins = T.INSTRUCTION.format(bare=f["bare"], noncritical=f["noncritical"], type=typ, template=T.TEMPLATES["polarity"][typ])
    if retry: ins += T.RETRY_SUFFIX
    t = await chat("gpt-6.1-terra", ins, temperature=0, max_tokens=60)
    return t.strip().strip('"').strip("“”")

async def vote(f, turn, order):
    kw = f["bare"]
    rd = [T.READINGS["aff"].format(kw=kw), T.READINGS["neg"].format(kw=kw)]
    if order == 1: rd = rd[::-1]
    p = T.CHECKER.format(kw=kw, turn=turn, r1=rd[0], r2=rd[1])
    a = (await chat("gpt-6.1-sol", p, reasoning_effort="low", max_tokens=400)).lower()
    m = re.search(r"\b(1|2|neither)\b", a)
    if not m: return None
    v = m.group(1)
    if v == "neither": return "neither"
    idx = int(v) - 1
    kind = "aff" if (idx == 0) == (order == 0) else "neg"
    return kind

def passes(typ, votes, turn):
    n_ok = lambda lab: sum(v == lab for v in votes) >= 2
    lex = bool(NEG.search(turn))
    if typ in ("N", "Q"): return n_ok("neither") and not lex
    if typ == "D": return n_ok("aff") and not lex
    if typ == "X": return n_ok("neg")
    return False

async def one(f, typ):
    rec = {"family_id": f["family_id"], "type": typ, "attempts": []}
    for retry in (False, True):
        turn = await author(f, typ, retry)
        orders = [0, 1, 0]   # fixed reading-order pattern for votes 0,1,2
        votes = await asyncio.gather(*[vote(f, turn, o) for o in orders])
        ok = passes(typ, votes, turn) and len(turn.split()) <= 14
        rec["attempts"].append({"turn": turn, "votes": votes, "orders": orders, "pass": ok, "retry": retry})
        if ok: break
    rec["final"] = rec["attempts"][-1]["turn"]; rec["pass"] = rec["attempts"][-1]["pass"]
    return rec

async def main():
    jobs = [one(byid[i], t) for i in draw for t in "NDXQ"]
    res = await asyncio.gather(*jobs)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "turns.jsonl").open("w") as fh:
        for r in res: fh.write(json.dumps({"family_id": r["family_id"], "type": r["type"], "turn": r["final"], "pass": r["pass"]}, ensure_ascii=False) + "\n")
    with (OUT / "checker.jsonl").open("w") as fh:
        for r in res: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = collections.Counter((r["type"], r["pass"]) for r in res)
    first = collections.Counter((r["type"], r["attempts"][0]["pass"]) for r in res)
    meta = {"draw": draw, "seed": T.SEED, "templates_sha256": T.sha(), "n_turns": len(res),
            "pass_after_retry": {t: c[(t, True)] / sum(c[(t, x)] for x in (True, False)) for t in "NDXQ"},
            "pass_first_try": {t: first[(t, True)] / sum(first[(t, x)] for x in (True, False)) for t in "NDXQ"},
            "overall_pass_after_retry": sum(r["pass"] for r in res) / len(res),
            "n_fail_families": sorted({r["family_id"] for r in res if not r["pass"]})}
    (OUT / "turns_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))
asyncio.run(main())
