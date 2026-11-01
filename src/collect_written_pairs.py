"""B1: turn returned writer CSVs (annotation_package/write_pairs.html) into candidate hw families.

usage: python src/collect_written_pairs.py [CSV ...]          (default: annotation/returns_written/*.csv)
          [--out-dir annotation/written] [--assignment annotation/written/writer_assignment.csv]
          [--target-per-dim 150] [--no-batches] [--checkers P01,P02,... | --checkers-file ids.txt]

Per returned pair row (row_type == pair):
  * keep the latest export of each (writer, dimension, pair_no);
  * require consent == yes (CC BY 4.0 release), or the writer listed in <out>/consent_confirmed.csv, else reject;
  * re-run the writer-tool checks in Python (src/hw_rules.check_pair, the same rules as the page);
  * reject exact duplicates of an earlier pair (same two sentences, either order, any writer);
  * build the family in the project schema: split hw, family_id hw-<pol|act|plt|cer|agt|tim>-NNN,
    construction handwritten, cluster_id = writer_id, noncritical = first shared extra word,
    chips / all_chips derived by rule (hw_rules.derive_chips, s1_cues detector, r2 conventions);
  * run validate_items.validate_family on it; any ERROR rejects the pair.
Family ids are stable across re-runs: a (writer, dimension, pair_no, content) seen before keeps its id;
a pair edited after an earlier collection gets a new id (it must be re-checked).

Writes (private: these carry the writers' values, never hand them to checkers):
  <out>/hw_candidates.jsonl   accepted candidate families (NOT data/items: only score_pair_checks.py
                              writes data/items/hw.jsonl, after the blind checks)
  <out>/rejected.csv          every rejected row with reasons
  <out>/quota_report.md/.csv  per dimension x writer: assigned / returned / accepted / rejected, and per
                              dimension against --target-per-dim (kept after checks when
                              analysis/hw_checks/items.csv exists)
and then (unless --no-batches) calls src/make_check_batches.py to batch new candidates into blind check
files of 30 and, with --checkers, extend the 3-checkers-per-pair assignment sheet.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import hw_rules as H  # noqa: E402
from validate_items import validate_family  # noqa: E402

DEFAULT_OUT = ROOT / "annotation" / "written"


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def canon_value(dim: str, v: str) -> str:
    v = (v or "").strip()
    v = H.VALUE_ALIASES.get(v, v)
    return v if v in H.DIMS[dim]["values"] else ""


def content_sha(r: dict) -> str:
    blob = json.dumps([r["sentence_A"].strip(), r["value_A"], r["sentence_B"].strip(), r["value_B"],
                       r["keywords"].strip().lower(), (r.get("situation") or "").strip()], ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def load_rows(paths):
    """Latest export per (writer, dim, pair_no); returns rows and problems."""
    best, problems = {}, []
    for p in paths:
        for r in read_csv(p):
            if r.get("row_type") != "pair":
                continue
            dim = (r.get("dimension") or "").strip()
            if dim not in H.DIMS:
                problems.append(f"{p}: unknown dimension {dim!r}"); continue
            r["_file"] = str(Path(p).name)
            r["writer"] = (r.get("writer") or "").strip()
            k = (r["writer"], dim, int(r["pair_no"]))
            if k in best and best[k].get("exported_at", "") > r.get("exported_at", ""):
                continue
            best[k] = r
    return [best[k] for k in sorted(best)], problems


def load_detector():
    import s1_cues
    nlp = s1_cues.load_nlp()
    lex = s1_cues.Lexicon(nlp)
    return lambda s: s1_cues.detect_doc(nlp(s), lex)


def build_family(r, dim, fid, det):
    spec = H.DIMS[dim]
    va, vb = canon_value(dim, r["value_A"]), canon_value(dim, r["value_B"])
    chk = H.check_pair({"A": r["sentence_A"], "B": r["sentence_B"], "valA": va, "valB": vb,
                        "keywords": r["keywords"], "situation": r.get("situation", "")}, dim)
    if not chk["ok"]:
        return None, [m for _, m in chk["problems"]]
    A = {"source": r["sentence_A"].strip(), "critical_value": va}
    B = {"source": r["sentence_B"].strip(), "critical_value": vb}
    chips, notes = H.derive_chips(dim, A, B, det)
    for k, v in (("A", A), ("B", B)):
        v.update(chips[k])
    sit = (r.get("situation") or "").strip() or None
    fam = {"family_id": fid, "dimension": spec["family_dim"], "split": "hw", "context": sit,
           "variants": {"A": A, "B": B}, "bare": " ".join(chk["keywords"]), "noncritical": chk["extra"][0],
           "critical_options": spec["options"],
           "notes": f"Human-written (B1) by writer {r['writer']}, topic {r.get('topic') or 'n/a'}."
                    + (" Chip notes: " + "; ".join(notes) + "." if notes else ""),
           "construction": "handwritten", "cluster_id": r["writer"], "writer_id": r["writer"],
           "writer_dimension": dim, "writer_pair_no": int(r["pair_no"]), "topic": r.get("topic") or None,
           "topic_suggested": r.get("topic_suggested") or None, "license": "CC BY 4.0",
           "consent_at": r.get("consent_at") or None,
           "writer_time_ms": int(float(r["time_ms"])) if r.get("time_ms") else None,
           "writer_warnings": [m for _, m in chk["warnings"]], "content_sha": content_sha(r),
           "source_file": r["_file"]}
    errs, warns = [], []
    validate_family(fam, "hw", errs, warns)
    if errs:
        return None, ["validator: " + e.split(": ", 1)[-1] for e in errs]
    fam["validator_warnings"] = [w.split(": ", 1)[-1] for w in warns]
    return fam, []


def quota_report(out: Path, rows, accepted, rejected, assignment, target, kept):
    assigned = defaultdict(int)
    for a in assignment:
        assigned[(a["dimension"], a["writer_id"])] += int(a.get("n_pairs") or 15)
    returned = Counter((r["dimension"], r["writer"]) for r in rows)
    acc = Counter((f["writer_dimension"], f["writer_id"]) for f in accepted)
    rej = Counter((r["dimension"], r["writer"]) for r in rejected)
    kept_c = Counter((k["writer_dimension"], k["writer_id"]) for k in kept)
    keys = sorted(set(assigned) | set(returned))
    recs = [{"dimension": d, "writer_id": w, "assigned": assigned.get((d, w), ""), "returned": returned[(d, w)],
             "accepted": acc[(d, w)], "rejected": rej[(d, w)], "kept_after_checks": kept_c[(d, w)] if kept else ""}
            for d, w in keys]
    with open(out / "quota_report.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(recs[0]) if recs else ["dimension"]); wr.writeheader(); wr.writerows(recs)
    L = ["# B1 written pairs: quota report\n", f"Target per dimension: {target} usable families. "
         "Accepted = passed the format checks and validator (candidates for blind checking); "
         "kept = passed >= 2 of 3 independent checks (src/score_pair_checks.py).\n",
         "| dimension | writers assigned | pairs assigned | returned | accepted | rejected | kept | target | still needed (vs kept, else accepted) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for d in H.DIMS:
        ws = {w for (dd, w) in keys if dd == d}
        n_as = sum(v for (dd, _), v in assigned.items() if dd == d)
        n_ret = sum(v for (dd, _), v in returned.items() if dd == d)
        n_acc = sum(v for (dd, _), v in acc.items() if dd == d)
        n_rej = sum(v for (dd, _), v in rej.items() if dd == d)
        n_keep = sum(v for (dd, _), v in kept_c.items() if dd == d)
        base = n_keep if kept else n_acc
        L.append(f"| {d} | {len(ws)} | {n_as} | {n_ret} | {n_acc} | {n_rej} | {n_keep if kept else 'n/a'} | {target} | {max(0, target - base)} |")
    L += ["\n## Per writer\n", "| dimension | writer | assigned | returned | accepted | rejected | kept |", "|---|---|---|---|---|---|---|"]
    for x in recs:
        L.append(f"| {x['dimension']} | {x['writer_id']} | {x['assigned']} | {x['returned']} | {x['accepted']} | {x['rejected']} | {x['kept_after_checks']} |")
    (out / "quota_report.md").write_text("\n".join(L) + "\n")
    return "\n".join(L[:4 + len(H.DIMS)])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="*")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--assignment", default=None, help="writer assignment sheet (default <out>/writer_assignment.csv)")
    ap.add_argument("--target-per-dim", type=int, default=150)
    ap.add_argument("--kept", default=str(ROOT / "analysis" / "hw_checks" / "items.csv"))
    ap.add_argument("--no-batches", action="store_true")
    ap.add_argument("--checkers"); ap.add_argument("--checkers-file")
    a = ap.parse_args(argv)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    paths = a.csv or sorted(glob.glob(str(ROOT / "annotation" / "returns_written" / "*.csv")))
    if not paths:
        print("no writer CSVs found (annotation/returns_written/*.csv)", file=sys.stderr)
        return 1
    rows, problems = load_rows(paths)
    cand_path = out / "hw_candidates.jsonl"
    prev = [json.loads(l) for l in cand_path.open()] if cand_path.exists() else []
    id_of = {(f["writer_id"], f["writer_dimension"], f["writer_pair_no"], f["content_sha"]): f["family_id"] for f in prev}
    used = {f["family_id"] for f in prev}
    next_n = Counter()
    for fid in used:
        code, n = fid.split("-")[1], int(fid.split("-")[2])
        next_n[code] = max(next_n[code], n)
    det = load_detector()
    # Coordinator-confirmed consent (writers whose consent column was lost in format conversion; see the file's note)
    cpath = out / "consent_confirmed.csv"
    confirmed = {r["writer"].strip() for r in csv.DictReader(cpath.open())} if cpath.exists() else set()
    accepted, rejected, seen = [], [], {}
    for r in rows:
        dim = r["dimension"]
        why = []
        if (r.get("consent") or "").strip().lower() != "yes" and r["writer"].strip() not in confirmed:
            why.append("no CC BY 4.0 consent")
        pair = tuple(sorted([" ".join(H.toks(r["sentence_A"])), " ".join(H.toks(r["sentence_B"]))]))
        if pair in seen:
            why.append(f"duplicate of {seen[pair]}")
        if why:
            rejected.append({**r, "reasons": "; ".join(why)}); continue
        key = (r["writer"], dim, int(r["pair_no"]), content_sha(r))
        code = H.DIMS[dim]["code"]
        fid = id_of.get(key)
        if fid is None:
            next_n[code] += 1
            fid = f"hw-{code}-{next_n[code]:03d}"
        fam, why = build_family(r, dim, fid, det)
        if fam is None:
            if key not in id_of:
                next_n[code] -= 1          # do not burn an id on a rejected pair
            rejected.append({**r, "reasons": "; ".join(why)}); continue
        seen[pair] = fid
        accepted.append(fam)
    accepted.sort(key=lambda f: f["family_id"])
    with cand_path.open("w", encoding="utf-8") as f:
        for fam in accepted:
            f.write(json.dumps(fam, ensure_ascii=False) + "\n")
    head = ["writer", "dimension", "pair_no", "sentence_A", "value_A", "sentence_B", "value_B", "keywords", "reasons", "_file"]
    with open(out / "rejected.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=head, extrasaction="ignore"); wr.writeheader(); wr.writerows(rejected)
    asg_path = Path(a.assignment) if a.assignment else out / "writer_assignment.csv"
    assignment = read_csv(asg_path) if asg_path.exists() else []
    kept = []
    if Path(a.kept).exists():
        by = {f["family_id"]: f for f in accepted}
        kept = [by[k["family_id"]] for k in read_csv(a.kept) if k.get("decision") == "keep" and k["family_id"] in by]
    summary = quota_report(out, rows, accepted, rejected, assignment, a.target_per_dim, kept)
    print(f"{len(paths)} file(s), {len(rows)} pair rows -> {len(accepted)} candidates, {len(rejected)} rejected -> {cand_path}")
    for p in problems:
        print("problem:", p)
    print(summary)
    dropped_ids = sorted(used - {f["family_id"] for f in accepted})
    if dropped_ids:
        print(f"note: {len(dropped_ids)} earlier candidate id(s) no longer present (edited or withdrawn): {dropped_ids[:10]}")
    if not a.no_batches:
        import make_check_batches
        args = ["--candidates", str(cand_path), "--out-dir", str(out)]
        if a.checkers:
            args += ["--checkers", a.checkers]
        if a.checkers_file:
            args += ["--checkers-file", a.checkers_file]
        make_check_batches.main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
