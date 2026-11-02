"""Stage 2 pilot (API-only slice): build the pilot input set, generate A1 (P1) and A2 (minimal-expansion) for gpt-6.1-terra,
build A3 (deterministic exact-copy template), reuse A0 (stored hw1 P0). Writes runs/frontier_whole_message_s2/{outputs.jsonl,inputs.csv}."""
import asyncio, hashlib, json, re, sys, random
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models as M, prompts as P, runio
OUT = ROOT / "runs/frontier_whole_message_s2"; OUT.mkdir(parents=True, exist_ok=True)
D = ROOT / "analysis/frontier/whole_message"
A2 = (D / "prompt_A2_minimal.txt").read_text().strip()
LEG = (ROOT / "prompts/chip_legend.txt").read_text().strip()
S = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
T = S[(S.model == "gpt-6.1-terra") & (S.channel == "chip1") & (S.prompt_id == "P0")].copy()
fam = T.drop_duplicates("family_id")[["family_id", "dimension"]]
fam["h"] = fam.family_id.map(lambda f: hashlib.sha256(("wm-pilot|" + f).encode()).hexdigest())
sel = fam.sort_values("h").groupby("dimension").head(9)  # 9 per dimension x 7 = 63 families
T = T[T.family_id.isin(sel.family_id)].sort_values(["family_id", "variant"])
CHIP = {"[I]": "I", "[YOU]": "you", "[WE]": "we", "[THEY]": "they", "[NOT]": "not", "[YES]": "yes,", "[REFUSE]": "no,", "[MAYBE]": "maybe",
        "[SURE]": "definitely", "[MUST]": "must", "[WANT]": "want", "[PAST]": "already", "[NOW]": "now", "[LATER]": "later", "[PLEASE]": "please",
        "[PLAIN]": "", "[TELL]": "", "[ASK]": "can you", "[?]": ""}
def a3(x):
    s = re.sub(r"^Keywords:\s*", "", x); chips = re.findall(r"\[[^\]]+\]", s); words = " ".join(re.sub(r"\[[^\]]+\]", " ", s).split())
    pre = [CHIP.get(c, c.strip("[]")) for c in chips if c in ("[YES]", "[REFUSE]")]
    who = [CHIP[c] for c in chips if c in ("[I]", "[YOU]", "[WE]", "[THEY]")]
    mid = [CHIP.get(c, c.strip("[]")) for c in chips if c in ("[ASK]", "[MUST]", "[WANT]", "[NOT]", "[MAYBE]", "[SURE]", "[PLEASE]")]
    nums = [c.strip("[]") for c in chips if re.fullmatch(r"\[\d+\]", c)]
    tm = [CHIP[c] for c in chips if c in ("[PAST]", "[NOW]", "[LATER]")]
    t = " ".join(x_ for x_ in pre + who + mid + nums + [words] + tm if x_).strip()
    t = t[:1].upper() + t[1:]
    return t + ("?" if ("[?]" in chips or "[ASK]" in chips) else ".")
async def gen(prompt):
    from openai import AsyncOpenAI
    return prompt
async def main():
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0)
    sem = asyncio.Semaphore(4); cp = OUT / "gen_cache.jsonl"; cache = {}
    if cp.exists():
        for l in cp.read_text().splitlines(): o = json.loads(l); cache[o["k"]] = o["t"]
    fh = cp.open("a")
    async def one(arm, x):
        pr = P.render("P1", x) if arm == "A1" else A2.replace("{legend}", LEG).replace("{input}", x)
        k = hashlib.sha256((arm + pr).encode()).hexdigest()
        if k in cache: return cache[k]
        for att in range(8):
            try:
                async with sem:
                    r = await client.chat.completions.create(model="gpt-6.1-terra", temperature=0, max_tokens=96,
                                                             messages=[{"role": "user", "content": pr}], timeout=120)
                t = (r.choices[0].message.content or "").strip().splitlines()[0].strip().strip('"') if (r.choices[0].message.content or "").strip() else ""
                cache[k] = t; fh.write(json.dumps({"k": k, "t": t}) + "\n"); fh.flush(); return t
            except Exception as e:
                print("retry", type(e).__name__, str(e)[:80], flush=True); await asyncio.sleep(min(90, 3 * 2 ** att + random.random()))
        return ""
    rows = []
    jobs = [(arm, r) for _, r in T.iterrows() for arm in ("A1", "A2")]
    res = await asyncio.gather(*[one(a, r.input_text) for a, r in jobs])
    for (arm, r), t in zip(jobs, res):
        rows.append((arm, r, t))
    out = []
    for _, r in T.iterrows():
        out.append((("A0"), r, r.text)); out.append(("A3", r, a3(r.input_text)))
    out += rows
    recs = []
    for arm, r, t in out:
        oid = hashlib.sha256(f"{arm}|{r.family_id}|{r.variant}|{t}".encode()).hexdigest()[:16]
        recs.append(dict(output_id=oid, text=t, suggestion_idx=0, parse_ok=bool(t), model="gpt-6.1-terra", prompt_id=arm, temperature=0.0,
                         sample_idx=0, dimension=r.dimension, split="hw", input_text=r.input_text, family_id=r.family_id, variant=r.variant, channel="chip1"))
    runio.write_jsonl(OUT / "outputs.jsonl", recs)
    pd.DataFrame(recs).to_csv(OUT / "inputs.csv", index=False)
    print(len(recs), "outputs;", len(fam), "families; selected", sel.family_id.nunique())
if __name__ == "__main__":
    asyncio.run(main())
