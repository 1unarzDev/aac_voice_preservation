"""Column-width redraw of r2c/fig_politeness_ratchet for the SE4All paper (same numbers, larger type).

Reads analysis/r2c/politeness_direction_by_model.csv and primary.json (P2 addition/removal arms;
10,000 recorded-cluster resamples, seed 20261031). Writes paper/figs/r2c/fig_ratchet_col.{pdf,png}.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
pm = pd.read_csv(ROOT / "analysis/r2c/politeness_direction_by_model.csv")
p2 = json.load(open(ROOT / "analysis/r2c/primary.json"))["primaries"]["P2"]
rows = [("Pooled", {"plain": p2["addition"], "polite": p2["removal"]})]
for m, lab in [("gemma3-4b", "Gemma-3-4B"), ("gpt-6.1-terra", "gpt-6.1-terra"),
               ("llama3.1-8b", "Llama-3.1-8B"), ("qwen2.5-7b", "Qwen2.5-7B")]:
    d = {cv: pm[(pm.model == m) & (pm.cv == cv)].iloc[0].to_dict() for cv in ["plain", "polite"]}
    rows.append((lab, d))
ADD, REM = "#d9531e", "#2166ac"
plt.rcParams.update({"font.size": 7.5, "font.family": "DejaVu Sans", "axes.linewidth": 0.6})
fig, ax = plt.subplots(figsize=(3.45, 1.95))
for i, (lab, d) in enumerate(rows):
    y = len(rows) - 1 - i
    for cv, col, dy, mk in [("plain", ADD, 0.16, "D"), ("polite", REM, -0.16, "o")]:
        r = d[cv]
        ax.plot([100 * r["ci_low"], 100 * r["ci_high"]], [y + dy] * 2, color=col, lw=1.2)
        ax.plot(100 * r["estimate"], y + dy, mk, color=col, ms=3.8, mec="white", mew=0.4)
        ax.text(41.5, y + dy, f"{int(r['sum'])}/{int(r['n'])}", color=col, va="center", fontsize=7.5)
ax.axhline(len(rows) - 1.5, color="#bbb", lw=0.5)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
ax.get_yticklabels()[-1].set_fontweight("bold")
ax.set_xlim(-0.8, 40); ax.set_xticks([0, 10, 20, 30, 40]); ax.set_xticklabels(["0", "10", "20", "30", "40%"])
ax.set_xlabel("share of full-input politeness targets")
ax.grid(axis="x", color="#e5e5e5", lw=0.5); ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.tick_params(length=2, width=0.5)
h1, = ax.plot([], [], "D", color=ADD, ms=3.8, label="marker added to plain source")
h2, = ax.plot([], [], "o", color=REM, ms=3.8, label="marker removed from polite source")
ax.legend(handles=[h1, h2], loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=1, frameon=False,
          handletextpad=0.3, fontsize=7.5, borderaxespad=0.1)
fig.tight_layout(pad=0.2)
for ext in ["pdf", "png"]:
    fig.savefig(ROOT / f"paper/figs/r2c/fig_ratchet_col.{ext}", dpi=600, bbox_inches="tight", pad_inches=0.02)
print("ok")
