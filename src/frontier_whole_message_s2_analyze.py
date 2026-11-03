"""Stage 2 pilot analysis (API-only slice, gpt-6.1-terra, chip1, 54 families). Rules in PLAN.md deviation log."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_whole_message_m1 as m1, frontier_whole_message_s2_m1jobs as J2
import analyze_whole_message as AW
D = m1.D; R = ROOT / "runs/frontier_whole_message_s2"; SEED = 20261102; B = 10000
cache = m1.load(); g = lambda *a: cache.get(m1.key(*a))
d = pd.read_csv(R / "inputs.csv", keep_default_na=False)
items = J2.items
jr = {(j["text_id"], j["family_id"], j["input_text"]): j for j in map(json.loads, open(R / "judgments.jsonl"))}
arb = {(a["text_id"], a["family_id"], a["input_text"]): a["critical"] for a in map(json.loads, open(R / "arbiter.jsonl"))}
import runio
rows = []
for _, r in d.iterrows():
    it = items[r.family_id]; v = it["variants"][r.variant]; ref = v["source"]
    oth = it["variants"]["B" if r.variant == "A" else "A"]["critical_value"]
    tid = runio.text_key(r.text); k = (tid, r.family_id, r.input_text); j = jr.get(k)
    crit = None if j is None else (j["critical"] or arb.get(k))
    vf, vr = g("free", r.input_text, r.text, None), g("ref", r.input_text, r.text, ref)
    doc = AW.nlp(r.text)
    finite = any(t.tag_ in ("VBZ", "VBD", "VBP", "MD") or (t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX")) for t in doc)
    rw, yw = ref.lower().replace("?", "").replace(".", "").split(), r.text.lower().replace("?", "").replace(".", "").split()
    # word Levenshtein
    dp = list(range(len(yw) + 1))
    for i, a in enumerate(rw, 1):
        prev, dp[0] = dp[0], i
        for jx, b in enumerate(yw, 1):
            prev, dp[jx] = dp[jx], min(dp[jx] + 1, dp[jx - 1] + 1, prev + (a != b))
    rows.append(dict(arm=r.prompt_id, family_id=r.family_id, variant=r.variant, dimension=r.dimension, text=r.text, ref=ref,
        crit=crit, unresolved=int(crit is None), CK=int(crit == v["critical_value"]), reversal=int(crit == oth),
        free_fail=int(m1.wmf_fail(vf)), free_UC=int(bool(vf["unrequested"])), free_drop=int(bool(vf["dropped"])), free_frame=int(vf["frame_changed"]), free_score=vf["score_1to5"] / 5,
        ref_score=vr["score_1to5"] / 5, ref_UC=int(bool(vr["unrequested"])), ref_frame=int(vr["frame_changed"]), E=dp[-1], fragment=int(not finite), nwords=len(yw)))
F = pd.DataFrame(rows); F.to_csv(D / "stage2_outputs.csv", index=False)
arms = ["A0", "A1", "A2", "A3"]
mets = ["CK", "reversal", "free_fail", "free_UC", "free_drop", "free_score", "ref_score", "E", "fragment", "unresolved"]
fams = sorted(F.family_id.unique()); W = {m: F.pivot_table(index="family_id", columns="arm", values=m, aggfunc="sum") for m in mets}
N = F.groupby(["family_id", "arm"]).size().unstack()
rng = np.random.default_rng(SEED); draws = [rng.integers(0, len(fams), len(fams)) for _ in range(B)]
def rate(m, a, ix=None):
    s, n = W[m][a].values, N[a].values
    if ix is None: return s.sum() / n.sum()
    return s[ix].sum() / n[ix].sum()
summ = {}; tab = []
for m in mets:
    for a in arms:
        pt = rate(m, a); bs = [rate(m, a, ix) for ix in draws]
        tab.append(dict(metric=m, arm=a, est=pt, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
P = pd.DataFrame(tab); P.to_csv(D / "stage2_rates.csv", index=False)
cont = []
for m in mets:
    for a, b in [("A2", "A0"), ("A1", "A0"), ("A3", "A0"), ("A2", "A1"), ("A3", "A1")]:
        pt = rate(m, a) - rate(m, b); bs = [rate(m, a, ix) - rate(m, b, ix) for ix in draws]
        cont.append(dict(metric=m, contrast=f"{a}-{b}", diff=pt, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
C = pd.DataFrame(cont); C.to_csv(D / "stage2_contrasts.csv", index=False)
# per dimension
dm = F.groupby(["dimension", "arm"])[["CK", "free_UC", "free_fail", "ref_score", "fragment", "E"]].mean().round(3); dm.to_csv(D / "stage2_by_dimension.csv")
# CK-true subset UC (insufficiency of CK)
ckt = F[F.CK == 1].groupby("arm")[["free_UC", "free_fail", "ref_score"]].mean().round(3); ckt["n"] = F[F.CK == 1].groupby("arm").size()
ckt.to_csv(D / "stage2_ck_true.csv")
# go/no-go
gng = {}
for a in ["A2", "A3", "A1"]:
    uc = C[(C.metric == "free_UC") & (C.contrast == f"{a}-A0")].iloc[0]; ck = C[(C.metric == "CK") & (C.contrast == f"{a}-A0")].iloc[0]
    gng[a] = dict(UC_diff_pp=100 * uc["diff"], CK_diff_pp=100 * ck["diff"], go=bool(uc["diff"] <= -.05 and ck["diff"] >= -.03))
json.dump(dict(go_no_go=gng, n_outputs=len(F), n_families=len(fams)), open(D / "stage2_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 200)
print(P.pivot(index="metric", columns="arm", values="est").round(3)); print(C.round(3).to_string()); print(json.dumps(gng, indent=1)); print(ckt); print(dm.to_string())
