"""Detector-vs-judge validity check for knows_not_says (PLAN A19/A19b). Two steps:
  draw  <key:alias> ...   : draws the declared samples (seed 20261102) and builds runs/frontier_knows_not_says_judge/ (outputs.jsonl, items.jsonl,
                            config.json) for src/judge.py plus annotation/frontier_knows_not_says_key.csv (the key: set, unit, detector label)
  score <key:alias> ...   : after judge.py (+ blind arbiter decisions) -> analysis/frontier/knows_not_says/stage1/detector_validity.json
Model outputs: from the R1 domain (no-cue units of E-cap4 + E-human, pilot messages excluded) 100 units with detector polarity 'negated' and 100
with not negated per model, one random sampled output per drawn unit. Human sources: 100 messages (50 detector-negated, 50 not) from no-cue messages."""
import json, sys, hashlib, csv, collections
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import frontier_knows_not_says_lib as L, layer0
RUNS = ROOT / "runs/frontier_knows_not_says_stage1"; JR = ROOT / "runs/frontier_knows_not_says_judge"
OUT = ROOT / "analysis/frontier/knows_not_says/stage1"; OUT.mkdir(parents=True, exist_ok=True)
N_NEG = 100; N_OTH = 300; N_SRC = 50
OPTS = ["negated", "affirmative", "unclear/mixed"]
cmd = sys.argv[1]; specs = [s.split(":") for s in sys.argv[2:]]
cache_f = RUNS / "labels_cache.json"; cache = json.load(open(cache_f)) if cache_f.exists() else {}
def label(texts):
    need = sorted({t for t in texts if t not in cache})
    if need:
        for t, l in zip(need, layer0.label_many(need)): cache[t] = [l["polarity"], l["politeness"], l["speech_act"]]
        json.dump(cache, open(cache_f, "w"))
    return [cache[t][0] for t in texts]
pilot = json.load(open(ROOT / "analysis/frontier/knows_not_says/pilot/pilot_items.json"))
U = L.build_units({e["elic_item_id"] for e in pilot["e_human"]}); U = U[U.nocue_neg].reset_index(drop=True)
def sid(*p): return hashlib.sha256("|".join(map(str, p)).encode()).hexdigest()[:10]

def draw():
    import zlib
    kf = ROOT / "annotation/frontier_knows_not_says_key.csv"; old = pd.read_csv(kf) if kf.exists() else pd.DataFrame()
    have = set(old.set) if len(old) else set(); rows = old.to_dict("records") if len(old) else []
    for key, alias in specs:
        if f"model:{alias}" in have: continue
        rng = np.random.default_rng([L.SEED, zlib.crc32(alias.encode())])   # per-set stream: adding a model later never changes earlier draws
        G = collections.defaultdict(list)
        for l in open(RUNS / key / "gens.jsonl"):
            r = json.loads(l)
            if r["k"] >= 0: G[r["input"]].append(r["text"])
        Ud = U[U.input.isin(G)].reset_index(drop=True); label([t for ts in G.values() for t in ts])
        # detector-negated pool: every sampled output on an R1-domain unit that the detector calls negated (one random such sample per unit, units in random order)
        order = rng.permutation(len(Ud)); neg_rows, oth_rows = [], []
        for i in order:
            u = Ud.iloc[i]; ts = G[u.input]; labs = label(ts); ix = [j for j, l_ in enumerate(labs) if l_ == "negated"]
            if ix and len(neg_rows) < N_NEG: j = ix[int(rng.integers(0, len(ix)))]; neg_rows.append((u, ts[j], labs[j]))
            if len(oth_rows) < N_OTH:
                jx = [j for j, l_ in enumerate(labs) if l_ != "negated"]
                if jx: j = jx[int(rng.integers(0, len(jx)))]; oth_rows.append((u, ts[j], labs[j]))
        for lst in (neg_rows, oth_rows):
            for u, t, lb in lst: rows.append(dict(set=f"model:{alias}", detector=lb, detector_neg=int(lb == "negated"), text=t, input=u.input, item_id=u.item_id, dataset=u.dataset, w=u.w))
    if "source" not in have:
        rng = np.random.default_rng([L.SEED, 1])
        Ms = U.drop_duplicates("item_id").reset_index(drop=True); msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv").set_index("item_id")
        texts = [msg.loc[i, "text"] for i in Ms.item_id]; labs = label(texts); order = rng.permutation(len(Ms)); got = {"negated": [], "other": []}
        for i in order:
            c = "negated" if labs[i] == "negated" else "other"
            if len(got[c]) < N_SRC: got[c].append(i)
        for c, ix in got.items():
            for i in ix: rows.append(dict(set="source", detector=labs[i], detector_neg=int(labs[i] == "negated"), text=texts[i], input="(typed sentence)", item_id=Ms.item_id.iloc[i], dataset="msg", w=float(Ms.w.iloc[i])))
    for r in rows: r.pop("family_id", None); r.pop("valid", None)
    JR.mkdir(parents=True, exist_ok=True)
    with open(JR / "outputs.jsonl", "w") as fo, open(JR / "items.jsonl", "w") as fi:
        for n, r in enumerate(rows):
            r["family_id"] = f"knsv-{n:04d}"; r["valid"] = True
            fo.write(json.dumps(dict(family_id=r["family_id"], text=r["text"], input_text=r["input"], text_id=sid(r["text"]), valid=True, output_id=r["family_id"], sample_idx=0, suggestion_idx=0)) + "\n")
            fi.write(json.dumps(dict(family_id=r["family_id"], dimension="polarity", critical_options=OPTS, split="knsv", variants={"A": dict(source=r["text"], critical_value="unclear/mixed")}, bare="", context=None)) + "\n")
    json.dump(dict(items_path="runs/frontier_knows_not_says_judge/items.jsonl"), open(JR / "config.json", "w"))
    pd.DataFrame(rows).drop(columns=[]).to_csv(ROOT / "annotation/frontier_knows_not_says_key.csv", index=False)
    print(len(rows), "rows;", pd.DataFrame(rows).groupby(["set", "detector_neg"]).size().to_dict())

def beta_ci(k, n):
    from math import sqrt
    z = 1.96; p = k / n if n else float("nan")
    if not n: return (float("nan"), float("nan"))
    d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return (c - h, c + h)

def score():
    key = pd.read_csv(ROOT / "annotation/frontier_knows_not_says_key.csv")
    J = {json.loads(l)["family_id"]: json.loads(l) for l in open(JR / "judgments.jsonl")}
    arb = {}
    dec = JR / "arbiter_decisions.tsv"
    if dec.exists():
        for row in csv.reader(open(dec), delimiter="\t"):
            if len(row) >= 2 and row[0] != "key": arb[row[0]] = row[1]
    inv = json.load(open(JR / "arbiter_inventory.json")) if (JR / "arbiter_inventory.json").exists() else None
    ref = []; src_of = []
    for r in key.itertuples():
        j = J[r.family_id]; c = j["critical"]
        if c is None:   # judges disagree -> arbiter decision keyed by a_unit
            ak = f"{j['text_id']}|polarity|{'/'.join(OPTS)}"
            c = arb.get(ak) or next((v for k, v in arb.items() if k.startswith(j["text_id"])), None); src_of.append("arbiter" if c else "UNRESOLVED")
        else: src_of.append("judges agree")
        ref.append(c)
    key["reference"] = ref; key["ref_source"] = src_of; key["ref_neg"] = [1 if c == "negated" else 0 if c in ("affirmative",) else (0 if c == "unclear/mixed" else None) for c in ref]
    key.to_csv(OUT / "detector_validity_key_scored.csv", index=False)
    res = {"note": "reference = machine judge (J1+J2) + blind arbiter on disagreements; NOT human truth; unclear/mixed counted as not negated; human confirmation requested in ANNOTATION_REQUEST.md",
           "n_unresolved": int(key.ref_neg.isna().sum()), "ref_source_counts": key.ref_source.value_counts().to_dict(), "sets": {}}
    p_det = {}
    for s, g in key.groupby("set"):
        g = g[g.ref_neg.notna()]; d = {}
        for lab, nm in ((1, "ppv"), (0, "npv")):
            gg = g[g.detector_neg == lab]; k = int(((gg.ref_neg == 1) if lab else (gg.ref_neg == 0)).sum()); n = len(gg)
            lo, hi = beta_ci(k, n); w = gg.w.to_numpy(float); ok = ((gg.ref_neg == 1) if lab else (gg.ref_neg == 0)).to_numpy(float)
            d[nm] = dict(k=k, n=n, rate=k / n if n else None, wilson_lo=lo, wilson_hi=hi, ht_weighted=float((w * ok).sum() / w.sum()) if n else None)
        d["unclear_mixed_by_reference"] = int((g.reference == "unclear/mixed").sum())
        d["confusion"] = {f"det{a}_ref{b}": int(((g.detector_neg == a) & (g.ref_neg == b)).sum()) for a in (0, 1) for b in (0, 1)}
        res["sets"][s] = d
    # derived sensitivity/specificity (Bayes) with the detector-positive share of the R1 domain (HT weighted)
    msgtxt = pd.read_csv(ROOT / "analysis/elicitation/messages.csv").set_index("item_id")["text"]
    base = U.drop_duplicates("item_id"); pd_src = float(np.average([x == "negated" for x in label([msgtxt[i] for i in base.item_id])], weights=base.w))
    pd_mod = {}
    for k_, alias in specs:
        G = collections.defaultdict(list)
        for l in open(RUNS / k_ / "gens.jsonl"):
            r = json.loads(l)
            if r["k"] >= 0: G[r["input"]].append(r["text"])
        Ud = U[U.input.isin(G)]; sh = [np.mean([x == "negated" for x in label(G[i])]) for i in Ud.input]; pd_mod[f"model:{alias}"] = float(np.average(sh, weights=Ud.w))
    for s_, d in res["sets"].items():
        pdet = pd_src if s_ == "source" else pd_mod.get(s_); d["p_detector_neg_domain_ht"] = pdet
        if pdet is not None and d["ppv"]["rate"] is not None:
            ppv, npv = d["ppv"]["rate"], d["npv"]["rate"]; tp = pdet * ppv; fn = (1 - pdet) * (1 - npv); tn = (1 - pdet) * npv; fp = pdet * (1 - ppv)
            d["derived_sensitivity"] = tp / (tp + fn) if tp + fn else None; d["derived_specificity"] = tn / (tn + fp) if tn + fp else None
    json.dump(res, open(OUT / "detector_validity.json", "w"), indent=1); print(json.dumps(res, indent=1)[:3000])

{"draw": draw, "score": score}[cmd]()
