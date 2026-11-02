"""default_profiles round 1: profile gaps (H1), SLP-weighted price (H2), ask-or-assume policy comparison (H4), logprob validity.
    . .venv/bin/activate && python src/frontier_default_profiles_policy.py [--boot 1000] [--no-probe]
Stored outputs + S1 probe files (runs/frontier_default_profiles_probe/*.jsonl). 0 generation. Writes analysis/frontier/default_profiles/.
Decision rules: PLAN.md sections 4 and 8 (written before this ran)."""
import argparse, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import spearmanr
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/default_profiles"
ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=1000); ap.add_argument("--no-probe", action="store_true"); A = ap.parse_args()
SEED = 20261101; B = A.boot
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POL = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)
DIMS = {"polarity": dict(src="neg", nocue="nocue_neg", out="out_neg", lost="lost_neg", lex=NEG), "politeness": dict(src="polite", nocue="nocue_pol", out="out_pol", lost="lost_pol", lex=POL),
        "speech_act": dict(src="nonstmt", nocue="nocue_act", out="out_nonstmt", lost="lost_act", lex=ACT)}
SLP = {"polarity": (5, 5), "speech_act": (4, 4), "politeness": (3, 2)}      # (SLP1, SLP2) severity of NEG, ACT, POL from annotation/returns_slp task 1
WGT = {k: dict(mean=np.mean(v) / 5, slp1=v[0] / 5, slp2=v[1] / 5) for k, v in SLP.items()}

# ------------------------------------------------------------- units
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
msg["neg"] = [key[i]["detector_labels"]["polarity"] == "negated" for i in msg.item_id]
msg["polite"] = [key[i]["detector_labels"]["politeness"] != "none" for i in msg.item_id]
msg["nonstmt"] = [key[i]["detector_labels"]["speech_act"] != "statement" for i in msg.item_id]
msg["w"] = 1 / msg.inclusion_prob; msg["fam"] = "elic-" + msg.source_id; mi = msg.set_index("item_id")
rows = []
for r in rat.itertuples():
    if not isinstance(r.keywords, str) or not r.keywords.strip(): continue
    m = mi.loc[r.item_id]
    rows.append(dict(item_id=r.item_id, fam=m.fam, src_id=m.source_id, channel="human_" + r.annotator, kw=r.keywords, neg=m.neg, polite=m.polite, nonstmt=m.nonstmt,
                     lost_neg=r.polarity_lenient_lost, lost_pol=r.politeness_lenient_lost, lost_act=r.speech_act_lenient_lost, w=m.w, sample=m["sample"]))
for m in msg.itertuples():
    rows.append(dict(item_id=m.item_id, fam=m.fam, src_id=m.source_id, channel="pos_cap4", kw=str(m.pos_cap4), neg=m.neg, polite=m.polite, nonstmt=m.nonstmt,
                     lost_neg=m.polarity_lenient_pos_loss, lost_pol=m.politeness_lenient_pos_loss, lost_act=m.speech_act_lenient_pos_loss, w=m.w, sample=m.sample))
U = pd.DataFrame(rows)
U["kw_neg"] = U.kw.str.contains(NEG); U["kw_pol"] = U.kw.str.contains(POL); U["kw_act"] = U.kw.str.contains(ACT)
U["nocue_neg"] = ~U.kw_neg; U["nocue_pol"] = ~U.kw_pol
U["nocue_act"] = np.where(U.nonstmt, U.lost_act.fillna(1).astype(bool), ~U.kw_act)
U["unit"] = U.item_id + "|" + U.channel
for d, c in DIMS.items(): U["E_" + d] = (U[c["src"]].astype(bool) & U[c["nocue"]].astype(bool)).astype(float)
U["nw"] = U.kw.str.split().str.len()
# stored model outputs (P0, 4 models)
sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0")].rename(columns={"family_id": "fam"})
sc["out_neg"] = sc.polarity.eq("negated"); sc["out_pol"] = sc.politeness.ne("none"); sc["out_nonstmt"] = ~sc.speech_act.eq("statement")
SC = sc[["fam", "channel", "model", "out_neg", "out_pol", "out_nonstmt"]].merge(U[["fam", "channel", "unit"]], on=["fam", "channel"], how="inner")
MODELS4 = sorted(SC.model.unique())
for d, c in DIMS.items():   # per-unit model miss rate: mean over 4 models of 'output lacks cue'
    miss = SC.assign(m=(~SC[c["out"]]).astype(float)).groupby("unit").m.mean(); U["miss_" + d] = U.unit.map(miss).fillna(1.0)
msgidx = {i: j for j, i in enumerate(msg.item_id)}; U["mi"] = U.item_id.map(msgidx)
strata = [np.where(msg["sample"].eq(k))[0] for k in ("random", "enriched")]
rng = np.random.default_rng(SEED)
mults = []
for _ in range(B):
    mu = np.zeros(len(msg))
    for s in strata: np.add.at(mu, rng.choice(s, len(s)), 1)
    mults.append(mu)
mults = np.array(mults)

# ------------------------------------------------------------- H1/H2 profile (human keywords, model = stored 4)
def ht(x, w): return float((x * w).sum() / w.sum()) if w.sum() > 0 else np.nan
def profile(Uh, SCh, d, wv):   # wv: per-message multiplicity
    c = DIMS[d]; u = Uh.assign(ww=Uh.w * wv[Uh.mi.to_numpy()]); u = u[u.ww > 0]; noc = u[c["nocue"]].astype(bool); src = u[c["src"]].astype(bool)
    post = ht((src & noc), u.ww) / ht(noc, u.ww)
    res = dict(posterior=post, rev_exposure=1000 * ht(u["E_" + d], u.ww), n_noc=int(noc.sum()))
    gaps, revs = {}, {}
    for m in MODELS4:
        s = SCh[SCh.model.eq(m)]; s = s.assign(ww=s.w * wv[s.mi.to_numpy()]); s = s[s.ww > 0]; sn = s[c["nocue"]].astype(bool); ss = s[c["src"]].astype(bool); so = s[c["out"]].astype(bool)
        cue_share = ht(so[sn], s.ww[sn]); gaps[m] = post - cue_share                    # + = model more committed to the default than the posterior supports
        revs[m] = 1000 * ht((ss & sn & ~so), s.ww); res["cue_share_" + m] = cue_share
    res["gap_default"] = float(np.mean(list(gaps.values()))); res["rev_models_mean"] = float(np.mean(list(revs.values())))
    for m in MODELS4: res["gap_" + m] = gaps[m]; res["rev_" + m] = revs[m]
    return res
Uh = U[U.channel.str.startswith("human_")].reset_index(drop=True)
SCh = SC.merge(U[["unit", "item_id", "w", "mi", "channel"] + [c["src"] for c in DIMS.values()] + [c["nocue"] for c in DIMS.values()]].drop_duplicates("unit"), on="unit", how="left", suffixes=("", "_u"))
SCh = SCh[SCh.channel.str.startswith("human_")].reset_index(drop=True)
prof = {}
for d in DIMS:
    pt = profile(Uh, SCh, d, np.ones(len(msg))); bs = pd.DataFrame([profile(Uh, SCh, d, mults[b]) for b in range(B)]); prof[d] = (pt, bs)
def ci(x): return [float(v) for v in np.nanquantile(x, [.025, .975])]
prow = []
for d, (pt, bs) in prof.items():
    r = dict(dimension=d, posterior_cue_given_nocue=pt["posterior"], post_ci=ci(bs.posterior), gap_default_pp=100 * pt["gap_default"], gap_ci=[100 * v for v in ci(bs.gap_default)],
             exposure_per_1000=pt["rev_exposure"], exposure_ci=ci(bs.rev_exposure), reversals_models_mean_per_1000=pt["rev_models_mean"], rev_ci=ci(bs.rev_models_mean))
    # DerSimonian-Laird across the 4 models: gap_m, se from bootstrap
    g = np.array([pt["gap_" + m] for m in MODELS4]); se = np.array([bs["gap_" + m].std(ddof=1) for m in MODELS4]); wfix = 1 / se**2
    mu_f = (wfix * g).sum() / wfix.sum(); Q = (wfix * (g - mu_f)**2).sum(); k = len(g); C = wfix.sum() - (wfix**2).sum() / wfix.sum(); tau2 = max(0, (Q - (k - 1)) / C)
    wr = 1 / (se**2 + tau2); mu = (wr * g).sum() / wr.sum(); sem = (1 / wr.sum())**.5
    r |= dict(gap_RE_pp=100 * mu, gap_RE_ci=[100 * (mu - 1.96 * sem), 100 * (mu + 1.96 * sem)], I2=max(0, (Q - (k - 1)) / Q) if Q > 0 else 0.0, **{f"gap_{m}_pp": 100 * pt["gap_" + m] for m in MODELS4})
    prow.append(r)
PR = pd.DataFrame(prow); PR.to_csv(OUT / "profile_gap_h1.csv", index=False)
# H2 weighted ranking
h2 = []
for scheme in ("mean", "slp1", "slp2"):
    tot = sum(WGT[d][scheme] * prof[d][0]["rev_models_mean"] for d in DIMS); tot0 = sum(prof[d][0]["rev_models_mean"] for d in DIMS)
    for d in DIMS: h2.append(dict(scheme=scheme, dimension=d, weight=WGT[d][scheme], reversals_per_1000=prof[d][0]["rev_models_mean"], weighted=WGT[d][scheme] * prof[d][0]["rev_models_mean"],
                                  share_weighted=WGT[d][scheme] * prof[d][0]["rev_models_mean"] / tot, share_unweighted=prof[d][0]["rev_models_mean"] / tot0))
H2 = pd.DataFrame(h2); H2.to_csv(OUT / "slp_weighted_price_h2.csv", index=False)
from scipy.stats import kendalltau
tau = {s: float(kendalltau(H2[(H2.scheme == s)].reversals_per_1000, H2[(H2.scheme == s)].weighted)[0]) for s in ("mean", "slp1", "slp2")}

# ------------------------------------------------------------- policies
BUD = [.02, .05, .10, .20]; GRID = np.linspace(0, 1, 101)
def logit_fit(X, y, w, lam=1.0):
    n, p = X.shape; w = w / w.mean()
    def f(t):
        z = X @ t[:-1] + t[-1]; ll = np.sum(w * (np.logaddexp(0, z) - y * z)); return ll + .5 * lam * np.sum(t[:-1]**2)
    def g(t):
        z = X @ t[:-1] + t[-1]; p_ = 1 / (1 + np.exp(-z)); r = w * (p_ - y); return np.append(X.T @ r + lam * t[:-1], r.sum())
    return minimize(f, np.zeros(p + 1), jac=g, method="L-BFGS-B").x
FUNC = {"pron": re.compile(r"\b(i|me|my|you|your|we|us|he|she|they|them|it)\b", re.I), "modal": re.compile(r"\b(can|could|will|would|should|may|might|must|want|need|like)\b", re.I),
        "wh": re.compile(r"\b(what|where|when|who|why|how|which)\b", re.I)}
def prior_scores(df, d, seed=SEED):
    """5-fold CV grouped by source message; label = source has cue, trained on units whose keywords lack the lexical cue; units with the cue get score 0."""
    c = DIMS[d]; toks = df.kw.str.lower().str.findall(r"[a-z']+"); from collections import Counter
    cnt = Counter(t for ts in toks for t in set(ts)); vocab = {t: i for i, t in enumerate(t for t, n in sorted(cnt.items()) if n >= 5)}
    X = np.zeros((len(df), len(vocab) + 5))
    for i, ts in enumerate(toks):
        for t in set(ts):
            if t in vocab: X[i, vocab[t]] = 1
        X[i, -5] = np.log1p(len(ts)); X[i, -4] = bool(FUNC["pron"].search(df.kw.iloc[i])); X[i, -3] = bool(FUNC["modal"].search(df.kw.iloc[i])); X[i, -2] = bool(FUNC["wh"].search(df.kw.iloc[i])); X[i, -1] = len(ts) <= 2
    y = df[c["src"]].astype(float).to_numpy(); eligible = lexgate(df, d)
    r = np.random.default_rng(seed); gids = df.src_id.unique(); fold = dict(zip(gids, r.permutation(len(gids)) % 5)); f = df.src_id.map(fold).to_numpy(); sc_ = np.zeros(len(df))
    for k in range(5):
        tr = (f != k) & eligible; te = (f == k)
        t = logit_fit(X[tr], y[tr], df.w.to_numpy()[tr]); z = X[te] @ t[:-1] + t[-1]; sc_[te] = 1 / (1 + np.exp(-z))
    return np.where(eligible, sc_, 0.0)
def lexgate(df, d): return (~df[{"polarity": "kw_neg", "politeness": "kw_pol", "speech_act": "kw_act"}[d]]).to_numpy()

def load_probe():
    P = {}
    for m in ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "qwen2.5-14b", "mistral-nemo-12b"]:
        fn = ROOT / f"runs/frontier_default_profiles_probe/{m}.jsonl"
        if not fn.exists(): continue
        rr = pd.DataFrame([json.loads(l) for l in open(fn)]); rr["q"] = rr[["q0", "q1"]].mean(axis=1); P[m] = rr.pivot(index="unit", columns="dim", values="q")
    return P
PROBE = {} if A.no_probe else load_probe()
pol_rows, curve_rows, summ = [], [], {"probe_models": sorted(PROBE), "models4": MODELS4, "weights": WGT, "kendall_tau_weighted_vs_unweighted": tau}
def curves(Uc, scores, d, ev):
    """returns reversals per 1000 on grid for each policy under bootstrap; scores: dict name -> array (higher = ask first)."""
    wv = mults[:, Uc.mi.to_numpy()] * Uc.w.to_numpy()[None, :]            # B x n  (HT weight x multiplicity)
    W = wv.sum(1); out = {}
    allw = np.vstack([Uc.w.to_numpy()[None, :], wv]); W0 = allw.sum(1)
    e = ev
    for name, s in scores.items():
        rr = np.random.default_rng(SEED + 7).random(len(s)) * 1e-9; order = np.argsort(-(s + rr), kind="stable")
        cw = np.cumsum(allw[:, order], 1) / W0[:, None]; ce = np.cumsum((allw * e[None, :])[:, order], 1) / W0[:, None]
        cw = np.hstack([np.zeros((len(W0), 1)), cw]); ce = np.hstack([np.zeros((len(W0), 1)), ce]); tot = (allw * e[None, :]).sum(1) / W0
        res = np.array([tot[i] - np.interp(GRID, cw[i], ce[i]) for i in range(len(W0))]) * 1000       # reversals left per 1000 messages at each ask budget
        out[name] = res
    base = (allw * e[None, :]).sum(1) / W0 * 1000
    out["random"] = np.array([base[i] * (1 - GRID) for i in range(len(W0))])
    out["always_commit"] = np.tile(base[:, None], (1, len(GRID)))
    return out
def summarize(res, d, scope, evname):
    ac = res["always_commit"]
    for name, arr in res.items():
        for b in BUD:
            j = int(round(b * 100)); v = arr[:, j]; lo, hi = ci(v[1:]); rows = dict(scope=scope, dimension=d, event=evname, policy=name, budget=b, reversals_per_1000=v[0], lo=lo, hi=hi,
                                   asks_per_1000=1000 * b, caught_per_100_asks=100 * (ac[0, j] - v[0]) / (b * 1000) * 1  )
            pol_rows.append(rows)
        auc = np.trapezoid(arr, GRID, axis=1) / np.maximum(ac[:, 0], 1e-12)
        curve_rows.append(dict(scope=scope, dimension=d, event=evname, policy=name, auc_rel_to_commit=auc[0], lo=ci(auc[1:])[0], hi=ci(auc[1:])[1]))
pairs = []
for scope, Uc in (("human", Uh), ("pos_cap4", U[U.channel.eq("pos_cap4")].reset_index(drop=True))):
    for d in DIMS:
        sc_ = {"shortest_first_gated": np.where(lexgate(Uc, d), -Uc.nw.to_numpy().astype(float), -99.0), "prior_logistic_cv": prior_scores(Uc, d)}
        for m, P in PROBE.items():
            q = Uc.unit.map(P[d]).to_numpy() if d in P else None
            if q is None or np.isnan(q).all(): continue
            q = np.nan_to_num(q, nan=0.0); sc_["conf_raw_" + m] = q; sc_["conf_gated_" + m] = np.where(lexgate(Uc, d), q, -1.0)
        if PROBE:
            ms = [Uc.unit.map(P[d]).to_numpy() for P in PROBE.values() if d in P]
            if ms: sc_["conf_gated_mean_models"] = np.where(lexgate(Uc, d), np.nanmean(ms, 0), -1.0)
        for evname, ev in (("exposure", Uc["E_" + d].to_numpy()), ("model_output_miss", Uc["E_" + d].to_numpy() * Uc["miss_" + d].to_numpy())):
            res = curves(Uc, sc_, d, ev); summarize(res, d, scope, evname)
            # paired contrasts at 10% budget: prior vs random, prior vs best-confidence variants, conf vs random
            j = 10
            def pc(a, b_, lab):
                x, y = res[a][:, j], res[b_][:, j]; dlt = x - y; rel = (y - x) / np.maximum(y, 1e-12)
                pairs.append(dict(scope=scope, dimension=d, event=evname, a=a, b=b_, label=lab, a_rev=x[0], b_rev=y[0], diff=dlt[0], diff_lo=ci(dlt[1:])[0], diff_hi=ci(dlt[1:])[1],
                                  rel_reduction_vs_b=rel[0], rel_lo=ci(rel[1:])[0], rel_hi=ci(rel[1:])[1]))
            pc("prior_logistic_cv", "random", "prior vs random"); pc("prior_logistic_cv", "shortest_first_gated", "prior vs shortest-first")
            for k in sc_:
                if k.startswith("conf_gated"): pc("prior_logistic_cv", k, "prior vs " + k); pc(k, "random", k + " vs random")
                if k.startswith("conf_raw"): pc(k, "random", k + " vs random")
POL = pd.DataFrame(pol_rows); POL.to_csv(OUT / "policy_budgets.csv", index=False); pd.DataFrame(curve_rows).to_csv(OUT / "policy_auc.csv", index=False)
PC = pd.DataFrame(pairs); PC.to_csv(OUT / "policy_paired_contrasts.csv", index=False)
# ------------------------------------------------------------- logprob validity
val = []
for m, P in PROBE.items():
    if m not in MODELS4: continue
    for d in DIMS:
        c = DIMS[d]; s = SC[SC.model.eq(m)].merge(U[["unit", c["nocue"]]].rename(columns={c["nocue"]: "noc"}), on="unit", how="left", suffixes=("", "_x"))
        s = s[s.channel.str.startswith("human_") & s.noc.fillna(False).astype(bool)]; q = s.unit.map(P[d]); ok = q.notna()
        y = s[c["out"]].astype(float)[ok]
        rho = spearmanr(q[ok], y)[0] if y.nunique() > 1 else np.nan
        val.append(dict(model=m, dimension=d, n=int(ok.sum()), cue_asserting_output_rate=float(y.mean()), spearman_q_vs_output_asserts_cue=rho, mean_q=float(q[ok].mean())))
VAL = pd.DataFrame(val); VAL.to_csv(OUT / "logprob_validity.csv", index=False)
# calibration of q vs source posterior (is the model's forced-choice probability close to the human base rate?)
cal = []
for m, P in PROBE.items():
    for d in DIMS:
        c = DIMS[d]; u = Uh[Uh[c["nocue"]].astype(bool)]; q = u.unit.map(P[d]) if d in P else pd.Series(dtype=float)
        if len(q) and q.notna().any(): cal.append(dict(model=m, dimension=d, mean_q_nondefault_given_nocue=float(np.nansum(q * u.w) / u.w[q.notna()].sum()), human_posterior=prof[d][0]["posterior"]))
pd.DataFrame(cal).to_csv(OUT / "logprob_calibration.csv", index=False)
summ |= dict(profile=PR.to_dict("records"), kendall=tau, validity=VAL.to_dict("records"), n_units_human=len(Uh), n_boot=B)
json.dump(summ, open(OUT / "summary.json", "w"), indent=1, default=float)
print(PR.round(3).to_string()); print(H2.round(3).to_string()); print(tau); print(VAL.round(3).to_string())
print(POL[(POL.scope == "human") & (POL.event == "exposure") & POL.budget.eq(.10)].round(2).to_string())
