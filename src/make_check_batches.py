"""B1 coordinator: batch candidate hw families into blind check files and assign 3 checkers per pair.

usage: python src/make_check_batches.py [--candidates annotation/written/hw_candidates.jsonl]
          [--out-dir annotation/written] [--batch-size 30] [--per-pair 3]
          [--checkers P01,P02,... | --checkers-file ids.txt] [--max-load N] [--reassign]

Batches (incremental, frozen once written):
  * only candidates not yet in a batch are batched; existing batches never change, so files already
    sent out stay valid. Batch state: <out>/check_batches.json.
  * each writer's new pairs are cut into chunks of 5 (sha1 order); chunks are dealt greedily to the
    batch with the fewest pairs that has room and does not yet hold that writer, so a batch of 30
    mixes about 6 writers and several dimensions, and excludes as few checkers as possible.
  * blind check item ids: hc-<sha1(salt|family_id)[:8]>.
Files:
  <out>/check_files/<check_id>.json   blind: item_id, dimension, options, context, A, B, bare,
                                      noncritical; plus `exclude` = hashed IDs of the batch's writers
                                      (check_pairs.html refuses to start for them)
  <out>/check_key.csv                 item_id -> family, writer, writer values (private)
Assignment (when checkers are given; balanced incomplete design, greedy):
  each batch gets --per-pair distinct checkers, never a writer of any pair in the batch; checkers are
  picked by lowest current load, then lowest co-assignment count with the checkers already chosen
  for that batch, then a hash tie-break, so loads stay within 1 and checker pairs are spread.
  Existing assignments are kept unless --reassign.
  <out>/check_assignment.csv            check_id, file, n_pairs, dimensions, checker_1..k, writers
  <out>/check_assignment_by_checker.csv checker, n_batches, n_pairs, check_ids
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALT = "hw-check-2026"
CHUNK = 5
TOOL = "check_pairs_v1"
BLIND_FIELDS = ("item_id", "dimension", "options", "context", "A", "B", "bare", "noncritical")


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def id_hash(writer: str) -> str:
    """FNV-1a 32-bit of upper(ID)+'|hwcheck', as idHash() in check_pairs.html (not a secret, just not plain)."""
    h = 2166136261
    for ch in writer.strip().upper() + "|hwcheck":
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"


def item_id(fid: str) -> str:
    return "hc-" + sha(SALT + "|" + fid)[:8]


def batch_new(cands: list[dict], state: dict, size: int) -> list[str]:
    done = {f for b in state["batches"].values() for f in b["items"]}
    new = [c for c in cands if c["family_id"] not in done]
    if not new:
        return []
    by_w = defaultdict(list)
    for c in new:
        by_w[c["writer_id"]].append(c)
    chunks = []
    for w, cs in by_w.items():
        cs.sort(key=lambda c: sha(SALT + "|" + c["family_id"]))
        for i in range(0, len(cs), CHUNK):
            chunks.append((i // CHUNK, sha(SALT + "|w|" + w), w, cs[i:i + CHUNK]))
    chunks.sort(key=lambda x: (x[0], x[1]))
    start = len(state["batches"])
    nb = max(1, math.ceil(len(new) / size))
    fresh = [{"items": [], "writers": []} for _ in range(nb)]
    for _, _, w, cs in chunks:
        ok = [b for b in fresh if w not in b["writers"] and len(b["items"]) + len(cs) <= size]
        if not ok:   # only this writer left to place: share a batch rather than open a tiny one
            ok = [b for b in fresh if len(b["items"]) + len(cs) <= size]
        if not ok:
            fresh.append({"items": [], "writers": []}); ok = [fresh[-1]]
        b = min(ok, key=lambda b: len(b["items"]))
        b["items"] += [c["family_id"] for c in cs]; b["writers"].append(w)
    ids = []
    for k, b in enumerate([b for b in fresh if b["items"]]):
        cid = f"hwc{start + k + 1:03d}"
        b["writers"] = sorted(set(b["writers"]))
        state["batches"][cid] = b
        ids.append(cid)
    return ids


def write_file(out: Path, cid: str, b: dict, by: dict):
    items = []
    for fid in sorted(b["items"], key=lambda f: item_id(f)):
        f = by[fid]
        items.append({"item_id": item_id(fid), "dimension": f["dimension"], "options": f["critical_options"],
                      "context": f["context"], "A": f["variants"]["A"]["source"], "B": f["variants"]["B"]["source"],
                      "bare": f["bare"], "noncritical": f["noncritical"]})
    assert all(set(x) == set(BLIND_FIELDS) for x in items)
    doc = {"check_id": cid, "tool": TOOL, "version": 1, "n_items": len(items),
           "exclude": sorted(id_hash(w) for w in b["writers"]), "items": items}
    (out / "check_files").mkdir(parents=True, exist_ok=True)
    (out / "check_files" / f"{cid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def assign(state: dict, checkers: list[str], per: int, max_load: int | None, reassign: bool, tries: int = 200) -> list[str]:
    """Greedy assignment, repeated over `tries` deterministic batch orders; keeps the most balanced
    result (fewest unfilled slots, then smallest load range, then fewest repeated checker pairs)."""
    best = None
    base = {} if reassign else dict(state.get("assignment", {}))
    todo = sorted(c for c in state["batches"] if c not in base)
    for t in range(tries):
        order = todo if t == 0 else sorted(todo, key=lambda c: sha(f"{t}|{c}"))
        asg, problems, load, co = _greedy(state, dict(base), order, checkers, per, max_load)
        lv = [load[c] for c in checkers]
        score = (len(problems), (max(lv) - min(lv)) if lv else 0, sum(v * v for v in co.values()))
        if best is None or score < best[0]:
            best = (score, asg, problems)
        if score[0] == 0 and score[1] <= max((len(b["items"]) for b in state["batches"].values()), default=0) and t >= 20:
            break
    state["assignment"] = best[1]
    return best[2]


def _greedy(state, asg, order, checkers, per, max_load):
    load, co = Counter(), Counter()
    for cid, cs in asg.items():
        for c in cs:
            load[c] += len(state["batches"][cid]["items"])
        for x, y in combinations(sorted(cs), 2):
            co[(x, y)] += 1
    problems = []
    for cid in order:
        b = state["batches"][cid]
        chosen = []
        for _ in range(per):
            elig = [c for c in checkers if c not in b["writers"] and c not in chosen
                    and (max_load is None or load[c] + len(b["items"]) <= max_load)]
            if not elig:
                break
            c = min(elig, key=lambda c: (load[c], sum(co[tuple(sorted((c, x)))] for x in chosen), sha(cid + "|" + c)))
            chosen.append(c)
        if len(chosen) < per:
            problems.append(f"{cid}: only {len(chosen)} eligible checker(s) of {per} (writers {b['writers']}); add checkers")
        for c in chosen:
            load[c] += len(b["items"])
        for x, y in combinations(sorted(chosen), 2):
            co[(x, y)] += 1
        asg[cid] = chosen
    return asg, problems, load, co


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default=str(ROOT / "annotation" / "written" / "hw_candidates.jsonl"))
    ap.add_argument("--out-dir", default=str(ROOT / "annotation" / "written"))
    ap.add_argument("--batch-size", type=int, default=30)
    ap.add_argument("--per-pair", type=int, default=3)
    ap.add_argument("--checkers"); ap.add_argument("--checkers-file")
    ap.add_argument("--max-load", type=int, help="maximum pairs per checker")
    ap.add_argument("--reassign", action="store_true", help="recompute all checker assignments")
    a = ap.parse_args(argv)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    cands = [json.loads(l) for l in Path(a.candidates).open() if l.strip()]
    by = {c["family_id"]: c for c in cands}
    sp = out / "check_batches.json"
    state = json.loads(sp.read_text()) if sp.exists() else {"salt": SALT, "batch_size": a.batch_size, "batches": {}}
    missing = sorted({f for b in state["batches"].values() for f in b["items"]} - set(by))
    if missing:
        print(f"warning: {len(missing)} batched family id(s) are no longer candidates (edited/withdrawn); "
              f"their check returns will be ignored: {missing[:8]}", file=sys.stderr)
    new_ids = batch_new(cands, state, a.batch_size)
    for cid in new_ids:
        write_file(out, cid, state["batches"][cid], by)
    checkers = []
    if a.checkers:
        checkers += [c.strip() for c in a.checkers.split(",") if c.strip()]
    if a.checkers_file:
        checkers += [l.strip() for l in Path(a.checkers_file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    checkers = list(dict.fromkeys(checkers))
    problems = assign(state, checkers, a.per_pair, a.max_load, a.reassign) if checkers else []
    sp.write_text(json.dumps(state, indent=1) + "\n")
    with open(out / "check_key.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "check_id", "family_id", "writer_id", "dimension", "value_A", "value_B", "source_A", "source_B", "bare"])
        for cid, b in sorted(state["batches"].items()):
            for fid in b["items"]:
                c = by.get(fid)
                if c:
                    w.writerow([item_id(fid), cid, fid, c["writer_id"], c["dimension"], c["variants"]["A"]["critical_value"],
                                c["variants"]["B"]["critical_value"], c["variants"]["A"]["source"], c["variants"]["B"]["source"], c["bare"]])
    asg = state.get("assignment", {})
    if asg:
        per = max((len(v) for v in asg.values()), default=a.per_pair)
        with open(out / "check_assignment.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["check_id", "file", "n_pairs", "dimensions"] + [f"checker_{i + 1}" for i in range(per)] + ["writers_in_batch"])
            for cid, b in sorted(state["batches"].items()):
                dims = Counter(by[x]["dimension"] for x in b["items"] if x in by)
                cs = asg.get(cid, [])
                w.writerow([cid, f"check_files/{cid}.json", len(b["items"]), " ".join(f"{k}:{v}" for k, v in sorted(dims.items()))]
                           + cs + [""] * (per - len(cs)) + [" ".join(b["writers"])])
        byc = defaultdict(list)
        for cid, cs in asg.items():
            for c in cs:
                byc[c].append(cid)
        with open(out / "check_assignment_by_checker.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["checker", "n_batches", "n_pairs", "check_ids"])
            for c in sorted(byc):
                w.writerow([c, len(byc[c]), sum(len(state["batches"][x]["items"]) for x in byc[c]), " ".join(sorted(byc[c]))])
    n_pairs = sum(len(b["items"]) for b in state["batches"].values())
    print(f"{len(state['batches'])} check batch(es) ({len(new_ids)} new) covering {n_pairs} pairs -> {out / 'check_files'}")
    if checkers:
        loads = Counter()
        for cid, cs in asg.items():
            for c in cs:
                loads[c] += len(state["batches"][cid]["items"])
        print(f"assignment: {len(asg)} batches x {a.per_pair} checkers; checker load (pairs) min {min(loads.values(), default=0)} "
              f"max {max(loads.values(), default=0)} over {len(loads)} checkers -> {out / 'check_assignment.csv'}")
    else:
        print("no --checkers given: batches written, assignment sheet not (re)built")
    for p in problems:
        print("problem:", p)
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
