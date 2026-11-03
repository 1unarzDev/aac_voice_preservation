"""Round 2 metric validity (frontier whole_message): trivial baselines, graded critical-only comparator, independent-family judges,
mechanism of rejections, verbatim-copy stratum. Rules: PLAN.md 'ROUND 2 FREEZE RECORD' R2-A / R2-B. Writes r2_validity_*.csv, r2_validity_summary.json."""
import json, sys, re
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
import frontier_whole_message_stage1_jobs as J1
import frontier_whole_message_r2_local as L
import analyze_whole_message as AW
D = m1.D; R = ROOT / "runs/frontier_whole_message_r2"; SEED = 20261102; B = 5000
F = pd.read_csv(D / "stage1_features.csv", keep_default_na=False)
it = pd.read_csv(ROOT / "analysis/intent_check/items.csv", keep_default_na=False)
F = F.merge(it[["item_id", "text", "input_text", "family_id", "intended_value"]], on="item_id")
F["L1"] = pd.to_numeric(F.L1, errors="coerce")
fams = {}
for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
    o = json.loads(l); fams[o["family_id"]] = o

def wlev(a, b):
    dp = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, y in enumerate(b, 1):
            prev, dp[j] = dp[j], min(dp[j] + 1, dp[j - 1] + 1, prev + (x != y))
    return dp[-1]
tok = lambda s: re.sub(r"[^\w\s']", " ", s.lower()).split()
F["ed_kw"] = [wlev(tok(AW.parse_input(x)[1] and " ".join(AW.parse_input(x)[1])), tok(y)) / max(1, len(tok(y))) for x, y in zip(F.input_text, F.text)]
# ---- scores, oriented: higher = predicts rejection
F["T1_wordcount"] = F.out_len; F["T2_lenratio"] = F.LEN_ratio; F["T3_lexF1"] = 1 - F.M2_f1; F["T4_novelty"] = F.M2_novelty; F["T5_edit_kw"] = F.ed_kw
F["M0_binary"] = F.M0
F["M1free_gpt"] = (1 - F.M1free_score) + .01 * F.M1free_fail
F["M1ref_gpt_UPPERBOUND"] = (1 - F.M1ref_score) + .01 * F.M1ref_fail
F["M1free_gpt_UCflag"] = F.M1free_UC
# T6: CV logistic grouped by writer
def cv_grouped(Xc, y, groups, lam=1.0, seed=0):
    X = np.asarray(Xc, float); X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1); X = np.c_[np.ones(len(X)), X]
    ug = np.unique(groups); rng = np.random.default_rng(seed); fold = {g: i % 5 for i, g in enumerate(rng.permutation(ug))}
    f = np.array([fold[g] for g in groups]); pr = np.zeros(len(y))
    for k in range(5):
        tr = (f != k) & ~np.isnan(y)
        w = AW.fit_logit(X[tr], y[tr], lam); pr[f == k] = X[f == k] @ w
    return pr
F["T6_cv_logit"] = cv_grouped(F[["T1_wordcount", "T2_lenratio", "T4_novelty", "T5_edit_kw"]].values, F.L1.values.astype(float), F.writer.values)
# ---- local judges
LOCAL = {}
for alias in ["qwen2.5-14b", "mistral-nemo-12b"]:
    p = R / f"local_{alias}.jsonl"
    if not p.exists(): continue
    c = {}
    for l in p.read_text().splitlines():
        if l.strip(): o = json.loads(l); c[o["k"]] = o["v"]
    short = {"qwen2.5-14b": "Q14", "mistral-nemo-12b": "Nemo"}[alias]; ok = True
    uc, sc, m0g = [], [], []
    for _, r in F.iterrows():
        a = c.get(L.qkey(("uc", r.input_text, r.text, None))); b = c.get(L.qkey(("sc", r.input_text, r.text, None)))
        f = fams[r.family_id]; d = c.get(L.qkey(("crit", None, r.text, (f["dimension"], tuple(f["critical_options"])))))
        if a is None or b is None or d is None: ok = False; break
        uc.append(a["p"]); sc.append(1 - (b["e"] - 1) / 4); m0g.append(1 - d["opts"].get(r.intended_value, 0))
    if ok:
        F[f"{short}_UC"] = uc; F[f"{short}_SC"] = sc; F[f"M0g_{short}"] = m0g; LOCAL[short] = alias
F.to_csv(D / "r2_validity_features.csv", index=False)
trivial = ["T1_wordcount", "T2_lenratio", "T3_lexF1", "T4_novelty", "T5_edit_kw", "T6_cv_logit"]
locm = [f"{s}_{k}" for s in LOCAL for k in ("UC", "SC")] + [f"M0g_{s}" for s in LOCAL]
metrics = trivial + ["M0_binary", "M1free_gpt", "M1free_gpt_UCflag", "M1ref_gpt_UPPERBOUND"] + locm
wn = F.writer.str[1:].astype(int)
nov0 = F.T4_novelty == 0
subsets = {"chip1_all": F.channel == "chip1", "chip1_dev(P01-10)": (F.channel == "chip1") & (wn <= 10), "chip1_holdout(P11-20)": (F.channel == "chip1") & (wn > 10),
           "all200": F.channel.notna(), "bare": F.channel == "bare", "chip1_excl_zero_novelty": (F.channel == "chip1") & ~nov0}
def boot(sub, mets):
    sub = sub[sub.L1.notna()].reset_index(drop=True); y = sub.L1.astype(int).values
    ws = sub.writer.values; uw = np.unique(ws); idx = {w: np.where(ws == w)[0] for w in uw}
    rng = np.random.default_rng(SEED); draws = [np.concatenate([idx[w] for w in rng.choice(uw, len(uw))]) for _ in range(B)]
    pt = {m: AW.auroc(y, sub[m].values) for m in mets}
    bs = {m: np.array([AW.auroc(y[ix], sub[m].values[ix]) for ix in draws]) for m in mets}
    return sub, pt, bs
rows = []; paired = []
for sn, mask in subsets.items():
    sub, pt, bs = boot(F[mask], metrics)
    best = max(trivial, key=lambda m: pt[m]) if not np.isnan(pt[trivial[0]]) else trivial[0]
    for m in metrics:
        v = bs[m][~np.isnan(bs[m])]
        rows.append(dict(subset=sn, metric=m, n=len(sub), n_pos=int(sub.L1.sum()), auroc=pt[m], lo=np.percentile(v, 2.5), hi=np.percentile(v, 97.5), best_trivial=best))
    def pd_(a, b, name):
        dv = bs[a] - bs[b]; dv = dv[~np.isnan(dv)]
        paired.append(dict(subset=sn, contrast=name, a=a, b=b, delta=pt[a] - pt[b], lo=np.percentile(dv, 2.5), hi=np.percentile(dv, 97.5)))
    for a in ["M1free_gpt", "M1free_gpt_UCflag"] + [f"{s}_{k}" for s in LOCAL for k in ("UC", "SC")]:
        pd_(a, best, f"{a} - best_trivial({best})")
        for s in LOCAL: pd_(a, f"M0g_{s}", f"{a} - M0g_{s}")
        pd_(a, "M0_binary", f"{a} - M0_binary")
        pd_(a, "T1_wordcount", f"{a} - T1_wordcount")
    pd_("M1free_gpt", "T6_cv_logit", "M1free_gpt - T6_cv_logit")
A = pd.DataFrame(rows); A.to_csv(D / "r2_validity_auroc.csv", index=False); Pd = pd.DataFrame(paired); Pd.to_csv(D / "r2_validity_paired.csv", index=False)
# agreement of independent judges with gpt M1-free (graded score; Spearman)
agree = {}
for s in LOCAL:
    for k in ("UC", "SC"):
        for sn, mask in {"all200": F.channel.notna(), "chip1": F.channel == "chip1", "bare": F.channel == "bare"}.items():
            sub = F[mask]; x = sub["M1free_gpt"] if k == "SC" else sub["M1free_gpt_UCflag"]
            agree[f"{s}_{k}|{sn}"] = dict(spearman=float(sub[f"{s}_{k}"].rank().corr(x.rank())))
    # binary agreement on UC flag at p>=.5
    agree[f"{s}_UC_binary_agreement_with_gpt_UCflag"] = float(((F[f"{s}_UC"] >= .5).astype(int) == F.M1free_gpt_UCflag).mean())
# ---- R2-B mechanism (existing labels)
mech = []
for ch, sub in [("chip1", F[F.channel == "chip1"]), ("bare", F[F.channel == "bare"]), ("all", F)]:
    rj = sub[sub.L1 == 1]
    a = (rj.M0 == 1) | (rj.M1ref_frame == 1); b = (rj.M1free_UC == 1) | (rj.M1ref_UC == 1); c = rj.M1ref_drop == 1
    ex_a = a; ex_b = ~a & b; ex_c = ~a & ~b & c; ex_d = ~a & ~b & ~c
    ckt = sub[(sub.M0 == 0) & sub.L1.notna()]
    mech.append(dict(channel=ch, n_rejected=len(rj), a_misres=int(a.sum()), b_UC=int(b.sum()), c_drop=int(c.sum()),
                     excl_a=int(ex_a.sum()), excl_b=int(ex_b.sum()), excl_c=int(ex_c.sum()), excl_d_residual=int(ex_d.sum()),
                     ck_true_n=len(ckt), ck_true_rejected=int((ckt.L1 == 1).sum()),
                     reject_given_UC1=float(ckt[ckt.M1free_UC == 1].L1.mean()), n_UC1=int((ckt.M1free_UC == 1).sum()),
                     reject_given_UC0=float(ckt[ckt.M1free_UC == 0].L1.mean()), n_UC0=int((ckt.M1free_UC == 0).sum()),
                     reject_given_UC0_frame0=float(ckt[(ckt.M1free_UC == 0) & (ckt.M1ref_frame == 0)].L1.mean()), n_UC0_frame0=int(((ckt.M1free_UC == 0) & (ckt.M1ref_frame == 0)).sum())))
pd.DataFrame(mech).to_csv(D / "r2_mechanism.csv", index=False)
# ---- verbatim-copy stratum
cache = m1.load(); g = lambda *a: cache.get(m1.key(*a))
gc = [g("free", r.input_text, J1.kw(r.input_text), None) for _, r in J1.gate.iterrows()]
gc = [v for v in gc if v]
verb = dict(gate_c_n=len(gc), gate_c_UC_flag_rate=float(np.mean([bool(v["unrequested"]) for v in gc])), gate_c_WMFfail_rate=float(np.mean([m1.wmf_fail(v) for v in gc])),
            gate_c_dropped_rate=float(np.mean([bool(v["dropped"]) for v in gc])), gate_c_frame_rate=float(np.mean([v["frame_changed"] for v in gc])),
            p18_zero_novelty_n=int(nov0.sum()), p18_zero_novelty_UCflag_rate=float(F[nov0].M1free_UC.mean()), p18_zero_novelty_WMFfail_rate=float(F[nov0].M1free_fail.mean()),
            p18_zero_novelty_rejected_rate=float(F[nov0].L1.mean()))
json.dump(dict(agreement=agree, verbatim=verb, local_models=LOCAL, mechanism=mech), open(D / "r2_validity_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
print(A.pivot(index="metric", columns="subset", values="auroc").round(3).to_string())
print(Pd[Pd.contrast.str.contains("best_trivial|M0g|T6")].round(3).to_string())
print(json.dumps(dict(agreement=agree, verbatim=verb), indent=1, default=float)); print(pd.DataFrame(mech).T.to_string())
