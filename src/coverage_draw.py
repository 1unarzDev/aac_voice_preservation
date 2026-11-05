"""Draw the coverage-pilot items (PLAN 1.2). Seed 20261117. Writes analysis/coverage/items_draw.json (+ .sha256), prompt_shas.json,
models_used.json (probe: gpt-6.1-* preferred, fallback frozen and logged). No generation."""
from __future__ import annotations
import asyncio, csv, hashlib, json, random, sys
from collections import Counter, defaultdict
import coverage_lib as L
import prompts as P
import analyze_hw1 as H1
SEED = 20261117
W = [f"P{i:02d}" for i in range(1, 21)]
HW2W = {"P05", "P16", "P17", "P18"}


def load(p):
    return {o["family_id"]: o for o in (json.loads(l) for l in open(p))}


def inputs(it, v):
    chips = P.sort_chips(it["variants"][v]["chips"])
    return {"bare": f"Keywords: {it['bare']}", "chip": "Keywords: " + " ".join(chips + [it["bare"]]),
            "word": "Keywords: " + " ".join([L.NL[c] for c in chips] + [it["bare"]])}


def main():
    hw = load(L.ROOT / "data/items/hw.jsonl"); hw2 = load(L.ROOT / "annotation/written/hw2/hw_candidates.jsonl")
    items = {**hw, **hw2}
    seen = {r["family_id"] for r in csv.DictReader(open(L.ROOT / "annotation/intent_check_key.csv"))}
    _, comps = H1.near_dup_components(items)
    drop_dup = {f for c in comps for f in sorted(c)[1:]}
    def ok(f):
        i = items[f]
        if f in drop_dup: return False
        if any(v["critical_value"] in {"refusal", "acceptance"} for v in i["variants"].values()): return False
        if i["writer_id"] == "P06" and i["dimension"] == "speech_act": return False
        return True
    elig = {f for f in items if ok(f)}
    chosen, reserve, table = [], [], {}
    for wid in W:
        rng = random.Random(f"{SEED}|{wid}")
        own = sorted(f for f in elig if items[f]["writer_id"] == wid)
        h1 = [f for f in own if f in hw]; h2 = [f for f in own if f in hw2]
        dims = sorted({items[f]["dimension"] for f in h1})
        strata = {}
        for d in dims:
            fs = [f for f in h1 if items[f]["dimension"] == d]
            fresh = [f for f in fs if f not in seen]; old = [f for f in fs if f in seen]
            rng.shuffle(fresh); rng.shuffle(old)
            strata[d] = fresh + old    # unseen first; seen only if needed (P06)
        n = {d: (10 if len(dims) == 1 else 5) for d in dims}
        pick = {d: [] for d in dims}
        if wid in HW2W:
            for _ in range(3):
                mx = max(n.values()); cands = sorted(d for d in dims if n[d] == mx); d = cands[rng.randrange(len(cands))]
                n[d] -= 1
            sp = h2[:]; rng.shuffle(sp)
            hw2_pick = sp[:3]
        else:
            hw2_pick = []
        for d in dims:
            pick[d] = strata[d][:n[d]]
        rest = [f for d in dims for f in strata[d][n[d]:]]
        res = None
        rest = [f for f in rest if f not in seen] or rest
        if rest: res = rest[rng.randrange(len(rest))]
        # intended variant: balanced within writer-dimension
        recs = []
        groups = {d: pick[d] for d in dims}
        if hw2_pick: groups["speech_act"] = groups.get("speech_act", []) + hw2_pick
        for d, fs in groups.items():
            fs = fs[:]; start = rng.randrange(2)
            for i, f in enumerate(fs):
                recs.append((f, "AB"[(i + start) % 2], False))
        for f, v, _ in recs:
            chosen.append((f, v, wid, False))
        if res:
            reserve.append((res, "AB"[rng.randrange(2)], wid, True))
        table[wid] = Counter(items[f]["dimension"] for f, _, _ in recs)
    out = []
    for f, v, wid, rs in chosen + reserve:
        it = items[f]; o = "B" if v == "A" else "A"
        out.append({"item_id": ("rs-" if rs else "cv-") + hashlib.sha1(f"cov|{f}|{v}".encode()).hexdigest()[:6], "writer_id": wid, "family_id": f,
                    "dimension": it["dimension"], "intended": v, "reserve": rs, "seen_in_part18": f in seen, "hw2": f in hw2,
                    "A": it["variants"]["A"]["source"], "B": it["variants"]["B"]["source"], "r": it["variants"][v]["source"],
                    "intended_value": it["variants"][v]["critical_value"], "other_value": it["variants"][o]["critical_value"],
                    "values": {"A": it["variants"]["A"]["critical_value"], "B": it["variants"]["B"]["critical_value"]},
                    "bare": it["bare"], "inputs": inputs(it, v), "hw2_part16_checked": False if f in hw2 else True})
    main_items = [x for x in out if not x["reserve"]]
    summ = {"seed": SEED, "n_main": len(main_items), "n_reserve": len(out) - len(main_items),
            "by_dimension": dict(Counter(x["dimension"] for x in main_items)), "by_writer": dict(Counter(x["writer_id"] for x in main_items)),
            "intended": dict(Counter(x["intended"] for x in main_items)), "hw2_items": sum(x["hw2"] for x in main_items),
            "seen_in_part18": sum(x["seen_in_part18"] for x in main_items), "near_dup_dropped": len(drop_dup & set(items)),
            "eligible": len(elig), "per_writer_dims": {w: dict(c) for w, c in table.items()}}
    doc = {"summary": summ, "items": out}
    p = L.OUT / "items_draw.json"; txt = json.dumps(doc, indent=1, ensure_ascii=False); p.write_text(txt)
    (L.OUT / "items_draw.sha256").write_text(hashlib.sha256(txt.encode()).hexdigest() + "\n")
    print(json.dumps(summ, indent=1))
    shas = {n: hashlib.sha256((L.ROOT / "prompts" / n).read_bytes()).hexdigest() for n in sorted(x.name for x in (L.ROOT / "prompts").glob("coverage_*.txt"))}
    shas["P0"] = P.template_sha("P0")
    (L.OUT / "prompt_shas.json").write_text(json.dumps(shas, indent=1))

    # model probe
    from openai import AsyncOpenAI
    async def probe(m, **kw):
        c = AsyncOpenAI(base_url=L.M.API_BASE, api_key=L.M.api_key(), max_retries=0)
        try:
            await c.chat.completions.create(model=m, messages=[{"role": "user", "content": "Say ok"}], max_tokens=50, **kw); return True
        except Exception as e:  # noqa: BLE001
            return str(e)[:100]
    async def pr():
        g = await probe("gpt-6.1-terra", temperature=0); j = await probe("gpt-6.1-sol")
        return g, j
    g, j = asyncio.run(pr())
    mp = L.OUT / "models_used.json"
    if not mp.exists():
        mp.write_text(json.dumps({"gen": "gpt-6.1-terra" if g is True else "gpt-5.6-terra", "judge": "gpt-6.1-sol" if j is True else "gpt-6-luna",
                                  "probe_gen_gpt-6.1-terra": g, "probe_judge_gpt-6.1-sol": j}, indent=1))
    print(open(mp).read())

if __name__ == "__main__":
    main()
