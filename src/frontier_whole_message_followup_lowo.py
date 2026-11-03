"""F1 (whole_message follow-up): leave-one-writer-out AUROC of M1-free vs word count. Rule: PLAN.md 'Follow-up F1'."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from analyze_whole_message import auroc
D = ROOT / "analysis/frontier/whole_message"
F = pd.read_csv(D / "r2_validity_features.csv", keep_default_na=False)
F["L1"] = pd.to_numeric(F.L1, errors="coerce"); F = F[F.L1.notna()]
S = {"M1free": "M1free_gpt", "wc": "T1_wordcount"}
def strat(sub, col):
    # within-writer pairs: share of (rejected, accepted) pairs of the same writer ranked correctly (ties .5)
    n = c = 0
    for _, g in sub.groupby("writer"):
        p = g[g.L1 == 1][col].values; q = g[g.L1 == 0][col].values
        for a in p:
            for b in q: n += 1; c += 1.0 if a > b else .5 if a == b else 0
    return c / n if n else np.nan, n
rows = []; out = {}
for sn, sub in {"chip1": F[F.channel == "chip1"], "all200": F}.items():
    y = sub.L1.values; ws = sub.writer.values; U = np.unique(ws)
    full = {k: auroc(y, sub[c].values) for k, c in S.items()}
    lo = []
    for w in U:
        m = ws != w; a = auroc(y[m], sub[S["M1free"]].values[m]); b = auroc(y[m], sub[S["wc"]].values[m])
        lo.append((w, a, b, a - b)); rows.append(dict(subset=sn, dropped=w, auroc_m1free=a, auroc_wc=b, delta=a - b))
    d = np.array([x[3] for x in lo]); n = len(d); dfull = full["M1free"] - full["wc"]
    # delete-one jackknife SE of the delta
    se = np.sqrt((n - 1) / n * ((d - d.mean()) ** 2).sum()); 
    sa, na = strat(sub, S["M1free"]); sb, _ = strat(sub, S["wc"])
    out[sn] = dict(n=len(sub), writers=int(n), auroc_m1free=full["M1free"], auroc_wc=full["wc"], delta=dfull,
        lowo_m1free_min=min(x[1] for x in lo), lowo_m1free_max=max(x[1] for x in lo), lowo_wc_min=min(x[2] for x in lo), lowo_wc_max=max(x[2] for x in lo),
        lowo_delta_min=float(d.min()), lowo_delta_max=float(d.max()), jack_se=float(se), jack_ci=[float(dfull - 1.96 * se), float(dfull + 1.96 * se)],
        strat_auroc_m1free=sa, strat_auroc_wc=sb, strat_pairs=na, writers_most_influential=[lo[i][0] for i in np.argsort(-abs(d - dfull))[:3]])
    ok = out[sn]["jack_ci"][0] > 0 and d.min() > 0
    out[sn]["verdict"] = "SUPPORTED (flip)" if ok else ("parity" if out[sn]["jack_ci"][0] <= 0 <= out[sn]["jack_ci"][1] and max(abs(d)) < .10 else "inconclusive")
    out[sn]["m1free_threshold_.75_met_all_LOWO"] = bool(out[sn]["lowo_m1free_min"] >= .75)
pd.DataFrame(rows).to_csv(D / "followup_lowo.csv", index=False)
json.dump(out, open(D / "followup_summary.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
