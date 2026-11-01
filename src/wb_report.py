"""W-B analysis: defaults on confirmed-ambiguous dims, violations on supplied commitments,
focal-cue restoration effect. Random and enriched samples are reported separately.

Inputs: runs/wb1/scored.parquet (attribute.py), annotation/wb_admissibility/panel.jsonl +
agreement.json, data/items/wb.jsonl. All CIs are percentile bootstraps over MESSAGES
(cluster = message; 2000 reps, seed 20261101), resampled within the sample type.

Unit definitions (output = one P0 generation of one model for one channel of one message):
  general value of an output on dim d = judge label (J1==J2, else layer0 tiebreak, else NA).
  honours(d, source, out): equality, except certainty plain <- {plain, emphatic} (D-007) and
  politeness polite source <- any polite marker (SPEC [PLEASE]).
A. defaults: POS-cap4 outputs on (message, d) with panel status confirmed_ambiguous.
   committed = out value not in {mixed/unclear, unspecified, other}; also reports the share
   taking the unmarked default value, share honouring the source, share outside BOTH coders'
   admissible reading sets.
B. violations: (message, d) whose source value is a panel consensus, not mixed/unclear/other
   ("expressible"), and supplied (POS-cap4: both coders: single admissible reading == source;
   restored: focal d; full: every consensus d). violation = out does not honour source.
C. restoration: focal critical dim, critical_match from attribute.py (J1==J2 critical only;
   J1-fallback sensitivity), restored - POS-cap4 paired by (message, model); full as ceiling.

  python src/wb_report.py      # -> analysis/wb/report.md + analysis/wb/*.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/wb"
DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness"]
NONCOMMIT = {"mixed/unclear", "unclear/mixed", "unspecified", "other"}
DEFAULT = {"polarity": "affirmative", "speech_act": "statement", "agent": "speaker",
           "certainty": "plain assertion", "politeness": "none"}
POLITE = {"please", "softened request (could you/would you mind)", "thanks/apology"}
B = 2000
RNG = np.random.default_rng(20261101)


def honours(d, src, out):
    if out is None or src is None or (isinstance(out, float) and np.isnan(out)):
        return None
    if d == "certainty" and src == "plain assertion":
        return out in ("plain assertion", "strongly certain/emphatic")
    if d == "politeness" and src in POLITE:
        return out in POLITE
    return out == src


def boot(df, col, cluster="msg"):
    """Mean of boolean col with message-cluster bootstrap CI. Returns (k, n, est, lo, hi, n_msgs)."""
    d = df.dropna(subset=[col])
    if d.empty:
        return dict(k=0, n=0, est=None, lo=None, hi=None, msgs=0)
    g = d.groupby(cluster)[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    est = s.sum() / c.sum()
    idx = RNG.integers(0, len(g), size=(B, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return dict(k=int(s.sum()), n=int(c.sum()), est=est, lo=float(np.percentile(bs, 2.5)),
                hi=float(np.percentile(bs, 97.5)), msgs=len(g))


def boot_diff(df, a, b, cluster="msg"):
    """Paired difference mean(a) - mean(b) over rows with both, message-cluster bootstrap."""
    d = df.dropna(subset=[a, b])
    if d.empty:
        return dict(n=0, est=None, lo=None, hi=None, msgs=0)
    g = d.groupby(cluster).agg(sa=(a, "sum"), sb=(b, "sum"), c=(a, "count"))
    sa, sb, c = (g[k].to_numpy(float) for k in ("sa", "sb", "c"))
    est = (sa.sum() - sb.sum()) / c.sum()
    idx = RNG.integers(0, len(g), size=(B, len(g)))
    bs = (sa[idx].sum(1) - sb[idx].sum(1)) / c[idx].sum(1)
    return dict(n=int(c.sum()), est=est, lo=float(np.percentile(bs, 2.5)),
                hi=float(np.percentile(bs, 97.5)), msgs=len(g))


def fmt(r, pct=True):
    if r.get("est") is None:
        return "n/a (0)"
    f = (lambda x: f"{100 * x:.1f}") if pct else (lambda x: f"{x:+.3f}")
    if "k" in r:
        return f"{r['k']}/{r['n']} = {f(r['est'])}% [{f(r['lo'])}, {f(r['hi'])}] ({r['msgs']} msgs)"
    return f"{100 * r['est']:+.1f} pp [{100 * r['lo']:+.1f}, {100 * r['hi']:+.1f}] (n={r['n']} pairs, {r['msgs']} msgs)"


def load():
    items = {json.loads(l)["family_id"]: json.loads(l) for l in (ROOT / "data/items/wb.jsonl").open()}
    panel = {p["id"]: p for p in map(json.loads, (ROOT / "annotation/wb_admissibility/panel.jsonl").open())}
    sc = pd.read_parquet(ROOT / "runs/wb1/scored.parquet")
    sc = sc[sc["family_id"].isin(items)].copy()
    fbp = ROOT / "runs/wb1/scored_fallbackJ1.parquet"
    if fbp.exists():   # attribute.py --fallback J1, copied aside (sensitivity)
        fb = pd.read_parquet(fbp)[["output_id", "family_id", "channel", "critical_match"]]
        fb = fb.dropna(subset=["output_id"]).drop_duplicates(["output_id", "family_id", "channel"])
        sc = sc.merge(fb.rename(columns={"critical_match": "critical_match_fb"}),
                      on=["output_id", "family_id", "channel"], how="left")
    sc["msg"] = sc["family_id"]
    sc["sample"] = sc["family_id"].map(lambda f: items[f]["sample"])
    sc["stratum"] = sc["family_id"].map(lambda f: items[f]["stratum"])
    return items, panel, sc


def long_dims(sc, items, panel):
    """One row per (output occurrence, dim) with panel status + honours."""
    rows = []
    for r in sc.itertuples(index=False):
        it = items[r.family_id]
        p = panel[it["source_id"]]
        for d in DIMS:
            e = p["dims"][d]
            out = getattr(r, d)
            out = None if out is None or (isinstance(out, float) and np.isnan(out)) else out
            src = e["source_value"]
            rows.append(dict(msg=r.family_id, sample=r.sample, stratum=r.stratum, model=r.model,
                             channel=r.channel, valid=r.valid, dim=d, status=e["status"],
                             status_strict=e.get("status_strict"),
                             src=src, out=out, focal=it["focal_dim"] == d,
                             admissible_union=set(e["values_1"]) | set(e["values_2"]),
                             expressible=src is not None and src not in NONCOMMIT))
    L = pd.DataFrame(rows)
    L["honour"] = [honours(d, s, o) if o is not None and s is not None else None
                   for d, s, o in zip(L["dim"], L["src"], L["out"])]
    L["violation"] = L["honour"].map(lambda h: None if h is None else (not h))
    L["committed"] = L["out"].map(lambda o: None if o is None else o not in NONCOMMIT)
    L["takes_default"] = [None if o is None else o == DEFAULT[d] for d, o in zip(L["dim"], L["out"])]
    L["outside_admissible"] = [None if o is None else o not in adm
                               for o, adm in zip(L["out"], L["admissible_union"])]
    return L


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    items, panel, sc = load()
    agr = json.loads((ROOT / "annotation/wb_admissibility/agreement.json").read_text())
    man = json.loads((OUT / "sample_manifest.json").read_text())
    L = long_dims(sc, items, panel)
    md = ["# W-B corpus transfer (AACText): defaults, violations, restoration", "",
          "Generated by `python src/wb_report.py` (run wb1, P0, 4 models). Protocol: orchestration/PREREG_R2.md W-B. "
          "All intervals: 95% percentile bootstrap over messages (2000 reps). Random (SRS, pi = "
          f"{man['pi_random']:.4f}) and enriched (disjoint cue pools, pi in "
          f"{', '.join(f'{k} {v:.3f}' for k, v in man['pi_enriched'].items())}) samples are never pooled.", ""]

    # ---------- sample + denominators
    md += ["## Sample and denominators", "",
           f"Frame: {man['corpus_nonempty']} nonempty AACText lines -> exclusions {man['exclusions']} -> "
           f"N = {man['frame_n']} unique messages. Drawn: {man['n_by_stratum']}. "
           f"Overlap with sample400: {len(man['overlap_sample400'])} ids ({man['overlap_sample400_by_sample']}); "
           "ids listed in analysis/wb/sample_manifest.json.", ""]
    gen = sc.drop_duplicates(["request_key", "family_id", "channel"])
    tab = gen.groupby(["sample", "channel"]).agg(outputs=("valid", "size"), valid=("valid", "sum"),
                                                 critical_resolved=("critical", lambda s: s.notna().sum()))
    md += ["Outputs per sample x channel (one per message x model; invalid = empty/failed generation; "
           "critical_resolved = J1==J2 on the focal critical question):", "", tab.to_markdown(), ""]
    st = (L.drop_duplicates(["msg", "dim"]).groupby(["sample", "dim", "status"]).size()
          .unstack(fill_value=0))
    md += ["Panel status of every (message, dimension), POS-cap4 input (both coders): "
           "confirmed_ambiguous = both list >=2 values; supplied = both list exactly the source value; "
           "coder_disagree = the coders differ; unambiguous_wrong = both unambiguous but not equal to "
           "their source value (or source value disputed). Only the first two are eligible for A/B.", "",
           st.to_markdown(), ""]

    # ---------- panel agreement
    md += ["## Codex panel agreement (source-blind pass 1, source-revealed pass 2)", "",
           f"Coders: {', '.join(agr['models'])}, effort medium, batches of 20, separate sessions per pass.", "",
           "| dim | ambiguous rate c1 / c2 | ambiguous agree (kappa) | confirmed amb n | supplied agree (kappa) | supplied n | source value agree (kappa) |",
           "|---|---|---|---|---|---|---|"]
    for d, a in agr["by_dim"].items():
        md.append(f"| {d} | {a['ambiguous_rate_1']:.2f} / {a['ambiguous_rate_2']:.2f} | {a['ambiguous_agree']:.2f} ({a['ambiguous_kappa']}) | "
                  f"{a['confirmed_ambiguous_n']} | {a['supplied_agree']:.2f} ({a['supplied_kappa']}) | {a['supplied_n']} | "
                  f"{a['source_value_agree']:.2f} ({a['source_value_kappa']}) |")
    md += ["", "Human audit of 20 random messages: annotation/wb_audit.json (not yet returned).", ""]

    csv = []
    # ---------- A. defaults
    md += ["## A. Default commitments on confirmed-ambiguous dimensions (POS-cap4)", "",
           "Rows = POS-cap4 outputs (message x model) on (message, dim) that BOTH coders marked ambiguous. "
           "committed = definite value (not mixed/unclear, unspecified, other); default = the unmarked value "
           "(affirmative / statement / speaker / plain assertion / none); honours source = matches the "
           "panel-consensus source value (rows with disputed source value are dropped from that column only); "
           "outside admissible = a value neither coder listed.", ""]
    A = L[(L["channel"] == "pos_cap4") & (L["status"] == "confirmed_ambiguous")]
    for samp in ("random", "enriched"):
        md += [f"### {samp}", "", "| dim | eligible msgs | committed | takes default | honours source | outside admissible |",
               "|---|---|---|---|---|---|"]
        for d in DIMS + ["ALL"]:
            s = A[(A["sample"] == samp) & ((A["dim"] == d) if d != "ALL" else True)]
            r = {c: boot(s, c) for c in ("committed", "takes_default", "honour", "outside_admissible")}
            nm = s["msg"].nunique()
            md.append(f"| {d} | {nm} | {fmt(r['committed'])} | {fmt(r['takes_default'])} | {fmt(r['honour'])} | {fmt(r['outside_admissible'])} |")
            for c, v in r.items():
                csv.append(dict(analysis="A_default", sample=samp, dim=d, model="pooled", metric=c, **v))
        md.append("")
        dirn = (A[(A["sample"] == samp)].dropna(subset=["out"]).groupby(["dim", "out"]).size()
                .rename("n").reset_index())
        dirn["share"] = dirn["n"] / dirn.groupby("dim")["n"].transform("sum")
        md += [f"Direction (output value distribution) on confirmed-ambiguous dims, {samp}:", "",
               dirn.assign(share=dirn["share"].round(3)).to_markdown(index=False), ""]
        dirn.assign(sample=samp).to_csv(OUT / f"defaults_direction_{samp}.csv", index=False)
        mm = []
        for m, g in A[A["sample"] == samp].groupby("model"):
            mm.append(dict(model=m, takes_default=fmt(boot(g, "takes_default")), honours_source=fmt(boot(g, "honour"))))
        if mm:
            md += [f"By model ({samp}, all dims):", "", pd.DataFrame(mm).to_markdown(index=False), ""]

    # ---------- B. violations
    md += ["## B. Violations of supplied, expressible commitments", "",
           "POS-cap4: (message, dim) supplied per both coders and source value consensus & expressible. "
           "restored: the focal dimension (supplied by the chip/cue word). full: every dim with an "
           "expressible consensus source value (the source supplies all). violation = output does not "
           "honour the source value. Ineligible rows are counted in the status table above.", ""]
    Bv = L[L["expressible"]].copy()
    Bv["eligible"] = ((Bv["channel"] == "full") |
                      ((Bv["channel"] == "pos_cap4") & (Bv["status"] == "supplied")) |
                      ((Bv["channel"] == "restored") & Bv["focal"]))
    Bv = Bv[Bv["eligible"]]
    for samp in ("random", "enriched"):
        md += [f"### {samp}", "", "| dim | POS-cap4 (supplied) | restored (focal) | full |", "|---|---|---|---|"]
        for d in DIMS + ["ALL"]:
            cells = []
            for ch in ("pos_cap4", "restored", "full"):
                s = Bv[(Bv["sample"] == samp) & (Bv["channel"] == ch) & ((Bv["dim"] == d) if d != "ALL" else True)]
                r = boot(s, "violation")
                cells.append(fmt(r))
                csv.append(dict(analysis="B_violation", sample=samp, dim=d, model="pooled", metric=ch, **r))
            md.append(f"| {d} | " + " | ".join(cells) + " |")
        md.append("")
        mm = []
        for m, g in Bv[Bv["sample"] == samp].groupby("model"):
            mm.append(dict(model=m, **{ch: fmt(boot(g[g["channel"] == ch], "violation")) for ch in ("pos_cap4", "restored", "full")}))
        md += [f"By model ({samp}, all dims):", "", pd.DataFrame(mm).to_markdown(index=False), ""]
        ex = Bv[(Bv["sample"] == samp) & (Bv["violation"] == True)]  # noqa: E712
        vc = ex.groupby(["channel", "dim", "src", "out"]).size().rename("n").reset_index().sort_values("n", ascending=False)
        md += [f"Most frequent violation patterns ({samp}):", "", vc.head(12).to_markdown(index=False), ""]

    # ---------- sensitivity: strict (likely-only) admissibility from the graded pass p1g
    if L["status_strict"].notna().any():
        md += ["## Sensitivity: strict admissibility (graded pass p1g, only 'likely' readings count)", "",
               "Same estimands as A and B(POS-cap4) with the panel status recomputed from a separate graded "
               "source-blind pass in which each reading is tagged likely/possible (declared after the primary "
               "pass showed near-ceiling ambiguity, before any judged output was inspected).", ""]
        st2 = (L.drop_duplicates(["msg", "dim"]).groupby(["sample", "dim", "status_strict"]).size()
               .unstack(fill_value=0))
        md += [st2.to_markdown(), ""]
        md += ["| sample | dim | A: eligible msgs | A: takes default | A: honours source | B: POS-cap4 supplied violation |",
               "|---|---|---|---|---|---|"]
        for samp in ("random", "enriched"):
            for d in DIMS + ["ALL"]:
                sel = (L["sample"] == samp) & (L["channel"] == "pos_cap4") & ((L["dim"] == d) if d != "ALL" else True)
                a_ = L[sel & (L["status_strict"] == "confirmed_ambiguous")]
                b_ = L[sel & (L["status_strict"] == "supplied") & L["expressible"]]
                ra, rh, rb = boot(a_, "takes_default"), boot(a_, "honour"), boot(b_, "violation")
                md.append(f"| {samp} | {d} | {a_['msg'].nunique()} | {fmt(ra)} | {fmt(rh)} | {fmt(rb)} |")
                for name, v in (("takes_default", ra), ("honour", rh), ("violation_pos_cap4", rb)):
                    csv.append(dict(analysis="S_strict", sample=samp, dim=d, model="pooled", metric=name, **v))
        md.append("")

    # ---------- C. restoration
    md += ["## C. Focal-cue restoration effect (critical question = focal dimension)", "",
           "Per (message, model): critical_match of the focal critical label (judge J1==J2; disagreements "
           "excluded and counted) for POS-cap4, restored and full. Effect = restored - POS-cap4, paired. "
           "Messages with focal_dim = none (random sample, no lost focal-type cue) have no restored "
           "channel and are ineligible. 'focal ambiguous' restricts to messages whose focal dim is "
           "confirmed ambiguous at POS-cap4.", ""]
    for fb in ("agree", "fallbackJ1"):
        col = "critical_match" if fb == "agree" else "critical_match_fb"
        if fb == "fallbackJ1" and col not in sc:
            continue
        piv = sc.pivot_table(index=["family_id", "model"], columns="channel", values=col, aggfunc="first")
        piv = piv.reset_index()
        piv["msg"] = piv["family_id"]
        piv["sample"] = piv["family_id"].map(lambda f: items[f]["sample"])
        piv["focal"] = piv["family_id"].map(lambda f: items[f]["focal_dim"])
        piv["focal_amb"] = piv["family_id"].map(
            lambda f: items[f]["focal_dim"] != "none" and
            panel[items[f]["source_id"]]["dims"][items[f]["focal_dim"]]["status"] == "confirmed_ambiguous")
        for c in ("pos_cap4", "restored", "full"):
            if c in piv:
                piv[c] = piv[c].map(lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else float(bool(x)))
        md += [f"### critical labels: {'J1==J2 only' if fb == 'agree' else 'J1 fallback on disagreement (sensitivity)'}", "",
               "| sample | subset | focal msgs (ineligible) | POS-cap4 match | restored match | full match | restored - POS-cap4 | full - restored |",
               "|---|---|---|---|---|---|---|---|"]
        for samp in ("random", "enriched"):
            ps = piv[piv["sample"] == samp]
            inel = ps[ps["focal"] == "none"]["msg"].nunique()
            for sub, g in (("all focal", ps[ps["focal"] != "none"]), ("focal ambiguous", ps[ps["focal_amb"]]),
                           *[(f"focal={d}", ps[ps["focal"] == d]) for d in DIMS]):
                if g.empty:
                    continue
                r = [boot(g, c) for c in ("pos_cap4", "restored", "full")]
                d1, d2 = boot_diff(g, "restored", "pos_cap4"), boot_diff(g, "full", "restored")
                md.append(f"| {samp} | {sub} | {g['msg'].nunique()} ({inel if sub == 'all focal' else '-'}) | "
                          + " | ".join(fmt(x) for x in r) + f" | {fmt(d1)} | {fmt(d2)} |")
                for name, v in zip(("pos_cap4", "restored", "full"), r):
                    csv.append(dict(analysis=f"C_restoration_{fb}", sample=samp, dim=sub, model="pooled", metric=name, **v))
                csv.append(dict(analysis=f"C_restoration_{fb}", sample=samp, dim=sub, model="pooled", metric="restored-pos_cap4", **d1))
        md.append("")
        if fb == "agree":
            mm = []
            for (samp, m), g in piv[piv["focal"] != "none"].groupby(["sample", "model"]):
                mm.append(dict(sample=samp, model=m, pos_cap4=fmt(boot(g, "pos_cap4")),
                               restored=fmt(boot(g, "restored")), effect=fmt(boot_diff(g, "restored", "pos_cap4"))))
            md += ["By model:", "", pd.DataFrame(mm).to_markdown(index=False), ""]
    unres = sc[sc["valid"] & sc["critical"].isna()]
    md += [f"Unresolved focal critical labels (J1 != J2): {len(unres)} of {int(sc['valid'].sum())} valid output rows.", ""]
    pd.DataFrame(csv).to_csv(OUT / "estimates.csv", index=False)
    L.drop(columns=["admissible_union"]).to_csv(OUT / "long_dims.csv.gz", index=False)
    (OUT / "report_tables.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
