"""Round-3 figures, one per claim (reads r3_*.csv / r2_*.csv). Writes analysis/frontier/partner_context/r3_fig*.png"""
import json, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "analysis/frontier/partner_context"
import textwrap
_st = matplotlib.axes.Axes.set_title
matplotlib.axes.Axes.set_title = lambda self, t, **k: _st(self, "\n".join(textwrap.wrap(t, 52)), **k)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
C = {"echo": "#c0504d", "reply": "#e8a33d", "prop": "#2f6f9f", "aff": "#9aa5ad", "unc": "#bdbdbd", "good": "#3b8f5a"}
M = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
def forest(ax, rows, ref=None):
    y = np.arange(len(rows))[::-1]
    for yi, (lab, e, lo, hi, col) in zip(y, rows): ax.plot([lo, hi], [yi, yi], color=col, lw=2); ax.plot(e, yi, "o", color=col)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.axvline(0, color="k", lw=.6)
    for v in (ref or []): ax.axvline(v, color="k", lw=.5, ls=":")
# F1 echo vs propositional
d = pd.read_csv(OUT / "r2_decomp.csv"); d = d[(d.kind == "bare") & d.turn.isin(["Xa", "Xb", "Xc", "0"])]
fig, ax = plt.subplots(figsize=(6.2, 3.3)); w = .38
for i, m in enumerate(M):
    x = d[(d.model == m) & d.turn.isin(["Xa", "Xb", "Xc"])].mean(numeric_only=True); z = d[(d.model == m) & (d.turn == "0")].iloc[0]
    for xx, v, lab in ((i - w / 2, z, "no turn"), (i + w / 2, x, "partner turn")):
        b = 0
        for k, c in (("neg_prop", "prop"), ("neg_echo_only", "echo"), ("neg_reply", "reply")):
            ax.bar(xx, 100 * v[k], w, bottom=b, color=C[c], label={"prop": "propositional negation", "echo": "echo of partner wording", "reply": "agreement reply"}[c] if i == 0 and lab == "partner turn" else None); b += 100 * v[k]
ax.set_xticks(range(4)); ax.set_xticklabels([m.replace("gpt-6.1-", "") for m in M]); ax.set_ylabel("% of outputs written negated\n(user meant an affirmative message)"); ax.legend(frameon=False, fontsize=8)
ax.set_title("Claim 1: most negation after a negative partner remark is echo (left bar no turn, right bar X turn)", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig1_echo_vs_propositional.png"); plt.close()
# F2 C2 forest
c2 = pd.read_csv(OUT / "r3_c2.csv"); c2 = c2[c2.model == "pooled"].set_index("contrast"); au = pd.read_csv(OUT / "r3_author_writer.csv").set_index("estimate"); r2c = pd.read_csv(OUT / "r2_contrasts.csv"); m4 = r2c[(r2c.contrast == "C2 under M4 (background-only instruction) vs 0") & (r2c.model == "pooled")].iloc[0]
g = lambda k: c2.loc[k]
rows = [("all negation incl. echo", g("C2 all negation incl. echo (upper end)"), "echo"), ("propositional (primary)", g("C2 propositional (primary, lower end)"), "prop"),
        ("propositional, Xa+Xc only", g("C2 propositional Xa+Xc ITT"), "prop"), ("propositional, Xa+Xc checker-passing", g("C2 propositional Xa+Xc checker-passing only"), "prop")]
rows = [(a, r.est_pp, r.lo_pp, r.hi_pp, C[c]) for a, r, c in rows]
for lab, k in (("mistral-authored turns (40 shared fams)", "mistral-authored, 40 shared families, family bootstrap"), ("qwen14-authored turns (40 shared fams)", "qwen14-authored, 40 shared families, writer-cluster bootstrap")):
    r = au.loc[k]; rows.append((lab, r.est_pp, r.lo_pp, r.hi_pp, C["prop"]))
rows.append(("propositional with M4 instruction", m4.est_pp, m4.lo_pp, m4.hi_pp, C["prop"]))
fig, ax = plt.subplots(figsize=(6.4, 3.4)); forest(ax, rows); ax.set_xlabel("C2: bare channel, X turn minus no-turn (pp, 95% cluster CI)"); ax.set_title("Claim 2: partner-driven negation is +8.7 pp propositional (+36.7 with echoes)", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig2_c2_range.png"); plt.close()
# F3 C1
c1 = pd.read_csv(OUT / "r3_c1.csv"); c1 = c1[c1.model == "pooled"]
rows = [(lab, r.est_pp, r.lo_pp, r.hi_pp, col) for lab, i, col in (("unfiltered (primary; echo/agreement counted)", 0, C["echo"]), ("filtered, arm 0 unfiltered (lower bound)", 1, C["prop"]), ("filtered, arm 0 filtered (lower bound)", 2, C["prop"])) for r in [c1.iloc[i]]]
fig, ax = plt.subplots(figsize=(7.2, 2.6)); forest(ax, rows, ref=[-5, 5]); ax.axvspan(-2, 2, color="#eee", zorder=0); ax.set_xlabel("C1 (pp): chip supplied, X turn minus no turn"); ax.set_title("Claim 3: a supplied cue leaves 1.2-7.1 pp contamination (grey +-2 original, dotted +-5 widened margin)", fontsize=8); fig.tight_layout(); fig.savefig(OUT / "r3_fig3_c1.png"); plt.close()
# F4 benchmark frontier
p = pd.read_csv(OUT / "r3_policies.csv"); gp = pd.read_csv(OUT / "r3_gate_policies.csv")
fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
lab = {"noctx_arm0": "ignore partner", "commit_M0": "always commit (context)", "instr_M4_bare": "M4 instruction (0 taps)", "ablate_ask_M5b": "M5b ask-if-changed", "random_ask_matched": "random ask, matched taps",
       "word_M1": "plain word*", "chip_always_ask_M2": "chip*", "instr_M4_chip": "M4+chip*", "guard_G1": "chip+G1*"}
d = p[(p.frame == "X") & (p.q == 0.1)].set_index("policy"); ax = axs[0]
for k, l in lab.items():
    r = d.loc[k]; col = C["good"] if k.endswith(("M1", "M2", "G1", "M4_chip")) else C["prop"]; ax.errorbar(r.taps_per1000, r.weighted_all_per1000, yerr=[[r.weighted_all_per1000 - 5 * r.wrong_all_lo], [5 * r.wrong_all_hi - r.weighted_all_per1000]], fmt="o", color=C["echo"] if k == "random_ask_matched" else col, ms=4, lw=1)
    ax.annotate(l, (r.taps_per1000, r.weighted_all_per1000), fontsize=6.5, xytext=(4, 3 if k not in ("noctx_arm0", "chip_always_ask_M2") else -9 if k == "noctx_arm0" else 6), textcoords="offset points")
ax.plot([0, 1000], [d.loc["commit_M0"].weighted_all_per1000, d.loc["chip_always_ask_M2"].weighted_all_per1000], "--", color=C["echo"], lw=.8); ax.set_yscale("log")
ax.set_xlabel("taps per 1,000 messages"); ax.set_ylabel("SLP-weighted wrong polarity per 1,000 (log)"); ax.set_title("X-frame, q=0.10 (* = cue-supplied oracle)", fontsize=8.5)
ax = axs[1]; gm = gp[(gp.scope == "mixed X+D+Q") & (gp.q == 0.1) & (gp.outcome == "wrong_all")]
for _, r in gm.iterrows():
    ax.errorbar(r.taps_per1000, r.weighted_per1000, yerr=[[r.weighted_per1000 - 5 * r.lo], [5 * r.hi - r.weighted_per1000]], fmt="o", ms=4, color=C["echo"] if "random" in r.policy else C["prop"]); ax.annotate(r.policy.split(" (")[0].replace("_", " ") + (" (frame-aware)" if "aware" in r.policy else (" (frame-blind)" if "blind" in r.policy else "")), (r.taps_per1000, r.weighted_per1000), fontsize=6.5, xytext=(4, 3), textcoords="offset points")
ax.set_xlabel("taps per 1,000 messages"); ax.set_title("Mixed stream X+D+Q, q=0.10: negation gate", fontsize=8.5); fig.suptitle("Claim 4: zero-tap fixes do not beat matched-tap random ask; * rows are oracle upper bounds", fontsize=9); fig.tight_layout(); fig.savefig(OUT / "r3_fig4_benchmarks.png"); plt.close()
# F5 label robustness
lr = pd.read_csv(OUT / "r3_label_robustness.csv"); lr = lr[lr.model == "pooled"]
rows = []
for k, nm in (("critical", "final labels"), ("critical_J1", "judge J1 only"), ("critical_J2", "judge J2 only")):
    r = lr[lr.contrast == f"C2 all negation, labels = {k}"].iloc[0]; rows.append((nm, r.est_pp, r.lo_pp, r.hi_pp, C["prop"]))
fig, ax = plt.subplots(figsize=(5.6, 2.2)); forest(ax, rows); ax.set_xlabel("C2 all-negation, pooled (pp)"); ax.set_title("Claim 5: polarity labels are robust to the judge choice", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig5_label_robustness.png"); plt.close()
# F6 C3
ab = pd.read_csv(OUT / "r3_c3_abstention.csv"); fig, ax = plt.subplots(figsize=(6, 3)); w = .38
for i, m in enumerate(M):
    for xx, t in ((i - w / 2, "0"), (i + w / 2, "Q")):
        r = ab[(ab.model == m) & (ab.turn == t)].iloc[0]; b = 0
        for k, c, l in (("affirmative", "aff", "affirmative"), ("negated", "echo", "negated"), ("abstain", "unc", "abstained (unclear/mixed)")):
            ax.bar(xx, 100 * r[k], w, bottom=b, color=C[c], label=l if i == 0 and t == "Q" else None); b += 100 * r[k]
ax.set_ylim(70, 100.5); ax.set_xticks(range(4)); ax.set_xticklabels([m.replace("gpt-6.1-", "") for m in M]); ax.set_ylabel("% of outputs"); ax.legend(frameon=False, fontsize=7, loc="lower left"); ax.set_title("Claim 6: a question frame lowers the affirmative share via abstention (left no turn, right Q)", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig6_c3_abstention.png"); plt.close()
# F7 decomposition
D = pd.read_csv(OUT / "r3_decomp_units_labelled.csv"); D["c"] = D.cls.replace({"UNRESOLVED->PARAPHRASE": "PARAPHRASE (incl. unresolved)", "PARAPHRASE": "PARAPHRASE (incl. unresolved)"})
fig, ax = plt.subplots(figsize=(6.4, 3)); cols = {"PARAPHRASE (incl. unresolved)": C["echo"], "FABRICATION": C["reply"], "INDEPENDENT": C["prop"]}
groups = [("propositional_negation", t) for t in ("Xa", "Xb", "Xc")] + [("propositional_negation", None), ("affirmative_control", None)]
for i, (gname, t) in enumerate(groups):
    s = D[D.group == gname]; s = s[s.turn_type == t] if t else s; sh = s.c.value_counts(normalize=True); b = 0
    for k in cols: ax.bar(i, 100 * sh.get(k, 0), .6, bottom=b, color=cols[k], label=k if i == 0 else None); b += 100 * sh.get(k, 0)
    ax.text(i, 101, f"n={len(s)}", ha="center", fontsize=7)
ax.set_xticks(range(5)); ax.set_xticklabels(["negations Xa", "negations Xb", "negations Xc", "all negations", "affirmative\ncontrol"]); ax.set_ylabel("%"); ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(.5, -.18), ncol=3); ax.set_title("Claim 2b: half of the propositional negations still paraphrase the partner", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig7_decomposition.png"); plt.close()
# F8 G1 vs chip label sources
g1 = pd.read_csv(OUT / "r3_g1_vs_chip_label_sources.csv"); g1 = g1[g1.q == 0.1]
rows = [({"final": "final labels", "J1": "J1 only", "J2": "J2 only", "claude_blind_on_changed": "Claude blind (changed texts)"}[r.label_scheme], r.g1_minus_chip_per1000, r.lo, r.hi, C["good"]) for r in g1.itertuples()]
fig, ax = plt.subplots(figsize=(5.8, 2.4)); forest(ax, rows); ax.set_xlabel("G1 minus chip, wrong polarity per 1,000 X messages (q=0.10)"); ax.set_title("Claim 4b: G1 gain over the chip holds with Claude-only labels but halves in size", fontsize=8.5); fig.tight_layout(); fig.savefig(OUT / "r3_fig8_g1_label_sources.png"); plt.close()
print("ok")
