"""Stage 6 (intent-coverage, human measure): Parts 26 and 27 files for the 20 writers, from the frozen machine drafts.
PLAN: analysis/coverage/PLAN.md section 4. Nothing is generated or judged here: it reads the frozen
analysis/coverage/{items_draw.json, drafts_main.jsonl, selector_main.jsonl} and only decides WHO sees WHICH set.

Each writer P01..P20 gets their own 10 items (the writer's own kept pair; keywords and the writer's sentence are shown).
  Part 26  "set view": 10 items. Each item shows ONE draft set (condition bare|chip x arm G1|D3p|C3|E3, no arm label, drafts in
           the order a user would see them). Questions: is any draft what you meant (which one / none); would you send it
           (as it is / small edit / no); how hard was it to find it (1-5). The tool records reading time per item.
  Part 27  "draft check": for the SAME 10 items, every distinct draft of the four arms in the SAME condition as the set the writer
           saw, shuffled by the tool, arm-blind, de-duplicated across arms by normalised text. Questions per draft: does it say what
           you meant / your other version / something else; would you accept it (as it is / small edit / no); the note box asks for
           what is wrong when the answer is no. Part 27 comes after Part 26 so that the set answers are not primed.
Design record (differences from PLAN section 4, all made to fit about 30 minutes and critique1 B5/B6; logged in COORDINATOR_STEPS):
  * one condition per item (5 bare + 5 chip per writer); the pool is for that item's own condition, not both conditions.
  * 4 arms x 2 conditions = 8 cells; 25 sets per cell over 200 items; every cell 1 or 2 times per writer (rotation).
  * k = 3 arms are shown at exactly 3 drafts wherever the arm's own candidates allow it (short contrast sets are topped up
    from the same arm's own next candidates: critique1 B6); G1 is the one-draft baseline by design.
  * D3p in chip is filtered for cue consistency exactly like the contrast arms (critique1 B5); the unfiltered D3p drafts are
    added to the pool so that the unfiltered variant stays computable from the same ratings.
  * W1 (plain-word cue), the k = 5 audit arms and the side-by-side burden check are not in the human package (time).
Writes (frozen, seeded; refuses to overwrite without --force):
  annotation_package/stage6/<ID>_part26.json, <ID>_part27.json   blind files for annotation_package/rate_items.html
  annotation/coverage_key.csv                                   PRIVATE key (never in the package)
  annotation/coverage_key.sha256                                hash to deposit before sending
  annotation/assignments/stage6_coverage.json                   design record, per-person items and minutes, cell table
usage: python src/make_coverage_stage6.py [--force] [--out-pkg DIR --out-ann DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import coverage_analyze as CA  # noqa: E402
import coverage_lib as L  # noqa: E402
from make_repair_audit import CHIP_MEANING  # noqa: E402

TOOL = "rate_items_v1"
SALT = "s6-cov-20261117"
ARMS = ["G1", "D3p", "C3", "E3"]
CONDS = ["bare", "chip"]
K = {"G1": 1, "D3p": 3, "C3": 3, "E3": 3}
SEC_SET = 45        # seconds per set-view item (read keywords and sentence, up to 3 drafts, 3 answers)
SEC_DRAFT = 15      # seconds per draft in the draft check (2 answers)
SEC_PRAC_SET, SEC_PRAC_DRAFT = 60, 25
N_PRACTICE = 2
PART_SV, PART_POOL = "part26", "part27"
KEY_COLS = ["kind", "annotator", "check_id", "item_id", "cv_item", "dimension", "intended", "intended_value", "other_value", "cond", "arm",
            "cell", "k", "n_shown", "plan_n", "set_texts", "text", "pool_arms", "proxy_intended", "proxy_other", "proxy_value",
            "r", "other_text", "bare_keywords", "chip", "d3p_filter_changed", "seen_in_part18", "hw2"]


def fnv(s: str) -> str:
    x = 2166136261
    for c in s:
        x = ((x ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return f"{x:08x}"


def id_hash(annotator: str, check: str) -> str:
    return fnv(annotator.strip().upper() + "|" + check)


def oid(prefix: str, *parts) -> str:
    return prefix + "-" + hashlib.sha1((SALT + "|" + prefix + "|" + "|".join(parts)).encode()).hexdigest()[:8]


# ------------------------------------------------------------------ the sets
def human_sets(it: dict, s: dict, J: dict, cond: str) -> dict:
    """arm -> {"shown": [...], "plan": [...]} for one item and condition. 'plan' is the set exactly as coverage_analyze builds
    it (before top-up and before the identical cue filter on D3p); 'shown' is what the writer sees."""
    c = s[cond]; g = c["g1"]; iid = it["item_id"]; pdim = it["dimension"]
    get = lambda t: J.get((iid, t))  # noqa: E731
    pj = lambda t: CA.pairj(get(t)["judge"])  # noqa: E731

    def cue_ok(t):   # cue-consistent: only meaningful in chip, where the chip states the critical value
        v = get(t)
        return cond != "chip" or (v is not None and pj(t)["value"] == it["intended_value"])

    def edit_slot(d):   # identical to coverage_analyze.build_sets
        for key in (d, d + "|regen"):
            o = c["edits"].get(key)
            if o is None:
                continue
            t = L.clean_sentence(o["sentence"]); v = get(t)
            if v is None:
                continue
            j = v["judge"]; p = CA.pairj(j)
            val = p["value"] if d == pdim else (j.get(d) or {}).get("extra_value")
            viol = cond == "chip" and p["value"] != it["intended_value"]
            if val == o["new_value"] and o["new_value"] != o.get("current_value") and not viol and L.norm(t) != L.norm(g):
                return t
        return None

    es = {d: edit_slot(d) for d in set(c["sel"][:4] + c["static"][:2] + c["rnd"][:2])}
    dims = [es[d] for d in c["sel"][:4]]

    def dedupe(first, rest, cap=None):
        out = [first]; sn = {L.norm(first)}
        for t in rest:
            if t and L.norm(t) not in sn:
                sn.add(L.norm(t)); out.append(t)
                if cap and len(out) >= cap:
                    break
        return out

    ev = list(c["event"])
    if cond == "chip":
        ev = [t for t in ev if get(t) and pj(t)["value"] == it["intended_value"]]
    plan = {"G1": [g], "D3p": dedupe(g, c["div2"]), "C3": dedupe(g, dims[:2]), "E3": dedupe(g, dims[:1] + ev[:1])}
    shown = {"G1": [g]}
    # D3p: same cue filter as the contrast arms (chip only), replacements from the arm's own next diverse drafts (div4), cap 3
    dv = [t for t in c["div2"] + c["div4"] if cue_ok(t)]
    shown["D3p"] = dedupe(g, dv, 3)
    # C3: selector order, top-up from the next ranked dimensions (all already generated for the k = 5 arm)
    shown["C3"] = dedupe(g, dims, 3)
    # E3: dimension slot, event slot first; then the remaining dimension and event candidates in that alternation
    alt = []
    n = max(len(dims), len(ev))
    for i in range(n):
        if i < len(dims):
            alt.append(dims[i])
        if i < len(ev):
            alt.append(ev[i])
    shown["E3"] = dedupe(g, alt[:2] + alt[2:], 3)
    return {a: {"shown": shown[a], "plan": plan[a]} for a in ARMS}


def assign_cells(writer: str, widx: int, items: list[dict]) -> dict:
    """item_id -> (cond, arm). 5 bare + 5 chip, condition balanced inside each dimension; each arm once per condition plus
    one extra arm per condition, rotated over writers so that every cell has 25 sets."""
    rng = random.Random(f"{SALT}|assign|{writer}")
    by_dim = defaultdict(list)
    for it in items:
        by_dim[it["dimension"]].append(it)
    cnt = Counter(); cond_of = {}
    for d in sorted(by_dim):
        lst = by_dim[d][:]; rng.shuffle(lst)
        for it in lst:
            lo = min(cnt[c] for c in CONDS)
            cand = [c for c in CONDS if cnt[c] == lo]
            c = rng.choice(cand); cond_of[it["item_id"]] = c; cnt[c] += 1
    out = {}
    for ci, cond in enumerate(CONDS):
        its = [i for i in items if cond_of[i["item_id"]] == cond]
        arms = ARMS + [ARMS[(widx + ci) % 4]] * (len(its) - 4) if len(its) >= 4 else ARMS[: len(its)]
        rng.shuffle(arms)
        for it, a in zip(its, arms):
            out[it["item_id"]] = (cond, a)
    return out


# ------------------------------------------------------------------ files
def qdef(title, text, options):
    return {"title": title, "text": text, "options": [{"v": v, "label": lab} for v, lab in options]}


QS_SV = {
    "pick1": qdef("Is this what you meant?", "Yes if it says the message you meant (different words are fine). No if it says something else.",
                  [("yes", "Yes, this is what I meant"), ("none", "No, it is not")]),
    "pick2": qdef("Is any of these what you meant?", "Pick the one that says the message you meant (different words are fine), or none.",
                  [("1", "Draft 1"), ("2", "Draft 2"), ("none", "None of them")]),
    "pick3": qdef("Is any of these what you meant?", "Pick the one that says the message you meant (different words are fine), or none.",
                  [("1", "Draft 1"), ("2", "Draft 2"), ("3", "Draft 3"), ("none", "None of them")]),
    "send": qdef("Would you send it?", "Think of the draft you picked. If you picked none, choose the last option.",
                 [("as_is", "Yes, as it is"), ("small_edit", "Yes, with a small edit"), ("no", "No (or I picked none)")]),
    "hard": qdef("How hard was it to find what you meant?", "1 = very easy, 5 = very hard. If none was right, say how hard it was to be sure of that.",
                 [("1", "1 very easy"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5 very hard")]),
}
QS_POOL = {
    "ver": qdef("What does this draft say?", "Compare it with what you meant and with your other version.",
                [("meant", "What I meant"), ("other", "My other version"), ("else", "Something else")]),
    "acc": qdef("Would you accept it as your message?", "If you answer No, write in the note box what is wrong (a few words).",
                [("yes", "Yes, as it is"), ("small_edit", "Yes, with a small edit"), ("no", "No")]),
}
HELP_SV = [
    {"term": "What you see", "text": "The keywords you typed (and a cue button, if you pressed one), the sentence you meant, and the drafts a writing tool offers for those keywords."},
    {"term": "What counts as 'what you meant'", "text": "A draft says what you meant if it carries your message, even in different words or with less detail. A draft that says the opposite, asks instead of tells, changes who does it or when, or is a different message does not."},
    {"term": "Would you send it", "text": "As it is: you would send it unchanged. Small edit: you would fix a word or two. No: it would need more than that, or none was right."},
    {"term": "How hard", "text": "How hard it was to find the draft you meant (or to see that none was right)."},
]
HELP_POOL = [
    {"term": "What you see", "text": "One draft at a time, with the keywords it was made from, the sentence you meant and your other version."},
    {"term": "What does it say", "text": "What I meant: it carries the message you meant. My other version: it carries the message of your other sentence. Something else: neither."},
    {"term": "Would you accept it", "text": "Yes as it is, yes with a small edit (a word or two), or no. If no, write in the note box what is wrong."},
]


def kw_blocks(it, cond):
    chip = ""
    if cond == "chip":
        import re
        chips = re.findall(r"\[[^\]]+\]", it["inputs"]["chip"])
        chip = "; ".join(f"{c} = {CHIP_MEANING.get(c, c)}" for c in chips)
    b = [{"label": "Keywords you typed", "text": it["bare"]}]
    if chip:
        b.append({"label": "Cue button you pressed", "text": chip})
    return b


def sv_item(it, cond, texts):
    blocks = kw_blocks(it, cond) + [{"label": "What you meant (your sentence)", "text": it["r"]}]
    blocks += [{"label": f"Draft {i}", "text": t} for i, t in enumerate(texts, 1)]
    n = len(texts)
    return {"item_id": oid("sv", it["item_id"]), "blocks": blocks, "qs": [f"pick{n}", "send", "hard"]}


def pool_item(it, cond, text):
    other = it[("B" if it["intended"] == "A" else "A")]
    blocks = kw_blocks(it, cond) + [{"label": "What you meant (your sentence)", "text": it["r"]},
                                    {"label": "Your other version", "text": other},
                                    {"label": "Draft", "text": text}]
    return {"item_id": oid("pd", it["item_id"], L.norm(text)), "blocks": blocks, "qs": ["ver", "acc"]}


PRAC_SV = [
    {"item_id": "prac-sv1", "blocks": [{"label": "Keywords you typed", "text": "bus late"},
                                       {"label": "What you meant (your sentence)", "text": "The bus is late again."},
                                       {"label": "Draft 1", "text": "Is the bus late?"}, {"label": "Draft 2", "text": "The bus is late."},
                                       {"label": "Draft 3", "text": "Please wait for the late bus."}],
     "qs": ["pick3", "send", "hard"], "expected": {"pick3": "2", "send": "small_edit", "hard": "2"},
     "fb": "Draft 2 carries the message (the bus is late); it lacks 'again', a small edit. Draft 1 asks a question and Draft 3 asks for something else."},
    {"item_id": "prac-sv2", "blocks": [{"label": "Keywords you typed", "text": "coffee"},
                                       {"label": "Cue button you pressed", "text": "[NOT] = negation"},
                                       {"label": "What you meant (your sentence)", "text": "I don't want coffee."},
                                       {"label": "Draft 1", "text": "I want coffee."}],
     "qs": ["pick1", "send", "hard"], "expected": {"pick1": "none", "send": "no", "hard": "1"},
     "fb": "The draft says the opposite of what you meant, so the answer is no, and it is easy to see."},
]
PRAC_POOL = [
    {"item_id": "prac-pd1", "blocks": [{"label": "Keywords you typed", "text": "bus late"},
                                       {"label": "What you meant (your sentence)", "text": "The bus is late again."},
                                       {"label": "Your other version", "text": "The bus is not late."},
                                       {"label": "Draft", "text": "The bus is late."}],
     "qs": ["ver", "acc"], "expected": {"ver": "meant", "acc": "small_edit"},
     "fb": "It says the bus is late, which is what you meant; 'again' is missing, a small edit."},
    {"item_id": "prac-pd2", "blocks": [{"label": "Keywords you typed", "text": "bus late"},
                                       {"label": "What you meant (your sentence)", "text": "The bus is late again."},
                                       {"label": "Your other version", "text": "The bus is not late."},
                                       {"label": "Draft", "text": "Is the bus late?"}],
     "qs": ["ver", "acc"], "expected": {"ver": "else", "acc": "no"},
     "fb": "It asks a question: it is neither of your two sentences, and it would need more than a small edit."},
]


def doc(check_id, ann, title, intro, help_, questions, practice, items):
    qids = sorted({q for x in items + practice for q in x["qs"]})
    return {"check_id": check_id, "tool": TOOL, "version": 1, "n_items": len(items), "for": id_hash(ann, check_id), "title": title,
            "intro": intro, "help": help_, "questions": {q: questions[q] for q in qids}, "practice": practice, "items": items}


def minutes(n_sv, n_pool):
    sec = n_sv * SEC_SET + N_PRACTICE * SEC_PRAC_SET + n_pool * SEC_DRAFT + N_PRACTICE * SEC_PRAC_DRAFT
    return {"part26": round((n_sv * SEC_SET + N_PRACTICE * SEC_PRAC_SET) / 60), "part27": round((n_pool * SEC_DRAFT + N_PRACTICE * SEC_PRAC_DRAFT) / 60),
            "total": round(sec / 60)}


def build(out_pkg: Path, out_ann: Path, force=False, write=True):
    keyp, plan_p = out_ann / "coverage_key.csv", out_ann / "assignments" / "stage6_coverage.json"
    if write and keyp.exists() and not force:
        raise SystemExit(f"{keyp} exists; the Stage 6 package is frozen (use --force to redraw)")
    items, J, S = CA.load()
    items = {k: v for k, v in items.items() if not v.get("reserve")}
    by_w = defaultdict(list)
    for it in items.values():
        by_w[it["writer_id"]].append(it)
    writers = sorted(by_w)
    assert len(writers) == 20 and all(len(v) == 10 for v in by_w.values()), "expected 20 writers x 10 items"
    key, files, per_person = [], {}, {}
    cell_n, short, dim_cell = Counter(), Counter(), Counter()
    for widx, w in enumerate(writers):
        its = sorted(by_w[w], key=lambda x: x["item_id"])
        cells = assign_cells(w, widx, its)
        sv, pool = [], []
        for it in its:
            cond, arm = cells[it["item_id"]]
            hs = human_sets(it, S[it["item_id"]], J, cond)
            shown = hs[arm]["shown"]
            cell_n[(cond, arm)] += 1; dim_cell[(it["dimension"], cond, arm)] += 1
            if len(shown) < K[arm]:
                short[(cond, arm)] += 1
            item = sv_item(it, cond, shown); sv.append(item)
            base = dict(annotator=w, cv_item=it["item_id"], dimension=it["dimension"], intended=it["intended"], intended_value=it["intended_value"],
                        other_value=it["other_value"], cond=cond, r=it["r"], other_text=it["B" if it["intended"] == "A" else "A"],
                        bare_keywords=it["bare"], chip=it["inputs"]["chip"] if cond == "chip" else "",
                        seen_in_part18=int(it["seen_in_part18"]), hw2=int(it["hw2"]))
            key.append({**base, "kind": "sv", "check_id": PART_SV, "item_id": item["item_id"], "arm": arm, "cell": f"{cond}|{arm}", "k": K[arm],
                        "n_shown": len(shown), "plan_n": len(hs[arm]["plan"]), "set_texts": json.dumps(shown, ensure_ascii=False),
                        "d3p_filter_changed": int(hs["D3p"]["shown"] != hs["D3p"]["plan"])})
            # the pool for this item: every distinct draft of the four arms in this condition (+ unfiltered D3p drafts)
            members = {}
            for a in ARMS:
                for pos, t in enumerate(hs[a]["shown"], 1):
                    members.setdefault(L.norm(t), {"text": t, "arms": []})["arms"].append(f"{a}:{pos}")
            for pos, t in enumerate(hs["D3p"]["plan"], 1):
                members.setdefault(L.norm(t), {"text": t, "arms": []})["arms"].append(f"D3pU:{pos}")
            for m in members.values():
                v = J.get((it["item_id"], m["text"]))
                pc = CA.judge_cov(it, v) if v else {"A": "", "B": "", "val": ""}
                other = "B" if it["intended"] == "A" else "A"
                pi = pool_item(it, cond, m["text"]); pool.append(pi)
                key.append({**base, "kind": "pool", "check_id": PART_POOL, "item_id": pi["item_id"], "arm": "", "cell": f"{cond}|{arm}", "k": "",
                            "n_shown": "", "plan_n": "", "text": m["text"], "pool_arms": " ".join(m["arms"]),
                            "proxy_intended": int(pc[it["intended"]]) if v else "", "proxy_other": int(pc[other]) if v else "",
                            "proxy_value": pc["val"] or "", "d3p_filter_changed": int(hs["D3p"]["shown"] != hs["D3p"]["plan"])})
        ids = [x["item_id"] for x in sv + pool]
        assert len(ids) == len(set(ids)), f"duplicate opaque ids for {w}"
        d1 = doc(PART_SV, w, "Find what you meant among drafts",
                 ["For each of 10 messages, you see the keywords you typed for one of your own sentence pairs, the sentence you meant, and the drafts a writing tool offers for those keywords.",
                  "Say whether any draft is what you meant (which one), whether you would send it, and how hard it was to find. The drafts are shown in the order a user would see them."],
                 HELP_SV, QS_SV, PRAC_SV, sv)
        d2 = doc(PART_POOL, w, "Check each draft",
                 ["You will see single drafts made for your own messages, one at a time, in a mixed order. For each one, say what it says and whether you would accept it.",
                  "Some drafts are close to what you meant and some are not. If you answer No, write in the note box what is wrong."],
                 HELP_POOL, QS_POOL, PRAC_POOL, pool)
        files[w] = (d1, d2); per_person[w] = {"n_set": len(sv), "n_draft": len(pool), "minutes": minutes(len(sv), len(pool))}
    summary = {
        "seed_salt": SALT, "arms": ARMS, "cells": {f"{c}|{a}": cell_n[(c, a)] for c in CONDS for a in ARMS},
        "short_sets_after_topup": {f"{c}|{a}": short[(c, a)] for c in CONDS for a in ARMS if K[a] > 1},
        "per_person": per_person,
        "minutes_min_max": [min(v["minutes"]["total"] for v in per_person.values()), max(v["minutes"]["total"] for v in per_person.values())],
        "drafts_per_person_min_max": [min(v["n_draft"] for v in per_person.values()), max(v["n_draft"] for v in per_person.values())],
        "time_constants_sec": {"set_item": SEC_SET, "draft": SEC_DRAFT, "practice_set": SEC_PRAC_SET, "practice_draft": SEC_PRAC_DRAFT,
                               "note": "assumptions; replace with the timed pretest figures (PLAN section 9 step 2)"},
        "dimension_by_cell": {f"{d}|{c}|{a}": n for (d, c, a), n in sorted(dim_cell.items())},
        "design": ["one condition per item; pool for that condition only", "k=3 arms topped up to 3 from the arm's own candidates",
                   "D3p filtered for cue consistency in chip like C3/E3; unfiltered D3p drafts in the pool (tag D3pU)",
                   "W1, k=5 audit arms and side-by-side burden check not in the human package"]}
    if write:
        d = out_pkg / "stage6"; d.mkdir(parents=True, exist_ok=True); plan_p.parent.mkdir(parents=True, exist_ok=True)
        for w, (d1, d2) in files.items():
            (d / f"{w}_{PART_SV}.json").write_text(json.dumps(d1, ensure_ascii=False, indent=1))
            (d / f"{w}_{PART_POOL}.json").write_text(json.dumps(d2, ensure_ascii=False, indent=1))
        with open(keyp, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, KEY_COLS, extrasaction="ignore"); wr.writeheader(); wr.writerows(key)
        (out_ann / "coverage_key.sha256").write_text(hashlib.sha256(keyp.read_bytes()).hexdigest() + "  coverage_key.csv\n")
        plan_p.write_text(json.dumps(summary, indent=1))
    return {"key": key, "files": files, "summary": summary}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out-pkg", default=str(ROOT / "annotation_package"))
    ap.add_argument("--out-ann", default=str(ROOT / "annotation"))
    a = ap.parse_args(argv)
    r = build(Path(a.out_pkg), Path(a.out_ann), force=a.force)
    s = r["summary"]
    print("cells", s["cells"]); print("short after top-up", s["short_sets_after_topup"])
    print("minutes per person", s["minutes_min_max"], "drafts per person", s["drafts_per_person_min_max"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
