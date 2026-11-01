"""Fig. 1 (running example) for the HUMANE-LLM paper.

Examples are pulled from stored outputs, not typed by hand.
Selection rule: first test family in the dimension (data/items/test.jsonl order),
prompt P0, model Qwen2.5-7B. Exception, declared in the caption: the Violation
row needs a model that changed the plain directive. For that row the rule takes
the first model in the fixed order qwen, llama, gemma, terra whose full-channel P0
output adds "please". The Qwen output is shown next to it.

Usage (from repo root):  .venv/bin/python paper/humane/figs/make_fig1.py
Writes: paper/humane/figs/fig1_running_example.{pdf,png} and fig1_examples.json
"""
import json
import pathlib
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent
MODEL_ORDER = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
MODEL_NAME = {"qwen2.5-7b": "Qwen2.5-7B", "llama3.1-8b": "Llama-3.1-8B",
              "gemma3-4b": "Gemma-3-4B", "gpt-6.1-terra": "GPT (API)"}


def load():
    fams = [json.loads(l) for l in open(ROOT / "data/items/test.jsonl")]
    first = {}
    for f in fams:
        first.setdefault(f["dimension"], f)
    rows = [json.loads(l) for l in open(ROOT / "runs/main1/outputs.jsonl")]
    return first, rows


def out(rows, fid, var, ch, model, prompt="P0"):
    for r in rows:
        if (r["family_id"], r["variant"], r["channel"], r["model"], r["prompt_id"],
                r["sample_idx"], r["suggestion_idx"]) == (fid, var, ch, model, prompt, 0, 0):
            return r
    raise KeyError((fid, var, ch, model))


def select():
    first, rows = load()
    pol, pz = first["polarity"], first["politeness"]
    neg = next(v for v in "AB" if pol["variants"][v]["critical_value"] == "negated")
    aff = "B" if neg == "A" else "A"
    plain = next(v for v in "AB" if pz["variants"][v]["critical_value"] == "plain")
    ex = {
        "pol_family": pol["family_id"],
        "src_neg": pol["variants"][neg]["source"],
        "src_aff": pol["variants"][aff]["source"],
        "bare": pol["bare"],
        "bare_out": out(rows, pol["family_id"], neg, "bare", "qwen2.5-7b")["text"],
        "chip1_in": out(rows, pol["family_id"], neg, "chip1", "qwen2.5-7b")["input_text"],
        "chip1_out": out(rows, pol["family_id"], neg, "chip1", "qwen2.5-7b")["text"],
        "pz_family": pz["family_id"],
        "pz_src": pz["variants"][plain]["source"],
        "pz_qwen": out(rows, pz["family_id"], plain, "full", "qwen2.5-7b")["text"],
    }
    for m in MODEL_ORDER:
        t = out(rows, pz["family_id"], plain, "full", m)["text"]
        if re.search(r"\bplease\b", t, re.I):
            ex["pz_viol_model"], ex["pz_viol_out"] = m, t
            break
    ex["chip1_in"] = ex["chip1_in"].replace("Keywords: ", "")
    return ex


FIG_W_PT = 6.3 * 72


def tw(text, size):
    """Width (axis units) of monospace text: DejaVu Sans Mono advance = 0.602 em."""
    n = max(len(line) for line in text.split("\n"))
    return n * 0.602 * size / FIG_W_PT


def box(ax, x, y, text, fc, h=0.075, size=7.0, weight="normal", pad=0.022):
    w = tw(text, size) + pad
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=fc, ec="#444444", lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            family="DejaVu Sans Mono", weight=weight)
    return x + w  # right edge


def arrow(ax, x0, y0, x1, y1, label=None):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8,
                                 lw=0.9, color="#444444", shrinkA=2, shrinkB=2))
    if label:
        ax.text((x0 + x1) / 2, max(y0, y1) + 0.016, label, ha="center", va="bottom",
                fontsize=6.3, color="#333333", family="DejaVu Sans", style="italic")


def note(ax, x, y, text, color):
    ax.text(x, y, text, ha="left", va="center", fontsize=6.6, color=color,
            family="DejaVu Sans", linespacing=1.15)


def rowlabel(ax, y, title, sub):
    ax.text(0.01, y + 0.06, title, fontsize=8, family="DejaVu Sans", weight="bold", va="center")
    ax.text(0.01, y - 0.02, sub, fontsize=6.4, family="DejaVu Sans", va="center",
            color="#555555", linespacing=1.15)


def draw(ex):
    SRC, KW, OUTC, OK, BAD = "#eef2f7", "#fff6dc", "#ffffff", "#1b7a3a", "#b3261e"
    fig = plt.figure(figsize=(6.3, 3.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    X0, H = 0.175, 0.075

    # (a) Loss: two sources collide on one keyword string
    y = 0.80
    rowlabel(ax, y, "(a) Loss", "keywords drop\nthe cue")
    ra = box(ax, X0, y + 0.03, "A: " + ex["src_neg"], SRC)
    rb = box(ax, X0, y - 0.075, "B: " + ex["src_aff"], SRC)
    kx = max(ra, rb) + 0.07
    rk = box(ax, kx, y - 0.022, ex["bare"], KW, weight="bold")
    arrow(ax, ra, y + 0.03 + H / 2, kx, y - 0.022 + H * 0.7)
    arrow(ax, rb, y - 0.075 + H / 2, kx, y - 0.022 + H * 0.3)
    note(ax, rk + 0.015, y + 0.015, "identical input for A and B:\nnegation is not recoverable", "#444444")

    # (b) Assumption under bare input, and the one-chip repair
    y = 0.50
    rowlabel(ax, y, "(b) Assumption", "ambiguous input,\ndefinite output")
    r1 = box(ax, X0, y + 0.03, ex["bare"], KW, weight="bold")
    r2 = box(ax, X0, y - 0.075, ex["chip1_in"], KW, weight="bold")
    ox = max(r1, r2) + 0.12
    o1 = box(ax, ox, y + 0.03, ex["bare_out"], OUTC)
    o2 = box(ax, ox, y - 0.075, ex["chip1_out"], OUTC)
    arrow(ax, r1, y + 0.03 + H / 2, ox, y + 0.03 + H / 2, "Qwen2.5-7B, P0")
    arrow(ax, r2, y - 0.075 + H / 2, ox, y - 0.075 + H / 2)
    nx = max(o1, o2) + 0.015
    note(ax, nx, y + 0.03 + H / 2, "affirmative for A and B\n(0 extra actions)", BAD)
    note(ax, nx, y - 0.075 + H / 2, "negated reading\n(+1 chip selection)", OK)

    # (c) Violation: the full typed sentence is given, politeness changes anyway
    y = 0.17
    rowlabel(ax, y, "(c) Violation", "cue present,\nchanged anyway")
    rs = box(ax, X0, y - 0.022, "The user typed:\n" + ex["pz_src"], SRC, h=0.095, size=6.6)
    ox = rs + 0.05
    o1 = box(ax, ox, y + 0.035, ex["pz_viol_out"], OUTC, size=6.6)
    o2 = box(ax, ox, y - 0.075, ex["pz_qwen"], OUTC, size=6.6)
    arrow(ax, rs, y + 0.045, ox, y + 0.035 + H / 2)
    arrow(ax, rs, y + 0.005, ox, y - 0.075 + H / 2)
    nx = max(o1, o2) + 0.01
    note(ax, nx, y + 0.035 + H / 2, MODEL_NAME[ex["pz_viol_model"]] + ":\nadds \u201cplease\u201d", BAD)
    note(ax, nx, y - 0.075 + H / 2, "Qwen2.5-7B:\nkept plain", OK)

    for yy in (0.66, 0.335):
        ax.plot([0.01, 0.99], [yy, yy], color="#cccccc", lw=0.6)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig1_running_example.{ext}", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    ex = select()
    (OUT / "fig1_examples.json").write_text(json.dumps(ex, indent=2, ensure_ascii=False) + "\n")
    draw(ex)
    print(json.dumps(ex, indent=2, ensure_ascii=False))
