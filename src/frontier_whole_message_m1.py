"""M1 rubric judge for whole-message fidelity (frontier whole_message). Prompt: analysis/frontier/whole_message/m1_prompt_v1.txt
(sha256 fe9af5fd...). One call per (variant, input, output, ref). Cache: analysis/frontier/whole_message/cache_m1.jsonl.
Judge gpt-6.1-sol effort low via codex-lb; concurrency <=3."""
from __future__ import annotations
import asyncio, hashlib, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import models as M  # noqa: E402
D = ROOT / "analysis/frontier/whole_message"
PROMPT = (D / "m1_prompt_v1.txt").read_text()
PSHA = hashlib.sha256(PROMPT.encode()).hexdigest()
CACHE = D / "cache_m1.jsonl"
MODEL = "gpt-6.1-sol"
SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["unrequested", "dropped", "frame_changed", "score_1to5"],
          "properties": {"unrequested": {"type": "array", "items": {"type": "string"}},
                         "dropped": {"type": "array", "items": {"type": "string"}},
                         "frame_changed": {"type": "boolean"},
                         "score_1to5": {"type": "integer", "enum": [1, 2, 3, 4, 5]}}}

def build(variant, x, y, r=None):
    if variant == "ref":
        d = dict(REFBLOCK=f"INTENDED SENTENCE (what the person meant): {r}\n", REFWORD="or the intended sentence",
                 DROPWORD="from the INTENDED sentence or the input", FRAMEWORD="the intended sentence", FRAMEWORD2="the intended sentence")
    else:
        d = dict(REFBLOCK="", REFWORD="", DROPWORD="from the INPUT", FRAMEWORD="what the input chips and keywords indicate",
                 FRAMEWORD2="the input supports")
    p = PROMPT
    for k, v in dict(INPUT=x, OUTPUT=y, **d).items():
        p = p.replace("{" + k + "}", v)
    return p

def key(variant, x, y, r):
    return hashlib.sha256(json.dumps([PSHA, MODEL, variant, x, y, r if variant == "ref" else None]).encode()).hexdigest()

def load():
    c = {}
    if CACHE.exists():
        for l in CACHE.read_text().splitlines():
            if l.strip():
                o = json.loads(l); c[o["key"]] = o["value"]
    return c

async def run(jobs, conc=3):
    """jobs: list of (variant, x, y, r). Returns list of result dicts aligned to jobs."""
    from openai import AsyncOpenAI
    cache = load(); fh = CACHE.open("a")
    client = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0)
    sem = asyncio.Semaphore(conc); todo = {}
    for j in jobs:
        k = key(*j)
        if k not in cache: todo[k] = j
    print(f"M1: {len(jobs)} jobs, {len(todo)} uncached", flush=True)
    done = 0
    async def one(k, j):
        nonlocal done
        for att in range(8):
            try:
                async with sem:
                    r = await client.chat.completions.create(
                        model=MODEL, reasoning_effort="low",
                        messages=[{"role": "user", "content": build(*j)}],
                        response_format={"type": "json_schema", "json_schema": {"name": "m1", "strict": True, "schema": SCHEMA}},
                        timeout=180)
                v = json.loads(r.choices[0].message.content)
                cache[k] = v; fh.write(json.dumps({"key": k, "value": v}) + "\n"); fh.flush()
                done += 1
                if done % 50 == 0: print(f"  {done}/{len(todo)}", flush=True)
                return
            except Exception as e:  # noqa: BLE001
                print("  retry", type(e).__name__, str(e)[:100], flush=True)
                await asyncio.sleep(min(120, 3 * 2 ** att + random.random()))
    await asyncio.gather(*[one(k, j) for k, j in todo.items()])
    return [cache.get(key(*j)) for j in jobs]

def wmf_fail(v):
    return bool(v["unrequested"] or v["dropped"] or v["frame_changed"])
