"""Round 2 figures (frontier whole_message) from r2_validity_auroc.csv, r2_rates.csv, r2_contrasts.csv, r2_twocand_posthoc60.csv -> analysis/frontier/whole_message/figs/"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; D = ROOT / "analysis/frontier/whole_message"; F = D / "figs"; F.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
# Fig 1: metric validity forest (chip1)
A = pd.read_csv(D / "r2_validity_auroc.csv"); a = A[A.subset == "chip1_all"].set_index("metric")
rows = [("Critical-only, binary (round 1 M0)", "M0_binary", "#999"), ("Critical-only, graded (Qwen14B)", "M0g_Q14", "#999"), ("Critical-only, graded (Nemo12B)", "M0g_Nemo", "#999"),
        ("Word count", "T1_wordcount", "#c9a227"), ("Length ratio", "T2_lenratio", "#c9a227"), ("Lexical F1 to writer", "T3_lexF1", "#c9a227"), ("Novel lemmas", "T4_novelty", "#c9a227"),
        ("Edit dist. to keywords", "T5_edit_kw", "#c9a227"), ("CV logistic (length+lexical)", "T6_cv_logit", "#c9a227"),
        ("Whole-message, gpt-6.1-sol (M1-free)", "M1free_gpt", "#1f5fa8"), ("Whole-message, Qwen14B (independent)", "Q14_SC", "#4c9be8"), ("Whole-message, Nemo12B (independent)", "Nemo_SC", "#4c9be8"),
        ("M1-ref, sees writer sentence (upper bound)", "M1ref_gpt_UPPERBOUND", "#b8d4f0")]
fig, ax = plt.subplots(figsize=(6.6, 3.9))
for i, (lab, m, c) in enumerate(rows[::-1]):
    r = a.loc[m]; ax.errorbar(r.auroc, i, xerr=[[r.auroc - r.lo], [r.hi - r.auroc]], fmt="o", color=c, capsize=2)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8); ax.axvline(.5, color="#bbb", lw=.8, ls=":"); ax.axvline(a.loc["T1_wordcount"].auroc, color="#c9a227", lw=.8, ls="--")
ax.set_xlabel("AUROC, writer rejection (chip1, n=97)"); ax.set_xlim(.3, 1.02)
ax.set_title("Not separable from word count (dashed)", fontsize=9, loc="left"); fig.tight_layout(); fig.savefig(F / "fig1_metric_vs_baselines.png"); plt.close(fig)
# Fig 2: UC per 1,000 by arm, terra and luna, chip1 and bare
R = pd.read_csv(D / "r2_rates.csv"); R = R[(R.metric == "gpt_UC") & R.arm.isin(["A0", "A1", "A2"])]
fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True); cols = {"A0": "#bbbbbb", "A1": "#7aa6d6", "A2": "#1f5fa8"}
for a_, ch in zip(ax, ["chip1", "bare"]):
    for j, gen in enumerate(["gpt-6.1-terra", "gpt-5.6-luna"]):
        for k, arm in enumerate(["A0", "A1", "A2"]):
            r = R[(R.channel == ch) & (R.generator == gen) & (R.arm == arm)].iloc[0]; x = j * 4 + k
            a_.bar(x, 1000 * r.est, .8, color=cols[arm], label=arm if j == 0 else None); a_.errorbar(x, 1000 * r.est, [[1000 * (r.est - r.lo)], [1000 * (r.hi - r.est)]], color="k", lw=.8, capsize=1.5)
    a_.set_xticks([1, 5]); a_.set_xticklabels(["terra", "luna"]); a_.set_title(ch, fontsize=9)
ax[0].set_ylabel("flagged unrequested content per 1,000"); ax[0].legend(frameon=False, fontsize=7); fig.tight_layout(); fig.savefig(F / "fig2_uc_by_arm.png"); plt.close(fig)
# Fig 3: intent match (M1-ref mean score), A0/A1/A2/best-of-2 (terra)
T = pd.read_csv(D / "r2_twocand_posthoc60.csv"); fig, ax = plt.subplots(figsize=(5.4, 2.6))
O = pd.read_csv(D / "r2_outputs.csv"); t = O[(O.generator == "gpt-6.1-terra") & (O.draw == 0)]
labs = []; k = 0
for ch in ["chip1", "bare"]:
    for arm in ["A0", "A1", "A2"]:
        v = t[(t.channel == ch) & (t.arm == arm)].ref_score; ax.bar(k, v.mean(), .8, color=cols[arm]); k += 1
    s = T[(T.channel == ch) & (T.kind == "mean_ref_score")].set_index("arm")
    ax.bar(k, s.loc["A2+A6 best-of-2"].est, .8, color="#e07b39"); ax.errorbar(k, s.loc["A2+A6 best-of-2"].est, [[s.loc["A2+A6 best-of-2"].est - s.loc["A2+A6 best-of-2"].lo], [s.loc["A2+A6 best-of-2"].hi - s.loc["A2+A6 best-of-2"].est]], color="k", lw=.8, capsize=1.5); k += 2
ax.set_xticks([1.5, 7.5]); ax.set_xticklabels(["chip1", "bare"]); ax.set_ylabel("match to writer's sentence\n(M1-ref score, max .6)"); ax.set_ylim(0, .7)
ax.set_title("A0 / A1 / A2 / two candidates (orange): intent match barely moves", fontsize=9, loc="left"); fig.tight_layout(); fig.savefig(F / "fig3_intent_match.png"); plt.close(fig)
print("figs ok")
