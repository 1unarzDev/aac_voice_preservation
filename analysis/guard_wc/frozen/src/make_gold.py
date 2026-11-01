"""Draw the human gold sample from judgments and write the annotation file.

  python src/make_gold.py --run pilot1 [--n 160] [--seed 20261031]

Unit = one judgment row (text_id, family_id, input_text): an output sentence plus the
family's critical question (and the visible input, shown only for added_content).

Design
  strata   dimension x model x judge critical label (J1/J2 disagreement = 'DISAGREE').
           A text produced by several models takes the alphabetically first model.
  weights  w = 1 + 3*disagree(J1 != J2 on any dim) + 2*positive, where positive =
           judge-based Violation, Assumption (commitment under bare/noncrit), any stance
           addition or added_content=yes (from scored.parquet if present), then
           divided by sqrt(stratum size) so small strata are not swamped.
  sampling Poisson PPS: pi_i = min(1, c*w_i), c solved so sum(pi) = n; each unit is
           included independently with probability pi_i. The realised size is ~n; pi_i
           is exact, so Horvitz-Thompson / IPW weights 1/pi_i are unbiased.
Held out from annotators: source, model, prompt, channel, judge labels, family id. Those
live only in annotation/gold_key_<run>.csv.

Outputs
  annotation/gold_items_<run>.json   for annotate.html (5 practice items + sample)
  annotation/gold_key_<run>.csv      item_id -> unit, stratum, pi, judge labels
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runio  # noqa: E402
from judge import critical_question  # noqa: E402
from labels import ADDED_CONTENT_OPTIONS, DEFINITIONS, GENERAL_DIMS, GENERAL_OPTIONS  # noqa: E402

ROOT = runio.ROOT
SEED = 20261031
CODEBOOK_VERSION = "v0.2 (D-007)"
JUDGED_DIMS = ["critical"] + GENERAL_DIMS + ["added_content"]

# Practice items with expected answers + feedback (shown after answering).
PRACTICE = [
    {"item_id": "practice-1", "text": "I don't want to go to the party tonight.",
     "dimension": "polarity", "critical_options": ["negated", "affirmative", "unclear/mixed"],
     "input_text": "Keywords: want go party",
     "expected": {"critical": "negated", "polarity": "negated", "speech_act": "statement",
                  "agent": "speaker", "certainty": "plain assertion", "politeness": "none",
                  "added_content": "yes"},
     "feedback": "\"don't\" negates the main verb, so polarity is negated. 'tonight' is a time that "
                 "is not in the input words, so added content = yes."},
    {"item_id": "practice-2", "text": "Can you pick me up after work?",
     "dimension": "speech_act",
     "critical_options": ["statement", "question", "request/command", "refusal", "acceptance",
                          "offer/suggestion", "unclear/mixed"],
     "input_text": "Keywords: pick up work",
     "expected": {"critical": "request/command", "polarity": "affirmative",
                  "speech_act": "request/command", "agent": "addressee",
                  "certainty": "n/a (question/request)", "politeness": "none",
                  "added_content": "no"},
     "feedback": "'Can you ...?' asks the listener to do something: a request, done by the "
                 "addressee. 'Can you' alone is NOT a polite marker (codebook rule), so "
                 "politeness = none. Requests get certainty n/a."},
    {"item_id": "practice-3", "text": "I think the bus might be late today.",
     "dimension": "certainty",
     "critical_options": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic",
                          "unclear/mixed"],
     "input_text": "Keywords: [MAYBE] bus late",
     "expected": {"critical": "hedged/uncertain", "polarity": "affirmative",
                  "speech_act": "statement", "agent": "third party",
                  "certainty": "hedged/uncertain", "politeness": "none", "added_content": "yes"},
     "feedback": "'I think' and 'might' are hedges. The bus is the one that is late, so the agent "
                 "is a third party. 'today' is not in the input: added content = yes."},
    {"item_id": "practice-4", "text": "Could you please turn the TV down?",
     "dimension": "politeness", "critical_options": ["polite", "plain", "unclear/mixed"],
     "input_text": "Keywords: [ASK] [YOU] turn tv down",
     "expected": {"critical": "polite", "polarity": "affirmative", "speech_act": "request/command",
                  "agent": "addressee", "certainty": "n/a (question/request)",
                  "politeness": "please", "added_content": "no"},
     "feedback": "Both 'could you' and 'please' are present. For the general politeness question "
                 "pick the highest: please."},
    {"item_id": "practice-5", "text": "Let's go to the park later.",
     "dimension": "time_quantity", "critical_options": ["past", "now", "later", "unclear/mixed"],
     "input_text": "Keywords: go park",
     "expected": {"critical": "later", "polarity": "affirmative", "speech_act": "offer/suggestion",
                  "agent": "we/joint", "certainty": "plain assertion", "politeness": "none",
                  "added_content": "yes"},
     "feedback": "'Let's' is a suggestion done together (we/joint). 'later' places it in the "
                 "future and is not in the input words, so added content = yes."},
]


def _item_id(row: dict) -> str:
    return "g-" + hashlib.sha1(json.dumps([row["text_id"], row["family_id"], row["input_text"]])
                               .encode()).hexdigest()[:10]


def solve_pi(w: list[float], n: float) -> list[float]:
    """pi_i = min(1, c*w_i) with sum(pi) = n (bisection on c)."""
    if n >= len(w):
        return [1.0] * len(w)
    lo, hi = 0.0, 1.0
    while sum(min(1.0, hi * x) for x in w) < n:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if sum(min(1.0, mid * x) for x in w) < n:
            lo = mid
        else:
            hi = mid
    return [min(1.0, hi * x) for x in w]


def positives(run_dir: Path) -> dict[tuple, bool]:
    p = run_dir / "scored.parquet"
    if not p.exists():
        return {}
    import pandas as pd
    df = pd.read_parquet(p)
    df = df[df["judged"]]
    flag = (df["violation"].fillna(False).astype(bool) | df["assumption"].fillna(False).astype(bool)
            | df["any_stance_addition"].fillna(False).astype(bool) | (df["added_content"] == "yes"))
    df = df.assign(_pos=flag)
    return df.groupby(["text_id", "family_id", "input_text"])["_pos"].any().to_dict()


def item_for_annotator(u: dict) -> dict:
    """Only what annotators may see: sentence, questions, options; input for added_content."""
    return {"item_id": u["item_id"], "text": u["text"],
            "critical": {"dimension": u["dimension"],
                         "question": critical_question(u["dimension"], u["critical_options"]),
                         "options": u["critical_options"]},
            "input_text": u["input_text"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=160)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    run_dir = Path(a.run) if Path(a.run).exists() else ROOT / "runs" / a.run
    run = run_dir.name
    judg = runio.read_jsonl(run_dir / "judgments.jsonl")
    occ = runio.load_occurrences(run_dir)
    models: dict[str, set] = {}
    for o in occ:
        models.setdefault(o["text_id"], set()).add(o["model"])
    pos = positives(run_dir)

    units = []
    for j in judg:
        dis = any(j.get(f"J1_{d}") != j.get(f"J2_{d}") for d in JUDGED_DIMS)
        k = (j["text_id"], j["family_id"], j["input_text"])
        m = sorted(models.get(j["text_id"], {"?"}))
        crit = j["critical"] if j.get("critical") is not None else "DISAGREE"
        units.append({**j, "item_id": _item_id(j), "model": m[0], "models": "|".join(m),
                      "disagree": dis, "positive": bool(pos.get(k, False)),
                      "stratum": f"{j['dimension']}|{m[0]}|{crit}"})
    size: dict[str, int] = {}
    for u in units:
        size[u["stratum"]] = size.get(u["stratum"], 0) + 1
    w = [(1 + 3 * u["disagree"] + 2 * u["positive"]) / math.sqrt(size[u["stratum"]])
         for u in units]
    pis = solve_pi(w, a.n)
    rng = random.Random(a.seed)
    chosen = []
    for u, pi in zip(units, pis):
        u["pi"] = pi
        if rng.random() < pi:
            chosen.append(u)
    rng.shuffle(chosen)   # presentation order: random, not grouped by stratum

    out_dir = ROOT / "annotation"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "run": run, "codebook_version": CODEBOOK_VERSION, "seed": a.seed,
        "general_dims": [{"name": d, "definition": DEFINITIONS[d], "options": GENERAL_OPTIONS[d]}
                         for d in GENERAL_DIMS],
        "added_content": {"definition": DEFINITIONS["added_content"],
                          "options": ADDED_CONTENT_OPTIONS},
        "practice": [{**item_for_annotator(p), "expected": p["expected"], "feedback": p["feedback"]}
                     for p in (dict(p, item_id=p["item_id"]) for p in PRACTICE)],
        "items": [item_for_annotator(u) for u in chosen],
    }
    (out_dir / f"gold_items_{run}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    key_cols = (["item_id", "text_id", "family_id", "dimension", "input_text", "text", "models",
                 "stratum", "disagree", "positive", "pi"]
                + [f"{v}_{d}" for v in ("J1", "J2") for d in JUDGED_DIMS]
                + JUDGED_DIMS + [f"L0_{d}" for d in GENERAL_DIMS])
    with (out_dir / f"gold_key_{run}.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=key_cols, extrasaction="ignore")
        wr.writeheader()
        for u in chosen:
            wr.writerow({k: u.get(k) for k in key_cols})
    n_dis = sum(u["disagree"] for u in chosen)
    n_pos = sum(u["positive"] for u in chosen)
    print(f"{len(units)} units, {len(size)} strata -> sampled {len(chosen)} (target {a.n}); "
          f"{n_dis} with J1/J2 disagreement, {n_pos} positives; pi range "
          f"[{min(pis):.4f}, {max(pis):.3f}]")
    print(f"wrote annotation/gold_items_{run}.json and annotation/gold_key_{run}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
