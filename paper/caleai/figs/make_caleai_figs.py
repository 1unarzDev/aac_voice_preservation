"""CALE-AI figures, rebuilt only from stored scored tables (via paper/caleai/evidence.json).

    ~/aac-voice-preservation/.venv/bin/python paper/caleai/caleai_evidence.py   # stored tables -> evidence.json
    ~/aac-voice-preservation/.venv/bin/python paper/caleai/figs/make_caleai_figs.py

Writes
  figs/fig_ledger.pdf / .png   (a) benefit | harm ledger | cost + kill test, one row per intervention
  figs/gallery.tex             (b) before/after gallery: real stored strings, declared selection rule and
                                   the rate of the rule's population attached to every row; for sets,
                                   all three suggestions in both arms.
No number or string is typed here: everything comes from evidence.json, which is computed from
runs/*/scored.parquet, runs/*/generations.jsonl and analysis/interventions/report.json.

Style: dataviz reference palette, emphasis pattern: intervention = blue #256abf, cheap comparator = orange
#eb6834, untreated comparator = deliberately neutral gray #898781 (open marker). validate_palette.js (light):
CVD separation PASS (worst dE 9.8), normal-vision PASS (17.6), contrast PASS; the chroma-floor FAIL is the
intended gray de-emphasis. Identity is double-encoded by marker shape (open circle / filled circle / diamond),
so it survives greyscale print. One x-axis per panel; cost has incommensurable units and is printed, not plotted.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
EV = json.loads((HERE.parent / "evidence.json").read_text())
ROOT = HERE.parents[2]


def wc_ladder(dim: str, ch: str) -> dict:
    """W-C P0 critical-match row (arbiter-resolved analysis) from analysis/r2c/channel_ladder.csv."""
    import csv
    with (ROOT / "analysis/r2c/channel_ladder.csv").open() as fh:
        for r in csv.DictReader(fh):
            if r["dimension"] == dim and r["channel"] == ch and r["metric"] == "critical_match":
                return {"estimate": float(r["estimate"]), "ci_low": float(r["ci_low"]),
                        "ci_high": float(r["ci_high"]), "k": float(r["sum"]), "n": int(r["n"])}
    raise KeyError((dim, ch))


WC_NONC, WC_CHIP, WC_FULL = (wc_ladder("speech_act", c) for c in ("noncrit", "chip1", "full"))

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, BASE = "#256abf", "#eb6834", "#898781"   # intervention, cheap comparator, baseline
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0,
                     "pdf.fonttype": 42, "ps.fonttype": 42})


def p(r):  # estimate/CI in percent
    return 100 * r["estimate"], 100 * r["ci_low"], 100 * r["ci_high"]


def neg(r):  # coverage LOST in pp = -(I2 - P2), CI flipped
    return -100 * r["estimate"], -100 * r["ci_high"], -100 * r["ci_low"]


def frac(k, n):
    return f"{int(k):,}/{int(n):,}"


# ------------------------------------------------------------------ (a) ledger
def kill_verdicts() -> dict:
    """Pre-specified kill criteria, evaluated from stored estimates (never typed)."""
    g, s, c = EV["guard"]["report"], EV["span"]["report"], EV["chips"]
    return {
        "I1": g["G1_cue"]["fix"]["estimate"] >= .30 and g["G1_all"]["overcorr"]["estimate"] <= .10,
        "I2": s["polarity+certainty"]["diff_I2"]["estimate"] >= .30,
        "chip": c["d_chip1_noncrit"]["estimate"] >= .10 and c["chip1"]["estimate"] >= .8 * c["full"]["estimate"],
        "chip_wc": (WC_CHIP["estimate"] - WC_NONC["estimate"] >= .10
                    and WC_CHIP["estimate"] >= .8 * WC_FULL["estimate"]),
    }


def ledger():
    g, s, c = EV["guard"], EV["span"], EV["chips"]
    gr, sr = g["report"], s["report"]
    pc = sr["polarity+certainty"]
    sc = s["set_counts"]
    kv = kill_verdicts()

    def lvl(cnt, arm):  # matched-set level from counts (no interval; the paired change and its CI are in the text)
        v = 100 * cnt[arm] / cnt["n"]
        return v, v, v
    verdict = lambda ok: "PASS" if ok else "FAIL"
    n_cue = g["n_cue_targets"]
    rows = [
        dict(name="Menu", sub="adds missing readings\nto 3 suggestions\n(system side)",
             benefit=[("sets with both readings", p(pc["P2"]), p(pc["I2"]), None,
                       f"{frac(sc['polarity+certainty']['p2'], sc['polarity+certainty']['n'])}→{frac(sc['polarity+certainty']['i2'], sc['polarity+certainty']['n'])}",
                       100 * pc["P2"]["estimate"] + 30)],
             harm=[("politeness", lvl(sc["politeness"], "p2"), lvl(sc["politeness"], "i2"), None,
                    f"{frac(sc['politeness']['p2'], sc['politeness']['n'])}→{frac(sc['politeness']['i2'], sc['politeness']['n'])}, "
                    f"{100 * sr['politeness']['diff_I2']['estimate']:.0f} pp".replace("-", "−"), None),
                   ("speech act", lvl(sc["speech_act"], "p2"), lvl(sc["speech_act"], "i2"), None,
                    f"{frac(sc['speech_act']['p2'], sc['speech_act']['n'])}→{frac(sc['speech_act']['i2'], sc['speech_act']['n'])}, "
                    f"{100 * sr['speech_act']['diff_I2']['estimate']:.1f} pp".replace("-", "−"), None),
                   ("rewrites changing type", None, p(s["act_drift"]), None,
                    f"{int(s['act_drift']['k'])} of {s['act_drift']['n']}", None)],
             cost=[f"+{sr['cost_I2']['calls_per_set']:.2f} calls / set",
                   f"+{sr['cost_I2']['lat_per_set']:.2f} s / set¹",
                   f"{sr['cost_I2']['verified']}/{sr['cost_I2']['rewrites']} self-verified"],
             tests=[("gain ≥30 pp:", False), (verdict(kv['I2']), True)]),
        dict(name="Cue (chip)", sub="user adds one\ncue such as [NOT]\n(user side)",
             benefit=[("value kept: development", p(c["noncrit"]), p(c["chip1"]), None,
                       f"{int(c['noncrit']['k'])}→{int(c['chip1']['k'])} of {c['chip1']['n']}",
                       100 * c["noncrit"]["estimate"] + 10),
                      ("value kept: confirmation", p(WC_NONC), p(WC_CHIP), None,
                       f"{int(WC_NONC['k'])}→{int(WC_CHIP['k'])} of {WC_CHIP['n']}",
                       80 * WC_FULL["estimate"])],
             harm=[("kept, lost with cue", None, p(c["lost_with_chip"]), None,
                    f"{int(c['lost_with_chip']['k'])} of {c['lost_with_chip']['n']}", None),
                   ("missed, still missed", None, p(c["miss_persists"]), None,
                    f"{int(c['miss_persists']['k'])} of {c['miss_persists']['n']}", None),
                   ("cue given, contradicted", None, p(c["chip1_contra"]), None,
                    f"{int(c['chip1_contra']['k'])} of {c['chip1_contra']['n']}", None)],
             cost=["+1 selection²", "+0 calls",
                   f"all chips: {c['chipall_mean_chips']:.1f} selections"],
             tests=[("gain ≥10 pp, ≥80% of typed", False), ("development: " + verdict(kv['chip']), True),
                    ("confirmation: " + verdict(kv['chip_wc']), True)]),
    ]

    W, H = 7.0, 4.7
    fig = plt.figure(figsize=(W, H))
    X_NAME, X_BEN, W_BEN, X_HARM, W_HARM, X_COST = 0.03, 1.25, 1.75, 3.35, 1.75, 5.30
    TOP, ROW_H, GAP = 4.1, 1.62, 0.14
    def axes(x, y, w, hgt):
        return fig.add_axes([x / W, y / H, w / W, hgt / H])

    def item(ax, y, lab, val, b0, b1, cmp_, kill, xmax):
        ax.text(0, y + 0.40, lab, fontsize=7.8, color=INK, va="bottom", ha="left")
        ax.text(0, y + 0.14, val, fontsize=7.2, color=INK2, va="bottom", ha="left")
        if b0 is not None:
            ax.plot([b0[0], b1[0]], [y, y], color=AXIS, lw=1.6, zorder=1, solid_capstyle="round")
            ax.errorbar(b0[0], y, xerr=[[b0[0] - b0[1]], [b0[2] - b0[0]]], fmt="o", mfc="white", mec=BASE,
                        ecolor=BASE, ms=5, mew=1.2, elinewidth=0.9, capsize=0, zorder=3)
        ax.errorbar(b1[0], y, xerr=[[max(b1[0] - b1[1], 0)], [max(b1[2] - b1[0], 0)]], fmt="o", color=BLUE,
                    ms=5.5, elinewidth=0.9, capsize=0, zorder=4, mec="white", mew=0.8)
        if cmp_ is not None:
            ax.errorbar(cmp_[0], y - 0.17, xerr=[[max(cmp_[0] - cmp_[1], 0)], [max(cmp_[2] - cmp_[0], 0)]],
                        fmt="D", color=ORANGE, ms=3.8, elinewidth=0.8, capsize=0, zorder=3, mec="white", mew=0.5)
        if kill is not None:
            ax.plot([kill, kill], [y - 0.26, y + 0.26], color=INK, lw=1.0, zorder=5)

    def style(ax, xmax, ticks, n, last, xlabel):
        ax.set_xlim(0, xmax); ax.set_ylim(-0.4, n - 0.25)
        ax.set_yticks([]); ax.set_xticks(ticks)
        ax.tick_params(axis="x", labelsize=7.4, length=2, labelbottom=last)
        ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        if last:
            ax.set_xlabel(xlabel, fontsize=7.6, labelpad=2)

    y0 = TOP
    for i, r in enumerate(rows):
        n = 3
        hgt = ROW_H
        ybot = y0 - hgt
        last = i == len(rows) - 1
        fig.text(X_NAME / W, (y0 - 0.12) / H, r["name"], fontsize=9, fontweight="bold", color=INK, va="top")
        fig.text(X_NAME / W, (y0 - 0.33) / H, r["sub"], fontsize=7.6, color=INK2, va="top", linespacing=1.05)
        ax = axes(X_BEN, ybot, W_BEN, hgt)
        ys = [2, 1, 0][:len(r["benefit"])] if len(r["benefit"]) > 1 else [1.6]
        if len(r["benefit"]) == 2:
            ys = [1.9, 0.5]
        for y, (lab, b0, b1, cmp_, val, kill) in zip(ys, r["benefit"]):
            item(ax, y, lab, val, b0, b1, cmp_, kill, 100)
        style(ax, 100, [0, 25, 50, 75, 100], n, last, "% of targets or sets")
        ax = axes(X_HARM, ybot, W_HARM, hgt)
        for y, (lab, h0, h1, hcmp, val, kill) in zip([2, 1, 0], r["harm"]):
            item(ax, y, lab, val, h0, h1, hcmp, kill, 100)
        # Every plotted harm value is a percent LEVEL; percentage-point changes are printed, never plotted.
        style(ax, 100, [0, 25, 50, 75, 100], n, last, "% (levels, not changes)")
        for k, line in enumerate(r["cost"]):
            fig.text(X_COST / W, (y0 - 0.16 - k * 0.22) / H, line, fontsize=7.8 if k else 8.2,
                     color=INK if k < 2 else INK2, fontweight="bold" if k == 0 else "normal", va="top")
        yy = y0 - 0.16 - len(r["cost"]) * 0.22 - 0.06
        fig.text(X_COST / W, yy / H, "Pre-set test", fontsize=7.8, color=INK, fontweight="bold", va="top")
        for k2, (t, b) in enumerate(r["tests"]):
            fig.text(X_COST / W, (yy - 0.2 - k2 * 0.2) / H, t, fontsize=7.6, color=INK, fontweight="bold" if b else "normal", va="top")
        y0 = ybot - GAP - (0.0 if last else 0.06)
    # column heads
    for x, t in ((X_BEN, "Benefit"), (X_HARM, "What it leaves or breaks"), (X_COST, "Cost and test")):
        fig.text(x / W, (TOP + 0.08) / H, t, fontsize=9, fontweight="bold", color=INK, va="bottom")
    fig.text(X_NAME / W, 0.04 / H, "¹ local server, partial CPU offload   ² nominal; dwell, scanning, learning not counted\nTick on confirmation row: 80% of the typed-sentence rate",
             fontsize=7.0, color=INK2, va="bottom", linespacing=1.1)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", mfc="white", mec=BASE, mew=1.2, ms=5, label="comparator (baseline menu; length-matched word)"),
         Line2D([], [], marker="o", ls="", color=BLUE, ms=5.5, label="intervention"),
         Line2D([], [], marker="|", ls="", color=INK, ms=8, mew=1.0, label="pre-set pass line")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=3, frameon=False, fontsize=7.6,
               handletextpad=0.3, columnspacing=1.1)
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"fig_ledger.{ext}", dpi=400 if ext == "png" else None)
    plt.close(fig)


# ------------------------------------------------------------------ (b) gallery
def tex(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}
    s = "".join(rep.get(ch, ch) for ch in s)
    return s.replace("'", "'")


def q(s: str) -> str:
    return "``" + tex(s) + "''"


def kw(s: str) -> str:
    return r"\texttt{" + tex(s) + "}"


CH = {"chip1": "one cue", "chipall": "all cues", "full": "typed input"}
SHORT = {"qwen2.5-7b": "Qwen", "llama3.1-8b": "Llama", "gemma3-4b": "Gemma", "gpt-6.1-terra": "Terra"}
READ = {"A": "A", "B": "B", "unclear": "?", "other": "o"}


def setcell(arm: dict, rewritten: list[int], reading_names: dict) -> str:
    out = []
    for k, (t, ch) in enumerate(zip(arm["texts"], arm["chose"])):
        mark = r"$^\dagger$" if k in rewritten else ""
        lab = reading_names.get(ch, READ.get(ch, ch))
        out.append(rf"{k+1}.\,{q(t)}{mark} \textsf{{[{tex(lab)}]}}")
    return r"\newline ".join(out)


def applicability_row():
    """Full-input P2 vs S3 for the declared H1 exact-partner example (analysis/applicability/examples.json)."""
    exs = json.loads((ROOT / "analysis/applicability/examples.json").read_text())
    res = json.loads((ROOT / "analysis/applicability/results.json").read_text())["preserved"]["H1/exact_partner"]
    first = exs[0]
    seen = set()
    exs = [e for e in exs if not (e["output_id"] in seen or seen.add(e["output_id"]))]
    same = [e for e in exs if e["request_key"] and e["family_id"] == first["family_id"] and e["variant"] == first["variant"]
            and e["model"] == first["model"]]
    p2 = sorted([e for e in same if e["prompt_id"] == "P2"], key=lambda e: e["suggestion_idx"])
    s3 = sorted([e for e in same if e["prompt_id"] == "S3"], key=lambda e: (e["sample_idx"], e["suggestion_idx"]))
    assert len(p2) == 3 and len(s3) == 3, (len(p2), len(s3))
    def cell(arr):
        out = []
        for k, e in enumerate(arr):
            mark = r"$^\ddagger$" if e["output_id"] == first["output_id"] else ""
            out.append(rf"{k+1}.\,{q(e['text'])}{mark}")
        return r"\newline ".join(out)
    inp = first["input_text"]
    rate = (rf"{SHORT[first['model']]}, {tex(first['family_id'])}/{first['variant']}, full input. Rule: first full-input P2 set containing "
            rf"the other authored source ($\ddagger$) (family, model, variant, slot order). Sets reproducing the partner source: "
            rf"P2 {frac(res['P2']['k'], res['P2']['n'])} vs.\ S3 {frac(res['S3']['k'], res['S3']['n'])}.")
    return (r"Full-input set", kw(inp), "P2: " + cell(p2), "S3: " + cell(s3), rate)


def guard_examples():
    """figs/guard_examples.tex: rows for the guard display (main.tex table), P0 vs G1 for the same stored request.
    Discovery rows: first/second fail->pass and first fail->fail in the SHA-1 hash order of the intervention report.
    Transfer row: first correct-text-changed event in the frozen SHA-256 order of analysis/guard_wc/examples.json."""
    g = EV["guard"]
    G = {(x["category"], x["rank"]): x for x in g["gallery"]}
    def head(text):
        return r"\multicolumn{3}{@{}>{\raggedright\arraybackslash}p{\linewidth}@{}}{\textsf{" + text + r"}}\\"
    def strings(inp, before, after):
        return rf"{kw(inp)} & {q(before)} & {q(after)}\\[2pt]"
    L = [r"% AUTO-GENERATED by figs/make_caleai_figs.py from evidence.json and analysis/guard_wc/examples.json -- do not edit by hand."]
    x = G[("fixed", 1)]
    L += [head(rf"\textbf{{Development set, repaired}} ({SHORT[x['model']]}, {CH[x['channel']]}; "
               rf"1st by hash order; {frac(x['pool_k'], x['pool_n'])} scored failures repaired)"),
          strings(x["input"][10:], x["before"], x["after"])]
    x = G[("unfixed", 1)]
    L += [head(rf"\textbf{{Development set, failure that remains}} ({SHORT[x['model']]}, {CH[x['channel']]}; "
               rf"1st by hash order; {frac(x['pool_k'], x['pool_n'])} failures remain, {g['residual_flagged']['k']}/{g['residual_flagged']['n']} "
               r"still flagged; the source asks whether the listener is charging it)"),
          strings(x["input"][10:], x["before"], x["after"])]
    # the fragment and correct-text-changed rows are Figure 1 rows 3 and 1 and are not repeated here
    (HERE / "guard_examples.tex").write_text("\n".join(L) + "\n")


def gallery():
    """figs/gallery.tex: complete menus only (guard examples live in the guard display). Columns are configurations,
    not before/after: P2 vs I2 for bare-input menus, P2 vs S3 for the full-input appointment menu."""
    s = EV["span"]
    rows = []
    sc = s["set_counts"]
    for x in s["gallery"]:
        if x["dimension"] == "certainty":
            names = {"A": "plain", "B": "hedged", "unclear": "?"}
        elif x["dimension"] == "polarity":
            names = {"A": "affirm.", "B": "negated", "unclear": "?"}
        else:
            names = {"A": "plain", "B": "polite", "unclear": "?"}
        if x["kind"] == "gain":
            k = sc["polarity+certainty"]
            rate = (rf"Rule: first polarity/certainty set gaining both readings (hash order). Sets with both readings "
                    rf"{frac(k['p2'], k['n'])}$\rightarrow${frac(k['i2'], k['n'])}. "
                    r"Slot 3 also changed and locations were invented.")
            labl = "I2 target gain"
        else:
            k = sc["politeness"]
            rate = (rf"Rule: first politeness set losing both readings (hash order). Politeness coverage "
                    rf"{frac(k['p2'], k['n'])}$\rightarrow${frac(k['i2'], k['n'])} matched sets; "
                    r"different families from the row above.")
            labl = "I2 collateral loss"
        rows.append((labl, kw(x["bare"]), "P2: " + setcell(x["P2"], [], names), "I2: " + setcell(x["I2"], x["rewritten_slots"], names),
                     rf"{SHORT[x['model']]}, {tex(x['family_id'])}. {rate}"))
    rows.append(applicability_row())
    L = [r"% AUTO-GENERATED by figs/make_caleai_figs.py from evidence.json and analysis/applicability -- do not edit by hand.",
         r"\begin{figure*}[!t]", r"\centering\footnotesize", r"\setlength{\tabcolsep}{3pt}",
         r"\renewcommand{\arraystretch}{1.1}",
         r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{1.25cm}>{\raggedright\arraybackslash}p{2.5cm}>{\raggedright\arraybackslash}p{4.15cm}>{\raggedright\arraybackslash}p{4.15cm}>{\raggedright\arraybackslash}p{4.75cm}@{}}", r"\toprule",
         r"Menu & Visible input & Configuration 1 (comparator) & Configuration 2 & Model, item, declared rule, rate of that rule's population\\",
         r"\midrule"]
    for k, rr in enumerate(rows):
        L.append(" & ".join(rr) + r"\\")
        if k == 1:
            L.append(r"\midrule")
    L += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Complete three-suggestion menus from two configurations of the same stored request, verbatim, in slot order "
          r"(keyword inputs shown without their stored \texttt{Keywords:} wrapper). Columns compare configurations, not a before and after. "
          r"Rows follow the outcome-conditioned rule they name (hash order: SHA-1 of request, family, variant and channel), so they illustrate rather than sample; "
          r"each rate describes that rule's population. Bracketed: the machine-extracted reading ([?] = unclear); $\dagger$: slots I2 rewrote. "
          r"The first two rows are discovery bare input; the last is W-C full input, where the hidden source and the visible input coincide.}",
          r"\label{fig:gallery}", r"\end{figure*}"]
    (HERE / "gallery.tex").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    ledger()
    guard_examples()
    gallery()
    print("wrote", HERE / "fig_ledger.pdf", HERE / "gallery.tex")
