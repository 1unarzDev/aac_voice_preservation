"""Second translator (mistral-nemo-12b, local; call under the GPU lock with the nemo server up): REG keywords, infinitive forms, same FWD instructions as pilot."""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
sys.argv = sys.argv[:1]
import importlib
FWD = ("Translate into {lang}. Return ONLY a JSON object with the key \"keywords\".\n"
       "- \"keywords\" is a short English keyword string for an AAC app: translate it into {lang} as bare lemma/infinitive forms, "
       "with NO negation word and NO register-marking word (no du/Sie/tu/vous/usted, no please), no added words; keep any "
       "listener-directed verb in the infinitive.\nInput: {inp}")
LEX = {"de": r"nicht|kein\w*|nie|niemals|nichts|du|dich|dir|dein\w*|sie|ihnen|ihr\w*|bitte|euch|euer|ohne",
       "es": r"no|nunca|nada|sin|tu|tus|tú|usted|ustedes|te|ti|vos|su|sus|por favor|jamás|ningún\w*|ninguna",
       "fr": r"ne|pas|jamais|rien|n|tu|te|ton|ta|tes|toi|vous|votre|vos|s'il|plaît|plait|aucun\w*|sans"}
import re
async def main():
    tr = [r for r in jl(OUT / "translations.jsonl") if r["kind"] == "REG" and r["accepted"]]
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as c:
        async def one(r):
            t = await chat2(c, sem, "mistral-nemo-12b", FWD.format(lang=LANGS[r["lang"]], inp=json.dumps({"keywords": r["bare"]})), 200)
            j = pj(t)
            kw = (j or {}).get("keywords") if isinstance(j, dict) else None
            ok = bool(kw) and isinstance(kw, str) and not [x for x in re.findall(r"[\w']+", kw.lower()) if re.fullmatch(LEX[r["lang"]], x)]
            return {"lang": r["lang"], "family_id": r["family_id"], "bare": r["bare"], "kw_terra": r["t"]["keywords"], "kw2": kw, "ok": ok, "raw": t}
        res = await asyncio.gather(*[one(r) for r in tr])
    jdump(OUT / "r2_translator2_keywords.jsonl", res)
    print(len(res), sum(r["ok"] for r in res))
    for r in res[:12]:
        print(r["lang"], r["bare"], "|", r["kw_terra"], "|", r["kw2"], r["ok"])
asyncio.run(main())
