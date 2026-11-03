"""value_of_cue round 2: q sweep and break-even q for the signal policies (pooled outcome, primary scope), plus per-writer spread of P-I. Needs round2/signals_P.npz (from frontier_value_of_cue_signals.py)."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frontier_value_of_cue_lib import *
R2 = OUT / "round2"; z = np.load(R2 / "signals_P.npz"); WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]; Y = outcome("r")[:, PRIM]; pr = np.array([(w * Y[:, d]).sum() / w.sum() for d in range(3)]); B0 = b0(Y, WV3, w)
P = {k: np.stack([z[f"pooled|{k}|{d}"] for d in range(3)], 1) for k in ("P-K", "P-X", "P-I", "P-ALL", "P-O", "P-IO")}
boot = Boot(300); rows = []
def curves(q):
    c = {k: policy(P[k], WV3, q, RHO3, Y) for k in P}; c["B5"], _ = b5_curves(WV3, q, RHO3, Y, pr); c["B1"] = b1_curves(WV3, q, RHO3, Y); return c
def ci(vals): return np.percentile(vals, [2.5, 97.5])
for q in (0.5, 0.7, 0.9, 1.0):
    c = curves(q)
    for B in (50, 100):
        g = {k: at_budget(v, w, B)[0] / B0 for k, v in c.items()}
        dr = {k: [] for k in ("P-I", "P-O", "P-IO")}
        for wb in boot.draws["both"]:
            b = b0(Y, WV3, wb); b5 = at_budget(c["B5"], wb, B)[0]
            for k in dr: dr[k].append((at_budget(c[k], wb, B)[0] - b5) / b)
        r = dict(q=q, budget=B, **{k: v for k, v in g.items()})
        for k in dr: lo, hi = ci(dr[k]); r[f"{k}_minus_B5"] = g[k] - g["B5"]; r[f"{k}_minus_B5_lo"] = lo; r[f"{k}_minus_B5_hi"] = hi
        rows.append(r)
pd.DataFrame(rows).to_csv(R2 / "signals_q_sweep.csv", index=False); print(pd.DataFrame(rows).round(3).to_string())
be = []
for q in np.round(np.arange(0.3, 1.0001, 0.05), 2):
    c = curves(q); be.append(dict(q=q, **{k: at_budget(c[k], w, 100)[0] / B0 for k in ("P-I", "P-O", "B5", "B1")}))
pd.DataFrame(be).assign(PI_minus_B5=lambda d: d["P-I"] - d["B5"], PO_minus_B5=lambda d: d["P-O"] - d["B5"]).to_csv(R2 / "signals_breakeven_q.csv", index=False)
# per-writer spread of P-I and P-O at the pooled T=100 operating point
for k in ("P-I", "P-O"):
    c = policy(P[k], WV3, Q0, RHO3, Y); t = 1000 * (c["T"] @ w) / w.sum(); li = int(np.argmin(np.abs(t - 100))); rr = []
    for wi in range(20):
        m = wid == wi; ww = w[m]; b = 1000 * ((Y[m] * WV3).sum(1) @ ww) / ww.sum(); rr.append(dict(writer=writers[wi], policy=k, rel=1000 * (c["G"][li][m] @ ww) / ww.sum() / b, taps=1000 * (c["T"][li][m] @ ww) / ww.sum()))
    D = pd.DataFrame(rr); D.to_csv(R2 / f"per_writer_{k}.csv", index=False); print(k, "median writer rel", D.rel.median(), "IQR", D.rel.quantile([.25, .75]).tolist(), "writers>0:", int((D.rel > 0).sum()), "taps range", D.taps.min(), D.taps.max())
