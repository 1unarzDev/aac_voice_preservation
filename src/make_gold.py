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

Multi-run mode (B3, expanded gold on new outputs)
  python src/make_gold.py --runs r2c1:60,r2d1:45,guard_wc:45 --name new \
      --exclude-families r2act-078,r2act-079 \
      --part-out annotation_package/part10_gold_new.json
  unit     one extraction unit (exact text, family dimension, visible input) per run, built
           (normalised text as in explode.py) from runs/<run>/scored.parquet (production labels: the arbitrated critical label,
           critical_source kept) joined to judgments.jsonl (J1/J2/L0). Families that share
           a unit (W-D pol-i/pol-you) are collapsed; all memberships are kept in the key.
           guard_wc contributes only guard outputs (G1/G1s) whose unit was not already
           judged in r2c1 (repaired and please-stripped texts); its first passes ARE r2c1
           units. Excluded: --exclude-families (D-018) and refusal/acceptance quarantine
           families (attribute.quarantined; none in these runs).
  strata   run x dimension x production critical label ('DISAGREE' if J1 != J2 critical).
  weights  as above within each run; pi solved per run so sum(pi) = that run's allocation.
  outputs  <part-out> (annotate.html part file, neutral ids), annotation/gold_key_<name>.csv
           (run, families, models, channels, prompts, judge labels, pi), and
           annotation/gold_sample_<name>.json (frozen design + realised composition).
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


def build_units_multi(runs: list[str], exclude: set[str], run_dirs: dict | None = None,
                      items: dict | None = None) -> list[dict]:
    """Extraction units of several runs (see module docstring, multi-run mode).
    run_dirs / items override runs/<run> and data/items/*.jsonl (wrappers and tests)."""
    import pandas as pd
    from attribute import quarantined
    from explode import normalise
    items = items if items is not None else runio.load_items()
    seen: set[tuple] = set()
    units: list[dict] = []
    for run in runs:
        run_dir = Path((run_dirs or {}).get(run) or ROOT / "runs" / run)
        sc = pd.read_parquet(run_dir / "scored.parquet")
        sc = sc[sc.judged & sc.valid.fillna(False).astype(bool) & ~sc.family_id.isin(exclude)]
        sc = sc[~sc.family_id.map(lambda f: quarantined(items[f]))]
        if run == "guard_wc":
            sc = sc[sc.prompt_id.isin(["G1", "G1s"])]
            ch_p = ROOT / "analysis/guard_wc/scored.parquet"
            if ch_p.exists():
                ch = pd.read_parquet(ch_p, columns=["output_id", "prompt_id", "changed"])
                chg = {(o, p): bool(c) for o, p, c in ch.itertuples(index=False) if c is not None}
                sc = sc.assign(gchanged=[chg.get((o, p)) for o, p in zip(sc.output_id, sc.prompt_id)])
        judg = {(j["text_id"], j["family_id"], j["input_text"]): j
                for j in runio.read_jsonl(run_dir / "judgments.jsonl")}
        sc = sc.assign(gpos=(sc["violation"].fillna(False).astype(bool)
                             | sc["assumption"].fillna(False).astype(bool)
                             | sc["any_stance_addition"].fillna(False).astype(bool)
                             | (sc["added_content"] == "yes")))
        run_units: dict[tuple, dict] = {}
        for r in sc.itertuples(index=False):
            k = (normalise(r.text), r.dimension, r.input_text)
            if k in seen:          # already a unit of an earlier run (guard first passes)
                continue
            u = run_units.get(k)
            if u is None:
                u = run_units[k] = {"run": run, "dimension": r.dimension,
                                    "input_text": r.input_text, "jrows": {}, "families": set(),
                                    "models": set(), "channels": set(), "prompts": set(),
                                    "variants": set(), "text_ids": set(), "output_ids": set(),
                                    "positive": False, "crit": set(), "crit_src": set(),
                                    "guard_changed": set(), "n_occ": 0}
            u["families"].add(r.family_id); u["models"].add(r.model); u["channels"].add(r.channel)
            u["prompts"].add(r.prompt_id); u["variants"].add(f"{r.family_id}:{r.variant}")
            u["text_ids"].add(r.text_id); u["output_ids"].add(r.output_id); u["n_occ"] += 1
            u["positive"] |= bool(r.gpos)
            u["crit"].add(r.critical); u["crit_src"].add(r.critical_source)
            if run == "guard_wc" and getattr(r, "gchanged", None) is not None:
                u["guard_changed"].add(f"{r.prompt_id}:{r.gchanged}")
            jk = (r.text_id, r.family_id, r.input_text)
            u["jrows"].setdefault(jk, judg[jk])
        for k, u in sorted(run_units.items()):
            assert len(u["crit"]) == 1, (run, k, u["crit"])     # production label is unit-level
            jr = [u["jrows"][x] for x in sorted(u["jrows"])]
            j = jr[0]
            for x in jr[1:]:   # collapsed families must carry identical judge labels
                assert all(x.get(f"{v}_{d}") == j.get(f"{v}_{d}") for v in ("J1", "J2")
                           for d in JUDGED_DIMS), (run, k)
            fam = sorted(u["families"])[0]
            m = sorted(u["models"])
            crit = next(iter(u["crit"]))
            jcrit_dis = j.get("J1_critical") != j.get("J2_critical")
            units.append({
                **{c: j.get(c) for c in j if c[:3] in ("J1_", "J2_", "L0_")},
                **{d: j.get(d) for d in GENERAL_DIMS + ["added_content"]},
                "critical": crit, "critical_source": "|".join(sorted(map(str, u["crit_src"]))),
                "run": run, "text": j["text"], "norm_text": k[0], "dimension": u["dimension"], "input_text": u["input_text"],
                "family_id": fam, "families": "|".join(sorted(u["families"])),
                "critical_options": items[fam]["critical_options"],
                "text_id": sorted(u["text_ids"])[0], "text_ids": "|".join(sorted(u["text_ids"])),
                "model": m[0], "models": "|".join(m), "channels": "|".join(sorted(u["channels"])),
                "prompts": "|".join(sorted(u["prompts"])), "variants": "|".join(sorted(u["variants"])),
                "guard_changed": "|".join(sorted(u["guard_changed"])), "n_occurrences": u["n_occ"],
                "output_ids": "|".join(sorted(u["output_ids"])),
                "disagree": any(j.get(f"J1_{d}") != j.get(f"J2_{d}") for d in JUDGED_DIMS),
                "positive": u["positive"],
                "stratum": f"{run}|{u['dimension']}|{'DISAGREE' if jcrit_dis else crit}"})
            seen.add(k)
    return units


def main_multi(a) -> int:
    alloc = {}
    for part in a.runs.split(","):
        r, n = part.split(":")
        alloc[r] = int(n)
    exclude = set(filter(None, (a.exclude_families or "").split(",")))
    units = build_units_multi(list(alloc), exclude)
    size: dict[str, int] = {}
    for u in units:
        size[u["stratum"]] = size.get(u["stratum"], 0) + 1
    for run, n in alloc.items():
        ru = [u for u in units if u["run"] == run]
        w = [(1 + 3 * u["disagree"] + 2 * u["positive"]) / math.sqrt(size[u["stratum"]]) for u in ru]
        for u, pi in zip(ru, solve_pi(w, n)):
            u["pi"] = pi
    # frozen draw: units in a fixed hash order, one seeded uniform each
    order = sorted(units, key=lambda u: hashlib.sha1(json.dumps(
        [a.name, u["run"], u["norm_text"], u["dimension"], u["input_text"]]).encode()).hexdigest())
    rng = random.Random(a.seed)
    chosen = [u for u in order if rng.random() < u["pi"]]
    for u in chosen:
        u["item_id"] = "g-" + hashlib.sha1(json.dumps(
            [a.name, u["run"], u["norm_text"], u["dimension"], u["input_text"]]).encode()).hexdigest()[:10]
    assert len({u["item_id"] for u in chosen}) == len(chosen)
    rng.shuffle(chosen)   # presentation order: random, not grouped by run/stratum

    payload = {
        "run": f"gold_{a.name}", "codebook_version": CODEBOOK_VERSION,
        "general_dims": [{"name": d, "definition": DEFINITIONS[d], "options": GENERAL_OPTIONS[d]}
                         for d in GENERAL_DIMS],
        "added_content": {"definition": DEFINITIONS["added_content"],
                          "options": ADDED_CONTENT_OPTIONS},
        "practice": [{**item_for_annotator(p), "expected": p["expected"],
                      "feedback": p["feedback"]} for p in PRACTICE],
        "items": [item_for_annotator(u) for u in chosen],
        "part": f"gold_{a.name}",
    }
    part_out = Path(a.part_out) if a.part_out else ROOT / f"annotation/gold_items_{a.name}.json"
    part_out.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    key_cols = (["item_id", "run", "text_id", "family_id", "families", "dimension", "input_text", "text",
                 "model", "models", "channels", "prompts", "variants", "guard_changed", "n_occurrences",
                 "stratum", "disagree", "positive", "pi", "critical_source"]
                + [f"{v}_{d}" for v in ("J1", "J2") for d in JUDGED_DIMS]
                + JUDGED_DIMS + [f"L0_{d}" for d in GENERAL_DIMS] + ["text_ids", "output_ids"])
    key_p = ROOT / f"annotation/gold_key_{a.name}.csv"
    with key_p.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=key_cols, extrasaction="ignore")
        wr.writeheader()
        for u in sorted(chosen, key=lambda u: u["item_id"]):
            wr.writerow({k: u.get(k) for k in key_cols})

    from collections import Counter
    def comp(us):
        return {"n": len(us), "disagree": sum(u["disagree"] for u in us),
                "positive": sum(u["positive"] for u in us),
                "by_dimension": dict(sorted(Counter(u["dimension"] for u in us).items())),
                "by_model": dict(sorted(Counter(u["model"] for u in us).items())),
                "by_stratum": dict(sorted(Counter(u["stratum"] for u in us).items()))}
    summ = {"name": a.name, "seed": a.seed, "allocation": alloc, "excluded_families": sorted(exclude),
            "design": "Poisson PPS within run; w=(1+3*J1/J2 disagreement+2*positive)/sqrt(stratum size); "
                      "strata run x dimension x production critical label (DISAGREE if J1!=J2 critical); "
                      "fixed sha1 unit order, one seeded uniform per unit",
            "texts_duplicated_in_sample": sum(v > 1 for v in Counter(u["norm_text"] for u in chosen).values()),
            "runs": {}}
    for run in alloc:
        ru = [u for u in units if u["run"] == run]
        cu = [u for u in chosen if u["run"] == run]
        summ["runs"][run] = {"population": comp(ru), "sample": comp(cu),
                             "expected_n": round(sum(u["pi"] for u in ru), 2),
                             "pi_range": [round(min(u["pi"] for u in ru), 5), round(max(u["pi"] for u in ru), 4)],
                             "sample_by_prompt": dict(sorted(Counter(u["prompts"] for u in cu).items())),
                             "sample_by_channel": dict(sorted(Counter(u["channels"] for u in cu).items())),
                             "sample_guard_changed": dict(sorted(Counter(u["guard_changed"] for u in cu).items()))}
    summ["sample_total"] = len(chosen)
    summ["key_sha256"] = hashlib.sha256(key_p.read_bytes()).hexdigest()
    summ["part_sha256"] = hashlib.sha256(part_out.read_bytes()).hexdigest()
    (ROOT / f"annotation/gold_sample_{a.name}.json").write_text(json.dumps(summ, indent=1) + "\n")
    for run, x in summ["runs"].items():
        print(f"{run}: population {x['population']['n']} units -> sampled {x['sample']['n']} "
              f"(expected {x['expected_n']}); disagree {x['sample']['disagree']}, positive "
              f"{x['sample']['positive']}; dims {x['sample']['by_dimension']}; models {x['sample']['by_model']}")
    print(f"total {len(chosen)}; wrote {part_out}, {key_p}, annotation/gold_sample_{a.name}.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run")
    ap.add_argument("--n", type=int, default=160)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--runs", help="multi-run mode: run:n,run:n,... (allocation per run)")
    ap.add_argument("--name", default="new", help="multi-run mode: key/part name")
    ap.add_argument("--exclude-families", default="", help="multi-run mode: comma-separated family ids")
    ap.add_argument("--part-out", default=None, help="multi-run mode: path of the annotate.html part file")
    a = ap.parse_args()
    if a.runs:
        return main_multi(a)
    if not a.run:
        ap.error("--run (or --runs) is required")
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
