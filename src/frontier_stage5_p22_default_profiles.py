"""Stage 5 Part 22 (default_profiles human scoring). Rules: annotation/COORDINATOR_STEPS.md section 5 (Part 22), analysis/frontier/default_profiles/ANNOTATION_REQUEST.md + PLAN.md sections 1, 5.
  A. detector vs human validity per stratum (precision/miss, kappa, Wilson, HT + Kish n), human-human kappa, Q3/Q4 vs the lexical gate.
  B. re-run of the exposure / always-commit estimates with human consensus substituted for the detector proxies (class-calibrated, see human.md), message-cluster bootstrap.
    . .venv/bin/activate && python src/frontier_stage5_p22_default_profiles.py   -> analysis/frontier/default_profiles/human_*.csv, human_summary.json"""
import glob, json, sys, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/default_profiles"; B = 2000; rng = np.random.default_rng(20261117)
key = pd.read_csv(ROOT / "annotation/frontier_default_profiles_key.csv")
r = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "annotation/returns_part22/*.csv")))]); r = r[r.practice == 0]
a = pd.read_csv(ROOT / "annotation/assignments/stage5_frontier_assignment.csv"); a = a[a.part == "part22"]
assert set(zip(a.item_id, a.annotator)) == set(zip(r.item_id, r.annotator)) and r.groupby("item_id").size().eq(2).all()
def cons(g, c):
    v = g[c].tolist(); return v[0] if v[0] == v[1] else "NOCONS"
H = pd.DataFrame([dict(item_id=i, **{c: cons(g, c) for c in ("q1", "q2", "q3", "q4")}) for i, g in r.groupby("item_id")]).merge(key, on="item_id")
H["h_nonstmt"] = H.q1.map({"question": 1, "request/command": 1, "statement": 0})            # primary: other / no consensus = NaN (not counted non-statement)
H["h_nonstmt_sens"] = H.q1.map({"question": 1, "request/command": 1, "statement": 0, "other": 1, "NOCONS": 1})   # sensitivity: other (and no consensus) counted as non-statement
H["h_polite"] = H.q2.map({"polite": 1, "not polite": 0}); H["h_polite_sens"] = H.q2.map({"polite": 1, "not polite": 0, "NOCONS": 0})
H["h_q3"] = H.q3.map({"yes": 1, "no": 0}); H["h_q4"] = H.q4.map({"yes": 1, "no": 0})
H.to_csv(OUT / "human_items.csv", index=False)
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, c - h), min(1, c + h)
def kish(w): w = np.asarray(w, float); return w.sum() ** 2 / (w ** 2).sum()
def kappa(x, y):
    x = np.asarray(x); y = np.asarray(y); cats = sorted(set(x) | set(y)); po = (x == y).mean(); pe = sum((x == c).mean() * (y == c).mean() for c in cats); return (po - pe) / (1 - pe) if pe < 1 else np.nan
def wkappa(x, y, w):
    x = np.asarray(x, int); y = np.asarray(y, int); w = np.asarray(w, float) / np.sum(w); po = w[x == y].sum(); px = w[x == 1].sum(); py = w[y == 1].sum(); pe = px * py + (1 - px) * (1 - py); return (po - pe) / (1 - pe)
# ------------------------------------------------ A1. per-stratum rates (detector label is constant within a stratum for the cue that defines it)
rows = []
def rate_row(name, g, col, extra=""):
    ok = g[col].notna(); gg = g[ok]; k = int(gg[col].sum()); n = len(gg); lo, hi = wilson(k, n); w = gg.w.to_numpy(); hw = float(np.average(gg[col], weights=w)) if n else np.nan
    rows.append(dict(set=name, measure=col + extra, k=k, n=n, n_excluded=int((~ok).sum()), share=k / n if n else np.nan, wilson_lo=lo, wilson_hi=hi, ht_share=hw, kish_n=kish(w) if n else np.nan))
for st, g in H.groupby("stratum"):
    for col in ("h_nonstmt", "h_nonstmt_sens", "h_polite", "h_polite_sens"): rate_row(st, g, col)
    rows.append(dict(set=st, measure="Q1 distribution", k=np.nan, n=len(g), note=json.dumps(g.q1.value_counts().to_dict()))); rows.append(dict(set=st, measure="Q2 distribution", k=np.nan, n=len(g), note=json.dumps(g.q2.value_counts().to_dict())))
R1 = pd.DataFrame(rows); R1.to_csv(OUT / "human_validity_rates.csv", index=False)
# precision / miss framing
PR = []
E = H[H.stratum == "E_speech_act"]; C = H[H.stratum == "control"]; P_ = H[H.stratum == "E_politeness"]
for nm, num, den, sens in (("speech act: detector says non-statement; human agrees (PPV)", E, "h_nonstmt", "h_nonstmt_sens"), ("speech act: detector says non-statement (E_politeness stratum, 86% detector nonstmt)", P_[P_.detector_nonstmt], "h_nonstmt", "h_nonstmt_sens")):
    for col in (den, sens): k = int(num[col].sum()); n = int(num[col].notna().sum()); lo, hi = wilson(k, n); PR.append(dict(quantity=nm, version=col, k=k, n=n, est=k / n, lo=lo, hi=hi))
for col in ("h_nonstmt", "h_nonstmt_sens"):
    k = int(C[col].sum()); n = int(C[col].notna().sum()); lo, hi = wilson(k, n); PR.append(dict(quantity="speech act: detector says statement (controls); human says non-statement (miss rate)", version=col, k=k, n=n, est=k / n, lo=lo, hi=hi))
for nm, g in (("politeness: detector says polite (E_politeness); human agrees (PPV)", P_), ("politeness: detector says polite (E_speech_act units, 33% detector polite)", E[E.detector_polite])):
    for col in ("h_polite", "h_polite_sens"): k = int(g[col].sum()); n = int(g[col].notna().sum()); lo, hi = wilson(k, n); PR.append(dict(quantity=nm, version=col, k=k, n=n, est=k / n, lo=lo, hi=hi))
for col in ("h_polite", "h_polite_sens"):
    k = int(C[col].sum()); n = int(C[col].notna().sum()); lo, hi = wilson(k, n); PR.append(dict(quantity="politeness: detector says not polite (controls); human says polite (miss rate)", version=col, k=k, n=n, est=k / n, lo=lo, hi=hi))
Eh = E[~E.detector_polite]; k = int(Eh.h_polite.sum()); n = int(Eh.h_polite.notna().sum()); lo, hi = wilson(k, n); PR.append(dict(quantity="politeness: detector says not polite (E_speech_act units); human says polite", version="h_polite", k=k, n=n, est=k / n, lo=lo, hi=hi))
pd.DataFrame(PR).to_csv(OUT / "human_validity_ppv_miss.csv", index=False)
# pooled kappa detector vs human (all 223 items; strata are targeted draws, so this is descriptive and over-represents positives), HT-weighted and unweighted
KR = []
for dnm, dcol, hcols in (("speech act", "detector_nonstmt", ("h_nonstmt", "h_nonstmt_sens")), ("politeness", "detector_polite", ("h_polite", "h_polite_sens"))):
    for hc in hcols:
        g = H[H[hc].notna()]; x = g[dcol].astype(int).to_numpy(); y = g[hc].astype(int).to_numpy()
        fam = np.arange(len(g)); bs = []; bw = []
        for _ in range(B):
            ii = rng.integers(0, len(g), len(g)); bs.append(kappa(x[ii], y[ii]))
            try: bw.append(wkappa(x[ii], y[ii], g.w.to_numpy()[ii]))
            except Exception: pass
        KR.append(dict(dimension=dnm, human_label=hc, n=len(g), agreement=float((x == y).mean()), kappa_unweighted=kappa(x, y), k_lo=np.nanpercentile(bs, 2.5), k_hi=np.nanpercentile(bs, 97.5), kappa_HT=wkappa(x, y, g.w.to_numpy()), kht_lo=np.nanpercentile(bw, 2.5), kht_hi=np.nanpercentile(bw, 97.5), kish_n=kish(g.w)))
pd.DataFrame(KR).to_csv(OUT / "human_validity_kappa.csv", index=False)
# human-human agreement
HHR = []
for q in ("q1", "q2", "q3", "q4"):
    pairs = []
    for i, g in r.groupby("item_id"):
        gg = g.sort_values("annotator")[q].tolist(); pairs.append(gg)
    x = np.array([p[0] for p in pairs]); y = np.array([p[1] for p in pairs]); k0 = kappa(x, y); bs = []
    for _ in range(B): ii = rng.integers(0, len(x), len(x)); bs.append(kappa(x[ii], y[ii]))
    HHR.append(dict(question=q, n_items=len(x), pct_agree=float((x == y).mean()), kappa=k0, lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5)))
    # kappa within the cue-relevant stratum
HH = pd.DataFrame(HHR); HH.to_csv(OUT / "human_human_agreement.csv", index=False)
# ------------------------------------------------ A2. Q3/Q4 vs the lexical gate "keywords lack the cue"
sys.argv = ["x", "--boot", "1", "--procs", "1"]; sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("r3", ROOT / "src/frontier_default_profiles_r3.py"); r3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r3)
Ux = r3.U.copy(); Ux["gate_act"] = r3.GATE["speech_act"]; Ux["gate_pol"] = r3.GATE["politeness"]
Hx = H.merge(Ux[["unit", "gate_act", "gate_pol", "kw_act", "kw_pol", "nocue_act", "nocue_pol", "E_speech_act", "E_politeness"]], on="unit", how="left"); assert Hx.gate_act.notna().all()
GR = []
for dnm, q, gate, st in (("speech act (Q3)", "h_q3", "gate_act", ["E_speech_act", "control"]), ("politeness (Q4)", "h_q4", "gate_pol", ["E_politeness", "E_speech_act", "control"])):
    for s_ in st:
        g = Hx[Hx.stratum == s_]; qq = g[q]
        GR.append(dict(question=dnm, stratum=s_, n=len(g), gate_true_n=int(g[gate].sum()), human_yes=int((qq == 1).sum()), human_no=int((qq == 0).sum()), human_nocons=int(qq.isna().sum()),
                       gate_true_and_human_no=int(((g[gate]) & (qq == 0)).sum()), gate_true_and_human_yes=int(((g[gate]) & (qq == 1)).sum()), gate_false_and_human_no=int(((~g[gate]) & (qq == 0)).sum()), gate_false_and_human_yes=int(((~g[gate]) & (qq == 1)).sum()),
                       human_yes_share_decided=float((qq == 1).sum() / max(qq.notna().sum(), 1)), human_yes_lo=wilson(int((qq == 1).sum()), int(qq.notna().sum()))[0], human_yes_hi=wilson(int((qq == 1).sum()), int(qq.notna().sum()))[1]))
GR = pd.DataFrame(GR); GR.to_csv(OUT / "human_gate_vs_q3q4.csv", index=False)
# agreement of gate with Q3/Q4 over decided items in the exposure strata
agr = []
for dnm, q, gate, st in (("speech act", "h_q3", "gate_act", ["E_speech_act"]), ("politeness", "h_q4", "gate_pol", ["E_politeness"])):
    g = Hx[Hx.stratum.isin(st) & Hx[q].notna()]; pred_lack = g[gate].astype(int); hum_lack = (1 - g[q]).astype(int); k = int(((pred_lack == 1) & (hum_lack == 1)).sum()); n_gate = int((pred_lack == 1).sum())
    agr.append(dict(dimension=dnm, strata=",".join(st), n_decided=len(g), n_total=int(Hx.stratum.isin(st).sum()), agreement=float((pred_lack == hum_lack).mean()), kappa=kappa(pred_lack, hum_lack) if pred_lack.nunique() > 1 and hum_lack.nunique() > 1 else np.nan,
                    gate_says_lacks=n_gate, of_which_human_says_lacks=k, human_lacks_given_gate=k / max(n_gate, 1), wilson_lo=wilson(k, max(n_gate, 1))[0], wilson_hi=wilson(k, max(n_gate, 1))[1], human_says_shows=int((hum_lack == 0).sum())))
pd.DataFrame(agr).to_csv(OUT / "human_gate_agreement.csv", index=False)
# ------------------------------------------------ B. class-calibrated re-run of exposure and always-commit
msg = r3.msg; U = r3.U; MI = r3.MI; WH = r3.WH; NMSG = r3.NMSG; strata = r3.strata; n = len(U)
class_E = {"speech_act": (U.E_speech_act > 0).to_numpy(), "politeness": (U.E_politeness > 0).to_numpy()}
class_C = ((~U.nonstmt) & (~U.polite) & (~U.kw_act) & (~U.kw_pol)).to_numpy()
# human samples per class (exposure stratum, control stratum), keyed by message (cluster) with HT weights
Hm = Hx.copy()
def human_rate(col, st):
    g = Hm[(Hm.stratum == st) & Hm[col].notna()]; return g
SPECS = {"speech_act": dict(E_stratum="E_speech_act", hcol="h_nonstmt", hcol_sens="h_nonstmt_sens", q="h_q3"), "politeness": dict(E_stratum="E_politeness", hcol="h_polite", hcol_sens="h_polite_sens", q="h_q4")}
mv = {d: r3.EV[(d, "model_visible")] / np.maximum(r3.EV[(d, "exposure")], 1e-12) for d in SPECS}
# model-miss per unit regardless of E (for control-class units): miss share over 4 models of output labelled no-cue
def unit_miss(d):
    c = r3.DIMS[d]; SC = r3.SC; m = SC.assign(m=(~SC[c["out"]]).astype(float)).groupby("unit").m.mean(); return U.unit.map(m).fillna(1.0).to_numpy()
MISS = {d: unit_miss(d) for d in SPECS}
def estimate(mu, hmu, d, variant):
    """mu: message multiplicity (NMSG,), hmu: dict item -> multiplicity for human sample items. returns exposure, model-visible per 1,000 (detector and human-calibrated)"""
    sp = SPECS[d]; ww = WH * mu[MI]; W = ww.sum(); col = sp["hcol_sens"] if variant == "sens" else sp["hcol"]
    gE = Hm[(Hm.stratum == sp["E_stratum"]) & Hm[col].notna()]; gC = Hm[(Hm.stratum == "control") & Hm[col].notna()]
    if variant == "strictq": gE = gE[gE[sp["q"]] != 1] if False else gE
    def hrate(g):
        wt = g.w.to_numpy() * np.array([hmu.get(i, 0) for i in g.item_id]); v = g[col].to_numpy(float)
        if variant == "strictq": v = v * (g[sp["q"]] != 1).to_numpy()          # keywords already show the cue (Q3/Q4 consensus yes) -> not exposure
        return (wt * v).sum() / wt.sum() if wt.sum() > 0 else np.nan
    pe, pc = hrate(gE), hrate(gC); eu = class_E[d]; cu = class_C
    det_exp = (ww * eu).sum() / W * 1000; det_mv = (ww * eu * mv[d]).sum() / W * 1000
    h_exp = ((ww * eu).sum() * pe + (ww * cu).sum() * pc) / W * 1000; h_mv = ((ww * eu * MISS[d]).sum() * pe + (ww * cu * MISS[d]).sum() * pc) / W * 1000
    return dict(det_exposure=det_exp, det_modelvisible=det_mv, human_exposure=h_exp, human_modelvisible=h_mv, human_exposure_from_E=(ww * eu).sum() / W * 1000 * pe, human_exposure_from_ctl=(ww * cu).sum() / W * 1000 * pc, ppv=pe, miss=pc)
# note: det_modelvisible recomputed from MISS to match r3 EV (E units only)
def run(variant):
    out = {d: [] for d in SPECS}
    ids = Hm.item_id.unique(); samp = {st: Hm[Hm.stratum == st].item_id.unique() for st in Hm.stratum.unique()}
    for b in range(B + 1):
        if b == 0: mu = np.ones(NMSG); hmu = {i: 1 for i in ids}
        else:
            mu = np.zeros(NMSG)
            for s_ in strata: np.add.at(mu, rng.choice(s_, len(s_)), 1)
            hmu = {}
            for st, its in samp.items():
                c = rng.integers(0, len(its), len(its))
                for j in c: hmu[its[j]] = hmu.get(its[j], 0) + 1
        for d in SPECS: out[d].append(estimate(mu, hmu, d, variant))
    return out
rows = []; SUMM = {}
for variant in ("primary", "sens", "strictq"):
    o = run(variant)
    for d in SPECS:
        df = pd.DataFrame(o[d])
        for c in df.columns:
            rows.append(dict(variant=variant, dimension=d, quantity=c, est=df[c].iloc[0], lo=np.nanpercentile(df[c].iloc[1:], 2.5), hi=np.nanpercentile(df[c].iloc[1:], 97.5)))
        for c1, c2 in (("human_exposure", "det_exposure"), ("human_modelvisible", "det_modelvisible")):
            dd = df[c1] - df[c2]; rows.append(dict(variant=variant, dimension=d, quantity=f"{c1} minus {c2}", est=dd.iloc[0], lo=np.nanpercentile(dd.iloc[1:], 2.5), hi=np.nanpercentile(dd.iloc[1:], 97.5)))
        rr_ = df.human_modelvisible / df.det_modelvisible; rows.append(dict(variant=variant, dimension=d, quantity="ratio human/detector model-visible", est=rr_.iloc[0], lo=np.nanpercentile(rr_.iloc[1:], 2.5), hi=np.nanpercentile(rr_.iloc[1:], 97.5)))
RR = pd.DataFrame(rows); RR.to_csv(OUT / "human_rerun_exposure.csv", index=False)
# derived price with measured restoration (F1; chip / plain word), applied to human-calibrated exposure
rest = pd.read_csv(OUT / "followup/f1_restoration.csv"); rest = rest[rest.model.str.startswith("pooled(mode=arb)")]
pr = []
for d in SPECS:
    for arm in ("bare", "chip", "word"):
        rs = rest[(rest.dimension == d) & (rest.arm == arm)].iloc[0]
        for variant in ("primary", "sens", "strictq"):
            for q in ("human_exposure", "det_exposure"):
                e = RR[(RR.variant == variant) & (RR.dimension == d) & (RR.quantity == q)].iloc[0]
                pr.append(dict(variant=variant, dimension=d, arm=arm, exposure_basis=q, r=rs.r, r_lo=rs.lo, r_hi=rs.hi, exposure_per_1000=e.est, rev_per_1000=e.est * (1 - rs.r), rev_lo_corner=e.lo * (1 - rs.hi), rev_hi_corner=e.hi * (1 - rs.lo)))
pd.DataFrame(pr).to_csv(OUT / "human_rerun_price.csv", index=False)
pd.set_option("display.width", 250)
print(R1.round(3).to_string()); print(pd.DataFrame(PR).round(3).to_string()); print(pd.DataFrame(KR).round(3).to_string()); print(HH.round(3).to_string()); print(GR.round(3).to_string()); print(pd.DataFrame(agr).round(3).to_string())
print(RR[RR.quantity.isin(["det_exposure", "det_modelvisible", "human_exposure", "human_modelvisible", "ppv", "miss", "ratio human/detector model-visible", "human_exposure_from_ctl"])].round(3).to_string())
