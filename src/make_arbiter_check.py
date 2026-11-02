"""Part 19: human check of the arbiter's labels (and of the "Can you ...?" speech-act rule). 0 generation, 0 judge calls.

Why: the arbiter (a Claude subagent, blind to everything but the output text and the critical question) settled the
units on which the two judges disagreed, and in doing so added precedents the codebook does not state (D-055, D-057).
People who did not write or check the pair, and who see only the output sentence, label the same units; the scorer
(src/score_arbiter_check.py) reports human vs arbiter, human vs each judge, and how people code "Can you ...?".

Items (130; seeded, declared; seed 20261101):
  * 100 arbiter units, drawn from runs/r2c1, runs/hw1, runs/elic1 `arbiter.jsonl` (one unit = exact text x critical
    dimension x visible input). Frame: a unit already in a human gold file (Parts 10/12/13: annotation/gold_key_*.csv) is
    left out (people already labelled it); hw1 units of families not kept after Stage 2/3 are left out.
    Every unit is tagged with the arbiter precedent it used (TAG_RULES below, from the text, dimension, label and the
    arbiter's rationale). The draw is quota-based and oversamples the precedents: PRECEDENT_QUOTA per tag (spread over
    the runs that have the tag, roughly in proportion to the square root of its count, at least 1 per run), then the
    rest of the 100 from untagged ("other") units spread over run x dimension cells. Within a group, units are taken in
    ascending sha1(seed | run | text_id | family_id) order.
  * 30 "Can you ...?" / "Could you ...?" outputs: speech-act units of runs r2c1 (W-C, 15) and hw1 (15) whose output
    sentence contains "can you" or "could you" and ends with "?" (production label: request/command, from the judges
    when they agreed). In r2c1: 5 from typed inputs, 10 from keyword inputs. Same hash order. Not already in the 100.
The "Can you" items show the critical question without its two parenthetical examples ("'Can I ...?' is a question",
"'Can you ...?' is a request"), and Part 19's practice items 2 and 4 are replaced (the standard ones use "Can you" and
"Could you please"), so these items test the rule instead of reading it back. The tool's general speech-act question
(asked on every item) has no examples either; the scorer reports both.
Tool: annotation_package/annotate.html with a part file (same as Parts 10/12/13: the output sentence and the critical
question; the visible input only for the last question, added content). Run tag `part19`, so the CSV is
labels_part19_<ID>.csv (returns -> annotation/returns_arbiter_check/).

Assignment: 2 independent coders per item from the 20 annotators (about 13 items each). Never a person who WROTE or
CHECKED the pair (hw1: writer_id; check_key.csv check ids incl. tie-breaks), nor who chose the keywords of the message
(elic1: the annotators of the elicitation set, any replicate). Greedy hardest-item-first on the lowest current load,
then load-balancing swaps; coders of an item are always two different people.

Writes:
  annotation_package/stage4/<ID>_part19.json    blind part file per person (5 practice items + the person's items)
  annotation/arbiter_check_key.csv               private: arbiter label, J1, J2, production label, run, precedent tag, coders
  annotation/arbiter_check_sample.json           rule, seed, composition by run / dimension / tag, loads, exclusions
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_gold as G  # noqa: E402
import runio  # noqa: E402
from explode import normalise  # noqa: E402

SEED = 20261101
RUNS = ["r2c1", "hw1", "elic1"]
N_ARBITER, N_CANYOU = 100, 30
CAN_YOU_PER_RUN = {"r2c1": 15, "hw1": 15}
CAN_YOU_TYPED_R2C1 = 5
PER_ITEM = 2
OUT_DIR = ROOT / "annotation_package" / "stage4"
KEY = ROOT / "annotation" / "arbiter_check_key.csv"
SUMMARY = ROOT / "annotation" / "arbiter_check_sample.json"
RUN_TAG = "part19"

# precedent tag -> number of the 100 arbiter slots (capped by what exists; the remainder goes to "other")
PRECEDENT_QUOTA = {
    "no_time_word_unclear": 8, "vague_time_word_unclear": 7, "will_now": 3, "will_or_lets_later": 4,
    "sure_emphatic": 6, "maybe_hedged": 2, "certainty_on_request_unclear": 3,
    "hope_hedged": 6, "wonder_hedged": 3, "could_hedged": 2, "may_permission_plain": 3,
    "want_please_request": 6, "will_you_request": 4, "tell_you_to_request": 3, "ask_with_please": 2,
    "should_we_proposal": 2, "can_could_you": 2, "may_i_softener": 2, "would_softener": 2,
    "inanimate_third_party": 3, "negation_uncertainty_unclear": 3,
}


def tag_of(x: dict) -> str:
    """Which arbiter precedent a unit used (first matching rule). x has text, dimension, critical (arbiter), rationale."""
    t, d, c, r = x["text"].lower(), x["dimension"], x["critical"], (x.get("rationale") or "").lower()
    if d == "certainty":
        if re.search(r"\bhope\b", t) or "hope" in r:
            return "hope_hedged"
        if "wonder" in t or "wonder" in r:
            return "wonder_hedged"
        if re.search(r"\b(sure|certain|definitely)\b", t) and c.startswith("strongly"):
            return "sure_emphatic"
        if re.search(r"\bmay\b", t) and c == "plain assertion":
            return "may_permission_plain"
        if re.search(r"\bmaybe\b", t) and c.startswith("hedged"):
            return "maybe_hedged"
        if re.search(r"\bcould\b", t) and c.startswith("hedged"):
            return "could_hedged"
        if c == "unclear/mixed" and ("request" in r or "question" in r):
            return "certainty_on_request_unclear"
    elif d == "time_quantity":
        if c == "unclear/mixed":
            return "no_time_word_unclear" if "no time word" in r else "vague_time_word_unclear"
        if c == "now" and re.search(r"\bnow\b", t):
            return "will_now"
        if c == "later":
            return "will_or_lets_later"
    elif d == "speech_act":
        if c == "request/command" and "please" in t and re.search(r"\bi (want|need|would like)\b", t):
            return "want_please_request"
        if c == "request/command" and re.search(r"\bi('m| am)? tell(ing)? you to\b", t):
            return "tell_you_to_request"
        if c == "request/command" and re.search(r"\b(will|are) you (be )?(able to)?", t):
            return "will_you_request"
        if re.search(r"\b(can|could) you\b", t):
            return "can_could_you"
        if c == "request/command" and "please" in t:
            return "ask_with_please"
        if c.startswith("offer") and re.search(r"\bshould we\b|\bshall we\b|\blet's\b", t):
            return "should_we_proposal"
    elif d == "politeness" and c == "polite":
        if re.search(r"\bmay i\b", t):
            return "may_i_softener"
        if re.search(r"would .*if you could|would it be possible|i was wondering", t):
            return "would_softener"
    elif d == "agent" and c == "third party" and "inanimate" in r:
        return "inanimate_third_party"
    elif d == "polarity" and c == "unclear/mixed":
        return "negation_uncertainty_unclear"
    return "other"


def h(*parts) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()


# ------------------------------------------------------------------ frame
def gold_texts() -> set:
    """(normalised text, dimension) already labelled by people in Parts 10/12/13."""
    out = set()
    for f in ("gold_key_new.csv", "gold_key_elic.csv", "gold_key_hw.csv"):
        p = ROOT / "annotation" / f
        if p.exists():
            with open(p, newline="", encoding="utf-8") as fh:
                out |= {(normalise(r["text"]), r["dimension"]) for r in csv.DictReader(fh)}
    return out


def judge_labels(run: str) -> dict:
    return {(j["text_id"], j["family_id"], j["input_text"]): j for j in runio.read_jsonl(ROOT / "runs" / run / "judgments.jsonl")}


def arbiter_units(items: dict, gold: set):
    units, why = [], Counter()
    seen = set()
    for run in RUNS:
        jl = judge_labels(run)
        for x in runio.read_jsonl(ROOT / "runs" / run / "arbiter.jsonl"):
            fam = x["family_id"]
            if fam not in items:
                why["family not kept / not in data/items"] += 1; continue
            key = (normalise(x["text"]), x["dimension"])
            if key in gold:
                why["already labelled in Parts 10/12/13"] += 1; continue
            uk = (run, key, x["input_text"])
            if uk in seen:
                why["same unit twice"] += 1; continue
            seen.add(uk)
            j = jl[(x["text_id"], fam, x["input_text"])]
            opts = items[fam]["critical_options"]
            assert x["critical"] in opts, (run, fam, x["critical"])
            units.append({"source": "arbiter", "run": run, "text_id": x["text_id"], "family_id": fam, "families": fam,
                          "dimension": x["dimension"], "input_text": x["input_text"], "text": x["text"],
                          "critical_options": opts, "arbiter_label": x["critical"], "production_label": x["critical"],
                          "J1": j.get("J1_critical"), "J2": j.get("J2_critical"), "rationale": x.get("rationale", ""),
                          "tag": tag_of(x), "norm": key[0]})
    return units, why


def can_you_units(items: dict, gold: set, taken: set):
    import pandas as pd
    from attribute import quarantined
    pat = re.compile(r"\b(?:can|could) you\b", re.I)
    out, why = [], Counter()
    for run in CAN_YOU_PER_RUN:
        jl = judge_labels(run)
        sc = pd.read_parquet(ROOT / "runs" / run / "scored.parquet")
        sc = sc[sc.judged & sc.valid.fillna(False).astype(bool) & (sc.dimension == "speech_act")]
        sc = sc[sc.text.map(lambda t: bool(pat.search(t)) and t.strip().endswith("?"))]
        sc = sc[sc.family_id.isin(items)]
        sc = sc[~sc.family_id.map(lambda f: quarantined(items[f]))]
        seen = set()
        for r in sc.sort_values(["family_id", "text_id"]).itertuples(index=False):
            n = normalise(r.text)
            if (n, "speech_act") in gold or (n, "speech_act") in taken or (run, n, r.input_text) in seen:
                why["already used / labelled"] += 1; continue
            seen.add((run, n, r.input_text))
            j = jl[(r.text_id, r.family_id, r.input_text)]
            out.append({"source": "canyou", "run": run, "text_id": r.text_id, "family_id": r.family_id,
                        "families": r.family_id, "dimension": "speech_act", "input_text": r.input_text, "text": r.text,
                        "critical_options": items[r.family_id]["critical_options"], "arbiter_label": "",
                        "production_label": r.critical, "J1": j.get("J1_critical"), "J2": j.get("J2_critical"),
                        "rationale": "", "tag": "canyou_request", "norm": n,
                        "typed": r.input_text.startswith("The user typed")})
    return out, why


# ------------------------------------------------------------------ draws
def alloc_over(counts: dict, n: int) -> dict:
    """Spread n over groups ~ sqrt(count), at least 1 each when n allows, never above the count (largest remainder)."""
    keys = [k for k in counts if counts[k] > 0]
    if not keys or n <= 0:
        return {k: 0 for k in counts}
    n = min(n, sum(counts[k] for k in keys))
    a = {k: 1 if n >= len(keys) else 0 for k in keys}
    w = {k: math.sqrt(counts[k]) for k in keys}
    while sum(a.values()) < n:
        room = [k for k in keys if a[k] < counts[k]]
        k = max(room, key=lambda k: (w[k] / (a[k] + 1), k))
        a[k] += 1
    return {**{k: 0 for k in counts}, **a}


def order_key(u):
    return h(SEED, u["run"], u["text_id"], u["family_id"])


def draw_arbiter(units: list[dict]) -> list[dict]:
    chosen = []
    by_tag = defaultdict(list)
    for u in units:
        by_tag[u["tag"]].append(u)
    for tag, quota in PRECEDENT_QUOTA.items():
        cand = by_tag.get(tag, [])
        per_run = alloc_over(dict(Counter(u["run"] for u in cand)), quota)
        for run, k in per_run.items():
            pool = sorted((u for u in cand if u["run"] == run), key=order_key)
            chosen += pool[:k]
    # remaining slots: untagged units over run x dimension cells; if tags ran short the cells absorb the difference
    left = N_ARBITER - len(chosen)
    chosen_ids = {id(u) for u in chosen}
    rest = [u for u in units if id(u) not in chosen_ids and u["tag"] == "other"]
    cells = Counter((u["run"], u["dimension"]) for u in rest)
    per_cell = alloc_over({k: v for k, v in cells.items()}, left)
    for cell, k in per_cell.items():
        pool = sorted((u for u in rest if (u["run"], u["dimension"]) == cell), key=order_key)
        chosen += pool[:k]
    assert len(chosen) == N_ARBITER, len(chosen)
    return chosen


def draw_can_you(units: list[dict]) -> list[dict]:
    chosen, used = [], set()
    for run, n in CAN_YOU_PER_RUN.items():
        pool = sorted((u for u in units if u["run"] == run), key=order_key)
        if run == "r2c1":
            plan = [(True, CAN_YOU_TYPED_R2C1), (False, n - CAN_YOU_TYPED_R2C1)]
        else:
            plan = [(None, n)]
        for typed, k in plan:
            got = 0
            for u in pool:
                if got >= k:
                    break
                if typed is not None and u["typed"] != typed:
                    continue
                if u["norm"] in used or u in chosen:
                    continue
                used.add(u["norm"]); chosen.append(u); got += 1
            assert got == k, (run, typed, got, k)
    return chosen


# ------------------------------------------------------------------ independence + assignment
def blocked_people(items: dict, ids: list[str]) -> dict[str, set]:
    """family_id -> people who wrote or checked the pair, or chose the keywords of the message."""
    b = defaultdict(set)
    for f, it in items.items():
        if it.get("writer_id"):
            b[f].add(it["writer_id"])
    ck = ROOT / "annotation" / "written" / "check_key.csv"
    if ck.exists():
        with open(ck, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                for c in (r.get("check_id") or "").split():
                    who = c.rsplit("_check_", 1)[0] if "_check_" in c else c.rsplit("_tiebreak", 1)[0]
                    b[r["family_id"]].add(who)
    # elicitation: family elic-<id> -> set -> annotators of the set (all replicates)
    ek = {}
    p = ROOT / "annotation" / "elicitation_key.jsonl"
    for r in runio.read_jsonl(p):
        ek[r["id"]] = r["set"]
    people = defaultdict(set)
    with open(ROOT / "annotation" / "elicitation_assignment.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            people[r["set"]].add(r["annotator"])
    for f in items:
        if f.startswith("elic-"):
            s = ek.get(f[len("elic-"):])
            if s:
                b[f] |= people[s]
    return b


def assign(units: list[dict], ids: list[str], blocked: dict) -> dict[str, int]:
    rng = random.Random(SEED)
    for u in units:
        u["blocked"] = set().union(*(blocked.get(f, set()) for f in u["families"].split("|"))) & set(ids)
        u["eligible"] = [a for a in ids if a not in u["blocked"]]
        assert len(u["eligible"]) >= PER_ITEM, (u["family_id"], u["blocked"])
    load = Counter({a: 0 for a in ids})
    tie = {a: rng.random() for a in ids}
    for u in sorted(units, key=lambda u: (len(u["eligible"]), h(SEED, "ord", u["run"], u["text_id"], u["family_id"]))):
        u["coders"] = []
        for _ in range(PER_ITEM):
            c = min((a for a in u["eligible"] if a not in u["coders"]), key=lambda a: (load[a], tie[a]))
            u["coders"].append(c); load[c] += 1
    # balancing swaps: move a coding from the most to the least loaded person where allowed
    for _ in range(2000):
        hi, lo = max(load, key=lambda a: (load[a], tie[a])), min(load, key=lambda a: (load[a], -tie[a]))
        if load[hi] - load[lo] <= 1:
            break
        moved = False
        for u in units:
            if hi in u["coders"] and lo in u["eligible"] and lo not in u["coders"]:
                u["coders"][u["coders"].index(hi)] = lo; load[hi] -= 1; load[lo] += 1; moved = True; break
        if not moved:
            # two-step: hi gives item to a mid person who gives another to lo
            for u in units:
                if hi not in u["coders"]:
                    continue
                for m in sorted(ids, key=lambda a: load[a]):
                    if m in (hi, lo) or m in u["coders"] or m not in u["eligible"]:
                        continue
                    v = next((v for v in units if m in v["coders"] and lo in v["eligible"] and lo not in v["coders"]), None)
                    if v:
                        u["coders"][u["coders"].index(hi)] = m
                        v["coders"][v["coders"].index(m)] = lo
                        load[hi] -= 1; load[lo] += 1; moved = True
                        break
                if moved:
                    break
        if not moved:
            break
    for u in units:
        assert len(set(u["coders"])) == PER_ITEM and not set(u["coders"]) & u["blocked"]
    return dict(load)


# ------------------------------------------------------------------ outputs
KEY_COLS = ["item_id", "source", "run", "dimension", "precedent_tag", "arbiter_label", "J1", "J2", "production_label",
            "family_id", "text_id", "input_text", "text", "critical_options", "arbiter_rationale", "coders", "blocked_people"]


def item_id(u) -> str:
    return "p19-" + h("part19-item", u["run"], u["norm"], u["dimension"], u["input_text"])[:8]


# Part 19 practice: the standard five, except items 2 and 4, whose sentences ("Can you ...", "Could you please ...") and
# feedback would teach the very rule the "Can you" items test. Replacements keep the same format.
PRACTICE_19 = [
    G.PRACTICE[0],
    {"item_id": "practice-2", "text": "Please pass me the salt.", "dimension": "speech_act",
     "critical_options": ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"],
     "input_text": "Keywords: pass salt",
     "expected": {"critical": "request/command", "polarity": "affirmative", "speech_act": "request/command",
                  "agent": "addressee", "certainty": "n/a (question/request)", "politeness": "please", "added_content": "no"},
     "feedback": "\"Please\" plus a verb asks the listener to do something: a request, done by the addressee. "
                 "Requests get certainty n/a. \"Please\" is the politeness marker."},
    G.PRACTICE[2],
    {"item_id": "practice-4", "text": "Thank you for helping me.", "dimension": "politeness",
     "critical_options": ["polite", "plain", "unclear/mixed"], "input_text": "Keywords: thank help",
     "expected": {"critical": "polite", "polarity": "affirmative", "speech_act": "statement", "agent": "speaker",
                  "certainty": "plain assertion", "politeness": "thanks/apology", "added_content": "no"},
     "feedback": "Thanks is a politeness marker. The speaker is the one thanking."},
    G.PRACTICE[4],
]
HINT = re.compile(r"\s*\('Can (?:I|you) \.\.\.\?' is an? [a-z/]+(?: or permission)?\)")


def annotator_item(u: dict) -> dict:
    """item_for_annotator; the "Can you" items get the critical question WITHOUT the parenthetical examples
    ('Can I ...?' is a question; 'Can you ...?' is a request), so the item tests the rule instead of reading it back."""
    it = G.item_for_annotator(u)
    if u["source"] == "canyou":
        q = HINT.sub("", it["critical"]["question"])
        assert "Can " not in q and "Can you" not in q, q
        it["critical"]["question"] = q
    return it


def part_payload(its: list[dict]) -> dict:
    from labels import ADDED_CONTENT_OPTIONS, DEFINITIONS, GENERAL_DIMS, GENERAL_OPTIONS
    return {"run": RUN_TAG, "codebook_version": G.CODEBOOK_VERSION,
            "general_dims": [{"name": d, "definition": DEFINITIONS[d], "options": GENERAL_OPTIONS[d]} for d in GENERAL_DIMS],
            "added_content": {"definition": DEFINITIONS["added_content"], "options": ADDED_CONTENT_OPTIONS},
            "practice": [{**G.item_for_annotator(p), "expected": p["expected"], "feedback": p["feedback"]} for p in PRACTICE_19],
            "items": [annotator_item(u) for u in its], "part": RUN_TAG}


def experienced_labellers() -> list[str]:
    """People who had a sentence-labelling part (Parts 1-3, 10, 12, 13) in Stages 1-3: they have seen annotate.html,
    the codebook and its examples. The others have not."""
    done = set()
    for f in ("stage1.csv", "stage2.csv", "stage3.csv"):
        p = ROOT / "annotation" / "assignments" / f
        if p.exists():
            with open(p, newline="", encoding="utf-8") as fh:
                done |= {r["annotator"] for r in csv.DictReader(fh) if r["task"] in ("parts13", "part10", "part12", "part13")}
    return sorted(done)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--annotators", default="", help="default: annotators of annotation/assignments/plan.json")
    ap.add_argument("--out-dir", default=str(OUT_DIR)); ap.add_argument("--key", default=str(KEY))
    ap.add_argument("--summary", default=str(SUMMARY))
    a = ap.parse_args(argv)
    ids = [x for x in a.annotators.split(",") if x] or json.loads((ROOT / "annotation/assignments/plan.json").read_text())["annotators"]
    items = runio.load_items()
    gold = gold_texts()
    arb_frame, why_a = arbiter_units(items, gold)
    arb = draw_arbiter(arb_frame)
    can_frame, why_c = can_you_units(items, gold, {(u["norm"], u["dimension"]) for u in arb})
    can = draw_can_you(can_frame)
    units = arb + can
    for u in units:
        u["item_id"] = item_id(u)
    assert len({u["item_id"] for u in units}) == len(units) == N_ARBITER + N_CANYOU
    assert len({(u["norm"], u["dimension"]) for u in units}) == len(units), "same sentence twice"
    load = assign(units, ids, blocked_people(items, ids))

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*_part19.json"):
        old.unlink()
    per = defaultdict(list)
    for u in sorted(units, key=lambda u: u["item_id"]):
        for c in u["coders"]:
            per[c].append(u)
    for c in ids:
        mine = sorted(per[c], key=lambda u: h(SEED, "present", c, u["item_id"]))
        (out / f"{c}_part19.json").write_text(json.dumps(part_payload(mine), indent=1, ensure_ascii=False))
    with open(a.key, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEY_COLS); w.writeheader()
        for u in sorted(units, key=lambda u: u["item_id"]):
            w.writerow({"item_id": u["item_id"], "source": u["source"], "run": u["run"], "dimension": u["dimension"],
                        "precedent_tag": u["tag"], "arbiter_label": u["arbiter_label"], "J1": u["J1"], "J2": u["J2"],
                        "production_label": u["production_label"], "family_id": u["family_id"], "text_id": u["text_id"],
                        "input_text": u["input_text"], "text": u["text"], "critical_options": "|".join(u["critical_options"]),
                        "arbiter_rationale": u["rationale"], "coders": "|".join(sorted(u["coders"])),
                        "blocked_people": "|".join(sorted(u["blocked"]))})
    comp = lambda us: {  # noqa: E731
        "n": len(us), "by_run": dict(sorted(Counter(u["run"] for u in us).items())),
        "by_dimension": dict(sorted(Counter(u["dimension"] for u in us).items())),
        "by_tag": dict(sorted(Counter(u["tag"] for u in us).items())),
        "arbiter_picked_J1": sum(u["arbiter_label"] == u["J1"] for u in us if u["source"] == "arbiter"),
        "arbiter_picked_J2": sum(u["arbiter_label"] == u["J2"] for u in us if u["source"] == "arbiter"),
        "arbiter_picked_neither": sum(u["arbiter_label"] not in (u["J1"], u["J2"]) for u in us if u["source"] == "arbiter")}
    summ = {"seed": SEED, "rule": __doc__.split("Items (130")[1].split("Tool:")[0].strip(),
            "annotators": ids, "per_item": PER_ITEM, "labelled_sentences_before": experienced_labellers(), "precedent_quota": PRECEDENT_QUOTA,
            "arbiter_frame": {"units_after_exclusions": len(arb_frame), "excluded": dict(why_a),
                              "frame_by_tag": dict(sorted(Counter(u["tag"] for u in arb_frame).items()))},
            "can_you_frame": {"units": len(can_frame), "excluded": dict(why_c), "by_run": dict(Counter(u["run"] for u in can_frame))},
            "arbiter_sample": comp(arb), "can_you_sample": comp(can), "codings": sum(len(u["coders"]) for u in units),
            "items_per_person": dict(sorted(load.items())),
            "min_max_items_per_person": [min(load.values()), max(load.values())],
            "key_sha256": hashlib.sha256(Path(a.key).read_bytes()).hexdigest()}
    Path(a.summary).write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps({k: summ[k] for k in ("arbiter_frame", "can_you_frame", "arbiter_sample", "can_you_sample",
                                            "codings", "items_per_person")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
