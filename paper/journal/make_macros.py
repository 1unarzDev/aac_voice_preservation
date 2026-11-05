#!/usr/bin/env python3
"""Generate results_macros.tex (+ macro_sources.json) for the TACCESS journal manuscript.

Every number in main.tex is a \\jm... macro defined here. Each macro is read from a stored
analysis file (read-only); the source path is recorded in macro_sources.json. Missing inputs
never crash the script: the macro is simply left undefined and main.tex shows \\pending{key}
via \\jmv{key}. Typed values are limited to design constants (marked DESIGN in the sources).

Usage (repo root):  . .venv/bin/activate && python paper/journal/make_macros.py
Slots for pending work (Stage 5 Parts 20-25; intent-coverage pilot) are read from the files
listed in SLOTS below if they exist; until then they are undefined and render as pending.
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
A = ROOT / "analysis"
macros: dict[str, str] = {}
sources: dict[str, str] = {}
DIG = "Zero One Two Three Four Five Six Seven Eight Nine".split()


def tname(key: str) -> str:
    out = []
    for ch in key:
        if ch.isdigit():
            out.append(DIG[int(ch)])
        elif ch.isalpha():
            out.append(ch)
        elif ch in "_.-":
            out.append("X")
    return "jm" + "".join(out)


def put(key, val, src, fmt="pct"):
    if val is None or (isinstance(val, float) and val != val):
        return
    f = {"pct": lambda v: f"{100*v:.1f}", "pp": lambda v: f"{100*v:+.1f}".replace("-", "$-$"),
         "int": lambda v: f"{int(round(v)):,}", "f2": lambda v: f"{v:.2f}", "f3": lambda v: f"{v:.3f}".lstrip("0"),
         "f1": lambda v: f"{v:.1f}", "raw1": lambda v: f"{v:.1f}", "s": str}[fmt]
    macros[key] = f(val)
    sources[key] = src


def ci(key, est, lo, hi, src, fmt="pct"):
    put(key, est, src, fmt); put(key + "Lo", lo, src, fmt); put(key + "Hi", hi, src, fmt)


def J(path):
    p = ROOT / path
    return json.loads(p.read_text()) if p.exists() else None


def safe(fn):
    try:
        fn()
    except Exception as e:  # never crash: keys stay undefined
        print(f"[warn] {fn.__name__}: {type(e).__name__}: {e}", file=sys.stderr)


# --------------------------------------------------------------- Part 17 repair audit
def part17():
    p = "analysis/repair_audit_v2/summary.json"; d = J(p)
    pa = d["per_arm"]
    for arm, k in [("repaired", "Rep"), ("control", "Ctl")]:
        for fld, n in [("usable", "Usable"), ("preserving", "Pres"), ("added_stance", "Stance")]:
            x = pa[arm][fld]; ci(f"p17{k}{n}", x["p"], *x["ci"], p)
            put(f"p17{k}{n}K", x["k"], p, "int"); put(f"p17{k}{n}N", x["n"], p, "int")
    for fld, n in [("usable", "Usable"), ("preserving", "Pres"), ("usable_and_preserving", "UsPres"),
                   ("usable_or_minor", "UsMinor"), ("added_stance", "Stance")]:
        x = d["difference_repaired_minus_control"][fld]; ci(f"p17Diff{n}", x["diff"], *x["ci"], p, "pp")
    sec = d["secondary"]["original_failed"]["paired"]
    for fld, n in [("usable", "Usable"), ("preserving", "Pres"), ("added_stance", "Stance")]:
        x = sec[fld]; ci(f"p17Orig{n}", x["diff"], *x["ci"], p + " secondary.original_failed.paired", "pp")
        put(f"p17Orig{n}P", x["sign_test_p"], p + " secondary.original_failed.paired sign_test_p", "f3")
        put(f"p17Orig{n}Pairs", x["n_pairs"], p, "int")
    put("p17Raters", len(d["annotators"]), p, "int")
    put("p17ItemsPerArm", pa["repaired"]["items"], p, "int")
    for m in ["gemma3-4b"]:
        x = d["by_model_descriptive"].get(f"repaired/{m}", {}).get("usable")
        if x: put("p17GemmaUsable", x["p"], p + f" by_model_descriptive repaired/{m}"); put("p17GemmaUsableK", x["k"], p, "int"); put("p17GemmaUsableN", x["n"], p, "int")


# --------------------------------------------------------------- Part 18 intent
def part18():
    p = "analysis/intent_check/summary.json"; d = J(p)
    for k, n in [("chip1", "Chip"), ("bare", "Bare"), ("all", "All")]:
        x = d["match_rate"][k]; ci(f"p18Match{n}", x["p"], *x["ci"], p)
    x = d["match_rate_chip1_minus_bare"]; ci("p18CueGain", x["diff"], *x["writer_cluster_ci"], p, "pp")
    a = d["acceptability"]["all"]
    ci("p18AcceptYes", a["yes"]["p"], *a["yes"]["ci"], p); put("p18AcceptYesK", a["yes"]["k"], p, "int"); put("p18AcceptN", a["yes"]["n"], p, "int")
    put("p18AcceptNo", a["no"]["p"], p); put("p18AcceptYesSmall", a["yes_or_small_edit"]["p"], p)
    put("p18Kappa", d["agreement"]["all"]["q1_four_labels"]["kappa"], p, "f2")
    put("p18Writers", len(d["writers"]), p, "int")
    w = J("analysis/whole_message/summary.json"); q = "analysis/whole_message/summary.json"
    p18 = w["part18"]
    put("wmRejectDiff", None, q)
    rr = w["key_question"]["judge critical RIGHT"]
    put("wmRightN", rr["n"], q, "int"); put("wmRightR1K", rr["R1"][0], q, "int"); put("wmRightR1N", rr["R1"][1], q, "int")
    put("wmRightR1", rr["R1"][0] / rr["R1"][1], q)
    reas = w["key_question"]["reason_right_not_accepted"]; tot = sum(reas.values())
    put("wmRightSubst", reas["substitution"] / tot, q); put("wmRightDropped", reas["dropped"] / tot, q)
    put("wmRightNotAccN", tot, q, "int")
    fl = w["key_question"]["right_not_accepted_flags"]
    put("wmDroppedUnrec", J("analysis/whole_message/summary.json") and None, q)
    # share of non-accepted writer sentences with words absent from the keywords: from the report table (flags)
    txt = (ROOT / "analysis/whole_message/report.md").read_text()
    m = re.search(r"\| all \| 199 \| [\d%]+ \| [\d%]+ \| [\d%]+ \| [\d%]+ \| (\d+)% \| (\d+)%", txt)
    if m: macros["wmDroppedUnrecShare"] = m.group(2); sources["wmDroppedUnrecShare"] = "analysis/whole_message/report.md 1b multi-label flags (all)"
    put("wmAdded", p18["reason_all"]["added"] / sum(p18["reason_all"].values()), q)
    put("wmHandKappa", w["hand_check"]["kappa"], q, "f2"); put("wmHandN", w["hand_check"]["n"], q, "int")
    put("slpJudgeKappaOne", w["slp"]["kappa_SLP1"], q, "f2"); put("slpJudgeKappaTwo", w["slp"]["kappa_SLP2"], q, "f2")


# --------------------------------------------------------------- Part 19 arbiter
def part19():
    p = "analysis/arbiter_check/summary.json"; d = J(p)
    for k, n in [("arbiter", "Arb"), ("J1", "JOne"), ("J2", "JTwo")]:
        x = d[f"human_vs_{k}"]; ci(f"p19Agree{n}", x["per_coding"]["p"], x["per_coding"]["ci"][0], x["per_coding"]["ci"][1], p)
        put(f"p19Kappa{n}", x["kappa"], p, "f2")
    put("p19Codings", d["human_vs_arbiter"]["per_coding"]["n"], p, "int")
    cy = d["can_you"]["per_coding_share"]["request/command"]
    ci("p19CanYouRequest", cy["p"], *cy["ci"], p); put("p19CanYouK", cy["k"], p, "int"); put("p19CanYouN", cy["n"], p, "int")


# --------------------------------------------------------------- SLP panel (runs the scorer into tmp/)
def slp():
    tmp = ROOT / "tmp"; tmp.mkdir(exist_ok=True); out = tmp / "slp_report_journal.md"
    subprocess.run([sys.executable, str(ROOT / "src/score_slp_panel.py"), "--out", str(out)], check=True, capture_output=True, cwd=ROOT)
    t = out.read_text(); out.unlink(); s = "src/score_slp_panel.py -> expert_package/returns_slp (n=2 raters)"
    m = re.search(r"\| negation dropped/added \| ([\d.]+) .*? \| (\d+) \| (\d+) \|", t)
    if m: put("slpNegSeverity", float(m.group(1)), s, "f1"); put("slpNegBlock", float(m.group(3)) / 100, s)
    def row(pop, arm):
        mm = re.search(rf"\| {re.escape(pop)}[^|]*\| {arm} \| \d+ \| ([\d.]+) \| ([\d.]+) \|", t); return mm
    for key, pop, arm in [("GuardBase", "W-C speech-act", "baseline_P0"), ("GuardG", "W-C speech-act", "guard_G1"),
                          ("CueBare", "hw1", "baseline_bare"), ("CueChip", "hw1", "chip"), ("CueWord", "hw1", "word")]:
        mm = row(pop, arm)
        if mm: put("slpW" + key, float(mm.group(2)) / 100, s); put("slpU" + key, float(mm.group(1)) / 100, s)
    for key, arm in [("Repair", "guard_repair"), ("Orig", "guard_original"), ("Chip", "chip"), ("Word", "word")]:
        mm = re.search(rf"\| {arm} \| (\d+) \| [\d /]+ \| [\d /]+ \| (\d+) \| (\d+) \| (\d+) \|", t)
        if mm: put("slpAcc" + key, int(mm.group(3)) / 100, s); put("slpAcc" + key + "N", int(mm.group(1)), s, "int")


# --------------------------------------------------------------- hw1 replication, legend, controls, breadth
def hw1():
    p = "analysis/hw1/summary.json"; d = J(p)
    for k, n in [("P1", "ChipGain"), ("P2", "PolGain"), ("P3", "AffShare")]:
        x = d["primary"][k]["writer"]; ci("hw" + n, x["estimate"], x["ci_low"], x["ci_high"], p)
        put("hw" + n + "Writers", x["n_clusters"], p, "int"); put("hw" + n + "Families", x["n_families"], p, "int")
    put("hwFamilies", d["n_analysed_families"], p, "int")
    pol = d["P3_affirmative_share"]; put("hwAffAll", pol["estimate"], p)
    lg = J("analysis/legend_test/summary.json"); q = "analysis/legend_test/summary.json"
    put("legendNoLegend", lg["pooled_d1"]["b_nolegend"]["aff"], q) if "aff" in lg["pooled_d1"]["b_nolegend"] else None
    # reuse CSV for no-legend pooled
    df = pd.read_csv(ROOT / "analysis/legend_test/arm_share.csv")
    r = df[(df.draw == "d1") & (df.source == "pooled") & (df.arm == "b_nolegend") & (df.model == "ALL")].iloc[0]
    ci("legendNoLegendAff", r.aff, r.aff_lo, r.aff_hi, "analysis/legend_test/arm_share.csv")
    r = df[(df.draw == "d1") & (df.source == "pooled") & (df.arm == "a_legend") & (df.model == "ALL")].iloc[0]
    ci("legendAff", r.aff, r.aff_lo, r.aff_hi, "analysis/legend_test/arm_share.csv")
    cc = J("analysis/chip_controls/summary.json"); q = "analysis/chip_controls/summary.json"
    for dim, n in [("agent", "Agent"), ("certainty", "Cert"), ("polarity", "Pol")]:
        x = cc["decision_by_dimension"].get(dim)
        if x: put(f"ctlIrrel{n}", x["chip1_minus_irrel"], q, "pp")
    mb = J("analysis/model_breadth/summary.json"); q = "analysis/model_breadth/summary.json"
    put("breadthModels", len(mb["models"]), q, "int")
    put("breadthMinAff", min(v["bare_affirmative_share"] for v in mb["checks"].values()), q)
    put("breadthPolChipMin", min(v["per_dimension"]["polarity"]["chip_over_noncrit_pp"] for v in mb["checks"].values()) / 100, q, "pp")
    put("breadthSpeechChipMin", min(v["speech_act_chip_contrast_pp"] for v in mb["checks"].values()) / 100, q, "pp")
    put("breadthSpeechChipMax", max(v["speech_act_chip_contrast_pp"] for v in mb["checks"].values()) / 100, q, "pp")


# --------------------------------------------------------------- guard, default profiles, ask policies
def guard():
    p = "analysis/guard_wc/headline.json"; d = J(p)
    a = d["arms"]
    ci("gtJointG", a["G1"]["joint_pass"]["estimate"], a["G1"]["joint_pass"]["ci_low"], a["G1"]["joint_pass"]["ci_high"], p)
    put("gtTargets", d["n_targets"], p, "int"); put("gtFamilies", d["n_families"], p, "int")
    for k in a["G1"]:
        pass
    # P0 baseline joint
    if "P0" in a: ci("gtJointP", a["P0"]["joint_pass"]["estimate"], a["P0"]["joint_pass"]["ci_low"], a["P0"]["joint_pass"]["ci_high"], p)


def f1():
    base = "analysis/frontier/default_profiles/followup/"
    pr = pd.read_csv(ROOT / base / "f1_price.csv"); pr = pr[pr["mode"] == "arb"]
    names = {"polarity": "Pol", "politeness": "Polite", "speech_act": "Act"}
    for _, r in pr.iterrows():
        arm = {"bare": "Bare", "chip": "Chip", "word": "Word", "chipG1": "ChipG"}[r.arm]
        ci(f"f1Rev{names[r.dimension]}{arm}", r.rev_per_1000, r.lo, r.hi, base + "f1_price.csv", "f1")
    rs = pd.read_csv(ROOT / base / "f1_restoration.csv")
    rs = rs[(rs.model == "pooled(mode=arb)") & (rs.dimension == "speech_act")]
    for _, r in rs.iterrows():
        arm = {"bare": "Bare", "chip": "Chip", "word": "Word", "chipG1": "ChipG"}[r.arm]
        ci(f"f1ActRestore{arm}", r.r, r.lo, r.hi, base + "f1_restoration.csv")
    s = J(base + "f1_summary.json"); put("f1Units", sum(s["units"].values()), base + "f1_summary.json", "int")
    dp = "analysis/frontier/default_profiles/"
    pc = pd.read_csv(ROOT / dp / "intervention_same_items_r3.csv")
    r = pc[(pc.dimension == "polarity") & (pc.strategy == "always-commit")].iloc[0]
    ci("dpAlwaysCommitPol", r.reversals_per_1000, r.lo, r.hi, dp + "intervention_same_items_r3.csv", "f1")
    # ask policies: reversals at 5% taps, prior-ranked vs random gated (polarity), for the frontier figure caption
    for key, nm in [("Prior", "prior_cv_refit"), ("Rand", "random_gated")]:
        m = pc[(pc.dimension == "polarity") & pc.strategy.str.startswith(f"ask policy {nm}, 10%")]
        if len(m): ci(f"dpAsk{key}Pol", m.iloc[0].reversals_per_1000, m.iloc[0].lo, m.iloc[0].hi, dp + "intervention_same_items_r3.csv", "f1")
    cl = pd.read_csv(ROOT / dp / "followup/clam_contrasts.csv")
    m = cl[(cl.dimension == "polarity") & (cl.name == "clam_mean_gated")]
    if len(m): ci("clamPol", m.iloc[0].rev_per_1000, m.iloc[0].lo, m.iloc[0].hi, dp + "followup/clam_contrasts.csv", "f1")
    wt = pd.read_csv(ROOT / dp / "slp_weighted_price_h2.csv"); wt = wt[wt.scheme == "mean"]
    for _, r in wt.iterrows():
        put("w" + names[r.dimension], r.weight, dp + "slp_weighted_price_h2.csv", "f2")
        put("wShare" + names[r.dimension], r.share_weighted, dp + "slp_weighted_price_h2.csv")


# --------------------------------------------------------------- section 5 (discussion) extras
def s5_discussion():
    q = "analysis/robust/t2_posterior/tables.csv"
    t = pd.read_csv(ROOT / q); r = t[(t.dimension == "polarity") & (t.channel == "human")].iloc[0]
    ci("t2NegBase", r.posterior_empirical, r.posterior_empirical_lo, r.posterior_empirical_hi, q)
    q = "analysis/model_breadth/summary.json"; mb = J(q)
    fam = {re.match(r"[a-z]+", m).group(0) for m in mb["models"]}
    put("breadthFamilies", len(fam), q + " (distinct model-name stems)", "int")
    q = "analysis/frontier/default_profiles/mde_r3.csv"; m = pd.read_csv(ROOT / q)
    m = m[(m.dimension == "polarity") & (m.a == "prior_cv_refit") & (m.b == "random_gated")].iloc[0]
    put("dpMdePol", m.mde_per_1000, q, "f1")
    q = "analysis/guard_wc/headline.json"; d = J(q)
    ci("gtStripJoint", d["arms"]["G1s"]["joint_pass"]["estimate"], d["arms"]["G1s"]["joint_pass"]["ci_low"], d["arms"]["G1s"]["joint_pass"]["ci_high"], q)
    # DESIGN constants: numbers of expert reviewers (design of the expert packages, expert_package/)
    for k, v in [("designSlp", 2), ("designConsultants", 2), ("designRatersPerItem", 3), ("designDims", 7)]:
        macros[k] = str(v); sources[k] = "DESIGN: expert_package/ (two SLP raters; two consultants C01, C02); annotation/COORDINATOR_STEPS.md 4 (three raters per item); seven-dimension commitment vector"



# --------------------------------------------------------------- Section 1 additions (introduction example and counts)
def s1():
    q = "analysis/hw1/examples.md"; t = (ROOT / q).read_text()
    blk = t.split("## polarity")[1].split("## speech_act")[0]
    fam = re.search(r"Family `(hw-pol-\d+)` \(writer (P\d+)\); first of (\d+) qualifying families", blk)
    r = re.search(r"occur at ([\d.]+) \[([\d.]+), ([\d.]+)\]% of bare rows \(n=(\d+), (\d+) writers\); when they do, the chip1 output matches the target ([\d.]+) \[([\d.]+), ([\d.]+)\]% of the time \(n=(\d+)\)", blk)
    s = q + " ## polarity (declared hash rule)"
    for k, v, f in [("exPolWrong", r.group(1), "s"), ("exPolWrongLo", r.group(2), "s"), ("exPolWrongHi", r.group(3), "s"),
                    ("exPolWrongN", r.group(4), "s"), ("exPolWriters", r.group(5), "s"), ("exPolChipMatch", r.group(6), "s"),
                    ("exPolChipMatchLo", r.group(7), "s"), ("exPolChipMatchHi", r.group(8), "s"), ("exPolChipMatchN", r.group(9), "s"),
                    ("exPolFamilies", fam.group(3), "s")]:
        macros[k] = v; sources[k] = s
    w = J("analysis/whole_message/summary.json"); p = "analysis/whole_message/summary.json"
    rr = w["key_question"]["judge critical RIGHT"]
    put("wmRightIntendedK", rr["R1"][1] - rr["R1"][0], p, "int")
    put("wmRightIntendedN", rr["R1"][1], p, "int")
    d = J("analysis/arbiter_check/summary.json")
    put("p19JOneN", d["human_vs_J1"]["per_coding"]["n"], "analysis/arbiter_check/summary.json", "int")
    sp = None
    b = J("analysis/model_breadth/summary.json")
    put("breadthFamilies", len({re.match(r"[a-z]+", m).group(0) for m in b["models"]}), "analysis/model_breadth/summary.json (distinct leading family names: qwen, llama, gemma, gpt, mistral)", "int")

# --------------------------------------------------------------- section 3 (studies and results I)
def s3():
    """Macros for paper/journal/sections/s3.tex: base rates, legend, controls, breadth, same-items, asks, guard, SLP extras."""
    def sgn(v):
        s_ = f"{v:.1f}"  # plain minus: sections wrap these in $...$
        return "0.0" if s_ == "-0.0" else s_
    D3 = {"polarity": "Pol", "politeness": "Polite", "speech_act": "Act"}
    DIM6 = {"agent": "Agent", "certainty": "Cert", "polarity": "Pol", "politeness": "Polite", "speech_act": "Act", "time_quantity": "Time"}
    # ---- human base rates (T2 posterior; detector source labels)
    p = "analysis/robust/t2_posterior/summary.json"; d = J(p)
    rows = {(r["dimension"], r["channel"]): r for r in d["table"]}
    for dim, n in D3.items():
        r = rows[(dim, "human")]
        ci(f"t2Post{n}", r["posterior_empirical"], r["posterior_empirical_lo"], r["posterior_empirical_hi"], p)
        ci(f"t2Rev{n}", r["silent_reversal_per_1000"], r["silent_reversal_per_1000_lo"], r["silent_reversal_per_1000_hi"], p, "f1")
        ci(f"t2Dropped{n}", r["d_loss"], r["d_loss_lo"], r["d_loss_hi"], p)
        put(f"t2ModelCue{n}", r["model_share_cue_given_nocue"], p)
        put(f"t2Spur{n}", r["spurious_cue_per_1000"], p, "f1")
        put(f"t2Break{n}", r["breakeven_cost_ratio"], p, "f1")
        put(f"t2Queries{n}", r["queries_per_catch"], p, "f1")
        put(f"t2Prev{n}", r["pi_frame"], p)
    pol = rows[("polarity", "human")]
    put("t2AffGivenNoNeg", 1 - pol["model_share_cue_given_nocue"], p)
    put("t2PostBayesPol", pol["posterior_bayes_corpus_pi"], p)
    put("t2Units", pol["n_units"], p, "int"); put("t2Messages", pol["n_messages"], p, "int")
    put("t2CorpusNeg", d["corpus_prevalence_detector_6142"]["neg"], p)
    m = re.search(r"corpus_prevalence_detector_(\d+)", " ".join(d.keys()))
    if m: macros["t2Corpus"] = f"{int(m.group(1)):,}"; sources["t2Corpus"] = p + " (key name)"
    put("t2PolRandHalf", d["random_half_check"]["random_half_polarity_human"]["posterior_no_negation_word"], p)
    put("t2HwAffShare", d["hw1_P3_affirmative_share"]["estimate"], p)
    # ---- legend test
    q = "analysis/legend_test/summary.json"; lg = J(q); pd1 = lg["pooled_d1"]
    ci("legC", pd1["c_markers_missing"]["aff"], pd1["c_markers_missing"]["lo"], pd1["c_markers_missing"]["hi"], q)
    for k, n in [("a_legend", "A"), ("b_nolegend", "B"), ("c_markers_missing", "C")]:
        put(f"leg{n}N", pd1[k]["n"], q, "int"); put(f"leg{n}Commit", pd1[k]["commit"], q)
    put("legDrawTwoA", lg["d2_pooled"]["a_legend"], q); put("legDrawTwoB", lg["d2_pooled"]["b_nolegend"], q); put("legDrawTwoC", lg["d2_pooled"]["c_markers_missing"], q)
    ad = pd.read_csv(ROOT / "analysis/legend_test/arm_diff.csv"); ad = ad[(ad.draw == "d1") & (ad.source == "pooled") & (ad.model == "ALL") & (ad.metric == "aff")]
    for _, r in ad.iterrows():
        n = {"b_nolegend - a_legend": "BminusA", "c_markers_missing - a_legend": "CminusA"}.get(r.contrast)
        if n: ci("leg" + n, r.estimate, r.ci_low, r.ci_high, "analysis/legend_test/arm_diff.csv", "pp")
    af = pd.read_csv(ROOT / "analysis/legend_test/arm_share.csv"); af = af[(af.draw == "d1") & (af.source == "pooled") & (af.arm == "a_legend") & (af.model == "ALL")].iloc[0]
    put("legFamilies", af["n_families"], "analysis/legend_test/arm_share.csv", "int")
    pm = lg["per_model_class_d1"]
    put("legMinModelNoLegend", min(v["b_nolegend"]["aff"] for v in pm.values()), q)
    # ---- cue-content controls (hw1; writer-cluster CIs)
    cp = "analysis/chip_controls/chip_controls.csv"
    cc = pd.read_csv(ROOT / cp); cc = cc[(cc.set == "all_kept") & (cc.model == "ALL")]
    for dim, n in DIM6.items():
        for pre, nm in [("G_chip", "G"), ("G_irrel", "IrrelAdd"), ("chip1-irrel", "OverIrrel"), ("chip1-nlcue", "OverWord")]:
            r = cc[(cc.dimension == dim) & cc.contrast.str.startswith(pre)]
            if len(r): r = r.iloc[0]; ci(f"ctl{nm}{n}", r.estimate, r.writer_lo, r.writer_hi, cp, "pp")
    hs = pd.read_csv(ROOT / "analysis/hw1/six_dim_rates.csv"); hs = hs[(hs.model == "ALL") & (hs.metric == "critical_match")]
    for dim, n in DIM6.items():
        for ch, nm in [("bare", "Bare"), ("chip1", "Chip"), ("full", "Full")]:
            r = hs[(hs.dimension == dim) & (hs.channel == ch)]
            if len(r): r = r.iloc[0]; ci(f"hwMatch{nm}{n}", r.estimate, r.ci_low, r.ci_high, "analysis/hw1/six_dim_rates.csv")
    put("hwWritersTotal", J("analysis/model_breadth/summary.json")["meta"]["hw_writers"], "analysis/model_breadth/summary.json", "int")
    # ---- declared-rule examples (analysis/hw1/examples.md): rate each example represents
    hp = "analysis/hw1/summary.json"; ex = J(hp)["examples"]
    for dim, n in [("polarity", "Pol"), ("speech_act", "Act"), ("politeness", "Polite")]:
        e = ex[dim]; x = e["bare_wrong_committed_rate"]; ci(f"ex{n}BareWrong", x["estimate"], x["ci_low"], x["ci_high"], hp + f" examples.{dim}")
        x = e["repair_rate_given_bare_wrong"]; ci(f"ex{n}Repair", x["estimate"], x["ci_low"], x["ci_high"], hp + f" examples.{dim}")
        put(f"ex{n}RepairN", x["n"], hp, "int"); put(f"ex{n}Families", e["n_qualifying_families"], hp, "int")
    # ---- conventions and Part 17 by-model rows
    h1 = J("analysis/hw1/summary.json"); put("convBoot", h1["n_boot"], "analysis/hw1/summary.json", "int"); macros["convSeed"] = str(h1["seed"]); sources["convSeed"] = "analysis/hw1/summary.json"
    put("convBootF1", J("analysis/frontier/default_profiles/followup/f1_summary.json")["boot"], "analysis/frontier/default_profiles/followup/f1_summary.json", "int")
    macros["convSeedF1"] = str(J("analysis/frontier/default_profiles/followup/f1_summary.json")["seed"]); sources["convSeedF1"] = "analysis/frontier/default_profiles/followup/f1_summary.json"
    put("p17PerItem", 3, "annotation/COORDINATOR_STEPS.md section 4b (DESIGN: 3 raters per item)", "int")
    a17 = J("analysis/repair_audit_v2/summary.json")
    put("p17OrigItems", a17["per_arm"]["original_failed"]["items"], "analysis/repair_audit_v2/summary.json", "int") if "original_failed" in a17["per_arm"] else None
    for m, n in [("gemma3-4b", "Gemma"), ("gpt-6.1-terra", "Terra"), ("llama3.1-8b", "Llama"), ("qwen2.5-7b", "QwenS")]:
        x = a17["by_model_descriptive"].get(f"repaired/{m}", {}).get("usable")
        if x: put(f"p17Rep{n}Usable", x["p"], "analysis/repair_audit_v2/summary.json by_model_descriptive"); put(f"p17Rep{n}UsableK", x["k"], "analysis/repair_audit_v2/summary.json", "int"); put(f"p17Rep{n}UsableN", x["n"], "analysis/repair_audit_v2/summary.json", "int")
    # ---- model breadth
    q = "analysis/model_breadth/summary.json"; mb = J(q); ck = mb["checks"]
    fam = {"qwen2.5-7b": "Qwen", "qwen2.5-14b": "Qwen", "llama3.1-8b": "Llama", "gemma3-4b": "Gemma", "gpt-6.1-terra": "GPT", "mistral-nemo-12b": "Mistral"}  # DESIGN: family of each model
    put("breadthFamilies", len(set(fam[m] for m in mb["models"])), q + " (families: DESIGN map)", "int")
    tag = {"qwen2.5-7b": "QwenS", "qwen2.5-14b": "QwenL", "llama3.1-8b": "Llama", "gemma3-4b": "Gemma", "gpt-6.1-terra": "Terra", "mistral-nemo-12b": "Nemo"}
    for m, t in tag.items():
        c = ck[m]
        put(f"bm{t}Bare", c["bare_affirmative_share"], q); put(f"bm{t}NoLeg", c["legend_arms_d1"]["b_nolegend"], q)
        put(f"bm{t}PolGain", c["per_dimension"]["polarity"]["chip_over_noncrit_pp"] / 100, q, "pp")
        put(f"bm{t}ActGain", c["speech_act_chip_contrast_pp"] / 100, q, "pp")
        put(f"bm{t}ActWord", -c["per_dimension"]["speech_act"]["chip_over_word_pp"] / 100, q, "pp")  # word minus chip
    put("breadthOrigModels", len(mb["models"]) - len(mb["new_models"]), q, "int")
    cells = [(m, dm) for m in ck for dm in ck[m]["per_dimension"]]
    put("bmCells", len(cells), q, "int")
    put("bmIrrelCells", sum(ck[m]["per_dimension"][dm]["irrel_lo_gt0"] for m, dm in cells), q, "int")
    put("bmWordEqCells", sum(ck[m]["per_dimension"][dm]["word_equals_chip_within5"] for m, dm in cells), q, "int")
    put("bmMinLegendArm", min(min(ck[m]["legend_arms_d1"].values()) for m in ck), q)
    fc = pd.read_csv(ROOT / "analysis/model_breadth/full_channel_critical_match.csv"); fc = fc[fc.model.isin(tag)]
    put("bmFullMin", fc.estimate.min(), "analysis/model_breadth/full_channel_critical_match.csv")
    g = J("analysis/model_breadth/gemini_summary.json"); q = "analysis/model_breadth/gemini_summary.json"
    gl = g["legend_pooled_sources"]["gemini-3.1-flash-lite"]
    put("gemA", gl["a_aff"], q); put("gemC", gl["c_aff"], q); put("gemN", gl["n_a"], q, "int"); put("gemCommit", gl["a_commit"], q)
    # ---- same-items restoration (F1), all three dimensions
    base = "analysis/frontier/default_profiles/followup/"
    rs = pd.read_csv(ROOT / base / "f1_restoration.csv"); rs = rs[rs.model == "pooled(mode=arb)"]
    for _, r in rs.iterrows():
        arm = {"bare": "Bare", "chip": "Chip", "word": "Word", "chipG1": "ChipG"}[r.arm]
        ci(f"f1Rest{D3[r.dimension]}{arm}", r.r, r.lo, r.hi, base + "f1_restoration.csv")
        put(f"f1Units{D3[r.dimension]}", r.n_units, base + "f1_restoration.csv", "int")
    dc = pd.read_csv(ROOT / base / "f1_decisions.csv"); dc = dc[dc["mode"] == "arb"]
    for _, r in dc.iterrows():
        n = D3[r.dimension]
        put(f"f1ChipMinusWord{n}", r.chip_minus_word, base + "f1_decisions.csv", "pp")
        lo, hi = eval(r.c95.replace("np.float64", "")); put(f"f1ChipMinusWord{n}Lo", lo, base + "f1_decisions.csv", "pp"); put(f"f1ChipMinusWord{n}Hi", hi, base + "f1_decisions.csv", "pp")
        lo, hi = eval(r.g1_ci.replace("np.float64", "")); ci(f"f1GuardGain{n}", r.g1_minus_chip, lo, hi, base + "f1_decisions.csv", "pp")
        macros[f"f1Decision{n}"] = r.D1.split(" (")[0]; sources[f"f1Decision{n}"] = base + "f1_decisions.csv (D1 label)"
    s = J(base + "f1_summary.json")
    put("f1Models", 3, base + "f1_summary.json (DESIGN: terra, qwen2.5-7b, llama3.1-8b)", "int")
    put("f1ArbRows", s["arbitrated_rows"], base + "f1_summary.json", "int")
    pr = pd.read_csv(ROOT / base / "f1_price.csv"); pr = pr[pr["mode"] == "arb"]
    # ---- ask policies (r3 primary contrasts, CLAM comparator)
    dp = "analysis/frontier/default_profiles/"
    c3 = pd.read_csv(ROOT / dp / "contrasts_r3.csv"); c3 = c3[c3.tag == "primary"]
    put("askPrimaryN", len(c3), dp + "contrasts_r3.csv", "int"); put("askPrimarySig", int((c3.p_adj < 0.05).sum()), dp + "contrasts_r3.csv", "int")
    r = c3[(c3.dimension == "polarity") & (c3.b == "random_gated")].iloc[0]
    put("askPriorMinusRandPol", sgn(r["diff"]), dp + "contrasts_r3.csv", "s"); put("askPriorMinusRandPolLo", sgn(r.lo), dp + "contrasts_r3.csv", "s"); put("askPriorMinusRandPolHi", sgn(r.hi), dp + "contrasts_r3.csv", "s")
    mde = pd.read_csv(ROOT / dp / "mde_r3.csv"); mm = mde[(mde.dimension == "polarity") & (mde.a == "prior_cv_refit") & (mde.b == "random_gated")].iloc[0]
    put("askMdePol", mm.mde_per_1000, dp + "mde_r3.csv", "f1"); put("askMdeRelPol", mm.mde_rel_to_always_commit, dp + "mde_r3.csv")
    cl = pd.read_csv(ROOT / dp / "followup/clam_contrasts.csv")
    m = cl[(cl.dimension == "polarity") & (cl.name == "clam_mean_gated - random_gated")].iloc[0]
    put("clamDiffPol", sgn(m["diff"]), dp + "followup/clam_contrasts.csv", "s"); put("clamDiffPolLo", sgn(m.lo), dp + "followup/clam_contrasts.csv", "s"); put("clamDiffPolHi", sgn(m.hi), dp + "followup/clam_contrasts.csv", "s")
    put("clamMdePol", m.mde, dp + "followup/clam_contrasts.csv", "f1"); put("clamPHolmPol", m.p_holm, dp + "followup/clam_contrasts.csv", "f2")
    m = cl[(cl.dimension == "politeness") & (cl.name == "clam_mean_gated - random_gated")].iloc[0]
    put("clamDiffPolite", sgn(m["diff"]), dp + "followup/clam_contrasts.csv", "s"); put("clamDiffPoliteLo", sgn(m.lo), dp + "followup/clam_contrasts.csv", "s"); put("clamDiffPoliteHi", sgn(m.hi), dp + "followup/clam_contrasts.csv", "s")
    # ---- guard transfer and no-feedback baseline
    p = "analysis/guard_wc/headline.json"; h = J(p)
    ci("gwG1s", h["g1s_joint_pass"], h["g1s_joint_pass_ci_low"], h["g1s_joint_pass_ci_high"], p)
    ci("gwGain", h["g1_joint_gain"], h["g1_joint_gain_ci_low"], h["g1_joint_gain_ci_high"], p, "pp")
    x = h["G1_minus_G1s"]["joint"]["family"]; ci("gwG1MinusG1s", x["estimate"], x["ci_low"], x["ci_high"], p + " G1_minus_G1s.joint.family", "pp")
    ci("gwStrictRepair", h["g1_strict_repair"], h["g1_strict_repair_ci_low"], h["g1_strict_repair_ci_high"], p)
    put("gwStrictRepairN", h["g1_strict_repair_n"], p, "int"); put("gwStrictRepairK", round(h["g1_strict_repair"] * h["g1_strict_repair_n"]), p, "int")
    put("gwChangedK", round(h["g1_strict_changed_correct"] * h["g1_strict_changed_correct_n"]), p, "int"); put("gwChangedN", h["g1_strict_changed_correct_n"], p, "int")
    put("gwPassToFailK", round(h["g1_strict_pass_to_fail"] * h["g1_strict_pass_to_fail_n"]), p, "int")
    put("gwStripRepair", h["g1s_strict_repair"], p); put("gwFlaggedF", h["F"], p, "int")
    put("gwGenCalls", h["cost"]["actual_generation_calls"], p, "int")
    gp = "analysis/guard_baseline/"; gs = J(gp + "summary.json")
    for st, S in [("wc", "Wc"), ("disc", "Disc")]:
        for arm in ["P0", "G1", "G1s", "G1r", "G1t"]:
            x = gs[st]["arms"][arm]["joint_pass"]; ci(f"gb{S}{arm}", x["estimate"], x["ci_low"], x["ci_high"], gp + "summary.json")
        put(f"gb{S}Targets", gs[st]["n_targets"], gp + "summary.json", "int"); put(f"gb{S}Families", gs[st]["n_families"], gp + "summary.json", "int")
    am = pd.read_csv(ROOT / gp / "arm_metrics.csv")
    for st, S in [("wc", "Wc"), ("disc", "Disc")]:
        for arm in ["G1", "G1s", "G1r", "G1t"]:
            r = am[(am.set == st) & (am.arm == arm) & (am.metric == "strict_repair")]
            if len(r): r = r.iloc[0]; ci(f"gb{S}Repair{arm}", r.estimate, r.ci_low, r.ci_high, gp + "arm_metrics.csv"); put(f"gb{S}Repair{arm}K", r.k, gp + "arm_metrics.csv", "int"); put(f"gb{S}Repair{arm}N", r.n, gp + "arm_metrics.csv", "int")
    ct = pd.read_csv(ROOT / gp / "contrasts.csv"); ct = ct[ct.endpoint == "joint"]
    for _, r in ct.iterrows():
        S = {"wc": "Wc", "disc": "Disc"}[r.set]; nm = r.contrast.replace("-", "M")
        ci(f"gbC{S}{nm}", r.estimate_pp / 100, r.ci_low_pp / 100, r.ci_high_pp / 100, gp + "contrasts.csv", "pp")
    # ---- SLP extras (parse scorer output once more)
    tmp = ROOT / "tmp"; tmp.mkdir(exist_ok=True); out = tmp / "slp_report_journal_s3.md"
    subprocess.run([sys.executable, str(ROOT / "src/score_slp_panel.py"), "--out", str(out)], check=True, capture_output=True, cwd=ROOT)
    t = out.read_text(); out.unlink(); s_ = "src/score_slp_panel.py -> expert_package/returns_slp (n=2 raters)"
    mm = re.search(r"\| hw1 human-written pairs, six dimensions \| irrelevant_chip \| \d+ \| ([\d.]+) \| ([\d.]+) \|", t)
    if mm: put("slpWCueIrrel", float(mm.group(2)) / 100, s_); put("slpUCueIrrel", float(mm.group(1)) / 100, s_)
    mm = re.search(r"\| W-C speech-act[^|]*\| guard_G1s \| \d+ \| ([\d.]+) \| ([\d.]+) \|", t)
    if mm: put("slpWGuardGs", float(mm.group(2)) / 100, s_)
    mm = re.search(r"\| guard_repair \| \d+ \| [\d /]+ \| (\d+) / (\d+) / (\d+) \|", t)
    if mm: put("slpRepairEdit", (int(mm.group(1)) + int(mm.group(2))) / (int(mm.group(1)) + int(mm.group(2)) + int(mm.group(3))), s_)
    for q_, n in [("a\\) says what selected", "A"), ("b\\) acceptable to speak", "B")]:
        mm = re.search(rf"\| \({q_} \| (\d+) \| (\d+) \| ([\d.]+) \|", t)
        if mm: put(f"slpKappa{n}", float(mm.group(3)), s_, "f2"); put(f"slpAgree{n}", int(mm.group(2)) / 100, s_)
    mm = re.search(r"\| W-C speech-act[^|]*\| baseline_P0 \| (\d+)", t)
    if mm: put("slpWcN", int(mm.group(1)), s_, "int")
    mm = re.search(r"\| hw1 human-written pairs, six dimensions \| baseline_bare \| (\d+)", t)
    if mm: put("slpHwN", int(mm.group(1)), s_, "int")


# --------------------------------------------------------------- section 4 (studies and results II)
def s4():
    """Macros for paper/journal/sections/s4.tex: Part 18 detail, whole-message, SLP severity/pairs, Part 19, consultants, frontier limits."""
    p = "analysis/intent_check/summary.json"; d = J(p)
    for k, n in [("all", "All"), ("chip1", "Chip"), ("bare", "Bare")]:
        x = d["match_rate"][k]; put(f"p18Match{n}K", x["k"], p, "int"); put(f"p18Match{n}N", x["n"], p, "int")
    sp = d["says_split"]
    put("p18Else", sp["all"]["something else"] / d["match_rate"]["all"]["n"], p); put("p18ElseK", sp["all"]["something else"], p, "int")
    put("p18ElseChip", sp["chip1"]["something else"] / d["match_rate"]["chip1"]["n"], p); put("p18ElseBare", sp["bare"]["something else"] / d["match_rate"]["bare"]["n"], p)
    ac = d["acceptability"]
    put("p18AcceptYesSmallK", ac["all"]["yes_or_small_edit"]["k"], p, "int"); put("p18AcceptNoK", ac["all"]["no"]["k"], p, "int")
    put("p18SmallChip", ac["chip1"]["yes_or_small_edit"]["p"], p); put("p18SmallBare", ac["bare"]["yes_or_small_edit"]["p"], p)
    put("p18YesChipK", ac["chip1"]["yes"]["k"], p, "int"); put("p18YesChipN", ac["chip1"]["yes"]["n"], p, "int")
    put("p18YesBareK", ac["bare"]["yes"]["k"], p, "int"); put("p18YesBareN", ac["bare"]["yes"]["n"], p, "int")
    put("p18YesIfMatchK", ac["all"]["yes_when_matches_intended"]["k"], p, "int"); put("p18YesIfMatchN", ac["all"]["yes_when_matches_intended"]["n"], p, "int")
    put("p18AgreeFour", d["agreement"]["all"]["q1_four_labels"]["agree"], p)
    put("p18PerWriter", d["per_writer"]["P01"]["n"], p + " per_writer", "int")
    # ---- whole-message decomposition
    q = "analysis/whole_message/summary.json"; w = J(q); kq = w["key_question"]; p18w = w["part18"]
    right = kq["judge critical RIGHT"]; wrong = kq["judge critical WRONG"]
    put("wmRightShare", right["n"] / p18w["n"], q); put("wmRightAccK", right["n"] - right["R3"], q, "int")
    put("wmRightIntShare", 1 - right["R1"][0] / right["R1"][1], q); put("wmModels", len(p18w["reason_by_model"]), q + " part18.reason_by_model", "int")
    put("wmHandN", w["hand_check"]["n"], q, "int"); put("wmHandAgree", w["hand_check"]["agree_diff_classifier"], q)
    put("wmAllN", p18w["n"], q, "int")
    put("wmWrongN", wrong["n"], q, "int"); put("wmWrongNotIntK", wrong["R1"][0], q, "int"); put("wmWrongNotIntN", wrong["R1"][1], q, "int")
    for tag, nm in [("RIGHT, chip1", "Chip"), ("RIGHT, bare", "Bare")]:
        x = kq[tag]
        put(f"wmRight{nm}N", x["n"], q, "int"); put(f"wmRight{nm}IntK", x["R1"][1] - x["R1"][0], q, "int")
        put(f"wmRight{nm}IntN", x["R1"][1], q, "int"); put(f"wmRight{nm}AccK", x["n"] - x["R3"], q, "int")
    r1 = kq["reason_right_R1"]; t1 = sum(r1.values())
    put("wmR1N", t1, q, "int"); put("wmR1SubstK", r1["substitution"], q, "int"); put("wmR1Subst", r1["substitution"] / t1, q)
    put("wmR1DroppedK", r1["dropped"], q, "int"); put("wmR1Dropped", r1["dropped"] / t1, q)
    reas = kq["reason_right_not_accepted"]; tot = sum(reas.values()); put("wmRightFluency", reas["fluency"] / tot, q)
    fl = kq["right_not_accepted_flags"]
    put("wmRightUnrec", fl["dropped_unrecoverable"], q); put("wmRightSubstFlag", fl["substitution"], q); put("wmRightAddedFlag", fl["added"], q)
    ra = p18w["reason_all"]; ta = sum(ra.values())
    put("wmAllNotAccN", ta, q, "int"); put("wmAllCritical", ra["critical"] / ta, q); put("wmAllSubst", ra["substitution"] / ta, q); put("wmAllDropped", ra["dropped"] / ta, q)
    for ch, nm in [("bare", "Bare"), ("chip1", "Chip")]:
        rc = p18w["reason_by_channel"][ch]; tc = sum(rc.values()); put(f"wm{nm}NotAccN", tc, q, "int")
        for r_, n_ in [("critical", "Critical"), ("substitution", "Subst"), ("dropped", "Dropped")]:
            put(f"wm{nm}{n_}", rc.get(r_, 0) / tc, q)
    b = w["bridge"]
    x = b["p18_ok_R1"]["length ratio to keywords (deployable)"]; ci("wmLenAuc", x["auroc"], x["ci"][0], x["ci"][1], q + " bridge.p18_ok_R1", "f2")
    inc = b["p18_incremental_R1"]
    x = inc["critical (binary, raw AUROC)"]; ci("wmCritAuc", x["auroc"], x["ci"][0], x["ci"][1], q + " bridge.p18_incremental_R1", "f2")
    x = inc["critical + all 3 deployable"]; ci("wmCritPlusAuc", x["auroc"], x["ci"][0], x["ci"][1], q + " bridge.p18_incremental_R1", "f2")
    sl = w["slp"]
    put("wmSlpPassN", sl["judge PASS (meaning_fail=0)"]["n"], q, "int"); put("wmSlpPassPartlyK", sl["judge PASS (meaning_fail=0)"]["reject"], q, "int")
    put("wmSlpPassPartly", sl["judge PASS (meaning_fail=0)"]["reject"] / sl["judge PASS (meaning_fail=0)"]["n"], q)
    x = sl["judge PASS and no added_content"]; put("wmSlpPassNoAddN", x["n"], q, "int"); put("wmSlpPassNoAddK", x["reject"], q, "int"); put("wmSlpPassNoAdd", x["reject"] / x["n"], q)
    x = sl["judge FAIL"]; put("wmSlpFailN", x["n"], q, "int"); put("wmSlpFailK", x["reject"], q, "int")
    rp = sl["reason_pass_partly_no"]; put("wmSlpAddedK", rp["added"], q, "int"); put("wmSlpSubstK", rp["substitution"], q, "int"); put("wmSlpReasonN", sum(rp.values()), q, "int")
    # ---- SLP: severity by type, paired repair/original, extra weighted rows
    tmp = ROOT / "tmp"; tmp.mkdir(exist_ok=True); out = tmp / "slp_report_journal_s4.md"
    subprocess.run([sys.executable, str(ROOT / "src/score_slp_panel.py"), "--out", str(out)], check=True, capture_output=True, cwd=ROOT)
    t = out.read_text(); out.unlink(); s_ = "src/score_slp_panel.py -> expert_package/returns_slp (n=2 raters)"
    for lab, nm in [("question/statement/command changed", "Sent"), ("actor switched", "Actor"), ("certainty added/removed", "Cert"),
                    ("politeness added/removed", "Polite"), ("time changed", "Time"), ("added content", "Added")]:
        mm = re.search(rf"\| {re.escape(lab)} \| ([\d.]+) \(n=2\) \|", t)
        if mm: put("slpSev" + nm, float(mm.group(1)), s_, "f1")
    rows = re.findall(r"^\| ([a-z/ ]+) \| [\d.]+ \(n=2\) \| [^|]+\| [\d.]+ \| (\d+) \| (\d+) \|", t, re.M)
    put("slpTypesN", len(rows), s_, "int"); put("slpFlagTypesK", sum(1 for r in rows if int(r[1]) == 100), s_, "int"); put("slpBlockTypesK", sum(1 for r in rows if int(r[2]) == 100), s_, "int")
    mm = re.search(r"\| hw1 human-written pairs, six dimensions \| baseline_noncrit \| \d+ \| ([\d.]+) \| ([\d.]+) \|", t)
    if mm: put("slpWCueNoncrit", float(mm.group(2)) / 100, s_)
    mm = re.search(r"\| guard_original \| \d+ \| [\d /]+ \| (\d+) / (\d+) / (\d+) \|", t)
    if mm: put("slpOrigEdit", (int(mm.group(1)) + int(mm.group(2))) / (int(mm.group(1)) + int(mm.group(2)) + int(mm.group(3))), s_)
    mm = re.search(r"guard_repair vs guard_original: both good (\d+); only guard_repair (\d+); only guard_original (\d+); neither (\d+)", t)
    if mm:
        put("slpPairBothK", int(mm.group(1)), s_, "int"); put("slpPairRepOnlyK", int(mm.group(2)), s_, "int"); put("slpPairOrigOnlyK", int(mm.group(3)), s_, "int")
        put("slpPairN", sum(int(mm.group(i)) for i in range(1, 5)), s_, "int")
    mm = re.search(r"\| \(a\) says what selected \| (\d+) \|", t)
    if mm: put("slpItemsRated", int(mm.group(1)), s_, "int")
    # ---- Part 19 additions
    q = "analysis/arbiter_check/summary.json"; a = J(q)
    put("p19CanYouItems", a["can_you"]["items"], q, "int")
    put("p19Units", a["arbiter_items"], q, "int"); put("p19Annotators", len(a["annotators"]), q, "int")
    put("p19SidedJOne", a["arbiter_sided_with"]["J1"], q, "int"); put("p19SidedJTwo", a["arbiter_sided_with"]["J2"], q, "int"); put("p19SidedNeither", a["arbiter_sided_with"]["neither"], q, "int")
    x = a["human_vs_arbiter"]["per_item_when_coders_agree"]; ci("p19ItemAgreeArb", x["p"], x["ci"][0], x["ci"][1], q); put("p19ItemAgreeArbK", x["k"], q, "int"); put("p19ItemAgreeArbN", x["n"], q, "int")
    put("p19HumanHumanArb", a["human_human"]["arbiter"]["agree"]["p"], q)
    # ---- consultants: ratings and example verdicts (parsed from stored returns; design feedback, not experience data)
    cp = "annotation/returns_consultant/{C01,C02}/design_review_progress.json"
    prog = [J(f"annotation/returns_consultant/{c}/design_review_progress.json") for c in ("C01", "C02")]
    put("consImpK", sum(1 for pr in prog for r_ in ("R1", "R2", "R3", "R4", "R5") if pr[f"imp_{r_}"] == "important"), cp, "int")
    put("consImpN", 5 * len(prog), cp, "int")
    put("consChipK", sum(1 for pr in prog if pr["chip_word"] == "chip"), cp, "int")
    key = pd.read_csv(ROOT / "expert_package/consultant_key.csv"); key = key[key.id.str.fullmatch(r"E\d\d")]
    kp = cp + " + expert_package/consultant_key.csv"
    for kind, nm in [("repaired", "Rep"), ("bad", "Bad"), ("good", "Good")]:
        ids = list(key[key.kind == kind].id)
        put(f"cons{nm}N", len(ids), kp, "int")
        put(f"cons{nm}NotOkK", sum(all(pr[f"send_{i}"] == "notok" for pr in prog) for i in ids), kp, "int")
        put(f"cons{nm}OkK", sum(all(pr[f"send_{i}"] == "ok" for pr in prog) for i in ids), kp, "int")
        put(f"cons{nm}NeitherOkK", sum(all(pr[f"send_{i}"] != "ok" for pr in prog) for i in ids), kp, "int")
    put("consExN", len(key), kp, "int")
    # ---- frontier limits: model uncertainty (knows_not_says)
    base = "analysis/frontier/knows_not_says/"
    r1 = pd.read_csv(ROOT / base / "stage1/r1.csv"); r1 = r1[(r1.model == "qwen2.5-7b") & (r1.dimension == "polarity")]
    for ds, nm in [("cap4", "Cap"), ("human", "Hum")]:
        r = r1[r1.dataset == ds].iloc[0]
        macros[f"kns{nm}Sampled"] = f"{100*r.sampled_share:.2f}"; sources[f"kns{nm}Sampled"] = base + "stage1/r1.csv (qwen2.5-7b, K=16 untruncated)"
        put(f"kns{nm}Target", r.posterior, base + "stage1/r1.csv")
        put(f"kns{nm}Ratio", r.ratio, base + "stage1/r1.csv", "f2")
    r2 = pd.read_csv(ROOT / base / "stage1/r2.csv"); r2 = r2[r2.dataset == "cap4"]
    for mdl, nm in [("qwen2.5-7b", "Qwen"), ("llama3.1-8b", "Llama")]:
        x = r2[(r2.model == mdl) & (r2.score == "sampled_share(K=16)")].iloc[0]; ci(f"knsAucK16{nm}", x.auroc, x.lo, x.hi, base + "stage1/r2.csv", "f2")
    x = r2[(r2.model == "qwen2.5-7b") & (r2.score == "lexical_cv_logistic")].iloc[0]; ci("knsAucLex", x.auroc, x.lo, x.hi, base + "stage1/r2.csv", "f2")
    rt = pd.read_csv(ROOT / base / "followup/r2_retest.csv")
    x = rt[(rt.score == "S1_negmass") & (rt.row == "pooled")].iloc[0]
    ci("knsAucNegmass", x.auroc, x.lo, x.hi, base + "followup/r2_retest.csv", "f2"); ci("knsNegmassVsLex", x["diff"], x.diff_lo, x.diff_hi, base + "followup/r2_retest.csv", "f2")
    x = rt[(rt.score == "S3_verbal") & rt.row.str.startswith("gpt-6.1-terra")].iloc[0]
    ci("knsAucTerraVerbal", x.auroc, x.lo, x.hi, base + "followup/r2_retest.csv", "f2"); ci("knsTerraVsLex", x["diff"], x.diff_lo, x.diff_hi, base + "followup/r2_retest.csv", "f2")
    put("knsUnitsCap", r1[r1.dataset == "cap4"].iloc[0].n_msgs, base + "stage1/r1.csv", "int")
    macros["knsModels"] = "2"; sources["knsModels"] = "DESIGN: qwen2.5-7b and llama3.1-8b (knows_not_says REPORT.md section 3)"
    # ---- frontier limits: partner context
    pb = "analysis/frontier/partner_context/r3_summary.json"; pc = J(pb)
    def pick(lst, key, val, model=None):
        for r in lst:
            if r.get(key, "").startswith(val) and (model is None or r.get("model") == model): return r
    x = pick(pc["c2"], "contrast", "C2 all negation incl. echo", "pooled"); ci("pcAll", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " c2", "pp")
    x = pick(pc["c2"], "contrast", "C2 propositional (primary", "pooled"); ci("pcProp", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " c2", "pp")
    put("pcFamilies", x["n_fam"], pb, "int")
    x = pick(pc["author_writer"], "estimate", "mistral-authored, 40 shared families, family"); ci("pcAuthMistral", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " author_writer", "pp")
    x = pick(pc["author_writer"], "estimate", "qwen14-authored, 40 shared families, family"); ci("pcAuthQwen", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " author_writer", "pp")
    put("pcAuthFamilies", x["n_fam"], pb, "int")
    x = pick(pc["c1"], "contrast", "C1 PRIMARY unfiltered", "pooled"); ci("pcCue", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " c1", "pp")
    x = pick(pc["c1"], "contrast", "C1 filtered lower bound, arm 0 unfiltered", "pooled"); ci("pcCueLow", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " c1", "pp")
    x = pick(pc["c3"], "contrast", "C3 Q minus arm 0, affirmative share of ALL", "pooled"); ci("pcQAff", x["est_pp"] / 100, x["lo_pp"] / 100, x["hi_pp"] / 100, pb + " c3", "pp")
    macros["pcModels"] = "4"; sources["pcModels"] = "DESIGN: qwen2.5-7b, llama3.1-8b, gemma3-4b, gpt-6.1-terra (partner_context REPORT.md section 3)"
    # ---- frontier limits: ask policies, politeness prior-minus-random
    dp = "analysis/frontier/default_profiles/"
    c3 = pd.read_csv(ROOT / dp / "contrasts_r3.csv"); c3 = c3[(c3.tag == "primary") & (c3.dimension == "politeness") & (c3.b == "random_gated")].iloc[0]
    ci("askPriorMinusRandPolite", c3["diff"], c3.lo, c3.hi, dp + "contrasts_r3.csv", "f1")
    put("askBudgetPct", c3.budget * 100, dp + "contrasts_r3.csv budget (share of messages asked)", "int")


safe(s4)

# --------------------------------------------------------------- pending slots
SLOTS = {  # key prefix -> file that must exist for the slot to fill (scored by a future script)
    "s5": "analysis/stage5/summary.json",       # Stage 5 Parts 20-25 (due Nov 5)
    "cov": "analysis/intent_coverage/summary.json",  # intent-coverage pilot (not yet run)
}


def slots():
    for k, f in SLOTS.items():
        macros["slot" + k.capitalize() + "Ready"] = "1" if (ROOT / f).exists() else "0"
        sources["slot" + k.capitalize() + "Ready"] = f"exists({f})"


for fn in [part17, part18, part19, slp, hw1, guard, f1, s5_discussion, s1, s3, slots]:
    safe(fn)

# --- section macro modules: macros_sec_*.py define register(ctx) -> list of functions (Method section: macros_sec_method.py)
import importlib.util as _iu
for _f in sorted(OUT.glob("macros_sec_*.py")):
    _sp = _iu.spec_from_file_location(_f.stem, _f); _mod = _iu.module_from_spec(_sp); _sp.loader.exec_module(_mod)
    for _fn in _mod.register(dict(put=put, ci=ci, J=J, ROOT=ROOT, A=A, macros=macros, sources=sources)):
        safe(_fn)

lines = ["% results_macros.tex -- GENERATED by paper/journal/make_macros.py. Do not edit by hand."]
for k in sorted(macros):
    lines.append(f"\\newcommand{{\\{tname(k)}}}{{{macros[k]}}}")
lines.append("\\newcommand{\\jmv}[1]{\\csname jm#1\\endcsname}  % unused fallback")
(OUT / "results_macros.tex").write_text("\n".join(lines) + "\n")
(OUT / "macro_sources.json").write_text(json.dumps({tname(k): {"value": macros[k], "source": sources[k]} for k in sorted(macros)}, indent=1))
print(f"{len(macros)} macros written")
