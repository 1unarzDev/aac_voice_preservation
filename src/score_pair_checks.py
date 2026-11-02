"""B1: score blind checks of human-written pairs (annotation_package/check_pairs.html) and freeze hw.jsonl.

usage: python src/score_pair_checks.py [CSV ...]            (default: annotation/returns_hwcheck/*.csv)
          [--key annotation/written/check_key.csv] [--candidates annotation/written/hw_candidates.jsonl]
          [--exclude P07,P09:P12,... | --exclude-file pairs.txt] [--min-pass 2] [--planned 3]
          [--out analysis/hw_checks] [--items-out data/items/hw.jsonl] [--no-write]
          [--batch hw2]

--batch hw2 (Stage 4, Part 16) switches every default to that batch: returns annotation/returns_hwcheck_hw2/*.csv,
key and candidates annotation/written/hw2/{check_key.csv,hw_candidates.jsonl}, outputs analysis/hw2_checks/ and
data/items/hw2.jsonl. The hw1 outputs are never touched.

Independence: a check is used only if the checker is not the pair's writer (always enforced; such rows
are dropped and listed) and is not excluded. --exclude takes checker IDs (all their checks dropped)
and/or checker:writer pairs (that checker's checks of that writer's pairs dropped, e.g. people who
discussed items). Practice rows are dropped; for a repeated (checker, item) the later export is kept.

A checker PASSES a pair when all three hold: their values for A and B both equal the writer's values,
"Could the bare keywords reasonably mean either sentence?" = yes, and "Do A and B differ ONLY on that
dimension?" = yes. "Can't judge" or a missing answer is not a pass (it is counted as unknown).
Decision per pair (planned 3 checkers):
  keep     n_pass >= --min-pass and n_pass > n_checks / 2
  drop     the pair can no longer reach the keep rule within the planned checks (or n_checks >= planned)
  pending  otherwise (waiting for more checks)
Only `keep` families go to data/items/hw.jsonl (validated with validate_items.validate_family first,
annotated with their check counts). Outputs <out>/items.csv, summary.json, report.md.
Agreement (descriptive): Krippendorff nominal alpha over the checkers' value labels (A and B stacked),
the keywords-fit answer and the differ-only answer; per writer and per dimension pass rates (Wilson CIs).
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from score_gold import alpha_nominal, wilson  # noqa: E402
from validate_items import validate_family  # noqa: E402

BARE = ["yes", "only A", "only B", "neither"]
PRIVATE = ("content_sha", "source_file", "writer_warnings", "validator_warnings", "consent_at", "writer_time_ms")


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rate(vals):
    known = [v for v in vals if v is not None]
    k, n = sum(known), len(known)
    return {"k": k, "n": n, "unknown": len(vals) - n, "p": (k / n) if n else None, "ci": wilson(k, n)}


def fmt(r):
    if not r or not r["n"]:
        return "n/a"
    lo, hi = r["ci"]
    return f"{r['k']}/{r['n']} = {100 * r['p']:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"


def parse_exclude(s: str | None, path: str | None):
    toks = []
    if s:
        toks += [t.strip() for t in s.split(",") if t.strip()]
    if path:
        toks += [l.strip() for l in Path(path).read_text().splitlines() if l.strip() and not l.startswith("#")]
    whole, pairs = set(), set()
    for t in toks:
        if ":" in t:
            c, w = t.split(":", 1); pairs.add((c.strip(), w.strip()))
        else:
            whole.add(t)
    return whole, pairs


def decide(n, n_pass, min_pass, planned):
    if n_pass >= min_pass and n_pass * 2 > n:
        return "keep"
    remaining = max(0, planned - n)
    if n >= planned or n_pass + remaining < min_pass:
        return "drop"
    return "pending"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "annotation" / "written" / "check_key.csv"))
    ap.add_argument("--candidates", default=str(ROOT / "annotation" / "written" / "hw_candidates.jsonl"))
    ap.add_argument("--exclude"); ap.add_argument("--exclude-file")
    ap.add_argument("--min-pass", type=int, default=2)
    ap.add_argument("--planned", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "analysis" / "hw_checks"))
    ap.add_argument("--items-out", default=str(ROOT / "data" / "items" / "hw.jsonl"))
    ap.add_argument("--no-write", action="store_true", help="do not write the items file")
    ap.add_argument("--batch", default=None, help="batch tag (hw2): batch-specific defaults for all paths")
    a = ap.parse_args(argv)
    rdir = "returns_hwcheck"
    if a.batch:
        b = a.batch
        rdir = f"returns_hwcheck_{b}"
        for attr, old, new in (("key", ROOT / "annotation" / "written" / "check_key.csv", ROOT / "annotation" / "written" / b / "check_key.csv"),
                               ("candidates", ROOT / "annotation" / "written" / "hw_candidates.jsonl", ROOT / "annotation" / "written" / b / "hw_candidates.jsonl"),
                               ("out", ROOT / "analysis" / "hw_checks", ROOT / "analysis" / f"{b}_checks"),
                               ("items_out", ROOT / "data" / "items" / "hw.jsonl", ROOT / "data" / "items" / f"{b}.jsonl")):
            if getattr(a, attr) == str(old):
                setattr(a, attr, str(new))
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / rdir / "*.csv")))
    if not paths:
        print(f"no check CSVs found (annotation/{rdir}/*.csv)", file=sys.stderr)
        return 1
    key = {r["item_id"]: r for r in read_csv(a.key)}
    cands = {f["family_id"]: f for f in map(json.loads, Path(a.candidates).open()) if f}
    ex_whole, ex_pairs = parse_exclude(a.exclude, a.exclude_file)
    ratings, problems, dropped = {}, [], Counter()
    for p in paths:
        for r in read_csv(p):
            if r.get("practice") == "1" or r["item_id"].startswith("prac-"):
                continue
            k = key.get(r["item_id"])
            if not k or k["family_id"] not in cands:
                problems.append(f"{Path(p).name}: unknown or withdrawn item {r['item_id']}"); continue
            c, w = r["annotator"].strip(), k["writer_id"]
            if c.upper() == w.upper():
                dropped["own_pair"] += 1; problems.append(f"{Path(p).name}: {c} checked own pair {k['family_id']}; dropped"); continue
            if c in ex_whole or (c, w) in ex_pairs:
                dropped["excluded"] += 1; continue
            fam = cands[k["family_id"]]
            opts = set(fam["critical_options"])
            uns = set(filter(None, (r.get("unsure") or "").split("|")))
            rec = {"checker": c, "item_id": r["item_id"], "family_id": k["family_id"], "writer": w,
                   "dimension": fam["dimension"], "check_id": r.get("check_id", ""),
                   "A": None if "valA" in uns else (r.get("value_A") or None),
                   "B": None if "valB" in uns else (r.get("value_B") or None),
                   "bare": None if "bare" in uns else (r.get("bare_fits") or None),
                   "only": None if "only" in uns else (r.get("differ_only") or None),
                   "note": r.get("note", ""), "time_ms": float(r["time_ms"]) if r.get("time_ms") else None,
                   "exported_at": r.get("exported_at", "")}
            for f, allowed in (("A", opts), ("B", opts), ("bare", set(BARE)), ("only", {"yes", "no"})):
                if rec[f] is not None and rec[f] not in allowed:
                    problems.append(f"{Path(p).name}: {(c, r['item_id'])} {f}={rec[f]!r} invalid; unknown"); rec[f] = None
            kk = (c, r["item_id"])
            if kk in ratings and ratings[kk]["exported_at"] > rec["exported_at"]:
                continue
            ratings[kk] = rec
    for r in ratings.values():
        fam = cands[r["family_id"]]
        wa, wb = fam["variants"]["A"]["critical_value"], fam["variants"]["B"]["critical_value"]
        r["values_ok"] = None if r["A"] is None or r["B"] is None else (r["A"] == wa and r["B"] == wb)
        r["ambiguous_ok"] = None if r["bare"] is None else r["bare"] == "yes"
        r["minimal_ok"] = None if r["only"] is None else r["only"] == "yes"
        r["passes"] = bool(r["values_ok"] and r["ambiguous_ok"] and r["minimal_ok"])
    by_fam = defaultdict(list)
    for r in ratings.values():
        by_fam[r["family_id"]].append(r)
    rows = []
    for fid, fam in sorted(cands.items()):
        rs = sorted(by_fam.get(fid, []), key=lambda r: r["checker"])
        n, n_pass = len(rs), sum(r["passes"] for r in rs)
        rows.append({"family_id": fid, "item_id": next((k for k, v in key.items() if v["family_id"] == fid), ""),
                     "writer_id": fam["writer_id"], "dimension": fam["dimension"], "writer_dimension": fam["writer_dimension"],
                     "n_checks": n, "n_pass": n_pass,
                     "n_values_ok": sum(bool(r["values_ok"]) for r in rs), "n_ambiguous_ok": sum(bool(r["ambiguous_ok"]) for r in rs),
                     "n_minimal_ok": sum(bool(r["minimal_ok"]) for r in rs),
                     "decision": decide(n, n_pass, a.min_pass, a.planned), "checkers": " ".join(r["checker"] for r in rs),
                     "source_A": fam["variants"]["A"]["source"], "source_B": fam["variants"]["B"]["source"], "bare": fam["bare"],
                     "notes": " / ".join(r["note"] for r in rs if r["note"])})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "items.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    dec = Counter(r["decision"] for r in rows)
    allr = list(ratings.values())
    dims = sorted({r["dimension"] for r in rows})
    S = {"returns": [str(p) for p in paths], "n_candidates": len(rows), "n_ratings": len(allr),
         "checkers": sorted({r["checker"] for r in allr}), "dropped": dict(dropped), "decisions": dict(dec),
         "rule": {"min_pass": a.min_pass, "planned": a.planned}, "problems": problems,
         "pooled": {e: rate([r[e] for r in allr]) for e in ("values_ok", "ambiguous_ok", "minimal_ok")},
         "by_dimension": {}, "by_writer": {}, "agreement": {}}
    S["pooled"]["passes"] = rate([r["passes"] for r in allr])
    for d in dims:
        rr = [r for r in allr if r["dimension"] == d]
        fr = [r for r in rows if r["dimension"] == d]
        S["by_dimension"][d] = {"candidates": len(fr), "decisions": dict(Counter(r["decision"] for r in fr)),
                                **{e: rate([r[e] for r in rr]) for e in ("values_ok", "ambiguous_ok", "minimal_ok", "passes")}}
    for wr in sorted({r["writer_id"] for r in rows}):
        fr = [r for r in rows if r["writer_id"] == wr]
        decided = [r for r in fr if r["decision"] != "pending"]
        S["by_writer"][wr] = {"candidates": len(fr), "kept": sum(r["decision"] == "keep" for r in fr),
                              "keep_rate_decided": rate([r["decision"] == "keep" for r in decided])}
    for name, fn in (("value", lambda r: [r["A"], r["B"]]), ("bare", lambda r: [r["bare"]]), ("only", lambda r: [r["only"]])):
        cats = sorted({v for r in allr for v in fn(r) if v is not None})
        idx = {c: i for i, c in enumerate(cats)}
        units = []
        for fid, rs in by_fam.items():
            for s in range(len(fn(rs[0]))):
                u = [idx[fn(r)[s]] for r in rs if fn(r)[s] is not None]
                if len(u) >= 2:
                    units.append(u)
        S["agreement"][name] = {"units_with_2plus": len(units),
                                "krippendorff_alpha_nominal": alpha_nominal(units, len(cats)) if units and len(cats) > 1 else None}
    (out / "summary.json").write_text(json.dumps(S, indent=2, default=str) + "\n")
    kept = []
    for r in rows:
        if r["decision"] == "keep":
            fam = {k: v for k, v in cands[r["family_id"]].items() if k not in PRIVATE}
            fam["human_check"] = {"n_checks": r["n_checks"], "n_pass": r["n_pass"], "rule": f">={a.min_pass} of {a.planned}"}
            errs, warns = [], []
            validate_family(fam, "hw", errs, warns)
            if errs:
                problems.append(f"{r['family_id']}: validator errors {errs}; not written"); continue
            kept.append(fam)
    L = ["# B1 human-written pairs: blind checks\n",
         f"Generated by `src/score_pair_checks.py`. {len(paths)} return file(s), {len(allr)} independent checks by "
         f"{len(S['checkers'])} checkers on {len(rows)} candidate pairs. Dropped: {dict(dropped) or 'none'}.\n",
         f"Rule: keep a pair when >= {a.min_pass} of its (planned {a.planned}) independent checkers agree with both writer "
         "values, say the keywords could mean either sentence, and judge the pair minimal.\n",
         f"Decisions: keep {dec['keep']}, drop {dec['drop']}, pending {dec['pending']}.\n",
         "| dimension | candidates | keep / drop / pending | values agree (checks) | keywords fit both | minimal | full pass |",
         "|---|---|---|---|---|---|---|"]
    for d in dims:
        x = S["by_dimension"][d]; dd = x["decisions"]
        L.append(f"| {d} | {x['candidates']} | {dd.get('keep', 0)} / {dd.get('drop', 0)} / {dd.get('pending', 0)} | "
                 f"{fmt(x['values_ok'])} | {fmt(x['ambiguous_ok'])} | {fmt(x['minimal_ok'])} | {fmt(x['passes'])} |")
    L += ["\n## Agreement between checkers\n"] + [
        f"- {k}: alpha = {'n/a' if v['krippendorff_alpha_nominal'] is None else round(v['krippendorff_alpha_nominal'], 3)} "
        f"({v['units_with_2plus']} units with 2+ checks)" for k, v in S["agreement"].items()]
    L += ["\n## Per writer\n", "| writer | candidates | kept | keep rate (decided) |", "|---|---|---|---|"]
    for wr, x in S["by_writer"].items():
        L.append(f"| {wr} | {x['candidates']} | {x['kept']} | {fmt(x['keep_rate_decided'])} |")
    if problems:
        L += ["\n## Problems\n"] + [f"- {p}" for p in problems[:200]]
    if not a.no_write:
        if kept:
            Path(a.items_out).parent.mkdir(parents=True, exist_ok=True)
            with open(a.items_out, "w", encoding="utf-8") as f:
                for fam in kept:
                    f.write(json.dumps(fam, ensure_ascii=False) + "\n")
            L.append(f"\nWrote {len(kept)} kept families to `{Path(a.items_out).name}`.")
        else:
            L.append("\nNo family is kept yet; items file not written.")
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
