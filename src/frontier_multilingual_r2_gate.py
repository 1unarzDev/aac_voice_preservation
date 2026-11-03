"""E8 strict translation gate: full-word overlap (>=0.5) under BOTH back-translators + polarity preserved under both (sol classifier)."""
import asyncio, sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx
POLQ = ("Is the following English sentence negated (contains a negation of the main statement) or affirmative? Answer with one word: negated or affirmative.\nSentence: {s}")
def norm(w):
    w = w.lower()
    for s in ("ing", "es", "s"):
        if w.endswith(s) and len(w) > len(s) + 2: return w[:-len(s)]
    return w
def overlap(en, back):
    stop = {"to", "a", "the", "of", "and", "be"}
    e = [norm(t) for t in re.findall(r"[a-z]+", en.lower()) if t not in stop]; b = {norm(t) for t in re.findall(r"[a-z]+", back.lower()) if t not in stop}
    return sum(x in b for x in e) / len(e) if e else 0.0
async def main():
    tr = jl(OUT / "translations.jsonl"); BM = "qwen2.5-14b" if (OUT / "r2_backtrans2_qwen2.5-14b.jsonl").exists() else "gpt-6.1-terra"
    b2 = {(r["lang"], r["family_id"]): r["back2"] for r in jl(OUT / f"r2_backtrans2_{BM}.jsonl")}
    sem = asyncio.Semaphore(3)
    async with httpx.AsyncClient() as c:
        async def one(r):
            if not r.get("t") or not r.get("back"): return {"lang": r["lang"], "kind": r["kind"], "family_id": r["family_id"], "strict": False, "why": ["missing"], "loose": False}
            q = b2.get((r["lang"], r["family_id"])); why = []
            if not q: return {"lang": r["lang"], "kind": r["kind"], "family_id": r["family_id"], "strict": False, "why": ["no_back2"], "loose": r["accepted"]}
            o1 = overlap(r["bare"], r["back"].get("keywords", "")); o2 = overlap(r["bare"], q.get("keywords", ""))
            if o1 < .5: why.append("overlap_sol")
            if o2 < .5: why.append("overlap_back2")
            if r["kind"] == "POL":
                for k, want in (("A", "affirmative"), ("B", "negated")):
                    x = (await chat2(c, sem, "gpt-6.1-sol", POLQ.format(s=q.get(k, "")), 2000) or "").strip().lower()
                    got = "negated" if x.startswith("neg") else "affirmative" if x.startswith("aff") else "?"
                    if got != want: why.append(f"pol_{k}_back2")
                    if (r.get("back_pol") or {}).get(k) != want: why.append(f"pol_{k}_sol")
            return {"lang": r["lang"], "kind": r["kind"], "family_id": r["family_id"], "strict": not why, "why": why, "loose": r["accepted"], "ov_sol": o1, "ov_back2": o2}
        res = await asyncio.gather(*[one(r) for r in tr])
    surv = {}
    for l in LANGS:
        for k in ("POL", "REG"):
            x = [r for r in res if r["lang"] == l and r["kind"] == k]
            surv[f"{l}|{k}"] = {"n": len(x), "pilot_gate": sum(r["loose"] for r in x), "strict_gate": sum(r["strict"] for r in x)}
        x = [r for r in res if r["lang"] == l]
        surv[f"{l}|all"] = {"n": len(x), "pilot_gate": sum(r["loose"] for r in x), "strict_gate": sum(r["strict"] for r in x), "strict_rate": sum(r["strict"] for r in x) / len(x)}
    json.dump({"second_back_translator": BM, "survival": surv, "rows": res}, open(OUT / "r2_strict_gate.json", "w"), indent=1)
    print(json.dumps(surv, indent=1))
asyncio.run(main())
