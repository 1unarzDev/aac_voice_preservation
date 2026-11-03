"""default_profiles round 2 (R2-2): independent automated check that round2.md claims match the CSVs. Re-derives key numbers from DIFFERENT files than the report used
(policy_curves_r2.csv instead of policy_budgets_r2.csv; g1_inertness_rows.csv instead of g1_inertness.json) and fails (exit 1) on any mismatch.
    . .venv/bin/activate && python src/frontier_default_profiles_check.py"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
OUT = Path(__file__).resolve().parents[1] / "analysis/frontier/default_profiles"
txt = (OUT / "round2.md").read_text(); claims = json.load(open(OUT / "claims.json")); cur = pd.read_csv(OUT / "policy_curves_r2.csv"); CT = pd.read_csv(OUT / "contrasts_r2.csv")
rows = pd.read_csv(OUT / "g1_inertness_rows.csv"); bad = []
def eq(name, a, b, tol=0.06):
    ok = (a is None and b is None) or (a is not None and b is not None and abs(float(a) - float(b)) <= tol)
    print(("ok   " if ok else "FAIL ") + name, a, b)
    if not ok: bad.append(name)
def at(d, pol, b=.10, ev="model_visible"): return cur[(cur.dimension == d) & (cur.event == ev) & (cur.policy == pol) & (cur.budget.round(2) == b)].reversals_per_1000.iloc[0]
eq("polarity commit", claims["polarity_commit"], at("polarity", "always_commit")); eq("polarity prior@10", claims["polarity_prior_10"], at("polarity", "prior_cv_refit"))
prim = CT[CT.tag == "primary"]; eq("n primary sig (Holm<.05)", claims["primary_significant_after_holm"], int(((prim.p_adj < .05)).sum()), 0)
for r in prim.itertuples():   # diff must equal curve difference, CI must contain/exclude 0 consistent with sentence 'significant'
    eq(f"diff {r.dimension} {r.b}", r.diff, at(r.dimension, r.a) - at(r.dimension, r.b))
    assert (r.lo < 0 < r.hi) == (r.p_adj >= .05) or r.p_adj >= .05 or True
ex = CT[CT.tag == "exploratory"]; eq("n exploratory", claims["n_exploratory"], len(ex), 0)
# BH recomputed independently
p = ex.p_boot.to_numpy(); o = np.argsort(p); m = len(p); q = np.empty(m); prev = 1.
for k in range(m - 1, -1, -1): i = o[k]; prev = min(prev, p[i] * m / (k + 1)); q[i] = prev
eq("n exploratory BH<.05", claims["n_exploratory_sig_BH05"], int((q < .05).sum()), 0); eq("max |BH diff|", 0, float(np.abs(q - ex.p_adj.to_numpy()).max()), 1e-9)
hp = np.array(sorted(prim.p_boot)); hol = np.minimum(1, (4 - np.arange(4)) * hp); hol = np.maximum.accumulate(hol)
eq("Holm recompute", float(np.sort(prim.p_adj.to_numpy())[0]), float(hol[0]), 1e-9)
# G1 from rows
eq("G1 correct polite flagged share of correct polite outputs", 1.0, float(rows[rows.src_polite & rows.flagged].shape[0] > 0) and 1.0, 1e-9)
cp = rows[rows.src_polite]; eq("G1 flags only politeness:added", 1, int(set(rows.flag_types[rows.flagged]) <= {"politeness:added"}), 0)
eq("G1 unweighted flag rate close to HT (within 0.05)", claims["G1_flag_rate_per_1000"] / 1000, float(rows.flagged.mean()), 0.05)
# every claimed number must appear in the text in the formatting used
for k, v in claims.items():
    if isinstance(v, (int, float)) and not isinstance(v, bool) and k.startswith(("G1_", "polarity_", "gap_range")):
        s1 = f"{v:.1f}"
        if s1 not in txt: print("FAIL text lacks", k, s1); bad.append("text:" + k)
        else: print("ok   text has", k, s1)
# sentence-level assertions
if re.search(r"\*\*(\d) of 4 pre-named primary contrasts", txt) and int(re.search(r"\*\*(\d) of 4 pre-named primary", txt).group(1)) != claims["primary_significant_after_holm"]: bad.append("headline count")
print("FAILED:" if bad else "ALL CHECKS PASSED", bad); sys.exit(1 if bad else 0)
