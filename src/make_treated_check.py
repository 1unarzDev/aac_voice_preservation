"""Part 20: human label check on treated outputs (is the judge right where the headline claims rest?). 0 generation, 0 judge calls.

Why: the papers' headline numbers (guard repair rates, chip and plain-word gains, the new-model and Gemini replications)
are read through the automatic judges. Human gold (Parts 10/12/13) covered the original runs. Part 20 asks people to label
real outputs of the treated arms and of the later runs, so judge validity can be reported where the claims rest.

Items (120 = 6 classes x 20; seeded, declared; seed 20261102). One item = ONE real output occurrence (a sentence that a
model really produced in one run, family, variant and channel); the same sentence is never shown twice.
  G1       guard repairs: outputs of prompt G1 that the guard CHANGED   (runs/guard1 discovery, runs/guard_wc W-C)
  G1r      no-feedback retries: prompt G1r outputs that CHANGED         (runs/guard_baseline_disc, guard_baseline_wc)
  chip1    outputs under channel chip1 (one chip)                        (runs/hw1, prompt P0, four models)
  nlcue    outputs under channel nlcue (the cue as a plain word)         (runs/hwctl1, prompt P0, four models)
  newmodel Qwen2.5-14B and Mistral-Nemo-12B, channels chip1 and bare     (runs/ext_hw_qwen14, runs/ext_hw_nemo)
  gemini   gemini-3.1-flash-lite outputs                                 (runs/gem_31-flash-lite_{legend,hwctl,hw})
Frame of a class: judged, valid outputs with a production critical label (arbiter where the judges disagreed; rows with
an unresolved disagreement are not in the frame), of families not quarantined, minus the exclusions below.
Allocation: 20 per class spread EQUALLY over the dimensions present in the class frame (round robin, order rotated by
hash, capped by availability; newmodel: 10 per model); inside a dimension, units are taken in ascending
sha1(seed | class | output_id | family | channel) order, but always from the least-used run/model/channel/prompt cell
first, so the class is also spread over models and channels. The key records the stratum size and the draw size per
class x dimension (weight = frame size / drawn), so a class result can be re-weighted over its dimensions.
Exclusions (frame level): a sentence (normalised text, any dimension) already labelled by people in Parts 1-3/10/12/13
(annotation/gold_key_*.csv), used in Part 19 (arbiter_check_key.csv), or shown in the sentence audits of Parts 4/11/17/18
(Stage 4 has returned, so those keys are known); an output whose text is arm-revealing (square
brackets, "keywords", chip/guard/feedback wording, model or vendor names, assistant boilerplate); a sentence already drawn
for another class. Coder level (assignment): never a person who WROTE or CHECKED the pair (hw: writer_id, check_key.csv
incl. tie-breaks) or chose the keywords of the message (same rule and code as Part 19).
Tool: annotation_package/annotate.html with a part file (same as Parts 10/12/13/19): the output sentence and the critical
question; the visible input only for the last question (added content). Run tag part20 -> labels_part20_<ID>.csv
(returns -> annotation/returns_treated_check/). Practice: the standard five items.
Assignment: 2 independent coders per item from the 20 annotators (12 items each), the Part 19 assignment code.

Writes:
  annotation_package/stage5/<ID>_part20.json    blind part file per person (5 practice items + the person's 12 items)
  annotation/treated_check_key.csv              private: class, run, model, channel, judge labels (+J1/J2 critical), weights, coders
  annotation/treated_check_sample.json          rule, seed, frame sizes, exclusions, composition, loads, key hash
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_arbiter_check as MC  # noqa: E402
import make_gold as G  # noqa: E402
import runio  # noqa: E402
from explode import normalise  # noqa: E402

SEED = 20261102
RUN_TAG = "part20"
CLASSES = ["G1", "G1r", "chip1", "nlcue", "newmodel", "gemini"]
PER_CLASS = 20
PER_ITEM = 2
OUT_DIR = ROOT / "annotation_package" / "stage5"
KEY = ROOT / "annotation" / "treated_check_key.csv"
SUMMARY = ROOT / "annotation" / "treated_check_sample.json"
LABEL_COLS = ["critical", "polarity", "speech_act", "agent", "certainty", "politeness", "added_content"]
DIM_ORDER = ["polarity", "speech_act", "politeness", "certainty", "agent", "time_quantity"]

ARM_REVEALING = re.compile(
    r"[\[\]{}<>]|keywords?\b|\bchips?\b|\bguard\b|\bfeedback\b|your sentence|must keep|\bG1r?s?\b|\bP0m?\b|legend|"
    r"\b(?:gemma|llama|qwen|mistral|nemo|gemini|gpt|openai|claude|anthropic|terra|sol)\b|"
    r"\b(?:as an ai|language model|here is|here's|sure, here|output:|sentence:)\b", re.I)


def h(*parts) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()


# ------------------------------------------------------------------ frames (one DataFrame per class)
def _std(df, run=None, prompt_col="prompt_id"):
    """Normalise a scored table to the columns the key needs."""
    import pandas as pd
    df = df.copy()
    if "crit" in df.columns and "critical" not in df.columns:
        df["critical"] = df["crit"]
    if "label_source" in df.columns and "critical_source" not in df.columns:
        df["critical_source"] = df["label_source"]
    if run is not None:
        df["run"] = run
    df["added_content"] = df["added_content"].map(lambda v: "yes" if v is True or v == "yes" else ("no" if v is False or v == "no" else None))
    for c in ("constraint_preserving", "violation", "assumption"):
        if c not in df.columns:
            df[c] = None
    return df


def class_frames() -> dict:
    import pandas as pd
    out = {}
    cols = ["output_id", "text_id", "run", "model", "prompt_id", "channel", "family_id", "variant", "dimension", "input_text", "text",
            "valid", "judged", "critical", "critical_J1", "critical_J2", "critical_source"] + LABEL_COLS[1:] + \
           ["violation", "constraint_preserving", "assumption", "changed"]

    def load(path, run=None):
        df = _std(pd.read_parquet(path), run)
        for c in cols:
            if c not in df.columns:
                df[c] = None
        return df[cols]

    # guard: G1 repairs / G1r retries that changed the sentence (analysis/guard_baseline holds all arms of both sets, with labels)
    srcs = {"disc": ("guard1", "guard_baseline_disc"), "wc": ("guard_wc", "guard_baseline_wc")}
    g1, g1r = [], []
    for s, (r1, rr) in srcs.items():
        df = load(ROOT / f"analysis/guard_baseline/scored_{s}.parquet")
        df = df[df.changed.fillna(False).astype(bool)]
        g1.append(df[df.prompt_id == "G1"].assign(run=r1))
        g1r.append(df[df.prompt_id == "G1r"].assign(run=rr))
    out["G1"], out["G1r"] = pd.concat(g1), pd.concat(g1r)
    hw = load(ROOT / "runs/hw1/scored.parquet", "hw1")
    out["chip1"] = hw[(hw.channel == "chip1") & (hw.prompt_id == "P0")]
    hc = load(ROOT / "runs/hwctl1/scored.parquet", "hwctl1")
    out["nlcue"] = hc[(hc.channel == "nlcue") & (hc.prompt_id == "P0")]
    nm = pd.concat([load(ROOT / f"runs/{r}/scored.parquet", r) for r in ("ext_hw_qwen14", "ext_hw_nemo")])
    out["newmodel"] = nm[nm.channel.isin(["chip1", "bare"]) & (nm.prompt_id == "P0")]
    gm = pd.concat([load(ROOT / f"runs/{r}/scored.parquet", r) for r in
                    ("gem_31-flash-lite_legend", "gem_31-flash-lite_hwctl", "gem_31-flash-lite_hw")])
    out["gemini"] = gm[gm.channel != "irrel"]          # irrelevant-chip rows are the control arm of hwctl
    return out


def labelled_texts() -> set:
    """Normalised texts people already labelled (Parts 1-3, 10, 12, 13), saw in Part 19, or rated/read in the Stage 1-4 sentence
    audits (Parts 4, 11, 17: usable-or-not ratings; Part 18: writers' intent), so no coder meets a sentence twice."""
    out = set()
    files = sorted((ROOT / "annotation").glob("gold_key_*.csv")) + [ROOT / "annotation" / n for n in (
        "arbiter_check_key.csv", "repair_audit_key.csv", "repair_audit_transfer_key.csv", "repair_audit_v2_key.csv", "intent_check_key.csv")]
    for p in files:
        if p.exists():
            with open(p, newline="", encoding="utf-8") as fh:
                out |= {normalise(r["text"]) for r in csv.DictReader(fh) if r.get("text")}
    return out


def frame_units(frames: dict, items: dict, labelled: set):
    from attribute import quarantined
    units, why = {}, defaultdict(Counter)
    for cls in CLASSES:
        df = frames[cls]
        seen = set()
        for r in df.itertuples(index=False):
            w = why[cls]
            if not (bool(r.judged) and bool(r.valid)):
                w["not judged / invalid"] += 1; continue
            if r.critical is None or (isinstance(r.critical, float)) or not str(r.critical):
                w["no production critical label (unresolved)"] += 1; continue
            if not isinstance(r.text, str) or not r.text.strip():
                w["empty text"] += 1; continue
            if r.family_id not in items:
                w["family not in data/items"] += 1; continue
            if quarantined(items[r.family_id]):
                w["quarantined family"] += 1; continue
            n = normalise(r.text)
            if n in labelled:
                w["already labelled or shown to people (Parts 1-3/4/10-13/17-19)"] += 1; continue
            if ARM_REVEALING.search(r.text):
                w["arm-revealing text"] += 1; continue
            if r.critical not in items[r.family_id]["critical_options"]:
                w["critical label not an option"] += 1; continue
            if (n, r.family_id, r.variant, r.channel, r.model) in seen:
                w["same sentence twice in class"] += 1; continue
            seen.add((n, r.family_id, r.variant, r.channel, r.model))
            units.setdefault(cls, []).append({
                "class": cls, "run": r.run, "model": r.model, "prompt_id": r.prompt_id, "channel": r.channel,
                "dimension": r.dimension, "family_id": r.family_id, "families": r.family_id, "variant": r.variant,
                "output_id": r.output_id, "text_id": r.text_id, "input_text": r.input_text, "text": r.text, "norm": n,
                "critical_options": items[r.family_id]["critical_options"], "critical_source": r.critical_source,
                "J1_critical": r.critical_J1, "J2_critical": r.critical_J2,
                **{c: getattr(r, c) for c in LABEL_COLS},
                **{c: (None if getattr(r, c) is None or getattr(r, c) != getattr(r, c) else getattr(r, c))
                   for c in ("violation", "constraint_preserving", "assumption")}})
    return units, why


# ------------------------------------------------------------------ draw
def order_key(u):
    return h(SEED, u["class"], u["output_id"], u["family_id"], u["channel"])


def equal_alloc(counts: dict, n: int) -> dict:
    """n spread as equally as possible over the groups, capped by availability; ties rotate by hash."""
    keys = sorted((k for k in counts if counts[k] > 0), key=lambda k: h(SEED, "dim-order", k))
    a = {k: 0 for k in counts}
    n = min(n, sum(counts[k] for k in keys))
    while sum(a.values()) < n:
        for k in keys:
            if sum(a.values()) >= n:
                break
            if a[k] < counts[k]:
                a[k] += 1
    return a


def cell_of(u):
    return (u["run"], u["model"], u["channel"], u["prompt_id"])


def pick(pool: list, k: int, used: Counter, forbid: set) -> list:
    """k units from pool: always from the least-used cell, hash order inside a cell; a sentence in `forbid` is skipped
    and every unit taken is added to it (so no sentence is drawn twice)."""
    pool = sorted((u for u in pool if u["norm"] not in forbid), key=order_key)
    out = []
    while len(out) < k and pool:
        u = min(pool, key=lambda u: (used[cell_of(u)], order_key(u)))
        pool = [x for x in pool if x is not u and x["norm"] != u["norm"]]
        out.append(u); used[cell_of(u)] += 1; forbid.add(u["norm"])
    return out


def draw_class(cls: str, frame: list, taken_norm: set) -> tuple[list, dict]:
    if cls == "newmodel":
        parts = [("ext_hw_qwen14", PER_CLASS // 2), ("ext_hw_nemo", PER_CLASS - PER_CLASS // 2)]
    else:
        parts = [(None, PER_CLASS)]
    chosen, strata = [], {}
    used, forbid = Counter(), set(taken_norm)
    for run, n in parts:
        sub = [u for u in frame if run is None or u["run"] == run]
        counts = Counter(u["dimension"] for u in sub if u["norm"] not in taken_norm)
        alloc = equal_alloc(dict(counts), n)
        for d in sorted(counts, key=lambda d: DIM_ORDER.index(d) if d in DIM_ORDER else 99):
            pool = [u for u in sub if u["dimension"] == d]
            got = pick(pool, alloc[d], used, forbid)
            chosen += got
            strata[f"{run or cls}|{d}"] = {"frame_n": counts[d], "drawn": len(got)}
        short = n - sum(1 for u in chosen if run is None or u["run"] == run)
        while short > 0:                   # duplicate sentences made a dimension run dry: top up round robin
            before = short
            for d in sorted(counts, key=lambda d: h(SEED, "topup", d)):
                if short <= 0:
                    break
                got = pick([u for u in sub if u["dimension"] == d], 1, used, forbid)
                if got:
                    chosen += got; short -= 1; strata[f"{run or cls}|{d}"]["drawn"] += 1
            if short == before:
                break
    for u in chosen:
        s = strata[f"{(u['run'] if cls == 'newmodel' else cls)}|{u['dimension']}"]
        u["stratum"] = f"{cls}|{u['dimension']}" + (f"|{u['run']}" if cls == "newmodel" else "")
        u["frame_n"], u["drawn_n"] = s["frame_n"], s["drawn"]
        u["weight"] = round(s["frame_n"] / s["drawn"], 4) if s["drawn"] else None
    assert len(chosen) == PER_CLASS, (cls, len(chosen), strata)
    return chosen, strata


def item_id(u) -> str:
    return "p20-" + h("part20-item", u["class"], u["norm"], u["family_id"], u["variant"], u["channel"], u["model"])[:8]


# ------------------------------------------------------------------ outputs
KEY_COLS = ["item_id", "class", "run", "model", "prompt_id", "channel", "dimension", "family_id", "variant", "output_id", "text_id",
            "input_text", "text", "critical_options", "critical_source", "J1_critical", "J2_critical"] + LABEL_COLS + \
           ["violation", "constraint_preserving", "assumption", "stratum", "frame_n", "drawn_n", "weight", "coders", "blocked_people"]


def part_payload(its: list[dict]) -> dict:
    from labels import ADDED_CONTENT_OPTIONS, DEFINITIONS, GENERAL_DIMS, GENERAL_OPTIONS
    return {"run": RUN_TAG, "codebook_version": G.CODEBOOK_VERSION,
            "general_dims": [{"name": d, "definition": DEFINITIONS[d], "options": GENERAL_OPTIONS[d]} for d in GENERAL_DIMS],
            "added_content": {"definition": DEFINITIONS["added_content"], "options": ADDED_CONTENT_OPTIONS},
            "practice": [{**G.item_for_annotator(p), "expected": p["expected"], "feedback": p["feedback"]} for p in G.PRACTICE],
            "items": [G.item_for_annotator(u) for u in its], "part": RUN_TAG}


def load_all_items() -> dict:
    """data/items plus the hw candidates (hw1 was generated and judged on all of them, D-052)."""
    items = runio.load_items()
    cand = ROOT / "annotation" / "written" / "hw_candidates.jsonl"
    if cand.exists():
        for fid, it in runio.load_items(cand).items():
            items.setdefault(fid, it)
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--annotators", default="", help="default: annotators of annotation/assignments/plan.json")
    ap.add_argument("--out-dir", default=str(OUT_DIR)); ap.add_argument("--key", default=str(KEY))
    ap.add_argument("--summary", default=str(SUMMARY))
    ap.add_argument("--force", action="store_true", help="overwrite an existing key (the frame of the Gemini and guard-baseline runs "
                    "grows, so a re-draw would give different items)")
    a = ap.parse_args(argv)
    if Path(a.key).exists() and not a.force:
        print(f"{a.key} exists and is frozen; pass --force to redraw (the Gemini frame has grown since)", file=sys.stderr)
        return 2
    ids = [x for x in a.annotators.split(",") if x] or json.loads((ROOT / "annotation/assignments/plan.json").read_text())["annotators"]
    items = load_all_items()
    frames = class_frames()
    units, why = frame_units(frames, items, labelled_texts())
    taken, chosen, strata_all = set(), [], {}
    for cls in CLASSES:                                  # fixed class order: later classes never reuse an earlier sentence
        got, st = draw_class(cls, units[cls], taken)
        taken |= {u["norm"] for u in got}
        chosen += got; strata_all[cls] = st
    for u in chosen:
        u["item_id"] = item_id(u)
    assert len(chosen) == PER_CLASS * len(CLASSES) and len({u["item_id"] for u in chosen}) == len(chosen)
    assert len({u["norm"] for u in chosen}) == len(chosen), "same sentence twice"
    blocked = MC.blocked_people(items, ids)
    # MC.assign hashes on run/text_id/family_id; text_id is shared by occurrences, so make the hash unique per item
    for u in chosen:
        u["_tid"], u["text_id"] = u["text_id"], u["item_id"]
    load = MC.assign(chosen, ids, blocked)
    for u in chosen:
        u["text_id"] = u.pop("_tid")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*_part20.json"):
        old.unlink()
    per = defaultdict(list)
    for u in sorted(chosen, key=lambda u: u["item_id"]):
        for c in u["coders"]:
            per[c].append(u)
    for c in ids:
        mine = sorted(per[c], key=lambda u: h(SEED, "present", c, u["item_id"]))
        (out / f"{c}_part20.json").write_text(json.dumps(part_payload(mine), indent=1, ensure_ascii=False))
    with open(a.key, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEY_COLS); w.writeheader()
        for u in sorted(chosen, key=lambda u: (CLASSES.index(u["class"]), u["item_id"])):
            row = {c: u.get(c) for c in KEY_COLS if c not in ("critical_options", "coders", "blocked_people")}
            row |= {"critical_options": "|".join(u["critical_options"]), "coders": "|".join(sorted(u["coders"])),
                    "blocked_people": "|".join(sorted(u["blocked"]))}
            w.writerow({k: ("" if v is None else v) for k, v in row.items()})
    comp = {cls: {"n": sum(u["class"] == cls for u in chosen),
                  "by_dimension": dict(sorted(Counter(u["dimension"] for u in chosen if u["class"] == cls).items())),
                  "by_run": dict(sorted(Counter(u["run"] for u in chosen if u["class"] == cls).items())),
                  "by_model": dict(sorted(Counter(u["model"] for u in chosen if u["class"] == cls).items())),
                  "by_channel": dict(sorted(Counter(u["channel"] for u in chosen if u["class"] == cls).items())),
                  "by_judge_critical_source": dict(sorted(Counter(u["critical_source"] for u in chosen if u["class"] == cls).items()))}
            for cls in CLASSES}
    summ = {"seed": SEED, "rule": __doc__.split("Items (120")[1].split("Tool:")[0].strip(), "annotators": ids, "per_item": PER_ITEM,
            "frame_sizes_after_exclusions": {c: len(units[c]) for c in CLASSES},
            "frame_exclusions": {c: dict(why[c]) for c in CLASSES}, "strata": strata_all, "composition": comp,
            "codings": sum(len(u["coders"]) for u in chosen), "items_per_person": dict(sorted(load.items())),
            "min_max_items_per_person": [min(load.values()), max(load.values())],
            "note": "Gemini and guard-baseline runs were still accumulating when the frame was drawn; the key stores the text, so the draw is frozen.",
            "key_sha256": hashlib.sha256(Path(a.key).read_bytes()).hexdigest()}
    Path(a.summary).write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps({k: summ[k] for k in ("frame_sizes_after_exclusions", "composition", "codings", "items_per_person")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
