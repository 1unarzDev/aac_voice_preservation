"""Generate pilot outputs for one model (greedy T=0, max_tokens 96)."""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import httpx

model = sys.argv[1]
conc = int(sys.argv[2]) if len(sys.argv) > 2 else 4


async def main():
    reqs = jl(RUN / "requests.jsonl")
    sem = asyncio.Semaphore(conc)
    async with httpx.AsyncClient() as c:
        outs = await asyncio.gather(*[chat(c, sem, model, r["prompt"], 96, 0.0) for r in reqs])
    rows = [{**{k: r[k] for k in ("id", "lang", "kind", "family_id", "arm", "variant", "pset")}, "model": model, "text": (o or "").strip(), "ok": o is not None}
            for r, o in zip(reqs, outs)]
    jdump(RUN / f"gen_{model}.jsonl", rows)
    print(model, len(rows), sum(r["ok"] for r in rows))

asyncio.run(main())
