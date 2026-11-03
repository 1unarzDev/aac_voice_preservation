"""Round-3 analysis (rules fixed in PLAN.md 'ROUND-3 ANALYSIS PLAN'). Re-runs the round-2 analysis (namespace reuse; refreshes r2_*.csv / summary_r2.json for whatever models exist)
and adds: non-ceiling polarity test, fair-cost polarity table, register break-even / no-address sensitivity / equal-cost / leak-filter, E6 on meaning-check survivors,
Holm family, k-model criteria. Outputs: summary_r3.json, r3_*.csv, r3_auto_tables.md."""
import runpy, sys, json, re, csv, collections
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
g = runpy.run_path(str(HERE / "frontier_multilingual_r2_analyze.py"), run_name="r2")
vec, ratio, bootarr, summ, pval, holm, cp = (g[k] for k in ("vec", "ratio", "bootarr", "summ", "pval", "holm", "cp"))
IDX, FAM, FI, MODELS, TL, OUT, RUN2, W, OUTJ = (g[k] for k in ("IDX", "FAM", "FI", "MODELS", "TL", "OUT", "RUN2", "W", "OUTJ"))
cell, reg_cell_lab, jl = g["cell"], g["reg_cell_lab"], g["jl"]
R3 = {"models": MODELS, "k_models": len(MODELS)}
MD = []
def md(s=""):
    MD.append(s)
def pct(x):
    return "n/a" if x is None or x != x else f"{100 * x:.1f}"
def ci_s(e, ci, scale=100, d=1):
    return f"{scale * e:.{d}f} [{scale * ci[0]:.{d}f}, {scale * ci[1]:.{d}f}]"
isaff = lambda r: r["lab"] == "affirmative"; isneg = lambda r: r["lab"] == "negated"; iscom = lambda r: r["lab"] in ("affirmative", "negated")
PI = 0.027

# ============================================================ A. non-ceiling polarity test (question context)
A_ = {}; rowsA = []
for pre in ("ctxq", "ctxn"):
    ctx_models = [m for m in MODELS if IDX.get(("POL", "en", m, pre + "_bare", "L"))]
    R3[f"{pre}_models"] = ctx_models
    md(f"## A. Non-ceiling polarity test, arm family {pre} ({'yes/no question context' if pre == 'ctxq' else 'question context + refusal prior'}); models with data: {ctx_models}")
    md("| scope | lang | n bare (committed) | P(negated bare) % [CI] | diff vs EN pp [CI] | P(negated, [NOT]) % | P(affirmative, [YES]) % | bare reversals/1000 @pi=2.7% | @pi=50% | cued reversals/1000 @2.7% | @50% |")
    md("|---|---|---|---|---|---|---|---|---|---|---|")
    for sc, ms in ([("pooled", ctx_models)] + [(m, [m]) for m in ctx_models] if ctx_models else []):
        en = vec("POL", "en", ms, pre + "_bare", isneg, iscom)
        for lang in ["en"] + TL:
            nb = vec("POL", lang, ms, pre + "_bare", isneg, iscom)
            has_not = pre == "ctxq"
            nn = vec("POL", lang, ms, pre + "_not", isneg, iscom, variant="B") if has_not else (np.zeros(20), np.ones(20))
            ay = vec("POL", lang, ms, pre + "_yes", isaff, iscom, variant="A")
            pb, cib = ratio("POL", *nb)
            pn = ratio("POL", *nn)[0] if has_not else float("nan"); py, _ = ratio("POL", *ay)
            bb, by = bootarr("POL", *nb), bootarr("POL", *ay)
            bn_ = bootarr("POL", *nn) if has_not else None
            out = {"n_bare": int(nb[1].sum()), "P_neg_bare": [pb, cib], "P_neg_with_NOT": pn, "P_aff_with_YES": py}
            for pi in (PI, 0.5):
                rb = 1000 * (pi * (1 - bb) + (1 - pi) * bb); eb = 1000 * (pi * (1 - pb) + (1 - pi) * pb)
                out[f"bare_rev_per_1000@{pi}"] = summ(rb, eb)
                if has_not:
                    rc = 1000 * (pi * (1 - bn_) + (1 - pi) * (1 - by)); ec = 1000 * (pi * (1 - pn) + (1 - pi) * (1 - py))
                else:  # only the A-direction (affirmative intended under a refusal prior) is measured: reversal prob of [YES] chip
                    rc = 1000 * (1 - pi) * (1 - by); ec = 1000 * (1 - pi) * (1 - py)
                out[f"chip_rev_per_1000@{pi}"] = summ(rc, ec)
            if lang != "en":
                d = bb - bootarr("POL", *en); pt = pb - ratio("POL", *en)[0]
                out["diff_vs_en"] = summ(d, pt)
                out["effect_ge10pp_ci_excl0"] = bool(abs(pt) >= .10 and (out["diff_vs_en"]["ci"][0] > 0 or out["diff_vs_en"]["ci"][1] < 0))
            A_[f"{pre}|{sc}|{lang}"] = out
            dv = out.get("diff_vs_en")
            if has_not:
                md(f"| {sc} | {lang} | {out['n_bare']} | {ci_s(pb, cib)} | {'-' if not dv else ci_s(dv['est'], dv['ci'])} | {pct(pn)} | {pct(py)} | "
                   f"{out[f'bare_rev_per_1000@{PI}']['est']:.0f} | {out['bare_rev_per_1000@0.5']['est']:.0f} | {out[f'chip_rev_per_1000@{PI}']['est']:.1f} | {out['chip_rev_per_1000@0.5']['est']:.1f} |")
            else:  # refusal prior: the context itself states the intended polarity, so reversal accounting does not apply; report cue-vs-context conflict only
                md(f"| {sc} | {lang} | {out['n_bare']} | {ci_s(pb, cib)} | {'-' if not dv else ci_s(dv['est'], dv['ci'])} | n/a | {pct(py)} (cue beats context) | n/a | n/a | n/a | n/a |")
            rowsA.append({"arms": pre, "scope": sc, "lang": lang, "n_bare": out["n_bare"], "P_neg_bare": pb, "P_neg_bare_lo": cib[0], "P_neg_bare_hi": cib[1], "P_neg_with_NOT": pn, "P_aff_with_YES": py,
                          "diff_vs_en": dv["est"] if dv else "", "diff_lo": dv["ci"][0] if dv else "", "diff_hi": dv["ci"][1] if dv else ""})
    md()
R3["A_nonceiling_polarity"] = A_
md()

# ============================================================ B. polarity fair costs
md("## B. Polarity, fair-cost comparison (B messages; reversal = output not negated; pi_neg = 2.7%; per 1,000 messages)")
md("Chip every message = 1 tap on all messages; chip cued-only = 1 tap on the pi_neg share; plain word 'not' = 1 tap (single core word) or 3 keystroke-equivalents, on cued messages only or on all messages (round-2 convention).")
md("| lang | policy | taps/1000 | silent reversals/1000 [CI] | SLP-weighted/1000 |")
md("|---|---|---|---|---|")
B_ = {}; rowsB = []
for lang in ["en"] + TL:
    rb = vec("POL", lang, MODELS, "restored", isneg, lambda r: 1, variant="B")
    pw = vec("POL", lang, MODELS, "plain_neg", isneg, lambda r: 1)
    bare = vec("POL", lang, MODELS, "bare", isneg, lambda r: 1)
    arms = {"always-commit (bare)": (bare, 0), "chip, every message": (rb, 1000), "chip, cued messages only": (rb, 1000 * PI), "plain word 'not', 1 tap, cued only": (pw, 1000 * PI),
            "plain word 'not', 3 keystrokes, cued only": (pw, 3000 * PI), "plain word 'not', 3 keystrokes, every message (r2 convention)": (pw, 3000)}
    for nm, ((n, d), tp) in arms.items():
        e, ci = ratio("POL", n, d)
        rv = 1000 * PI * (1 - e); lo = 1000 * PI * (1 - ci[1]); hi = 1000 * PI * (1 - ci[0])
        B_[f"{lang}|{nm}"] = {"taps_per_1000": tp, "reversals_per_1000": [rv, [lo, hi]], "slp_weighted": rv * W["NEG"]}
        md(f"| {lang} | {nm} | {tp:.0f} | {rv:.1f} [{lo:.1f}, {hi:.1f}] | {rv * W['NEG']:.1f} |")
        rowsB.append({"lang": lang, "policy": nm, "taps_per_1000": tp, "reversals_per_1000": rv, "ci_lo": lo, "ci_hi": hi})
    d_ = bootarr("POL", *pw) - bootarr("POL", *rb)  # plain negated - chip negated: positive = chip better
    pt = pw[0].sum() / pw[1].sum() - rb[0].sum() / rb[1].sum()
    B_[f"{lang}|equal_cost_chip_minus_plain_negated_rate"] = summ(-d_, float(-pt))
    s = summ(-d_, float(-pt))
    md(f"| {lang} | equal-cost contrast (chip cued-only vs plain 1 tap): negated-rate diff pp | 0 | {ci_s(s['est'], s['ci'])} | {'indistinguishable' if s['ci'][0] <= 0 <= s['ci'][1] else 'chip differs'} |")
R3["B_polarity_fair_costs"] = B_
md()

# ============================================================ C. register
LEXW = {"de": ("formell", "informell"), "es": ("formal", "informal"), "fr": ("formel", "informel")}
LEX = {"de": r"nicht|kein\w*|nie|niemals|nichts|du|dich|dir|dein\w*|sie|ihnen|ihr\w*|bitte|euch|euer|ohne",
       "es": r"no|nunca|nada|sin|tu|tus|tú|usted|ustedes|te|ti|vos|su|sus|por favor|jamás|ningún\w*|ninguna",
       "fr": r"ne|pas|jamais|rien|n|tu|te|ton|ta|tes|toi|vous|votre|vos|s'il|plaît|plait|aucun\w*|sans"}
kwmap = {(r["lang"], r["family_id"]): r["t"]["keywords"] for r in jl(OUT / "translations.jsonl") if r.get("t") and r["accepted"] and r["kind"] == "REG"}
def lexok(lang, kw):
    return not [x for x in re.findall(r"[\w']+", kw.lower()) if re.fullmatch(LEX[lang], x)]
fams = FAM["REG"]
def mask(lang, filt):
    if not filt:
        return np.ones(len(fams))
    return np.array([float(lexok(lang, kwmap.get((lang, f), "")) if (lang, f) in kwmap else 0.0) for f in fams])
def leaked(lang, arm, text):
    w = LEXW[lang][0 if "formal" in arm and "informal" not in arm else 1]
    return bool(re.search(r"\b" + w + r"\w*", text, re.I))
def mis2(lab, need, cn):
    if lab in ("T", "V", "mixed"):
        return float(lab != need)
    return float(cn)
def reg_arrays(lang, cn, filt=False):
    mk = mask(lang, filt)
    P = {n: {N: np.zeros(len(fams)) for N in "VT"} for n in ("commit", "chip", "plain_x", "plain_x_leakfilter", "ctx_x", "ask_if_address")}
    TP = {n: np.zeros(len(fams)) for n in P}; CNT = np.zeros(len(fams)); LK = np.zeros(len(fams)); LKD = np.zeros(len(fams))
    for m in MODELS:
        for i, f in enumerate(fams):
            if not mk[i]:
                continue
            c = lambda arm: cell("REG", lang, m, arm, f)
            b = c("bare"); chf, chi = c("chip_formal"), c("chip_informal"); pf, pi_ = c("plain_formal_x"), c("plain_informal_x"); cf, ci_ = c("ctx_formal_x"), c("ctx_informal_x")
            if not all((b, chf, chi, pf, pi_, cf, ci_)):
                continue
            CNT[i] += 1
            addr = float(b[0]["lab"] in ("T", "V", "mixed"))
            for N, ch, pw, cx, arm in (("V", chf, pf, cf, "plain_formal_x"), ("T", chi, pi_, ci_, "plain_informal_x")):
                lk = float(leaked(lang, arm, pw[0]["text"]))
                P["commit"][N][i] += mis2(b[0]["lab"], N, cn); P["chip"][N][i] += mis2(ch[0]["lab"], N, cn); P["plain_x"][N][i] += mis2(pw[0]["lab"], N, cn)
                P["plain_x_leakfilter"][N][i] += 1.0 if lk else mis2(pw[0]["lab"], N, cn)
                P["ctx_x"][N][i] += mis2(cx[0]["lab"], N, cn)
                P["ask_if_address"][N][i] += addr * mis2(ch[0]["lab"], N, cn) + (1 - addr) * mis2(b[0]["lab"], N, cn)
                LK[i] += lk * 0.5; LKD[i] += 0.5
            TP["chip"][i] += 1; TP["plain_x"][i] += 1; TP["ctx_x"][i] += 1; TP["ask_if_address"][i] += addr
            TP["plain_x_leakfilter"][i] += 1 + 0.5 * (float(leaked(lang, "plain_formal_x", pf[0]["text"])) + float(leaked(lang, "plain_informal_x", pi_[0]["text"])))
    return P, TP, CNT, LK, LKD
def mix(P, n, piV):
    return piV * P[n]["V"] + (1 - piV) * P[n]["T"]
names = ["commit", "chip", "plain_x", "plain_x_leakfilter", "ctx_x", "ask_if_address"]
C_ = {}; rowsC = []
md("## C. Register policies = MECHANISM ILLUSTRATION (pi_V assumed, chip treated as ground truth for the requested register, borrowed 0.5 SLP weight)")
md("Mismatch per 1,000 messages; 'harmless' = no-address output not counted (declared, flatters bare and ask-if-address); 'cost' = no-address output counted as a failure to realise the register. taps/1000 per message when every message is cued.")
md("| lang | policy | taps/1000 | mismatch/1000 harmless pi_V=.5 | mismatch/1000 no-address=cost pi_V=.5 | no-address=cost, pi_V=.1 | pi_V=.9 |")
md("|---|---|---|---|---|---|---|")
BE = {}
for lang in TL:
    P0_, TP, CNT, LK, LKD = reg_arrays(lang, 0.0); P1_, _, _, _, _ = reg_arrays(lang, 1.0)
    for n in names:
        e0, c0 = ratio("REG", mix(P0_, n, .5), CNT); e1, c1 = ratio("REG", mix(P1_, n, .5), CNT)
        e1a, _ = ratio("REG", mix(P1_, n, .1), CNT); e1b, _ = ratio("REG", mix(P1_, n, .9), CNT)
        t, _ = ratio("REG", TP[n], CNT)
        C_[f"{lang}|{n}"] = {"taps_per_1000": 1000 * t, "harmless@.5": [1000 * e0, [1000 * c0[0], 1000 * c0[1]]], "cost@.5": [1000 * e1, [1000 * c1[0], 1000 * c1[1]]], "cost@.1": 1000 * e1a, "cost@.9": 1000 * e1b}
        md(f"| {lang}{' (expl.)' if lang == 'es' else ''} | {n} | {1000 * t:.0f} | {1000 * e0:.0f} [{1000 * c0[0]:.0f}, {1000 * c0[1]:.0f}] | {1000 * e1:.0f} [{1000 * c1[0]:.0f}, {1000 * c1[1]:.0f}] | {1000 * e1a:.0f} | {1000 * e1b:.0f} |")
        for piV in (.1, .3, .5, .7, .9):
            rowsC.append({"lang": lang, "policy": n, "piV": piV, "taps_per_1000": 1000 * t, "mismatch_harmless_per_1000": 1000 * ratio("REG", mix(P0_, n, piV), CNT)[0], "mismatch_noaddr_cost_per_1000": 1000 * ratio("REG", mix(P1_, n, piV), CNT)[0]})
    # break-even tap cost (mismatches avoided per tap): policy pays off iff one tap costs less than c*
    for n in ("chip", "ask_if_address", "plain_x"):
        for cn, PP_ in (("harmless", P0_), ("cost", P1_)):
            for piV in (.1, .3, .5, .7, .9):
                bm = bootarr("REG", mix(PP_, "commit", piV) - mix(PP_, n, piV), CNT); bt = bootarr("REG", TP[n], CNT)
                est = ratio("REG", mix(PP_, "commit", piV) - mix(PP_, n, piV), CNT)[0] / ratio("REG", TP[n], CNT)[0]
                cc = bm / bt; cc = cc[~np.isnan(cc)]
                BE[f"{lang}|{n}|{cn}|piV={piV}"] = {"c_star_mismatch_per_tap": est, "ci": [float(np.percentile(cc, 2.5)), float(np.percentile(cc, 97.5))]}
R3["C_register_policies"] = C_; R3["C_break_even_tap_cost"] = BE
md()
md("Break-even tap cost c* (mismatches avoided per tap vs always-commit; the policy pays off only if one tap is cheaper than c* mismatches), pi_V = .5, no-address counted as cost:")
md("| lang | chip | ask-if-address | plain word (1 tap) |"); md("|---|---|---|---|")
for lang in TL:
    md(f"| {lang} | " + " | ".join(f"{BE[f'{lang}|{n}|cost|piV=0.5']['c_star_mismatch_per_tap']:.2f} [{BE[f'{lang}|{n}|cost|piV=0.5']['ci'][0]:.2f}, {BE[f'{lang}|{n}|cost|piV=0.5']['ci'][1]:.2f}]" for n in ("chip", "ask_if_address", "plain_x")) + " |")
md()
md("### C2. Equal-cost register comparison (every cue = 1 tap on cued messages; no-address = cost; pi_V = .5): chip vs plain word, legend-equalised; with the leak filter; and on the keyword-lexicon-filtered family subset")
md("| lang | subset | n msgs | chip | plain | plain + output leak filter | chip - plain pp [CI] | chip - plain-leakfilter pp [CI] | plain outputs echoing the cue word % |")
md("|---|---|---|---|---|---|---|---|---|")
C2 = {}
for lang in TL:
    for filt in (False, True):
        Pm, TPm, CNT, LK, LKD = reg_arrays(lang, 1.0, filt)
        if CNT.sum() == 0:
            continue
        a, b, c = (ratio("REG", mix(Pm, n, .5), CNT) for n in ("chip", "plain_x", "plain_x_leakfilter"))
        d1 = bootarr("REG", mix(Pm, "plain_x", .5), CNT) - bootarr("REG", mix(Pm, "chip", .5), CNT)
        d2 = bootarr("REG", mix(Pm, "plain_x_leakfilter", .5), CNT) - bootarr("REG", mix(Pm, "chip", .5), CNT)
        s1 = summ(d1, float(b[0] - a[0])); s2 = summ(d2, float(c[0] - a[0])); lk = ratio("REG", LK, LKD)[0]
        C2[f"{lang}|{'lexicon_filtered' if filt else 'all'}"] = {"n_msgs": int(CNT.sum()), "families": int((CNT > 0).sum()), "chip_fail": a, "plain_fail": b, "plain_leakfilter_fail": c, "plain_minus_chip": s1, "plainleak_minus_chip": s2, "leak_rate": lk}
        md(f"| {lang} | {'lexicon-filtered keywords (' + str(int((CNT > 0).sum())) + ' fam.)' if filt else 'all (' + str(int((CNT > 0).sum())) + ' fam.)'} | {int(CNT.sum())} | {pct(a[0])} | {pct(b[0])} | {pct(c[0])} | "
           f"{ci_s(s1['est'], s1['ci'])} | {ci_s(s2['est'], s2['ci'])} | {pct(lk)} |")
md("(values are failure rates: share of outputs not in the requested register; positive 'chip - plain' columns here are plain minus chip, i.e. positive = chip better)")
R3["C2_equal_cost_and_leak_filter"] = C2
md()

# ============================================================ D. E6 on meaning-check survivors
cg = OUT / "r3_control_gate.json"
if cg.exists():
    gate = json.load(open(cg)); surv = {(r["cond"], r["lang"], r["family_id"]) for r in gate["rows"] if r["survives"]}
    R3["D_control_gate_survival"] = gate["summary"]
    md("## D. E6 keyword-condition controls on E8 meaning-check survivors only (sol and terra back-translation overlap >= 0.5 under both)")
    md("| lang | condition | survivors/total | V share pooled (n T/V) | same families, bare | address rate | per-model V (n) |"); md("|---|---|---|---|---|---|---|")
    D_ = {}
    for cond in ("bare_nom", "bare_sep", "bare_kw2"):
        for lang in TL:
            tot = gate["summary"].get(f"{lang}|{cond}")
            if not tot:
                continue
            mk = np.array([float((cond, lang, f) in surv) for f in fams])
            if mk.sum() == 0:
                md(f"| {lang} | {cond} | 0/{tot['n']} | - | - | - | - |"); continue
            vv = vec("REG", lang, MODELS, cond, lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
            ad = vec("REG", lang, MODELS, cond, lambda r: r["lab"] in ("T", "V", "mixed"), lambda r: 1)
            bv = vec("REG", lang, MODELS, "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
            e, c = ratio("REG", vv[0] * mk, vv[1] * mk); be, bc = ratio("REG", bv[0] * mk, bv[1] * mk); ae, _ = ratio("REG", ad[0] * mk, ad[1] * mk)
            per = {}
            for m in MODELS:
                x = vec("REG", lang, [m], cond, lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
                per[m] = [None if not (x[1] * mk).sum() else float((x[0] * mk).sum() / (x[1] * mk).sum()), int((x[1] * mk).sum())]
            D_[f"{lang}|{cond}"] = {"survivors": int(mk.sum()), "total": tot["n"], "V_share": [e, c], "n_TV": int((vv[1] * mk).sum()), "bare_same_families": [be, bc], "address_rate": ae, "per_model": per}
            md(f"| {lang} | {cond} | {int(mk.sum())}/{tot['n']} | {pct(e)} [{pct(c[0])}, {pct(c[1])}] (n={int((vv[1] * mk).sum())}) | {pct(be)} (n={int((bv[1] * mk).sum())}) | {pct(ae)} | "
               + "; ".join(f"{m}: {'-' if p[0] is None else pct(p[0])} (n={p[1]})" for m, p in per.items()) + " |")
    R3["D_E6_survivors"] = D_
    md()

# ============================================================ E. inference bookkeeping and k-model criteria
H2 = OUTJ["E2_language_contrasts_holm"]
md("## E. Inference bookkeeping")
md(f"Holm family actually used (ES contrasts excluded because the ES detector failed the 95% gate, 94.2%): DE-FR for each model with data = {len(H2)} tests ({', '.join(H2)}). The declared family would have been up to 18 tests (3 contrasts x 6 models); it was not reached.")
md("| test | est pp [CI] | n DE | n FR | Holm p | language effect confirmed (Holm<.05 and |d|>=30pp) |"); md("|---|---|---|---|---|---|")
for t, v in H2.items():
    md(f"| {t} | {ci_s(v['est'], v['ci'])} | {v['n1']} | {v['n2']} | {v['p_holm']:.3f} | {v['language_effect_confirmed']} |")
md("| V-share cells (bare, per model; n = outputs with a T or V form) | DE | FR | ES (exploratory, excluded from headline) |"); md("|---|---|---|---|")
RG = OUTJ["E2_model_range"]
for m in MODELS:
    cellv = {}
    for lang in TL:
        v = vec("REG", lang, [m], "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        k, n = int(v[0].sum()), int(v[1].sum())
        cellv[lang] = f"{pct(k / n) if n else 'n/a'}% ({k}/{n}), CP [{', '.join(pct(x) for x in cp(k, n))}]"
    md(f"| {m} | {cellv['de']} | {cellv['fr']} | {cellv['es']} |")
md()
md("E1 single register given an address form, with n and Clopper-Pearson 95% interval:")
for lang in TL:
    e = OUTJ["E1_E2_register_bare"][f"pooled|{lang}"]
    md(f"- {lang}: {int(round(e['P_single_given_address'][0] * e['n_address']))}/{e['n_address']} single-register, CP [{pct(e['single_cp'][0])}, {pct(e['single_cp'][1])}]; no address form in {pct(e['P_no_address'][0])}% of {e['n_outputs']} outputs")
md()
md("E3b declared rule (pronoun-address share vs English 'you', pooled; |d| >= 15 pp and CI excluding 0) and the post-hoc clean pronoun-only sensitivity:")
for lang in TL:
    a = OUTJ["E3b_pronoun_address_vs_english"][f"pooled|{lang}"]; b = OUTJ["E3b_clean_pronoun_only"][f"pooled|{lang}"]
    md(f"- {lang}: declared {ci_s(a['est'], a['ci'])} pp, meets declared rule = {a['effect_ge15pp_ci_excl0']}; clean pronoun-only (post-hoc) {ci_s(b['est'], b['ci'])} pp")
R3["E3b_declared_meets"] = {lang: OUTJ["E3b_pronoun_address_vs_english"][f"pooled|{lang}"]["effect_ge15pp_ci_excl0"] for lang in TL}
md()
k = len(MODELS)
md(f"## F. Six-model criteria ({k} of 6 models have data: {MODELS})")
E4m = OUTJ["E4_models_meeting_50pp"]
if k == 6:
    h4 = {lang: len(E4m[lang]) for lang in ["en"] + TL}
    h4ok = all(v >= 5 for v in h4.values())
    rg_ok = any(RG[l]["range"]["est"] >= .30 and RG[l]["range"]["ci"][0] > 0 for l in ("de", "fr"))
    prom = any(OUTJ["E3b_pronoun_address_vs_english"][f"pooled|{l}"]["effect_ge15pp_ci_excl0"] for l in TL) or any(v.get("effect_ge10pp_ci_excl0") for kx, v in OUTJ["E3_polarity_default"].items() if "pooled" in kx)
    R3["six_model"] = {"H4_models_meeting_per_lang": h4, "H4_replicates_5of6_all_langs": h4ok, "E2_range_criterion_de_or_fr": rg_ok, "stop_rule_stop": bool(h4ok and rg_ok), "promote_trigger_E3_E3b": bool(prom)}
    md(f"- H4 (E4 lower bound >= 50 pp) models meeting per language: {h4}; replicates in >=5/6 in every language incl. English: {h4ok}")
    md(f"- E2 model-range criterion (>=30 pp, CI excluding 0, in DE or FR): {rg_ok}")
    md(f"- R2.9 stop rule applied literally: stop iff H4 and H2 criteria hold = {h4ok and rg_ok}; promote trigger (E3/E3b language effect) = {prom} (the E3b trigger rests on the unstable pronoun measure)")
else:
    R3["six_model"] = None
    md(f"- Fewer than 6 models: this is a {k}-model pilot. No 6-model claim; E2 range, E4 5-of-6 and R2.9 stop rule are NOT evaluated. E4 per-model lower bound >= 50 pp: {E4m}")
md("- Model-range of V share (bare, within language): " + "; ".join(f"{l}: {pct(RG[l]['range']['est'])} pp CI [{pct(RG[l]['range']['ci'][0])}, {pct(RG[l]['range']['ci'][1])}]" for l in TL))

json.dump(R3, open(OUT / "summary_r3.json", "w"), indent=1, default=lambda o: None if o != o else float(o) if isinstance(o, np.floating) else int(o) if isinstance(o, np.integer) else str(o))
for nm, rr in (("a_nonceiling_polarity", rowsA), ("b_polarity_fair_costs", rowsB), ("c_register_policies", rowsC)):
    if rr:
        with open(OUT / f"r3_{nm}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rr[0])); w.writeheader(); w.writerows(rr)
(OUT / "r3_auto_tables.md").write_text("\n".join(MD) + "\n")
print("r3 done", MODELS)
