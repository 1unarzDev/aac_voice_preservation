"""B1 coordinator: assign writers to dimensions and topic rotations; print their write_pairs.html links.

usage: python src/make_writer_links.py --writers P01,P02,... | --n 60   [--pairs 15]
          [--dims polarity,speech_act,politeness,certainty,agent,time] [--out annotation/written/writer_assignment.csv]

Writers are dealt to dimensions round-robin in a hash-shuffled order, so each dimension gets
floor/ceil(W / 6) writers (expected pairs per dimension = writers x pairs). Each writer gets a topic
rotation `rot` (0-10): pair i of that writer suggests topic TOPICS[(rot + i) % 11]. Rotations are
spread within each dimension (writer j of a dimension gets rot = (3 j + dimension index) % 11), so the
11 domains (health, sensory, boundaries, work/school, plans, food, transport, money, relationships,
self-advocacy, hobbies) are covered about evenly per dimension.
The link fragment, e.g. write_pairs.html#dim=agent&rot=4&n=15&id=P07, opens the tool with the
dimension fixed and the ID filled in. Existing rows of --out are kept unless --force (writers already
working must keep their dimension).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hw_rules import DIMS, TOPICS  # noqa: E402


def rotation(j: int, dim_index: int) -> int:
    """Topic rotation of the j-th writer (0-based) of the dimension with index dim_index."""
    return (3 * j + dim_index) % len(TOPICS)


def first_topics(rot: int, k: int = 3) -> str:
    return " ".join(TOPICS[(rot + i) % len(TOPICS)] for i in range(k))


def link_fragment(dim: str, rot: int, n: int, writer: str) -> str:
    return f"#dim={dim}&rot={rot}&n={n}&id={writer}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--writers"); g.add_argument("--n", type=int)
    ap.add_argument("--pairs", type=int, default=15)
    ap.add_argument("--dims", default=",".join(DIMS))
    ap.add_argument("--out", default=str(ROOT / "annotation" / "written" / "writer_assignment.csv"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    dims = [d.strip() for d in a.dims.split(",") if d.strip()]
    bad = [d for d in dims if d not in DIMS]
    if bad:
        raise SystemExit(f"unknown dimension(s) {bad}; choose from {list(DIMS)}")
    writers = [w.strip() for w in a.writers.split(",") if w.strip()] if a.writers else [f"P{i:02d}" for i in range(1, a.n + 1)]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if out.exists() and not a.force:
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    have = {r["writer_id"] for r in rows}
    per_dim = Counter(r["dimension"] for r in rows)
    new = sorted((w for w in writers if w not in have), key=lambda w: hashlib.sha1(f"hw-writers|{w}".encode()).hexdigest())
    for w in new:
        d = min(dims, key=lambda d: (per_dim[d], dims.index(d)))
        j = per_dim[d]; per_dim[d] += 1
        rot = rotation(j, dims.index(d))
        rows.append({"writer_id": w, "dimension": d, "rot": rot, "n_pairs": a.pairs,
                     "first_topics": first_topics(rot), "link_fragment": link_fragment(d, rot, a.pairs, w)})
    with open(out, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["writer_id", "dimension", "rot", "n_pairs", "first_topics", "link_fragment"])
        wr.writeheader(); wr.writerows(rows)
    tot = Counter()
    for r in rows:
        tot[r["dimension"]] += int(r["n_pairs"])
    print(f"{len(rows)} writers ({len(new)} new) -> {out}")
    print("expected pairs per dimension:", dict(tot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
