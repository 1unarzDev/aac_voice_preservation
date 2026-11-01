"""Explode generations into one row per suggestion, and dedupe texts for judging.

  python src/explode.py --run runs/<run_id>

Writes in the run folder:
  outputs.jsonl         one row per (generation x suggestion x target). A deduplicated
                        request (e.g. `bare`, shared by variants A and B) yields one row per
                        (family_id, variant, channel) target, all with the same output_id.
                        output_id = sha1(request_key, suggestion_idx, text)[:16]
                        text_id   = sha1(normalised text)[:16]
  unique_outputs.jsonl  one row per distinct normalised text (text_id), with the
                        output_ids and distinct input_texts it came from. Judge each text once.
                        With --by-input the unit is (text, input_text), needed for judge
                        questions that look at the visible input (added_content, Pass A).
Normalisation: NFKC, curly->straight quotes, lowercase, collapse whitespace, drop a single
trailing period. '?' and '!' are kept because they carry speech act / certainty.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path


def sha1(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]


def normalise(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = t.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    t = re.sub(r"\s+", " ", t.lower()).strip()
    return t[:-1].rstrip() if t.endswith(".") and not t.endswith("..") else t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="run folder containing generations.jsonl")
    ap.add_argument("--by-input", action="store_true", help="unique unit = (text, input_text)")
    a = ap.parse_args()
    run = Path(a.run)
    gens = [json.loads(l) for l in (run / "generations.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    rows, uniq = [], {}
    for g in gens:
        if g.get("error"):
            continue
        for i, text in enumerate(g["suggestions"]):
            norm = normalise(text)
            oid = sha1(g["request_key"], i, text)
            tid = sha1(norm, g["input_text"]) if a.by_input else sha1(norm)
            base = {"output_id": oid, "text_id": tid, "text": text, "suggestion_idx": i,
                    "n_suggestions_got": len(g["suggestions"]), "parse_ok": g["parse_ok"],
                    "request_key": g["request_key"], "model": g["model"], "prompt_id": g["prompt_id"],
                    "temperature": g["temperature"], "sample_idx": g["sample_idx"],
                    "dimension": g["dimension"], "split": g["split"], "input_text": g["input_text"],
                    "finish_reason": g.get("finish_reason")}
            if g.get("namespace"):   # draw id (only on namespaced requests)
                base["namespace"] = g["namespace"]
            for t in g["targets"]:
                rows.append({**base, **t})
            u = uniq.setdefault(tid, {"text_id": tid, "text": text, "norm_text": norm,
                                      "output_ids": [], "input_texts": [], "n_outputs": 0})
            u["n_outputs"] += 1
            u["output_ids"].append(oid)
            if g["input_text"] not in u["input_texts"]:
                u["input_texts"].append(g["input_text"])

    with (run / "outputs.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (run / "unique_outputs.jsonl").open("w", encoding="utf-8") as f:
        for u in uniq.values():
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    n_out = len({r["output_id"] for r in rows})
    print(f"{len(gens)} generations -> {n_out} outputs ({len(rows)} target rows) -> {len(uniq)} unique texts")


if __name__ == "__main__":
    main()
