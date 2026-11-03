"""value_of_cue round 2, Stage 2: external keyword-only cue-drop detector (gpt-6.1-sol, effort low, concurrency 3). Sees keywords ONLY. PLAN.md A2 R2-6.
Writes runs/frontier_value_of_cue_s2/detector.jsonl (resumable)."""
import asyncio, json, re, sys, random
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models as M
OUT = ROOT / "runs/frontier_value_of_cue_s2"; OUT.mkdir(parents=True, exist_ok=True); fp = OUT / "detector.jsonl"
PROMPT = """An AAC user typed only these keywords to compose a sentence: "{kw}"
The keywords may have dropped parts of the intended meaning. For each item, give the probability (integer 0-100) that the sentence the user actually wanted to say has that property although the keywords do not show it:
negation: the intended sentence is negated (contains not, no, never, n't, ...)
question_or_request: the intended sentence is a question or a request/command to someone, not a plain statement
polite: the intended sentence contains polite wording (please, thank you, could you, ...)
hedged_or_emphatic: the intended sentence expresses uncertainty or strong certainty
subject_other_than_i: the intended sentence is about someone other than the speaker (not "I")
Answer with one JSON object with exactly those five keys and integer values, nothing else."""
U = pd.read_parquet(ROOT / "analysis/frontier/value_of_cue/units.parquet")
E = {j["family_id"]: j for j in map(json.loads, open(ROOT / "data/items/elic.jsonl"))}
inputs = sorted({E[r.fam]["custom_channels"]["A"]["human_" + r.writer]["input"] for r in U.itertuples()})
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else None
if LIM: inputs = inputs[:LIM]
done = set()
if fp.exists(): done = {json.loads(l)["input"] for l in fp.read_text().splitlines()}
todo = [x for x in inputs if x not in done]; print("todo", len(todo), flush=True)
async def main():
    from openai import AsyncOpenAI
    cl = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0); sem = asyncio.Semaphore(3); fh = fp.open("a"); n = [0]
    async def one(inp):
        kw = inp.replace("Keywords:", "", 1).strip()
        for att in range(10):
            try:
                async with sem:
                    r = await cl.chat.completions.create(model="gpt-6.1-sol", reasoning_effort="low", max_completion_tokens=1500, messages=[{"role": "user", "content": PROMPT.format(kw=kw)}], timeout=180)
                t = r.choices[0].message.content or ""; m = re.search(r"\{.*\}", t, re.S); j = json.loads(m.group(0))
                assert set(j) == {"negation", "question_or_request", "polite", "hedged_or_emphatic", "subject_other_than_i"}
                fh.write(json.dumps({"input": inp, **{k: float(v) for k, v in j.items()}}) + "\n"); fh.flush(); n[0] += 1
                if n[0] % 100 == 0: print(n[0], flush=True)
                return
            except Exception as e:
                print("retry", type(e).__name__, str(e)[:100], flush=True); await asyncio.sleep(min(120, 4 * 2 ** att + random.random()))
    await asyncio.gather(*[one(x) for x in todo])
asyncio.run(main())
