"""Score gold labels: reliability and judge validity (PLAN H7, PREREG_R2 W-A).

  python src/score_gold.py --run main1 --human annotation/returns/*.csv \
      --panel annotation/returns_codex/*.csv \
      --challenge-judgments runs/oracle_challenges
  python src/score_gold.py --self-check
  (main1 as reported: --human 'annotation/returns/*.csv' --panel
   annotation/returns_codex/C_gpt-5.6-sol.csv 'annotation/returns_codex/C_gpt-6-astra_*.csv')

Reference sets (provenance is kept separate in every output; never pooled)
  --human  annotate.html CSV exports from people (alias: --csv).  Gate set: the
           PREREG_R2 kappa >= 0.6 gate is evaluated ONLY against this set.
  --panel  codex annotator panel exports (same CSV schema, machine annotators).
           Reported as provisional machine agreement, never as human validation.
Inputs
  annotation/gold_key_<run>.csv from make_gold.py (judge labels, layer0 labels, pi).
  runs/<run>/arbiter.jsonl: fills the production critical label where J1 != J2
  (the gold key stores null there; the production pipeline uses the arbiter).
  --challenge-judgments <dir>: judgments.jsonl (+ arbiter.jsonl) of the challenge
  items (src/oracle_wa.py); challenge ids are scored in their own, unweighted subset.
  Optional annotation/adjudicated_<run>.csv (item_id + dims) overrides the HUMAN consensus.
Outputs
  annotation/judge_validation_<run>.json / .csv   (sections "human" and "panel")
  annotation/panel_majority_<run>.csv             (machine provenance column)
  annotation/human_consensus_<run>.csv            (when human returns exist)
Method
  alpha     Krippendorff nominal alpha per dimension within each reference set.
            Skipped / blank answers and, by default, dims listed in unsure_dims are
            missing data (the annotate.html protocol exports "unsure" as blank).
  pairwise  raw agreement and Cohen kappa for every pair of {members, judge}.
  consensus human: plurality, ties -> adjudicated file, else excluded.
            panel: strict majority (>= 2 votes and > half of the non-missing votes).
  split     human: calibration vs test by a seeded hash (report TEST). panel: all
            sampled items (and the test split for comparability).
  metrics   per dim and source (final, J1, J2, L0): accuracy (Wilson CI), Cohen kappa
            (item bootstrap CI), per-label precision/recall (Wilson CIs), confusion
            (rows = reference), and design-weighted (1/pi, Horvitz-Thompson) accuracy,
            kappa, precision and recall with Kish-effective-n Wilson CIs. Challenge
            items have no inclusion probability: unweighted only, separate subset.
  verdict   per reference set: Violation / constraint_preserving (cue channels) and
            Assumption (bare/noncrit) recomputed with the production rules from the
            reference consensus and from the judge labels on the sampled items; agreement
            (Wilson CI), kappa, 2x2 counts, design-weighted agreement; "primary" excludes
            the quarantined refusal/acceptance families. The judge recomputation is checked
            against runs/<run>/scored.parquet (consistency_check).
  challenge_key  each member, the consensus and the judge against the authored challenge
            keys (annotation/challenge_items.jsonl).
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agree_stats import cohen_kappa, confusion, prf  # noqa: E402
from labels import GENERAL_OPTIONS  # noqa: E402
from labels import GENERAL_DIMS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIMS = ["critical"] + GENERAL_DIMS + ["added_content"]
SEED = 20261031
H7_KAPPA = 0.6


# ----------------------------------------------- Krippendorff (from old reliability.py)

def coincidence(units: list[list[int]], k: int) -> list[list[float]]:
    o = [[0.0] * k for _ in range(k)]
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        w = 1.0 / (m - 1)
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[vals[i]][vals[j]] += w
    return o


def alpha_nominal(units: list[list[int]], k: int) -> float | None:
    o = coincidence(units, k)
    marg = [sum(r) for r in o]
    n = sum(marg)
    if n < 2:
        return None
    do = sum(o[c][g] for c in range(k) for g in range(k) if c != g) / n
    de = sum(marg[c] * marg[g] for c in range(k) for g in range(k) if c != g) / (n * (n - 1))
    return None if de == 0 else 1.0 - do / de


def bootstrap_ci(units, k, seed, reps=2000):
    rng = random.Random(seed)
    if len(units) < 2:
        return None
    draws = [a for _ in range(reps)
             if (a := alpha_nominal([units[rng.randrange(len(units))] for _ in units], k)) is not None]
    if len(draws) < reps // 2:
        return None
    draws.sort()
    return round(draws[int(0.025 * len(draws))], 3), round(draws[int(0.975 * len(draws)) - 1], 3)


def self_check() -> int:
    obs = [[1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
           [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
           [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None]]
    units = [[o[u] - 1 for o in obs if o[u] is not None] for u in range(12)]
    units = [u for u in units if len(u) >= 2]
    got = alpha_nominal(units, 5)
    ok = abs(got - 0.675258) < 5e-6           # pinned value from old reliability.py
    try:
        import numpy as np
        import krippendorff as ref
        arr = np.array([[np.nan if v is None else v for v in r] for r in obs], dtype=float)
        want = ref.alpha(reliability_data=arr, level_of_measurement="nominal")
        ok &= abs(got - want) < 1e-9
        print(f"nominal alpha {got:.6f}  pinned 0.675258  krippendorff pkg {want:.6f}")
    except ImportError:
        print(f"nominal alpha {got:.6f}  pinned 0.675258")
    print("self-check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------- io

def read_csv(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def is_cal(item_id: str, seed: int, frac: float) -> bool:
    h = int(hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest()[:8], 16)
    return h / 0xFFFFFFFF < frac




# ----------------------------------------------------------------------- stats

def wilson(k: float, n: float, z: float = 1.959964) -> list | None:
    """Wilson score interval; k and n may be non-integer (Kish effective n)."""
    if not n:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def kappa_w(pred: list, gold: list, w: list[float]) -> float | None:
    """Cohen kappa on the design-weighted joint distribution."""
    tw = sum(w)
    if not tw:
        return None
    po = sum(wi for p, g, wi in zip(pred, gold, w) if p == g) / tw
    mp, mg = Counter(), Counter()
    for p, g, wi in zip(pred, gold, w):
        mp[p] += wi / tw
        mg[g] += wi / tw
    pe = sum(mp[k] * mg.get(k, 0) for k in mp)
    return None if pe >= 1 - 1e-12 else round((po - pe) / (1 - pe), 3)


def kappa_boot(pred, gold, w=None, seed=SEED, reps=1000):
    n = len(pred)
    if n < 2:
        return None
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        ix = [rng.randrange(n) for _ in range(n)]
        p, g = [pred[i] for i in ix], [gold[i] for i in ix]
        k = kappa_w(p, g, [w[i] for i in ix]) if w else cohen_kappa(p, g)
        if k is not None:
            out.append(k)
    if len(out) < reps // 2:
        return None
    out.sort()
    return [round(out[int(0.025 * len(out))], 3), round(out[int(0.975 * len(out)) - 1], 3)]


def n_eff(w: list[float]) -> float:
    s2 = sum(x * x for x in w)
    return (sum(w) ** 2 / s2) if s2 else 0.0


def metrics(pred: list, gold: list, w: list[float] | None = None, seed: int = SEED) -> dict:
    n = len(pred)
    if n == 0:
        return {"n": 0}
    k_ok = sum(p == g for p, g in zip(pred, gold))
    labels = sorted(set(gold) | set(pred), key=str)
    per = {}
    for l in labels:
        d = prf(pred, gold, l)
        d["precision_ci"] = wilson(d["tp"], d["tp"] + d["fp"])
        d["recall_ci"] = wilson(d["tp"], d["tp"] + d["fn"])
        d["n_reference"] = d["tp"] + d["fn"]
        per[l] = d
    m = {"n": n, "acc": round(k_ok / n, 3), "acc_ci": wilson(k_ok, n),
         "kappa": cohen_kappa(pred, gold), "kappa_ci": kappa_boot(pred, gold, seed=seed),
         "per_label": per, "confusion_rows_reference": confusion(pred, gold)}
    if w:
        tw, ne = sum(w), n_eff(w)
        acc_w = sum(wi for p, g, wi in zip(pred, gold, w) if p == g) / tw
        m.update(acc_w=round(acc_w, 3), n_eff=round(ne, 1), acc_w_ci=wilson(acc_w * ne, ne),
                 kappa_w=kappa_w(pred, gold, w), kappa_w_ci=kappa_boot(pred, gold, w, seed=seed))
        for l in labels:
            tp = sum(wi for p, g, wi in zip(pred, gold, w) if p == l and g == l)
            pp = sum(wi for p, g, wi in zip(pred, gold, w) if p == l)
            rr = sum(wi for p, g, wi in zip(pred, gold, w) if g == l)
            wp = [wi for p, wi in zip(pred, w) if p == l]
            wr = [wi for g, wi in zip(gold, w) if g == l]
            per[l]["precision_w"] = round(tp / pp, 3) if pp else None
            per[l]["recall_w"] = round(tp / rr, 3) if rr else None
            per[l]["precision_w_ci"] = wilson(tp / pp * n_eff(wp), n_eff(wp)) if pp else None
            per[l]["recall_w_ci"] = wilson(tp / rr * n_eff(wr), n_eff(wr)) if rr else None
    return m


# ------------------------------------------------------------------- loading

def _jkey(r):
    return (r["text_id"], r["family_id"], r["input_text"])


def load_key(run: str, challenge_dir: Path | None) -> dict[str, dict]:
    """item_id -> production labels. Null final critical is filled from the arbiter."""
    key = {}
    import runio
    fam_opts = {f: it["critical_options"] for f, it in runio.load_items().items()}
    arb_p = ROOT / f"runs/{run}/arbiter.jsonl"
    arb = {_jkey(a): a["critical"] for a in map(json.loads, open(arb_p))} if arb_p.exists() else {}
    for r in read_csv(ROOT / f"annotation/gold_key_{run}.csv"):
        r = {k: (v if v != "" else None) for k, v in r.items()}
        r["subset"], r["pi"] = "sampled", float(r["pi"])
        r["critical_options"] = fam_opts.get(r["family_id"])
        r["critical_source"] = "agree" if r["critical"] else None
        if r["critical"] is None and _jkey(r) in arb:
            r["critical"], r["critical_source"] = arb[_jkey(r)], "arbiter"
        key[r["item_id"]] = r
    if challenge_dir:
        cd = Path(challenge_dir)
        carb_p = cd / "arbiter.jsonl"
        carb = {_jkey(a): a["critical"] for a in map(json.loads, open(carb_p))} if carb_p.exists() else {}
        for j in map(json.loads, open(cd / "judgments.jsonl")):
            r = {k: j.get(k) for k in ("text_id", "family_id", "input_text", "text", "dimension")}
            r.update({f"{v}_{d}": j.get(f"{v}_{d}") for v in ("J1", "J2") for d in DIMS})
            r.update({f"L0_{d}": j.get(f"L0_{d}") for d in GENERAL_DIMS})
            r.update({d: j.get(d) for d in DIMS})
            r["critical_source"] = "agree" if r["critical"] else None
            if r["critical"] is None and _jkey(r) in carb:
                r["critical"], r["critical_source"] = carb[_jkey(r)], "arbiter"
            r.update(item_id=j["family_id"], subset="challenge", pi=None, critical_options=j["critical_options"])
            key[r["item_id"]] = r
    return key


def load_returns(patterns: list[str], key: dict, unsure_missing: bool = True):
    """item -> annotator -> {dim: label|None}. Returns (ann, notes)."""
    paths = sorted({p for pat in patterns for p in glob.glob(pat)})
    ann: dict[str, dict[str, dict]] = {}
    notes = Counter()
    for p in paths:
        for r in read_csv(p):
            iid = r.get("item_id", "")
            if iid.startswith("practice") or str(r.get("practice", "0")) == "1":
                continue
            if iid not in key:
                notes["not_in_key"] += 1
                continue
            if None in r:
                notes["rows_with_extra_columns"] += 1
            uns = {u.strip() for u in (r.get("unsure_dims") or "").replace(";", ",").replace("|", ",").split(",")}
            lab = {}
            for d in DIMS:
                v = (r.get(d) or "").strip() or None
                if v is not None and d in GENERAL_OPTIONS and v not in GENERAL_OPTIONS[d]:
                    notes[f"out_of_schema:{d}={v}"] += 1
                if v is not None and d == "critical":
                    opts = key[iid].get("critical_options") or []
                    if v == "mixed/unclear" and "unclear/mixed" in opts:
                        v = "unclear/mixed"
                    if opts and v not in opts:   # answer is not an option of this item: invalid
                        notes[f"critical_off_option_dropped:{r.get('annotator')}"] += 1
                        v = None
                if v is not None and d in uns:
                    notes[f"unsure:{d}"] += 1
                    if unsure_missing:
                        v = None
                lab[d] = v
            if r.get("annotator") in ann.get(iid, {}):
                notes["duplicate_rows_last_wins"] += 1
            ann.setdefault(iid, {})[r["annotator"]] = lab
    return ann, {"files": paths, **dict(sorted(notes.items()))}


# ---------------------------------------------------------------- reference set

def consensus(ann, d, rule, adj=None):
    cons, ties = {}, 0
    for item, v in ann.items():
        if adj and item in adj and (adj[item].get(d) or "").strip():
            cons[item] = adj[item][d].strip()
            continue
        votes = [x[d] for x in v.values() if x[d] is not None]
        c = Counter(votes).most_common()
        if not c:
            continue
        if rule == "majority":
            if c[0][1] >= 2 and c[0][1] > len(votes) / 2:
                cons[item] = c[0][0]
            else:
                ties += 1
        else:
            if len(c) > 1 and c[0][1] == c[1][1]:
                ties += 1
            else:
                cons[item] = c[0][0]
    return cons, ties


def pairwise(ann, key, d):
    raters = sorted({a for v in ann.values() for a in v})
    cols = {a: {i: v[a][d] for i, v in ann.items() if a in v and v[a][d] is not None} for a in raters}
    cols["judge(final)"] = {i: key[i][d] for i in ann if key[i].get(d)}
    out = {}
    names = list(cols)
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            a, b = names[x], names[y]
            common = sorted(set(cols[a]) & set(cols[b]))
            pa, pb = [cols[a][i] for i in common], [cols[b][i] for i in common]
            for sub in ("sampled", "challenge"):
                ix = [k for k, i in enumerate(common) if key[i]["subset"] == sub]
                if not ix:
                    continue
                qa, qb = [pa[k] for k in ix], [pb[k] for k in ix]
                ok = sum(p == q for p, q in zip(qa, qb))
                out[f"{a}~{b}|{sub}"] = {"n": len(ix), "agree": round(ok / len(ix), 3),
                                         "agree_ci": wilson(ok, len(ix)), "kappa": cohen_kappa(qa, qb)}
    return out


def score_reference(name, ann, key, rule, args, adj=None):
    members = sorted({a_ for v in ann.values() for a_ in v})
    rep = {"reference_set": name, "provenance": "human" if name == "human" else "machine (codex panel)",
           "members": members, "n_items": len(ann), "consensus_rule": rule,
           "alpha_nominal": {}, "pairwise": {}, "judge": {}}
    nk = Counter(len(v) for v in ann.values())
    rep["design"] = {"items_by_n_coders": {str(k): v for k, v in sorted(nk.items())},
                     "multi_coded_sampled": sum(len(v) >= 2 and key[i]["subset"] == "sampled" for i, v in ann.items()),
                     "multi_coded_challenge": sum(len(v) >= 2 and key[i]["subset"] == "challenge" for i, v in ann.items()),
                     "sampled_items": sum(key[i]["subset"] == "sampled" for i in ann),
                     "challenge_items": sum(key[i]["subset"] == "challenge" for i in ann),
                     "items_per_member": {m: sum(m in v for v in ann.values()) for m in members},
                     "single_coded_per_member": {m: sum(list(v) == [m] for v in ann.values()) for m in members}}
    rows, cons_all = [], {}
    for d in DIMS:
        cats = sorted({x[d] for v in ann.values() for x in v.values()} - {None})
        idx = {c: i for i, c in enumerate(cats)}
        units = [[idx[x[d]] for x in v.values() if x[d] is not None] for v in ann.values()]
        units = [u for u in units if len(u) >= 2]
        al = alpha_nominal(units, max(len(cats), 1))
        rep["alpha_nominal"][d] = {"alpha": None if al is None else round(al, 3), "n_units": len(units),
                                   "ci95": bootstrap_ci(units, len(cats), args.seed)}
        rep["pairwise"][d] = pairwise(ann, key, d)
        cons, ties = consensus(ann, d, rule, adj)
        cons_all[d] = cons
        rep["judge"][d] = {"no_consensus_excluded": ties}
        subsets = {"sampled": lambda i: key[i]["subset"] == "sampled",
                   "sampled_test": lambda i: key[i]["subset"] == "sampled" and not is_cal(i, args.seed, args.cal_frac),
                   "sampled_calibration": lambda i: key[i]["subset"] == "sampled" and is_cal(i, args.seed, args.cal_frac),
                   "challenge": lambda i: key[i]["subset"] == "challenge"}
        for sub, f in subsets.items():
            items = sorted(i for i in cons if f(i))
            for src in ("final", "J1", "J2", "L0"):
                col = d if src == "final" else f"{src}_{d}"
                if not items or col not in key[items[0]]:
                    continue
                pr = [(key[i].get(col), cons[i], key[i]["pi"]) for i in items]
                n_null = sum(x[0] is None for x in pr)
                pr = [x for x in pr if x[0] is not None]
                w = [1 / x[2] for x in pr] if sub.startswith("sampled") else None
                m = metrics([x[0] for x in pr], [x[1] for x in pr], w, args.seed)
                m["n_judge_null"] = n_null
                rep["judge"][d][f"{sub}/{src}"] = m
                gate = name == "human" and sub == "sampled_test" and src == "final"
                rows.append({"reference_set": name, "reference_provenance": rep["provenance"],
                             "dimension": d, "subset": sub, "source": src, "n": m["n"],
                             "n_judge_null": n_null, "acc": m.get("acc"), "acc_ci": m.get("acc_ci"),
                             "acc_w": m.get("acc_w"), "kappa": m.get("kappa"), "kappa_ci": m.get("kappa_ci"),
                             "kappa_w": m.get("kappa_w"), "kappa_w_ci": m.get("kappa_w_ci"),
                             "gate_applicable": gate,
                             "passes_H7": ((m.get("kappa") or 0) >= H7_KAPPA) if gate else None})
    return rep, rows, cons_all


# ------------------------------------------------------------ verdict level

def _verdicts(dim, var, channel, lab):
    """Violation / constraint_preserving / assumption from one label set, with the
    production rules of attribute.py (critical_match, general_spec, channel_dims).
    A missing label on a dimension the verdict needs makes that verdict undetermined."""
    from attribute import AMBIG_CHANNELS, CUE_CHANNELS, channel_dims
    from labels import NA_CERTAINTY, critical_match, general_spec, is_unclear
    crit = lab.get("critical")
    out = {"violation": None, "constraint_preserving": None, "assumption": None}
    if crit is None:
        return out
    if channel in CUE_CHANNELS:
        match = critical_match(dim, var["critical_value"], crit)
        out["violation"] = not match
        spec = general_spec(var.get("all_chips", []), var.get("general_spec"))
        contra, undetermined = False, False
        for d in channel_dims(channel, var):
            s = spec.get(d)
            if d == dim or s is None or NA_CERTAINTY in s:
                continue
            v = lab.get(d)
            if v is None:
                undetermined = True
                continue
            if d == "certainty" and v == NA_CERTAINTY:
                continue
            contra |= v not in s
        out["constraint_preserving"] = (False if (not match or contra) else
                                        None if undetermined else True)
    elif channel in AMBIG_CHANNELS:
        out["assumption"] = not is_unclear(crit)
    return out


def verdict_agreement(run: str, key: dict, cons_all: dict) -> dict:
    """Recompute each sampled item's verdicts from the reference labels and from the
    judge (production) labels; report agreement, kappa and the 2x2 table.
    Unit = (item, variant, channel) for Violation/CP (cue channels map 1:1 to a variant);
    Assumption does not depend on the variant, so its unit is the item."""
    import pandas as pd
    import runio
    from attribute import quarantined
    sp = ROOT / f"runs/{run}/scored.parquet"
    if not sp.exists():
        return {}
    items = runio.load_items()
    sc = pd.read_parquet(sp, columns=["text_id", "family_id", "input_text", "variant", "channel",
                                      "valid", "violation", "constraint_preserving", "assumption"])
    sc = sc[sc.valid.fillna(False).astype(bool)]
    stored = {}
    for r in sc.drop_duplicates(["text_id", "family_id", "input_text", "variant", "channel"]).itertuples():
        stored.setdefault((r.text_id, r.family_id, r.input_text), []).append(r)
    res, check = {}, Counter()
    rows = {"violation": [], "constraint_preserving": [], "assumption": []}
    for iid, k in key.items():
        if k["subset"] != "sampled":
            continue
        human = {d: cons_all[d].get(iid) for d in DIMS}
        if not any(v is not None for v in human.values()):
            continue
        judge = {d: k.get(d) for d in DIMS}
        it = items[k["family_id"]]
        seen_assumption = False
        for r in stored.get((k["text_id"], k["family_id"], k["input_text"]), []):
            var = it["variants"][r.variant]
            vh = _verdicts(it["dimension"], var, r.channel, human)
            vj = _verdicts(it["dimension"], var, r.channel, judge)
            for e in rows:
                if e == "assumption":
                    if seen_assumption or vj[e] is None and vh[e] is None:
                        continue
                st = getattr(r, e)
                if vj[e] is not None and st is not None and not pd.isna(st):
                    check["judge_recomputed_matches_stored" if bool(st) == vj[e] else "judge_recomputed_differs"] += 1
                if vj[e] is None and vh[e] is None:
                    continue
                rows[e].append({"item": iid, "judge": vj[e], "ref": vh[e], "pi": k["pi"],
                                "quarantine": quarantined(it)})
            if r.channel in ("bare", "noncrit"):
                seen_assumption = True
    for e, rr in rows.items():
        out = {}
        for scope, sel in (("all", rr), ("primary", [x for x in rr if not x["quarantine"]])):
            both = [x for x in sel if x["judge"] is not None and x["ref"] is not None]
            n = len(both)
            if not n:
                continue
            ok = sum(x["judge"] == x["ref"] for x in both)
            w = [1 / x["pi"] for x in both]
            tw = sum(w)
            aw = sum(wi for x, wi in zip(both, w) if x["judge"] == x["ref"]) / tw
            ne = n_eff(w)
            tab = Counter((x["judge"], x["ref"]) for x in both)
            out[scope] = {
                "n": n, "n_units_ref_undetermined": sum(x["ref"] is None for x in sel),
                "n_items": len({x["item"] for x in both}),
                "agree_k": ok, "agree": round(ok / n, 3), "agree_ci": wilson(ok, n),
                "kappa": cohen_kappa([x["judge"] for x in both], [x["ref"] for x in both]),
                "agree_w": round(aw, 3), "n_eff": round(ne, 1), "agree_w_ci": wilson(aw * ne, ne),
                "judge_T_ref_T": tab[(True, True)], "judge_T_ref_F": tab[(True, False)],
                "judge_F_ref_T": tab[(False, True)], "judge_F_ref_F": tab[(False, False)],
                "ref_positive": tab[(True, True)] + tab[(False, True)],
                "judge_positive": tab[(True, True)] + tab[(True, False)]}
        res[e] = out
    res["consistency_check"] = dict(check)
    return res


def challenge_key_accuracy(ann: dict, key: dict, cons_all: dict) -> dict:
    """Each member (and the judge) against the authored challenge keys
    (annotation/challenge_items.jsonl): critical, and every keyed dimension."""
    kp = ROOT / "annotation/challenge_items.jsonl"
    if not kp.exists():
        return {}
    keys = {c["cid"]: c for c in map(json.loads, open(kp))}
    members = sorted({a for i, v in ann.items() if i in keys for a in v})
    coders = {m: {i: v[m] for i, v in ann.items() if i in keys and m in v} for m in members}
    coders["judge(final)"] = {i: {d: key[i].get(d) for d in DIMS} for i in keys if i in key}
    coders["consensus"] = {i: {d: cons_all[d].get(i) for d in DIMS} for i in keys if i in ann}
    out = {}
    for m, lab in coders.items():
        crit = [(i, lab[i].get("critical"), keys[i]["key"]["critical"]) for i in sorted(lab)]
        ck = sum(g == k for _, g, k in crit)
        alld = [(lab[i].get(d), v) for i in lab for d, v in keys[i]["key"].items()]
        ak = sum(g == k for g, k in alld)
        out[m] = {"critical_k": ck, "critical_n": len(crit), "critical_ci": wilson(ck, len(crit)),
                  "keyed_k": ak, "keyed_n": len(alld),
                  "critical_misses": [{"cid": i, "text": keys[i]["text"], "key": k, "label": g}
                                      for i, g, k in crit if g != k]}
    return out


# --------------------------------------------------------------- paper macros

MACRO_DIMS = {"critical": "crit", "polarity": "pol", "speech_act": "act", "agent": "agt",
              "certainty": "cer", "politeness": "pz", "added_content": "add"}


def paper_macros(rep: dict, prefix: str = "human") -> dict[str, str]:
    """Flatten one reference-set section of judge_validation_<run>.json into formatted
    paper macros (shared by paper/se4all and paper/caleai make_macros.py).
    Percentages 0-100 with one decimal; kappa/alpha two decimals; counts as integers.
    Judge-vs-reference metrics: sampled/final (all sampled items, unweighted, Wilson CI on
    accuracy, item-bootstrap CI on kappa); design-weighted kappa_w; the preregistered H7
    gate on sampled_test/final; the challenge subset separately."""
    if not rep or not rep.get("n_items"):
        return {}
    f2 = lambda v: f"{v:.2f}"
    pc = lambda v: f"{100 * v:.1f}"
    M = {f"{prefix}_ready": "1", f"{prefix}_n_items": str(rep["n_items"]),
         f"{prefix}_n_members": str(len(rep["members"]))}
    des = rep.get("design") or {}
    for k in ("multi_coded_sampled", "multi_coded_challenge", "sampled_items", "challenge_items"):
        if k in des:
            M[f"{prefix}_{k.replace('_', '')}"] = str(des[k])
    if des:
        M[f"{prefix}_multicoded"] = str(des["multi_coded_sampled"] + des["multi_coded_challenge"])
        M[f"{prefix}_singlecoded"] = str(des["items_by_n_coders"].get("1", 0))
        for m, n in des["items_per_member"].items():
            M[f"{prefix}_items_{''.join(c for c in m if c.isalnum())}"] = str(n)
        for m, n in des.get("single_coded_per_member", {}).items():
            M[f"{prefix}_single_{''.join(c for c in m if c.isalnum())}"] = str(n)
    al, ka, gk, gate = [], [], [], []
    for d, s in MACRO_DIMS.items():
        a = rep["alpha_nominal"].get(d) or {}
        if a.get("alpha") is not None:
            M[f"{prefix}_{s}_alpha"] = f2(a["alpha"]); al.append(a["alpha"])
            M[f"{prefix}_{s}_alpha_n"] = str(a["n_units"])
            if a.get("ci95"):
                M[f"{prefix}_{s}_alpha_lo"], M[f"{prefix}_{s}_alpha_hi"] = map(f2, a["ci95"])
        j = rep["judge"].get(d) or {}
        t = j.get("sampled/final") or {}
        if t.get("n"):
            M[f"{prefix}_{s}_n"] = str(t["n"])
            M[f"{prefix}_{s}_acc"] = pc(t["acc"])
            M[f"{prefix}_{s}_acc_k"] = str(round(t["acc"] * t["n"]))
            M[f"{prefix}_{s}_acc_lo"], M[f"{prefix}_{s}_acc_hi"] = map(pc, t["acc_ci"])
            if t.get("kappa") is not None:
                M[f"{prefix}_{s}_kappa"] = f2(t["kappa"]); ka.append(t["kappa"])
                if t.get("kappa_ci"):
                    M[f"{prefix}_{s}_kappa_lo"], M[f"{prefix}_{s}_kappa_hi"] = map(f2, t["kappa_ci"])
            if t.get("kappa_w") is not None:
                M[f"{prefix}_{s}_kappaw"] = f2(t["kappa_w"])
                if t.get("kappa_w_ci"):
                    M[f"{prefix}_{s}_kappaw_lo"], M[f"{prefix}_{s}_kappaw_hi"] = map(f2, t["kappa_w_ci"])
            if t.get("acc_w") is not None:
                M[f"{prefix}_{s}_accw"] = pc(t["acc_w"])
            M[f"{prefix}_{s}_nnull"] = str(t.get("n_judge_null", 0))
            M[f"{prefix}_{s}_noconsensus"] = str(j.get("no_consensus_excluded", 0))
        g = j.get("sampled_test/final") or {}
        if g.get("kappa") is not None:
            M[f"{prefix}_{s}_gkappa"] = f2(g["kappa"]); gk.append(g["kappa"])
            M[f"{prefix}_{s}_gn"] = str(g["n"])
            if g.get("kappa_ci"):
                M[f"{prefix}_{s}_gkappa_lo"], M[f"{prefix}_{s}_gkappa_hi"] = map(f2, g["kappa_ci"])
            ok = g["kappa"] >= H7_KAPPA
            M[f"{prefix}_{s}_gate"] = "pass" if ok else "fail"
            gate.append(ok)
        c = j.get("challenge/final") or {}
        if c.get("n"):
            M[f"{prefix}_{s}_chn"] = str(c["n"])
            M[f"{prefix}_{s}_chacc_k"] = str(round(c["acc"] * c["n"]))
            M[f"{prefix}_{s}_chacc"] = pc(c["acc"])
    nc = [(rep["judge"].get(d) or {}).get("no_consensus_excluded", 0) for d in MACRO_DIMS]
    M[f"{prefix}_noconsensus_max"], M[f"{prefix}_noconsensus_sum"] = str(max(nc)), str(sum(nc))
    cc = (rep.get("verdict") or {}).get("consistency_check") or {}
    M[f"{prefix}_v_recomputed_ok"] = str(cc.get("judge_recomputed_matches_stored", 0))
    M[f"{prefix}_v_recomputed_diff"] = str(cc.get("judge_recomputed_differs", 0))
    glo = [float(v) for k, v in M.items() if k.endswith("_gkappa_lo")]
    if glo:
        M[f"{prefix}_gkappa_lo_min"] = f2(min(glo))
    for nm, xs in (("alpha", al), ("kappa", ka), ("gkappa", gk)):
        if xs:
            M[f"{prefix}_{nm}_min"], M[f"{prefix}_{nm}_max"] = f2(min(xs)), f2(max(xs))
    if gate:
        M[f"{prefix}_gate_pass_k"], M[f"{prefix}_gate_n"] = str(sum(gate)), str(len(gate))
        M[f"{prefix}_gate_all"] = "1" if all(gate) else "0"
    for e, s in (("violation", "viol"), ("constraint_preserving", "cp"), ("assumption", "asm")):
        for scope in ("primary", "all"):
            v = ((rep.get("verdict") or {}).get(e) or {}).get(scope)
            if not v:
                continue
            b = f"{prefix}_v_{s}" + ("" if scope == "primary" else "_all")
            M[b + "_k"], M[b + "_n"] = str(v["agree_k"]), str(v["n"])
            M[b], (M[b + "_lo"], M[b + "_hi"]) = pc(v["agree"]), map(pc, v["agree_ci"])
            M[b + "_kappa"] = f2(v["kappa"]) if v.get("kappa") is not None else "NA"
            M[b + "_w"] = pc(v["agree_w"])
            M[b + "_w_lo"], M[b + "_w_hi"] = map(pc, v["agree_w_ci"])
            # tp/fp/fn/tn: judge verdict vs reference verdict (reference = truth)
            for t, nm in (("judge_T_ref_T", "tp"), ("judge_T_ref_F", "fp"), ("judge_F_ref_T", "fn"),
                          ("judge_F_ref_F", "tn"), ("ref_positive", "refpos"),
                          ("judge_positive", "judgepos"), ("n_units_ref_undetermined", "undet")):
                M[b + "_" + nm] = str(v[t])
    for m, c in (rep.get("challenge_key") or {}).items():
        b = f"{prefix}_chkey_" + "".join(ch for ch in m.split("(")[0] if ch.isalnum())
        M[b + "_k"], M[b + "_n"] = str(c["critical_k"]), str(c["critical_n"])
        M[b + "_keyed_k"], M[b + "_keyed_n"] = str(c["keyed_k"]), str(c["keyed_n"])
    return M


def write_consensus(path, name, members, cons_all, ann):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "reference_set", "provenance", "members"] + DIMS + [f"votes_{d}" for d in DIMS])
        for i in sorted(ann):
            votes = [";".join(f"{a}={ann[i][a][d]}" for a in sorted(ann[i])) for d in DIMS]
            w.writerow([i, name, "human" if name == "human" else "machine", "|".join(members)]
                       + [cons_all[d].get(i, "") for d in DIMS] + votes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run")
    ap.add_argument("--human", "--csv", dest="human", nargs="*", default=[],
                    help="human annotate.html exports (gate set)")
    ap.add_argument("--panel", nargs="*", default=[], help="codex panel exports (machine, provisional)")
    ap.add_argument("--challenge-judgments", type=Path, default=None,
                    help="dir with judgments.jsonl (+arbiter.jsonl) for ch-* items")
    ap.add_argument("--panel-members", default=None,
                    help="comma-separated annotator ids to keep from --panel (sensitivity)")
    ap.add_argument("--tag", default="", help="suffix for output files (sensitivity runs)")
    ap.add_argument("--unsure-as-label", action="store_true",
                    help="keep labels listed in unsure_dims (default: treat as missing)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--cal-frac", type=float, default=0.25)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not a.run or not (a.human or a.panel):
        ap.error("--run and at least one of --human/--panel are required")
    key = load_key(a.run, a.challenge_judgments)
    adj_p = ROOT / f"annotation/adjudicated_{a.run}.csv"
    adj = {r["item_id"]: r for r in read_csv(adj_p)} if adj_p.exists() else {}
    rep = {"run": a.run, "seed": a.seed, "cal_frac": a.cal_frac,
           "unsure_policy": "label kept" if a.unsure_as_label else "unsure dims -> missing",
           "key": {"n_sampled": sum(k["subset"] == "sampled" for k in key.values()),
                   "n_challenge": sum(k["subset"] == "challenge" for k in key.values()),
                   "critical_source": dict(Counter(k["critical_source"] for k in key.values()))},
           "human": None, "panel": None}
    rows = []
    for name, pats, rule in (("human", a.human, "plurality"), ("panel", a.panel, "majority")):
        if not pats:
            continue
        ann, notes = load_returns(pats, key, not a.unsure_as_label)
        if name == "panel" and a.panel_members:
            keep = set(a.panel_members.split(","))
            ann = {i: {m: x for m, x in v.items() if m in keep} for i, v in ann.items()}
            ann = {i: v for i, v in ann.items() if v}
        if not ann:
            rep[name] = {"reference_set": name, "n_items": 0, "notes": notes}
            continue
        r, rr, cons_all = score_reference(name, ann, key, rule, a, adj if name == "human" else None)
        r["notes"] = notes
        r["verdict"] = verdict_agreement(a.run, key, cons_all)
        r["challenge_key"] = challenge_key_accuracy(ann, key, cons_all)
        rep[name] = r
        rows += rr
        fn = "human_consensus" if name == "human" else "panel_majority"
        write_consensus(ROOT / f"annotation/{fn}_{a.run}{a.tag}.csv", name, r["members"], cons_all, ann)
    out = ROOT / f"annotation/judge_validation_{a.run}{a.tag}"
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    if rows:
        with out.with_suffix(".csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    for name in ("human", "panel"):
        r = rep[name]
        if not r or not r.get("n_items"):
            print(f"[{name}] no returns")
            continue
        print(f"[{name}] members: {r['members']}; items: {r['n_items']}")
        for d in DIMS:
            al = r["alpha_nominal"][d]
            t = r["judge"][d].get("sampled/final", {})
            print(f"  {d:13s} alpha={al['alpha']} (n={al['n_units']})  sampled/final: n={t.get('n')} "
                  f"acc={t.get('acc')} kappa={t.get('kappa')} kappa_w={t.get('kappa_w')}")
        for e, v in (r.get("verdict") or {}).items():
            if isinstance(v, dict) and "primary" in v:
                p = v["primary"]
                print(f"  verdict {e:22s} primary: {p['agree_k']}/{p['n']} agree kappa={p['kappa']} "
                      f"(judge+/ref+ {p['judge_positive']}/{p['ref_positive']})")
        for m, c in (r.get("challenge_key") or {}).items():
            print(f"  challenge key {m:14s} critical {c['critical_k']}/{c['critical_n']}  "
                  f"keyed dims {c['keyed_k']}/{c['keyed_n']}")
    print(f"wrote {out}.json/.csv  (H7 gate kappa >= {H7_KAPPA}: human set, sampled_test, final only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
