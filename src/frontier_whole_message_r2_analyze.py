"""Round 2 generation-experiment analysis (frontier whole_message). Rules: PLAN.md 'ROUND 2 FREEZE RECORD' R2-C.
Writes r2_outputs.csv, r2_rates.csv, r2_contrasts.csv, r2_noise.csv, r2_g1sim.csv, r2_twocand.csv, r2_policies.csv, r2_selfcheck.csv, r2_summary.json."""
import json, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1
import frontier_whole_message_r2_local as L
import frontier_whole_message_r2_assemble as AS
import analyze_whole_message as AW
import runio
D = m1.D; R = ROOT / "runs/frontier_whole_message_r2"; SEED = 20261102; B = 5000
THR = float(os.environ.get('WM_THR', '0.8')); SUF = '' if THR == 0.8 else f'_posthoc{int(THR*100):02d}'   # 0.8 = declared match threshold; others are post hoc
W = json.load(open(ROOT / "analysis/frontier/multilingual/slp_weights_and_translator.json"))["slp_weights"]
DIMW = dict(polarity=W["NEG"], speech_act=W["ACT"], agent=W["AGT"], certainty=W["CRT"], politeness=W["POL"], time_quantity=W["TIM"]); UCW = W["ADD"]
inp = pd.read_csv(R / "inputs.csv", keep_default_na=False)
g = AS.gens(); g = g[g.text != ""].copy()
meta = inp.set_index(["family_id", "variant", "channel"])
for c in ["ref", "critical_value", "other_value", "writer_id"]:
    g[c] = [meta.loc[(f, v, ch)][c] for f, v, ch in zip(g.family_id, g.variant, g.channel)]
# critical judge + arbiter
items = {}
for l in open(ROOT / "annotation/written/hw_candidates.jsonl"):
    o = json.loads(l); items[o["family_id"]] = o
jr = {(j["text_id"], j["family_id"], j["input_text"]): j for j in map(json.loads, open(R / "judgments.jsonl"))} if (R / "judgments.jsonl").exists() else {}
arb = {(a["text_id"], a["family_id"], a["input_text"]): a["critical"] for a in map(json.loads, open(R / "arbiter.jsonl"))} if (R / "arbiter.jsonl").exists() else {}
def crit(r):
    k = (runio.text_key(r.text), r.family_id, r.input_text); j = jr.get(k)
    return None if j is None else (j["critical"] or arb.get(k))
g["crit"] = [crit(r) for r in g.itertuples()]
g["judged"] = g.crit.notna()
g["CK"] = (g.crit == g.critical_value).astype(int); g["reversal"] = (g.crit == g.other_value).astype(int)
# M1
cache = m1.load()
def free(r): return cache.get(m1.key("free", r.input_text, r.text, None))
def ref(r): return cache.get(m1.key("ref", r.input_text, r.text, r.ref))
fv = [free(r) for r in g.itertuples()]; rv = [ref(r) for r in g.itertuples()]
g["gpt_UC"] = [np.nan if v is None else int(bool(v["unrequested"])) for v in fv]
g["gpt_free_score"] = [np.nan if v is None else v["score_1to5"] / 5 for v in fv]
g["ref_score"] = [np.nan if v is None else v["score_1to5"] / 5 for v in rv]
# local judges
for alias, short in [("qwen2.5-14b", "Q14"), ("mistral-nemo-12b", "Nemo")]:
    p = R / f"local_{alias}.jsonl"
    if p.exists():
        c = {}
        for l in p.read_text().splitlines():
            if l.strip(): o = json.loads(l); c[o["k"]] = o["v"]
        g[f"{short}_p"] = [c.get(L.qkey(("uc", r.input_text, r.text, None)), {}).get("p", np.nan) for r in g.itertuples()]
        g[f"{short}_UC"] = (g[f"{short}_p"] >= .5).astype(float).where(g[f"{short}_p"].notna())
# fragments, edits
fr = {t: AW.nlp(t) for t in g.text.unique()}
def finite(t): return any(x.tag_ in ("VBZ", "VBD", "VBP", "MD") or (x.dep_ == "ROOT" and x.pos_ in ("VERB", "AUX")) for x in fr[t])
g["fragment"] = [int(not finite(t)) for t in g.text]
def wlev(a, b):
    dp = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, y in enumerate(b, 1):
            prev, dp[j] = dp[j], min(dp[j] + 1, dp[j - 1] + 1, prev + (x != y))
    return dp[-1]
tk = lambda s: s.lower().replace("?", "").replace(".", "").replace(",", "").split()
g["E"] = [wlev(tk(r.ref), tk(r.text)) for r in g.itertuples()]
g["nwords"] = [len(tk(t)) for t in g.text]
g["dimw"] = g.dimension.map(DIMW)
UCc = "gpt_UC"
g["harm_w"] = np.maximum(g.reversal * g.dimw, g[UCc].fillna(0) * UCW)
g["composite"] = ((g.reversal == 1) | (g[UCc].fillna(0) == 1) | (g.fragment == 1)).astype(int)
g.to_csv(D / "r2_outputs.csv", index=False)
fams = sorted(inp.family_id.unique()); fidx = {f: i for i, f in enumerate(fams)}
rng = np.random.default_rng(SEED); DR = rng.integers(0, len(fams), (B, len(fams)))
def wide(df, col, key=("family_id", "variant", "channel")):
    return df.set_index(list(key))[col]
def rate_ci(vals, fam):
    """vals: array over rows, fam: family ids of rows -> (est, lo, hi, k, n) family-cluster bootstrap."""
    ok = ~np.isnan(vals); vals = vals[ok]; fam = np.array(fam)[ok]; fi = np.array([fidx[f] for f in fam])
    s = np.bincount(fi, weights=vals, minlength=len(fams)); n = np.bincount(fi, minlength=len(fams)).astype(float)
    est = s.sum() / n.sum(); bs = s[DR].sum(1) / np.maximum(1, n[DR].sum(1))
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5), int(vals.sum()), int(len(vals))
def diff_ci(a, b, fam):
    """paired arrays (same rows)."""
    ok = ~(np.isnan(a) | np.isnan(b)); d = (a - b)[ok]; fam = np.array(fam)[ok]; fi = np.array([fidx[f] for f in fam])
    s = np.bincount(fi, weights=d, minlength=len(fams)); n = np.bincount(fi, minlength=len(fams)).astype(float)
    bs = s[DR].sum(1) / np.maximum(1, n[DR].sum(1)); return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(d)
metrics = ["CK", "reversal", "gpt_UC", "fragment", "composite", "harm_w", "E", "ref_score", "gpt_free_score", "Q14_UC", "Nemo_UC"]
metrics = [m for m in metrics if m in g.columns]
d0 = g[g.draw == 0]
# ---- rates (d0)
rows = []
for (gen, ch, arm), sub in d0.groupby(["generator", "channel", "arm"]):
    for m in metrics:
        v = sub[m].values.astype(float)
        if np.isnan(v).all(): continue
        e, lo, hi, k, n = rate_ci(v, sub.family_id.values)
        per1000 = m in ("CK", "reversal", "gpt_UC", "fragment", "composite", "harm_w", "Q14_UC", "Nemo_UC")
        rows.append(dict(generator=gen, channel=ch, arm=arm, metric=m, est=e, lo=lo, hi=hi, events=k, n=n, per1000=1000 * e if per1000 else np.nan,
                         per1000_lo=1000 * lo if per1000 else np.nan, per1000_hi=1000 * hi if per1000 else np.nan,
                         headline_ok=bool(m not in ("E", "ref_score", "gpt_free_score", "harm_w", "CK") and k >= 10) or m in ("E", "ref_score", "gpt_free_score", "harm_w", "CK")))
Rt = pd.DataFrame(rows); Rt.to_csv(D / "r2_rates.csv", index=False)
# ---- contrasts (d0, paired by input, per generator x channel + pooled equal generator weight)
cont = []
CONTR = [("A2", "A0"), ("A1", "A0"), ("A2", "A1")]
for m in metrics:
    for (a, b) in CONTR:
        per = {}
        for gen in d0.generator.unique():
            for ch in ["chip1", "bare", "both"]:
                s = d0[(d0.generator == gen) & ((d0.channel == ch) | (ch == "both"))]
                A_ = wide(s[s.arm == a], m); B_ = wide(s[s.arm == b], m); ix = A_.index.intersection(B_.index)
                if len(ix) == 0: continue
                fam = [i[0] for i in ix]; x, y = A_.loc[ix].values.astype(float), B_.loc[ix].values.astype(float)
                if np.isnan(x).all() or np.isnan(y).all(): continue
                dd, lo, hi, n = diff_ci(x, y, fam); cont.append(dict(metric=m, contrast=f"{a}-{b}", generator=gen, channel=ch, diff=dd, lo=lo, hi=hi, n=n)); per[(gen, ch)] = (x, y, fam)
        for ch in ["chip1", "bare", "both"]:   # pooled: equal weight per generator (average of per-generator paired differences, same bootstrap draws)
            gens_ = [k for k in per if k[1] == ch]
            if len(gens_) < 2: continue
            fi_ = {}
            est = []; bs = np.zeros(B)
            for k in gens_:
                x, y, fam = per[k]; ok = ~(np.isnan(x) | np.isnan(y)); d = (x - y)[ok]; fi = np.array([fidx[f] for f in np.array(fam)[ok]])
                s_ = np.bincount(fi, weights=d, minlength=len(fams)); n_ = np.bincount(fi, minlength=len(fams)).astype(float)
                est.append(d.mean()); bs += s_[DR].sum(1) / np.maximum(1, n_[DR].sum(1))
            bs /= len(gens_)
            cont.append(dict(metric=m, contrast=f"{a}-{b}", generator="POOLED(equal weight)", channel=ch, diff=float(np.mean(est)), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), n=len(gens_)))
C = pd.DataFrame(cont); C.to_csv(D / "r2_contrasts.csv", index=False)
# ---- noise floor (local judge across draws; terra, llama): per arm rate by draw, sd across d1-d3, flip share, paired contrast per draw
noise = []
if "Q14_UC" in g.columns:
    for gen in ["gpt-6.1-terra", "llama3.1-8b"]:
        for ch in ["chip1", "bare"]:
            for arm in ["A0", "A1", "A2"]:
                sub = g[(g.generator == gen) & (g.channel == ch) & (g.arm == arm)]
                if sub.empty: continue
                byd = {d: sub[sub.draw == d].set_index(["family_id", "variant"])["Q14_UC"] for d in sorted(sub.draw.unique())}
                rates = {d: float(v.mean()) for d, v in byd.items()}
                samp = [rates[d] for d in rates if d > 0]
                if len(samp) >= 2:
                    M_ = pd.concat([byd[d] for d in byd if d > 0], axis=1).dropna()
                    flip = float((M_.nunique(axis=1) > 1).mean())
                    noise.append(dict(generator=gen, channel=ch, arm=arm, **{f"UC_q14_d{d}": rates[d] for d in rates}, sd_d1_d3=float(np.std(samp, ddof=1)), flip_share_d1_d3=flip, n_draws_sampled=len(samp)))
    for gen in ["gpt-6.1-terra", "llama3.1-8b"]:
        for ch in ["chip1", "bare"]:
            for (a, b) in CONTR:
                for d in range(4):
                    sa = g[(g.generator == gen) & (g.channel == ch) & (g.arm == a) & (g.draw == d)].set_index(["family_id", "variant"])["Q14_UC"]
                    sb = g[(g.generator == gen) & (g.channel == ch) & (g.arm == b) & (g.draw == d)].set_index(["family_id", "variant"])["Q14_UC"]
                    ix = sa.index.intersection(sb.index)
                    if len(ix): noise.append(dict(generator=gen, channel=ch, arm=f"{a}-{b}", draw=d, contrast_UC_q14=float((sa.loc[ix] - sb.loc[ix]).mean()), n=len(ix)))
pd.DataFrame(noise).to_csv(D / "r2_noise.csv", index=False)
# ---- stored A0 secondary check (hw1 stored P0 greedy vs fresh d0 A0): CK/reversal from scored.parquet critical
S = pd.read_parquet(ROOT / "runs/hw1/scored.parquet"); S = S[(S.prompt_id == "P0") & S.channel.isin(["chip1", "bare"])]
sec = []
for gen in ["gpt-6.1-terra", "llama3.1-8b"]:
    for ch in ["chip1", "bare"]:
        st = S[(S.model == gen) & (S.channel == ch)].merge(inp[["family_id", "variant", "channel"]].drop_duplicates(), on=["family_id", "variant", "channel"])
        fr_ = d0[(d0.generator == gen) & (d0.channel == ch) & (d0.arm == "A0")]
        if st.empty or fr_.empty: continue
        sec.append(dict(generator=gen, channel=ch, n=len(st), stored_CK=float(st.critical_match.astype(float).mean()), fresh_d0_CK=float(fr_.CK.mean()),
                        stored_same_text_as_fresh=float(np.mean([a == b for a, b in zip(st.sort_values(["family_id", "variant"]).text.values, fr_.sort_values(["family_id", "variant"]).text.values)])) if len(st) == len(fr_) else np.nan))
pd.DataFrame(sec).to_csv(D / "r2_stored_a0_check.csv", index=False)
# ---- G1-sim (A0): first of d0..d3 with CK=1 (critical judge as a perfect monitor; upper bound)
g1 = []
for gen in ["gpt-6.1-terra", "llama3.1-8b"]:
    for ch in ["chip1", "bare"]:
        sub = g[(g.generator == gen) & (g.channel == ch) & (g.arm == "A0")]
        if sub.empty: continue
        pick = []
        for (f, v), s in sub.groupby(["family_id", "variant"]):
            s = s.sort_values("draw"); ok = s[s.CK == 1]; pick.append((ok.iloc[0] if len(ok) else s.iloc[0]).to_dict())
        P = pd.DataFrame(pick)
        for nm, df in [("A0_d0", sub[sub.draw == 0]), ("G1sim_A0", P), ("A1_d0", g[(g.generator == gen) & (g.channel == ch) & (g.arm == "A1") & (g.draw == 0)]), ("A2_d0", g[(g.generator == gen) & (g.channel == ch) & (g.arm == "A2") & (g.draw == 0)])]:
            r_ = dict(generator=gen, channel=ch, policy=nm, n=len(df))
            for m in ["CK", "reversal", "Q14_UC", "Nemo_UC", "fragment", "E"]:
                if m in df.columns and df[m].notna().any(): e, lo, hi, k, n = rate_ci(df[m].values.astype(float), df.family_id.values); r_[m] = e; r_[m + "_lo"] = lo; r_[m + "_hi"] = hi; r_[m + "_k"] = k
            g1.append(r_)
pd.DataFrame(g1).to_csv(D / "r2_g1sim.csv", index=False)
# ---- two-candidate (terra): match = ref_score >= .8
T = g[g.generator == "gpt-6.1-terra"]
def pick(arm, draw): return T[(T.arm == arm) & (T.draw == draw)].set_index(["family_id", "variant", "channel"])
tc = []; pol = []; sc = []
if "A6" in set(T.arm) and T.ref_score.notna().any():
    c1, c2, b4, a0, a1 = pick("A2", 0), pick("A6", 0), pick("A2", 1), pick("A0", 0), pick("A1", 0)
    for ch in ["chip1", "bare"]:
        ix = [i for i in c1.index if i[2] == ch and i in c2.index and i in b4.index and i in a0.index and i in a1.index]
        fam = [i[0] for i in ix]
        rs = lambda df: df.loc[ix].ref_score.values.astype(float)
        m1_, m2_, mb_, ma0, ma1 = rs(c1), rs(c2), rs(b4), rs(a0), rs(a1)
        hit = lambda x: (x >= THR - 1e-9).astype(float)
        series = {"A0 single": hit(ma0), "A1 single": hit(ma1), "A2 single (cand1)": hit(m1_), "A6 alt single": hit(m2_), "B4 (A2 d1) single": hit(mb_),
                  "A2+A6 best-of-2": np.maximum(hit(m1_), hit(m2_)), "A2+B4 best-of-2 (equal budget)": np.maximum(hit(m1_), hit(mb_))}
        for nm, v in series.items():
            e, lo, hi, k, n = rate_ci(v, fam); tc.append(dict(channel=ch, arm=nm, kind="match_rate", est=e, lo=lo, hi=hi, k=k, n=n))
        meanscore = {"A2 single": m1_, "A2+A6 best-of-2": np.maximum(m1_, m2_), "A2+B4 best-of-2": np.maximum(m1_, mb_)}
        for nm, v in meanscore.items():
            e, lo, hi, k, n = rate_ci(v, fam); tc.append(dict(channel=ch, arm=nm, kind="mean_ref_score", est=e, lo=lo, hi=hi, k=np.nan, n=n))
        for nm, a_, b_ in [("A2+A6 best-of-2 minus A2 single", series["A2+A6 best-of-2"], series["A2 single (cand1)"]),
                           ("A2+B4 best-of-2 minus A2 single", series["A2+B4 best-of-2 (equal budget)"], series["A2 single (cand1)"]),
                           ("A2+A6 best-of-2 minus A2+B4 best-of-2", series["A2+A6 best-of-2"], series["A2+B4 best-of-2 (equal budget)"]),
                           ("A2 single minus A0 single", series["A2 single (cand1)"], series["A0 single"]), ("A1 single minus A0 single", series["A1 single"], series["A0 single"])]:
            e, lo, hi, n = diff_ci(a_, b_, fam); tc.append(dict(channel=ch, arm=nm, kind="paired_diff_match", est=e, lo=lo, hi=hi, k=np.nan, n=n))
        for nm, a_, b_ in [("A2+A6 best-of-2 minus A2 single (mean score)", np.maximum(m1_, m2_), m1_), ("A2+A6 minus A2+B4 (mean score)", np.maximum(m1_, m2_), np.maximum(m1_, mb_))]:
            e, lo, hi, n = diff_ci(a_, b_, fam); tc.append(dict(channel=ch, arm=nm, kind="paired_diff_meanscore", est=e, lo=lo, hi=hi, k=np.nan, n=n))
        # policies on cand1 = A2 d0: ask => best-of-2 (A6) at 1 tap; flag = gpt UC of cand1, SelfCheck-unigram vs A2 d1-d3 samples
        cand = c1.loc[ix]; uc = cand.gpt_UC.values.astype(float)
        sam = {d: pick("A2", d) for d in (1, 2, 3)}
        def selfcheck(i):
            y = set(AW.content(AW.nlp(c1.loc[i].text))) or {"_"}
            vals = []
            for d in (1, 2, 3):
                if i in sam[d].index:
                    z = set(AW.content(AW.nlp(sam[d].loc[i].text))); vals.append(len([w for w in y if w not in z]) / len(y))
            return float(np.mean(vals)) if vals else np.nan
        scs = np.array([selfcheck(i) for i in ix])
        nwd = cand.nwords.values.astype(float)
        best2 = series["A2+A6 best-of-2"]; one = series["A2 single (cand1)"]
        def policy(name, flag_rank, qq=None):
            # ask on the top-q ranked (ties broken randomly, averaged 200x) at the ask rate q of the gpt-UC flag
            q = float(np.mean(uc >= 1)) if qq is None else qq; k = int(round(q * len(ix))); res = []
            r_ = np.random.default_rng(SEED)
            for _ in range(200):
                order = np.lexsort((r_.random(len(ix)), -flag_rank)); ask = np.zeros(len(ix)); ask[order[:k]] = 1
                res.append(np.where(ask == 1, best2, one))
            v = np.mean(res, 0); e, lo, hi, kk, n = rate_ci(v, fam)
            pol.append(dict(channel=ch, policy=name + ('' if qq is None else f' @ask {int(qq*100)}%'), ask_rate=k / len(ix), taps_per_1000=1000 * k / len(ix), match_rate=e, lo=lo, hi=hi, n=n))
        e, lo, hi, kk, n = rate_ci(one, fam); pol.append(dict(channel=ch, policy="always-commit (A2 cand1)", ask_rate=0, taps_per_1000=0, match_rate=e, lo=lo, hi=hi, n=n))
        e, lo, hi, kk, n = rate_ci(best2, fam); pol.append(dict(channel=ch, policy="always-ask (A2+A6)", ask_rate=1, taps_per_1000=1000, match_rate=e, lo=lo, hi=hi, n=n))
        e, lo, hi, kk, n = rate_ci(series["A2+B4 best-of-2 (equal budget)"], fam); pol.append(dict(channel=ch, policy="always-ask (A2+B4 resample)", ask_rate=1, taps_per_1000=1000, match_rate=e, lo=lo, hi=hi, n=n))
        policy("flag-ask: gpt M1-free UC flag", uc + 1e-6 * np.nan_to_num(nwd))
        policy("flag-ask: SelfCheck-Unigram-style", np.nan_to_num(scs))
        policy("flag-ask: output length (trivial)", nwd)
        policy("random-ask (matched rate)", np.zeros(len(ix)))
        for qq in (.25, .5):
            policy("flag-ask: gpt M1-free UC flag", uc + 1e-6 * np.nan_to_num(nwd), qq); policy("flag-ask: SelfCheck-Unigram-style", np.nan_to_num(scs), qq)
            policy("flag-ask: output length (trivial)", nwd, qq); policy("random-ask", np.zeros(len(ix)), qq)
        # detector AUROC for cand1 non-match and for gpt UC
        y_nm = 1 - one
        for nm, s_ in [("gpt M1-free UC flag", uc), ("SelfCheck-Unigram-style", scs), ("output word count", nwd), ("Q14 UC p", cand.get("Q14_p", pd.Series(np.nan, index=cand.index)).values.astype(float))]:
            if np.isnan(s_).all(): continue
            ok = ~np.isnan(s_); sc.append(dict(channel=ch, detector=nm, target="cand1 fails intent match (ref<.8)", auroc=AW.auroc(y_nm[ok], s_[ok]), n=int(ok.sum()), pos=int(y_nm[ok].sum())))
        for nm, s_ in [("SelfCheck-Unigram-style", scs), ("output word count", nwd), ("Q14 UC p", cand.get("Q14_p", pd.Series(np.nan, index=cand.index)).values.astype(float))]:
            if np.isnan(s_).all() or np.isnan(uc).all(): continue
            ok = ~np.isnan(s_) & ~np.isnan(uc)
            if uc[ok].sum() and (1 - uc[ok]).sum(): sc.append(dict(channel=ch, detector=nm, target="gpt UC flag on A2 d0", auroc=AW.auroc(uc[ok], s_[ok]), n=int(ok.sum()), pos=int(uc[ok].sum())))
pd.DataFrame(tc).to_csv(D / f"r2_twocand{SUF}.csv", index=False); pd.DataFrame(pol).to_csv(D / f"r2_policies{SUF}.csv", index=False); pd.DataFrame(sc).to_csv(D / f"r2_selfcheck{SUF}.csv", index=False)
# ---- agreement gpt UC vs local UC on d0 + coverage
ag = {}
for sh in ["Q14", "Nemo"]:
    if f"{sh}_UC" in g.columns:
        s = d0[d0.gpt_UC.notna() & d0[f"{sh}_UC"].notna()]
        if len(s): ag[sh] = dict(n=len(s), binary_agreement=float((s.gpt_UC == s[f"{sh}_UC"]).mean()), gpt_UC_rate=float(s.gpt_UC.mean()), local_UC_rate=float(s[f"{sh}_UC"].mean()), spearman_p=float(s[f"{sh}_p"].rank().corr(s.gpt_UC.rank())))
cov = dict(n_rows=len(g), judged=float(g[g.draw == 0].judged.mean()), gpt_UC_coverage_d0=float(d0.gpt_UC.notna().mean()), ref_coverage_terra_d0=float(d0[d0.generator == "gpt-6.1-terra"].ref_score.notna().mean()),
           unresolved_crit_d0=int((~d0.judged).sum()))
json.dump(dict(agreement_local_vs_gpt=ag, coverage=cov, n_families=len(fams), writers=int(inp.writer_id.nunique()), writer_counts=inp.drop_duplicates("family_id").writer_id.value_counts().to_dict()), open(D / "r2_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
print(json.dumps(dict(ag=ag, cov=cov), indent=1, default=float))
