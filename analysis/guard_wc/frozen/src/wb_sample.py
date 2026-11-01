"""W-B corpus-transfer sample (PREREG_R2 W-B): 80 simple-random + 80 enriched AACText messages.

Frame (frozen before drawing):
  * every nonempty line of data/raw/aactext/sent_{train,dev,test}_aac.txt (ids as in s1_analyze);
  * exclude messages with < 3 whitespace words;
  * exclude messages whose POS-cap4 keyword list is empty (nothing to expand);
  * deduplicate exact texts after normalisation (lowercase, curly->straight quotes, strip
    non-alphanumerics except apostrophes, collapse spaces). Frozen replacement rule: the
    representative of a duplicate group is its FIRST occurrence in corpus order
    (train, dev, test; line order). Any draw of a duplicate is thereby replaced by that
    representative, and the frame contains each text once.
Draw order: every frame message gets rank = sha256(f"{SEED}|{id}"); "first k by rank" is a
simple random sample without replacement. If an item must be dropped later (e.g. a coder
failure), the replacement is the next-ranked unused frame message of the same stratum.
  * random: first 80 by rank.  pi = 80 / N_frame.
  * enriched: frame minus the random 80, partitioned into DISJOINT cue pools by detector
    (s1_cues revision 1; analysis/s1/message_cues.jsonl) with priority
    certainty > polarity > politeness > speech_act (rarest first); 20 drawn from each pool.
    pi = 20 / |pool| (conditional on the random draw; exact under this design).
Focal dimension: enriched = the stratum dimension. Random = the first dimension in
FOCAL_PRIORITY whose detected cue is LOST under POS-cap4, else "none" (no restoration channel).
Overlap with data/specs/aactext_sample400.jsonl is recorded per item (in_sample400) and in
the manifest, so downstream seed drawing can check collisions by id.

  python src/wb_sample.py        # writes data/specs/wb_sample.jsonl + analysis/wb/sample_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = "wb-20261101"
N_RANDOM, N_PER_STRATUM = 80, 20
STRATA = ["certainty", "polarity", "politeness", "speech_act"]       # pool priority
FOCAL_PRIORITY = ["polarity", "certainty", "politeness", "speech_act", "agent"]
CUES = ROOT / "analysis/s1/message_cues.jsonl"
OUT = ROOT / "data/specs/wb_sample.jsonl"


def norm_text(t: str) -> str:
    t = t.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def rank(mid: str) -> str:
    return hashlib.sha256(f"{SEED}|{mid}".encode()).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    rows = [json.loads(l) for l in CUES.open()]
    order = {"train": 0, "dev": 1, "test": 2}
    rows.sort(key=lambda r: (order[r["split"]], r["line"]))
    s400 = {json.loads(l)["id"] for l in (ROOT / "data/specs/aactext_sample400.jsonl").open()}
    excl = Counter()
    seen, frame = {}, []
    for r in rows:
        if len(r["text"].split()) < 3:
            excl["lt3_words"] += 1; continue
        if not r["keywords"]["pos_cap4"]["words"]:
            excl["empty_pos_cap4"] += 1; continue
        k = norm_text(r["text"])
        if k in seen:
            excl["duplicate_text"] += 1; seen[k]["dup_ids"].append(r["id"]); continue
        r["dup_ids"] = []
        seen[k] = r
        frame.append(r)
    frame.sort(key=lambda r: rank(r["id"]))
    N = len(frame)
    present = lambda r, d: r["loss"]["pos_cap4"]["present"][d]
    lost = lambda r, d: r["loss"]["pos_cap4"]["lost"][d]

    chosen = []
    for r in frame[:N_RANDOM]:
        focal = next((d for d in FOCAL_PRIORITY if lost(r, d)), "none")
        chosen.append((r, "random", focal, N_RANDOM / N))
    rest = frame[N_RANDOM:]
    pools = {d: [] for d in STRATA}
    for r in rest:
        d = next((d for d in STRATA if present(r, d)), None)
        if d:
            pools[d].append(r)
    for d in STRATA:
        for r in pools[d][:N_PER_STRATUM]:
            chosen.append((r, f"enriched_{d}", d, N_PER_STRATUM / len(pools[d])))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for r, stratum, focal, pi in chosen:
            f.write(json.dumps({
                "id": r["id"], "split": r["split"], "line": r["line"], "text": r["text"],
                "sample": "random" if stratum == "random" else "enriched",
                "stratum": stratum, "focal_dim": focal, "inclusion_prob": pi,
                "rank": rank(r["id"]), "in_sample400": r["id"] in s400,
                "duplicate_ids": r["dup_ids"],
                "pos_cap4": r["keywords"]["pos_cap4"]["words"],
                "pos_cap4_token_ids": r["keywords"]["pos_cap4"]["token_ids"],
                "detector_labels": r["detector"]["labels"],
                "detector_cues": r["detector"]["cues"],
                "lost_pos_cap4": r["loss"]["pos_cap4"]["lost"],
                "present": r["loss"]["pos_cap4"]["present"],
                "corpus": "AACText (Vertanen & Kristensson 2011), CC BY 4.0"}) + "\n")
    man = {"seed": SEED, "frame_n": N, "exclusions": dict(excl),
           "corpus_nonempty": len(rows),
           "pool_sizes": {d: len(p) for d, p in pools.items()},
           "pi_random": N_RANDOM / N,
           "pi_enriched": {d: N_PER_STRATUM / len(p) for d, p in pools.items()},
           "n_by_stratum": dict(Counter(s for _, s, _, _ in chosen)),
           "focal_by_stratum": {s: dict(Counter(f for _, ss, f, _ in chosen if ss == s))
                                for s in sorted({s for _, s, _, _ in chosen})},
           "overlap_sample400": sorted(r["id"] for r, *_ in chosen if r["id"] in s400),
           "overlap_sample400_by_sample": dict(Counter(
               ("random" if s == "random" else "enriched") for r, s, *_ in chosen if r["id"] in s400)),
           "inputs_sha256": {str(CUES.relative_to(ROOT)): sha_file(CUES),
                             "data/specs/aactext_sample400.jsonl": sha_file(ROOT / "data/specs/aactext_sample400.jsonl")},
           "code_sha256": sha_file(Path(__file__))}
    (ROOT / "analysis/wb").mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis/wb/sample_manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps({k: v for k, v in man.items() if k != "overlap_sample400"}, indent=1))
    print("overlap with sample400:", len(man["overlap_sample400"]))


if __name__ == "__main__":
    main()
