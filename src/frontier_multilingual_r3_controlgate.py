"""Round-3 E8 machine meaning-check for the control keyword sets (nominal, DE separable-prefix, second-translator kw2).
Blind back-translation by gpt-6.1-sol and gpt-6.1-terra (text only); survivor iff full-word overlap with the English bare keywords >= 0.5 under BOTH.
No native-speaker check. Output: analysis/frontier/multilingual/r3_control_gate.json"""
import asyncio, sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
BACK = "Translate this {lang} keyword string into English, literally, keeping it a short keyword string. You see no original. Return ONLY a JSON object {{\"keywords\": \"...\"}}.\n{kw}"
def norm(w):
    for s in ("ing", "es", "s"):
        if w.endswith(s) and len(w) > len(s) + 2: return w[:-len(s)]
    return w
def overlap(en, back):
    stop = {"to", "a", "the", "of", "and", "be"}
    e = [norm(t) for t in re.findall(r"[a-z]+", en.lower()) if t not in stop]; b = {norm(t) for t in re.findall(r"[a-z]+", (back or "").lower()) if t not in stop}
    return sum(x in b for x in e) / len(e) if e else 0.0
async def main():
    kc = json.load(open(OUT / "r2_keyword_conditions.json"))
    bare = {(r["lang"], r["family_id"]): r["bare"] for r in jl(OUT / "translations.jsonl")}
    sem = asyncio.Semaphore(3); res = []
    async with httpx.AsyncClient() as c:
        async def one(cond, key, kw):
            lang, fam = key.split("|")
            ov = {}; bk = {}
            for m in ("gpt-6.1-sol", "gpt-6.1-terra"):
                j = pj(await chat2(c, sem, m, BACK.format(lang=LANGS[lang], kw=kw), 1500))
                bk[m] = (j or {}).get("keywords") if isinstance(j, dict) else None
                ov[m] = overlap(bare[(lang, fam)], bk[m])
            res.append({"cond": cond, "lang": lang, "family_id": fam, "kw": kw, "english": bare[(lang, fam)], "back": bk, "overlap": ov, "survives": all(v >= .5 for v in ov.values())})
        await asyncio.gather(*[one(cond, k, v) for cond, d in (("bare_nom", kc["nominal"]), ("bare_sep", kc["sep_de"]), ("bare_kw2", kc["kw2"])) for k, v in d.items()])
    summ = {}
    for cond in ("bare_nom", "bare_sep", "bare_kw2"):
        for lang in ("de", "es", "fr"):
            x = [r for r in res if r["cond"] == cond and r["lang"] == lang]
            if x: summ[f"{lang}|{cond}"] = {"n": len(x), "survive": sum(r["survives"] for r in x)}
    json.dump({"summary": summ, "rows": sorted(res, key=lambda r: (r["cond"], r["lang"], r["family_id"]))}, open(OUT / "r3_control_gate.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summ))
asyncio.run(main())
