"""Round-2 helpers: cached chat with draw/seed support (reuses pilot cache for identical greedy requests)."""
from __future__ import annotations
import asyncio, json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import frontier_multilingual_lib as L1

RUN2 = ROOT / "runs/frontier_multilingual_r2"
CACHE2 = RUN2 / "cache"
CACHE2.mkdir(parents=True, exist_ok=True)
MODELS6 = ["gemma3-4b", "mistral-nemo-12b", "qwen2.5-7b", "llama3.1-8b", "qwen2.5-14b", "gpt-6.1-terra"]
L4 = {"en": "English", **LANGS}


async def chat2(client, sem, model, prompt, max_tokens=96, temp=0.0, draw=0, tries=6):
    if temp == 0.0 and draw == 0:
        f0 = L1.CACHE / f"{ckey(model, prompt, max_tokens, temp)}.json"
        if f0.exists():
            return json.loads(f0.read_text())["text"]
    k = h("r2", model, max_tokens, temp, draw, prompt)
    f = CACHE2 / f"{k}.json"
    if f.exists():
        return json.loads(f.read_text())["text"]
    spec = M.get(model)
    body = {"model": spec.model, "messages": [{"role": "user", "content": prompt}], "temperature": temp, "max_tokens": max_tokens}
    if spec.kind == "local":
        body["seed"] = 1000 if temp == 0.0 else 3000 + draw
    last = None
    for i in range(tries):
        async with sem:
            try:
                r = await client.post(spec.base_url + "/chat/completions", json=body, headers=M.headers(spec), timeout=300)
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


def pj(t):
    if not t:
        return None
    m = re.search(r"\{.*\}", t, re.S)
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None

# fixed negation monitor regexes (G1)
NEGRX = {
    "en": re.compile(r"\b(not|no|never|nothing|nobody|none|neither|nowhere|cannot)\b|n['’]t\b", re.I),
    "de": re.compile(r"\b(nicht|kein\w*|nie|niemals|nichts|nirgend\w*|weder)\b", re.I),
    "es": re.compile(r"(?<![\w])(no|nunca|nada|ningún|ninguno|ninguna|jamás|tampoco|nadie)(?![\w])", re.I),
    "fr": re.compile(r"(?<![\w])(ne|n['’]|pas|jamais|rien|aucun\w*|personne|nulle)(?![\w])", re.I),
}
