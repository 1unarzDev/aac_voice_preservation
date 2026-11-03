"""Second blind back-translator (qwen2.5-14b, local) for the strict translation gate. Run with the qwen14 server up."""
import asyncio, sys, json
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-14b"
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
BACK = "Translate this {lang} text into English, literally. You see no original. Return ONLY a JSON object with the same keys.\n{inp}"
async def main():
    rows = [r for r in jl(OUT / "translations.jsonl") if r.get("t")]
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as c:
        async def one(r):
            bk = {k: r["t"][k] for k in ("A", "B", "keywords") if k in r["t"] and r["t"][k]}
            t = await chat2(c, sem, MODEL, BACK.format(lang=LANGS[r["lang"]], inp=json.dumps(bk, ensure_ascii=False)), 600)
            return {"lang": r["lang"], "family_id": r["family_id"], "kind": r["kind"], "back2": pj(t)}
        res = await asyncio.gather(*[one(r) for r in rows])
    jdump(OUT / ("r2_backtrans2_" + MODEL + ".jsonl"), res)
    print(len(res), sum(1 for r in res if r["back2"]))
asyncio.run(main())
