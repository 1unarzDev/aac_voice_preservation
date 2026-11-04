"""default_profiles F1 (c): same-items bare / chip / plain-word / chip+G1 restoration on the exposure units.
Rule: analysis/frontier/default_profiles/PLAN.md section 11 (D1-D3 + derived price). CPU only.
Outcome: judge.py final critical (J1==J2) else blind arbiter (src/arbiter_tool.py, output text only); no J1 fallback.
Writes followup/{f1_restoration.csv,f1_decisions.csv,f1_price.csv,f1_models.csv} and followup_summary.json (merged with clam_summary.json by the report step)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; DP = ROOT / "analysis/frontier/default_profiles"; OUT = DP / "followup"
B, SEED = 2000, 20261103
MODELS = ["gpt-6.1-terra", "qwen2.5-7b", "llama3.1-8b"]; DIMS = ["polarity", "politeness", "speech_act"]
EXPO = {"polarity": 24.4, "politeness": 56.4, "speech_act": 277.5}; R3_AC = {"polarity": 23.9, "politeness": 49.4}
RHO = pd.read_csv(DP / "rho_draws.csv").groupby(["dimension", "channel"]).rho.agg(mean="mean", lo=lambda x: x.quantile(.025), hi=lambda x: x.quantile(.975))
U = pd.read_csv(OUT / "units.csv")
def final(run):
    J = {}; 
    for l in open(ROOT / f"runs/{run}/judgments.jsonl"):
        j = json.loads(l); J[(j["text_id"], j["family_id"], j["input_text"])] = [j["critical"], bool(j["needs_arbiter"])]
    ap = ROOT / f"runs/{run}/arbiter.jsonl"
    if ap.exists():
        for l in open(ap):
            a = json.loads(l); k = (a["text_id"], a["family_id"], a["input_text"]); J[k][0] = a["critical"]
    return J
def rows(run):
    J = final(run); R = []
    for l in open(ROOT / f"runs/{run}/outputs.jsonl"):
        o = json.loads(l); arm, ch = o["channel"].split("|")
        c, disp = J[(o["text_id"], o["family_id"], o["input_text"])]
        R.append(dict(model=o["model"], prompt=o["prompt_id"], arm=arm, channel=ch, fam=o["family_id"].replace("dpf1-", ""), crit=c, disputed=disp, text=o["text"]))
    return pd.DataFrame(R)
A = rows("frontier_default_profiles_f1all"); G = rows("frontier_default_profiles_f1g"); G["arm"] = "chipG1"
D = pd.concat([A, G]); 
U["fam_dim"] = U.fam + "-" + U.dim; D["key"] = D.fam; U["key"] = U.fam_dim
D = D.merge(U[["key", "channel" if False else "uid", "dim", "value", "w", "sample", "item_id"]].assign(channel=U.channel), left_on=["key", "channel"], right_on=["key", "channel"], how="left")
assert D.uid.notna().all(), D[D.uid.isna()].head()
D["hit"] = (D.crit == D.value).astype(float); D.loc[D.crit.isna(), "hit"] = np.nan
D.to_csv(OUT / "f1_unit_outcomes.csv", index=False)
print("rows", len(D), "disputed rows (arbitrated)", int(D.disputed.sum()), "missing crit", int(D.crit.isna().sum()))
# bootstrap multiplicities over message clusters (item_id), stratified by sample within each dimension
rng = np.random.default_rng(SEED)
def mults(d):
    us = U[U.dim == d]; ids = us.item_id.unique(); smp = us.groupby("item_id")["sample"].first(); strata = [ids[(smp.loc[ids] == s).to_numpy()] for s in smp.unique()]
    out = []
    for b in range(B + 1):
        m = pd.Series(0.0, index=ids)
        if b == 0: m[:] = 1
        else:
            for s in strata:
                for i in rng.choice(s, len(s)): m[i] += 1
        out.append(m)
    return out
MU = {d: mults(d) for d in DIMS}
def arm_vec(d, arm, model, mode="arb"):
    x = D[(D.dim == d) & (D.arm == arm) & (D.model == model)].set_index("uid"); us = U[U.dim == d].set_index("uid")
    h = x.hit.reindex(us.index); dis = x.disputed.reindex(us.index).fillna(False).astype(bool)
    if mode == "excl": h = h.where(~dis)
    elif mode == "allfail": h = h.where(~dis, 0.0)
    elif mode == "allpass": h = h.where(~dis, 1.0)
    return h.to_numpy(float), us.w.to_numpy(float), us.item_id.to_numpy()
def draws(d, vec_fn):
    """vec_fn -> (values per unit, weights, item ids); returns draws of the HT mean over units with value present, using cluster multiplicities."""
    v, w, ids = vec_fn; ok = ~np.isnan(v); out = np.empty(B + 1)
    for b in range(B + 1):
        m = MU[d][b].reindex(ids).to_numpy(); ww = (w * m)[ok]; out[b] = (ww * v[ok]).sum() / ww.sum() if ww.sum() > 0 else np.nan
    return out
def ci(x, lev=95): a = (100 - lev) / 2; return np.nanpercentile(x[1:], a), np.nanpercentile(x[1:], 100 - a)
res, perm, R = [], [], {}
for d in DIMS:
    for arm in ("bare", "chip", "word", "chipG1"):
        for mode in ("arb", "excl", "allfail", "allpass"):
            per = []
            for m in MODELS:
                if arm == "chipG1" and False: pass
                v = arm_vec(d, "chip" if arm == "chipG1" else arm, m, mode) if arm != "chipG1" else None
                if arm == "chipG1":
                    x = D[(D.dim == d) & (D.arm == "chipG1") & (D.model == m)].set_index("uid"); us = U[U.dim == d].set_index("uid")
                    h = x.hit.reindex(us.index); dis = x.disputed.reindex(us.index).fillna(False).astype(bool)
                    h = {"excl": h.where(~dis), "allfail": h.where(~dis, 0.0), "allpass": h.where(~dis, 1.0)}.get(mode, h)
                    v = (h.to_numpy(float), us.w.to_numpy(float), us.item_id.to_numpy())
                dr = draws(d, v); R[(d, arm, mode, m)] = dr; per.append(dr)
                if mode == "arb": res.append(dict(dimension=d, arm=arm, model=m, r=dr[0], lo=ci(dr)[0], hi=ci(dr)[1], n_units=int(np.sum(~np.isnan(v[0])))))
            pooled = np.mean(per, 0); R[(d, arm, mode, "pooled")] = pooled
            res.append(dict(dimension=d, arm=arm, model="pooled(mode=%s)" % mode, r=pooled[0], lo=ci(pooled)[0], hi=ci(pooled)[1], n_units=int(len(U[U.dim == d]))))
pd.DataFrame(res).to_csv(OUT / "f1_restoration.csv", index=False)
dec = []
for d in DIMS:
    for mode in ("arb", "excl", "allfail", "allpass"):
        P = lambda a: R[(d, a, mode, "pooled")]
        x = P("chip") - P("word"); lo90, hi90 = ci(x, 90); lo95, hi95 = ci(x)
        d1 = "equivalent (+-5pp)" if (lo90 > -.05 and hi90 < .05) else ("chip better" if lo95 > 0 else "word better" if hi95 < 0 else "not distinguishable")
        g = P("chipG1") - P("chip"); glo, ghi = ci(g)
        d2 = "guard helps" if (glo > 0 or ghi < 0) and g[0] > 0 else ("guard hurts" if (glo > 0 or ghi < 0) else "no detectable effect")
        t = {}
        for ch, a in (("chip1", "chip"), ("nlcue", "word")):
            rt = RHO.loc[(d, ch), "mean"]; lo, hi = ci(P(a)); r0 = P(a)[0]
            t[a] = dict(transported=rt, measured=r0, lo=lo, hi=hi, within5pp=bool(abs(r0 - rt) <= .05), inside_ci=bool(lo <= rt <= hi))
        d3 = "held" if all(v["within5pp"] and v["inside_ci"] for v in t.values()) else "did not transport"
        dec.append(dict(dimension=d, mode=mode, chip_minus_word=x[0], c90=(lo90, hi90), c95=(lo95, hi95), D1=d1, g1_minus_chip=g[0], g1_ci=(glo, ghi), D2=d2, D3=d3,
                        chip_transport=t["chip"], word_transport=t["word"]))
pd.DataFrame(dec).to_csv(OUT / "f1_decisions.csv", index=False)
# derived price per 1,000 messages, arm applied to every message
price = []
for d in DIMS:
    for arm in ("bare", "chip", "word", "chipG1"):
        for mode in ("arb", "allfail", "allpass"):
            r = R[(d, arm, mode, "pooled")]; rev = EXPO[d] * (1 - r)
            price.append(dict(dimension=d, arm=arm, mode=mode, rev_per_1000=rev[0], lo=ci(rev)[0], hi=ci(rev)[1], r3_always_commit=R3_AC.get(d)))
pd.DataFrame(price).to_csv(OUT / "f1_price.csv", index=False)
print(pd.DataFrame(res).round(3).to_string()); 
for r in dec: print({k: (np.round(v, 3).tolist() if isinstance(v, (float, tuple)) else v) for k, v in r.items() if k not in ("chip_transport", "word_transport")}, r["chip_transport"], r["word_transport"] if r["mode"] == "arb" else "")
print(pd.DataFrame(price).round(2).to_string())
s = dict(boot=B, seed=SEED, units={d: int((U.dim == d).sum()) for d in DIMS}, arbitrated_rows=int(D.disputed.sum()), decisions=dec)
json.dump(s, open(OUT / "f1_summary.json", "w"), indent=1, default=float)
