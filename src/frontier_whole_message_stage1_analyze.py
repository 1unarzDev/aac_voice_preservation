"""Stage 1 analysis: metric validation vs writer labels (Part 18) and SLP ratings. Rules: PLAN.md Stage 1 + freeze record."""
import json, sys, re
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
import frontier_whole_message_stage1_jobs as J
import analyze_whole_message as AW
D = m1.D; SEED = 20261102; B = 5000
cache = m1.load()
def g(variant, x, y, r): return cache.get(m1.key(variant, x, y, r))
it = J.it.copy()
# ---- gates
gates = {}
ga = [g("ref", r.input_text, r.r, r.r) for _, r in J.gate.iterrows()]
gb = [g("ref", r.input_text, r.r_other, r.r) for _, r in J.gate.iterrows()]
gc = [g("free", r.input_text, J.kw(r.input_text), None) for _, r in J.gate.iterrows()]
ok = lambda L: [v for v in L if v]
gates["a_ref_y_eq_r_pass"] = float(np.mean([not m1.wmf_fail(v) for v in ok(ga)])); gates["a_n"] = len(ok(ga))
gates["b_ref_other_family_fail"] = float(np.mean([m1.wmf_fail(v) for v in ok(gb)])); gates["b_n"] = len(ok(gb))
gates["c_free_keywords_no_UC"] = float(np.mean([not v["unrequested"] for v in ok(gc)])); gates["c_n"] = len(ok(gc))
gates["c_free_keywords_WMFpass"] = float(np.mean([not m1.wmf_fail(v) for v in ok(gc)]))
gates["pass"] = bool(gates["a_ref_y_eq_r_pass"] >= .95 and gates["b_ref_other_family_fail"] >= .95 and gates["c_free_keywords_no_UC"] >= .90)
gates["pass_by_gate"] = dict(a=gates["a_ref_y_eq_r_pass"] >= .95, b=gates["b_ref_other_family_fail"] >= .95, c=gates["c_free_keywords_no_UC"] >= .90)
# ---- features
rows = []
for _, r in it.iterrows():
    vr, vf = g("ref", r.input_text, r.text, r.r), g("free", r.input_text, r.text, None)
    chips, kws = AW.parse_input(r.input_text)
    yo, ro = AW.content(AW.nlp(r.text)), AW.content(AW.nlp(r.r))
    ys, rs = set(yo), set(ro)
    inter = len(ys & rs); f1 = 0 if not inter else 2 * (inter / len(ys)) * (inter / len(rs)) / ((inter / len(ys)) + (inter / len(rs)))
    allowed = AW.lemmas_of(kws) | set().union(*[AW.CHIP_WORDS.get(c, set()) for c in chips]) if chips else AW.lemmas_of(kws)
    nov = len([w for w in ys if w not in allowed]) / max(1, len(ys))
    says_match = r.says == f"version {r.intended_variant}"
    rows.append(dict(item_id=r.item_id, writer=r.writer_id, channel=r.channel, model=r.model, dimension=r.dimension,
        L1=(None if r.says == "" else int(not says_match)), L2=int(r.accept == "no"),
        M0=int(not r.judge_critical_match in (True, "True")), M1ref_fail=int(m1.wmf_fail(vr)), M1ref_score=vr["score_1to5"] / 5,
        M1free_fail=int(m1.wmf_fail(vf)), M1free_score=vf["score_1to5"] / 5, M1free_UC=int(bool(vf["unrequested"])), M1ref_UC=int(bool(vr["unrequested"])),
        M1ref_drop=int(bool(vr["dropped"])), M1ref_frame=int(vr["frame_changed"]),
        M2_f1=f1, M2_novelty=nov, LEN_ratio=len(r.text.split()) / max(1, len(kws)), ref_len=len(r.r.split()) , out_len=len(r.text.split())))
F = pd.DataFrame(rows); F.to_csv(D / "stage1_features.csv", index=False)
# score orientation: higher = predicts rejection
F["s_M0"] = F.M0; F["s_M1ref"] = (1 - F.M1ref_score) + .01 * F.M1ref_fail; F["s_M1free"] = (1 - F.M1free_score) + .01 * F.M1free_fail
F["s_M1ref_bin"] = F.M1ref_fail; F["s_M1free_bin"] = F.M1free_fail
F["s_M2f1"] = 1 - F.M2_f1; F["s_M2nov"] = F.M2_novelty; F["s_len"] = F.LEN_ratio
F["s_M0+M1ref"] = F.s_M0 + F.s_M1ref  # unweighted sum, declared, not fitted
metrics = ["s_M0", "s_M1ref", "s_M1free", "s_M1ref_bin", "s_M1free_bin", "s_M2f1", "s_M2nov", "s_len", "s_M0+M1ref"]
def boots(sub, label, mets, B=B):
    sub = sub[sub[label].notna()].reset_index(drop=True); y = sub[label].astype(int).values
    ws = sub.writer.values; uw = np.unique(ws); idx = {w: np.where(ws == w)[0] for w in uw}
    rng = np.random.default_rng(SEED); draws = []
    for _ in range(B):
        ix = np.concatenate([idx[w] for w in rng.choice(uw, len(uw))]); draws.append(ix)
    out = {}
    pt = {m: AW.auroc(y, sub[m].values) for m in mets}
    bs = {m: np.array([AW.auroc(y[ix], sub[m].values[ix]) for ix in draws]) for m in mets}
    for m in mets:
        v = bs[m][~np.isnan(bs[m])]
        dv = bs[m] - bs["s_M0"]; dv = dv[~np.isnan(dv)]
        out[m] = dict(auroc=pt[m], lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)),
                      d_vs_M0=pt[m] - pt["s_M0"], d_lo=float(np.percentile(dv, 2.5)), d_hi=float(np.percentile(dv, 97.5)))
    out["n"] = len(sub); out["n_pos"] = int(y.sum())
    return out
wn = F.writer.str[1:].astype(int)
subsets = {"chip1_all": F[F.channel == "chip1"], "chip1_dev(P01-10)": F[(F.channel == "chip1") & (wn <= 10)], "chip1_holdout(P11-20)": F[(F.channel == "chip1") & (wn > 10)],
           "all200": F, "bare": F[F.channel == "bare"], "all_holdout": F[wn > 10]}
res = {}; tab = []
for lab in ["L1", "L2"]:
    for sn, sub in subsets.items():
        r_ = boots(sub, lab, metrics); res[f"{lab}|{sn}"] = r_
        for m in metrics: tab.append(dict(label=lab, subset=sn, metric=m, n=r_["n"], n_pos=r_["n_pos"], **r_[m]))
T = pd.DataFrame(tab); T.to_csv(D / "stage1_auroc.csv", index=False)
# decision rule (primary: L1, chip1 channel)
dec = {}
for m in ["s_M1ref", "s_M1free"]:
    h = res["L1|chip1_holdout(P11-20)"][m]; a = res["L1|chip1_all"][m]
    dec[m] = dict(holdout_auroc=h["auroc"], holdout_ci=[h["lo"], h["hi"]], full_chip1_delta_vs_M0=a["d_vs_M0"], delta_ci=[a["d_lo"], a["d_hi"]],
                  validated=bool(h["auroc"] >= .75 and a["d_lo"] > 0 and gates["pass"]))
# secondary: all-200 delta (the literal plan wording)
for m in ["s_M1ref", "s_M1free"]:
    a = res["L1|all200"][m]; dec[m]["all200_delta_vs_M0"] = a["d_vs_M0"]; dec[m]["all200_delta_ci"] = [a["d_lo"], a["d_hi"]]; dec[m]["all200_auroc"] = a["auroc"]
# ---- H2: among CK true outputs, share UC / dropped / frame (per model, chip1) 
ck = F[F.M0 == 0]
h2 = []
for scope, sub in [("ALL", ck), *[(m, ck[ck.model == m]) for m in sorted(ck.model.unique())]]:
    for ch in ["chip1", "bare", "both"]:
        s2 = sub if ch == "both" else sub[sub.channel == ch]
        if len(s2): h2.append(dict(model=scope, channel=ch, n_CKtrue=len(s2), WMFfail_ref_per1000=1000 * s2.M1ref_fail.mean(), WMFfail_free_per1000=1000 * s2.M1free_fail.mean(),
              UC_ref_per1000=1000 * s2.M1ref_UC.mean(), UC_free_per1000=1000 * s2.M1free_UC.mean(), dropped_ref_per1000=1000 * s2.M1ref_drop.mean(), writer_reject_L1_among_CK=s2.L1.dropna().mean()))
pd.DataFrame(h2).to_csv(D / "stage1_h2_ck_true.csv", index=False)
# confusion: M1ref reasons vs prior classifier?
# ---- SLP
slp = J.slp.copy(); rt = pd.concat([pd.read_csv(ROOT / f"expert_package/returns_slp/slp_rating_SLP{i}.csv") for i in (1, 2)])
rt = rt[rt.task == 2]; rt["notyes"] = (rt.acceptable != "yes").astype(int)
S = rt.merge(slp[["item_id", "input_text", "text", "judge_meaning_fail", "arm"]], on="item_id")
S["M1free_fail"] = [int(m1.wmf_fail(g("free", r.input_text, r.text, None))) for _, r in S.iterrows()]
S["M1free_score"] = [g("free", r.input_text, r.text, None)["score_1to5"] / 5 for _, r in S.iterrows()]
S["s_M1free"] = (1 - S.M1free_score) + .01 * S.M1free_fail; S["s_M0"] = S.judge_meaning_fail.astype(float)
rng = np.random.default_rng(SEED); ui = S.item_id.unique(); ix_by = {i: np.where(S.item_id.values == i)[0] for i in ui}
slp_res = {}
for m in ["s_M0", "s_M1free"]:
    y = S.notyes.values; pt = AW.auroc(y, S[m].values); bs = []
    for _ in range(B):
        ix = np.concatenate([ix_by[i] for i in rng.choice(ui, len(ui))]); v = AW.auroc(y[ix], S[m].values[ix]); bs.append(v)
    bs = np.array([b for b in bs if not np.isnan(b)]); slp_res[m] = dict(auroc=pt, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), n_ratings=len(S), n_notyes=int(y.sum()))
# ---- sanity extras: how often does M1 reproduce which reasons among writer rejected chip1
summ = dict(gates=gates, decision=dec, slp_L4=slp_res, n_items=len(F), L1_usable=int(F.L1.notna().sum()),
            seed=SEED, B=B, m1_prompt_sha=m1.PSHA, missing_calls=int(sum(1 for _, r in it.iterrows() if g("ref", r.input_text, r.text, r.r) is None)))
json.dump(summ, open(D / "summary.json", "w"), indent=1, default=float)
print(json.dumps(summ, indent=1, default=float)); print(T[(T.label == "L1")].round(3).to_string())
print(pd.DataFrame(h2).round(1).to_string())
