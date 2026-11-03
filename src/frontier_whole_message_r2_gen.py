"""Round 2 generation (frontier whole_message). Rules: PLAN.md 'ROUND 2 FREEZE RECORD'.
  python src/frontier_whole_message_r2_gen.py build            # inputs.csv (36 families x 2 variants x chip1/bare)
  python src/frontier_whole_message_r2_gen.py api <model>      # gpt-6.1-terra | gpt-5.6-luna ; arms A0 A1 A2, draws d0..d3, + A6 for terra
  python src/frontier_whole_message_r2_gen.py local <model> [port]  # llama3.1-8b via a running llama-server (caller holds flock)
Cache: runs/frontier_whole_message_r2/gen_cache.jsonl ; outputs: gens_<model>.jsonl (one row per input x arm x draw)."""
import asyncio, hashlib, json, random, sys, itertools
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models as M, prompts as P
R = ROOT / "runs/frontier_whole_message_r2"; R.mkdir(parents=True, exist_ok=True)
D = ROOT / "analysis/frontier/whole_message"
LEG = (ROOT / "prompts/chip_legend.txt").read_text().strip()
A2 = (D / "prompt_A2_minimal.txt").read_text().strip()
A6 = (D / "prompt_A6_alt.txt").read_text().strip()
ARMS = ["A0", "A1", "A2"]; DRAWS = [(0, 0.0), (1, 0.7), (2, 0.7), (3, 0.7)]
DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness", "time_quantity"]

def build():
    import analyze_hw1 as H
    items = {}
    for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
        o = json.loads(l); items[o["family_id"]] = o
    S = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
    S = S[(S.model == "gpt-6.1-terra") & (S.channel.isin(["chip1", "bare"])) & (S.prompt_id == "P0")]
    kept = set(S.family_id)
    _, comps = H.near_dup_components({f: items[f] for f in kept})
    incomp = {f: i for i, c in enumerate(comps) for f in c}
    h = lambda f: hashlib.sha256(("wm-r2|" + f).encode()).hexdigest()
    fam = pd.DataFrame(sorted(kept), columns=["family_id"]); fam["dimension"] = fam.family_id.map(lambda f: items[f]["dimension"])
    fam["comp"] = fam.family_id.map(lambda f: incomp.get(f, -1 - hash(f) % 10**9)); fam["h"] = fam.family_id.map(h)
    fam = fam.sort_values("h").drop_duplicates("comp")           # one family per near-duplicate component (lowest hash)
    sel = fam.groupby("dimension").head(6); sel = sel[sel.dimension.isin(DIMS)]
    rows = S[S.family_id.isin(sel.family_id)][["family_id", "variant", "channel", "dimension", "input_text", "text"]].rename(columns={"text": "stored_P0"})
    rows["writer_id"] = rows.family_id.map(lambda f: items[f]["writer_id"])
    rows["ref"] = [items[f]["variants"][v]["source"] for f, v in zip(rows.family_id, rows.variant)]
    rows["critical_value"] = [items[f]["variants"][v]["critical_value"] for f, v in zip(rows.family_id, rows.variant)]
    rows["other_value"] = [items[f]["variants"]["B" if v == "A" else "A"]["critical_value"] for f, v in zip(rows.family_id, rows.variant)]
    rows = rows.sort_values(["channel", "family_id", "variant"]).reset_index(drop=True)
    rows.to_csv(R / "inputs.csv", index=False)
    print(len(rows), "inputs;", rows.family_id.nunique(), "families;", rows.writer_id.nunique(), "writers;", rows.input_text.nunique(), "unique input strings")
    print(rows.drop_duplicates("family_id").groupby("dimension").size().to_dict(), rows.drop_duplicates("family_id").writer_id.value_counts().to_dict())

def prompt(arm, x, first=None):
    if arm == "A0": return P.render("P0", x)
    if arm == "A1": return P.render("P1", x)
    if arm == "A2": return A2.replace("{legend}", LEG).replace("{input}", x)
    if arm == "A6": return A6.replace("{legend}", LEG).replace("{input}", x).replace("{first}", first)
    raise ValueError(arm)

def clean(t):
    t = (t or "").strip()
    return t.splitlines()[0].strip().strip('"') if t else ""

def ckey(model, arm, draw, pr): return hashlib.sha256(json.dumps([model, arm, draw, pr]).encode()).hexdigest()

def load_cache():
    c = {}
    p = R / "gen_cache.jsonl"
    if p.exists():
        for l in p.read_text().splitlines():
            if l.strip(): o = json.loads(l); c[o["k"]] = o["t"]
    return c

async def call_api(client, sem, model, pr, temp, k, cache, fh):
    if k in cache: return cache[k]
    for att in range(8):
        try:
            async with sem:
                kw = {} if model == 'gpt-5.6-luna' else {'temperature': temp}   # luna hangs when temperature is passed: default decoding
                r = await client.chat.completions.create(model=model, max_tokens=96, messages=[{"role": "user", "content": pr}], timeout=240, **kw)
            t = clean(r.choices[0].message.content); cache[k] = t; fh.write(json.dumps({"k": k, "t": t}) + "\n"); fh.flush(); return t
        except Exception as e:  # noqa: BLE001
            print("retry", type(e).__name__, str(e)[:100], flush=True); await asyncio.sleep(min(90, 3 * 2 ** att + random.random()))
    return ""

async def call_local(client, sem, model, pr, temp, seed, k, cache, fh):
    if k in cache: return cache[k]
    async with sem:
        r = await client.post("/v1/chat/completions", json=dict(model=model, temperature=temp, max_tokens=96, seed=seed, messages=[{"role": "user", "content": pr}]), timeout=120)
    t = clean(r.json()["choices"][0]["message"]["content"]); cache[k] = t; fh.write(json.dumps({"k": k, "t": t}) + "\n"); fh.flush(); return t

async def main_api(model):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0)
    await run(model, lambda pr, temp, seed, k, c, fh, sem: call_api(client, sem, model, pr, temp, k, c, fh), 4)

async def main_local(model, port):
    import httpx
    client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}")
    await run(model, lambda pr, temp, seed, k, c, fh, sem: call_local(client, sem, model, pr, temp, seed, k, c, fh), 4)

async def run(model, caller, conc):
    inp = pd.read_csv(R / "inputs.csv", keep_default_na=False)
    cache = load_cache(); fh = (R / "gen_cache.jsonl").open("a"); sem = asyncio.Semaphore(conc)
    uni = sorted(inp.input_text.unique()); api = model.startswith("gpt")
    res = {}
    async def one(arm, d, t, x):
        pr = prompt(arm, x); k = ckey(model, arm, d, pr)
        res[(arm, d, x)] = await caller(pr, t, 4000 + d, k, cache, fh, sem)
    def dump():
        rows = []
        for _, r in inp.iterrows():
            for (arm, d, x), t in res.items():
                if x == r.input_text:
                    rows.append(dict(generator=model, arm=arm, draw=d, family_id=r.family_id, variant=r.variant, channel=r.channel, dimension=r.dimension, input_text=x, text=t))
        pd.DataFrame(rows).to_csv(R / f"gens_{model}.csv", index=False); print("dumped", len(rows), flush=True)
    # budget (logged in round2.md): API models: d0 for all arms first; terra then A6, then d1-d3 for A0 and A2 only (A1 d1-d3 skipped); luna d0 only
    await asyncio.gather(*[one(arm, 0, 0.0, x) for arm in ARMS for x in uni]); dump()
    if model == "gpt-6.1-terra":
        async def six(x):
            first = res[("A2", 0, x)]; pr = prompt("A6", x, first); k = ckey(model, "A6", 0, pr)
            res[("A6", 0, x)] = await caller(pr, 0.0, 4000, k, cache, fh, sem)
        await asyncio.gather(*[six(x) for x in uni]); dump()
    if model != "gpt-5.6-luna":
        arms = ["A0", "A2"] if api else ARMS
        for d, t in DRAWS[1:]:
            await asyncio.gather(*[one(arm, d, t, x) for arm in arms for x in uni]); dump()
    print(model, len(res), "gens;", sum(1 for v in res.values() if not v), "empty")

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "build": build()
    elif c == "api": asyncio.run(main_api(sys.argv[2]))
    else: asyncio.run(main_local(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "8092"))
