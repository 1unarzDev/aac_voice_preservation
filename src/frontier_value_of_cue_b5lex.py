"""value_of_cue A7: lexicon-gated B5 baseline (CPU only). Rule in PLAN.md A7, written before the outcome."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frontier_value_of_cue_lib import *
R3 = OUT / "round3"; O = OUT / "b5lex"; O.mkdir(exist_ok=True)
Fm = np.array([feats(k) for k in U.kw], float); gate = (Fm[:, [5, 6, 7, 8]].sum(1) == 0).astype(float)
print("gated share (weighted)", (gate * w).sum() / w.sum())
WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]; Y3 = outcome("r")[:, PRIM]; BUD = [50, 100, 200]
z = np.load(R3 / "P_r3.npz"); Pp = {k: np.stack([z[f"pooled|{k}|{d}"] for d in range(3)], 1) for k in ("P-K", "P-I", "P-O")}
def b5(q, gated):
    g_ = gate if gated else 1; d = 1
    gr = np.linspace(0, 1, 401)[:, None]; t = np.ones(n) * g_
    return dict(T=gr * t[None], G=gr * (WV3[d] * Y3[:, d] * q * g_)[None], R=gr * (Y3[:, d] * q * g_)[None])
draws = Boot(300).draws; rows = []
for q in (0.9, 0.7):
    pols = {k: policy(Pp[k], WV3, q, RHO3, Y3) for k in Pp}; pols["B5"] = b5(q, False); pols["B5-lex"] = b5(q, True)
    B0 = b0(Y3, WV3, w)
    ev = lambda wb: {k: {B: v[0] for B, v in at_budgets(pols[k], wb, BUD).items()} for k in pols}
    pt = ev(w); res = {m: [dict(b0=b0(Y3, WV3, wb), **ev(wb)) for wb in ws] for m, ws in draws.items()}
    def ci(g):
        lo, hi = [], []
        for m, rs in res.items(): a, b = np.percentile([g(r) for r in rs], [2.5, 97.5]); lo.append(a); hi.append(b)
        return min(lo), max(hi)
    for B in BUD:
        for k in pols:
            lo, hi = ci(lambda x: x[k][B] / x["b0"]); rows.append(dict(q=q, T=B, what=k, pct_B0=100 * pt[k][B] / B0, lo=100 * lo, hi=100 * hi, weighted_per1000=pt[k][B]))
        for a, b in [("B5-lex", "B5"), ("B5-lex", "P-K"), ("B5-lex", "P-O"), ("B5-lex", "P-I"), ("P-I", "B5-lex"), ("P-O", "B5-lex"), ("P-K", "B5-lex")]:
            lo, hi = ci(lambda x: (x[a][B] - x[b][B]) / x["b0"]); rows.append(dict(q=q, T=B, what=f"{a} minus {b}", pct_B0=100 * (pt[a][B] - pt[b][B]) / B0, lo=100 * lo, hi=100 * hi))
D = pd.DataFrame(rows); D.to_csv(O / "b5lex.csv", index=False); print(D.round(2).to_string())
