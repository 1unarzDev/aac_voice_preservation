"""Part 21: human check of the source-message labels behind the T2 posterior. 0 generation, 0 judge calls.

Why: the T2 analysis (analysis/robust/t2_posterior) asks "how often was the message negated when its keywords contain no
negation word?". "Negated", "polite" and "question/request" for the SOURCE message come from a rule-based detector
(polarity 150/150 against an LLM first pass; the other two less validated). Part 21 asks people to read real AACText
messages and answer three quick questions, so the detector can be checked and the T2 estimate corrected with human labels.

Items (200 messages; seeded, declared; seed 20261102). Frame: the 600 AACText messages of the keyword-elicitation sample
(annotation/elicitation_key.jsonl; 300 uniform-random + 300 enriched; the sample behind analysis/elicitation and T2).
W-B messages are not used: they have no keyword sets, so they cannot enter the T2 correction.
Strata by DETECTOR label, disjoint, first match: negated (polarity = negated; 122 messages) -> 55; polite (politeness != none;
115) -> 55; question_request (speech act question or request/command; 181) -> 45; plain_other (the rest; 182) -> 45.
This oversamples what the detector calls negated, polite or question so the positives are well covered; negated + polite +
question_request are 155 of the 200. Within a stratum messages are taken in ascending sha1(seed | stratum | item_id) order.
Weights (kept in the key): w_stratum = stratum size / drawn (the 600-message frame); w_total = w_stratum / elicitation
inclusion probability (Horvitz-Thompson back to the 4,560-message frame, the weights T2 uses). The scorer reports
unweighted and w_total-reweighted agreement.
Questions (per message, shown with 3 practice messages first): (1) negated? yes / no / unsure; (2) polite? yes / no / unsure;
(3) statement / question / request / unsure. Only the message is shown: no keywords, no detector label, no stratum.
Tool: annotation_package/source_check.html (self-contained, same look as check_pairs.html), loading
stage5/<ID>_part21.json; returns labels_part21_<ID>.csv -> annotation/returns_source_check/.
Assignment: 2 independent coders per message (20 messages each; 400 codings over 20 people). A person never codes a message
whose keywords they typed in Part 9: blocked = every annotator of the message's elicitation set (any replicate; a superset of
the people who typed it, annotation/elicitation_assignment.csv; the typed keyword sets are listed in the key). Same greedy
load-balancing code as Part 19.

Writes:
  annotation_package/stage5/<ID>_part21.json   blind file per person (their 20 messages)
  annotation/source_check_key.csv              private: detector labels, strata, weights, coders, blocked people
  annotation/source_check_sample.json          rule, seed, composition, loads, key hash
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_arbiter_check as MC  # noqa: E402
import runio  # noqa: E402

SEED = 20261102
RUN_TAG = "part21"
TOOL = "source_check_v1"
QUOTA = {"negated": 55, "polite": 55, "question_request": 45, "plain_other": 45}
PER_ITEM = 2
OUT_DIR = ROOT / "annotation_package" / "stage5"
KEY = ROOT / "annotation" / "source_check_key.csv"
SUMMARY = ROOT / "annotation" / "source_check_sample.json"
KEY_COLS = ["item_id", "source_item_id", "source_id", "text", "elic_sample", "elic_stratum", "inclusion_prob", "stratum", "stratum_n",
            "drawn_n", "w_stratum", "w_total", "detector_negated", "detector_polite", "detector_speech_act", "detector_politeness",
            "detector_qr", "human_keyword_sets", "coders", "blocked_people"]


def h(*parts) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()


def id_hash(s: str) -> str:
    """FNV-1a (32 bit) of the upper-cased, trimmed ID + '|part21'; the same function runs in source_check.html."""
    x = 2166136261
    for c in s.strip().upper() + "|part21":
        x = ((x ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return f"{x:08x}"


def stratum_of(det: dict) -> str:
    if det["polarity"] == "negated":
        return "negated"
    if det["politeness"] != "none":
        return "polite"
    if det["speech_act"] in ("question", "request/command"):
        return "question_request"
    return "plain_other"


def frame() -> list[dict]:
    out = []
    for r in runio.read_jsonl(ROOT / "annotation" / "elicitation_key.jsonl"):
        d = r["detector_labels"]
        out.append({"source_item_id": r["item_id"], "source_id": r["id"], "text": r["text"], "set": r["set"],
                    "elic_sample": r["sample"], "elic_stratum": r["stratum"], "inclusion_prob": r["inclusion_prob"],
                    "stratum": stratum_of(d), "detector_negated": int(d["polarity"] == "negated"),
                    "detector_polite": int(d["politeness"] != "none"), "detector_speech_act": d["speech_act"],
                    "detector_politeness": d["politeness"],
                    "detector_qr": {"question": "question", "request/command": "request"}.get(d["speech_act"], "statement_or_other")})
    return out


def draw(fr: list[dict]) -> list[dict]:
    by = defaultdict(list)
    for m in fr:
        by[m["stratum"]].append(m)
    chosen = []
    for s, q in QUOTA.items():
        pool = sorted(by[s], key=lambda m: h(SEED, s, m["source_item_id"]))
        assert len(pool) >= q, (s, len(pool))
        for m in pool[:q]:
            m = dict(m); m["stratum_n"] = len(pool); m["drawn_n"] = q
            m["w_stratum"] = round(len(pool) / q, 6); m["w_total"] = round(len(pool) / q / m["inclusion_prob"], 6)
            chosen.append(m)
    for m in chosen:
        m["item_id"] = "p21-" + h("part21-item", m["source_item_id"])[:8]
    assert len({m["item_id"] for m in chosen}) == len(chosen) == sum(QUOTA.values())
    return chosen


def blocked_map(ids: list[str]) -> tuple[dict, dict]:
    """source_item_id -> people blocked (annotators of the message's set); source_item_id -> typed keyword sets."""
    people = defaultdict(set)
    with open(ROOT / "annotation" / "elicitation_assignment.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            people[r["set"]].add(r["annotator"])
    typed = defaultdict(list)
    p = ROOT / "analysis" / "elicitation" / "ratings.csv"
    if p.exists():
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                typed[r["item_id"]].append(f"{r['annotator']}: {r['keywords']}")
    b = {}
    for m in frame():
        b[m["source_item_id"]] = people[m["set"]]
    return b, typed


def part_payload(its: list[dict], annotator: str) -> dict:
    return {"check_id": RUN_TAG, "tool": TOOL, "version": 1, "n_items": len(its), "for": id_hash(annotator),
            "items": [{"item_id": m["item_id"], "text": m["text"]} for m in its]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--annotators", default="", help="default: annotators of annotation/assignments/plan.json")
    ap.add_argument("--out-dir", default=str(OUT_DIR)); ap.add_argument("--key", default=str(KEY))
    ap.add_argument("--summary", default=str(SUMMARY))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if Path(a.key).exists() and not a.force:
        print(f"{a.key} exists and is frozen; pass --force to overwrite", file=sys.stderr)
        return 2
    ids = [x for x in a.annotators.split(",") if x] or json.loads((ROOT / "annotation/assignments/plan.json").read_text())["annotators"]
    fr = frame()
    units = draw(fr)
    blk, typed = blocked_map(ids)
    for u in units:                                       # fields MC.assign reads
        u["families"], u["run"], u["text_id"], u["family_id"] = u["source_item_id"], "elic1", u["item_id"], u["source_item_id"]
    load = MC.assign(units, ids, blk)

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*_part21.json"):
        old.unlink()
    per = defaultdict(list)
    for u in sorted(units, key=lambda u: u["item_id"]):
        for c in u["coders"]:
            per[c].append(u)
    for c in ids:
        mine = sorted(per[c], key=lambda u: h(SEED, "present", c, u["item_id"]))
        (out / f"{c}_part21.json").write_text(json.dumps(part_payload(mine, c), indent=1, ensure_ascii=False))
    with open(a.key, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEY_COLS); w.writeheader()
        for u in sorted(units, key=lambda u: (list(QUOTA).index(u["stratum"]), u["item_id"])):
            row = {c: u.get(c, "") for c in KEY_COLS}
            row |= {"human_keyword_sets": " || ".join(typed.get(u["source_item_id"], [])),
                    "coders": "|".join(sorted(u["coders"])), "blocked_people": "|".join(sorted(u["blocked"]))}
            w.writerow(row)
    comp = {"n": len(units), "by_stratum": dict(Counter(u["stratum"] for u in units)),
            "detector_negated": sum(u["detector_negated"] for u in units), "detector_polite": sum(u["detector_polite"] for u in units),
            "detector_question": sum(u["detector_qr"] == "question" for u in units),
            "detector_request": sum(u["detector_qr"] == "request" for u in units),
            "by_elic_sample": dict(Counter(u["elic_sample"] for u in units))}
    summ = {"seed": SEED, "rule": __doc__.split("Items (200")[1].split("Tool:")[0].strip(), "annotators": ids, "per_item": PER_ITEM,
            "frame_n": len(fr), "frame_by_stratum": dict(Counter(m["stratum"] for m in fr)), "quota": QUOTA, "composition": comp,
            "codings": sum(len(u["coders"]) for u in units), "items_per_person": dict(sorted(load.items())),
            "min_max_items_per_person": [min(load.values()), max(load.values())],
            "key_sha256": hashlib.sha256(Path(a.key).read_bytes()).hexdigest()}
    Path(a.summary).write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps({k: summ[k] for k in ("frame_by_stratum", "composition", "codings", "min_max_items_per_person")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
