"""Score Part 4 repair-audit returns (annotation_package/repair_audit.html CSVs).

usage: python src/score_repair_audit.py [CSV ...]            (default: annotation/returns_repair/*.csv)
          [--key annotation/repair_audit_key.csv] [--out analysis/repair_audit]
       Part 11 (W-C guard transfer, make_repair_audit.py --source guard_wc):
       python src/score_repair_audit.py --key annotation/repair_audit_transfer_key.csv
          (defaults then follow the key's stem: returns annotation/returns_repair_transfer/*.csv,
           output analysis/repair_audit_transfer/, sample annotation/repair_audit_transfer_sample.json)

Per arm (repaired = guard G1 texts that differ from the first pass; control = unchanged
first-pass texts the judge scored as passing), Wilson 95% CIs on:
  usable              Pass A quality == "yes"            (sensitivity: yes or "minor fix needed")
  contract-preserving Pass B contract == "yes"
  usable & preserving both of the above
  added stance        Pass B added == "yes"  (meaning, certainty, politeness or speaker not given)
Units: (a) per annotator rating, items as the unit within an annotator; (b) item-level
consensus = strict majority of the annotators who gave a usable answer (ties and all-unsure
are 'unknown', reported, excluded from the denominator); (c) all ratings pooled (ratings
are not independent across annotators, so the pooled CI is descriptive only).
"Can't judge" and missing answers are unknown, never coded as failure or success. Practice
rows are dropped. The repaired-minus-control difference uses Newcombe's hybrid score CI.
Pool-weighted (Hajek, 1/pi_mc) consensus point estimates are given as a sensitivity: the
sample is model-balanced, not proportional to the eligible pool. A key without pi_mc (Part 11:
the FREEZE.md prespecified first-20-by-SHA256 list) has no design weights: no Hajek column,
sample rates only, plus a descriptive by-model table.
Agreement: pairwise Cohen's kappa and percent agreement per question, and Krippendorff's
nominal alpha across all annotators (Pass A also as yes / not-yes).
       Part 17 (repair audit v2, make_repair_audit_v2.py; 3 raters per item, 4 strata arm x pool):
       python src/score_repair_audit.py --key annotation/repair_audit_v2_key.csv
          (returns annotation/returns_repair_v2/*.csv, output analysis/repair_audit_v2/). Adds the
          repaired-minus-control Newcombe difference per pool (discovery, transfer) and the count of
          items with fewer than 3 usable ratings. Consensus = strict majority of the known answers.
       python src/score_repair_audit.py --self-check     (simulated returns on the real v2 key)
Outputs: <out>/report.md, <out>/items.csv (key joined with every rating + consensus),
<out>/summary.json.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agree_stats import cohen_kappa  # noqa: E402
from score_gold import alpha_nominal, wilson  # noqa: E402

Q = {"quality": ["yes", "minor fix needed", "no"], "contract": ["yes", "partly", "no"], "added": ["yes", "no"]}
ARMS = ("repaired", "control")


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_returns(paths, key):
    ratings = {}          # (annotator, item_id) -> dict
    problems = []
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac-"):
                continue
            if r["item_id"] not in key:
                problems.append(f"{p}: unknown item {r['item_id']}")
                continue
            a = r["annotator"].strip()
            k = (a, r["item_id"])
            if k in ratings:
                problems.append(f"{p}: duplicate rating {k}; keeping the later export")
            unsure_b = set(filter(None, (r.get("b_unsure") or "").split("|")))
            ratings[k] = {
                "annotator": a, "item_id": r["item_id"],
                "quality": None if r.get("a_unsure") == "1" else (r.get("a_quality") or None),
                "contract": None if "contract" in unsure_b else (r.get("b_contract") or None),
                "added": None if "added" in unsure_b else (r.get("b_added") or None),
                "a_note": r.get("a_note", ""),
                "a_time_ms": float(r["a_time_ms"]) if r.get("a_time_ms") else None,
                "b_time_ms": float(r["b_time_ms"]) if r.get("b_time_ms") else None,
            }
            for q, opts in Q.items():
                v = ratings[k][q]
                if v is not None and v not in opts:
                    problems.append(f"{p}: {k} {q}={v!r} not a valid option; treated as unknown")
                    ratings[k][q] = None
    return ratings, problems


def outcomes(r):
    """Binary endpoints from one rating; None = unknown."""
    q, c, ad = r["quality"], r["contract"], r["added"]
    usable = None if q is None else q == "yes"
    usable_lax = None if q is None else q in ("yes", "minor fix needed")
    pres = None if c is None else c == "yes"
    if usable is False or pres is False:
        both = False
    elif usable is None or pres is None:
        both = None
    else:
        both = True
    return {"usable": usable, "usable_or_minor": usable_lax, "preserving": pres,
            "usable_and_preserving": both, "added_stance": None if ad is None else ad == "yes"}


ENDPOINTS = ["usable", "usable_or_minor", "preserving", "usable_and_preserving", "added_stance"]


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "unknown": len(vals) - n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def newcombe(a, b):
    """Difference a.p - b.p with Newcombe hybrid score CI (method 10)."""
    if not a["n"] or not b["n"]:
        return None
    d = a["p"] - b["p"]
    l1, u1 = a["ci"]; l2, u2 = b["ci"]
    lo = d - ((a["p"] - l1) ** 2 + (u2 - b["p"]) ** 2) ** 0.5
    hi = d + ((u1 - a["p"]) ** 2 + (b["p"] - l2) ** 2) ** 0.5
    return {"diff": d, "ci": [round(max(-1, lo), 3), round(min(1, hi), 3)]}


def consensus(vals):
    known = [v for v in vals if v is not None]
    if not known:
        return None
    c = Counter(known)
    if c[True] * 2 > len(known):
        return True
    if c[False] * 2 > len(known):
        return False
    return None   # tie


def fmt(r):
    if not r or not r["n"]:
        return "n/a (0 known)"
    lo, hi = r["ci"]
    s = f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"
    return s + (f"; {r['unknown']} unknown" if r["unknown"] else "")


def self_check() -> int:
    """Simulate returns for the v2 key (repaired usable ~.65, control ~.92) and run the scorer on them."""
    import contextlib
    import io
    import random
    import tempfile
    keyp = ROOT / "annotation" / "repair_audit_v2_key.csv"
    key = read_csv(keyp)
    rng = random.Random(7)
    raters = sorted({x for r in key for x in r["raters"].split("|")})
    rows = {x: [] for x in raters}
    for r in key:
        rep_ = r["arm"] == "repaired"
        for x in r["raters"].split("|"):
            good = rng.random() < (0.65 if rep_ else 0.92)
            q = "yes" if good else rng.choice(["minor fix needed", "no"])
            c = "yes" if rng.random() < (0.85 if rep_ else 0.97) else rng.choice(["partly", "no"])
            rows[x].append({"item_id": r["item_id"], "annotator": x, "practice": 0, "a_quality": q,
                            "a_unsure": 0, "a_note": "" if good else "x", "a_time_ms": 4000,
                            "b_contract": c, "b_added": "yes" if rng.random() < 0.2 else "no", "b_unsure": "",
                            "b_time_ms": 6000})
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for x, rs in rows.items():
            p = Path(td) / f"repair_audit_v2_{x}.csv"
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
            paths.append(str(p))
        out = Path(td) / "out"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main([*paths, "--key", str(keyp), "--out", str(out)])
        S = json.loads((out / "summary.json").read_text())
    assert rc == 0
    assert len(key) == 120 and all(len(r["raters"].split("|")) == 3 for r in key)
    assert S["items_with_fewer_than_3_ratings"] == 0, S["items_with_fewer_than_3_ratings"]
    d = S["difference_repaired_minus_control"]["usable"]
    assert d["diff"] < 0 and d["ci"][1] < 0, d
    for pool in ("discovery", "transfer"):
        dp = S["difference_by_pool"][pool]["usable"]
        assert dp is not None and dp["diff"] < 0, (pool, dp)
        assert S["difference_by_pool"][pool]["n_items"] == {"repaired": 30, "control": 30}
    assert sum(S["per_arm"][a]["usable"]["n"] for a in ARMS) == 120
    print(f"self-check OK: usable diff {100 * d['diff']:+.1f} pp {d['ci']}; "
          f"per pool " + ", ".join(f"{p} {100 * S['difference_by_pool'][p]['usable']['diff']:+.1f}" for p in S["difference_by_pool"]))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-check", action="store_true", help="run on simulated Part 17 returns and exit")
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "repair_audit_key.csv"))
    ap.add_argument("--out", default=None, help="default: analysis/<key stem without _key>")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    stem = Path(a.key).name.removesuffix(".csv").removesuffix("_key")      # repair_audit[_transfer]
    suffix = stem.removeprefix("repair_audit")                              # "" or "_transfer"
    a.out = a.out or str(ROOT / "analysis" / stem)
    ret_dir = ROOT / "annotation" / f"returns_repair{suffix}"
    label = {"": "Part 4 repair audit", "_transfer": "Part 11 transfer repair audit (W-C guard)",
                                          "_v2": "Part 17 repair audit v2 (new sentences, 3 raters per item)"}.get(
        suffix, f"{stem} repair audit")
    paths = a.csv or sorted(glob.glob(str(ret_dir / "*.csv")))
    key = {r["item_id"]: r for r in read_csv(a.key)}
    if not paths:
        print(f"no return CSVs found ({ret_dir.relative_to(ROOT)}/*.csv)", file=sys.stderr)
        return 1
    ratings, problems = load_returns(paths, key)
    annots = sorted({r["annotator"] for r in ratings.values()})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    for r in ratings.values():
        r.update(outcomes(r))
    by_item = defaultdict(list)
    for r in ratings.values():
        by_item[r["item_id"]].append(r)

    S = {"returns": paths, "annotators": annots, "problems": problems, "n_items_key": len(key),
         "per_arm": {}, "per_annotator": {}, "pooled_ratings": {}, "agreement": {}}
    item_rows = []
    for iid, k in key.items():
        rs = by_item.get(iid, [])
        row = {**k, "n_ratings": len(rs)}
        for e in ENDPOINTS:
            row["cons_" + e] = consensus([r[e] for r in rs])
        for an in annots:
            m = next((r for r in rs if r["annotator"] == an), None)
            for f in ("quality", "contract", "added", "a_note", "a_time_ms", "b_time_ms"):
                row[f"{an}_{f}"] = m[f] if m else None
        item_rows.append(row)

    for arm in ARMS:
        its = [r for r in item_rows if r["arm"] == arm]
        S["per_arm"][arm] = {"items": len(its), "rated_items": sum(r["n_ratings"] > 0 for r in its)}
        for e in ENDPOINTS:
            S["per_arm"][arm][e] = rate([r["cons_" + e] for r in its if r["n_ratings"] > 0])
            # Hajek pool-weighted point estimate (sensitivity; only for keys with pi)
            kw = [(r["cons_" + e], 1 / float(r["pi_mc"])) for r in its
                  if r["cons_" + e] is not None and (r.get("pi_mc") or "") != "" and float(r["pi_mc"]) > 0]
            S["per_arm"][arm][e]["hajek_weighted_p"] = (sum(w for v, w in kw if v) / sum(w for _, w in kw)) if kw else None
        S["pooled_ratings"][arm] = {e: rate([r[e] for r in ratings.values() if key[r["item_id"]]["arm"] == arm])
                                    for e in ENDPOINTS}
        for an in annots:
            rr = [r for r in ratings.values() if r["annotator"] == an and key[r["item_id"]]["arm"] == arm]
            S["per_annotator"].setdefault(an, {})[arm] = {e: rate([r[e] for r in rr]) for e in ENDPOINTS}
            S["per_annotator"][an]["median_time_s"] = {
                p: (sorted(t)[len(t) // 2] / 1000 if t else None)
                for p, t in (("A", [r["a_time_ms"] for r in ratings.values() if r["annotator"] == an and r["a_time_ms"]]),
                             ("B", [r["b_time_ms"] for r in ratings.values() if r["annotator"] == an and r["b_time_ms"]]))}
    S["difference_repaired_minus_control"] = {
        e: newcombe(S["per_arm"]["repaired"][e], S["per_arm"]["control"][e]) for e in ENDPOINTS}

    # Part 17: items with fewer than 3 usable ratings, and the difference within each pool
    S["items_with_fewer_than_3_ratings"] = sum(r["n_ratings"] < 3 for r in item_rows) if "raters" in next(iter(key.values())) else None
    S["difference_by_pool"] = {}
    if "pool" in next(iter(key.values())):
        for pool in sorted({k["pool"] for k in key.values()}):
            pr = {arm: [r for r in item_rows if r["pool"] == pool and r["arm"] == arm and r["n_ratings"]] for arm in ARMS}
            rt = {arm: {e: rate([r["cons_" + e] for r in pr[arm]]) for e in ENDPOINTS} for arm in ARMS}
            S["difference_by_pool"][pool] = {
                "n_items": {arm: sum(1 for r in item_rows if r["pool"] == pool and r["arm"] == arm) for arm in ARMS},
                "per_arm": rt,
                **{e: newcombe(rt["repaired"][e], rt["control"][e]) for e in ENDPOINTS}}

    # breakdown of consensus by channel group (descriptive)
    S["by_channel_group"] = {}
    for arm in ARMS:
        for g in ("cue", "ambiguous"):
            its = [r for r in item_rows if r["arm"] == arm and r["channel_group"] == g and r["n_ratings"]]
            S["by_channel_group"][f"{arm}/{g}"] = {e: rate([r["cons_" + e] for r in its])
                                                  for e in ("usable", "preserving", "usable_and_preserving", "added_stance")}

    # agreement
    variants = {"quality": lambda v: v, "quality_yes_vs_not": lambda v: None if v is None else v == "yes",
                "contract": lambda v: v, "contract_yes_vs_not": lambda v: None if v is None else v == "yes",
                "added": lambda v: v}
    for name, f in variants.items():
        q = name.split("_")[0]
        pw = []
        for x, y in combinations(annots, 2):
            common = [(f(ratings[(x, i)][q]), f(ratings[(y, i)][q])) for i in key
                      if (x, i) in ratings and (y, i) in ratings]
            common = [(u, v) for u, v in common if u is not None and v is not None]
            pw.append({"pair": f"{x}-{y}", "n": len(common),
                       "agree": round(sum(u == v for u, v in common) / len(common), 3) if common else None,
                       "kappa": cohen_kappa([u for u, _ in common], [v for _, v in common]) if common else None})
        cats = sorted({str(f(r[q])) for r in ratings.values() if f(r[q]) is not None})
        idx = {c: i for i, c in enumerate(cats)}
        units = [[idx[str(f(r[q]))] for r in by_item[i] if f(r[q]) is not None] for i in key]
        units = [u for u in units if len(u) >= 2]
        alpha = alpha_nominal(units, len(cats)) if units and len(cats) > 1 else None
        S["agreement"][name] = {"pairwise": pw, "krippendorff_alpha_nominal": alpha, "units_with_2plus": len(units)}

    cols = list(item_rows[0].keys())
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(item_rows)

    weighted = any((k.get("pi_mc") or "") != "" for k in key.values())
    S["design_weights"] = weighted
    S["by_model_descriptive"] = {
        f"{arm}/{m}": {"items": sum(r["arm"] == arm and r["assigned_model"] == m for r in item_rows),
                       **{e: rate([r["cons_" + e] for r in item_rows if r["arm"] == arm
                                   and r["assigned_model"] == m and r["n_ratings"]])
                          for e in ("usable", "preserving", "usable_and_preserving")}}
        for arm in ARMS for m in sorted({r["assigned_model"] for r in item_rows})}
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")
    L = [f"# {label}: human ratings\n",
         f"Generated by `src/score_repair_audit.py`. Returns: {len(paths)} file(s), annotators: {', '.join(annots)}. "
         f"Key: `{Path(a.key).relative_to(ROOT) if Path(a.key).is_relative_to(ROOT) else a.key}` "
         f"(frozen hash-ordered sample, {sum(k["arm"] == "repaired" for k in key.values())} repaired + {sum(k["arm"] == "control" for k in key.values())} controls; `annotation/{stem}_sample.json`).\n",
         "Wilson 95% CIs on item-level consensus (strict majority of known answers; ties/unsure = unknown, excluded "
         "from n and reported). "
         + ("Human ratings of a model-balanced sample: these are sample rates, not pool "
            "prevalences; Hajek 1/pi weighted points are a sensitivity. Report the actual completed n.\n" if weighted else
            "Prespecified deterministic list (FREEZE.md: first 20 distinct texts per arm by ascending SHA256), "
            "not a probability sample: no design weights; these are rates on the listed items only. "
            "Counts by model are descriptive. Report the actual completed n.\n"),
         "| endpoint | repaired | control | repaired - control [Newcombe 95%] |" + (" Hajek-weighted (rep / ctl) |" if weighted else ""),
         "|---|---|---|---|" + ("---|" if weighted else "")]
    for e in ENDPOINTS:
        d = S["difference_repaired_minus_control"][e]
        hw = [S["per_arm"][arm][e]["hajek_weighted_p"] for arm in ARMS]
        L.append(f"| {e} | {fmt(S['per_arm']['repaired'][e])} | {fmt(S['per_arm']['control'][e])} | "
                 + (f"{100 * d['diff']:+.1f} pp [{100 * d['ci'][0]:+.1f}, {100 * d['ci'][1]:+.1f}]" if d else "n/a")
                 + (" | " + " / ".join("n/a" if v is None else f"{100 * v:.1f}%" for v in hw) if weighted else "") + " |")
    if not weighted:
        L += ["\n## By model (consensus, descriptive; unbalanced prespecified list)\n",
              "| arm/model | items | usable | preserving | usable & preserving |", "|---|---|---|---|---|"]
        for g, x in S["by_model_descriptive"].items():
            L.append(f"| {g} | {x['items']} | {fmt(x['usable'])} | {fmt(x['preserving'])} | {fmt(x['usable_and_preserving'])} |")
    if S["difference_by_pool"]:
        L += ["\n## Repaired minus control, per pool (item consensus, Newcombe 95%)\n",
              f"Items with fewer than 3 usable ratings: {S['items_with_fewer_than_3_ratings']}.\n",
              "| pool | endpoint | repaired | control | difference |", "|---|---|---|---|---|"]
        for pool, x in S["difference_by_pool"].items():
            for e in ENDPOINTS:
                d = x[e]
                L.append(f"| {pool} | {e} | {fmt(x['per_arm']['repaired'][e])} | {fmt(x['per_arm']['control'][e])} | "
                         + (f"{100 * d['diff']:+.1f} pp [{100 * d['ci'][0]:+.1f}, {100 * d['ci'][1]:+.1f}]" if d else "n/a") + " |")
    L += ["\n## Per annotator (items within annotator)\n", "| annotator | arm | usable | preserving | usable & preserving | added stance |",
          "|---|---|---|---|---|---|"]
    for an in annots:
        for arm in ARMS:
            x = S["per_annotator"][an][arm]
            L.append(f"| {an} | {arm} | {fmt(x['usable'])} | {fmt(x['preserving'])} | {fmt(x['usable_and_preserving'])} | {fmt(x['added_stance'])} |")
    L += ["\n## By channel group (consensus, descriptive)\n", "| arm/group | usable | preserving | usable & preserving | added stance |", "|---|---|---|---|---|"]
    for g, x in S["by_channel_group"].items():
        L.append(f"| {g} | {fmt(x['usable'])} | {fmt(x['preserving'])} | {fmt(x['usable_and_preserving'])} | {fmt(x['added_stance'])} |")
    L += ["\n## Agreement between annotators\n", "| question | pairwise (n, % agree, Cohen kappa) | Krippendorff alpha (nominal) |", "|---|---|---|"]
    for name, x in S["agreement"].items():
        pw = "; ".join(f"{p['pair']}: n={p['n']}, {'n/a' if p['agree'] is None else f'{100 * p['agree']:.0f}%'}, "
                       f"k={'n/a' if p['kappa'] is None else p['kappa']}" for p in x["pairwise"]) or "single annotator"
        al = x["krippendorff_alpha_nominal"]
        L.append(f"| {name} | {pw} | {'n/a' if al is None else round(al, 3)} |")
    L += ["\n## Not usable or not preserving (all kept; consensus)\n", "| item | arm | model | channel | input | sentence | notes |", "|---|---|---|---|---|---|---|"]
    for r in sorted(item_rows, key=lambda r: (r["arm"], r["item_id"])):
        if r["cons_usable"] is False or r["cons_preserving"] is False:
            notes = " / ".join(str(r[f"{an}_a_note"]) for an in annots if r.get(f"{an}_a_note"))
            L.append(f"| {r['item_id']} | {r['arm']} | {r['assigned_model']} | {r['channels']} | {r['input_text']} | "
                     f"{r['text']} | {notes.replace('|', '/')} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
