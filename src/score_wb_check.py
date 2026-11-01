"""Score Part 6 W-B corpus-check returns (annotation_package/wb_corpus_check.html CSVs).

usage: python src/score_wb_check.py [CSV ...]                (default: annotation/returns_wb/*.csv)
          [--key annotation/wb_check_key.csv] [--out analysis/wb_check]

Cells = (message, dimension): 20 messages x 5 dimensions. Pass 1 (keywords only) gives a set
of plausible values; the human calls a cell ambiguous when >=2 values are ticked (the panel's
own definition: a coder lists >=2 values). Pass 2 (full message) gives the source value.
Endpoints, Wilson 95% CIs (cells are clustered in messages, so the CIs are optimistic; the
per-message counts are also reported):
  ambiguity confirmation (primary)  P(human ambiguous | panel status confirmed_ambiguous)
  ambiguity confirmation (strict)   P(human ambiguous | strict likely-only status confirmed_ambiguous)
  supplied confirmation             P(human ticks exactly the panel source value | panel status supplied)
  human-ambiguous rate              P(human ambiguous) over all cells, by sample (random / enriched)
  source agreement                  human Pass 2 value == panel consensus source value (coders agree)
                                    and == each coder's source value
  source admissible (blind)         human's own Pass 2 value is among the values the same human
                                    ticked in Pass 1 (was the true reading anticipated?)
  ambiguity agreement               % agreement and Cohen's kappa, human ambiguous vs each coder's
                                    primary (values_k) and strict (values_likely_k) ambiguity
Human status mirrors the panel: ambiguous (>=2), supplied (exactly the Pass 2 value), or
unambiguous_wrong; agreement with the panel's primary and strict status is tabulated.
Units: per annotator; item consensus (strict majority of known answers; ties and unsure are
unknown); pooled ratings (descriptive). Random and enriched messages are also shown separately
(W-B rule: never pool their prevalence estimates; the audit sample mixes them).
Inter-annotator: pairwise Cohen's kappa / % agreement and Krippendorff's nominal alpha on
ambiguous yes/no and Pass 2 value.
Outputs: <out>/report.md, <out>/cells.csv, <out>/summary.json.
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

DIMS = ["polarity", "speech_act", "agent", "certainty", "politeness"]
SAMPLES = ["random", "enriched"]


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "unknown": len(vals) - n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def consensus(vals):
    known = [v for v in vals if v is not None]
    if not known:
        return None
    top, cnt = Counter(known).most_common(1)[0]
    return top if cnt * 2 > len(known) else None


def fmt(r):
    if not r or not r["n"]:
        return "n/a (0 known)"
    lo, hi = r["ci"]
    s = f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"
    return s + (f"; {r['unknown']} unknown" if r["unknown"] else "")


def agree(pairs):
    pairs = [(u, v) for u, v in pairs if u is not None and v is not None]
    if not pairs:
        return {"n": 0, "agree": None, "kappa": None}
    return {"n": len(pairs), "agree": round(sum(u == v for u, v in pairs) / len(pairs), 3),
            "kappa": cohen_kappa([u for u, _ in pairs], [v for _, v in pairs])}


def split(s):
    return [x for x in (s or "").split("|") if x]


def load_returns(paths, key, options):
    ratings, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac"):
                continue
            ck = (r["item_id"], r["dimension"])
            if ck not in key:
                problems.append(f"{p}: unknown cell {ck}"); continue
            a = r["annotator"].strip()
            if (a, *ck) in ratings:
                problems.append(f"{p}: duplicate rating {(a, *ck)}; keeping the later export")
            opts = set(options[r["dimension"]])
            p1 = None if r.get("p1_unsure") == "1" else split(r.get("p1_plausible"))
            if p1 is not None and not p1:
                p1 = None
            if p1 and not set(p1) <= opts:
                problems.append(f"{p}: {(a, *ck)} p1 {p1} has invalid values; treated as unknown"); p1 = None
            p2 = None if r.get("p2_unsure") == "1" else (r.get("p2_value") or None)
            if p2 is not None and p2 not in opts:
                problems.append(f"{p}: {(a, *ck)} p2={p2!r} invalid; treated as unknown"); p2 = None
            ratings[(a, *ck)] = {"annotator": a, "item_id": ck[0], "dimension": ck[1], "p1": p1, "p2": p2,
                                 "p1_note": r.get("p1_note", ""), "p2_note": r.get("p2_note", ""),
                                 "p1_time_ms": float(r["p1_time_ms"]) if r.get("p1_time_ms") else None,
                                 "p2_time_ms": float(r["p2_time_ms"]) if r.get("p2_time_ms") else None}
    return ratings, problems


def outcomes(r, k):
    p1, p2 = r["p1"], r["p2"]
    amb = None if p1 is None else len(p1) >= 2
    if p1 is None:
        status = None
    elif len(p1) >= 2:
        status = "ambiguous"
    elif p2 is None:
        status = None
    else:
        status = "supplied" if p1 == [p2] else "unambiguous_wrong"
    src = k["source_value"] or None
    v1, v2, l1, l2 = split(k["values_1"]), split(k["values_2"]), split(k["values_likely_1"]), split(k["values_likely_2"])
    return {
        "human_ambiguous": amb, "human_status": status,
        "amb_confirm_primary": amb if k["status"] == "confirmed_ambiguous" else None,
        "amb_confirm_strict": amb if k["status_strict"] == "confirmed_ambiguous" else None,
        "supplied_confirm": (None if p1 is None or not src else p1 == [src]) if k["status"] == "supplied" else None,
        "source_match_consensus": None if p2 is None or not src else p2 == src,
        "source_match_coder1": None if p2 is None else p2 == k["src_1"],
        "source_match_coder2": None if p2 is None else p2 == k["src_2"],
        "source_admissible_blind": None if p1 is None or p2 is None else p2 in p1,
        "panel_source_in_human_set": None if p1 is None or not src else src in p1,
        "_c1_amb": len(v1) >= 2, "_c2_amb": len(v2) >= 2, "_c1_amb_strict": len(l1) >= 2, "_c2_amb_strict": len(l2) >= 2,
    }


ELIGIBLE = {  # conditional endpoints: only these cells enter the denominator (others are n/a, not unknown)
    "amb_confirm_primary": lambda k: k["status"] == "confirmed_ambiguous",
    "amb_confirm_strict": lambda k: k["status_strict"] == "confirmed_ambiguous",
    "supplied_confirm": lambda k: k["status"] == "supplied" and bool(k["source_value"]),
    "source_match_consensus": lambda k: bool(k["source_value"]),
    "panel_source_in_human_set": lambda k: bool(k["source_value"]),
}


def elig(e, k):
    return ELIGIBLE.get(e, lambda _: True)(k)


RATE_ENDPOINTS = ["amb_confirm_primary", "amb_confirm_strict", "supplied_confirm", "human_ambiguous",
                  "source_match_consensus", "source_match_coder1", "source_match_coder2",
                  "source_admissible_blind", "panel_source_in_human_set"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "wb_check_key.csv"))
    ap.add_argument("--audit", default=str(ROOT / "annotation" / "wb_audit.json"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "wb_check"))
    a = ap.parse_args()
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_wb" / "*.csv")))
    key = {(r["item_id"], r["dimension"]): r for r in read_csv(a.key)}
    options = json.loads(Path(a.audit).read_text())["options"]
    if not paths:
        print("no return CSVs found (annotation/returns_wb/*.csv)", file=sys.stderr)
        return 1
    ratings, problems = load_returns(paths, key, options)
    annots = sorted({r["annotator"] for r in ratings.values()})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for r in ratings.values():
        r.update(outcomes(r, key[(r["item_id"], r["dimension"])]))
    by_cell = defaultdict(list)
    for r in ratings.values():
        by_cell[(r["item_id"], r["dimension"])].append(r)

    cells = []
    for ck, k in key.items():
        rs = by_cell.get(ck, [])
        row = {**k, "n_ratings": len(rs)}
        for e in RATE_ENDPOINTS + ["human_status"]:
            row["cons_" + e] = consensus([r[e] for r in rs])
        row["cons_p2"] = consensus([r["p2"] for r in rs])
        for an in annots:
            m = next((r for r in rs if r["annotator"] == an), None)
            row[f"{an}_p1"] = "|".join(m["p1"]) if m and m["p1"] else ""
            row[f"{an}_p2"] = m["p2"] if m else ""
            row[f"{an}_notes"] = " / ".join(x for x in ((m or {}).get("p1_note"), (m or {}).get("p2_note")) if x)
        cells.append(row)
    rated = [c for c in cells if c["n_ratings"]]

    def block(rows):
        return {e: rate([c["cons_" + e] for c in rows if elig(e, c)]) for e in RATE_ENDPOINTS}

    S = {"returns": paths, "annotators": annots, "problems": problems, "cells_key": len(key), "cells_rated": len(rated),
         "messages_rated": len({c["item_id"] for c in rated}),
         "sample_mix": dict(Counter(k["sample"] for k in key.values() if k["dimension"] == "polarity")),
         "consensus": block(rated), "by_sample": {s: block([c for c in rated if c["sample"] == s]) for s in SAMPLES},
         "by_dimension": {d: block([c for c in rated if c["dimension"] == d]) for d in DIMS},
         "status_crosstab_primary": {}, "status_crosstab_strict": {}, "per_annotator": {}, "agreement": {}}
    for c in rated:
        h = c["cons_human_status"] or "unknown"
        S["status_crosstab_primary"].setdefault(c["status"], Counter())[h] += 1
        S["status_crosstab_strict"].setdefault(c["status_strict"] or "n/a", Counter())[h] += 1
    # messages with >=1 primary-confirmed-ambiguous cell that humans also call ambiguous (cluster view)
    per_msg = defaultdict(list)
    for c in rated:
        if c["cons_amb_confirm_primary"] is not None:
            per_msg[c["item_id"]].append(c["cons_amb_confirm_primary"])
    S["messages_all_primary_amb_confirmed"] = rate([all(v) for v in per_msg.values()])
    for an in annots:
        rr = [r for r in ratings.values() if r["annotator"] == an]
        x = {e: rate([r[e] for r in rr if elig(e, key[(r["item_id"], r["dimension"])])]) for e in RATE_ENDPOINTS}
        for coder in ("_c1_amb", "_c2_amb", "_c1_amb_strict", "_c2_amb_strict"):
            x["ambiguity_vs" + coder] = agree([(r["human_ambiguous"], r[coder]) for r in rr])
        for t in ("p1_time_ms", "p2_time_ms"):
            # one time per message: take it from the polarity row
            ts = sorted(r[t] for r in rr if r[t] and r["dimension"] == "polarity")
            x[t.replace("_ms", "_total_min")] = round(sum(ts) / 60000, 1) if ts else None
        S["per_annotator"][an] = x
    S["pooled_ratings"] = {e: rate([r[e] for r in ratings.values() if elig(e, key[(r["item_id"], r["dimension"])])])
                           for e in RATE_ENDPOINTS}
    for name, f in {"human_ambiguous": lambda r: r["human_ambiguous"], "p2_value": lambda r: r["p2"]}.items():
        pw = []
        for x, y in combinations(annots, 2):
            pw.append({"pair": f"{x}-{y}", **agree([(f(ratings[(x, *ck)]), f(ratings[(y, *ck)])) for ck in key
                                                       if (x, *ck) in ratings and (y, *ck) in ratings])})
        cats = sorted({str(f(r)) for r in ratings.values() if f(r) is not None})
        idx = {c: i for i, c in enumerate(cats)}
        units = [[idx[str(f(r))] for r in by_cell[ck] if f(r) is not None] for ck in key]
        units = [u for u in units if len(u) >= 2]
        S["agreement"][name] = {"pairwise": pw, "units_with_2plus": len(units),
                                "krippendorff_alpha_nominal": alpha_nominal(units, len(cats)) if units and len(cats) > 1 else None}

    with open(out / "cells.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cells[0].keys())); w.writeheader(); w.writerows(cells)
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")

    L = ["# Part 6 W-B corpus check: human audit of the admissibility panel\n",
         f"Generated by `src/score_wb_check.py`. Returns: {len(paths)} file(s); annotators: {', '.join(annots)}; "
         f"cells rated {len(rated)}/{len(key)} ({S['messages_rated']} messages). Audit sample: `annotation/wb_audit.json`, "
         f"drawn from all 160 W-B messages (sample mix {S['sample_mix']}).\n",
         "Consensus = strict majority of known answers. Wilson 95% CIs over cells; cells are clustered in 20 messages, so "
         "the intervals are optimistic. Human ambiguous = >=2 values ticked in Pass 1 (keywords only). The panel is "
         "two codex coders; its labels are not ground truth and neither is this audit.\n",
         "| endpoint (consensus) | all | random | enriched |", "|---|---|---|---|"]
    for e in RATE_ENDPOINTS:
        L.append(f"| {e} | {fmt(S['consensus'][e])} | {fmt(S['by_sample']['random'][e])} | {fmt(S['by_sample']['enriched'][e])} |")
    L += [f"\nMessages whose every primary-confirmed-ambiguous cell is also human-ambiguous: {fmt(S['messages_all_primary_amb_confirmed'])}.\n",
          "## By dimension (consensus)\n", "| dim | amb confirm (primary) | amb confirm (strict) | human ambiguous | source = panel | source admissible (blind) |",
          "|---|---|---|---|---|---|"]
    for d in DIMS:
        x = S["by_dimension"][d]
        L.append(f"| {d} | {fmt(x['amb_confirm_primary'])} | {fmt(x['amb_confirm_strict'])} | {fmt(x['human_ambiguous'])} | "
                 f"{fmt(x['source_match_consensus'])} | {fmt(x['source_admissible_blind'])} |")
    for nm in ("primary", "strict"):
        tab = S[f"status_crosstab_{nm}"]
        hs = sorted({h for v in tab.values() for h in v})
        L += [f"\n## Panel {nm} status x human consensus status\n", "| panel \\ human | " + " | ".join(hs) + " |", "|---" * (len(hs) + 1) + "|"]
        for st, v in sorted(tab.items()):
            L.append(f"| {st} | " + " | ".join(str(v.get(h, 0)) for h in hs) + " |")
    L += ["\n## Per annotator\n", "| annotator | amb confirm primary | amb confirm strict | source = panel | ambiguity vs coder1 / coder2 (primary) | vs coder1 / coder2 (strict) | Pass 1 / Pass 2 min |",
          "|---|---|---|---|---|---|---|"]
    fa = lambda g: f"{'n/a' if g['agree'] is None else f'{100 * g['agree']:.0f}%'} k={g['kappa']}"
    for an, x in S["per_annotator"].items():
        L.append(f"| {an} | {fmt(x['amb_confirm_primary'])} | {fmt(x['amb_confirm_strict'])} | {fmt(x['source_match_consensus'])} | "
                 f"{fa(x['ambiguity_vs_c1_amb'])} / {fa(x['ambiguity_vs_c2_amb'])} | {fa(x['ambiguity_vs_c1_amb_strict'])} / {fa(x['ambiguity_vs_c2_amb_strict'])} | "
                 f"{x['p1_time_total_min']} / {x['p2_time_total_min']} |")
    L += ["\n## Agreement between annotators\n", "| question | pairwise (n, % agree, Cohen kappa) | Krippendorff alpha (nominal) |", "|---|---|---|"]
    for name, x in S["agreement"].items():
        pw = "; ".join(f"{p['pair']}: n={p['n']}, {fa(p)}" for p in x["pairwise"]) or "single annotator"
        al = x["krippendorff_alpha_nominal"]
        L.append(f"| {name} | {pw} | {'n/a' if al is None else round(al, 3)} |")
    L += ["\n## Disagreements with the panel (consensus; all kept)\n", "| item | dim | keywords | message | panel status / strict | panel source | human sets / values | notes |",
          "|---|---|---|---|---|---|---|---|"]
    for c in rated:
        if c["cons_amb_confirm_primary"] is False or c["cons_source_match_consensus"] is False or c["cons_supplied_confirm"] is False:
            hv = "; ".join(f"{an}: {{{c[f'{an}_p1']}}} -> {c[f'{an}_p2']}" for an in annots)
            nt = " / ".join(c[f"{an}_notes"] for an in annots if c[f"{an}_notes"])
            L.append(f"| {c['item_id']} | {c['dimension']} | {c['keywords']} | {c['message']} | {c['status']} / {c['status_strict']} | "
                     f"{c['source_value']} | {hv.replace('|', '/')} | {nt.replace('|', '/')} |")
    if problems:
        L += ["\n## Problems in returns\n"] + [f"- {p}" for p in problems]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
