#!/usr/bin/env python3
"""Journal figures 1-4 (matplotlib, light/print theme). Run from repo root:
   . .venv/bin/activate && python paper/journal/figs/make_figs.py
Every plotted value is read from analysis files; figure_values.json records value + source,
and the script asserts agreement with results_macros.tex where a macro exists."""
import json, re
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[3]; OUT = Path(__file__).resolve().parent
A = ROOT / "analysis"; DP = A / "frontier/default_profiles"
J = lambda p: json.load(open(ROOT / p))
# Okabe-Ito (colorblind safe); text always in ink, never in series color
BLUE, ORANGE, GREEN, VERM, SKY, PURPLE, YEL, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#F0E442", "#7F7F7F"
INK, MUTED, GRID = "#1a1a1a", "#555555", "#dddddd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42})
VALS: dict = {}
def rec(k, v, src): VALS[k] = {"value": v, "source": src}
MAC = dict(re.findall(r"\\newcommand\{\\jm(\w+)\}\{([^}]*)\}", (OUT.parent / "results_macros.tex").read_text()))
def check(mac, val, tol=0.051):
    """Assert a plotted value equals the paper macro (digits-spelled key already given)."""
    m = MAC.get(mac)
    assert m is not None, f"macro {mac} missing"
    assert abs(float(m.replace(",", "").replace("+", "")) - val) <= tol, (mac, m, val)
def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight"); fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- Fig 1 pipeline (static, no numbers)
def fig1():
    fig, ax = plt.subplots(figsize=(6.6, 2.9)); ax.set_xlim(0, 100); ax.set_ylim(0, 44); ax.axis("off")
    def box(x, y, w, h, t, fc="#f4f4f4", ec=MUTED, bold=False, ls="-"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1, ls=ls))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5, fontweight="bold" if bold else "normal", linespacing=1.15)
    def arr(x1, y1, x2, y2, c=MUTED, ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8, color=c, lw=1, ls=ls, shrinkA=0, shrinkB=0))
    y = 28
    box(1, y, 15, 10, "Writer types\nkeywords", "#e8f1fa")
    box(1, 10, 15, 8, "Optional cue\n(one token)", "#fdf3df", ls="--")
    box(22, y, 14, 10, "Model\n(expands)", "#f4f4f4")
    box(42, y, 15, 10, "Draft or\nset of drafts", "#f4f4f4")
    box(60, y, 21, 10, "Commitment check\n(7 dimensions;\njudge + arbiter)", "#f4f4f4")
    box(87, y, 12, 10, "Writer\napproval\ngate", "#e1f3ec", ec=GREEN, bold=True)
    box(87, 10, 12, 8, "Speak", "#e1f3ec", ec=GREEN)
    arr(16.5, y + 5, 21.5, y + 5); arr(36.5, y + 5, 41.5, y + 5); arr(57.5, y + 5, 62.5, y + 5); arr(81.5, y + 5, 86.5, y + 5)
    arr(8.5, 18.5, 26, y - 0.3, ls="--"); arr(93, y - 0.3, 93, 18.5, c=GREEN)
    ax.text(80, 23.3, "never spoken without\napproval (R6)", fontsize=6.5, ha="center", va="center", color=MUTED)
    # evidence plug-ins
    ev = [(22, 14, "hw1, 6 models,\ncue controls"), (42, 15, "Guard and repair\naudit"), (60, 21, "SLP severity weights\n(n=2 expert review)"), (87, 12, "Writer-intent\nstudy")]
    ax.text(0, 3.8, "Evidence\nfor each stage", fontsize=6.8, color=MUTED, va="center", linespacing=1.1)
    for x, w, t in ev:
        ax.add_patch(Rectangle((x, 1.0), w, 5.6, fc="white", ec=GRID, lw=1))
        ax.text(x + w / 2, 3.8, t, fontsize=6.2, ha="center", va="center", color=MUTED, linespacing=1.1)
        ax.plot([x + w / 2, x + w / 2], [6.8, y - 0.6], color=GRID, lw=0.8, ls=":", zorder=0)
    ax.text(0, 42.6, "Study stages mapped onto the keyword-expansion pipeline", fontsize=8, fontweight="bold", va="center")
    save(fig, "fig1_pipeline")

# ---------------------------------------------------------------- Fig 2 waterfall
def fig2():
    wm = J("analysis/whole_message/summary.json"); ic = J("analysis/intent_check/summary.json")
    kq = wm["key_question"]; right = kq["judge critical RIGHT"]; rc, rb = kq["RIGHT, chip1"], kq["RIGHT, bare"]
    mr = ic["match_rate"]
    n_chip = mr["chip1"]["n"] + mr["chip1"]["unknown"]; n_bare = mr["bare"]["n"] + mr["bare"]["unknown"]
    tot = wm["part18"]["n"]; assert n_chip + n_bare == tot == 200
    intended = {"chip": rc["R1"][1] - rc["R1"][0], "bare": rb["R1"][1] - rb["R1"][0]}
    acc = {"chip": rc["n"] - (rc["R3"] if rc["R3"] <= rc["n"] else rc["n"]), "bare": rb["n"] - rb["R3"]}
    # R3 = not accepted as written; judge-WRONG outputs: 70 all R3 -> accepted 0
    assert kq["judge critical WRONG"]["R3"] == kq["judge critical WRONG"]["n"]
    stages = [("Rated\noutputs", n_chip, n_bare), ("Judge:\ncritical\nkept", rc["n"], rb["n"]),
              ("Writer:\nintended\nversion", intended["chip"], intended["bare"]), ("Accepted\nas written", acc["chip"], acc["bare"])]
    check("wmRightN", right["n"], 0); check("wmRightIntendedK", intended["chip"] + intended["bare"], 0)
    check("pOneEightAcceptYesK", acc["chip"] + acc["bare"], 0)
    rec("waterfall", {s[0].replace("\n", " "): {"chip": s[1], "bare": s[2]} for s in stages}, "analysis/whole_message/summary.json key_question; analysis/intent_check/summary.json match_rate")
    fig = plt.figure(figsize=(6.6, 2.9)); gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], wspace=0.5)
    ax = fig.add_subplot(gs[0]); x = np.arange(4)
    for i, (lab, c, b) in enumerate(stages):
        ax.bar(i, c, 0.62, color=BLUE, label="Cue shown (chip)" if i == 0 else None)
        ax.bar(i, b, 0.62, bottom=c, color=ORANGE, hatch="////", edgecolor="white", lw=0, label="Bare keywords" if i == 0 else None)
        ax.text(i, c + b + 4, f"{c + b}", ha="center", fontsize=8, fontweight="bold")
        if c: ax.text(i, c / 2, str(c), ha="center", va="center", color="white", fontsize=7)
        if b >= 8: ax.text(i, c + b / 2, str(b), ha="center", va="center", color=INK, fontsize=7, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    ax.set_xticks(x, [s[0] for s in stages], fontsize=6.8); ax.set_ylim(0, 225); ax.set_ylabel("Outputs (of 200)")
    ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=6.8, loc="upper right", handlelength=1.2)
    ax.set_title("Judge-correct is not writer-intended", fontsize=8, loc="left", fontweight="bold")
    unk = right["n"] - right["R1"][1]
    ax.text(2.5, 150, f"{unk} of the 130 judge-correct\noutputs have no writer rating", fontsize=6.3, color=MUTED, ha="center") if unk else None
    # reasons panel: judge-correct but not accepted as written
    ax2 = fig.add_subplot(gs[1]); r = kq["reason_right_not_accepted"]
    order = [("substitution", "Who did what\nmisresolved"), ("dropped", "Writer detail\ndropped"), ("fluency", "Fluency"), ("reword", "Rewording only")]
    vals = [r.get(k, 0) for k, _ in order]; N = kq["judge critical RIGHT"]["R3"]; assert sum(vals) == N
    ypos = np.arange(len(order))[::-1]
    ax2.barh(ypos, vals, 0.6, color=[GREEN, GREEN, SKY, SKY])
    for yy, v in zip(ypos, vals): ax2.text(v + 1.5, yy, f"{v} ({100 * v / N:.0f}%)", va="center", fontsize=7)
    ax2.set_yticks(ypos, [l for _, l in order], fontsize=6.8); ax2.set_xlim(0, 100); ax2.set_xlabel("Judge-correct, not accepted as written")
    ax2.xaxis.grid(True, color=GRID, lw=0.6); ax2.set_axisbelow(True)
    ax2.set_title(f"Why (n = {N}); added content: {wm['part18']['reason_all'].get('added', 0)}", fontsize=8, loc="left", fontweight="bold")
    rec("reasons_right_not_accepted", dict(zip([k for k, _ in order], vals)), "analysis/whole_message/summary.json key_question.reason_right_not_accepted")
    save(fig, "fig2_waterfall")

# ---------------------------------------------------------------- Fig 3 frontier
def fig3():
    d = pd.read_csv(DP / "intervention_same_items_r3.csv"); d = d[d.event == "model_visible"]
    f1 = pd.read_csv(DP / "followup/f1_price.csv"); f1 = f1[f1["mode"] == "arb"].set_index(["dimension", "arm"])
    dims = [("polarity", "Polarity (negation)"), ("politeness", "Politeness"), ("speech_act", "Speech act")]
    pol = {"prior_cv_refit": ("Ask, ranked by prior", BLUE, "o"), "random_gated": ("Ask, random", GREY, "s"), "conf_gated_mean": ("Ask, model confidence", ORANGE, "^")}
    fig, axs = plt.subplots(1, 3, figsize=(6.9, 2.9), sharex=True)
    for ax, (dim, title) in zip(axs, dims):
        s = d[d.dimension == dim]
        ac = s[s.strategy == "always-commit"].iloc[0]
        for key, (lab, c, mk) in pol.items():
            rows = s[s.strategy.str.startswith(f"ask policy {key}, ")].sort_values("taps_per_1000")
            xs = [0] + list(rows.taps_per_1000); ys = [ac.reversals_per_1000] + list(rows.reversals_per_1000)
            lo = [ac.lo] + list(rows.lo); hi = [ac.hi] + list(rows.hi)
            ax.plot(xs, ys, color=c, marker=mk, ms=3.8, lw=1.2, label=lab, zorder=3)
            ax.fill_between(xs, lo, hi, color=c, alpha=0.10, lw=0)
            rec(f"ask_{key}_{dim}", dict(zip(xs, ys)), "analysis/frontier/default_profiles/intervention_same_items_r3.csv")
        for arm, lab, c, mk in [("chip", "Cue on every message (chip)", GREEN, "D"), ("word", "Cue on every message (plain word)", SKY, "v"), ("chipG1", "Chip + guard", VERM, "P")]:
            r = f1.loc[(dim, arm)]
            ax.errorbar(1000, r.rev_per_1000, yerr=[[r.rev_per_1000 - r.lo], [r.hi - r.rev_per_1000]], color=c, marker=mk, ms=5, lw=1, capsize=2, ls="none", label=lab, zorder=4)
            rec(f"cue_{arm}_{dim}", [r.rev_per_1000, r.lo, r.hi], "analysis/frontier/default_profiles/followup/f1_price.csv (arb)")
        ax.annotate(f"{ac.reversals_per_1000:.1f}", (0, ac.reversals_per_1000), xytext=(8, 6), textcoords="offset points", fontsize=6.8)
        ax.set_yscale("symlog", linthresh=1); ax.set_ylim(0, 400 if dim == "speech_act" else 100)
        ax.set_yticks([0, 1, 10, 100] + ([] if dim != "speech_act" else [])); ax.set_yticklabels(["0", "1", "10", "100"])
        ax.set_xlim(-40, 1060); ax.set_xticks([0, 200, 500, 1000]); ax.set_title(title, fontsize=8, loc="left", fontweight="bold")
        ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    axs[0].set_ylabel("Reversals per 1,000 messages (symlog)")
    fig.supxlabel("Taps per 1,000 messages (asks at 5, 10, 20%; cue on every message = 1,000)", fontsize=7.5, y=-0.03)
    h, l = axs[0].get_legend_handles_labels(); ax_ = axs[2]
    h2, l2 = ax_.get_legend_handles_labels(); seen = dict(zip(l + l2, h + h2))
    fig.legend(seen.values(), seen.keys(), ncol=3, fontsize=6.6, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.27))
    # checks against paper macros
    pc = d[(d.dimension == "polarity") & (d.strategy == "always-commit")].iloc[0]; check("dpAlwaysCommitPol", pc.reversals_per_1000)
    check("fOneRevPolBare", f1.loc[("polarity", "bare")].rev_per_1000); check("fOneRevPolChip", f1.loc[("polarity", "chip")].rev_per_1000)
    check("fOneRevPolWord", f1.loc[("polarity", "word")].rev_per_1000)
    m10 = d[(d.dimension == "polarity") & d.strategy.str.startswith("ask policy prior_cv_refit, 10%")].iloc[0]; check("dpAskPriorPol", m10.reversals_per_1000)
    m10 = d[(d.dimension == "polarity") & d.strategy.str.startswith("ask policy random_gated, 10%")].iloc[0]; check("dpAskRandPol", m10.reversals_per_1000)
    save(fig, "fig3_frontier")

# ---------------------------------------------------------------- Fig 4 dimension x intervention table
def fig4():
    h = pd.read_csv(A / "hw1/six_dim_rates.csv"); h = h[(h.model == "ALL") & (h.metric == "critical_match")]
    cc = pd.read_csv(A / "chip_controls/chip_controls.csv"); cc = cc[(cc.model == "ALL") & (cc.set == "all_kept")]
    f1 = pd.read_csv(DP / "followup/f1_price.csv"); f1 = f1[f1["mode"] == "arb"].set_index(["dimension", "arm"])
    w = pd.read_csv(DP / "slp_weighted_price_h2.csv"); w = w[w.scheme == "mean"].set_index("dimension")
    dims = [("polarity", "Polarity"), ("politeness", "Politeness"), ("speech_act", "Speech act"), ("agent", "Agent"), ("certainty", "Certainty"), ("time_quantity", "Time / quantity")]
    cols = ["Bare:\nkept (%)", "Chip", "Irrel-\nevant\ncue", "Natural-\nlanguage\ncue", "Bare", "Chip", "Plain\nword", "Chip +\nguard", "SLP\nweight"]
    groups = [(0, 1, "hw1"), (1, 4, "Gain over non-critical cue (pp)"), (4, 8, "Same-items reversals / 1,000"), (8, 9, "")]
    rows = []
    for dim, lab in dims:
        n = int(h[(h.dimension == dim) & (h.channel == "bare")].n.iloc[0])
        bare = h[(h.dimension == dim) & (h.channel == "bare")].estimate.iloc[0] * 100
        g = lambda k: cc[(cc.dimension == dim) & cc.contrast.str.startswith(k)].estimate.iloc[0] * 100
        r = [bare, g("G_chip"), g("G_irrel"), g("G_nl")]
        r += [f1.loc[(dim, a)].rev_per_1000 if (dim, a) in f1.index else np.nan for a in ["bare", "chip", "word", "chipG1"]]
        r += [w.loc[dim].weight if dim in w.index else np.nan]
        rows.append((f"{lab} (n={n})", r)); rec(f"table_{dim}", dict(zip(["bare", "chip", "irrel", "nl", "rev_bare", "rev_chip", "rev_word", "rev_chipG1", "slp_w"], r)), "analysis/hw1/six_dim_rates.csv; analysis/chip_controls/chip_controls.csv; followup/f1_price.csv; slp_weighted_price_h2.csv")
    rows.append(("Event / role (proposed; no data yet)", [np.nan] * 9))
    check("fOneRevPolBare", rows[0][1][4]); check("fOneRevPolChip", rows[0][1][5]); check("fOneRevPoliteBare", rows[1][1][4]); check("fOneRevPoliteChip", rows[1][1][5])
    check("hwChipGain", rows[2][1][1])  # speech-act chip gain = hw1 headline contrast
    fig, ax = plt.subplots(figsize=(6.9, 3.5)); nr = len(rows); ax.set_xlim(-3.3, 9); ax.set_ylim(nr + 0.3, -1.9); ax.axis("off")
    cm_b, cm_o, cm_g = plt.get_cmap("Blues"), plt.get_cmap("Oranges"), plt.get_cmap("Greys")
    for ci, c in enumerate(cols): ax.text(ci + 0.5, -0.6, c, ha="center", va="center", fontsize=6.4, fontweight="bold", linespacing=1.1)
    for a, b, t in groups:
        if t: ax.text((a + b) / 2, -1.55, t, ha="center", fontsize=6.4, color=MUTED); ax.plot([a + 0.08, b - 0.08], [-1.2, -1.2], color=MUTED, lw=0.8)
    for ri, (lab, vals) in enumerate(rows):
        ax.text(-0.1, ri + 0.5, lab, ha="right", va="center", fontsize=7)
        for ci, v in enumerate(vals):
            if ci == 8: face, txt = (cm_g(0.08 + 0.5 * v) if v == v else "white"), (f"{v:.2f}" if v == v else "n/a")
            elif v != v: face, txt = "white", "n/a"
            elif ci in (0, 1, 2, 3): face, txt = cm_b(min(max(v, 0), 100) / 100 * 0.85 + 0.05), f"{v:+.0f}" if ci > 0 else f"{v:.0f}"
            else: face, txt = cm_o(min(v / 200, 1) ** 0.5 * 0.85 + 0.05), f"{v:.1f}" if v < 10 else f"{v:.0f}"
            ax.add_patch(Rectangle((ci + 0.03, ri + 0.04), 0.94, 0.92, fc=face, ec="white" if v == v else GRID, lw=1, hatch="" if v == v else "////"))
            rgb = matplotlib.colors.to_rgb(face) if v == v else (1, 1, 1)
            ax.text(ci + 0.5, ri + 0.5, txt, ha="center", va="center", fontsize=7, color="white" if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] < 0.5 else INK, fontweight="bold" if v == v else "normal")
    ax.text(-3.3, nr + 0.25, "Cells: hw1 channels, four models, writer-cluster CIs in source files. Reversals: F1 same-items run (arb mode). n/a = not measured. Chip = one-token cue.", fontsize=6.2, color=MUTED)
    save(fig, "fig4_dimension_table")

if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4): f()
    json.dump(VALS, open(OUT / "figure_values.json", "w"), indent=1, default=float)
    print("ok", list(OUT.glob("*.pdf")))
