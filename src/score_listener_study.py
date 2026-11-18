"""Score the Part 28 listener communication study. Rules (frozen before any return): analysis/listener/PLAN.md sections 3 to 6 and
annotation/COORDINATOR_STEPS.md section 7.

  python src/score_listener_study.py --self-check              # synthetic listeners on the real key; no private file is changed; scratch in tmp/
  python src/score_listener_study.py [--returns DIR] [--out DIR] [--B 10000]
Inputs: annotation/listener_key.csv (PRIVATE), annotation/returns_part28/labels_part28_<ID>.csv.
Outputs (default analysis/listener_human/): qc.json, by_condition.csv, contrasts.csv, summary.json.
Unit of analysis is the judgment; a judge unit (one sentence, identical text merged across conditions) is expanded to one judgment per condition it stands for.
Condition means are item-balanced (mean over items of the item's mean over its judgments). Two-way cluster bootstrap: items and listeners resampled
independently with replacement, judgments kept with multiplicity when both their item and listener are drawn. Missing answers are never imputed.
Listeners are adult non-author annotators, not AAC communication partners; comprehension is not a real-world consequence."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = ROOT / "annotation" / "listener_key.csv"
SEED = 20261117
CONDS = ["bare", "chip1", "nlcue", "G1", "reference"]
METRICS = ["success", "reversal", "unclear", "conseq", "conseq_sens", "slp_reversal"]
DIMS = ["polarity", "speech_act", "agent", "time_quantity"]
PRIMARY = [("chip1", "bare"), ("G1", "bare"), ("nlcue", "chip1")]
SECONDARY = [("bare", "reference")]
CONTRAST_METRICS = ["success", "reversal", "slp_reversal", "conseq"]
EQUIV_PP = 5.0
ATTN_MIN = 0.75
COMPLETE_MIN = 0.80


def load_key(path=KEY) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def read_returns(folder: Path) -> pd.DataFrame:
    fs = sorted(Path(folder).glob("labels_part28_*.csv")) if Path(folder).exists() else []
    parts = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in fs]
    return pd.concat(parts, ignore_index=True).fillna("") if parts else pd.DataFrame()


def qc(ret: pd.DataFrame, key: pd.DataFrame):
    rep = {"rows": int(len(ret)), "practice_dropped": 0, "unknown_item": 0, "wrong_annotator": 0, "duplicate": 0, "missing_q1": 0, "invalid_q1": 0,
           "invalid_q2_set_missing": 0, "invalid_q3_set_missing": 0}
    if ret.empty:
        return ret, rep
    ret = ret[ret["practice"].astype(str) != "1"].copy(); rep["practice_dropped"] = rep["rows"] - len(ret)
    ret["annotator"] = ret["annotator"].str.strip().str.upper()
    pair = set(zip(key.item_id, key.annotator))
    unk = ~ret.item_id.isin(set(key.item_id)); rep["unknown_item"] = int(unk.sum()); ret = ret[~unk]
    bad = [(i, a) not in pair for i, a in zip(ret.item_id, ret.annotator)]; rep["wrong_annotator"] = int(sum(bad)); ret = ret[~np.array(bad, dtype=bool)] if len(ret) else ret
    dup = ret.duplicated(["item_id", "annotator"], keep="last"); rep["duplicate"] = int(dup.sum()); ret = ret[~dup]     # later export wins
    miss = ret["q1"] == ""; rep["missing_q1"] = int(miss.sum()); ret = ret[~miss]
    inv = ~ret["q1"].isin(["reading 1", "reading 2", "unclear"]); rep["invalid_q1"] = int(inv.sum()); ret = ret[~inv].copy()
    q2bad = ~ret["q2"].isin([f"action {i}" for i in range(1, 5)]); rep["invalid_q2_set_missing"] = int(q2bad.sum()); ret.loc[q2bad, "q2"] = ""
    q3bad = ~ret["q3"].isin(["1", "2", "3"]); rep["invalid_q3_set_missing"] = int(q3bad.sum()); ret.loc[q3bad, "q3"] = ""
    return ret, rep


def decode(ret: pd.DataFrame, key: pd.DataFrame) -> pd.DataFrame:
    """One row per answered unit judgment with the reading and response roles decoded from the private key."""
    k = key.set_index(["item_id", "annotator"])
    out = []
    for r in ret.itertuples():
        kr = k.loc[(r.item_id, r.annotator)]
        r1 = kr["reading1"]; r2 = "B" if r1 == "A" else "A"
        pick = {"reading 1": r1, "reading 2": r2, "unclear": "unclear"}[r.q1]
        intended = kr["intended_reading"]
        roles = kr["q2_roles"].split("|")
        role = roles[int(r.q2.split()[1]) - 1] if r.q2 else None
        out.append({"item_id": r.item_id, "annotator": r.annotator, "item": kr["item"], "conds": kr["conditions"].split(";"), "dimension": kr["dimension"],
                    "nondefault": kr["nondefault"] == "True", "hw_file": kr["hw_file"], "model": kr["model"], "slp_w": float(kr["slp_weight"]),
                    "success": float(pick == intended), "reversal": float(pick not in (intended, "unclear")), "unclear": float(pick == "unclear"),
                    "conseq": np.nan if role is None else float(role == "opposite"),
                    "conseq_sens": np.nan if role is None else float(role not in ("correct", "clarify")),
                    "q3": float(r.q3) if r.q3 else np.nan})
    return pd.DataFrame(out)


def exclusions(dec: pd.DataFrame, key: pd.DataFrame, attn=ATTN_MIN, comp=COMPLETE_MIN):
    """Listener exclusions of PLAN section 6: reference success below 75%, or fewer than 80% of assigned judgments answered."""
    assigned = key.groupby("annotator").size()
    done = dec.groupby("annotator").size().reindex(assigned.index).fillna(0)
    ref = dec[dec.conds.apply(lambda c: "reference" in c)]
    rs = ref.groupby("annotator").success.agg(["mean", "size"])
    low_attn = sorted(a for a in rs.index if rs.loc[a, "mean"] < attn)
    low_comp = sorted(a for a in assigned.index if done[a] < comp * assigned[a])
    return {"low_attention": low_attn, "low_completion": low_comp, "excluded": sorted(set(low_attn) | set(low_comp)),
            "reference_success": {a: round(float(rs.loc[a, "mean"]), 3) for a in rs.index},
            "completion": {a: round(float(done[a] / assigned[a]), 3) for a in assigned.index}}


def expand(dec: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in dec.itertuples(index=False):
        for c in r.conds:
            d = r._asdict(); d["cond"] = c; rows.append(d)
    x = pd.DataFrame(rows).drop(columns="conds")
    x["slp_reversal"] = x["slp_w"] * x["reversal"]
    return x


class Design:
    """Index structures for the item-balanced estimator and its two-way cluster bootstrap."""

    def __init__(self, x: pd.DataFrame):
        self.x = x.reset_index(drop=True)
        self.items = sorted(self.x["item"].unique()); self.lis = sorted(self.x["annotator"].unique())
        ii = {v: i for i, v in enumerate(self.items)}; li = {v: i for i, v in enumerate(self.lis)}
        self.ji = self.x["item"].map(ii).to_numpy(); self.jl = self.x["annotator"].map(li).to_numpy()
        g = self.x[["cond", "item"]].drop_duplicates().reset_index(drop=True)
        self.groups = g
        gi = {(c, i): n for n, (c, i) in enumerate(zip(g.cond, g["item"]))}
        self.jg = np.array([gi[(c, i)] for c, i in zip(self.x.cond, self.x["item"])])
        self.gitem = g["item"].map(ii).to_numpy()
        meta = self.x.drop_duplicates("item").set_index("item")
        self.item_nd = np.array([bool(meta.loc[i, "nondefault"]) for i in self.items]); self.item_dim = np.array([meta.loc[i, "dimension"] for i in self.items])
        self.item_file = np.array([meta.loc[i, "hw_file"] for i in self.items])
        self.Y = {m: self.x[m].to_numpy(float) for m in METRICS}
        # summary cells: (cond, subset) -> indicator over groups
        self.subsets = {"all": np.ones(len(self.items), bool), "nondefault": self.item_nd, "default": ~self.item_nd,
                        **{f"dim:{d}": self.item_dim == d for d in DIMS}}
        self.cells = [(c, s) for c in CONDS for s in self.subsets]
        self.M = np.zeros((len(self.cells), len(g)))
        for n, (c, s) in enumerate(self.cells):
            self.M[n] = ((g.cond == c).to_numpy() & self.subsets[s][self.gitem]).astype(float)
        # paired items for each contrast
        self.pairs = {}
        for a, b in PRIMARY + SECONDARY:
            ga = {i: n for n, (c, i) in enumerate(zip(g.cond, g["item"])) if c == a}; gb = {i: n for n, (c, i) in enumerate(zip(g.cond, g["item"])) if c == b}
            both = sorted(set(ga) & set(gb))
            self.pairs[(a, b)] = (np.array([ga[i] for i in both], int), np.array([gb[i] for i in both], int), np.array([ii[i] for i in both], int))

    def group_means(self, wl):
        out = {}
        w = wl[self.jl]
        for m in METRICS:
            y = self.Y[m]; ok = ~np.isnan(y)
            num = np.bincount(self.jg, weights=w * np.where(ok, y, 0), minlength=len(self.groups)); den = np.bincount(self.jg, weights=w * ok, minlength=len(self.groups))
            out[m] = (np.where(den > 0, num / np.maximum(den, 1e-12), np.nan), den)
        return out

    def estimate(self, wi, wl):
        gm = self.group_means(wl); wg = wi[self.gitem]
        cell, contr = {}, {}
        for m in METRICS:
            mean, den = gm[m]; d = (den > 0) & (wg > 0)
            num = self.M @ np.where(d, wg * np.nan_to_num(mean), 0); dd = self.M @ np.where(d, wg, 0)
            cell[m] = np.where(dd > 0, num / np.maximum(dd, 1e-12), np.nan)
        for (a, b), (ga, gb, it) in self.pairs.items():
            for m in CONTRAST_METRICS:
                mean, den = gm[m]; ok = (den[ga] > 0) & (den[gb] > 0) & (wi[it] > 0)
                contr[(a, b, m)] = float((wi[it][ok] * (mean[ga][ok] - mean[gb][ok])).sum() / wi[it][ok].sum()) if ok.any() else np.nan
        return cell, contr


def analyse(x: pd.DataFrame, B=10000, seed=SEED):
    D = Design(x)
    cell0, contr0 = D.estimate(np.ones(len(D.items)), np.ones(len(D.lis)))
    rng = np.random.default_rng(seed)
    cells = {m: np.full((B, len(D.cells)), np.nan) for m in METRICS}; cons = {k: np.full(B, np.nan) for k in contr0}
    for b in range(B):
        wi = np.bincount(rng.integers(0, len(D.items), len(D.items)), minlength=len(D.items)).astype(float)
        wl = np.bincount(rng.integers(0, len(D.lis), len(D.lis)), minlength=len(D.lis)).astype(float)
        c, k = D.estimate(wi, wl)
        for m in METRICS:
            cells[m][b] = c[m]
        for kk, v in k.items():
            cons[kk][b] = v
    return D, cell0, contr0, cells, cons


def pct(v, q):
    v = v[~np.isnan(v)]
    return float(np.percentile(v, q)) if len(v) else float("nan")


def tables(D, cell0, contr0, cells, cons, x):
    rows = []
    for n, (c, s) in enumerate(D.cells):
        sel = (x.cond == c)
        if s != "all":
            sel &= (x.nondefault if s == "nondefault" else ~x.nondefault if s == "default" else x.dimension == s[4:])
        nj, ni = int(sel.sum()), int(x[sel]["item"].nunique())
        for m in METRICS:
            e = cell0[m][n]
            if np.isnan(e):
                continue
            scale = 1000 if m in ("reversal", "slp_reversal") else 100
            rows.append({"metric": m, "cond": c, "subset": s, "estimate": round(float(e) * scale, 2), "lo": round(pct(cells[m][:, n], 2.5) * scale, 2),
                         "hi": round(pct(cells[m][:, n], 97.5) * scale, 2), "unit": "per 1000" if scale == 1000 else "pp", "n_judgments": nj, "n_items": ni})
    # Holm-adjusted intervals for the three primary contrasts on success: order by bootstrap p, level alpha/(3-rank)
    pv = {}
    for a, b in PRIMARY:
        v = cons[(a, b, "success")]; v = v[~np.isnan(v)]
        pv[(a, b)] = 2 * min((v <= 0).mean(), (v >= 0).mean()) if len(v) else np.nan
    order = sorted(PRIMARY, key=lambda t: (np.inf if np.isnan(pv[t]) else pv[t]))
    alpha = {t: 0.05 / (len(PRIMARY) - i) for i, t in enumerate(order)}
    crow = []
    for (a, b) in PRIMARY + SECONDARY:
        ga, gb, it = D.pairs[(a, b)]
        for m in CONTRAST_METRICS:
            v = cons[(a, b, m)]; e = contr0[(a, b, m)]
            if np.isnan(e):
                continue
            scale = 1000 if m in ("reversal", "slp_reversal") else 100
            r = {"contrast": f"{a} - {b}", "metric": m, "primary": (a, b) in PRIMARY and m == "success", "n_items": int(len(it)), "estimate": round(e * scale, 2),
                 "lo": round(pct(v, 2.5) * scale, 2), "hi": round(pct(v, 97.5) * scale, 2), "unit": "per 1000" if scale == 1000 else "pp"}
            if r["primary"]:
                al = alpha[(a, b)]
                r.update(p_boot=round(float(pv[(a, b)]), 4), lo_holm=round(pct(v, 100 * al / 2) * scale, 2), hi_holm=round(pct(v, 100 * (1 - al / 2)) * scale, 2),
                         holm_alpha=round(al, 4))
                if (a, b) == ("nlcue", "chip1"):
                    lo90, hi90 = pct(v, 5) * 100, pct(v, 95) * 100
                    r.update(lo90=round(lo90, 2), hi90=round(hi90, 2), equivalent_pm5pp=bool(lo90 > -EQUIV_PP and hi90 < EQUIV_PP))
            crow.append(r)
    return pd.DataFrame(rows), pd.DataFrame(crow)


def run(returns: Path, out: Path, B=10000, key_path=KEY):
    key = load_key(key_path)
    ret, rep = qc(read_returns(returns), key)
    res = {"qc": rep, "n_key_rows": int(len(key)), "n_listeners_assigned": int(key.annotator.nunique())}
    out.mkdir(parents=True, exist_ok=True)
    if ret.empty:
        (out / "qc.json").write_text(json.dumps(res, indent=1)); return {"res": res}
    dec = decode(ret, key)
    ex = exclusions(dec, key)
    res["exclusions"] = {k: ex[k] for k in ("low_attention", "low_completion", "excluded")}
    keep = dec[~dec.annotator.isin(ex["excluded"])]
    res["n_listeners_used"] = int(keep.annotator.nunique()); res["n_unit_judgments_used"] = int(len(keep))
    res["underpowered"] = bool(res["n_listeners_used"] < 16)
    x = expand(keep)
    D, c0, k0, cells, cons = analyse(x, B)
    bytab, ctab = tables(D, c0, k0, cells, cons, x)
    bytab.to_csv(out / "by_condition.csv", index=False); ctab.to_csv(out / "contrasts.csv", index=False)
    # sensitivity: nobody excluded
    xs = expand(dec); Ds, c0s, k0s, cells_s, cons_s = analyse(xs, max(200, B // 5))
    _, ctab_s = tables(Ds, c0s, k0s, cells_s, cons_s, xs); ctab_s.to_csv(out / "contrasts_no_exclusion.csv", index=False)
    ceil = bytab[(bytab.metric == "success") & (bytab.cond == "reference") & (bytab.subset == "all")]
    res["reference_ceiling_pp"] = None if ceil.empty else float(ceil.estimate.iloc[0])
    def g(m, c, s="all"):
        r = bytab[(bytab.metric == m) & (bytab.cond == c) & (bytab.subset == s)]
        return None if r.empty else float(r.estimate.iloc[0])
    res["headline_inputs"] = {"reversal_per_1000_bare": g("reversal", "bare"), "reversal_per_1000_chip1": g("reversal", "chip1"),
                              "reversal_per_1000_bare_nondefault": g("reversal", "bare", "nondefault"), "reversal_per_1000_chip1_nondefault": g("reversal", "chip1", "nondefault"),
                              "design_note": "50% of the intended messages are non-default by design; the headline states this mix"}
    res["mixed_model_sensitivity"] = "not run: statsmodels is not installed in the project environment; the cluster bootstrap stands alone (PLAN section 5)"
    res["nlcue_scope"] = "nlcue contrasts use only items that have a plain-word output (hw1 items)"
    (out / "qc.json").write_text(json.dumps(res, indent=1)); (out / "summary.json").write_text(json.dumps({"qc": res, "contrasts": ctab.to_dict("records")}, indent=1, default=str))
    return {"res": res, "by": bytab, "contrasts": ctab, "dec": dec, "x": x}


# ------------------------------------------------------------------ self-check
def synthetic(key: pd.DataFrame, probs, seed=11, careless=(), partial=None):
    """Planted listeners on the real key. probs: condition -> (P success, P reversal | not success, P clarify | q2). Careless listeners answer at random."""
    rng = np.random.default_rng(seed)
    rows = []
    for r in key.itertuples():
        conds = r.conditions.split(";")
        c = conds[0]
        ps, pr = probs[c]
        r1 = r.reading1; intended = r.intended_reading; other = "B" if intended == "A" else "A"
        if r.annotator in careless:
            pick = rng.choice([intended, other, "unclear"])
        else:
            u = rng.random()
            pick = intended if u < ps else (other if u < ps + (1 - ps) * pr else "unclear")
        q1 = "unclear" if pick == "unclear" else ("reading 1" if pick == r1 else "reading 2")
        roles = r.q2_roles.split("|")
        role = {intended: "correct", other: "opposite", "unclear": "clarify"}[pick] if r.annotator not in careless else rng.choice(roles)
        q2 = f"action {roles.index(role) + 1}"
        rows.append({"item_id": r.item_id, "annotator": r.annotator, "check_id": "part28", "practice": "0", "order": "1", "q1": q1, "q2": q2, "q3": str(int(rng.integers(1, 4))),
                     "note": "", "time_ms": "9000", "_conds": r.conditions, "_pick": pick})
    df = pd.DataFrame(rows)
    if partial:
        for a, frac in partial.items():
            idx = df.index[df.annotator == a]; df = df.drop(idx[int(len(idx) * frac):])
    return df


def self_check(B=300):
    key = load_key()
    scratch = ROOT / "tmp" / "s7_listener_selfcheck"; shutil.rmtree(scratch, ignore_errors=True); scratch.mkdir(parents=True)
    fails = []
    def ok(c, m):
        print(("ok   " if c else "FAIL ") + m)
        if not c:
            fails.append(m)
    try:
        ok(key.annotator.nunique() == 20 and key.item_id.nunique() == 423, "key: 20 listeners, 423 judge units")
        ok((key.groupby("item_id").annotator.nunique() == 2).all(), "key: every judge unit has exactly 2 different listeners")
        ok(key.groupby(["annotator", "item"]).size().max() == 1, "key: no listener sees one intended message in more than one unit (Latin square)")
        ok(key.item.nunique() == 120 and key.groupby("item").family_id.nunique().max() == 1, "key: 120 intended messages, one family each")
        ok(abs(key.groupby("annotator").size().max() - key.groupby("annotator").size().min()) <= 1, "key: listener loads differ by at most one judgment")
        # synthetic listeners with known success rates
        probs = {"reference": (0.96, 0.5), "bare": (0.55, 0.7), "chip1": (0.88, 0.5), "G1": (0.55, 0.7), "nlcue": (0.86, 0.5)}
        s = synthetic(key, probs, careless={"P05"}, partial={"P07": 0.5})
        d = scratch / "ret"; d.mkdir()
        for a, g in s.groupby("annotator"):
            g.drop(columns=["_conds", "_pick"]).to_csv(d / f"labels_part28_{a}.csv", index=False)
        # QC: practice rows, duplicates, another person's unit
        x = pd.read_csv(d / "labels_part28_P01.csv", dtype=str, keep_default_na=False)
        x2 = pd.concat([x, x.iloc[:2], x.iloc[:1].assign(practice="1"), x.iloc[:1].assign(annotator="P02")])
        y, rep = qc(x2, key)
        ok(rep["practice_dropped"] == 1 and rep["duplicate"] == 2 and rep["wrong_annotator"] == 1 and len(y) == len(x), f"qc: practice, duplicates and another listener's item handled {rep}")
        o = scratch / "out"
        a = run(d, o, B)
        res = a["res"]
        ok(res["exclusions"]["low_attention"] == ["P05"] and "P07" in res["exclusions"]["low_completion"], f"exclusions: careless listener (attention) and half-complete listener removed {res['exclusions']}")
        by, ct = a["by"], a["contrasts"]
        def est(m, c, sub="all"):
            return float(by[(by.metric == m) & (by.cond == c) & (by.subset == sub)].estimate.iloc[0])
        ok(abs(est("success", "reference") - 96) < 5 and abs(est("success", "bare") - 55) < 8 and abs(est("success", "chip1") - 88) < 6, "scoring: recovers the planted success rates (reference 96, bare 55, chip1 88)")
        ok(abs(est("reversal", "bare") - 1000 * 0.45 * 0.7) < 110, f"scoring: reversal per 1000 for bare near the planted {1000*0.45*0.7:.0f} ({est('reversal', 'bare'):.0f})")
        c = ct[(ct.primary)]
        ok(len(c) == 3 and set(c.contrast) == {"chip1 - bare", "G1 - bare", "nlcue - chip1"}, "scoring: three declared primary contrasts")
        cb = c[c.contrast == "chip1 - bare"].iloc[0]; cg = c[c.contrast == "G1 - bare"].iloc[0]
        ok(cb.lo > 15 and abs(cg.estimate) < 10, f"scoring: chip1 - bare large and positive ({cb.estimate}), G1 - bare near zero ({cg.estimate})")
        ok(c.lo_holm.le(c.lo).all() and c.hi_holm.ge(c.hi).all(), "scoring: Holm-adjusted intervals are at least as wide as the unadjusted ones")
        ok(bool(c[c.contrast == "nlcue - chip1"].iloc[0].equivalent_pm5pp) in (True, False), "scoring: equivalence flag from the 90% interval is reported")
        # a perfect listener pool: everyone reads the intended message; reference ceiling 100, reversal 0
        s2 = synthetic(key, {k: (1.0, 0.0) for k in probs}); d2 = scratch / "ret2"; d2.mkdir()
        for a_, g in s2.groupby("annotator"):
            g.drop(columns=["_conds", "_pick"]).to_csv(d2 / f"labels_part28_{a_}.csv", index=False)
        a2 = run(d2, scratch / "out2", 100)
        ok(a2["res"]["reference_ceiling_pp"] == 100 and a2["res"]["headline_inputs"]["reversal_per_1000_bare"] == 0, "scoring: perfect listeners give ceiling 100 and zero reversals")
        # the decoder reads the key correctly: every success row decodes to the intended reading
        dec = decode(qc(read_returns(d2), key)[0], key)
        ok((dec.success == 1).all() and (dec.conseq == 0).all(), "decode: planted correct answers decode to success and a correct (not opposite) response")
        ok(a["res"]["underpowered"] is False, "scoring: 18 usable listeners are not flagged underpowered")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print("SELF-CHECK", "PASSED" if not fails else f"FAILED ({len(fails)})")
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--returns", default=str(ROOT / "annotation" / "returns_part28"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "listener_human"))
    ap.add_argument("--B", type=int, default=10000)
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    r = run(Path(a.returns), Path(a.out), a.B)
    print(json.dumps(r["res"], indent=1, default=str)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
