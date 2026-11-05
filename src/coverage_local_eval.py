"""Machine proxy for the two local replication models (plain-generation arms only: G1 bare/chip, W1 word, D3s, D5s from T=1.0 samples).
Reads runs/cache/<request_key>.json for runs/requests/coverage_local.jsonl; judges with the same coverage judge; writes
analysis/coverage/local_replication.csv. Arms that need an LLM selector or edit calls (C/E/R/D-p) are not run on local models."""
from __future__ import annotations
import asyncio, json, sys
import numpy as np, pandas as pd
import coverage_lib as L, coverage_judge as J
import generate as G
import coverage_analyze as CA


def texts_for(models=("qwen2.5-14b", "llama3.1-8b")):
    reqs = [json.loads(l) for l in open(L.ROOT / "runs/requests/coverage_local.jsonl")]
    out = {}
    for r in reqs:
        p = L.ROOT / "runs/cache" / f"{r['request_key']}.json"
        if not p.exists():
            continue
        t = G.clean_one((json.loads(p.read_text()).get("raw_text") or "").strip().splitlines()[0] if (json.loads(p.read_text()).get("raw_text") or "").strip() else "")
        for tg in r["targets"]:
            out.setdefault((r["model"], tg["item_id"], tg["cond"]), {})[(r["temperature"], r["sample_idx"])] = t
    return out


async def main():
    items = {x["item_id"]: x for x in json.load(open(L.OUT / "items_draw.json"))["items"] if not x["reserve"]}
    tx = texts_for(); m = L.resolve_models(); chat = L.Chat("judge", 3)
    rows = []; todo = {}
    for (model, iid, cond), d in tx.items():
        g = d.get((0.0, 0))
        if g is None:
            continue
        smp = [d[k] for k in sorted(d) if k[0] == 1.0]
        seen = {L.norm(g)}; dist = []
        for t in smp:
            if L.norm(t) and L.norm(t) not in seen:
                seen.add(L.norm(t)); dist.append(t)
        arms = {"W1" if cond == "word" else "G1": [g]}
        if cond != "word":
            arms["D3s"] = [g] + dist[:2]; arms["D5s"] = [g] + dist[:4]
        for a, ts in arms.items():
            rows.append((model, iid, cond, a, ts))
            for t in ts:
                todo[(iid, t)] = 1
    async def one(k):
        it = items[k[0]]; return k, await J.judge(chat, m["judge"], k[1], it["A"], it["B"], it["dimension"])
    res = dict(await asyncio.gather(*[one(k) for k in todo]))
    recs = []
    for model, iid, cond, a, ts in rows:
        it = items[iid]; cov = [CA.judge_cov(it, {"judge": {"": res[(iid, t)]}}) if res.get((iid, t)) else {"A": False, "B": False, "val": None} for t in ts]
        recs.append(dict(model=model, item_id=iid, writer_id=it["writer_id"], cond=cond, arm=a, k=len(ts), covered=int(any(c[it["intended"]] for c in cov)),
                         wrong_first=int(cov[0]["val"] == it["other_value"]), short=int(len(ts) < {"G1": 1, "W1": 1, "D3s": 3, "D5s": 5}[a])))
    df = pd.DataFrame(recs); df.to_csv(L.OUT / "local_replication_items.csv", index=False)
    out = []
    for (mo, cond, a), x in df.groupby(["model", "cond", "arm"]):
        ci = CA.boot_mean(x.covered.values, x.writer_id.values, 2000)
        out.append(dict(model=mo, cond=cond, arm=a, n=len(x), coverage=x.covered.mean(), ci_lo=ci[0], ci_hi=ci[1], wrong_first=x.wrong_first.mean(), short_rate=x.short.mean()))
    o = pd.DataFrame(out); o.to_csv(L.OUT / "local_replication.csv", index=False); print(o.round(3).to_string())

if __name__ == "__main__":
    asyncio.run(main())
