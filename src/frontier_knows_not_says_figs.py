"""Figures for knows_not_says round 3, from analysis/frontier/knows_not_says/stage1/*.csv.  usage: python src/frontier_knows_not_says_figs.py [outdir-name]"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parent.parent
arg = sys.argv[1] if len(sys.argv) > 1 else "stage1"
D = Path(arg) if arg.startswith("/") else ROOT / "analysis/frontier/knows_not_says" / arg; F = D / "figs"; F.mkdir(exist_ok=True, parents=True)
r1 = pd.read_csv(D / "r1.csv"); r2 = pd.read_csv(D / "r2.csv"); pol = pd.read_csv(D / "pol.csv"); par = pd.read_csv(D / "pareto.csv"); rel = pd.read_csv(D / "bins.csv")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
models = sorted(r1.model.unique()); C = {"human": "#7a5195", "cap4": "#ef5675"}

# Fig 1: R1 polarity share vs posterior (detector-relative; corrected when available)
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
for a, ds in zip(ax, ("cap4", "human")):
    d = r1[(r1.dataset == ds) & (r1.dimension == "polarity")]
    for i, r in enumerate(d.itertuples()):
        x = i * 3
        a.bar(x, r.posterior, 0.8, color="#999", label="source posterior (detector)" if i == 0 else None); a.errorbar(x, r.posterior, [[r.posterior - r.posterior_lo], [r.posterior_hi - r.posterior]], color="k", lw=1)
        a.bar(x + 1, r.greedy_share, 0.8, color="#4c78a8", label="greedy" if i == 0 else None)
        a.bar(x + 2, r.sampled_share, 0.8, color="#f58518", label="sampled (K=16)" if i == 0 else None); a.errorbar(x + 2, r.sampled_share, [[r.sampled_share - r.sampled_lo], [r.sampled_hi - r.sampled_share]], color="k", lw=1)
        a.text(x + 1, -0.012, r.model.split("-")[0], ha="center", va="top", fontsize=8)
    a.set_xticks([]); a.set_title(f"E-{ds}" + (" (exploratory)" if ds == "human" else ""))
ax[0].set_ylabel("share of no-cue units, output negated"); ax[0].legend(frameon=False, fontsize=7); fig.tight_layout(); fig.savefig(F / "fig1_r1_shares.png"); plt.close(fig)

# Fig 2: R2 AUROC with CIs
fig, ax = plt.subplots(1, 1, figsize=(6.2, 3.0)); d = r2[r2.dataset == "cap4"]; scores = ["sampled_share(K=16)", "greedy_first_token_entropy", "greedy_mean_token_entropy", "lexical_cv_logistic", "greedy_output_negated"]
w = 0.8 / len(models)
for j, m in enumerate(models):
    for i, sc in enumerate(scores):
        r = d[(d.model == m) & (d.score == sc)]
        if len(r): r = r.iloc[0]; ax.errorbar(i + j * w, r.auroc, [[r.auroc - r.lo], [r.hi - r.auroc]], fmt="o", color=["#4c78a8", "#f58518", "#54a24b"][j % 3], label=m if i == 0 else None)
ax.axhline(0.5, color="#aaa", ls="--", lw=0.8); ax.set_xticks(np.arange(len(scores)) + w / 2); ax.set_xticklabels(["sampled\nshare", "first-tok.\nentropy", "mean-tok.\nentropy", "lexical\n(CV logit)", "greedy\noutput"]); ax.set_ylabel("HT-weighted AUROC, E-cap4"); ax.set_ylim(0.3, 1.0); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(F / "fig2_r2_auroc.png"); plt.close(fig)

# Fig 3: Pareto (reversals vs taps per 1,000 units) E-cap4
fig, ax = plt.subplots(1, len(models), figsize=(3.6 * len(models), 3.0), sharey=True); ax = np.atleast_1d(ax)
lab = {"sampled_share(K=16)": "sampled share", "greedy_first_token_entropy": "first-token entropy", "greedy_mean_token_entropy": "mean-token entropy", "lexical_cv_logistic": "lexical"}
for a, m in zip(ax, models):
    p = par[(par.model == m) & (par.dataset == "cap4")]
    for sc, g in p.groupby("score"): a.plot(g.taps_per_1000, g.reversals_per_1000, label=lab.get(sc, sc), lw=1.3)
    c = pol[(pol.model == m) & (pol.dataset == "cap4") & (pol.policy == "always-commit (greedy)")].iloc[0]; aa = pol[(pol.model == m) & (pol.dataset == "cap4") & (pol.policy.str.startswith("always-ask"))].iloc[0]
    a.plot([0, aa.taps_per_1000], [c.reversals_per_1000, 0], "k--", lw=0.9, label="random-ask (expected)"); a.scatter([0, aa.taps_per_1000], [c.reversals_per_1000, 0], c="k", s=14, zorder=3)
    a.set_title(m); a.set_xlabel("taps per 1,000 units (simulated ask)")
ax[0].set_ylabel("silent polarity reversals per 1,000"); ax[0].legend(frameon=False, fontsize=7); fig.tight_layout(); fig.savefig(F / "fig3_pareto.png"); plt.close(fig)

# Fig 4: reliability bins
fig, ax = plt.subplots(1, 2, figsize=(6.4, 3.0), sharey=True, sharex=True)
for a, ds in zip(ax, ("cap4", "human")):
    for m in models:
        b = rel[(rel.model == m) & (rel.dataset == ds)]; a.plot(b.mean_p, b.obs_rate, "o-", label=m, ms=4)
    a.plot([0, 1], [0, 1], color="#aaa", ls="--"); a.set_title(f"E-{ds}"); a.set_xlabel("mean sampled share in bin")
ax[0].set_ylabel("observed source-negated rate (HT)"); ax[0].legend(frameon=False); fig.tight_layout(); fig.savefig(F / "fig4_reliability.png"); plt.close(fig)
print("figs ->", F)
