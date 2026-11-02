"""Write paper/caleai/results_macros.tex from evidence.json (itself built from stored scored tables).

    ~/aac-voice-preservation/.venv/bin/python paper/caleai/caleai_evidence.py
    ~/aac-voice-preservation/.venv/bin/python paper/caleai/make_macros.py

Every number in main.tex is \\RES{key}. Never type a result by hand. Keys ending _lo/_hi are 95%
family-cluster bootstrap bounds; _k/_n are counts. Percentages carry one decimal.

Human gold is read directly from annotation/judge_validation_main1.json (score_gold.paper_macros,
keys human_*; human_gold_ready). Pending inputs (W-B, W-C, W-D, repair audit, T3) are exported as <name>_ready only
when their file exists; any numeric leaves of a pending JSON report are exported generically as
<name>__<path> so the paper's conditional slots can pick them up without editing this script.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EV = json.loads((HERE / "evidence.json").read_text())
M: dict[str, str] = {}


def put(k: str, v) -> None:
    M[k] = str(v)


def pc(k: str, r: dict, sign=1.0, d=1) -> None:
    """estimate/CI dict -> k, k_lo, k_hi in percent (sign=-1 flips a difference into a loss)."""
    e, lo, hi = 100 * sign * r["estimate"], 100 * sign * r["ci_low"], 100 * sign * r["ci_high"]
    lo, hi = min(lo, hi), max(lo, hi)
    put(k, f"{e:.{d}f}"); put(k + "_lo", f"{lo:.{d}f}"); put(k + "_hi", f"{hi:.{d}f}")
    if "n" in r:
        put(k + "_n", f"{r['n']:,}")
    if "k" in r:
        put(k + "_k", f"{int(round(r['k'])):,}")


def kn(k: str, num, den) -> None:
    put(k + "_k", f"{int(num):,}"); put(k + "_n", f"{int(den):,}")
    put(k, f"{100 * num / den:.1f}" if den else "NA")


g, s, c = EV["guard"], EV["span"], EV["chips"]
gr, sr = g["report"], s["report"]

# ---------------- population
put("n_fam", gr["population"]["n_families"]); put("n_models", 4)
put("n_cue_targets", f"{g['n_cue_targets']:,}")
# ---------------- I1 guard
for arm in ("P0", "G1", "G1s"):
    a = arm.lower()
    pc(f"g_sp_{a}", gr[arm]["sp"]); pc(f"g_cm_{a}", gr[arm]["cm"])
    pc(f"g_ct_{a}", gr[arm]["ct"]); pc(f"g_pa_{a}", gr[arm]["pol_add"])
    pc(f"g_spx_{a}", gr[arm]["sp"], d=2)  # two-decimal view used in the abstract and decision ledger
    put(f"g_spc_{a}", f"{round(gr[arm]['sp']['estimate'] * g['n_cue_targets']):,}")
put("g_sp_gain", f"{100 * (gr['G1']['sp']['estimate'] - gr['P0']['sp']['estimate']):.2f}")
pc("g_fix", gr["G1_cue"]["fix"]); kn("g_fixc", round(gr["G1_cue"]["fix"]["estimate"] * gr["G1_cue"]["n_bad"]), gr["G1_cue"]["n_bad"])
put("g_fix_fam", gr["G1_cue"]["fix"]["n_families"])
pc("g_fixs", gr["G1s_cue"]["fix"]); kn("g_fixsc", round(gr["G1s_cue"]["fix"]["estimate"] * gr["G1s_cue"]["n_bad"]), gr["G1s_cue"]["n_bad"])
pc("g_fix_all", gr["G1_all"]["fix"]); put("g_bad_all", gr["G1_all"]["n_bad"])
kn("g_amb_fix", round(gr["G1_ambiguous"]["fix"]["estimate"] * gr["G1_ambiguous"]["n_bad"]), gr["G1_ambiguous"]["n_bad"])
pc("g_oc_all", gr["G1_all"]["overcorr"]); kn("g_occ_all", round(gr["G1_all"]["overcorr"]["estimate"] * gr["G1_all"]["n_ok"]), gr["G1_all"]["n_ok"])
pc("g_oc_amb", gr["G1_ambiguous"]["overcorr"])
pc("g_ocs_all", gr["G1s_all"]["overcorr"]); kn("g_ocsc_all", round(gr["G1s_all"]["overcorr"]["estimate"] * gr["G1s_all"]["n_ok"]), gr["G1s_all"]["n_ok"])
kn("g_oc_cue", g["changed_correct_cue"]["k"], g["changed_correct_cue"]["n"])
pc("g_broken", gr["G1_all"]["broken"])
pc("g_res", g["residual"])
kn("g_res_flag", g["residual_flagged"]["k"], g["residual_flagged"]["n"])
kn("g_res_act", g["residual_act"]["k"], g["residual_act"]["n"])
kn("g_unfixed", g["unfixed_of_bad"]["k"], g["unfixed_of_bad"]["n"])
kn("g_ask", g["ask_you_prefix"]["k"], g["ask_you_prefix"]["n"])
co = gr["cost"]
put("g_calls", f"{co['calls_per_input']:.3f}"); put("g_calls_flag", f"{co['calls_per_flagged']:.2f}")
put("g_lat", f"{co['lat_per_input']:.2f}"); put("g_lat_flag_med", f"{co['lat_flagged_median']:.2f}")
put("g_check_ms", f"{co['check_ms']:.1f}")
kn("g_flagged", co["flagged"], co["inputs"])
lj = gr["l0_vs_judge"]
put("mon_tp", lj["tp"]); put("mon_fp", lj["fp"]); put("mon_fn", lj["fn"]); put("mon_tn", lj["tn"])
put("mon_prec", f"{lj['tp'] / (lj['tp'] + lj['fp']):.2f}"); put("mon_rec", f"{lj['tp'] / (lj['tp'] + lj['fn']):.2f}")
put("mon_kappa", f"{lj['kappa']:.2f}"); put("mon_rep_kappa", f"{gr['agree_repaired']['kappa']:.2f}")
put("mon_rep_n", gr["agree_repaired"]["n"])
inc = EV["sensitivity_inclusive"]["guard_fix"]
pc("g_fix_incl", inc); kn("g_fixc_incl", round(inc["estimate"] * inc["n"]), inc["n"])
put("g_calls_incl", f"{EV['sensitivity_inclusive']['cost']['calls_per_input']:.3f}")
cp = EV["copy_full_mode"]
put("copy_k", cp["primary_pass"]); put("copy_n", cp["primary_n"])
for m, short in (("qwen2.5-7b", "qwen"), ("gemma3-4b", "gemma"), ("llama3.1-8b", "llama"), ("gpt-6.1-terra", "terra")):
    d = g["by_model"][m]
    kn(f"g_fix_{short}", d["fixed"], d["bad"]); kn(f"g_occue_{short}", d["changed_ok"], d["ok"])
    put(f"g_sp0_{short}", f"{100 * d['sp0']:.1f}"); put(f"g_sp1_{short}", f"{100 * d['sp1']:.1f}")
# ---------------- I2 set
for lab, key in (("pc", "polarity+certainty"), ("pol", "polarity"), ("cer", "certainty"), ("agt", "agent"),
                 ("act", "speech_act"), ("pz", "politeness"), ("tq", "time_quantity"), ("all", "all")):
    for arm in ("S3", "P2", "I2", "I2t"):
        pc(f"s_{lab}_{arm.lower()}", sr[key][arm])
    pc(f"s_{lab}_d", sr[key]["diff_I2"]); pc(f"s_{lab}_dt", sr[key]["diff_I2t"])
    pc(f"s_{lab}_loss", sr[key]["diff_I2"], sign=-1)
for lab, key in (("pc", "polarity+certainty"), ("act", "speech_act"), ("pz", "politeness"), ("agt", "agent")):
    sc = s["set_counts"][key]
    kn(f"sc_{lab}_p2", sc["p2"], sc["n"]); kn(f"sc_{lab}_i2", sc["i2"], sc["n"])
    kn(f"sc_{lab}_gain", sc["gained"], sc["p2_uncovered"]); kn(f"sc_{lab}_lost", sc["lost"], sc["p2_covered"])
for _lab, _key in (("pz", "politeness"), ("act", "speech_act"), ("pc", "polarity+certainty")):  # two-decimal views
    pc(f"s_{_lab}_lossx", sr[_key]["diff_I2"], sign=-1, d=2); pc(f"s_{_lab}_dx", sr[_key]["diff_I2"], d=2)
pc("s_coll", s["collateral_lost"]); put("s_coll_fam", s["collateral_lost"]["n_families"])
kn("s_coll_cov", s["collateral_lost_of_covered"]["k"], s["collateral_lost_of_covered"]["n"])
kn("s_coll_gain", s["collateral_gained"]["k"], s["collateral_gained"]["n"])
pc("s_drift", s["act_drift"]); put("s_edit_fam", s["edits"]["families"])
pc("s_drift_cer", s["act_drift_by_dim"]["certainty"]); pc("s_drift_pol", s["act_drift_by_dim"]["polarity"])
pc("s_drift_diff", s["act_drift_cer_minus_pol"]); pc("s_drift_ach", s["act_drift_achieved"])
put("s_drift_stmt", s["act_drift_to_statement"])
for m, short in (("qwen2.5-7b", "qwen"), ("gemma3-4b", "gemma"), ("llama3.1-8b", "llama"), ("gpt-6.1-terra", "terra")):
    d = s["act_drift_by_model"][m]; kn(f"s_drift_{short}", d["k"], d["n"])
kn("s_verified", s["edits"]["verified"], s["edits"]["n"]); kn("s_achieved", s["edits"]["achieved"], s["edits"]["n"])
put("s_calls", f"{sr['cost_I2']['calls_per_set']:.2f}"); put("s_lat", f"{sr['cost_I2']['lat_per_set']:.2f}")
put("s_calls_t", f"{sr['cost_I2t']['calls_per_set']:.2f}"); put("s_sets", sr["cost_I2"]["sets"])
# ---------------- chips
for k in ("bare", "noncrit", "chip1", "chipall", "full", "lost_with_chip", "miss_persists", "chip1_contra",
          "chip1_pol_add", "noncrit_pol_add"):
    pc("c_" + k.replace("_", ""), c[k])
pc("c_d", c["d_chip1_noncrit"])
put("c_nchips", f"{c['chipall_mean_chips']:.1f}"); put("c_ratio", f"{100 * c['chip1']['estimate'] / c['full']['estimate']:.1f}")
put("c_n", c["n_targets"])
for dim, short in (("speech_act", "act"), ("politeness", "pz"), ("polarity", "pol"), ("certainty", "cer"),
                   ("agent", "agt"), ("time_quantity", "tq")):
    put(f"c_{short}_chip1", f"{100 * c['by_dim'][dim]['chip1']:.1f}"); put(f"c_{short}_noncrit", f"{100 * c['by_dim'][dim]['noncrit']:.1f}")
nd = EV["nondeterminism"]
for k in ("api_min", "api_max", "local_min", "local_max"):
    put("nd_" + k.replace("_min", "_min").replace("api", "api").replace("local", "local"), f"{100 * nd[k]:.1f}")
for m, short in (("qwen2.5-7b", "qwen"), ("gemma3-4b", "gemma"), ("llama3.1-8b", "llama"), ("gpt-6.1-terra", "terra")):
    d = c["by_model"][m]
    put(f"c_noncrit_{short}", f"{100 * d['noncrit']:.1f}"); put(f"c_chip1_{short}", f"{100 * d['chip1']:.1f}")
# ---------------- kill verdicts (computed, never typed)
put("kill_i1", "passed" if gr["G1_cue"]["fix"]["estimate"] >= .30 and gr["G1_all"]["overcorr"]["estimate"] <= .10 else "failed")
put("kill_i2", "passed" if sr["polarity+certainty"]["diff_I2"]["estimate"] >= .30 else "failed")
put("kill_chip", "passed" if c["d_chip1_noncrit"]["estimate"] >= .10 and c["chip1"]["estimate"] >= .8 * c["full"]["estimate"] else "failed")


# ---------------- pending inputs (conditional slots)
def leaves(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{path}_{k}" if path else str(k))
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, x


for name, ready in EV["pending"].items():
    if not ready or name in ("wc", "wd", "repair_audit"):
        continue
    put(f"{name}_ready", 1)
    f = ROOT / {"wc": "analysis/r2c/report.json", "wd": "analysis/r2d/report.json", "t3": "analysis/t3/report.json",
                "repair_audit": "annotation/repair_audit/results.json"}.get(name, "")
    if f.suffix == ".json" and f.exists():
        for pth, v in leaves(json.loads(f.read_text())):
            key = f"{name}__" + "".join(ch if ch.isalnum() else "_" for ch in pth)
            put(key, f"{v:.3g}" if isinstance(v, float) else v)


# ---------------- round-2 evidence read directly from the frozen analysis JSON/CSV files
# (W-C headline/primary, W-C ladder CSVs, applicability results.json, W-D headline.json).
# Nothing below is typed: every value is read from a stored file and formatted here.
import csv  # noqa: E402


def pcu(k: str, est, lo=None, hi=None, d=2) -> None:
    """Unit-scale estimate (and optional CI) -> percent macros k, k_lo, k_hi."""
    put(k, f"{100 * est:.{d}f}")
    if lo is not None:
        lo, hi = sorted((100 * lo, 100 * hi))
        put(k + "_lo", f"{lo:.{d}f}"); put(k + "_hi", f"{hi:.{d}f}")


def csv_row(path: Path, **match) -> dict:
    with path.open() as fh:
        for r in csv.DictReader(fh):
            if all(r.get(c) == v for c, v in match.items()):
                return r
    raise KeyError(f"{path}: no row {match}")


R2C = ROOT / "analysis/r2c"
if (R2C / "headline.json").exists() and (R2C / "primary.json").exists():
    put("wc_ready", 1)
    H = json.loads((R2C / "headline.json").read_text())
    PR = json.loads((R2C / "primary.json").read_text())["primaries"]
    for key in [k for k in H if k + "_ci_low" in H]:
        pcu("wc_" + key.replace("_", ""), H[key], H[key + "_ci_low"], H[key + "_ci_high"])
        put("wc_" + key.replace("_", "") + "_n", f"{H[key + '_n']:,}")
        put("wc_" + key.replace("_", "") + "_ntot", f"{H[key + '_n_total']:,}")
        put("wc_" + key.replace("_", "") + "_ncl", H[key + "_n_clusters"])
    for c in ("p1", "p2", "p3"):
        put(f"wc_{c}_pholm", f"{PR[c.upper()]['p_holm']:.4f}".lstrip("0"))
        put(f"wc_{c}_reject", "passed" if PR[c.upper()]["reject_holm_005"] else "failed")
    kn("wc_poladd", PR["P2"]["addition"]["sum"], PR["P2"]["addition"]["n"])
    kn("wc_polrem", PR["P2"]["removal"]["sum"], PR["P2"]["removal"]["n"])
    put("wc_fam", H["n_families"]); put("wc_fam_incl", H["n_families_inclusive"])
    put("wc_clusters", H["n_clusters"]); put("wc_early", H["pre_freeze_cache_requests"])
    put("wc_arb_rows", H["arbiter_resolved_rows"])
    with (R2C / "primary_pre_freeze_cache.csv").open() as fh:
        put("wc_early_primary", len({r["request_key"] for r in csv.DictReader(fh)}))
    arb = json.loads((R2C / "arbitration/agreement.json").read_text())
    put("wc_arb_units", arb["n_units"])
    # speech-act ladder (P0): noncrit, chip1, full; and chip1-full paired difference
    lad = R2C / "channel_ladder.csv"
    for ch in ("bare", "noncrit", "chip1", "chipall", "full"):
        r = csv_row(lad, dimension="speech_act", channel=ch, metric="critical_match")
        pcu(f"wc_act_{ch}", float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"]))
        kn(f"wc_act_{ch}c", float(r["sum"]), int(r["n"]))
    for dim, short in (("polarity", "pol"), ("politeness", "pz")):
        for ch in ("chip1", "full"):
            r = csv_row(lad, dimension=dim, channel=ch, metric="critical_match")
            pcu(f"wc_{short}_{ch}", float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"]))
    r = csv_row(R2C / "channel_differences.csv", dimension="speech_act", metric="chip1-full")
    pcu("wc_act_gap", float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"]))
    put("wc_act_gap_n", r["n"]); put("wc_act_gap_ncl", r["n_clusters"])
    put("wc_act_fam", csv_row(lad, dimension="speech_act", channel="chip1", metric="critical_match")["n_families"])
    a_chip = float(csv_row(lad, dimension="speech_act", channel="chip1", metric="critical_match")["estimate"])
    a_full = float(csv_row(lad, dimension="speech_act", channel="full", metric="critical_match")["estimate"])
    a_nonc = float(csv_row(lad, dimension="speech_act", channel="noncrit", metric="critical_match")["estimate"])
    put("wc_act_ratio", f"{100 * a_chip / a_full:.1f}")
    put("wc_kill_gain", "passes" if a_chip - a_nonc >= .10 else "fails")
    put("wc_kill_ratio", "passes" if a_chip >= .8 * a_full else "fails")
    put("wc_kill_chip", "passed" if (a_chip - a_nonc >= .10 and a_chip >= .8 * a_full) else "failed")
    q = csv_row(R2C / "cue_value_match.csv", dimension="speech_act", cv="question", metric="critical_match")
    kn("wc_qfail", int(q["n"]) - float(q["sum"]), int(q["n"]))
    # selected W-C example (hash-first question chip1 failure), from the stored example manifest
    for ex in json.loads((R2C / "examples.json").read_text()):
        if ex["category"] == "Question cue failure":
            put("wc_ex_q_model", {"llama3.1-8b": "Llama", "qwen2.5-7b": "Qwen", "gemma3-4b": "Gemma",
                                  "gpt-6.1-terra": "Terra"}[ex["model"]])

APP = ROOT / "analysis/applicability/results.json"
if APP.exists():
    put("app_ready", 1)
    A = json.loads(APP.read_text())["preserved"]
    for ch in ("full", "chip1", "chipall"):
        for arm in ("P0", "P2", "S3"):
            x = A[f"H1/{ch}"][arm]
            pcu(f"app_{ch}_{arm.lower()}", x["estimate"], x["lo"], x["hi"])
            kn(f"app_{ch}_{arm.lower()}c", x["k"], x["n"])
        d = A[f"H1/{ch}"]["P2_minus_S3"]
        pcu(f"app_{ch}_d", d["estimate"], d["lo"], d["hi"])
        put(f"app_{ch}_avail", f"{A[f'H1/{ch}']['available_targets']:,}")
        put(f"app_{ch}_ncl", d["clusters"])
    ep = A["H1/exact_partner"]
    for arm in ("P0", "P2", "S3"):
        kn(f"app_ex_{arm.lower()}", ep[arm]["k"], ep[arm]["n"])
        pcu(f"app_ex_{arm.lower()}", ep[arm]["estimate"], ep[arm]["lo"], ep[arm]["hi"])
    pcu("app_ex_d", ep["P2_minus_S3"]["estimate"], ep["P2_minus_S3"]["lo"], ep["P2_minus_S3"]["hi"])
    put("app_ex_ncl", ep["P2_minus_S3"]["clusters"])
    der = json.loads(APP.read_text())["derivative"]
    x = der["early_cache_sensitivity"]["full"]
    pcu("app_full_d_noearly", x["estimate"], x["lo"], x["hi"])
    # W-D NOTxYOU cell decomposition (C32)
    h2 = A["H2"]
    kn("wd_notyou", h2["NOT|YOU"]["k"], h2["NOT|YOU"]["n"]); kn("wd_othercells", h2["other"]["k"], h2["other"]["n"])
    kn("wd_negabsent", h2["among_damage"]["negation_absent"]["k"], h2["among_damage"]["negation_absent"]["n"])

WD = ROOT / "analysis/r2d/headline.json"
if WD.exists():
    put("wd_ready", 1)
    W = json.loads(WD.read_text())
    put("wd_scen", W["n_clusters"])
    for key, short in (("statement_polarity_llama", "llpol"), ("tell_agent_qwen", "qwagt")):
        pcu(f"wd_{short}", W[key + "_damage"], W[key + "_damage_ci_low"], W[key + "_damage_ci_high"])
        kn(f"wd_{short}c", W[key + "_damage_k"], W[key + "_damage_n"])
        put(f"wd_{short}_scen", W[key + "_damage_n_event_clusters"])
        kn(f"wd_{short}_rep", W[key + "_repeat_disagreement_k"], W[key + "_repeat_disagreement_n"])
        kn(f"wd_{short}_repboth", W[key + "_both_repeat_disagreement_k"], W[key + "_both_repeat_disagreement_n"])
        pcu(f"wd_{short}_dboth", W[key + "_damage_minus_both_repeat"], W[key + "_damage_minus_both_repeat_ci_low"],
            W[key + "_damage_minus_both_repeat_ci_high"])

# ---------------- frozen guard transfer to W-C speech act (accepted with qualifications).
# Read from analysis/guard_wc/headline.json (written by analysis/guard_wc/analyze.py + close_action1.py from
# scored.parquet / paired_G1*.parquet). Separate population from the discovery guard result above. Prefix gt_.
GT = ROOT / "analysis/guard_wc/headline.json"
if GT.exists():
    T = json.loads(GT.read_text())
    assert T["status"] == "complete", T["status"]
    put("gt_ready", 1)
    put("gt_fam", T["n_families"]); put("gt_targets", f"{T['n_targets']:,}"); put("gt_unique", f"{T['n_unique']:,}")
    put("gt_F", f"{T['F']:,}")

    def pcg(k: str, r: dict, d=2) -> None:
        pc(k, r, d=d)
        if "k" in r:
            put(k + "_k", f"{int(round(r['k'])):,}")
        if "n" in r:
            put(k + "_n", f"{int(r['n']):,}")

    for arm in ("P0", "G1", "G1s"):
        a = arm.lower()
        pcg(f"gt_jp_{a}", T["arms"][arm]["joint_pass"]); pcg(f"gt_sp_{a}", T["arms"][arm]["strict_pass"])
        pcg(f"gt_pa_{a}", T["arms"][arm]["politeness_added"])
    for arm in ("G1", "G1s"):
        a = arm.lower()
        P = T["paired"][arm]
        for key, short in (("joint_gain", "jgain"), ("strict_gain", "sgain"), ("strict_repair", "rep"),
                           ("strict_changed_correct", "cc"), ("strict_pass_to_fail", "pf"),
                           ("strict_residual", "res"), ("joint_repair", "jrep")):
            pcg(f"gt_{short}_{a}", P[key])
        put(f"gt_resflag_{a}_k", P["strict_residual_flagged"]); put(f"gt_resflag_{a}_n", P["strict_residual_targets"])
        put(f"gt_flagged_{a}", P["initial_flagged_targets"])
    for end in ("joint", "strict"):
        cmp_ = T["G1_minus_G1s"][end]
        pcg(f"gt_cmp_{end}", cmp_["family"])
        put(f"gt_cmp_{end}_g1only", cmp_["G1_only_pass"]); put(f"gt_cmp_{end}_g1sonly", cmp_["G1s_only_pass"])
    cr = T["criteria"]
    put("gt_verdict", "passed" if T["transfer_success"] and all(cr.values()) else "failed")
    for k, v in cr.items():
        put("gt_crit_" + k.replace("_", ""), "passes" if v else "fails")
    put("gt_rep_ge30", "passes" if T["paired"]["G1"]["strict_repair"]["estimate"] >= .30 else "fails")
    put("gt_cc_le10", "passes" if T["paired"]["G1"]["strict_changed_correct"]["estimate"] <= .10 else "fails")
    put("gt_usable_validated", "yes" if T.get("usable_repair_validated") else "no")
    co = T["cost"]
    put("gt_calls", f"{co['calls_per_input']:.2f}"); put("gt_calls_flag", f"{co['calls_per_flagged']:.2f}")
    # Actual HTTP calls come from the formal acceptance audit (analysis/guard_wc/ACCEPTANCE.md ->
    # acceptance_check.json), which corrects an earlier unsupported "937 calls" figure.
    AC = json.loads((ROOT / "analysis/guard_wc/acceptance_check.json").read_text())
    assert AC["verdict"] == "ACCEPT WITH QUALIFICATIONS", AC["verdict"]
    ac = AC["calls"]
    assert ac["retry_generation_http"] == co["actual_generation_calls"], "acceptance vs headline generation calls"
    assert ac["judge_batch_http"] == co["actual_judge_batch_calls"], "acceptance vs headline judge batches"
    put("gt_gen_calls", f"{ac['retry_generation_http']:,}"); put("gt_gen_cap", f"{AC['frozen_limits']['retry_generation_http']:,}")
    put("gt_gen_failed", f"{ac['retry_generation_failed']:,}")
    put("gt_judge_calls", f"{ac['judge_batch_http']:,}"); put("gt_judge_cap", f"{AC['frozen_limits']['judge_batch_http']:,}")
    put("gt_judge_failed", f"{ac['judge_batch_failed']:,}")
    put("gt_judge_conc", f"{AC['concurrency']['judge_peak']}")
    put("gt_probe_calls", f"{AC['uninstrumented_http']['inferred_probe_calls']}")
    put("gt_probe_calls_word", {0: "no", 1: "one", 2: "two", 3: "three"}[AC['uninstrumented_http']['inferred_probe_calls']])
    put("gt_accepted", "accepted with qualifications")
    put("gt_resid_flag_unique", f"{co['residual_flagged_unique']:,}")
    for m, short in (("qwen2.5-7b", "qwen"), ("gemma3-4b", "gemma"), ("llama3.1-8b", "llama"), ("gpt-6.1-terra", "terra")):
        pm = T["per_model"][m]["paired"]["G1"]
        pcg(f"gt_jgain_{short}", pm["joint_gain"]); pcg(f"gt_rep_{short}", pm["strict_repair"])
    for ch in ("chip1", "chipall", "full"):
        pch = T["per_channel"][ch]
        pcg(f"gt_jp_p0_{ch}", pch["arms"]["P0"]["joint_pass"]); pcg(f"gt_jp_g1_{ch}", pch["arms"]["G1"]["joint_pass"])
    # declared-rule transfer examples: event counts must match the headline counts
    for ex in json.loads((ROOT / "analysis/guard_wc/examples.json").read_text()):
        if ex["category"] == "correct-text-changed":
            assert (ex["event_k"], ex["eligible_n"]) == (T["paired"]["G1"]["strict_changed_correct"]["k"],
                                                         T["paired"]["G1"]["strict_changed_correct"]["n"])
            put("gt_ex_cc_model", {"llama3.1-8b": "Llama", "qwen2.5-7b": "Qwen", "gemma3-4b": "Gemma",
                                   "gpt-6.1-terra": "Terra"}[ex["model"]])
# discovery guard: strip-only gain over P0 (strict, cue targets) from the C35 pass counts, for the guard display
_inc = EV["guard"]["increment_vs_strip"]
put("g_s_gain", f"{100 * (_inc['pass_counts']['G1s'] - _inc['pass_counts']['P0']) / _inc['n']:.2f}")
put("g_cmp_n", f"{_inc['n']:,}")
for _arm in ("P0", "G1", "G1s"):  # constraint-preserving = joint supplied-predicate pass (same construct as gt_jp_*)
    pc(f"g_cpx_{_arm.lower()}", EV["guard"]["report"][_arm]["cp"], d=2)
_b = EV["guard"]["report"]["G1_cue"]["broken"]
kn("g_broken_cue", round(_b["estimate"] * _b["n"]), _b["n"])

# Repair audit (Part 4): only if human returns were scored by src/score_repair_audit.py
if (ROOT / "analysis/repair_audit/summary.json").exists():
    put("repair_audit_ready", 1)


# ---------------- human gold (W-A): judge vs two human annotators, from score_gold.py --human.
# Same keys as the SE4All paper (shared score_gold.paper_macros, prefix human_); human_gold_ready
# switches on the conditional slot whenever the human section exists.
JV = ROOT / "annotation/judge_validation_main1.json"
if JV.exists():
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from score_gold import paper_macros
    hm = paper_macros(json.loads(JV.read_text()).get("human") or {}, "human")
    for k, v in hm.items():
        put(k, v)
    if hm:
        put("human_gold_ready", 1)


# ---------------- cycle-1 additions: repair-usability audits, hw1 replication, human keyword elicitation.
# Everything below is read from stored analysis files; design constants are typed and marked as such.
import csv as _csv

def _ci(k, est, lo, hi, d=1):
    put(k, f"{100 * est:.{d}f}"); put(k + "_lo", f"{100 * lo:.{d}f}"); put(k + "_hi", f"{100 * hi:.{d}f}")

_ra = json.loads((ROOT / "analysis/repair_audit/summary.json").read_text())
for _arm, _t in (("repaired", "rep"), ("control", "ctl")):
    _u = _ra["per_arm"][_arm]["usable"]
    _ci(f"ra_{_t}", _u["p"], *_u["ci"]); kn(f"ra_{_t}_c", _u["k"], _u["n"]); put(f"ra_{_t}_unk", _u["unknown"])
    put(f"ra_{_t}_items", _ra["per_arm"][_arm]["items"])
_d = _ra["difference_repaired_minus_control"]["usable"]
_ci("ra_gap", _d["diff"], *_d["ci"])
put("ra_raters", len(_ra["annotators"]))
_rt = json.loads((ROOT / "analysis/repair_audit_transfer/summary.json").read_text())
for _arm, _t in (("repaired", "rep"), ("control", "ctl")):
    _u = _rt["per_arm"][_arm]["usable"]
    _ci(f"rt_{_t}", _u["p"], *_u["ci"]); kn(f"rt_{_t}_c", _u["k"], _u["n"])
    put(f"rt_{_t}_items", _rt["per_arm"][_arm]["items"])
# Declared example rule: the first (hash_rank order) consensus-unusable repaired items of each pool.
for _pre, _f in (("ra", "repair_audit"), ("rt", "repair_audit_transfer")):
    _rows = [r for r in _csv.DictReader((ROOT / f"analysis/{_f}/items.csv").open()) if r["arm"] == "repaired"]
    _bad = sorted((r for r in _rows if r["cons_usable"] == "False"), key=lambda r: int(r["hash_rank"]))
    kn(f"{_pre}_unusable", len(_bad), sum(1 for r in _rows if r["cons_usable"] in ("True", "False")))
    for _i, r in enumerate(_bad[:3]):
        _inp = r["input_text"].replace("Keywords: ", "")
        put(f"{_pre}_ex{_i}_in", _inp); put(f"{_pre}_ex{_i}_out", r["text"])
        put(f"{_pre}_ex{_i}_model", r.get("assigned_model", ""))
    put(f"{_pre}_ex_echo", sum(1 for r in _bad[:3] if r["text"].startswith(("Ask you", "Tell you"))))  # among the three SHOWN (caption)
    put(f"{_pre}_echo_all", sum(1 for r in _bad if r["text"].startswith(("Ask you", "Tell you"))))
# Part 17 design constants (typed; frozen in annotation/COORDINATOR_STEPS.md section 4)
put("p18_per_writer", 10); put("p17_texts", 120); put("p17_raters", 3); put("p17_margin", 10)
# hw1 human-written replication
_h = json.loads((ROOT / "analysis/hw1/summary.json").read_text())
_hc = {(r["contrast"], r["cluster"]): r for r in _csv.DictReader((ROOT / "analysis/hw1/primary_contrasts.csv").open())}
for _c, _n in (("P1", "hw_p1"), ("P2", "hw_p2")):
    _r = _hc[(_c, "writer")]; _ci(_n, float(_r["estimate"]), float(_r["ci_low"]), float(_r["ci_high"]))
_p3 = _h["P3_affirmative_share"]; _ci("hw_p3", _p3["estimate"], _p3["ci_low"], _p3["ci_high"])
_cg = [r for r in _csv.DictReader((ROOT / "analysis/hw1/chip_gain.csv").open()) if r["model"] == "ALL"]
put("hw_chip_min", f"{100 * min(float(r['estimate']) for r in _cg):.1f}")
put("hw_chip_max", f"{100 * max(float(r['estimate']) for r in _cg):.1f}")
put("hw_chip_dims", len(_cg))
put("hw_kept", _h["n_kept"]); put("hw_wr_min", min(_h["writers_by_dim"].values())); put("hw_wr_max", max(_h["writers_by_dim"].values()))
put("hw_maxshift", f"{max(_h['max_shift_pp'].values()):.1f}")
# human keyword elicitation (Part 9)
_e = json.loads((ROOT / "analysis/elicitation/summary.json").read_text())
for _dim, _t in (("polarity", "el_pol"), ("politeness", "el_pt")):
    _b = _e["by_dimension"][_dim]["lenient"]
    _ci(_t + "_h", _b["human_pooled"]["p"], *_b["human_pooled"]["ci"])
    _ci(_t + "_c", _b["pos_cap4"]["p"], *_b["pos_cap4"]["ci"])
put("el_alpha", f"{_e['agreement']['alpha_lenient_loss']:.2f}")
put("el_msgs", _e["n_messages_rated"]); put("el_sets", _e["n_ratings_valid"]); put("el_annot", len(_e["annotators"]))
# judge validation on the new human data
for _f, _t in (("judge_validation_elic.json", "jve"), ("judge_validation_hw.json", "jvh")):
    _jp = ROOT / "annotation" / _f
    put(_t + "_ready", 1) if _jp.exists() else None


# ---------------- cycle-2 additions (all read from stored files; design assumptions typed and labelled)
import math as _m
import re as _re


def _newcombe(k1, n1, k0, n0, z=1.96):
    """Newcombe hybrid-score 95% CI for p1 - p0 (the interval the audit's frozen rule names)."""
    def wil(k, n):
        p = k / n
        d = 1 + z * z / n
        c = (p + z * z / (2 * n)) / d
        h = z * _m.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
        return c - h, c + h
    l1, u1 = wil(k1, n1); l0, u0 = wil(k0, n0)
    p1, p0 = k1 / n1, k0 / n0
    return (p1 - p0, p1 - p0 - _m.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), p1 - p0 + _m.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2))


# pooled pilots (descriptive, post hoc; the frozen decision rule applies to the larger audit, not to this)
_kr = _ra["per_arm"]["repaired"]["usable"]; _kc = _ra["per_arm"]["control"]["usable"]
_tr = _rt["per_arm"]["repaired"]["usable"]; _tc = _rt["per_arm"]["control"]["usable"]
_g, _lo, _hi = _newcombe(_kr["k"] + _tr["k"], _kr["n"] + _tr["n"], _kc["k"] + _tc["k"], _kc["n"] + _tc["n"])
put("pp_gap", f"{100 * _g:.1f}"); put("pp_gap_lo", f"{100 * _lo:.1f}"); put("pp_gap_hi", f"{100 * _hi:.1f}")
put("pp_rep_k", _kr["k"] + _tr["k"]); put("pp_rep_n", _kr["n"] + _tr["n"])
put("pp_ctl_k", _kc["k"] + _tc["k"]); put("pp_ctl_n", _kc["n"] + _tc["n"])
put("pp_rep", f"{100 * (_kr['k'] + _tr['k']) / (_kr['n'] + _tr['n']):.1f}")
put("pp_ctl", f"{100 * (_kc['k'] + _tc['k']) / (_kc['n'] + _tc['n']):.1f}")
# do raters agree that scored-passing repairs preserve the meaning? (all repaired items are scorer passes)
for _pre, _f in (("ra", "repair_audit"), ("rt", "repair_audit_transfer")):
    _rows = [r for r in _csv.DictReader((ROOT / f"analysis/{_f}/items.csv").open()) if r["arm"] == "repaired"]
    _res = [r for r in _rows if r["cons_preserving"] in ("True", "False")]
    kn(f"{_pre}_pres", sum(r["cons_preserving"] == "True" for r in _res), len(_res))
# input vs target accounting for the guard display (definitions printed in the caption)
put("g_amb_req", f"{EV['guard']['report']['cost']['inputs'] - EV['guard']['n_cue_targets']:,}")
# page-1 examples: real stored strings, each chosen by its declared rule (see figs/make_caleai_figs.py)
for _ex in json.loads((ROOT / "analysis/guard_wc/examples.json").read_text()):
    if _ex["category"] == "correct-text-changed":
        put("bx1_in", _ex["input_text"].replace("Keywords: ", "")); put("bx1_before", _ex["before"]); put("bx1_after", _ex["after"])
        put("bx1_k", _ex["event_k"]); put("bx1_n", f"{_ex['eligible_n']:,}")
for _x in EV["span"]["gallery"]:
    if _x["kind"] == "loss":
        put("bx2_in", _x["bare"]); put("bx2_before", _x["P2"]["texts"][2]); put("bx2_after", _x["I2"]["texts"][2])
for _x in EV["guard"]["gallery"]:
    if (_x["category"], _x["rank"]) == ("fixed", 2):
        put("bx3_in", _x["input"].replace("Keywords: ", "")); put("bx3_before", _x["before"]); put("bx3_after", _x["after"])
# ---- design constants for the pre-specified human-effect study (TYPED assumptions, labelled as such in the paper)
_z = 1.96 + 0.8416                                     # two-sided 5% size, 80% power
_pc = _kc["k"] / _kc["n"]                              # control usable rate taken from the pilot
put("dz_ctl_assumed", f"{100 * _pc:.0f}")
put("dz_mde", f"{100 * _z * _m.sqrt(2 * _pc * (1 - _pc) / 60):.0f}")   # detectable gap with 60 vs 60 texts (3 raters, consensus)
_writers = {m for l in (ROOT / "data/items/hw.jsonl").read_text().splitlines()
            for m in _re.findall(r"writer (P\d+)", json.loads(l).get("notes") or "")}
put("hw_writers", len(_writers))
_icc, _m_per = 0.2, 10                                 # assumed within-writer correlation; outputs judged per writer
_neff = len(_writers) * _m_per / (1 + (_m_per - 1) * _icc)
put("dz_icc", _icc); put("dz_p18_judg", len(_writers) * _m_per); put("dz_p18_neff", f"{_neff:.0f}")
put("dz_p18_mde", f"{100 * _z * _m.sqrt(2 * 0.25 / _neff):.0f}")      # detectable agreement gap, worst case p = .5
_d_mrt, _T, _rho = 0.2, 40, 0.3                        # standardized proximal effect, decision points per user, within-user correlation
put("mrt_d", _d_mrt); put("mrt_T", _T); put("mrt_rho", _rho)
put("mrt_msgs", f"{_m.ceil(_T / (EV['guard']['report']['cost']['flagged'] / EV['guard']['report']['cost']['inputs']))}")
put("mrt_users", f"{_m.ceil(2 * (_z / _d_mrt) ** 2 * (1 + (_T - 1) * _rho) / _T)}")

# ---------------- cycle 3: robustness analyses (analysis/robust/*/summary.json); no typed results
RB = ROOT / "analysis/robust"
def _rj(name):
    return json.loads((RB / name / "summary.json").read_text())

def _f(x, d=1):
    return f"{100 * x:.{d}f}"

# Part 4 repair-audit confounds
_ac = _rj("repair_audit_confounds")
_u = next(e for e in _ac["endpoints"] if e["endpoint"] == "usable")["unknown = unusable/failing"]
put("ra_unk_gap", _f(_u["diff"])); put("ra_unk_gap_lo", _f(_u["diff_ci"][0])); put("ra_unk_gap_hi", _f(_u["diff_ci"][1]))
put("ra_unk_rep", _f(_u["repaired"]["p"], 0)); put("ra_unk_ctl", _f(_u["control"]["p"], 0))
put("ra_effn", f"{_ac['rater_patterns']['design_effect_effective_raters']:.1f}")
put("ra_rho", f"{_ac['rater_patterns']['mean_pairwise_correlation_usable']:.2f}")
put("ra_usable_patterns", _ac["rater_patterns"]["distinct_usable_binary_patterns"])
_pf = _ac["composition"]["p0_strict_fail"]
assert _pf["control"] == {"False": 20}
kn("ra_repfail", _pf["repaired"]["True"], sum(_pf["repaired"].values()))
put("ra_ctl_passed_n", sum(_pf["control"].values()))
_dm = _ac["composition"]["dim"]
put("ra_dim_pol_rep", _dm["table"]["repaired"]["politeness"]); put("ra_dim_pol_ctl", _dm["table"]["control"]["politeness"])
put("ra_dim_p", f"{_dm['perm_p']:.3f}")

# T2: affirmative default as the Bayes-preferred guess; asymmetric cost
_t2 = _rj("t2_posterior"); _tt = {(r["dimension"], r["channel"]): r for r in _t2["table"]}
_ph, _pcx = _tt[("polarity", "human")], _tt[("polarity", "pos_cap4")]
put("t2_post_h", _f(_ph["posterior_empirical"])); put("t2_post_h_lo", _f(_ph["posterior_empirical_lo"])); put("t2_post_h_hi", _f(_ph["posterior_empirical_hi"]))
put("t2_post_c", _f(_pcx["posterior_empirical"])); put("t2_post_c_lo", _f(_pcx["posterior_empirical_lo"])); put("t2_post_c_hi", _f(_pcx["posterior_empirical_hi"]))
put("t2_rev_h", f"{_ph['silent_reversal_per_1000']:.0f}"); put("t2_rev_h_lo", f"{_ph['silent_reversal_per_1000_lo']:.0f}"); put("t2_rev_h_hi", f"{_ph['silent_reversal_per_1000_hi']:.0f}")
put("t2_acc_h", _f(1 - _ph["posterior_empirical"])); put("t2_post_h_bayes", _f(_ph["posterior_bayes_corpus_pi"]))
put("t2_spur_h", f"{_ph['spurious_cue_per_1000']:.1f}")
put("t2_aff_h", _f(1 - _ph["model_share_cue_given_nocue"]))
put("t2_ratio_h", f"{_ph['breakeven_cost_ratio']:.0f}")
put("t2_neg_prev", _f(_t2["corpus_prevalence_detector_6142"]["neg"]))
_po = _tt[("politeness", "human")]
put("t2_pol_post", _f(_po["posterior_empirical"])); put("t2_pol_model", _f(_po["model_share_cue_given_nocue"]))
_sa = _tt[("speech_act", "human")]
put("t2_sa_post", _f(_sa["posterior_empirical"])); put("t2_sa_model", _f(_sa["model_share_cue_given_nocue"]))
put("t2_d_h", _f(_ph["d_loss"])); put("t2_d_h_lo", _f(_ph["d_loss_lo"])); put("t2_d_h_hi", _f(_ph["d_loss_hi"]))

# T4: "Can you ...?" coded as a statement-request (base) or as a question
_t4 = {(r["run"], r["variant"]): r for r in _rj("t4_codebook")["speech_act_chip_gain"]}
_b, _a = _t4[("W-C r2c1", "base")], _t4[("W-C r2c1", "a_can_you_question")]
put("t4_wc_base", _f(_b["estimate"])); put("t4_wc_alt", _f(_a["estimate"])); put("t4_wc_alt_lo", _f(_a["ci_low"])); put("t4_wc_alt_hi", _f(_a["ci_high"]))
put("t4_hw_base", _f(_t4[("hw1", "base")]["estimate"])); put("t4_hw_alt", _f(_t4[("hw1", "a_can_you_question")]["estimate"]))

# T6: human-written pairs, writer-level inference (t intervals; exact writer sign-flip randomization)
_t6 = _rj("t6_small_cluster")
for _c, _n in (("P1", "t6_p1"), ("P2", "t6_p2"), ("P3", "t6_p3")):
    _r = _t6["contrasts"][_c]
    put(_n + "_w", _r["writers"]); put(_n + "_rp", f"{_r['sign_flip_randomization']['p_one_sided']:.3f}")
    put(_n + "_holm", f"{_t6['holm_signflip_one_sided'][_c]:.3f}")
    assert _r["sign_flip_randomization"]["all_writer_signs_positive"]
    if _c != "P3":
        put(_n, _f(_r["estimate"])); put(_n + "_lo", _f(_r["t_ci_low"])); put(_n + "_hi", _f(_r["t_ci_high"]))
put("t6_minp", f"{min(r['sign_flip_randomization']['min_attainable_one_sided'] for r in _t6['contrasts'].values()):.4f}")

# T7: ties and unresolved items counted as disagreement (R1)
_t7 = _rj("t7_human_gate"); _gs = ("main1_H7_A1A2", "part12_elic", "part13_hw")
_crit = [_t7[g]["dims"]["critical"]["test/R1"]["kappa"] for g in _gs]
put("t7_crit_min", f"{min(_crit):.3f}"); put("t7_crit_max", f"{max(_crit):.3f}")
_ac_k = [_t7[g]["dims"]["added_content"]["test/R1"]["kappa"] for g in _gs]
put("t7_ac_min", f"{min(_ac_k):.3f}"); put("t7_ac_max", f"{max(_ac_k):.3f}")
for _g in _gs:  # added_content is lowest, or within 0.02 of the lowest, among the seven fields in every gate
    _ks = [v["test/R1"]["kappa"] for k, v in _t7[_g]["dims"].items() if k != "critical" and "test/R1" in v]
    assert _t7[_g]["dims"]["added_content"]["test/R1"]["kappa"] <= min(_ks) + 0.02, _g

# MRT: proximal outcome on a random subset of sends (typed assumption: collection probability)
_q = 0.5
put("mrt_q", f"{100 * _q:.0f}"); put("mrt_Teff", f"{_T * _q:.0f}")
put("mrt_users_q", f"{_m.ceil(2 * (_z / _d_mrt) ** 2 * (1 + (_T * _q - 1) * _rho) / (_T * _q))}")

# ---- cycle 4: no-feedback resample baseline (analysis/guard_baseline) and legend test (analysis/legend_test)
_gb = json.loads((ROOT / "analysis/guard_baseline/summary.json").read_text())
for _sk, _pre in (("disc", "bd"), ("wc", "bw")):
    _S = _gb[_sk]
    for _a in ("G1", "G1s", "G1r", "G1t"):
        pc(f"{_pre}_jp_{_a.lower()}", _S["arms"][_a]["joint_pass"])
        pc(f"{_pre}_sp_{_a.lower()}", _S["arms"][_a]["strict_pass"])
        _r = _S["paired"][_a]["strict_repair"]
        kn(f"{_pre}_rep_{_a.lower()}", round(_r["k"]), _r["n"])
        _ci = (100 * _r["ci_low"], 100 * _r["ci_high"]); put(f"{_pre}_rep_{_a.lower()}_lo", f"{_ci[0]:.1f}"); put(f"{_pre}_rep_{_a.lower()}_hi", f"{_ci[1]:.1f}")
    for _c, _n in (("G1-G1r", "gr"), ("G1t-G1r", "tr"), ("G1r-G1s", "rs")):
        pc(f"{_pre}_{_n}", _S["contrasts"][_c]["joint"], d=2)
        pc(f"{_pre}_{_n}_strict", _S["contrasts"][_c]["strict"], d=2)
    _ptf = sum(_S["paired"][_a]["strict_pass_to_fail"]["k"] for _a in ("G1", "G1s", "G1r", "G1t"))
    put(f"{_pre}_ptf_all", f"{int(_ptf)}")
    _cs = _gb[_sk]["cost"]["G1r"]
    kn(f"{_pre}_same", _cs["identical_to_original"], _cs["flagged_requests"])
# resampling alone is no better than strip-only: both sets, joint, G1r minus G1s
assert _gb["disc"]["contrasts"]["G1r-G1s"]["joint"]["estimate"] <= 0 and _gb["wc"]["contrasts"]["G1r-G1s"]["joint"]["ci_low"] < 0 < _gb["wc"]["contrasts"]["G1r-G1s"]["joint"]["ci_high"]
assert _gb["disc"]["contrasts"]["G1-G1r"]["joint"]["ci_low"] > 0 and _gb["wc"]["contrasts"]["G1-G1r"]["joint"]["ci_low"] > 0

_lg = json.loads((ROOT / "analysis/legend_test/summary.json").read_text())
for _a, _n in (("a_legend", "a"), ("b_nolegend", "b"), ("c_markers_missing", "c")):
    put(f"lg_{_n}", f"{100 * _lg['pooled_d1'][_a]['aff']:.1f}")
    put(f"lg_{_n}_lo", f"{100 * _lg['pooled_d1'][_a]['lo']:.1f}"); put(f"lg_{_n}_hi", f"{100 * _lg['pooled_d1'][_a]['hi']:.1f}")
    put(f"lg_{_n}_d2", f"{100 * _lg['d2_pooled'][_a]:.1f}")
    put(f"lg_{_n}_commit", f"{100 * _lg['pooled_d1'][_a]['commit']:.1f}")
put("lg_unclear_max", f"{100 * max(1 - _lg['pooled_d1'][_a]['commit'] for _a in _lg['pooled_d1']):.1f}")
put("lg_n_models", len(_lg["per_model_class_d1"]))
assert _lg["unresolved_valid_rows"] == 0 and all(v["cls"] == "not_artifact" for m in _lg["per_model_class_d1"].values() for v in m.values())
assert min(_lg["pooled_d1"][_a]["aff"] for _a in ("b_nolegend", "c_markers_missing")) >= 0.9

# ---- cycle 7: chip controls (C52-C53)
_CC = json.loads((ROOT / "analysis/chip_controls/summary.json").read_text())
_cd = _CC["decision_by_dimension"]
assert _CC["unresolved_valid_ctl_rows"] == 0
put("cc_irrel_min", f"{100 * min(v['chip1_minus_irrel'] for v in _cd.values()):.1f}")
put("cc_irrel_max", f"{100 * max(v['chip1_minus_irrel'] for v in _cd.values()):.1f}")
put("cc_nl_act", f"{-100 * _cd['speech_act']['chip1_minus_nlcue']:.1f}")
_near = [k for k, v in _cd.items() if abs(v["chip1_minus_nlcue"]) < 0.05]
assert "speech_act" not in _near
put("cc_nl_near", len(_near)); put("cc_nl_dims", len(_cd))
put("cc_nl_near_max", f"{100 * max(abs(_cd[k]['chip1_minus_nlcue']) for k in _near):.1f}")

def esc(v: str) -> str:
    v = v.replace("%", r"\%").replace("_", r"\_")
    return "$-$" + v[1:] if v.startswith("-") and v[1:2].isdigit() else v  # typographic minus


from c3_exports import macros as c3_macros
for _key, _value in c3_macros().items():
    put(_key, _value)
lines = ["% AUTO-GENERATED by make_macros.py from evidence.json + analysis/evidence_c3/current.json -- do not edit by hand."]
lines += [f"\\resdef{{{k}}}{{{esc(v)}}}" for k, v in sorted(M.items())]
(HERE / "results_macros.tex").write_text("\n".join(lines) + "\n")
print(f"wrote {len(M)} macros to", HERE / "results_macros.tex")
