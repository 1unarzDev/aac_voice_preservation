#!/usr/bin/env python3
"""Generate results_macros.tex and examples_table.tex for the SE4All paper.

Every number in main.tex comes from here. Inputs (read-only):
  analysis/main1/*.csv            per-model estimates with family-bootstrap CIs (analysis pipeline)
  runs/main1/scored.parquet       row-level verdicts (pooled estimates are recomputed here)
  runs/main1/outputs.jsonl        output texts (examples table)
  runs/main1/judge_report.json    J1-vs-J2 consistency
  runs/expB1/scored.parquet       Exp B (cue interaction, encodings)      -- optional
  runs/expC1/scored.parquet       Exp C (factorial noninterference)       -- optional (PENDING)
  runs/{expB1,expC1}/generations.jsonl   draw-to-draw agreement (nondeterminism)
  analysis/s1/message_metrics.csv AACText cue loss
  data/items/test.jsonl           source messages (examples table)
  annotation/*                    oracle-validation sample sizes; human returns if present

Usage (repo root):  . .venv/bin/activate && python paper/se4all/make_macros.py
Pooled estimates: P0 unless named, row-weighted, 95% percentile CI from 2,000 whole-family
bootstrap resamples (seed 20261031), matching analysis/main1/report.md.
Missing inputs never crash the script: the corresponding keys are simply not defined and
main.tex prints a red [key] tag or a \\pending note instead.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SEED = 20261031
NBOOT = 2000
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]  # fixed order (examples rule)
SHORT = {"qwen2.5-7b": "qwen", "llama3.1-8b": "llama", "gemma3-4b": "gemma", "gpt-6.1-terra": "terra"}
DIMS = ["polarity", "agent", "certainty", "speech_act", "politeness", "time_quantity"]
DSHORT = {"polarity": "pol", "agent": "agt", "certainty": "cer", "speech_act": "act",
          "politeness": "pz", "time_quantity": "tq"}

macros: dict[str, str] = {}
sources: dict[str, str] = {}


def put(key: str, value, src: str, fmt: str = "pct"):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return
    if fmt == "pct":
        s = f"{100 * value:.1f}"
    elif fmt == "pp":
        s = f"{100 * value:+.1f}".replace("+", "+")
    elif fmt == "int":
        s = f"{int(round(value)):,}"
    elif fmt == "f2":
        s = f"{value:.2f}"
    elif fmt == "f3":
        s = f"{value:.3f}"
    else:
        s = str(value)
    macros[key] = s
    sources[key] = src


def boot(df: pd.DataFrame, col: str, cluster: str = "family_id"):
    """Row-weighted mean of df[col] (bool/float) with whole-family percentile bootstrap."""
    x = df[[cluster, col]].dropna()
    if x.empty:
        return np.nan, np.nan, np.nan, 0
    v = x[col].astype(float)
    g = x.assign(v=v).groupby(cluster)["v"].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    est = s.sum() / n.sum()
    rng = np.random.default_rng(SEED)
    k = len(g)
    idx = rng.integers(0, k, size=(NBOOT, k))
    bs = s[idx].sum(1) / n[idx].sum(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, int(n.sum())


def put_ci(key, df, col, src, cluster="family_id"):
    est, lo, hi, n = boot(df, col, cluster)
    put(key, est, src)
    put(key + "_lo", lo, src)
    put(key + "_hi", hi, src)
    put(key + "_n", n, src, "int")
    return est


def put_frac(key, k, n, src):
    put(key + "_k", k, src, "int")
    put(key + "_den", n, src, "int")
    if n:
        put(key, k / n, src)


def boot_diff(df, col, a, b, keys, src):
    """Paired difference (channel a minus channel b) of family-level means, family bootstrap."""
    x = df[df.channel.isin([a, b])].copy()
    x["v"] = x[col].astype(float)
    m = x.groupby(["family_id", "channel"])["v"].agg(["sum", "count"]).unstack("channel")
    m = m.dropna()
    if m.empty:
        return
    sa, na = m[("sum", a)].to_numpy(), m[("count", a)].to_numpy()
    sb, nb = m[("sum", b)].to_numpy(), m[("count", b)].to_numpy()
    est = sa.sum() / na.sum() - sb.sum() / nb.sum()
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(m), size=(NBOOT, len(m)))
    bs = sa[idx].sum(1) / na[idx].sum(1) - sb[idx].sum(1) / nb[idx].sum(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    put(keys, est, src, "pp")
    put(keys + "_lo", lo, src, "pp")
    put(keys + "_hi", hi, src, "pp")


# ---------------------------------------------------------------- main1 ----
SC = ROOT / "runs/main1/scored.parquet"
d = pd.read_parquet(SC)
src_main = "runs/main1/scored.parquet"
d["critical_match"] = d["critical_match"].astype(bool)
p0 = d[d.prompt_id == "P0"].copy()

put("n_fam_test", d.family_id.nunique(), src_main, "int")
put("n_fam_dim", d.groupby("dimension").family_id.nunique().min(), src_main, "int")
put("n_rows_main", len(d[d.prompt_id != "P1"]), src_main + " (P1 excluded, D-010)", "int")
put("n_texts_main", d[d.prompt_id != "P1"].text_id.nunique(), src_main, "int")
put("n_requests_main", d[d.prompt_id != "P1"].request_key.nunique(), src_main, "int")
put("n_models", d.model.nunique(), src_main, "int")
put("n_j1_fallback", (d.critical_source == "J1").sum(), src_main, "int")
put("n_fam_pilot", sum(1 for _ in open(ROOT / "data/items/pilot.jsonl")), "data/items/pilot.jsonl", "int")
put("n_fam_dev", sum(1 for _ in open(ROOT / "data/items/dev.jsonl")), "data/items/dev.jsonl", "int")

# judge self-consistency (J1 vs J2): reliability, NOT validity
jr = ROOT / "runs/main1/judge_report.json"
if jr.exists():
    r = json.load(open(jr))["J1_vs_J2"]
    put("jj_n", r["critical"]["n"], str(jr.relative_to(ROOT)), "int")
    put("jj_kappa_crit", r["critical"]["kappa"], str(jr.relative_to(ROOT)), "f2")
    put("jj_kappa_added", r["added_content"]["kappa"], str(jr.relative_to(ROOT)), "f2")
    put("jj_kappa_min_general", min(r[k]["kappa"] for k in ["polarity", "speech_act", "agent", "certainty", "politeness"]),
        str(jr.relative_to(ROOT)), "f2")

# ---- defaults under ambiguity (bare). bare/noncrit requests are shared by A and B: count variant A only.
bareA = d[(d.channel == "bare") & (d.variant == "A") & (d.prompt_id.isin(["P0", "P2", "S3"]))]
pol = bareA[(bareA.dimension == "polarity") & (bareA.critical != "unclear/mixed")]
put_frac("bare_pol_aff_all", int((pol.critical == "affirmative").sum()), len(pol), src_main + " bare, variant A, P0/P2/S3")
pol0 = pol[pol.prompt_id == "P0"]
put_frac("bare_pol_aff_p0", int((pol0.critical == "affirmative").sum()), len(pol0), src_main + " bare P0")
b0 = p0[(p0.channel == "bare") & (p0.variant == "A")].copy()
b0["committed_f"] = b0.critical != "unclear/mixed"
put_ci("bare_commit", b0, "committed_f", src_main + " bare P0 variant A, all dims")
for dim in DIMS:
    x = b0[b0.dimension == dim]
    put(f"bare_commit_{DSHORT[dim]}", (x.critical != "unclear/mixed").mean(), src_main)
    com = x[x.critical != "unclear/mixed"]
    if len(com):
        top = com.critical.value_counts()
        put(f"bare_mode_{DSHORT[dim]}", top.index[0], src_main, "str")
        put_frac(f"bare_modeshare_{DSHORT[dim]}", int(top.iloc[0]), len(com), src_main)
# agent default = speaker; certainty default = plain assertion; act default = statement
# S3/P2 negated-offer for polarity, from coverage.csv (per model) -> pooled mean of model estimates
cov = pd.read_csv(ROOT / "analysis/main1/coverage.csv")
cov = cov[(cov.metric == "coverage_at_3") & (cov.channel == "bare")]
for pr in ["P2", "S3"]:
    for dim in DIMS:
        x = cov[(cov.prompt_id == pr) & (cov.dimension == dim)]
        if len(x):
            put(f"cov_{pr.lower()}_{DSHORT[dim]}", x.estimate.mean(), "analysis/main1/coverage.csv (mean of 4 models)")
    x = cov[cov.prompt_id == pr]
    put(f"cov_{pr.lower()}_all", x.estimate.mean(), "analysis/main1/coverage.csv (mean over dims x models)")

# ---- MR1: noncritical-word invariance (bare vs noncrit, aligned P0 pairs, variant A dedup)
key = ["family_id", "model", "prompt_id", "sample_idx", "suggestion_idx"]
pairs = []
for pr in ["P0"]:
    a = d[(d.channel == "bare") & (d.variant == "A") & (d.prompt_id == pr)].set_index(key)
    b = d[(d.channel == "noncrit") & (d.variant == "A") & (d.prompt_id == pr)].set_index(key)
    j = a[["critical", "dimension", "politeness", "agent", "speech_act", "certainty", "polarity"]].join(
        b[["critical", "politeness", "agent", "speech_act", "certainty", "polarity"]], rsuffix="_n", how="inner")
    pairs.append(j.reset_index())
mr1 = pd.concat(pairs)
mr1["inv_crit"] = mr1.critical == mr1.critical_n
gen = ["politeness", "agent", "speech_act", "certainty", "polarity"]
mr1["inv_all"] = mr1.inv_crit & np.logical_and.reduce([mr1[g] == mr1[g + "_n"] for g in gen])
put_ci("mr1_inv_crit", mr1, "inv_crit", src_main + " bare vs noncrit P0 aligned")
put_ci("mr1_inv_all", mr1, "inv_all", src_main)
for m in MODELS:
    put(f"mr1_inv_crit_{SHORT[m]}", mr1[mr1.model == m].inv_crit.mean(), src_main)
    put(f"mr1_inv_all_{SHORT[m]}", mr1[mr1.model == m].inv_all.mean(), src_main)
# aggregate rate is unchanged even though outputs change
boot_diff(p0, "critical_match", "noncrit", "bare", "mr1_match_diff", src_main + " P0 noncrit minus bare")

# ---- MR2: cue restoration (chip1); MR3: full-input preservation
for ch in ["chip1", "chipall", "full", "bare", "noncrit"]:
    x = p0[p0.channel == ch]
    put_ci(f"match_{ch}", x, "critical_match", src_main + f" P0 {ch}")
    for dim in DIMS:
        put(f"match_{DSHORT[dim]}_{ch}", x[x.dimension == dim].critical_match.mean(), src_main)
    for m in MODELS:
        put(f"match_{ch}_{SHORT[m]}", x[x.model == m].critical_match.mean(), src_main)
boot_diff(p0, "critical_match", "chip1", "noncrit", "mr2_gain", src_main + " P0 chip1 minus noncrit")
boot_diff(p0, "critical_match", "full", "chip1", "full_minus_chip1", src_main)
cue = p0[p0.channel.isin(["chip1", "chipall", "full"])].copy()
cue["viol"] = cue.violation.astype(float)
for dim in DIMS:
    put(f"viol_{DSHORT[dim]}", cue[cue.dimension == dim].viol.mean(), src_main + " P0 cue-present")
put_frac("viol_chip1", int(p0[p0.channel == "chip1"].violation.astype(bool).sum()), int((p0.channel == "chip1").sum()), src_main)
f0 = p0[p0.channel == "full"].copy()
f0["any_contra_f"] = f0.any_contra.astype(float)
put_ci("full_contra", f0, "any_contra_f", src_main + " P0 full any general-dim contradiction")
for m in MODELS:
    put(f"full_contra_{SHORT[m]}", f0[f0.model == m].any_contra_f.mean(), src_main)

# ---- politeness ratchet (politeness families, P0)
pz = p0[p0.dimension == "politeness"]
for ch in ["bare", "noncrit", "chip1", "chipall", "full"]:
    x = pz[pz.channel == ch]
    pl, po = x[x.variant_value == "plain"], x[x.variant_value == "polite"]
    put_frac(f"pz_plainkept_{ch}", int(pl.critical_match.sum()), len(pl), src_main)
    put_frac(f"pz_politekept_{ch}", int(po.critical_match.sum()), len(po), src_main)
    for m in MODELS:
        put_frac(f"pz_plainkept_{ch}_{SHORT[m]}", int(pl[pl.model == m].critical_match.sum()), int((pl.model == m).sum()), src_main)
        put_frac(f"pz_politekept_{ch}_{SHORT[m]}", int(po[po.model == m].critical_match.sum()), int((po.model == m).sum()), src_main)
x = pz[pz.channel == "full"]
add = x[(x.variant_value == "plain") & (x.critical == "polite")]
rem = x[(x.variant_value == "polite") & (x.critical == "plain")]
put("pz_full_added", len(add), src_main, "int")
put("pz_full_removed", len(rem), src_main, "int")
put("pz_full_added_models", add.model.nunique(), src_main, "int")
put("pz_full_added_fams", add.family_id.nunique(), src_main, "int")
put("pz_full_den", int((x.variant_value == "plain").sum()), src_main, "int")
# politeness added anywhere on full input (all families, plain-spec rows)
fa = p0[(p0.channel == "full")]
put_frac("full_pz_added_allfam", int(fa.politeness_added.astype(bool).sum()), len(fa), src_main)


# certainty families with full input: hedges added to plain sources / removed from hedged ones
cf = p0[(p0.dimension == "certainty") & (p0.channel == "full")]
hp = cf[cf.variant_value == "hedged/uncertain"]
pp = cf[cf.variant_value != "hedged/uncertain"]
put_frac("cer_full_hedge_removed", int((hp.critical != "hedged/uncertain").sum()), len(hp), src_main)
put_frac("cer_full_hedge_added", int((pp.critical == "hedged/uncertain").sum()), len(pp), src_main)

# ---- cost asymmetry (analysis/main1/reaching_cost_by_model.csv, P0)
rc = pd.read_csv(ROOT / "analysis/main1/reaching_cost_by_model.csv")
rc0 = rc[(rc.prompt_id == "P0") & (rc.metric == "nondefault_extra_actions")]
put("cost_nondefault", rc0.estimate.mean(), "analysis/main1/reaching_cost_by_model.csv", "f2")
fc = pd.read_csv(ROOT / "analysis/main1/fidelity_cost.csv")
fc0 = fc[(fc.prompt_id == "P0") & (fc.metric == "input_actions")]
for ch in ["bare", "chip1", "chipall", "full"]:
    put(f"actions_{ch}", fc0[fc0.channel == ch].estimate.mean(), "analysis/main1/fidelity_cost.csv", "f2")


# figure-side numbers (paper/figs/make_figs.py computes them from the same scored.parquet);
# read here so text and figure cannot disagree.
FN = ROOT / "paper/figs/fig_numbers.json"
if FN.exists():
    fn = json.load(open(FN))
    ca = fn.get("fig_cost_asymmetry", {})
    for name, v in (ca.get("pooled") or {}).items():
        pr, reading = name.split("_", 1)
        tag = "nondef" if reading.startswith("non") else "def"
        for suf, fld in [("", "estimate"), ("_lo", "ci_low"), ("_hi", "ci_high")]:
            put(f"fcost_{pr.lower()}_{tag}{suf}", v[fld], "paper/figs/fig_numbers.json", "f2")
    put("fcost_n_fam", ca.get("n_families_with_default"), "paper/figs/fig_numbers.json", "int")

# ---------------------------------------------------------------- Exp B ----
B = ROOT / "runs/expB1/scored.parquet"
if B.exists():
    e = pd.read_parquet(B)
    e["critical_match"] = e["critical_match"].astype(bool)
    srcB = "runs/expB1/scored.parquet"
    put("xb_n_rows", len(e), srcB, "int")
    put("xb_n_fam", e.family_id.nunique(), srcB, "int")
    ex = e[e.prompt_id == "P0x"]  # common legend: all channels incl. padding/aliases
    xp = ex[(ex.dimension == "politeness")]
    for ch in ["i_crit", "i_x", "i_y", "i_xy", "i_pad", "e_chips", "e_alias", "e_nl"]:
        pl = xp[(xp.channel == ch) & (xp.variant_value == "plain")]
        put_frac(f"xb_plain_{ch.replace('_', '')}", int(pl.critical_match.sum()), len(pl), srcB + " P0x plain targets")
        for m in MODELS:
            q = pl[pl.model == m]
            put_frac(f"xb_plain_{ch.replace('_', '')}_{SHORT[m]}", int(q.critical_match.sum()), len(q), srcB)
    # pooled over both prompts (P0, P0x) and both draws, for channels that exist under both
    bp = e[(e.dimension == "politeness") & (e.variant_value == "plain")]
    for ch in ["i_crit", "i_x", "i_y", "i_xy"]:
        for m in MODELS + [None]:
            q = bp[(bp.channel == ch) & ((bp.model == m) if m else True)]
            put_frac(f"xbb_plain_{ch.replace('_', '')}" + (f"_{SHORT[m]}" if m else ""), int(q.critical_match.sum()), len(q), srcB + " P0+P0x plain targets")
    for ch in ["e_chips", "e_alias", "e_nl"]:
        q = ex[ex.channel == ch]
        put(f"xb_enc_{ch.replace('_', '')}", q.critical_match.mean(), srcB + " P0x both dims")
        for m in MODELS:
            put(f"xb_enc_{ch.replace('_', '')}_{SHORT[m]}", q[q.model == m].critical_match.mean(), srcB)
    put("xb_ready", 1, srcB, "int")

# ---------------------------------------------------------------- Exp C ----
C = ROOT / "runs/expC1/scored.parquet"
if C.exists():
    c = pd.read_parquet(C)
    c["critical_match"] = c["critical_match"].astype(bool)
    srcC = "runs/expC1/scored.parquet"
    pc = c[c.dimension == "polarity"]
    ac = c[c.dimension == "agent"]
    put_frac("xc_pol_single", int(pc[pc.channel == "pol"].critical_match.sum()), int((pc.channel == "pol").sum()), srcC)
    put_frac("xc_pol_both", int(pc[pc.channel == "both"].critical_match.sum()), int((pc.channel == "both").sum()), srcC)
    put_frac("xc_agt_single", int(ac[ac.channel == "actor"].critical_match.sum()), int((ac.channel == "actor").sum()), srcC)
    put_frac("xc_agt_both", int(ac[ac.channel == "both"].critical_match.sum()), int((ac.channel == "both").sum()), srcC)
    boot_diff(pc, "critical_match", "both", "pol", "xc_pol_drop", srcC)
    boot_diff(ac, "critical_match", "both", "actor", "xc_agt_drop", srcC)
    for m in MODELS:
        for dimdf, single, tag in [(pc, "pol", "pol"), (ac, "actor", "agt")]:
            for chn in [single, "both", "neither"]:
                q_ = dimdf[(dimdf.model == m) & (dimdf.channel == chn)]
                put_frac(f"xc_{tag}_{'single' if chn == single else chn}_{SHORT[m]}", int(q_.critical_match.sum()), len(q_), srcC)
    put("xc_n_fam", c.get("factorial_family", c.family_id.str[:5]).nunique() if "factorial_family" in c else c.family_id.str[:5].nunique(), srcC, "int")
    put("xc_ready", 1, srcC, "int")

# ------------------------------------------------- nondeterminism (draws) ---
agree = defaultdict(lambda: [0, 0])
for run in ["expB1", "expC1"]:
    gp = ROOT / f"runs/{run}/generations.jsonl"
    if not gp.exists():
        continue
    by = defaultdict(dict)
    for line in open(gp):
        r = json.loads(line)
        by[(run, r["model"], r["prompt_id"], r["input_text"], r["sample_idx"])][r.get("namespace")] = r["raw_text"].strip()
    for k, v in by.items():
        if "d1" in v and "d2" in v:
            agree[(run, k[1])][0] += v["d1"] == v["d2"]
            agree[(run, k[1])][1] += 1
rates = {k: a / n for k, (a, n) in agree.items() if n}
if rates:
    api = [v for (run, m), v in rates.items() if m == "gpt-6.1-terra"]
    loc = [v for (run, m), v in rates.items() if m != "gpt-6.1-terra"]
    put("nd_api_min", min(api), "runs/expB1,expC1 generations.jsonl d1 vs d2")
    put("nd_api_max", max(api), "runs/expB1,expC1 generations.jsonl d1 vs d2")
    put("nd_local_min", min(loc), "runs/expB1,expC1 generations.jsonl d1 vs d2")
    put("nd_local_max", max(loc), "runs/expB1,expC1 generations.jsonl d1 vs d2")

# ------------------------------------------------------------------- S1 ----
mm = ROOT / "analysis/s1/message_metrics.csv"
if mm.exists():
    s = pd.read_csv(mm)
    s = s[s.compressor == "pos_cap4"]
    lost = s.lost_dimensions.map(json.loads)
    put("s1_n", len(s), str(mm.relative_to(ROOT)), "int")
    put("s1_loss_any", s.any_loss.astype(bool).mean(), str(mm.relative_to(ROOT)))
    put("s1_loss_excl_agent", lost.map(lambda x: any(v for k, v in x.items() if k != "agent")).mean(), str(mm.relative_to(ROOT)))
    put("s1_loss_pol", lost.map(lambda x: x.get("polarity", False)).mean(), str(mm.relative_to(ROOT)))
    put("s1_loss_act", lost.map(lambda x: x.get("speech_act", False)).mean(), str(mm.relative_to(ROOT)))
    put("s1_collision", s.collision.astype(bool).mean(), str(mm.relative_to(ROOT)))

# ------------------------------------------------------- oracle validation ---
ch = ROOT / "annotation/challenge_items.jsonl"
if ch.exists():
    put("challenge_n", sum(1 for _ in open(ch)), str(ch.relative_to(ROOT)), "int")
gk = ROOT / "annotation/gold_key_main1.csv"
if gk.exists():
    g = pd.read_csv(gk)
    put("gold_n", len(g), str(gk.relative_to(ROOT)), "int")
    put("gold_fams", g.family_id.nunique(), str(gk.relative_to(ROOT)), "int")
returns = sorted(glob.glob(str(ROOT / "annotation/returns/*.csv")))
put("human_returns", len(returns), "annotation/returns/*.csv", "int")
# When human returns exist, run src/score_gold.py and add its outputs here (keys: human_alpha,
# judge_kappa, judge_sens_violation, judge_spec_violation, challenge_acc). Until then the paper
# prints the validation section conditionally (\IfRES{oracle_ready}).
sg = ROOT / "annotation/score_gold_main1.json"
if sg.exists():
    r = json.load(open(sg))
    for k in ["human_alpha", "judge_kappa", "judge_kappa_min", "judge_sens_violation",
              "judge_spec_violation", "challenge_acc"]:
        if k in r:
            put(k, r[k], str(sg.relative_to(ROOT)), "f2" if "kappa" in k or "alpha" in k else "pct")
    put("oracle_ready", 1, str(sg.relative_to(ROOT)), "int")


# ------------------------------------------- oracle identity relation (D-015) ---
# MR0 (identity): if the output repeats the full source verbatim, the verdict must be PASS.
import re as _re
_all_items = {}
for _f in sorted(glob.glob(str(ROOT / "data/items/*.jsonl"))):
    for _l in open(_f):
        _r = json.loads(_l)
        _all_items[_r["family_id"]] = _r


def _norm(t: str) -> str:
    return _re.sub(r"[^a-z0-9 ]", "", t.lower().replace("’", "'").replace("'", "")).strip()


def identity_rows(df):
    f = df[df.channel == "full"].copy()
    f["src"] = [_all_items[a]["variants"][b]["source"] for a, b in zip(f.family_id, f.variant)]
    return f[[_norm(a) == _norm(b) for a, b in zip(f.text, f.src)]]


RAW = ROOT / "runs/main1/scored_raw_oracle.parquet"
if RAW.exists():
    raw = pd.read_parquet(RAW)
    vr = identity_rows(raw)
    fails = vr[~vr.critical_match.astype(bool)]
    srcI = "runs/main1/scored_raw_oracle.parquet (ORACLE_RAW=1), full channel, verbatim outputs, all prompts"
    put("id_n", len(vr), srcI, "int")
    put("id_fail_raw", len(fails), srcI, "int")
    put("id_fail_raw_fams", fails.family_id.nunique(), srcI, "int")
    put("id_contra_raw", int(vr.any_contra.astype(bool).sum()), srcI, "int")
    if len(fails):
        top = fails.groupby(["variant_value", "critical"]).size().sort_values(ascending=False)
        put("id_fail_want", top.index[0][0], srcI, "str")
        put("id_fail_got", top.index[0][1], srcI, "str")
        put("id_fail_share_top", top.iloc[0] / len(fails), srcI)
    vf = identity_rows(d)
    put("id_fail_fixed", int((~vf.critical_match.astype(bool)).sum()), src_main + " (fixed oracle, D-015)", "int")
    # how much the fix moves the headline cue-present numbers
    r0 = raw[(raw.prompt_id == "P0") & (raw.channel == "full")]
    put("match_full_raw", r0.critical_match.astype(bool).mean(), srcI)

# speech-act cue weakness (C11): chip1 by target value, and [?] -> request conversions
sa = p0[(p0.dimension == "speech_act") & (p0.channel == "chip1")]
for val in ["question", "request/command", "statement", "refusal", "acceptance"]:
    x = sa[sa.variant_value == val]
    if len(x):
        put_frac("act_chip1_" + val.split("/")[0], int(x.critical_match.sum()), len(x), src_main)
qx = sa[sa.input_text.str.contains(r"\[\?\]", regex=True)]
put_frac("act_q_to_req", int((qx.critical == "request/command").sum()), len(qx), src_main + " chip1 inputs with [?]")
put_frac("act_q_to_offer", int((qx.critical == "offer/suggestion").sum()), len(qx), src_main + " chip1 inputs with [?]")
fr = p0[(p0.dimension == "speech_act") & (p0.channel == "full") & (p0.variant_value == "refusal")]
put_frac("act_full_refusal_kept", int(fr.critical_match.sum()), len(fr), src_main)

# --------------------------------------------------------- examples table ---
# Declared deterministic rule (also printed in the table caption):
#   prompt P0; families sorted by family_id; models in the fixed order MODELS;
#   E1-E3: first polarity family; its negated variant; channels bare / noncrit / chip1; first model.
#   E4: first politeness family whose plain variant, under `full`, gets an output labelled polite;
#       first such model in MODELS order.
#   E5: first speech_act row (family, then variant A<B, then model order) with a chip1 violation.
#   E6: first politeness plain-target row under chipall that is a violation.
items = {}
for line in open(ROOT / "data/items/test.jsonl"):
    r = json.loads(line)
    items[r["family_id"]] = r
texts = {}
op = ROOT / "runs/main1/outputs.jsonl"
for line in open(op):
    r = json.loads(line)
    texts[r["output_id"]] = r["text"]
morder = {m: i for i, m in enumerate(MODELS)}
q = p0.assign(mo=p0.model.map(morder)).sort_values(["family_id", "variant", "mo"])


def first(df):
    return None if df.empty else df.iloc[0]


rows = []
fam_pol = sorted(q[q.dimension == "polarity"].family_id.unique())[0]
negv = [v for v, s in items[fam_pol]["variants"].items() if s["critical_value"] == "negated"][0]
for ch_, rel in [("bare", "Ambiguous input"), ("noncrit", "MR1 $+$noncritical word"), ("chip1", "MR2 $+$cue")]:
    rows.append((rel, first(q[(q.family_id == fam_pol) & (q.variant == negv) & (q.channel == ch_) & (q.model == MODELS[0])])))
x = q[(q.dimension == "politeness") & (q.channel == "full") & (q.variant_value == "plain") & (q.critical == "polite")]
rows.append(("MR3 full input", first(x)))
x = q[(q.dimension == "speech_act") & (q.channel == "chip1") & (q.violation == True)]  # noqa: E712
rows.append(("MR2 $+$cue", first(x)))
x = q[(q.dimension == "politeness") & (q.channel == "chipall") & (q.variant_value == "plain") & (q.violation == True)]  # noqa: E712
rows.append(("All cues", first(x)))


def tex(s: str) -> str:
    s = str(s).replace("’", "'")
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    return s


def visible(inp: str) -> str:
    inp = inp.replace("Keywords: ", "").replace("The user typed: ", "typed: ")
    out = []
    for tok in inp.split(" "):
        out.append(r"\chip{" + tex(tok[1:-1]) + "}" if tok.startswith("[") and tok.endswith("]") else tex(tok))
    return r"\kw{" + " ".join(out) + "}"


def verdict(r) -> str:
    if r.channel in ("bare", "noncrit"):
        return ("commits: " if r.critical != "unclear/mixed" else "no commitment: ") + tex(r.critical)
    ok = bool(r.critical_match)
    return (r"\textsc{pass}" if ok else r"\textsc{fail}") + f" (wants {tex(r.variant_value)}, got {tex(r.critical)})"


lines = []
for rel, r in rows:
    if r is None:
        continue
    src_txt = items[r.family_id]["variants"][r.variant]["source"]
    out_txt = texts.get(r.output_id, r.text)
    lines.append(f"{rel} & {tex(src_txt)} & {visible(r.input_text)} & \\say{{{tex(out_txt)}}} ({SHORT[r.model]}) & {verdict(r)}\\\\")
(OUT / "examples_table.tex").write_text(
    "% generated by make_macros.py -- do not edit\n" + "\n".join(lines) + "\n")

# ------------------------------------------------------------------ write ---
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


hdr = [
    "% results_macros.tex -- GENERATED by paper/se4all/make_macros.py. Do not edit by hand.",
    f"% inputs: runs/main1/scored.parquet sha256:{sha(SC)}"
    + (f"; runs/expB1/scored.parquet sha256:{sha(B)}" if B.exists() else "; expB1: absent")
    + (f"; runs/expC1/scored.parquet sha256:{sha(C)}" if C.exists() else "; expC1 scored: absent (PENDING)"),
    f"% make_macros.py sha256:{sha(Path(__file__))}; labels: judge final (J1==J2, else J1 fallback); human gold: "
    + ("present" if "oracle_ready" in macros else "PENDING"),
    "% Percentages are 0-100 with one decimal; *_pp are percentage points; *_k/*_den are counts.",
]
body = [f"\\resdef{{{k}}}{{{v}}} % {sources[k]}" for k, v in sorted(macros.items())]
(OUT / "results_macros.tex").write_text("\n".join(hdr + body) + "\n")
print(f"wrote {len(macros)} macros, {len(lines)} example rows", file=sys.stderr)
