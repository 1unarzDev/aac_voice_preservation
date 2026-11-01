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
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0,
                     "pdf.fonttype": 42, "ps.fonttype": 42})


def p(r):  # estimate/CI in percent
    return 100 * r["estimate"], 100 * r["ci_low"], 100 * r["ci_high"]


def neg(r):  # coverage LOST in pp = -(I2 - P2), CI flipped
    return -100 * r["estimate"], -100 * r["ci_high"], -100 * r["ci_low"]


def frac(k, n):
    return f"{int(k)}/{int(n)}"


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
    kv = kill_verdicts()
    verdict = lambda ok: "PASS" if ok else "FAIL"
    n_cue = g["n_cue_targets"]
    rows = [
        dict(name="I1 Guard", sub="check supplied cues,\nregenerate on a flag\n(system side, runtime)",
             benefit=[("strict pass, cue targets", p(gr["P0"]["sp"]), p(gr["G1"]["sp"]), p(gr["G1s"]["sp"]),
                       f"{round(gr['P0']['sp']['estimate']*n_cue)}→{round(gr['G1']['sp']['estimate']*n_cue)} of {n_cue}", None),
                      ("scored violations repaired", None, p(gr["G1_cue"]["fix"]), p(gr["G1s_cue"]["fix"]),
                       f"{round(gr['G1_cue']['fix']['estimate']*gr['G1_cue']['n_bad'])} of {gr['G1_cue']['n_bad']}", 30)],
             harm=[("correct outputs changed", p(gr["G1_all"]["overcorr"]), p(gr["G1s_all"]["overcorr"]),
                    f"{round(gr['G1_all']['overcorr']['estimate']*gr['G1_all']['n_ok'])} of {gr['G1_all']['n_ok']}", 10),
                   ("correct → scored failure", p(gr["G1_all"]["broken"]), p(gr["G1s_all"]["broken"]),
                    f"0 of {gr['G1_all']['n_ok']}", None),
                   ("violations left unrepaired", (100 * g["unfixed_of_bad"]["k"] / g["unfixed_of_bad"]["n"],) * 3,
                    (100 * (1 - gr["G1s_cue"]["fix"]["estimate"]),) * 3,
                    f"{g['unfixed_of_bad']['k']} of {g['unfixed_of_bad']['n']}", None)],
             cost=[f"+{gr['cost']['calls_per_input']:.2f} calls / input",
                   f"+{gr['cost']['lat_per_input']:.2f} s / input¹",
                   "strip-only: 0 calls"],
             kill=f"fix ≥30% and changes ≤10%: {verdict(kv['I1'])}"),
        dict(name="I2 Complete set", sub="fill missing readings\nin k = 3 suggestions\n(system side)",
             benefit=[("sets offering both polarity\nor both certainty readings", p(pc["P2"]), p(pc["I2"]), None,
                       f"{s['set_counts']['polarity+certainty']['p2']}→{s['set_counts']['polarity+certainty']['i2']} of 80",
                       100 * pc["P2"]["estimate"] + 30)],
             harm=[("politeness coverage lost", neg(sr["politeness"]["diff_I2"]), None,
                    f"{s['set_counts']['politeness']['lost']} of {s['set_counts']['politeness']['p2_covered']} sets", None),
                   ("speech-act coverage lost", neg(sr["speech_act"]["diff_I2"]), None,
                    f"{s['set_counts']['speech_act']['lost']} of {s['set_counts']['speech_act']['p2_covered']} sets", None),
                   ("rewrites that change act", p(s["act_drift"]), None,
                    f"{int(s['act_drift']['k'])} of {s['act_drift']['n']}", None)],
             cost=[f"+{sr['cost_I2']['calls_per_set']:.2f} calls / set",
                   f"+{sr['cost_I2']['lat_per_set']:.2f} s / set¹",
                   f"{sr['cost_I2']['verified']}/{sr['cost_I2']['rewrites']} self-verified"],
             kill=f"gain ≥30 pp: {verdict(kv['I2'])}"),
        dict(name="Chip", sub="user adds one\ncommitment marker\n(user side)",
             benefit=[("critical value matched,\ndiscovery (6 dimensions)", p(c["noncrit"]), p(c["chip1"]), None,
                       f"{int(c['noncrit']['k'])}→{int(c['chip1']['k'])} of {c['chip1']['n']}",
                       100 * c["noncrit"]["estimate"] + 10),
                      ("W-C speech act", p(WC_NONC), p(WC_CHIP), None,
                       f"{int(WC_NONC['k'])}→{int(WC_CHIP['k'])} of {WC_CHIP['n']}",
                       80 * WC_FULL["estimate"])],
             harm=[("lost after adding chip", p(c["lost_with_chip"]), None,
                    f"{int(c['lost_with_chip']['k'])} of {c['lost_with_chip']['n']}", None),
                   ("bare miss still missed", p(c["miss_persists"]), None,
                    f"{int(c['miss_persists']['k'])} of {c['miss_persists']['n']}", None),
                   ("supplied value contradicted", p(c["chip1_contra"]), None,
                    f"{int(c['chip1_contra']['k'])} of {c['chip1_contra']['n']}", None)],
             cost=["+1 selection (nominal)²", "+0 calls",
                   f"all chips: {c['chipall_mean_chips']:.1f} selections"],
             kill=f"gain ≥10 pp, ≥80% of full: discovery {verdict(kv['chip'])}",
             kill2=f"W-C speech act: {verdict(kv['chip_wc'])}"),
    ]

    W, H = 7.0, 4.4
    fig = plt.figure(figsize=(W, H))
    X_NAME, X_BEN, W_BEN, X_HARM, W_HARM, X_COST = 0.03, 1.50, 1.95, 3.72, 1.72, 5.62
    TOP, ROW_H, GAP = 3.86, 1.02, 0.12
    def axes(x, y, w, hgt):
        return fig.add_axes([x / W, y / H, w / W, hgt / H])

    def item(ax, y, lab, val, b0, b1, cmp_, kill, xmax):
        ax.text(0, y + 0.36, lab, fontsize=6.5, color=INK, va="bottom", ha="left", linespacing=0.95)
        ax.text(xmax, y + 0.36, val, fontsize=6.3, color=INK2, va="bottom", ha="right")
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
        ax.tick_params(axis="x", labelsize=6.3, length=2, labelbottom=last)
        ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        if last:
            ax.set_xlabel(xlabel, fontsize=6.5, labelpad=2)

    y0 = TOP
    for i, r in enumerate(rows):
        n = 3
        hgt = ROW_H
        ybot = y0 - hgt
        last = i == len(rows) - 1
        fig.text(X_NAME / W, (y0 - 0.12) / H, r["name"], fontsize=7.6, fontweight="bold", color=INK, va="top")
        fig.text(X_NAME / W, (y0 - 0.33) / H, r["sub"], fontsize=6.5, color=INK2, va="top", linespacing=1.05)
        ax = axes(X_BEN, ybot, W_BEN, hgt)
        ys = [2, 1, 0][:len(r["benefit"])] if len(r["benefit"]) > 1 else [1.6]
        if len(r["benefit"]) == 2:
            ys = [1.9, 0.5]
        for y, (lab, b0, b1, cmp_, val, kill) in zip(ys, r["benefit"]):
            item(ax, y, lab, val, b0, b1, cmp_, kill, 100)
        style(ax, 100, [0, 25, 50, 75, 100], n, last, "% of targets, sets or violations")
        ax = axes(X_HARM, ybot, W_HARM, hgt)
        for y, (lab, hv, hcmp, val, kill) in zip([2, 1, 0], r["harm"]):
            item(ax, y, lab, val, None, hv, hcmp, kill, 60)
        style(ax, 60, [0, 20, 40, 60], n, last, "% (rates) or pp (coverage lost)")
        for k, line in enumerate(r["cost"]):
            fig.text(X_COST / W, (y0 - 0.16 - k * 0.19) / H, line, fontsize=6.6 if k else 7.0,
                     color=INK if k < 2 else INK2, fontweight="bold" if k == 0 else "normal", va="top")
        kl = r["kill"].split(": ")
        fig.text(X_COST / W, (y0 - 0.16 - 3 * 0.19 - 0.04) / H, "Kill test: " + kl[-1], fontsize=6.6,
                 color=INK, fontweight="bold", va="top")
        fig.text(X_COST / W, (y0 - 0.16 - 4 * 0.19 - 0.04) / H, ": ".join(kl[:-1]), fontsize=6.0,
                 color=INK2, va="top")
        if "kill2" in r:
            fig.text(X_COST / W, (y0 - 0.16 - 5 * 0.19 - 0.04) / H, r["kill2"], fontsize=6.6,
                     color=INK, fontweight="bold", va="top")
        y0 = ybot - GAP - (0.0 if last else 0.06)
    # column heads
    for x, t in ((X_BEN, "Benefit (targeted endpoint)"), (X_HARM, "Harm ledger"), (X_COST, "Cost")):
        fig.text(x / W, (TOP + 0.08) / H, t, fontsize=7.8, fontweight="bold", color=INK, va="bottom")
    fig.text(X_NAME / W, 0.04 / H, "¹ local server, partial CPU offload\n² reading time not counted\nW-C tick: 80% of full-input match",
             fontsize=5.8, color=INK2, va="bottom", linespacing=1.1)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", mfc="white", mec=BASE, mew=1.2, ms=5, label="comparator (first pass, P2 set, length-matched word)"),
         Line2D([], [], marker="o", ls="", color=BLUE, ms=5.5, label="intervention"),
         Line2D([], [], marker="D", ls="", color=ORANGE, ms=3.8, label="strip-only guard"),
         Line2D([], [], marker="|", ls="", color=INK, ms=8, mew=1.0, label="pre-specified kill line")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=4, frameon=False, fontsize=6.5,
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


def gallery():
    g, s, c = EV["guard"], EV["span"], EV["chips"]
    G = {(x["category"], x["rank"]): x for x in g["gallery"]}
    cg = c["gallery"]
    rows = []
    lab = {"fixed": "I1 repaired", "unfixed": "I1 not repaired", "changed_correct": "I1 changed correct"}
    for key, note in ((("fixed", 1), "first"), (("fixed", 2), "second"), (("unfixed", 1), "first"),
                      (("changed_correct", 1), "first")):
        x = G[key]
        inp = x["input"][10:] if x["input"].startswith("Keywords: ") else x["input"]
        if key[0] == "fixed" and key[1] == 1:
            rate = rf"{frac(x['pool_k'], x['pool_n'])} scored failures repaired."
        elif key[0] == "unfixed":
            rate = (rf"{frac(x['pool_k'], x['pool_n'])} failures remain; {g['residual_act']['k']}/{g['residual_act']['n']} involve speech act; "
                    rf"{g['residual_flagged']['k']}/{g['residual_flagged']['n']} still flagged by the monitor.")
        elif key[0] == "fixed":
            rate = (rf"Scored repair that is a fragment: {frac(g['ask_you_prefix']['k'], g['ask_you_prefix']['n'])} "
                    r"scored repairs start ``Ask you'' (post hoc lexical count, not a fluency rate).")
        else:
            rate = (rf"Already-correct cue targets changed: {frac(g['changed_correct_cue']['k'], g['changed_correct_cue']['n'])}; "
                    r"none became a scored failure, yet the softener form changed.")
        rows.append((lab[key[0]], kw(inp), q(x["before"]), q(x["after"]),
                     rf"{SHORT[x['model']]}, {tex(x['family_id'])}/{x['variant']}, {x['channel']}. Rule: {note} by hash order. {rate}"))
    # set rows: all three suggestions in both arms
    for x in s["gallery"]:
        if x["dimension"] == "certainty":
            names = {"A": "plain", "B": "hedged", "unclear": "?"}
        elif x["dimension"] == "polarity":
            names = {"A": "affirm.", "B": "negated", "unclear": "?"}
        else:
            names = {"A": "plain", "B": "polite", "unclear": "?"}
        sc = s["set_counts"]
        if x["kind"] == "gain":
            k = sc["polarity+certainty"]
            rate = (rf"Rule: first polarity/certainty set gaining both readings (hash order). Sets with both readings "
                    rf"{frac(k['p2'], k['n'])}$\rightarrow${frac(k['i2'], k['n'])}; {frac(k['gained'], k['p2_uncovered'])} uncovered sets gained. "
                    r"Slot 3 also changed and locations were invented.")
            labl = "I2 coverage gain"
        else:
            k = sc["politeness"]
            rate = (rf"Rule: first politeness set losing both readings (hash order). Politeness coverage "
                    rf"{frac(k['p2'], k['n'])}$\rightarrow${frac(k['i2'], k['n'])}; {frac(k['lost'], k['p2_covered'])} covered sets lost. "
                    r"Different families from the row above.")
            labl = "I2 collateral loss"
        rows.append((labl, kw(x["bare"]), setcell(x["P2"], [], names), setcell(x["I2"], x["rewritten_slots"], names),
                     rf"{SHORT[x['model']]}, {tex(x['family_id'])}. {rate}"))
    e = s["act_drift_example"]
    bd = s["act_drift_by_dim"]["certainty"]
    rows.append(("I2 act drift", kw(e["bare"]), q(e["before"]), q(e["after"]),
                 rf"{SHORT[e['model']]}, {tex(e['family_id'])}, slot {e['slot']+1} (certainty rewrite). Rule: first certainty edit "
                 rf"that changes act (family, model, slot). Certainty edits changing act: {frac(bd['k'], bd['n'])}."))
    rows.append(applicability_row())
    L = [r"% AUTO-GENERATED by figs/make_caleai_figs.py from evidence.json and analysis/applicability -- do not edit by hand.",
         r"\begin{figure*}[!t]", r"\centering\footnotesize", r"\setlength{\tabcolsep}{3pt}",
         r"\renewcommand{\arraystretch}{1.12}",
         r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{1.3cm}>{\raggedright\arraybackslash}p{2.55cm}>{\raggedright\arraybackslash}p{3.95cm}>{\raggedright\arraybackslash}p{4.05cm}>{\raggedright\arraybackslash}p{5.0cm}@{}}", r"\toprule",
         r"Arm & Visible input & Before (comparator) & After (intervention) & Model, item, declared rule, rate of that rule's population\\",
         r"\midrule"]
    for k, rr in enumerate(rows):
        L.append(" & ".join(rr) + r"\\")
        if k in (3, 6):
            L.append(r"\midrule")
    L += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Before/after gallery of stored outputs, verbatim. Each row is chosen by the outcome-conditioned rule it names "
          r"(hash order is SHA-1 of request, family, variant and channel, as in the intervention report); its rate describes that rule's population, "
          r"so the gallery is illustrative, not a random sample. Set rows show all three suggestions in both arms, in slot order, with the scored reading "
          r"([?] = unclear on that dimension); $\dagger$ marks slots I2 rewrote. Guard and I2 rows come from the discovery benchmark; the last row is "
          r"W-C (exploratory channel comparison), whose two columns are the P2 and S3 arms for the same typed sentence rather than before and after. Labels are machine-extracted; the human extraction gate covered untreated outputs, not these repairs.}",
          r"\label{fig:gallery}", r"\end{figure*}"]
    (HERE / "gallery.tex").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    ledger()
    gallery()
    print("wrote", HERE / "fig_ledger.pdf", HERE / "gallery.tex")
