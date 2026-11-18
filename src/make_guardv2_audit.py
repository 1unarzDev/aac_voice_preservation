"""Guard v2 item-matched audit: stimuli, dedup map, balanced assignment, catch items, private key, rater sheets.
Plan: analysis/guard_v2/PLAN.md sections 3, 4, 6.  Builds stimuli only; computes NO audit outcome (no ratings exist).

  python src/make_guardv2_audit.py build                      # key + units + sheets (needs runs/guard_v2/generations.jsonl)
  python src/make_guardv2_audit.py reassign --from P05 --to P21   # spare sheet takes over a dropped rater's units

Private (never in the package): annotation/guardv2_key.csv (item level), annotation/guardv2_units.csv (unit level +
raters + catch answers), annotation/guardv2_sample.json.  Sheets: annotation_package/guardv2/guardv2_<ID>.html.
Seed 20261118; explicit sorts before every draw.  Rater IDs P01..P20, spares P21 P22, SLPs SLP1 SLP2.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_repair_audit as mra  # noqa: E402
import runio  # noqa: E402

SEED = 20261118
RATERS = [f"P{i:02d}" for i in range(1, 21)]
SPARES = ["P21", "P22"]
SLPS = ["SLP1", "SLP2"]
PER_UNIT = 3
OUT_DIR = ROOT / "annotation_package" / "guardv2"
KEY = ROOT / "annotation/guardv2_key.csv"
UNITS = ROOT / "annotation/guardv2_units.csv"
SAMPLE = ROOT / "annotation/guardv2_sample.json"
PLAN = ROOT / "analysis/guard_v2"
ARMS = ("O", "R1", "R2")


def norm(t: str) -> str:
    return re.sub(r"[.!?\s]+$", "", re.sub(r"\s+", " ", t.lower().strip()))


def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def gather():
    frame = {r["output_id"]: r for r in csv.DictReader((PLAN / "frame.csv").open())}
    draw = json.loads((PLAN / "draw.json").read_text())
    g1 = {g["request_key"]: g for g in runio.read_jsonl(ROOT / "runs/guard_wc/generations.jsonl") if g["prompt_id"] == "G1"}
    g2 = {g["base_request_key"]: g for g in runio.read_jsonl(ROOT / "runs/guard_v2/generations.jsonl") if g.get("g2_eligible")}
    items = []
    for oid in draw["ids"]:
        f = frame[oid]
        a, b = g1[f["request_key"]], g2[f["base_request_key"]]
        O = a["attempts"][0]["text"]
        assert a["suggestions"][0] != O
        items.append({**f, "O": O, "R1": a["suggestions"][0], "R2": b["suggestions"][0], "g2_rejected": b.get("g2_rejected"),
                      "g2_accepted": b.get("g2_accepted"), "g1_flags_final": a["flags_final"]})
    return items, draw


def catch_items():
    """8 catch items: 4 planted-bad independent mutants (meaning changed), 4 known-good (control rewrites of the same kind).
    Input shown as typed source = the original sentence. Deterministic: first by sha1 of id within each group."""
    cand = {r["id"]: r for r in runio.read_jsonl(ROOT / "analysis/oracle_indep/candidates.jsonl")}
    key = {r["id"]: r for r in runio.read_jsonl(ROOT / "analysis/oracle_indep/key.private.jsonl")}
    bad_ops = ["neg_fail_to", "neg_refuse_to", "neg_nobody", "role_passive"]
    good_ops = ["ctl_paraphrase", "ctl_contraction"]
    out = []
    for ops, n, kind in ((bad_ops, 1, "bad"), (good_ops, 2, "good")):
        for op in ops:
            ids = sorted((i for i in key if key[i]["op"] == op and norm(cand[i]["mutant"]) != norm(cand[i]["original"])),
                         key=lambda i: sha1("guardv2-catch" + i))
            for i in ids[:n]:
                out.append({"kind": kind, "src_id": i, "op": op, "input_text": "The user typed: " + cand[i]["original"],
                            "text": cand[i]["mutant"]})
    bad = [c for c in out if c["kind"] == "bad"][:4]
    good = [c for c in out if c["kind"] == "good"][:4]
    assert len(bad) == 4 and len(good) == 4, (len(bad), len(good))
    return bad + good


def build_units(items):
    units = {}
    for it in items:
        for arm in ARMS:
            k = (it["input_text"], norm(it[arm]))
            u = units.setdefault(k, {"unit_id": "gv-" + sha1("guardv2-unit" + k[0] + "|" + k[1])[:6], "input_text": k[0],
                                     "text": it[arm], "occ": []})
            u["occ"].append((it["output_id"], arm))
    ul = sorted(units.values(), key=lambda u: u["unit_id"])
    assert len({u["unit_id"] for u in ul}) == len(ul)
    return ul


def assign(units, forbid_groups):
    """3 distinct raters per unit; a rater sees at most one unit of any item (forbid_groups: unit_id -> list of item ids)."""
    for attempt in range(200):
        rng = random.Random(f"{SEED}|assign|{attempt}")
        order = sorted(units, key=lambda u: u["unit_id"])
        rng.shuffle(order)
        load = Counter({r: 0 for r in RATERS})
        item_raters = defaultdict(set)
        res, ok = {}, True
        for u in order:
            bad = set().union(*[item_raters[i] for i in forbid_groups[u["unit_id"]]]) if forbid_groups[u["unit_id"]] else set()
            cands = [r for r in RATERS if r not in bad]
            if len(cands) < PER_UNIT:
                ok = False; break
            cands.sort(key=lambda r: (load[r], rng.random()))
            pick = sorted(cands[:PER_UNIT])
            res[u["unit_id"]] = pick
            for r in pick:
                load[r] += 1
                for i in forbid_groups[u["unit_id"]]:
                    item_raters[i].add(r)
        if ok and max(load.values()) - min(load.values()) <= 2:
            return res, dict(load), attempt
    raise SystemExit("no balanced assignment found")


GUARD_OLD = "function startFor(id) {\n  if (!id) { S = null; return; }\n"
GUARD_NEW = ("function startFor(id) {\n  if (!id) { S = null; return; }\n"
             "  if (id.trim().toUpperCase() !== ASSIGNED) {\n"
             "    S = null; renderProgress();\n"
             "    say(\"This file is for annotator \" + ASSIGNED + \". Ask the study coordinator for your own file.\");\n"
             "    return;\n  }\n  id = ASSIGNED;\n")


def render_html(rid: str, items: list[dict]) -> str:
    html = (ROOT / "annotation_package" / "repair_audit.html").read_text()
    blob = json.dumps(items, ensure_ascii=False, indent=0).replace("</", "<\\/")
    new, n = re.subn(r"(/\*AUDIT_ITEMS_BEGIN\*/).*?(/\*AUDIT_ITEMS_END\*/)", lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
    assert n == 1
    for old, rep, cnt in (("(Part 4)", "(guard v2 audit)", 2),
                          ('const RUN = "repair_audit_v1";', f'const RUN = "guardv2_{rid}";\nconst ASSIGNED = "{rid}";', 1),
                          ('return "repairaudit:v1:" + id;', 'return "repairaudit:guardv2:" + id;', 1),
                          ('a.download = "repair_audit_" + S.annot', 'a.download = "guardv2_" + S.annot', 1),
                          (GUARD_OLD, GUARD_NEW, 1)):
        assert new.count(old) == cnt, (old, new.count(old))
        new = new.replace(old, rep)
    return new


def sheet_items(rows):
    return [{"item_id": r["unit_id"], "text": r["text"], "input": mra.visible_input(r["input_text"])} for r in rows]


def write_sheet(rid, rows):
    rng = random.Random(f"{SEED}|order|{rid}")
    rows = sorted(rows, key=lambda r: r["unit_id"])
    rng.shuffle(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"guardv2_{rid}.html").write_text(render_html(rid, sheet_items(rows)))
    return len(rows)


def build():
    items, draw = gather()
    units = build_units(items)
    catch = catch_items()
    forbid = {u["unit_id"]: sorted({o for o, _ in u["occ"]}) for u in units}
    res, load, attempt = assign(units, forbid)
    cunits = [{"unit_id": "cq-" + sha1("guardv2-catch-id" + c["src_id"])[:6], **c} for c in catch]
    # key (item level)
    uid = {(u["input_text"], norm(u["text"])): u["unit_id"] for u in units}
    KEY.parent.mkdir(exist_ok=True)
    cols = ["output_id", "model", "family_id", "dimension", "input_text", "O_unit", "R1_unit", "R2_unit", "O_text", "R1_text",
            "R2_text", "R2_equals", "g2_rejected", "g1_flags_final", "slp_subset"]
    slp = set(draw["slp_order"])
    with open(KEY, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for it in sorted(items, key=lambda i: i["output_id"]):
            eq = "O" if norm(it["R2"]) == norm(it["O"]) else "R1" if norm(it["R2"]) == norm(it["R1"]) else "new"
            w.writerow({"output_id": it["output_id"], "model": it["model"], "family_id": it["family_id"], "dimension": it["dimension"],
                        "input_text": it["input_text"], **{f"{a}_unit": uid[(it["input_text"], norm(it[a]))] for a in ARMS},
                        **{f"{a}_text": it[a] for a in ARMS}, "R2_equals": eq,
                        "g2_rejected": "|".join(it["g2_rejected"] or []), "g1_flags_final": "|".join(it["g1_flags_final"]),
                        "slp_subset": int(it["output_id"] in slp)})
    ucols = ["unit_id", "kind", "input_text", "text", "occurrences", "raters", "catch_op", "catch_expect"]
    with open(UNITS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ucols); w.writeheader()
        for u in units:
            w.writerow({"unit_id": u["unit_id"], "kind": "study", "input_text": u["input_text"], "text": u["text"],
                        "occurrences": "|".join(f"{o}:{a}" for o, a in sorted(u["occ"])), "raters": "|".join(res[u["unit_id"]])})
        for c in cunits:
            exp = "usable=yes;meaning=yes" if c["kind"] == "good" else "meaning=no_or_partly"
            w.writerow({"unit_id": c["unit_id"], "kind": "catch_" + c["kind"], "input_text": c["input_text"], "text": c["text"],
                        "raters": "ALL", "catch_op": c["op"], "catch_expect": exp})
    by = defaultdict(list)
    for u in units:
        for r in res[u["unit_id"]]:
            by[r].append(u)
    nrows = {}
    for rid in RATERS:
        nrows[rid] = write_sheet(rid, by[rid] + cunits)
    slp_units = [u for u in units if any(o in slp for o, _ in u["occ"])]
    for rid in SLPS:
        nrows[rid] = write_sheet(rid, slp_units)
    nd = Counter()
    for it in items:
        nd[(it["model"], "R2==O" if norm(it["R2"]) == norm(it["O"]) else "R2==R1" if norm(it["R2"]) == norm(it["R1"]) else "R2 new")] += 1
    summ = {"seed": SEED, "n_items": len(items), "n_unique_study_units": len(units), "ratings_study": sum(len(v) for v in res.values()),
            "per_rater_study_units": load, "assignment_attempt": attempt, "catch_per_rater": len(cunits), "practice_per_rater": 3,
            "sheet_rows": nrows, "slp_items": len(slp), "slp_units": len(slp_units),
            "arm_equalities_by_model": {f"{k[0]}|{k[1]}": v for k, v in sorted(nd.items())},
            "units_shared_by_multiple_items": sum(len({o for o, _ in u['occ']}) > 1 for u in units),
            "spares": SPARES, "note": "stimuli only; no ratings; no outcome computed"}
    SAMPLE.write_text(json.dumps(summ, indent=2) + "\n")
    print(json.dumps(summ, indent=1))


def reassign(frm, to):
    rows = list(csv.DictReader(UNITS.open()))
    mine = [r for r in rows if r["kind"].startswith("catch") or frm in r["raters"].split("|")]
    for r in rows:
        if r["kind"] == "study" and frm in r["raters"].split("|"):
            r["raters"] = "|".join(sorted(set(r["raters"].split("|")) - {frm}) + [to])  # spare takes over
    with open(UNITS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(write_sheet(to, mine), "rows ->", OUT_DIR / f"guardv2_{to}.html")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build")
    r = sp.add_parser("reassign"); r.add_argument("--from", dest="frm", required=True); r.add_argument("--to", required=True)
    a = ap.parse_args()
    build() if a.cmd == "build" else reassign(a.frm, a.to)


if __name__ == "__main__":
    main()
