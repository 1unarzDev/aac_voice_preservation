"""value_of_cue round 2, items 1-4 (CPU, 0 model calls): primary-scope frontier, ASK vs SHOW split, q sweep, no-lexicon fit, H3 restated. PLAN.md A2."""
import json, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import frontier_value_of_cue_lib as L
from frontier_value_of_cue_lib import *
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
R2 = OUT / "round2"; R2.mkdir(exist_ok=True)
Yr5 = outcome("r"); Ys5 = outcome("s"); Y3 = Yr5[:, PRIM]; WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]; D3 = [DIMS[i] for i in PRIM]
BUD = [20, 50, 100, 200, 400, 600]; G1_REPAIR = 0.525                      # W-C strict-failure repair rate of G1 (analysis/guard_baseline/report.md)
def cached(name, fn):
    p = R2 / name
    if p.exists(): return np.load(p)
    a = fn(); np.save(p, a); return a
t0 = time.time()
P_nl = cached("P_noLex_prim.npy", lambda: np.stack([oof(XS1_NOLEX, Y3[:, d]) for d in range(3)], 1))
P_fu = cached("P_full_prim.npy", lambda: np.stack([oof(XS1_FULL, Y3[:, d]) for d in range(3)], 1))
P_nl5 = cached("P_noLex_all5_r.npy", lambda: np.stack([oof(XS1_NOLEX, Yr5[:, d]) for d in range(5)], 1)); print("fits", round(time.time() - t0), "s", flush=True)
PRIOR3 = np.array([(w * Y3[:, d]).sum() / w.sum() for d in range(3)]); PRIOR5 = np.array([(w * Yr5[:, d]).sum() / w.sum() for d in range(5)])
B0P = b0(Y3, WV3, w); B0A = b0(Yr5, WV5, w); print("B0 primary", B0P, "all5 r-only", B0A)
boot = Boot(NB)

def build(P, wv=WV3, q=Q0, rho=RHO3, Yr=Y3, prior=PRIOR3):
    pols = {"P-K": policy(P, wv, q, rho, Yr), "P-K ASK-only": policy(P, wv, q, rho, Yr, "ask"), "P-K SHOW-only": policy(P, wv, q, rho, Yr, "show"),
            "Oracle": policy(Yr, wv, q, rho, Yr)}
    pols["B5"], a5 = b5_curves(wv, q, rho, Yr, prior); pols["B5 ASK-only"], _ = b5_curves(wv, q, rho, Yr, prior, "ask"); pols["B5 SHOW-only"], _ = b5_curves(wv, q, rho, Yr, prior, "show")
    pols["B1"] = b1_curves(wv, q, rho, Yr); pols["B1 ASK-only"] = b1_curves(wv, q, rho, Yr, "ask"); pols["B1 SHOW-only"] = b1_curves(wv, q, rho, Yr, "show")
    return pols, a5
def ev(pols, wb, Bs): return {k: at_budgets(c, wb, Bs) for k, c in pols.items()}
def run_boot(fn):
    return {m: [fn(x) for x in ws] for m, ws in boot.draws.items()}
def ci(res, g):
    lo, hi = [], []
    for m, rs in res.items(): a, b = np.percentile([g(r) for r in rs], [2.5, 97.5]); lo.append(a); hi.append(b)
    return min(lo), max(hi)

# ================================================================ 1. primary frontier (noLex = primary, full lexicon = comparison)
rows = []; summ = {}
for tag, P in (("noLex", P_nl), ("withLex", P_fu)):
    pols, a5 = build(P); summ["B5_action"] = a5
    pt = ev(pols, w, BUD); res = run_boot(lambda wb: dict(b0=b0(Y3, WV3, wb), **ev(pols, wb, BUD)))
    for B in BUD:
        for k in ("P-K", "P-K ASK-only", "P-K SHOW-only", "B5", "B5 ASK-only", "B5 SHOW-only", "B1", "B1 ASK-only", "B1 SHOW-only", "Oracle"):
            g, r = pt[k][B]; lo, hi = ci(res, lambda x: x[k][B][0] / x["b0"])
            rows.append(dict(features=tag, budget=B, policy=k, weighted_averted_per1000=g, rel_reduction=g / B0P, rel_lo=lo, rel_hi=hi, raw_averted_per1000=r, taps_per_event_averted=B / r if r > 0 else np.nan,
                             share_msgs_prompted=share_acted(pols[k], w, B) if k in ("P-K", "P-K ASK-only", "P-K SHOW-only", "Oracle") else np.nan))
        for a, b in (("P-K", "B5"), ("P-K", "B1"), ("P-K ASK-only", "B5 ASK-only"), ("P-K SHOW-only", "B5 SHOW-only"), ("P-K ASK-only", "B1 ASK-only"), ("P-K SHOW-only", "B1 SHOW-only")):
            lo, hi = ci(res, lambda x: (x[a][B][0] - x[b][B][0]) / x["b0"]); d = pt[a][B][0] - pt[b][B][0]
            rows.append(dict(features=tag, budget=B, policy=f"{a} minus {b}", weighted_averted_per1000=d, rel_reduction=d / B0P, rel_lo=lo, rel_hi=hi))
    if tag == "noLex":
        # ASK vs SHOW split of the primary policy at each budget
        sp = []
        for B in BUD:
            t, a, s = split_ask_show(pols["P-K"], w, B); sp.append(dict(budget=B, realised_taps=t, share_msgs_ASK=a, share_msgs_SHOW=s,
                                                                    taps_from_ask=2 * a * 1000, taps_from_show=s * 1000))
        pd.DataFrame(sp).to_csv(R2 / "ask_show_split.csv", index=False)
        # G1 transfer: ASK-only with G1 repairing G1_REPAIR of residual after the cue is restored
        rho_g = RHO3 + (1 - RHO3) * G1_REPAIR; pg = {"P-K ASK-only + G1 (transfer)": policy(P, WV3, Q0, rho_g, Y3, "ask"), "P-K ASK-only": pols["P-K ASK-only"]}
        for B in BUD:
            gg = at_budget(pg["P-K ASK-only + G1 (transfer)"], w, B); ga = at_budget(pg["P-K ASK-only"], w, B)
            rows.append(dict(features=tag, budget=B, policy="P-K ASK-only + G1 (transfer est.)", weighted_averted_per1000=gg[0], rel_reduction=gg[0] / B0P, raw_averted_per1000=gg[1], taps_per_event_averted=B / gg[1]))
        # always-ask baselines (taps fixed), primary scope
        L3 = Y3 * WV3; s_ = w.sum()
        fixed = [dict(policy="B0 always-commit", taps=0, residual_weighted=B0P),
                 dict(policy="B2 always-ask 3 primary dims (chip row)", taps=6000, residual_weighted=1000 * ((L3 * (1 - RHO3)).sum(1) @ w) / s_),
                 dict(policy="B2 + G1 after ask (transfer est.)", taps=6000, residual_weighted=1000 * ((L3 * (1 - rho_g)).sum(1) @ w) / s_),
                 dict(policy="B3 always-ask polarity only", taps=2000, residual_weighted=1000 * ((L3.sum(1) - L3[:, 0] * RHO3[0]) @ w) / s_),
                 dict(policy="B4 always-show-two 3 primary dims", taps=3000, residual_weighted=1000 * ((L3 * (1 - Q0)).sum(1) @ w) / s_),
                 dict(policy="G1 alone (keyword-only inputs carry no chip to check: 0 by construction)", taps=0, residual_weighted=B0P)]
        for f in fixed: f["averted"] = B0P - f["residual_weighted"]; f["raw_events_B0"] = 1000 * (Y3.sum(1) @ w) / s_
        pd.DataFrame(fixed).to_csv(R2 / "fixed_baselines.csv", index=False)
        # curves for figure
        cv = {}
        for k in ("P-K", "P-K ASK-only", "P-K SHOW-only", "Oracle", "B5", "B1"):
            c = pols[k]; grid = np.arange(0, 1001, 10)
            if isinstance(c, list): cv[k] = dict(taps=grid.tolist(), averted=[at_budget(c, w, B)[0] for B in grid])
            else: cv[k] = dict(taps=grid.tolist(), averted=[at_budget(c, w, B)[0] for B in grid])
        # CI bands at a grid for P-K, B5, B1 (rel reduction)
        g2 = np.arange(0, 701, 25)
        bands = run_boot(lambda wb: {k: [v[0] / b0(Y3, WV3, wb) for v in at_budgets(pols[k], wb, g2).values()] for k in ("P-K", "B5", "B1")})
        cv["bands"] = {k: dict(taps=g2.tolist(), lo=np.min([np.percentile([r[k][i] for r in rs], 2.5) for rs in bands.values()], 0).tolist() if False else
                               [min(np.percentile([r[k][i] for r in rs], 2.5) for rs in bands.values()) for i in range(len(g2))],
                               hi=[max(np.percentile([r[k][i] for r in rs], 97.5) for rs in bands.values()) for i in range(len(g2))]) for k in ("P-K", "B5", "B1")}
        json.dump(dict(curves=cv, b0=B0P), open(R2 / "curves_prim.json", "w"))
FR = pd.DataFrame(rows); FR.to_csv(R2 / "frontier_primary.csv", index=False)
print(FR[(FR.features == "noLex") & FR.budget.isin([50, 100, 400])].round(3).to_string(), flush=True)

# ================================================================ 2. q sweep, rho=1, break-even q
sw_rows = []
for q in (0.5, 0.7, 0.9, 1.0):
    for rtag, rho in (("rho=measured", RHO3), ("rho=1", np.ones(3))):
        pols, _ = build(P_nl, q=q, rho=rho); pt = ev(pols, w, [50, 100]); res = run_boot(lambda wb: dict(b0=b0(Y3, WV3, wb), **ev(pols, wb, [50, 100]))) if q in (0.5, 0.7, 1.0) or rtag == "rho=1" or q == .9 else None
        for B in (50, 100):
            r = dict(q=q, rho=rtag, budget=B, B0=B0P)
            for k in ("P-K", "P-K ASK-only", "P-K SHOW-only", "B5", "B1"): r[k] = pt[k][B][0] / B0P
            for b in ("B5", "B1"):
                lo, hi = ci(res, lambda x: (x["P-K"][B][0] - x[b][B][0]) / x["b0"]); r[f"PK_minus_{b}"] = r["P-K"] - r[b]; r[f"PK_minus_{b}_lo"] = lo; r[f"PK_minus_{b}_hi"] = hi
            sw_rows.append(r)
SW_ = pd.DataFrame(sw_rows); SW_.to_csv(R2 / "q_sweep.csv", index=False); print(SW_.round(3).to_string(), flush=True)
be = []
for q in np.round(np.arange(0.30, 1.0001, 0.01), 2):
    pols, _ = build(P_nl, q=q); g = {k: at_budget(pols[k], w, 100)[0] / B0P for k in ("P-K", "B5", "B1")}; be.append(dict(q=q, **g, PK_minus_B5=g["P-K"] - g["B5"], PK_minus_B1=g["P-K"] - g["B1"]))
BE = pd.DataFrame(be); BE.to_csv(R2 / "breakeven_q.csv", index=False)
def first_pos(col):
    ok = BE[BE[col] >= 0]; return float(ok.q.min()) if len(ok) else None
summ["breakeven_q_vs_B5"] = first_pos("PK_minus_B5"); summ["breakeven_q_vs_B1"] = first_pos("PK_minus_B1")
summ["q_range_PK_beats_B5"] = [float(BE[BE.PK_minus_B5 >= 0].q.min()), float(BE[BE.PK_minus_B5 >= 0].q.max())] if (BE.PK_minus_B5 >= 0).any() else None

# ================================================================ 3. AUROC, noLex vs full lexicon, all five dims
au = []
for d in range(5):
    yb = (Yr5[:, d] >= .5).astype(float); a_nl = [wauc(yb, P_nl5[:, d], x) for x in boot.draws["both"][:300]]
    r = dict(dimension=DIMS[d], scope="primary" if d < 3 else "exploratory", prior=PRIOR5[d], n_pos=int(yb.sum()), auroc_noLex=wauc(yb, P_nl5[:, d], w), noLex_lo=np.percentile(a_nl, 2.5), noLex_hi=np.percentile(a_nl, 97.5))
    if d < 3:
        a_f = [wauc(yb, P_fu[:, d], x) for x in boot.draws["both"][:300]]; r.update(auroc_withLex=wauc(yb, P_fu[:, d], w), withLex_lo=np.percentile(a_f, 2.5), withLex_hi=np.percentile(a_f, 97.5))
    au.append(r)
AU = pd.DataFrame(au); AU.to_csv(R2 / "auroc.csv", index=False); print(AU.round(3).to_string(), flush=True)

# ================================================================ 4. exploratory dimensions + all-five scope + spurious burden (separate denominators)
ex = []
for d in range(5):
    wv1 = np.zeros(5); wv1[d] = WV5[d]; pols, _ = build(P_nl5, wv=wv1, rho=RHO5, Yr=Yr5, prior=PRIOR5)
    for B in (20, 50, 100):
        pt = {k: at_budget(pols[k], w, B)[0] for k in ("P-K", "B5", "B1", "Oracle")}
        ex.append(dict(dimension=DIMS[d], scope="primary" if d < 3 else "exploratory", budget=B, B0_dim=b0(Yr5, wv1, w), **{k: v for k, v in pt.items()}, PK_rel=pt["P-K"] / b0(Yr5, wv1, w),
                       PK_minus_B1=pt["P-K"] - pt["B1"], PK_minus_B5=pt["P-K"] - pt["B5"], helped=bool(pt["P-K"] > max(pt["B1"], pt["B5"]))))
pd.DataFrame(ex).to_csv(R2 / "per_dimension.csv", index=False); print(pd.DataFrame(ex).round(2).to_string())
pa, _ = build(P_nl5, WV5, Q0, RHO5, Yr5, PRIOR5); res5 = run_boot(lambda wb: dict(b0=b0(Yr5, WV5, wb), **ev(pa, wb, [50, 100, 400])))
a5rows = []
for B in (50, 100, 400):
    for k in ("P-K", "B5", "B1"):
        lo, hi = ci(res5, lambda x: x[k][B][0] / x["b0"]); a5rows.append(dict(scope="all five dims, lost cues only (r)", budget=B, policy=k, rel_reduction=at_budget(pa[k], w, B)[0] / B0A, lo=lo, hi=hi, B0=B0A))
    lo, hi = ci(res5, lambda x: (x["P-K"][B][0] - x["B5"][B][0]) / x["b0"]); a5rows.append(dict(scope="all five dims, lost cues only (r)", budget=B, policy="P-K minus B5", rel_reduction=(at_budget(pa["P-K"], w, B)[0] - at_budget(pa["B5"], w, B)[0]) / B0A, lo=lo, hi=hi, B0=B0A))
for B in (50, 100, 400):
    k = FR[(FR.features == "noLex") & (FR.budget == B) & (FR.policy == "P-K")].iloc[0]; a5rows.append(dict(scope="PRIMARY (polarity, speech act, politeness-lost)", budget=B, policy="P-K", rel_reduction=k.rel_reduction, lo=k.rel_lo, hi=k.rel_hi, B0=B0P))
pd.DataFrame(a5rows).to_csv(R2 / "scope_comparison.csv", index=False)
spur = [dict(dimension=DIMS[d], lost_weighted_per1000=1000 * (Yr5[:, d] * WV5[d] @ w) / w.sum(), lost_raw_per1000=1000 * (Yr5[:, d] @ w) / w.sum(), spurious_weighted_per1000=1000 * (Ys5[:, d] * WV5[d] @ w) / w.sum(),
             spurious_raw_per1000=1000 * (Ys5[:, d] @ w) / w.sum()) for d in range(5)]
pd.DataFrame(spur).to_csv(R2 / "burden_lost_vs_spurious.csv", index=False); print(pd.DataFrame(spur).round(1).to_string(), flush=True)

# ================================================================ 5. H3 restated: heuristic calibration (CRC-style), equal-realised-risk B5 on randomised ladder
FG = np.linspace(0, 3, 601)
def perdim_loss(P, wv, q=Q0, rho=RHO3, Yr=Y3):
    Lm = np.zeros((len(LAM), n)); T = np.zeros_like(Lm); C = np.zeros_like(Lm)
    for li, lam in enumerate(LAM):
        for d in range(3):
            bs = wv[d] * P[:, d] * q - lam; ba = wv[d] * P[:, d] * rho[d] - 2 * lam; a_s = (bs > ba) & (bs > 0); a_a = (ba >= bs) & (ba > 0)
            eff = np.where(a_a, rho[d], np.where(a_s, q, 0)); Lm[li] += wv[d] * Yr[:, d] * (1 - eff); T[li] += np.where(a_a, 2, np.where(a_s, 1, 0)); C[li] += (a_a | a_s)
    return Lm, T, C
LK, TK, CK = perdim_loss(P_nl, WV3)
order = np.argsort(-(WV3 * PRIOR3))                                          # B5: prior-ordered dims; ladder f in [0,3]: dim k acted w.p. clip(f-k,0,1)
def ladder(kind):
    Lm = np.zeros((len(FG), n)); T = np.zeros_like(Lm); C = np.zeros_like(Lm)
    for fi, f in enumerate(FG):
        for k, d in enumerate(order if kind == "B5" else range(3)):
            pr = np.clip(f - k, 0, 1) if kind == "B5" else min(f, 1.0)
            if kind == "B1" and f > 1: pr = 1.0
            Lm[fi] += WV3[d] * Y3[:, d] * (1 - pr * Q0); T[fi] += pr; C[fi] += pr
    return Lm, T, C
LB5, TB5, CB5 = ladder("B5"); LB1, TB1, CB1 = ladder("B1")
Bmax = WV3.sum() * 1000; res = []; rg = np.random.default_rng(SEED + 5); fl = {}
fl["always_ask_floor"] = float(1000 * ((Y3 * WV3 * (1 - RHO3)).sum(1) @ w) / w.sum()); fl["lambda0_floor"] = float(1000 * (LK[0] @ w) / w.sum())
fl["lambda0_taps"] = float(1000 * (TK[0] @ w) / w.sum()); fl["lambda0_prompts_per_msg"] = float((CK[0] @ w) / w.sum())
for sp in range(500):
    wp = rg.permutation(20); cw_ = np.isin(wid, wp[:10]); cm_ = np.isin(mid, rg.permutation(600)[:300]); cal_m = cw_ & cm_; te_m = (~cw_) & (~cm_); nc = cal_m.sum()
    rk = lambda Lm, m: 1000 * (Lm[:, m] @ w[m]) / w[m].sum()
    for fr in (0.22, 0.33, 0.55):
        alpha = fr * B0P
        for nm, (Lm, T, C) in dict(PK=(LK, TK, CK), B5rand=(LB5, TB5, CB5), B1rand=(LB1, TB1, CB1)).items():
            adj = nc / (nc + 1) * rk(Lm, cal_m) + Bmax / (nc + 1); ok = np.where(adj <= alpha)[0]
            if nm == "PK": li = ok[np.argmax(LAM[ok])] if len(ok) else 0
            else: li = ok[0] if len(ok) else len(adj) - 1
            tr = rk(Lm, te_m); res.append(dict(split=sp, frac=fr, alpha=alpha, policy=nm, feasible=bool(len(ok)), test_risk=tr[li], taps=1000 * (T[li][te_m] @ w[te_m]) / w[te_m].sum(), prompts_per_msg=(C[li][te_m] @ w[te_m]) / w[te_m].sum()))
            if nm == "PK": rpk = tr[li]
        # B5/B1 taps needed to reach P-K's REALISED test risk (equal realised risk)
        for nm, (Lm, T, C) in dict(B5rand=(LB5, TB5, CB5), B1rand=(LB1, TB1, CB1)).items():
            tr = rk(Lm, te_m); tp = 1000 * (T[:, te_m] @ w[te_m]) / w[te_m].sum(); o = np.argsort(-tr)
            res.append(dict(split=sp, frac=fr, alpha=alpha, policy=nm + "_at_PK_realised_risk", feasible=True, test_risk=rpk, taps=float(np.interp(rpk, tr[o][::-1], tp[o][::-1])) if rpk >= tr.min() else np.nan, prompts_per_msg=np.nan))
CR = pd.DataFrame(res); agg = CR.groupby(["frac", "alpha", "policy"]).agg(feasible_share=("feasible", "mean"), mean_test_risk=("test_risk", "mean"), taps=("taps", "mean"), prompts_per_msg=("prompts_per_msg", "mean")).reset_index()
v = CR.assign(viol=CR.test_risk > CR.alpha).groupby(["frac", "alpha", "policy"]).viol.mean().reset_index(); agg["exceedance_rate"] = v.viol.values; agg["B0_prim"] = B0P
agg.to_csv(R2 / "h3_calibration.csv", index=False); print(agg.round(2).to_string(), flush=True)
# round-1 (all five dims, y=r+s) floors restated from the stored pilot predictions
Yall = outcome("y"); P1 = np.load(OUT / "P_K_oof.npy"); L_ = Yall * WV5; fl["round1_always_ask_floor_rho_lt_1"] = float(1000 * ((L_ * (1 - RHO5)).sum(1) @ w) / w.sum())
r0 = np.zeros(n)
for d in range(5):
    bs = WV5[d] * P1[:, d] * Q0; ba = WV5[d] * P1[:, d] * RHO5[d] / 1; r0 += WV5[d] * Yall[:, d] * (1 - np.where(ba * 1 >= bs, RHO5[d], Q0))
fl["round1_lambda0_floor_all5"] = float(1000 * (r0 @ w) / w.sum()); fl["round1_B0"] = float(b0(Yall, WV5, w))
summ.update(floors=fl, B0_primary=B0P, B0_all5_r_only=B0A, prior_primary=dict(zip(D3, PRIOR3)), weights_primary=dict(zip(D3, WV3)), nb=NB, seed=SEED, g1_repair_rate_transfer=G1_REPAIR)
json.dump(summ, open(R2 / "cpu_summary.json", "w"), indent=1, default=float); print(json.dumps(summ, indent=1, default=float)); print("done", round(time.time() - t0), "s")
