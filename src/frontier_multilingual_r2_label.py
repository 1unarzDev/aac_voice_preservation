"""Round-2 labelling (blind, text only): polarity via gpt-6.1-sol (direct + translate-then-English routes; EN direct only), register ambiguous outputs via sol arbiter.
Idempotent (cached). usage: python frontier_multilingual_r2_label.py"""
import asyncio, sys, json, re, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
from frontier_multilingual_register import label as det

DIRECT = ("You label sentences written in {lang}. For each numbered sentence decide whether the MAIN thing it says is negated "
          "(not/never/no/don't/n't equivalents) or affirmative. Uncertainty wording such as 'not sure' counts as unclear. "
          "Return ONLY a JSON list of strings, one per sentence, each exactly one of: negated, affirmative, unclear.\n{items}")
TRANS = "Translate each numbered {lang} sentence into English, literally. Return ONLY a JSON list of strings, same order.\n{items}"
ARB = ("Each numbered sentence is written in {lang}. Decide how it addresses the listener. Options: T = addresses the listener with the informal singular "
       "(du / tu / tú forms, including imperative or verb forms of that person); V = addresses the listener formally (Sie / vous / usted forms, including formal imperatives "
       "or verb forms); none = does not address the listener at all (first person, impersonal, infinitive-only, noun phrase); mixed = both T and V. "
       "Return ONLY a JSON list of strings, one per sentence, each exactly one of: T, V, none, mixed.\n{items}")
B = 15


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


async def batched(c, sem, tmpl, lang, texts, mt=4000):
    out = {}
    chunks = [texts[i:i + B] for i in range(0, len(texts), B)]
    async def one(ch):
        for attempt in range(3):
            t = await chat2(c, sem, "gpt-6.1-sol", tmpl.format(lang=lang, items=numbered(ch)) + " " * attempt, mt)
            v = pl(t, len(ch))
            if v:
                return dict(zip(ch, v))
        return {x: None for x in ch}
    for d in await asyncio.gather(*[one(ch) for ch in chunks]):
        out.update(d)
    return out


async def main():
    import collections
    rows, g1 = [], []
    for f in glob.glob(str(RUN2 / "gen_*.jsonl")):
        rows += jl(f)
    for f in glob.glob(str(RUN2 / "g1_*.jsonl")):
        g1 += jl(f)
    sem = asyncio.Semaphore(3)
    pol_texts = collections.defaultdict(set) if False else {}
    import collections
    pol_texts = collections.defaultdict(set); reg_texts = collections.defaultdict(set)
    for r in rows:
        if r["text"]:
            (pol_texts if r["kind"] == "POL" else reg_texts)[r["lang"]].add(r["text"])
    for r in g1:
        if r["text"]:
            (pol_texts if r["kind"] == "POL" else reg_texts)[r["lang"]].add(r["text"])
    res = {}
    async with httpx.AsyncClient() as c:
        for lang in L4:
            texts = sorted(pol_texts[lang])
            if not texts:
                continue
            d = await batched(c, sem, DIRECT, L4[lang], texts)
            if lang == "en":
                for t in texts:
                    res[f"{lang}|{t}"] = {"direct": d.get(t), "back": None, "route": None}
                continue
            tr = await batched(c, sem, TRANS, L4[lang], texts)
            en = sorted({v for v in tr.values() if isinstance(v, str) and v})
            ed = await batched(c, sem, DIRECT, "English", en)
            for t in texts:
                res[f"{lang}|{t}"] = {"direct": d.get(t), "back": tr.get(t), "route": ed.get(tr.get(t)) if tr.get(t) else None}
            print("pol", lang, len(texts), flush=True)
        json.dump(res, open(OUT / "r2_pol_labels.json", "w"), ensure_ascii=False)
        arb = {}
        for lang in LANGS:
            amb = sorted(t for t in reg_texts[lang] if det(lang, t) == "ambig")
            if amb:
                d = await batched(c, sem, ARB, L4[lang], amb)
                for t in amb:
                    arb[f"{lang}|{t}"] = d.get(t)
            print("reg-ambig", lang, len(amb), flush=True)
        json.dump(arb, open(OUT / "r2_reg_arbiter_sol.json", "w"), ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
