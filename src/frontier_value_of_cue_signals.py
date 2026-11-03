"""value_of_cue round 2: H2 (internal vs external signals), H4 (B6 entropy-gated asking), stop rule. Primary scope (polarity, speech act, politeness-lost). PLAN.md A2 R2-5..R2-9."""
import json, os, sys, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import frontier_value_of_cue_lib as L
from frontier_value_of_cue_lib import *
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
R2 = OUT / "round2"; LOCAL = os.environ.get("VOC_LOCALS", "qwen2.5-7b,llama3.1-8b,gemma3-4b").split(","); SUF = os.environ.get("VOC_SUF", ""); PD3 = ["polarity", "speech_act", "politeness"]; BUD = [20, 50, 100, 200, 400]
WV3 = WV5[PRIM]; RHO3 = RHO5[PRIM]
F = {m: pd.read_parquet(R2 / f"features_{m}.parquet") for m in LOCAL}; FX = pd.read_parquet(R2 / "features_S2.parquet")
assert all((F[m].item_id.values == U.item_id.values).all() for m in LOCAL)
def s3cols(m, df): return [c for c in df.columns if c.startswith(("g_", "s_freq", "s_ent", "p_logit", "jH")) and df[c].dtype != object]
S3 = {m: F[m][s3cols(m, F[m])].to_numpy(float) for m in LOCAL}; S3cols = s3cols(LOCAL[0], F[LOCAL[0]]); S3["pooled"] = np.mean([S3[m] for m in LOCAL], 0)
lg = lambda p: np.log(np.clip(p, .01, .99) / (1 - np.clip(p, .01, .99))); S2 = zs(np.stack([lg(FX[f"x_{d}"].to_numpy(float)) for d in PD3], 1))
S1 = XS1_NOLEX
XSETS = {}
for sc in LOCAL + ["pooled"]:
    s3 = zs(S3[sc]); ms = LOCAL if sc == "pooled" else [sc]; so = zs(np.mean([F[m][["o_polarity", "o_speech_act", "o_politeness"]].to_numpy(float) for m in ms], 0))
    XSETS[sc] = {"P-K": S1, "P-X": np.c_[S1, S2], "P-I": np.c_[S1, s3], "P-ALL": np.c_[S1, S2, s3], "P-O": np.c_[S1, so], "P-IO": np.c_[S1, s3, so]}
Ysc = {sc: outcome("r", model=sc if sc != "pooled" else None)[:, PRIM] for sc in LOCAL + ["pooled"]}
def job(a): sc, k, d = a; return a, oof(XSETS[sc][k], Ysc[sc][:, d])
t0 = time.time(); cache = R2 / f"signals_P{SUF}.npz"
if cache.exists():
    z = np.load(cache); PP = {tuple(k.split("|")): z[k] for k in z.files}
else:
    jobs = [(sc, k, d) for sc in XSETS for k in XSETS[sc] for d in range(3)]
    with Pool(16) as p: out = p.map(job, jobs)
    PP = {(sc, k, str(d)): v for (sc, k, d), v in out}; np.savez(cache, **{"|".join(k): v for k, v in PP.items()})
print("fits", round(time.time() - t0), "s", flush=True)
P = {sc: {k: np.stack([PP[(sc, k, str(d))] for d in range(3)], 1) for k in XSETS[sc]} for sc in XSETS}
boot = Boot(NB)
def prior(Y): return np.array([(w * Y[:, d]).sum() / w.sum() for d in range(3)])
def b6_inputs(sc):
    ms = LOCAL if sc == "pooled" else [sc]; H = np.mean([F[m].jH.to_numpy(float) for m in ms], 0); MN = np.stack([np.mean([F[m][f"s_minor_{d}"].to_numpy(float) for m in ms], 0) for d in PD3], 1); return H, MN
def pols_for(sc, q=Q0):
    Y = Ysc[sc]; pr = prior(Y); pols = {k: policy(P[sc][k], WV3, q, RHO3, Y) for k in P[sc]}; pols["Oracle"] = policy(Y, WV3, q, RHO3, Y)
    pols["B5"], a5 = b5_curves(WV3, q, RHO3, Y, pr); pols["B1"] = b1_curves(WV3, q, RHO3, Y); H, MN = b6_inputs(sc)
    pols["B6"] = gated_policy(H, MN.argmax(1), WV3, q, Y); pols["B6-w"] = gated_policy(H, (MN * WV3).argmax(1), WV3, q, Y)
    return pols, Y
ALL = ["P-K", "P-X", "P-I", "P-ALL", "P-O", "P-IO", "B6", "B6-w", "B5", "B1", "Oracle"]
DIFFS = [("P-O", "P-K"), ("P-I", "P-O"), ("P-IO", "P-O"), ("P-O", "B5"), ("P-IO", "B5"), ("P-I", "P-K"), ("P-X", "P-K"), ("P-ALL", "P-K"), ("P-I", "P-X"), ("P-K", "B5"), ("P-X", "B5"), ("P-I", "B5"), ("P-ALL", "B5"), ("P-K", "B6"), ("P-X", "B6"), ("P-I", "B6"), ("P-ALL", "B6"),
         ("B6", "B1"), ("B6", "B5"), ("P-K", "B1")]
def ci(res, g):
    lo, hi = [], []
    for m, rs in res.items(): a, b = np.percentile([g(r) for r in rs], [2.5, 97.5]); lo.append(a); hi.append(b)
    return min(lo), max(hi)
rows = []; au = []; cal = []
for sc in ["pooled"] + LOCAL:
    pols, Y = pols_for(sc); B0 = b0(Y, WV3, w); pt = {k: {B: at_budget(c, w, B) for B in BUD} for k, c in pols.items()}
    res = {m: [dict(b0=b0(Y, WV3, wb), **{k: {B: v[0] for B, v in at_budgets(c, wb, BUD).items()} for k, c in pols.items()}) for wb in ws] for m, ws in boot.draws.items()}
    for B in BUD:
        for k in ALL:
            lo, hi = ci(res, lambda x: x[k][B] / x["b0"]); rows.append(dict(scope=sc, budget=B, policy=k, B0=B0, weighted_averted_per1000=pt[k][B][0], rel=pt[k][B][0] / B0, lo=lo, hi=hi, raw_averted_per1000=pt[k][B][1]))
        for a, b in DIFFS:
            lo, hi = ci(res, lambda x: (x[a][B] - x[b][B]) / x["b0"]); d = pt[a][B][0] - pt[b][B][0]; rows.append(dict(scope=sc, budget=B, policy=f"{a} minus {b}", B0=B0, weighted_averted_per1000=d, rel=d / B0, lo=lo, hi=hi))
    for d in range(3):
        yb = (Y[:, d] >= .5).astype(float); base = None
        for k in P[sc]:
            a = wauc(yb, P[sc][k][:, d], w); bs = [wauc(yb, P[sc][k][:, d], x) for x in boot.draws["both"][:300]]
            r = dict(scope=sc, dimension=PD3[d], features=k, auroc=a, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5))
            if k != "P-K":
                dd = [wauc(yb, P[sc][k][:, d], x) - wauc(yb, P[sc]["P-K"][:, d], x) for x in boot.draws["both"][:300]]; r.update(delta_vs_PK=a - wauc(yb, P[sc]["P-K"][:, d], w), dlo=np.percentile(dd, 2.5), dhi=np.percentile(dd, 97.5))
            au.append(r)
        # B6 raw signal AUROC (entropy / minority frequency alone)
        H, MN = b6_inputs(sc); au.append(dict(scope=sc, dimension=PD3[d], features="B6 minority-frequency (single signal)", auroc=wauc(yb, MN[:, d], w)))
        pk = P[sc]["P-I"][:, d]; ece = lambda p: sum((w[m].sum() / w.sum()) * abs((w[m] * p[m]).sum() / w[m].sum() - (w[m] * Y[m, d]).sum() / w[m].sum()) for lo_, hi_ in zip(np.quantile(p, np.linspace(0, 1, 11))[:-1], np.quantile(p, np.linspace(0, 1, 11))[1:]) for m in [(p >= lo_) & (p <= hi_)] if m.sum())
        for k in P[sc]: cal.append(dict(scope=sc, dimension=PD3[d], features=k, ece=ece(P[sc][k][:, d]), mean_p=(w * P[sc][k][:, d]).sum() / w.sum(), prior=prior(Y)[d]))
    print(sc, "done", round(time.time() - t0), flush=True)
R = pd.DataFrame(rows); R.to_csv(R2 / f"signals_frontier{SUF}.csv", index=False); AU = pd.DataFrame(au); AU.to_csv(R2 / f"signals_auroc{SUF}.csv", index=False); pd.DataFrame(cal).to_csv(R2 / f"signals_calibration{SUF}.csv", index=False)
# identical-text rate of greedy regeneration vs stored output
idr = {}
rawS = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); rawS = rawS[rawS.prompt_id.eq("P0") & rawS.channel.str.startswith("human_")].rename(columns={"family_id": "fam"}); rawS["writer"] = rawS.channel.str.replace("human_", "", regex=False)
for m in LOCAL:
    s = rawS[rawS.model.eq(m)].set_index(["fam", "writer"]); o = s.reindex(pd.MultiIndex.from_frame(U[["fam", "writer"]]))
    txt = [c for c in ("text", "output_text", "output") if c in o.columns]
    if txt: idr[m] = float((o[txt[0]].fillna("").str.strip().to_numpy() == F[m].greedy_text.str.strip().to_numpy()).mean())
# sensitivity: P-I restricted to units whose regenerated greedy text equals stored output (primary per PLAN section 6 Stage 1(a); reported as fraction only here)
# ---------------------------------------------------------------- stop rule (pooled, T=100, primary scope)
pl = R[(R.scope == "pooled") & (R.budget == 100)].set_index("policy")
cand = {k: pl.loc[k, "rel"] for k in ("P-K", "P-X", "P-I", "P-ALL")}; best = max(cand, key=cand.get)
d = pl.loc[f"{best} minus B5"]; stop = bool((d.rel * 100 <= 1.0) or d.lo <= 0)
summ = dict(best_policy=best, rel_best=float(cand[best]), rel_B5=float(pl.loc["B5", "rel"]), best_minus_B5_pp=float(d.rel * 100), ci_pp=[float(d.lo * 100), float(d.hi * 100)], stop_round3=stop,
            stop_text="modest and prior-driven; stop" if stop else "signals beat B5 with CI excluding 0: run full test", all_candidates={k: float(v) for k, v in cand.items()}, identical_text_rate=idr, nb=NB)
json.dump(summ, open(R2 / f"signals_summary{SUF}.json", "w"), indent=1); print(json.dumps(summ, indent=1)); print(R[(R.scope == "pooled") & R.budget.isin([50, 100])].round(3).to_string()); print(AU.round(3).to_string())
