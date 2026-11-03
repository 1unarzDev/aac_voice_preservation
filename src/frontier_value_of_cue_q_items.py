"""value_of_cue round 2 (R2-10): build (do NOT send) the q-measurement annotation items. Real stored default sentence (qwen2.5-7b P0 output) vs a real cue-restored
alternative (gpt-6.1-terra, same P0 prompt, one chip added). Draw: sha256 rank, seed 'voc2-2026-11-02'. Writes annotation/frontier_value_of_cue_{items.json,key.csv}."""
import asyncio, hashlib, json, random, re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import models as M, prompts as P
from frontier_value_of_cue_units import DIMS
U = pd.read_parquet(ROOT / "analysis/frontier/value_of_cue/units.parquet"); MODEL = "qwen2.5-7b"; SEED = "voc2-2026-11-02"
S = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); S = S[S.prompt_id.eq("P0") & S.channel.str.startswith("human_") & S.model.eq(MODEL)].rename(columns={"family_id": "fam"})
S["writer"] = S.channel.str.replace("human_", "", regex=False); S = S.set_index(["fam", "writer"])
E = {j["family_id"]: j for j in map(json.loads, open(ROOT / "data/items/elic.jsonl"))}
h = lambda *a: int(hashlib.sha256("|".join(map(str, a)).encode()).hexdigest(), 16)
DESC = {"polarity": "whether it is negated (says something is NOT so)", "speech_act": "whether it is a question or request rather than a plain statement", "politeness": "whether it uses polite wording (please, thank you, could you)"}
def chip(d, row):
    if d == "polarity": return "[NOT]"
    if d == "politeness": return "[PLEASE]"
    return "[?]" if row.src_act == "question" else "[ASK]"
sel = []
for d in ("polarity", "speech_act", "politeness"):
    A = U[(U[f"r_{d}_{MODEL}"] == 1)]; A = A.assign(k=[h(SEED, "A", d, i) for i in A.item_id]).sort_values("k").drop_duplicates("item_id").head(40)
    B = U[(U[f"pres_{d}"] == False) & (U[f"s_{d}_{MODEL}"] == 0)]; B = B.assign(k=[h(SEED, "B", d, i) for i in B.item_id]).sort_values("k").drop_duplicates("item_id").head(14)
    sel += [(r, d, "A_cue_lost") for r in A.itertuples()] + [(r, d, "B_control_no_cue_in_source") for r in B.itertuples()]
seen = set(); sel2 = []
for r, d, s in sel:
    if r.item_id in seen: continue
    seen.add(r.item_id); sel2.append((r, d, s))
async def main():
    from openai import AsyncOpenAI
    cl = AsyncOpenAI(base_url="https://codex.lunarz.dev/v1", api_key=M.api_key(), max_retries=0); sem = asyncio.Semaphore(2)
    async def alt(r, d):
        inp = E[r.fam]["custom_channels"]["A"]["human_" + r.writer]["input"]; inp2 = inp.replace("Keywords:", "Keywords: " + chip(d, r), 1)
        for a in range(8):
            try:
                async with sem:
                    x = await cl.chat.completions.create(model="gpt-6.1-terra", temperature=0, max_tokens=96, messages=[{"role": "user", "content": P.render("P0", inp2)}], timeout=120)
                return inp2, (x.choices[0].message.content or "").strip().splitlines()[0].strip().strip('"')
            except Exception as e: await asyncio.sleep(3 * 2 ** a + random.random())
        return inp2, ""
    return await asyncio.gather(*[alt(r, d) for r, d, _ in sel2])
alts = asyncio.run(main()); items = []; key = []; rg = random.Random(h(SEED, "order"))
for n, ((r, d, s), (inp2, a)) in enumerate(zip(sel2, alts)):
    dflt = S.loc[(r.fam, r.writer)].text
    if isinstance(dflt, pd.Series): dflt = dflt.iloc[0]
    flip = rg.random() < 0.5; first, second = (a, dflt) if flip else (dflt, a); iid = f"vq{n:03d}"
    items.append({"id": iid, "original": r.text, "keywords": r.kw, "sentence_A": first, "sentence_B": second, "dimension_asked": DESC[d],
                  "q1": f"Which sentence says the same thing as the original message about: {DESC[d]}? (A / B / both equally / neither)",
                  "q2": "If you had typed those keywords, which sentence would you tap to say your message? (A / B / neither)"})
    key.append(dict(id=iid, item_id=r.item_id, writer=r.writer, dimension=d, stratum=s, default_is="B" if flip else "A", alternative_is="A" if flip else "B", default_text=dflt, alternative_text=a, alt_input=inp2))
json.dump(items, open(ROOT / "annotation/frontier_value_of_cue_items.json", "w"), indent=1); pd.DataFrame(key).to_csv(ROOT / "annotation/frontier_value_of_cue_key.csv", index=False)
print(len(items), pd.DataFrame(key).groupby(["dimension", "stratum"]).size())
