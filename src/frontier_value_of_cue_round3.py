"""value_of_cue round 3 (PLAN.md A5, written before outcomes). CPU only. Strict S1, stored-label P-O, supervised B6, G1-after-ask, refit bootstrap,
q sweep 0.3-1.0, false-alarm / mis-pick / spurious sensitivity, primary vs five-dimension scope, per-writer, per-model H2. PROVISIONAL (machine labels, simulated q, rho).
Usage: python src/frontier_value_of_cue_round3.py [NB_fixed=300] [NB_refit=200]   (env VOC_LOCALS=qwen2.5-7b,llama3.1-8b[,gemma3-4b])"""
import json, os, sys, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frontier_value_of_cue_lib import *
import frontier_value_of_cue_lib as L
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 300; NR = int(sys.argv[2]) if len(sys.argv) > 2 else 200
R2 = OUT / "round2"; R3 = OUT / "round3"; R3.mkdir(exist_ok=True)
LOCAL = os.environ.get("VOC_LOCALS", "qwen2.5-7b,llama3.1-8b").split(","); PD3 = ["polarity", "speech_act", "politeness"]; BUD = [20, 50, 100, 200, 400]
WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]; G1R = 0.525; RHOG3 = RHO3 + (1 - RHO3) * G1R; RHOG5 = RHO5 + (1 - RHO5) * G1R
t0 = time.time(); log = lambda *a: print(round(time.time() - t0), "s", *a, flush=True)

# ------------------------------------------------------------------ features
_F = np.array([feats(k) for k in U.kw], float)
S1_STRICT = zs(np.delete(_F, [3, 4, 5, 6, 7, 8, 9, 16], axis=1)); S1_NL = XS1_NOLEX
F = {m: pd.read_parquet(R2 / f"features_{m}.parquet") for m in LOCAL}
def s3cols(df): return [c for c in df.columns if c.startswith(("g_", "s_freq", "s_ent", "p_logit", "jH")) and df[c].dtype != object]
B6COLS = ["jH"] + [f"s_{k}_{d}" for k in ("freq", "ent", "minor") for d in PD3]
rawS = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); rawS = rawS[rawS.prompt_id.eq("P0") & rawS.channel.str.startswith("human_")].rename(columns={"family_id": "fam"}); rawS["writer"] = rawS.channel.str.replace("human_", "", regex=False)
def stored(m):
    o = rawS[rawS.model.eq(m)].set_index(["fam", "writer"]).reindex(pd.MultiIndex.from_frame(U[["fam", "writer"]]))
    return np.stack([o.polarity.eq("negated").to_numpy(float), (~o.speech_act.eq("statement")).to_numpy(float), o.politeness.ne("none").to_numpy(float)], 1)
ST = {m: stored(m) for m in LOCAL}; assert all(np.isfinite(ST[m]).all() for m in LOCAL)
XSETS = {}; YSC = {}
for sc in LOCAL + ["pooled"]:
    ms = LOCAL if sc == "pooled" else [sc]
    s3 = zs(np.mean([F[m][s3cols(F[m])].to_numpy(float) for m in ms], 0)); b6 = zs(np.mean([F[m][B6COLS].to_numpy(float) for m in ms], 0))
    so = zs(np.mean([ST[m] for m in ms], 0)); sr = zs(np.mean([F[m][["o_polarity", "o_speech_act", "o_politeness"]].to_numpy(float) for m in ms], 0))
    XSETS[sc] = {"P-K": S1_STRICT, "P-K-noLex": S1_NL, "P-O": np.c_[S1_STRICT, so], "P-O-regen": np.c_[S1_STRICT, sr], "P-I": np.c_[S1_STRICT, s3], "P-IO": np.c_[S1_STRICT, s3, so],
                 "B6-sup": b6, "B6-sup+S1": np.c_[S1_STRICT, b6]}
    YSC[sc] = outcome("r", model=sc if sc != "pooled" else None)
    if sc != "pooled": XSETS[sc] = {k: XSETS[sc][k] for k in ("P-K", "P-I", "P-O")}
# round-2 noLex P-I (pooled) reused for the "both S1 variants" comparison
z2 = np.load(R2 / "signals_P.npz"); PNL_I = np.stack([z2[f"pooled|P-I|{d}"] for d in range(3)], 1) if all(f"pooled|P-I|{d}" in z2.files for d in range(3)) else None
Y5 = YSC["pooled"]; Y3 = Y5[:, PRIM]; S3o = outcome("s")[:, PRIM]

# ------------------------------------------------------------------ cross-fitted predictions (cached)
def job(a): sc, k, d = a; return a, oof(XSETS[sc][k], YSC[sc][:, d])
cache = R3 / "P_r3.npz"
jobs = [(sc, k, d) for sc in XSETS for k in XSETS[sc] for d in (range(5) if sc == "pooled" and k in ("P-K", "P-O", "P-I") else range(3))]
old = {tuple(k.split("|")): v for k, v in np.load(cache).items()} if cache.exists() else {}
todo = [j for j in jobs if (j[0], j[1], str(j[2])) not in old]
if todo:
    with Pool(14) as p: out = p.map(job, todo)
    for (sc, k, d), v in out: old[(sc, k, str(d))] = v
    np.savez(cache, **{"|".join(k): v for k, v in old.items()})
log("fits done", len(todo), "new")
def Pm(sc, k, nd=3): return np.stack([old[(sc, k, str(d))] for d in range(nd)], 1)
P = {sc: {k: Pm(sc, k) for k in XSETS[sc]} for sc in XSETS}
if PNL_I is not None: P["pooled"]["P-I-noLex"] = PNL_I
P["pooled"]["P-K-noLex"] = np.load(R2 / "P_noLex_prim.npy")
boot = Boot(NB); log("boot drawn")
def prior(Y, wb=w): return np.array([(wb * Y[:, d]).sum() / wb.sum() for d in range(Y.shape[1])])
def ci(res, g):
    lo, hi = [], []
    for m, rs in res.items(): a, b = np.percentile([g(r) for r in rs], [2.5, 97.5]); lo.append(a); hi.append(b)
    return min(lo), max(hi)

# ------------------------------------------------------------------ policies
def policy3(Pp, wv, q, rho, Yr, actions="both"):
    """as lib.policy but also returns chosen dimension, action flag, expected lost prob y on chosen dim"""
    D = Pp.shape[1]; B = np.full((n, 2 * D), -1e9); tp = np.r_[np.ones(D), 2 * np.ones(D)]
    for d in range(D):
        if actions in ("both", "show"): B[:, d] = wv[d] * Pp[:, d] * q
        if actions in ("both", "ask"): B[:, D + d] = wv[d] * Pp[:, d] * rho[d]
    net = B[None] - LAM[:, None, None] * tp[None, None]; k = net.argmax(2); act = np.take_along_axis(net, k[..., None], 2)[..., 0] > 0
    d = k % D; isask = k >= D; eff = np.where(isask, rho[d], q); idx = np.arange(n)[None]; y = Yr[idx, d]
    return dict(T=np.where(act, np.where(isask, 2, 1), 0).astype(float), G=np.where(act, wv[d] * y * eff, 0), R=np.where(act, y * eff, 0), ask=isask & act, show=(~isask) & act, d=d, act=act, y=y, wv=wv)
def b6_gate_ask(score, dsel, wv, rho, Yr, seed=7):
    jit = np.random.default_rng(seed).uniform(0, 1e-9, n); o = np.argsort(-(score + jit)); rank = np.empty(n); rank[o] = np.arange(n) / n
    act = rank[None] < np.linspace(0, 1, 401)[:, None]; idx = np.arange(n); y = Yr[idx, dsel]
    return dict(T=act * 2.0, G=act * (wv[dsel] * y * rho[dsel])[None], R=act * (y * rho[dsel])[None])
def fixed_dict(wv, Yr, q, rho, pr, kind):
    """B5 (best fixed prompt by prior) or B1 (random dim, SHOW) as ladder dicts with per-message false-alarm / mispick bases"""
    if kind == "B5":
        c, (a, dn) = b5_curves(wv, q, rho, Yr, pr); d = DIMS.index(dn); e = q if a == "S" else rho[d]; tp = 1 if a == "S" else 2
        g, r, fa, mp = wv[d] * Yr[:, d] * e, Yr[:, d] * e, 1 - Yr[:, d], (wv[d] * (1 - Yr[:, d]) if a == "S" else 0 * Yr[:, d])
    else:
        tp = 1; g, r, fa, mp = (wv * Yr * q).mean(1), (Yr * q).mean(1), (1 - Yr).mean(1), (wv * (1 - Yr)).mean(1)
    gr = np.linspace(0, 1, 401)[:, None]
    return dict(T=gr * np.full(n, float(tp))[None], G=gr * g[None], R=gr * r[None], FA=gr * fa[None], MP=gr * mp[None])
def with_cost(c, a, m):
    """effective-tap / net-gain version of a ladder dict (a = false-alarm tap-equivalents, m = mispick probability)"""
    if "FA" in c: FA, MP = c["FA"], c["MP"]
    else: FA = c["act"] * (1 - c["y"]); MP = c["act"] * (~c["ask"]) * c["wv"][c["d"]] * (1 - c["y"])
    return dict(T=c["T"] + a * FA, G=c["G"] - m * MP, R=c["R"])
def build(Pd, wv, q, rho, Yr, pr, sc, dims_n, extra=True):
    pols = {k: policy3(v, wv, q, rho, Yr) for k, v in Pd.items()}
    pols["Oracle"] = policy3(Yr, wv, q, rho, Yr); pols["B5"] = fixed_dict(wv, Yr, q, rho, pr, "B5"); pols["B1"] = fixed_dict(wv, Yr, q, rho, pr, "B1")
    if extra:
        ms = LOCAL if sc == "pooled" else [sc]; H = np.mean([F[m].jH.to_numpy(float) for m in ms], 0); MN = np.stack([np.mean([F[m][f"s_minor_{d}"].to_numpy(float) for m in ms], 0) for d in PD3], 1)
        pols["B6"] = gated_policy(H, MN.argmax(1), wv, q, Yr); pols["B6-w"] = gated_policy(H, (MN * wv).argmax(1), wv, q, Yr)
        pols["B6 ASK+G1"] = b6_gate_ask(H, MN.argmax(1), wv, RHOG3, Yr)
        for k in ("P-I", "P-K", "P-O"):
            if k in Pd: pols[f"{k} ASK+G1"] = policy3(Pd[k], wv, q, RHOG3, Yr, "ask")
    return pols
def evalp(pols, wb, Bs, ks): return {k: {B: v[0] for B, v in at_budgets(pols[k], wb, Bs).items()} for k in ks}

# ================================================================== 1. main frontier, pooled, primary scope, all policies
pr3 = prior(Y3); pols = build(P["pooled"], WV3, Q0, RHO3, Y3, pr3, "pooled", 3)
ALLK = list(pols); B0 = b0(Y3, WV3, w); B0raw = 1000 * (Y3.sum(1) @ w) / w.sum(); log("B0", B0, B0raw)
pt = {k: at_budgets(pols[k], w, BUD) for k in ALLK}
res = {m: [dict(b0=b0(Y3, WV3, wb), **evalp(pols, wb, BUD, ALLK)) for wb in ws] for m, ws in boot.draws.items()}; log("fixed boot")
DIFFS = [("P-I", "P-O"), ("P-IO", "P-O"), ("P-O", "P-O-regen"), ("P-O", "B5"), ("P-I", "B5"), ("P-K", "B5"), ("P-K", "B1"), ("P-I", "P-K"), ("P-O", "P-K"), ("P-K-noLex", "B5"), ("P-I-noLex", "B5"), ("P-I", "P-I-noLex"),
         ("P-K", "P-K-noLex"), ("P-I", "B6-sup"), ("P-I", "B6-sup+S1"), ("B6-sup", "B5"), ("B6-sup+S1", "P-K"), ("P-I", "B6"), ("P-K", "B6"), ("B6", "B5"), ("B6", "B1"), ("P-I ASK+G1", "P-I"), ("P-I ASK+G1", "B6 ASK+G1"), ("P-I", "B6 ASK+G1"), ("P-K ASK+G1", "B6 ASK+G1"), ("P-O", "B1"), ("P-I", "B1")]
rows = []
for B in BUD:
    for k in ALLK:
        g, r = pt[k][B]; lo, hi = ci(res, lambda x: x[k][B] / x["b0"])
        rows.append(dict(budget=B, policy=k, B0_weighted=B0, B0_raw=B0raw, weighted_averted_per1000=g, rel=g / B0, lo=lo, hi=hi, raw_averted_per1000=r, residual_weighted=B0 - g, residual_raw=B0raw - r,
                         taps_per_error_averted=B / r if r > 1e-9 else np.nan, share_msgs_prompted=share_acted(pols[k], w, B) if k in pols and "T" in pols[k] else np.nan))
    for a, b in DIFFS:
        lo, hi = ci(res, lambda x: (x[a][B] - x[b][B]) / x["b0"]); d = pt[a][B][0] - pt[b][B][0]; rows.append(dict(budget=B, policy=f"{a} minus {b}", weighted_averted_per1000=d, rel=d / B0, lo=lo, hi=hi))
FR = pd.DataFrame(rows); FR.to_csv(R3 / "r3_frontier.csv", index=False)
print(FR[FR.budget == 100].round(3).to_string(), flush=True)

# AUROC, both S1 variants
au = []
for d in range(3):
    yb = (Y3[:, d] >= .5).astype(float)
    for k in P["pooled"]:
        pk = P["pooled"][k][:, d]; a = wauc(yb, pk, w); bs = [wauc(yb, pk, x) for x in boot.draws["both"][:300]]; r = dict(dimension=PD3[d], features=k, auroc=a, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5))
        if k not in ("P-K",):
            dd = [wauc(yb, pk, x) - wauc(yb, P["pooled"]["P-K"][:, d], x) for x in boot.draws["both"][:300]]; r.update(delta_vs_PK=a - wauc(yb, P["pooled"]["P-K"][:, d], w), dlo=np.percentile(dd, 2.5), dhi=np.percentile(dd, 97.5))
        au.append(r)
AU = pd.DataFrame(au); AU.to_csv(R3 / "r3_auroc.csv", index=False)

# ================================================================== 2. per-model (H2 under strict S1)
pm = []
for sc in LOCAL:
    Ys = YSC[sc][:, PRIM]; ps = build(P[sc], WV3, Q0, RHO3, Ys, prior(Ys), sc, 3, extra=False); ks = list(ps); B0s = b0(Ys, WV3, w)
    rs = {m: [dict(b0=b0(Ys, WV3, wb), **evalp(ps, wb, [50, 100], ks)) for wb in wsx[:150]] for m, wsx in boot.draws.items()}; p_ = {k: at_budgets(ps[k], w, [50, 100]) for k in ks}
    for B in (50, 100):
        for a, b in (("P-I", "P-K"), ("P-I", "P-O"), ("P-O", "P-K"), ("P-I", "B5"), ("P-K", "B5")):
            lo, hi = ci(rs, lambda x: (x[a][B] - x[b][B]) / x["b0"]); pm.append(dict(model=sc, budget=B, contrast=f"{a} minus {b}", rel=(p_[a][B][0] - p_[b][B][0]) / B0s, lo=lo, hi=hi))
    for d in (0, 1):
        yb = (Ys[:, d] >= .5).astype(float); pm.append(dict(model=sc, budget=-1, contrast=f"AUROC {PD3[d]} P-K / P-I / P-O", rel=wauc(yb, P[sc]["P-K"][:, d], w), lo=wauc(yb, P[sc]["P-I"][:, d], w), hi=wauc(yb, P[sc]["P-O"][:, d], w)))
pd.DataFrame(pm).to_csv(R3 / "r3_per_model.csv", index=False); log("per-model")

# ================================================================== 3. q sweep 0.3-1.0
QS = [round(x, 1) for x in np.arange(0.3, 1.01, .1)]; qrows = []
for q in QS:
    pq = build({k: P["pooled"][k] for k in ("P-K", "P-O", "P-I")}, WV3, q, RHO3, Y3, pr3, "pooled", 3, extra=False); ks = list(pq); ptq = {k: at_budget(pq[k], w, 100)[0] for k in ks}
    rq = {m: [dict(b0=b0(Y3, WV3, wb), **evalp(pq, wb, [100], ks)) for wb in wsx] for m, wsx in boot.draws.items()}
    for k in ks:
        lo, hi = ci(rq, lambda x: x[k][100] / x["b0"]); qrows.append(dict(q=q, contrast=k, rel=ptq[k] / B0, lo=lo, hi=hi))
    for a, b in (("P-K", "B5"), ("P-O", "B5"), ("P-I", "B5"), ("P-I", "P-O"), ("P-K", "B1"), ("P-I", "B1")):
        lo, hi = ci(rq, lambda x: (x[a][100] - x[b][100]) / x["b0"]); qrows.append(dict(q=q, contrast=f"{a} minus {b}", rel=(ptq[a] - ptq[b]) / B0, lo=lo, hi=hi))
QD = pd.DataFrame(qrows); QD.to_csv(R3 / "r3_qsweep.csv", index=False); log("q sweep")
be = {}
for q in np.round(np.arange(0.30, 1.0001, 0.01), 2):
    pq = build({k: P["pooled"][k] for k in ("P-K", "P-I")}, WV3, q, RHO3, Y3, pr3, "pooled", 3, extra=False); g = {k: at_budget(pq[k], w, 100)[0] for k in ("P-K", "P-I", "B5", "B1")}
    be[float(q)] = g
def first_q(a, b): ok = [q for q, g in be.items() if g[a] >= g[b]]; return min(ok) if ok else None
BEQ = {f"{a}_vs_{b}": first_q(a, b) for a, b in (("P-K", "B5"), ("P-K", "B1"), ("P-I", "B5"), ("P-I", "B1"))}

# ================================================================== 4. cost model: false alarm a, mispick m
crow = []; ks = ["P-K", "P-O", "P-I", "B5", "B1", "Oracle"]
for a_ in (0, .5, 1):
    for m_ in (0, .05, .10):
        cp = {k: with_cost(pols[k], a_, m_) for k in ks}; ptc = {k: at_budget(cp[k], w, 100)[0] for k in ks}
        rc = {mm: [dict(b0=b0(Y3, WV3, wb), **evalp(cp, wb, [100], ks)) for wb in wsx[:150]] for mm, wsx in boot.draws.items()}
        for k in ks:
            lo, hi = ci(rc, lambda x: x[k][100] / x["b0"]); crow.append(dict(a_falsealarm_taps=a_, m_mispick=m_, contrast=k, rel=ptc[k] / B0, lo=lo, hi=hi, weighted_net=ptc[k]))
        for x, y in (("P-K", "B5"), ("P-O", "B5"), ("P-I", "B5"), ("P-I", "P-O"), ("P-K", "B1")):
            lo, hi = ci(rc, lambda z: (z[x][100] - z[y][100]) / z["b0"]); crow.append(dict(a_falsealarm_taps=a_, m_mispick=m_, contrast=f"{x} minus {y}", rel=(ptc[x] - ptc[y]) / B0, lo=lo, hi=hi))
pd.DataFrame(crow).to_csv(R3 / "r3_cost.csv", index=False); log("cost")

# spurious-addition sensitivity: evaluate on r + e*s, policies trained on r
srow = []
for e in (0, .5, 1):
    Ye = Y3 + e * S3o; pe = {k: policy3(P["pooled"][k], WV3, Q0, RHO3, Ye) for k in ("P-K", "P-O", "P-I")}; pe["Oracle"] = policy3(Ye, WV3, Q0, RHO3, Ye)
    pe["B5"] = fixed_dict(WV3, Ye, Q0, RHO3, prior(Ye), "B5"); pe["B1"] = fixed_dict(WV3, Ye, Q0, RHO3, prior(Ye), "B1"); kk = list(pe); B0e = b0(Ye, WV3, w); pte = {k: at_budget(pe[k], w, 100)[0] for k in kk}
    re_ = {m: [dict(b0=b0(Ye, WV3, wb), **evalp(pe, wb, [100], kk)) for wb in wsx[:150]] for m, wsx in boot.draws.items()}
    for k in kk:
        lo, hi = ci(re_, lambda x: x[k][100] / x["b0"]); srow.append(dict(e_spurious_efficacy=e, B0=B0e, contrast=k, rel=pte[k] / B0e, lo=lo, hi=hi, weighted=pte[k]))
    for x, y in (("P-K", "B5"), ("P-O", "B5"), ("P-I", "B5"), ("P-I", "P-O")):
        lo, hi = ci(re_, lambda z: (z[x][100] - z[y][100]) / z["b0"]); srow.append(dict(e_spurious_efficacy=e, B0=B0e, contrast=f"{x} minus {y}", rel=(pte[x] - pte[y]) / B0e, lo=lo, hi=hi))
pd.DataFrame(srow).to_csv(R3 / "r3_spurious.csv", index=False); log("spurious")

# ================================================================== 5. full five-dimension scope (lost cues only; exploratory)
P5 = {k: Pm("pooled", k, 5) for k in ("P-K", "P-O", "P-I")}; pr5 = prior(Y5); p5 = build(P5, WV5, Q0, RHO5, Y5, pr5, "pooled", 5, extra=False); k5 = list(p5); B05 = b0(Y5, WV5, w); pt5 = {k: at_budgets(p5[k], w, [50, 100, 200]) for k in k5}
r5 = {m: [dict(b0=b0(Y5, WV5, wb), **evalp(p5, wb, [50, 100, 200], k5)) for wb in wsx] for m, wsx in boot.draws.items()}; s5 = []
for B in (50, 100, 200):
    for k in k5:
        lo, hi = ci(r5, lambda x: x[k][B] / x["b0"]); s5.append(dict(scope="five-dim (lost cues)", budget=B, contrast=k, B0=B05, rel=pt5[k][B][0] / B05, lo=lo, hi=hi, weighted=pt5[k][B][0], raw=pt5[k][B][1]))
    for x, y in (("P-K", "B5"), ("P-O", "B5"), ("P-I", "B5"), ("P-I", "P-O"), ("P-K", "B1")):
        lo, hi = ci(r5, lambda z: (z[x][B] - z[y][B]) / z["b0"]); s5.append(dict(scope="five-dim (lost cues)", budget=B, contrast=f"{x} minus {y}", B0=B05, rel=(pt5[x][B][0] - pt5[y][B][0]) / B05, lo=lo, hi=hi))
for B in (50, 100, 200):
    for k in ("P-K", "P-O", "P-I", "B5", "B1", "Oracle"): g = pt[k][B][0] if B in BUD else at_budget(pols[k], w, B)[0]; s5.append(dict(scope="primary (3-dim)", budget=B, contrast=k, B0=B0, rel=g / B0, weighted=g))
for dd, nm in ((3, "certainty"), (4, "agent")):
    yb = (Y5[:, dd] >= .5).astype(float)
    for k in P5: s5.append(dict(scope="auroc " + nm, budget=-1, contrast=k, rel=wauc(yb, P5[k][:, dd], w)))
pd.DataFrame(s5).to_csv(R3 / "r3_scope.csv", index=False); log("scope")

# ================================================================== 6. per writer + gain decomposition by dimension
sw_ = w.sum(); pw = []; dec = []
for k in ("P-K", "P-O", "P-I"):
    c = pols[k]; t = 1000 * (c["T"] @ w) / sw_; li = int(np.argmin(np.abs(t - 100))); f5 = (c["T"][li] @ w) / sw_; v5 = WV3[1] * Y3[:, 1] * Q0
    for wi, wr in enumerate(writers):
        mk = wid == wi; ww = w[mk]; b0w = 1000 * ((Y3[mk] * WV3).sum(1) @ ww) / ww.sum(); g = 1000 * (c["G"][li][mk] @ ww) / ww.sum(); g5 = f5 * 1000 * (v5[mk] @ ww) / ww.sum()
        pw.append(dict(policy=k, writer=wr, B0=b0w, averted=g, taps=1000 * (c["T"][li][mk] @ ww) / ww.sum(), B5_same_prompt_rate=g5, rel=g / b0w, B5_rel=g5 / b0w, minus_B5=g - g5))
    for d in range(3):
        mk = (c["d"][li] == d) & c["act"][li]; dec.append(dict(policy=k, dimension=PD3[d], share_of_prompts=(mk @ w) / sw_ / max(f5, 1e-9), weighted_averted=1000 * (c["G"][li] * mk @ w) / sw_, raw_averted=1000 * (c["R"][li] * mk @ w) / sw_,
                                                                  B0_dim=1000 * (Y3[:, d] * WV3[d] @ w) / sw_))
PW = pd.DataFrame(pw); PW.to_csv(R3 / "r3_per_writer.csv", index=False); pd.DataFrame(dec).to_csv(R3 / "r3_decomp.csv", index=False)
pws = {k: dict(beats_B5=int((g.minus_B5 > 0).sum()), n=len(g), median_rel=float(g.rel.median()), median_B5_rel=float(g.B5_rel.median()), q25=float(g.rel.quantile(.25)), q75=float(g.rel.quantile(.75)), min_rel=float(g.rel.min()), max_rel=float(g.rel.max())) for k, g in PW.groupby("policy")}
log("per-writer", pws)

# ================================================================== 7. curves + CI bands for figure
g2 = np.arange(0, 701, 25); cur = {}; ck = ["P-K", "P-O", "P-I", "B5", "B1", "Oracle", "B6-sup", "B6"]
for k in ck: cur[k] = dict(taps=list(range(0, 701, 10)), averted=[at_budget(pols[k], w, B)[0] for B in range(0, 701, 10)])
bd = {m: [{k: [v[0] / b0(Y3, WV3, wb) for v in at_budgets(pols[k], wb, g2).values()] for k in ("P-K", "P-O", "P-I", "B5", "B1", "B6-sup")} for wb in wsx] for m, wsx in boot.draws.items()}
cur["bands"] = {k: dict(taps=g2.tolist(), lo=[min(np.percentile([r[k][i] for r in rs], 2.5) for rs in bd.values()) for i in range(len(g2))], hi=[max(np.percentile([r[k][i] for r in rs], 97.5) for rs in bd.values()) for i in range(len(g2))]) for k in ("P-K", "P-O", "P-I", "B5", "B1", "B6-sup")}
json.dump(dict(curves=cur, b0=B0), open(R3 / "curves_r3.json", "w")); log("curves")

# ================================================================== 8. refit bootstrap (P-K strict, P-O stored, P-I refit end to end per resample)
def oof_w(X, y, wt):
    Pq = np.full(n, np.nan); wp = wt > 0
    for i in range(5):
        for j in range(5):
            te = (wg == i) & (mg == j); tr = (wg != i) & (mg != j) & wp; best, bC = 1e9, 1
            for C in (0.01, 0.1, 1, 10):
                ll = 0
                for k in range(3):
                    itr = tr & (mg % 3 != k); iva = tr & (mg % 3 == k)
                    if y[itr].sum() < 3 or y[iva].sum() == 0: continue
                    ll += wll(y[iva], pred_lr(fit_lr(X[itr], y[itr], wt[itr], C), X[iva]), wt[iva])
                if ll < best: best, bC = ll, C
            Pq[te] = pred_lr(fit_lr(X[tr], y[tr], wt[tr], bC), X[te])
    return Pq
RX = {k: XSETS["pooled"][k] for k in ("P-K", "P-O", "P-I")}; RB = np.random.default_rng(SEED + 7)
RW = []
for _ in range(NR):
    cw = np.bincount(RB.integers(0, 20, 20), minlength=20); cm = np.bincount(RB.integers(0, 600, 600), minlength=600); RW.append(w * cw[wid] * cm[mid])
def refit_job(wb):
    Pd = {k: np.stack([oof_w(RX[k], Y3[:, d], wb) for d in range(3)], 1) for k in RX}; ps = {k: policy3(Pd[k], WV3, Q0, RHO3, Y3) for k in Pd}
    ps["B5"] = fixed_dict(WV3, Y3, Q0, RHO3, prior(Y3, wb), "B5"); ps["B1"] = fixed_dict(WV3, Y3, Q0, RHO3, prior(Y3, wb), "B1"); ps["Oracle"] = policy3(Y3, WV3, Q0, RHO3, Y3)
    return dict(b0=b0(Y3, WV3, wb), **evalp(ps, wb, [50, 100, 200], list(ps)))
rf_path = R3 / f"refit_{NR}.json"
if rf_path.exists(): RF = json.load(open(rf_path)); RF = [{k: ({int(b): x for b, x in v.items()} if isinstance(v, dict) else v) for k, v in r.items()} for r in RF]
else:
    with Pool(14) as p: RF = p.map(refit_job, RW)
    json.dump(RF, open(rf_path, "w"))
log("refit boot done")
rr = []
for B in (50, 100, 200):
    for k in ("P-K", "P-O", "P-I", "B5", "B1", "Oracle"):
        v = np.array([r[k][B] / r["b0"] for r in RF]); rr.append(dict(budget=B, contrast=k, refit_mean=v.mean(), refit_lo=np.percentile(v, 2.5), refit_hi=np.percentile(v, 97.5), fixed_rel=pt[k][B][0] / B0 if B in BUD else np.nan,
                                                                  fixed_lo=FR[(FR.budget == B) & (FR.policy == k)].lo.iloc[0], fixed_hi=FR[(FR.budget == B) & (FR.policy == k)].hi.iloc[0]))
    for a, b in (("P-K", "B5"), ("P-O", "B5"), ("P-I", "B5"), ("P-I", "P-O"), ("P-I", "P-K"), ("P-K", "B1")):
        v = np.array([(r[a][B] - r[b][B]) / r["b0"] for r in RF]); fx = FR[(FR.budget == B) & (FR.policy == f"{a} minus {b}")].iloc[0]
        rr.append(dict(budget=B, contrast=f"{a} minus {b}", refit_mean=v.mean(), refit_lo=np.percentile(v, 2.5), refit_hi=np.percentile(v, 97.5), fixed_rel=fx.rel, fixed_lo=fx.lo, fixed_hi=fx.hi))
RR = pd.DataFrame(rr); RR.to_csv(R3 / "r3_refit.csv", index=False); print(RR.round(3).to_string(), flush=True)

# ================================================================== summary
g = lambda pol, B=100, col="rel": float(FR[(FR.budget == B) & (FR.policy == pol)][col].iloc[0])
summ = dict(B0_weighted=B0, B0_raw=B0raw, locals=LOCAL, nb_fixed=NB, nb_refit=NR, breakeven_q=BEQ, per_writer=pws,
            T100={k: dict(rel=g(k), lo=g(k, col="lo"), hi=g(k, col="hi"), weighted=g(k, col="weighted_averted_per1000"), raw=g(k, col="raw_averted_per1000"), taps_per_error=g(k, col="taps_per_error_averted")) for k in ALLK})
json.dump(summ, open(R3 / "summary_round3.json", "w"), indent=1, default=float); log("DONE")
