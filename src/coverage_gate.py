"""Proxy validity gate (PLAN section 3): judge the 195 usable Part 18 outputs with the coverage judge and compare with writers.
usage: python coverage_gate.py train   (judge + report P01-P10 only; prompt may be revised on this part only)
       python coverage_gate.py final   (judge P11-P20, apply the frozen cutoff, write proxy_validity.json; run once)"""
from __future__ import annotations
import asyncio, json, sys
import numpy as np, pandas as pd
import coverage_lib as L, coverage_judge as J
SEED = 20261117
ev = {"yes": 1.0, "partly": 0.5, "no": 0.0}

def load():
    d = pd.read_csv(L.ROOT / "analysis/intent_check/items.csv")
    d = d[d.rated.astype(str).str.lower().eq("true") & d.says.notna()].copy()
    d["match"] = (d.says == "version " + d.intended_variant).astype(int)
    d["accept_ok"] = d.accept.isin(["yes", "with a small edit"]).astype(int)
    return d

def score(row, r):
    s = 0.0
    iv = row.intended_variant
    val = r["value"]; e = r["event_" + iv]
    return (1.0 + ev[e]) if val == row.intended_value else 0.0

def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s, float)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0: return float("nan")
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg)))

def kappa(a, b):
    a = np.asarray(a); b = np.asarray(b); po = (a == b).mean()
    pe = sum(((a == k).mean() * (b == k).mean()) for k in (0, 1))
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")

async def run(df):
    m = L.resolve_models(); chat = L.Chat("judge", 3)
    res = await asyncio.gather(*[J.judge(chat, m["judge"], r.text, r.version_A, r.version_B, r.dimension) for r in df.itertuples()])
    return res

def cluster_boot(df, fn, B=2000, seed=SEED):
    rng = np.random.default_rng(seed); ws = sorted(df.writer_id.unique()); g = {w: df[df.writer_id == w] for w in ws}; out = []
    for _ in range(B):
        s = pd.concat([g[w] for w in rng.choice(ws, len(ws))])
        v = fn(s)
        if v == v: out.append(v)
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]

def main(mode):
    d = load(); tr = d[d.writer_id <= "P10"].copy(); ho = d[d.writer_id > "P10"].copy()
    part = tr if mode == "train" else d
    res = asyncio.run(run(part)); part = part.assign(res=res)
    bad = sum(r is None for r in res); print("judge failures:", bad)
    part = part[part.res.notna()].copy()
    part["score"] = [score(r, r.res) for r in part.itertuples()]
    part["words"] = part.text.str.split().str.len()
    t = part[part.writer_id <= "P10"]
    print("train n", len(t), "match rate", t.match.mean().round(3), "AUROC", round(auroc(t.match, t.score), 3))
    best = max((kappa(t.match, (t.score >= c).astype(int)), c) for c in (1.0, 1.5, 2.0)); print("train best kappa/cutoff", best)
    print(t.groupby("score").match.agg(["mean", "size"]))
    part.drop(columns=["res"]).assign(**{k: [r[k] for r in part.res] for k in ("value", "event_A", "event_B")}).to_csv(L.OUT / f"gate_{mode}.csv", index=False)
    if mode == "train": return
    cut = best[1]; h = part[part.writer_id > "P10"].copy()
    h["pred"] = (h.score >= cut).astype(int)
    # orientation of word count frozen on train: fewer words -> more likely match iff train AUROC(-words) >= .5
    sgn = -1 if auroc(t.match, -t.words) >= 0.5 else 1
    h["wscore"] = sgn * h.words
    a = auroc(h.match, h.score); ci = cluster_boot(h, lambda s: auroc(s.match, s.score))
    k = kappa(h.match, h.pred); kci = cluster_boot(h, lambda s: kappa(s.match, s.pred))
    aw = auroc(h.match, h.wscore)
    dci = cluster_boot(h, lambda s: auroc(s.match, s.score) - auroc(s.match, s.wscore))
    # sanity: identical sentence covers itself; unrelated does not
    sa = asyncio.run(sanity(h))
    out = {"n_train": int(len(t)), "n_holdout": int(len(h)), "frozen_cutoff": cut, "holdout_match_rate": float(h.match.mean()),
           "auroc": a, "auroc_cluster_ci": ci, "kappa": k, "kappa_cluster_ci": kci, "word_count_auroc": aw, "word_orientation": int(sgn),
           "auroc_gain_over_words": a - aw, "gain_cluster_ci": dci, "sanity": sa,
           "train_auroc": auroc(t.match, t.score),
           "gate_a": bool(a >= .80 and ci[0] >= .70), "gate_b": bool(k >= .50), "gate_c": bool(dci[0] > 0), "gate_d": bool(sa["pass"])}
    out["pass"] = bool(out["gate_a"] and out["gate_b"] and out["gate_c"] and out["gate_d"])
    # secondary: agreement with accept-ok among holdout
    out["auroc_vs_accept_ok"] = auroc(h.accept_ok, h.score)
    (L.OUT / "proxy_validity.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))

async def sanity(h):
    m = L.resolve_models(); chat = L.Chat("judge", 3); sub = h.iloc[:20]
    selfc = await asyncio.gather(*[J.judge(chat, m["judge"], r.version_A if r.intended_variant == "A" else r.version_B, r.version_A, r.version_B, r.dimension) for r in sub.itertuples()])
    unrel = await asyncio.gather(*[J.judge(chat, m["judge"], "The purple elephant sings loudly on the roof.", r.version_A, r.version_B, r.dimension) for r in sub.itertuples()])
    sc = np.mean([score(r, x) >= 2.0 for r, x in zip(sub.itertuples(), selfc) if x]); uc = np.mean([score(r, x) >= 2.0 for r, x in zip(sub.itertuples(), unrel) if x])
    return {"self_covers": float(sc), "unrelated_covers": float(uc), "pass": bool(sc >= .95 and uc <= .05)}

if __name__ == "__main__":
    main(sys.argv[1])
