"""default_profiles round 2 (R2-9): model-visible silent reversals per 1,000 messages vs asks (taps) per 1,000, with intervention points. Reads CSVs only.
    . .venv/bin/activate && python src/frontier_default_profiles_fig.py"""
from pathlib import Path
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = Path(__file__).resolve().parents[1] / "analysis/frontier/default_profiles"
cur = pd.read_csv(OUT / "policy_curves_r2.csv"); itv = pd.read_csv(OUT / "intervention_same_items.csv")
COL = {"always_commit": "#555555", "random_gated": "#999999", "conf_gated_mean": "#0072B2", "prior_cv_refit": "#D55E00"}
LAB = {"always_commit": "always-commit (G1 sits here: repairs 0)", "random_gated": "random ask (gated)", "conf_gated_mean": "model confidence (probe mean)", "prior_cv_refit": "keyword prior (no model call)"}
TITLE = {"polarity": "Negation dropped", "politeness": "Politeness dropped", "speech_act": "Question/request dropped (provisional labels)"}
fig, axs = plt.subplots(1, 3, figsize=(13, 4.1), sharex=True)
for ax, d in zip(axs, TITLE):
    for pol in COL:
        c = cur[(cur.dimension == d) & (cur.event == "model_visible") & (cur.policy == pol) & (cur.budget <= .40)]
        ax.plot(c.budget * 1000, c.reversals_per_1000, color=COL[pol], lw=2 if pol == "prior_cv_refit" else 1.4, ls="--" if pol == "always_commit" else "-", label=LAB[pol])
        if pol == "prior_cv_refit": ax.fill_between(c.budget * 1000, c.lo, c.hi, color=COL[pol], alpha=.15, lw=0)
    for ch, mk in (("chip", "o"), ("word", "s")):
        for bgt in (100, 200):
            r = itv[(itv.dimension == d) & (itv.event == "model_visible") & (itv.strategy == f"{ch} shown on {bgt // 10}% ranked by prior_cv_refit")]
            if len(r): ax.errorbar(bgt, r.reversals_per_1000.iloc[0], yerr=[[r.reversals_per_1000.iloc[0] - r.lo.iloc[0]], [r.hi.iloc[0] - r.reversals_per_1000.iloc[0]]], fmt=mk, color="#009E73" if ch == "chip" else "#CC79A7", ms=6, capsize=2, label=f"{ch} prompt on prior-ranked {bgt // 10}% of messages" if bgt == 100 else None)
    ax.set_title(TITLE[d], fontsize=10); ax.set_xlabel("asks / taps per 1,000 messages"); ax.set_ylim(bottom=0); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("silent reversals per 1,000 messages\n(model-visible, 4-model mean)")
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(.5, -.04)); fig.tight_layout(rect=(0, .1, 1, 1))
fig.savefig(OUT / "fig_reversals_vs_asks.png", dpi=200, bbox_inches="tight"); fig.savefig(OUT / "fig_reversals_vs_asks.pdf", bbox_inches="tight"); print("ok")
