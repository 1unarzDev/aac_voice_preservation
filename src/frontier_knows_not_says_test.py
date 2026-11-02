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


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
