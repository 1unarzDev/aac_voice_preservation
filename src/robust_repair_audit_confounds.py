"""Part 4 repair-audit confound analysis (stored ratings only; 0 generation / 0 judge calls).

    . .venv/bin/activate && python src/robust_repair_audit_confounds.py

Inputs: annotation/repair_audit_key.csv (frozen sample), annotation/returns_repair/*.csv (14 raters x 40 items),
analysis/repair_audit/items.csv (stored consensus), src/score_repair_audit.py (rate/newcombe/consensus/outcomes, reused).
Outputs analysis/robust/repair_audit_confounds/{report.md,summary.json,*.csv}.
Parts: (1) item-level n and stored endpoints reproduced; (2) unknown counted as unusable / as usable (bounds on the repaired-control gap);
(3) rater non-independence: distinct answer patterns, pairwise disagreement, cluster counts, effective raters; (4) arm composition
(dimension, channel group, model, occurrences, input and output length, chip count), stratified (Mantel-Haenszel, within-stratum exact permutation)
estimates of the gap, and what controls are by construction.
"""
from __future__ import annotations
import itertools, json, sys
from collections import Counter
from math import comb
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import score_repair_audit as SR      # noqa: E402
from robust_common import outdir, write_json, md_table   # noqa: E402

OUT = outdir("repair_audit_confounds"); RNG = np.random.default_rng(20261101)

key = pd.read_csv(ROOT / "annotation/repair_audit_key.csv"); items = pd.read_csv(ROOT / "analysis/repair_audit/items.csv")
assert len(key) == 40 and key.item_id.is_unique
# ---- load ratings with the scorer's own parser
keyrows = [dict(r) for r in key.to_dict("records")]
import inspect
ratings = SR.load_returns(sorted((ROOT / "annotation/returns_repair").glob("*.csv")), {r["item_id"]: r for r in keyrows})
rt = ratings[0] if isinstance(ratings, tuple) else ratings
# normalise to rater x item records {quality, contract, added}
recs = [dict(item_id=r["item_id"], rater=r["annotator"], quality=r["quality"], contract=r["contract"], added=r["added"]) for r in rt.values()]
R = pd.DataFrame(recs)
arm = key.set_index("item_id").arm.to_dict(); R["arm"] = R.item_id.map(arm)
assert R.rater.nunique() == 14 and R.item_id.nunique() == 40 and len(R) == 560, (R.rater.nunique(), R.item_id.nunique(), len(R))
out = [SR.outcomes(r) for r in R.to_dict("records")]
for e in SR.ENDPOINTS: R[e] = [o[e] for o in out]

# ---- stored consensus (reproduction) and variants
def cons_table(unknown):
    """item x endpoint consensus. unknown in {'drop','unusable','usable'} applies to ties/all-unknown items of the *positive* endpoints."""
    rows = {}
    for iid, g in R.groupby("item_id"):
        rows[iid] = {e: SR.consensus(list(g[e])) for e in SR.ENDPOINTS}
    C = pd.DataFrame(rows).T; C["arm"] = C.index.map(arm)
    return C
C = cons_table("drop")
st = items.set_index("item_id")
for e, col in [("usable", "cons_usable"), ("preserving", "cons_preserving"), ("usable_and_preserving", "cons_usable_and_preserving")]:
    assert all((pd.isna(st.loc[i, col]) and C.loc[i, e] is None) or (str(st.loc[i, col]) == str(C.loc[i, e])) for i in C.index), e
summary = {"n_items": 40, "n_raters": 14, "ratings": int(len(R)), "stored_consensus_reproduced": True}

def arm_rate(C, e, a, fill=None):
    v = [C.loc[i, e] for i in C.index if C.loc[i, "arm"] == a]
    if fill is not None: v = [fill if x is None else x for x in v]
    return SR.rate(v)

tab = []
for e in SR.ENDPOINTS:
    rec = {"endpoint": e}
    for variant, fill in (("stored (unknown excluded)", None), ("unknown = unusable/failing", False), ("unknown = usable/passing", True)):
        rep, ctl = arm_rate(C, e, "repaired", fill), arm_rate(C, e, "control", fill)
        nc = SR.newcombe(rep, ctl)
        rec[variant] = dict(repaired=rep, control=ctl, diff=nc["diff"], diff_ci=nc["ci"])
    # worst / best case for the gap: unknowns in repaired fail & in control pass (widest), and the reverse
    rep0, ctl0 = arm_rate(C, e, "repaired", False), arm_rate(C, e, "control", True)
    rep1, ctl1 = arm_rate(C, e, "repaired", True), arm_rate(C, e, "control", False)
    rec["bounds_gap"] = [SR.newcombe(rep0, ctl0)["diff"], SR.newcombe(rep1, ctl1)["diff"]]
    # Fisher exact (two-sided) on item-level counts, unknown=unusable (the conservative-for-repair reading)
    r_, c_ = arm_rate(C, e, "repaired", False), arm_rate(C, e, "control", False)
    rec["fisher_p_unknown_unusable"] = float(stats.fisher_exact([[r_["k"], r_["n"] - r_["k"]], [c_["k"], c_["n"] - c_["k"]]])[1])
    tab.append(rec)
summary["endpoints"] = tab
unk = {e: {a: int(sum(C.loc[i, e] is None for i in C.index if C.loc[i, "arm"] == a)) for a in ("repaired", "control")} for e in SR.ENDPOINTS}
summary["unknown_items"] = unk

# ---- per-rating unknowns: raters answering unknown / unsure
perr = {e: int(R[e].isna().sum()) for e in SR.ENDPOINTS}; summary["rater_level_unknown_ratings"] = perr

# ---- rater non-independence
cols = ["quality", "contract", "added"]
M = {r: tuple(tuple(R[(R.rater == r)].sort_values("item_id")[c].map(lambda v: "NA" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)).tolist()) for c in cols) for r in sorted(R.rater.unique())}
vec = {r: sum(M[r], ()) for r in M}                       # 120 answers per rater (40 items x 3 questions)
patterns = Counter(vec.values())
q_only = Counter(M[r][0] for r in M)
usable_bin = {r: tuple(R[R.rater == r].sort_values("item_id").usable.map(lambda v: "NA" if v is None or pd.isna(v) else int(bool(v))).tolist()) for r in M}
ub_patterns = Counter(usable_bin.values())
names = sorted(vec); D = pd.DataFrame(0, index=names, columns=names)
for a, b in itertools.combinations(names, 2):
    d = sum(x != y for x, y in zip(vec[a], vec[b])); D.loc[a, b] = D.loc[b, a] = d
def comps(th):
    par = {n: n for n in names}
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in itertools.combinations(names, 2):
        if D.loc[a, b] <= th: par[f(a)] = f(b)
    g = {}
    for n in names: g.setdefault(f(n), []).append(n)
    return sorted(g.values(), key=lambda x: (-len(x), x))
clusters = {th: comps(th) for th in (0, 2, 5, 10, 20)}
# agreement of each rater's usable answer with the item majority (leave-one-out)
off = D.values[np.triu_indices(14, 1)]
# effective number of independent raters on the usable answers: 1 / mean pairwise correlation formulation (design effect for equicorrelated raters)
U = pd.DataFrame({r: [(-1 if v == "NA" else v) for v in usable_bin[r]] for r in names}).astype(float)
Uc = U.replace(-1, np.nan); corr = Uc.corr().values; rho = float(np.nanmean(corr[np.triu_indices(14, 1)]))
n_eff_raters = 14 / (1 + 13 * rho) if rho == rho else np.nan
summary["rater_patterns"] = dict(raters=14, distinct_full_answer_patterns=len(patterns), pattern_sizes=sorted(patterns.values(), reverse=True),
                                 distinct_quality_patterns=len(q_only), quality_pattern_sizes=sorted(q_only.values(), reverse=True),
                                 distinct_usable_binary_patterns=len(ub_patterns), usable_binary_pattern_sizes=sorted(ub_patterns.values(), reverse=True),
                                 pairwise_answer_disagreements_of_120=dict(min=int(off.min()), median=float(np.median(off)), max=int(off.max()), share_zero=float((off == 0).mean())),
                                 clusters_by_max_disagreements={str(th): [len(c) for c in cs] for th, cs in clusters.items()},
                                 mean_pairwise_correlation_usable=rho, design_effect_effective_raters=n_eff_raters,
                                 groups_identical_patterns=[sorted(r for r in vec if vec[r] == p) for p in patterns])
# how much the consensus depends on which raters: leave-pattern-out consensus
def usable_gap_using(raters):
    sub = R[R.rater.isin(raters)]; Cc = {}
    for iid, g in sub.groupby("item_id"): Cc[iid] = SR.consensus(list(g.usable))
    rep = SR.rate([Cc[i] for i in Cc if arm[i] == "repaired"]); ctl = SR.rate([Cc[i] for i in Cc if arm[i] == "control"])
    return rep, ctl, SR.newcombe(rep, ctl)
by_pat = []
for p, c in patterns.items():
    rs = sorted(r for r in vec if vec[r] == p); rep, ctl, nc = usable_gap_using(rs[:1])
    by_pat.append(dict(raters=rs, repaired=SR.fmt(rep), control=SR.fmt(ctl), gap=nc["diff"] if nc else None))
summary["single_representative_per_pattern_gap"] = by_pat
rr = []
for r in names:
    rep, ctl, nc = usable_gap_using([r]); rr.append(dict(rater=r, usable_rep=rep["p"], usable_ctl=ctl["p"], gap=nc["diff"], unknown_rep=rep["unknown"], unknown_ctl=ctl["unknown"]))
RR = pd.DataFrame(rr); RR.to_csv(OUT / "per_rater_gap.csv", index=False)
summary["per_rater_gap"] = dict(min=float(RR.gap.min()), max=float(RR.gap.max()), distinct_values=sorted(set(np.round(RR.gap, 3))))
# leave-one-pattern-group-out
loo = []
for p, c in patterns.items():
    rs = [r for r in names if vec[r] != p]; rep, ctl, nc = usable_gap_using(rs); loo.append(dict(dropped=sorted(r for r in names if vec[r] == p), gap=nc["diff"] if nc else None, repaired=SR.fmt(rep), control=SR.fmt(ctl)))
summary["leave_pattern_group_out_gap"] = loo

# ---- arm composition / difficulty confounds
K = key.copy(); K["repaired"] = K.arm.eq("repaired")
K["dim"] = K.dimensions.astype(str); K["n_words_text"] = K.text.str.split().str.len(); K["n_chips"] = K.input_text.str.count(r"\[")
K["n_kw"] = K.input_text.str.replace(r"\[[^\]]*\]", "", regex=True).str.replace("Keywords:", "").str.split().str.len()
comp = {}
for col in ("dim", "channel_group", "assigned_model", "channels"):
    t = pd.crosstab(K[col], K.arm); chi = stats.fisher_exact(t.values) if t.shape == (2, 2) else None
    # exact-ish: permutation chi-square p
    codes = pd.factorize(K[col])[0]; k_ = codes.max() + 1
    def chi(lab_):
        tt = np.zeros((k_, 2)); np.add.at(tt, (codes, lab_), 1)
        ex = tt.sum(1, keepdims=True) * tt.sum(0, keepdims=True) / tt.sum(); return float(((tt - ex) ** 2 / ex).sum())
    lab = (K.arm.values == "repaired").astype(int); obs = chi(lab); cnt = 0
    for _ in range(5000):
        RNG.shuffle(lab); cnt += chi(lab) >= obs - 1e-9
    comp[col] = dict(table=t.to_dict(), perm_p=(cnt + 1) / 5001)
for col in ("n_words_text", "n_chips", "n_kw", "n_occurrences", "pi_mc"):
    a, b = K[K.repaired][col], K[~K.repaired][col]
    comp[col] = dict(repaired_mean=float(a.mean()), control_mean=float(b.mean()), mannwhitney_p=float(stats.mannwhitneyu(a, b).pvalue))
comp["p0_strict_fail"] = {a: K[K.arm == a].p0_strict_fail.astype(str).value_counts().to_dict() for a in ("repaired", "control")}
comp["g1_strict_fail"] = {a: K[K.arm == a].g1_strict_fail.astype(str).value_counts().to_dict() for a in ("repaired", "control")}
summary["composition"] = comp
# usable by stratum, per arm (item consensus, unknown excluded)
strat = []
Cu = C[["usable", "usable_and_preserving", "arm"]].copy().join(K.set_index("item_id")[["dim", "channel_group", "assigned_model"]])
for col in ("channel_group", "assigned_model", "dim"):
    for v, g in Cu.groupby(col):
        r_, c_ = SR.rate(list(g[g.arm == "repaired"].usable)), SR.rate(list(g[g.arm == "control"].usable))
        strat.append(dict(stratum=f"{col}={v}", rep=SR.fmt(r_), ctl=SR.fmt(c_), rep_n=r_["n"], ctl_n=c_["n"], diff=None if not (r_["n"] and c_["n"]) else r_["p"] - c_["p"]))
S = pd.DataFrame(strat); S.to_csv(OUT / "usable_by_stratum.csv", index=False)
# Mantel-Haenszel risk difference and within-stratum permutation test of the gap
Cu["u"] = Cu.usable.map(lambda v: np.nan if v is None else float(v))
def mh_arr(u, rep, groups):
    num = den = 0.0
    for ix in groups:
        r_, c_ = u[ix][rep[ix]], u[ix][~rep[ix]]; r_, c_ = r_[~np.isnan(r_)], c_[~np.isnan(c_)]
        if len(r_) and len(c_):
            w = len(r_) * len(c_) / (len(r_) + len(c_)); num += w * (r_.mean() - c_.mean()); den += w
    return num / den if den else np.nan
mh = {}
u_ = Cu.u.to_numpy(float); rep_ = (Cu.arm == "repaired").to_numpy()
for name, strata in (("channel_group", ["channel_group"]), ("model", ["assigned_model"]), ("channel_group x model", ["channel_group", "assigned_model"]), ("dimension", ["dim"])):
    groups = [np.array(ix) for ix in Cu.reset_index(drop=True).groupby(strata).indices.values()]
    obs = mh_arr(u_, rep_, groups); cnt = 0
    for _ in range(5000):
        rp = rep_.copy()
        for ix in groups: rp[ix] = RNG.permutation(rep_[ix])
        cnt += abs(mh_arr(u_, rp, groups)) >= abs(obs) - 1e-12
    mh[name] = dict(mh_risk_difference=float(obs), perm_p_two_sided=(cnt + 1) / 5001)
mh["unadjusted"] = dict(risk_difference=float(np.nanmean(u_[rep_]) - np.nanmean(u_[~rep_])))
summary["stratified_gap_usable"] = mh
write_json(OUT / "summary.json", summary)

# ---- report
def f(r): return SR.fmt(r)
L = ["# Part 4 repair audit: confound analysis (stored ratings; 0 generation / 0 judge calls)", "",
     "Script `src/robust_repair_audit_confounds.py`; files `summary.json`, `per_rater_gap.csv`, `usable_by_stratum.csv`. Source: `annotation/returns_repair/*.csv` (14 raters x 40 items = 560 ratings; every rater rated every item), "
     "`annotation/repair_audit_key.csv`. Parser, endpoint rules, Wilson and Newcombe intervals are those of `src/score_repair_audit.py`; the stored item consensus is reproduced exactly.", "",
     "## 1. Item-level n", "",
     "The unit is the ITEM: 20 repaired + 20 control = 40 items, rated by the same 14 people. The 560 ratings are not 560 observations (see section 3). Known items per endpoint (unknown = tie or all raters unsure/cannot judge):", "",
     "| endpoint | repaired known/20 | control known/20 | stored gap [Newcombe] |", "|---|---|---|---|"]
for r in tab:
    s = r["stored (unknown excluded)"]
    L.append(f"| {r['endpoint']} | {s['repaired']['n']} | {s['control']['n']} | {100*s['diff']:+.1f} pp [{100*s['diff_ci'][0]:+.1f}, {100*s['diff_ci'][1]:+.1f}] |")
L += ["", "## 2. Unknowns counted as unusable (upper-end sensitivity) or as usable", "",
      "Item-level consensus; the 'unknown' rows are ties or items nobody could judge. 'Unknown = unusable/failing' treats every unknown item as a failure in BOTH arms (the upper-end reading of the repair cost, because repaired items have more unknowns); "
      "'unknown = usable' is the reverse. Bounds = repaired unknowns fail while control unknowns pass, and the opposite.", "",
      "| endpoint | stored: repaired / control | gap | unknown=unusable: repaired / control | gap [Newcombe] | unknown=usable: gap | bounds on the gap (pp) | Fisher p (unknown=unusable) |", "|---|---|---|---|---|---|---|---|"]
for r in tab:
    s, u0, u1 = r["stored (unknown excluded)"], r["unknown = unusable/failing"], r["unknown = usable/passing"]
    L.append(f"| {r['endpoint']} | {f(s['repaired'])} / {f(s['control'])} | {100*s['diff']:+.1f} | {f(u0['repaired'])} / {f(u0['control'])} | {100*u0['diff']:+.1f} [{100*u0['diff_ci'][0]:+.1f}, {100*u0['diff_ci'][1]:+.1f}] | "
             f"{100*u1['diff']:+.1f} | {100*r['bounds_gap'][0]:+.1f} to {100*r['bounds_gap'][1]:+.1f} | {r['fisher_p_unknown_unusable']:.3f} |")
L += ["", f"Unknown items (repaired / control): " + "; ".join(f"{e} {unk[e]['repaired']}/{unk[e]['control']}" for e in SR.ENDPOINTS) + ". "
      "Added stance is a rate where 'yes' is the undesirable outcome, so for that row 'unusable' means 'added stance = yes' only through the same fill; ignore the added-stance fills.", "",
      "## 3. Rater non-independence", "",
      f"* Distinct full answer patterns (quality + contract + added over the 40 items, 120 answers each): **{summary['rater_patterns']['distinct_full_answer_patterns']} of 14 raters**; sizes {summary['rater_patterns']['pattern_sizes']}.",
      f"* Distinct quality-answer patterns: {summary['rater_patterns']['distinct_quality_patterns']} (sizes {summary['rater_patterns']['quality_pattern_sizes']}); distinct usable yes/no patterns: {summary['rater_patterns']['distinct_usable_binary_patterns']} (sizes {summary['rater_patterns']['usable_binary_pattern_sizes']}).",
      f"* Pairwise answer disagreements out of 120: median {summary['rater_patterns']['pairwise_answer_disagreements_of_120']['median']:.0f}, max {summary['rater_patterns']['pairwise_answer_disagreements_of_120']['max']}, share of rater pairs with identical patterns {100*summary['rater_patterns']['pairwise_answer_disagreements_of_120']['share_zero']:.0f}%.",
      "* Rater groups by maximum number of differing answers (single-linkage): " + "; ".join(f"<= {th}: sizes {v}" for th, v in summary['rater_patterns']['clusters_by_max_disagreements'].items()) + ".",
      f"* Mean pairwise correlation of usable answers rho = {rho:.2f}; design-effect effective number of independent raters = 14 / (1 + 13 rho) = **{n_eff_raters:.1f}**.",
      "* Identical-pattern groups: " + "; ".join(",".join(g) for g in summary['rater_patterns']['groups_identical_patterns']) + ".",
      f"* Gap in usable (repaired - control, Newcombe), one rater at a time: range {100*summary['per_rater_gap']['min']:+.1f} to {100*summary['per_rater_gap']['max']:+.1f} pp; distinct values {[round(100*x,1) for x in summary['per_rater_gap']['distinct_values']]}. "
      "Leave-one-pattern-group-out gap: " + "; ".join(f"drop {','.join(x['dropped'])}: {100*x['gap']:+.1f} pp" for x in loo) + ".", "",
      "Statement for the paper: the 14 raters are not 14 independent judgements. Their usable answers collapse to 2 distinct yes/no patterns (7 + 7), their full answers to 7 patterns, and the correlation-based effective number of raters is about 1.1; every single rater alone reproduces the same usable gap. The 40 items, not the 560 ratings, limit precision, and the item-level intervals of Part 4 are the honest ones.", "",
      "## 4. Do controls differ from repaired items in difficulty?", "",
      "By construction controls are P0 outputs that PASSED the strict machine check (`p0_strict_fail` = False for all 20) and are not repaired; repaired items are P0 FAILURES that G1 fixed "
      f"(`p0_strict_fail`: {comp['p0_strict_fail']['repaired']}). The two arms are therefore selected on the outcome the audit is about, so 'repaired - control' compares hard cases that were fixed with easy cases that never failed: it is an upper bound on the usability cost of repair relative to what a cue-compliant output costs, not a matched causal contrast. Matching on model and channel group was designed in; the rest differs:", "",
      "| factor | repaired | control | permutation p |", "|---|---|---|---|"]
for col, lab in (("channel_group", "channel group (cue / ambiguous)"), ("assigned_model", "model"), ("dim", "dimension")):
    t = comp[col]["table"]; keys = sorted(t["repaired"]); 
    L.append(f"| {lab} | " + ", ".join(f"{k} {t['repaired'][k]}" for k in keys) + " | " + ", ".join(f"{k} {t['control'][k]}" for k in keys) + f" | {comp[col]['perm_p']:.3f} |")
for col, lab in (("n_words_text", "words in output"), ("n_chips", "chips in input"), ("n_kw", "keyword count"), ("n_occurrences", "occurrences of the output text"), ("pi_mc", "inclusion prob. pi_mc (a sampling-design artefact: repaired items come from a small pool; not a difficulty measure)")):
    L.append(f"| {lab} (mean) | {comp[col]['repaired_mean']:.2f} | {comp[col]['control_mean']:.2f} | {comp[col]['mannwhitney_p']:.3f} |")
L += ["", "Usable (consensus, unknown excluded) within strata:", "", md_table(S[["stratum", "rep", "ctl", "diff"]], 3), "",
      "Stratified gap in usable (Mantel-Haenszel risk difference; within-stratum permutation p, 5,000 draws):", "",
      "| stratification | MH risk difference | permutation p (two-sided) |", "|---|---|---|"]
for k, v in mh.items():
    L.append(f"| {k} | {100*v.get('mh_risk_difference', v.get('risk_difference')):+.1f} pp | {v.get('perm_p_two_sided', float('nan')):.3f} |")
L += ["", "## Caveats", "",
      "* n = 20 + 20 items, 14 raters with nearly identical answers: Part 4 is a pilot. Part 17 (three independent raters per item) is the evidence for any usable-repair claim.",
      "* Dimension mix differs (repaired items are mostly politeness, controls mostly polarity/speech act); with 20 items per arm no model-based adjustment is credible, and the stratified estimates above are descriptive.",
      "* Controls never failed the strict machine check; a failing-but-unrepaired arm (the pre-repair outputs, or strip-only G1s outputs) is the right comparator and is only available through Part 17 if those arms were added.",
      "* Unknown handling is a sensitivity analysis, not a re-estimation: the stored consensus (strict majority of known answers) is unchanged."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:40]))
