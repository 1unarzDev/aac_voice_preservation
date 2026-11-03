"""value_of_cue round 3 figure: A frontier (all policies, CI bands), B q sensitivity, C per-writer, D taps per error averted. Reads analysis/frontier/value_of_cue/round3/*. PROVISIONAL labels."""
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np, pandas as pd
from pathlib import Path
O = Path(__file__).resolve().parents[1] / "analysis/frontier/value_of_cue/round3"; c = json.load(open(O / "curves_r3.json")); b0 = c["b0"]
CB = {"P-K": "#1b6ca8", "P-O": "#d4a017", "P-I": "#7b3fa0", "B5": "#6b6b6b", "B1": "#c0504d", "Oracle": "#2e8b57", "B6-sup": "#2a9d8f", "B6": "#8fc9c2"}
NM = {"P-K": "keyword-only policy (P-K, strict S1)", "P-O": "P-O: + labelled committed output", "P-I": "P-I: + model internals", "B5": "B5 best fixed prompt (prior)", "B1": "B1 random ask",
      "Oracle": "oracle (upper bound)", "B6-sup": "B6-sup: entropy features, learned", "B6": "B6 entropy gate (inspired-by)"}
fig, axs = plt.subplots(2, 2, figsize=(13, 9)); ax = axs[0, 0]
for k in ("Oracle", "P-I", "P-O", "B6-sup", "P-K", "B5", "B1"):
    t = np.array(c["curves"][k]["taps"]); g = np.array(c["curves"][k]["averted"]); o = np.argsort(t); t, g = t[o], np.maximum.accumulate(g[o]); m = t <= 600
    ax.plot(t[m], 100 * g[m] / b0, color=CB[k], label=NM[k], ls="--" if k == "Oracle" else "-", lw=2 if k in ("P-K", "P-I", "B5") else 1.4)
for k in ("P-K", "P-I", "B5"):
    bd = c["curves"]["bands"][k]; tb = np.array(bd["taps"]); mb = tb <= 600; ax.fill_between(tb[mb], 100 * np.array(bd["lo"])[mb], 100 * np.array(bd["hi"])[mb], color=CB[k], alpha=.16, lw=0)
ax.axvline(100, color="k", lw=.5, alpha=.4); ax.set_xlabel("taps per 1,000 messages (at most one prompt per message)"); ax.set_ylabel("SLP-weighted silent errors averted (% of status quo)")
ax.set_title("A. Frontier: ask-or-assume policies vs baselines (shaded: 95% CI)", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=7.5, loc="upper left")
ax = axs[0, 1]; q = pd.read_csv(O / "r3_qsweep.csv")
for k in ("Oracle", "P-I", "P-O", "P-K", "B5", "B1"):
    d = q[q.contrast == k]; ax.plot(d.q, 100 * d.rel, "o-", color=CB[k], lw=2 if k in ("P-K", "P-I", "B5") else 1.4, ms=3.5, label=k, ls="--" if k == "Oracle" else "-")
    if k in ("P-K", "P-I", "B5"): ax.fill_between(d.q, 100 * d.lo, 100 * d.hi, color=CB[k], alpha=.14, lw=0)
ax.set_xlabel("assumed pick-right probability q for SHOW-TWO"); ax.set_ylabel("% averted at 100 taps / 1,000"); ax.set_title("B. Every number is conditional on q (not yet measured)", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=8, ncol=2)
ax = axs[1, 0]; pw = pd.read_csv(O / "r3_per_writer.csv"); pi = pw[pw.policy == "P-I"].sort_values("averted").reset_index(drop=True); pk = pw[pw.policy == "P-K"].set_index("writer").loc[pi.writer].reset_index(); y = np.arange(len(pi))
ax.hlines(y, pi.B5_same_prompt_rate, pi.averted, color="#bbb", lw=1); ax.scatter(pi.B5_same_prompt_rate, y, color=CB["B5"], s=22, label="B5 at the same prompt rate", zorder=3)
ax.scatter(pk.averted, y, color=CB["P-K"], s=22, marker="s", label="P-K", zorder=3); ax.scatter(pi.averted, y, color=CB["P-I"], s=26, label="P-I", zorder=3)
ax.set_yticks(y); ax.set_yticklabels(pi.writer, fontsize=7); ax.set_xlabel("weighted errors averted per 1,000 of that writer's messages (pooled T = 100)"); ax.set_title("C. Per-writer: gain is concentrated, P-K beats B5 for 7 of 20", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=8, loc="lower right")
ax = axs[1, 1]; S = pd.read_csv(O / "r3_frontier.csv"); S = S[(S.budget == 100) & S.policy.isin(["Oracle", "P-I", "B6-sup", "P-O", "P-K", "B5", "B6", "B1"])].sort_values("taps_per_error_averted", ascending=False); y = np.arange(len(S))
ax.barh(y, S.taps_per_error_averted, color=[CB[k] for k in S.policy]); ax.set_yticks(y); ax.set_yticklabels(S.policy)
for i, r in enumerate(S.itertuples()): ax.text(r.taps_per_error_averted + .2, i, f"{r.taps_per_error_averted:.1f}  ({r.weighted_averted_per1000:.0f} weighted / 1,000 averted)", va="center", fontsize=8)
ax.set_xlim(0, 24); ax.set_xlabel("taps spent per silent error averted at 100 taps / 1,000 (lower is better)"); ax.set_title("D. Cost in AAC terms (q = 0.9)", fontsize=10, loc="left")
for a in axs.ravel(): a.spines[["top", "right"]].set_visible(False)
fig.text(.01, .004, "PROVISIONAL: detector source labels, machine-arbitrated output labels, simulated q = 0.9 and rho; 20 writers, 600 messages; primary scope = polarity, speech act, politeness-lost.", fontsize=7.5, color="#555")
fig.tight_layout(rect=(0, .02, 1, 1)); fig.savefig(O / "fig_round3.png", dpi=170); print("ok")
