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
    elif fmt == "pct2":
        s = f"{100 * value:.2f}"
    elif fmt == "pp2":
        s = f"{100 * value:.2f}".replace("-", "$-$")
    elif fmt == "p4":
        s = f"{value:.4f}".lstrip("0")
    elif fmt == "f1":
        s = f"{value:.1f}"
    elif fmt == "f1x":
        s = f"{100 * value:.1f}"
    elif fmt == "f3":
        s = f"{value:.3f}"
    elif fmt == "p3":
        s = f"{value:.3f}".lstrip("0")
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
put("n_rows_main", len(d[d.prompt_id != "P1"]), src_main + " (P1 excluded: cached sensitivity arm)", "int")
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


# ------------------------------------------- oracle identity relation (fixed oracle) ---
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
    put("id_fail_fixed", int((~vf.critical_match.astype(bool)).sum()), src_main + " (fixed oracle)", "int")
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

# ============================================== refreshed artifacts ===
# Everything below reads the refreshed artifacts (shared label resolution,
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
             + (" (cached P1 sensitivity, not a primary arm)" if pr == "P1" else ""))
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
    put_wilson("or_new_ctrl_fa_raw", int((~co.match_raw.astype(bool)).sum()), len(co), srcC_ + " raw rule")
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

# ---- exploratory H1 (main1 hypothesis screen; replication is W-C's job)
HC = ROOT / "analysis/derived/main1_hyp_checks.json"
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

# ================================================================ round 2 ===
# Manuscript-formatted macros for the round-2 analyses.
# Every value is read from a frozen analysis file; nothing is typed. Keys are prefixed c2:
#   wc*  W-C arbitrated analysis (analysis/r2c/*; 10,000 cluster resamples, seed 20261031)
#   wd*  W-D (analysis/r2d/headline.json) and its C32 decomposition (analysis/applicability)
#   wb*  W-B original tables + contract audit (analysis/wb/*)
#   ap*  applicability exploratory checks (analysis/applicability/results.json)
R2C = ROOT / "analysis/r2c"
if (R2C / "primary.json").exists():
    srcP = "analysis/r2c/primary.json (arbitrated)"
    prim = json.load(open(R2C / "primary.json"))["primaries"]
    hd = json.load(open(R2C / "headline.json"))
    for k_ in ["P1", "P2", "P3"]:
        p_ = prim[k_]
        t = "wc" + k_.lower()
        put(t, p_["estimate"], srcP, "pp2")
        put(t + "_lo", p_["ci_low"], srcP, "pp2")
        put(t + "_hi", p_["ci_high"], srcP, "pp2")
        put(t + "_n", p_["n"], srcP, "int")
        put(t + "_ntot", p_["n_total"], srcP, "int")
        put(t + "_cl", p_["n_clusters"], srcP, "int")
        put(t + "_eff", p_["n_clusters_effective"], srcP, "f1")
        put(t + "_holm", p_["p_holm"], srcP, "p4")
        put(t + "_reject", int(bool(p_["reject_holm_005"])), srcP, "int")
    put("wcp1_sum", prim["P1"]["sum"], srcP, "int")
    put("wc_n_reject", sum(bool(prim[k_]["reject_holm_005"]) for k_ in prim), srcP, "int")
    # P3 directional share and all-output view (fig_numbers / headline)
    put("wcaff", hd["bare_affirmative_share"], "analysis/r2c/headline.json", "pct2")
    put("wcaff_lo", hd["bare_affirmative_share_ci_low"], "analysis/r2c/headline.json", "pct2")
    put("wcaff_hi", hd["bare_affirmative_share_ci_high"], "analysis/r2c/headline.json", "pct2")
    put("wcaff_k", round(hd["bare_affirmative_share"] * hd["bare_affirmative_share_n"]), "analysis/r2c/headline.json", "int")
    put("wcaff_n", hd["bare_affirmative_share_n"], "analysis/r2c/headline.json", "int")
    put("wcaff_ntot", hd["bare_affirmative_share_n_total"], "analysis/r2c/headline.json", "int")
    # politeness addition/removal
    for side in ["addition", "removal"]:
        a_ = prim["P2"][side]
        t = "wcpz" + side[:3]
        put(t, a_["estimate"], srcP, "pct2"); put(t + "_lo", a_["ci_low"], srcP, "pct2"); put(t + "_hi", a_["ci_high"], srcP, "pct2")
        put(t + "_k", a_["sum"], srcP, "int"); put(t + "_n", a_["n"], srcP, "int")
    pm = pd.read_csv(R2C / "politeness_direction_by_model.csv")
    for m in MODELS:
        for cv, t in [("plain", "add"), ("polite", "rem")]:
            r_ = pm[(pm.model == m) & (pm.cv == cv)].iloc[0]
            put(f"wcpz{t}_{SHORT[m]}_k", r_["sum"], "analysis/r2c/politeness_direction_by_model.csv", "int")
            put(f"wcpz{t}_{SHORT[m]}_n", r_["n"], "analysis/r2c/politeness_direction_by_model.csv", "int")
    # inventory and qualifications
    put("wc_n_fam", hd["n_families"], "analysis/r2c/headline.json", "int")
    put("wc_n_fam_incl", hd["n_families_inclusive"], "analysis/r2c/headline.json", "int")
    put("wc_n_models", hd["n_models"], "analysis/r2c/headline.json", "int")
    # analyzed families per dimension: scored inventory minus the frozen primary exclusions
    _md = json.load(open(R2C / "metadata.json"))
    _fams = pd.read_parquet(ROOT / _md["table"], columns=["family_id"])["family_id"].drop_duplicates()
    _fams = _fams[~_fams.isin(_md["exclusions"])]
    _srcF = "runs/r2c1/scored.parquet unique family_id minus analysis/r2c/metadata.json exclusions"
    for _pre, _key in [("r2pol", "wc_nfam_pol"), ("r2act", "wc_nfam_act"), ("r2plt", "wc_nfam_pz")]:
        put(_key, int(_fams.str.startswith(_pre).sum()), _srcF, "int")
    assert sum(int(_fams.str.startswith(p).sum()) for p in ["r2pol", "r2act", "r2plt"]) == hd["n_families"]
    put("wc_prefreeze", hd["pre_freeze_cache_requests"], "analysis/r2c/headline.json", "int")
    put("wc_arb_rows", hd["arbiter_resolved_rows"], "analysis/r2c/headline.json", "int")
    put("wc_unadj_rows", hd["unadjudicated_fallback_rows"], "analysis/r2c/headline.json", "int")
    inv = json.load(open(R2C / "arbiter_inventory.json"))
    put("wc_arb_units", len(inv["a_units"]), "analysis/r2c/arbiter_inventory.json", "int")
    pc = pd.read_csv(R2C / "primary_pre_freeze_cache.csv")
    put("wc_prefreeze_primary", pc.request_key.nunique() if "request_key" in pc else len(pc),
        "analysis/r2c/primary_pre_freeze_cache.csv", "int")
    # pre-arbitration (unknown-masked) P1, printed beside the arbitrated value
    sens = pd.read_csv(R2C / "primary_sensitivity.csv")
    def sens_row(name, c):
        return sens[(sens.sensitivity == name) & (sens.contrast == c)].iloc[0]
    for name, t in [("unknown_masked_pre_arbitration", "wcp1_um"), ("exclude_any_pre_freeze_cache_family", "wcp1_xc")]:
        s_ = sens_row(name, "P1")
        put(t, s_["estimate"], "analysis/r2c/primary_sensitivity.csv " + name, "pp2")
        put(t + "_lo", s_["ci_low"], "analysis/r2c/primary_sensitivity.csv " + name, "pp2")
        put(t + "_hi", s_["ci_high"], "analysis/r2c/primary_sensitivity.csv " + name, "pp2")
        put(t + "_n", s_["n"], "analysis/r2c/primary_sensitivity.csv " + name, "int")
    # channel ladder (critical match and joint supplied-predicate pass)
    lad = pd.read_csv(R2C / "channel_ladder.csv")
    for dim in ["polarity", "speech_act", "politeness"]:
        for ch in ["bare", "noncrit", "chip1", "chipall", "full"]:
            for met, t in [("critical_match", "m"), ("constraint_preserving", "j")]:
                r_ = lad[(lad.dimension == dim) & (lad.channel == ch) & (lad.metric == met)]
                if len(r_) and pd.notna(r_.iloc[0].estimate):
                    r_ = r_.iloc[0]
                    key = f"wc{t}_{DSHORT[dim]}_{ch}"
                    put(key, r_.estimate, "analysis/r2c/channel_ladder.csv", "pct2")
                    put(key + "_lo", r_.ci_low, "analysis/r2c/channel_ladder.csv", "pct2")
                    put(key + "_hi", r_.ci_high, "analysis/r2c/channel_ladder.csv", "pct2")
                    put(key + "_n", r_.n, "analysis/r2c/channel_ladder.csv", "int")
    cd_ = pd.read_csv(R2C / "channel_differences.csv")
    r_ = cd_[(cd_.dimension == "speech_act") & (cd_.metric == "chip1-full")].iloc[0]
    put("wc_act_chip1_full", r_.estimate, "analysis/r2c/channel_differences.csv", "pp2")
    put("wc_act_chip1_full_lo", r_.ci_low, "analysis/r2c/channel_differences.csv", "pp2")
    put("wc_act_chip1_full_hi", r_.ci_high, "analysis/r2c/channel_differences.csv", "pp2")
    put("wc_act_chip1_full_n", r_.n, "analysis/r2c/channel_differences.csv", "int")
    put("wc_act_chip1_full_cl", r_.n_clusters, "analysis/r2c/channel_differences.csv", "int")
    # question chip1 failures (S5 stratum) and negated chip1 matches (S2 stratum)
    cv_ = pd.read_csv(R2C / "cue_value_match.csv")
    q_ = cv_[(cv_.dimension == "speech_act") & (cv_.cv == "question")].iloc[0]
    put("wc_qfail_k", q_.n - q_["sum"], "analysis/r2c/cue_value_match.csv (question chip1)", "int")
    put("wc_qfail_n", q_.n, "analysis/r2c/cue_value_match.csv (question chip1)", "int")
    put("wc_qfail", 1 - q_.estimate, "analysis/r2c/cue_value_match.csv (question chip1)", "pct2")
    put("wc_qfail_lo", 1 - q_.ci_high, "analysis/r2c/cue_value_match.csv (question chip1)", "pct2")
    put("wc_qfail_hi", 1 - q_.ci_low, "analysis/r2c/cue_value_match.csv (question chip1)", "pct2")
    put("wc_qfail_cl", q_.n_clusters, "analysis/r2c/cue_value_match.csv (question chip1)", "int")
    tr = pd.read_csv(R2C / "speech_act_transitions.csv")
    put("wc_q2req_k", int(tr[(tr.cv == "question") & (tr.crit == "request/command")].n.sum()),
        "analysis/r2c/speech_act_transitions.csv (chip1)", "int")
    n_ = cv_[(cv_.dimension == "polarity") & (cv_.cv == "negated")].iloc[0]
    put("wc_negchip_k", n_["sum"], "analysis/r2c/cue_value_match.csv", "int")
    put("wc_negchip_n", n_.n, "analysis/r2c/cue_value_match.csv", "int")
    put("wc_negchip", n_.estimate, "analysis/r2c/cue_value_match.csv", "pct2")
    put("wc_negchip_lo", n_.ci_low, "analysis/r2c/cue_value_match.csv", "pct2")
    put("wc_negchip_hi", n_.ci_high, "analysis/r2c/cue_value_match.csv", "pct2")
    # coverage@3 polarity (bare)
    for pr in ["p2", "s3"]:
        b_ = f"coverage_polarity_{pr}"
        put(f"wccov_{pr}_k", round(hd[b_] * hd[b_ + "_n"]), "analysis/r2c/headline.json", "int")
        put(f"wccov_{pr}_n", hd[b_ + "_n"], "analysis/r2c/headline.json", "int")
    # C17 secondary replication (Llama request retention)

R2D = ROOT / "analysis/r2d/headline.json"
if R2D.exists():
    wd = json.load(open(R2D))
    srcD = "analysis/r2d/headline.json"
    put("wd_n_scen", wd["n_clusters"], srcD, "int")
    put("wd_n_requests", wd["n_requests"], srcD, "int")
    b_ = "statement_polarity_llama_"
    put("wdll_k", wd[b_ + "damage_k"], srcD, "int"); put("wdll_n", wd[b_ + "damage_n"], srcD, "int")
    put("wdll_scen", wd[b_ + "damage_n_event_clusters"], srcD, "int")
    put("wdll_rep_k", wd[b_ + "repeat_disagreement_k"], srcD, "int"); put("wdll_rep_n", wd[b_ + "repeat_disagreement_n"], srcD, "int")
    put("wdll_brep_k", wd[b_ + "both_repeat_disagreement_k"], srcD, "int"); put("wdll_brep_n", wd[b_ + "both_repeat_disagreement_n"], srcD, "int")
    for t, key in [("wdll_d", "damage_minus_repeat"), ("wdll_db", "damage_minus_both_repeat")]:
        put(t, wd[b_ + key], srcD, "pp2"); put(t + "_lo", wd[b_ + key + "_ci_low"], srcD, "pp2"); put(t + "_hi", wd[b_ + key + "_ci_high"], srcD, "pp2")
    b_ = "tell_agent_qwen_"
    put("wdqa_k", wd[b_ + "damage_k"], srcD, "int"); put("wdqa_n", wd[b_ + "damage_n"], srcD, "int")
    put("wdqa_scen", wd[b_ + "damage_n_event_clusters"], srcD, "int")
    sb_ = "statement_agent_qwen_damage_k"
    put("wdqa_stmt_k", wd[sb_], srcD, "int")
    # other models' STATEMENT polarity damage (expected zero; printed from file)
    put("wd_stmt_pol_other_k", sum(wd[f"statement_polarity_{m}_damage_k"] for m in ["qwen", "gemma", "terra"]
                                   if f"statement_polarity_{m}_damage_k" in wd), srcD, "int")
    sc2 = pd.read_parquet(ROOT / "runs/r2d1/scored.parquet", columns=["critical_source"])
    put("wd_j1_rows", int((sc2.critical_source == "J1").sum()), "runs/r2d1/scored.parquet J1-fallback critical rows", "int")
    put("wd_rows", len(sc2), "runs/r2d1/scored.parquet", "int")
AP = ROOT / "analysis/applicability/results.json"
if AP.exists():
    ap = json.load(open(AP))
    srcA = "analysis/applicability/results.json (exploratory, seed 20261101)"
    h2 = ap["preserved"]["H2"]
    put("wd_notyou_k", h2["NOT|YOU"]["k"], srcA, "int"); put("wd_notyou_n", h2["NOT|YOU"]["n"], srcA, "int")
    put("wd_other_k", h2["other"]["k"], srcA, "int"); put("wd_other_n", h2["other"]["n"], srcA, "int")
    put("wd_negabs_k", h2["among_damage"]["negation_absent"]["k"], srcA, "int")
    xp = ap["preserved"]["H1/exact_partner"]
    put("ap_xp_p2_k", xp["P2"]["k"], srcA, "int"); put("ap_xp_p2_n", xp["P2"]["n"], srcA, "int")
    put("ap_xp_s3_k", xp["S3"]["k"], srcA, "int"); put("ap_xp_s3_n", xp["S3"]["n"], srcA, "int")
    put("ap_xp_d", xp["P2_minus_S3"]["estimate"], srcA, "pp2")
    put("ap_xp_d_lo", xp["P2_minus_S3"]["lo"], srcA, "pp2"); put("ap_xp_d_hi", xp["P2_minus_S3"]["hi"], srcA, "pp2")
    put("ap_xp_cl", xp["P2_minus_S3"]["clusters"], srcA, "int")

WBE = ROOT / "analysis/wb/estimates.csv"
WBA = ROOT / "analysis/wb/contract_audit.json"
if WBE.exists() and WBA.exists():
    we = pd.read_csv(WBE)
    srcWB = "analysis/wb/estimates.csv (original tables, 2,000 message resamples)"
    def wrow(an, sample, metric, dim="ALL"):
        return we[(we.analysis == an) & (we["sample"] == sample) & (we.metric == metric) & (we.dim == dim) & (we.model == "pooled")].iloc[0]
    for smp, t in [("random", "r"), ("enriched", "e")]:
        r_ = wrow("A_default", smp, "takes_default")
        put(f"wb{t}_def", r_.est, srcWB); put(f"wb{t}_def_lo", r_.lo, srcWB); put(f"wb{t}_def_hi", r_.hi, srcWB)
        r_ = wrow("A_default", smp, "honour_nondefault")
        put(f"wb{t}_hnd", r_.est, srcWB); put(f"wb{t}_hnd_lo", r_.lo, srcWB); put(f"wb{t}_hnd_hi", r_.hi, srcWB)
        r_ = wrow("B_violation", smp, "full")
        put(f"wb{t}_vfull", r_.est, srcWB); put(f"wb{t}_vfull_lo", r_.lo, srcWB); put(f"wb{t}_vfull_hi", r_.hi, srcWB)
        put(f"wb{t}_vfull_k", r_.k, srcWB, "int"); put(f"wb{t}_vfull_n", r_.n, srcWB, "int")
        r_ = wrow("C_restoration_agree", smp, "restored-pos_cap4", dim="all focal")
        put(f"wb{t}_gain", r_.est, srcWB, "pp"); put(f"wb{t}_gain_lo", r_.lo, srcWB, "pp"); put(f"wb{t}_gain_hi", r_.hi, srcWB, "pp")
    ca = json.load(open(WBA))
    srcCA = "analysis/wb/contract_audit.json (10,000 message resamples, seed 20261101)"
    st = ca["inventory"]["statuses"]
    put("wb_msgs_restored", ca["inventory"]["messages"], srcCA, "int")
    put("wb_outputs_restored", ca["inventory"]["outputs"], srcCA, "int")
    put("wb_conflicts", st["definite_conflict"], srcCA, "int")
    put("wb_aligned", st["aligned"], srcCA, "int")
    put("wb_unknown", st["unknown_reference"] + st["unknown_source_consensus"] + st["unknown_word"], srcCA, "int")
    put("wb_maybe_k", ca["example"]["k"], srcCA, "int"); put("wb_maybe_n", ca["example"]["n"], srcCA, "int")
    put("wb_maybe_msgs", ca["example"]["message_clusters"], srcCA, "int")
    est_ = pd.DataFrame(ca["estimates"])
    for smp, t in [("random", "r"), ("enriched", "e")]:
        r_ = est_[(est_["sample"] == smp) & (est_.subset == "all_restored") & (est_.dim == "ALL") & (est_.model == "pooled")
                  & (est_.metric == "actual_input_general_match")].iloc[0]
        put(f"wb{t}_actual_k", r_.k, srcCA, "int"); put(f"wb{t}_actual_n", r_.n, srcCA, "int")
        put(f"wb{t}_actual", r_.estimate, srcCA)
        lo_, hi_ = (r_.ci95 if "ci95" in r_ and isinstance(r_.ci95, list) else (r_.get("ci_low"), r_.get("ci_high")))
        put(f"wb{t}_actual_lo", lo_, srcCA); put(f"wb{t}_actual_hi", hi_, srcCA)
    for row in ca["polarity_denominators"]:
        t = ("wbr" if row["sample"] == "random" else "wbe") + ("_nondef" if row["stratum"] == "non_default" else "_neg")
        put(t + "_k", row["k"], srcCA, "int"); put(t + "_n", row["n"], srcCA, "int")
    put("wb_human_fields", ca["human"]["wb_human_fields_filled"], srcCA, "int")
    put("wb_human_items", ca["human"]["wb_audit_items"], srcCA, "int")
for sub in ["returns_wc", "returns_wb", "returns_repair"]:
    put(f"n_{sub}", len([p for p in glob.glob(str(ROOT / f"annotation/{sub}/*")) if not p.endswith(".gitkeep")]),
        f"annotation/{sub}/ (completed return files)", "int")

# --------------------------------------------------------- examples table ---
# Examples are NOT reselected here. They are the stored occurrences frozen in
# paper/figs/example_manifest.json (story rules E1-E10, analysis/examples/main1_story_evidence.json). This
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

# ------------------------------------------------- example gallery (Fig. 1) ---
# Cards S1, S2, S5, S7, S9 from analysis/examples/story_evidence.v2.json (declared selection rules per card)
# plus the E10 oracle inset from paper/figs/example_manifest.json. Every (output_id, visible
# input, text) triple is re-read from runs/<run>/outputs.jsonl; any mismatch aborts.
SE = ROOT / "analysis/examples/story_evidence.v2.json"
_occ_cache: dict[str, set] = {}


def stored_triple(run, oid, inp, txt):
    if run not in _occ_cache:
        _occ_cache[run] = set()
        for line in open(ROOT / f"runs/{run}/outputs.jsonl"):
            r = json.loads(line)
            _occ_cache[run].add((r["output_id"], r.get("input_text"), r["text"]))
    return (oid, inp, txt) in _occ_cache[run]


if SE.exists():
    cards = {c["id"]: c for c in json.load(open(SE))["cards"]}
    n_gal = 0
    for cid in ["S1", "S2", "S5", "S7", "S9"]:
        for o in cards[cid]["outputs"]:
            if not stored_triple(o["run"], o["output_id"], o["input_text"], o["text"]):
                raise SystemExit(f"gallery {cid} {o['output_id']}: story_evidence != stored output")
            n_gal += 1
    e10 = E["E10"][0]
    if not stored_triple(e10["run"], e10["occurrence"]["output_id"], e10["occurrence"]["input_text"], e10["occurrence"]["text"]):
        raise SystemExit("gallery E10 mismatch")
    n_gal += 1
    put("gal_n_verified", n_gal, "story_evidence.json + example_manifest.json strings re-read from runs/*/outputs.jsonl", "int")
    ay = cards["S7"]["rates"]["ask_you_prefix_among_fixed"]
    put("gal_askyou_k", ay["k"], "analysis/examples/story_evidence.v2.json S7/S9 (post hoc lexical diagnostic)", "int")
    put("gal_askyou_n", ay["n"], "analysis/examples/story_evidence.v2.json S7/S9 (post hoc lexical diagnostic)", "int")

    def exact(inp):  # the stored input string verbatim, wrapper prefix included (no rendering)
        return r"\kw{" + tex(inp) + "}"

    def outq(t):
        return r"\say{" + tex(t) + "}"

    MS = {"qwen2.5-7b": "Qwen2.5-7B", "llama3.1-8b": "Llama-3.1-8B", "gemma3-4b": "Gemma-3-4B",
          "gpt-6.1-terra": "gpt-6.1-terra"}
    ARROW = r"\,$\Rightarrow$\,"
    HID = r"\newline {\scriptsize\emph{hidden source, not shown to the model:} \say{%s}}"

    def lab(name, model, pop):
        return rf"\textbf{{{name}}}\newline {{\scriptsize {MS[model]}, {pop}}}"

    # Fig. 1: teaching sequence (S2) first, then two compact failure cards (S1, S5).
    g = []
    s2 = cards["S2"]["outputs"]
    chname = {"bare": "bare", "noncrit": "+word", "chip1": "+chip", "full": "full"}
    seq = r"\newline ".join(rf"\makebox[2.9em][l]{{\scriptsize {chname[x['channel']]}}}" + exact(x["input_text"]) + ARROW + outq(x["text"]) for x in s2)
    g.append((lab("1\\ \\ Missing vs.\\ supplied", s2[0]["model"], "W-C"),
              seq + HID % tex(cards["S2"]["source"]),
              r"Without a negation cue (bare, +word) the input does not say whether the person feels well; the affirmative is an \emph{Assumption} the input forced, not a model error. Once \texttt{[NOT]} or the full sentence is supplied, the negation is kept. \emph{Owner:} the input channel.",
              r"bare outputs affirmative: \RES{wcaff_k}/\RES{wcaff_n} directional (\RES{wcaff_k}/\RES{wcaff_ntot} all outputs); \texttt{[NOT]} targets negated: \RES{wc_negchip_k}/\RES{wc_negchip_n}. Separate endpoints, not a paired repair rate."))
    o = cards["S1"]["outputs"][0]
    g.append((lab("2\\ \\ Typed text changed", o["model"], "W-C"),
              exact(o["input_text"]) + ARROW + outq(o["text"]),
              r"A constructed full-input test: the whole sentence was supplied, and the model added \say{Please} (an R2 \emph{Violation}). \emph{Owner:} the generation step; copying the sentence avoids it.",
              r"plain sources gained a marker in \RES{wcpzadd_k}/\RES{wcpzadd_n} outputs (this model \RES{wcpzadd_gemma_k}/\RES{wcpzadd_gemma_n}); polite sources lost it in \RES{wcpzrem_k}/\RES{wcpzrem_n}"))
    o = cards["S5"]["outputs"][0]
    g.append((lab("3\\ \\ Question cue lost", o["model"], "W-C"),
              exact(o["input_text"]) + ARROW + outq(o["text"]) + HID % tex(cards["S5"]["source"]),
              r"Phrased as a question, but it asks someone to sign; the source asks whether a signature is required. Our codebook codes it a \emph{request}, so the supplied \texttt{[?]} cue was not kept (R1). \emph{Owner:} the model, given that cue.",
              r"\texttt{[?]} targets not kept as questions: \RES{wc_qfail_k}/\RES{wc_qfail_n}; of these, coded as requests: \RES{wc_q2req_k}/\RES{wc_qfail_n}"))
    glines = [f"{a_} & {b_} & {c_} & {d_}\\\\" for a_, b_, c_, d_ in g]
    (OUT / "gallery_table.tex").write_text(
        "% generated by make_macros.py from analysis/examples/story_evidence.v2.json (S2, S1, S5) -- do not edit\n"
        + "\n\\midrule\n".join(glines) + "\n")

    # Oracle inset (E10) for sec:oracle.
    o = e10["occurrence"]
    (OUT / "checker_table.tex").write_text(
        "% generated by make_macros.py from paper/figs/example_manifest.json (E10) -- do not edit\n"
        + rf"input & {exact(o['input_text'])}\\" + "\n"
        + rf"output & {outq(o['text'])}\\" + "\n"
        + rf"model & {MS[o['model']]}, discovery set, prompt P0, full channel\\" + "\n")

    # Guard inset (S7 repair, S9 fragment) for sec:decisions.
    s7, s9 = cards["S7"]["outputs"], cards["S9"]["outputs"]
    rows = []
    for name, ss in [("repair", s7), ("fragment", s9)]:
        rows.append(rf"{name}\newline {{\scriptsize {MS[ss[0]['model']]}}} & {exact(ss[0]['input_text'])}\newline "
                    rf"P0: {outq(ss[0]['text'])}\newline G1: {outq(ss[1]['text'])}\\")
    (OUT / "guard_table.tex").write_text(
        "% generated by make_macros.py from analysis/examples/story_evidence.v2.json (S7, S9) -- do not edit\n"
        + "\n\\midrule\n".join(rows) + "\n")

# W-C headline import check (consumed by analysis/r2c/verify_artifacts.py)
_hj = json.load(open(ROOT / "analysis/r2c/headline.json"))
_imp = {k_: v_ for k_, v_ in _hj.items() if isinstance(v_, (int, float))}
_ok = all(macros.get("wc_" + k_) == (f"{int(round(v_)):,}" if isinstance(v_, int) else f"{v_:.3f}") for k_, v_ in _imp.items())
_mv = ROOT / "analysis/r2c/macro_verification.json"
_mvj = json.load(open(_mv)) if _mv.exists() else {}
_mvj["se4all"] = {"headline_keys_imported": len(_imp), "values_match": bool(_ok)}
_mv.write_text(json.dumps(_mvj, indent=2) + "\n")

# ---- R5 input-builder validator replay. Census, no CI.
_R5 = "analysis/r5_validator/replay.json"
_r5 = json.load(open(ROOT / _R5))
assert _r5["known_conflicts_rejected"] == _r5["known_conflicts"] == _r5["verdicts"]["conflicting"], "R5 conflicts"
put("r5_n", _r5["n"], _R5, "int")
put("r5_agree", _r5["agrees_with_audit"], _R5, "int")
put("r5_rej", _r5["known_conflicts_rejected"], _R5, "int")
put("r5_conf", _r5["known_conflicts"], _R5, "int")
put("r5_sure", _r5["sure_granularity_flagged"], _R5, "int")
put("r5_sure_cert", _r5["coarse_certified"], _R5, "int")
put("r5_unknown", _r5["verdicts"]["unknown"], _R5, "int")

# ---- frozen guard transfer to W-C speech act (accepted with qualifications). Macro view only;
# the intervention analysis belongs to CALE-AI. Source: analysis/guard_wc/headline.json, gated on ACCEPTANCE.
_GT = "analysis/guard_wc/headline.json"
_gt = json.load(open(ROOT / _GT))
_ac = json.load(open(ROOT / "analysis/guard_wc/acceptance_check.json"))
assert _gt["status"] == "complete" and _gt["transfer_success"] and all(_gt["criteria"].values())
assert _ac["verdict"] == "ACCEPT WITH QUALIFICATIONS", _ac["verdict"]
_gp = _gt["paired"]["G1"]
put("gtw_fam", _gt["n_families"], _GT, "int")
put("gtw_targets", _gt["n_targets"], _GT, "int")
put("gtw_jgain", _gp["joint_gain"]["estimate"], _GT, "pct2")
put("gtw_jgain_lo", _gp["joint_gain"]["ci_low"], _GT, "pct2")
put("gtw_jgain_hi", _gp["joint_gain"]["ci_high"], _GT, "pct2")
put("gtw_cc", _gp["strict_changed_correct"]["estimate"], _GT, "pct2")
put("gtw_cc_k", _gp["strict_changed_correct"]["k"], _GT, "int")
put("gtw_cc_n", _gp["strict_changed_correct"]["n"], _GT, "int")
put("gtw_pf_k", _gp["strict_pass_to_fail"]["k"], _GT, "int")
put("gtw_pf_n", _gp["strict_pass_to_fail"]["n"], _GT, "int")

# ================================================================ cycle 1 ===
# hw1 (human-written replication, primary), judge validation Parts 12/13, elicitation anchor,
# and the hw1 example figure. Everything is read from analysis/hw1/*, annotation/judge_validation_*.json,
# analysis/elicitation/summary.json; nothing is typed.
import re as _re
_H = "analysis/hw1/summary.json"
_hs = json.load(open(ROOT / _H))
put("hw_ncand", _hs["n_candidates"], _H, "int")
put("hw_nkept", _hs["n_kept"], _H, "int")
put("hw_nfam", _hs["n_analysed_families"], _H, "int")
_wr = {r_["writer_id"] for r_ in map(json.loads, open(ROOT / "data/items/hw.jsonl"))}
put("hw_nwriters", len(_wr), "data/items/hw.jsonl (distinct writer_id among kept families)", "int")
put("hw_wr_min", min(_hs["writers_by_dim"].values()), _H, "int")
put("hw_wr_max", max(_hs["writers_by_dim"].values()), _H, "int")
for _k, _n in (("P1", "hwp1"), ("P2", "hwp2")):
    _e = _hs["primary"][_k]["writer"]
    put(_n, _e["estimate"], _H, "pct")
    put(_n + "_lo", _e["ci_low"], _H, "pct")
    put(_n + "_hi", _e["ci_high"], _H, "pct")
    put(_n + "_n", _e["n"], _H, "int")
    put(_n + "_wr", _e["n_clusters"], _H, "int")
    put(_n + "_holm", _e["p_holm"], _H, "p4")
_e = _hs["P3_affirmative_share"]
put("hwaff", _e["estimate"], _H, "pct")
put("hwaff_lo", _e["ci_low"], _H, "pct")
put("hwaff_hi", _e["ci_high"], _H, "pct")
put("hwaff_n", _e["n"], _H, "int")
put("hwp3_wr", _e["n_clusters"], _H, "int")
put("hwp3_holm", _hs["primary"]["P3"]["writer"]["p_holm"], _H, "p4")
for _k, _n in (("addition_plain_to_polite", "hwpzadd"), ("removal_polite_to_plain", "hwpzrem")):
    _e = _hs["P2_arms"][_k]
    put(_n, _e["estimate"], _H, "pct")
    put(_n + "_k", _e["sum"], _H, "int")
    put(_n + "_n", _e["n"], _H, "int")
_pm = pd.read_csv(ROOT / "analysis/hw1/primary_by_model.csv")
for _m_, _s_ in (("gemma3-4b", "gemma"), ("gpt-6.1-terra", "terra"), ("llama3.1-8b", "llama"), ("qwen2.5-7b", "qwen")):
    put("hwpz_" + _s_, _pm[(_pm.contrast == "P2") & (_pm.model == _m_)].estimate.iloc[0], "analysis/hw1/primary_by_model.csv", "pct")
_cg = pd.read_csv(ROOT / "analysis/hw1/chip_gain.csv")
_cg = _cg[_cg.model == "ALL"]
put("hw_gain_min", _cg.estimate.min(), "analysis/hw1/chip_gain.csv", "pct")
put("hw_gain_max", _cg.estimate.max(), "analysis/hw1/chip_gain.csv", "pct")
put("hw_gain_lo_min", _cg.ci_low.min(), "analysis/hw1/chip_gain.csv", "pct")
_ms = _hs["max_shift_pp"]
put("hw_shift_max", max(v for k, v in _ms.items() if not k.startswith("d_")) / 100, _H + " max_shift_pp (a,b,c scenarios)", "f1x")
put("hw_shift_all", _ms["d_all_574_candidates"] / 100, _H + " max_shift_pp (all 574 candidates)", "f1x")
put("hw_sens_flags", len(_hs["sensitivity_flags"]), _H + " sensitivity_flags", "int")

# judge validation on new human data (Parts 12 elicitation outputs, 13 human-written-pair outputs)
for _tag, _f in (("jve", "elic"), ("jvh", "hw")):
    _JV = f"annotation/judge_validation_{_f}.json"
    _j = json.load(open(ROOT / _JV))["human"]
    _c = _j["judge"]["critical"]["sampled/final"]
    put(_tag + "_kappa", _c["kappa"], _JV, "f2")
    put(_tag + "_kappa_lo", _c["kappa_ci"][0], _JV, "f2")
    put(_tag + "_kappa_hi", _c["kappa_ci"][1], _JV, "f2")
    put(_tag + "_n", _c["n"], _JV, "int")
    put(_tag + "_items", _j["n_items"], _JV, "int")
    put(_tag + "_coders", len(_j["members"]), _JV, "int")
    put(_tag + "_alpha", _j["alpha_nominal"]["critical"]["alpha"], _JV, "f2")
    _vk = []
    for _vn in ("violation", "constraint_preserving", "assumption"):
        _vv = _j["verdict"].get(_vn, {}).get("primary") or _j["verdict"].get(_vn, {}).get("all")
        if _vv:
            _vk.append(_vv)
    put(_tag + "_vk_min", min(v["kappa"] for v in _vk if v.get("kappa") is not None), _JV, "f2")
    put(_tag + "_vk_max", max(v["kappa"] for v in _vk if v.get("kappa") is not None), _JV, "f2")
    _va = _j["verdict"]["assumption"].get("primary") or _j["verdict"]["assumption"]["all"]
    put(_tag + "_va_k", _va["agree_k"], _JV, "int")
    put(_tag + "_va_n", _va["n"], _JV, "int")
    _vv = _j["verdict"]["violation"].get("primary")
    if _vv:
        put(_tag + "_vv_k", _vv["agree_k"], _JV, "int")
        put(_tag + "_vv_n", _vv["n"], _JV, "int")

# elicitation anchor (one sentence in this paper): negation loss, humans vs the POS-cap4 compressor
_EL = "analysis/elicitation/summary.json"
_el = json.load(open(ROOT / _EL))
_pl = _el["by_dimension"]["polarity"]["lenient"]
put("el_neg_h", _pl["human_pooled"]["p"], _EL, "pct")
put("el_neg_h_k", _pl["human_pooled"]["k"], _EL, "int")
put("el_neg_h_n", _pl["human_pooled"]["n"], _EL, "int")
put("el_neg_c", _pl["pos_cap4"]["p"], _EL, "pct")
put("el_neg_c_k", _pl["pos_cap4"]["k"], _EL, "int")
put("el_neg_c_n", _pl["pos_cap4"]["n"], _EL, "int")
put("el_nmsg", _el["n_messages_rated"], _EL, "int")
put("el_nsets", _el["n_ratings_valid"], _EL, "int")
put("el_nann", len(_el["annotators"]), _EL, "int")
macros["hash_release"] = "protocol-hash-2026-11-01"
sources["hash_release"] = "GitHub release tag named in orchestration/LOOP_BRIEF (identifier, not a result)"

# Fig. 1 (hw1 examples): declared hash rule in analysis/hw1/examples.md; strings re-read from runs/hw1.
_hout = set()
for _l in open(ROOT / "runs/hw1/outputs.jsonl"):
    _r = json.loads(_l)
    _hout.add((_r["family_id"], _r["model"], _r["channel"], _r["input_text"], _r["text"]))
_md = (ROOT / "analysis/hw1/examples.md").read_text()
_blocks = _re.split(r"^## ", _md, flags=_re.M)[1:]
_MOD = {"gemma3-4b": "Gemma-3-4B", "llama3.1-8b": "Llama-3.1-8B", "qwen2.5-7b": "Qwen2.5-7B", "gpt-6.1-terra": "gpt-6.1-terra"}
_cards = []
for _b in _blocks:
    _dim = _b.split("\n", 1)[0].strip()
    if _dim not in ("polarity", "speech_act", "politeness"):
        continue
    _hd = _re.search(r"Family `(hw-[a-z]+-\d+)` \(writer (P\d+)\); first of (\d+) qualifying families by hash; model `([^`]+)`, variant (\w) \(target value: \*\*(.+?)\*\*\)\. Source sentence: \"(.+?)\"\n", _b, _re.S)
    assert _hd, _dim
    _fam, _wid, _nq, _mod, _var, _tv, _src = _hd.groups()
    _rows = {}
    for _m in _re.finditer(r"^\| (bare|noncrit|chip1|chipall|full) \| `(.+?)` \| (.+?) \| (.+?) \| (\w+) \|$", _b, _re.M):
        _ch, _inp, _out, _lab, _ls = _m.groups()
        assert (_fam, _mod, _ch, _inp, _out) in _hout, (_fam, _ch, _inp, _out)
        _rows[_ch] = (_inp, _out, _lab)
    _key = "hwe_" + DSHORT[_dim]
    _ex = _hs["examples"][_dim]
    assert _ex["family_id"] == _fam and _ex["model"] == _mod
    put(_key + "_nq", int(_nq), _H + " examples", "int")
    put(_key + "_wrong", _ex["bare_wrong_committed_rate"]["estimate"], _H + " examples", "pct")
    put(_key + "_wrong_lo", _ex["bare_wrong_committed_rate"]["ci_low"], _H + " examples", "pct")
    put(_key + "_wrong_hi", _ex["bare_wrong_committed_rate"]["ci_high"], _H + " examples", "pct")
    put(_key + "_fix", _ex["repair_rate_given_bare_wrong"]["estimate"], _H + " examples", "pct")
    put(_key + "_fix_lo", _ex["repair_rate_given_bare_wrong"]["ci_low"], _H + " examples", "pct")
    put(_key + "_fix_hi", _ex["repair_rate_given_bare_wrong"]["ci_high"], _H + " examples", "pct")
    put(_key + "_fix_n", _ex["repair_rate_given_bare_wrong"]["n"], _H + " examples", "int")
    put(_key + "_wr", _ex["bare_wrong_committed_rate"]["n_clusters"], _H + " examples", "int")
    _cards.append((_dim, _fam, _wid, _mod, _tv, _src, _rows, _key))
_DN = {"polarity": "polarity", "speech_act": "speech act", "politeness": "politeness"}
_CN = {"bare": "bare", "chip1": "+chip", "full": "full"}
_READ = {
    "polarity": r"A bare input does not say whether the sentence is negated, so the affirmative is an \emph{Assumption}, not a model error. With the supplied cue or the typed sentence, negation is kept. \emph{Owner of the fix (our taxonomy's choice):} the input channel.",
    "speech_act": r"A bare input leaves question vs.\ statement open; the statement is an \emph{Assumption}. With \texttt{[?]} this output is a question, but a supplied tag is not always kept. \emph{Owner:} the input channel for the bare miss, the model when a supplied tag is dropped.",
    "politeness": r"Bare keywords carry no politeness marker, so \say{Please} is an \emph{Assumption}; with the typed sentence the plain wording is kept. \emph{Owner:} the input channel.",
}
_hl = []
for _i, (_dim, _fam, _wid, _mod, _tv, _src, _rows, _key) in enumerate(_cards, 1):
    _seq = r"\newline ".join(
        rf"\makebox[2.9em][l]{{\scriptsize {_CN[c_]}}}\kw{{{tex(_rows[c_][0])}}}\,$\Rightarrow$\,\say{{{tex(_rows[c_][1])}}} {{\scriptsize({tex(_rows[c_][2])})}}"
        for c_ in ("bare", "chip1", "full"))
    _lab = rf"\textbf{{{_i}\ \ {_DN[_dim]}}}\newline {{\scriptsize {_MOD[_mod]}, writer {_wid}; target \emph{{{tex(_tv)}}}}}"
    _rate = (rf"bare commits to a wrong value: \RES{{{_key}_wrong}}\% \cip{{{_key}_wrong}} of bare rows (\RES{{{_key}_wr}} writers); "
             rf"then the \texttt{{[chip]}} output matches: \RES{{{_key}_fix}}\% \cip{{{_key}_fix}} (\RES{{{_key}_fix_n}}). First of \RES{{{_key}_nq}} qualifying families by hash.")
    _hl.append(f"{_lab} & {_seq}\\newline {{\\scriptsize\\emph{{hidden source:}} \\say{{{tex(_src)}}}}} & {_READ[_dim]} & {_rate}\\\\")
(OUT / "hw_gallery_table.tex").write_text(
    "% generated by make_macros.py from analysis/hw1/examples.md + summary.json (strings verified in runs/hw1/outputs.jsonl) -- do not edit\n"
    + "\n\\midrule\n".join(_hl) + "\n")

# ================================================================ cycle 2 ===
# Consistency fixes, composition study (R4), extension cost, replacement tables for the two old figures,
# and the one-card Fig. 1. Everything is read from analysis files; nothing typed.
# --- (1) item counts behind the human-agreement rows: excluded = items with no determinate human critical label
for _tag, _f in (("jve", "elic"), ("jvh", "hw")):
    _c2 = json.load(open(ROOT / f"annotation/judge_validation_{_f}.json"))["human"]["judge"]["critical"]["sampled/final"]
    put(_tag + "_acc", _c2["acc"], f"annotation/judge_validation_{_f}.json", "pct")
    put(_tag + "_excl", int(macros[_tag + "_items"].replace(",", "")) - int(macros[_tag + "_n"].replace(",", "")),
        "annotation/judge_validation_*.json: n_items minus critical n (all coders unsure, or tied plurality)", "int")
# --- hw1 added/removed/net must agree: net = added - removed (percentage points)
assert abs(float(macros["hwpzadd"]) - float(macros["hwpzrem"]) - float(macros["hwp2"])) < 0.15, "hw1 net != added - removed"
assert abs(float(macros["wcpzadd"]) - float(macros["wcpzrem"]) - float(macros["wcp2"])) < 0.02, "W-C net != added - removed"
# --- composition study (R4)
_D = json.load(open(ROOT / "analysis/r2d/headline.json"))
_DS = "analysis/r2d/headline.json"
for _t, _b in (("wdqa_d", "tell_agent_qwen_damage_minus_repeat"),):
    put(_t, _D[_b], _DS, "pp2"); put(_t + "_lo", _D[_b + "_ci_low"], _DS, "pp2"); put(_t + "_hi", _D[_b + "_ci_high"], _DS, "pp2")
put("wd_tellpol_llama_k", _D["tell_polarity_llama_damage_k"], _DS, "int")
put("wd_rep_n_single", _D["tell_polarity_qwen_repeat_disagreement_n"], _DS, "int")
put("wd_nscen", _D["n_clusters"], _DS, "int")
put("wd_nreq", _D["n_requests"], _DS, "int")
# --- extension cost (extend_cost.py dry run)
_EC = json.load(open(OUT / "extend_cost.json"))
for _k in ("new_entry_lines", "rescored_rows", "rescore_seconds", "model_calls", "loc_attribute", "loc_validator", "loc_labels", "n_chips"):
    put("ec_" + _k, _EC[_k], "paper/se4all/extend_cost.json (dry run, src/attribute.py + src/validate_cue_inputs.py)", "int" if _k != "rescore_seconds" else "f1")
assert _EC["validator_ok"] == "compatible" and _EC["validator_conflict"] == "conflicting"
# --- replacement for the two figures: channel table and per-model politeness table
_cl = pd.read_csv(ROOT / "analysis/r2c/channel_ladder.csv")
_cl = _cl[_cl.metric == "critical_match"]
_CH = [("bare", "bare"), ("noncrit", "+word"), ("chip1", "+chip"), ("chipall", "+all"), ("full", "full")]
_DL = [("polarity", "polarity"), ("speech_act", "speech act"), ("politeness", "politeness")]
_rows = []
for _d, _dn in _DL:
    _cells = []
    for _c, _ in _CH:
        _r = _cl[(_cl.dimension == _d) & (_cl.channel == _c)].iloc[0]
        _v = f"{100 * _r.estimate:.1f}"
        _cells.append(rf"\textit{{{_v}}}" if _c in ("bare", "noncrit") else _v)
    _n = int(_cl[(_cl.dimension == _d) & (_cl.channel == "bare")].iloc[0].n)
    _rows.append(f"{_dn} & " + " & ".join(_cells) + f" & {_n}\\\\")
(OUT / "wc_ladder_table.tex").write_text("% generated from analysis/r2c/channel_ladder.csv -- do not edit\n" + "\n".join(_rows) + "\n")
_pm2 = pd.read_csv(ROOT / "analysis/r2c/politeness_direction_by_model.csv")
_hm = pd.read_csv(ROOT / "analysis/hw1/primary_by_model.csv")
_pr = json.load(open(ROOT / "analysis/r2c/primary.json"))["primaries"]["P2"]
_rows = []
for _m, _ml in (("gemma3-4b", "Gemma-3-4B"), ("gpt-6.1-terra", "gpt-6.1-terra"), ("llama3.1-8b", "Llama-3.1-8B"), ("qwen2.5-7b", "Qwen2.5-7B")):
    _h = _hm[(_hm.contrast == "P2") & (_hm.model == _m)].iloc[0]
    _a = _pm2[(_pm2.model == _m) & (_pm2.cv == "plain")].iloc[0]
    _r = _pm2[(_pm2.model == _m) & (_pm2.cv == "polite")].iloc[0]
    _net = ('%+.1f' % (100 * _h.estimate)).replace('-', '$-$')
    _rows.append(f"{_ml} & {_net} & {int(_a['sum'])}/{int(_a.n)} & {int(_r['sum'])}/{int(_r.n)}\\\\")
_ad, _rm = _pr["addition"], _pr["removal"]
_rows.append("\\midrule\n" + f"Pooled & {macros['hwp2']} & {int(_ad['sum'])}/{int(_ad['n'])} & {int(_rm['sum'])}/{int(_rm['n'])}\\\\".replace(macros['hwp2'], "+" + macros["hwp2"]))
(OUT / "wc_pol_table.tex").write_text("% generated from analysis/hw1/primary_by_model.csv and analysis/r2c/politeness_direction_by_model.csv -- do not edit\n" + "\n".join(_rows) + "\n")
# --- Fig. 1: one hook card (polarity) at column width; cards 2-3 kept as a table
def _card_rows(_rows, _src):
    _l = [rf"\makebox[2.6em][l]{{\scriptsize {_CN[c_]}}}\kw{{{tex(_rows[c_][0])}}}\,$\Rightarrow$\,\say{{{tex(_rows[c_][1])}}} {{\scriptsize({tex(_rows[c_][2])})}}" for c_ in ("bare", "chip1", "full")]
    return _l
_dim, _fam, _wid, _mod, _tv, _src, _rws, _key = _cards[0]
assert _dim == "polarity"
(OUT / "hw_card1.tex").write_text(
    "% generated by make_macros.py from analysis/hw1/examples.md (strings verified in runs/hw1/outputs.jsonl) -- do not edit\n"
    + "\\par\n".join(_card_rows(_rws, _src)).replace("\\par\n", "\\\\[1pt]\n")
    + rf"\\[1pt]{{\scriptsize\emph{{hidden source:}} \say{{{tex(_src)}}}}}" + "\n")
# ------------------------------------------------------------------ cycle 3: robustness (C43-C48) ---
# Every value is read from analysis/robust/*/summary.json; nothing is typed.
_R = "analysis/robust/"
_t6 = json.load(open(ROOT / _R / "t6_small_cluster/summary.json"))
_T6 = _R + "t6_small_cluster/summary.json"
assert _t6["name"] == "hw1"
for _k, _n in (("P1", "t6p1"), ("P2", "t6p2"), ("P3", "t6p3")):
    _c = _t6["contrasts"][_k]
    assert _c["sign_flip_randomization"]["all_writer_signs_positive"] is True
    put(_n + "_wr", _c["writers"], _T6, "int")
    put(_n + "_df", _c["writers"] - 1, _T6, "int")
    put(_n + "_tlo", _c["t_ci_low"], _T6, "pct")
    put(_n + "_thi", _c["t_ci_high"], _T6, "pct")
    put(_n + "_p1s", _c["sign_flip_randomization"]["p_one_sided"], _T6, "p4")
    put(_n + "_holm", _t6["holm_signflip_one_sided"][_k], _T6, "p3")
    put(_n + "_het_p", _c["heterogeneity_model_permutation"]["p"], _T6, "p4")
put("t6p3_tlo_share", 0.5 + _t6["contrasts"]["P3"]["t_ci_low"], _T6, "pct")
put("t6p3_thi_share", 0.5 + _t6["contrasts"]["P3"]["t_ci_high"], _T6, "pct")
for _m_, _s_ in (("gpt-6.1-terra", "terra"), ("llama3.1-8b", "llama"), ("gemma3-4b", "gemma")):
    put(f"t6p1_{_s_}", _t6["contrasts"]["P1"]["per_model"][_m_]["estimate"], _T6, "pp")
    put(f"t6p2_{_s_}", _t6["contrasts"]["P2"]["per_model"][_m_]["estimate"], _T6, "pp")

_T4 = _R + "t4_codebook/summary.json"
_t4 = json.load(open(ROOT / _T4))
assert _t4["any_holm_decision_change"] == []
_g = {(r_["run"], r_["variant"]): r_ for r_ in _t4["speech_act_chip_gain"]}
for _run, _n in (("W-C r2c1", "cb_wc"), ("hw1", "cb_hw")):
    for _v, _vn in (("base", "base"), ("a_can_you_question", "q")):
        _e = _g[(_run, _v)]
        put(f"{_n}_{_vn}", _e["estimate"], _T4, "pct")
        put(f"{_n}_{_vn}_lo", _e["ci_low"], _T4, "pct")
        put(f"{_n}_{_vn}_hi", _e["ci_high"], _T4, "pct")
_mask = [abs(r_["shift_pp"]) for r_ in _t4["speech_act_chip_gain"] if r_["variant"].startswith("mask_")]
_pcv = pd.read_csv(ROOT / _R / "t4_codebook/primary_contrasts_by_variant.csv")
_pcm = _pcv[_pcv.variant.str.startswith("mask_") & _pcv.contrast.isin(["P1", "P2"])].copy()
_pcb = _pcv[(_pcv.variant == "base")].set_index(["run", "contrast"]).estimate
_pcm["shift"] = [abs(100 * (r_.estimate - _pcb[(r_.run, r_.contrast)])) for r_ in _pcm.itertuples()]
put("cb_mask_max_pp", max(_pcm["shift"].max(), max(_mask)) / 100, _T4 + " and primary_contrasts_by_variant.csv (P1, P2 masks; hw1 time-chip gain excluded)", "f1x")
put("cb_nchanged_wc", int(_pcv[(_pcv.run == "W-C r2c1") & (_pcv.variant == "a_can_you_question")].rows_changed.iloc[0]), _T4, "int")

_T2 = _R + "t2_posterior/summary.json"
_t2 = {(r_["dimension"], r_["channel"]): r_ for r_ in json.load(open(ROOT / _T2))["table"]}
_r = _t2[("polarity", "human")]
put("t2_post", _r["posterior_empirical"], _T2, "pct")
put("t2_post_lo", _r["posterior_empirical_lo"], _T2, "pct")
put("t2_post_hi", _r["posterior_empirical_hi"], _T2, "pct")
put("t2_rev", _r["silent_reversal_per_1000"], _T2, "int")
put("t2_spur", _r["spurious_cue_per_1000"], _T2, "f1")
put("t2_ratio", _r["breakeven_cost_ratio"], _T2, "int")
put("t2_modelshare", 1 - _r["model_share_cue_given_nocue"], _T2, "pct")

_T7 = _R + "t7_human_gate/summary.json"
_t7 = json.load(open(ROOT / _T7))
for _g_, _n in (("part12_elic", "t7e"), ("part13_hw", "t7h"), ("main1_H7_A1A2", "t7g")):
    _e = _t7[_g_]["dims"]["critical"]["test/R1"]
    put(_n + "_k", _e["kappa"], _T7, "p3")
    put(_n + "_lo", _e["ci"][0], _T7, "p3")
    put(_n + "_hi", _e["ci"][1], _T7, "p3")
_dims = {d_: _t7["part13_hw"]["dims"][d_]["test/R1"]["kappa"] for d_ in _t7["part13_hw"]["dims"] if d_ not in ("critical",)}
assert min(_dims, key=_dims.get) == "added_content"
put("t7h_ac_k", _dims["added_content"], _T7, "p3")
put("t7h_ac_lo", _t7["part13_hw"]["dims"]["added_content"]["test/R1"]["ci"][0], _T7, "p3")
put("t7h_ac_hi", _t7["part13_hw"]["dims"]["added_content"]["test/R1"]["ci"][1], _T7, "p3")

_T9 = _R + "t9_validator_replay/summary.json"
_t9 = json.load(open(ROOT / _T9))
_c9 = [_t9["raw"][k_] for k_ in ("W-C r2c1", "hw1", "W-D r2d1")]
assert all(len(c_["conflicts"]) == 0 and c_["leaks"] == 0 for c_ in _c9)
assert _t9["generation_calls"] == 0 and _t9["judge_calls"] == 0
put("t9_inputs", sum(c_["cue_inputs"] for c_ in _c9), _T9, "int")
put("t9_compat", sum(c_["verdicts"].get("compatible", 0) for c_ in _c9), _T9, "int")
put("t9_unknown", sum(c_["verdicts"].get("unknown", 0) for c_ in _c9), _T9, "int")
put("t9_conflicts", sum(len(c_["conflicts"]) for c_ in _c9), _T9, "int")

# cycle 4: legend test (E1) and oracle on real outputs (C49)
_LG = "analysis/legend_test/summary.json"
_lg = json.load(open(ROOT / _LG))
assert _lg["unresolved_valid_rows"] == 0 and _lg["verdict_d1"].startswith("default is NOT")
for _a_, _n in (("a_legend", "lg_a"), ("b_nolegend", "lg_b"), ("c_markers_missing", "lg_c")):
    put(_n, _lg["pooled_d1"][_a_]["aff"], _LG, "pct")
    put(_n + "_d2", _lg["d2_pooled"][_a_], _LG, "pct")
    put(_n + "_unclear", 1 - _lg["pooled_d1"][_a_]["commit"], _LG, "pct")
put("lg_min", min(_lg["pooled_d1"][a_]["aff"] for a_ in _lg["pooled_d1"]), _LG, "pct")
put("lg_unclear_max", max(1 - _lg["pooled_d1"][a_]["commit"] for a_ in _lg["pooled_d1"]), _LG, "pct")
put("lg_nmodels", len(_lg["per_model_class_d1"]), _LG, "int")

_OR = "analysis/oracle_real/summary.json"
_or = json.load(open(ROOT / _OR))
_oh = _or["headline"]
assert _or["n_unresolved_judge"] == 0
for _o_, _n in (("judge", "orr_j"), ("surface", "orr_s"), ("overlap", "orr_o")):
    put_frac(_n + "_mut", _oh[_o_ + "_mut"]["k"], _oh[_o_ + "_mut"]["n"], _OR)
    put_frac(_n + "_fa", _oh[_o_ + "_fa"]["k"], _oh[_o_ + "_fa"]["n"], _OR)
put("orr_nctl", _oh["judge_fa"]["n"], _OR, "int")
put("orr_nmut_all", _or["n_mutants"], _OR, "int")
put_frac("orr_wa", _or["wa"]["W-A injection / all"]["judge_mut"]["k"], _or["wa"]["W-A injection / all"]["judge_mut"]["n"], _OR)
_miss = [m_ for m_ in _or["judge_missed_mutants"] if m_["op"] != "booster_insert"]
assert sorted(m_["op"] for m_ in _miss) == ["speech_act_to_question", "time_shift", "time_shift"]
put("orr_nboost", _or["booster_only"]["n_mut"], _OR, "int")
put("orr_nmiss", len(_miss), _OR, "int")

# ---- cycle 5: oracle precision/recall on natural (unseeded) outputs vs human-consensus verdicts
_NP = "analysis/oracle_natural/summary.json"
_np = json.load(open(ROOT / _NP))
for _vn, _tag in (("violation", "viol"), ("preservation_failure", "pres")):
    _pl = _np["pooled_failure_sets"][_vn]
    for _m_, _mk in (("precision", "p"), ("recall", "r")):
        put(f"nat_{_tag}_{_mk}", _pl[_m_], _NP, "pct")
        put(f"nat_{_tag}_{_mk}_lo", _pl[_m_ + "_ci"][0], _NP, "pct")
        put(f"nat_{_tag}_{_mk}_hi", _pl[_m_ + "_ci"][1], _NP, "pct")
    put("nat_%s_f1" % _tag, _pl["f1"], _NP, "pct")
    put("nat_%s_npos" % _tag, _pl["n_ref_pos"], _NP, "int")
    for _m_, _mk in (("precision", "p"), ("recall", "r")):
        _vals = [_np["sets"][k_][_vn][_m_] for k_ in ("main1", "new", "hw")]
        put(f"nat_{_tag}_{_mk}_setmin", min(_vals), _NP, "pct")
        put(f"nat_{_tag}_{_mk}_setmax", max(_vals), _NP, "pct")
    put(f"nat_{_tag}_posmin", min(_np["sets"][k_][_vn]["n_ref_pos"] for k_ in ("main1", "new", "hw")), _NP, "int")
    put(f"nat_{_tag}_posmax", max(_np["sets"][k_][_vn]["n_ref_pos"] for k_ in ("main1", "new", "hw")), _NP, "int")
_ea = _np["sets"]["elic"]["assumption"]
put("nat_elic_p", _ea["precision"], _NP, "pct")
put("nat_elic_r", _ea["recall"], _NP, "pct")
put("nat_elic_n", _ea["n_units"], _NP, "int")
put("nat_nsets", 4, _NP, "int")
put("nat_nunits_viol", sum(_np["sets"][k_]["violation"]["n_units"] for k_ in ("main1", "new", "hw")), _NP, "int")

# ------------------------------------------------------------------ write ---
from c3_exports import macros as c3_macros
for _key, _value in c3_macros().items():
    put(_key, _value, "analysis/evidence_c3/current.json (C35/C36; populations separate)", "raw")

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
