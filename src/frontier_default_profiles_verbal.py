"""default_profiles round 2: verbalized-confidence fallback arm (PLAN round-2 item 1/3). gpt-6.1-terra (a stored-profile model), concurrency 3, resumable.
Sees keywords ONLY (no source message). One call per unique keyword string; three probabilities 0-100.
Output: runs/frontier_default_profiles_verbal/terra.jsonl.   python src/frontier_default_profiles_verbal.py [limit]"""
import asyncio, json, re, sys, random
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models as M
OUT = ROOT / "runs/frontier_default_profiles_verbal"; OUT.mkdir(parents=True, exist_ok=True); fp = OUT / "terra.jsonl"
PROMPT = """A person who cannot speak typed only these keywords on a communication device: "{kw}"
The device has to expand them into the full message the person meant. Give the probability (integer 0-100) that the message the person meant:
negation: contains a negation or refusal (not, no, never, n't, ...)
question_or_request: is a question or a request/command, not a plain statement
polite: contains polite wording (please, thank you, sorry, softened wording)
Answer with one JSON object with exactly those three keys and integer values, nothing else."""
rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv"); msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv")
inputs = sorted({str(k).strip() for k in rat.keywords if isinstance(k, str) and k.strip()} | {str(k).strip() for k in msg.pos_cap4})
random.Random(20261102).shuffle(inputs)   # seeded order: any completed prefix is a simple random sample of unique keyword strings
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else None
if LIM: inputs = inputs[:LIM]
done = set()
if fp.exists(): done = {json.loads(l)["kw"] for l in fp.read_text().splitlines()}
todo = [x for x in inputs if x not in done]; print("todo", len(todo), flush=True)
async def main():
    from openai import AsyncOpenAI
    cl = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0); sem = asyncio.Semaphore(3); fh = fp.open("a"); n = [0]
    async def one(kw):
        for att in range(10):
            try:
                async with sem:
                    r = await cl.chat.completions.create(model="gpt-6.1-terra", max_completion_tokens=200, temperature=0, messages=[{"role": "user", "content": PROMPT.format(kw=kw)}], timeout=60)
                t = r.choices[0].message.content or ""; j = json.loads(re.search(r"\{.*\}", t, re.S).group(0))
                assert set(j) == {"negation", "question_or_request", "polite"}
                fh.write(json.dumps({"kw": kw, **{k: float(v) for k, v in j.items()}}) + "\n"); fh.flush(); n[0] += 1
                if n[0] % 200 == 0: print(n[0], flush=True)
                return
            except Exception as e:
                print("retry", type(e).__name__, str(e)[:100], flush=True); await asyncio.sleep(min(120, 3 * 2 ** att + random.random()))
    for i in range(0, len(todo), 12): await asyncio.gather(*[one(x) for x in todo[i:i + 12]])   # chunks keep completion order ~ shuffled order
asyncio.run(main())
