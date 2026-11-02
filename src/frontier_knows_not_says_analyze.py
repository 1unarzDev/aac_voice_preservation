"""Stage 1 analysis for knows_not_says (PLAN.md A12-A17). Offline; reads runs/frontier_knows_not_says_stage1/<model>/gens.jsonl (+ pairs_raw.json).
usage: python src/frontier_knows_not_says_analyze.py qwen:qwen2.5-7b llama:llama3.1-8b [--boot 10000]
Writes analysis/frontier/knows_not_says/stage1/ (CSVs, summary.json, figures)."""
from __future__ import annotations
import json, sys, math, argparse, collections
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import frontier_knows_not_says_lib as L
ap = argparse.ArgumentParser(); ap.add_argument("models", nargs="+"); ap.add_argument("--boot", type=int, default=10000)
ap.add_argument("--out", default="stage1"); ap.add_argument("--fixture", default=None, help="synthetic fixture dir (units.csv, runs/<key>/gens.jsonl); output to <dir>/out")
A = ap.parse_args()
if A.fixture:
    FIX = Path(A.fixture); OUT = FIX / "out"; RUNS = FIX / "runs"
else:
    OUT = ROOT / "analysis/frontier/knows_not_says" / A.out; RUNS = ROOT / "runs/frontier_knows_not_says_stage1"
OUT.mkdir(parents=True, exist_ok=True); B = A.boot; K = 16
TARGET_T2 = {("polarity", "human"): 0.027, ("polarity", "cap4"): 0.114, ("politeness", "human"): 0.065, ("politeness", "cap4"): 0.039,
             ("speech_act", "human"): 0.479, ("speech_act", "cap4"): 0.533}
DIMS = {"polarity": dict(src="neg", nocue="nocue_neg", lab="polarity", pos=lambda v: v == "negated"),
        "politeness": dict(src="polite", nocue="nocue_pol", lab="politeness", pos=lambda v: v != "none"),
        "speech_act": dict(src="nonstmt", nocue="nocue_act", lab="speech_act", pos=lambda v: v != "statement")}
W_REV = 1.0   # SLP Task 1: NEG mean severity 5.0/5 -> weight 1.0 (reversal and spurious negation are both the NEG type)
CHIP = collections.defaultdict(lambda: (0.99, 0.99), {"qwen2.5-7b": (0.9952, 0.9856), "llama3.1-8b": (0.9904, 0.9952)})   # (chip1, nlcue) polarity honour rates, analysis/chip_controls/channel_rates.csv

# ------------------------------------------------------------------ labels (cached; layer0 detector, as T2)
import layer0
LAB_CACHE = RUNS / "labels_cache.json"
cache = json.load(open(LAB_CACHE)) if LAB_CACHE.exists() else {}
def labels_for(texts):
    need = sorted({t for t in texts if t not in cache})
    if need:
        for t, l in zip(need, layer0.label_many(need)): cache[t] = [l["polarity"], l["politeness"], l["speech_act"]]
        json.dump(cache, open(LAB_CACHE, "w"))
    return [cache[t] for t in texts]

if A.fixture:
    U0 = pd.read_csv(FIX / "units.csv"); U0["kw"] = U0.kw.fillna("").astype(str); U0["input"] = U0.input.astype(str)
else:
    pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json"))
    U0 = L.build_units({e["elic_item_id"] for e in pilot["e_human"]})
HOLM_FAMILY: list = []   # (model, test, p) collected for the declared E-cap4 confirmatory family (A22)
BOOTV: dict = {}   # (alias, ds, name) -> bootstrap vector (for pooled-over-models rows)
SUMM: dict = {"seed": L.SEED, "boot": B, "models": {}, "weights": {"w_reversal": W_REV}, "status": "PROVISIONAL (detector labels; Part 21 not in)"}


def entropy_top(top):  # truncated (top-20) entropy in nats of one position
    p = np.exp(np.array([t[1] for t in top])); return float(-(p * np.log(np.clip(p, 1e-12, 1))).sum())


def load_model(key):
    G = collections.defaultdict(lambda: {"g": None, "s": []})
    for l in open(RUNS / key / "gens.jsonl"):
        r = json.loads(l)
        if r["k"] < 0: G[r["input"]]["g"] = r
        else: G[r["input"]]["s"].append(r)
    return G


def unit_frame(G, alias):
    ins = sorted(G); texts = []
    for i in ins: texts += [G[i]["g"]["text"]] + [x["text"] for x in G[i]["s"]]
    labs = dict(zip(range(len(texts)), labels_for(texts))); p = 0; rec = {}
    for i in ins:
        g = G[i]["g"]; ss = G[i]["s"]; n = 1 + len(ss); ls = [labs[p + j] for j in range(n)]; p += n
        gl, sl = ls[0], ls[1:]
        r = dict(g_neg=gl[0] == "negated", g_pol=gl[1] != "none", g_act=gl[2] != "statement",
                 s_neg=np.mean([x[0] == "negated" for x in sl]), s_pol=np.mean([x[1] != "none" for x in sl]),
                 s_act=np.mean([x[2] != "statement" for x in sl]), n_samp=len(ss),
                 g_neg_logp=g["lp"][0], H1=entropy_top(g["top"][0]), Hm=float(np.mean([entropy_top(t) for t in g["top"]])),
                 n_unique=len({x["text"] for x in ss}), len_g=len(g["toks"]), finish_len=sum(x["finish"] == "length" for x in ss) + (g["finish"] == "length"))
        rec[i] = r
    R = pd.DataFrame.from_dict(rec, orient="index"); R.index.name = "input"; return R


def mult_for(U):
    return L.boot_multiplicity(U.item_id.to_numpy(), U["sample"].to_numpy(), B)


def chunks(M, size=1000):
    for i in range(0, M.shape[0], size): yield M[i:i + size].astype(np.float64)


# ------------------------------------------------------------------ detector validity (A19/A19b): predictive-value correction
DETV = json.load(open(OUT / "detector_validity.json")) if (OUT / "detector_validity.json").exists() else None


def corrected_r1(shb, pob, alias):
    """Predictive-value correction of the bootstrap share vectors (polarity only). None when the validity check is absent."""
    if DETV is None or f"model:{alias}" not in DETV["sets"] or "source" not in DETV["sets"]: return None
    rng = np.random.default_rng(L.SEED + 7); n = len(shb); so, ss = DETV["sets"][f"model:{alias}"], DETV["sets"]["source"]
    def bt(d, k): return rng.beta(d[k]["k"] + 1, d[k]["n"] - d[k]["k"] + 1, n)
    ppv_o, npv_o, ppv_s, npv_s = bt(so, "ppv"), bt(so, "npv"), bt(ss, "ppv"), bt(ss, "npv")
    shc = shb * ppv_o + (1 - shb) * (1 - npv_o); poc = pob * ppv_s + (1 - pob) * (1 - npv_s)
    ratio = shc / np.where(poc > 0, poc, np.nan); cls, lo90, hi90 = L.r1_class(ratio)
    return dict(corr_sampled_share=float(np.mean(shc)), corr_sampled_lo=L.pct_ci(shc)[0], corr_sampled_hi=L.pct_ci(shc)[1],
                corr_posterior=float(np.mean(poc)), corr_posterior_lo=L.pct_ci(poc)[0], corr_posterior_hi=L.pct_ci(poc)[1],
                corr_ratio=float(np.nanmedian(ratio)), corr_ratio_lo90=lo90, corr_ratio_hi90=hi90, corr_r1_class=cls,
                corr_ratio_lo95=L.pct_ci(ratio)[0], corr_ratio_hi95=L.pct_ci(ratio)[1])


# ------------------------------------------------------------------ R1: calibration of the sampled distribution
def r1_table(U, M, alias, ds):
    rows = []
    for d, c in DIMS.items():
        src, noc = U[c["src"]].to_numpy(bool), U[c["nocue"]].to_numpy(bool)
        s = U["s_" + {"polarity": "neg", "politeness": "pol", "speech_act": "act"}[d]].to_numpy(float)
        g = U["g_" + {"polarity": "neg", "politeness": "pol", "speech_act": "act"}[d]].to_numpy(float)
        w = U.w.to_numpy(float); wn = w * noc
        def point(wv): return (wv * s * noc).sum() / (wv * noc).sum(), (wv * g * noc).sum() / (wv * noc).sum(), (wv * src * noc).sum() / (wv * noc).sum()
        sh, gr, po = point(w); shb, grb, pob = [], [], []
        for Mc in chunks(M):
            Wb = w[None, :] * Mc; den = (Wb * noc).sum(1)
            shb.append((Wb * s * noc).sum(1) / den); grb.append((Wb * g * noc).sum(1) / den); pob.append((Wb * src * noc).sum(1) / den)
        shb, grb, pob = map(np.concatenate, (shb, grb, pob)); ratio = shb / np.where(pob > 0, pob, np.nan)
        cls, lo90, hi90 = L.r1_class(ratio)
        tgt = TARGET_T2[(d, ds)]; corr = corrected_r1(shb, pob, alias) if d == "polarity" else None
        rows.append(dict(model=alias, dataset=ds, dimension=d, n_units=len(U), n_msgs=U.item_id.nunique(), n_nocue_units=int(noc.sum()),
                         n_pos_nocue_raw=int((src & noc).sum()), power=L.power_label((src & noc).sum()),
                         posterior=po, posterior_lo=L.pct_ci(pob)[0], posterior_hi=L.pct_ci(pob)[1],
                         sampled_share=sh, sampled_lo=L.pct_ci(shb)[0], sampled_hi=L.pct_ci(shb)[1],
                         greedy_share=gr, greedy_lo=L.pct_ci(grb)[0], greedy_hi=L.pct_ci(grb)[1],
                         ratio=sh / po if po > 0 else float("nan"), ratio_lo90=lo90, ratio_hi90=hi90, ratio_lo95=L.pct_ci(ratio)[0], ratio_hi95=L.pct_ci(ratio)[1],
                         r1_class=cls, t2_target_fixed=tgt, ratio_to_fixed_target=sh / tgt, detector_status=("validated-corrected" if corr else "detector-relative, unvalidated"), **(corr or {})))
    return rows


# ------------------------------------------------------------------ reliability (ECE / Brier / bins)
def reliability(U, M, alias, ds):
    noc = U.nocue_neg.to_numpy(bool); u = U[noc]; m = M[:, noc]
    p = u.s_neg.to_numpy(float); y = u.neg.to_numpy(float); w = u.w.to_numpy(float)
    ece = L.w_ece(p, y, w); br = L.w_brier(p, y, w); base = L.w_brier(np.full(len(y), L.wmean(y, w)), y, w)
    eb = L.boot_stat(lambda wb, pp, yy: L.w_ece(pp, yy, wb), m, w, p, y)
    bb = L.boot_stat(lambda wb, pp, yy: L.w_brier(pp, yy, wb), m, w, p, y)
    bins = []
    b = np.clip(np.digitize(p, L.ECE_EDGES[1:-1], right=True), 0, len(L.ECE_EDGES) - 2)
    for k in range(len(L.ECE_EDGES) - 1):
        mk = b == k
        if mk.any(): bins.append(dict(model=alias, dataset=ds, bin=k, n=int(mk.sum()), w=float(w[mk].sum() / w.sum()), mean_p=L.wmean(p[mk], w[mk]), obs_rate=L.wmean(y[mk], w[mk])))
    return dict(model=alias, dataset=ds, ece=ece, ece_lo=L.pct_ci(eb)[0], ece_hi=L.pct_ci(eb)[1], brier=br, brier_lo=L.pct_ci(bb)[0], brier_hi=L.pct_ci(bb)[1],
                brier_const_base_rate=base), bins


# ------------------------------------------------------------------ R2: per-input knowledge
def lex_features(U):
    kws = U.kw.str.lower().str.findall(r"[a-z']+"); df = collections.Counter(w for ws in kws for w in set(ws))
    vocab = sorted(w for w, n in df.items() if n >= 5); ix = {w: j for j, w in enumerate(vocab)}
    X = np.zeros((len(U), 2 + len(vocab)))
    for r, ws in enumerate(kws):
        X[r, 0] = len(ws); X[r, 1] = len(U.kw.iloc[r]) / 10
        for w in ws:
            if w in ix: X[r, 2 + ix[w]] = 1
    return X


def r2_table(U, M, alias, ds):
    noc = U.nocue_neg.to_numpy(bool); u = U[noc].reset_index(drop=True); m = M[:, noc]
    y = u.neg.to_numpy(bool); w = u.w.to_numpy(float); X = lex_features(u)
    lex = L.cv_logreg_oof(X, y.astype(float), w, u.item_id.to_numpy(), n_folds=5, l2=1.0)
    scores = {"sampled_share(K=16)": u.s_neg.to_numpy(float), "greedy_first_token_entropy": u.H1.to_numpy(float), "greedy_mean_token_entropy": u.Hm.to_numpy(float),
              "lexical_cv_logistic": lex, "greedy_output_negated": u.g_neg.to_numpy(float)}
    pt = {k: L.w_auroc(v, y, w) for k, v in scores.items()}
    nb = B; boots = {}
    for k, v in scores.items(): boots[k] = np.array([L.w_auroc(v, y, w * m[b]) for b in range(nb)])
    sh = scores["sampled_share(K=16)"]; tied0 = dict(tied0_all=float((sh == 0).mean()), tied0_pos=float((sh[y] == 0).mean()) if y.any() else float("nan"), tied0_neg=float((sh[~y] == 0).mean()))
    for k in scores: BOOTV[(alias, ds, "auroc:" + k)] = boots[k]
    p_gt = lambda x, null=0.0: float((1 + (np.asarray(x) <= null).sum()) / (len(x) + 1))
    rows = []
    for k in scores:
        lo, hi = L.pct_ci(boots[k]); row = dict(model=alias, dataset=ds, score=k, auroc=pt[k], lo=lo, hi=hi, n_nocue_units=int(noc.sum()), n_pos_raw=int(y.sum()),
                                                n_msgs_pos=int(u[y].item_id.nunique()), power=L.power_label(y.sum()), status=("confirmatory family" if ds == "cap4" else "EXPLORATORY (human subset)"),
                                                **(tied0 if k == "sampled_share(K=16)" else {}))
        if k == "sampled_share(K=16)": row["p_auroc_gt_0.5"] = p_gt(boots[k], 0.5)
        for ref in ("lexical_cv_logistic", "greedy_first_token_entropy", "greedy_mean_token_entropy"):
            if k == "sampled_share(K=16)":
                dd = boots[k] - boots[ref]; a_, b_ = L.pct_ci(dd); row[f"diff_vs_{ref}"] = pt[k] - pt[ref]; row[f"diff_vs_{ref}_lo"] = a_; row[f"diff_vs_{ref}_hi"] = b_
                row[f"p_diff_vs_{ref}_gt0"] = p_gt(dd); BOOTV[(alias, ds, "diff:" + ref)] = dd
        rows.append(row)
    if ds == "cap4":
        HOLM_FAMILY.append((alias, "R2-a sampled-share AUROC > 0.5", p_gt(boots["sampled_share(K=16)"], 0.5)))
        HOLM_FAMILY.append((alias, "R2-b sampled-share AUROC > lexical (paired)", p_gt(boots["sampled_share(K=16)"] - boots["lexical_cv_logistic"])))
    return rows, scores, u


# ------------------------------------------------------------------ R3: policies
W_SPUR_GRID = (1.0, 1 / 8, 1 / 36)   # w_spurious as a fraction of w_reversal (A15/A21)


def policies(U, M, alias, ds, scores_u, u, cf_share, g1):
    """All arms on the same units. Returns rows (+ pareto curve rows, sensitivity rows)."""
    w = U.w.to_numpy(float); src = U.neg.to_numpy(float); noc = U.nocue_neg.to_numpy(float); gout = U.g_neg.to_numpy(float)
    sout_commit = (U.s_neg.to_numpy(float) >= 0.5).astype(float)
    msg = U.item_id.to_numpy(); strata = U["sample"].to_numpy(); n = len(U)
    idx_noc = np.flatnonzero(noc.astype(bool)); full = {}
    for k, v in scores_u.items():
        arr = np.zeros(n); arr[idx_noc] = v; full[k] = arr
    Wb = w[None, :] * M.astype(np.float64); Wsum = Wb.sum(1)           # all B resamples (A22)
    revc = Wb @ (src * noc * (1 - gout)) / Wsum * 1000; spurc = Wb @ ((1 - src) * gout) / Wsum * 1000   # always-commit (greedy)
    nocb = Wb @ noc / Wsum * 1000
    VEC = {}
    def evaluate(a, out, name, kind, extra=None, w_spur=1.0, c_tap=0.0, resid=None):
        rev, spur, taps = L.policy_outcomes(a, src, noc, out, w)
        revb = Wb @ ((1 - a) * src * noc * (1 - out)) / Wsum * 1000; spurb = Wb @ ((1 - a) * (1 - src) * out) / Wsum * 1000; tapb = Wb @ a / Wsum * 1000
        if resid is not None:   # user-supplied cue honoured with prob h: residual reversals = commit-level reversals x (1-h) (A21)
            revb = revc * resid; rev = L.policy_outcomes(np.zeros(n), src, noc, gout, w)[0] * resid
        caught_pol = revc - revb; rand_caught = np.minimum(1.0, tapb / nocb) * revc
        costb = W_REV * revb + w_spur * spurb + c_tap * tapb; costc = W_REV * revc + w_spur * spurc
        d_cost = costb - costc; dpr = {c: W_REV * revb + w_spur * spurb + c * W_REV * tapb - costc for c in (0.01, 0.03, 0.1)}; d_vs_rand = caught_pol - rand_caught; rec = caught_pol / np.where(revc > 0, revc, np.nan)
        VEC[name] = (dpr[0.03], d_vs_rand)
        r = dict(model=alias, dataset=ds, policy=name, kind=kind, w_spur=w_spur, c_tap=c_tap, reversals_per_1000=rev, rev_lo=L.pct_ci(revb)[0], rev_hi=L.pct_ci(revb)[1],
                 spurious_per_1000=spur, spur_lo=L.pct_ci(spurb)[0], spur_hi=L.pct_ci(spurb)[1], taps_per_1000=taps, taps_lo=L.pct_ci(tapb)[0], taps_hi=L.pct_ci(tapb)[1],
                 weighted_cost_per_1000=W_REV * rev + w_spur * spur, d_cost_vs_commit=float(np.mean(d_cost)), d_cost_lo=L.pct_ci(d_cost)[0], d_cost_hi=L.pct_ci(d_cost)[1],
                 **{f"d_cost_priced_c{c}": float(np.mean(v)) for c, v in dpr.items()},
                 **{f"d_cost_priced_c{c}_{t}": L.pct_ci(v)[i] for c, v in dpr.items() for i, t in enumerate(("lo", "hi"))},
                 caught_vs_commit=float(np.mean(caught_pol)), caught_lo=L.pct_ci(caught_pol)[0], caught_hi=L.pct_ci(caught_pol)[1], caught_random_same_taps=float(np.mean(rand_caught)),
                 caught_minus_random=float(np.mean(d_vs_rand)), cmr_lo=L.pct_ci(d_vs_rand)[0], cmr_hi=L.pct_ci(d_vs_rand)[1],
                 queries_per_catch=float(np.mean(tapb) / np.mean(caught_pol)) if np.mean(caught_pol) > 0 and np.mean(tapb) > 0 else float("nan"),
                 recall_of_reversals=float(np.nanmean(rec)), recall_lo=L.pct_ci(rec)[0], recall_hi=L.pct_ci(rec)[1], d_spur_vs_commit=float(np.mean(spurb - spurc)),
                 recovers_R3=bool(L.pct_ci(dpr[0.03])[1] < 0 and L.pct_ci(d_vs_rand)[0] > 1e-9) if kind not in ("baseline", "oracle") else None)
        if extra: r.update(extra)
        return r
    rows = []; pareto = []; zeros = np.zeros(n)
    rows.append(evaluate(zeros, gout, "always-commit (greedy)", "baseline"))
    rows.append(evaluate(np.ones(n) * noc, gout, "always-ask (every no-cue unit)", "baseline"))
    rows.append(evaluate(zeros, sout_commit, "sampled-commit (majority of 16)", "decoder"))
    # random-ask at the matched ask rate of the headline policy is analytic (caught_random_same_taps); explicit random-ask rows at fixed rates:
    for rate in (5, 10, 25):
        a = noc * (rate / 100) / np.maximum((w * noc).sum() / w.sum(), 1e-12)   # share of ALL units asked = rate/100, spread uniformly over no-cue units
        rows.append(evaluate(np.clip(a, 0, 1), gout, f"random-ask @ {rate}/100 (expectation)", "baseline", dict(budget_per_100=rate)))
    for t in (1, 2, 4, 8):
        a = ((full["sampled_share(K=16)"] >= t / K) & noc.astype(bool)).astype(float)
        rows.append(evaluate(a, gout, f"disagreement-ask (share>={t}/16)", "ask-threshold"))
    names = {"sampled_share(K=16)": "sampled share (semantic-entropy analogue)", "greedy_first_token_entropy": "greedy first-token entropy",
             "greedy_mean_token_entropy": "greedy mean token entropy", "lexical_cv_logistic": "lexical logistic (cross-fitted)"}
    for k, label in names.items():
        for bud in (5, 10, 25):
            a = L.crossfit_budget(full[k], w, msg, strata, bud / 100, repeats=20, domain=noc.astype(bool))
            rows.append(evaluate(a, gout, f"{label} @ {bud}/100", "ask-budget", dict(budget_per_100=bud, score=k)))
        for bud in range(0, 101, 2):
            a = L.crossfit_budget(full[k], w, msg, strata, bud / 100, repeats=6, domain=noc.astype(bool))
            rev, spur, taps = L.policy_outcomes(a, src, noc, gout, w)
            pareto.append(dict(model=alias, dataset=ds, score=k, budget_per_100=bud, reversals_per_1000=rev, spurious_per_1000=spur, taps_per_1000=taps))
    rows.append(evaluate(src * noc, gout, "oracle-ask (upper bound)", "oracle"))
    # user-supplied cue (oracle-triggered user), honour residual applied to every derived quantity (A21)
    chip, word = CHIP[alias]
    for nm, h in (("cue chip (ORACLE-triggered user x measured honour rate; upper bound)", chip), ("plain word (ORACLE-triggered user x measured honour rate; upper bound)", word)):
        r = evaluate(src * noc, gout, nm, "user-supplied-cue-oracle", dict(honour_rate=h), resid=1 - h)
        r["note"] = "taps = positives per 1000; residual reversals = commit-level reversals x (1-h); best case, no triggering error"
        rows.append(r)
    # G1: not applicable (monitor enforces supplied cues only)
    rows.append(dict(model=alias, dataset=ds, policy="guard G1 (NOT APPLICABLE to bare keywords)", kind="not-applicable", note=f"no cue supplied on these inputs, monitor has nothing to enforce; empirical flag check on {g1['n_units']} greedy outputs: {g1['flag_counts']} (neither a win nor a loss)"))
    # contextual calibration (Zhao 2021) + Platt cost-optimal ask, REFIT per w_spur (A21), cross-fitted
    s_full = full["sampled_share(K=16)"]; clip = lambda x: np.clip(x, 1 / (2 * K), 1 - 1 / (2 * K)); lg = lambda x: np.log(x / (1 - x))
    rng = np.random.default_rng(L.SEED); msgs, first = np.unique(msg, return_index=True); ms = strata[first]
    for variant in ("platt", "cbu"):
        for w_spur in W_SPUR_GRID:
            for c_tap in (0.01, 0.03, 0.1):
                acc = np.zeros(n); cnt = np.zeros(n)
                for rep in range(20):
                    half = np.zeros(len(msgs), bool)
                    for st in np.unique(ms):
                        ii = np.flatnonzero(ms == st); rng.shuffle(ii); half[ii[: len(ii) // 2]] = True
                    hm = dict(zip(msgs, half)); uh = np.array([hm[m] for m in msg])
                    for tr_is in (True, False):
                        tr = (uh == tr_is) & noc.astype(bool); te = (uh != tr_is)
                        if variant == "platt":
                            beta = L.fit_logreg(lg(clip(s_full[tr]))[:, None], src[tr], w[tr], l2=0.1); P = L.predict_logreg(beta, lg(clip(s_full[te]))[:, None])
                        else:
                            pi_tr = (w[tr] * src[tr]).sum() / w[tr].sum(); cf = float(clip(np.array([cf_share]))[0])
                            odds = np.exp(lg(clip(s_full[te]))) * (pi_tr / (1 - pi_tr)) / (cf / (1 - cf)); P = odds / (1 + odds)
                        benefit = P * (1 - gout[te]) * W_REV + (1 - P) * gout[te] * w_spur
                        acc[te] += ((benefit > c_tap) & noc[te].astype(bool)); cnt[te] += 1
                a = acc / np.maximum(cnt, 1)
                nm = ("Platt-calibrated cost-optimal ask" if variant == "platt" else "contextual-calibration (Zhao 2021) cost-optimal ask") + f" c={c_tap} w_spur=1/{round(1 / w_spur)}"
                rows.append(evaluate(a, gout, nm, "calibrated-ask", dict(variant=variant), w_spur=w_spur, c_tap=c_tap))
    # recompute-only weight sensitivity for the fixed arms (the refit arms above carry their own w_spur)
    sens = []
    for r in rows:
        if r.get("kind") in ("baseline", "decoder") or (r.get("policy", "").startswith("sampled share") and "@ 10/100" in r.get("policy", "")):
            for ratio in (1, 8, 36):
                sens.append(dict(model=alias, dataset=ds, policy=r["policy"], rev_to_spur_weight_ratio=ratio, weighted_cost_per_1000=W_REV * r["reversals_per_1000"] + (1 / ratio) * r["spurious_per_1000"]))
    hp = "sampled share (semantic-entropy analogue) @ 10/100"
    for k_, (dc, cm) in VEC.items():
        BOOTV[(alias, ds, "d_cost:" + k_)] = dc; BOOTV[(alias, ds, "cmr:" + k_)] = cm
    if ds == "cap4":
        dc, cm = VEC[hp]
        HOLM_FAMILY.append((alias, "R3-a tap-priced (0.03) weighted cost of sampled-share-ask @10/100 < always-commit", float((1 + (dc >= 0).sum()) / (len(dc) + 1))))
        HOLM_FAMILY.append((alias, "R3-b caught_minus_random > 0 for sampled-share-ask @10/100", float((1 + (cm <= 0).sum()) / (len(cm) + 1))))
    return rows, pareto, sens


# ------------------------------------------------------------------ G1 check
def g1_check(U, G):
    import interventions as I
    flags = collections.Counter(); n = 0
    gl = labels_for([G[i]["g"]["text"] for i in U.input])
    for inp, l in zip(U.input, gl):
        spec = I.supplied(inp); fl = I.check(G[inp]["g"]["text"], spec, label=dict(polarity=l[0], politeness=l[1], speech_act=l[2], agent="speaker", certainty="plain assertion")); n += 1
        for f in fl: flags[f.split(":")[0] + ":" + f.split(":")[1] if f.startswith("politeness") else f.split(":")[0]] += 1
    return dict(n_units=n, supplied_dims_on_bare_keywords=sorted(I.supplied(U.input.iloc[0]).keys()), flag_counts=dict(flags))


# ------------------------------------------------------------------ pair scoring
def pair_summary(key, alias, G):
    f = RUNS / key / "pairs_raw.json"
    if not f.exists(): return None
    rows = json.load(open(f)); out = []
    for r in rows:
        if "aff" not in r or "neg" not in r: continue
        sc = L.pair_scores(r["neg"]["ids"], r["neg"]["lp"], r["aff"]["ids"], r["aff"]["lp"])   # positive = affirmative preferred over negated
        d = dict(dataset=r["dataset"], family_id=r["family_id"], **{f"true_{k}": v for k, v in sc.items()}, imputed=sum(r[k]["imputed"] for k in r if isinstance(r[k], dict) and "imputed" in r[k]),
                 imp_aff=r["aff"]["imputed"], imp_neg=r["neg"]["imputed"])
        for pk, (a, b) in {"tog": ("neg", "neg_tog"), "nopneg": ("neg", "neg_nop"), "nopaff": ("aff", "aff_nop")}.items():
            if a in r and b in r:
                sp = L.pair_scores(r[a]["ids"], r[a]["lp"], r[b]["ids"], r[b]["lp"]); d.update({f"{pk}_{k}": v for k, v in sp.items()})
        inp = "Keywords: " + r["bare"]
        if inp in G: d["sampled_neg_share_bare"] = float(np.mean([x[0] == "negated" for x in labels_for([s["text"] for s in G[inp]["s"]])])); d["greedy_neg_bare"] = labels_for([G[inp]["g"]["text"]])[0][0] == "negated"
        out.append(d)
    P = pd.DataFrame(out); res = {"n_pairs": len(P), "scorers": {}}
    for sc in ("full_sum", "len_norm", "span_sum", "span_mean"):
        t = P[f"true_{sc}"].to_numpy(); pl = np.concatenate([P[c].dropna().to_numpy() for c in (f"tog_{sc}", f"nopneg_{sc}", f"nopaff_{sc}") if c in P])
        res["scorers"][sc] = dict(median_logodds_aff_over_neg=float(np.median(t)), share_aff_preferred=float((t > 0).mean()), n_placebo=int(len(pl)), **L.placebo_contrast(t, pl),
                                  by_placebo={k: dict(n=int(P[f"{k}_{sc}"].notna().sum()), median_abs=float(np.median(np.abs(P[f"{k}_{sc}"].dropna()))) if P[f"{k}_{sc}"].notna().any() else None)
                                              for k in ("tog", "nopneg", "nopaff") if f"{k}_{sc}" in P})
    # A18: top-1000 imputation sensitivity. Imputed value = upper bound of the missing logprob: imputation in neg can only understate the
    # aff-over-neg log-odds, imputation in aff can only overstate it.
    cl = P[(P.imp_aff == 0) & (P.imp_neg == 0)]
    res["imputation_sensitivity"] = dict(n_all=len(P), n_clean=len(cl), n_imp_aff_only=int(((P.imp_aff > 0) & (P.imp_neg == 0)).sum()), n_imp_neg_only=int(((P.imp_aff == 0) & (P.imp_neg > 0)).sum()),
        n_imp_both=int(((P.imp_aff > 0) & (P.imp_neg > 0)).sum()),
        by_scorer={sc: dict(median_all=float(P[f"true_{sc}"].median()), median_clean=float(cl[f"true_{sc}"].median()) if len(cl) else None,
                            share_aff_pref_all=float((P[f"true_{sc}"] > 0).mean()), share_aff_pref_clean=float((cl[f"true_{sc}"] > 0).mean()) if len(cl) else None,
                            # conservative: flip every sign-unsafe pair against the claim "aff preferred" (imp in aff & positive -> may be overstated)
                            share_aff_pref_conservative=float((((P[f"true_{sc}"] > 0) & ~((P.imp_aff > 0) & (P.imp_neg == 0))).sum()) / len(P)),
                            share_aff_pref_optimistic=float((((P[f"true_{sc}"] > 0) | ((P.imp_neg > 0) & (P.imp_aff == 0))).sum()) / len(P))) for sc in ("full_sum", "len_norm", "span_sum", "span_mean")})
    res["status"] = "PROVISIONAL, noise-limited (0.1-0.4 nats per token; A10/A18)"
    res["imputed_tokens_total"] = int(P.imputed.sum()); res["median_span_len_neg_vs_aff"] = [float(P.true_span_len_a.median()), float(P.true_span_len_b.median())]
    if "sampled_neg_share_bare" in P:
        res["sampled_neg_share_on_bare_pairs_mean"] = float(P.sampled_neg_share_bare.mean()); res["greedy_neg_share_on_bare_pairs"] = float(P.greedy_neg_bare.mean())
        res["corr_span_sum_vs_sampled_neg_share"] = float(np.corrcoef(P.true_span_sum, P.sampled_neg_share_bare)[0, 1]) if P.sampled_neg_share_bare.std() > 0 else None
    P.to_csv(OUT / f"pairs_{alias}.csv", index=False); return res


# ------------------------------------------------------------------ main
ALL = {"r1": [], "rel": [], "bins": [], "r2": [], "pol": [], "pareto": [], "sens": []}
for spec in A.models:
    key, alias = spec.split(":"); G = load_model(key); R = unit_frame(G, alias)
    U = U0.merge(R, left_on="input", right_index=True, how="inner"); assert len(U) == len(U0), (len(U), len(U0))
    cf = R.loc["Keywords: N/A"] if "Keywords: N/A" in R.index else None
    ms = {"n_inputs": len(G), "requests_missing": int(sum(1 for i in G if len(G[i]["s"]) != K or G[i]["g"] is None)), "mean_unique_texts_per_16": float(R.n_unique.mean()),
          "finish_length_total": int(R.finish_len.sum()), "content_free_N/A": (dict(sampled_neg=float(cf.s_neg), sampled_politeness=float(cf.s_pol), sampled_nonstatement=float(cf.s_act), greedy_neg=bool(cf.g_neg)) if cf is not None else None)}
    ms["g1_check"] = g1_check(U, G)
    for ds in ("human", "cap4"):
        Ud = U[U.dataset == ds].reset_index(drop=True); M = mult_for(Ud)
        ALL["r1"] += r1_table(Ud, M, alias, ds)
        r, bins = reliability(Ud, M, alias, ds); ALL["rel"].append(r); ALL["bins"] += bins
        rr, scores_u, u = r2_table(Ud, M, alias, ds); ALL["r2"] += rr
        pr, par, sens = policies(Ud, M, alias, ds, scores_u, u, float(cf.s_neg) if cf is not None else 0.0, ms["g1_check"])
        ALL["pol"] += pr; ALL["pareto"] += par; ALL["sens"] += sens
        print(alias, ds, "done", flush=True)
    ms["pairs"] = pair_summary(key, alias, G); SUMM["models"][alias] = ms
# ------------------------------------------------------------------ pooled over models (item-clustered, same resample) and Holm (A20, A22)
POOL = []
aliases = [sp.split(":")[1] for sp in A.models]
if len(aliases) > 1:
    for ds in ("human", "cap4"):
        for nm in sorted({k[2] for k in BOOTV if k[1] == ds and k[2].startswith("auroc:")}):
            vs = [BOOTV[(a_, ds, nm)] for a_ in aliases if (a_, ds, nm) in BOOTV]; pooled = np.mean(vs, axis=0)
            pt = float(np.mean([next(r["auroc"] for r in ALL["r2"] if r["model"] == a_ and r["dataset"] == ds and r["score"] == nm.split(":", 1)[1]) for a_ in aliases]))
            POOL.append(dict(dataset=ds, quantity=nm, n_models=len(vs), point=pt, lo=L.pct_ci(pooled)[0], hi=L.pct_ci(pooled)[1], status="pooled, item-clustered" + ("" if ds == "cap4" else " EXPLORATORY")))
        for nm in ("diff:lexical_cv_logistic", "diff:greedy_first_token_entropy", "diff:greedy_mean_token_entropy"):
            vs = [BOOTV[(a_, ds, nm)] for a_ in aliases if (a_, ds, nm) in BOOTV]; pooled = np.mean(vs, axis=0)
            POOL.append(dict(dataset=ds, quantity="sampled_share AUROC minus " + nm[5:], n_models=len(vs), point=float(np.mean(vs)), lo=L.pct_ci(pooled)[0], hi=L.pct_ci(pooled)[1], p_gt0=float((1 + (pooled <= 0).sum()) / (len(pooled) + 1)), status="pooled, item-clustered" + ("" if ds == "cap4" else " EXPLORATORY")))
        hp = "sampled share (semantic-entropy analogue) @ 10/100"
        for q, lab in (("d_cost:", "d_cost vs always-commit (sampled-share-ask @10/100)"), ("cmr:", "caught minus random (sampled-share-ask @10/100)")):
            vs = [BOOTV[(a_, ds, q + hp)] for a_ in aliases if (a_, ds, q + hp) in BOOTV]
            if vs:
                pooled = np.mean(vs, axis=0); POOL.append(dict(dataset=ds, quantity=lab, n_models=len(vs), point=float(np.mean(vs)), lo=L.pct_ci(pooled)[0], hi=L.pct_ci(pooled)[1], status="pooled, item-clustered" + ("" if ds == "cap4" else " EXPLORATORY")))
ALL["pooled"] = POOL
H = pd.DataFrame(HOLM_FAMILY, columns=["model", "test", "p_raw"])
if len(H):
    order = np.argsort(H.p_raw.to_numpy()); m_ = len(H); adj = np.empty(m_); run = 0.0
    for rank, i in enumerate(order): run = max(run, (m_ - rank) * H.p_raw.iloc[i]); adj[i] = min(1.0, run)
    H["p_holm"] = adj; H["reject_at_0.05"] = H.p_holm < 0.05; H["family"] = "E-cap4 confirmatory (A22), one-sided bootstrap p"
ALL["holm"] = H.to_dict("records")
for k, v in ALL.items(): pd.DataFrame(v).to_csv(OUT / f"{k}.csv", index=False)
SUMM["tables"] = {k: pd.DataFrame(v).to_dict("records") for k, v in ALL.items() if k in ("r1", "rel", "r2", "pol", "pooled", "holm")}
SUMM["detector_validity_applied"] = DETV is not None
json.dump(SUMM, open(OUT / "summary.json", "w"), indent=1, default=lambda o: None if isinstance(o, float) and math.isnan(o) else (o.item() if hasattr(o, "item") else str(o)))
print("written", OUT)
