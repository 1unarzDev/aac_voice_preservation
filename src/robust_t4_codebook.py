"""T4: codebook-sensitivity re-scoring of P1/P2/P3 and the speech-act chip gain (stored labels only).

    . .venv/bin/activate && python src/robust_t4_codebook.py

Runs: W-C (runs/r2c1, arbitrated), hw1 (runs/hw1), elic1 (runs/elic1). No generation, no judge calls: stored final
critical labels are re-mapped by output-text pattern, or arbitrated units are masked (critical -> unknown; unknowns leave the
denominators exactly as in analysis/r2c 'unknown_masked').
Variants
  base                    stored labels (reproduces analysis/r2c and analysis/hw1)
  a_can_you_question      'Can you / Could you ...?' outputs coded question, not request/command (speech-act families)
  a2_can_you_no_please    same, but only when the output has no 'please' (CB: any ask with please = request)
  b_want_please_statement 'I want/need/would like X, please' outputs coded statement, not request/command
  ab                      a + b
  mask_tag:<tag>          drop the arbitrated units of one precedent class (tags from the arbiter rationale / dimension / text)
  mask_all_arbitrated     drop all arbitrated units
Estimators are those of analysis/r2c/analyze_confirmatory.py and src/analyze_hw1.py (cluster bootstrap, 10,000 resamples, seed
20261031, Holm over P1-P3). The base rows are checked against the stored headline numbers.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A                                   # noqa: E402
from robust_common import outdir, write_json, pct, md_table   # noqa: E402

OUT = outdir("t4_codebook"); B = 10000; SEED = 20261031
CAN_YOU = re.compile(r"(?:^|[.!?;,]\s+)(?:can|could)\s+you\b[^.!?]*\?", re.I)
WANT_PLEASE = re.compile(r"^\W*I\s+(?:want|need|would like|'d like|’d like)\b.*\bplease\b", re.I)


# ------------------------------------------------------------------ tags for arbiter precedents
def tag_unit(r) -> str:
    dim, crit, rat, text = r["dimension"], r["critical"], str(r.get("rationale", "")).lower(), str(r.get("text", "")).lower()
    if dim == "politeness":
        return "polite_softener(May I/would...if you could/would it be possible)"
    if dim == "speech_act":
        if "cb-9" in rat or re.search(r"can/could i|can i|could i", rat): return "cb9_Can_I_please_question"
        if "please" in rat and crit == "request/command": return "please_ask_request"
        if "tell" in rat: return "performative_I_tell_you_to_X"
        if re.search(r"will you|are you able|will you be", rat): return "will_you_request_or_plans"
        if crit == "offer/suggestion": return "should_we_let_us_offer"
        if "fragment" in rat or "garbled" in rat or "verbless" in rat or "no clear" in rat: return "fragment_unclear"
        if crit == "question": return "indirect_or_info_question"
        return "speech_act_other"
    if dim == "polarity":
        if re.search(r"uncertain|not-know|did not think", rat): return "negation_only_shows_uncertainty"
        return "negation_scope_embedded_or_contrastive"
    if dim == "time_quantity":
        if crit == "unclear/mixed" and re.search(r"today|this week|on sunday", text): return "time_vague_word_unclear(D-057 judgment call)"
        if crit == "unclear/mixed": return "time_no_time_word_unclear(~118)"
        if crit == "now": return "time_will_now"
        if crit == "later": return "time_will_later"
        return "time_other"
    if dim == "certainty":
        if crit == "strongly certain/emphatic": return "certainty_sure_emphatic(D-057)"
        if crit == "hedged/uncertain":
            return "certainty_hope_wonder_could_hedge" if re.search(r"hope|wonder|could", rat + " " + text) else "certainty_hedge_other"
        if crit == "unclear/mixed": return "certainty_request_question_unclear"
        return "certainty_plain_or_other"
    if dim == "agent":
        return "agent_inanimate_CB4" if "inanimate" in rat else "agent_other(CB-5/7)"
    return "other"


def load_arbiter(run):
    a = pd.read_json(ROOT / f"runs/{run}/arbiter.jsonl", lines=True)
    a["tag"] = a.apply(tag_unit, axis=1)
    return a


# ------------------------------------------------------------------ data per run
def wc_setup():
    items = A.load_items(str(ROOT / "data/items/r2_c[12].jsonl"))
    raw = pd.read_parquet(ROOT / "runs/r2c1/scored.parquet")
    fb = raw.critical_source.isin(["J1", "J2"]); raw.loc[fb, ["critical", "critical_source"]] = None
    ex = {f for f, i in items.items() if i.get("primary_exclude") or (i["dimension"] == "speech_act" and any(
        v["critical_value"] in {"refusal", "acceptance"} for v in i["variants"].values()))}
    return dict(items=items, raw=raw, excl=ex, cluster=lambda i: i["cluster_id"], arbiter=load_arbiter("r2c1"), label="W-C r2c1")


def hw_setup():
    import analyze_hw1 as H1
    items, raw = H1.kept, H1.raw0
    ex = {f for f, i in items.items() if i["dimension"] == "speech_act" and (
        any(v["critical_value"] in {"refusal", "acceptance"} for v in i["variants"].values()) or i["writer_id"] == "P06")}
    return dict(items=items, raw=raw, excl=ex, cluster=lambda i: i["writer_id"], arbiter=load_arbiter("hw1"), label="hw1")


# ------------------------------------------------------------------ variants
def remap(raw, kind):
    r = raw.copy(); m = r.dimension.eq("speech_act") if "dimension" in r else None
    sa = r.critical.eq("request/command") & r.text.fillna("").str.len().gt(0)
    # dimension is the family's; derive from the item file passed through 'dimension' col if present
    return r, sa


def variant_frame(raw, items, spec, arb):
    r = raw.copy()
    dim = r.family_id.map(lambda f: items[f]["dimension"]) if "dimension" not in r else r.dimension
    isreq = dim.eq("speech_act") & r.critical.eq("request/command")
    txt = r.text.fillna("")
    changed = 0
    if spec in ("a_can_you_question", "ab"):
        m = isreq & txt.map(lambda t: bool(CAN_YOU.search(t))); r.loc[m, "critical"] = "question"; changed += int(m.sum())
    if spec == "a2_can_you_no_please":
        m = isreq & txt.map(lambda t: bool(CAN_YOU.search(t)) and "please" not in t.lower()); r.loc[m, "critical"] = "question"; changed += int(m.sum())
    if spec in ("b_want_please_statement", "ab"):
        isreq = dim.eq("speech_act") & r.critical.eq("request/command")
        m = isreq & txt.map(lambda t: bool(WANT_PLEASE.search(t))); r.loc[m, "critical"] = "statement"; changed += int(m.sum())
    if spec == "mask_all_arbitrated" or spec.startswith("mask_tag:"):
        units = arb if spec == "mask_all_arbitrated" else arb[arb.tag == spec.split(":", 1)[1]]
        keys = set(zip(units.text_id, units.family_id, units.input_text))
        m = pd.Series([k in keys for k in zip(r.text_id, r.family_id, r.input_text)], index=r.index) & r.critical_source.eq("arbiter")
        r.loc[m, ["critical", "critical_source"]] = None; changed += int(m.sum())
    return r, changed


def build(raw, items, ex, cl):
    r = raw[raw.prompt_id.eq("P0") & raw.channel.isin(["bare", "noncrit", "chip1", "full"]) & raw.family_id.isin(items)]
    d = A.normalize_table(r, items)
    d["cl"] = d.family_id.map(lambda f: cl(items[f]))
    return d[~d.family_id.isin(ex)].copy()


def boot(g, col="value", test=False):
    x = g.copy(); x["family_id"] = x["cl"]
    r = A.family_bootstrap(x, col, n_boot=B, seed=SEED)
    r["n_clusters"] = r.pop("n_families"); r["n_clusters_observed"] = r.pop("n_families_observed")
    if test and r["n"]:
        agg = x.groupby("family_id", sort=True)[col].agg(["sum", "count"])
        w = np.random.default_rng(SEED).multinomial(len(agg), np.full(len(agg), 1 / len(agg)), size=B)
        den = w @ agg["count"].to_numpy(float); draws = (w @ agg["sum"].to_numpy(float))[den > 0] / den[den > 0]
        r["p_one_sided"] = (1 + int(((draws - r["estimate"]) >= r["estimate"] - 1e-12).sum())) / (len(draws) + 1)
    return r


def frames(d):
    keys = ["family_id", "cl", "variant", "model"]
    a = d[d.dimension.eq("speech_act")].pivot(index=keys, columns="channel", values="critical_match").reset_index()
    a["value"] = pd.to_numeric(a.chip1).astype(float) - pd.to_numeric(a.noncrit).astype(float)
    pol = d[d.dimension.eq("politeness") & d.channel.eq("full")].copy()
    pol["switch"] = [np.nan if not A.known(r.crit) or not r.valid else float(r.crit == ("polite" if r.cv == "plain" else "plain")) for r in pol.itertuples()]
    b = pol.pivot(index=["family_id", "cl", "model"], columns="cv", values="switch").reset_index(); b["value"] = b.plain - b.polite
    amb = A.unique_ambiguous(d[d.dimension.eq("polarity") & d.channel.eq("bare")]).copy()
    amb["value"] = [float(r.crit == "affirmative") - .5 if r.valid and r.crit in {"affirmative", "negated"} else np.nan for r in amb.itertuples()]
    return {"P1": a, "P2": b, "P3": amb}


def holm(rs):
    order = sorted(rs, key=lambda k: rs[k]["p_one_sided"]); prev = 0
    for j, k in enumerate(order):
        prev = max(prev, min(1., (len(order) - j) * rs[k]["p_one_sided"])); rs[k]["p_holm"] = prev


def evaluate(d, full_gain=True):
    fr = frames(d); res = {k: boot(v, test=True) for k, v in fr.items()}; holm(res)
    for r in res.values(): r["reject"] = bool(r["p_holm"] <= .05 and r["estimate"] > 0)
    out = dict(res)
    p0 = d[d.channel.isin(["chip1", "noncrit"])]
    a = p0.pivot(index=["family_id", "cl", "variant", "dimension", "model"], columns="channel", values="critical_match").reset_index()
    a["value"] = pd.to_numeric(a.chip1).astype(float) - pd.to_numeric(a.noncrit).astype(float)
    gains = {dm: boot(g) for dm, g in a.groupby("dimension")} if full_gain else {"speech_act": boot(a[a.dimension.eq("speech_act")])}
    # P3 arm: direct affirmative share of committed bare outputs
    bare = fr["P3"].assign(share=lambda x: x.value + .5); out["P3_share"] = boot(bare, "share")
    return out, gains


def run_one(S, variants):
    rows, grows = [], []
    for spec in variants:
        raw2, changed = variant_frame(S["raw"], S["items"], spec, S["arbiter"])
        d = build(raw2, S["items"], S["excl"], S["cluster"])
        res, gains = evaluate(d)
        for k in ("P1", "P2", "P3"):
            r = res[k]
            rows.append(dict(run=S["label"], variant=spec, rows_changed=changed, contrast=k, estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                             n=r["n"], n_clusters=r["n_clusters"], p_holm=r["p_holm"], reject_holm=r["reject"]))
        r = res["P3_share"]
        rows.append(dict(run=S["label"], variant=spec, rows_changed=changed, contrast="P3_affirmative_share", estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                         n=r["n"], n_clusters=r["n_clusters"], p_holm=np.nan, reject_holm=np.nan))
        for dm, r in gains.items():
            grows.append(dict(run=S["label"], variant=spec, dimension=dm, estimate=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"], n=r["n"], n_clusters=r["n_clusters"]))
        print(S["label"], spec, changed, flush=True)
    return pd.DataFrame(rows), pd.DataFrame(grows)


# ------------------------------------------------------------------ elic1 (descriptive outcomes: match rate of focal critical label)
def elic():
    items = A.load_items(str(ROOT / "data/items/elic.jsonl"))
    raw = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); raw = raw[raw.prompt_id.eq("P0")]
    arb = load_arbiter("elic1")
    rows = []; spec_list = ["base", "a_can_you_question", "a2_can_you_no_please", "b_want_please_statement", "ab"] + \
        [f"mask_tag:{t}" for t in sorted(arb.tag.unique())] + ["mask_all_arbitrated"]
    n_by = {}
    for spec in spec_list:
        r2, changed = variant_frame(raw, items, spec, arb)
        from labels import critical_match as cm
        d = r2.copy(); d["cl"] = d.family_id
        d["dimension"] = d.family_id.map(lambda f: items[f]["dimension"]); d["cv"] = d.family_id.map(lambda f: items[f]["variants"]["A"]["critical_value"])
        d["critical_match"] = [None if (not v or c is None or pd.isna(c)) else cm(dm, cv_, c) for v, c, dm, cv_ in zip(d.valid.astype(bool), d.critical, d.dimension, d.cv)]
        d["grp"] = np.where(d.channel.eq("pos_cap4"), "POS-cap4", "human keywords")
        for (dm, grp), g in d.groupby(["dimension", "grp"]):
            if dm not in ("speech_act", "politeness", "polarity"): continue
            r = A.family_bootstrap(g.assign(v=pd.to_numeric(g.critical_match).astype(float)), "v", n_boot=2000, seed=SEED)
            rows.append(dict(variant=spec, rows_changed=changed, dimension=dm, keywords=grp, match=r["estimate"], ci_low=r["ci_low"], ci_high=r["ci_high"], n=r["n"], families=r["n_families"]))
        # question-family outputs coded request, request-family outputs coded question (speech act families only)
        sa = d[d.dimension.eq("speech_act") & d.valid.astype(bool)]
        for cv, g in sa.groupby("cv"):
            rows.append(dict(variant=spec, rows_changed=changed, dimension=f"speech_act[{cv}]", keywords="all", match=float(pd.to_numeric(g.critical_match).astype(float).mean()),
                             ci_low=np.nan, ci_high=np.nan, n=int(g.critical_match.notna().sum()), families=int(g.family_id.nunique())))
        print("elic1", spec, flush=True)
    return pd.DataFrame(rows), arb


def main():
    out = {}
    SETS = [wc_setup(), hw_setup()]
    allp, allg = [], []
    for S in SETS:
        arb = S["arbiter"]
        tags = sorted(arb.tag.unique())
        variants = ["base", "a_can_you_question", "a2_can_you_no_please", "b_want_please_statement", "ab"] + [f"mask_tag:{t}" for t in tags] + ["mask_all_arbitrated"]
        p, g = run_one(S, variants); allp.append(p); allg.append(g)
        out[S["label"]] = {"arbiter_units": len(arb), "tags": arb.tag.value_counts().to_dict()}
    P = pd.concat(allp); G = pd.concat(allg); P.to_csv(OUT / "primary_contrasts_by_variant.csv", index=False); G.to_csv(OUT / "chip_gain_by_variant.csv", index=False)
    E, earb = elic(); E.to_csv(OUT / "elic1_by_variant.csv", index=False)
    out["elic1"] = {"arbiter_units": len(earb), "tags": earb.tag.value_counts().to_dict()}
    # flags
    base = P[P.variant.eq("base")].set_index(["run", "contrast"])
    def flag(r):
        b = base.loc[(r.run, r.contrast)]
        f = []
        if r.contrast in ("P1", "P2", "P3") and bool(r.reject_holm) != bool(b.reject_holm): f.append("HOLM DECISION CHANGES")
        if r.contrast in ("P1", "P2", "P3") and ((r.ci_low <= 0 <= r.ci_high) != (b.ci_low <= 0 <= b.ci_high)): f.append("CI-vs-0 changes")
        if abs(r.estimate - b.estimate) >= .05: f.append(f"shift {100*(r.estimate-b.estimate):+.1f} pp")
        return "; ".join(f)
    P["flag"] = P.apply(flag, axis=1); P.to_csv(OUT / "primary_contrasts_by_variant.csv", index=False)
    # stored checks
    wc = json.load(open(ROOT / "analysis/r2c/headline.json")); hw = pd.read_csv(ROOT / "analysis/hw1/primary_contrasts.csv"); hw = hw[hw.cluster == "writer"].set_index("contrast")
    b = P[P.variant.eq("base")]
    chk = {"W-C_P1_stored": [wc.get("p1"), wc.get("p1_ci_low"), wc.get("p1_ci_high")], "W-C_P1_here": b[(b.run == "W-C r2c1") & (b.contrast == "P1")][["estimate", "ci_low", "ci_high"]].values.tolist(),
           "hw1_P1_stored": hw.loc["P1", ["estimate", "ci_low", "ci_high"]].tolist(), "hw1_P1_here": b[(b.run == "hw1") & (b.contrast == "P1")][["estimate", "ci_low", "ci_high"]].values.tolist(),
           "W-C_P2_stored": [wc.get("p2"), wc.get("p2_ci_low"), wc.get("p2_ci_high")], "W-C_P2_here": b[(b.run == "W-C r2c1") & (b.contrast == "P2")][["estimate", "ci_low", "ci_high"]].values.tolist(),
           "hw1_P2_stored": hw.loc["P2", ["estimate", "ci_low", "ci_high"]].tolist(), "hw1_P2_here": b[(b.run == "hw1") & (b.contrast == "P2")][["estimate", "ci_low", "ci_high"]].values.tolist()}
    out["baseline_reproduction"] = chk
    out["any_holm_decision_change"] = P[P.flag.str.contains("HOLM", na=False)][["run", "variant", "contrast", "estimate", "flag"]].to_dict("records")
    out["max_abs_shift_pp"] = {c: float(100 * (P[(P.contrast == c)].groupby("run").apply(lambda g: (g.estimate - g[g.variant.eq("base")].estimate.iloc[0]).abs().max())).max()) for c in ("P1", "P2", "P3")}
    gb = G[G.variant.eq("base")].set_index(["run", "dimension"])
    G["shift_pp"] = [100 * (r.estimate - gb.loc[(r.run, r.dimension)].estimate) for r in G.itertuples()]; G.to_csv(OUT / "chip_gain_by_variant.csv", index=False)
    sa = G[G.dimension.eq("speech_act")]
    out["speech_act_chip_gain"] = sa[["run", "variant", "estimate", "ci_low", "ci_high", "shift_pp"]].to_dict("records")
    write_json(OUT / "summary.json", out)
    report(P, G, E, out)


def fmt(r): return f"{100*r.estimate:+.1f} [{100*r.ci_low:+.1f}, {100*r.ci_high:+.1f}]"


def report(P, G, E, out):
    L = ["# T4: codebook sensitivity re-scoring (stored labels only; 0 generation / 0 judge calls)", "",
         "Script `src/robust_t4_codebook.py`. Tables: `primary_contrasts_by_variant.csv`, `chip_gain_by_variant.csv` (all six dimensions for hw1, three for W-C), `elic1_by_variant.csv`. "
         "Estimators reproduce analysis/r2c and analysis/hw1 (cluster bootstrap, 10,000 resamples, seed 20261031; clusters: W-C `cluster_id`, hw1 `writer_id`).", "",
         "Variants: (a) 'Can you / Could you ...?' coded question (a2: only without 'please'); (b) 'I want/need X, please' coded statement; (c) drop the arbitrated units of one precedent class at a time "
         "(tags assigned from the stored arbiter rationale, output text and dimension; D-016/D-055/D-057 and the W-C arbitration); (d) drop all arbitrated units. A remapped row keeps every other column; a masked row leaves the denominator.", "",
         "Baseline reproduction (stored vs recomputed): " + json.dumps(out["baseline_reproduction"]), ""]
    for run in ("W-C r2c1", "hw1"):
        L += [f"## {run}", "", f"Arbiter units: {out[run]['arbiter_units']}; tags: {json.dumps(out[run]['tags'])}", "",
              "| variant | rows changed | P1 chip1-noncrit pp [CI] | P2 pp [CI] | P3 bare affirmative share % [CI] | Holm P1/P2/P3 | flags |", "|---|---|---|---|---|---|---|"]
        for v in P[P.run.eq(run)].variant.unique():
            g = P[(P.run == run) & (P.variant == v)].set_index("contrast")
            sh = g.loc["P3_affirmative_share"]
            L.append(f"| {v} | {int(g.rows_changed.iloc[0])} | {fmt(g.loc['P1'])} | {fmt(g.loc['P2'])} | {100*sh.estimate:.2f} [{100*sh.ci_low:.2f}, {100*sh.ci_high:.2f}] | "
                     f"{'/'.join('Y' if g.loc[k].reject_holm else 'N' for k in ('P1','P2','P3'))} | {'; '.join(x for x in g.flag.dropna() if x and x != '')} |")
        L.append("")
        gg = G[(G.run == run)]
        L += [f"### {run}: chip gain (chip1 - noncrit critical match), pp, by dimension; speech act = P1", "",
              "| variant | " + " | ".join(sorted(gg.dimension.unique())) + " |", "|---|" + "---|" * gg.dimension.nunique()]
        for v in gg.variant.unique():
            x = gg[gg.variant == v].set_index("dimension")
            L.append(f"| {v} | " + " | ".join(f"{100*x.loc[d].estimate:+.1f}" for d in sorted(x.index)) + " |")
        L.append("")
    L += ["## elic1 (descriptive: share of P0 outputs whose focal critical label matches the source; no designed contrast exists)", "",
          "Match rate by dimension and keyword source; a coding change that moves a request/question label moves these. Message-cluster bootstrap, 2,000 resamples.", "",
          md_table(E[E.variant.isin(["base", "a_can_you_question", "b_want_please_statement", "ab", "mask_all_arbitrated"]) & E.dimension.str.startswith("speech_act")].round(3)), "",
          f"elic1 arbiter units: {out['elic1']['arbiter_units']}, tags {json.dumps(out['elic1']['tags'])}. Per-tag masks are in `elic1_by_variant.csv`.", ""]
    L += ["## Holm decisions and maximum shifts", "", f"Decision changes: {json.dumps(out['any_holm_decision_change'])}", f"Max absolute shift of any estimate over all variants (pp): {json.dumps(out['max_abs_shift_pp'])}", "",
          "## Caveats", "",
          "* Remapping is by output-text pattern on the final stored label; it cannot tell whether an annotator trained on the alternative rule would label differently in other respects (e.g. 'Can you ... please?').",
          "* Tags are assigned by rule from rationale text (declared in `tag_unit`); 'other' classes are small and heterogeneous.",
          "* Masking an arbitrated unit removes every occurrence of that output text (same text_id), so the denominator shrinks; this is the same operation as the W-C 'unknown_masked' sensitivity.",
          "* 'rows changed' counts stored rows of every prompt and channel (P0, P2, S3), not only the P0 rows entering P1-P3.",
          "* Reading: (a) is the only variant that moves a registered contrast materially (W-C P1 falls by about 13 pp, hw1 P1 by about 3 pp; both stay Holm-significant). Under (a) a chip-ASK request that the model words 'Can you ...?' stops counting as honoured, so the chip gain shrinks.",
          "* P2 (politeness) and P3 (polarity) do not depend on speech-act coding, so (a), (b) leave them unchanged by construction; the stored politeness 'Can you = plain' rule is not varied here."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
