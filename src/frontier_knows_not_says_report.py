"""Markdown tables for round3.md from analysis/frontier/knows_not_says/<dir>/*.csv|json -> <dir>/tables.md.  usage: python src/frontier_knows_not_says_report.py [dir]"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "analysis/frontier/knows_not_says" / (sys.argv[1] if len(sys.argv) > 1 else "stage1")
r1 = pd.read_csv(D / "r1.csv"); r2 = pd.read_csv(D / "r2.csv"); pol = pd.read_csv(D / "pol.csv").rename(columns={"d_cost_priced_c0.03": "dc", "d_cost_priced_c0.03_lo": "dc_lo", "d_cost_priced_c0.03_hi": "dc_hi"}); rel = pd.read_csv(D / "rel.csv"); holm = pd.read_csv(D / "holm.csv")
pooled = pd.read_csv(D / "pooled.csv") if (D / "pooled.csv").exists() and (D / "pooled.csv").stat().st_size > 5 else pd.DataFrame()
S = json.load(open(D / "summary.json")); out = []
pc = lambda x: "" if pd.isna(x) else f"{100 * x:.2f}%"
f2 = lambda x: "" if pd.isna(x) else f"{x:.2f}"
f1 = lambda x: "" if pd.isna(x) else f"{x:.1f}"
ci = lambda v, lo, hi, f=f2: "" if pd.isna(v) else f"{f(v)} [{f(lo)}, {f(hi)}]"
def table(df, cols):
    out.append("| " + " | ".join(cols) + " |"); out.append("|" + "---|" * len(cols))
    for r in df: out.append("| " + " | ".join(map(str, r)) + " |")
    out.append("")
out.append("## T1. R1, polarity (detector-relative share of no-cue units whose output is negated; HT-weighted; 10,000 item resamples)")
rows = []
for r in r1[r1.dimension == "polarity"].itertuples():
    rows.append([r.model, r.dataset, r.n_nocue_units, r.n_pos_nocue_raw, ci(100 * r.posterior, 100 * r.posterior_lo, 100 * r.posterior_hi), ci(100 * r.greedy_share, 100 * r.greedy_lo, 100 * r.greedy_hi), ci(100 * r.sampled_share, 100 * r.sampled_lo, 100 * r.sampled_hi),
                 ci(r.ratio, r.ratio_lo90, r.ratio_hi90), r.r1_class, (ci(r.corr_ratio, r.corr_ratio_lo90, r.corr_ratio_hi90) if "corr_ratio" in r1 and not pd.isna(r.corr_ratio) else ""), (r.corr_r1_class if "corr_r1_class" in r1 else ""), r.power])
table(rows, ["model", "set", "no-cue units", "raw pos.", "source posterior % [95%]", "greedy share % [95%]", "sampled share % [95%]", "ratio sampled/posterior [90%]", "class (detector)", "corrected ratio [90%]", "class (corrected)", "power"])
out.append("## T1b. other dimensions (descriptive only; detector labels, no validity check)")
rows = [[r.model, r.dataset, r.dimension, r.n_nocue_units, r.n_pos_nocue_raw, pc(r.posterior), pc(r.greedy_share), pc(r.sampled_share), f2(r.ratio), r.r1_class] for r in r1[r1.dimension != "polarity"].itertuples()]
table(rows, ["model", "set", "dimension", "no-cue units", "raw pos.", "source posterior", "greedy share", "sampled share", "ratio", "class"])
out.append("## T2. R2, per-input AUROC on no-cue units (tie-aware, HT-weighted; E-human EXPLORATORY)")
rows = []
for r in r2.itertuples():
    rows.append([r.model, r.dataset, r.score, ci(r.auroc, r.lo, r.hi), r.n_pos_raw, r.power, (f2(r.tied0_all) + " / " + f2(r.tied0_pos) + " / " + f2(r.tied0_neg)) if not pd.isna(getattr(r, "tied0_all", np.nan)) else "",
                 (ci(getattr(r, "diff_vs_lexical_cv_logistic"), getattr(r, "diff_vs_lexical_cv_logistic_lo"), getattr(r, "diff_vs_lexical_cv_logistic_hi"))) if not pd.isna(getattr(r, "diff_vs_lexical_cv_logistic", np.nan)) else ""])
table(rows, ["model", "set", "score", "AUROC [95%]", "raw pos.", "power", "tied-at-0 (all/pos/neg)", "sampled minus lexical [95%]"])
if len(pooled):
    out.append("## T2b. Model-pooled, item-clustered (same resample for both models)")
    table([[r.dataset, r.quantity, r.n_models, ci(r.point, r.lo, r.hi), r.status] for r in pooled.itertuples()], ["set", "quantity", "models", "estimate [95%]", "status"])
out.append("## T3. Holm family (E-cap4 confirmatory; one-sided bootstrap p)")
table([[r["model"], r["test"], f"{r.p_raw:.4f}", f"{r.p_holm:.4f}", "yes" if r["reject_at_0.05"] else "no"] for _, r in holm.iterrows()], ["model", "test", "p raw", "p Holm", "reject at 0.05"])
for ds in ("cap4", "human"):
    out.append(f"## T4. Benchmark, E-{ds}: silent polarity reversals, spurious negations and taps per 1,000 units (SLP weights w_rev = w_spur = 1 unless stated; simulated, assumes asking resolves the cue){' EXPLORATORY' if ds == 'human' else ''}")
    for m in sorted(pol.model.unique()):
        d = pol[(pol.model == m) & (pol.dataset == ds)]
        keep = d[~d.policy.str.contains("Platt|contextual") | d.policy.str.contains("c=0.1 w_spur|c=0.03 w_spur=1/1$", regex=True)]
        rows = []
        for r in keep.itertuples():
            if r.kind == "not-applicable": rows.append([r.policy, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", r.note[:140]]); continue
            rows.append([r.policy, ci(r.reversals_per_1000, r.rev_lo, r.rev_hi, f1), ci(r.spurious_per_1000, r.spur_lo, r.spur_hi, f1), ci(r.taps_per_1000, r.taps_lo, r.taps_hi, f1),
                         ci(r._asdict()["d_cost_priced_c0_03"] if "d_cost_priced_c0_03" in r._asdict() else np.nan, 0, 0, f1) if False else ci(getattr(r, "dc"), getattr(r, "dc_lo"), getattr(r, "dc_hi"), f1), ci(r.caught_minus_random, r.cmr_lo, r.cmr_hi, f1), ci(r.recall_of_reversals, r.recall_lo, r.recall_hi), "" if pd.isna(r.recovers_R3) else ("YES" if r.recovers_R3 else "no"), ""])
        out.append(f"**{m}**"); out.append("")
        table(rows, ["policy", "reversals/1000", "spurious/1000", "taps/1000", "d priced cost vs commit (tap = 0.03)", "caught minus matched random-ask", "recall of reversals", "recovers R3", "note"])
out.append("## T5. Reliability (HT-weighted ECE and Brier, no-cue units; constant base-rate Brier for reference)")
table([[r.model, r.dataset, ci(r.ece, r.ece_lo, r.ece_hi, lambda x: f"{x:.4f}"), ci(r.brier, r.brier_lo, r.brier_hi, lambda x: f"{x:.4f}"), f"{r.brier_const_base_rate:.4f}"] for r in rel.itertuples()], ["model", "set", "ECE [95%]", "Brier [95%]", "Brier of a constant base-rate predictor"])
out.append("## T7. Detector validity (machine reference: judge J1+J2 + blind arbiter; NOT human truth)")
V = json.load(open(D / "detector_validity.json")); rows = []
for k, v in V["sets"].items():
    rows.append([k, f"{v['ppv']['k']}/{v['ppv']['n']} = {v['ppv']['rate']:.3f} [{v['ppv']['wilson_lo']:.3f}, {v['ppv']['wilson_hi']:.3f}]", f"{v['npv']['k']}/{v['npv']['n']} = {v['npv']['rate']:.3f} [{v['npv']['wilson_lo']:.3f}, {v['npv']['wilson_hi']:.3f}]", v["unclear_mixed_by_reference"], f2(v.get("p_detector_neg_domain_ht")) , f2(v.get("derived_sensitivity")), f2(v.get("derived_specificity"))])
table(rows, ["set", "PPV (ref negated | detector negated) [Wilson]", "NPV (ref not negated | detector not negated) [Wilson]", "ref unclear/mixed among drawn", "detector-negated share of domain (HT)", "derived sensitivity", "derived specificity"])
out.append("## T8. Pair scoring (PROVISIONAL, noise-limited), hw1 + W-C polarity pairs")
rows = []
for m, v in S["models"].items():
    P = v.get("pairs")
    if not P: continue
    for sc, d in P["scorers"].items(): rows.append([m, sc, P["n_pairs"], f2(d["median_logodds_aff_over_neg"]), f2(d["share_aff_preferred"]), f2(d["placebo_abs_p95"]), f2(d["share_true_beyond_placebo_p95"])])
table(rows, ["model", "scorer", "pairs", "median log-odds aff over neg (nats)", "share aff preferred", "placebo |logodds| p95", "share of pairs beyond placebo p95"])
rows = []
for m, v in S["models"].items():
    P = v.get("pairs")
    if not P: continue
    I = P["imputation_sensitivity"]
    for sc, d in I["by_scorer"].items(): rows.append([m, sc, I["n_all"], I["n_clean"], f"{I['n_imp_aff_only']}/{I['n_imp_neg_only']}/{I['n_imp_both']}", f2(d["median_all"]), f2(d["median_clean"]), f2(d["share_aff_pref_all"]), f2(d["share_aff_pref_clean"]), f2(d["share_aff_pref_conservative"]), f2(d["share_aff_pref_optimistic"])])
table(rows, ["model", "scorer", "pairs", "clean pairs (no imputed token)", "imputed in aff-only/neg-only/both", "median all", "median clean", "share aff pref. all", "clean", "conservative bound", "optimistic bound"])
out.append("## T6. Mechanics")
for m, v in S["models"].items():
    out.append(f"- {m}: inputs {v['n_inputs']}, missing requests {v['requests_missing']}, mean unique texts per 16 samples {v['mean_unique_texts_per_16']:.2f}, finish=length {v['finish_length_total']}, content-free 'Keywords: N/A' sampled negated share {v['content_free_N/A']['sampled_neg']}; G1 check on {v['g1_check']['n_units']} greedy outputs: {v['g1_check']['flag_counts']}")
(D / "tables.md").write_text("\n".join(out)); print("tables ->", D / "tables.md", len(out), "lines")
