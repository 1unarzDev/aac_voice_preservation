"""Echo/reply judge (A3.1, A8). Sees only partner turn + output text. Two prompt variants (EJ1 yes|no, EJ2 no|yes), batches of 10, concurrency 3.
  python src/frontier_partner_context_echo.py --runs frontier_partner_context_r2[,frontier_partner_context_r2g]
Writes analysis/frontier/partner_context/echo_labels.jsonl (turn, text, EJ1_A, EJ1_B, EJ2_A, EJ2_B) and echo_units.json."""
import asyncio, json, re, sys, hashlib, argparse
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models, frontier_partner_context_templates2 as T
from openai import AsyncOpenAI
OUT = ROOT / "analysis/frontier/partner_context"
ap = argparse.ArgumentParser(); ap.add_argument("--runs", required=True); ap.add_argument("--limit", type=int, default=0); a = ap.parse_args()
items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
units = {}
for run in a.runs.split(","):
    df = pd.read_parquet(ROOT / "runs" / run / "scored.parquet")
    for r in df.itertuples():
        parts = r.channel.split("|"); t = parts[1]
        if t == "0": continue
        turn = items[r.family_id]["partner_turns"][t]
        cue_not = r.variant_value == "negated" and parts[0] == "chip"
        # cue [NOT] cells: chip channel with negated variant; bare/word also matter for intent-negated policy cells -> use variant_value for all kinds
        cue_not = r.variant_value == "negated"
        if r.critical == "negated" or t == "D" or cue_not:
            units[(turn, r.text)] = 1
units = sorted(units)
if a.limit: units = units[:a.limit]
print(len(units), "units")
cache_p = OUT / "echo_cache.jsonl"; cache = {}
if cache_p.exists():
    for l in open(cache_p):
        j = json.loads(l); cache[j["k"]] = j
client = AsyncOpenAI(base_url=models.API_BASE, api_key=models.api_key(), max_retries=3); sem = asyncio.Semaphore(3)
def key(v, turn, text): return hashlib.sha256(json.dumps([v, turn, text, T.sha()]).encode()).hexdigest()
async def call(v, batch):
    o1, o2 = ("yes", "no") if v == "EJ1" else ("no", "yes")
    body = ("For each numbered case, answer the two questions about the sentence.\n\n" if False else "")
    lines = []
    for i, (turn, text) in enumerate(batch, 1):
        lines.append(f"### Case {i}\n" + T.EJ.format(turn=turn, out=text, o1=o1, o2=o2))
    prompt = "Answer every case. For each case output one line exactly like `<case number>: A=<answer> B=<answer>`.\n\n" + "\n\n".join(lines)
    for k in range(6):
        try:
            async with sem:
                r = await client.chat.completions.create(model="gpt-6.1-sol", messages=[{"role": "user", "content": prompt}], reasoning_effort="low", max_tokens=1500, timeout=240)
            txt = r.choices[0].message.content or ""
            got = {int(m.group(1)): (m.group(2), m.group(3)) for m in re.finditer(r"(\d+)\s*:\s*A\s*=\s*<?(yes|no)>?\s*B\s*=\s*<?(yes|no)>?", txt, re.I)}
            if len(got) == len(batch): return got
        except Exception as e:
            print("retry", type(e).__name__, str(e)[:100], file=sys.stderr)
        await asyncio.sleep(2 ** k)
    return {}
async def main():
    todo = {v: [u for u in units if key(v, *u) not in cache] for v in ("EJ1", "EJ2")}
    async def run_batch(v, b):
        got = await call(v, b)
        with cache_p.open("a") as fh:
            for i, u in enumerate(b, 1):
                if i in got:
                    j = {"k": key(v, *u), "v": v, "turn": u[0], "text": u[1], "A": got[i][0].lower(), "B": got[i][1].lower()}; cache[j["k"]] = j; fh.write(json.dumps(j, ensure_ascii=False) + "\n")
    jobs = [run_batch(v, todo[v][i:i + 10]) for v in todo for i in range(0, len(todo[v]), 10)]
    print(len(jobs), "calls"); await asyncio.gather(*jobs)
    n_miss = 0
    with (OUT / "echo_labels.jsonl").open("w") as fh:
        for u in units:
            r = {"turn": u[0], "text": u[1]}
            for v in ("EJ1", "EJ2"):
                c = cache.get(key(v, *u))
                r[v + "_echo"] = c["A"] if c else None; r[v + "_reply"] = c["B"] if c else None
            if r["EJ1_echo"] is None or r["EJ2_echo"] is None: n_miss += 1
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("missing units", n_miss)
asyncio.run(main())
