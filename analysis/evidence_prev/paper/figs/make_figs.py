"""Publication figures for the main study, built from scored rows only.

    . .venv/bin/activate
    python paper/figs/make_figs.py                       # runs/main1/scored.parquet
    python paper/figs/make_figs.py --table a.parquet b.parquet --items 'data/items/*.jsonl'

Reads only the scored parquet table(s) and the item files. It reuses the
deterministic normalisation in src/analyze.py, so the numbers match
analysis/main1/*.csv. Every CI is a 95% percentile interval from 2000
whole-family bootstrap resamples (seed 20261031).

Writes paper/figs/fig_*.pdf (vector) and fig_*.png (600 dpi), plus
fig_numbers.json (every number quoted in CAPTIONS.md).

Widths are set for the narrower of the two targets, AAAI (3.3 in single column,
7.0 in double column). In IEEE, include them at \\columnwidth (3.5 in) or
\\textwidth (7.16 in): the scale factor is about 1.02-1.06, so 7 pt text stays
between 7 and 7.5 pt.

A/B never appears in a figure. Every direction is shown as the semantic value
(negated, hedged, addressee, ...) or as default vs non-default reading.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import analyze as A  # noqa: E402
from labels import general_spec  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent
N_BOOT, SEED = 2000, 20261031
SINGLE, DOUBLE = 3.3, 7.0

# ---------------------------------------------------------------- style
# Reference palette (dataviz skill), validated: blue/orange pass all-pairs CVD
# (dE 23.8) and normal-vision (dE 34.1) checks; greyscale luminance 0.37 vs 0.54.
# Each colour also has its own marker shape, so identity survives greyscale.
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, BLUE_LT, ORANGE = "#256abf", "#9ec5f4", "#eb6834"
MODEL_ORDER = ["gpt-6.1-terra", "qwen2.5-7b", "llama3.1-8b", "gemma3-4b"]
MODEL_LABEL = {"gpt-6.1-terra": "GPT-6.1-terra", "qwen2.5-7b": "Qwen2.5-7B",
               "llama3.1-8b": "Llama-3.1-8B", "gemma3-4b": "Gemma-3-4B"}
MODEL_MARK = {"gpt-6.1-terra": "o", "qwen2.5-7b": "s", "llama3.1-8b": "^", "gemma3-4b": "D"}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.titleweight": "medium", "axes.titlelocation": "left", "axes.titlepad": 3,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 0, "xtick.major.pad": 2, "ytick.major.pad": 3,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.5,
    "text.color": INK, "legend.frameon": False, "legend.handletextpad": 0.4,
    "legend.borderaxespad": 0.2, "legend.columnspacing": 1.0,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
    "figure.dpi": 150, "lines.solid_capstyle": "round",
})

# Dimension rows. time_quantity is split into its two kinds of pair because
# their value sets differ (past/now/later vs two numbers).
DIMS = ["polarity", "certainty", "agent", "speech_act", "politeness", "time", "quantity"]
DIM_LABEL = {"polarity": "Polarity", "certainty": "Certainty", "agent": "Agent",
             "speech_act": "Speech act", "politeness": "Politeness", "time": "Time",
             "quantity": "Quantity"}
VALUE_ORDER = {
    "polarity": ["affirmative", "negated", "unclear/mixed"],
    "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
    "agent": ["speaker", "addressee", "third party", "we/joint", "unspecified", "unclear/mixed"],
    "speech_act": ["statement", "question", "request/command", "refusal", "acceptance",
                   "offer/suggestion", "other", "unclear/mixed"],
    "politeness": ["plain", "polite", "unclear/mixed"],
    "time": ["past", "now", "later", "unclear/mixed"],
    "quantity": ["lower number", "higher number", "other number", "unclear/mixed"],
}
VALUE_LABEL = {"plain assertion": "plain", "hedged/uncertain": "hedged",
               "strongly certain/emphatic": "emphatic", "third party": "third party",
               "we/joint": "we (joint)", "request/command": "request", "offer/suggestion": "offer",
               "unclear/mixed": "unclear", "lower number": "lower no.", "higher number": "higher no.",
               "other number": "other no."}
NUM = {"two": 2, "three": 3, "four": 4, "six": 6, "nine": 9, "ten": 10, "twenty": 20,
       "forty": 40, "fifty": 50}
CHANNELS = ["bare", "noncrit", "chip1", "chipall", "full"]
CH_LABEL = {"bare": "bare", "noncrit": "+word", "chip1": "+chip", "chipall": "+all",
            "full": "full"}


def boot(frame: pd.DataFrame, col: str) -> dict:
    return A.family_bootstrap(frame, col, n_boot=N_BOOT, seed=SEED)


def subdim(r) -> str:
    if r["dimension"] != "time_quantity":
        return r["dimension"]
    return "time" if r["value_A"] in {"past", "now", "later"} else "quantity"


def value_of(r) -> str | None:
    """Semantic value expressed by an output, on the family's critical dimension."""
    c = r["crit"]
    if c is None or (isinstance(c, float) and np.isnan(c)):
        return None
    if r["subdim"] != "quantity" or c == "unclear/mixed":
        return c
    a, b = NUM[r["value_A"]], NUM[r["value_B"]]
    if c in NUM and NUM[c] == min(a, b) and c in (r["value_A"], r["value_B"]):
        return "lower number"
    if c in NUM and NUM[c] == max(a, b) and c in (r["value_A"], r["value_B"]):
        return "higher number"
    return "other number"


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.02,
                    facecolor="white")
    plt.close(fig)


def hgrid(ax):
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)


def pct_axis(ax, axis="x"):
    ticks = [0, .25, .5, .75, 1]
    labels = ["0", "", "50", "", "100%"]
    if axis == "x":
        ax.set_xlim(-0.02, 1.02)
        ax.set_xticks(ticks, labels)
    else:
        ax.set_ylim(-0.03, 1.03)
        ax.set_yticks(ticks, labels)


# ---------------------------------------------------------------- data
def load(tables: list[Path], items_glob: str) -> tuple[pd.DataFrame, dict]:
    items = A.load_items(items_glob)
    raw = pd.concat([pd.read_parquet(t) for t in tables], ignore_index=True)
    raw = raw[raw.channel.isin(CHANNELS)]
    df = A.normalize_table(raw, items)
    df["subdim"] = df.apply(subdim, axis=1)
    df["value"] = df.apply(value_of, axis=1)
    return df, items


# ---------------------------------------------------------------- fig 1
def fig_defaults(df: pd.DataFrame, nums: dict) -> None:
    amb = A.unique_ambiguous(df)
    b = amb[(amb.channel == "bare") & (amb.prompt_id == "P0") & amb.valid.astype(bool)].copy()
    fig, axes = plt.subplots(2, 4, figsize=(DOUBLE, 2.75),
                             gridspec_kw=dict(hspace=0.62, wspace=1.05))
    axes = axes.ravel()
    nums["fig_defaults"] = {"n_outputs": int(len(b)), "n_families": int(b.family_id.nunique()),
                            "rule": "bare channel, P0, one output per family x model (A/B share the request)"}
    for ax, dim in zip(axes, DIMS):
        g = b[b.subdim == dim]
        pairs = set(g.value_A) | set(g.value_B)
        if dim == "quantity":
            pairs = {"lower number", "higher number"}
        vals = [v for v in VALUE_ORDER[dim] if v in pairs or v in set(g.value) or v == "unclear/mixed"]
        res = {}
        for i, v in enumerate(vals):
            g2 = g.assign(hit=(g.value == v).astype(float))
            r = boot(g2, "hit")
            res[v] = {k: r[k] for k in ("estimate", "ci_low", "ci_high")}
            res[v]["by_model"] = {m: float(g2[g2.model == m].hit.mean()) for m in MODEL_ORDER}
            ax.barh(i, r["estimate"], height=0.56, color=BLUE, zorder=2, lw=0)
            if r["ci_high"] > r["ci_low"]:
                ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=INK, lw=0.7, zorder=4,
                        solid_capstyle="butt")
            for k, m in enumerate(MODEL_ORDER):
                ax.scatter(res[v]["by_model"][m], i + (k - 1.5) * 0.1, marker=MODEL_MARK[m], s=6,
                           facecolor="white", edgecolor=INK, lw=0.5, zorder=5)
            ax.text(1.1, i, f"{r['estimate']*100:.0f}%", va="center", ha="left", fontsize=6,
                    color=INK if r["estimate"] > 0 else MUTED, transform=ax.get_yaxis_transform(),
                    clip_on=False)
        ax.axvline(0.5, color=INK2, lw=0.6, ls=(0, (2, 1.5)), zorder=3)
        ax.set_yticks(range(len(vals)), [VALUE_LABEL.get(v, v) for v in vals])
        ax.invert_yaxis()
        ax.set_ylim(len(vals) - 0.45, -0.75)
        pct_axis(ax)
        hgrid(ax)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{DIM_LABEL[dim]}  (n={len(g)})", fontsize=7)
        nums["fig_defaults"][dim] = {"n": int(len(g)), "families": int(g.family_id.nunique()),
                                     "shares": res}
    # legend panel
    lg = axes[-1]
    lg.axis("off")
    hs = [plt.Rectangle((0, 0), 1, 1, color=BLUE, lw=0),
          Line2D([], [], color=INK, lw=0.7)]
    ls = ["pooled share", "95% CI (families)"]
    for m in MODEL_ORDER:
        hs.append(Line2D([], [], marker=MODEL_MARK[m], ls="", ms=3.2, mfc="white", mec=INK, mew=0.5))
        ls.append(MODEL_LABEL[m])
    hs.append(Line2D([], [], color=INK2, lw=0.6, ls=(0, (2, 1.5))))
    ls.append("50%: what a balanced\nminimal pair implies")
    lg.legend(hs, ls, loc="center left", bbox_to_anchor=(-0.25, 0.5), handlelength=1.4,
              labelspacing=0.45, fontsize=6.5)
    for ax in axes[4:7]:
        ax.set_xlabel("share of outputs", labelpad=1.5)
    save(fig, "fig_defaults")


# ---------------------------------------------------------------- fig 2
def fig_channel_ladder(df: pd.DataFrame, nums: dict) -> None:
    d = df[df.prompt_id == "P0"].copy()
    d["cm"] = d.critical_match.astype(float)
    fig, axes = plt.subplots(2, 4, figsize=(DOUBLE, 2.7), sharey=True,
                             gridspec_kw=dict(hspace=0.5, wspace=0.22))
    axes = axes.ravel()
    x = np.arange(len(CHANNELS))
    nums["fig_channel_ladder"] = {"n_outputs": int(len(d)), "n_families": int(d.family_id.nunique())}
    pooled_all = {}
    for ch in CHANNELS:
        pooled_all[ch] = {k: boot(d[d.channel == ch], "cm")[k] for k in ("estimate", "ci_low", "ci_high")}
    nums["fig_channel_ladder"]["all_dims"] = pooled_all
    for j, (ax, dim) in enumerate(zip(axes, DIMS)):
        g = d[d.subdim == dim]
        est, lo, hi = [], [], []
        for ch in CHANNELS:
            r = boot(g[g.channel == ch], "cm")
            est.append(r["estimate"]); lo.append(r["ci_low"]); hi.append(r["ci_high"])
        for k, m in enumerate(MODEL_ORDER):
            gm = g[g.model == m].groupby("channel").cm.mean().reindex(CHANNELS)
            ax.plot(x + (k - 1.5) * 0.09, gm.values, ls="", marker=MODEL_MARK[m], ms=2.6,
                    mfc="white", mec=MUTED, mew=0.5, zorder=3)
        ax.fill_between(x, lo, hi, color=BLUE_LT, alpha=0.55, lw=0, zorder=1)
        ax.plot(x, est, color=BLUE, lw=1.4, marker="o", ms=3.4, mfc=BLUE, mec="white", mew=0.6, zorder=4)
        ax.axhline(0.5, color=INK2, lw=0.5, ls=(0, (2, 1.5)), zorder=1.5)
        pct_axis(ax, "y")
        ax.set_xticks(x, [CH_LABEL[c] for c in CHANNELS])
        ax.set_xlim(-0.35, 4.35)
        ax.grid(axis="y", color=GRID, lw=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelsize=5.8)
        ax.axvspan(1.5, 4.5, color="#f3f2ee", lw=0, zorder=-1)
        ax.set_title(f"{DIM_LABEL[dim]}  ({g.family_id.nunique()} fam.)")
        if j % 4 == 0:
            ax.set_ylabel("critical match")
        nums["fig_channel_ladder"][dim] = dict(zip(CHANNELS, [dict(estimate=e, ci_low=l, ci_high=h)
                                                              for e, l, h in zip(est, lo, hi)]))
    lg = axes[-1]
    lg.axis("off")
    hs = [Line2D([], [], color=BLUE, lw=1.4, marker="o", ms=3.4, mec="white", mew=0.6),
          plt.Rectangle((0, 0), 1, 1, color=BLUE_LT, alpha=0.55, lw=0)]
    ls = ["pooled over 4 models", "95% CI (families)"]
    for m in MODEL_ORDER:
        hs.append(Line2D([], [], marker=MODEL_MARK[m], ls="", ms=3, mfc="white", mec=MUTED, mew=0.5))
        ls.append(MODEL_LABEL[m])
    hs.append(plt.Rectangle((0, 0), 1, 1, color="#f3f2ee", lw=0))
    ls.append("critical cue visible")
    hs.append(Line2D([], [], color=INK2, lw=0.5, ls=(0, (2, 1.5))))
    ls.append("50%: bare ceiling (A and B\nget the same input)")
    lg.legend(hs, ls, loc="center left", bbox_to_anchor=(0.0, 0.4), handlelength=1.6,
              labelspacing=0.32, fontsize=6)
    save(fig, "fig_channel_ladder")


# ---------------------------------------------------------------- fig 3
def family_defaults(df: pd.DataFrame) -> dict:
    """Default reading of each family = the A/B value most often produced under bare.

    Primary count: P0 bare top-1 over the 4 models (one output each). Ties are broken
    by all bare P2 and S3 outputs. Families whose P0 bare outputs never commit to A or B
    (unclear, or a third value), or that stay tied, have no default and are excluded."""
    amb = A.unique_ambiguous(df)
    b = amb[amb.channel == "bare"]
    out = {}
    for fid, g in b.groupby("family_id"):
        p0 = g[g.prompt_id == "P0"].chose.value_counts()
        a, bb = p0.get("A", 0), p0.get("B", 0)
        if a == bb == 0:
            out[fid] = None
            continue
        if a == bb:
            alt = g[g.prompt_id.isin(["P2", "S3"])].chose.value_counts()
            a, bb = alt.get("A", 0), alt.get("B", 0)
        out[fid] = None if a == bb else ("A" if a > bb else "B")
    return out


def fig_cost_asymmetry(df: pd.DataFrame, nums: dict) -> None:
    defaults = family_defaults(df)
    p0 = df[(df.prompt_id == "P0") & (df.channel == "bare")].copy()
    p0["cost"] = [0.0 if r.chose == r.variant else float(r.repair_chip_cost) for r in p0.itertuples()]
    sets = A.suggestion_sets(df)
    p2 = sets[(sets.prompt_id == "P2") & (sets.channel == "bare")].copy()
    p2["cost"] = p2.extra_actions.astype(float)
    p2["subdim"] = p2.family_id.map(df.drop_duplicates("family_id").set_index("family_id").subdim)
    rows = []
    for prompt, t in (("P0", p0), ("P2", p2)):
        t = t.copy()
        t["default"] = t.family_id.map(defaults)
        t = t[t.default.notna()]
        t["reading"] = np.where(t.variant == t.default, "default", "non-default")
        for dim in DIMS:
            for reading in ("default", "non-default"):
                g = t[(t.subdim == dim) & (t.reading == reading)]
                if not len(g):
                    continue
                r = boot(g, "cost")
                rows.append(dict(prompt=prompt, dim=dim, reading=reading, **{k: r[k] for k in (
                    "estimate", "ci_low", "ci_high", "n", "n_families")}))
    res = pd.DataFrame(rows)
    dims = [d for d in DIMS if d in set(res.dim)]
    excluded = sorted(f for f, v in defaults.items() if v is None)
    fig, axes = plt.subplots(1, 2, figsize=(SINGLE, 2.05), sharey=True,
                             gridspec_kw=dict(wspace=0.12))
    y = np.arange(len(dims))
    for ax, prompt, title in zip(axes, ("P0", "P2"), ("1 suggestion (P0)", "3 suggestions (P2)")):
        s = res[res.prompt == prompt].set_index(["dim", "reading"])
        for i, dim in enumerate(dims):
            dd, nd = s.loc[(dim, "default")], s.loc[(dim, "non-default")]
            for row, col, mk, off in ((dd, BLUE, "o", -0.14), (nd, ORANGE, "D", 0.14)):
                ax.plot([row.ci_low, row.ci_high], [i + off, i + off], color=col, lw=0.7, zorder=2,
                        solid_capstyle="butt")
                ax.plot(row.estimate, i + off, marker=mk, ms=3.6 if mk == "o" else 3.2, color=col,
                        mec="white", mew=0.5, zorder=3)
        ax.set_yticks(y, [DIM_LABEL[d] for d in dims])
        ax.set_ylim(len(dims) - 0.4, -0.6)
        ax.set_xlim(-0.06, 1.12)
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        hgrid(ax)
        ax.spines["left"].set_visible(False)
        ax.set_title(title, fontsize=7)
        ax.set_xlabel("extra input actions", labelpad=1.5)
    hs = [Line2D([], [], marker="o", ls="", ms=3.6, color=BLUE, mec="white", mew=0.5),
          Line2D([], [], marker="D", ls="", ms=3.2, color=ORANGE, mec="white", mew=0.5)]
    fig.legend(hs, ["default reading (most common under bare)", "non-default reading"],
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.14), handlelength=1.0,
               fontsize=6)
    save(fig, "fig_cost_asymmetry")
    nums["fig_cost_asymmetry"] = {
        "rule": "bare channel; default = A/B value most often produced by P0 top-1 over 4 models "
                "(ties broken by bare P2+S3 outputs); P0 cost 0 if top-1 matches else chip count; "
                "P2 cost 0 if top-1, 1 if in 3 suggestions, else chip count",
        "families_without_default": excluded,
        "n_families_with_default": int(sum(v is not None for v in defaults.values())),
        "rows": res.to_dict("records")}
    pooled = {}
    for prompt, t in (("P0", p0), ("P2", p2)):
        t = t.copy()
        t["default"] = t.family_id.map(defaults)
        t = t[t.default.notna()]
        for reading, g in t.groupby(np.where(t.variant == t.default, "default", "non-default")):
            r = boot(g, "cost")
            pooled[f"{prompt}_{reading}"] = {k: r[k] for k in ("estimate", "ci_low", "ci_high", "n",
                                                               "n_families")}
    nums["fig_cost_asymmetry"]["pooled"] = pooled


# ---------------------------------------------------------------- fig 4
def fig_politeness_ratchet(df: pd.DataFrame, items: dict, nums: dict) -> None:
    f = df[(df.channel == "full") & (df.prompt_id == "P0") & df.valid.astype(bool)].copy()
    spec = [general_spec(items[r.family_id]["variants"][r.variant].get("all_chips", []),
                         items[r.family_id]["variants"][r.variant].get("general_spec"))
            for r in f.itertuples()]
    f["pol_plain"] = [s["politeness"] == {"none"} for s in spec]
    f["polite_out"] = (f.politeness != "none").astype(float)
    f["impolite_out"] = (f.politeness == "none").astype(float)
    f["hedged_out"] = (f.certainty == "hedged/uncertain").astype(float)
    f["unhedged_out"] = f.certainty.isin(["plain assertion", "strongly certain/emphatic"]).astype(float)
    pol = f[f.subdim == "politeness"]
    cer = f[f.subdim == "certainty"]
    panels = [
        ("Politeness",
         (pol[pol.pol_plain], "polite_out", "added to a plain source"),
         (pol[~pol.pol_plain], "impolite_out", "removed from a polite source")),
        ("Hedging",
         (cer[cer.cv == "plain assertion"], "hedged_out", "added to a plain source"),
         (cer[cer.cv == "hedged/uncertain"], "unhedged_out", "removed from a hedged source")),
    ]
    rows_lbl = ["Pooled"] + [MODEL_LABEL[m] for m in MODEL_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(SINGLE - 0.04, 1.8), sharey=True,
                             gridspec_kw=dict(wspace=0.22))
    nums["fig_politeness_ratchet"] = {"rule": "full channel (user typed the source), P0"}
    for ax, (title, add, rem) in zip(axes, panels):
        rec = {}
        for i, key in enumerate(["Pooled"] + MODEL_ORDER):
            pts = []
            for (frame, col, name), colr, mk, off in ((add, ORANGE, "D", -0.13), (rem, BLUE, "o", 0.13)):
                g = frame if key == "Pooled" else frame[frame.model == key]
                r = boot(g, col)
                pts.append(r["estimate"])
                ax.plot([r["ci_low"], r["ci_high"]], [i + off, i + off], color=colr, lw=0.7,
                        solid_capstyle="butt", zorder=2)
                ax.plot(r["estimate"], i + off, marker=mk, ms=3.6 if mk == "o" else 3.2, color=colr,
                        mec="white", mew=0.5, zorder=3)
                rec.setdefault(key, {})[name] = {k: r[k] for k in ("estimate", "ci_low", "ci_high",
                                                                   "n", "n_families")}
        ax.axhline(0.5, color=AXIS, lw=0.5)
        if all(v[n]["estimate"] == 0 for v in rec.values() for n in v):
            n_add = rec["Pooled"][add[2]]["n"]; n_rem = rec["Pooled"][rem[2]]["n"]
            ax.text(0.13, 2.5, f"no hedge added\n(0 of {n_add} plain sources)\nor removed\n(0 of {n_rem} hedged sources)",
                    fontsize=5.8, color=INK2, va="center", ha="left", linespacing=1.2,
                    bbox=dict(fc="white", ec="none", pad=1))
        ax.set_yticks(range(5), rows_lbl)
        [t.set_fontweight("bold") for t in ax.get_yticklabels()[:1]]
        ax.set_ylim(4.5, -0.6)
        pct_axis(ax)
        ax.set_xticks([0, .25, .5, .75, 1], ["0", "", "50", "", "100%"])
        hgrid(ax)
        ax.spines["left"].set_visible(False)
        ax.set_title(title, fontsize=7)
        ax.set_xlabel("share of outputs", labelpad=1.5)
        nums["fig_politeness_ratchet"][title] = rec
    # all-source politeness addition, for the caption
    allp = f[f.pol_plain]
    nums["fig_politeness_ratchet"]["politeness_added_all_plain_sources"] = {
        k: boot(allp if k == "Pooled" else allp[allp.model == k], "polite_out")["estimate"]
        for k in ["Pooled"] + MODEL_ORDER} | {"n": int(len(allp)), "families": int(allp.family_id.nunique())}
    hs = [Line2D([], [], marker="D", ls="", ms=3.2, color=ORANGE, mec="white", mew=0.5),
          Line2D([], [], marker="o", ls="", ms=3.6, color=BLUE, mec="white", mew=0.5)]
    fig.legend(hs, ["added to a plain source", "removed from a marked source"],
               loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.16), handlelength=1.0,
               fontsize=6)
    save(fig, "fig_politeness_ratchet")


# ---------------------------------------------------------------- fig 5
def fig_sets(df: pd.DataFrame, nums: dict) -> None:
    sets = A.suggestion_sets(df)
    u = sets.sort_values("variant").drop_duplicates(["family_id", "channel", "model", "prompt_id", "set_id"])
    u = u[u.channel == "bare"].copy()
    u["subdim"] = u.family_id.map(df.drop_duplicates("family_id").set_index("family_id").subdim)
    u["cov"] = u.coverage_at_3.astype(float)
    fig, ax = plt.subplots(figsize=(SINGLE - 0.36, 1.9))
    res = {}
    for i, dim in enumerate(DIMS):
        pts = []
        for prompt, colr, mk, off in (("S3", ORANGE, "D", 0.13), ("P2", BLUE, "o", -0.13)):
            g = u[(u.subdim == dim) & (u.prompt_id == prompt)]
            r = boot(g, "cov")
            pts.append(r["estimate"])
            ax.plot([r["ci_low"], r["ci_high"]], [i + off, i + off], color=colr, lw=0.7,
                    solid_capstyle="butt", zorder=2)
            ax.plot(r["estimate"], i + off, marker=mk, ms=3.6 if mk == "o" else 3.2, color=colr,
                    mec="white", mew=0.5, zorder=3)
            bym = g.groupby("model")["cov"].mean().to_dict()
            res.setdefault(dim, {})[prompt] = {k: r[k] for k in ("estimate", "ci_low", "ci_high", "n",
                                                                "n_families")} | {"by_model": bym}
        ax.text(1.05, i, f"{res[dim]['P2']['estimate']*100:.0f}%", va="center", ha="left",
                fontsize=6, color=BLUE)
        ax.text(1.16, i, f"{res[dim]['S3']['estimate']*100:.0f}%", va="center", ha="left",
                fontsize=6, color=INK2)
    ax.text(1.05, -0.85, "P2", fontsize=6, color=BLUE, fontweight="medium", ha="left")
    ax.text(1.16, -0.85, "S3", fontsize=6, color=INK2, fontweight="medium", ha="left")
    ax.set_yticks(range(len(DIMS)), [DIM_LABEL[d] for d in DIMS])
    ax.set_ylim(len(DIMS) - 0.45, -0.6)
    pct_axis(ax)
    hgrid(ax)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("coverage@3: both readings of the pair among the 3 suggestions", labelpad=1.5)
    hs = [Line2D([], [], marker="o", ls="", ms=3.6, color=BLUE, mec="white", mew=0.5),
          Line2D([], [], marker="D", ls="", ms=3.2, color=ORANGE, mec="white", mew=0.5)]
    ax.legend(hs, ["P2: one request for 3 different meanings", "S3: 3 samples at T=0.7"],
              loc="lower right", bbox_to_anchor=(1.0, 0.0), handlelength=1.0, fontsize=6)
    allp = {}
    for prompt in ("P2", "S3"):
        r = boot(u[u.prompt_id == prompt], "cov")
        allp[prompt] = {k: r[k] for k in ("estimate", "ci_low", "ci_high", "n", "n_families")}
    nums["fig_sets"] = {"rule": "bare channel, one set per family x model x prompt", "by_dim": res,
                        "pooled": allp}
    save(fig, "fig_sets")


# ---------------------------------------------------------------- fig 6
def fig_pipeline(df: pd.DataFrame, items: dict, nums: dict) -> None:
    """Method schematic. The example output and its extracted labels are read from the
    stored data (family pol-07, bare channel, P0, first model in MODEL_ORDER)."""
    fam = items["pol-07"]
    va, vb = fam["variants"]["A"], fam["variants"]["B"]
    ex = df[(df.family_id == "pol-07") & (df.channel == "bare") & (df.prompt_id == "P0")]
    ex = ex[ex.model == MODEL_ORDER[0]].iloc[0]
    nums["fig_pipeline"] = {"example_family": "pol-07", "model": ex.model, "output": ex.text,
                            "polarity": ex.polarity, "agent": ex.agent, "speech_act": ex.speech_act}
    bare, nc = fam["bare"], fam["noncritical"]
    chans = [("bare", bare), ("+noncritical", f"{bare} {nc}"),
             ("+chip", f"{' '.join(va['chips'])} {bare}"),
             ("+all chips", f"{' '.join(va['all_chips'])} {bare}"),
             ("full", va["source"])]
    W, H = DOUBLE - 0.22, 1.72
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    CUE_FC = "#eef4fc"

    def box(x, y, w, h, fc="white", ec=AXIS, lw=0.7, r=0.035):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                    fc=fc, ec=ec, lw=lw, zorder=2))

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=3,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.32,head_width=0.16", color=INK2,
                                    lw=0.7, shrinkA=0, shrinkB=0))

    def stage(x, label):
        ax.text(x, H - 0.03, label, ha="left", va="top", fontsize=5.6, color=MUTED,
                fontweight="bold")

    top, bot = H - 0.2, 0.17
    mid = (top + bot) / 2
    gap = 0.15
    widths = dict(src=0.86, ch=1.76, llm=0.46, out=0.7, judge=0.92, att=1.3)
    xs, x = {}, 0.01
    for k, w in widths.items():
        xs[k] = x
        x += w + gap
    # 1 source pair
    x, w = xs["src"], widths["src"]
    stage(x, "1  SOURCE PAIR")
    for k, (var, lab, yb) in enumerate(((va, "variant A: negated", mid + 0.03),
                                         (vb, "variant B: affirmative", mid - 0.57))):
        box(x, yb, w, 0.54)
        ax.text(x + 0.05, yb + 0.49, lab, fontsize=5.2, color=MUTED, va="top")
        words = var["source"].split()
        cut = len(words) // 2 + 1
        ax.text(x + 0.05, yb + 0.39, "“" + " ".join(words[:cut]) + "\n" + " ".join(words[cut:]) + "”",
                fontsize=6, va="top", linespacing=1.15)
    ax.text(x + w / 2, bot - 0.05, "differ on one dimension", fontsize=5.2, color=MUTED, ha="center",
            va="top")
    # 2 channels
    x2, w2 = xs["ch"], widths["ch"]
    arrow(x + w + 0.015, mid, x2 - 0.015, mid)
    stage(x2, "2  VISIBLE INPUT CHANNEL")
    sep = 0.035
    hgt = (top - bot - sep * 4) / 5
    ys = []
    for k, (name, inp) in enumerate(chans):
        yb = top - (k + 1) * hgt - k * sep
        ys.append(yb + hgt / 2)
        cue = k >= 2
        box(x2, yb, w2, hgt, fc=CUE_FC if cue else "white", ec=BLUE if cue else AXIS)
        ax.text(x2 + 0.05, yb + hgt / 2, name, fontsize=5.6, fontweight="bold", va="center")
        ax.text(x2 + 0.56, yb + hgt / 2, inp, fontsize=5.5, va="center")
    ax.text(x2 + w2 / 2, bot - 0.05, "blue = critical cue visible to the model", fontsize=5.2,
            color=MUTED, ha="center", va="top")
    # 3 LLM (fan-in)
    x3, w3 = xs["llm"], widths["llm"]
    for k, yy in enumerate(ys):
        ax.plot([x2 + w2, x3], [yy, mid + (2 - k) * 0.06], color=AXIS, lw=0.5, zorder=1)
    stage(x3, "3  GENERATE")
    box(x3, mid - 0.34, w3, 0.68, fc=INK, ec=INK)
    ax.text(x3 + w3 / 2, mid + 0.13, "LLM", fontsize=7.5, color="white", ha="center", va="center",
            fontweight="bold")
    ax.text(x3 + w3 / 2, mid - 0.13, "4 models\nP0 / P2 / S3", fontsize=5.2, color="#e1e0d9",
            ha="center", va="center", linespacing=1.25)
    # 4 output
    x4, w4 = xs["out"], widths["out"]
    arrow(x3 + w3 + 0.015, mid, x4 - 0.015, mid)
    stage(x4, "4  OUTPUT")
    box(x4, mid - 0.24, w4, 0.48)
    words = ex.text.split()
    cut = (len(words) + 1) // 2
    ax.text(x4 + w4 / 2, mid, "“" + " ".join(words[:cut]) + "\n" + " ".join(words[cut:]) + "”",
            fontsize=6, ha="center", va="center", linespacing=1.15)
    ax.text(x4 + w4 / 2, mid - 0.31, f"{MODEL_LABEL[ex.model]},\nbare input", fontsize=5,
            color=MUTED, ha="center", va="top", linespacing=1.15)
    # 5 blind extraction
    x5, w5 = xs["judge"], widths["judge"]
    arrow(x4 + w4 + 0.015, mid, x5 - 0.015, mid)
    stage(x5, "5  BLIND EXTRACTION")
    box(x5, mid - 0.4, w5, 0.8)
    ax.text(x5 + 0.06, mid + 0.31, "LLM judge", fontsize=6, fontweight="bold", va="center")
    ax.text(x5 + 0.06, mid + 0.17, "sees the output only,\nnot the source or channel", fontsize=5,
            color=MUTED, va="top", linespacing=1.15)
    lab = [("polarity", ex.polarity), ("agent", ex.agent), ("speech act", ex.speech_act)]
    for k, (d, v) in enumerate(lab):
        ax.text(x5 + 0.06, mid - 0.12 - k * 0.1, d, fontsize=5.2, color=INK2, va="center")
        ax.text(x5 + 0.5, mid - 0.12 - k * 0.1, v, fontsize=5.2, va="center", fontweight="bold")
    # 6 attribution
    x6, w6 = xs["att"], W - xs["att"] - 0.01
    arrow(x5 + w5 + 0.015, mid, x6 - 0.015, mid)
    stage(x6, "6  DETERMINISTIC ATTRIBUTION")
    outs = [("Loss", "critical value not recoverable\nfrom the visible input"),
            ("Violation", "cue visible, but output\nvalue ≠ source value"),
            ("Assumption", "no cue, but output commits\nto a definite value")]
    sep6 = 0.05
    bh = (top - bot - 2 * sep6) / 3
    for k, (name, desc) in enumerate(outs):
        yb = top - (k + 1) * bh - k * sep6
        box(x6, yb, w6, bh)
        ax.add_patch(plt.Rectangle((x6, yb + 0.03), 0.025, bh - 0.06, color=ORANGE if k else MUTED,
                                   lw=0, zorder=3))
        ax.text(x6 + 0.07, yb + bh - 0.055, name, fontsize=6, fontweight="bold", va="top")
        ax.text(x6 + 0.07, yb + bh - 0.16, desc, fontsize=5.1, color=INK2, va="top", linespacing=1.15)
    ax.text(x6 + w6 / 2, bot - 0.05, "label vs item spec + channel; no judgment", fontsize=5.2,
            color=MUTED, ha="center", va="top")
    save(fig, "fig_pipeline")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", type=Path, nargs="+", default=[ROOT / "runs/main1/scored.parquet"])
    ap.add_argument("--items", default=str(ROOT / "data/items/*.jsonl"))
    ap.add_argument("--only", nargs="*", help="subset of figure names")
    args = ap.parse_args()
    df, items = load(args.table, args.items)
    nums = {"n_families": int(df.family_id.nunique()), "n_rows": int(len(df)),
            "models": MODEL_ORDER, "n_boot": N_BOOT, "seed": SEED,
            "tables": [str(t) for t in args.table]}
    nums["note"] = "widths in inches of the saved PDFs are reported under pdf_sizes"
    todo = {"fig_defaults": lambda: fig_defaults(df, nums),
            "fig_channel_ladder": lambda: fig_channel_ladder(df, nums),
            "fig_cost_asymmetry": lambda: fig_cost_asymmetry(df, nums),
            "fig_politeness_ratchet": lambda: fig_politeness_ratchet(df, items, nums),
            "fig_sets": lambda: fig_sets(df, nums),
            "fig_pipeline": lambda: fig_pipeline(df, items, nums)}
    for name, fn in todo.items():
        if not args.only or name in args.only:
            fn()
            print("wrote", name)
    import re
    nums["pdf_sizes"] = {}
    for f in sorted(OUT.glob("fig_*.pdf")):
        m = re.search(rb"/MediaBox \[([^\]]+)\]", f.read_bytes())
        nums["pdf_sizes"][f.stem] = [round(float(v) / 72, 2) for v in m.group(1).split()[2:]]
    path = OUT / "fig_numbers.json"
    old = json.loads(path.read_text()) if args.only and path.exists() else {}
    path.write_text(json.dumps(old | nums, indent=1, default=float) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
