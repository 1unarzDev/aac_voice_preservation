"""E10 acceptability proxy: blind sol naturalness 1-5 (target language) on unique greedy outputs of POL (bare/restored B/plain_neg) and REG (bare/chip/plain)."""
import asyncio, sys, json, re, glob, collections
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
NAT = ("Rate how natural and fluent each numbered {lang} sentence is as something a native speaker would say (1 = unnatural or ungrammatical, 5 = fully natural). "
       "Return ONLY a JSON list of integers, one per sentence.\n{items}")
B = 15
ARMS = {("POL", "bare"), ("POL", "restored"), ("POL", "plain_neg"), ("REG", "bare"), ("REG", "chip_formal"), ("REG", "chip_informal"), ("REG", "plain_formal"), ("REG", "plain_informal")}
def num(i, xs): return "\n".join(f"{k+1}. {x}" for k, x in enumerate(xs))
async def main():
    rows = []
    for f in glob.glob(str(RUN2 / "gen_*.jsonl")):
        rows += [r for r in jl(f) if r["text"] and r["temp"] == 0.0 and r["pset"] == "L" and (r["kind"], r["arm"]) in ARMS and not (r["arm"] == "restored" and r["variant"] == "A")]
    sem = asyncio.Semaphore(3); score = {}
    async with httpx.AsyncClient() as c:
        for lang in ["en"] + list(LANGS):
            texts = sorted({r["text"] for r in rows if r["lang"] == lang})
            chunks = [texts[i:i + B] for i in range(0, len(texts), B)]
            async def one(ch):
                for att in range(3):
                    t = await chat2(c, sem, "gpt-6.1-sol", NAT.format(lang=L4[lang], items=num(0, ch)) + " " * att, 3000)
                    m = re.search(r"\[.*\]", t or "", re.S)
                    try:
                        v = json.loads(m.group(0))
                        if len(v) == len(ch): return dict(zip(ch, v))
                    except Exception: pass
                return {}
            for d in await asyncio.gather(*[one(ch) for ch in chunks]):
                for k, v in d.items(): score[f"{lang}|{k}"] = v
            print("nat", lang, len(texts), flush=True)
    json.dump(score, open(OUT / "r2_naturalness.json", "w"), ensure_ascii=False)
    res = {}
    for lang in ["en"] + list(LANGS):
        by = collections.defaultdict(list)
        for r in rows:
            s = score.get(f"{r['lang']}|{r['text']}")
            if r["lang"] == lang and isinstance(s, (int, float)):
                by[(r["kind"], r["arm"], r["variant"] if r["arm"] == "restored" else "")].append((r["family_id"], s))
        for k, v in by.items():
            res[f"{lang}|{k[0]}|{k[1]}"] = {"mean": float(np.mean([s for _, s in v])), "n": len(v)}
    # paired cluster bootstrap: restored B minus bare, chip - bare per (family): mean over models
    rng = np.random.default_rng(20261102)
    def fam_mean(lang, kind, arm, variant=None):
        d = collections.defaultdict(list)
        for r in rows:
            if r["lang"] == lang and r["kind"] == kind and r["arm"] == arm and (variant is None or r["variant"] == variant):
                s = score.get(f"{lang}|{r['text']}")
                if isinstance(s, (int, float)): d[r["family_id"]].append(s)
        return {f: np.mean(v) for f, v in d.items()}
    paired = {}
    for lang in ["en"] + list(LANGS):
        for kind, a, b, va in (("POL", "restored", "bare", "B"), ("POL", "plain_neg", "bare", None), ("REG", "chip_formal", "bare", None), ("REG", "chip_informal", "bare", None), ("REG", "plain_formal", "bare", None)):
            x, y = fam_mean(lang, kind, a, va), fam_mean(lang, kind, b)
            fs = sorted(set(x) & set(y))
            if len(fs) < 5: continue
            dd = np.array([x[f] - y[f] for f in fs]); bs = [dd[rng.integers(0, len(dd), len(dd))].mean() for _ in range(5000)]
            paired[f"{lang}|{kind}|{a}-{b}"] = {"diff": float(dd.mean()), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "n_fam": len(fs)}
    json.dump({"means": res, "paired": paired}, open(OUT / "r2_naturalness_summary.json", "w"), indent=1)
    print(json.dumps(paired, indent=1))
asyncio.run(main())
