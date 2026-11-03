"""Round-2 analysis (plan A3-A7). Cluster bootstrap over families (5,000, seed 20261103), pooled = mean over 4 models.
  python src/frontier_partner_context_analyze2.py
Writes analysis/frontier/partner_context/{r2_contrasts.csv, r2_forms.csv, r2_decomp.csv, r2_policies.csv, r2_policy_contrasts.csv, r2_author_subset.csv, r2_lex_sens.csv, r2_summary.json}."""
import json, re, sys, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "analysis/frontier/partner_context"
rng = np.random.default_rng(20261103); B = 5000
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]; XF = ["Xa", "Xb", "Xc"]
Q_GRID = [0.05, 0.10, 0.20, 0.30, 0.50]; P_NEG = 0.027; W = 5
def load():
    df = pd.read_parquet(ROOT / "runs/frontier_partner_context_r2/scored.parquet"); df["src"] = "gen"
    g = ROOT / "runs/frontier_partner_context_r2g/scored.parquet"
    if g.exists():
        d2 = pd.read_parquet(g); d2["src"] = "g1"; df = pd.concat([df, d2], ignore_index=True)
    p = df.channel.str.split("|", expand=True); df["kind"], df["turn"] = p[0], p[1]; df["cb"] = p[2].eq("cb") if p.shape[1] > 2 else False
    items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
    df["turn_text"] = [None if t == "0" else items[f]["partner_turns"][t] for f, t in zip(df.family_id, df.turn)]
    echo = {}
    for l in open(OUT / "echo_labels.jsonl"):
        j = json.loads(l); echo[(j["turn"], j["text"])] = j
    def fl(turn, text, which):
        j = echo.get((turn, text))
        if j is None: return None
        a, b = j[f"EJ1_{which}"], j[f"EJ2_{which}"]
        if a is None or b is None: return True   # unresolved -> conservative (A3.1)
        return (a == "yes") or (b == "yes")
    df["echo"] = [fl(t, x, "echo") if t else None for t, x in zip(df.turn_text, df.text)]
    df["reply"] = [fl(t, x, "reply") if t else None for t, x in zip(df.turn_text, df.text)]
    # arbiter-resolved overrides handled upstream (arbiter.jsonl feeds attribute.py); lexical sensitivity
    df["lab"] = df.critical
    df["intent"] = df.variant_value
    lic = (df.echo.fillna(False).astype(bool)) | (df.reply.fillna(False).astype(bool))
    df["lic"] = lic
    committed = df.lab.isin(["affirmative", "negated"])
    df["wrong_all"] = (committed & (df.lab != df.intent)).astype(float)
    df["wrong_prop"] = (df.wrong_all.astype(bool) & ~df.lic).astype(float)
    df["unc"] = df.lab.eq("unclear/mixed").astype(float)
    df["neg_all"] = df.lab.eq("negated").astype(float); df["neg_prop"] = (df.lab.eq("negated") & ~df.lic).astype(float)
    df["aff"] = df.lab.eq("affirmative").astype(float)
    return df
df = load(); df = df[df.lab.notna()]
fams = sorted(df.family_id.unique()); FI = {f: i for i, f in enumerate(fams)}; n = len(fams)
meta = json.load(open(OUT / "turns2_meta_mistral-nemo-12b.json"))
passmap = {}
for l in open(OUT / "turns2.jsonl"):
    j = json.loads(l); passmap[(j["family_id"], j["type"])] = j["pass"]

def vec(model, kind, turns, col, src="gen", cb=False, intent=None, pp=False, prefix=""):
    """family vector: mean over `turns` (forms) of col, (model, kind) cells, optionally restricted to intent; NaN if none. pp = per-protocol (passing turns only)."""
    d = df[(df.model == model) & (df.kind == kind) & (df.src == src) & (df.cb == cb) & df.turn.isin([prefix + t for t in turns])]
    if intent: d = d[d.intent == intent]
    if pp: d = d[[passmap.get((f, t.replace("q14", "")), False) for f, t in zip(d.family_id, d.turn)]]
    g = d.groupby("family_id")[col].mean()
    v = np.full(n, np.nan); 
    for f, x in g.items(): v[FI[f]] = x
    return v
def boot(x):
    x = np.asarray(x, float); ok = ~np.isnan(x); x = x[ok]; m = len(x)
    idx = rng.integers(0, m, (B, m)); bm = x[idx].mean(1)
    return float(x.mean()), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), m
def perm_p(x, flips=20000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    s = rng.choice([-1, 1], (flips, len(x))); t = abs(x.mean()); return float((((np.abs((s * x).mean(1)) >= t - 1e-12).sum()) + 1) / (flips + 1))
def pooled(fn):
    return np.nanmean(np.vstack([fn(m) for m in MODELS]), 0)
def contrast(name, fn_a, fn_b, **kw):
    rows = []
    for m in MODELS + ["pooled"]:
        if m == "pooled": d = pooled(lambda mm: fn_a(mm) - fn_b(mm))
        else: d = fn_a(m) - fn_b(m)
        est, lo, hi, k = boot(d); p = perm_p(d)
        rows.append(dict(contrast=name, model=m, est_pp=100 * est, lo_pp=100 * lo, hi_pp=100 * hi, p_perm=p, n_fam=k, **kw))
    return rows
def holm(ps):
    o = np.argsort(ps); adj = np.empty(len(ps)); run = 0
    for r, i in enumerate(o): run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1, run)
    return adj
res = {}
def C1(pp=False, forms=XF, cb=False, prefix="", all_out=False):
    col = "wrong_all" if all_out else "wrong_prop"
    return (lambda m: vec(m, "chip", forms, col, intent="affirmative", cb=cb, pp=pp, prefix=prefix),
            lambda m: vec(m, "chip", ["0"], "wrong_all", intent="affirmative"))
def C2(pp=False, forms=XF, cb=False, prefix="", all_out=False):
    col = "neg_all" if all_out else "neg_prop"
    return (lambda m: vec(m, "bare", forms, col, cb=cb, pp=pp, prefix=prefix, intent="affirmative"), lambda m: vec(m, "bare", ["0"], "neg_all", intent="affirmative"))
conf = []
a, b = C1(); conf += contrast("C1_chip_harm_X_vs_0 (propositional, [YES] cue)", a, b, analysis="ITT")
a, b = C2(); conf += contrast("C2_bare_X_vs_0 (propositional negation)", a, b, analysis="ITT")
conf += contrast("C3_bare_Q_vs_0 (share affirmative)", lambda m: vec(m, "bare", ["Q"], "aff", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "aff", intent="affirmative"), analysis="ITT")
pool = [r for r in conf if r["model"] == "pooled"]; adj = holm([r["p_perm"] for r in pool])
for r, ad in zip(pool, adj): r["p_holm"] = float(ad)
def verdict(r, ms):
    pos = sum(1 for x in ms if x["est_pp"] > 0)
    if r["lo_pp"] >= 0 and r.get("p_holm", 1) < 0.05 and r["est_pp"] >= 5 and pos >= 3: return "CONFIRMED (material)"
    if r["lo_pp"] >= -5 and r["hi_pp"] <= 5: return "CI inside +-5 pp (margin widened from +-2 post-pilot; not an equivalence claim)"
    return "INCONCLUSIVE"
for r in pool:
    ms = [x for x in conf if x["contrast"] == r["contrast"] and x["model"] != "pooled"]; r["verdict"] = verdict(r, ms)
sens = []
for lab, kw in [("PP", dict(pp=True))]:
    a, b = C1(**kw); sens += contrast("C1 per-protocol", a, b, analysis="PP")
    a, b = C2(**kw); sens += contrast("C2 per-protocol", a, b, analysis="PP")
a, b = C1(all_out=True); sens += contrast("C1 upper bound (echo/reply counted as harm)", a, b, analysis="ITT")
a, b = C2(all_out=True); sens += contrast("C2 all negation (echo included)", a, b, analysis="ITT")
for f in XF:
    a, b = C1(forms=[f]); sens += contrast(f"C1 form {f}", a, b, analysis="ITT")
    a, b = C2(forms=[f]); sens += contrast(f"C2 form {f}", a, b, analysis="ITT")
# exploratory: D turn, [NOT] cue override; M4 instruction on X
sens += contrast("expl D-incongruent chip ([NOT] cue) wrong_all vs 0", lambda m: vec(m, "chip", ["D"], "wrong_all", intent="negated"), lambda m: vec(m, "chip", ["0"], "wrong_all", intent="negated"), analysis="ITT")
sens += contrast("expl bare D vs 0 (share affirmative)", lambda m: vec(m, "bare", ["D"], "aff", intent="affirmative"), lambda m: vec(m, "bare", ["0"], "aff", intent="affirmative"), analysis="ITT")
a, b = C2(cb=True); sens += contrast("C2 under M4 (background-only instruction) vs 0", a, b, analysis="ITT")
a, b = C1(cb=True); sens += contrast("C1 under M4 vs 0", a, b, analysis="ITT")
# word channel harm (plain word cue) for X
sens += contrast("word-cue harm X vs 0 (propositional)", lambda m: vec(m, "word", XF, "wrong_prop", intent="affirmative"), lambda m: vec(m, "word", ["0"], "wrong_all", intent="affirmative"), analysis="ITT")
pd.DataFrame(conf + sens).to_csv(OUT / "r2_contrasts.csv", index=False)
# decomposition of negated outputs (share of cells), per model and X form, bare + chip([YES])
dec = []
for m in MODELS:
    for kind, intent in (("bare", "affirmative"), ("chip", "affirmative")):
        for t in XF + ["D", "Q", "0"]:
            d = df[(df.model == m) & (df.kind == kind) & (df.turn == t) & (df.src == "gen") & (~df.cb) & (df.intent == "affirmative")]
            if len(d) == 0: continue
            dec.append(dict(model=m, kind=kind, turn=t, n=len(d), neg_all=d.neg_all.mean(), neg_echo_only=((d.neg_all == 1) & d.echo.fillna(False).astype(bool) & ~d.reply.fillna(False).astype(bool)).mean(),
                            neg_reply=((d.neg_all == 1) & d.reply.fillna(False).astype(bool)).mean(), neg_prop=d.neg_prop.mean(), affirmative=d.aff.mean(), unclear=d.unc.mean()))
pd.DataFrame(dec).to_csv(OUT / "r2_decomp.csv", index=False)
# author subset: q14 turns vs mistral turns on the same 40 families
sub = sorted({f for f in df[df.turn.str.startswith("q14")].family_id})
asub = []
if sub:
    mask = np.zeros(n, bool); mask[[FI[f] for f in sub]] = True
    for nm, fn in (("C2 bare propositional", lambda m, p: vec(m, "bare", XF, "neg_prop", intent="affirmative", prefix=p)), ("C1 chip harm", lambda m, p: vec(m, "chip", XF, "wrong_prop", intent="affirmative", prefix=p))):
        for p, lab in (("", "mistral-author"), ("q14", "qwen14-author")):
            for m in MODELS + ["pooled"]:
                v = pooled(lambda mm: fn(mm, p)) if m == "pooled" else fn(m, p)
                est, lo, hi, k = boot(v[mask]); asub.append(dict(metric=nm, author=lab, model=m, est_pp=100 * est, lo_pp=100 * lo, hi_pp=100 * hi, n_fam=k))
pd.DataFrame(asub).to_csv(OUT / "r2_author_subset.csv", index=False)
# ----- policies
def cellvec(m, kind, t, col, intent, src="gen", cb=False): return vec(m, kind, [t], col, intent=intent, src=src, cb=cb)
def pol_arrays(frame, m, intent):
    forms = XF if frame == "X" else [frame]
    out = {}
    def avg(kind, col, src="gen", cb=False):
        return np.nanmean(np.vstack([cellvec(m, kind, t, col, intent, src, cb) for t in forms]), 0)
    lab_ok = lambda kind, t, cb=False: vec(m, kind, [t], "aff", intent=intent, cb=cb)  # presence only
    out["commit_M0"] = {c: avg("bare", c) for c in ("wrong_all", "wrong_prop", "unc")}
    out["noctx_arm0"] = {c: vec(m, "bare", ["0"], c if c != "wrong_prop" else "wrong_all", intent=intent) for c in ("wrong_all", "wrong_prop", "unc")}
    out["word_M1"] = {c: avg("word", c) for c in ("wrong_all", "wrong_prop", "unc")}
    out["chip_always_ask_M2"] = {c: avg("chip", c) for c in ("wrong_all", "wrong_prop", "unc")}
    if (df.src == "g1").any(): out["guard_G1"] = {c: avg("chip", c, src="g1") for c in ("wrong_all", "wrong_prop", "unc")}
    out["instr_M4_bare"] = {c: avg("bare", c, cb=True) for c in ("wrong_all", "wrong_prop", "unc")}
    out["instr_M4_chip"] = {c: avg("chip", c, cb=True) for c in ("wrong_all", "wrong_prop", "unc")}
    # M5: per (family, form) disagreement between bare|t label and bare|0 label
    dis = []; a_cols = {c: [] for c in ("wrong_all", "wrong_prop", "unc")}; b_cols = {c: [] for c in ("wrong_all", "wrong_prop", "unc")}
    L0 = df[(df.model == m) & (df.kind == "bare") & (df.turn == "0") & (df.intent == intent)].set_index("family_id").lab
    for t in forms:
        d = df[(df.model == m) & (df.kind == "bare") & (df.turn == t) & (df.intent == intent) & (df.src == "gen") & (~df.cb)].set_index("family_id")
        dc = df[(df.model == m) & (df.kind == "chip") & (df.turn == t) & (df.intent == intent) & (df.src == "gen") & (~df.cb)].set_index("family_id")
        z = np.full(n, np.nan); dv = z.copy(); rec = {c: z.copy() for c in a_cols}; recb = {c: z.copy() for c in b_cols}
        for f in fams:
            if f not in d.index or f not in L0.index or f not in dc.index: continue
            i = FI[f]; same = d.loc[f, "lab"] == L0.loc[f]; dv[i] = 0.0 if same else 1.0
            base0 = df[(df.model == m) & (df.kind == "bare") & (df.turn == "0") & (df.intent == intent) & (df.family_id == f)].iloc[0]
            for c in a_cols:
                src_c = d.loc[f, c] if same else base0["wrong_all" if c == "wrong_prop" else c]
                rec[c][i] = src_c; recb[c][i] = d.loc[f, c] if same else dc.loc[f, c]
        dis.append(dv); [a_cols[c].append(rec[c]) for c in a_cols]; [b_cols[c].append(recb[c]) for c in b_cols]
    dvm = np.nanmean(np.vstack(dis), 0)
    out["ablate_fallback_M5a"] = {c: np.nanmean(np.vstack(a_cols[c]), 0) for c in a_cols}
    out["ablate_ask_M5b"] = {c: np.nanmean(np.vstack(b_cols[c]), 0) for c in b_cols}
    out["_taps"] = {"M5b": dvm}
    return out
rows, pc_rows = [], []
frames = ["X", "D", "Q"]; store = {}
for fr in frames:
    for m in MODELS:
        store[(fr, m)] = {it: pol_arrays(fr, m, it) for it in ("affirmative", "negated")}
tapcost = {"word_M1": 1, "chip_always_ask_M2": 1, "guard_G1": 1, "instr_M4_chip": 1, "commit_M0": 0, "noctx_arm0": 0, "instr_M4_bare": 0, "ablate_fallback_M5a": 0}
def fam_value(fr, pol, metric, q, m):
    """per-family value of metric (reversals/1000 style rate) for model m, frame fr, policy pol at q; mixing by intent."""
    A, N_ = store[(fr, m)]["affirmative"], store[(fr, m)]["negated"]
    if fr == "X": wa, wn = q, 1 - q      # intent affirmative is the frame-incongruent one
    elif fr == "D": wa, wn = 1 - q, q
    else: wa, wn = 1 - P_NEG, P_NEG
    def get(S, polname):
        if polname == "random_ask_matched":
            p = np.nanmean(S["_taps"]["M5b"]) ; p = p if not np.isnan(p) else 0  # tap rate approx from this intent; refined below
            return None
        return S[polname]
    if pol == "random_ask_matched":
        pa = np.nanmean(np.concatenate([A["_taps"]["M5b"], N_["_taps"]["M5b"]]))
        def comp(S):
            return {c: pa * S["chip_always_ask_M2"][c] + (1 - pa) * S["commit_M0"][c] for c in ("wrong_all", "wrong_prop", "unc")}
        VA, VN = comp(A), comp(N_); taps = pa
    else:
        VA, VN = A[pol], N_[pol]
        if pol == "ablate_ask_M5b": taps = 0.5 * (A["_taps"]["M5b"] + N_["_taps"]["M5b"])
        else: taps = tapcost.get(pol, 0)
    if metric == "taps": return np.broadcast_to(taps, (n,)).astype(float) if np.isscalar(taps) else np.asarray(taps, float)
    return wa * VA[metric] + wn * VN[metric]
pols = ["noctx_arm0", "commit_M0", "word_M1", "chip_always_ask_M2", "guard_G1", "instr_M4_bare", "instr_M4_chip", "ablate_fallback_M5a", "ablate_ask_M5b", "random_ask_matched"]
pols = [p for p in pols if p != "guard_G1" or (df.src == "g1").any()]
metrics = ("wrong_prop", "wrong_all", "unc", "taps")
for fr in frames:
    for q in (Q_GRID if fr != "Q" else [None]):
        qq = 0.1 if q is None else q
        vals = {}
        for pol in pols:
            for met in metrics:
                vals[(pol, met)] = np.nanmean(np.vstack([fam_value(fr, pol, met, qq, m) for m in MODELS]), 0)
        for pol in pols:
            r = dict(frame=fr, q=q, policy=pol)
            for met in metrics:
                est, lo, hi, k = boot(1000 * vals[(pol, met)])
                r[f"{met}_per1000"] = est; r[f"{met}_lo"] = lo; r[f"{met}_hi"] = hi
            r["weighted_prop_per1000"] = W * r["wrong_prop_per1000"]; r["weighted_all_per1000"] = W * r["wrong_all_per1000"]
            r["weighted_all_lo"] = W * r["wrong_all_lo"]; r["weighted_all_hi"] = W * r["wrong_all_hi"]
            r["weighted_prop_lo"] = W * r["wrong_prop_lo"]; r["weighted_prop_hi"] = W * r["wrong_prop_hi"]
            rows.append(r)
        for pol in pols:
            refs = ["commit_M0", "random_ask_matched"] + (["chip_always_ask_M2"] if pol in ("word_M1", "guard_G1", "instr_M4_chip") else []) + (["noctx_arm0"] if pol in ("commit_M0", "instr_M4_bare", "ablate_fallback_M5a") else [])
            for ref in refs:
                if pol == ref: continue
                for met in ("wrong_prop", "wrong_all"):
                    d = 1000 * (vals[(pol, met)] - vals[(ref, met)]); est, lo, hi, k = boot(d)
                    pc_rows.append(dict(frame=fr, q=q, policy=pol, vs=ref, metric=met, d_per1000=est, lo=lo, hi=hi, weighted_d=W * est, taps_per1000=1000 * float(np.nanmean(vals[(pol, "taps")])), n_fam=k))
pd.DataFrame(rows).to_csv(OUT / "r2_policies.csv", index=False); pd.DataFrame(pc_rows).to_csv(OUT / "r2_policy_contrasts.csv", index=False)
# per-model policy table (X frame, q=0.1) for transparency
mm = []
for m in MODELS:
    for pol in pols:
        if pol == "random_ask_matched": continue
        v = {met: float(np.nanmean(fam_value("X", pol, met, 0.1, m))) * 1000 for met in metrics}; mm.append(dict(model=m, policy=pol, **v))
pd.DataFrame(mm).to_csv(OUT / "r2_policies_by_model_X_q10.csv", index=False)
# lexical sensitivity: echo_lex rule (A3.1)
STOPW = set("a an the of to in on at for with by is are was were be been it its this that these those do does did have has had will would can could and or but if so as from about up out there their they them he she his her we you i my your our me us what who which when where how why not no yes any some more than then just very also too into over after before again heard hear guess think said say says nobody nothing none never".split())
def stem(w): return re.sub(r"[^a-z]", "", w.lower())[:4]
items = {json.loads(l)["family_id"]: json.loads(l) for l in open(OUT / "items_r2.jsonl")}
def lex_echo(row):
    if row.lab != "negated" or row.turn_text is None: return np.nan
    kw = {stem(w) for w in re.findall(r"[A-Za-z']+", (items[row.family_id]["bare"] + " " + (items[row.family_id].get("noncritical") or "")))}
    tw = [w.lower() for w in re.findall(r"[A-Za-z']+", row.turn_text)]; ow = [w.lower() for w in re.findall(r"[A-Za-z']+", row.text)]
    spec = {stem(w) for w in tw if w not in STOPW and stem(w) not in kw}
    tri = {tuple(tw[i:i + 3]) for i in range(len(tw) - 2)}; otri = {tuple(ow[i:i + 3]) for i in range(len(ow) - 2)}
    return float(bool(tri & otri) or bool(spec & {stem(w) for w in ow}))
def lex_reply(row):
    t = row.text.lower().strip(); return float(bool(re.match(r"(yes|yeah|oh|right|ah|really|i heard|i know)\b", t)) or "heard" in t)
sub_df = df[(df.src == "gen") & (df.turn.isin(XF)) & (df.kind.isin(["bare", "chip"])) & (~df.cb) & (df.lab == "negated") & (df.intent == "affirmative")].copy()
sub_df["lex_echo"] = sub_df.apply(lex_echo, axis=1); sub_df["lex_reply"] = sub_df.apply(lex_reply, axis=1)
sub_df["lex_lic"] = ((sub_df.lex_echo == 1) | (sub_df.lex_reply == 1))
lx = [dict(model=m, kind=k, n_negated=len(g), judge_licensed=g.lic.mean(), lex_licensed=g.lex_lic.mean(), agree=(g.lic == g.lex_lic).mean(),
           judge_prop_share=1 - g.lic.mean(), lex_prop_share=1 - g.lex_lic.mean()) for (m, k), g in sub_df.groupby(["model", "kind"])]
pd.DataFrame(lx).to_csv(OUT / "r2_lex_sens.csv", index=False)
# lexical-rule re-estimate of C1/C2 pooled
def lex_c(kind, intent="affirmative"):
    vv = []
    for m in MODELS:
        d = df[(df.model == m) & (df.kind == kind) & (df.turn.isin(XF)) & (df.src == "gen") & (~df.cb) & (df.intent == intent)].copy()
        d["lex_lic"] = d.apply(lambda r: (lex_echo(r) == 1) or (lex_reply(r) == 1) if r.lab == "negated" else False, axis=1)
        d["h"] = ((d.lab == "negated") & (~d.lex_lic)).astype(float)
        g = d.groupby("family_id").h.mean(); v = np.full(n, np.nan)
        for f, x in g.items(): v[FI[f]] = x
        vv.append(v)
    return np.nanmean(np.vstack(vv), 0)
lexres = {}
for nm, kind in (("C2_lex", "bare"), ("C1_lex", "chip")):
    base = pooled(lambda mm_: vec(mm_, kind, ["0"], "neg_all", intent="affirmative"))
    est, lo, hi, k = boot(lex_c(kind) - base); lexres[nm] = dict(est_pp=100 * est, lo_pp=100 * lo, hi_pp=100 * hi)
# summary
tot = {"n_families": n, "models": MODELS, "rows_scored": int(len(df)), "judge_missing_label_rows_dropped": "see round2.md",
       "confirmatory": pool, "lex_sensitivity": lexres,
       "turn_check_pass_after_retry": meta["pass_after_retry"], "turn_check_first_try": meta["pass_first_try"]}
(OUT / "r2_summary.json").write_text(json.dumps(tot, indent=1, default=float))
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(pd.DataFrame(pool).round(3).to_string()); print(json.dumps(lexres, indent=1))
print(pd.DataFrame(dec).round(3).to_string())
