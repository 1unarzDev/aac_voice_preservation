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
pc("g_fix", gr["G1_cue"]["fix"]); kn("g_fixc", round(gr["G1_cue"]["fix"]["estimate"] * gr["G1_cue"]["n_bad"]), gr["G1_cue"]["n_bad"])
put("g_fix_fam", gr["G1_cue"]["fix"]["n_families"])
pc("g_fixs", gr["G1s_cue"]["fix"]); kn("g_fixsc", round(gr["G1s_cue"]["fix"]["estimate"] * 80), gr["G1s_cue"]["n_bad"])
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
    if not ready:
        continue
    put(f"{name}_ready", 1)
    f = ROOT / {"wc": "analysis/r2c/report.json", "wd": "analysis/r2d/report.json", "t3": "analysis/t3/report.json",
                "repair_audit": "annotation/repair_audit/results.json"}.get(name, "")
    if f.suffix == ".json" and f.exists():
        for pth, v in leaves(json.loads(f.read_text())):
            key = f"{name}__" + "".join(ch if ch.isalnum() else "_" for ch in pth)
            put(key, f"{v:.3g}" if isinstance(v, float) else v)


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


def esc(v: str) -> str:
    return v.replace("%", r"\%").replace("_", r"\_")


lines = ["% AUTO-GENERATED by make_macros.py from evidence.json -- do not edit by hand."]
lines += [f"\\resdef{{{k}}}{{{esc(v)}}}" for k, v in sorted(M.items())]
(HERE / "results_macros.tex").write_text("\n".join(lines) + "\n")
print(f"wrote {len(M)} macros to", HERE / "results_macros.tex")
