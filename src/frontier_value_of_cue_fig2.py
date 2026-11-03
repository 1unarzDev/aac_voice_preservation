"""value_of_cue round 2 figure: (A) primary-scope frontier with 95% CI bands to 600 taps, (B) q sweep at T=100, (C) signals (if computed). Reads analysis/frontier/value_of_cue/round2/*."""
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np, pandas as pd
from pathlib import Path
O = Path(__file__).resolve().parents[1] / "analysis/frontier/value_of_cue/round2"; c = json.load(open(O / "curves_prim.json")); b0 = c["b0"]
CB = {"P-K": "#1b6ca8", "B5": "#6b6b6b", "B1": "#c0504d", "Oracle": "#2e8b57", "P-K ASK-only": "#e08a1e", "P-I": "#7b3fa0", "P-X": "#b5651d", "B6": "#2a9d8f", "P-ALL": "#444444", "P-O": "#d4a017"}
sig = (O / "signals_frontier.csv").exists(); fig, axs = plt.subplots(1, 3 if sig else 2, figsize=(14.5 if sig else 10, 4.1))
ax = axs[0]
for k, lab in (("P-K", "keyword policy (P-K, no lexicon flags)"), ("B5", "B5 prior-only (best fixed prompt)"), ("B1", "B1 random ask"), ("P-K ASK-only", "P-K, ASK-only"), ("Oracle", "oracle (upper bound)")):
    t = np.array(c["curves"][k]["taps"]); g = np.array(c["curves"][k]["averted"]); o = np.argsort(t); t, g = t[o], np.maximum.accumulate(g[o]); m = t <= 600
    ax.plot(t[m], 100 * g[m] / b0, color=CB[k], label=lab, ls="--" if k == "Oracle" else ":" if "ASK" in k else "-", lw=2)
for k in ("P-K", "B5"):
    bd = c["curves"]["bands"][k]; tb = np.array(bd["taps"]); mb = tb <= 600; ax.fill_between(tb[mb], 100 * np.array(bd["lo"])[mb], 100 * np.array(bd["hi"])[mb], color=CB[k], alpha=.18, lw=0)
ax.axvline(100, color="k", lw=.5, alpha=.4); ax.set_xlabel("taps per 1,000 messages (one prompt per message)"); ax.set_ylabel("SLP-weighted silent errors averted (% of status quo)")
ax.set_title("A. Primary-scope frontier (shaded: 95% CI)", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=7.5, loc="center right")
q = pd.read_csv(O / "q_sweep.csv"); q = q[(q.rho == "rho=measured") & (q.budget == 100)]; ax = axs[1]
for k, lab in (("P-K", "P-K"), ("B5", "B5"), ("B1", "B1"), ("P-K ASK-only", "P-K ASK-only")):
    ax.plot(q.q, 100 * q[k], "o-", color=CB[k], label=lab, lw=2)
ax.set_xlabel("assumed pick-right probability q (SHOW-TWO)"); ax.set_ylabel("% of weighted errors averted at 100 taps"); ax.set_title("B. The result is conditional on q", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=8)
if sig:
    S = pd.read_csv(O / "signals_frontier.csv"); S = S[(S.scope == "pooled") & S.policy.isin(["P-K", "P-X", "P-I", "P-ALL", "P-O", "B6", "B5", "B1"])]; ax = axs[2]; bud = sorted(S.budget.unique()); xs = np.arange(len(bud)); pol = ["B1", "B5", "B6", "P-K", "P-X", "P-O", "P-I", "P-ALL"]; wd = .1
    for i, k in enumerate(pol):
        d = S[S.policy == k].set_index("budget").loc[bud]; ax.bar(xs + (i - 3.5) * wd, 100 * d.rel, wd, yerr=[np.clip(100 * (d.rel - d.lo), 0, None), np.clip(100 * (d.hi - d.rel), 0, None)], color=CB.get(k, "#444"), label=k, error_kw=dict(lw=.7))
    ax.set_xticks(xs); ax.set_xticklabels([f"{b}" for b in bud]); ax.set_xlabel("taps per 1,000 messages"); ax.set_ylabel("% averted (pooled local models)"); ax.set_title("C. Signals vs baselines (95% CI)", fontsize=10, loc="left"); ax.legend(frameon=False, fontsize=7, ncol=2)
for a in np.ravel(axs): a.spines[["top", "right"]].set_visible(False)
fig.text(.01, .005, "PROVISIONAL: detector source labels, machine-arbitrated output labels, simulated q and rho; 20 writers, 600 messages.", fontsize=7, color="#555")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(O / "fig_round2.png", dpi=200); print("ok")
