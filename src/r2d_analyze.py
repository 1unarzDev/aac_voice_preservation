"""W-D: encoding-controlled composition, with physical-scenario bootstrap.

Run from any directory with the project venv. No generation, GPU, or network.
All rates in JSON are proportions; figure/report differences are percentage points.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/r2d"
FIG = ROOT / "paper/figs"
SEED, NBOOT = 20261031, 10000
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
SHORT = dict(zip(MODELS, ["qwen", "llama", "gemma", "terra"]))
NAMES = dict(zip(MODELS, ["Qwen2.5 7B", "Llama3.1 8B", "Gemma3 4B", "GPT-6.1 Terra"]))
ENCS, DIMS = ["TELL", "STATEMENT"], ["polarity", "agent"]
TELL_RE = re.compile(r"\b(?:tell|tells|telling|told)\b", re.I)
LITERAL_RE = re.compile(
    r"\b(?:tell|tells|telling|told|say|says|saying|said|state|states|stating|stated)\b"
    r"|\b(?:this|my)\s+(?:is\s+)?(?:a\s+)?statement\b", re.I)


def records(path):
    return [json.loads(s) for s in (ROOT / path).read_text().splitlines() if s.strip()]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


SCENARIOS = [f"r2d-{i:03d}" for i in range(1, 81)]
indices = np.random.default_rng(SEED).integers(0, 80, size=(NBOOT, 80))
WEIGHTS = np.zeros((NBOOT, 80), dtype=np.int16)
np.add.at(WEIGHTS, (np.arange(NBOOT)[:, None], indices), 1)


def ratio(df, numerator, denominator=None):
    """Whole-scenario ratio bootstrap, retaining the same resamples everywhere."""
    x = pd.DataFrame({"scenario": df.scenario, "num": df[numerator].astype(float),
                      "den": 1.0 if denominator is None else df[denominator].astype(float)})
    sums = x.groupby("scenario")[["num", "den"]].sum().reindex(SCENARIOS, fill_value=0)
    a, b = sums.num.to_numpy(), sums.den.to_numpy()
    bsden = WEIGHTS @ b
    bs = np.divide(WEIGHTS @ a, bsden, out=np.full(NBOOT, np.nan), where=bsden > 0)
    good = bs[np.isfinite(bs)]
    ci = np.percentile(good, [2.5, 97.5]) if len(good) else [np.nan, np.nan]
    return {"estimate": float(a.sum() / b.sum()) if b.sum() else None,
            "ci_low": float(ci[0]) if len(good) else None,
            "ci_high": float(ci[1]) if len(good) else None,
            "k": int(a.sum()), "n": int(b.sum()),
            "n_clusters": int((b > 0).sum()), "n_event_clusters": int((a > 0).sum()),
            "n_boot_valid": int(len(good))}, bs


def difference(a, ab, b, bb, n, clusters=80):
    bs = ab - bb
    good = bs[np.isfinite(bs)]
    lo, hi = np.percentile(good, [2.5, 97.5]) if len(good) else (None, None)
    return {"estimate": a["estimate"] - b["estimate"],
            "ci_low": float(lo) if lo is not None else None,
            "ci_high": float(hi) if hi is not None else None,
            "n": int(n), "n_clusters": int(clusters), "n_boot_valid": int(len(good))}, bs


def load():
    d = pd.read_parquet(ROOT / "runs/r2d1/scored.parquet")
    items = {x["family_id"]: x for x in records("data/items/r2_d.jsonl")}
    requests = records("runs/requests/r2d.jsonl")
    bykey = {x["request_key"]: x for x in requests}
    assert len(requests) == len(bykey) == 11520
    assert len(d) == 40960 and d.request_key.nunique() == 11520
    assert d.valid.all() and d.parse_ok.all() and d.judged.all()
    assert set(d.model) == set(MODELS) and set(d.prompt_id) == {"P0x"}
    assert not d.quarantine_refusal_acceptance.any()
    d["draw"] = d.request_key.map({k: x["namespace"] for k, x in bykey.items()})
    assert set(d.draw) == {"d1", "d2"}
    d["scenario"] = d.family_id.map({k: x["factorial_family"] for k, x in items.items()})
    d["cell"] = [items[f]["variants"][v]["cell"] for f, v in zip(d.family_id, d.variant)]
    d[["cue", "encoding"]] = d.channel.str.rsplit("_", n=1, expand=True)
    assert set(d.scenario) == set(SCENARIOS)
    assert d.groupby("scenario").family_id.nunique().eq(4).all()
    for r in requests:
        for t in r["targets"]:
            inp = items[t["family_id"]]["custom_channels"][t["variant"]][t["channel"]]["input"]
            assert inp == r["input_text"]
    # General agent labels can differ by extraction context. Use the focal critical
    # label for each dimension, including joint fidelity, never arbitrary first rows.
    d["literal_tell"] = d.text.str.contains(TELL_RE)
    d["literal_regex"] = d.text.str.contains(LITERAL_RE)
    d["nonstatement"] = d.speech_act.ne("statement")
    d["literal_nonstatement"] = d.literal_regex & d.nonstatement
    d["literal_statement"] = d.literal_regex & ~d.nonstatement
    d["literal_request"] = d.literal_regex & d.speech_act.eq("request/command")
    return d, requests, items


def transitions(d, label="critical", agreement_only=False, repeat_at="single"):
    x = d.copy()
    x["match"] = x[label].eq(x.variant_value)
    x["known"] = x[label].notna()
    if agreement_only:
        x["known"] &= x.critical_J1.eq(x.critical_J2)
    keys = ["scenario", "model", "encoding", "dimension", "family_id", "variant", "cell", "draw"]
    single = x[((x.dimension == "polarity") & (x.cue == "pol")) |
               ((x.dimension == "agent") & (x.cue == "actor"))].copy()
    both = x[x.cue == "both"].copy()
    fields = list(dict.fromkeys(["match", "known", "request_key", "output_id", "input_text", "text", label,
                                "critical_J1", "critical_J2", "critical_source", "speech_act"]))
    p = single[keys + fields].merge(both[keys + fields], on=keys, suffixes=("_s", "_b"), validate="one_to_one")
    p = p[p.known_s & p.known_b].copy()
    p["damage"] = p.match_s & ~p.match_b
    p["recovery"] = ~p.match_s & p.match_b
    p["single_pass"], p["both_pass"] = p.match_s, p.match_b
    p["single_fail"] = ~p.match_s
    # Each single input supplies one protected target, regardless of the missing
    # second cue. Deduplicate its two expanded cell references before repeats.
    rkeys = ["scenario", "model", "encoding", "dimension", "input_text"]
    base = single if repeat_at == "single" else both
    assert base.groupby(rkeys + ["draw"])[label].nunique(dropna=False).le(1).all()
    s = base.drop_duplicates(rkeys + ["draw"])
    rf = ["match", "known", label, "request_key", "output_id", "text"]
    r = s[s.draw == "d1"][rkeys + rf].merge(s[s.draw == "d2"][rkeys + rf], on=rkeys,
              suffixes=("_d1", "_d2"), validate="one_to_one")
    r = r[r.known_d1 & r.known_d2].copy()
    r["repeat_disagreement"] = r.match_d1.ne(r.match_d2)
    r["label_disagreement"] = r[f"{label}_d1"].ne(r[f"{label}_d2"])
    r["text_disagreement"] = r.text_d1.ne(r.text_d2)
    r["passing_draws"] = r.match_d1.astype(int) + r.match_d2.astype(int)
    return p, r


def summarize(p, r):
    result, bs = {}, {}
    for name, col, den in [("damage", "damage", None), ("recovery", "recovery", None),
                           ("single_fidelity", "single_pass", None), ("both_fidelity", "both_pass", None),
                           ("damage_given_pass", "damage", "single_pass"),
                           ("recovery_given_fail", "recovery", "single_fail")]:
        result[name], bs[name] = ratio(p, col, den)
    for name, col, den in [("repeat_disagreement", "repeat_disagreement", None),
                           ("repeat_label_disagreement", "label_disagreement", None),
                           ("repeat_text_disagreement", "text_disagreement", None),
                           ("repeat_given_pass", "repeat_disagreement", "passing_draws")]:
        result[name], bs[name] = ratio(r, col, den)
    for name, a, b in [("damage_minus_repeat", "damage", "repeat_disagreement"),
                       ("damage_minus_label_repeat", "damage", "repeat_label_disagreement"),
                       ("conditional_damage_minus_repeat", "damage_given_pass", "repeat_disagreement"),
                       ("conditional_damage_minus_conditional_repeat", "damage_given_pass", "repeat_given_pass"),
                       ("net_fidelity_change", "both_fidelity", "single_fidelity")]:
        result[name], bs[name] = difference(result[a], bs[a], result[b], bs[b], len(p), p.scenario.nunique())
    result["point_kill_pass"] = result["damage_minus_repeat"]["estimate"] > 0
    result["ci_excludes_zero"] = result["damage_minus_repeat"]["ci_low"] > 0
    result["n_pairs"], result["n_repeat_inputs"] = len(p), len(r)
    return result, bs


def scoped(df, enc, dim=None, model=None):
    q = df[df.encoding.eq(enc)]
    if dim is not None:
        q = q[q.dimension.eq(dim)]
    if model is not None:
        q = q[q.model.eq(model)]
    return q


def fmt(x, pp=False):
    if x["estimate"] is None:
        return "undefined"
    return f"{100*x['estimate']:.2f} [{100*x['ci_low']:.2f}, {100*x['ci_high']:.2f}]" + (" pp" if pp else "%")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    d, requests, items = load()
    p, r = transitions(d)
    _, rb = transitions(d, repeat_at="both")
    assert len(p) == 10240 and len(r) == 2560
    assert p.groupby(["model", "encoding", "dimension"]).size().eq(640).all()
    assert r.groupby(["model", "encoding", "dimension"]).size().eq(160).all()
    assert not p.duplicated(["scenario", "model", "encoding", "dimension", "cell", "draw"]).any()
    assert len(rb) == 5120
    by, draws, contrasts, repeat_sensitivity = {}, {}, {}, {}
    for enc in ENCS:
        by[enc], draws[enc] = {}, {}
        for dim in DIMS + ["pooled"]:
            dd = None if dim == "pooled" else dim
            by[enc][dim], draws[enc][dim] = {}, {}
            for model in MODELS + ["pooled"]:
                mm = None if model == "pooled" else model
                a, b = scoped(p, enc, dd, mm), scoped(r, enc, dd, mm)
                by[enc][dim][model], draws[enc][dim][model] = summarize(a, b)
    for dim in DIMS + ["pooled"]:
        contrasts[dim] = {}
        for model in MODELS + ["pooled"]:
            key = "damage_minus_repeat"
            contrasts[dim][model], _ = difference(by["TELL"][dim][model][key], draws["TELL"][dim][model][key],
                by["STATEMENT"][dim][model][key], draws["STATEMENT"][dim][model][key],
                by["TELL"][dim][model]["n_pairs"])
    for enc in ENCS:
        repeat_sensitivity[enc] = {}
        for dim in DIMS + ["pooled"]:
            dd = None if dim == "pooled" else dim
            repeat_sensitivity[enc][dim] = {}
            for model in MODELS + ["pooled"]:
                mm = None if model == "pooled" else model
                a, b = scoped(p, enc, dd, mm), scoped(rb, enc, dd, mm)
                z, bs = summarize(a, b)
                primary = by[enc][dim][model]
                primary_bs = draws[enc][dim][model]
                mean_bs = (primary_bs["repeat_disagreement"] + bs["repeat_disagreement"]) / 2
                mean_r = {"estimate": (primary["repeat_disagreement"]["estimate"] + z["repeat_disagreement"]["estimate"]) / 2,
                          "ci_low": float(np.percentile(mean_bs, 2.5)), "ci_high": float(np.percentile(mean_bs, 97.5)),
                          "n": primary["n_repeat_inputs"] + len(b), "n_clusters": 80}
                mean_delta, _ = difference(primary["damage"], primary_bs["damage"], mean_r, mean_bs, len(a))
                repeat_sensitivity[enc][dim][model] = {"both_repeat_disagreement": z["repeat_disagreement"],
                    "both_repeat_label_disagreement": z["repeat_label_disagreement"],
                    "damage_minus_both_repeat": z["damage_minus_repeat"],
                    "mean_endpoint_repeat": mean_r, "damage_minus_mean_endpoint_repeat": mean_delta}
    sensitivity = {}
    for name, label, only in [("J2", "critical_J2", False), ("agreement_only", "critical", True)]:
        sp, sr = transitions(d, label, only)
        sensitivity[name] = {}
        for enc in ENCS:
            sensitivity[name][enc] = {}
            for dim in DIMS:
                sensitivity[name][enc][dim] = {}
                for model in MODELS + ["pooled"]:
                    mm = None if model == "pooled" else model
                    z, _ = summarize(scoped(sp, enc, dim, mm), scoped(sr, enc, dim, mm))
                    sensitivity[name][enc][dim][model] = z

    # One fully specified output has two focal-record references: one per dimension.
    both = d[d.cue == "both"]
    jk = ["scenario", "model", "encoding", "cell", "draw", "request_key"]
    jp = both[both.dimension == "polarity"][jk + ["critical_match"]].merge(
        both[both.dimension == "agent"][jk + ["critical_match", "speech_act"]], on=jk,
        suffixes=("_pol", "_agent"), validate="one_to_one")
    assert len(jp) == 5120
    jp["joint_pa"] = jp.critical_match_pol & jp.critical_match_agent
    jp["joint_pas"] = jp.joint_pa & jp.speech_act.eq("statement")
    u = d.drop_duplicates("request_key").copy()
    assert u.groupby(["scenario", "model", "encoding", "draw"]).size().eq(9).all()
    diagnostics = {}
    for enc in ENCS:
        diagnostics[enc] = {}
        for model in MODELS + ["pooled"]:
            mm = None if model == "pooled" else model
            uj, jj = scoped(u, enc, model=mm), scoped(jp, enc, model=mm)
            z = {k: ratio(uj, k)[0] for k in ["literal_regex", "literal_tell", "nonstatement",
                         "literal_nonstatement", "literal_statement", "literal_request"]}
            z.update({k: ratio(jj, k)[0] for k in ["joint_pa", "joint_pas"]})
            z["by_cue"] = {cue: {k: ratio(uj[uj.cue == cue], k)[0] for k in
                                 ["literal_regex", "nonstatement", "literal_nonstatement"]}
                           for cue in ["neither", "pol", "actor", "both"]}
            diagnostics[enc][model] = z

    # Per-row and pooled verdicts obey the point-estimate rule literally. CIs are
    # separately reported evidence, not an invented preregistered significance gate.
    verdict = {}
    for dim in DIMS + ["pooled"]:
        verdict[dim] = {}
        for model in MODELS + ["pooled"]:
            t, s = by["TELL"][dim][model], by["STATEMENT"][dim][model]
            if s["point_kill_pass"]:
                text = "transparent_encoding_point_gate_passes"
            elif t["point_kill_pass"]:
                text = "TELL_only_encoding_defect"
            else:
                text = "no_interference_headline"
            verdict[dim][model] = {"verdict": text, "TELL_ci_excludes_zero": t["ci_excludes_zero"],
                                   "STATEMENT_ci_excludes_zero": s["ci_excludes_zero"]}

    paths = ["runs/r2d1/scored.parquet", "data/items/r2_d.jsonl", "runs/requests/r2d.jsonl",
             "runs/r2d1/config.json", "runs/r2d1/judgments.jsonl", "runs/r2d1/generations.jsonl",
             "orchestration/PREREG_R2.md", "orchestration/decision_log.md", "ideas/cycles/c1/decision.md",
             "annotation/CB_rules.md", "annotation/CODEBOOK.md", "src/attribute.py", "src/judge.py", "src/r2d_analyze.py",
             "prompts/P0.txt", "prompts/chip_legend_x.txt"]
    gens = records("runs/r2d1/generations.jsonl")
    result = {"schema_version": 1, "run": "r2d1", "n": len(p), "n_clusters": 80,
              "n_requests": 11520, "n_scored_rows": len(d), "n_repeat_inputs": len(r),
              "bootstrap": {"unit": "factorial_family / physical scenario", "n_boot": NBOOT,
                            "seed": SEED, "ci": "pointwise 95% percentile", "paired_across_all_strata": True},
              "primary": "P(single pass, both fail) minus P(single d1 pass status != single d2 pass status)",
              "primary_denominators": "all aligned cue-addition pairs; unique same-input single-cue repeat pairs",
              "by_encoding_dimension_model": by, "TELL_minus_STATEMENT": contrasts,
              "diagnostics": diagnostics, "scoring_sensitivities": sensitivity,
              "repeat_endpoint_sensitivity": repeat_sensitivity, "kill_rules": verdict,
              "regex": {"tell": TELL_RE.pattern, "broad": LITERAL_RE.pattern},
              "provenance": {"sha256": {path: digest(path) for path in paths},
                  "generation_utc_range": [min(g["created_utc"] for g in gens), max(g["created_utc"] for g in gens)],
                  "critical_source_occurrences": d.critical_source.value_counts().to_dict(),
                  "critical_source_request_dimension_units": d.drop_duplicates(["request_key", "dimension"]).critical_source.value_counts().to_dict(),
                  "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}}
    (OUT / "primary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    headline = {"n": len(p), "n_clusters": 80, "n_requests": 11520, "n_scored_rows": len(d),
                "n_boot": NBOOT, "bootstrap_seed": SEED, "n_repeat_inputs": len(r)}

    def flatten(prefix, z):
        for k, v in z.items():
            if isinstance(v, dict) and "estimate" in v:
                stem = f"{prefix}_{k}"
                for field in ["estimate", "ci_low", "ci_high", "k", "n", "n_clusters", "n_event_clusters"]:
                    if field in v and v[field] is not None:
                        headline[stem if field == "estimate" else f"{stem}_{field}"] = v[field]

    for enc in ENCS:
        for dim in DIMS + ["pooled"]:
            for model in MODELS + ["pooled"]:
                stem = f"{enc.lower()}_{dim}_{SHORT.get(model, model)}"
                flatten(stem, by[enc][dim][model])
                flatten(stem, repeat_sensitivity[enc][dim][model])
                headline[stem + "_point_kill_pass"] = int(by[enc][dim][model]["point_kill_pass"])
        for model in MODELS + ["pooled"]:
            flatten(f"{enc.lower()}_{SHORT.get(model, model)}", diagnostics[enc][model])
        # Convenient encoding-wide aliases for paper importers.
        flatten(enc.lower(), by[enc]["pooled"]["pooled"])
    for dim in DIMS + ["pooled"]:
        flatten(f"tell_minus_statement_{dim}", contrasts[dim])
    (OUT / "headline.json").write_text(json.dumps(headline, indent=2, allow_nan=False) + "\n")
    # CALE-AI's existing discovery path expects report.json, while SE4All reads
    # headline.json directly. Keep report.json equally flat and numeric.
    (OUT / "report.json").write_text(json.dumps(headline, indent=2, allow_nan=False) + "\n")
    p.to_parquet(OUT / "transitions.parquet", index=False)
    r.to_parquet(OUT / "repeats.parquet", index=False)
    rb.to_parquet(OUT / "repeats_both.parquet", index=False)
    metric_rows = []
    for enc in ENCS:
        for dim in DIMS + ["pooled"]:
            for model in MODELS + ["pooled"]:
                for name, v in by[enc][dim][model].items():
                    if isinstance(v, dict):
                        metric_rows.append(dict(encoding=enc, dimension=dim, model=model, metric=name, **v))
    pd.DataFrame(metric_rows).to_csv(OUT / "metrics.csv", index=False)
    make_examples(d, p, r, rb, by)
    make_figure(by)
    make_report(d, p, r, by, contrasts, diagnostics, sensitivity, repeat_sensitivity, verdict, result)
    # Detect concurrent scoring/data changes during analysis rather than mix snapshots.
    for path, expected in result["provenance"]["sha256"].items():
        assert digest(path) == expected, f"Input changed during analysis: {path}"
    print(json.dumps({"outputs": str(OUT), "kill": verdict, "n": len(p), "n_clusters": 80}, indent=2))


def make_figure(by):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "axes.titleweight": "bold"})
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.45), sharey=True)
    colors = {"TELL": "#C14B24", "STATEMENT": "#176A94"}
    plotmodels = MODELS + ["pooled"]
    bounds = [100 * by[e][di][m]["damage_minus_repeat"][b]
              for e in ENCS for di in DIMS for m in plotmodels for b in ["ci_low", "ci_high"]]
    xmin, xmax = min(-2, min(bounds) - 2), max(2, max(bounds) + 2)
    for ax, dim, title in zip(axs, DIMS, ["Polarity protected · add actor", "Agent protected · add polarity"]):
        ax.axvspan(0, xmax, color="#F4F4F0", zorder=0)
        ax.axvline(0, color="#777777", linewidth=.85, linestyle=(0, (3, 3)))
        ax.axhline(3.5, color="#D7D7D7", linewidth=.8)
        for i, model in enumerate(plotmodels):
            vals = [100 * by[e][dim][model]["damage_minus_repeat"]["estimate"] for e in ENCS]
            ax.plot(vals, [i - .13, i + .13], color="#B4B4B4", lw=1, zorder=1)
            for enc, yy in zip(ENCS, [i - .13, i + .13]):
                z = by[enc][dim][model]["damage_minus_repeat"]
                v, lo, hi = [100*z[k] for k in ["estimate", "ci_low", "ci_high"]]
                ax.errorbar(v, yy, xerr=[[v-lo], [hi-v]], color=colors[enc],
                            fmt="D" if model == "pooled" else "o", ms=4.7, capsize=2.2,
                            elinewidth=1.25, markeredgecolor="white", markeredgewidth=.5, zorder=3)
        ax.set(title=title, xlim=(xmin, xmax), ylim=(4.5, -.55), xlabel="Damage − repeat disagreement (pp)")
        ax.set_yticks(range(5), [NAMES.get(m, "Four-model pool") for m in plotmodels])
        ax.tick_params(axis="both", length=0)
        ax.grid(axis="x", color="#E3E3E3", linewidth=.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Does adding a cue break a protected commitment?", x=.03, ha="left", fontsize=12, weight="bold", y=.98)
    fig.legend(handles=[Line2D([], [], marker="o", color=colors[e], label=f"[{e}]", lw=1.2, ms=5)
                        for e in ENCS], loc="upper left", bbox_to_anchor=(.02, .91), ncol=2, frameon=False)
    fig.text(.03, .018, "95% CIs: 10,000 paired resamples of 80 physical scenarios. Positive values exceed the repeat baseline.",
             fontsize=8, color="#555555")
    fig.subplots_adjust(left=.19, right=.985, bottom=.19, top=.75, wspace=.14)
    fig.savefig(FIG / "r2d_composition.pdf", metadata={"Title": "W-D encoding-controlled composition"})
    fig.savefig(FIG / "r2d_composition.png", dpi=240)
    plt.close(fig)


def make_examples(d, p, r, rb, by):
    order = ["scenario", "model", "encoding", "dimension", "cell", "draw"]
    model_rank = {m: i for i, m in enumerate(MODELS)}
    q = p.assign(model_order=p.model.map(model_rank)).sort_values(
        ["scenario", "model_order", "encoding", "dimension", "cell", "draw"])
    lines = ["# W-D stored examples", "",
        "These are selected counterexamples, not representative utterances. Selection is declared here and implemented in `src/r2d_analyze.py`: "
        "within each encoding × protected dimension × transition direction, select the first eligible stored pair ordered by physical scenario ID, "
        "fixed model order (Qwen, Llama, Gemma, Terra), encoding, dimension, YES/NOT|I/YOU cell string, and draw. "
        "Select one repeat-disagreement pair per cue endpoint × encoding × dimension in the same scenario/model order, then input text. "
        "Select one broad-regex literalization example per encoding ordered by scenario, model, input text, draw. "
        "No text is rewritten. Empty eligible strata are reported. Full paired encoding controls are shown for every transition example.", "",
        "Labels: `runs/r2d1/scored.parquet` focal `critical`, agreement else J1 fallback; "
        "general `speech_act` uses the stored J1/J2/layer0 resolution. Exact hashes are in `primary.json`. "
        "Eligibility rates below use all aligned pairs in that encoding × dimension; selected-model rates are also given.", ""]
    for enc in ENCS:
        for dim in DIMS:
            for event in ["damage", "recovery"]:
                eligible = q[(q.encoding == enc) & (q.dimension == dim) & q[event]]
                z = by[enc][dim]["pooled"][event]
                lines += [f"## {enc} / {dim} / {event}", "", f"Eligible: {z['k']}/{z['n']} ({fmt(z)}), across 80 scenarios.", ""]
                if eligible.empty:
                    lines += ["No eligible example.", ""]
                    continue
                x = eligible.iloc[0]
                zz = by[enc][dim][x.model][event]
                lines += [f"Selected: `{x.scenario}`, `{x.family_id}`, variant `{x.variant}`, cell `{x.cell}`, "
                          f"`{x.model}`, `{x.draw}`. Selected-model stratum: {zz['k']}/{zz['n']}.", ""]
                controls = p[(p.scenario == x.scenario) & (p.model == x.model) & (p.dimension == dim) &
                             (p.cell == x.cell) & (p.draw == x.draw)].sort_values("encoding")
                for row in controls.itertuples():
                    lines += [f"**[{row.encoding}]**", ""]
                    for arm in ["s", "b"]:
                        lines += [f"- Input: `{getattr(row, 'input_text_'+arm)}`",
                                  f"- Output `{getattr(row, 'output_id_'+arm)}`: {json.dumps(getattr(row, 'text_'+arm), ensure_ascii=False)}",
                                  f"- Protected label: `{getattr(row, 'critical_'+arm)}`; pass: `{bool(getattr(row, 'match_'+arm))}`; "
                                  f"J1/J2: `{getattr(row, 'critical_J1_'+arm)}` / `{getattr(row, 'critical_J2_'+arm)}`; "
                                  f"source: `{getattr(row, 'critical_source_'+arm)}`; speech_act: `{getattr(row, 'speech_act_'+arm)}`."]
                    lines += [""]
    lines += ["**CB-7 caveat:** the selected Qwen TELL damage example labels 'I don't tell you to book a taxi.' "
              "as agent=speaker in both J1 and J2. CB-7's embedded-doer rule instead points to addressee. "
              "This is an observed scoring concern, not an independently adjudicated correction. "
              "The stored scores are retained; selected TELL transitions must not be presented as verified semantic damage.", ""]
    for endpoint, repeat in [("single", r), ("both", rb)]:
        for enc in ENCS:
            for dim in DIMS:
                rr = repeat[(repeat.encoding == enc) & (repeat.dimension == dim)]
                eligible = rr[rr.repeat_disagreement].assign(model_order=lambda x: x.model.map(model_rank)).sort_values(
                    ["scenario", "model_order", "input_text"])
                lines += [f"## {endpoint} / {enc} / {dim} / repeat disagreement", "", f"Eligible unique repeat inputs: {len(eligible)}/{len(rr)}.", ""]
                if eligible.empty:
                    lines += ["No eligible example.", ""]
                    continue
                x = eligible.iloc[0]
                lines += [f"`{x.scenario}`, `{x.model}`. Input: `{x.input_text}`.", ""]
                for dr in ["d1", "d2"]:
                    lines += [f"- {dr}, `{x['output_id_'+dr]}`: {json.dumps(x['text_'+dr], ensure_ascii=False)}; "
                              f"label `{x['critical_'+dr]}`, pass `{bool(x['match_'+dr])}`."]
                lines += [""]
    u = d.drop_duplicates("request_key")
    for enc in ENCS:
        uu = u[u.encoding == enc]
        eligible = uu[uu.literal_regex].assign(model_order=lambda x: x.model.map(model_rank)).sort_values(
            ["scenario", "model_order", "input_text", "draw"])
        lines += [f"## {enc} / lexical literalization", "", f"Eligible unique outputs: {len(eligible)}/{len(uu)}.", ""]
        if eligible.empty:
            lines += ["No eligible example.", ""]
            continue
        x = eligible.iloc[0]
        lines += [f"`{x.scenario}`, `{x.model}`, `{x.draw}`, `{x.channel}`; output `{x.output_id}`.", "",
                  f"Input: `{x.input_text}`", "", f"Output: {json.dumps(x.text, ensure_ascii=False)}", "",
                  f"Broad regex: true; tell regex: `{bool(x.literal_tell)}`; judge speech_act: `{x.speech_act}`.", ""]
    (OUT / "examples.md").write_text("\n".join(lines))


def make_report(d, p, r, by, contrasts, diagnostics, sensitivity, repeat_sensitivity, verdict, result):
    lines = ["# W-D: encoding-controlled composition", "",
        "## Decision", ""]
    for dim in DIMS + ["pooled"]:
        t, s = by["TELL"][dim]["pooled"], by["STATEMENT"][dim]["pooled"]
        lines += [f"- **{dim}**: [TELL] damage minus repeat {fmt(t['damage_minus_repeat'], True)}; "
                  f"[STATEMENT] {fmt(s['damage_minus_repeat'], True)}. "
                  f"Literal point-rule verdict: `{verdict[dim]['pooled']['verdict']}`."]
    lines += ["", "**Interpretation:** the independent transparent-encoding effect is specific to Llama polarity: "
        "55/640 pass→fail transitions across 30/80 scenarios, Δ=8.59 pp [6.25, 11.09], "
        "with 0/160 single-cue pass-status repeat disagreements. It survives J2 and agreement-only scoring unchanged. "
        "Under [TELL], Qwen agent damage is 84/640 across 44 scenarios (Δ=13.12 pp [10.31, 16.09]); "
        "Gemma has 10/640 across six scenarios (1.56 pp [0.47, 2.97]). Those effects are [TELL]-only and therefore encoding defects under the kill rule. "
        "Llama's [STATEMENT] agent damage is four transitions from one scenario, with a CI touching zero; "
        "Terra has no observed protected-dimension damage. These results support a bounded model/encoding-specific composition failure, "
        "not model-general interference or equivalence in the zero-event strata.", "",
        "The binding kill rule is applied literally to the point difference: damage ≤ repeat disagreement licenses no interference headline; "
        "a positive difference confined to [TELL] licenses only an encoding-defect description. Confidence intervals are reported separately: "
        "a point-rule pass is not proof of a nonzero effect, and a wide interval containing zero does not establish equivalence. "
        "No multiplicity-adjusted significance claim is made. Per-model/dimension outcomes below must not be replaced by the pooled verdict.", "",
        "## Inventory, freeze, and scoring", "",
        "All 11,520 planned requests are present: 80 physical scenarios × 9 unique inputs × 2 encodings × 4 models × 2 greedy draws. "
        "The 320 A/B records expand to 40,960 scored occurrences; they are not independent scenarios. "
        "All outputs are valid, parsed, judged, stop-terminated, and P0x at temperature 0. "
        "The two namespace draws d1/d2 use the same greedy configuration; repeat disagreement measures observed run/batching/API instability, not a sampling-temperature effect. "
        "Models are a fixed roster; pooled results give them equal weight in this balanced design, without inference to a population of models.", "",
        "Readiness: the complete run finished November 1, before the November 5 action-6 gate. "
        "Git commit `168702e` records the W-D protocol at 2026-11-01 02:34:13 UTC, before the earliest stored generation "
        f"({result['provenance']['generation_utc_range'][0]}). "
        "The item-freeze commit `3f24c80` is at 02:55:11 UTC and says W-D was running, after the first stored outputs (02:52:20 UTC). "
        "The assembled run config was created at 16:19:01 UTC and includes prompt/model/code hashes but no frozen item/codebook hashes. "
        "Thus protocol-before-generation is supported; a complete prospective item/codebook hash freeze is not independently established by these files. "
        "This report is an encoding/repeat sensitivity analysis under the registered design; it does not certify an entirely audited confirmatory freeze. "
        "Current input and analysis hashes are recorded in `primary.json`.", "",
        f"Stored critical-label sources over scored occurrences: `{d.critical_source.value_counts().to_dict()}`. "
        "This run has J1 fallback on critical disagreements, with no run-local arbiter file; it must not inherit the main1 pipeline's no-fallback description. "
        "General dimensions use J1/J2 agreement, otherwise layer0 tie-breaking as implemented in `judge.py`. "
        "Protected correctness uses the dimension's focal `critical` label. Joint polarity/agent fidelity joins the two focal records for each fully specified output; "
        "it does not substitute general agent labels, which can disagree with focal extraction. "
        "No authored refusal/acceptance families occur here. Generated refusals remain failures of supplied statement cues. "
        "CB-7 appears explicitly in `annotation/CODEBOOK.md`; the current J1/J2 rules in `src/judge.py` "
        "include the general content-verb agent rule but do not spell out CB-7's tell/to example. "
        "The stored judge outputs and codebook are retained as supplied. Human validation elsewhere is not a W-D output-specific audit.", "",
        "**Observed CB-7 limitation:** the declared-rule Qwen TELL example 'I don't tell you to book a taxi.' "
        "has focal agent=speaker in both judge variants, although the embedded-doer rule points to addressee. "
        "Thus judge agreement does not certify correct application of CB-7, and the stored TELL agent damage is a machine-scored diagnostic, "
        "not independently verified semantic damage. No post-hoc relabeling was performed. "
        "The Llama transparent polarity counterexample instead visibly drops negation ('I will not lock the door.' → 'You lock the door.').", "",
        "## Estimands and uncertainty", "",
        "The protocol does not specify conditional versus unconditional damage denominators or which repeat inputs to use. "
        "The following operational choices are explicit analysis choices, not additional preregistered clauses:", "",
        "- **Primary damage D** = mean( single-cue protected pass AND both-cue protected fail ) over all four factorial cells and both draws. "
        "Protect polarity for pol→both; protect agent for actor→both. Per model × encoding × dimension, n=640 aligned transitions.",
        "- **Primary repeat R** = mean( single-cue d1 protected pass status ≠ d2 protected pass status ) over the exact single-cue inputs used in those transitions. "
        "Remove duplicate references to the missing second cue: per model × encoding × dimension, n=160 unique same-input repeat pairs. "
        "R is symmetric disagreement, so it is more conservative than one-direction repeat pass→fail counted over all repeat draws. "
        "Primary Δ=D−R compares two probabilities on the same protected binary endpoint; paired resampling retains their covariance.",
        "- **Companion denominators**: conditional damage = pass→fail / initial passes; conditional recovery = fail→pass / initial failures. "
        "Also report conditional damage minus symmetric R, and conditional damage minus directed conditional repeat breakage "
        "(number of discordant repeat pairs / number of passing draws). The latter uses both repeat directions and counts each discordant pair once. "
        "Neither companion replaces the primary result after outcomes are known.",
        "- **Other checks**: raw focal-label and exact-text repeat disagreement; net fidelity change = recoveries−damage; "
        "joint P/A correctness and joint P/A/statement correctness on unique both-cue outputs. "
        "Repeat-endpoint sensitivities also use both-cue inputs and an equal-weight mean of single- and both-cue disagreement. "
        "Unsupplied agent/polarity choices are not called preservation failures.",
        "- **Literalization** is a lexical diagnostic, not a causal mechanism: strict tell/tells/telling/told regex; "
        "broad regex additionally includes say/state inflections and explicit 'this/my statement' frames. "
        "Report broad matches, all nonstatement speech-act labels, and their intersection separately. "
        "'I tell you…' can itself be judged a statement, so requiring a nonstatement label would miss lexical literalization. "
        "Regex false positives/negatives are possible; exact regexes and real examples are supplied. Rates use 11,520 unique requests, not repeated A/B occurrences.",
        "- **Bootstrap**: 10,000 draws of 80 physical scenario IDs with replacement, seed 20261031, shared across models, dimensions, encodings, draws, and all contrasts. "
        "Recompute numerator/denominator ratios in each resample. Intervals are pointwise 95% percentile intervals. "
        "Conditional rates with zero-denominator resamples use finite resamples only; `n_boot_valid` is retained in `primary.json`. "
        "Zero-event empirical bootstrap intervals are degenerate and do not imply zero population risk. "
        "The two greedy repeats estimate a limited noise floor, not a stable measure of every future source of instability.", "",
        "## Per-model protected transitions", "",
        "Rates and intervals are percentages except Δ, which is in percentage points. 'Damage / pass' is conditional; D and recovery use all aligned transitions. "
        "All rows have 80 physical clusters. Repeat numerators count unique input pairs.", "",
        "| Encoding | Protected | Model | Damage k/n; D [CI] | Damage / pass | Recoveries k/n | Repeat k/n; R [CI] | Δ=D−R [CI], pp | Point rule |",
        "|---|---|---|---|---|---|---|---|---|"]
    for enc in ENCS:
        for dim in DIMS:
            for model in MODELS + ["pooled"]:
                z = by[enc][dim][model]
                a, b, c, cond = [z[k] for k in ["damage", "repeat_disagreement", "recovery", "damage_given_pass"]]
                lines += [f"| {enc} | {dim} | {model} | {a['k']}/{a['n']}; {fmt(a)} | {cond['k']}/{cond['n']}; {fmt(cond)} "
                          f"| {c['k']}/{c['n']}; {fmt(c)} | {b['k']}/{b['n']}; {fmt(b)} | {fmt(z['damage_minus_repeat'], True)} "
                          f"| {'exceeds repeat' if z['point_kill_pass'] else 'no headline'} |"]
    lines += ["", "## Fidelity, recoveries, and other noise endpoints", "",
        "| Encoding | Protected | Model | Single fidelity [CI] | Both fidelity [CI] | Net both−single, pp | Recovery / initial fail | Label-repeat disagreement | Text-repeat disagreement |",
        "|---|---|---|---|---|---|---|---|---|"]
    for enc in ENCS:
        for dim in DIMS:
            for model in MODELS + ["pooled"]:
                z = by[enc][dim][model]
                lines += [f"| {enc} | {dim} | {model} | {fmt(z['single_fidelity'])} | {fmt(z['both_fidelity'])} "
                          f"| {fmt(z['net_fidelity_change'], True)} | {fmt(z['recovery_given_fail'])} "
                          f"| {fmt(z['repeat_label_disagreement'])} | {fmt(z['repeat_text_disagreement'])} |"]
    lines += ["", "### Repeat floor on fully specified inputs", "",
        "The primary single-cue repeat floor is zero in every stratum despite substantial text variation. "
        "Fully specified inputs can be less stable; this secondary check avoids treating the single-cue floor as universal. "
        "Both-cue repeat inputs number 320 per model/encoding/dimension. Mean-endpoint R gives equal weight to the two endpoints, "
        "rather than letting the four both-cue inputs outweigh the two single-cue inputs. "
        "These sensitivities were added to check endpoint dependence; they do not change the declared primary denominator.", "",
        "| Encoding | Protected | Model | Both repeat k/n [CI] | D−both repeat, pp | D−mean endpoint repeat, pp |",
        "|---|---|---|---|---|---|"]
    for enc in ENCS:
        for dim in DIMS:
            for model in MODELS + ["pooled"]:
                z = repeat_sensitivity[enc][dim][model]
                v = z["both_repeat_disagreement"]
                lines += [f"| {enc} | {dim} | {model} | {v['k']}/{v['n']}; {fmt(v)} | "
                          f"{fmt(z['damage_minus_both_repeat'], True)} | {fmt(z['damage_minus_mean_endpoint_repeat'], True)} |"]
    lines += ["", "Llama [STATEMENT] polarity remains above the both-cue noise floor: 5/320 repeat disagreements (1.56%), "
        "leaving D−R_both=7.03 pp [4.38, 9.84]. Qwen [TELL] agent likewise remains positive at 9.38 pp [6.25, 12.50]. "
        "Gemma [TELL] agent becomes less certain against this endpoint: 0.94 pp [−0.31, 2.34]. "
        "Thus the transparent-encoding polarity result survives the repeat-endpoint choice; precision of the smaller [TELL] effect depends on that choice."]
    lines += ["", "## Paired encoding contrast", "",
        "Difference of primary Δ values, [TELL]−[STATEMENT], preserving all pairing. Positive means more excess damage under [TELL].", "",
        "| Protected | Model | Difference [95% CI], pp |", "|---|---|---|"]
    for dim in DIMS + ["pooled"]:
        for model in MODELS + ["pooled"]:
            lines += [f"| {dim} | {model} | {fmt(contrasts[dim][model], True)} |"]
    lines += ["", "## Joint fidelity and literalization", "",
        "Joint P/A and P/A/statement fidelity use 640 unique both-cue outputs per model/encoding; lexical and speech-act rates "
        "use 1,440 unique outputs across all nine inputs per model/encoding. 'Lexical ∩ nonstatement' is a corroborated subset of regex hits, not the whole literalization rate.", "",
        "| Encoding | Model | Joint P/A k/n [CI] | Joint P/A/statement k/n [CI] | Broad lexical k/n [CI] | Tell lexical [CI] | Nonstatement act [CI] | Lexical ∩ nonstatement [CI] |",
        "|---|---|---|---|---|---|---|---|"]
    for enc in ENCS:
        for model in MODELS + ["pooled"]:
            z = diagnostics[enc][model]
            def countfmt(k):
                v = z[k]
                return f"{v['k']}/{v['n']}; {fmt(v)}"
            lines += [f"| {enc} | {model} | {countfmt('joint_pa')} | {countfmt('joint_pas')} | {countfmt('literal_regex')} "
                      f"| {fmt(z['literal_tell'])} | {fmt(z['nonstatement'])} | {fmt(z['literal_nonstatement'])} |"]
    lines += ["", "Per-cue literalization and speech-act rates, including literalized statements and literalized requests, are in `primary.json` under `diagnostics`.", "",
        "## Label and denominator sensitivities", "",
        "J2 replaces focal labels for every row. Agreement-only removes a transition if either endpoint has focal J1/J2 disagreement, "
        "and removes a repeat pair if either draw disagrees; these are selected subsets and retain their own denominators. "
        "No scored table is modified. General-label ties and CB-7 remain separate measurement limitations.", "",
        "| Scoring | Encoding | Protected | Model | Δ=D−R, pp | Paired n | Repeat n |", "|---|---|---|---|---|---|---|"]
    for name, val in sensitivity.items():
        for enc in ENCS:
            for dim in DIMS:
                for model in MODELS + ["pooled"]:
                    z = val[enc][dim][model]
                    lines += [f"| {name} | {enc} | {dim} | {model} | {fmt(z['damage_minus_repeat'], True)} | {z['n_pairs']} | {z['n_repeat_inputs']} |"]
    lines += ["", "| Encoding | Protected | Model | Conditional damage−symmetric repeat, pp | Conditional damage−directed conditional repeat, pp | D−raw-label repeat, pp |",
              "|---|---|---|---|---|---|"]
    for enc in ENCS:
        for dim in DIMS:
            for model in MODELS + ["pooled"]:
                z = by[enc][dim][model]
                lines += [f"| {enc} | {dim} | {model} | {fmt(z['conditional_damage_minus_repeat'], True)} "
                          f"| {fmt(z['conditional_damage_minus_conditional_repeat'], True)} | {fmt(z['damage_minus_label_repeat'], True)} |"]
    lines += ["", "## Artifacts and reproduction", "",
        "Run `OPENBLAS_NUM_THREADS=1 .venv/bin/python src/r2d_analyze.py` from the repository root. No GPU or model calls. "
        "`primary.json` contains every estimate, CI, denominator, sensitivity, exact input hashes, and literal kill-rule verdict. "
        "`headline.json` is flat numeric data in proportion units, with `<key>_ci_low`, `<key>_ci_high`, `<key>_n`, `<key>_n_clusters` and counts where applicable. "
        "Global `n=10240` is aligned protected transitions, not independent observations; `n_clusters=80`. "
        "SE4All imports it as `wd_<key>`. The identical flat `report.json` supports CALE-AI's existing `wd__<key>` loader after its evidence refresh. "
        "`metrics.csv`, `transitions.parquet`, `repeats.parquet`, and `repeats_both.parquet` expose the analysis units; `examples.md` gives deterministically selected real texts and encoding controls. "
        "`paper/figs/r2d_composition.pdf` and `.png` show per-model paired dots and 95% scenario-bootstrap CIs for Δ, with a fixed-roster pooled row. "
        "The figure's two panels protect polarity and agent, respectively; positive Δ exceeds the repeat baseline. "
        "No generic interference claim should be imported solely from artifact readiness or from the exploratory Exp C agent drop. "
        "Use the encoding/dimension/model verdicts and their uncertainty above.", ""]
    (OUT / "report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
