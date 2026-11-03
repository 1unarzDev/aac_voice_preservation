"""value_of_cue round 2 library: unit table, S1 features (with/without lexicon flags), nested-block logistic cross-fitting, policy curves, paired cluster bootstrap.
Machinery identical in form to frontier_value_of_cue_stage0.py (PLAN.md A1/A2). All numbers PROVISIONAL (detector/machine labels)."""
import re, sys
import numpy as np, pandas as pd
from pathlib import Path
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_value_of_cue_units import ROOT, OUT, DIMS, MODELS, NEG, POL, ACT, slp_weights
SEED = 20261102
U = pd.read_parquet(OUT / "units.parquet").reset_index(drop=True); n = len(U)
w = U.w.to_numpy(float)
SW = slp_weights(); _mp = dict(polarity="NEG", speech_act="ACT", politeness="POL", certainty="CRT", agent="AGT")
WV5 = np.array([np.mean([SW["SLP1"][_mp[d]], SW["SLP2"][_mp[d]]]) for d in DIMS])
RHO5 = np.array([.995, .787, .882, .954, 1.0]); Q0 = 0.9
PRIM = [0, 1, 2]                      # primary scope dims: polarity, speech act, politeness-lost
rng0 = np.random.default_rng(SEED)
writers = sorted(U.writer.unique()); wid = U.writer.map({x: i for i, x in enumerate(writers)}).to_numpy()
mids = sorted(U.item_id.unique()); mid = U.item_id.map({x: i for i, x in enumerate(mids)}).to_numpy()
_pw = rng0.permutation(len(writers)); wg = _pw[wid] % 5; _pm = rng0.permutation(len(mids)); mg = _pm[mid] % 5   # same blocks as stage0 (same first two draws)
def outcome(kind="r", model=None, dims=range(5)):
    """[n,5] outcome matrix: r (lost) / s (spurious) / y (=r+s); model None = mean over 4 P0 models"""
    sfx = f"_{model}" if model else ""
    f = lambda p, d: np.nan_to_num(U[f"{p}_{d}{sfx}"].to_numpy(float))
    return np.stack([f("r", d) if kind == "r" else f("s", d) if kind == "s" else f("r", d) + f("s", d) for d in DIMS], 1)

# ---------------------------------------------------------------- S1 keyword features
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
def zs(X): X = np.asarray(X, float); return (X - X.mean(0)) / (X.std(0) + 1e-9)
_F = np.array([feats(k) for k in U.kw], float)
XS1_FULL = zs(_F); XS1_NOLEX = zs(np.delete(_F, [3, 4, 5], axis=1))     # columns 3,4,5 = NEG/POL/ACT lexicon flags = the outcome-defining lexicons

# ---------------------------------------------------------------- logistic cross-fitting
def fit_lr(X, y, sw, C):
    Xb = np.c_[np.ones(len(X)), X]; sw = sw / sw.mean()
    def f(b):
        z = Xb @ b; p = 1 / (1 + np.exp(-z)); ll = -(sw * (y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))).sum() + 0.5 / C * (b[1:] ** 2).sum()
        return ll, Xb.T @ (sw * (p - y)) + np.r_[0, b[1:] / C]
    return minimize(f, np.zeros(Xb.shape[1]), jac=True, method="L-BFGS-B").x
def pred_lr(b, X): return 1 / (1 + np.exp(-(np.c_[np.ones(len(X)), X] @ b)))
def wll(y, p, sw): return -(sw * (y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9))).sum() / sw.sum()
def oof(X, y):
    """held-out prediction of each unit by a model trained with its writer group AND message group excluded; C by inner 3-fold CV on training blocks"""
    P = np.full(n, np.nan)
    for i in range(5):
        for j in range(5):
            te = (wg == i) & (mg == j); tr = (wg != i) & (mg != j); best, bC = 1e9, 1
            for C in (0.01, 0.1, 1, 10):
                ll = 0
                for k in range(3):
                    itr = tr & (mg % 3 != k); iva = tr & (mg % 3 == k)
                    if y[itr].sum() < 3 or y[iva].sum() == 0: continue
                    ll += wll(y[iva], pred_lr(fit_lr(X[itr], y[itr], w[itr], C), X[iva]), w[iva])
                if ll < best: best, bC = ll, C
            P[te] = pred_lr(fit_lr(X[tr], y[tr], w[tr], bC), X[te])
    return P
def wauc(y, s, sw):
    o = np.argsort(s, kind="mergesort"); y, s, sw = y[o], s[o], sw[o]; pos = sw * y; neg = sw * (1 - y); cn = np.cumsum(neg) - neg
    return (pos * cn).sum() / (pos.sum() * neg.sum())

# ---------------------------------------------------------------- policy curves (all return taps[L,n], gain_w[L,n], gain_raw[L,n]; averaged with weights later)
LAM = np.r_[0, np.geomspace(1e-4, 1.0, 300)]
def policy(P, wv, q=Q0, rho=RHO5, Yr=None, actions="both", dims=None):
    """one action per message: SHOW-TWO (1 tap, eff q) or ASK-ONE-CUE (2 taps, eff rho_d); P,Yr [n,D]; wv,rho [D]"""
    D = P.shape[1]; dims = list(range(D)) if dims is None else dims; Yr = P if Yr is None else Yr
    B = np.full((n, 2 * D), -1e9); tp = np.r_[np.ones(D), 2 * np.ones(D)]
    for d in dims:
        if actions in ("both", "show"): B[:, d] = wv[d] * P[:, d] * q
        if actions in ("both", "ask"): B[:, D + d] = wv[d] * P[:, d] * rho[d]
    net = B[None] - LAM[:, None, None] * tp[None, None]; k = net.argmax(2); act = np.take_along_axis(net, k[..., None], 2)[..., 0] > 0
    d = k % D; isask = k >= D; eff = np.where(isask, rho[d], q); idx = np.arange(n)[None]
    y = Yr[idx, d]; G = np.where(act, wv[d] * y * eff, 0); R = np.where(act, y * eff, 0); T = np.where(act, np.where(isask, 2, 1), 0)
    return dict(T=T, G=G, R=R, ask=isask & act, show=(~isask) & act)
def curve_fixed(per_msg_gain, per_msg_raw, taps, grid=np.linspace(0, 1, 401)):
    """randomised ladder: act on each message independently w.p. f (expectation): T=f*taps, G=f*gain"""
    return dict(T=grid[:, None] * np.full(n, taps)[None], G=grid[:, None] * per_msg_gain[None], R=grid[:, None] * per_msg_raw[None])
def b5_curves(wv, q, rho, Yr, prior, actions="both"):
    D = Yr.shape[1]; cand = []
    if actions in ("both", "show"): cand += [(wv[d] * prior[d] * q / 1, "S", d) for d in range(D)]
    if actions in ("both", "ask"): cand += [(wv[d] * prior[d] * rho[d] / 2, "A", d) for d in range(D)]
    _, a, d = max(cand); e = q if a == "S" else rho[d]
    return curve_fixed(wv[d] * Yr[:, d] * e, Yr[:, d] * e, 1 if a == "S" else 2), (a, DIMS[d])
def b1_curves(wv, q, rho, Yr, actions="both"):
    """random dimension, random message fraction; returns list of candidate curves (best of ASK / SHOW at evaluation)"""
    D = Yr.shape[1]; out = []
    if actions in ("both", "show"): out.append(curve_fixed((wv * Yr * q).mean(1), (Yr * q).mean(1), 1))
    if actions in ("both", "ask"): out.append(curve_fixed((wv * Yr * rho).mean(1), (Yr * rho).mean(1), 2))
    return out
def gated_policy(score, dsel, wv, q, Yr, seed=7):
    """rank messages by score (B6 entropy gate), ask SHOW-TWO on dimension dsel[n] for the top fraction; ladder over 401 rank fractions"""
    jit = np.random.default_rng(seed).uniform(0, 1e-9, n); o = np.argsort(-(score + jit)); rank = np.empty(n); rank[o] = np.arange(n) / n
    grid = np.linspace(0, 1, 401); act = rank[None] < grid[:, None]; idx = np.arange(n)
    y = Yr[idx, dsel]; G = act * (wv[dsel] * y * q)[None]; R = act * (y * q)[None]; T = act * 1.0
    return dict(T=T, G=G, R=R)
def cum_curve(c, wb):
    s = wb.sum(); t = 1000 * (c["T"] @ wb) / s; g = 1000 * (c["G"] @ wb) / s; r = 1000 * (c["R"] @ wb) / s; o = np.argsort(t, kind="mergesort")
    return t[o], np.maximum.accumulate(g[o]), np.maximum.accumulate(r[o])
def at_budget(c, wb, B):
    """interpolated (weighted gain, raw gain) per 1000 messages at tap budget B; c may be a list (best of candidates)"""
    cs = c if isinstance(c, list) else [c]; best = (-1, 0)
    for x in cs:
        t, g, r = cum_curve(x, wb); gv = np.interp(B, t, g)
        if gv > best[0]: best = (gv, np.interp(B, t, r))
    return best
def at_budgets(c, wb, Bs):
    """same as at_budget for several budgets with one curve build per candidate; returns {B: (gain, raw)}"""
    cs = c if isinstance(c, list) else [c]; best = {B: (-1, 0) for B in Bs}
    for x in cs:
        t, g, r = cum_curve(x, wb)
        for B in Bs:
            gv = np.interp(B, t, g)
            if gv > best[B][0]: best[B] = (gv, np.interp(B, t, r))
    return best
def share_acted(c, wb, B):
    s = wb.sum(); t = 1000 * (c["T"] @ wb) / s; sh = ((c["T"] > 0) @ wb) / s; o = np.argsort(t, kind="mergesort"); return float(np.interp(B, t[o], sh[o]))
def split_ask_show(c, wb, B):
    """at tap budget B: shares of acted messages that are ASK (2 taps) vs SHOW-TWO, from the ladder point nearest B"""
    s = wb.sum(); t = 1000 * (c["T"] @ wb) / s; l = int(np.argmin(np.abs(t - B))); a = (c["ask"][l] @ wb) / s; sh = (c["show"][l] @ wb) / s
    return float(t[l]), float(a), float(sh)

# ---------------------------------------------------------------- bootstrap
class Boot:
    """draws weight vectors once (writers x messages jointly / writers only / messages only), reused for every statistic so differences are paired"""
    def __init__(self, nb, seed=SEED + 1):
        r = np.random.default_rng(seed); self.draws = {}
        for mode in ("both", "writer", "message"):
            ws = []
            for _ in range(nb):
                cw = np.bincount(r.integers(0, 20, 20), minlength=20) if mode in ("both", "writer") else np.ones(20)
                cm = np.bincount(r.integers(0, 600, 600), minlength=600) if mode in ("both", "message") else np.ones(600)
                ws.append(w * cw[wid] * cm[mid])
            self.draws[mode] = ws
    def ci(self, f):
        """widest of the three cluster 95% percentile intervals for statistic f(wb)"""
        lo, hi = [], []
        for m, ws in self.draws.items():
            v = np.array([f(x) for x in ws]); a, b = np.percentile(v, [2.5, 97.5]); lo.append(a); hi.append(b)
        return min(lo), max(hi)
def b0(Yr, wv, wb): return 1000 * ((Yr * wv).sum(1) @ wb) / wb.sum()
