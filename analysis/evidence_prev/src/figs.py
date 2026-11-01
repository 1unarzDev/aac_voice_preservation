"""Publication-sized matplotlib figures for analyze.py (no interactive backend)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns

CHANNELS = ["bare", "noncrit", "chip1", "chipall", "full"]
DIM_NAMES = {"polarity": "Polarity", "agent": "Agent", "certainty": "Certainty",
             "time_quantity": "Time/quantity", "speech_act": "Speech act", "politeness": "Politeness"}
# Okabe–Ito colors; channel markers provide redundant encoding.
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
MARKERS = dict(zip(CHANNELS, ["o", "s", "^", "D", "*"]))


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def empty(ax, message="No observed labels"):
    ax.text(.5, .5, message, transform=ax.transAxes, ha="center", va="center", color="0.4")


def make_figures(tables: dict[str, pd.DataFrame], out: Path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.titlesize": 8,
                         "axes.labelsize": 7, "xtick.labelsize": 6, "ytick.labelsize": 6,
                         "legend.fontsize": 6, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.facecolor": "white"})
    fidelity = tables["critical_match"]
    prompts = sorted(fidelity.prompt_id.unique())
    prompt = "P0" if "P0" in prompts else next((p for p in prompts if p != "P1"), prompts[0])
    models = sorted(fidelity.model.unique())
    dims = list(d for d in DIM_NAMES if d in set(fidelity.dimension))
    palette = dict(zip(models, COLORS * (len(models) // len(COLORS) + 1)))

    # F1: model panels, dimension × channel. NA is gray, never a zero-rate cell.
    fig, axs = plt.subplots(len(models), 1, figsize=(3.45, 1.7 * len(models)), squeeze=False,
                            constrained_layout=True)
    for ax, model in zip(axs[:, 0], models):
        x = fidelity[(fidelity.model == model) & (fidelity.prompt_id == prompt)]
        mat = x.pivot(index="dimension", columns="channel", values="estimate").reindex(index=dims, columns=CHANNELS)
        ax.set_facecolor("#dddddd")
        sns.heatmap(mat.rename(index=DIM_NAMES), ax=ax, cmap="cividis", vmin=0, vmax=1,
                    annot=True, fmt=".2f", annot_kws={"size": 6}, linewidths=.4,
                    cbar=True, cbar_kws={"label": "Match", "ticks": [0, .5, 1]})
        ax.set(title=f"{model} · {prompt}", xlabel="", ylabel="")
        ax.tick_params(axis="x", rotation=0)
        ax.tick_params(axis="y", rotation=0)
    save(fig, out, "F1_attribution")

    # F2: signed conditional A/B imbalance; CIs transformed linearly.
    fig, axs = plt.subplots(len(models), 1, figsize=(3.45, 1.65 * len(models)), squeeze=False,
                            constrained_layout=True)
    direction = tables["direction"]
    for ax, model in zip(axs[:, 0], models):
        x = direction[(direction.model == model) & direction.prompt_id.eq(prompt) &
                      direction.channel.eq("bare") & direction.metric.eq("share_A")].set_index("dimension").reindex(dims)
        for i, (_, r) in enumerate(x.iterrows()):
            if pd.isna(r.estimate):
                ax.text(0, i, "NA", ha="center", va="center", color="0.45")
                continue
            est = (r.estimate - .5) * 2
            ax.barh(i, est, height=.65, color="#0072B2" if est >= 0 else "#D55E00")
            ax.plot([(r.ci_low - .5) * 2, (r.ci_high - .5) * 2], [i, i], color="black", lw=.8)
        ax.axvline(0, color="0.3", lw=.6)
        ax.set(yticks=range(len(dims)), yticklabels=[DIM_NAMES[d] for d in dims], xlim=(-1.08, 1.08),
               xticks=[-1, 0, 1], xticklabels=["All B", "Equal", "All A"], title=f"{model} · {prompt} · bare")
        ax.invert_yaxis()
    save(fig, out, "F2_defaults")

    # F3: mean fidelity and input actions, with nondominated channel frontiers.
    pareto = tables["pareto"]
    fig, axs = plt.subplots(len(dims), 1, figsize=(3.45, 1.55 * len(dims)), squeeze=False,
                            constrained_layout=True)
    for ax, dim in zip(axs[:, 0], dims):
        for model in models:
            x = pareto[pareto.dimension.eq(dim) & pareto.prompt_id.eq(prompt) & pareto.model.eq(model)]
            front = x[x.pareto_efficient & x.critical_match.notna()].sort_values("input_actions")
            ax.plot(front.input_actions, front.critical_match, lw=.7, color=palette[model], alpha=.7)
            for r in x.itertuples():
                if pd.isna(r.critical_match):
                    continue
                ax.scatter(r.input_actions, r.critical_match, marker=MARKERS[r.channel], color=palette[model],
                           s=21, alpha=.65, edgecolors="white", linewidths=.25, zorder=3)
        if not pareto[pareto.dimension.eq(dim) & pareto.prompt_id.eq(prompt)].critical_match.notna().any():
            empty(ax)
            costs = pareto[pareto.dimension.eq(dim)].input_actions.dropna()
            if len(costs):
                ax.set_xlim(costs.min() - .2, costs.max() + .2)
        ax.set(title=DIM_NAMES[dim], ylim=(-.04, 1.04), ylabel="Critical match", xlabel="Input actions (words + chips)")
        ax.grid(alpha=.15)
    handles = [Line2D([], [], color=palette[m], label=m, lw=1.5) for m in models]
    handles += [Line2D([], [], color="0.3", marker=MARKERS[c], linestyle="None", label=c, markersize=4) for c in CHANNELS]
    fig.legend(handles=handles, loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle(f"Fidelity versus input cost · {prompt}", fontsize=8)
    save(fig, out, "F3_pareto")

    # F4: paired P2/S3 bars and family-bootstrap CIs, both ambiguous channels.
    cov = tables["coverage"]
    fig, axs = plt.subplots(len(dims), 1, figsize=(3.45, 1.55 * len(dims)), squeeze=False,
                            constrained_layout=True)
    for ax, dim in zip(axs[:, 0], dims):
        any_data = False
        for j, (channel, pid) in enumerate([(c, p) for c in ["bare", "noncrit"] for p in ["P2", "S3"]]):
            for i, model in enumerate(models):
                x = cov[cov.dimension.eq(dim) & cov.channel.eq(channel) & cov.prompt_id.eq(pid) &
                        cov.model.eq(model) & cov.metric.eq("coverage_at_3")]
                if x.empty or pd.isna(x.iloc[0].estimate):
                    continue
                r = x.iloc[0]
                pos = i + (j - 1.5) * .19
                ax.bar(pos, r.estimate, width=.18, color=COLORS[j], hatch="//" if channel == "noncrit" else None)
                if r.estimate == 0:
                    ax.plot(pos, 0, marker="_", color=COLORS[j], markersize=4, zorder=4)
                ax.plot([pos, pos], [r.ci_low, r.ci_high], color="black", lw=.6)
                any_data = True
        if not any_data:
            empty(ax)
        ax.set(title=DIM_NAMES[dim], ylim=(-.02, 1.04), ylabel="Coverage@3", xticks=range(len(models)),
               xticklabels=[m.replace("-", "-\n", 1) for m in models])
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=COLORS[j], hatch="//" if c == "noncrit" else None,
                            label=f"{p} · {c}") for j, (c, p) in enumerate([(c, p) for c in ["bare", "noncrit"] for p in ["P2", "S3"]])]
    fig.legend(handles=handles, loc="outside lower center", ncol=2, frameon=False)
    save(fig, out, "F4_coverage")

    # F5: general dimensions, marginal across target dimensions; bare/noncrit panels.
    stance = tables["stance_overall"]
    metrics = ["addition_polarity", "addition_speech_act", "addition_agent", "addition_certainty",
               "addition_politeness", "politeness_added", "certainty_raised"]
    labels = ["Polarity differs", "Speech act differs", "Agent differs", "Certainty differs", "Politeness differs",
              "Politeness added", "Certainty raised"]
    fig, axs = plt.subplots(2, 1, figsize=(3.45, 4.5), constrained_layout=True)
    for ax, channel in zip(axs, ["bare", "noncrit"]):
        for j, model in enumerate(models):
            for i, metric in enumerate(metrics):
                x = stance[stance.channel.eq(channel) & stance.prompt_id.eq(prompt) & stance.model.eq(model) & stance.metric.eq(metric)]
                if x.empty or pd.isna(x.iloc[0].estimate):
                    continue
                r = x.iloc[0]
                y = i + (j - (len(models) - 1) / 2) * .15
                ax.plot([r.ci_low, r.ci_high], [y, y], color=palette[model], lw=.9)
                ax.scatter(r.estimate, y, color=palette[model], s=9, zorder=3)
        ax.set(yticks=range(len(labels)), yticklabels=labels, xlim=(-.02, 1.02),
               title=f"{channel} · {prompt}", xlabel="Reference-relative stance rate")
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=.15)
    fig.legend(handles=[Line2D([], [], marker="o", color=palette[m], label=m, lw=.8, markersize=3) for m in models],
               loc="outside lower center", ncol=2, frameon=False)
    save(fig, out, "F5_stance")
