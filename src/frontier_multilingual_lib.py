"""Shared helpers for the multilingual pilot (frontier multilingual). Cached async chat calls."""
from __future__ import annotations
import asyncio, hashlib, json, sys
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import models as M  # noqa: E402
OUT = ROOT / "analysis/frontier/multilingual"
RUN = ROOT / "runs/frontier_multilingual_pilot"
CACHE = RUN / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
LANGS = {"de": "German", "es": "Spanish", "fr": "French"}


def h(*p) -> str:
    return hashlib.sha256("|".join(map(str, p)).encode()).hexdigest()


def ckey(model, prompt, mt, temp):
    return h(model, mt, temp, prompt)


async def chat(client, sem, model: str, prompt: str, max_tokens=96, temp=0.0, tries=6):
    k = ckey(model, prompt, max_tokens, temp)
    f = CACHE / f"{k}.json"
    if f.exists():
        return json.loads(f.read_text())["text"]
    spec = M.get(model)
    body = {"model": spec.model, "messages": [{"role": "user", "content": prompt}],
            "temperature": temp, "max_tokens": max_tokens}
    if spec.kind == "local":
        body["seed"] = 1000
    last = None
    for i in range(tries):
        async with sem:
            try:
                r = await client.post(spec.base_url + "/chat/completions", json=body,
                                      headers=M.headers(spec), timeout=240)
                if r.status_code == 200:
                    j = r.json()
                    t = j["choices"][0]["message"].get("content") or ""
                    if model == "gpt-6.1-sol" and not t.strip() and i < tries - 1:
                        last = "empty"; continue
                    f.write_text(json.dumps({"model": model, "text": t, "finish": j["choices"][0].get("finish_reason")}))
                    return t
                last = r.status_code
            except Exception as e:  # noqa: BLE001
                last = type(e).__name__
        await asyncio.sleep(2 ** (i + 1))
    print("FAILED", model, last, file=sys.stderr)
    return None


def jl(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def jdump(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
