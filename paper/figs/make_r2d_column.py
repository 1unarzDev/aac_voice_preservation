"""Column-width redraw of r2d_composition for the SE4All paper (same numbers, larger type).

Reads analysis/r2d/headline.json only: {enc}_{dim}_{model}_damage_minus_repeat and its CI
(10,000 physical-scenario resamples, seed 20261031). Writes paper/figs/r2d/fig_composition_col.{pdf,png}.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
h = json.load(open(ROOT / "analysis/r2d/headline.json"))
MODELS = [("qwen", "Qwen2.5-7B"), ("llama", "Llama-3.1-8B"), ("gemma", "Gemma-3-4B"),
          ("terra", "gpt-6.1-terra"), ("pooled", "4-model pool")]
ENC = [("tell", "[TELL]", "#c0472a", 0.17), ("statement", "[STATEMENT]", "#1f6b96", -0.17)]
PANELS = [("polarity", "Negation protected,\nactor cue added"), ("agent", "Actor protected,\nnegation cue added")]
plt.rcParams.update({"font.size": 7.5, "font.family": "DejaVu Sans", "axes.linewidth": 0.6})
fig, axes = plt.subplots(1, 2, figsize=(3.45, 2.15), sharey=True)
for ax, (dim, title) in zip(axes, PANELS):
    for i, (m, _) in enumerate(MODELS):
        y = len(MODELS) - 1 - i
        for enc, lab, col, dy in ENC:
            k = f"{enc}_{dim}_{m}_damage_minus_repeat"
            v, lo, hi = 100 * h[k], 100 * h[k + "_ci_low"], 100 * h[k + "_ci_high"]
            ax.plot([lo, hi], [y + dy] * 2, color=col, lw=1.1, solid_capstyle="butt")
            ax.plot(v, y + dy, "D" if m == "pooled" else "o", color=col, ms=3.6, mec="white", mew=0.4,
                    label=lab if (i == 0 and dim == "polarity") else None)
    ax.axvline(0, color="#555", lw=0.6, ls=(0, (2, 2)))
    ax.axhline(0.5, color="#bbb", lw=0.5)
    ax.set_xlim(-1, 17.5); ax.set_xticks([0, 5, 10, 15])
    ax.set_title(title, fontsize=7.5, pad=3)
    ax.grid(axis="x", color="#e5e5e5", lw=0.5); ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2, width=0.5)
axes[0].set_yticks(range(len(MODELS))); axes[0].set_yticklabels([n for _, n in MODELS][::-1])
fig.supxlabel("damage minus repeat disagreement (pp)", fontsize=7.5, y=0.0)
fig.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.6, 1.02), handletextpad=0.3,
           columnspacing=1.2, fontsize=7.5)
fig.tight_layout(rect=(0, 0.0, 1, 0.9), w_pad=0.6)
out = ROOT / "paper/figs/r2d"
for ext in ["pdf", "png"]:
    fig.savefig(out / f"fig_composition_col.{ext}", dpi=600, bbox_inches="tight", pad_inches=0.02)
print("wrote", out / "fig_composition_col.pdf")
