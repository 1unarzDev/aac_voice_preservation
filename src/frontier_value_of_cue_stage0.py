"""value_of_cue Stage 0 (CPU only): keyword-feature (S1) policy, frontier vs baselines, cluster bootstrap, CRC. See analysis/frontier/value_of_cue/PLAN.md (+A1)."""
import json, re, sys
import numpy as np, pandas as pd
from pathlib import Path
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_value_of_cue_units import ROOT, OUT, DIMS, MODELS, NEG, POL, ACT, slp_weights
SEED = 20261102; rng = np.random.default_rng(SEED)
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
U = pd.read_parquet(OUT / "units.parquet").reset_index(drop=True); n = len(U)
for d in DIMS: U[f"y_{d}"] = U[f"y_{d}"].fillna(0.0)
Y = np.stack([U[f"y_{d}"] for d in DIMS], 1); w = U.w.to_numpy(float)
SW = slp_weights(); mp = dict(polarity="NEG", speech_act="ACT", politeness="POL", certainty="CRT", agent="AGT")
WV = np.array([np.mean([SW["SLP1"][mp[d]], SW["SLP2"][mp[d]]]) for d in DIMS]); print("weights", dict(zip(DIMS, WV)))
RHO = np.array([.995, .787, .882, .954, 1.0]); Q = 0.9
writers = sorted(U.writer.unique()); wid = U.writer.map({x: i for i, x in enumerate(writers)}).to_numpy()
mids = sorted(U.item_id.unique()); mid = U.item_id.map({x: i for i, x in enumerate(mids)}).to_numpy()
perm_w = rng.permutation(len(writers)); wg = (perm_w[wid] % 5); perm_m = rng.permutation(len(mids)); mg = (perm_m[mid] % 5)

# ---------------------------------------------------------------- S1 keyword features (no source, no writer id)
MOD = re.compile(r"\b(?:can|could|would|will|shall|may|might|should|must)\b", re.I); WH = re.compile(r"\b(?:why|what|where|when|who|whom|how|which)\b", re.I)
CERT = re.compile(r"\b(?:maybe|perhaps|might|probably|think|guess|sure|definitely|really|very|certainly|always|never|surely|hope)\b", re.I)
PRON = re.compile(r"\b(?:i|me|my|mine|we|our|us|you|your|he|she|they|him|her|them|his|their|it)\b", re.I)
STOP = set("a an the to of in on at for and or but is are am be was were do does did it this that with from by as so if then than".split())
def feats(kw):
    t = re.findall(r"[A-Za-z']+", kw.lower()); nw = max(len(t), 1)
    return [len(t), np.log1p(len(kw)), np.mean([len(x) for x in t]) if t else 0, len(NEG.findall(kw)) > 0, len(POL.findall(kw)) > 0, len(ACT.findall(kw)) > 0,
            len(MOD.findall(kw)) > 0, len(WH.findall(kw)) > 0, "?" in kw, len(CERT.findall(kw)) > 0, len(PRON.findall(kw)) > 0, len(PRON.findall(kw)),
            sum(x in STOP for x in t) / nw, len(t) == 1, len(t) == 2, len(t) >= 5, "please" in t, bool(re.search(r"\b(?:i|me|my)\b", kw.lower())), bool(re.search(r"\b(?:you|your)\b", kw.lower())),
            bool(re.search(r"\b(?:we|our|us)\b", kw.lower())), bool(re.search(r"\b(?:he|she|they|him|her|them|his|their)\b", kw.lower()))]
XS1 = np.array([feats(k) for k in U.kw], float); XS1 = (XS1 - XS1.mean(0)) / (XS1.std(0) + 1e-9)

def fit_lr(X, y, sw, C):
    Xb = np.c_[np.ones(len(X)), X]; sw = sw / sw.mean()
    def f(b):
        z = Xb @ b; p = 1 / (1 + np.exp(-z)); ll = -(sw * (y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))).sum() + 0.5 / C * (b[1:] ** 2).sum()
        return ll, Xb.T @ (sw * (p - y)) + np.r_[0, b[1:] / C]
    return minimize(f, np.zeros(Xb.shape[1]), jac=True, method="L-BFGS-B").x
def pred_lr(b, X): return 1 / (1 + np.exp(-(np.c_[np.ones(len(X)), X] @ b)))
def wll(y, p, sw): return -(sw * (y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9))).sum() / sw.sum()

def oof(X, d):
    y = Y[:, d]; P = np.full(n, np.nan); Cs = {}
    for i in range(5):
        for j in range(5):
            te = (wg == i) & (mg == j); tr = (wg != i) & (mg != j)
            best, bC = 1e9, 1
            for C in (0.01, 0.1, 1, 10):
                ll = 0
                for k in range(3):
                    itr = tr & (mg % 3 != k); iva = tr & (mg % 3 == k)
                    if y[itr].sum() < 3 or y[iva].sum() == 0: continue
                    ll += wll(y[iva], pred_lr(fit_lr(X[itr], y[itr], w[itr], C), X[iva]), w[iva])
                if ll < best: best, bC = ll, C
            P[te] = pred_lr(fit_lr(X[tr], y[tr], w[tr], bC), X[te]); Cs[(i, j)] = bC
    return P

def wauc(y, s, sw):
    o = np.argsort(s, kind="mergesort"); y, s, sw = y[o], s[o], sw[o]
    pos = sw * y; neg = sw * (1 - y)
    cn = np.cumsum(neg) - neg                                   # ties handled approximately (ties broken arbitrarily; scores continuous)
    return (pos * cn).sum() / (pos.sum() * neg.sum())

P_K = np.stack([oof(XS1, d) for d in range(5)], 1)
PRIOR = np.array([(w * Y[:, d]).sum() / w.sum() for d in range(5)])
# ---------------------------------------------------------------- calibration / AUROC
cal = []
for d, nm in enumerate(DIMS):
    yb = (Y[:, d] >= 0.5).astype(float); a = wauc(yb, P_K[:, d], w)
    bins = np.quantile(P_K[:, d], np.linspace(0, 1, 11)); ece = 0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (P_K[:, d] >= lo) & (P_K[:, d] <= hi);
        if m.sum(): ece += (w[m].sum() / w.sum()) * abs((w[m] * P_K[m, d]).sum() / w[m].sum() - (w[m] * Y[m, d]).sum() / w[m].sum())
    cal.append(dict(dimension=nm, prior=PRIOR[d], auroc_S1=a, ece_S1=ece, mean_p=(w * P_K[:, d]).sum() / w.sum(), n_pos=int(yb.sum())))
CAL = pd.DataFrame(cal)

# ---------------------------------------------------------------- policy machinery
LAM = np.r_[0, np.geomspace(1e-4, 1.0, 300)]
def policy(P, wv, q=Q, rho=RHO, Yr=Y, dims=None):
    """per-unit one action: returns taps[L,n], gain_w[L,n], gain_raw[L,n]. Gain uses realised Y (expected resolution eff)."""
    dims = list(range(5)) if dims is None else dims
    BS = wv * P * q; BA = wv * P * rho
    G = np.zeros((len(LAM), n)); R = np.zeros_like(G); T = np.zeros_like(G); idx = np.arange(n)
    for li, lam in enumerate(LAM):
        net = np.full((n, 10), -1e9)
        for d in dims: net[:, d] = BS[:, d] - lam * 1; net[:, 5 + d] = BA[:, d] - lam * 2
        k = net.argmax(1); act = net[idx, k] > 0; d = k % 5; isask = k >= 5
        eff = np.where(isask, rho[d], q)
        G[li] = np.where(act, wv[d] * Yr[idx, d] * eff, 0); R[li] = np.where(act, Yr[idx, d] * eff, 0); T[li] = np.where(act, np.where(isask, 2, 1), 0)
    return T, G, R
def perdim_policy(P, wv, q=Q, rho=RHO, Yr=Y):
    """independent decision per dimension at shared lambda (CRC variant): returns taps, residual loss per message [L,n]"""
    L = np.zeros((len(LAM), n)); T = np.zeros_like(L)
    for li, lam in enumerate(LAM):
        res = np.zeros(n)
        for d in range(5):
            bs = wv[d] * P[:, d] * q - lam; ba = wv[d] * P[:, d] * rho[d] - 2 * lam
            a_s = (bs > ba) & (bs > 0); a_a = (ba >= bs) & (ba > 0)
            eff = np.where(a_a, rho[d], np.where(a_s, q, 0)); res += wv[d] * Yr[:, d] * (1 - eff); T[li] += np.where(a_a, 2, np.where(a_s, 1, 0))
        L[li] = res
    return T, L
_CACHE = {}
def at_budget(Tm, Gm, wb, B):
    """interpolated gain per 1000 at tap budget B; Tm,Gm [L,n]; wb weights [n] (curve cached per (policy matrices, weights))"""
    key = (id(Tm), id(Gm), id(wb))
    if key not in _CACHE:
        if len(_CACHE) > 64: _CACHE.clear()
        s = wb.sum(); t = 1000 * (Tm @ wb) / s; g = 1000 * (Gm @ wb) / s
        o = np.argsort(t); _CACHE[key] = (t[o], np.maximum.accumulate(g[o]), wb)   # keep wb alive so ids are not reused
    t, g, _ = _CACHE[key]; return np.interp(B, t, g)
def frac_acted(Tm, wb, B):
    s = wb.sum(); t = 1000 * (Tm @ wb) / s; sh = ((Tm > 0) @ wb) / s; o = np.argsort(t); return np.interp(B, t[o], sh[o])

BUD = [20, 50, 100, 200, 400]
def build_pols(wv, q=Q, rho=RHO, P=None, Yr=Y):
    P = P_K if P is None else P
    pols = {}
    pols["P-K"] = policy(P, wv, q, rho, Yr)
    pols["Oracle"] = policy(Yr, wv, q, rho, Yr)
    # B1 random: random dimension, random fraction of messages; analytic expectation; better of ASK(2 taps) and SHOW-TWO(1 tap)
    vS = (wv * Yr * q).mean(1); vA = (wv * Yr * rho).mean(1); rS = (Yr * q).mean(1); rA = (Yr * rho).mean(1)
    # B5 prior-only: the single (action,dim) maximising value per tap under the population prior, random fraction of messages
    cand = [(wv[d] * PRIOR[d] * q / 1, "S", d) for d in range(5)] + [(wv[d] * PRIOR[d] * rho[d] / 2, "A", d) for d in range(5)]
    _, a5, d5 = max(cand); e5 = (q if a5 == "S" else rho[d5]); v5 = wv[d5] * Yr[:, d5] * e5; r5 = Yr[:, d5] * e5; t5 = 1 if a5 == "S" else 2
    return pols, dict(vS=vS, vA=vA, rS=rS, rA=rA, v5=v5, r5=r5, t5=t5, B5=(a5, DIMS[d5]))
def evaluate(wb, pols, aux, B):
    """returns dict policy -> (gain_w at B, gain_raw at B, taps share) ; B0 loss"""
    out = {}
    s = wb.sum()
    for k in ("P-K", "Oracle"):
        T, G, R = pols[k]; out[k] = (at_budget(T, G, wb, B), at_budget(T, R, wb, B))
    for nm, (vS, vA, rS, rA, t) in dict(B1S=(aux["vS"], aux["vA"], aux["rS"], aux["rA"], 1)).items():
        fS = min(1, B / 1000); fA = min(1, B / 2000)
        gS = fS * (vS @ wb) / s * 1000; gA = fA * (vA @ wb) / s * 1000
        rs_ = fS * (aux["rS"] @ wb) / s * 1000; ra_ = fA * (aux["rA"] @ wb) / s * 1000
        out["B1"] = (max(gS, gA), rs_ if gS >= gA else ra_)
    f5 = min(1, B / (1000 * aux["t5"])); out["B5"] = (f5 * (aux["v5"] @ wb) / s * 1000, f5 * (aux["r5"] @ wb) / s * 1000)
    return out

wvec_variants = {"SLP-mean": WV, "SLP1": np.array([SW["SLP1"][mp[d]] for d in DIMS]), "SLP2": np.array([SW["SLP2"][mp[d]] for d in DIMS]), "uniform": np.ones(5)}
POLS, AUX = build_pols(WV); print("B5 action", AUX["B5"])
wfull = w.copy(); b0 = lambda wb, wv=WV, Yr=Y: 1000 * ((Yr * wv).sum(1) @ wb) / wb.sum(); b0raw = lambda wb, Yr=Y: 1000 * (Yr.sum(1) @ wb) / wb.sum()
print("B0 weighted /1000", b0(wfull), "raw events/1000", b0raw(wfull))

# ---------------------------------------------------------------- bootstrap
def draw(mode):
    cw = np.bincount(rng.integers(0, 20, 20), minlength=20) if mode in ("both", "writer") else np.ones(20)
    cm = np.bincount(rng.integers(0, 600, 600), minlength=600) if mode in ("both", "message") else np.ones(600)
    return w * cw[wid] * cm[mid]
def boot(pols, aux, wv, budgets, nb=NB):
    res = {m: {B: {} for B in budgets} for m in ("both", "writer", "message")}
    for m in res:
        acc = {B: [] for B in budgets}
        for _ in range(nb):
            wb = draw(m); b0w = b0(wb, wv)
            for B in budgets: ev = evaluate(wb, pols, aux, B); acc[B].append(dict(b0=b0w, **{k: v for k, v in ev.items()}))
        res[m] = acc
    return res
def summ(x, f):
    v = np.array([f(r) for r in x]); return np.percentile(v, [2.5, 97.5])
BS = boot(POLS, AUX, WV, BUD); rows = []
pt = {B: evaluate(wfull, POLS, AUX, B) for B in BUD}; b0pt = b0(wfull)
for B in BUD:
    for k in ("P-K", "B5", "B1", "Oracle"):
        g, r = pt[B][k]
        def ci(f): return tuple(np.min([summ(BS[m][B], f)[0] for m in BS]) for _ in (0,)) + tuple(np.max([summ(BS[m][B], f)[1] for m in BS]) for _ in (0,))
        lo, hi = ci(lambda x: x[k][0] / x["b0"]); sh = frac_acted(POLS["P-K"][0], wfull, B) if k == "P-K" else np.nan
        rows.append(dict(budget=B, policy=k, weighted_averted_per1000=g, rel_reduction_vs_B0=g / b0pt, rel_lo=lo, rel_hi=hi, raw_events_averted_per1000=r, taps_per_event_averted=B / r if r > 0 else np.nan))
    for ref in ("B1", "B5"):
        f = lambda x: (x["P-K"][0] - x[ref][0]) / x["b0"]; lo = min(summ(BS[m][B], f)[0] for m in BS); hi = max(summ(BS[m][B], f)[1] for m in BS)
        rows.append(dict(budget=B, policy=f"P-K minus {ref}", weighted_averted_per1000=pt[B]["P-K"][0] - pt[B][ref][0], rel_reduction_vs_B0=(pt[B]["P-K"][0] - pt[B][ref][0]) / b0pt, rel_lo=lo, rel_hi=hi))
FR = pd.DataFrame(rows); FR.to_csv(OUT / "stage0_frontier_budgets.csv", index=False)
print(FR.round(3).to_string())

# full curves (point estimates) for the figure
curves = {}
for k in ("P-K", "Oracle"):
    T, G, R = POLS[k]; s = wfull.sum(); curves[k] = dict(taps=(1000 * (T @ wfull) / s).tolist(), averted=(1000 * (G @ wfull) / s).tolist())
grid = np.arange(0, 1001, 10)
curves["B1"] = dict(taps=grid.tolist(), averted=[evaluate(wfull, POLS, AUX, B)["B1"][0] for B in grid]); curves["B5"] = dict(taps=grid.tolist(), averted=[evaluate(wfull, POLS, AUX, B)["B5"][0] for B in grid])
json.dump(dict(curves=curves, b0=b0pt), open(OUT / "stage0_curves.json", "w"))

# ---------------------------------------------------------------- fixed baselines B0,B2,B3,B4
fixed = []
s = wfull.sum(); L = Y * WV
fixed += [dict(policy="B0 always-commit", taps=0, residual_weighted=b0pt, averted=0), 
          dict(policy="B2 always-ask all 5 dims", taps=10000, residual_weighted=1000 * ((L * (1 - RHO)).sum(1) @ wfull) / s),
          dict(policy="B3 always-ask polarity only", taps=2000, residual_weighted=1000 * ((L.sum(1) - L[:, 0] * RHO[0]) @ wfull) / s),
          dict(policy="B4 always-show-two all 5 dims", taps=5000, residual_weighted=1000 * ((L * (1 - Q)).sum(1) @ wfull) / s)]
for f in fixed: f["averted"] = b0pt - f["residual_weighted"]
pd.DataFrame(fixed).to_csv(OUT / "stage0_fixed_baselines.csv", index=False); print(pd.DataFrame(fixed).round(1).to_string())

# ---------------------------------------------------------------- sensitivity (point estimates + bootstrap sign for P-K vs B1 at T=50,100)
sens = []
def sens_row(tag, wv, q=Q, rho=RHO, Yr=Y, P=None, nb=300):
    pols, aux = build_pols(wv, q, rho, P, Yr); r = {"setting": tag}
    for B in (50, 100):
        ev = evaluate(wfull, pols, aux, B); b0w = b0(wfull, wv, Yr); r[f"T{B}_PK_rel"] = ev["P-K"][0] / b0w; r[f"T{B}_B1_rel"] = ev["B1"][0] / b0w; r[f"T{B}_B5_rel"] = ev["B5"][0] / b0w
        dd = []
        for _ in range(nb):
            wb = draw("both"); e = evaluate(wb, pols, aux, B); dd.append((e["P-K"][0] - e["B1"][0]) / b0(wb, wv, Yr))
        r[f"T{B}_PKminusB1_lo"], r[f"T{B}_PKminusB1_hi"] = np.percentile(dd, [2.5, 97.5])
    sens.append(r)
for k, v in wvec_variants.items(): sens_row(f"weights={k}", v)
for q in (0.7, 1.0): sens_row(f"q={q}", WV, q=q)
sens_row("rho=1", WV, rho=np.ones(5))
Ysp = np.stack([U[f"r_{d}"].fillna(0) + 0.5 * U[f"s_{d}"].fillna(0) for d in DIMS], 1); Ysp2 = np.stack([U[f"r_{d}"].fillna(0) + 2 * U[f"s_{d}"].fillna(0) for d in DIMS], 1)
# spurious reweighting changes the outcome the policy is scored on (model refit not repeated: same P_K)
sens_row("spurious x0.5 (scored)", WV, Yr=np.clip(Ysp, 0, 2)); sens_row("spurious x2 (scored)", WV, Yr=np.clip(Ysp2, 0, 2))
for m in MODELS:
    Ym = np.stack([np.nan_to_num(U[f"r_{d}_{m}"]) + np.nan_to_num(U[f"s_{d}_{m}"]) for d in DIMS], 1); sens_row(f"outcome model={m} (same P)", WV, Yr=Ym)
keep3 = WV.copy(); keep3[3] = keep3[4] = 0.0; sens_row("excluding certainty+agent (w=0)", keep3)
# per-dimension: does P-K beat random inside each dimension? AUROC with CI
rng_a = []
for d, nm in enumerate(DIMS):
    yb = (Y[:, d] >= .5).astype(float); a = []
    for _ in range(500):
        wb = draw("both"); a.append(wauc(yb, P_K[:, d], wb))
    lo, hi = np.percentile(a, [2.5, 97.5]); CAL.loc[CAL.dimension == nm, ["auroc_lo", "auroc_hi"]] = lo, hi
CAL.to_csv(OUT / "stage0_calibration_auroc.csv", index=False); print(CAL.round(3).to_string())
# random weight vectors in [0.2, 1]: P-K minus B1 at T=100 (point estimate sign + share of vectors)
rw = []
for _ in range(300):
    wv = rng.uniform(0.2, 1, 5); pols, aux = build_pols(wv); e = evaluate(wfull, pols, aux, 100); rw.append(dict(gain=e["P-K"][0] / b0(wfull, wv), b1=e["B1"][0] / b0(wfull, wv), b5=e["B5"][0] / b0(wfull, wv)))
RW = pd.DataFrame(rw); rwsum = dict(share_PK_gt_B1=float((RW.gain > RW.b1).mean()), share_PK_gt_B5=float((RW.gain > RW.b5).mean()), pk_rel_median=float(RW.gain.median()), pk_rel_min=float(RW.gain.min()))
SENS = pd.DataFrame(sens); SENS.to_csv(OUT / "stage0_sensitivity.csv", index=False); print(SENS.round(3).to_string()); print(rwsum)
# per-dimension frontier: policy restricted to one dimension (weighted averted at T=50 within that dim) vs random within dim
perdim = []
for d, nm in enumerate(DIMS):
    wv1 = np.zeros(5); wv1[d] = WV[d]; pols, aux = build_pols(wv1); r = dict(dimension=nm)
    for B in (20, 50, 100):
        e = evaluate(wfull, pols, aux, B); r[f"T{B}_PK"] = e["P-K"][0]; r[f"T{B}_B1"] = e["B1"][0]; r[f"T{B}_Oracle"] = e["Oracle"][0]; r[f"T{B}_B0dim"] = b0(wfull, wv1)
    perdim.append(r)
PD = pd.DataFrame(perdim); PD.to_csv(OUT / "stage0_perdim.csv", index=False); print(PD.round(2).to_string())

# ---------------------------------------------------------------- CRC (A1 targets), independent per-dim decisions, 500 writer x message splits
PT_K, LS_K = perdim_policy(P_K, WV)
Pprior = np.tile(PRIOR, (n, 1)); PT_5, LS_5 = perdim_policy(Pprior, WV)
# B1 random: ask every (unit,dim) with prob f; use the better of ASK/SHOW per tap analytically as loss = sum wv*Y*(1-f*eff); taps = f*taps ; choose ASK (strong baseline: SHOW-TWO q=.9 cheaper)
FGR = np.linspace(0, 1, 201)
def risk(L_, mask, wb): return 1000 * (L_[:, mask] @ wb[mask]) / wb[mask].sum()
Bmax = WV.sum() * 1000; res = []
Ltot0 = (Y * WV).sum(1)
for sp in range(500):
    wp = rng.permutation(20); cw_ = np.isin(wid, wp[:10]); mp_ = rng.permutation(600)[:300]; cm_ = np.isin(mid, mp_)
    cal_m = cw_ & cm_; te_m = (~cw_) & (~cm_)
    nc = cal_m.sum()
    for alpha in (5, 10, 20, 100, 150, 250):
        for nm, (T_, L_) in dict(PK=(PT_K, LS_K), B5=(PT_5, LS_5)).items():
            rc = risk(L_, cal_m, w) ; adj = nc / (nc + 1) * rc + Bmax / (nc + 1)
            ok = np.where(adj <= alpha)[0]
            if len(ok): li = ok[-1] if False else ok[np.argmax(LAM[ok])]; feas = True       # largest lambda (fewest asks) satisfying the CRC condition
            else: li, feas = 0, False
            res.append(dict(split=sp, alpha=alpha, policy=nm, feasible=feas, test_risk=risk(L_, te_m, w)[li], test_taps=1000 * (T_[li][te_m] @ w[te_m]) / w[te_m].sum()))
        # B1 random: SHOW-TWO on random (unit,dim) pairs w.p. f -> expected residual loss = sum wv*Y*(1-f q), taps = 5 f
        for nm, eff, tp in (("B1_show", Q, 5), ("B1_ask", None, 10)):
            def rr(mask, f): 
                e = np.array([Q] * 5) if eff is not None else RHO
                return 1000 * (((Y * WV * (1 - f * e)).sum(1))[mask] @ w[mask]) / w[mask].sum()
            adjv = np.array([nc / (nc + 1) * rr(cal_m, f) + Bmax / (nc + 1) for f in FGR]); ok = np.where(adjv <= alpha)[0]
            if len(ok): f = FGR[ok[0]]; feas = True
            else: f, feas = 1.0, False
            res.append(dict(split=sp, alpha=alpha, policy=nm, feasible=feas, test_risk=rr(te_m, f), test_taps=f * tp * 1000))
CR = pd.DataFrame(res)
agg = CR.groupby(["alpha", "policy"]).agg(feasible_share=("feasible", "mean"), mean_test_risk=("test_risk", "mean"), taps=("test_taps", "mean"),
                                           violation=("test_risk", lambda x: np.nan)).reset_index()
al_ = CR.copy(); al_["viol"] = al_.test_risk > al_.alpha; v = al_.groupby(["alpha", "policy"]).viol.mean().reset_index(); agg["violation"] = v.viol.values
agg["B0_risk"] = b0pt; agg.to_csv(OUT / "stage0_crc.csv", index=False); print(agg.round(2).to_string())
json.dump(dict(rw=rwsum, B0=b0pt, B0_raw=b0raw(wfull), prior=dict(zip(DIMS, PRIOR)), weights=dict(zip(DIMS, WV)), seed=SEED, n_boot=NB, B5_action=AUX["B5"]), open(OUT / "stage0_summary.json", "w"), indent=1)
np.save(OUT / "P_K_oof.npy", P_K)
