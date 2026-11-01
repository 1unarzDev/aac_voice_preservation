"""Score Part 5 W-C source-check returns (annotation_package/wc_source_check.html CSVs).

usage: python src/score_wc_source_check.py [CSV ...]        (default: annotation/returns_wc/*.csv)
          [--key annotation/wc_source_check_key.csv] [--out analysis/wc_source_check]

Per family (20, frozen hash-ordered sample, 7 polarity / 7 speech act / 6 politeness):
  authored agreement   human value of source A / B == authored critical value (source unit, n=40)
  codex agreement      human value == codex verifier's critical value (analysis/item_verification/verifier_r2.csv)
  both authored        both sources of the family match the authored values
  ambiguity confirmed  "Could the bare keywords reasonably mean either sentence?" == yes
                       (also reported: only A / only B / neither counts)
  minimal pair         "Do A and B differ ONLY on that dimension?" == yes
  family passes        both authored & ambiguity confirmed & minimal pair
Reference rows without humans: authored-vs-codex agreement and codex bare_supports_both on the
same sample. Units as in Part 4: (a) per annotator, (b) item consensus = strict majority of
the annotators with a known answer (ties and all-unsure are unknown: reported, excluded from
n), (c) pooled ratings (not independent; descriptive only). Wilson 95% CIs. "Can't judge"
and missing answers are unknown, never success or failure. Practice rows are dropped.
Agreement: pairwise Cohen's kappa / % agreement and Krippendorff's nominal alpha on the value
labels (A and B stacked), the keywords-fit answer and the differ-only answer.
Outputs: <out>/report.md, <out>/items.csv, <out>/summary.json.
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

BARE = ["yes", "only A", "only B", "neither"]
FAM_ENDPOINTS = ["both_authored", "both_codex", "ambiguity_confirmed", "minimal_pair", "family_passes"]
SRC_ENDPOINTS = ["authored_match", "codex_match"]
STRATA = ["polarity", "speech_act", "politeness"]


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def and3(*vals):
    if any(v is False for v in vals):
        return False
    if any(v is None for v in vals):
        return None
    return True


def eq(a, b):
    return None if not a or not b else a == b


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "unknown": len(vals) - n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def consensus(vals):
    known = [v for v in vals if v is not None]
    if not known:
        return None
    c = Counter(known)
    top, cnt = c.most_common(1)[0]
    return top if cnt * 2 > len(known) else None


def fmt(r):
    if not r or not r["n"]:
        return "n/a (0 known)"
    lo, hi = r["ci"]
    s = f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"
    return s + (f"; {r['unknown']} unknown" if r["unknown"] else "")


def load_returns(paths, key):
    ratings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac-"):
                continue
            k = key.get(r["item_id"])
            if not k:
                problems.append(f"{p}: unknown item {r['item_id']}"); continue
            a = r["annotator"].strip()
            if (a, r["item_id"]) in ratings:
                problems.append(f"{p}: duplicate rating {(a, r['item_id'])}; keeping the later export")
            uns = set(filter(None, (r.get("unsure") or "").split("|")))
            opts = set(json.loads(k["options"])) if k.get("options") else None
            rec = {"annotator": a, "item_id": r["item_id"],
                   "A": None if "valA" in uns else (r.get("value_A") or None),
                   "B": None if "valB" in uns else (r.get("value_B") or None),
                   "bare": None if "bare" in uns else (r.get("bare_fits") or None),
                   "only": None if "only" in uns else (r.get("differ_only") or None),
                   "note": r.get("note", ""), "time_ms": float(r["time_ms"]) if r.get("time_ms") else None}
            for f, allowed in (("A", opts), ("B", opts), ("bare", set(BARE)), ("only", {"yes", "no"})):
                if rec[f] is not None and allowed and rec[f] not in allowed:
                    problems.append(f"{p}: {(a, r['item_id'])} {f}={rec[f]!r} invalid; treated as unknown"); rec[f] = None
            ratings[(a, r["item_id"])] = rec
    return ratings, problems


def outcomes(r, k):
    am, bm = eq(r["A"], k["authored_A"]), eq(r["B"], k["authored_B"])
    cm_a, cm_b = eq(r["A"], k["codex_A"]), eq(r["B"], k["codex_B"])
    amb = None if r["bare"] is None else r["bare"] == "yes"
    mp = None if r["only"] is None else r["only"] == "yes"
    return {"authored_match_A": am, "authored_match_B": bm, "codex_match_A": cm_a, "codex_match_B": cm_b,
            "both_authored": and3(am, bm), "both_codex": and3(cm_a, cm_b),
            "ambiguity_confirmed": amb, "minimal_pair": mp, "family_passes": and3(am, bm, amb, mp)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "wc_source_check_key.csv"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "wc_source_check"))
    a = ap.parse_args()
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_wc" / "*.csv")))
    key = {r["item_id"]: r for r in read_csv(a.key)}
    if not paths:
        print("no return CSVs found (annotation/returns_wc/*.csv)", file=sys.stderr)
        return 1
    ratings, problems = load_returns(paths, key)
    annots = sorted({r["annotator"] for r in ratings.values()})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for r in ratings.values():
        r.update(outcomes(r, key[r["item_id"]]))
    by_item = defaultdict(list)
    for r in ratings.values():
        by_item[r["item_id"]].append(r)

    item_rows = []
    for iid, k in key.items():
        rs = by_item.get(iid, [])
        row = {**k, "n_ratings": len(rs)}
        for e in FAM_ENDPOINTS + ["authored_match_A", "authored_match_B", "codex_match_A", "codex_match_B"]:
            row["cons_" + e] = consensus([r[e] for r in rs])
        row["cons_bare"] = consensus([r["bare"] for r in rs])
        for an in annots:
            m = next((r for r in rs if r["annotator"] == an), None)
            for f in ("A", "B", "bare", "only", "note", "time_ms"):
                row[f"{an}_{f}"] = m[f] if m else None
        item_rows.append(row)
    rated = [r for r in item_rows if r["n_ratings"]]

    def src_vals(rows, e, prefix="cons_"):
        return [r[prefix + e + "_A"] for r in rows] + [r[prefix + e + "_B"] for r in rows]

    S = {"returns": paths, "annotators": annots, "problems": problems, "n_families_key": len(key),
         "n_families_rated": len(rated), "consensus": {}, "by_dimension": {}, "per_annotator": {},
         "pooled_ratings": {}, "reference_no_humans": {}, "agreement": {}}
    S["consensus"] = {e: rate([r["cons_" + e] for r in rated]) for e in FAM_ENDPOINTS}
    S["consensus"].update({e: rate(src_vals(rated, e)) for e in SRC_ENDPOINTS})
    S["consensus"]["bare_answer_counts"] = dict(Counter(r["cons_bare"] or "unknown" for r in rated))
    for d in STRATA:
        rows = [r for r in rated if r["dimension"] == d]
        S["by_dimension"][d] = {e: rate([r["cons_" + e] for r in rows]) for e in FAM_ENDPOINTS}
        S["by_dimension"][d].update({e: rate(src_vals(rows, e)) for e in SRC_ENDPOINTS})
    for an in annots:
        rr = [r for r in ratings.values() if r["annotator"] == an]
        x = {e: rate([r[e] for r in rr]) for e in FAM_ENDPOINTS}
        x.update({e: rate([r[e + "_A"] for r in rr] + [r[e + "_B"] for r in rr]) for e in SRC_ENDPOINTS})
        x["bare_answer_counts"] = dict(Counter(r["bare"] or "unknown" for r in rr))
        t = sorted(r["time_ms"] for r in rr if r["time_ms"])
        x["median_time_s"] = t[len(t) // 2] / 1000 if t else None
        x["total_time_min"] = round(sum(t) / 60000, 1) if t else None
        S["per_annotator"][an] = x
    allr = list(ratings.values())
    S["pooled_ratings"] = {e: rate([r[e] for r in allr]) for e in FAM_ENDPOINTS}
    S["pooled_ratings"].update({e: rate([r[e + "_A"] for r in allr] + [r[e + "_B"] for r in allr]) for e in SRC_ENDPOINTS})
    ks = list(key.values())
    S["reference_no_humans"] = {
        "authored_vs_codex_source": rate([eq(k["authored_A"], k["codex_A"]) for k in ks] + [eq(k["authored_B"], k["codex_B"]) for k in ks]),
        "codex_bare_supports_both_family": rate([None if not (k["codex_bare_supports_both_A"] and k["codex_bare_supports_both_B"])
                                                 else (k["codex_bare_supports_both_A"] == "yes" and k["codex_bare_supports_both_B"] == "yes") for k in ks]),
    }
    # human consensus ambiguity vs codex verifier's bare_supports_both (both variants yes)
    pairs = [(r["cons_ambiguity_confirmed"], r["codex_bare_supports_both_A"] == "yes" and r["codex_bare_supports_both_B"] == "yes")
             for r in rated if r["cons_ambiguity_confirmed"] is not None]
    S["ambiguity_human_vs_codex"] = rate([h == c for h, c in pairs])

    fields = {"value": lambda r: [("A", r["A"]), ("B", r["B"])], "bare": lambda r: [("", r["bare"])],
              "only": lambda r: [("", r["only"])]}
    for name, f in fields.items():
        pw = []
        for x, y in combinations(annots, 2):
            common = []
            for i in key:
                if (x, i) in ratings and (y, i) in ratings:
                    for (s, u), (_, v) in zip(f(ratings[(x, i)]), f(ratings[(y, i)])):
                        if u is not None and v is not None:
                            common.append((u, v))
            pw.append({"pair": f"{x}-{y}", "n": len(common),
                       "agree": round(sum(u == v for u, v in common) / len(common), 3) if common else None,
                       "kappa": cohen_kappa([u for u, _ in common], [v for _, v in common]) if common else None})
        cats = sorted({v for r in ratings.values() for _, v in f(r) if v is not None})
        idx = {c: i for i, c in enumerate(cats)}
        units = []
        for i in key:
            for s in ([0, 1] if name == "value" else [0]):
                u = [idx[f(r)[s][1]] for r in by_item[i] if f(r)[s][1] is not None]
                if len(u) >= 2:
                    units.append(u)
        S["agreement"][name] = {"pairwise": pw, "units_with_2plus": len(units),
                                "krippendorff_alpha_nominal": alpha_nominal(units, len(cats)) if units and len(cats) > 1 else None}

    with open(out / "items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(item_rows[0].keys())); w.writeheader(); w.writerows(item_rows)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    L = ["# Part 5 W-C source check: human ratings\n",
         f"Generated by `src/score_wc_source_check.py`. Returns: {len(paths)} file(s); annotators: {', '.join(annots)}; "
         f"families rated: {len(rated)}/{len(key)} (frozen hash-ordered sample, `annotation/wc_source_check_sample.json`).\n",
         "Item consensus = strict majority of known answers; ties/unsure are unknown, excluded from n and reported. "
         "Wilson 95% CIs. A 20-family spot-check of 238 analysed families: sample rates, not certified item validity. "
         "Report the actual completed denominators.\n",
         "| endpoint (consensus) | all | polarity | speech act | politeness |", "|---|---|---|---|---|"]
    for e in SRC_ENDPOINTS + FAM_ENDPOINTS:
        L.append(f"| {e}{' (sources)' if e in SRC_ENDPOINTS else ''} | {fmt(S['consensus'][e])} | "
                 + " | ".join(fmt(S["by_dimension"][d][e]) for d in STRATA) + " |")
    L += [f"\nKeywords-fit consensus answers: {S['consensus']['bare_answer_counts']}.",
          f"Human ambiguity consensus agrees with the codex verifier's bare_supports_both (both variants): {fmt(S['ambiguity_human_vs_codex'])}.",
          f"Reference without humans, same sample: authored vs codex source values {fmt(S['reference_no_humans']['authored_vs_codex_source'])}; "
          f"codex bare_supports_both {fmt(S['reference_no_humans']['codex_bare_supports_both_family'])}.\n",
          "## Per annotator\n", "| annotator | authored match (sources) | codex match (sources) | both authored | ambiguity confirmed | minimal pair | family passes | median s / total min |",
          "|---|---|---|---|---|---|---|---|"]
    for an, x in S["per_annotator"].items():
        L.append(f"| {an} | {fmt(x['authored_match'])} | {fmt(x['codex_match'])} | {fmt(x['both_authored'])} | {fmt(x['ambiguity_confirmed'])} | "
                 f"{fmt(x['minimal_pair'])} | {fmt(x['family_passes'])} | {x['median_time_s']} / {x['total_time_min']} |")
    L += ["\nPooled ratings (not independent): " + "; ".join(f"{e} {fmt(v)}" for e, v in S["pooled_ratings"].items()) + "\n",
          "## Agreement between annotators\n", "| question | pairwise (n, % agree, Cohen kappa) | Krippendorff alpha (nominal) |", "|---|---|---|"]
    for name, x in S["agreement"].items():
        pw = "; ".join(f"{p['pair']}: n={p['n']}, {'n/a' if p['agree'] is None else f'{100 * p['agree']:.0f}%'}, "
                       f"k={'n/a' if p['kappa'] is None else p['kappa']}" for p in x["pairwise"]) or "single annotator"
        al = x["krippendorff_alpha_nominal"]
        L.append(f"| {name} | {pw} | {'n/a' if al is None else round(al, 3)} |")
    L += ["\n## Families not passing (consensus; all kept)\n", "| item | family | dim | A (authored) | B (authored) | bare | human A / B / fit / only | notes |",
          "|---|---|---|---|---|---|---|---|"]
    for r in sorted(item_rows, key=lambda r: r["family_id"]):
        if r["n_ratings"] and r["cons_family_passes"] is not True:
            hv = "; ".join(f"{an}: {r[f'{an}_A']} / {r[f'{an}_B']} / {r[f'{an}_bare']} / {r[f'{an}_only']}" for an in annots if r.get(f"{an}_A") or r.get(f"{an}_bare"))
            notes = " / ".join(str(r[f"{an}_note"]) for an in annots if r.get(f"{an}_note"))
            L.append(f"| {r['item_id']} | {r['family_id']} | {r['dimension']} | {r['source_A']} ({r['authored_A']}) | "
                     f"{r['source_B']} ({r['authored_B']}) | {r['bare']} | {hv} | {notes.replace('|', '/')} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
