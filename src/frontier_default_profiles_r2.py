"""default_profiles round 2 analysis (post-pilot amendments R2-1..R2-6, PLAN.md section 9, written before this ran).
    . .venv/bin/activate && python src/frontier_default_profiles_r2.py [--boot 500] [--procs 16]
0 generation. Inputs: stored elic1 outputs, probe files (runs/frontier_default_profiles_probe), verbalized arm (runs/frontier_default_profiles_verbal), g1_inertness.json,
chip_controls/channel_rates.csv, SLP panel. Outputs (analysis/frontier/default_profiles/): h1_belief_scale.csv, h1_reliability_bins.csv, policy_curves_r2.csv, policy_budgets_r2.csv,
contrasts_r2.csv, intervention_same_items.csv, acceptability_slp.csv, summary_r2.json."""
import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[k] = "1"
import argparse, json, re, sys, time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, scipy.sparse as sp
from scipy.optimize import minimize
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/default_profiles"
ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=500); ap.add_argument("--procs", type=int, default=16); ap.add_argument("--quick", action="store_true"); A = ap.parse_args()
SEED = 20261101; B = A.boot
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POLR = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)
DIMS = {"polarity": dict(src="neg", nocue="nocue_neg", out="out_neg", lex=NEG, kw="kw_neg"), "politeness": dict(src="polite", nocue="nocue_pol", out="out_pol", lex=POLR, kw="kw_pol"),
        "speech_act": dict(src="nonstmt", nocue="nocue_act", out="out_nonstmt", lex=ACT, kw="kw_act")}
DL = list(DIMS)
SLP = {"polarity": (5, 5), "speech_act": (4, 4), "politeness": (3, 2)}; WGT = {k: float(np.mean(v) / 5) for k, v in SLP.items()}
BUD = [.02, .05, .10, .20]; GRID = np.linspace(0, 1, 101); MARGIN = {"polarity": 5.0, "politeness": 10.0, "speech_act": 25.0}   # TOST margins, reversals per 1,000 (PLAN R2-6)
LAMS = [0.3, 1.0, 3.0, 10.0]

# ---------------------------------------------------------------- units (human keyword sets only; pos_cap4 secondary scope dropped in round 2)
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
msg["neg"] = [key[i]["detector_labels"]["polarity"] == "negated" for i in msg.item_id]
msg["polite"] = [key[i]["detector_labels"]["politeness"] != "none" for i in msg.item_id]
msg["nonstmt"] = [key[i]["detector_labels"]["speech_act"] != "statement" for i in msg.item_id]
msg["w"] = 1 / msg.inclusion_prob; msg["fam"] = "elic-" + msg.source_id; mi_ = msg.set_index("item_id"); NMSG = len(msg)
rows = []
for r in rat.itertuples():
    if not isinstance(r.keywords, str) or not r.keywords.strip(): continue
    m = mi_.loc[r.item_id]
    rows.append(dict(item_id=r.item_id, fam=m.fam, src_id=m.source_id, channel="human_" + r.annotator, kw=r.keywords.strip(), neg=m.neg, polite=m.polite, nonstmt=m.nonstmt, lost_act=r.speech_act_lenient_lost, w=m.w, sample=m["sample"]))
U = pd.DataFrame(rows); n = len(U)
U["kw_neg"] = U.kw.str.contains(NEG); U["kw_pol"] = U.kw.str.contains(POLR); U["kw_act"] = U.kw.str.contains(ACT)
U["nocue_neg"] = ~U.kw_neg; U["nocue_pol"] = ~U.kw_pol; U["nocue_act"] = np.where(U.nonstmt, U.lost_act.fillna(1).astype(bool), ~U.kw_act)
U["unit"] = U.item_id + "|" + U.channel; U["nw"] = U.kw.str.split().str.len()
U["mi"] = U.item_id.map({i: j for j, i in enumerate(msg.item_id)}); MI = U.mi.to_numpy(); WH = U.w.to_numpy()
for d, c in DIMS.items(): U["E_" + d] = (U[c["src"]].astype(bool) & U[c["nocue"]].astype(bool)).astype(float)
sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0") & sc.channel.str.startswith("human_")].rename(columns={"family_id": "fam"})
sc["out_neg"] = sc.polarity.eq("negated"); sc["out_pol"] = sc.politeness.ne("none"); sc["out_nonstmt"] = ~sc.speech_act.eq("statement")
SC = sc[["fam", "channel", "model", "out_neg", "out_pol", "out_nonstmt"]].merge(U[["fam", "channel", "unit"]], on=["fam", "channel"], how="inner"); MODELS4 = sorted(SC.model.unique())
EV = {}; GATE = {}; NOC = {}; SRC = {}; OUTM = {}   # per dim arrays aligned to U
for d, c in DIMS.items():
    miss = SC.assign(m=(~SC[c["out"]]).astype(float)).groupby("unit").m.mean(); mv = U.unit.map(miss).fillna(1.0).to_numpy()
    EV[(d, "exposure")] = U["E_" + d].to_numpy(); EV[(d, "model_visible")] = U["E_" + d].to_numpy() * mv
    GATE[d] = (~U[c["kw"]]).to_numpy(); NOC[d] = U[c["nocue"]].to_numpy().astype(bool); SRC[d] = U[c["src"]].to_numpy().astype(bool)
    OUTM[d] = {m: U.unit.map(SC[SC.model.eq(m)].set_index("unit")[c["out"]]).to_numpy() for m in MODELS4}
# probes
Q = {}
for m in ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "qwen2.5-14b", "mistral-nemo-12b"]:
    fn = ROOT / f"runs/frontier_default_profiles_probe/{m}.jsonl"
    if not fn.exists(): continue
    rr = pd.DataFrame([json.loads(l) for l in open(fn)]); rr["q"] = rr[["q0", "q1"]].mean(axis=1, skipna=False); P = rr.pivot(index="unit", columns="dim", values="q")
    if P.notna().sum().min() < 1500: print("skip incomplete probe", m, P.notna().sum().to_dict()); continue
    Q[m] = {d: U.unit.map(P[d]).to_numpy(float) for d in DL}
PM = sorted(Q); print("probe models", PM, flush=True)
VERB = {}; vf = ROOT / "runs/frontier_default_profiles_verbal/terra.jsonl"
if vf.exists():
    V = {j["kw"]: j for j in map(json.loads, open(vf))}
    for d, k in zip(DL, ("negation", "polite", "question_or_request")): VERB[d] = np.array([V[kw][k] / 100 if kw in V else np.nan for kw in U.kw])
VNKW = len(V) if vf.exists() else 0
if VNKW < 300: VERB = {}   # declared: fewer than 300 completed keyword strings is too small to evaluate; reported as not completed
VCOV = float(np.mean(~np.isnan(VERB["polarity"]))) if VERB else 0.0; print("verbal coverage of units", round(VCOV, 3), flush=True)
# features (unsupervised vocabulary, >=5 occurrences; no labels used)
FUNC = {"pron": re.compile(r"\b(i|me|my|you|your|we|us|he|she|they|them|it)\b", re.I), "modal": re.compile(r"\b(can|could|will|would|should|may|might|must|want|need|like)\b", re.I), "wh": re.compile(r"\b(what|where|when|who|why|how|which)\b", re.I)}
toks = U.kw.str.lower().str.findall(r"[a-z']+"); cnt = Counter(t for ts in toks for t in set(ts)); vocab = {t: i for i, t in enumerate(t for t, c_ in sorted(cnt.items()) if c_ >= 5)}
Xd = np.zeros((n, len(vocab) + 5))
for i, ts in enumerate(toks):
    for t in set(ts):
        if t in vocab: Xd[i, vocab[t]] = 1
    k = U.kw.iloc[i]; Xd[i, -5] = np.log1p(len(ts)); Xd[i, -4] = bool(FUNC["pron"].search(k)); Xd[i, -3] = bool(FUNC["modal"].search(k)); Xd[i, -2] = bool(FUNC["wh"].search(k)); Xd[i, -1] = len(ts) <= 2
XS = sp.csr_matrix(Xd)
TIE = np.random.default_rng(SEED + 7).random(n) * 1e-9
# strata + multiplicities
strata = [np.where(msg["sample"].eq(k_))[0] for k_ in ("random", "enriched")]
rng0 = np.random.default_rng(SEED); MULT = [np.ones(NMSG)]
for _ in range(B):
    mu = np.zeros(NMSG)
    for s_ in strata: np.add.at(mu, rng0.choice(s_, len(s_)), 1)
    MULT.append(mu)

# ---------------------------------------------------------------- helpers
def fit(X, y, w, lam):
    w = w / w.mean(); XT = X.T.tocsr(); p = X.shape[1]
    def fg(t):
        z = X @ t[:-1] + t[-1]; pr = 1 / (1 + np.exp(-z)); r = w * (pr - y)
        return np.sum(w * (np.logaddexp(0, z) - y * z)) + .5 * lam * np.sum(t[:-1]**2), np.append(XT @ r + lam * t[:-1], r.sum())
    return minimize(fg, np.zeros(p + 1), jac=True, method="L-BFGS-B", options=dict(maxiter=150, ftol=1e-8)).x
def predict(X, t): return 1 / (1 + np.exp(-(X @ t[:-1] + t[-1])))
def wll(y, p, w): p = np.clip(p, 1e-6, 1 - 1e-6); return float(np.sum(w * -(y * np.log(p) + (1 - y) * np.log(1 - p))) / max(w.sum(), 1e-12))
def prior_scores(d, ww, mu, seed):
    """grouped 5-fold CV (copies of a message share a fold); lambda chosen inside each outer training fold by inner grouped 3-fold weighted log-loss."""
    elig = GATE[d]; y = SRC[d].astype(float); r = np.random.default_rng(seed); msgs = np.where(mu > 0)[0]; fo = np.full(NMSG, -1); fo[msgs] = r.permutation(len(msgs)) % 5
    f = fo[MI]; s = np.zeros(n)
    for k in range(5):
        tr = (f != k) & (f >= 0) & elig & (ww > 0); te = (f == k) & elig
        if te.sum() == 0: continue
        trm = np.unique(MI[tr]); inn = dict(zip(trm, r.permutation(len(trm)) % 3)); fi = np.array([inn.get(m_, -1) for m_ in MI]); best = (1e18, 1.0)
        for lam in LAMS:
            L = 0.0
            for j in range(3):
                a = tr & (fi != j); b = tr & (fi == j)
                if b.sum() == 0 or a.sum() == 0: continue
                t = fit(XS[a], y[a], ww[a], lam); L += wll(y[b], predict(XS[b], t), ww[b]) * ww[b].sum()
            if L < best[0]: best = (L, lam)
        t = fit(XS[tr], y[tr], ww[tr], best[1]); s[te] = predict(XS[te], t)
    return np.where(elig, s, 0.0)
def curve(score, ww, ev):
    o = np.argsort(-(score + TIE), kind="stable"); W = ww.sum(); cw = np.concatenate([[0], np.cumsum(ww[o]) / W]); ce = np.concatenate([[0], np.cumsum((ww * ev)[o]) / W]); tot = (ww * ev).sum() / W
    return 1000 * (tot - np.interp(GRID, cw, ce))
def rand_gated(d, ww, ev):
    W = ww.sum(); g = (ww * GATE[d]).sum() / W; f = np.minimum(1, GRID / max(g, 1e-12)); tot_g = (ww * ev * GATE[d]).sum() / W; tot_n = (ww * ev * ~GATE[d]).sum() / W
    return 1000 * (tot_n + tot_g * (1 - f))
def wauc(sc_, y, w):
    ok = w > 0; sc_, y, w = sc_[ok], y[ok].astype(bool), w[ok]
    if y.sum() == 0 or (~y).sum() == 0: return np.nan
    u, inv = np.unique(sc_, return_inverse=True); pos = np.bincount(inv, weights=w * y); neg = np.bincount(inv, weights=w * ~y); cneg = np.cumsum(neg) - neg
    return float((pos * (cneg + .5 * neg)).sum() / (pos.sum() * neg.sum()))
def wq_bins(q, y, w, nb=10):
    o = np.argsort(q, kind="stable"); cw = np.cumsum(w[o]) / w.sum(); b = np.minimum((cw * nb - 1e-12).astype(int), nb - 1); out = []
    for k in range(nb):
        ix = o[b == k]
        if len(ix) and w[ix].sum() > 0: out.append((float(np.average(q[ix], weights=w[ix])), float(np.average(y[ix], weights=w[ix])), float(w[ix].sum() / w.sum())))
    return out
# static scores for non-fitted policies
STAT = {}
for d in DL:
    S = {"shortest_first_gated": np.where(GATE[d], -U.nw.to_numpy().astype(float), -99.0)}
    for m in PM: S["conf_gated_" + m] = np.where(GATE[d], np.nan_to_num(Q[m][d], nan=0.0), -1.0)
    if PM:
        qm = np.nanmean([Q[m][d] for m in PM], 0); S["conf_gated_mean"] = np.where(GATE[d], qm, -1.0); S["conf_raw_mean"] = qm
        S["entropy_gated_mean"] = np.where(GATE[d], -np.abs(qm - .5), -9.0); Q.setdefault("_mean", {})[d] = qm
    STAT[d] = S

def worker(b):
    mu = MULT[b]; ww = WH * mu[MI]; res = dict(curves={}, h1={}, vcurves={})
    for d in DL:
        ps = prior_scores(d, ww, mu, SEED + 1000 * b + DL.index(d)); S = dict(STAT[d], prior_cv_refit=ps)
        for evn in ("exposure", "model_visible"):
            ev = EV[(d, evn)]; W = ww.sum(); tot = (ww * ev).sum() / W * 1000
            for name, s in S.items(): res["curves"][(d, evn, name)] = curve(s, ww, ev)
            res["curves"][(d, evn, "always_commit")] = np.full(len(GRID), tot); res["curves"][(d, evn, "random_ungated")] = tot * (1 - GRID); res["curves"][(d, evn, "random_gated")] = rand_gated(d, ww, ev)
            if VERB:
                cov = ~np.isnan(VERB[d]); wv = ww * cov
                if wv.sum() > 0:
                    totv = (wv * ev).sum() / wv.sum() * 1000
                    res["vcurves"][(d, evn, "verbal_terra_gated")] = curve(np.where(GATE[d] & cov, np.nan_to_num(VERB[d]), -1.0), wv, ev)
                    res["vcurves"][(d, evn, "prior_cv_refit")] = curve(ps, wv, ev); res["vcurves"][(d, evn, "always_commit")] = np.full(len(GRID), totv)
                    res["vcurves"][(d, evn, "random_gated")] = rand_gated(d, wv, ev)
                    if PM: res["vcurves"][(d, evn, "conf_gated_mean")] = curve(S["conf_gated_mean"], wv, ev)
        # H1 belief scale
        noc = NOC[d] & (ww > 0); y = SRC[d].astype(float); post = np.average(y[noc], weights=ww[noc]); el = GATE[d] & (ww > 0); E = U["E_" + d].to_numpy()
        h = dict(post=post)
        srcs = {m: Q[m][d] for m in PM}
        if VERB: srcs["terra_verbal"] = VERB[d]
        for m, q in srcs.items():
            ok = noc & ~np.isnan(q)
            if ok.sum() < 20: continue
            qq = q[ok]; yy = y[ok]; w_ = ww[ok]; po = np.average(yy, weights=w_); qb = np.average(qq, weights=w_); bins = wq_bins(qq, yy, w_)
            ece = sum(sh * abs(a - c_) for a, c_, sh in bins); br = np.average((qq - yy)**2, weights=w_); br0 = np.average((po - yy)**2, weights=w_)
            oke = el & ~np.isnan(q)
            h[m] = dict(emp=po, qbar=qb, gap=qb - po, ece=ece, bss=1 - br / br0, auroc=wauc(q[oke], E[oke], ww[oke]), n=int(ok.sum()))
            if b == 0: h[m]["bins"] = bins
        for m in MODELS4:   # greedy argmax rate (round-1 quantity, relabelled)
            o = OUTM[d][m]; ok = noc & ~pd.isna(o); h["greedy_" + m] = dict(rate=float(np.average(o[ok].astype(float), weights=ww[ok])), gap=float(np.average(o[ok].astype(float), weights=ww[ok]) - np.average(y[ok], weights=ww[ok])))
        res["h1"][d] = h
    return res

if __name__ == "__main__":
    t0 = time.time(); nb = 3 if A.quick else B
    with Pool(A.procs) as pool: R = pool.map(worker, range(nb + 1), chunksize=1)
    print("bootstrap done", round(time.time() - t0), "s", flush=True)
    def ci(x, lo=2.5, hi=97.5): x = np.asarray(x, float); return float(np.nanpercentile(x, lo)), float(np.nanpercentile(x, hi))
    # ------------------------------------------------ H1 table
    h1 = []; bins = []
    for d in DL:
        keys = set().union(*[set(r["h1"][d]) for r in R]) - {"post"}
        for m in sorted(keys):
            if m.startswith("greedy_"):
                for var in ("rate", "gap"):
                    v = [r["h1"][d][m][var] for r in R if m in r["h1"][d]]
                    h1.append(dict(basis="greedy_argmax_output (NOT calibration)", model=m[7:], dimension=d, metric=var, est=100 * v[0], lo=100 * ci(v[1:])[0], hi=100 * ci(v[1:])[1]))
                continue
            basis = "verbalized_probability" if m == "terra_verbal" else "logprob_forced_choice"
            for var in ("emp", "qbar", "gap", "ece", "bss", "auroc"):
                v = [r["h1"][d][m][var] for r in R if m in r["h1"][d]]; sc_ = 100 if var in ("emp", "qbar", "gap", "ece") else 1
                h1.append(dict(basis=basis, model=m, dimension=d, metric=var, est=sc_ * v[0], lo=sc_ * ci(v[1:])[0], hi=sc_ * ci(v[1:])[1], n=R[0]["h1"][d][m]["n"]))
            bins += [dict(model=m, dimension=d, bin=i, mean_q=a, empirical_rate=c_, weight_share=sh) for i, (a, c_, sh) in enumerate(R[0]["h1"][d][m]["bins"])]
        post = [r["h1"][d]["post"] for r in R]; h1.append(dict(basis="empirical", model="human", dimension=d, metric="rate_cue_given_nocue_keywords", est=100 * post[0], lo=100 * ci(post[1:])[0], hi=100 * ci(post[1:])[1]))
    H1 = pd.DataFrame(h1); H1.to_csv(OUT / "h1_belief_scale.csv", index=False); pd.DataFrame(bins).to_csv(OUT / "h1_reliability_bins.csv", index=False)
    # heterogeneity of gap across probe models
    het = []
    for d in DL:
        g = np.array([[r["h1"][d][m]["gap"] for m in PM] for r in R]) * 100
        if len(PM) > 1: rg = g.max(1) - g.min(1); het.append(dict(dimension=d, models=PM, range_pp=float(rg[0]), lo=ci(rg[1:])[0], hi=ci(rg[1:])[1], same_sign_all_excl0=bool(all((np.percentile(g[1:, j], 2.5) > 0) or (np.percentile(g[1:, j], 97.5) < 0) for j in range(len(PM))) and len({np.sign(g[0, j]) for j in range(len(PM))}) == 1)))
    # ------------------------------------------------ curves
    C = {}
    for r in R:
        for k, v in r["curves"].items(): C.setdefault(k, []).append(v)
    C = {k: np.array(v) for k, v in C.items()}; CV_ = {}
    for r in R:
        for k, v in r["vcurves"].items(): CV_.setdefault(k, []).append(v)
    CV_ = {k: np.array(v) for k, v in CV_.items()}
    crow = []; brow = []
    for (d, evn, name), a in list(C.items()) + [((d, evn, "SUBSET:" + nm), a) for (d, evn, nm), a in CV_.items()]:
        ac = C[(d, evn, "always_commit")] if not name.startswith("SUBSET:") else CV_[(d, evn, name[7:] if name[7:] == "always_commit" else "always_commit")]
        for j, bgt in enumerate(GRID):
            crow.append(dict(dimension=d, event=evn, policy=name, budget=float(bgt), reversals_per_1000=a[0, j], lo=ci(a[1:, j])[0], hi=ci(a[1:, j])[1]))
        for bgt in BUD:
            j = int(round(bgt * 100)); brow.append(dict(dimension=d, event=evn, policy=name, budget=bgt, asks_per_1000=1000 * bgt, reversals_per_1000=a[0, j], lo=ci(a[1:, j])[0], hi=ci(a[1:, j])[1],
                                                         asks_per_reversal_avoided=(1000 * bgt) / max(ac[0, 0] - a[0, j], 1e-9), slp_weighted_reversals=WGT[d] * a[0, j]))
    pd.DataFrame(crow).to_csv(OUT / "policy_curves_r2.csv", index=False); BR = pd.DataFrame(brow); BR.to_csv(OUT / "policy_budgets_r2.csv", index=False)
    # ------------------------------------------------ contrasts (10% primary; 5/20 exploratory)
    def pval(x): x = np.asarray(x); return float((1 + 2 * min((x >= 0).sum(), (x <= 0).sum())) / (len(x) + 1))
    pairs = []
    def contrast(d, evn, a_, b_, bgt, tag):
        j = int(round(bgt * 100)); x = C[(d, evn, a_)][:, j] - C[(d, evn, b_)][:, j]; base = C[(d, evn, b_)][:, j]; rel = (base - C[(d, evn, a_)][:, j]) / np.maximum(base, 1e-9)
        lo90, hi90 = ci(x[1:], 5, 95); lo, hi = ci(x[1:]); m = MARGIN[d]
        pairs.append(dict(dimension=d, event=evn, a=a_, b=b_, budget=bgt, tag=tag, a_rev=C[(d, evn, a_)][0, j], b_rev=C[(d, evn, b_)][0, j], diff=x[0], lo=lo, hi=hi, rel_reduction=rel[0], rel_lo=ci(rel[1:])[0], rel_hi=ci(rel[1:])[1],
                          p_boot=pval(x[1:]), tost_margin=m, ci90_lo=lo90, ci90_hi=hi90, equivalent_tost=bool(lo90 > -m and hi90 < m)))
    PRIM = [("polarity", "prior_cv_refit", "random_gated"), ("polarity", "prior_cv_refit", "conf_gated_mean"), ("politeness", "prior_cv_refit", "random_gated"), ("politeness", "prior_cv_refit", "conf_gated_mean")]
    for d, a_, b_ in PRIM: contrast(d, "model_visible", a_, b_, .10, "primary")
    for d in DL:
        for evn in ("model_visible", "exposure"):
            for bgt in (.05, .10, .20):
                others = ["random_gated", "random_ungated", "shortest_first_gated"] + (["conf_gated_mean", "entropy_gated_mean"] + ["conf_gated_" + m for m in PM] if PM else [])
                for o in others:
                    if (d, evn, "prior_cv_refit", o, bgt) and not (bgt == .10 and evn == "model_visible" and (d, "prior_cv_refit", o) in PRIM): contrast(d, evn, "prior_cv_refit", o, bgt, "exploratory")
                if PM:
                    for a_ in ["conf_gated_mean"] + ["conf_gated_" + m for m in PM]: contrast(d, evn, a_, "random_gated", bgt, "exploratory")
    for d in DL:
        for evn in ("model_visible", "exposure"):
            for bgt in (.05, .10, .20):
                for a_ in ["prior_cv_refit", "random_gated"] + (["conf_gated_mean"] if PM else []): contrast(d, evn, a_, "always_commit", bgt, "descriptive_vs_commit")
    CT = pd.DataFrame(pairs)
    pr = CT.tag.eq("primary"); order = np.argsort(CT.p_boot[pr].to_numpy()); p = CT.p_boot[pr].to_numpy(); holm = np.zeros(len(p)); run = 0
    for rnk, i in enumerate(order): run = max(run, min(1, (len(p) - rnk) * p[i])); holm[i] = run
    CT["p_adj"] = np.nan; CT.loc[pr, "p_adj"] = holm
    ex = CT.tag.eq("exploratory")
    CT.loc[CT.tag.eq('descriptive_vs_commit'), 'p_adj'] = np.nan; pe = CT.p_boot[ex].to_numpy(); o = np.argsort(pe); m_ = len(pe); q = np.zeros(m_); prev = 1.0
    for rnk in range(m_ - 1, -1, -1): i = o[rnk]; prev = min(prev, pe[i] * m_ / (rnk + 1)); q[i] = prev
    CT.loc[ex, "p_adj"] = q; CT["adjust"] = np.where(pr, "Holm(4)", "BH(exploratory)"); CT.to_csv(OUT / "contrasts_r2.csv", index=False)
    # ------------------------------------------------ same-items interventions
    rates = pd.read_csv(ROOT / "analysis/chip_controls/channel_rates.csv"); rates = rates[rates.model.eq("ALL")].set_index("dimension")
    RHO = {("chip", d): (rates.loc[d, "chip1"], rates.loc[d, "chip1_lo"]) for d in DL} | {("word", d): (rates.loc[d, "nlcue"], rates.loc[d, "nlcue_lo"]) for d in DL}
    g1 = json.load(open(OUT / "g1_inertness.json")) if (OUT / "g1_inertness.json").exists() else None
    irow = []
    for d in DL:
        for evn in ("model_visible", "exposure"):
            com = C[(d, evn, "always_commit")]
            def add(strategy, left, taps, extra=None):
                irow.append(dict(dimension=d, event=evn, strategy=strategy, taps_per_1000=taps, reversals_per_1000=left[0], lo=ci(left[1:])[0], hi=ci(left[1:])[1], slp_weighted=WGT[d] * left[0], slp_weighted_lo=WGT[d] * ci(left[1:])[0], slp_weighted_hi=WGT[d] * ci(left[1:])[1], **(extra or {})))
            add("always-commit", com[:, 0], 0)
            if g1:
                add("G1 guard: reversals repaired = 0 (measured)", com[:, 0], 0, dict(note="G1 flags %.1f per 1,000 outputs (HT), all 'politeness:added'; its feedback never names polarity/speech act" % (1000 * g1["flag_rate_HT_weighted"])))
                if d == "politeness": add("G1 guard, WORST CASE (every flagged correct polite output stripped)", com[:, 0] + g1["correct_polite_flagged_HT_per_1000_outputs"], 0, dict(note="upper bound, no regeneration run; +%.1f per 1,000" % g1["correct_polite_flagged_HT_per_1000_outputs"]))
            for pol in ("prior_cv_refit", "random_gated", "conf_gated_mean"):
                if (d, evn, pol) not in C: continue
                for bgt in (.05, .10, .20, 1.0):
                    j = int(round(bgt * 100)); a = C[(d, evn, pol)][:, j]
                    if bgt < 1: add(f"ask(user supplies cue), ranked by {pol}, {int(bgt*100)}%", a, 1000 * bgt)
                    for ch in ("chip", "word"):
                        rho, rho_lo = RHO[(ch, d)]
                        for tag, rr in (("", rho), (" [rho lower CI]", rho_lo)):
                            left = com - rr * (com - C[(d, evn, pol)][:, j:j + 1].reshape(-1, 1)).reshape(-1) if False else com[:, j] - rr * (com[:, j] - a)
                            if bgt == 1.0 and pol != "prior_cv_refit": continue
                            add(f"{ch} shown on {int(bgt*100)}% ranked by {pol}{tag}", left, 1000 * bgt, dict(rho=rr))
    pd.DataFrame(irow).to_csv(OUT / "intervention_same_items.csv", index=False)
    # ------------------------------------------------ SLP acceptability (stored)
    from math import sqrt
    sk = pd.read_csv(ROOT / "expert_package/slp_key.csv"); sr = pd.concat([pd.read_csv(ROOT / f"annotation/returns_slp/slp_rating_SLP{i}.csv") for i in (1, 2)]); sr = sr[sr.task.astype(str).eq("2")].merge(sk, on="item_id")
    ac = []
    for arm, g in sr.groupby("arm"):
        k = int((g.acceptable == "yes").sum()); nn = len(g); z = 1.96; p_ = k / nn; den = 1 + z * z / nn; cen = (p_ + z * z / (2 * nn)) / den; hw = z * sqrt(p_ * (1 - p_) / nn + z * z / (4 * nn * nn)) / den
        ac.append(dict(arm=arm, rater_items=nn, acceptable_yes=k, share=p_, wilson_lo=cen - hw, wilson_hi=cen + hw, edit=int((g.acceptable == "edit").sum()), no=int((g.acceptable == "no").sum())))
    pd.DataFrame(ac).to_csv(OUT / "acceptability_slp.csv", index=False)
    # ------------------------------------------------ unreachable speech act etc
    unre = {}
    for d in DL:
        E = U["E_" + d].to_numpy() > 0; unre[d] = dict(E_units=int(E.sum()), E_unreachable_gated=int((E & ~GATE[d]).sum()), E_reachable=int((E & GATE[d]).sum()), gate_eligible_units=int(GATE[d].sum()), units=n)
    json.dump(dict(probe_models=PM, models4=MODELS4, boot=B, verbal_coverage_units=VCOV, verbal_unique_kw=VNKW, verbal_used=bool(VERB), n_units=n, unreachable=unre, heterogeneity=het, weights=WGT, margins=MARGIN, slp_note="2 raters, descriptive"), open(OUT / "summary_r2.json", "w"), indent=1, default=float)
    print(H1[H1.metric.isin(["gap", "auroc"]) & ~H1.basis.str.startswith("greedy")].round(3).to_string()); print(CT[CT.tag.eq("primary")].round(3).to_string())
