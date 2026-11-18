"""Stage 5 Part 25 (partner_context round 3 human scoring). Rules: annotation/COORDINATOR_STEPS.md section 5 (Part 25), analysis/frontier/partner_context/ANNOTATION_REQUEST.md round-3, PLAN R8/R9.
    . .venv/bin/activate && python src/frontier_stage5_p25_partner_context.py -> analysis/frontier/partner_context/human_*.csv, human_summary.json"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "analysis/frontier/partner_context"; B = 10000; rng = np.random.default_rng(20261117)
key = pd.read_csv(ROOT / "annotation/frontier_partner_context_r3_key.csv")
r = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "annotation/returns_part25/*.csv")))]); r = r[r.practice == 0]
a = pd.read_csv(ROOT / "annotation/assignments/stage5_frontier_assignment.csv"); a = a[a.part == "part25"]
assert set(zip(a.item_id, a.annotator)) == set(zip(r.item_id, r.annotator)) and r.groupby("item_id").size().eq(3).all()
def maj(v):
    v = list(v)
    for c in set(v):
        if v.count(c) >= 2: return c
    return "NOCONS"
CATS = ["a", "b", "c", "d", "e"]; NAMES = dict(a="restates partner", b="reply to partner", c="invented", d="plain statement", e="other/unclear", NOCONS="no consensus")
# ---------------- Part A
ra = r[r.item_id.str.startswith("pc3A")]; A = pd.DataFrame([dict(id=i, human=maj(g.pa.tolist()), n_a=(g.pa == "a").sum(), n_b=(g.pa == "b").sum(), n_c=(g.pa == "c").sum(), n_d=(g.pa == "d").sum(), n_e=(g.pa == "e").sum()) for i, g in ra.groupby("item_id")]).merge(key, on="id")
A.to_csv(OUT / "human_partA_items.csv", index=False)
fams = {f: np.where(A.family_id.to_numpy() == f)[0] for f in A.family_id.unique()}
def shares(df, labs=CATS + ["NOCONS"]):
    return {l: float((df.human == l).mean()) for l in labs}
def cl_boot(df, fn, Bn=B):
    fam = df.family_id.to_numpy(); idx = {f: np.where(fam == f)[0] for f in np.unique(fam)}; fl = list(idx); est = fn(df); bs = []
    for _ in range(Bn):
        p = rng.integers(0, len(fl), len(fl)); ii = np.concatenate([idx[fl[j]] for j in p]); bs.append(fn(df.iloc[ii]))
    return est, np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5)
# vectorised bootstrap for shares: use family count matrix
def share_ci(df, labs):
    fam = df.family_id.to_numpy(); fu = np.unique(fam); M = np.array([[((fam == f) & (df.human.to_numpy() == l)).sum() for l in labs] for f in fu]); N = np.array([(fam == f).sum() for f in fu]); est = M.sum(0) / N.sum(); bs = []
    for _ in range(B):
        p = rng.integers(0, len(fu), len(fu)); bs.append(M[p].sum(0) / N[p].sum())
    bs = np.array(bs); return est, np.percentile(bs, 2.5, 0), np.percentile(bs, 97.5, 0), len(df), len(fu)
rows = []
for grp, g in list(A.groupby("group")) + [("ALL", A)]:
    labs = CATS + ["NOCONS"]; e, lo, hi, n, nf = share_ci(g, labs)
    for i, l in enumerate(labs): rows.append(dict(group=grp, category=l, name=NAMES[l], share=e[i], lo=lo[i], hi=hi[i], k=int((g.human == l).sum()), n=n, n_families=nf))
# derived: paraphrase-like = a or b ; propositional (partner-independent) = d
for grp, g in A.groupby("group"):
    g = g.copy(); g["human"] = g.human.map({"a": "ab", "b": "ab"}).fillna(g.human); e, lo, hi, n, nf = share_ci(g, ["ab"]); rows.append(dict(group=grp, category="a+b", name="restates or replies to partner", share=e[0], lo=lo[0], hi=hi[0], k=int((g.human == "ab").sum()), n=n, n_families=nf))
SH = pd.DataFrame(rows); SH.to_csv(OUT / "human_partA_shares.csv", index=False)
# confusion with machine labels
conf = []
for col in ("machine_class", "machine_class2"):
    x = A.dropna(subset=[col]); ct = pd.crosstab(x[col], x.human); ct.to_csv(OUT / f"human_partA_confusion_{col}.csv"); conf.append((col, ct))
MAP = dict(a="PARAPHRASE", b="PARAPHRASE", c="FABRICATION", d="INDEPENDENT")
def kappa(x, y):
    cats = sorted(set(x) | set(y)); po = np.mean(np.array(x) == np.array(y)); pe = sum(np.mean(np.array(x) == c) * np.mean(np.array(y) == c) for c in cats); return (po - pe) / (1 - pe)
krows = []
for col in ("machine_class", "machine_class2"):
    x = A.dropna(subset=[col]); x = x[x.human.isin(MAP)]; hm = x.human.map(MAP).to_numpy(); mm = x[col].to_numpy(); fam = x.family_id.to_numpy(); fu = np.unique(fam); idx = {f: np.where(fam == f)[0] for f in fu}
    k0 = kappa(hm, mm); bs = []
    for _ in range(3000):
        ii = np.concatenate([idx[fu[j]] for j in rng.integers(0, len(fu), len(fu))]); bs.append(kappa(hm[ii], mm[ii]))
    krows.append(dict(machine_label=col, kappa=k0, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), agreement=float((hm == mm).mean()), n=len(x), human_mapping="a,b->PARAPHRASE c->FABRICATION d->INDEPENDENT (e and no consensus excluded)"))
    # collapsed: independent vs not
    hb = (hm == "INDEPENDENT").astype(int); mb = (mm == "INDEPENDENT").astype(int); krows.append(dict(machine_label=col + " (independent vs partner-linked/invented, binary)", kappa=kappa(hb, mb), agreement=float((hb == mb).mean()), n=len(x)))
pd.DataFrame(krows).to_csv(OUT / "human_partA_machine_kappa.csv", index=False)

# partner-linked (human a or b) vs machine PARAPHRASE, all 197 and the 137 propositional negations; plus by turn form and model (descriptive)
pl = []
for nm, x in (("all Part A (n=197 minus e/NOCONS)", A), ("propositional negations", A[A.group == "propositional_negation"])):
    for col in ("machine_class", "machine_class2"):
        y = x.dropna(subset=[col]); y = y[y.human.isin(["a", "b", "c", "d"])]; hb = y.human.isin(["a", "b"]).astype(int).to_numpy(); mb = (y[col] == "PARAPHRASE").astype(int).to_numpy(); fam = y.family_id.to_numpy(); fu = np.unique(fam); idx = {f: np.where(fam == f)[0] for f in fu}; bs = []
        for _ in range(3000):
            ii = np.concatenate([idx[fu[j]] for j in rng.integers(0, len(fu), len(fu))]); bs.append(kappa(hb[ii], mb[ii]))
        pl.append(dict(set=nm, machine_label=col, n=len(y), kappa=kappa(hb, mb), lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5), agreement=float((hb == mb).mean()), machine_paraphrase_share=float(mb.mean()), human_partner_linked_share=float(hb.mean())))
pd.DataFrame(pl).to_csv(OUT / "human_partA_partner_linked_kappa.csv", index=False); print(pd.DataFrame(pl).round(3).to_string())
Pp = A[A.group == "propositional_negation"]
pd.crosstab(Pp.turn_type, Pp.human, margins=True).to_csv(OUT / "human_partA_by_turn_type.csv"); pd.crosstab(Pp.model, Pp.human, margins=True).to_csv(OUT / "human_partA_by_model.csv")
# human-human agreement (Fleiss)
def fleiss(df, col, cats):
    M = np.array([[(g[col] == c).sum() for c in cats] for _, g in df.groupby("item_id")]); P = (M * (M - 1)).sum(1) / 6; Pe = ((M.sum(0) / M.sum()) ** 2).sum(); k = (P.mean() - Pe) / (1 - Pe)
    bs = []
    for _ in range(2000):
        m_ = M[rng.integers(0, len(M), len(M))]; P_ = (m_ * (m_ - 1)).sum(1) / 6; Pe_ = ((m_.sum(0) / m_.sum()) ** 2).sum(); bs.append((P_.mean() - Pe_) / (1 - Pe_))
    return k, np.percentile(bs, 2.5), np.percentile(bs, 97.5), float((M.max(1) == 3).mean()), float((M.max(1) == 1).mean()), len(M)
fa = fleiss(ra, "pa", CATS)
# re-split of the headline propositional C2 (+8.72 pp pooled, r3_c2.csv row "C2 propositional (primary, lower end)", pooled) by the HUMAN class shares of the 137 propositional negations
c2 = pd.read_csv(OUT / "r3_c2.csv"); c2p = c2[(c2.contrast == "C2 propositional (primary, lower end)") & (c2.model == "pooled")].iloc[0]; c2u = c2[(c2.contrast == "C2 all negation incl. echo (upper end)") & (c2.model == "pooled")].iloc[0]
P = SH[SH.group == "propositional_negation"].set_index("category"); rows = []
mach = pd.read_csv(OUT / "r3_decomp_units_labelled.csv"); mp = mach[mach.group == "propositional_negation"].cls.value_counts(normalize=True).to_dict()
for lab, nm in [("a+b", "restates or replies to partner (partner-driven)"), ("c", "invented (not supported by keywords or remark)"), ("d", "plain statement (partner-independent)"), ("e", "other/unclear"), ("NOCONS", "no consensus")]:
    rr_ = P.loc[lab]; rows.append(dict(component=nm, human_share=rr_.share, share_lo=rr_.lo, share_hi=rr_.hi, pp_of_C2=rr_.share * c2p.est_pp, pp_lo_share_only=rr_.lo * c2p.est_pp, pp_hi_share_only=rr_.hi * c2p.est_pp))
mrows = [("PARAPHRASE (machine, incl unresolved)", mp.get("PARAPHRASE", np.nan)), ("FABRICATION (machine)", mp.get("FABRICATION", np.nan)), ("INDEPENDENT (machine)", mp.get("INDEPENDENT", np.nan))]
RS = pd.DataFrame(rows); RS.attrs["c2"] = (c2p.est_pp, c2p.lo_pp, c2p.hi_pp); RS.to_csv(OUT / "human_partA_resplit_c2.csv", index=False)
pd.DataFrame([dict(machine_component=n_, machine_share_units=v, pp_of_C2=v * c2p.est_pp) for n_, v in mrows]).to_csv(OUT / "human_partA_resplit_c2_machine_reference.csv", index=False)
# ---------------- Part B
rb = r[r.item_id.str.startswith("pc3B")]
Bd = pd.DataFrame([dict(id=i, echo=maj(g.pb1.tolist()), reply=maj(g.pb2.tolist()), n_echo=int((g.pb1 == "yes").sum()), n_reply=int((g.pb2 == "yes").sum())) for i, g in rb.groupby("item_id")]).merge(key, on="id")
Bd["h_echo"] = (Bd.n_echo >= 2).astype(int); Bd["h_reply"] = (Bd.n_reply >= 2).astype(int); Bd["h_either"] = ((Bd.h_echo + Bd.h_reply) > 0).astype(int)
Bd["m_echo"] = (Bd.machine_class == "echo").astype(int); Bd["m_reply"] = (Bd.machine_class == "reply").astype(int); Bd["m_licensed"] = Bd.machine_class.isin(["echo", "reply"]).astype(int)
Bd.to_csv(OUT / "human_partB_items.csv", index=False)
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, c - h), min(1, c + h)
rows = []
for (grp, mc), g in Bd.groupby(["group", "machine_class"]):
    for col, nm in (("h_echo", "human echo (re-uses partner's wording)"), ("h_reply", "human reply (phrased as reply)"), ("h_either", "human echo or reply")):
        k = int(g[col].sum()); lo, hi = wilson(k, len(g)); rows.append(dict(group=grp, machine_class=mc, measure=nm, k=k, n=len(g), rate=k / len(g), wilson_lo=lo, wilson_hi=hi))
for mc, g in Bd[Bd.group == "turn_present"].groupby("machine_class"): pass
TP = Bd[Bd.group == "turn_present"]
for mc_name, mask in (("none (all)", Bd.machine_class == "none"),):
    g = Bd[mask]
    for col in ("h_echo", "h_reply", "h_either"):
        k = int(g[col].sum()); lo, hi = wilson(k, len(g)); rows.append(dict(group="turn_present + no_turn", machine_class=mc_name, measure=col, k=k, n=len(g), rate=k / len(g), wilson_lo=lo, wilson_hi=hi))
HB = pd.DataFrame(rows); HB.to_csv(OUT / "human_partB_by_machine_class.csv", index=False)
# sensitivity / specificity of the machine filter (turn-present units; arm-0 reported separately)
srows = []
for nm, g in (("turn_present (n=56)", TP), ("turn_present + no_turn counterfactual (n=61)", Bd)):
    for hcol, mcol, lab in (("h_echo", "m_echo", "echo flag vs human echo"), ("h_echo", "m_licensed", "machine echo-or-reply flag vs human echo"), ("h_either", "m_licensed", "machine filter (echo or reply) vs human echo-or-reply"), ("h_reply", "m_reply", "reply flag vs human reply")):
        tp = int(((g[hcol] == 1) & (g[mcol] == 1)).sum()); fn = int(((g[hcol] == 1) & (g[mcol] == 0)).sum()); tn = int(((g[hcol] == 0) & (g[mcol] == 0)).sum()); fp = int(((g[hcol] == 0) & (g[mcol] == 1)).sum())
        se = wilson(tp, tp + fn); sp = wilson(tn, tn + fp); ppv = wilson(tp, tp + fp); npv = wilson(tn, tn + fn)
        srows.append(dict(set=nm, comparison=lab, tp=tp, fn=fn, tn=tn, fp=fp, sensitivity=tp / max(tp + fn, 1), sens_lo=se[0], sens_hi=se[1], specificity=tn / max(tn + fp, 1), spec_lo=sp[0], spec_hi=sp[1], ppv=tp / max(tp + fp, 1), npv=tn / max(tn + fn, 1), npv_lo=npv[0], npv_hi=npv[1], kappa=kappa(g[hcol].to_numpy(), g[mcol].to_numpy()) if g[hcol].nunique() > 1 and g[mcol].nunique() > 1 else np.nan))
SS = pd.DataFrame(srows); SS.to_csv(OUT / "human_partB_filter_validity.csv", index=False)
none = Bd[Bd.machine_class == "none"]; none_tp = none[none.group == "turn_present"]
rate_none = dict(echo_rate_none_all=float(none.h_echo.mean()), n_none=len(none), k=int(none.h_echo.sum()), wilson=wilson(int(none.h_echo.sum()), len(none)), echo_rate_none_turn_present=float(none_tp.h_echo.mean()), n_none_tp=len(none_tp), k_tp=int(none_tp.h_echo.sum()), wilson_tp=wilson(int(none_tp.h_echo.sum()), len(none_tp)),
                 either_rate_none_tp=float(none_tp.h_either.mean()), k_either_tp=int(none_tp.h_either.sum()))
rate_none["unvalidated_rule_20pct_triggered"] = bool(rate_none["echo_rate_none_turn_present"] > 0.20)
fb = fleiss(rb, "pb1", ["yes", "no"]); fr = fleiss(rb, "pb2", ["yes", "no"])
summ = dict(n_annotators=int(r.annotator.nunique()), partA=dict(n=len(A), fleiss_kappa=fa[0], lo=fa[1], hi=fa[2], unanimous=fa[3], no_consensus=fa[4]), partB=dict(n=len(Bd), echo_fleiss=fb[:3], reply_fleiss=fr[:3], echo_unanimous=fb[3], reply_unanimous=fr[3]),
            rate_none=rate_none, c2_prop=[c2p.est_pp, c2p.lo_pp, c2p.hi_pp], c2_all=[c2u.est_pp, c2u.lo_pp, c2u.hi_pp], human_vs_machine_kappa=krows)
json.dump(summ, open(OUT / "human_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
print(SH.round(3).to_string()); print(RS.round(3).to_string()); [print(n, "\n", c) for n, c in conf]; print(pd.DataFrame(krows).round(3).to_string()); print(HB.round(3).to_string()); print(SS.round(3).to_string()); print(json.dumps(summ, indent=1, default=float)[:2500])
