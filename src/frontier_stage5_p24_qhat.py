"""Stage 5 Part 24 (value_of_cue): measured q (cue-supply rate), wrong-pick rate m, adequacy, kappa. Rules: annotation/COORDINATOR_STEPS.md section 5 (Part 24).
    . .venv/bin/activate && python src/frontier_stage5_p24_qhat.py   ->  analysis/frontier/value_of_cue/human_*.csv, human_q.json"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/value_of_cue"; B = 10000; rng = np.random.default_rng(20261117)
key = pd.read_csv(ROOT / "annotation/frontier_value_of_cue_key.csv").rename(columns={"item_id": "msg_item"})
r = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "annotation/returns_part24/*.csv")))]); r = r[r.practice == 0]
a = pd.read_csv(ROOT / "annotation/assignments/stage5_frontier_assignment.csv"); a = a[a.part == "part24"]
assert set(zip(a.item_id, a.annotator)) == set(zip(r.item_id, r.annotator)) and r.groupby("item_id").size().eq(2).all()
d = r.merge(key, left_on="item_id", right_on="id")
d["q1"] = d.q1_neg.fillna(d.q1_act).fillna(d.q1_pol)
alt = d.alternative_is
d["q2_alt"] = (d.q2 == alt).astype(int); d["q2_def"] = (d.q2 == d.default_is).astype(int); d["q2_neither"] = (d.q2 == "neither").astype(int)
d["q1_alt"] = (d.q1 == alt).astype(int); d["q1_def"] = (d.q1 == d.default_is).astype(int); d["q1_both_neither"] = d.q1.isin(["both", "neither"]).astype(int)
def cluster_ci(g, col):
    items = g.item_id.unique(); idx = {i: np.where(g.item_id.to_numpy() == i)[0] for i in items}; v = g[col].to_numpy(float)
    est = v.mean(); bs = []
    for _ in range(B):
        pick = rng.choice(len(items), len(items)); vals = np.concatenate([v[idx[items[p]]] for p in pick]); bs.append(vals.mean())
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(g), g.item_id.nunique()
rows = []
def add(name, g, col):
    e, lo, hi, nj, ni = cluster_ci(g, col); rows.append(dict(set=name, measure=col, est=e, lo=lo, hi=hi, n_judgments=nj, n_items=ni))
for st, sg in d.groupby("stratum"):
    for dim, g in list(sg.groupby("dimension")) + [("ALL", sg)]:
        nm = f"{st}|{dim}"
        for c in ("q2_alt", "q2_def", "q2_neither", "q1_alt", "q1_def", "q1_both_neither"): add(nm, g, c)
R = pd.DataFrame(rows); R.to_csv(OUT / "human_q_estimates.csv", index=False)
# kappa between the two annotators of an item on Q2 (3 categories), item-cluster CI
def kappa(x, y):
    cats = sorted(set(x) | set(y)); po = np.mean(x == y); pe = sum(np.mean(x == c) * np.mean(y == c) for c in cats); return (po - pe) / (1 - pe) if pe < 1 else np.nan
def pair(g, col):
    s = g.sort_values(["item_id", "annotator"]).groupby("item_id")[col].apply(list); s = s[s.map(lambda z: all(isinstance(t, str) for t in z))]
    return np.array([z[0] for z in s]), np.array([z[1] for z in s])
kap = []
for nm, g in [("A speech_act", d[(d.stratum == "A_cue_lost") & (d.dimension == "speech_act")]), ("B all", d[d.stratum.str.startswith("B")]), ("A+B all", d)]:
    for col in ("q2", "q1"):
        x, y = pair(g, col)
        if len(x) < 5: continue
        k0 = kappa(x, y); bs = []
        for _ in range(B):
            p = rng.integers(0, len(x), len(x)); bs.append(kappa(x[p], y[p]))
        kap.append(dict(set=nm, question=col, kappa=k0, lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5), pct_agree=float(np.mean(x == y)), n_items=len(x)))
K = pd.DataFrame(kap); K.to_csv(OUT / "human_q_kappa.csv", index=False)
# Q1 vs Q2 consistency in stratum A speech act (cross-check)
sa = d[(d.stratum == "A_cue_lost") & (d.dimension == "speech_act")]
rel = lambda x, row: "alt" if x == row.alternative_is else ("default" if x == row.default_is else x)
cross = pd.crosstab(sa.apply(lambda z: rel(z.q1, z), axis=1), sa.apply(lambda z: rel(z.q2, z), axis=1)); cross.to_csv(OUT / "human_q_q1_q2_crosstab_speech_act.csv")
# item-level: both annotators pick the alternative / neither / split
it = sa.groupby("item_id").q2_alt.sum().value_counts().sort_index().to_dict()
# per-annotator q (heterogeneity)
pa = sa.groupby("annotator").q2_alt.agg(["mean", "size"]).reset_index(); pa.to_csv(OUT / "human_q_per_annotator_speech_act.csv", index=False)
# denominator: q conditional on a pick (excluding neither)
pick = sa[sa.q2 != "neither"]; cq = cluster_ci(pick, "q2_alt")
out = dict(qhat_speech_act=R[(R.set == "A_cue_lost|speech_act") & (R.measure == "q2_alt")].iloc[0].to_dict(), q1_alt_speech_act=R[(R.set == "A_cue_lost|speech_act") & (R.measure == "q1_alt")].iloc[0].to_dict(),
           q_given_pick_speech_act=dict(est=cq[0], lo=cq[1], hi=cq[2], n_judgments=cq[3], n_items=cq[4]), both_annotators_alt_counts=it,
           m_B_all=R[(R.set == "B_control_no_cue_in_source|ALL") & (R.measure == "q2_alt")].iloc[0].to_dict())
json.dump(out, open(OUT / "human_q.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); print(R.round(3).to_string()); print(K.round(3).to_string()); print(cross); print(it); print(pa.round(2).to_string()); print(cq)
