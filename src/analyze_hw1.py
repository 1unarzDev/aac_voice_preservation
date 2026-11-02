"""Human-written replication analysis (run hw1) for the AAC keyword-expansion study.

    . .venv/bin/activate && python src/analyze_hw1.py

Deterministic (seed 20261031, 10,000 resamples). Reads only local files; writes analysis/hw1/.
Estimators are those of analysis/r2c/analyze_confirmatory.py (W-C): analyze.normalize_table to recompute
attribution columns, analyze.family_bootstrap (row-weighted multinomial resampling of clusters), the same
P1/P2/P3 frames, the same centred one-sided bootstrap p-value and Holm step-down. Only the cluster column
changes (writer_id for the primary CI; family_id reported for comparison).
Hand-written commentary lives in analysis/hw1/interpretation.md and is appended verbatim if present.
"""
from __future__ import annotations
import hashlib, itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import analyze as A          # noqa: E402
import hw_rules as H         # noqa: E402

OUT = ROOT / "analysis/hw1"; OUT.mkdir(parents=True, exist_ok=True)
B = 10000; SEED = 20261031
DIMS = ["polarity", "speech_act", "politeness", "agent", "time_quantity", "certainty"]
CHANNELS = A.CHANNELS
WC_DIMS = {"polarity", "speech_act", "politeness"}
JACCARD = 0.75

cand = A.load_items(str(ROOT / "annotation/written/hw_candidates.jsonl"))
kept = A.load_items(str(ROOT / "data/items/hw.jsonl"))
assert len(cand) == 574 and len(kept) == 547 and set(kept) <= set(cand)
raw0 = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
assert set(raw0.family_id) == set(cand) and not raw0.critical_source.isin(["J1", "J2"]).any()
assert raw0.critical.notna().all()   # 0 unresolved, no fallback


# ---------------------------------------------------------------- bootstrap (W-C boot, cluster column explicit)
def boot(g, col="value", cluster="writer_id", test=False):
    x = g.copy(); x["family_id"] = x[cluster]
    r = A.family_bootstrap(x, col, n_boot=B, seed=SEED)
    r["n_clusters"] = r.pop("n_families"); r["n_clusters_observed"] = r.pop("n_families_observed")
    r["n_families"] = int(g.family_id.nunique())
    if r["n"]:
        r["sum"] = float(pd.to_numeric(g[col]).sum())
    if test and r["n"]:
        agg = x.groupby("family_id", sort=True)[col].agg(["sum", "count"])
        w = np.random.default_rng(SEED).multinomial(len(agg), np.full(len(agg), 1 / len(agg)), size=B)
        den = w @ agg["count"].to_numpy(float); draws = (w @ agg["sum"].to_numpy(float))[den > 0] / den[den > 0]
        c = draws - r["estimate"]; n = len(draws)
        r["p_one_sided"] = (1 + int((c >= r["estimate"] - 1e-12).sum())) / (n + 1)
        r["p_two_sided"] = (1 + int((abs(c) >= abs(r["estimate"]) - 1e-12).sum())) / (n + 1)
    return r


def holm(rs, pkey, outkey):
    order = sorted(rs, key=lambda k: rs[k][pkey]); prev = 0
    for j, k in enumerate(order):
        prev = max(prev, min(1., (len(order) - j) * rs[k][pkey])); rs[k][outkey] = prev


# ---------------------------------------------------------------- data
def near_dup_components(items):
    fams = sorted(items); toks = {f: set(H.toks(items[f]["variants"]["A"]["source"])) |
                                  set(H.toks(items[f]["variants"]["B"]["source"])) for f in fams}
    par = {f: f for f in fams}
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    edges = []
    for f, g in itertools.combinations(fams, 2):
        if items[f]["writer_id"] == items[g]["writer_id"]:
            continue
        u = toks[f] | toks[g]
        if u and len(toks[f] & toks[g]) / len(u) >= JACCARD:
            edges.append((f, g)); par[find(f)] = find(g)
    comp = {}
    for f in fams:
        comp.setdefault(find(f), []).append(f)
    return edges, [c for c in comp.values() if len(c) > 1]


def vague_and_sure_units(raw):
    """D-057 judgment-call units: arbiter-resolved rows (key text_id, family_id, input_text)."""
    a = raw[raw.critical_source == "arbiter"]
    vague = a[(a.dimension == "time_quantity") & (a.critical == "unclear/mixed") &
              a.text.str.contains(r"today|this week|on sunday", case=False)]
    sure = a[(a.dimension == "certainty") & (a.critical == "strongly certain/emphatic") &
             a.text.str.contains(r"\bsure\b|\bcertain\b", case=False)]
    key = lambda d: set(zip(d.text_id, d.family_id, d.input_text))
    return key(vague), key(sure)


def reverse_arbiter(raw, vague, sure, which=("time", "certainty")):
    """Reverse arbiter judgment calls to the non-arbiter judge label.
    Vague time words: J1 label if substantive else J2 label (declared tie rule). 'Sure,' units: the judge
    label that differs from the arbiter's."""
    r = raw.copy()
    k = list(zip(r.text_id, r.family_id, r.input_text))
    changed = 0
    for i, key in enumerate(k):
        if (("time" in which and key in vague) or ("certainty" in which and key in sure)):
            row = r.iloc[i]
            if key in vague:
                new = row.critical_J1 if row.critical_J1 != "unclear/mixed" else row.critical_J2
            else:
                alts = [v for v in (row.critical_J1, row.critical_J2) if v != row.critical]
                new = alts[0]
            if new != row.critical:
                r.iat[i, r.columns.get_loc("critical")] = new; changed += 1
    return r, changed


def build(items, raw, drop_writers=()):
    r = raw[raw.family_id.isin(items)]
    df = A.normalize_table(r, items)
    for c in ("writer_id", "construction"):
        df[c] = df.family_id.map(lambda f: items[f].get(c, ""))
    # W-C rule: speech-act refusal/acceptance families quarantined; D-058: P06 speech-act pair excluded.
    ex = {f for f, i in items.items() if i["dimension"] == "speech_act" and (
        any(v["critical_value"] in {"refusal", "acceptance"} for v in i["variants"].values()) or i["writer_id"] == "P06")}
    ex |= {f for f, i in items.items() if i["writer_id"] in drop_writers}
    return df[~df.family_id.isin(ex)].copy(), ex


def frames(d):
    p0 = d[d.prompt_id.eq("P0")]
    keys = ["family_id", "writer_id", "variant", "model"]
    a = p0[p0.dimension.eq("speech_act")].pivot(index=keys, columns="channel", values="critical_match").reset_index()
    a["value"] = pd.to_numeric(a.chip1).astype(float) - pd.to_numeric(a.noncrit).astype(float)
    pol = p0[p0.dimension.eq("politeness") & p0.channel.eq("full")].copy()
    pol["switch"] = [np.nan if not A.known(r.crit) or not r.valid else float(r.crit == ("polite" if r.cv == "plain" else "plain"))
                     for r in pol.itertuples()]
    b = pol.pivot(index=["family_id", "writer_id", "model"], columns="cv", values="switch").reset_index()
    b["value"] = b.plain - b.polite
    amb = A.unique_ambiguous(p0[p0.dimension.eq("polarity") & p0.channel.eq("bare")]).copy()
    amb["value"] = [float(r.crit == "affirmative") - .5 if r.valid and r.crit in {"affirmative", "negated"} else np.nan
                    for r in amb.itertuples()]
    return {"P1": a, "P2": b, "P3": amb}


def primary(d, cluster="writer_id"):
    fr = frames(d)
    res = {k: boot(v, cluster=cluster, test=True) for k, v in fr.items()}
    holm(res, "p_one_sided", "p_holm")
    for r in res.values():
        r["reject_holm_005"] = bool(r["p_holm"] <= .05 and r["estimate"] > 0)
    return res, fr


def chip_gain(d, cluster="writer_id", by_model=False):
    p0 = d[d.prompt_id.eq("P0")]
    keys = ["family_id", "writer_id", "variant", "dimension", "model"]
    a = p0.pivot(index=keys, columns="channel", values="critical_match").reset_index()
    a["value"] = pd.to_numeric(a.chip1).astype(float) - pd.to_numeric(a.noncrit).astype(float)
    rows = []
    for dim, g in a.groupby("dimension"):
        rows.append(dict(dimension=dim, model="ALL") | boot(g, cluster=cluster))
        if by_model:
            for m, x in g.groupby("model"):
                rows.append(dict(dimension=dim, model=m) | boot(x, cluster=cluster))
    return pd.DataFrame(rows)


def rates(d):
    p0 = d[d.prompt_id.eq("P0")].copy()
    p0["loss"] = 1 - pd.to_numeric(p0.critical_match).astype(float)
    p0["violation_f"] = pd.to_numeric(p0.violation).astype(float)
    p0["assumption_f"] = pd.to_numeric(p0.commitment).astype(float)
    p0["match_f"] = pd.to_numeric(p0.critical_match).astype(float)
    rows = []
    for dim in DIMS:
        for ch in CHANNELS:
            g0 = p0[p0.dimension.eq(dim) & p0.channel.eq(ch)]
            mets = {"critical_match": "match_f", "loss": "loss"}
            mets |= {"violation": "violation_f"} if ch in A.CUE else {"assumption": "assumption_f"}
            for model in ["ALL"] + sorted(g0.model.unique()):
                g = g0 if model == "ALL" else g0[g0.model.eq(model)]
                for name, col in mets.items():
                    rows.append(dict(dimension=dim, channel=ch, model=model, metric=name) | boot(g, col))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main
def fmt(r, pct=True, ci=True):
    s = 100 if pct else 1
    return f"{r['estimate']*s:+.1f}" if False else f"{r['estimate']*s:.1f} [{r['ci_low']*s:.1f}, {r['ci_high']*s:.1f}]"


def main():
    edges, comps = near_dup_components(kept); edges_c, _ = near_dup_components(cand)
    vague, sure = vague_and_sure_units(raw0)
    df, excl = build(kept, raw0)
    # consistency of recomputed vs stored attribution columns
    chk = A.normalize_table(raw0, cand)
    consistency = {c: float((chk[c].astype(object).fillna("N") == raw0[s].astype(object).fillna("N").values).mean())
                   for c, s in [("critical_match", "critical_match"), ("violation", "violation"), ("commitment", "assumption")]}
    summary = {"seed": SEED, "n_boot": B, "n_candidates": len(cand), "n_kept": len(kept),
               "primary_excluded_families": sorted(excl), "n_analysed_families": int(df.family_id.nunique()),
               "families_by_dim": df.drop_duplicates("family_id").dimension.value_counts().to_dict(),
               "writers_by_dim": df.drop_duplicates("family_id").groupby("dimension").writer_id.nunique().to_dict(),
               "consistency_with_stored_columns": consistency,
               "near_dup": {"jaccard": JACCARD, "cross_writer_pairs": len(edges), "cross_writer_pairs_all_574": len(edges_c), "components": comps},
               "arbiter_judgment_units": {"vague_time_units": len(vague), "sure_units": len(sure)}}

    # 1. registered contrasts
    pw, fr = primary(df, "writer_id"); pf, _ = primary(df, "family_id")
    rows = []
    for k in pw:
        for lab, res in (("writer", pw), ("family", pf)):
            r = res[k]
            rows.append(dict(contrast=k, cluster=lab, estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                             n=r["n"], n_clusters=r["n_clusters"], n_families=r["n_families"], p_one_sided=r["p_one_sided"],
                             p_holm=r["p_holm"], reject_holm_005=r["reject_holm_005"]))
    prim = pd.DataFrame(rows); prim.to_csv(OUT / "primary_contrasts.csv", index=False)
    # extra P2 arms / P3 share
    pol = df[df.prompt_id.eq("P0") & df.dimension.eq("politeness") & df.channel.eq("full")].copy()
    pol["switch"] = [np.nan if not A.known(r.crit) or not r.valid else float(r.crit == ("polite" if r.cv == "plain" else "plain"))
                     for r in pol.itertuples()]
    arms = {cv: boot(pol[pol.cv.eq(cv)], "switch") for cv in ("plain", "polite")}
    bare = fr["P3"].copy(); bare["share"] = bare.value + .5
    summary["P2_arms"] = {"addition_plain_to_polite": arms["plain"], "removal_polite_to_plain": arms["polite"]}
    summary["P3_affirmative_share"] = boot(bare, "share")
    summary["P1_arms"] = {ch: boot(df[df.prompt_id.eq("P0") & df.dimension.eq("speech_act") & df.channel.eq(ch)].assign(
        m=lambda x: pd.to_numeric(x.critical_match).astype(float)), "m") for ch in ("chip1", "noncrit")}
    summary["primary"] = {k: {"writer": pw[k], "family": pf[k]} for k in pw}
    bm = []
    for k, f in fr.items():
        for m, g in f.groupby("model"):
            bm.append(dict(contrast=k, model=m) | boot(g))
    pd.DataFrame(bm).to_csv(OUT / "primary_by_model.csv", index=False)

    # 2. six-dimension rates and chip gain
    rt = rates(df); rt.to_csv(OUT / "six_dim_rates.csv", index=False)
    cg_w = chip_gain(df, "writer_id", by_model=True); cg_f = chip_gain(df, "family_id")
    cg = cg_w.merge(cg_f[["dimension", "model", "ci_low", "ci_high"]].rename(columns={"ci_low": "fam_ci_low", "ci_high": "fam_ci_high"}),
                    on=["dimension", "model"], how="left")
    cg.to_csv(OUT / "chip_gain.csv", index=False)

    # W-C / main1 comparators
    wc_l = pd.read_csv(ROOT / "analysis/r2c/channel_ladder.csv"); wc_lm = pd.read_csv(ROOT / "analysis/r2c/channel_ladder_by_model.csv")
    wc_d = pd.read_csv(ROOT / "analysis/r2c/channel_differences.csv"); wc_c = pd.read_csv(ROOT / "analysis/r2c/commitment.csv")
    m1 = pd.read_parquet(ROOT / "analysis/main1/scored.parquet"); m1 = m1[m1.prompt_id.eq("P0")]
    sbs = []
    def add(dim, q, ch, h, comp, src):
        sbs.append(dict(dimension=dim, quantity=q, channel=ch, hw_est=h["estimate"], hw_lo=h["ci_low"], hw_hi=h["ci_high"],
                        hw_n=h["n"], hw_writers=h.get("n_clusters"), comp_source=src,
                        comp_est=comp.get("estimate"), comp_lo=comp.get("ci_low"), comp_hi=comp.get("ci_high"), comp_n=comp.get("n")))
    for dim in DIMS:
        wc = dim in WC_DIMS
        for ch in CHANNELS:
            h = rt[(rt.dimension == dim) & (rt.channel == ch) & (rt.model == "ALL") & (rt.metric == "critical_match")].iloc[0].to_dict()
            if wc:
                c = wc_l[(wc_l.dimension == dim) & (wc_l.channel == ch) & (wc_l.metric == "critical_match")].iloc[0].to_dict()
                src = "W-C r2c1"
            else:
                g = m1[m1.dimension.eq(dim) & m1.channel.eq(ch)]
                c = A.family_bootstrap(g.assign(v=pd.to_numeric(g.critical_match).astype(float)), "v", n_boot=B, seed=SEED); src = "main1 (discovery)"
            add(dim, "critical_match", ch, h, c, src)
        h = cg[(cg.dimension == dim) & (cg.model == "ALL")].iloc[0].to_dict()
        if wc:
            c = wc_d[(wc_d.dimension == dim) & (wc_d.metric == "chip1-noncrit")].iloc[0].to_dict(); src = "W-C r2c1"
        else:
            p = m1[m1.dimension.eq(dim)].pivot(index=["family_id", "variant", "model"], columns="channel", values="critical_match").reset_index()
            p["v"] = pd.to_numeric(p.chip1).astype(float) - pd.to_numeric(p.noncrit).astype(float)
            c = A.family_bootstrap(p, "v", n_boot=B, seed=SEED); src = "main1 (discovery)"
        add(dim, "chip_gain(chip1-noncrit)", "-", h, c, src)
        for ch in ("bare", "noncrit"):
            h = rt[(rt.dimension == dim) & (rt.channel == ch) & (rt.model == "ALL") & (rt.metric == "assumption")].iloc[0].to_dict()
            if wc:
                c = wc_c[(wc_c.dimension == dim) & (wc_c.channel == ch) & (wc_c.prompt_id == "P0") & (wc_c.metric == "commitment")].iloc[0].to_dict(); src = "W-C r2c1"
            else:
                g = m1[m1.dimension.eq(dim) & m1.channel.eq(ch)]
                c = A.family_bootstrap(g.assign(v=pd.to_numeric(g.commitment).astype(float)), "v", n_boot=B, seed=SEED); src = "main1 (discovery)"
            add(dim, "assumption", ch, h, c, src)
        for ch in ("chip1", "chipall", "full"):
            h = rt[(rt.dimension == dim) & (rt.channel == ch) & (rt.model == "ALL") & (rt.metric == "violation")].iloc[0].to_dict()
            if wc:
                c0 = wc_l[(wc_l.dimension == dim) & (wc_l.channel == ch) & (wc_l.metric == "critical_match")].iloc[0].to_dict()
                c = {"estimate": 1 - c0["estimate"], "ci_low": 1 - c0["ci_high"], "ci_high": 1 - c0["ci_low"], "n": c0["n"]}; src = "W-C r2c1 (1-match)"
            else:
                g = m1[m1.dimension.eq(dim) & m1.channel.eq(ch)]
                c = A.family_bootstrap(g.assign(v=pd.to_numeric(g.violation).astype(float)), "v", n_boot=B, seed=SEED); src = "main1 (discovery)"
            add(dim, "violation", ch, h, c, src)
    pd.DataFrame(sbs).to_csv(OUT / "side_by_side.csv", index=False)
    # per-model critical_match side by side (W-C dims)
    pm = []
    for dim in DIMS:
        for ch in CHANNELS:
            for m in sorted(df.model.unique()):
                h = rt[(rt.dimension == dim) & (rt.channel == ch) & (rt.model == m) & (rt.metric == "critical_match")].iloc[0]
                c = wc_lm[(wc_lm.dimension == dim) & (wc_lm.channel == ch) & (wc_lm.model == m) & (wc_lm.metric == "critical_match")]
                pm.append(dict(dimension=dim, channel=ch, model=m, hw_est=h.estimate, hw_lo=h.ci_low, hw_hi=h.ci_high,
                               wc_est=float(c.estimate.iloc[0]) if len(c) else np.nan))
    pd.DataFrame(pm).to_csv(OUT / "critical_match_by_model_vs_wc.csv", index=False)

    # 3. sensitivities
    scen = {}
    scen["primary"] = df
    collapse_drop = {f for c in comps for f in sorted(c)[1:]}
    scen["a_collapse_near_duplicates"] = df[~df.family_id.isin(collapse_drop)]
    scen["b_exclude_P06"], _ = build(kept, raw0, drop_writers=("P06",))
    r_rev, nrev = reverse_arbiter(raw0, vague, sure)
    scen["c_reverse_arbiter_time_and_sure"], _ = build(kept, r_rev)
    r_t, nt = reverse_arbiter(raw0, vague, sure, ("time",)); scen["c1_reverse_vague_time_only"], _ = build(kept, r_t)
    r_s, ns = reverse_arbiter(raw0, vague, sure, ("certainty",)); scen["c2_reverse_sure_only"], _ = build(kept, r_s)
    scen["d_all_574_candidates"], _ = build(cand, raw0)
    summary["sensitivity_n"] = {"near_dup_dropped_families": len(collapse_drop), "rows_reversed_time_and_sure": nrev,
                                "rows_reversed_time": nt, "rows_reversed_sure": ns,
                                "families": {k: int(v.family_id.nunique()) for k, v in scen.items()}}
    srows = []
    for name, d in scen.items():
        res, _ = primary(d)
        for k, r in res.items():
            srows.append(dict(scenario=name, kind="registered", subject=k, estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                              n=r["n"], n_clusters=r["n_clusters"], p_holm=r["p_holm"], reject_holm_005=r["reject_holm_005"]))
        g = chip_gain(d)
        for r in g.itertuples():
            srows.append(dict(scenario=name, kind="chip_gain", subject=r.dimension, estimate=r.estimate, ci_low=r.ci_low, ci_high=r.ci_high,
                              n=r.n, n_clusters=r.n_clusters, p_holm=np.nan, reject_holm_005=np.nan))
        rr = rates(d)
        for r in rr[(rr.model == "ALL") & rr.metric.isin(["assumption", "violation"])].itertuples():
            srows.append(dict(scenario=name, kind=f"{r.metric}_{r.channel}", subject=r.dimension, estimate=r.estimate, ci_low=r.ci_low,
                              ci_high=r.ci_high, n=r.n, n_clusters=r.n_clusters, p_holm=np.nan, reject_holm_005=np.nan))
        e = d[d.prompt_id.eq("P0") & d.dimension.eq("certainty") & d.channel.isin(["chip1", "chipall"]) & d.valid].copy()
        e["emph"] = (e.crit == "strongly certain/emphatic").astype(float)
        r = boot(e[e.cv.eq("plain assertion")], "emph")
        srows.append(dict(scenario=name, kind="emphatic_share_chip1+chipall_plain_variant", subject="certainty", estimate=r["estimate"],
                          ci_low=r["ci_low"], ci_high=r["ci_high"], n=r["n"], n_clusters=r["n_clusters"], p_holm=np.nan, reject_holm_005=np.nan))
    sens = pd.DataFrame(srows)
    base = sens[sens.scenario == "primary"].set_index(["kind", "subject"])
    def flag(r):
        if r.scenario == "primary":
            return ""
        b = base.loc[(r.kind, r.subject)]
        out = []
        if r.kind == "registered" and bool(r.reject_holm_005) != bool(b.reject_holm_005): out.append("HOLM DECISION CHANGES")
        zero = lambda lo, hi: lo <= 0 <= hi
        if r.kind in ("registered", "chip_gain") and zero(r.ci_low, r.ci_high) != zero(b.ci_low, b.ci_high): out.append("CI-vs-0 CHANGES")
        if abs(r.estimate - b.estimate) >= .05 and r.estimate == r.estimate: out.append("shift>=5pp")
        return "; ".join(out)
    sens["flag"] = sens.apply(flag, axis=1); sens.to_csv(OUT / "sensitivity.csv", index=False)
    summary["sensitivity_flags"] = sens[sens.flag.ne("")][["scenario", "kind", "subject", "estimate", "flag"]].to_dict("records")

    # 4. examples (declared rule)
    ex_md = ["# Representative examples (declared rule, no cherry-picking)\n",
             "Rule: per dimension, order kept & analysed families by SHA256(family_id); take the first family that has, in P0,",
             "a bare-channel output that is committed (not unclear) yet does not match the variant's critical value, while the",
             "chip1 output for the same family/variant/model does match. Within the family: models in alphabetical order, then variant A, then B.",
             "All text below is the stored model output; labels are the stored judge/arbiter labels. The rates show how typical the example is "
             "(writer-cluster 95% CI, pooled over models).\n"]
    ex_json = {}
    p0 = df[df.prompt_id.eq("P0")]
    for dim in DIMS:
        d = p0[p0.dimension.eq(dim)]
        key = ["family_id", "variant", "model"]
        bare_ = d[d.channel.eq("bare")].set_index(key); chip_ = d[d.channel.eq("chip1")].set_index(key)
        if dim == "polarity":
            pass
        cand_idx = [i for i in bare_.index if i in chip_.index and T(bare_.loc[i].commitment) and F(bare_.loc[i].critical_match)
                    and T(chip_.loc[i].critical_match)]
        cand_idx = [i for i in cand_idx if True]
        sb = bare_.copy(); sb["rep"] = [(i in set(cand_idx)) for i in sb.index]
        if not cand_idx:
            ex_md.append(f"## {dim}\nNo qualifying family.\n"); continue
        fam_order = sorted({i[0] for i in cand_idx}, key=lambda f: hashlib.sha256(f.encode()).hexdigest())
        fam = fam_order[0]
        pick = sorted([i for i in cand_idx if i[0] == fam], key=lambda i: (i[2], i[1]))[0]
        it = kept.get(fam) or cand[fam]
        rows_ = d[(d.family_id == fam) & (d.variant == pick[1]) & (d.model == pick[2])].set_index("channel")
        # rates represented
        bw = d[d.channel.eq("bare")].copy(); bw["bare_wrong_committed"] = [float(T(c) and F(m)) for c, m in zip(bw.commitment, bw.critical_match)]
        r_bw = boot(bw, "bare_wrong_committed")
        q = [i for i in bare_.index if T(bare_.loc[i].commitment) and F(bare_.loc[i].critical_match) and i in chip_.index]
        qq = pd.DataFrame({"family_id": [i[0] for i in q], "writer_id": [it_w(kept, cand, i[0]) for i in q],
                           "v": [float(T(chip_.loc[i].critical_match)) for i in q]})
        r_rep = boot(qq, "v")
        ex_md.append(f"## {dim}\n")
        ex_md.append(f"Family `{fam}` (writer {it['writer_id']}); first of {len(fam_order)} qualifying families by hash; model `{pick[2]}`, variant {pick[1]} "
                     f"(target value: **{rows_.loc['bare'].cv}**). Source sentence: \"{rows_.loc['bare'].source}\"\n")
        ex_md.append("| channel | input given to the model | stored output | judged label | label source |\n|---|---|---|---|---|")
        for ch in CHANNELS:
            r = rows_.loc[ch]
            ex_md.append(f"| {ch} | `{r.input_text}` | {r.text} | {r.crit} | {r.label_source} |")
        ex_md.append(f"\nRate the example represents: in this dimension, bare outputs that commit to a wrong value occur at "
                     f"{fmt(r_bw)}% of bare rows (n={r_bw['n']}, {r_bw['n_clusters']} writers); when they do, the chip1 output matches the target "
                     f"{fmt(r_rep)}% of the time (n={r_rep['n']}). (A binary dimension whose two variants share one bare input is wrong on exactly one variant whenever the model commits, so ~50% is the design ceiling there, not a finding.) Pooled chip gain (chip1 - noncrit): {fmt(cg[(cg.dimension==dim)&(cg.model=='ALL')].iloc[0])} pp.\n")
        ex_json[dim] = {"family_id": fam, "model": pick[2], "variant": pick[1], "n_qualifying_families": len(fam_order),
                        "bare_wrong_committed_rate": r_bw, "repair_rate_given_bare_wrong": r_rep}
    (OUT / "examples.md").write_text("\n".join(ex_md) + "\n")
    summary["examples"] = ex_json

    # ---------------------------------------------------------------- report
    L = ["# hw1 human-written replication (generated by src/analyze_hw1.py)\n",
         f"Run hw1: 4 models, P0, 5 channels, judged + blind-arbitrated, attributed without fallback (0 unresolved). Analysed: "
         f"{summary['n_analysed_families']} of 547 kept families (primary exclusions: {len(excl)}: the P06 speech-act pair per D-058 and any "
         f"refusal/acceptance speech-act family, as in W-C). Bootstrap: {B} cluster resamples, seed {SEED}, W-C estimator "
         f"(`analyze.family_bootstrap`); primary clusters = writer_id.\n",
         f"Families by dimension: {summary['families_by_dim']}. Writers by dimension: {summary['writers_by_dim']}. "
         "**Each contrast rests on only 5-7 writers; writer-cluster percentile CIs with so few clusters are unstable and probably too narrow "
         "at the tails (P1: the speech-act subset).**\n",
         "## 1. Registered contrasts (Holm across 3, one-sided centred-bootstrap p)\n",
         "| contrast | estimate pp | writer-cluster 95% CI | family-cluster 95% CI | n rows | writers (families) | Holm p (writer) | Holm decision | W-C (arbitrated) |",
         "|---|---|---|---|---|---|---|---|---|"]
    wcp = json.loads((ROOT / "analysis/r2c/primary.json").read_text())["primaries"]
    for k in ("P1", "P2", "P3"):
        w, f = pw[k], pf[k]; c = wcp[k]
        L.append(f"| {k} | {w['estimate']*100:.2f} | [{w['ci_low']*100:.2f}, {w['ci_high']*100:.2f}] | [{f['ci_low']*100:.2f}, {f['ci_high']*100:.2f}] | "
                 f"{w['n']} | {w['n_clusters']} ({w['n_families']}) | {w['p_holm']:.4f} | {'reject' if w['reject_holm_005'] else 'not rejected'} | "
                 f"{c['estimate']*100:.2f} [{c['ci_low']*100:.2f}, {c['ci_high']*100:.2f}], n={c['n']} |")
    L.append(f"\nFamily-cluster Holm decisions: " + ", ".join(f"{k} {'reject' if pf[k]['reject_holm_005'] else 'not rejected'} (p={pf[k]['p_holm']:.4f})" for k in pf))
    a1, a2 = arms["plain"], arms["polite"]; s3 = summary["P3_affirmative_share"]
    L.append(f"\nP1 arms: chip1 critical match {fmt(summary['P1_arms']['chip1'])}%, noncrit {fmt(summary['P1_arms']['noncrit'])}% (rows pooled over variants and models). "
             f"P2 arms: addition (plain->polite) {fmt(a1)}%, removal (polite->plain) {fmt(a2)}%. P3: bare affirmative share {fmt(s3)}% "
             f"(n={s3['n']}; the contrast is share - 50%). P3 uses the same frame as W-C (one bare row per family x model, share of 'affirmative' among valid affirmative/negated outputs).\n")
    L.append("Per-model contrasts: `primary_by_model.csv`.\n")
    L.append("## 2. Six-dimension replication (P0, pooled over models; writer-cluster CIs; rates in %)\n")
    L.append("Chip gain = chip1 - noncrit critical match. Violation = cue channels (chip1/chipall/full): output contradicts the supplied cue. "
             "Assumption = bare/noncrit: output commits to a value (not unclear). Loss = 1 - critical match. Comparator: W-C (arbitrated, machine-written) for "
             "polarity/speech act/politeness; main1 (discovery, machine-written, 10 families/dimension) for agent/time/certainty.\n")
    sb = pd.DataFrame(sbs)
    def cell(est, lo, hi): return "NA" if est != est else f"{est*100:.1f} [{lo*100:.1f}, {hi*100:.1f}]"
    L.append("| dimension | quantity | channel | hw1 | writers | n | comparator | comparator est |\n|---|---|---|---|---|---|---|---|")
    for r in sb.itertuples():
        L.append(f"| {r.dimension} | {r.quantity} | {r.channel} | {cell(r.hw_est, r.hw_lo, r.hw_hi)} | {r.hw_writers} | {r.hw_n} | {r.comp_source} | {cell(r.comp_est, r.comp_lo, r.comp_hi)} |")
    L.append("\nBy channel x model: `six_dim_rates.csv` (critical_match, loss, violation/assumption), `critical_match_by_model_vs_wc.csv`, `chip_gain.csv` (also by model, with family-cluster CIs).\n")
    L.append("## 3. Sensitivity (writer-cluster; full table in `sensitivity.csv`)\n")
    L.append(f"Near-duplicate components (token Jaccard >= {JACCARD} across writers on the union of both sentences' tokens): {len(edges)} cross-writer pairs "
             f"among the 547 kept ({len(edges_c)} among all 574 candidates; D-048 recorded 33), {len(comps)} components; collapsing keeps the lowest family_id per component (drops {len(collapse_drop)}). "
             f"Arbiter reversal changed {nrev} rows ({len(vague)} vague-time units, {len(sure)} 'Sure' units).\n")
    sub = sens[sens.kind.isin(["registered", "chip_gain"])].copy()
    L.append("| scenario | item | kind | estimate pp | 95% CI | n | writers | flag |\n|---|---|---|---|---|---|---|---|")
    for r in sub.itertuples():
        L.append(f"| {r.scenario} | {r.subject} | {r.kind} | {r.estimate*100:.1f} | [{r.ci_low*100:.1f}, {r.ci_high*100:.1f}] | {r.n} | {r.n_clusters} | {r.flag} |")
    mx = sens[sens.scenario.ne("primary")].assign(b=lambda x: [base.loc[(k, u)].estimate for k, u in zip(x.kind, x.subject)])
    mx["dshift"] = (mx.estimate - mx.b).abs()
    L.append("\nLargest absolute shift from primary per scenario (any kind, pp): " + "; ".join(
        f"{n}: {g.dshift.max()*100:.1f} ({g.loc[g.dshift.idxmax(), 'kind']}/{g.loc[g.dshift.idxmax(), 'subject']})" for n, g in mx.groupby("scenario")))
    summary["max_shift_pp"] = {n: float(g.dshift.max() * 100) for n, g in mx.groupby("scenario")}
    L.append("\nFlagged changes (any kind):\n")
    fl = sens[sens.flag.ne("")]
    L.append("\n".join(f"- {r.scenario} / {r.kind} / {r.subject}: {r.estimate*100:.1f} pp ({r.flag})" for r in fl.itertuples()) or "- none")
    L.append("\n## 4. Examples\nSee `examples.md` (declared hash rule).\n")
    L.append(f"## Integrity\nRecomputed vs stored attribution agreement: {consistency}.\n")
    interp = OUT / "interpretation.md"
    if interp.exists():
        L.append("\n" + interp.read_text())
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print("done", {k: (round(v["writer"]["estimate"], 4), round(v["writer"]["ci_low"], 4), round(v["writer"]["ci_high"], 4), round(v["writer"]["p_holm"], 4)) for k, v in summary["primary"].items()})


def T(x):
    return x is not None and not pd.isna(x) and bool(x)


def F(x):
    return x is not None and not pd.isna(x) and not bool(x)


def it_w(kept_, cand_, f):
    return (kept_.get(f) or cand_[f])["writer_id"]


if __name__ == "__main__":
    main()
