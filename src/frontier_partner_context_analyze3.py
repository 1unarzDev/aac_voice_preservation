"""Round-3 machine-only re-analysis (PLAN A10). Re-uses the round-2 loader/helpers and policy code from analyze2 verbatim (exec of its source segments),
adds: symmetric arm-0 echo filter, C1 restated, C2 decomposition/Xa-Xc/author/writer-cluster, label robustness, extended q grid + negation gate,
C3 abstention, arbiter-only G1 vs chip. Seed 20261103, B=5000.
  python src/frontier_partner_context_analyze3.py
Writes analysis/frontier/partner_context/r3_*.csv, r3_summary.json."""
import json, re, sys, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
src2 = (ROOT / "src/frontier_partner_context_analyze2.py").read_text()
exec(src2[:src2.index("res = {}")], globals())          # loader, vec, boot, perm_p, pooled, contrast, holm
Q_GRID = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90]
S = {}   # summary
def ci(d):
    est, lo, hi, k = boot(d); return dict(est_pp=100 * est, lo_pp=100 * lo, hi_pp=100 * hi, n=k)
def pooled_ci(fn): return ci(pooled(fn))
# ---------- arm-0 echo labels (counterfactual turns)
a0 = {}
for l in open(OUT / "r3_arm0_echo_labels.jsonl"):
    j = json.loads(l); a0[(j["turn"], j["text"])] = j
def lic0(turn, text):
    j = a0.get((turn, text))
    if j is None: return True
    return any(j[k] is None or j[k] == "yes" for k in ("EJ1_echo", "EJ2_echo", "EJ1_reply", "EJ2_reply"))
z = df.turn == "0"
npz = pd.Series(0.0, index=df.index)
itm = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
for ix, r in df[z & (df.lab == "negated")].iterrows():
    v = np.mean([0.0 if lic0(itm[r.family_id]["partner_turns"][t], r.text) else 1.0 for t in XF])
    npz[ix] = v   # for intent affirmative, wrong_all == negated
df["neg_prop0"] = np.where(z, npz, df.neg_prop)
df["wrong_prop0"] = np.where(z, np.where((df.lab == "negated") & (df.intent == "affirmative"), npz, df.wrong_all), df.wrong_prop)
# arm-0 summary: how many arm-0 negated outputs are licensed against counterfactual turns
a0rows = df[z & (df.lab == "negated") & (df.intent == "affirmative")]
S["arm0_negated_affirmative_cells"] = int(len(a0rows)); S["arm0_mean_unlicensed_share"] = float(a0rows.neg_prop0.mean()) if len(a0rows) else None
# ---------- C1 restated
c1 = []
aA = lambda m: vec(m, "chip", XF, "wrong_all", intent="affirmative")
aF = lambda m: vec(m, "chip", XF, "wrong_prop", intent="affirmative")
b_all = lambda m: vec(m, "chip", ["0"], "wrong_all", intent="affirmative")
b_fil = lambda m: vec(m, "chip", ["0"], "neg_prop0", intent="affirmative")
c1 += contrast("C1 PRIMARY unfiltered (echo/agreement counted as harm) minus arm 0", aA, b_all)
c1 += contrast("C1 filtered lower bound, arm 0 unfiltered (round-2 definition)", aF, b_all)
c1 += contrast("C1 filtered lower bound, arm 0 filtered symmetrically", aF, b_fil)
c1 += contrast("C1 unfiltered both arms, arm 0 filtered (shows arm-0 filter is immaterial)", aA, b_fil)
for r in c1:
    r["inside_pm5"] = bool(r["lo_pp"] >= -5 and r["hi_pp"] <= 5); r["inside_pm2"] = bool(r["lo_pp"] >= -2 and r["hi_pp"] <= 2)
    r["ci_excludes_0"] = bool(r["lo_pp"] > 0 or r["hi_pp"] < 0)
    r["label"] = ("detectable (CI excludes 0), " if r["ci_excludes_0"] else "not detectable, ") + ("CI outside original +-2 pp margin" if not r["inside_pm2"] else "CI inside original +-2 pp margin") + "; margin widened +-2 -> +-5 post-pilot"
pd.DataFrame(c1).to_csv(OUT / "r3_c1.csv", index=False)
S["c1"] = [r for r in c1 if r["model"] == "pooled"]
# ---------- C2: range, forms, Xa/Xc confound
c2 = []
base_all = lambda m: vec(m, "bare", ["0"], "neg_all", intent="affirmative")
base_fil = lambda m: vec(m, "bare", ["0"], "neg_prop0", intent="affirmative")
def add(name, col, forms, pp=False, base=base_all, cb=False):
    c2.extend(contrast(name, lambda m: vec(m, "bare", forms, col, intent="affirmative", pp=pp, cb=cb), base, analysis="PP" if pp else "ITT"))
add("C2 all negation incl. echo (upper end)", "neg_all", XF)
add("C2 propositional (primary, lower end)", "neg_prop", XF)
add("C2 propositional, arm 0 filtered symmetrically", "neg_prop", XF, base=base_fil)
for forms, nm in ((["Xa", "Xc"], "Xa+Xc"), (["Xb"], "Xb"), (["Xa"], "Xa"), (["Xc"], "Xc")):
    add(f"C2 propositional {nm} ITT", "neg_prop", forms); add(f"C2 propositional {nm} checker-passing only", "neg_prop", forms, pp=True)
    add(f"C2 all negation {nm} ITT", "neg_all", forms)
pd.DataFrame(c2).to_csv(OUT / "r3_c2.csv", index=False)
S["c2"] = [r for r in c2 if r["model"] == "pooled"]
# ---------- decomposition labels
dl = [json.loads(l) for l in open(OUT / "r3_decomp_labels.jsonl")]
def cls(r):
    a, b = r["D1"], r["D2"]
    if a is None or b is None: return "UNRESOLVED->PARAPHRASE"
    return a if a == b else "UNRESOLVED->PARAPHRASE"
for r in dl: r["cls"] = cls(r); r["agree"] = (r["D1"] == r["D2"]) and r["D1"] is not None
D = pd.DataFrame(dl); D.to_csv(OUT / "r3_decomp_units_labelled.csv", index=False)
cnt = D.groupby(["group", "turn_type", "cls"]).size().unstack(fill_value=0); cnt.to_csv(OUT / "r3_decomp_counts_by_turn.csv")
cm = D.groupby(["group", "model", "cls"]).size().unstack(fill_value=0); cm.to_csv(OUT / "r3_decomp_counts_by_model.csv")
tot = D.groupby(["group", "cls"]).size().unstack(fill_value=0); tot.to_csv(OUT / "r3_decomp_counts_total.csv")
S["decomp"] = dict(total=tot.to_dict("index"), judge_agreement=float(D.agree.mean()), n=int(len(D)), n_neg=int((D.group == "propositional_negation").sum()))
# ---------- author dependence + writer cluster
shared = sorted({f for f in df[df.turn.str.startswith("q14")].family_id}); mask = np.zeros(n, bool); mask[[FI[f] for f in shared]] = True
wr = {json.loads(l)["family_id"]: (json.loads(l).get("writer_id") or json.loads(l)["family_id"]) for l in open(OUT / "items_r2.jsonl")}
wid = np.array([wr[f] for f in fams]); uw = sorted(set(wid)); widx = {w: np.where(wid == w)[0] for w in uw}
def boot_cl(x, clusters=True, ratio=None):
    x = np.asarray(x, float); out = []
    for _ in range(B):
        if clusters: pick = rng.integers(0, len(uw), len(uw)); idx = np.concatenate([widx[uw[k]] for k in pick])
        else: idx = rng.integers(0, len(x), len(x))
        v = x[idx]; v = v[~np.isnan(v)]
        if len(v): out.append(v.mean())
    return float(np.nanmean(x)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))
c2m = pooled(lambda m: vec(m, "bare", XF, "neg_prop", intent="affirmative") - base_all(m))
c2q = pooled(lambda m: vec(m, "bare", XF, "neg_prop", intent="affirmative", prefix="q14") - base_all(m))
c2a = pooled(lambda m: vec(m, "bare", XF, "neg_all", intent="affirmative") - base_all(m))
au = []
def put(name, est_lo_hi, nfam): au.append(dict(estimate=name, est_pp=100 * est_lo_hi[0], lo_pp=100 * est_lo_hi[1], hi_pp=100 * est_lo_hi[2], n_fam=nfam))
put("mistral-authored, all 130 families, family bootstrap", boot_cl(c2m, False), n)
put("mistral-authored, all 130 families, writer-cluster bootstrap", boot_cl(c2m, True), n)
put("mistral-authored, 40 shared families, family bootstrap", boot_cl(np.where(mask, c2m, np.nan), False), int(mask.sum()))
put("qwen14-authored, 40 shared families, family bootstrap", boot_cl(np.where(mask, c2q, np.nan), False), int(mask.sum()))
put("qwen14-authored, 40 shared families, writer-cluster bootstrap", boot_cl(np.where(mask, c2q, np.nan), True), int(mask.sum()))
eq = np.where(mask, 0.5 * (c2m + c2q), np.nan)
put("both authors, equal weight, 40 shared families, family bootstrap", boot_cl(eq, False), int(mask.sum()))
put("both authors, equal weight, 40 shared families, writer-cluster bootstrap", boot_cl(eq, True), int(mask.sum()))
# by-n weighting: 130 mistral vectors + 40 qwen14 vectors (ratio estimator over resampled clusters)
def byn(idx):
    num = np.nansum(c2m[idx]) + np.nansum(c2q[idx]); den = np.sum(~np.isnan(c2m[idx])) + np.sum(~np.isnan(c2q[idx])); return num / den
bn = []
for _ in range(B):
    pick = rng.integers(0, len(uw), len(uw)); bn.append(byn(np.concatenate([widx[uw[k]] for k in pick])))
put("both authors weighted by n (130 + 40 family-vectors), writer-cluster bootstrap", (byn(np.arange(n)), np.percentile(bn, 2.5), np.percentile(bn, 97.5)), n)
cons = min([a for a in au if a["estimate"].startswith(("mistral-authored, 40", "qwen14-authored, 40"))] + [a for a in au if "writer-cluster" in a["estimate"] and a["estimate"].startswith("qwen14")], key=lambda a: a["est_pp"])
cons_lo = min(a["lo_pp"] for a in au if "writer-cluster" in a["estimate"]); 
au.append(dict(estimate="CONSERVATIVE: smaller author-subset effect (qwen14, 40 shared families)", est_pp=cons["est_pp"], lo_pp=cons["lo_pp"], hi_pp=cons["hi_pp"], n_fam=cons["n_fam"]))
au.append(dict(estimate="CONSERVATIVE lower bound: minimum CI lower end over all writer-cluster rows", est_pp=np.nan, lo_pp=cons_lo, hi_pp=np.nan, n_fam=np.nan))
pd.DataFrame(au).to_csv(OUT / "r3_author_writer.csv", index=False); S["author_writer"] = au
# per-model author split
pm = []
for m in MODELS:
    for nm, p in (("mistral", ""), ("qwen14", "q14")):
        v = (vec(m, "bare", XF, "neg_prop", intent="affirmative", prefix=p) - base_all(m)); v = np.where(mask, v, np.nan); e = ci(v); pm.append(dict(model=m, author=nm, **e))
pd.DataFrame(pm).to_csv(OUT / "r3_author_by_model.csv", index=False)
# ---------- label robustness: C2 all-negation under J1 / J2 / final
rob = []
for which in ("critical", "critical_J1", "critical_J2"):
    df["_neg"] = (df[which] == "negated").astype(float); df.loc[df[which].isna(), "_neg"] = np.nan
    rr = contrast(f"C2 all negation, labels = {which}", lambda m: vec(m, "bare", XF, "_neg", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "_neg", intent="affirmative"))
    rob += rr
    rr2 = contrast(f"C1 unfiltered, labels = {which}", lambda m: vec(m, "chip", XF, "_neg", intent="affirmative"), lambda m: vec(m, "chip", ["0"], "_neg", intent="affirmative")); rob += rr2
pd.DataFrame(rob).to_csv(OUT / "r3_label_robustness.csv", index=False); S["label_robustness"] = [r for r in rob if r["model"] == "pooled"]
# ---------- C3 reworded
c3 = []
df["_nonab"] = np.where(df.aff + df.neg_all > 0, df.aff / (df.aff + df.neg_all).replace(0, np.nan), np.nan)
c3 += contrast("C3 Q minus arm 0, affirmative share of ALL outputs", lambda m: vec(m, "bare", ["Q"], "aff", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "aff", intent="affirmative"))
c3 += contrast("C3 Q minus arm 0, affirmative share of NON-ABSTAINED outputs", lambda m: vec(m, "bare", ["Q"], "_nonab", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "_nonab", intent="affirmative"))
c3 += contrast("C3 Q minus arm 0, abstention (unclear/mixed) share", lambda m: vec(m, "bare", ["Q"], "unc", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "unc", intent="affirmative"))
c3 += contrast("C3 Q minus arm 0, negated share", lambda m: vec(m, "bare", ["Q"], "neg_all", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "neg_all", intent="affirmative"))
pd.DataFrame(c3).to_csv(OUT / "r3_c3.csv", index=False); S["c3"] = c3
ab = []
for m in MODELS:
    for t in ("0", "Q"):
        d = df[(df.model == m) & (df.kind == "bare") & (df.turn == t) & (df.intent == "affirmative") & (df.src == "gen") & ~df.cb]
        ab.append(dict(model=m, turn=t, n=len(d), affirmative=d.aff.mean(), negated=d.neg_all.mean(), abstain=d.unc.mean(), nonabstained_aff=d.aff.sum() / max(1, (d.aff + d.neg_all).sum())))
pd.DataFrame(ab).to_csv(OUT / "r3_c3_abstention.csv", index=False)
# ---------- policies with extended q grid (verbatim round-2 code)
seg2 = src2[src2.index("# ----- policies"):src2.index("# lexical sensitivity")].replace("r2_", "r3_")
exec(seg2, globals())
# ---------- negation-frame gate vs matched random ask
NEG_LEX = re.compile(r"\b(not|no|nobody|nothing|none|never|nor|neither|without|but|however|although|unfortunately|sadly|instead|fail\w*|fell through|fall through|fallen through|cancel\w*|call\w* off|collaps\w*|drop\w*|abandon\w*|scrap\w*)\b|n't|n’t", re.I)
def gate_vec(t):
    g = np.full(n, np.nan)
    for f in fams: g[FI[f]] = float(bool(NEG_LEX.search(itm[f]["partner_turns"][t])))
    return g
GATE = {t: gate_vec(t) for t in XF + ["D", "Q"]}
S["gate_ask_rate_by_turn_type"] = {t: float(np.nanmean(v)) for t, v in GATE.items()}
def frame_vals(fr, m, intent, col):
    forms = XF if fr == "X" else [fr]
    chip = np.vstack([vec(m, "chip", [t], col, intent=intent) for t in forms]); com = np.vstack([vec(m, "bare", [t], col, intent=intent) for t in forms])
    g = np.vstack([GATE[t] for t in forms]); return chip, com, g
def mix(fr, q):
    if fr == "X": return q, 1 - q
    if fr == "D": return 1 - q, q
    return 1 - P_NEG, P_NEG
gate_rows = []; gate_con = []
def stream_vals(fr, q, col, m):
    wa, wn = mix(fr, q); out = {}
    ca, ma, g = frame_vals(fr, m, "affirmative", col); cn, mn, _ = frame_vals(fr, m, "negated", col)
    chip = wa * ca + wn * cn; com = wa * ma + wn * mn
    gate_v = g * chip + (1 - g) * com
    pa = float(np.nanmean(g)); rnd_v = pa * chip + (1 - pa) * com
    return dict(chip=np.nanmean(chip, 0), commit=np.nanmean(com, 0), gate=np.nanmean(gate_v, 0), rand=np.nanmean(rnd_v, 0), taps=np.nanmean(g, 0), pa=pa)
for q in (0.1, 0.3, 0.5, 0.9):
    per = {}
    for col in ("wrong_all", "wrong_prop"):
        for fr in ("X", "D", "Q"):
            per[(fr, col)] = {m: stream_vals(fr, q, col, m) for m in MODELS}
    for scope in ("X", "D", "Q", "mixed X+D+Q"):
        for col in ("wrong_all", "wrong_prop"):
            frs = ["X", "D", "Q"] if scope.startswith("mixed") else [scope]
            def agg(key): return np.nanmean(np.vstack([np.mean([per[(fr, col)][m][key] for fr in frs], 0) for m in MODELS]), 0)
            V = {k: agg(k) for k in ("chip", "commit", "gate", "rand", "taps")}
            mixed = scope.startswith("mixed")
            if mixed:   # stream-level matched random: does not know the frame, asks at the gate's overall tap rate
                pa_s = float(np.mean([per[(fr, col)][MODELS[0]]["pa"] for fr in frs])); V["rand_stream"] = pa_s * V["chip"] + (1 - pa_s) * V["commit"]
            for pol, key in (("always_commit_with_context", "commit"), ("cue_oracle_chip_always_ask", "chip"), ("negation_gate_ask", "gate"), ("random_ask_matched_to_gate (frame-aware)", "rand")) + ((("random_ask_matched_stream (frame-blind)", "rand_stream"),) if mixed else ()):
                e = boot(1000 * V[key]); gate_rows.append(dict(scope=scope, q=q, outcome=col, policy=pol, per1000=e[0], lo=e[1], hi=e[2], weighted_per1000=W * e[0], taps_per1000=1000 * float(np.mean(V["taps"] if key in ("gate", "rand", "rand_stream") else (1.0 if key == "chip" else 0.0)))))
            for vs in ("rand", "commit", "chip") + (("rand_stream",) if mixed else ()):
                e = boot(1000 * (V["gate"] - V[vs])); gate_con.append(dict(scope=scope, q=q, outcome=col, contrast=f"negation gate minus {vs}", d_per1000=e[0], lo=e[1], hi=e[2], weighted_d=W * e[0], beats_matched_random=bool(vs in ("rand", "rand_stream") and e[2] < 0)))
pd.DataFrame(gate_rows).to_csv(OUT / "r3_gate_policies.csv", index=False); pd.DataFrame(gate_con).to_csv(OUT / "r3_gate_contrasts.csv", index=False)
# ---------- G1 vs chip, label sources (arbiter-only = Claude blind on changed units)
ar = dict(l.rstrip("\n").split("\t") for l in open(OUT / "r3_g1_arbiter_labels.tsv"))
units = {x["text"]: ar[x["id"]] for x in json.load(open(OUT / "r3_g1_blind_units.json"))}
gdf = df[df.src == "g1"]; cdf = df[(df.src == "gen") & (df.kind == "chip") & (~df.cb)]
k = ["model", "family_id", "variant_value", "turn"]
g_ = gdf[gdf.turn.isin(XF)][k + ["text", "critical", "critical_J1", "critical_J2"]]; c_ = cdf[cdf.turn.isin(XF)][k + ["text", "critical", "critical_J1", "critical_J2"]]
mg = c_.merge(g_, on=k, suffixes=("_c", "_g")); mg["changed"] = mg.text_c != mg.text_g
def lab_of(r, side, scheme):
    if scheme == "claude_blind_on_changed" and r.changed: return units[getattr(r, "text_" + side)]
    return getattr(r, {"final": "critical", "claude_blind_on_changed": "critical", "J1": "critical_J1", "J2": "critical_J2"}[scheme] + "_" + side)
g1rows = []
for scheme in ("final", "J1", "J2", "claude_blind_on_changed"):
    for side in ("c", "g"): mg[f"w_{side}"] = [float(lab_of(r, side, scheme) in ("affirmative", "negated") and lab_of(r, side, scheme) != r.variant_value) for r in mg.itertuples()]
    mg[f"w_{side}"] = mg[f"w_{side}"]
    for side in ("c", "g"): mg[f"{side}_{scheme}"] = mg[f"w_{side}"]
    res_s = {}
    for q in (0.1, 0.3, 0.5):
        vv = []
        for m in MODELS:
            d = mg[mg.model == m]; per = {}
            for side in ("c", "g"):
                v = {}
                for it, w_ in (("affirmative", q), ("negated", 1 - q)):
                    gg = d[d.variant_value == it].groupby("family_id")[f"w_{side}"].mean(); a = np.full(n, np.nan)
                    for f, x in gg.items(): a[FI[f]] = x
                    v[it] = w_ * a
                per[side] = v["affirmative"] + v["negated"]
            vv.append(per["g"] - per["c"])
        e = boot(1000 * np.nanmean(np.vstack(vv), 0)); g1rows.append(dict(label_scheme=scheme, q=q, g1_minus_chip_per1000=e[0], lo=e[1], hi=e[2], weighted_x5=W * e[0], n_changed_pairs=int(mg.changed.sum()), n_pairs=int(len(mg))))
pd.DataFrame(g1rows).to_csv(OUT / "r3_g1_vs_chip_label_sources.csv", index=False); S["g1_vs_chip"] = g1rows
cl = mg[mg.changed].copy(); cl["claude_c"] = [units[t] for t in cl.text_c]; cl["claude_g"] = [units[t] for t in cl.text_g]
S["claude_vs_judge_agreement_changed_texts"] = dict(
    chip=float((cl.claude_c == cl.critical_c).mean()), g1=float((cl.claude_g == cl.critical_g).mean()))
(OUT / "r3_summary.json").write_text(json.dumps(S, indent=1, default=float))
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 70)
for nm in ("c1", "c2"): print(pd.DataFrame(S[nm]).drop(columns=["analysis"], errors="ignore").round(2).to_string())
print(pd.DataFrame(au).round(2).to_string()); print(tot); print(cnt)
print(pd.DataFrame(S["label_robustness"]).round(2)[["contrast", "est_pp", "lo_pp", "hi_pp"]].to_string())
print(pd.DataFrame(g1rows).round(2).to_string()); print(S["claude_vs_judge_agreement_changed_texts"], S["arm0_negated_affirmative_cells"], S["arm0_mean_unlicensed_share"])
