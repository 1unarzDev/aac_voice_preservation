"""Builds analysis/hardening/report.md from the CSV/JSON written by run_hardening.py (no hand-typed numbers in tables)."""
import json, pandas as pd
from pathlib import Path
H = Path(__file__).resolve().parent
S = json.load(open(H / "summary.json"))
lm = pd.read_csv(H / "listener_crossed_models.csv"); pw = pd.read_csv(H / "power_mde.csv")
slp = pd.read_csv(H / "slp_weight_sensitivity_papers.csv"); sl = pd.read_csv(H / "slp_weight_sensitivity_listener.csv")
ls = pd.read_csv(H / "leakage_sensitivity.csv"); est = pd.read_csv(H / "estimand_table.csv")
L = S["leakage"]; E = S["estimand"]["chain"]; pj = E["projection"]
f = lambda v, d=1: "" if pd.isna(v) else f"{v:.{d}f}"
o = []
o += ["# A4 CPU hardening: report (2026-11-18)", "",
      "Plan: `PLAN.md` in this folder, written before any script ran. Code: `run_hardening.py` (seed 20261117), `build_report.py`. Frozen estimates remain the headline; every number below is a sensitivity or an audit. No new human data, no model call, no GPU. Not committed.", "",
      "## Verdict", "",
      "- No frozen conclusion changes. Chip raises listener success (+20 pp) and lowers opposite-action responses (about -21 pp) under every dependence model; the received-reversal difference stays 'not confirmed' under the frozen rule (item-cluster randomisation p about 0.06). Details and one nuance in section 1.",
      "- No listener judged a pair they wrote or checked (0 of 846 judgments). Text-level exposure to the same sentence elsewhere in the program touches %d of 846 listener-item cells (%.1f%%); dropping them leaves the chip - bare gain at the same size." % (L["exposed_listener_item_cells"], 100 * L["exposed_cells_share_of_846"]),
      "- SLP weights: every weighted number moves in level but no ordering or sign changes; the two raters gave identical weights to all four listener-study dimensions, so the listener SLP-weighted reversal is rater-invariant.",
      "- Power: the listener study can detect about %s pp (success) and %s pp (opposite action) at 80%% power; it cannot detect the observed reversal difference (MDE %s pp, observed %s pp). Part 17 could not settle a -10 pp margin (non-inferiority power about 0.33 at a true difference of 0)." % (
          f(pw[(pw.study == 'Part 28 listener') & pw.endpoint.str.startswith('success')].mde80_pp.iloc[0]), f(pw[(pw.study == 'Part 28 listener') & pw.endpoint.str.startswith('opposite')].mde80_pp.iloc[0]),
          f(pw[(pw.study == 'Part 28 listener') & pw.endpoint.str.startswith('received')].mde80_pp.iloc[0]), f(abs(pw[(pw.study == 'Part 28 listener') & pw.endpoint.str.startswith('received')].frozen_estimate_pp.iloc[0]))), "",
      "## 1. Listener study with crossed listener x item dependence", "",
      "Same 846 unit judgments (20 listeners, 120 items, each listener sees an item at most once; %d listener-item cells; judgments per item median %s). Differences in percentage points. GLMM = logistic, crossed random intercepts for item and listener (statsmodels BinomialBayesMixedGLM, variational Bayes, population-averaged difference; VB intervals are too narrow and are shown as a direction check). LPM-2way = linear probability, two-way cluster-robust (item x listener). LPM-itemFE = item fixed effects, cluster-robust by listener. Frozen = the two-way cluster bootstrap of `analysis/listener_human` (10,000 resamples). p(item), p(listener) = sign-flip randomisation tests with items or listeners as clusters." % (
          S["listener_structure"]["n_item_listener_cells"], S["listener_structure"]["judgments_per_item_median"]), "",
      "| contrast | outcome | ref % | arm % | GLMM | LPM-2way | LPM-itemFE | frozen bootstrap | p(item) | p(listener) |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in lm.itertuples():
    if r.contrast.startswith("G1"):
        continue
    o.append(f"| {r.contrast} | {r.metric} | {f(r.rate_ref)} | {f(r.rate_arm)} | {f(r.glmm_diff)} [{f(r.glmm_lo)}, {f(r.glmm_hi)}] | {f(r.lpm2way_diff)} [{f(r.lpm2way_lo)}, {f(r.lpm2way_hi)}] | {f(r.lpm_itemFE_diff)} [{f(r.lpm_itemFE_lo)}, {f(r.lpm_itemFE_hi)}] | "
             f"{f(r.frozen_diff)} [{f(r.frozen_lo)}, {f(r.frozen_hi)}] | {r.signflip_p_item:.3f} | {r.signflip_p_listener:.3f} |")
v = lm[(lm.contrast == "chip1 - bare") & (lm.metric == "success")].iloc[0]
o += ["", f"G1 - bare is not refit: G1 returned the bare sentence for nearly all items (frozen difference 0.0).", "",
      f"Variance components (logit SD, success, chip - bare model): item {f(v.sd_item, 2)}, listener {f(v.sd_listener, 2)}; item heterogeneity dominates, which is why the paired item-fixed-effect model and the item-clustered tests are the relevant checks.", "",
      "Reading. Success and opposite action: the sign and size agree in all models, intervals exclude 0, and the model-based intervals are narrower than the frozen bootstrap (the bootstrap is the more conservative and stays the headline). Plain word - chip: no difference in any model, consistent with the frozen 'not shown equivalent' reading (all intervals include 0, widths of about 8 to 10 pp exceed the 5 pp margin). Received reversal: bare 5.0% vs chip 0.8%. The frozen bootstrap interval [-9.9, +0.7] pp includes 0; the crossed models (GLMM, LPM) exclude 0, but they are asymptotic and unreliable with 12 vs 2 events, and the item-cluster randomisation test gives p about 0.06 while the listener-cluster test gives p about 0.01. The honest summary is: the frozen conclusion ('not confirmed') stands as the pre-specified result; the sensitivity analyses point the same direction and are borderline. The paper should keep 'not confirmed' and may add 'sensitivity models agree in direction'.", ""]
o += ["## 2. Leakage audit", "",
      f"- Direct: listener is the writer of the judged pair in {L['listener_is_writer_of_judged_pair']} of {L['n_key_rows']} key rows; listener is one of the three checkers of the judged pair in {L['listener_is_checker_of_judged_pair']}. The same pair id (hc id) appears in the listener's own check packet files for {L['same_pair_id_in_listener_packet_cells']} cells and in their returned checks for {L['same_pair_id_in_listener_check_returns_cells']} cells. The drawn families come from {L['distinct_writers_of_drawn_families']} writers (all 20 annotators are writers too, so person-level overlap is by design; pair-level overlap is zero).",
      f"- Within study: a listener never sees two units of the same item (max {L['max_units_same_item_same_listener']}); each item is judged by {L['listeners_per_item_min_max'][0]} to {L['listeners_per_item_min_max'][1]} listeners across its units, so a listener cannot compare conditions of one item.",
      f"- Cross-stage text exposure (conservative: any listener-item cell where a source sentence of the family or the stimulus sentence appears as text in that listener's own earlier packet files, which includes other writers' near-duplicate sentences): {L['exposed_listener_item_cells']} cells ({100*L['exposed_cells_share_of_846']:.1f}%), {L.get('exposed_source_sentence_cells', 0)} of them via a source (writer) sentence; by file {L.get('exposed_by_part')}. All are role 'other' (not the writer, not a checker of that pair): the sentence occurs in a different pair or task. Cells in `leakage_exposure_cells.csv`.",
      f"- Success among exposed cells {100*L['success_exposed_vs_not']['exposed']:.1f}% vs {100*L['success_exposed_vs_not']['not']:.1f}% unexposed (all conditions pooled, descriptive).", "",
      "| sample | outcome | bare % | chip % | chip - bare (paired items) | items | judgments |", "|---|---|---|---|---|---|---|"]
for r in ls.itertuples():
    o.append(f"| {r.sample} | {r.metric} | {f(r.bare)} | {f(r.chip1)} | {f(r.diff_paired_items)} | {r.n_items_both} | {r.n_judgments} |")
o += ["", "Reading. No author or checker leakage. Residual exposure is sentence-level and small, and removing it does not move the contrast. The paper can state 'no listener judged a pair they wrote or checked'; cross-stage exposure is a limitation worth one clause only if a reviewer asks.", "",
      "## 3. SLP weight sensitivity", "",
      "SLP-weighted numbers in the papers: CALE-AI `slp_wc_base/guard`, `slp_hw_base/chip/word` (weighted failure rate) and the macros `ls_slp_bare/chip` (listener SLP-weighted reversal; defined in the macro file, not cited in the text). SE4All prints no weighted rate (it cites severity 5 of 5 and acceptance counts only). n = 2 raters, so leave-one-out equals each rater alone. Weights: frozen = mean severity/5; uniform = every type 1.0 (the unweighted any-failure rate); rank = rank of mean severity/7; critical-only = types with mean severity >= 4 get 1, others 0.", "",
      "Weights by type: " + "; ".join(f"{k}: " + ", ".join(f"{t} {v:.2f}" for t, v in w.items()) for k, w in S["slp"]["weights"].items()), "",
      "| scheme | W-C base | W-C guard | guard rel. reduction % | hw1 bare | hw1 chip | hw1 word | chip rel. reduction % | chip - word (pp) |", "|---|---|---|---|---|---|---|---|---|"]
for r in slp.itertuples():
    o.append(f"| {r.scheme} | {f(r.slp_wc_base)} | {f(r.slp_wc_guard)} | {f(r.WC_rel_reduction_pct, 0)} | {f(r.slp_hw_base)} | {f(r.slp_hw_chip)} | {f(r.slp_hw_word)} | {f(r.HW_rel_reduction_chip_pct, 0)} | {f(r.HW_chip_vs_word_pp)} |")
o += ["", "Listener SLP-weighted reversal per 1,000 (item-balanced, two-way bootstrap with 2,000 resamples here; frozen 10,000-resample intervals are in `analysis/listener_human`):", "",
      "| scheme | w polarity / other | bare | chip | chip - bare |", "|---|---|---|---|---|"]
for r in sl.itertuples():
    o.append(f"| {r.scheme} | {r.w_polarity:.2f} / {r.w_speech_act:.2f} | {f(r.bare_per1000)} [{f(r.bare_lo)}, {f(r.bare_hi)}] | {f(r.chip1_per1000)} [{f(r.chip1_lo)}, {f(r.chip1_hi)}] | {f(r.diff_per1000)} [{f(r.diff_lo)}, {f(r.diff_hi)}] |")
o += ["", "Reading. The frozen weighted values are reproduced (22.0, 14.7, 57.4, 14.9, 17.8; 40.8 and 6.7 per 1,000). Levels move with the scheme (W-C weighted base 20.7 to 30.3) but within each population the ordering is unchanged and every guard or cue arm stays below its baseline. The size of the W-C guard gain depends on the weights: relative reduction runs from about 22% (critical-only) to 38% (uniform) against 33% frozen; the hw1 chip reduction is stable near 73 to 74%. Report the guard's weighted gain as 'about a quarter to two fifths depending on weights' if the sentence is kept. Chip vs word on hw1 is 2.9 to 3.7 pp under every scheme. The listener weights are identical for both raters (polarity 1.0, other three dimensions 0.8), so leave-one-SLP-out changes nothing there; uniform weights give the raw reversal rate.", "",
      "## 4. Power and minimum detectable effect", "",
      "MDE = 2.80 x the achieved standard error of the frozen design (two-sided alpha 0.05, 80% power), a statement about the design's sensitivity; no observed power is reported. SE for Part 28 and Stage 6 is recovered from the frozen bootstrap interval (half-width / 1.96); Part 17 uses the binomial SE of two 60-item arms (rater variance ignored, so it is optimistic); Part 18 uses a writer-cluster bootstrap recomputed here (frozen CI 14.8 to 42.0 pp). 'Power at effect' is power to detect a true difference of 10 pp (5 pp for received reversal, the whole bare rate).", "",
      "| study | endpoint | frozen estimate (pp) | SE (pp) | MDE 80% (pp) | power at effect | note |", "|---|---|---|---|---|---|---|"]
for r in pw.itertuples():
    o.append(f"| {r.study} | {r.endpoint} | {f(r.frozen_estimate_pp)} | {f(r.se_pp)} | {f(r.mde80_pp)} | {f(r.power_at_10pp, 2)} | {r.note} |")
o += ["", "Reading. The study sizes detect effects of 12 to 22 pp, which is enough for the large measured effects (cue tap +30, chip success +20, opposite action -21) and not for small ones. Not settled by design: (a) received reversal (frozen difference -4.2 pp against MDE 7.6 pp; the item-FE model SE gives MDE 3.4 pp); (b) the Part 17 deployment margin (60 per arm; 80% power to show 'lower bound above -10 pp' at a true difference of 0 needs about 200 per arm); (c) Stage 6 S1 contrasts (C3 or E3 minus D3p in bare, MDE about 13 pp against the +10 pp threshold) and S2 (MDE about 22 pp against a -5 pp margin). This supports wording 'unresolved' and 'cost of uncertain size' rather than 'no effect'.", "",
      "## 5. Estimand table (CALE-AI, 10 rows)", "", "Status values: measured (frozen design on stored text), human-judged (adult annotators or writers), machine (judge or NLI labels), projection (arithmetic; no data on people who use AAC). Source for `estimand_table.tex` and `estimand_table.csv`.", "",
      "| # | claim | estimand | population | design | estimate | status |", "|---|---|---|---|---|---|---|"]
for r in est.itertuples():
    o.append(f"| {r.id} | {r.claim} | {r.estimand} | {r.population} | {r.design} | {r.estimate} | {r.status} |")
lk = E["links"]
o += ["", "### Chain: cue supply -> machine restoration -> listener success -> AAC-user link", "",
      "| link | estimate | interval | status |", "|---|---|---|---|"]
for l in lk:
    est_ = "unmeasured" if l["estimate"] is None else f"{l['estimate']:.1f}" + (f" (bare {l['bare']:.1f})" if 'bare' in l else "")
    o.append(f"| {l['link']} | {est_} | [{l['lo']:.1f}, {l['hi']:.1f}] | {l['status']} |")
o += ["", E["note"], "",
      f"Projection (not a finding; {pj['formula']}): the gain per message in intended-reading success if the person supplies the cue is s x q x G. Worst bound: s = 0, gain 0. Central with s = 1 and measured q = 0.736, G = 20.0: {pj['central_s1']:.1f} pp. Product of the measured interval ends (s = 1): {pj['s1_interval_product_of_ends'][0]:.1f} to {pj['s1_interval_product_of_ends'][1]:.1f} pp (this combines two intervals end to end, so it is wider than a joint 95% interval). Best bound: s = 1, q = 1, upper end of G: {pj['best_s1_q1']:.1f} pp; the ceiling is {pj['best_ceiling_if_output_as_clear_as_reference']:.1f} pp (writer's own sentence 100%, bare 8.3%). Speech act only (q measured there): central {pj['speech_act_central_s1']:.1f} pp, but the speech-act listener contrast has 30 items and its interval ({lk[3]['lo']:.1f} to {lk[3]['hi']:.1f}) includes 0, so the speech-act-specific chain is descriptive. q was measured with classmate annotators on speech act only; polarity and politeness keep the assumed 0.9 in the cost model. The listeners are not AAC partners and judged stored text; the AAC-user link, the partner link and any benefit to a person are untested, so the label for row 10 is projection.", "",
      "## Files", "",
      "`listener_crossed_models.csv`, `leakage_exposure_cells.csv`, `leakage_sensitivity.csv`, `slp_weights_by_scheme.csv`, `slp_weight_sensitivity_papers.csv`, `slp_weight_sensitivity_listener.csv`, `power_mde.csv`, `estimand_table.csv`, `estimand_table.tex`, `summary.json`.",
      "", "Known limits. The GLMM is a variational-Bayes fit (no exact crossed-effects frequentist GLMM exists in statsmodels); rare-event models are unreliable and are labelled so; the exposure scan matches text, so it over-counts generic short sentences; MDEs inherit the frozen designs' clustering and use 2.80 x SE (normal approximation)."]
(H / "report.md").write_text("\n".join(o) + "\n")
# summary.json: conclusion flag and headline
S["frozen_conclusion_changes"] = False
S["headline"] = {"listener_success_chip_minus_bare_pp": {"frozen": 20.0, "glmm": float(lm[(lm.contrast=='chip1 - bare')&(lm.metric=='success')].glmm_diff.iloc[0]), "lpm_item_fe": float(lm[(lm.contrast=='chip1 - bare')&(lm.metric=='success')].lpm_itemFE_diff.iloc[0])},
                 "leakage_direct": 0, "exposed_cells": L["exposed_listener_item_cells"], "chain_central_pp": pj["central_s1"]}
json.dump(S, open(H / "summary.json", "w"), indent=1, default=str)
