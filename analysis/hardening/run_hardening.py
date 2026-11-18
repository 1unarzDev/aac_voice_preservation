"""A4 CPU hardening (plan: analysis/hardening/PLAN.md, written before this was run).
  . .venv/bin/activate; python analysis/hardening/run_hardening.py [--part listener|leak|slp|power|estimand|all] [--B 10000]
Writes analysis/hardening/*.csv, summary.json. Frozen estimates are read, never overwritten."""
from __future__ import annotations
import argparse, json, re, sys, math, warnings
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "hardening"
sys.path.insert(0, str(ROOT / "src"))
import score_listener_study as S
import score_slp_panel as P
SEED = 20261117
warnings.filterwarnings("ignore")


def listener_frame():
    key = S.load_key(); ret = S.read_returns(ROOT / "annotation" / "returns_part28")
    ret, rep = S.qc(ret, key); dec = S.decode(ret, key); ex = S.exclusions(dec, key)
    assert not ex["excluded"]
    x = S.expand(dec)
    return key, dec, x


# ---------------------------------------------------------------- 1. crossed models
def vb_fit(d, seed):
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    d = d.copy()
    conds = [c for c in ["bare"] + sorted(set(d.cond) - {"bare"})]
    d["cond"] = pd.Categorical(d.cond, categories=conds)
    vc = {"item": "0 + C(item)", "listener": "0 + C(annotator)"}
    m = BinomialBayesMixedGLM.from_formula("y ~ C(cond)", vc, d)
    r = m.fit_vb()
    names = list(m.exog_names)
    rng = np.random.default_rng(seed)
    nd = 4000
    fe = rng.normal(r.fe_mean, r.fe_sd, size=(nd, len(r.fe_mean)))
    sd = np.exp(rng.normal(r.vcp_mean, r.vcp_sd, size=(nd, len(r.vcp_mean))))
    # population-averaged probability by condition, integrating the two random intercepts (Monte Carlo, 400 nodes per draw)
    z = rng.standard_normal((nd, 400, 2))
    tot = np.sqrt((sd ** 2).sum(1))[:, None]
    pa = {}
    for j, c in enumerate(conds):
        eta = fe[:, [0]] + (fe[:, [j]] if j else 0) + (z * sd[:, None, :]).sum(2)
        pa[c] = (1 / (1 + np.exp(-eta))).mean(1)
    return {"conds": conds, "fe_mean": dict(zip(names, map(float, r.fe_mean))), "fe_sd": dict(zip(names, map(float, r.fe_sd))),
            "vcp_sd_item": float(np.exp(r.vcp_mean[0])), "vcp_sd_listener": float(np.exp(r.vcp_mean[1])), "pa": pa}


def lpm(d, paired):
    import statsmodels.formula.api as smf
    d = d.copy(); d["item_c"] = pd.factorize(d["item"])[0]; d["lis_c"] = pd.factorize(d["annotator"])[0]
    d["t"] = (d.cond != "bare").astype(float)
    if paired:
        m = smf.ols("y ~ t + C(item)", d).fit(cov_type="cluster", cov_kwds={"groups": d["lis_c"]})
    else:
        m = smf.ols("y ~ t", d).fit(cov_type="cluster", cov_kwds={"groups": np.column_stack([d.item_c, d.lis_c])})
    b = float(m.params["t"]); se = float(m.bse["t"])
    return b, se


def listener_models(x, frozen):
    rows = []
    specs = [("chip1", "bare", "success"), ("chip1", "bare", "reversal"), ("chip1", "bare", "conseq"), ("chip1", "bare", "unclear"),
             ("G1", "bare", "success"), ("nlcue", "chip1", "success"), ("nlcue", "chip1", "reversal"), ("nlcue", "chip1", "conseq")]
    vcs = {}
    for a, b, m in specs:
        d = x[x.cond.isin([a, b])].copy(); d["y"] = d[m]; d = d.dropna(subset=["y"])
        if b != "bare":
            # keep the second arm as reference: relabel so the reference is called "bare" inside the helper
            d["cond"] = np.where(d.cond == b, "bare", d.cond)
        # items present in both arms only (paired items), as in the frozen contrasts
        both = set(d[d.cond == "bare"]["item"]) & set(d[d.cond != "bare"]["item"]); d = d[d["item"].isin(both)]
        out = {"contrast": f"{a} - {b}", "metric": m, "n_rows": len(d), "n_items": d["item"].nunique(), "n_listeners": d.annotator.nunique(),
               "rate_ref": d[d.cond == "bare"].y.mean() * 100, "rate_arm": d[d.cond != "bare"].y.mean() * 100}
        if a == "G1":
            out.update(note="G1 identical to bare for 118/120 items by construction; GLMM not fitted"); rows.append(out); continue
        try:
            v = vb_fit(d, SEED)
            diff = (v["pa"][a] - v["pa"]["bare"]) * 100
            out.update(glmm_diff=float(np.mean(diff)), glmm_lo=float(np.percentile(diff, 2.5)), glmm_hi=float(np.percentile(diff, 97.5)),
                       glmm_logit=v["fe_mean"].get(f"C(cond)[T.{a}]"), glmm_logit_sd=v["fe_sd"].get(f"C(cond)[T.{a}]"),
                       sd_item=v["vcp_sd_item"], sd_listener=v["vcp_sd_listener"])
        except Exception as e:  # reported, not hidden
            out["glmm_error"] = repr(e)[:200]
        for tag, paired in (("lpm2way", False), ("lpm_itemFE", True)):
            try:
                b_, se_ = lpm(d, paired)
                out.update({f"{tag}_diff": b_ * 100, f"{tag}_lo": (b_ - 1.96 * se_) * 100, f"{tag}_hi": (b_ + 1.96 * se_) * 100, f"{tag}_se": se_ * 100})
            except Exception as e:
                out[f"{tag}_error"] = repr(e)[:200]
        out.update(signflip(d))
        fk = frozen.get((f"{a} - {b}", m))
        if fk:
            out.update(frozen_diff=fk[0], frozen_lo=fk[1], frozen_hi=fk[2])
        rows.append(out)
    return pd.DataFrame(rows)


def signflip(d, n=100000):
    """Randomisation tests on the arm difference: items as clusters (item-balanced difference, sign flips) and listeners as clusters."""
    rng = np.random.default_rng(SEED)
    out = {}
    for tag, g in (("item", "item"), ("listener", "annotator")):
        t = d.assign(arm=(d.cond != "bare")).groupby([g, "arm"]).y.mean().unstack()
        diff = (t[True] - t[False]).dropna().to_numpy()
        obs = diff.mean()
        flips = rng.choice([-1.0, 1.0], size=(n, len(diff)))
        sim = (flips * diff).mean(1)
        out[f"signflip_p_{tag}"] = float((np.abs(sim) >= abs(obs) - 1e-12).mean())
    return out


def frozen_contrasts():
    c = pd.read_csv(ROOT / "analysis" / "listener_human" / "contrasts.csv")
    f = {}
    for r in c.itertuples():
        sc = 1.0 if r.unit == "pp" else 0.1          # per 1000 -> pp
        f[(r.contrast, r.metric)] = (r.estimate * sc, r.lo * sc, r.hi * sc)
    return f


def run_listener():
    key, dec, x = listener_frame()
    df = listener_models(x, frozen_contrasts())
    df.to_csv(OUT / "listener_crossed_models.csv", index=False)
    # crossing structure
    cells = x.drop_duplicates(["item", "annotator"]).shape[0]
    struct = {"n_listeners": int(x.annotator.nunique()), "n_items": int(x["item"].nunique()), "n_item_listener_cells": int(cells),
              "judgments_per_item_median": float(x.drop_duplicates(["item", "annotator"]).groupby("item").size().median())}
    return df, struct


# ---------------------------------------------------------------- 2. leakage audit
def norm(t):
    return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(t).lower())).strip() + " "


def files_for(L):
    return [p for p in sorted((ROOT / "annotation_package").glob(f"stage*/{L}_*")) if "part28" not in p.name]


def run_leak():
    key = S.load_key(); stim = pd.read_json(ROOT / "analysis" / "listener" / "stimuli.jsonl", lines=True)
    hw = pd.concat([pd.read_json(ROOT / "data/items/hw.jsonl", lines=True), pd.read_json(ROOT / "data/items/hw2.jsonl", lines=True)])
    chk = pd.concat([pd.read_csv(ROOT / "analysis/hw_checks/items.csv"), pd.read_csv(ROOT / "analysis/hw2_checks/items.csv")])
    fam = key.drop_duplicates("item").set_index("item")["family_id"]
    hwi = hw.set_index("family_id"); chki = chk.set_index("family_id")
    res = {"n_families": int(fam.nunique())}
    # (a) direct roles
    listeners = sorted(key.annotator.unique())
    self_w = self_c = 0; rows = []
    for r in key.itertuples():
        w = hwi.loc[r.family_id, "writer_id"]; cs = str(chki.loc[r.family_id, "checkers"]).split()
        self_w += (w == r.annotator); self_c += (r.annotator in cs)
    res.update(listener_is_writer_of_judged_pair=int(self_w), listener_is_checker_of_judged_pair=int(self_c), n_key_rows=int(len(key)))
    # writers/checkers of the drawn families who are also listeners (all 20 are the same pool, so overlap in persons is expected)
    fw = set(hwi.loc[fam.values, "writer_id"]); res["distinct_writers_of_drawn_families"] = len(fw)
    # same pair (by hc item id, packet files as sent and returns as received) vs. same sentence text in another pair
    hc_of = chk.set_index("family_id")["item_id"]
    pair_seen = 0; pair_cells = []
    for r in key.itertuples():
        hid = hc_of[r.family_id]
        for p in files_for(r.annotator):
            if hid in p.read_text(errors="ignore"):
                pair_seen += 1; pair_cells.append((r.item, r.annotator, p.name)); break
    res["same_pair_id_in_listener_packet_cells"] = int(pair_seen)
    ret_seen = 0
    for f in (ROOT / "annotation/returns_hwcheck").glob("*.csv"):
        d = pd.read_csv(f, dtype=str)
        for r in key.itertuples():
            if (d.annotator == r.annotator).any() and (d.item_id == hc_of[r.family_id]).any() and (d.annotator == r.annotator)[d.item_id == hc_of[r.family_id]].any():
                ret_seen += 1
    for f in (ROOT / "annotation/returns_hwcheck_hw2").glob("*.csv"):
        d = pd.read_csv(f, dtype=str)
        for r in key.itertuples():
            m = d[(d.item_id == hc_of[r.family_id]) & (d.annotator == r.annotator)]
            ret_seen += len(m) > 0
    res["same_pair_id_in_listener_check_returns_cells"] = int(ret_seen)
    # (b) within-study
    res["max_units_same_item_same_listener"] = int(key.groupby(["item", "annotator"]).size().max())
    res["listeners_per_item_min_max"] = [int(key.groupby("item").annotator.nunique().min()), int(key.groupby("item").annotator.nunique().max())]
    ref_unit_listeners = key[key.conditions == "reference"].groupby("item").annotator.apply(set)
    # (c) cross-stage text exposure
    pat = {}
    for it, f in fam.items():
        sents = [hwi.loc[f, "variants"][v]["source"] for v in "AB"] + list(stim[stim["item"] == it].output_text)
        pat[it] = {norm(t) for t in sents if len(str(t).split()) >= 3}
    srcs = {it: {norm(hwi.loc[f, "variants"][v]["source"]) for v in "AB"} for it, f in fam.items()}
    files = {}
    for L in listeners:
        fl = [p for p in sorted((ROOT / "annotation_package").glob(f"stage*/{L}_*")) if "part28" not in p.name]
        files[L] = fl
    rows = []
    for r in key.itertuples():
        for p in files[r.annotator]:
            txt = norm(p.read_text(errors="ignore"))
            src = any(t in txt for t in srcs[r.item]); out = any(t in txt for t in pat[r.item])
            if src or out:
                rows.append({"item": r.item, "family_id": r.family_id, "listener": r.annotator, "file": f"{p.parent.name}/{p.name}", "source_sentence_seen": src, "any_sentence_seen": out,
                             "role": "writer" if hwi.loc[r.family_id, "writer_id"] == r.annotator else "checker" if r.annotator in str(chki.loc[r.family_id, "checkers"]).split() else "other"})
    ex = pd.DataFrame(rows)
    ex.to_csv(OUT / "leakage_exposure_cells.csv", index=False)
    res["exposed_listener_item_cells"] = int(ex.drop_duplicates(["item", "listener"]).shape[0]) if len(ex) else 0
    res["exposed_cells_share_of_846"] = res["exposed_listener_item_cells"] / len(key)
    if len(ex):
        res["exposed_by_part"] = ex.assign(part=ex.file.str.extract(r"(part\d+|check_\d|check_hw2|intent|tiebreak)")[0]).groupby("part").size().to_dict()
        res["exposed_by_role"] = ex.drop_duplicates(["item", "listener"]).role.value_counts().to_dict()
        res["exposed_source_sentence_cells"] = int(ex[ex.source_sentence_seen].drop_duplicates(["item", "listener"]).shape[0])
    # sensitivity: drop exposed cells
    key_, dec, x = listener_frame()
    bad = set(zip(ex["item"], ex["listener"])) if len(ex) else set()
    x["exposed"] = [(i, a) in bad for i, a in zip(x["item"], x["annotator"])]
    sens = []
    for lab, d in (("all", x), ("drop_exposed_cells", x[~x.exposed])):
        for m in ("success", "reversal", "conseq"):
            t = {}
            for c in ("bare", "chip1"):
                g = d[d.cond == c].groupby("item")[m].mean()
                t[c] = g
            both = t["bare"].index.intersection(t["chip1"].index)
            sens.append({"sample": lab, "metric": m, "bare": t["bare"].mean() * 100, "chip1": t["chip1"].mean() * 100,
                         "diff_paired_items": float((t["chip1"][both] - t["bare"][both]).mean() * 100), "n_items_both": len(both), "n_judgments": int(len(d))})
    sdf = pd.DataFrame(sens); sdf.to_csv(OUT / "leakage_sensitivity.csv", index=False)
    res["sensitivity"] = sdf.round(2).to_dict("records")
    # exposed-cell vs unexposed success
    res["success_exposed_vs_not"] = {"exposed": float(x[x.exposed].success.mean()) if x.exposed.any() else None, "not": float(x[~x.exposed].success.mean())}
    return res


# ---------------------------------------------------------------- 3. SLP weight sensitivity
DIM2TYPE = {"polarity": "NEG", "speech_act": "ACT", "agent": "AGT", "time_quantity": "TIM"}


def slp_schemes(t1, raters):
    w = {"frozen_mean": P.weights_from(t1)}
    for r in raters:
        w[f"only_{r}"] = P.weights_from(t1, r)            # leave-one-out with n = 2 is the other rater alone
    w["uniform_1"] = {t: 1.0 for t in P.TYPES}
    order = sorted(P.TYPES, key=lambda t: t1[t]["mean"])
    w["rank_based"] = {t: (sum(t1[u]["mean"] <= t1[t]["mean"] for u in P.TYPES)) / len(P.TYPES) for t in P.TYPES}
    w["critical_only(sev>=4)"] = {t: 1.0 if t1[t]["mean"] >= 4 else 0.0 for t in P.TYPES}
    return w


def run_slp(B=2000):
    by = P.load_returns(ROOT / "expert_package/returns_slp"); raters = sorted(by); t1 = P.task1(by)
    pop, nn = P.load_counts(ROOT / "expert_package/judge_failure_counts.csv")
    W = slp_schemes(t1, raters)
    papers = {"slp_wc_base": ("W-C speech-act (1,872 targets)", "baseline_P0"), "slp_wc_guard": ("W-C speech-act (1,872 targets)", "guard_G1"),
              "slp_hw_base": ("hw1 human-written pairs, six dimensions", "baseline_bare"), "slp_hw_chip": ("hw1 human-written pairs, six dimensions", "chip"),
              "slp_hw_word": ("hw1 human-written pairs, six dimensions", "word")}
    rows = []
    for k, (pp, arm) in papers.items():
        pats = pop[pp][arm]; n = nn[(pp, arm)]
        for sch, w in W.items():
            v, miss = P.weighted_rate(pats, n, w)
            rows.append({"macro": k, "population": pp, "arm": arm, "scheme": sch, "weighted_rate_pct": v})
    df = pd.DataFrame(rows)
    pv = df.pivot(index="scheme", columns="macro", values="weighted_rate_pct")
    pv["WC_guard_minus_base_pp"] = pv["slp_wc_guard"] - pv["slp_wc_base"]; pv["WC_rel_reduction_pct"] = 100 * (1 - pv["slp_wc_guard"] / pv["slp_wc_base"])
    pv["HW_chip_minus_bare_pp"] = pv["slp_hw_chip"] - pv["slp_hw_base"]; pv["HW_rel_reduction_chip_pct"] = 100 * (1 - pv["slp_hw_chip"] / pv["slp_hw_base"])
    pv["HW_word_minus_bare_pp"] = pv["slp_hw_word"] - pv["slp_hw_base"]
    pv["HW_chip_vs_word_pp"] = pv["slp_hw_chip"] - pv["slp_hw_word"]
    pv.to_csv(OUT / "slp_weight_sensitivity_papers.csv")
    wt = pd.DataFrame(W).T; wt.to_csv(OUT / "slp_weights_by_scheme.csv")
    # listener SLP-weighted reversal
    key, dec, x = listener_frame(); res_l = []
    for sch, w in W.items():
        x2 = x.copy(); x2["slp_reversal"] = x2["dimension"].map(lambda d: w[DIM2TYPE[d]]) * x2["reversal"]
        D, cell0, contr0, cells, cons = S.analyse(x2, B=B, seed=SEED)
        out = {"scheme": sch, "w_polarity": w["NEG"], "w_speech_act": w["ACT"], "w_agent": w["AGT"], "w_time": w["TIM"]}
        for c in ("bare", "chip1"):
            n = D.cells.index((c, "all")); out[f"{c}_per1000"] = float(cell0["slp_reversal"][n] * 1000)
            out[f"{c}_lo"] = S.pct(cells["slp_reversal"][:, n], 2.5) * 1000; out[f"{c}_hi"] = S.pct(cells["slp_reversal"][:, n], 97.5) * 1000
        k = ("chip1", "bare", "slp_reversal"); out["diff_per1000"] = float(contr0[k] * 1000)
        out["diff_lo"] = S.pct(cons[k], 2.5) * 1000; out["diff_hi"] = S.pct(cons[k], 97.5) * 1000
        res_l.append(out)
    ldf = pd.DataFrame(res_l); ldf.to_csv(OUT / "slp_weight_sensitivity_listener.csv", index=False)
    return {"raters": raters, "weights": wt.round(3).to_dict("index"), "papers": pv.round(2).to_dict("index"), "listener": ldf.round(2).to_dict("records"),
            "severity_by_rater": {t: t1[t]["by_rater"] for t in P.TYPES}}


# ---------------------------------------------------------------- 4. power / MDE
Z_A, Z_B = 1.959964, 0.841621
def npdf_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))
def power_two_sided(delta, se):
    return npdf_cdf(abs(delta) / se - Z_A) + npdf_cdf(-abs(delta) / se - Z_A)
def mde(se):
    return (Z_A + Z_B) * se


def newcombe(k1, n1, k2, n2):
    def wil(k, n):
        p = k / n; z = 1.959964; d = 1 + z * z / n
        c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
        return p, c - h, c + h
    p1, l1, u1 = wil(k1, n1); p2, l2, u2 = wil(k2, n2); d = p1 - p2
    return d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def run_power():
    rows = []
    # Part 17: repaired vs control usable, 60 v 60 items (item-level consensus), frozen rule margin -10 pp
    n = 60; pc, pr = 51 / 60, 43 / 60
    se_obs = math.sqrt(pc * (1 - pc) / n + pr * (1 - pr) / n)
    pbar = (pc + pr) / 2; se_h0 = math.sqrt(2 * pbar * (1 - pbar) / n)
    rng = np.random.default_rng(SEED)
    def sim_power(true_diff, pc_=pc, n_=60, margin=-0.10, reps=20000):
        pr_ = pc_ + true_diff; ok = 0
        kc = rng.binomial(n_, pc_, reps); kr = rng.binomial(n_, pr_, reps)
        for a_, b_ in zip(kc, kr):
            if 0 < a_ < n_ and 0 < b_ < n_ or True:
                d, lo, hi = newcombe(int(b_), n_, int(a_), n_)
                ok += lo > margin
        return ok / reps
    pw0 = sim_power(0.0, reps=4000); pw5 = sim_power(-0.05, reps=4000)
    n80 = int(math.ceil((Z_A + Z_B) ** 2 * 2 * pc * (1 - pc) / 0.10 ** 2))
    rows.append({"study": "Part 17 repair audit v2", "endpoint": "usable, repaired - control (item consensus)", "design": "60 v 60 items, Newcombe CI, binomial items (rater variance ignored)",
                 "frozen_estimate_pp": (pr - pc) * 100, "se_pp": se_obs * 100, "mde80_pp": mde(se_obs) * 100,
                 "power_at_10pp": power_two_sided(0.10, se_obs), "note": f"non-inferiority rule (lower bound > -10 pp): power {pw0:.2f} if true diff 0, {pw5:.2f} if -5 pp; n per arm for 80% at 0 true diff and -10 pp margin = {n80}"})
    # Part 18: writer-intent match chip - bare, writer cluster bootstrap recomputed
    d = pd.read_csv(ROOT / "analysis/intent_check/items.csv"); d = d[d.says.notna()].copy()
    d["match"] = (d.says == "version " + d.intended_variant).astype(float)
    ws = sorted(d.writer_id.unique()); g = {w: d[d.writer_id == w] for w in ws}
    diffs = []
    for _ in range(5000):
        samp = pd.concat([g[w] for w in rng.choice(ws, len(ws))])
        diffs.append(samp[samp.channel == "chip1"].match.mean() - samp[samp.channel == "bare"].match.mean())
    obs = d[d.channel == "chip1"].match.mean() - d[d.channel == "bare"].match.mean(); se18 = float(np.std(diffs, ddof=1))
    rows.append({"study": "Part 18 writer intent", "endpoint": "match (says = intended version), chip - bare", "design": f"{d.writer_id.nunique()} writers, {len(d)} rated items, writer-cluster bootstrap SE",
                 "frozen_estimate_pp": obs * 100, "se_pp": se18 * 100, "mde80_pp": mde(se18) * 100, "power_at_10pp": power_two_sided(0.10, se18), "note": "frozen CI 14.8 to 42.0 pp"})
    # Part 28 listener: SE from the frozen two-way bootstrap CI, and from the crossed models
    lc = pd.read_csv(ROOT / "analysis/listener_human/contrasts.csv"); lm = pd.read_csv(OUT / "listener_crossed_models.csv")
    for metric, label, sc in (("success", "success, chip - bare", 1.0), ("conseq", "opposite action, chip - bare", 1.0), ("reversal", "received reversal, chip - bare", 0.1)):
        r = lc[(lc.contrast == "chip1 - bare") & (lc.metric == metric)].iloc[0]
        se = (r.hi - r.lo) / 3.92 * sc; m_ = lm[(lm.contrast == "chip1 - bare") & (lm.metric == metric)].iloc[0]
        rows.append({"study": "Part 28 listener", "endpoint": label, "design": "120 items x 20 listeners, two-way cluster bootstrap SE (frozen)", "frozen_estimate_pp": r.estimate * sc, "se_pp": se,
                     "mde80_pp": mde(se), "power_at_10pp": power_two_sided(5.0 if metric == "reversal" else 10.0, se),
                     "note": ("power column is at 5 pp (the whole bare rate), not 10 pp; " if metric == "reversal" else "") + f"item-FE LPM SE {m_.lpm_itemFE_se:.2f} pp gives MDE {mde(m_.lpm_itemFE_se):.1f} pp; two-way LPM SE {m_.lpm2way_se:.2f} pp gives {mde(m_.lpm2way_se):.1f} pp"})
    # Stage 6
    cc = pd.read_csv(ROOT / "analysis/coverage_human/contrasts.csv")
    for r in cc[cc.primary].itertuples():
        se = (r.hi_pp - r.lo_pp) / 3.92
        rows.append({"study": "Stage 6 (Parts 26/27)", "endpoint": f"H-cov {r.name}", "design": "100 items, 20 writers, writer-cluster bootstrap SE (frozen)", "frozen_estimate_pp": r.diff_pp, "se_pp": se,
                     "mde80_pp": mde(se), "power_at_10pp": power_two_sided(10.0, se), "note": f"{r.kind}; frozen status {r.status}"})
    df = pd.DataFrame(rows); df.to_csv(OUT / "power_mde.csv", index=False)
    return df.round(3).to_dict("records")


# ---------------------------------------------------------------- 5. estimand table and chain
def pp(v, d=1):
    return f"{v:+.{d}f}".replace("-", "-")


def run_estimand(B=5000):
    key, dec, x = listener_frame()
    lc = pd.read_csv(ROOT / "analysis/listener_human/contrasts.csv"); bc = pd.read_csv(ROOT / "analysis/listener_human/by_condition.csv")
    g = lambda m: lc[(lc.contrast == "chip1 - bare") & (lc.metric == m)].iloc[0]
    # speech-act-only listener contrast (the dimension q-hat was measured on)
    xs = x[x.dimension == "speech_act"]
    D, c0, k0, cells, cons = S.analyse(xs, B=B, seed=SEED); kk = ("chip1", "bare", "success")
    sa = {"est": float(k0[kk] * 100), "lo": S.pct(cons[kk], 2.5) * 100, "hi": S.pct(cons[kk], 97.5) * 100, "n_items": len(D.items)}
    q = pd.read_csv(ROOT / "analysis/frontier/value_of_cue/human_q_estimates.csv"); q = q[(q.set == "A_cue_lost|speech_act") & (q.measure == "q2_alt")].iloc[0]
    rs = pd.read_csv(ROOT / "analysis/frontier/default_profiles/followup/f1_restoration.csv")
    rs = rs[(rs.dimension == "speech_act") & (rs.model == "pooled(mode=arb)")].set_index("arm")
    G, Glo, Ghi = float(g("success").estimate), float(g("success").lo), float(g("success").hi)
    ref_ceiling = 100.0; bare_s = float(bc[(bc.metric == "success") & (bc.cond == "bare") & (bc.subset == "all")].estimate.iloc[0])
    chain = {
        "links": [
            {"link": "L1 cue supply (writer supplies the dropped speech-act cue and the restored draft is chosen)", "estimate": q.est * 100, "lo": q.lo * 100, "hi": q.hi * 100, "status": "human-judged (9 classmate annotators; speech act only; 36 items)"},
            {"link": "L2 machine restoration given the cue (speech act; bare -> chip, 3 models)", "estimate": rs.loc["chip", "r"] * 100, "lo": rs.loc["chip", "lo"] * 100, "hi": rs.loc["chip", "hi"] * 100, "bare": rs.loc["bare", "r"] * 100, "status": "machine (judge labels, arbiter-resolved)"},
            {"link": "L3 listener success given the cue-in-hand chip output (chip - bare, 4 dimensions)", "estimate": G, "lo": Glo, "hi": Ghi, "status": "measured on 20 adult non-AAC listeners, stored outputs"},
            {"link": "L3s listener success, speech act only (chip - bare)", "estimate": sa["est"], "lo": sa["lo"], "hi": sa["hi"], "status": "measured, subset (30 items), descriptive"},
            {"link": "L4 AAC-user link s (a person who uses AAC supplies the needed cue and picks the restored draft, relative to the classmates of L1)", "estimate": None, "lo": 0.0, "hi": 1.0, "status": "unmeasured; bounds only"}],
        "note": "L2 is embedded in L3 for the chip arm (listeners judged the stored chip outputs), so it is not multiplied in again.",
    }
    qe, ql, qh = q.est, q.lo, q.hi
    proj = {"formula": "gain_pp(s) = s x q x G, with G the cue-in-hand listener gain; s unmeasured",
            "central_s1": qe * G, "s1_interval_product_of_ends": [ql * Glo, qh * Ghi],
            "worst_s0": 0.0, "best_s1_q1": Ghi, "best_ceiling_if_output_as_clear_as_reference": ref_ceiling - bare_s,
            "speech_act_central_s1": qe * sa["est"], "speech_act_interval_product_of_ends": [ql * max(sa["lo"], 0), qh * sa["hi"]],
            "label": "projection (arithmetic on measured links; the AAC-user link is not measured; not a finding)"}
    chain["projection"] = proj
    # table rows (<= 10)
    f1 = lambda v: f"{v:.1f}"
    def rowfromlc(m): r = g(m); sc = 1.0 if r.unit == "pp" else 0.1; return r.estimate * sc, r.lo * sc, r.hi * sc
    rv = rowfromlc("reversal"); cq = rowfromlc("conseq")
    rows = [
        {"id": 1, "claim": "The guard repairs supplied-value failures on fresh items", "estimand": "difference in joint-pass rate, guard minus first pass (machine labels)", "population": "1,872 supplied-cue targets, 4 models, fresh confirmation items",
         "design": "same items, pre-specified, family-cluster bootstrap", "estimate": "+9.8 pts [8.4, 11.3]", "status": "machine"},
        {"id": 2, "claim": "A supplied cue restores the dropped commitment", "estimand": "share of outputs honouring the dropped cue, chip minus bare (speech act)", "population": "120 elicited speech-act units, 3 models",
         "design": "same-item regeneration, arbiter-resolved labels", "estimate": f"{rs.loc['bare','r']*100:.0f}% -> {rs.loc['chip','r']*100:.0f}% [{rs.loc['chip','lo']*100:.0f}, {rs.loc['chip','hi']*100:.0f}]", "status": "machine"},
        {"id": 3, "claim": "People supply the cue when it matters (cue supply q)", "estimand": "share of judgments choosing the cue-restored draft when keywords lost the speech-act cue", "population": "36 items x 2 judgments, 9 adult annotators (not AAC users), speech act only",
         "design": "blind choice between draft pair, item-cluster bootstrap", "estimate": f"{qe*100:.1f}% [{ql*100:.1f}, {qh*100:.1f}]", "status": "human-judged"},
        {"id": 4, "claim": "Listeners pick the intended reading more often with a cue chip", "estimand": "difference in P(intended reading chosen), chip minus bare", "population": "120 messages, 20 adult non-AAC listeners judging stored text",
         "design": "paired by item, crossed listeners, two-way cluster bootstrap (frozen)", "estimate": f"{G:+.1f} pts [{Glo:.1f}, {Ghi:.1f}]", "status": "measured"},
        {"id": 5, "claim": "The cue lowers the consequential error of a listener", "estimand": "difference in P(response implied by the opposite reading), chip minus bare", "population": "as row 4", "design": "as row 4, descriptive secondary",
         "estimate": f"{cq[0]:+.1f} pts [{cq[1]:.1f}, {cq[2]:.1f}]", "status": "measured"},
        {"id": 6, "claim": "The cue lowers received reversals", "estimand": "difference in P(opposite reading chosen), chip minus bare", "population": "as row 4", "design": "as row 4; frozen primary, not confirmed",
         "estimate": f"{rv[0]:+.1f} pts [{rv[1]:.1f}, {rv[2]:+.1f}] (not confirmed)", "status": "measured"},
        {"id": 7, "claim": "Guard repairs are about as usable as untouched outputs", "estimand": "difference in usable share, repaired minus control (item consensus)", "population": "60 + 60 outputs, 6 adult annotators (3 per item)",
         "design": "frozen hash-ordered list, Newcombe CI, margin -10 pts", "estimate": "-13.3 pts [-27.6, +1.5]", "status": "human-judged"},
        {"id": 8, "claim": "Cue outputs carry what the writer meant", "estimand": "difference in writer-named intended version, chip minus bare", "population": "200 outputs of the writers' own pairs, 20 writers", "design": "writer-cluster bootstrap",
         "estimate": "+28 pts [14.8, 42.0]", "status": "human-judged"},
        {"id": 9, "claim": "A cue tap is the cheapest route to stored-text coverage", "estimand": "difference in H-cov, chip G1 minus bare G1", "population": "100 items, 20 writers judging their own pairs", "design": "writer-cluster bootstrap, exploratory",
         "estimate": "+30 pts [15, 44]", "status": "human-judged"},
        {"id": 10, "claim": "A cue helps a person who uses AAC and a listener (chain L1-L4)", "estimand": "s x q x G: gain in listener success per message if the cue is supplied", "population": "people who use AAC and their partners (no data)", "design": "projection from rows 3-4; AAC link unmeasured",
         "estimate": f"worst 0 (s = 0); central {proj['central_s1']:.1f} pts (s = 1); best {Ghi:.0f} pts (s = 1, q = 1, upper end of row 4)", "status": "projection"},
    ]
    pd.DataFrame(rows).to_csv(OUT / "estimand_table.csv", index=False)
    esc = lambda t: t.replace("%", "\\%").replace("&", "\\&").replace("->", "$\\to$").replace("x ", "$\\times$ ")
    with open(OUT / "estimand_table.tex", "w") as f:
        f.write("% Source data for the CALE-AI estimand table; generated by analysis/hardening/run_hardening.py. Numbers are plain text here: convert to macros in paper/caleai/make_macros.py before use.\n")
        f.write("% columns: claim & estimand & population & design & estimate & status\n")
        for r in rows:
            f.write(" & ".join(esc(str(r[c])) for c in ("claim", "estimand", "population", "design", "estimate", "status")) + " \\\\\n")
    return {"rows": rows, "chain": chain}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--part", default="all"); ap.add_argument("--B", type=int, default=10000)
    a = ap.parse_args()
    if a.part in ("leak",):
        r = run_leak(); print(json.dumps(r, indent=1, default=str))
    if a.part == "estimand":
        print(json.dumps(run_estimand(), indent=1, default=str))
    if a.part == "power":
        print(json.dumps(run_power(), indent=1, default=str))
    if a.part == "slp":
        r = run_slp(); print(json.dumps(r, indent=1, default=str))
    if a.part == "all":
        df, st = run_listener(); leak = run_leak(); slp = run_slp(); pw = run_power(); est = run_estimand()
        lm = df.drop(columns=[c for c in df.columns if c == "note"]).round(3).to_dict("records")
        json.dump({"seed": SEED, "listener_models": lm, "listener_structure": st, "leakage": leak, "slp": slp, "power": pw, "estimand": est,
                   "frozen_conclusion_changes": None}, open(OUT / "summary.json", "w"), indent=1, default=str)
        print("ok")
    if a.part == "listener":
        df, st = run_listener(); pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); print(df.round(2).T); print(st)
