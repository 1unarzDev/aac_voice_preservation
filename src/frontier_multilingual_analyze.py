"""Pilot analysis (rules in PLAN.md Sec. 1, 4, 6). Family-cluster bootstrap, 10,000 resamples, seed 20261102."""
import sys, json, csv, glob, collections, random
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
from frontier_multilingual_register import label as det

MODELS = [m for m in ("gemma3-4b", "mistral-nemo-12b", "gpt-6.1-terra") if (RUN / f"gen_{m}.jsonl").exists()
          and (OUT / f"pol_labels_{m}.jsonl").exists()]
B = 10000
rng = np.random.default_rng(20261102)


def tsv(path):
    d = {}
    if Path(path).exists():
        for l in open(path):
            p = l.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0] != "n":
                d[p[0]] = p[1]
    return d


# ---------------- register labels
arb_items = json.load(open(OUT / "arbiter_register_items.json")) if (OUT / "arbiter_register_items.json").exists() else []
arb = tsv(OUT / "arbiter_register.tsv")
text2arb = {(it["lang"], it["text"]): arb.get(str(it["n"])) for it in arb_items}
reg = []
for m in MODELS:
    for r in jl(RUN / f"gen_{m}.jsonl"):
        if r["kind"] != "REG":
            continue
        d = det(r["lang"], r["text"])
        a = text2arb.get((r["lang"], r["text"]))
        lab = d
        if d == "ambig":
            lab = a if a else "unresolved"
        reg.append({**r, "det": d, "arb": a, "label": lab})
jdump(OUT / "register_labels.jsonl", reg)

# validation: detector vs arbiter on non-ambiguous items
val = collections.defaultdict(lambda: [0, 0])
for it in arb_items:
    if it.get("kind") == "validation" and arb.get(str(it["n"])):
        d = det(it["lang"], it["text"])
        val[it["lang"]][0] += 1
        val[it["lang"]][1] += (d == arb[str(it["n"])])


def boot_ci(fams, stat, rows_by_fam, nb=B):
    """cluster bootstrap over family ids; stat(list_of_rows)->float"""
    fl = list(fams)
    est = stat([r for f in fl for r in rows_by_fam[f]])
    bs = []
    for _ in range(nb):
        pick = rng.integers(0, len(fl), len(fl))
        v = stat([r for i in pick for r in rows_by_fam[fl[i]]])
        if v == v:
            bs.append(v)
    if not bs:
        return est, (float("nan"),) * 2
    return est, tuple(np.percentile(bs, [2.5, 97.5]))


def grp(rows):
    d = collections.defaultdict(list)
    for r in rows:
        d[r["family_id"]].append(r)
    return d


def share(num, den):
    def f(rs):
        n = sum(den(r) for r in rs)
        return sum(num(r) for r in rs) / n if n else float("nan")
    return f


out = {"models": MODELS, "register": {}, "polarity": {}, "validation": {k: {"n": v[0], "agree": v[1], "rate": v[1] / v[0] if v[0] else None} for k, v in val.items()}}
tab = []  # csv rows
# ---------------- H1/H2 register commitment, bare prompt P0-L
isadd = lambda r: r["label"] in ("T", "V", "mixed")
for scope, models in [("pooled", MODELS)] + [(m, [m]) for m in MODELS]:
    for lang in LANGS:
        rs = [r for r in reg if r["lang"] == lang and r["arm"] == "bare" and r["pset"] == "L" and r["model"] in models and r["label"] != "unresolved"]
        g = grp(rs)
        if not g:
            continue
        n_add = sum(map(isadd, rs))
        c = collections.Counter(r["label"] for r in rs)
        commit, ci = boot_ci(g, share(lambda r: r["label"] in ("T", "V"), isadd), g)
        vsh, vci = boot_ci(g, share(lambda r: r["label"] == "V", lambda r: r["label"] in ("T", "V")), g)
        none_sh, nci = boot_ci(g, share(lambda r: r["label"] == "none", lambda r: 1), g)
        out["register"][f"bare|{scope}|{lang}"] = {"n_outputs": len(rs), "n_with_address": n_add, "T": c["T"], "V": c["V"], "mixed": c["mixed"], "none": c["none"],
              "commit_share": commit, "commit_ci": list(ci), "V_share": vsh, "V_ci": list(vci), "none_share": none_sh, "none_ci": list(nci)}
# language-pair V-share differences per model and pooled (H2)
h2 = {}
for scope, models in [("pooled", MODELS)] + [(m, [m]) for m in MODELS]:
    for l1, l2 in (("de", "es"), ("de", "fr"), ("es", "fr")):
        rs1 = [r for r in reg if r["lang"] == l1 and r["arm"] == "bare" and r["pset"] == "L" and r["model"] in models]
        rs2 = [r for r in reg if r["lang"] == l2 and r["arm"] == "bare" and r["pset"] == "L" and r["model"] in models]
        def vs(rs):
            tv = [r for r in rs if r["label"] in ("T", "V")]
            return (sum(r["label"] == "V" for r in tv), len(tv))
        a, b = vs(rs1), vs(rs2)
        if a[1] and b[1]:
            fam = sorted({r["family_id"] for r in rs1 + rs2})
            g1, g2 = grp(rs1), grp(rs2)
            diffs = []
            for _ in range(2000):  # families differ per language only by translation; same family ids resampled jointly
                pick = [fam[i] for i in rng.integers(0, len(fam), len(fam))]
                x1 = [r for f in pick for r in g1.get(f, []) if r["label"] in ("T", "V")]
                x2 = [r for f in pick for r in g2.get(f, []) if r["label"] in ("T", "V")]
                if x1 and x2:
                    diffs.append(np.mean([r["label"] == "V" for r in x1]) - np.mean([r["label"] == "V" for r in x2]))
            h2[f"{scope}|{l1}-{l2}"] = {"V_share_1": a[0] / a[1], "n1": a[1], "V_share_2": b[0] / b[1], "n2": b[1],
                                      "diff": a[0] / a[1] - b[0] / b[1], "ci": list(np.percentile(diffs, [2.5, 97.5])) if diffs else None}
out["H2_pairs"] = h2
# P0-LL sensitivity (bare, translated prompt)
for lang in LANGS:
    for pset in ("L", "LL"):
        rs = [r for r in reg if r["lang"] == lang and r["arm"] == "bare" and r["pset"] == pset and r["label"] != "unresolved"]
        c = collections.Counter(r["label"] for r in rs)
        out["register"][f"bare_{pset}|all_models|{lang}"] = {"n": len(rs), **{k: c[k] for k in ("T", "V", "mixed", "none")}}
# ---------------- H4 register cue arms
for arm, want in (("chip_formal", "V"), ("chip_informal", "T"), ("plain_formal", "V"), ("plain_informal", "T"), ("ctx_formal", "V"), ("ctx_informal", "T"), ("bare", None)):
    for scope, models in [("pooled", MODELS)] + [(m, [m]) for m in MODELS]:
        for lang in LANGS:
            rs = [r for r in reg if r["lang"] == lang and r["arm"] == arm and r["pset"] == "L" and r["model"] in models and r["label"] != "unresolved"]
            if not rs or want is None:
                continue
            g = grp(rs)
            hit, hci = boot_ci(g, share(lambda r: r["label"] == want, isadd), g, 3000)
            comp, cci = boot_ci(g, share(lambda r: r["label"] == want, lambda r: 1), g, 3000)
            ar, arci = boot_ci(g, share(isadd, lambda r: 1), g, 3000)
            out["register"][f"{arm}|{scope}|{lang}"] = {"n": len(rs), "want": want, "match_among_address": hit, "match_ci": list(hci),
                "match_of_all": comp, "match_all_ci": list(cci), "address_rate": ar, "address_ci": list(arci)}
# ---------------- polarity
pol = []
for m in MODELS:
    pol += jl(OUT / f"pol_labels_{m}.jsonl")
parb = tsv(OUT / "arbiter_polarity.tsv")
parb_items = json.load(open(OUT / "arbiter_polarity_items.json")) if (OUT / "arbiter_polarity_items.json").exists() else []
ptext = {(it["lang"], it["text"]): parb.get(str(it["n"])) for it in parb_items}
for r in pol:
    d, ro = r.get("direct"), r.get("route")
    if d and ro and d == ro:
        r["label"], r["how"] = d, "agree"
    else:
        a = ptext.get((r["lang"], r["text"]))
        r["label"], r["how"] = (a, "arbiter") if a else (None, "unresolved")
jdump(OUT / "pol_final.jsonl", pol)
# kappa direct vs route per language (unique text)
def kappa(pairs):
    cats = sorted({x for p in pairs for x in p})
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), po
out["polarity_kappa"] = {}
for lang in LANGS:
    ps = list({(r["text"], r["direct"], r["route"]) for r in pol if r["lang"] == lang and r.get("direct") and r.get("route")})
    k, po = kappa([(a, b) for _, a, b in ps]) if ps else (None, None)
    out["polarity_kappa"][lang] = {"n_unique_texts": len(ps), "kappa": k, "raw_agree": po}
# English baseline
eng = {}
for r in jl(OUT / "english_baseline.jsonl"):
    if r["J1"] == r["J2"]:
        eng[(r["model"], r["family_id"])] = r["J1"]
isaff = lambda r: r["label"] == "affirmative"
iscom = lambda r: r["label"] in ("affirmative", "negated")
PI = {"0.5%": 0.005, "2.7%": 0.027, "10%": 0.10}
for scope, models in [("pooled", MODELS)] + [(m, [m]) for m in MODELS]:
    for lang in LANGS:
        bare = [r for r in pol if r["lang"] == lang and r["arm"] == "bare" and r["pset"] == "L" and r["model"] in models and r["label"]]
        if not bare:
            continue
        g = grp(bare)
        a, ci = boot_ci(g, share(isaff, iscom), g)
        un, uci = boot_ci(g, share(lambda r: r["label"] == "unclear", lambda r: 1), g)
        ent = {"n": len(bare), "aff_share_of_committed": a, "aff_ci": list(ci), "unclear_share": un}
        # English same families & models
        er = [{"family_id": r["family_id"], "label": eng[(r["model"], r["family_id"])]} for r in bare if (r["model"], r["family_id"]) in eng]
        if er:
            ge = grp(er)
            ea, eci = boot_ci(ge, share(isaff, iscom), ge)
            ent["english_aff_share"] = ea; ent["english_n"] = len(er)
            ent["diff_vs_english"] = a - ea
        # restored
        rb = [r for r in pol if r["lang"] == lang and r["arm"] == "restored" and r["variant"] == "B" and r["pset"] == "L" and r["model"] in models and r["label"]]
        ra = [r for r in pol if r["lang"] == lang and r["arm"] == "restored" and r["variant"] == "A" and r["pset"] == "L" and r["model"] in models and r["label"]]
        if rb:
            gb = grp(rb)
            neg_r, nci = boot_ci(gb, share(lambda r: r["label"] == "negated", lambda r: 1), gb)
            ent["B_restored_negated"] = neg_r; ent["B_restored_negated_ci"] = list(nci)
            # paired difference restored - bare on B families (bare label per family/model)
            bmap = {(r["model"], r["family_id"]): r["label"] for r in bare}
            pr = [{"family_id": r["family_id"], "d": (r["label"] == "negated") - (bmap.get((r["model"], r["family_id"])) == "negated")} for r in rb if (r["model"], r["family_id"]) in bmap]
            gp = grp(pr)
            dd, dci = boot_ci(gp, lambda rs: float(np.mean([x["d"] for x in rs])), gp)
            ent["B_neg_gain_restored_minus_bare"] = dd; ent["B_neg_gain_ci"] = list(dci)
            # AAC units: silent reversals per 1000 messages = P(aff | bare, B intent)*pi*1000 ; restored same with restored output
            pa_bare = np.mean([r["label"] == "affirmative" for r in bare])
            pa_rest = np.mean([r["label"] == "affirmative" for r in rb])
            ent["silent_reversals_per_1000"] = {k: {"bare_always_commit": 1000 * v * pa_bare, "always_ask_chip": 1000 * v * pa_rest, "taps_always_ask": 1000} for k, v in PI.items()}
            ent["P_aff_given_B_bare"] = float(pa_bare); ent["P_aff_given_B_restored"] = float(pa_rest)
        if ra:
            ent["A_restored_affirmative"] = float(np.mean([r["label"] == "affirmative" for r in ra]))
        out["polarity"][f"{scope}|{lang}"] = ent
json.dump(out, open(OUT / "summary.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float)[:6000])
