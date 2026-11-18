"""Stage 5 Part 23 (whole_message R-WM-1 human scoring). Rules: annotation/COORDINATOR_STEPS.md section 5 (Part 23) + analysis/frontier/whole_message/ANNOTATION_REQUEST.md.
    . .venv/bin/activate && python src/frontier_stage5_p23_whole_message.py  -> analysis/frontier/whole_message/human_*.csv, human_summary.json"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/whole_message"; B = 4000; rng = np.random.default_rng(20261117)
key = pd.read_csv(ROOT / "annotation/frontier_whole_message_key.csv")
r = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "annotation/returns_part23/*.csv")))]); r = r[r.practice == 0]
a = pd.read_csv(ROOT / "annotation/assignments/stage5_frontier_assignment.csv"); a = a[a.part == "part23"]
assert set(zip(a.item_id, a.annotator)) == set(zip(r.item_id, r.annotator)) and r.groupby("item_id").size().eq(3).all()
def maj(vals, ok=None):
    """2-of-3 label; three different answers -> 'NOCONS'"""
    v = [x for x in vals]; 
    for c in set(v):
        if v.count(c) >= 2: return c
    return "NOCONS"
rows = []
for iid, g in r.groupby("item_id"):
    rows.append(dict(id=iid, q1=maj(g.q1.tolist()) if g.q1.notna().all() else None, q2=maj(g.q2.tolist()) if g.q2.notna().all() else None, q3=maj(g.q3.tolist()) if g.q3.notna().all() else None,
                     q4=maj(g.q4.tolist()) if g.q4.notna().all() else None, q5=maj(g.q5.tolist()) if g.q5.notna().all() else None,
                     n_accept=int(g.q3.isin(["yes", "yes with a small edit"]).sum()), n_yes=int((g.q3 == "yes").sum()), n_added=int(g.q2.isin(["added", "both"]).sum()), n_left=int(g.q2.isin(["left out", "both"]).sum()),
                     n_q1_intended=None))
H = pd.DataFrame(rows).merge(key, on="id")
O = H[H.kind == "output"].copy(); V = H[H.kind == "verbatim_copy"].copy()
# per-judgment match counts
rr = r.merge(key[["id", "intended_variant"]], left_on="item_id", right_on="id"); mm = rr.assign(m=(rr.q1 == rr.intended_variant).astype(int)).groupby("item_id").m.sum()
O["n_match"] = O.id.map(mm)
O["accept"] = (O.n_accept >= 2).astype(int); O["accept_strict"] = (O.n_yes >= 2).astype(int); O["match"] = (O.q1 == O.intended_variant).astype(int); O["match_any2"] = (O.n_match >= 2).astype(int)
O["added"] = (O.n_added >= 2).astype(int); O["left_out"] = (O.n_left >= 2).astype(int); O["reject"] = 1 - O.accept
O["q3_nocons"] = ((O.n_accept == 1) & (O.n_yes < 2) & False).astype(int)
O["q1_nocons"] = (O.q1 == "NOCONS").astype(int); O["q1_else"] = (O.q1 == "something else").astype(int)
O.to_csv(OUT / "human_items.csv", index=False); V.to_csv(OUT / "human_verbatim_items.csv", index=False)
fams = sorted(O.family_id.unique()); fidx = {f: np.where(O.family_id.to_numpy() == f)[0] for f in fams}
class SimpleNamespace(dict):
    __getattr__ = dict.__getitem__
def cl_ci(fn, df=None, Bn=B):
    """family-cluster bootstrap (resample families = inputs, keep all arms of a family together); fn gets an object with numpy columns"""
    df = O if df is None else df; cols = {c: df[c].to_numpy() for c in df.columns}; fam = cols["family_id"]; idx = {f: np.where(fam == f)[0] for f in np.unique(fam)}; fl = list(idx)
    est = fn(SimpleNamespace(cols)); bs = []
    for _ in range(Bn):
        p = rng.integers(0, len(fl), len(fl)); ii = np.concatenate([idx[fl[j]] for j in p]); bs.append(fn(SimpleNamespace({c: v[ii] for c, v in cols.items()})))
    bs = np.array(bs, float); return est, np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5)
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
# ---- per-arm rates
rows = []
for col, nm in [("accept", "acceptable (Q3 yes or small edit, 2 of 3)"), ("accept_strict", "acceptable as-is (Q3 yes, 2 of 3)"), ("match", "Q1 = intended version (2 of 3)"), ("match_any2", "Q1 = intended (same)"), ("added", "added content (Q2 added or both, 2 of 3)"), ("left_out", "left out (Q2 left out or both, 2 of 3)"), ("q1_else", "Q1 = something else (2 of 3)")]:
    if col == "match_any2": continue
    for arm, g in list(O.groupby("arm")) + [("ALL", O)]:
        e, lo, hi = cl_ci(lambda d: d[col].mean(), g); rows.append(dict(measure=nm, arm=arm, est=e, lo=lo, hi=hi, k=int(g[col].sum()), n=len(g), n_families=g.family_id.nunique()))
AR = pd.DataFrame(rows); AR.to_csv(OUT / "human_arm_rates.csv", index=False)
# judgment-level (each rater answer) sensitivity
rj = r.merge(key[["id", "arm", "family_id", "intended_variant", "kind"]], left_on="item_id", right_on="id"); rj = rj[rj.kind == "output"]
rj["accept"] = rj.q3.isin(["yes", "yes with a small edit"]).astype(int); rj["added"] = rj.q2.isin(["added", "both"]).astype(int); rj["match"] = (rj.q1 == rj.intended_variant).astype(int)
rows = []
for col in ("accept", "added", "match"):
    for arm, g in list(rj.groupby("arm")) + [("ALL", rj)]:
        e, lo, hi = cl_ci(lambda d: d[col].mean(), g); rows.append(dict(measure=col + " (per rater judgment)", arm=arm, est=e, lo=lo, hi=hi, n_judgments=len(g)))
pd.DataFrame(rows).to_csv(OUT / "human_arm_rates_judgment_level.csv", index=False)
# ---- paired contrasts (same input: family x variant), family cluster
piv = {c: O.pivot(index="family_id", columns="arm", values=c) for c in ("accept", "accept_strict", "match", "added", "left_out")}
rows = []
for c, p in piv.items():
    for x, y in (("A2", "A0"), ("A1", "A0"), ("A2", "A1")):
        d = (p[x] - p[y]).to_numpy(float); n = len(d); est = d.mean(); bs = np.array([d[rng.integers(0, n, n)].mean() for _ in range(B)])
        rows.append(dict(measure=c, contrast=f"{x} - {y}", diff=est, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), n_inputs=n, x_only=int(((p[x] == 1) & (p[y] == 0)).sum()), y_only=int(((p[x] == 0) & (p[y] == 1)).sum())))
PC = pd.DataFrame(rows); PC.to_csv(OUT / "human_paired.csv", index=False)
# ---- agreement (Fleiss kappa, 3 raters per item)
def fleiss(df, col):
    d = rj if True else None; cats = sorted(d[col].dropna().unique()); M = np.array([[ (g[col] == c).sum() for c in cats] for _, g in d.groupby("item_id")]); N = M.sum(1)[0]
    P = (M * (M - 1)).sum(1) / (N * (N - 1)); Pbar = P.mean(); pj = M.sum(0) / M.sum(); Pe = (pj ** 2).sum(); return (Pbar - Pe) / (1 - Pe), Pbar
rj["q1c"] = rj.q1; rj["q2c"] = rj.q2; rj["q3c"] = rj.q3
agr = []
for col in ("q1c", "q2c", "q3c"):
    k_, pa = fleiss(None, col); idx = {i: np.where(rj.item_id.to_numpy() == i)[0] for i in rj.item_id.unique()}; il = list(idx); bs = []
    cats = sorted(rj[col].dropna().unique())
    M = np.array([[(rj.iloc[idx[i]][col] == c).sum() for c in cats] for i in il])
    for _ in range(2000):
        m_ = M[rng.integers(0, len(il), len(il))]; P = (m_ * (m_ - 1)).sum(1) / 6; Pe = ((m_.sum(0) / m_.sum()) ** 2).sum(); bs.append((P.mean() - Pe) / (1 - Pe))
    agr.append(dict(question=col[:2], fleiss_kappa=k_, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), mean_pairwise_agreement=pa, n_items=len(il), unanimous=float((M.max(1) == 3).mean()), no_consensus=float((M.max(1) == 1).mean())))
pd.DataFrame(agr).to_csv(OUT / "human_agreement.csv", index=False)
# ---- judge flag vs human added content
def kappa2(x, y):
    x = np.asarray(x, int); y = np.asarray(y, int); po = (x == y).mean(); pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean()); return (po - pe) / (1 - pe) if pe < 1 else np.nan
def auroc(score, y):
    score = np.asarray(score, float); y = np.asarray(y, int); p = score[y == 1]; n = score[y == 0]
    if len(p) == 0 or len(n) == 0: return np.nan
    return float(((p[:, None] > n[None]).sum() + .5 * (p[:, None] == n[None]).sum()) / (len(p) * len(n)))
rows = []
for nm, fn in [("kappa gpt_UC vs human added (2 of 3)", lambda d: kappa2(d.gpt_UC, d.added)), ("agreement", lambda d: float((d.gpt_UC.astype(int) == d.added).mean())),
               ("sensitivity (flag | human added)", lambda d: (float(d.gpt_UC[d.added == 1].mean()) if (d.added == 1).any() else np.nan)), ("specificity (no flag | human not added)", lambda d: (float(1 - d.gpt_UC[d.added == 0].mean()) if (d.added == 0).any() else np.nan)),
               ("AUROC gpt_UC (binary) for human added", lambda d: auroc(d.gpt_UC, d.added)), ("AUROC -gpt_score for human added", lambda d: auroc(-d.gpt_score, d.added)),
               ("AUROC gpt_UC for human 'added or left out'", lambda d: auroc(d.gpt_UC, ((d.added + d.left_out) >= 1).astype(int)))]:
    e, lo, hi = cl_ci(fn); rows.append(dict(measure=nm, est=e, lo=lo, hi=hi, n_outputs=len(O)))
JV = pd.DataFrame(rows); JV.to_csv(OUT / "human_judge_vs_added.csv", index=False)
print("human added rate by arm vs flag rate by arm"); print(O.groupby("arm")[["added", "gpt_UC", "accept", "match", "left_out"]].mean().round(3))
# ---- metric validity: AUROC for human rejection (not acceptable)
t = pd.read_csv(OUT / "r2_outputs.csv"); t = t[(t.generator == "gpt-6.1-terra") & (t.channel == "chip1") & (t.draw == 0)][["family_id", "variant", "arm", "CK", "reversal", "nwords", "ref", "ref_score", "gpt_free_score", "Q14_p", "Nemo_p", "crit", "critical_value", "fragment"]]
O2 = O.merge(t, on=["family_id", "variant", "arm"], how="left"); assert len(O2) == 108 and O2.CK.notna().all()
O2["kw_words"] = O2.input_text.str.replace(r"\[[A-Z?]+\]", "", regex=True).str.split().str.len() if "input_text" in O2 else np.nan
items = json.load(open(ROOT / "annotation/frontier_whole_message_items.json"))["items"]; it = {i["id"]: i for i in items}
O2["kw_words"] = [len(__import__("re").sub(r"\[[A-Za-z?]+\]", " ", it[i]["input_text"].replace("Keywords:", "")).split()) for i in O2.id]; O2["lenratio"] = O2.nwords / O2.kw_words.clip(lower=1)
O2["out_words"] = O2.text.str.split().str.len(); O2["lenratio"] = O2.out_words / O2.kw_words.clip(lower=1)
O2.to_csv(OUT / "human_items_with_machine_scores.csv", index=False)
rows = []
for target, tn in (("reject", "human rejection (Q3 no, 2 of 3)"), ("added", "human added content"), ("match_no", "human Q1 not the intended version")):
    O2["match_no"] = 1 - O2["match"]
    for nm, sc in [("critical-only reversal flag (1-CK)", 1 - O2.CK), ("gpt_UC flag (reference-free)", O2.gpt_UC), ("-gpt_score (1-5 reference-free)", -O2.gpt_score), ("output length / keyword words", O2.lenratio), ("output words", O2.out_words),
                   ("-ref_score (sees writer sentence)", -O2.ref_score.fillna(O2.ref_score.mean()))]:
        O2["_s"] = sc.to_numpy(float); e, lo, hi = cl_ci(lambda d: auroc(d._s, d[target]), O2); rows.append(dict(target=tn, score=nm, auroc=e, lo=lo, hi=hi, n=len(O2), n_positive=int(O2[target].sum())))
MV = pd.DataFrame(rows); MV.to_csv(OUT / "human_metric_validity.csv", index=False)
# acceptability by critical correctness (does keeping the critical commitment predict human acceptance?)
cx = O2.groupby("CK").agg(n=("accept", "size"), accept=("accept", "mean"), match=("match", "mean"), added=("added", "mean")).reset_index(); cx.to_csv(OUT / "human_by_critical_kept.csv", index=False)
cu = O2.groupby(["CK", "gpt_UC"]).agg(n=("accept", "size"), accept=("accept", "mean"), match=("match", "mean")).reset_index(); cu.to_csv(OUT / "human_by_critical_and_flag.csv", index=False)
# among critical-kept: accept by gpt_UC
# ---- verbatim stratum
vq = r.merge(key, left_on="item_id", right_on="id"); vq = vq[vq.kind == "verbatim_copy"]
vrows = []
for q, nm in (("q4", "says something beyond keywords (Q4 yes)"), ("q5", "complete sentence, sayable as is (Q5 yes)")):
    yes_item = V[q].eq("yes").sum(); yes_j = (vq[q] == "yes").sum(); vrows.append(dict(measure=nm, items_majority_yes=int(yes_item), n_items=len(V), wilson_lo=wilson(yes_item, len(V))[0], wilson_hi=wilson(yes_item, len(V))[1], judgments_yes=int(yes_j), n_judgments=len(vq)))
vrows.append(dict(measure="gpt_UC flag on the 12 copies (mean)", items_majority_yes=int(V.gpt_UC.sum()), n_items=len(V), wilson_lo=wilson(int(V.gpt_UC.sum()), len(V))[0], wilson_hi=wilson(int(V.gpt_UC.sum()), len(V))[1]))
pd.DataFrame(vrows).to_csv(OUT / "human_verbatim.csv", index=False)
summ = dict(n_outputs=len(O), n_verbatim=len(V), n_annotators=int(r.annotator.nunique()), q1_nocons=int(O.q1_nocons.sum()), q3_dist=O.q3.value_counts().to_dict(), q1_dist=O.q1.value_counts().to_dict(), q2_dist=O.q2.value_counts().to_dict(),
            n_distinct_pairs=int(O.drop_duplicates(["family_id", "variant", "text"]).shape[0]))
json.dump(summ, open(OUT / "human_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
for t_ in (AR, PC, pd.DataFrame(agr), JV, MV, cx, cu, pd.DataFrame(vrows)): print(t_.round(3).to_string()); print()
print(summ)
# ---- paired AUROC deltas (same outputs, family cluster): human rejection
O2["rej"] = O2["reject"]; rows = []
for a_, b_ in (("lenratio", "gpt_score"), ("out_words", "gpt_score"), ("lenratio", "CK_flag")):
    O2["CK_flag"] = 1 - O2.CK; O2["_a"] = O2[a_] * (-1 if a_ == "gpt_score" else 1); O2["_b"] = O2[b_] * (-1 if b_ == "gpt_score" else 1)
    e, lo, hi = cl_ci(lambda d: auroc(d._a, d.rej) - auroc(d._b, d.rej), O2); rows.append(dict(target="human rejection", delta=f"AUROC({a_}) - AUROC({b_})", est=e, lo=lo, hi=hi))
pd.DataFrame(rows).to_csv(OUT / "human_metric_paired.csv", index=False); print(pd.DataFrame(rows).round(3))
