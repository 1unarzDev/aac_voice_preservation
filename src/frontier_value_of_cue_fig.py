import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np
from pathlib import Path
O = Path(__file__).resolve().parents[1] / "analysis/frontier/value_of_cue"; c = json.load(open(O / "stage0_curves.json")); b0 = c["b0"]
fig, ax = plt.subplots(figsize=(6.2, 4)); sty = {"P-K": ("#1b6ca8", "keyword-feature policy (P-K)"), "B5": ("#888888", "B5 prior-only"), "B1": ("#c0504d", "B1 random ask"), "Oracle": ("#2e8b57", "oracle (upper bound)")}
for k, (col, lab) in sty.items():
    t = np.array(c["curves"][k]["taps"]); g = np.array(c["curves"][k]["averted"]); o = np.argsort(t); t, g = t[o], np.maximum.accumulate(g[o]); m = t <= 600
    ax.plot(t[m], 100 * g[m] / b0, color=col, label=lab, ls="--" if k == "Oracle" else "-", lw=2)
ax.set_xlabel("taps per 1,000 messages (one prompt per message at most)"); ax.set_ylabel("SLP-weighted silent errors averted (%)"); ax.legend(frameon=False, fontsize=8); ax.set_title("Value-of-cue pilot: held-out frontier, keyword features only", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(O / "fig_frontier.png", dpi=200)
