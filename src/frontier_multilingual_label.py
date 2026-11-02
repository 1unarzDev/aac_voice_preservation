"""Label pilot outputs. Polarity: blind sol judge, direct (target language) + back-translation route, batched 10/call, text only."""
import asyncio, sys, json, re, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import httpx

DIRECT = ("You label sentences written in {lang}. For each numbered sentence decide whether the MAIN thing it says is negated "
          "(not/never/no/don't/n't equivalents) or affirmative. Uncertainty wording such as 'not sure' counts as unclear. "
          "Return ONLY a JSON list of strings, one per sentence, each exactly one of: negated, affirmative, unclear.\n{items}")
TRANS = ("Translate each numbered {lang} sentence into English, literally. Return ONLY a JSON list of strings, same order.\n{items}")
EN = ("You label English sentences. For each numbered sentence decide whether the MAIN thing it says is negated "
      "(not/never/no/don't) or affirmative. Uncertainty wording such as 'not sure' counts as unclear. "
      "Return ONLY a JSON list of strings, one per sentence, each exactly one of: negated, affirmative, unclear.\n{items}")


def numbered(xs):
    return "\n".join(f"{i+1}. {x}" for i, x in enumerate(xs))


def pl(t, n):
    m = re.search(r"\[.*\]", t or "", re.S)
    try:
        v = json.loads(m.group(0))
        if len(v) == n:
            return v
    except Exception:  # noqa: BLE001
        pass
    return None


async def batched(c, sem, tmpl, lang, texts, mt=3500, B=10):
    out = {}
    chunks = [texts[i:i + B] for i in range(0, len(texts), B)]
    async def one(ch):
        for attempt in range(3):
            t = await chat(c, sem, "gpt-6.1-sol", tmpl.format(lang=lang, items=numbered(ch)) + ("" if attempt == 0 else " "*attempt), mt)
            v = pl(t, len(ch))
            if v:
                return dict(zip(ch, v))
        return {x: None for x in ch}
    for d in await asyncio.gather(*[one(ch) for ch in chunks]):
        out.update(d)
    return out


async def main():
    rows = []
    mname = sys.argv[1]
    rows += jl(RUN / f"gen_{mname}.jsonl")
    sem = asyncio.Semaphore(3)
    pol = [r for r in rows if r["kind"] == "POL"]
    res = {}
    async with httpx.AsyncClient() as c:
        for lang, L in LANGS.items():
            texts = sorted({r["text"] for r in pol if r["lang"] == lang and r["text"]})
            d = await batched(c, sem, DIRECT, L, texts)
            tr = await batched(c, sem, TRANS, L, texts)
            en = sorted({v for v in tr.values() if v})
            ed = await batched(c, sem, EN, "English", en)
            for t in texts:
                res[(lang, t)] = {"direct": d.get(t), "back": tr.get(t), "route": ed.get(tr.get(t)) if tr.get(t) else None}
    out = []
    for r in pol:
        x = res.get((r["lang"], r["text"]), {})
        out.append({**r, **x})
    jdump(OUT / f"pol_labels_{mname}.jsonl", out)
    n = len(out); ok = sum(1 for o in out if o.get("direct") and o.get("route"))
    print(n, ok, sum(1 for o in out if o.get("direct") and o.get("route") and o["direct"] != o["route"]))

asyncio.run(main())
