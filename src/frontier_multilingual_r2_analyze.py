"""Round-2 analysis (rules fixed in PLAN.md 'ROUND-2 ANALYSIS PLAN'). Family-cluster bootstrap (10,000, seed 20261102)."""
import sys, json, csv, glob, collections, re, itertools
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
from frontier_multilingual_register import label as det, _label_v1

NB = 10000
rng = np.random.default_rng(20261102)
MODELS = [m for m in MODELS6 if (RUN2 / f"gen_{m}.jsonl").exists()]
TL = ["de", "es", "fr"]
pol_lab = json.load(open(OUT / "r2_pol_labels.json"))
reg_arb = json.load(open(OUT / "r2_reg_arbiter_sol.json"))
STRICT = None
if (OUT / "r2_strict_gate.json").exists():
    STRICT = json.load(open(OUT / "r2_strict_gate.json"))

# ------------------------------------------------------------ labels
def plabel(lang, text):
    x = pol_lab.get(f"{lang}|{text}")
    if not x or not x.get("direct"):
        return None
    if lang == "en":
        return x["direct"]
    if x.get("route") and x["route"] == x["direct"]:
        return x["direct"]
    return None  # instrument disagreement -> unresolved (no fallback), counted


def rlabel(lang, text):
    if lang == "en":
        return "addr" if re.search(r"\b(you|your|yours|yourself)\b", text, re.I) else "none"
    d = det(lang, text)
    if d == "ambig":
        a = reg_arb.get(f"{lang}|{text}")
        return a if a in ("T", "V", "none", "mixed") else None
    return d

rows = []
unres = collections.Counter()
for m in MODELS:
    for r in jl(RUN2 / f"gen_{m}.jsonl"):
        if not r["ok"] or not r["text"]:
            continue
        r["lab"] = plabel(r["lang"], r["text"]) if r["kind"] == "POL" else rlabel(r["lang"], r["text"])
        if r["lab"] is None:
            unres[(r["kind"], r["lang"])] += 1
            continue
        rows.append(r)
g1rows = []
for m in MODELS:
    if (RUN2 / f"g1_{m}.jsonl").exists():
        for r in jl(RUN2 / f"g1_{m}.jsonl"):
            r["lab"] = plabel(r["lang"], r["text"]) if r["kind"] == "POL" else rlabel(r["lang"], r["text"])
            r["lab0"] = plabel(r["lang"], r["orig"]) if r["kind"] == "POL" else rlabel(r["lang"], r["orig"])
            g1rows.append(r)
IDX = collections.defaultdict(list)
for r in rows:
    IDX[(r["kind"], r["lang"], r["model"], r["arm"], r["pset"])].append(r)
FAM = {"POL": sorted({r["family_id"] for r in rows if r["kind"] == "POL"}), "REG": sorted({r["family_id"] for r in rows if r["kind"] == "REG"})}
BI = {k: rng.integers(0, len(v), (NB, len(v))) for k, v in FAM.items()}
FI = {k: {f: i for i, f in enumerate(v)} for k, v in FAM.items()}


def vec(kind, lang, models, arm, num, den=lambda r: 1, pset="L", variant=None, rs=None):
    n = np.zeros(len(FAM[kind])); d = np.zeros(len(FAM[kind]))
    for m in models:
        for r in (rs if rs is not None else IDX.get((kind, lang, m, arm, pset), [])):
            if rs is not None and r["model"] != m:
                continue
            if variant and r["variant"] != variant:
                continue
            i = FI[kind][r["family_id"]]
            n[i] += num(r); d[i] += den(r)
    return n, d


def ratio(kind, n, d):
    """point, boot array, ci"""
    bi = BI[kind]
    with np.errstate(all="ignore"):
        est = n.sum() / d.sum() if d.sum() else np.nan
        b = n[bi].sum(1) / d[bi].sum(1)
    b = b[~np.isnan(b)]
    ci = [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))] if len(b) > 50 else [np.nan, np.nan]
    return float(est), ci


def bootarr(kind, n, d):
    with np.errstate(all="ignore"):
        return n[BI[kind]].sum(1) / d[BI[kind]].sum(1)


def summ(b, est=None):
    bb = b[~np.isnan(b)]
    e = float(np.nanmean(b)) if est is None else est
    return {"est": e, "ci": [float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))], "n_boot": int(len(bb))}


def pval(b):
    bb = b[~np.isnan(b)]
    return float(min(1.0, 2 * min((bb <= 0).mean(), (bb >= 0).mean()))) if len(bb) else np.nan


def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [None] * len(ps); mx = 0
    for k, i in enumerate(o):
        mx = max(mx, (len(ps) - k) * ps[i]); adj[i] = min(1.0, mx)
    return adj


from scipy.stats import beta
def cp(k, n):
    if n == 0:
        return [np.nan, np.nan]
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1); hi = 1.0 if k == n else beta.ppf(0.975, k + 1, n - k)
    return [float(lo), float(hi)]

OUTJ = {"models": MODELS, "unresolved_label_rows": {f"{k[0]}|{k[1]}": v for k, v in unres.items()}, "n_rows": len(rows)}
csvrows = collections.defaultdict(list)
ISADD = lambda r: r["lab"] in ("T", "V", "mixed")
ADDR = lambda r: r["lab"] in ("T", "V", "mixed", "addr")

# ============================================================ E1, E2
scopes = [("pooled", MODELS)] + [(m, [m]) for m in MODELS]
E1 = {}
for sc, ms in scopes:
    for lang in TL:
        n_all = vec("REG", lang, ms, "bare", lambda r: 1)[0]
        none = vec("REG", lang, ms, "bare", lambda r: r["lab"] == "none")
        adr = vec("REG", lang, ms, "bare", ISADD)
        sing = vec("REG", lang, ms, "bare", lambda r: r["lab"] in ("T", "V"), ISADD)
        mix = vec("REG", lang, ms, "bare", lambda r: r["lab"] == "mixed", ISADD)
        V = vec("REG", lang, ms, "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        tot = int(n_all.sum()); k_add = int(adr[0].sum()); k_s = int(sing[0].sum())
        E1[f"{sc}|{lang}"] = {"n_outputs": tot, "n_address": k_add, "P_no_address": ratio("REG", *none), "P_single_given_address": ratio("REG", *sing),
                               "single_cp": cp(k_s, k_add), "P_mixed_given_address": ratio("REG", *mix), "V_share": ratio("REG", *V), "n_TV": int(V[1].sum()), "V": int(V[0].sum())}
        csvrows["e1_register_commitment"].append({"scope": sc, "lang": lang, **{k: json.dumps(v) if isinstance(v, (list, tuple)) else v for k, v in E1[f"{sc}|{lang}"].items()}})
OUTJ["E1_E2_register_bare"] = E1

# detector validation gate status (from r2_validate.py output)
VAL = json.load(open(OUT / "r2_detector_validation.json")) if (OUT / "r2_detector_validation.json").exists() else {}
es_pass = bool(VAL.get("es", {}).get("pass"))
OUTJ["es_detector_gate_pass"] = es_pass
pairs = [("de", "fr")] + ([("de", "es"), ("es", "fr")] if es_pass else [])
H2 = {}
tests = []
for m in MODELS:
    for l1, l2 in pairs:
        a = vec("REG", l1, [m], "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        b = vec("REG", l2, [m], "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        bb = bootarr("REG", *a) - bootarr("REG", *b)
        pt = (a[0].sum() / a[1].sum() if a[1].sum() else np.nan) - (b[0].sum() / b[1].sum() if b[1].sum() else np.nan)
        H2[f"{m}|{l1}-{l2}"] = {**summ(bb, float(pt)), "p": pval(bb), "n1": int(a[1].sum()), "n2": int(b[1].sum())}
        tests.append(f"{m}|{l1}-{l2}")
adj = holm([H2[t]["p"] if H2[t]["p"] == H2[t]["p"] else 1.0 for t in tests])
for t, a_ in zip(tests, adj):
    H2[t]["p_holm"] = a_
    H2[t]["language_effect_confirmed"] = bool(a_ < 0.05 and abs(H2[t]["est"]) >= 0.30)
    csvrows["e2_language_contrasts"].append({"test": t, **{k: json.dumps(v) if isinstance(v, list) else v for k, v in H2[t].items()}})
OUTJ["E2_language_contrasts_holm"] = H2
# model range
RANGE = {}
for lang in TL:
    bs = []
    for m in MODELS:
        v = vec("REG", lang, [m], "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        bs.append(bootarr("REG", *v))
    A = np.vstack(bs)
    rg = np.nanmax(A, 0) - np.nanmin(A, 0)
    pts = [vec("REG", lang, [m], "bare", lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V")) for m in MODELS]
    ps = [x[0].sum() / x[1].sum() if x[1].sum() else np.nan for x in pts]
    RANGE[lang] = {"V_share_by_model": dict(zip(MODELS, [None if p != p else float(p) for p in ps])), "range": summ(rg, float(np.nanmax(ps) - np.nanmin(ps)))}
OUTJ["E2_model_range"] = RANGE

# ============================================================ E3b commitment vs English (pronoun only)
E3B = {}
pron = lambda lang: (lambda r: 1)
def pron_num(lang):
    if lang == "en":
        return lambda r: r["lab"] == "addr"
    return lambda r: _label_v1(lang, r["text"]) != "none"
for sc, ms in scopes:
    en = vec("REG", "en", ms, "bare", pron_num("en"))
    for lang in TL:
        t = vec("REG", lang, ms, "bare", pron_num(lang), rs=None)
        # pronoun detector needs raw v1 on every row: rebuild with rows
        tt = np.zeros(20); td = np.zeros(20)
        for m in ms:
            for r in IDX.get(("REG", lang, m, "bare", "L"), []):
                tt[FI["REG"][r["family_id"]]] += _label_v1(lang, r["text"]) != "none"; td[FI["REG"][r["family_id"]]] += 1
        ed = vec("REG", "en", ms, "bare", lambda r: 1)
        bb = bootarr("REG", tt, td) - bootarr("REG", en[0], ed[0])
        E3B[f"{sc}|{lang}"] = {"P_pronoun_target": float(tt.sum() / td.sum()), "P_you_english": float(en[0].sum() / ed[0].sum()), **summ(bb, float(tt.sum() / td.sum() - en[0].sum() / ed[0].sum()))}
        E3B[f"{sc}|{lang}"]["effect_ge15pp_ci_excl0"] = bool(abs(E3B[f"{sc}|{lang}"]["est"]) >= .15 and (E3B[f"{sc}|{lang}"]["ci"][0] > 0 or E3B[f"{sc}|{lang}"]["ci"][1] < 0))
        csvrows["e3b_commitment_vs_english"].append({"scope": sc, "lang": lang, **{k: json.dumps(v) if isinstance(v, list) else v for k, v in E3B[f"{sc}|{lang}"].items()}})
OUTJ["E3b_pronoun_address_vs_english"] = E3B
# clean pronoun-only variant (sensitivity added after noticing the v1 lexicons contain a few imperative/verb tokens; declared in DEVIATIONS 15)
PRON = {"de": r"(?<![\w])(du|dich|dir|dein\w*|Sie|Ihnen|Ihr\w*|euch)(?![\w])", "es": r"(?<![\w])(t[uú]|tus|ti|contigo|usted(es)?|te)(?![\w])", "fr": r"(?<![\w'’])(tu|toi|te|ton|ta|tes|vous|votre|vos)(?![\w])|(?<![\w])t['’]\w"}
E3C = {}
for sc, ms in scopes:
    en = vec("REG", "en", ms, "bare", lambda r: r["lab"] == "addr")
    ed = vec("REG", "en", ms, "bare", lambda r: 1)
    for lang in TL:
        tt = np.zeros(20); td = np.zeros(20)
        for m in ms:
            for r in IDX.get(("REG", lang, m, "bare", "L"), []):
                tt[FI["REG"][r["family_id"]]] += bool(re.search(PRON[lang], r["text"], re.I if lang != "de" else 0) if lang != "de" else (re.search(PRON[lang], r["text"]) or re.search(r"(?<![\w])du(?![\w])", r["text"], re.I))); td[FI["REG"][r["family_id"]]] += 1
        bb = bootarr("REG", tt, td) - bootarr("REG", en[0], ed[0])
        E3C[f"{sc}|{lang}"] = {"P_pronoun_target": float(tt.sum() / td.sum()), "P_you_english": float(en[0].sum() / ed[0].sum()), **summ(bb, float(tt.sum() / td.sum() - en[0].sum() / ed[0].sum()))}
OUTJ["E3b_clean_pronoun_only"] = E3C

# ============================================================ E3 polarity default, matched English
isaff = lambda r: r["lab"] == "affirmative"; iscom = lambda r: r["lab"] in ("affirmative", "negated"); isneg = lambda r: r["lab"] == "negated"
E3 = {}
for arm, tag in (("bare", "greedy"), ("bare_s", "sampled")):
    for sc, ms in scopes:
        en = vec("POL", "en", ms, arm, isaff, iscom)
        for lang in ["en"] + TL:
            a = vec("POL", lang, ms, arm, isaff, iscom)
            neg_ = vec("POL", lang, ms, arm, isneg, lambda r: 1)
            e = ratio("POL", *a)
            ent = {"n": int(vec("POL", lang, ms, arm, lambda r: 1)[0].sum()), "P_aff_committed": e, "P_neg_all": ratio("POL", *neg_), "n_unclear": int(vec("POL", lang, ms, arm, lambda r: r["lab"] == "unclear")[0].sum())}
            if lang != "en":
                bb = bootarr("POL", *a) - bootarr("POL", *en)
                pt = (a[0].sum() / a[1].sum()) - (en[0].sum() / en[1].sum())
                ent["diff_vs_english"] = summ(bb, float(pt))
                ent["effect_ge10pp_ci_excl0"] = bool(abs(pt) >= .10 and (ent["diff_vs_english"]["ci"][0] > 0 or ent["diff_vs_english"]["ci"][1] < 0))
            E3[f"{tag}|{sc}|{lang}"] = ent
            csvrows["e3_polarity_default"].append({"draw": tag, "scope": sc, "lang": lang, **{k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in ent.items()}})
OUTJ["E3_polarity_default"] = E3

# ============================================================ E4 restored vs bare, plain_neg, negated-class agreement
E4 = {}
for sc, ms in scopes:
    for lang in ["en"] + TL:
        rb = vec("POL", lang, ms, "restored", isneg, lambda r: 1, variant="B")
        bar = vec("POL", lang, ms, "bare", isneg, lambda r: 1)
        pl_ = vec("POL", lang, ms, "plain_neg", isneg, lambda r: 1)
        ra = vec("POL", lang, ms, "restored", isaff, lambda r: 1, variant="A")
        gain = bootarr("POL", *rb) - bootarr("POL", *bar)
        gp = float(rb[0].sum() / max(rb[1].sum(), 1) - bar[0].sum() / max(bar[1].sum(), 1))
        cvp = bootarr("POL", *rb) - bootarr("POL", *pl_)
        ent = {"restored_B_negated": ratio("POL", *rb), "bare_negated": ratio("POL", *bar), "plain_neg_negated": ratio("POL", *pl_), "restored_A_affirmative": ratio("POL", *ra),
               "gain_restored_minus_bare": summ(gain, gp), "chip_minus_plainword": summ(cvp, float(rb[0].sum() / max(rb[1].sum(), 1) - pl_[0].sum() / max(pl_[1].sum(), 1))), "n_B_restored": int(rb[1].sum())}
        ent["meets_50pp_lower"] = bool(ent["gain_restored_minus_bare"]["ci"][0] >= 0.5)
        E4[f"{sc}|{lang}"] = ent
        csvrows["e4_cue_restoration"].append({"scope": sc, "lang": lang, **{k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in ent.items()}})
OUTJ["E4_cue_restoration"] = E4
OUTJ["E4_models_meeting_50pp"] = {lang: [m for m in MODELS if E4[f"{m}|{lang}"]["meets_50pp_lower"]] for lang in ["en"] + TL}
# instrument agreement on negated class (restored B outputs; direct vs translate-then-English route), all texts incl. disagreements
AG = {}
for lang in TL:
    pairs_ = []
    for r in IDX_ALL if False else []:
        pass
    pr = collections.defaultdict(list)
    for m in MODELS:
        for r in jl(RUN2 / f"gen_{m}.jsonl"):
            if r["lang"] == lang and r["kind"] == "POL" and r["arm"] == "restored" and r["text"] and r["pset"] == "L":
                x = pol_lab.get(f"{lang}|{r['text']}")
                if x and x.get("direct") and x.get("route"):
                    pr[r["variant"]].append((x["direct"], x["route"]))
    def pa(ps, cls):
        n11 = sum(a == cls and b == cls for a, b in ps); n1 = sum(a == cls for a, b in ps); n2 = sum(b == cls for a, b in ps)
        return {"pos_agreement": (2 * n11 / (n1 + n2)) if (n1 + n2) else None, "n_direct": n1, "n_route": n2, "n_both": n11, "n": len(ps), "raw_agree": sum(a == b for a, b in ps) / len(ps) if ps else None}
    AG[lang] = {"negated_class_on_restored_B": pa(pr["B"], "negated"), "affirmative_class_on_restored_A": pa(pr["A"], "affirmative")}
OUTJ["E4_instrument_agreement"] = AG

# ============================================================ E5 register cues
E5 = {}
for sc, ms in scopes:
    for lang in TL:
        for want, nm in (("V", "formal"), ("T", "informal")):
            arms = [f"chip_{nm}", f"plain_{nm}", f"ctx_{nm}", f"plain_{nm}_x", f"ctx_{nm}_x"]
            D = {}
            for arm in arms:
                am = vec("REG", lang, ms, arm, lambda r: r["lab"] == want, ISADD)
                allm = vec("REG", lang, ms, arm, lambda r: r["lab"] == want, lambda r: 1)
                adr = vec("REG", lang, ms, arm, ISADD, lambda r: 1)
                D[arm] = {"match_among_address": ratio("REG", *am), "match_of_all": ratio("REG", *allm), "address_rate": ratio("REG", *adr), "_allm": allm, "n": int(allm[1].sum())}
            for other in arms[1:]:
                bb = bootarr("REG", *D[arms[0]]["_allm"]) - bootarr("REG", *D[other]["_allm"])
                pt = D[arms[0]]["_allm"][0].sum() / D[arms[0]]["_allm"][1].sum() - D[other]["_allm"][0].sum() / D[other]["_allm"][1].sum()
                D[arms[0]][f"minus_{other}_match_of_all"] = summ(bb, float(pt))
            for arm in arms:
                D[arm].pop("_allm")
            E5[f"{sc}|{lang}|{nm}"] = D
            for arm, v in D.items():
                csvrows["e5_register_cues"].append({"scope": sc, "lang": lang, "requested": nm, "arm": arm, **{k: json.dumps(x) if isinstance(x, (list, dict)) else x for k, x in v.items()}})
OUTJ["E5_register_cues"] = E5
# plain-word leakage into the output
LEAK = {}
for lang, (wf, wi) in {"de": ("formell", "informell"), "es": ("formal", "informal"), "fr": ("formel", "informel")}.items():
    for arm, w in (("plain_formal", wf), ("plain_informal", wi)):
        for m in ["pooled"] + MODELS:
            rs = [r for mm in (MODELS if m == "pooled" else [m]) for r in IDX.get(("REG", lang, mm, arm, "L"), [])]
            k = sum(bool(re.search(r"\b" + w + r"\w*", r["text"], re.I)) for r in rs)
            LEAK[f"{lang}|{arm}|{m}"] = {"leaked": k, "n": len(rs)}
OUTJ["plain_word_leakage_into_output"] = LEAK
# FR informal chip failure
FRI = {}
for m in MODELS:
    rs = IDX.get(("REG", "fr", m, "chip_informal", "L"), [])
    c = collections.Counter(r["lab"] for r in rs)
    trig = collections.Counter()
    ex = []
    for r in rs:
        if r["lab"] == "V":
            for k in ("s'il vous pla", "veuillez", "vous", "votre", "vos"):
                if k in r["text"].lower().replace("’", "'"):
                    trig[k] += 1
            if len(ex) < 3:
                ex.append(r["text"])
    FRI[m] = {"labels": dict(c), "V_trigger_tokens": dict(trig), "examples_V": ex, "n": len(rs)}
OUTJ["FR_informal_chip_failure"] = FRI
# fraction of FR-informal chip V outputs that contain 'plait' (politeness phrase default)

# ============================================================ E6 keyword-condition controls
E6 = {}
for lang in TL:
    for arm in ("bare", "bare_nom", "bare_sep", "bare_kw2", "bare_x"):
        if arm == "bare_sep" and lang != "de":
            continue
        per = {}
        bs = []
        for m in MODELS:
            v = vec("REG", lang, [m], arm, lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
            ad = vec("REG", lang, [m], arm, ISADD, lambda r: 1)
            per[m] = {"V_share": None if not v[1].sum() else float(v[0].sum() / v[1].sum()), "n_TV": int(v[1].sum()), "address_rate": float(ad[0].sum() / max(ad[1].sum(), 1))}
            bs.append(bootarr("REG", *v))
        A = np.vstack(bs)
        vals = [p["V_share"] for p in per.values() if p["V_share"] is not None]
        po = vec("REG", lang, MODELS, arm, lambda r: r["lab"] == "V", lambda r: r["lab"] in ("T", "V"))
        ao = vec("REG", lang, MODELS, arm, ISADD, lambda r: 1)
        E6[f"{lang}|{arm}"] = {"per_model": per, "pooled_V_share": ratio("REG", *po), "pooled_address_rate": ratio("REG", *ao),
                               "range": summ(np.nanmax(A, 0) - np.nanmin(A, 0), float(max(vals) - min(vals))) if len(vals) > 1 else None}
        csvrows["e6_keyword_conditions"].append({"lang": lang, "condition": arm, "pooled_V_share": json.dumps(E6[f"{lang}|{arm}"]["pooled_V_share"]),
                                                  "pooled_address_rate": json.dumps(E6[f"{lang}|{arm}"]["pooled_address_rate"]), "range": json.dumps(E6[f"{lang}|{arm}"]["range"]),
                                                  **{f"V_{m}": per[m]["V_share"] for m in MODELS}, **{f"n_{m}": per[m]["n_TV"] for m in MODELS}})
OUTJ["E6_keyword_conditions"] = E6

# ============================================================ E9 policies
import csv as _csv
sev = collections.defaultdict(list)
for f in glob.glob(str(ROOT / "expert_package/returns_slp/slp_rating_SLP*.csv")):
    for r in _csv.DictReader(open(f)):
        if r["task"] == "1" and r["severity"].strip().isdigit():
            sev[r["item_id"]].append(int(r["severity"]))
W = {k: float(np.mean(v)) / 5 for k, v in sev.items()}
OUTJ["slp_weights"] = W
PIN = {"0.5%": 0.005, "2.7%": 0.027, "10%": 0.10}
POLICY = []  # rows for csv


def cell(kind, lang, model, arm, fam, pset="L", variant=None):
    return [r for r in IDX.get((kind, lang, model, arm, pset), []) if r["family_id"] == fam and (variant is None or r["variant"] == variant)]


def pol_policies(lang):
    """returns dict policy-> (rev[f], taps[f]) arrays over families (per-family means across models)"""
    fams = FAM["POL"]; out = collections.defaultdict(lambda: [np.zeros(len(fams)), np.zeros(len(fams)), np.zeros(len(fams))])
    for m in MODELS:
        for i, f in enumerate(fams):
            b = cell("POL", lang, m, "bare", f); rs = cell("POL", lang, m, "restored", f, variant="B"); pn = cell("POL", lang, m, "plain_neg", f)
            ss = [r["lab"] for r in cell("POL", lang, m, "bare_s", f)]
            g = [r for r in g1rows if r["lang"] == lang and r["model"] == m and r["family_id"] == f and r["kind"] == "POL"]
            if not (b and rs and pn):
                continue
            ab, ar, ap = [float(x[0]["lab"] == "affirmative") for x in (b, rs, pn)]
            split = float(len(set(x for x in ss if x in ("affirmative", "negated"))) > 1)
            pol = {"always_commit(bare)": (ab, 0), "always_ask_chip": (ar, 1), "plain_word": (ap, 3), "entropy_ask": ((1 - split) * ab + split * ar, split)}
            if g:
                pol["G1_written_cue"] = (float(g[0]["lab"] == "affirmative"), 1)
            for k, (rv, tp) in pol.items():
                out[k][0][i] += rv; out[k][1][i] += tp; out[k][2][i] += 1
            out["_ask_entropy"][0][i] += split; out["_ask_entropy"][2][i] += 1
    return out
PP = {}
for lang in ["en"] + TL:
    out = pol_policies(lang)
    pe = out["_ask_entropy"]; ask = float(pe[0].sum() / pe[2].sum())
    for k, (rv, tp, nn) in out.items():
        if k.startswith("_"):
            continue
        r_est, r_ci = ratio("POL", rv, nn); t_est, _ = ratio("POL", tp, nn)
        ent = {"affirmative_rate_on_B(reversal_prob)": [r_est, r_ci], "taps_per_message": t_est}
        for pn_, pi in PIN.items():
            ent[f"silent_reversals_per_1000@pi={pn_}"] = [1000 * pi * r_est, [1000 * pi * r_ci[0], 1000 * pi * r_ci[1]]]
        ent["slp_weighted_per_1000@2.7%"] = 1000 * 0.027 * r_est * W["NEG"]
        PP[f"pol|{lang}|{k}"] = ent
        POLICY.append({"domain": "polarity", "lang": lang, "policy": k, "taps_per_1000": 1000 * t_est, "reversal_prob": r_est, "ci_lo": r_ci[0], "ci_hi": r_ci[1],
                       "per_1000@2.7%": 1000 * 0.027 * r_est, "slp_weighted@2.7%": 1000 * 0.027 * r_est * W["NEG"], "n_msgs": int(nn.sum())})
    # random-ask matched to entropy ask rate and to 1,000
    ab = out["always_commit(bare)"]; ar = out["always_ask_chip"]
    p = ask
    rv = (1 - p) * ab[0] + p * ar[0]
    r_est, r_ci = ratio("POL", rv, ab[2])
    POLICY.append({"domain": "polarity", "lang": lang, "policy": f"random_ask_matched_to_entropy(p={p:.3f})", "taps_per_1000": 1000 * p, "reversal_prob": r_est, "ci_lo": r_ci[0], "ci_hi": r_ci[1],
                   "per_1000@2.7%": 1000 * 0.027 * r_est, "slp_weighted@2.7%": 1000 * 0.027 * r_est * W["NEG"], "n_msgs": int(ab[2].sum())})
    ee = out["entropy_ask"]
    bb = bootarr("POL", ee[0], ee[2]) - bootarr("POL", rv, ab[2])
    PP[f"pol|{lang}|entropy_minus_random_matched"] = summ(bb)
    PP[f"pol|{lang}|entropy_ask_rate"] = ask
OUTJ["E9_polarity_policies"] = PP

# register
def reg_cell_lab(lang, m, arm, f):
    c = cell("REG", lang, m, arm, f)
    return c[0]["lab"] if c else None
def mis(lab, need):
    return float(lab in ("T", "V", "mixed") and lab != need)
def reg_policies(lang):
    fams = FAM["REG"]
    names = ["always_commit(bare)", "always_ask_chip", "plain_word", "plain_word_x(legend-equalised)", "ctx_cue", "ctx_cue_x(legend-equalised)", "ask_if_address", "entropy_ask(T/V split)", "entropy_ask(any disagreement)", "G1_written_cue"]
    A = {n: {N: np.zeros(len(fams)) for N in "VT"} for n in names}; TP = {n: np.zeros(len(fams)) for n in names}; CNT = np.zeros(len(fams)); ASKR = {n: np.zeros(len(fams)) for n in names}
    for m in MODELS:
        for i, f in enumerate(fams):
            b = reg_cell_lab(lang, m, "bare", f)
            ch = {"V": reg_cell_lab(lang, m, "chip_formal", f), "T": reg_cell_lab(lang, m, "chip_informal", f)}
            pw = {"V": reg_cell_lab(lang, m, "plain_formal", f), "T": reg_cell_lab(lang, m, "plain_informal", f)}
            pwx = {"V": reg_cell_lab(lang, m, "plain_formal_x", f), "T": reg_cell_lab(lang, m, "plain_informal_x", f)}
            cx = {"V": reg_cell_lab(lang, m, "ctx_formal", f), "T": reg_cell_lab(lang, m, "ctx_informal", f)}
            cxx = {"V": reg_cell_lab(lang, m, "ctx_formal_x", f), "T": reg_cell_lab(lang, m, "ctx_informal_x", f)}
            ss = [r["lab"] for r in cell("REG", lang, m, "bare_s", f)]
            if None in (b, *ch.values(), *pw.values(), *pwx.values(), *cx.values(), *cxx.values()):
                continue
            tvs = set(x for x in ss if x in ("T", "V"))
            e_tv = float(len(tvs) > 1); e_any = float(len(set(ss)) > 1) if ss else 0.0
            addr = float(b in ("T", "V", "mixed"))
            g = {r["need"]: r for r in g1rows if r["lang"] == lang and r["model"] == m and r["family_id"] == f and r["kind"] == "REG"}
            CNT[i] += 1
            for N in "VT":
                A["always_commit(bare)"][N][i] += mis(b, N)
                A["always_ask_chip"][N][i] += mis(ch[N], N)
                A["plain_word"][N][i] += mis(pw[N], N); A["plain_word_x(legend-equalised)"][N][i] += mis(pwx[N], N)
                A["ctx_cue"][N][i] += mis(cx[N], N); A["ctx_cue_x(legend-equalised)"][N][i] += mis(cxx[N], N)
                A["ask_if_address"][N][i] += addr * mis(ch[N], N) + (1 - addr) * mis(b, N)
                A["entropy_ask(T/V split)"][N][i] += e_tv * mis(ch[N], N) + (1 - e_tv) * mis(b, N)
                A["entropy_ask(any disagreement)"][N][i] += e_any * mis(ch[N], N) + (1 - e_any) * mis(b, N)
                if N in g and g[N]["lab"]:
                    A["G1_written_cue"][N][i] += mis(g[N]["lab"], N)
                else:
                    A["G1_written_cue"][N][i] += mis(b, N)
            for n_, t_ in (("always_ask_chip", 1), ("plain_word", 3), ("plain_word_x(legend-equalised)", 3), ("ctx_cue", 1), ("ctx_cue_x(legend-equalised)", 1), ("G1_written_cue", 1),
                           ("ask_if_address", addr), ("entropy_ask(T/V split)", e_tv), ("entropy_ask(any disagreement)", e_any), ("always_commit(bare)", 0)):
                TP[n_][i] += t_
    return A, TP, CNT, names
RP = {}
for lang in TL:
    A, TP, CNT, names = reg_policies(lang)
    askr = TP["ask_if_address"].sum() / CNT.sum()
    for n_ in names:
        for piV in (0.1, 0.3, 0.5, 0.7, 0.9):
            mv = piV * A[n_]["V"] + (1 - piV) * A[n_]["T"]
            est, ci = ratio("REG", mv, CNT); te, _ = ratio("REG", TP[n_], CNT)
            POLICY.append({"domain": "register", "lang": lang, "policy": n_, "piV": piV, "taps_per_1000": 1000 * te, "reversal_prob": est, "ci_lo": ci[0], "ci_hi": ci[1],
                           "per_1000@2.7%": 1000 * est, "slp_weighted@2.7%": 1000 * est * W["POL"], "n_msgs": int(CNT.sum())})
            if piV == 0.5:
                RP[f"reg|{lang}|{n_}|piV=0.5"] = {"mismatch_per_1000": [1000 * est, [1000 * ci[0], 1000 * ci[1]]], "taps_per_1000": 1000 * te, "slp_weighted(POL weight, borrowed)": 1000 * est * W["POL"]}
    # random-ask matched rates
    for tag, p in (("matched_to_ask_if_address", askr), ("matched_to_1000", 1.0)):
        for piV in (0.5,):
            for rn, base in (("random_ask", "always_ask_chip"),):
                mv = piV * ((1 - p) * A["always_commit(bare)"]["V"] + p * A[base]["V"]) + (1 - piV) * ((1 - p) * A["always_commit(bare)"]["T"] + p * A[base]["T"])
                est, ci = ratio("REG", mv, CNT)
                RP[f"reg|{lang}|random_ask_{tag}|piV=0.5"] = {"mismatch_per_1000": [1000 * est, [1000 * ci[0], 1000 * ci[1]]], "taps_per_1000": 1000 * p}
                POLICY.append({"domain": "register", "lang": lang, "policy": f"random_ask_{tag}(p={p:.3f})", "piV": piV, "taps_per_1000": 1000 * p, "reversal_prob": est, "ci_lo": ci[0], "ci_hi": ci[1],
                               "per_1000@2.7%": 1000 * est, "slp_weighted@2.7%": 1000 * est * W["POL"], "n_msgs": int(CNT.sum())})
    # ask-if-address minus random matched (paired, piV .5)
    mvA = 0.5 * A["ask_if_address"]["V"] + 0.5 * A["ask_if_address"]["T"]
    mvR = 0.5 * ((1 - askr) * A["always_commit(bare)"]["V"] + askr * A["always_ask_chip"]["V"]) + 0.5 * ((1 - askr) * A["always_commit(bare)"]["T"] + askr * A["always_ask_chip"]["T"])
    RP[f"reg|{lang}|ask_if_address_minus_random_matched|piV=0.5"] = summ(bootarr("REG", mvA, CNT) - bootarr("REG", mvR, CNT))
    # break-even piV of bare default (pooled): default beats opposite constant iff ...
OUTJ["E9_register_policies"] = RP
with open(OUT / "r2_policies.csv", "w", newline="") as f:
    cols = sorted({k for r in POLICY for k in r}, key=lambda c: (c not in ("domain", "lang", "policy"), c))
    w = _csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(POLICY)
for name, rr in csvrows.items():
    if rr:
        cols = sorted({k for r in rr for k in r})
        with open(OUT / f"r2_{name}.csv", "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rr)

# ============================================================ G1 summary
G = {}
for lang in ["en"] + TL:
    gs = [r for r in g1rows if r["lang"] == lang]
    if gs:
        for need in sorted({r["need"] for r in gs}):
            x = [r for r in gs if r["need"] == need]
            G[f"{lang}|{need}"] = {"n": len(x), "monitor_fired": sum(r["retries"] > 0 for r in x), "still_bad_after_retries": sum(r["still_bad"] for r in x)}
OUTJ["G1_written_cue"] = G
# ============================================================ strict gate sensitivity (restrict to surviving families)
if STRICT:
    OUTJ["E8_strict_gate"] = STRICT["survival"]
json.dump(OUTJ, open(OUT / "summary_r2.json", "w"), indent=1, default=lambda o: None if o != o else float(o) if isinstance(o, (np.floating,)) else int(o) if isinstance(o, np.integer) else str(o))
print("done", len(rows), MODELS)
