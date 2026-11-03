"""default_profiles F1 D4: CLAM-style generic clarification trigger vs gated random and vs the r3 probe confidence mean.
Rule: analysis/frontier/default_profiles/PLAN.md section 11 (D4). CPU only; imports the r3 unit/event construction (stored outputs, stored probes) without running its bootstrap.
Writes analysis/frontier/default_profiles/followup/{clam_contrasts.csv,clam_auroc.csv,clam_summary.json}"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
sys.argv = ["r3", "--boot", "0"]
import frontier_default_profiles_r3 as R3
OUT = ROOT / "analysis/frontier/default_profiles/followup"; B = 1000; SEED = 20261103
U, DL, MI, WH, NMSG, GATE, EV = R3.U, R3.DL, R3.MI, R3.WH, R3.NMSG, R3.GATE, R3.EV
R3PM = ["gemma3-4b", "llama3.1-8b", "qwen2.5-7b"]       # the probe models r3 used (the probe dir now also holds qwen14 and nemo)
CL = {}
for m in ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b"]:
    r = pd.DataFrame([json.loads(l) for l in open(ROOT / f"runs/frontier_default_profiles_clam/{m}.jsonl")]).drop_duplicates("unit").set_index("unit")
    CL[m] = U.unit.map(r.p_yes).to_numpy(float)
nulls = {m: float(np.isnan(v).mean()) for m, v in CL.items()}; mean = np.nanmean(np.vstack(list(CL.values())), axis=0); mean = np.where(np.isnan(mean), 0.0, mean)
# multiplicities (message clusters, stratified by sample type as in r3)
rng = np.random.default_rng(SEED); strata = [np.where(R3.msg["sample"].eq(k_))[0] for k_ in ("random", "enriched")]; MULT = [np.ones(NMSG)]
for _ in range(B):
    mu = np.zeros(NMSG)
    for s_ in strata: np.add.at(mu, rng.choice(s_, len(s_)), 1)
    MULT.append(mu)
J = 10  # 10% budget on the 0..100 grid
def curves(score, d, evn):
    return np.array([R3.curve(score, WH * mu[MI], EV[(d, evn)])[J] for mu in MULT])
def rg(d, evn): return np.array([R3.rand_gated(d, WH * mu[MI], EV[(d, evn)])[J] for mu in MULT])
def ac(d, evn): return np.array([(WH * mu[MI] * EV[(d, evn)]).sum() / (WH * mu[MI]).sum() * 1000 for mu in MULT])
rows = []; aur = []
def ci(x, a=2.5): x = np.asarray(x)[1:]; return float(np.percentile(x, a)), float(np.percentile(x, 100 - a))
def p2(x): x = np.asarray(x)[1:]; return float((1 + 2 * min((x >= 0).sum(), (x <= 0).sum())) / (len(x) + 1))
named = []
for d in ("polarity", "politeness"):
    evn = "model_visible"; qm = np.nanmean([R3.Q[m][d] for m in R3PM], 0)
    S = {"clam_mean_gated": np.where(GATE[d], mean, -1.0), "clam_mean_ungated": mean.copy(), "conf_gated_mean_r3": np.where(GATE[d], qm, -1.0)}
    for m in CL: S["clam_" + m + "_gated"] = np.where(GATE[d], np.nan_to_num(CL[m], nan=0.0), -1.0)
    Cv = {k: curves(v, d, evn) for k, v in S.items()}; Cv["random_gated"] = rg(d, evn); Cv["always_commit"] = ac(d, evn)
    for k, v in Cv.items(): rows.append(dict(dimension=d, kind="level", name=k, rev_per_1000=v[0], lo=ci(v)[0], hi=ci(v)[1]))
    for a_, b_, tag in (("clam_mean_gated", "random_gated", "named"), ("clam_mean_gated", "conf_gated_mean_r3", "named"), ("clam_mean_ungated", "random_gated", "exploratory"),
                        ("clam_qwen2.5-7b_gated", "random_gated", "exploratory"), ("clam_llama3.1-8b_gated", "random_gated", "exploratory"), ("clam_gemma3-4b_gated", "random_gated", "exploratory")):
        x = Cv[a_] - Cv[b_]; se = float(np.std(x[1:], ddof=1)); lo, hi = ci(x)
        rows.append(dict(dimension=d, kind="contrast", name=f"{a_} - {b_}", tag=tag, diff=x[0], lo=lo, hi=hi, p=p2(x), se=se, mde=2.8 * se, a_rev=Cv[a_][0], b_rev=Cv[b_][0]))
        if tag == "named": named.append(len(rows) - 1)
    E = EV[(d, "exposure")] > 0; el = E | ~(R3.NOC[d] & (EV[(d, "exposure")] == 0)) if False else None
    # AUROC of the trigger for exposure events among units eligible for asking (gated), HT weights
    elig = GATE[d] & R3.NOC[d]
    for k, s in (("clam_mean", mean), ("r3_conf_mean", qm), *[("clam_" + m, np.nan_to_num(CL[m], nan=0.0)) for m in CL]):
        aur.append(dict(dimension=d, score=k, auroc_exposure_among_gated_nocue=R3.wauc(s[elig], EV[(d, "exposure")][elig], WH[elig]), n=int(elig.sum()), n_E=int(EV[(d, "exposure")][elig].sum())))
# Holm over the 4 named contrasts
p = np.array([rows[i]["p"] for i in named]); o = np.argsort(p); holm = np.zeros(4); run = 0
for r_, i in enumerate(o): run = max(run, min(1, (4 - r_) * p[i])); holm[i] = run
for k, i in enumerate(named): rows[i]["p_holm"] = float(holm[k])
pd.DataFrame(rows).to_csv(OUT / "clam_contrasts.csv", index=False); pd.DataFrame(aur).to_csv(OUT / "clam_auroc.csv", index=False)
neg_vs_rand = next(r for r in rows if r.get("name") == "clam_mean_gated - random_gated" and r["dimension"] == "polarity")
summ = dict(clam_null_rate=nulls, boot=B, seed=SEED, probe_models_r3=R3PM, named=[rows[i] for i in named], h4_revised=bool(neg_vs_rand["p_holm"] < .05 and neg_vs_rand["diff"] < 0),
            benchmark_delivered=True, units=int(len(U)))
json.dump(summ, open(OUT / "clam_summary.json", "w"), indent=1, default=float)
print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(aur).round(3).to_string()); print("nulls", nulls, "H4 revised", summ["h4_revised"])
