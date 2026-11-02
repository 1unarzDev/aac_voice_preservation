"""Analysis library for frontier knows_not_says (amendments A2-A7, see analysis/frontier/knows_not_says/PLAN.md).

Everything here is pure numpy/pandas and unit-tested on synthetic data (src/frontier_knows_not_says_test.py).
 * Horvitz-Thompson weighted metrics with item (message) bootstrap stratified by sample type      (A2)
 * R1 equivalence classes (calibrated / miscalibrated / inconclusive) on the ratio to the target  (A4)
 * power labels per dataset                                                                       (A5)
 * policies, random-ask matched at the same ask rate, Pareto, cross-fitted thresholds             (A3, A6)
 * divergent-span pair scoring with placebo contrast                                              (A7)
"""
from __future__ import annotations
import math, re
import numpy as np, pandas as pd

SEED = 20261102
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POL = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|which|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)


# ---------------------------------------------------------------------------------------------- weighted metrics
def wmean(x, w):
    w = np.asarray(w, float); return float((np.asarray(x, float) * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def w_auroc(s, y, w):
    """Weighted AUROC = P(score_pos > score_neg) + 0.5 P(tie), weights multiply across the pair."""
    s = np.asarray(s, float); y = np.asarray(y, bool); w = np.asarray(w, float)
    m = w > 0; s, y, w = s[m], y[m], w[m]
    if not y.any() or y.all(): return float("nan")
    uniq, inv = np.unique(s, return_inverse=True)
    wp = np.bincount(inv, weights=w * y, minlength=len(uniq)); wn = np.bincount(inv, weights=w * (~y), minlength=len(uniq))
    below = np.cumsum(wn) - wn
    return float((wp * (below + 0.5 * wn)).sum() / (wp.sum() * wn.sum()))


ECE_EDGES = np.array([0, 1e-9, 0.125, 0.25, 0.5, 1.0 + 1e-9])   # fixed bins on a [0,1] probability: {0}, (0,.125], (.125,.25], (.25,.5], (.5,1]


def w_ece(p, y, w, edges=ECE_EDGES):
    p = np.asarray(p, float); y = np.asarray(y, float); w = np.asarray(w, float)
    b = np.clip(np.digitize(p, edges[1:-1], right=True), 0, len(edges) - 2)
    tot = w.sum(); e = 0.0
    for k in range(len(edges) - 1):
        m = b == k
        if w[m].sum() > 0: e += w[m].sum() / tot * abs(wmean(y[m], w[m]) - wmean(p[m], w[m]))
    return float(e)


def w_brier(p, y, w): return wmean((np.asarray(p, float) - np.asarray(y, float)) ** 2, w)


# ---------------------------------------------------------------------------------------------- item bootstrap
def boot_multiplicity(msg_index: np.ndarray, strata: np.ndarray, B: int, seed: int = SEED) -> np.ndarray:
    """B x n_units integer multiplicities. Resamples MESSAGES (items) with replacement within each stratum; every unit
    (keyword set / sample) of a drawn message is carried with the message. msg_index: unit -> message id (any hashable codes);
    strata: unit -> stratum label (constant within a message)."""
    rng = np.random.default_rng(seed)
    msg_index = np.asarray(msg_index); strata = np.asarray(strata)
    msgs, first = np.unique(msg_index, return_index=True); mstrata = strata[first]
    pos = {m: i for i, m in enumerate(msgs)}; unit_m = np.array([pos[m] for m in msg_index])
    M = np.zeros((B, len(msgs)), dtype=np.int32)
    for s in np.unique(mstrata):
        idx = np.flatnonzero(mstrata == s)
        draws = rng.integers(0, len(idx), size=(B, len(idx)))
        for b in range(B): M[b, idx] += np.bincount(draws[b], minlength=len(idx)).astype(np.int32)
    return M[:, unit_m]


def pct_ci(x, lo=2.5, hi=97.5):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return (float(np.percentile(x, lo)), float(np.percentile(x, hi))) if len(x) else (float("nan"), float("nan"))


def boot_stat(fn, mult, w, *arrs):
    """fn(w_b, *arrs) -> float for each bootstrap weight vector w_b = w * mult[b]."""
    return np.array([fn(w * mult[b], *arrs) for b in range(mult.shape[0])])


# ---------------------------------------------------------------------------------------------- R1 equivalence (A4)
def r1_class(ratio_samples, lo_eq=0.67, hi_eq=1.5, lo_mis=0.5, hi_mis=2.0, level=90):
    """90% CI of the ratio sampled-share/target. calibrated: CI inside [lo_eq,hi_eq]; miscalibrated: CI wholly outside [lo_mis,hi_mis]
    (below or above); else inconclusive."""
    r = np.asarray(ratio_samples, float); r = np.where(np.isfinite(r), r, np.inf)   # share / 0 posterior -> inf
    a = (100 - level) / 2; lo, hi = np.percentile(r, [a, 100 - a])
    if lo >= lo_eq and hi <= hi_eq: c = "calibrated"
    elif hi < lo_mis: c = "overconfident (default too strong)"
    elif lo > hi_mis: c = "underconfident (default too weak)"
    else: c = "inconclusive"
    return c, float(lo), float(hi)


def power_label(n_pos: float, min_confirmatory=40) -> str:
    """A5: positives (source-negated among no-cue units) decide the label."""
    return "confirmatory-eligible" if n_pos >= min_confirmatory else "underpowered: exploratory"


# ---------------------------------------------------------------------------------------------- logistic regression (weighted, L2)
def fit_logreg(X, y, w, l2=1.0, iters=50):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float) / np.mean(w)
    Xb = np.hstack([np.ones((len(X), 1)), X]); beta = np.zeros(Xb.shape[1]); R = np.eye(Xb.shape[1]) * l2; R[0, 0] = 0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xb @ beta)); g = Xb.T @ (w * (p - y)) + R @ beta
        H = Xb.T @ (Xb * (w * p * (1 - p))[:, None]) + R + 1e-8 * np.eye(len(beta))
        step = np.linalg.solve(H, g); beta -= step
        if np.abs(step).max() < 1e-7: break
    return beta


def predict_logreg(beta, X):
    Xb = np.hstack([np.ones((len(X), 1)), np.asarray(X, float)]); return 1 / (1 + np.exp(-Xb @ beta))


def grouped_folds(msg_index, n_folds=5, seed=SEED):
    rng = np.random.default_rng(seed); msgs = np.unique(msg_index); rng.shuffle(msgs)
    fold = {m: i % n_folds for i, m in enumerate(msgs)}; return np.array([fold[m] for m in msg_index])


def cv_logreg_oof(X, y, w, msg_index, n_folds=5, l2=1.0, seed=SEED):
    """Message-grouped cross-fitted out-of-fold probabilities."""
    f = grouped_folds(msg_index, n_folds, seed); oof = np.full(len(y), np.nan)
    for k in range(n_folds):
        tr, te = f != k, f == k
        beta = fit_logreg(X[tr], y[tr], w[tr], l2); oof[te] = predict_logreg(beta, X[te])
    return oof


# ---------------------------------------------------------------------------------------------- policies (A3, A6)
def fit_budget_rule(score, w, budget_rate, tiebreak=True):
    """Return (t, f): ask if score > t; ask a fraction f of units with score == t; chosen so the weighted ask rate = budget_rate."""
    score = np.asarray(score, float); w = np.asarray(w, float); tot = w.sum()
    if budget_rate <= 0: return float(score.max()) + 1.0, 0.0
    if budget_rate >= 1: return float(score.min()) - 1.0, 0.0
    for t in np.unique(score)[::-1]:
        above = w[score > t].sum() / tot; at = w[score == t].sum() / tot
        if above + at >= budget_rate - 1e-12:
            return float(t), float((budget_rate - above) / at) if tiebreak else 1.0
    return float(score.min()) - 1.0, 0.0


def apply_rule(score, rule):
    t, f = rule; score = np.asarray(score, float)
    return np.where(score > t, 1.0, np.where(score == t, f, 0.0))


def crossfit_budget(score, w, msg_index, strata, budget_rate, repeats=20, seed=SEED, domain=None):
    """2-fold message-split, swapped, repeated. Rule fitted on the training half (rate = budget_rate measured over `domain` units
    on the training half), applied to the test half. Returns the expected ask indicator per unit (mean over repeats)."""
    rng = np.random.default_rng(seed); msg_index = np.asarray(msg_index); strata = np.asarray(strata)
    domain = np.ones(len(score), bool) if domain is None else np.asarray(domain, bool)
    msgs, first = np.unique(msg_index, return_index=True); ms = strata[first]
    acc = np.zeros(len(score)); cnt = np.zeros(len(score))
    for _ in range(repeats):
        half = np.zeros(len(msgs), bool)
        for s in np.unique(ms):
            idx = np.flatnonzero(ms == s); rng.shuffle(idx); half[idx[: len(idx) // 2]] = True
        unit_half = dict(zip(msgs, half)); uh = np.array([unit_half[m] for m in msg_index])
        for tr_is in (True, False):
            tr = (uh == tr_is); te = ~tr
            d = tr & domain
            # budget is a share of ALL units: convert to a share of the domain units
            rate_in_dom = min(1.0, budget_rate * w[tr].sum() / w[d].sum())
            rule = fit_budget_rule(score[d], w[d], rate_in_dom)
            a = apply_rule(score[te], rule) * domain[te]
            acc[te] += a; cnt[te] += 1
    return acc / np.maximum(cnt, 1)


def policy_outcomes(a, src, noc, out_neg, w):
    """Weighted per-1000 outcomes for an ask vector a in [0,1] (T2 definitions; asking resolves to the source label).
    reversal: source negated, keywords carry no negation word, output not negated, not asked.
    spurious: source not negated, output negated, not asked.  taps = asks."""
    a = np.asarray(a, float); W = w.sum()
    rev = float((w * (1 - a) * src * noc * (1 - out_neg)).sum() / W * 1000)
    spur = float((w * (1 - a) * (1 - src) * out_neg).sum() / W * 1000)
    taps = float((w * a).sum() / W * 1000)
    return rev, spur, taps


def random_ask_reversals(rev_commit, noc_per1000, taps_per1000):
    """Expected reversals of random-ask over the no-cue units with the same number of taps (analytic, exact expectation)."""
    r = min(1.0, taps_per1000 / noc_per1000) if noc_per1000 > 0 else 0.0
    return rev_commit * (1 - r)


def wcost(rev, spur, taps, w_rev=1.0, w_spur=1.0, c_tap=0.0):
    return w_rev * rev + w_spur * spur + c_tap * taps


# ---------------------------------------------------------------------------------------------- pair scoring with placebo (A7)
def divergent_span(a_ids, b_ids):
    """Strip the common token prefix and suffix. Returns (i0, a_end, b_end): spans are a_ids[i0:a_end], b_ids[i0:b_end]."""
    n = min(len(a_ids), len(b_ids)); i0 = 0
    while i0 < n and a_ids[i0] == b_ids[i0]: i0 += 1
    ja, jb = len(a_ids), len(b_ids)
    while ja > i0 and jb > i0 and a_ids[ja - 1] == b_ids[jb - 1]: ja -= 1; jb -= 1
    return i0, ja, jb


def pair_scores(a_ids, a_lp, b_ids, b_lp):
    """Returns dict with log-odds of B over A under three scorers (positive = B preferred):
    full-sum, length-normalised (mean per token), divergent-span sum (the suffix after the span is conditioned on different
    content, so it is excluded) and divergent-span mean."""
    i0, ja, jb = divergent_span(a_ids, b_ids)
    sa, sb = a_lp[i0:ja], b_lp[i0:jb]
    sp_a, sp_b = float(np.sum(sa)) if len(sa) else 0.0, float(np.sum(sb)) if len(sb) else 0.0
    return {"full_sum": float(np.sum(b_lp) - np.sum(a_lp)), "len_norm": float(np.mean(b_lp) - np.mean(a_lp)),
            "span_sum": sp_b - sp_a, "span_mean": (float(np.mean(sb)) if len(sb) else 0.0) - (float(np.mean(sa)) if len(sa) else 0.0),
            "span_len_a": len(sa), "span_len_b": len(sb)}


def placebo_contrast(true_scores: np.ndarray, placebo_scores: np.ndarray):
    """Share of true-pair |log-odds| exceeding the 95th percentile of the placebo |log-odds| (meaning-neutral edits), plus medians."""
    t = np.abs(np.asarray(true_scores, float)); p = np.abs(np.asarray(placebo_scores, float))
    thr = float(np.percentile(p, 95)) if len(p) else float("nan")
    return {"placebo_abs_p95": thr, "true_abs_median": float(np.median(t)), "placebo_abs_median": float(np.median(p)) if len(p) else float("nan"),
            "share_true_beyond_placebo_p95": float((t > thr).mean()) if len(p) else float("nan")}


CONTRACTIONS = [("do not", "don't"), ("does not", "doesn't"), ("did not", "didn't"), ("cannot", "can't"), ("can not", "can't"), ("will not", "won't"),
                ("is not", "isn't"), ("are not", "aren't"), ("was not", "wasn't"), ("have not", "haven't"), ("would not", "wouldn't"),
                ("should not", "shouldn't"), ("could not", "couldn't"), ("I am not", "I'm not"), ("it is not", "it's not")]


def contraction_toggle(sent: str):
    """Meaning-neutral paraphrase of a negated sentence: expand<->contract the negation. None if no rule applies."""
    for full, short in CONTRACTIONS:
        if full in sent: return sent.replace(full, short, 1)
        if short in sent: return sent.replace(short, full, 1)
    return None


def drop_final_period(sent: str): return sent[:-1] if sent.endswith(".") else None
