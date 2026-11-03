"""Round-2 generation for one model: phase 1 = all requests (greedy + sampled), phase 2 = G1 with written cue (monitor regex/detector, <=2 retries).
usage: python frontier_multilingual_r2_gen.py <model> [conc]"""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
from frontier_multilingual_register import label as det

model = sys.argv[1]
conc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
FB_POL = {"en": "The sentence must be negated (the user's cue says NOT), but it is not.", "de": "Der Satz muss verneint sein (der Hinweis des Nutzers lautet NICHT), ist es aber nicht.",
          "es": "La oración debe ser negativa (la señal del usuario es NO), pero no lo es.", "fr": "La phrase doit être négative (l'indication de l'utilisateur est NE PAS), mais elle ne l'est pas."}
FB_REG = {"V": "The sentence must address the listener formally (Sie / usted / vous), but it uses the wrong register.",
          "T": "The sentence must address the listener informally (du / tú / tu), but it uses the wrong register."}
FIX = "\n\nA previous attempt wrote: \"{prev}\"\n{fb} Write the corrected sentence. Output only the sentence."


async def main():
    reqs = jl(RUN2 / "requests.jsonl")
    sem = asyncio.Semaphore(conc)
    async with httpx.AsyncClient() as c:
        outs = await asyncio.gather(*[chat2(c, sem, model, r["prompt"], 96, r["temp"], r["draw"]) for r in reqs])
        rows = [{**{k: r[k] for k in ("id", "lang", "kind", "family_id", "arm", "variant", "pset", "temp", "draw")}, "model": model, "text": (o or "").strip(), "ok": o is not None}
                for r, o in zip(reqs, outs)]
        jdump(RUN2 / f"gen_{model}.jsonl", rows)
        print(model, "phase1", len(rows), sum(r["ok"] for r in rows), flush=True)
        # phase 2: G1 with written cue on greedy bare (P0-L) outputs
        byid = {(r["lang"], r["family_id"], r["arm"], r["pset"], r["temp"]): (q, r) for q, r in zip(reqs, rows)}
        jobs = []
        for q, r in zip(reqs, rows):
            if q["pset"] != "L" or q["arm"] != "bare" or q["temp"] != 0.0 or not r["ok"]:
                continue
            if q["kind"] == "POL":
                jobs.append((q, r, "neg"))
            elif q["lang"] != "en":
                jobs += [(q, r, "V"), (q, r, "T")]

        async def g1(q, r, need):
            lang, text, tries, hist = q["lang"], r["text"], 0, []
            def bad(t):
                if need == "neg":
                    return not NEGRX[lang].search(t)
                lab = det(lang, t)
                return lab in ("T", "V", "mixed") and lab != need
            while bad(text) and tries < 2:
                fb = FB_POL[lang] if need == "neg" else FB_REG[need]
                o = await chat2(c, sem, model, q["prompt"] + FIX.format(prev=text, fb=fb), 96, 0.0, 0)
                if o is None:
                    break
                hist.append(text); text = o.strip(); tries += 1
            return {"lang": lang, "kind": q["kind"], "family_id": q["family_id"], "model": model, "need": need, "orig": r["text"], "text": text, "retries": tries, "still_bad": bad(text)}
        g = await asyncio.gather(*[g1(*j) for j in jobs])
        jdump(RUN2 / f"g1_{model}.jsonl", g)
        print(model, "G1", len(g), "retried", sum(x["retries"] > 0 for x in g), flush=True)

asyncio.run(main())
