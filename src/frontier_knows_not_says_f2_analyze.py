"""F2 analysis (knows_not_says): R2 re-test with continuous scores S1 (negation mass), S2 (K=256 sampled share), S3 (verbalised confidence).
Rule: analysis/frontier/knows_not_says/PLAN.md 'Follow-up F2'. CPU only. Writes analysis/frontier/knows_not_says/followup/*.csv and followup_summary.json."""
import json, re, sys, collections
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import frontier_knows_not_says_lib as L, layer0
FU = ROOT / "analysis/frontier/knows_not_says/followup"; RUN = ROOT / "runs/frontier_knows_not_says_f2"
B = 10000; MODELS = ["qwen2.5-7b", "llama3.1-8b"]; BONF = 0.05 / 3
pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json"))
U0 = L.build_units({e["elic_item_id"] for e in pilot["e_human"]}); C = U0[(U0.dataset == "cap4") & U0.nocue_neg].reset_index(drop=True)
sub = pd.read_csv(FU / "k256_units.csv"); nw = dict(zip(sub.item_id, sub.neg_weight))
y = C.neg.to_numpy(bool); w = C.w.to_numpy(float); inS = C.item_id.isin(set(sub.item_id)).to_numpy(); wS = w * C.item_id.map(nw).fillna(0).to_numpy()
# lexical (Stage 1 construction)
def lex_features(U):
    kws = U.kw.str.lower().str.findall(r"[a-z']+"); df = collections.Counter(t for ws in kws for t in set(ws))
    vocab = sorted(t for t, n in df.items() if n >= 5); ix = {t: j for j, t in enumerate(vocab)}; X = np.zeros((len(U), 2 + len(vocab)))
    for r, ws in enumerate(kws):
        X[r, 0] = len(ws); X[r, 1] = len(U.kw.iloc[r]) / 10
        for t in ws:
            if t in ix: X[r, 2 + ix[t]] = 1
    return X
lex = L.cv_logreg_oof(lex_features(C), y.astype(float), w, C.item_id.to_numpy(), n_folds=5, l2=1.0)
# scores
S = {m: {} for m in MODELS + ["gpt-6.1-terra"]}
for m in MODELS:
    nm = pd.read_csv(FU / f"negmass_{m}.csv").drop_duplicates("input").set_index("input")
    S[m]["S1_negmass"] = C.input.map(nm.negmass).to_numpy(float); S[m]["S1max_negmax"] = C.input.map(nm.negmass_max).to_numpy(float)
    rows = [json.loads(l) for l in open(RUN / m / "k256.jsonl")]
    cp = RUN / m / "labels_cache.json"; cache = json.load(open(cp)) if cp.exists() else {}
    need = sorted({r["text"] for r in rows} - set(cache))
    if need:
        for t, lab in zip(need, layer0.label_many(need)): cache[t] = lab["polarity"] == "negated"
        json.dump(cache, open(cp, "w"))
    d = collections.defaultdict(list)
    for r in rows: d[r["input"]].append(cache[r["text"]])
    n_per = {k: len(v) for k, v in d.items()}; assert set(n_per.values()) == {256}, collections.Counter(n_per.values())
    S[m]["S2_k256"] = np.array([np.mean(d[i]) if i in d else np.nan for i in C.input])
for m in S:
    rows = [json.loads(l) for l in open(RUN / m / "verbal.jsonl")]; v = {}
    for r in rows:
        mm = re.search(r"\d+(?:\.\d+)?", r["text"]); v[r["input"]] = min(float(mm.group()), 100.0) / 100 if mm else np.nan
    S[m]["S3_verbal"] = C.input.map(v).to_numpy(float)
parse = {m: float(np.isfinite(S[m]["S3_verbal"]).mean()) for m in S}
mult_all = L.boot_multiplicity(C.item_id.to_numpy(), C["sample"].to_numpy(), B)
def auc(s, ww, mask):
    ok = mask & np.isfinite(s); return L.w_auroc(s[ok], y[ok], ww[ok])
def pooled_boot(name, models, ww, mask, mult):
    V = {m: np.array([auc(S[m][name], ww * mult[b], mask) for b in range(B)]) for m in models}
    return V
def lexboot(ww, mask, mult): return np.array([auc(lex, ww * mult[b], mask) for b in range(B)])
out = []; summ = {"parse_rate": parse, "n_units": int(len(C)), "n_pos": int(y.sum()), "subset_units": int(inS.sum()), "boot": B, "bonferroni_alpha": BONF}
lb_all = lexboot(w, np.ones(len(C), bool), mult_all); sm = inS; mult_sub = L.boot_multiplicity(C.item_id.to_numpy()[sm], C["sample"].to_numpy()[sm], B)
# subset multipliers expanded to full length (0 outside subset) so the same helper works
mult_S = np.zeros_like(mult_all); mult_S[:, sm] = mult_sub
lb_sub = lexboot(wS, sm, mult_S)
specs = [("S1_negmass", MODELS, w, np.ones(len(C), bool), mult_all, lb_all), ("S1max_negmax", MODELS, w, np.ones(len(C), bool), mult_all, lb_all),
         ("S2_k256", MODELS, wS, sm, mult_S, lb_sub), ("S3_verbal", MODELS, w, np.ones(len(C), bool), mult_all, lb_all)]
verdicts = {}
for name, models, ww, mask, mult, lb in specs:
    V = pooled_boot(name, models, ww, mask, mult); pool = np.mean([V[m] for m in models], axis=0)
    pt = {m: auc(S[m][name], ww, mask) for m in models}; lpt = auc(lex, ww, mask); ppt = float(np.mean(list(pt.values())))
    d = pool - lb; lo95 = np.percentile(pool, 2.5); hi95 = np.percentile(pool, 97.5)
    dlo, dhi = np.percentile(d, [100 * BONF / 2, 100 * (1 - BONF / 2)])
    tie_pos = {m: float((S[m][name][mask & y & np.isfinite(S[m][name])] == 0).mean()) for m in models}
    tie_all = {m: float((S[m][name][mask & np.isfinite(S[m][name])] == 0).mean()) for m in models}
    a = lo95 > 0.55; b = (ppt - lpt >= 0.03) and dlo > 0; each = all(pt[m] > lpt for m in models)
    verdicts[name] = dict(pooled=ppt, ci=[float(lo95), float(hi95)], per_model=pt, lexical=lpt, lex_ci=[float(x) for x in np.percentile(lb, [2.5, 97.5])],
                          diff=ppt - lpt, diff_ci_bonf=[float(dlo), float(dhi)], a=bool(a), b=bool(b), each_model_above_lex=bool(each), tied0_pos=tie_pos, tied0_all=tie_all,
                          PASS=bool(a and b), FLIP_ELIGIBLE=bool(a and b and each))
    out.append(dict(score=name, row="pooled", auroc=ppt, lo=lo95, hi=hi95, lexical=lpt, diff=ppt - lpt, diff_lo=dlo, diff_hi=dhi, a=a, b=b, each_model_above_lex=each))
    for m in models:
        lo, hi = np.percentile(V[m], [2.5, 97.5]); dm = V[m] - lb; l2, h2 = np.percentile(dm, [100 * BONF / 2, 100 * (1 - BONF / 2)])
        out.append(dict(score=name, row=m, auroc=pt[m], lo=lo, hi=hi, lexical=lpt, diff=pt[m] - lpt, diff_lo=l2, diff_hi=h2, tied0_pos=tie_pos[m], tied0_all=tie_all[m]))
# terra verbal (informational)
m = "gpt-6.1-terra"; pt = auc(S[m]["S3_verbal"], w, np.ones(len(C), bool)); bt = np.array([auc(S[m]["S3_verbal"], w * mult_all[b], np.ones(len(C), bool)) for b in range(B)])
lo, hi = np.percentile(bt, [2.5, 97.5]); l2, h2 = np.percentile(bt - lb_all, [100 * BONF / 2, 100 * (1 - BONF / 2)])
out.append(dict(score="S3_verbal", row=m + " (informational)", auroc=pt, lo=lo, hi=hi, lexical=verdicts["S3_verbal"]["lexical"], diff=pt - verdicts["S3_verbal"]["lexical"], diff_lo=l2, diff_hi=h2))
verdicts["S3_verbal_terra"] = dict(auroc=pt, ci=[float(lo), float(hi)], diff_ci_bonf=[float(l2), float(h2)])
pd.DataFrame(out).to_csv(FU / "r2_retest.csv", index=False)
# policy check: caught - random at 10% asks per 1000 messages
pol = []
def policy(name, score, ww, mask, mult):
    ok = mask & np.isfinite(score); s = np.where(ok, score, -1.0); Wt = ww * ok
    rule = L.fit_budget_rule(s[ok], Wt[ok], 0.10); a = L.apply_rule(s, rule) * ok
    def stat(wv):
        tot = wv.sum(); caught = (wv * a * y).sum() / tot * 1000; rate = (wv * a).sum() / tot; rnd = rate * (wv * y).sum() / tot * 1000; return caught, rnd
    pt = stat(Wt); bs = np.array([stat(Wt * mult[b]) for b in range(B)]); dd = bs[:, 0] - bs[:, 1]
    return dict(score=name, caught_per1000=pt[0], random_per1000=pt[1], diff=pt[0] - pt[1], lo=np.percentile(dd, 2.5), hi=np.percentile(dd, 97.5), n_pos_per1000=float((Wt * y).sum() / Wt.sum() * 1000))
for m in MODELS:
    for name, ww, mask, mult in (("S1_negmass", w, np.ones(len(C), bool), mult_all), ("S2_k256", wS, sm, mult_S), ("S3_verbal", w, np.ones(len(C), bool), mult_all)):
        r = policy(name, S[m][name], ww, mask, mult); r["model"] = m; pol.append(r)
for name, ww, mask, mult in (("lexical", w, np.ones(len(C), bool), mult_all), ("lexical_on_S2_subset", wS, sm, mult_S)):
    r = policy(name, lex, ww, mask, mult); r["model"] = "-"; pol.append(r)
pd.DataFrame(pol).to_csv(FU / "policy10.csv", index=False)
summ["verdicts"] = verdicts; summ["any_pass"] = any(v.get("PASS") for v in verdicts.values() if isinstance(v, dict)); summ["flip"] = any(v.get("FLIP_ELIGIBLE") for v in verdicts.values() if isinstance(v, dict))
json.dump(summ, open(FU / "followup_summary.json", "w"), indent=1, default=float)
print(pd.DataFrame(out).round(3).to_string()); print(pd.DataFrame(pol).round(2).to_string()); print("parse", parse, "any_pass", summ["any_pass"], "flip", summ["flip"])
