"""value_of_cue round 2: per-writer heterogeneity of the primary-scope gain at the pooled T=100 operating point (fixed lambda), P-K(noLex) vs B5 at the same realised taps. CPU."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frontier_value_of_cue_lib import *
R2 = OUT / "round2"; Y3 = outcome("r")[:, PRIM]; WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]; P = np.load(R2 / "P_noLex_prim.npy"); pr = np.array([(w * Y3[:, d]).sum() / w.sum() for d in range(3)])
pk = policy(P, WV3, Q0, RHO3, Y3); b5, _ = b5_curves(WV3, Q0, RHO3, Y3, pr); s = w.sum()
t = 1000 * (pk["T"] @ w) / s; li = int(np.argmin(np.abs(t - 100))); rows = []
f5 = (pk["T"][li] @ w) / s / 1.0                                          # B5 = SHOW-TWO on speech act for a random fraction f of messages at the same pooled taps
f5 = f5; v5 = WV3[1] * Y3[:, 1] * Q0
for wi, wr in enumerate(writers):
    m = wid == wi; ww = w[m]; b0w = 1000 * ((Y3[m] * WV3).sum(1) @ ww) / ww.sum()
    g = 1000 * (pk["G"][li][m] @ ww) / ww.sum(); tp = 1000 * (pk["T"][li][m] @ ww) / ww.sum(); g5 = f5 * 1000 * (v5[m] @ ww) / ww.sum()
    rows.append(dict(writer=wr, B0=b0w, PK_averted=g, PK_taps=tp, B5_averted_same_pooled_prompt_rate=g5, PK_rel=g / b0w, B5_rel=g5 / b0w, PK_minus_B5=g - g5))
D = pd.DataFrame(rows); D.to_csv(R2 / "per_writer_T100.csv", index=False)
print(D.round(3).to_string()); print("writers with P-K > B5:", int((D.PK_minus_B5 > 0).sum()), "of", len(D), "median rel PK", D.PK_rel.median(), "median rel B5", D.B5_rel.median())
json.dump(dict(n_writers=len(D), pk_gt_b5=int((D.PK_minus_B5 > 0).sum()), median_PK_rel=float(D.PK_rel.median()), q25=float(D.PK_rel.quantile(.25)), q75=float(D.PK_rel.quantile(.75)), median_B5_rel=float(D.B5_rel.median())), open(R2 / "per_writer_summary.json", "w"))
