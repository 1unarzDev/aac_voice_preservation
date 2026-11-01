"""B2 keyword elicitation: draw 600 AACText messages and split them into blind sets for 3 annotators each.

usage: python src/make_elicitation_sets.py [--annotators P01,P02,... | --annotators-file ids.txt]

Frame (as W-B, src/wb_sample.py): every message in analysis/s1/message_cues.jsonl (s1_cues revision 1
on data/raw/aactext/sent_{train,dev,test}_aac.txt, CC BY 4.0, Vertanen & Kristensson 2011), minus
messages with < 3 words or an empty POS-cap4 list, deduplicated on normalised text (first occurrence),
and here additionally minus
  * the W-B sample (data/specs/wb_sample.jsonl: 160 ids, their duplicate ids, and their texts) and
  * the W-C seeds (seed_line of data/items/r2_c1.jsonl + r2_c2.jsonl = aactext-train-<line>, and texts).
Draw (frozen before any human data): rank = sha256("elic-20261101|" + id).
  * random:   first 150 by rank. pi = 150 / N_frame.
  * enriched: frame minus the random 150, partitioned into disjoint detector cue pools with W-B's
    priority certainty (hedges) > polarity (negation) > politeness > speech_act (questions/requests);
    first 38 / 38 / 37 / 37 by rank from each pool. pi = q / |pool| (conditional on the random draw,
    exact under this design). inclusion_prob is recorded per message.
Sets: the 300 messages are dealt round-robin, stratum by stratum in rank order, into 8 sets of 37-38
(each set mixes all strata). The program's "about 40" is kept as close as 300 allows without
repeating messages. Each set is done by 3 annotators; replicate r (1-3) sees the set's 3 blocks in a
cyclic Latin-square order (block order r, r+1, r+2), so every block appears once in each position.
Assignment: (set, replicate) sessions are given to annotators greedily (lowest load, never the same
set twice). Without --annotators, placeholder slots E01..E24 are used.
Writes:
  annotation_package/elicitation_sets/elic_sNN_rK.json  blind: item_id + message text only
  annotation/elicitation_key.jsonl      private: item -> source id, stratum, pi, POS-cap4, detector cues
  annotation/elicitation_assignment.csv session -> file, annotator
  annotation/elicitation_sample.json    manifest (frame, exclusions, pools, pi, input hashes)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = "elic-20261101"
N_RANDOM = 300
QUOTA = {"certainty": 75, "polarity": 75, "politeness": 75, "speech_act": 75}   # pool priority order
N_SETS, N_REPS = 16, 3
CUES = ROOT / "analysis/s1/message_cues.jsonl"
WB = ROOT / "data/specs/wb_sample.jsonl"
WC = [ROOT / "data/items/r2_c1.jsonl", ROOT / "data/items/r2_c2.jsonl"]
SET_DIR = ROOT / "annotation_package/elicitation_sets"
KEY = ROOT / "annotation/elicitation_key.jsonl"
ASSIGN = ROOT / "annotation/elicitation_assignment.csv"
MANIFEST = ROOT / "annotation/elicitation_sample.json"
TOOL = "keyword_elicitation_v1"


def norm_text(t: str) -> str:
    t = t.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def rank(mid: str) -> str:
    return hashlib.sha256(f"{SEED}|{mid}".encode()).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def item_id(mid: str) -> str:
    return "el-" + hashlib.sha1(f"{SEED}|item|{mid}".encode()).hexdigest()[:6]


def exclusions():
    ids, texts = set(), set()
    n_wb = n_wc = 0
    for l in WB.open():
        r = json.loads(l); n_wb += 1
        ids.add(r["id"]); ids.update(r.get("duplicate_ids") or []); texts.add(norm_text(r["text"]))
    for p in WC:
        for l in p.open():
            r = json.loads(l)
            if r.get("seed_line"):
                n_wc += 1
                ids.add(f"aactext-train-{int(r['seed_line']):05d}")
                texts.add(norm_text(r.get("seed_text") or ""))
    texts.discard("")
    return ids, texts, n_wb, n_wc


def frame():
    rows = [json.loads(l) for l in CUES.open()]
    order = {"train": 0, "dev": 1, "test": 2}
    rows.sort(key=lambda r: (order[r["split"]], r["line"]))
    ex_ids, ex_txt, n_wb, n_wc = exclusions()
    excl, seen, fr = Counter(), {}, []
    for r in rows:
        if len(r["text"].split()) < 3:
            excl["lt3_words"] += 1; continue
        if not r["keywords"]["pos_cap4"]["words"]:
            excl["empty_pos_cap4"] += 1; continue
        k = norm_text(r["text"])
        if k in seen:
            excl["duplicate_text"] += 1; continue
        seen[k] = r
        if r["id"] in ex_ids or k in ex_txt:
            excl["wb_or_wc_seed"] += 1; continue
        fr.append(r)
    fr.sort(key=lambda r: rank(r["id"]))
    return fr, excl, len(rows), n_wb, n_wc


def draw(fr):
    N = len(fr)
    chosen = [(r, "random", N_RANDOM / N) for r in fr[:N_RANDOM]]
    pools = {d: [] for d in QUOTA}
    for r in fr[N_RANDOM:]:
        d = next((d for d in QUOTA if r["loss"]["pos_cap4"]["present"][d]), None)
        if d:
            pools[d].append(r)
    for d, q in QUOTA.items():
        assert len(pools[d]) >= q, (d, len(pools[d]))
        chosen += [(r, f"enriched_{d}", q / len(pools[d])) for r in pools[d][:q]]
    return chosen, pools


def latin_orders(ids: list[str]) -> list[list[str]]:
    k = len(ids)
    cuts = [0, round(k / 3), round(2 * k / 3), k]
    blocks = [ids[cuts[i]:cuts[i + 1]] for i in range(3)]
    return [[x for j in range(3) for x in blocks[(r + j) % 3]] for r in range(N_REPS)]


def assign(sessions, annotators):
    load, got, out = Counter(), {}, []
    for s in sessions:
        elig = [a for a in annotators if s["set"] not in got.get(a, set())]
        if not elig:
            raise SystemExit(f"cannot place session {s['file']}: every annotator already has set {s['set']}")
        a = min(elig, key=lambda a: (load[a], annotators.index(a)))
        load[a] += 1; got.setdefault(a, set()).add(s["set"])
        out.append({**s, "annotator": a})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annotators"); ap.add_argument("--annotators-file")
    a = ap.parse_args(argv)
    fr, excl, n_rows, n_wb, n_wc = frame()
    chosen, pools = draw(fr)
    assert len(chosen) == 600 and len({r["id"] for r, *_ in chosen}) == 600
    # deal into sets: stratum by stratum, rank order, round-robin
    strata = ["random"] + [f"enriched_{d}" for d in QUOTA]
    dealt = [x for s in strata for x in sorted((c for c in chosen if c[1] == s), key=lambda c: rank(c[0]["id"]))]
    sets = {i: [] for i in range(N_SETS)}
    for j, c in enumerate(dealt):
        sets[j % N_SETS].append(c)
    SET_DIR.mkdir(parents=True, exist_ok=True)
    for old in SET_DIR.glob("elic_s*_r*.json"):
        old.unlink()
    key, sessions = [], []
    for si, members in sets.items():
        sid = f"s{si + 1:02d}"
        base = sorted((item_id(r["id"]) for r, *_ in members), key=lambda x: hashlib.sha1(f"{SEED}|order|{x}".encode()).hexdigest())
        text = {item_id(r["id"]): r["text"] for r, *_ in members}
        for ri, order in enumerate(latin_orders(base)):
            fname = f"elic_{sid}_r{ri + 1}"
            doc = {"set_file": fname, "set": sid, "order": ri + 1, "tool": TOOL, "version": 1, "n": len(order),
                   "messages": [{"item_id": x, "text": text[x]} for x in order]}
            (SET_DIR / f"{fname}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
            sessions.append({"set": sid, "replicate": ri + 1, "file": f"elicitation_sets/{fname}.json", "n_messages": len(order)})
        pos = {x: [o.index(x) + 1 for o in latin_orders(base)] for x in base}
        for r, stratum, pi in members:
            iid = item_id(r["id"])
            key.append({"item_id": iid, "set": sid, "positions_by_replicate": pos[iid], "id": r["id"], "split": r["split"],
                        "line": r["line"], "text": r["text"], "sample": "random" if stratum == "random" else "enriched",
                        "stratum": stratum, "inclusion_prob": pi, "rank": rank(r["id"]),
                        "pos_cap4": r["keywords"]["pos_cap4"]["words"], "pos_cap4_token_ids": r["keywords"]["pos_cap4"]["token_ids"],
                        "detector_labels": r["detector"]["labels"], "detector_cues": r["detector"]["cues"],
                        "present": r["loss"]["pos_cap4"]["present"], "lost_pos_cap4": r["loss"]["pos_cap4"]["lost"],
                        "corpus": "AACText (Vertanen & Kristensson 2011), CC BY 4.0"})
    assert len({k["item_id"] for k in key}) == 600
    key.sort(key=lambda k: (k["set"], k["item_id"]))
    KEY.parent.mkdir(parents=True, exist_ok=True)
    with KEY.open("w") as f:
        for k in key:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    annotators = []
    if a.annotators:
        annotators += [x.strip() for x in a.annotators.split(",") if x.strip()]
    if a.annotators_file:
        annotators += [l.strip() for l in Path(a.annotators_file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    annotators = list(dict.fromkeys(annotators)) or [f"E{i:02d}" for i in range(1, N_SETS * N_REPS + 1)]
    # replicate-major order: every set gets its first annotator before any set gets a second
    sessions.sort(key=lambda s: (s["replicate"], s["set"]))
    rows = assign(sessions, annotators)
    with ASSIGN.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["set", "replicate", "file", "n_messages", "annotator"])
        w.writeheader(); w.writerows(rows)
    man = {"seed": SEED, "corpus_nonempty": n_rows, "frame_n": len(fr), "exclusions": dict(excl),
           "excluded_wb_sample": n_wb, "excluded_wc_seed_families": n_wc,
           "pool_sizes": {d: len(p) for d, p in pools.items()}, "quota": QUOTA, "n_random": N_RANDOM,
           "pi_random": N_RANDOM / len(fr), "pi_enriched": {d: QUOTA[d] / len(p) for d, p in pools.items()},
           "n_by_stratum": dict(Counter(k["stratum"] for k in key)),
           "sets": {f"s{i + 1:02d}": len(m) for i, m in sets.items()}, "replicates_per_set": N_REPS,
           "annotators": annotators, "placeholder_annotators": not (a.annotators or a.annotators_file),
           "inputs_sha256": {str(p.relative_to(ROOT)): sha_file(p) for p in [CUES, WB, *WC]},
           "code_sha256": sha_file(Path(__file__))}
    MANIFEST.write_text(json.dumps(man, indent=1) + "\n")
    print(json.dumps({k: v for k, v in man.items() if k not in ("inputs_sha256", "annotators")}, indent=1))
    print(f"{len(sessions)} session files -> {SET_DIR}; key -> {KEY}; assignment -> {ASSIGN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
