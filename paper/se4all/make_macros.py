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
sys.path.insert(0, str(ROOT / "src"))
from analyze import family_bootstrap
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
    x = df[[cluster, col]].rename(columns={cluster: "family_id"})
    if x.empty:
        return np.nan, np.nan, np.nan, 0
    r = family_bootstrap(x, col, n_boot=NBOOT, seed=SEED)
    return r['estimate'], r['ci_low'], r['ci_high'], r['n']


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
all_scored = d.copy()
src_main = "runs/main1/scored.parquet; shared resolution; primary excludes act-10/act-16"
put("n_fam_test", d.family_id.nunique(), "runs/main1/scored.parquet (design inventory)", "int")
d = d[~d.quarantine_refusal_acceptance.fillna(False).astype(bool)].copy()
d["critical_match"] = d["critical_match"].astype(bool)
p0 = d[d.prompt_id == "P0"].copy()

put("n_fam_primary", d.family_id.nunique(), src_main, "int")
put("n_fam_quarantined", all_scored.family_id.nunique() - d.family_id.nunique(), src_main, "int")
for ch in ["chip1", "chipall", "full"]:
    inclusive = all_scored[(all_scored.prompt_id == "P0") & (all_scored.channel == ch)]
    put_frac(f"sensitivity_match_{ch}", int(inclusive.critical_match.sum()), len(inclusive),
             "runs/main1/scored.parquet; quarantine-inclusive sensitivity")
put("n_fam_dim", all_scored.groupby("dimension").family_id.nunique().min(), "runs/main1/scored.parquet (design inventory)", "int")
put("n_fam_dim_primary_min", d.groupby("dimension").family_id.nunique().min(), src_main, "int")
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
    put(f"cov_{pr.lower()}_all", (x.estimate*x.n).sum()/x.n.sum(), "analysis/main1/coverage.csv (weighted by observed sets)")

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
    pa = fn.get("fig_politeness_ratchet", {}).get("politeness_added_all_plain_sources", {})
    if pa:
        put_frac("full_pz_added_allfam", round(pa['Pooled']*pa['n']), pa['n'],
                 "paper/figs/fig_numbers.json; P0 full, source specs with plain politeness")
    ca = fn.get("fig_cost_asymmetry", {})
    for name, v in (ca.get("pooled") or {}).items():
        pr, reading = name.split("_", 1)
        tag = "nondef" if reading.startswith("non") else "def"
        for suf, fld in [("", "estimate"), ("_lo", "ci_low"), ("_hi", "ci_high")]:
            put(f"fcost_{pr.lower()}_{tag}{suf}", v[fld], "paper/figs/fig_numbers.json", "f2")
    put("fcost_n_fam", ca.get("n_families_with_default"), "paper/figs/fig_numbers.json", "int")
    for ch in ['chip1', 'chipall', 'full']:
        q = p0[p0.channel.eq(ch)]
        put_frac(f"joint_{ch}", int(q.constraint_preserving.sum()), int(q.constraint_preserving.notna().sum()), src_main)

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
    vf = identity_rows(all_scored)
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

# ============================================== REVISION (cycle-1 decision) ===
# Everything below reads the ACTION-2 refreshed artifacts (shared label resolution,
# primary exclusion of act-10/act-16). Each block is optional: missing inputs leave the
# keys undefined and main.tex prints \pending or a red [key].
def wilson(k, n, z=1.959964):
    if not n:
        return np.nan, np.nan
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def put_wilson(key, k, n, src):
    put_frac(key, k, n, src)
    lo, hi = wilson(k, n)
    put(key + "_lo", lo, src + " (Wilson 95%)")
    put(key + "_hi", hi, src + " (Wilson 95%)")


# ---- counts behind the headline percentages (primary pool)
for ch in ["bare", "noncrit", "chip1", "chipall", "full"]:
    q_ = p0[p0.channel == ch]
    put_frac(f"cm_{ch}", int(q_.critical_match.sum()), len(q_), src_main + f" P0 {ch} critical match")
put("n_targets_channel", len(p0[p0.channel == "full"]), src_main + " P0 targets per channel", "int")

# ---- E1 rates: negated chip1 targets
negc = p0[(p0.channel == "chip1") & (p0.dimension == "polarity") & (p0.variant_value == "negated")]
put_frac("pol_neg_chip1", int(negc.critical_match.sum()), len(negc), src_main + " P0 chip1 negated targets")

# ---- E3 / full-input politeness, per model, P1 cached sensitivity, paired difference
def pz_dir(frame):
    pl, po = frame[frame.variant_value == "plain"], frame[frame.variant_value == "polite"]
    return pl, po, pl.critical == "polite", po.critical == "plain"


pzf = d[(d.dimension == "politeness") & (d.channel == "full")]
for pr in ["P0", "P1"]:
    pl, po, a, r = pz_dir(pzf[pzf.prompt_id == pr])
    tag = pr.lower()
    put_frac(f"{tag}_pz_added", int(a.sum()), len(pl), src_main + f" {pr} full politeness plain targets made polite"
             + (" (cached P1 sensitivity, not a primary arm; D-010)" if pr == "P1" else ""))
    put_frac(f"{tag}_pz_removed", int(r.sum()), len(po), src_main + f" {pr} full polite targets made plain")
    for m in MODELS:
        put_frac(f"{tag}_pz_added_{SHORT[m]}", int(a[pl.model == m].sum()), int((pl.model == m).sum()), src_main)
        put_frac(f"{tag}_pz_removed_{SHORT[m]}", int(r[po.model == m].sum()), int((po.model == m).sum()), src_main)
# paired addition-minus-removal over families (P0)
pl, po, a, r = pz_dir(pzf[pzf.prompt_id == "P0"])
fa_ = pd.DataFrame({"family_id": pl.family_id, "v": a.astype(float)}).groupby("family_id").v.agg(["sum", "count"])
fr_ = pd.DataFrame({"family_id": po.family_id, "v": r.astype(float)}).groupby("family_id").v.agg(["sum", "count"])
m_ = fa_.add_suffix("_a").join(fr_.add_suffix("_r")).dropna()
rng = np.random.default_rng(SEED)
idx = rng.integers(0, len(m_), size=(NBOOT, len(m_)))
sa, na, sr, nr = (m_[c].to_numpy() for c in ["sum_a", "count_a", "sum_r", "count_r"])
bs = sa[idx].sum(1) / na[idx].sum(1) - sr[idx].sum(1) / nr[idx].sum(1)
put("pz_full_asym", sa.sum() / na.sum() - sr.sum() / nr.sum(), src_main + " P0 full: added minus removed", "pp")
put("pz_full_asym_lo", np.percentile(bs, 2.5), src_main, "pp")
put("pz_full_asym_hi", np.percentile(bs, 97.5), src_main, "pp")
put("pz_n_fam", pzf.family_id.nunique(), src_main, "int")

# ---- nominal-cost honesty: bare P0 target misses that chip1 does not repair
kk = ["family_id", "variant", "model"]
jj = p0[p0.channel == "bare"][kk + ["critical_match"]].merge(
    p0[p0.channel == "chip1"][kk + ["critical_match"]], on=kk, suffixes=("_b", "_c"))
miss = jj[~jj.critical_match_b.astype(bool)]
put_frac("bare_miss_chip1_fail", int((~miss.critical_match_c.astype(bool)).sum()), len(miss),
         src_main + " P0 bare target misses whose chip1 output also misses")

# ---- MR1 as default-sensitivity: without time/quantity families (supplied-time words)
mr1_ntq = mr1[mr1.dimension != "time_quantity"]
put_frac("mr1_crit_ntq", int(mr1_ntq.inv_crit.sum()), len(mr1_ntq), src_main + " bare vs noncrit, excl. time/quantity")
put_frac("mr1_crit", int(mr1.inv_crit.sum()), len(mr1), src_main + " bare vs noncrit")

# ---- oracle evidence status (analysis/oracle/*.csv; authored inputs, Wilson CIs)
OI = ROOT / "analysis/oracle/injection_results.csv"
if OI.exists():
    inj = pd.read_csv(OI)
    ide, mut = inj[inj.model == "identity"], inj[inj.model == "mutant"]
    put_wilson("or_identity_fa", int((~ide.constraint_preserving.astype(bool)).sum()), len(ide),
               "analysis/oracle/injection_results.csv identity (contract false alarm)")
    put_wilson("or_mut_det", int(mut.violation.astype(bool).sum()), len(mut),
               "analysis/oracle/injection_results.csv scoped mutations detected as Violation")
OC = ROOT / "analysis/oracle/challenge_results.csv"
if OC.exists():
    chl = pd.read_csv(OC)
    new = chl[chl.role.isin(["control", "mutant"])]
    mu, co = new[new.role == "mutant"], new[new.role == "control"]
    srcC_ = "analysis/oracle/challenge_results.csv (new keyed challenges, production rule)"
    put_wilson("or_new_mut_det", int((~mu.match_prod.astype(bool)).sum()), len(mu), srcC_)
    put_wilson("or_new_ctrl_fa", int((~co.match_prod.astype(bool)).sum()), len(co), srcC_)
    put_wilson("or_new_mut_det_raw", int((~mu.match_raw.astype(bool)).sum()), len(mu), srcC_ + " raw rule")
    am, ac = mu[mu.group == "acceptance"], co[co.group == "acceptance"]
    put_wilson("or_acc_mut_det", int((~am.match_prod.astype(bool)).sum()), len(am), srcC_ + " acceptance group")
    put_wilson("or_acc_ctrl_fa", int((~ac.match_prod.astype(bool)).sum()), len(ac), srcC_ + " acceptance group")
    put("n_groups_challenge", new.group.nunique(), srcC_, "int")
    r1 = chl[chl.role == "r1"]
    put_frac("or_r1_label_ok", int(r1.label_ok.astype(bool).sum()), len(r1), "analysis/oracle/challenge_results.csv round-1")
OS = ROOT / "analysis/oracle/refreshed_summary.json"
if OS.exists():
    osum = json.load(open(OS))["primary"]["violation"]
    put_frac("or_panel_flip", osum["units_flipped"], osum["n_units"], str(OS.relative_to(ROOT)) + " machine panel, not human")
    put("or_panel_flip_w", osum["weighted_flip"], str(OS.relative_to(ROOT)))
JV = ROOT / "annotation/judge_validation_main1.json"
if JV.exists():
    jv = json.load(open(JV))
    sys.path.insert(0, str(ROOT / "src"))
    from score_gold import paper_macros
    srcJV = str(JV.relative_to(ROOT))
    pan = jv.get("panel") or {}
    kap = [t["kappa"] for t in ((v.get("sampled/final") or {}) for v in (pan.get("judge") or {}).values()
                                if isinstance(v, dict)) if t.get("kappa") is not None]
    if kap:
        put("panel_kappa_min", min(kap), srcJV + " panel (machine), sampled/final", "f2")
    # HUMAN SECTION (score_gold.py --human): exported with prefix human_ via the shared
    # score_gold.paper_macros (per-dimension alpha, judge kappa / weighted kappa / accuracy
    # with Wilson CI / n, H7 gate on the test split, challenge subset, verdict-level
    # agreement, challenge-key accuracy). The paper's conditional block keys on human_ready.
    for k_, v_ in paper_macros(jv.get("human") or {}, "human").items():
        put(k_, v_, srcJV + " human section", "raw")
put("human_return_files", len(glob.glob(str(ROOT / "annotation/returns/*.csv"))), "annotation/returns/*.csv", "int")

# ---- guard + copy baseline (analysis/interventions/report.json, primary 58 families)
IR = ROOT / "analysis/interventions/report.json"
if IR.exists():
    ir = json.load(open(IR))
    g_ = ir["guard"]
    srcG = "analysis/interventions/report.json guard (primary 58 families)"
    cue = g_["G1_cue"]
    put_frac("g1_fix", round(cue["fix"]["estimate"] * cue["n_bad"]), cue["n_bad"], srcG)
    put("g1_fix_lo", cue["fix"]["ci_low"], srcG); put("g1_fix_hi", cue["fix"]["ci_high"], srcG)
    put("g1_remain_k", cue["n_bad"] - round(cue["fix"]["estimate"] * cue["n_bad"]), srcG, "int")
    put_frac("g1_changed_ok", round(cue["overcorr"]["estimate"] * cue["n_ok"]), cue["n_ok"], srcG + " cue-channel already-correct changed")
    put_frac("g1_broken", round(cue["broken"]["estimate"] * cue["n_ok"]), cue["n_ok"], srcG + " pass->fail")
    put_frac("g1s_fix", round(g_["G1s_cue"]["fix"]["estimate"] * cue["n_bad"]), cue["n_bad"], srcG + " strip-only")
    for arm in ["P0", "G1", "G1s"]:
        put(f"strict_{arm.lower()}", g_[arm]["sp"]["estimate"], srcG)
        put(f"strict_{arm.lower()}_lo", g_[arm]["sp"]["ci_low"], srcG)
        put(f"strict_{arm.lower()}_hi", g_[arm]["sp"]["ci_high"], srcG)
    put("strict_n", g_["P0"]["sp"]["n"], srcG, "int")
    put("g1_calls", g_["cost"]["calls_per_input"], srcG, "f3")
    put("g1_lat", g_["cost"]["lat_per_input"], srcG, "f2")
    put("g1_flagged_pct", g_["cost"]["flagged"] / g_["cost"]["inputs"], srcG)
    put("g1_check_ms", g_["cost"]["check_ms"], srcG, "f2")
    lv = g_["l0_vs_judge"]
    put("mon_prec", lv["tp"] / (lv["tp"] + lv["fp"]), srcG, "f2")
    put("mon_rec", lv["tp"] / (lv["tp"] + lv["fn"]), srcG, "f2")
    cp = ir.get("copy_full_mode")
    if cp:
        srcK = "analysis/interventions/report.json copy_full_mode (stored source-identity injections)"
        put_frac("copy_pass", cp["primary_pass"], cp["primary_n"], srcK)
        put_frac("copy_pass_all", cp["identity_pass"], cp["identity_n"], srcK)
        for arm in ["P0", "G1", "G1s"]:
            a_ = cp["arms"][arm]["contract"]
            put_frac(f"fullmode_{arm.lower()}", round(a_["estimate"] * a_["n"]), a_["n"], srcK)
            put(f"fullmode_{arm.lower()}_lo", a_["ci_low"], srcK); put(f"fullmode_{arm.lower()}_hi", a_["ci_high"], srcK)

# ---- Exp C: physical-scenario clustering and paired transitions (fixes the 16-ID cluster)
if C.exists():
    gen_ns = {}
    for line in open(ROOT / "runs/expC1/generations.jsonl"):
        r_ = json.loads(line)
        gen_ns[(r_["request_key"], r_["model"])] = r_.get("namespace")
    cc = c.copy()
    cc["scenario"] = cc.family_id.str[:5]
    cc["draw"] = [gen_ns.get((a, b)) for a, b in zip(cc.request_key, cc.model)]
    put("xc_n_scen", cc.scenario.nunique(), srcC, "int")
    for dimn, single, tag in [("agent", "actor", "agt"), ("polarity", "pol", "pol")]:
        x = cc[cc.dimension == dimn]
        boot_diff(x.assign(family_id=x.scenario), "critical_match", "both", single, f"xc_{tag}_drop_scen", srcC + " clustered by 8 physical scenarios")
        kk2 = ["family_id", "variant", "model", "draw"]
        aa = x[x.channel == single][kk2 + ["critical_match"]].merge(
            x[x.channel == "both"][kk2 + ["critical_match"]], on=kk2, suffixes=("_s", "_b"))
        put("xc_" + tag + "_pf", int((aa.critical_match_s & ~aa.critical_match_b).sum()), srcC + " pass->fail", "int")
        put("xc_" + tag + "_fp", int((~aa.critical_match_s & aa.critical_match_b).sum()), srcC + " fail->pass", "int")
        put("xc_" + tag + "_pass_single", int(aa.critical_match_s.sum()), srcC, "int")
        put("xc_" + tag + "_aligned", len(aa), srcC, "int")
        for m in MODELS:
            put(f"xc_{tag}_pf_{SHORT[m]}", int((aa[aa.model == m].critical_match_s & ~aa[aa.model == m].critical_match_b).sum()), srcC, "int")

# ---- label resolution actually used (shared arbiter > J1/J2 agreement > unknown; no J1 fallback)
dm = d[d.prompt_id != "P1"]
put("n_arbiter_rows", int((dm.critical_source == "arbiter").sum()), src_main + " P0/P2/S3 rows resolved by arbiter", "int")
put("n_arbiter_units", int(dm[dm.critical_source == "arbiter"].drop_duplicates(["text_id", "input_text", "dimension"]).shape[0]),
    src_main + " distinct (text,input,dimension) units resolved by arbiter", "int")
put("n_unknown_rows", int(dm.critical.isna().sum()), src_main + " unresolved critical labels", "int")

# ---- coverage@3 counts (bare P2/S3), so the text can print k/n beside the percentage
for pr in ["P2", "S3"]:
    for dim in ["polarity"]:
        x = cov[(cov.prompt_id == pr) & (cov.dimension == dim)]
        put_frac(f"covk_{pr.lower()}_{DSHORT[dim]}", int(round((x.estimate * x.n).sum())), int(x.n.sum()),
                 "analysis/main1/coverage.csv (sets)")

# ---- exploratory H1 (cycle-1 hypothesis screen; replication is W-C's job)
HC = ROOT / "ideas/cycles/c1/hyp_checks.json"
if HC.exists():
    hc = json.load(open(HC))
    h = hc.get("H1/main1/P0/llama3.1-8b")
    if h:
        put_frac("h1_llama_plain", int(h["plain"]["k"]), h["plain"]["n"], str(HC.relative_to(ROOT)) + " exploratory")
        put_frac("h1_llama_polite", int(h["polite"]["k"]), h["polite"]["n"], str(HC.relative_to(ROOT)) + " exploratory")

# ---- round-2 slots: W-B transfer, W-C confirmation, W-D encoding control.
# A workstream switches on only when its report exists; a sibling headline.json (flat
# {key: number}) is exported with the prefix wb_/wc_/wd_. No numbers are hand-copied.
for tag, rels in [("wb", ["analysis/wb/report.md", "analysis/wb/report_wb1i.md"]),
                  ("wc", ["analysis/r2c/report.md"]), ("wd", ["analysis/r2d/report.md"])]:
    for rel in rels:
        rp = ROOT / rel
        if rp.exists():
            put(f"{tag}_ready", 1, rel, "int")
            put(f"{tag}_interim", int("wb1i" in rel), rel, "int")
            hj = rp.parent / "headline.json"
            if hj.exists():
                for k_, v_ in json.load(open(hj)).items():
                    if isinstance(v_, (int, float)):
                        put(f"{tag}_{k_}", v_, str(hj.relative_to(ROOT)), "int" if isinstance(v_, int) else "f3")
            break

# --------------------------------------------------------- examples table ---
# Examples are NOT reselected here. They are the stored occurrences frozen in
# paper/figs/example_manifest.json (story rules E1-E10, ideas/cycles/c1/story.md). This
# script re-reads every quoted string from runs/<run>/outputs.jsonl by output_id and
# aborts on any mismatch, then prints each row with the rate of its declared stratum
# (as \RES keys, so the rate cannot drift from the macros).
def tex(s: str) -> str:
    s = str(s).replace("’", "'")
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    return s


def visible(inp: str) -> str:
    full = inp.startswith("The user typed: ")
    inp = inp.replace("Keywords: ", "").replace("The user typed: ", "")
    out = []
    for tok in inp.split(" "):
        out.append(r"\chip{" + tex(tok[1:-1]) + "}" if tok.startswith("[") and tok.endswith("]") else tex(tok))
    return (r"\emph{typed:} " if full else "") + r"\kw{" + " ".join(out) + "}"


EM = ROOT / "paper/figs/example_manifest.json"
man = json.load(open(EM))
occ = defaultdict(list)
for e in man["examples"]:
    occ[e["example"]].append(e)
_out_cache: dict[str, dict] = {}


def stored(run: str, oid: str) -> str:
    if run not in _out_cache:
        _out_cache[run] = {}
        for line in open(ROOT / f"runs/{run}/outputs.jsonl"):
            r = json.loads(line)
            _out_cache[run].setdefault(r["output_id"], r["text"])
    return _out_cache[run][oid]


n_verified = 0
for ex_id, es in occ.items():
    for e in es:
        o = e["occurrence"]
        if stored(e["run"], o["output_id"]) != o["text"]:
            raise SystemExit(f"example {ex_id} {o['output_id']}: manifest text != stored output")
        n_verified += 1
put("ex_n_verified", n_verified, str(EM.relative_to(ROOT)) + " strings re-read from runs/*/outputs.jsonl", "int")


def q(e):
    return r"\say{" + tex(e["occurrence"]["text"]) + "}"


def meta(e):
    o = e["occurrence"]
    return (f"{SHORT[o['model']]}, {tex(o['family_id'])}/{o['variant']}, {o['prompt_id']}, "
            f"{tex(o['channel'])}; \\texttt{{{o['output_id'][:8]}}}")


rows = []
E = occ
# E3 (lead): full-input politeness addition
e = E["E3"][0]
rows.append(("E3 full input", visible(e["occurrence"]["input_text"]), q(e), meta(e),
             r"plain$\to$polite \kof{p0_pz_added} (pooled); this model \kof{p0_pz_added_llama}; "
             r"reverse \kof{p0_pz_removed}"))
# E1: default, length control, supplied cue
for e, rate in zip(E["E1"], [r"affirmative in \kof{bare_pol_aff_p0} bare outputs (default, not a failure)",
                             r"length control / default-sensitivity diagnostic",
                             r"negated cue kept \kof{pol_neg_chip1}"]):
    rows.append(("E1 " + e["occurrence"]["channel"], visible(e["occurrence"]["input_text"]), q(e), meta(e), rate))
# E4: weak question cue
e = E["E4"][0]
rows.append(("E4 chip1", visible(e["occurrence"]["input_text"]), q(e), meta(e),
             r"question kept \kof{act_chip1_question}; became request \kof{act_q_to_req}"))
# E5 / E6: guard repair and residual
for tag, rate in [("E5", r"repaired: \kof{g1_fix} cue-channel failures"),
                  ("E6", r"still failing: \RES{g1_remain_k}/\RES{g1_fix_den}")]:
    b_, a_ = E[tag][0], E[tag][1]
    rows.append((tag + r" guard", visible(b_["occurrence"]["input_text"]),
                 q(b_) + r"\,$\to$\," + q(a_), meta(b_).replace(", P0,", r", P0$\to$G1,"), rate))
# E10: oracle identity defect (quarantined family; diagnostic only)
e = E["E10"][0]
rows.append(("E10 oracle", visible(e["occurrence"]["input_text"]), q(e), meta(e),
             r"raw oracle failed \RES{id_fail_raw}/\RES{id_n} normalized identity outputs; quarantined"))
lines = [f"{a} & {b} & {c} & {d} & {e_}\\\\[2pt]" for a, b, c, d, e_ in rows]
(OUT / "examples_table.tex").write_text(
    "% generated by make_macros.py from paper/figs/example_manifest.json -- do not edit\n" + "\n".join(lines) + "\n")

# ------------------------------------------------------------------ write ---
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


hdr = [
    "% results_macros.tex -- GENERATED by paper/se4all/make_macros.py. Do not edit by hand.",
    f"% inputs: runs/main1/scored.parquet sha256:{sha(SC)}"
    + (f"; runs/expB1/scored.parquet sha256:{sha(B)}" if B.exists() else "; expB1: absent")
    + (f"; runs/expC1/scored.parquet sha256:{sha(C)}" if C.exists() else "; expC1 scored: absent (PENDING)"),
    f"% make_macros.py sha256:{sha(Path(__file__))}; resolution sha256:{sha(ROOT / 'annotation/label_resolution.jsonl')}; "
    "labels: shared arbiter > J1/J2 agreement > unknown; human gold: "
    + ("present (human_ready)" if "human_ready" in macros else "PENDING"),
    "% Percentages are 0-100 with one decimal; *_pp are percentage points; *_k/*_den are counts.",
]
body = [f"\\resdef{{{k}}}{{{v}}} % {sources[k]}" for k, v in sorted(macros.items())]
(OUT / "results_macros.tex").write_text("\n".join(hdr + body) + "\n")
print(f"wrote {len(macros)} macros, {len(lines)} example rows", file=sys.stderr)
