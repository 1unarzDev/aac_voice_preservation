"""Synthetic-data unit tests for src/frontier_knows_not_says_lib.py (A2-A7).  python src/frontier_knows_not_says_test.py"""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import frontier_knows_not_says_lib as L


def test_weighted_auroc():
    rng = np.random.default_rng(1)
    s = rng.normal(size=400); y = rng.random(400) < 1 / (1 + np.exp(-2 * s)); w = np.ones(400)
    from itertools import product
    # brute force pairwise
    pos, neg = s[y], s[~y]
    brute = np.mean([(a > b) + 0.5 * (a == b) for a, b in product(pos, neg)])
    assert abs(L.w_auroc(s, y, w) - brute) < 1e-9
    # integer weights == replication
    wi = rng.integers(1, 4, 400).astype(float)
    rep = np.repeat(np.arange(400), wi.astype(int))
    assert abs(L.w_auroc(s, y, wi) - L.w_auroc(s[rep], y[rep], np.ones(len(rep)))) < 1e-9
    # ties
    assert abs(L.w_auroc([0, 0, 0, 0], [1, 0, 1, 0], np.ones(4)) - 0.5) < 1e-12
    # HT weighting matters: upweighting a subset of positives that score low lowers AUROC
    s2 = np.array([0.1, 0.9, 0.2, 0.8]); y2 = np.array([1, 1, 0, 0])
    assert L.w_auroc(s2, y2, np.array([1, 1, 1, 1.])) == 0.5
    assert L.w_auroc(s2, y2, np.array([10, 1, 1, 1.])) < 0.5


def test_ece_brier():
    p = np.array([0, 0, 0.2, 0.2, 0.9, 0.9]); y = np.array([0, 0, 0, 1, 1, 1]); w = np.ones(6)
    e = L.w_ece(p, y, w)
    # bins: {0}: |0-0|; (.125,.25]: |.5-.2|=.3 weight 2/6; (.5,1]: |1-.9|=.1 weight 2/6
    assert abs(e - (2 / 6 * 0.3 + 2 / 6 * 0.1)) < 1e-9
    assert abs(L.w_brier(p, y, w) - np.mean((p - y) ** 2)) < 1e-12


def test_bootstrap_multiplicity_and_weights():
    msg = np.repeat(np.arange(50), 3); strata = np.repeat(np.array(["a"] * 25 + ["b"] * 25), 3)
    M = L.boot_multiplicity(msg, strata, 200, seed=3)
    assert M.shape == (200, 150)
    # units of one message share multiplicity; total multiplicity per stratum constant (resample size = stratum size)
    assert (M[:, 0] == M[:, 1]).all() and (M[:, 0] == M[:, 2]).all()
    assert (M[:, strata == "a"].sum(1) == 75).all() and (M[:, strata == "b"].sum(1) == 75).all()
    # HT weights: weighted mean of a constant is constant; of x with w = 1/p recovers population mean
    rng = np.random.default_rng(0); pop = rng.random(20000) < 0.1
    p_incl = np.where(pop, 0.5, 0.05); keep = rng.random(20000) < p_incl
    est = L.wmean(pop[keep], 1 / p_incl[keep]); assert abs(est - 0.1) < 0.02
    # bootstrap CI covers truth on a simple mean
    x = (rng.random(150) < 0.3).astype(float); w = np.ones(150)
    bs = L.boot_stat(lambda wb, xx: L.wmean(xx, wb), M, w, x); lo, hi = L.pct_ci(bs); assert lo < 0.3 + 0.1 and hi > 0.3 - 0.1 and lo < hi


def test_r1_classes():
    rng = np.random.default_rng(2)
    assert L.r1_class(rng.normal(1.0, 0.1, 5000))[0] == "calibrated"
    assert L.r1_class(rng.normal(0.3, 0.05, 5000))[0].startswith("overconfident")
    assert L.r1_class(rng.normal(3.0, 0.2, 5000))[0].startswith("underconfident")
    assert L.r1_class(rng.normal(1.0, 0.6, 5000))[0] == "inconclusive"      # wide CI straddling both bands
    assert L.r1_class(rng.normal(1.6, 0.05, 5000))[0] == "inconclusive"     # narrow, but outside the equivalence band and not outside [0.5, 2]
    assert L.r1_class(np.full(100, np.inf))[0].startswith("underconfident")
    assert L.power_label(16).startswith("underpowered") and L.power_label(68) == "confirmatory-eligible"


def test_budget_rule_and_random_ask():
    rng = np.random.default_rng(4); n = 4000
    score = np.where(rng.random(n) < 0.7, 0.0, rng.random(n)); w = rng.uniform(1, 5, n)
    for rate in (0.05, 0.25, 0.9):
        a = L.apply_rule(score, L.fit_budget_rule(score, w, rate)); assert abs(L.wmean(a, w) - rate) < 1e-6
    # informative score beats random-ask at same ask rate; uninformative does not
    src = (rng.random(n) < 0.1).astype(float); noc = np.ones(n); out = np.zeros(n)
    good = src * 0.8 + rng.random(n) * 0.3; bad = rng.random(n)
    msg = np.arange(n); strata = np.where(rng.random(n) < 0.5, "a", "b")
    w1 = np.ones(n); rev0, _, _ = L.policy_outcomes(np.zeros(n), src, noc, out, w1)
    res = {}
    for name, sc in (("good", good), ("bad", bad)):
        a = L.crossfit_budget(sc, w1, msg, strata, 0.15, repeats=5)
        rev, spur, taps = L.policy_outcomes(a, src, noc, out, w1); rnd = L.random_ask_reversals(rev0, 1000 * noc.mean(), taps)
        res[name] = (rev, rnd, taps)
    assert abs(res["good"][2] - 150) < 8
    assert res["good"][0] < res["good"][1] - 30       # catches far more than random
    assert abs(res["bad"][0] - res["bad"][1]) < 12    # indistinguishable from random
    # always-ask removes every reversal and spends 1000 taps; always-commit spends none
    r, s, t = L.policy_outcomes(np.ones(n), src, noc, out, w1); assert r == 0 and s == 0 and abs(t - 1000) < 1e-9
    assert abs(rev0 - 1000 * src.mean()) < 1e-9


def test_logreg_cv():
    rng = np.random.default_rng(5); n = 600; X = rng.normal(size=(n, 3)); y = (rng.random(n) < 1 / (1 + np.exp(-(2 * X[:, 0] - 1)))).astype(float)
    oof = L.cv_logreg_oof(X, y, np.ones(n), np.arange(n) // 2)
    assert np.isfinite(oof).all() and L.w_auroc(oof, y > 0, np.ones(n)) > 0.75
    noise = L.cv_logreg_oof(rng.normal(size=(n, 3)), y, np.ones(n), np.arange(n))
    assert abs(L.w_auroc(noise, y > 0, np.ones(n)) - 0.5) < 0.1


def test_pair_scoring_and_placebo():
    a_ids, b_ids = [1, 2, 3, 9, 7], [1, 2, 3, 4, 5, 9, 7]      # B inserts tokens 4,5 (a negation); common prefix and suffix
    assert L.divergent_span(a_ids, b_ids) == (3, 3, 5)
    a_lp = [-1.0, -1.0, -1.0, -0.2, -0.1]; b_lp = [-1.0, -1.0, -1.0, -3.0, -2.0, -0.9, -0.1]
    s = L.pair_scores(a_ids, a_lp, b_ids, b_lp)
    assert abs(s["span_sum"] - (-5.0 - 0.0)) < 1e-9          # span A empty (0), span B = -3-2
    assert s["span_len_a"] == 0 and s["span_len_b"] == 2
    assert s["full_sum"] < s["span_sum"] + 1.0               # suffix terms differ: full-sum is contaminated by them
    # length confound: the longer sentence is always less likely under full-sum; the placebo exposes it
    rng = np.random.default_rng(6); placebo = rng.normal(-1.5, 0.5, 200); true = rng.normal(-1.7, 0.5, 100)
    pc = L.placebo_contrast(true, placebo); assert pc["share_true_beyond_placebo_p95"] < 0.2          # not distinguishable from the surface effect
    true2 = rng.normal(-6, 0.5, 100); assert L.placebo_contrast(true2, placebo)["share_true_beyond_placebo_p95"] > 0.95
    assert L.contraction_toggle("I do not take the bus.") == "I don't take the bus."
    assert L.contraction_toggle("I'm happy.") is None and L.drop_final_period("Hi.") == "Hi"


def _make_fixture(d):
    """Synthetic units + generations. Model 'inf' samples negated with prob .65 on source-negated units and .03 otherwise (informative);
    model 'unf' samples negated with prob .12 regardless of the source (uninformative). Keywords are random words (lexical baseline ~ chance)."""
    import json, pathlib, subprocess
    import pandas as pd
    d = pathlib.Path(d); rng = np.random.default_rng(11); vocab = [f"w{i}" for i in range(60)]; rows = []
    for m in range(420):
        neg = rng.random() < (0.3 if m < 210 else 0.08); sample = "enriched" if m < 210 else "random"; w = 1.0 if m < 210 else 4.0
        chans = [("pos_cap4", "cap4")] + [(f"human_P{j}", "human") for j in range(3)]
        for ch, ds in chans:
            kw = " ".join(rng.choice(vocab, 3, replace=False)) + (" not" if rng.random() < 0.08 else "")
            rows.append(dict(item_id=f"m{m:03d}", fam=f"f{m}", channel=ch, dataset=ds, kw=kw, neg=neg, polite=False, nonstmt=False, lost_act=0.0, w=w, sample=sample,
                             input=f"Keywords: {kw}", kw_neg=" not" in kw, kw_pol=False, kw_act=False, nocue_neg=" not" not in kw, nocue_pol=True, nocue_act=True))
    U = pd.DataFrame(rows); U.to_csv(d / "units.csv", index=False)
    inputs = sorted(set(U.input) | {"Keywords: N/A", "Keywords: "}); neg_of = dict(zip(U.input, U.neg))
    for key, (p_if_neg, p_else) in (("inf", (0.65, 0.03)), ("unf", (0.12, 0.12))):
        (d / "runs" / key).mkdir(parents=True, exist_ok=True)
        with open(d / "runs" / key / "gens.jsonl", "w") as f:
            for inp in inputs:
                p = (p_if_neg if neg_of.get(inp, False) else p_else)
                for k in [-1] + list(range(16)):
                    isneg = (rng.random() < (0.1 if (k < 0 and neg_of.get(inp, False)) else 0.0 if k < 0 else p))
                    text = ("I do not want it." if isneg else "I want it.") + (" Now." if rng.random() < 0.2 else "")
                    top = [[["a", -0.1 - 0.3 * (neg_of.get(inp, False) and key == "inf")], ["b", -2.5]] + [["c%d" % i, -6.0 - i] for i in range(18)]] * 3 if k < 0 else None
                    f.write(json.dumps(dict(input=inp, k=k, text=text, finish="stop", toks=["I", "x", "."], lp=[-0.1, -0.2, -0.1], top=top)) + "\n")


def test_analyze_end_to_end():
    import tempfile, subprocess, pathlib, json
    import pandas as pd
    root = pathlib.Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as td:
        _make_fixture(td)
        r = subprocess.run([sys.executable, str(root / "src/frontier_knows_not_says_analyze.py"), "inf:model-inf", "unf:model-unf", "--fixture", td, "--boot", "300"],
                           capture_output=True, text=True, cwd=str(root)); assert r.returncode == 0, r.stderr[-3000:]
        out = pathlib.Path(td) / "out"
        for f in ("r1.csv", "r2.csv", "pol.csv", "rel.csv", "pooled.csv", "holm.csv", "summary.json", "pareto.csv", "sens.csv"): assert (out / f).exists(), f
        r2 = pd.read_csv(out / "r2.csv"); r1 = pd.read_csv(out / "r1.csv"); pol = pd.read_csv(out / "pol.csv"); holm = pd.read_csv(out / "holm.csv")
        sh = lambda m, ds: r2[(r2.model == m) & (r2.dataset == ds) & (r2.score == "sampled_share(K=16)")].iloc[0]
        assert sh("model-inf", "cap4").auroc > 0.8 and sh("model-inf", "cap4").lo > 0.7
        assert abs(sh("model-unf", "cap4").auroc - 0.5) < 0.15 and sh("model-unf", "cap4").lo < 0.55
        assert 0 <= sh("model-inf", "cap4").tied0_all <= 1 and "EXPLORATORY" in sh("model-inf", "human").status
        lex = r2[(r2.model == "model-inf") & (r2.dataset == "cap4") & (r2.score == "lexical_cv_logistic")].iloc[0]; assert lex.auroc < 0.65   # planted: keywords uninformative
        # Holm: 8 tests, adjusted p >= raw, planted informative model rejects R2-a/R3-b, uninformative model does not reject R2-a
        assert len(holm) == 8 and (holm.p_holm >= holm.p_raw - 1e-12).all() and (holm.p_holm <= 1).all()
        a_inf = holm[(holm.model == "model-inf") & holm.test.str.startswith("R2-a")].iloc[0]; assert bool(a_inf["reject_at_0.05"])
        a_unf = holm[(holm.model == "model-unf") & holm.test.str.startswith("R2-a")].iloc[0]; assert not bool(a_unf["reject_at_0.05"])
        # policies: informative sampled-share ask beats matched random-ask and always-commit on the planted fixture; the uninformative one does not
        hp = "sampled share (semantic-entropy analogue) @ 10/100"
        g = lambda m, p: pol[(pol.model == m) & (pol.dataset == "cap4") & (pol.policy == p)].iloc[0]
        assert g("model-inf", hp).cmr_lo > 0 and g("model-inf", hp)["d_cost_priced_c0.03_hi"] < 0 and bool(g("model-inf", hp).recovers_R3)
        assert g("model-unf", hp).cmr_lo < 0.0 < g("model-unf", hp).cmr_hi + 5 and not bool(g("model-unf", hp).recovers_R3)
        rnd = g("model-unf", "random-ask @ 10/100 (expectation)"); assert pd.isna(rnd.recovers_R3) and abs(rnd.cmr_lo) < 1e-9   # random ask passes the priced-cost half (asking resolves the cue at a 10% base rate) but never the matched-random half
        assert rnd["d_cost_priced_c0.03_hi"] < 0
        ac = g("model-inf", "always-commit (greedy)"); aa = g("model-inf", "always-ask (every no-cue unit)"); assert aa.reversals_per_1000 == 0 and aa.taps_per_1000 > 100 and ac.taps_per_1000 == 0
        chip = pol[(pol.model == "model-inf") & (pol.dataset == "cap4") & pol.policy.str.startswith("cue chip")].iloc[0]
        assert chip.reversals_per_1000 <= ac.reversals_per_1000 * 0.02 + 1e-9 and chip.recall_of_reversals > 0.97       # honour residual 1-0.99 applied to recall too
        assert (pol.policy.str.startswith("guard G1 (NOT APPLICABLE")).any()
        refit = pol[pol.policy.str.startswith("Platt-calibrated") & (pol.model == "model-inf") & (pol.dataset == "cap4")]; assert set(refit.w_spur.round(4)) == {1.0, 0.125, round(1 / 36, 4)}
        assert (r1.model == "model-inf").any() and set(r1.r1_class.dropna()) <= {"calibrated", "inconclusive", "overconfident (default too strong)", "underconfident (default too weak)"}
        assert json.load(open(out / "summary.json"))["boot"] == 300


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
