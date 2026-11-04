"""Two-stage annotation plan for a fixed annotator pool (default P01..P20): assignments, task sheets, Stage 2 fill.

usage:
  python src/make_assignments.py --stage 1 --annotators P01..P20      # plan BOTH stages now, write sheets
  python src/make_assignments.py --stage 2 --prepare                  # Stage 2/3 sheets + CSVs from plan.json
  python src/make_assignments.py --stage 2 [--absent P07,...] [--still-checking P09,...]
                                                                       # between stages: fill the fixed Stage 2 files
  python src/make_assignments.py --stage 3 [--absent P11,...]         # after Stage 2 scoring: route Part 14 tie-breaks
  python src/make_assignments.py --stage 4 [--writers P05,..] [--raters ..] [--checkers ..]
                                                                       # Stage 4 roster, sheets, stage4.csv, empty check placeholders
  python src/make_assignments.py --stage 4 --fill-checks [--absent P05]
                                                                       # after Part 15 returns + collect_written_pairs.py --batch hw2

  python src/make_assignments.py --stage 5                            # Stage 5 (Parts 20, 21 for everyone + each person's share of 22-25): sheets, stage5.csv, hand-out block

Stage 5 (added after Stage 4 had been returned; Parts 20 and 21 for all annotators, 18 min each, plus Parts 22-25 shares; about 60 min each)
  Part 20   annotate.html + stage5/<ID>_part20.json (src/make_treated_check.py): 12 labelled sentences from treated outputs.
  Part 21   source_check.html + stage5/<ID>_part21.json (src/make_source_check.py): 20 source messages, 3 quick questions.
  The part files and keys come from the two make_* scripts (seeded, frozen); --stage 5 only writes the sheets
  annotation_package/assignments/<ID>_stage5.md, annotation/assignments/stage5.csv and the hand-out block, and checks that
  each person's part files exist. Everyone gets Parts 20 and 21, in this order.
  Parts 22-25 (src/make_frontier_parts.py; rate_items.html + stage5/<ID>_part22..25.json; item counts, minutes and the private
  assignment in annotation/assignments/stage5_frontier*.{json,csv}): each person gets a share of each, balanced to the same minutes.

Stage 1 (Nov 2-4, ~3-4 h each; ORDER IS MANDATORY: elicitation -> audits -> writing)
  roles     hash order of the IDs (sha1(SALT|roles|ID)): first 3 do Part 10, next 3 Parts 1-3 (extra coders),
            next 4 are the Part 12 coders (Stage 2 gold on elicited-keyword outputs), the rest are "regular".
  Part 9    48 sessions (16 sets x 3 Latin-square replicates, annotation_package/elicitation_sets/). Part 12 coders
            get 2 sessions on paired sets (coder 2g+r takes replicate r+1 of sets 2g+1 and 2g+2), so the Part 12
            sample can exclude every message they saw (4 sets) and every keyword set they typed. Part 10 and
            Parts 1-3 coders get 2 sessions; the remaining sessions go to regular annotators (2-3 each). Never two
            replicates of one set for one person. Elicitation is FIRST so the keywords are typed before the person
            has seen any model output, test pair or codebook (no priming).
  audits    Part 10 (3) and Parts 1-3 (3) are fixed by role; those six do no other audit. Required slots of
            Part 4 (10), Part 11 (10), Part 5 (6), Part 6 (6) go to the person with the fewest planned Stage 1+2
            minutes (distinct annotators per task); then everyone else is topped up to >= AUDIT_FLOOR (60) audit
            minutes (Part 12 coders: 40, as their Stage 2 is ~90 min longer) with the task whose count/required
            ratio is lowest (cap AUDIT_CAP = 100). Counts are therefore >= the required ones.
  Part 7    LAST. 2 sessions x 15 pairs per person in two different dimensions (40 writer-dimension slots,
            6-7 per dimension, 600 pairs). Person k (hash order) gets dims k%6 and (k%6 + 1 + (k//6)%5)%6;
            rotations as src/make_writer_links.py (writer j of a dimension -> rot (3j + dim index) % 11).
Stage 2 (Nov 5-7, ~1.2-2.6 h), decided NOW (fixed file paths):
  Part 8    checker graph: ring order R (sha1(SALT|check|ID)). Writer R[i]'s 30 pairs form 6 chunks of 5
            (chunk = 3*(session-1) + (pair_no-1)//5, capped at 2 within a session). Chunk c, replica k goes to
            checker R[(i + OFF[c][k]) % n], where OFF partitions 1..18 into 6 triples (deterministic search for
            the most even co-checker spread). Each pair gets 3 distinct checkers, never its writer; every person
            gets 18 chunks = 90 pairs; replica k of all chunks forms file annotation_package/stage2/<ID>_check_<k+1>.json
            (6 chunks of 5 from 6 different writers, 3 from each of their sessions).
  Part 12   annotation_package/stage2/part12_gold_elic.json (src/make_gold_elic.py, ~150 items) for the 4 Part 12 coders.
Stage 2 fill (--stage 2), after src/collect_written_pairs.py --no-batches:
  short returns   a chunk holds whatever pairs of that writer/session/index were accepted; files shrink; the
                  checker sets never change.
  missing writer  a writer with 0 accepted pairs leaves 18 freed slots (one per checker of their chunks). If that
                  person is also absent for Stage 2 (no write_pairs return file at all, or --absent; override
                  with --still-checking), their own 18 check chunks are reassigned ONE-TO-ONE to those freed
                  checkers (deterministic bipartite matching in ring order; a checker never gets their own pairs
                  or a chunk they already check), into the file whose chunk was freed. Only those checkers' files
                  change. Chunks that cannot be matched (e.g. an absent person who did write) go to the eligible
                  present person with the lowest pair load (ring-order tie-break), in their smallest file.
Writes (stage 1): annotation/assignments/{stage1,stage2}.csv, plan.json, check_graph.csv, part12_coders.txt,
  annotation/written/writer_assignment.csv, annotation/elicitation_assignment.csv,
  annotation_package/assignments/<ID>.md (both stages), annotation_package/stage2/README.md.
Writes (stage 2): annotation_package/stage2/<ID>_check_<k>.json, annotation/written/check_key.csv (for
  src/score_pair_checks.py), annotation/assignments/stage2_fill.csv and stage2_fill.json.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import hw_rules as H  # noqa: E402
import make_writer_links as WL  # noqa: E402

SALT = "assign-20261102"
PKG = ROOT / "annotation_package"
ASSIGN_DIR = ROOT / "annotation" / "assignments"
SHEET_DIR = PKG / "assignments"
STAGE2_DIR = PKG / "stage2"
ELIC_DIR = PKG / "elicitation_sets"
WRITTEN = ROOT / "annotation" / "written"
DATES = {"stage1": "Mon Nov 2 - Wed Nov 4", "stage1_due": "Wed Nov 4, 23:59", "stage2_open": "Sun Nov 1",
         "stage2": "Sun Nov 1", "stage2_due": "Sun Nov 1, 23:59", "stage3_open": "Sun Nov 1",
         "stage3": "Sun Nov 1", "stage3_due": "Sun Nov 1, 23:59"}   # D-051: all stages compressed to Nov 1
STAGE3_DIR = PKG / "stage3"
STAGE4_DIR = PKG / "stage4"
# Stage 4 (D-058). Dates are easy to change here; the sheets, stage4.csv and HANDOUT.md read them.
DATES.update({"stage4_open": "Mon Nov 2", "stage4": "Mon Nov 2", "stage4_due": "Mon Nov 2, 23:59",
              "stage4_check_open": "once Part 15 is back (Mon Nov 2 evening at the earliest; the coordinator tells you)",
              "stage4_check_due": "Tue Nov 3, 23:59", "stage4_end": "Tue Nov 3"})
S4_PLAN = ASSIGN_DIR / "stage4_plan.json"
# Stage 5 (Parts 20 and 21, built after Stage 4 had been returned). Dates are assumptions the coordinator can change here.
STAGE5_DIR = PKG / "stage5"
DATES.update({"stage5_open": "Wed Nov 4", "stage5": "Wed Nov 4", "stage5_due": "Thu Nov 5, 23:59", "stage5_end": "Thu Nov 5"})
S5_FRONTIER = ASSIGN_DIR / "stage5_frontier.json"   # written by src/make_frontier_parts.py: per-person items and minutes for Parts 22-25
S4_WRITTEN = WRITTEN / "hw2"
S4_BATCH = "hw2"
PART17_RATERS = ["P02", "P07", "P09", "P10", "P11", "P14"]   # people who did not do Parts 4/11 (D-058)
N_S4_WRITERS, N_S4_CHECKERS, S4_PAIRS, S4_PER_PAIR = 4, 6, 15, 3
N_PART13, N_TIEBREAK, TIEBREAK_CAP = 3, 6, 40
PAIRS_PER_SESSION, CHUNK, N_REPLICA, N_SESSIONS_WRITE = 15, 5, 3, 2
N_PART10, N_PARTS13, N_PART12 = 3, 3, 4
REQUIRED = {"part4": 10, "part11": 10, "part5": 6, "part6": 6, "part10": N_PART10, "parts13": N_PARTS13}
AUDIT_FLOOR, AUDIT_FLOOR_PART12, AUDIT_CAP = 60, 40, 100   # Part 12 coders carry ~90 extra min in Stage 2
DIMS = list(H.DIMS)
DIM_LABEL = {"polarity": "polarity (negation)", "speech_act": "speech act", "politeness": "politeness",
             "certainty": "certainty", "agent": "agent (who does it)", "time": "time"}

# task -> (part label, title, minutes, file, return file template ({ID}, {x}), return folder)
TASKS = {
    "codebook": ("-", "Read CODEBOOK.md once (definitions used by annotate.html)", 10, "CODEBOOK.md", "", ""),
    "elic": ("Part 9", "Keyword elicitation", 20, "keyword_elicitation.html + elicitation_sets/{x}.json",
             "keyword_elicitation_{x}_{ID}.csv", "annotation/returns_elic/"),
    "parts13": ("Parts 1-3", "Sentence labels (extra coder): part1_core.json, then part2_extraA.json, then part3_extraB.json",
                100, "annotate.html + part1_core.json, part2_extraA.json, part3_extraB.json",
                "labels_main1_core_{ID}.csv, labels_main1_extraA_{ID}.csv, labels_main1_extraB_{ID}.csv", "annotation/returns/"),
    "part10": ("Part 10", "Sentence labels on new outputs (162 sentences; may be split into two sittings)", 90,
               "annotate.html + part10_gold_new.json", "labels_gold_new_{ID}.csv", "annotation/returns_gold_new/"),
    "part4": ("Part 4", "Sentence check (40 sentences, two passes)", 20, "repair_audit.html",
              "repair_audit_{ID}.csv", "annotation/returns_repair/"),
    "part11": ("Part 11", "Second sentence check (40 new sentences, same task as Part 4)", 20, "repair_audit_transfer.html",
               "repair_audit_transfer_{ID}.csv", "annotation/returns_repair_transfer/"),
    "part5": ("Part 5", "Sentence pair check (20 pairs)", 15, "wc_source_check.html",
              "wc_source_check_{ID}.csv", "annotation/returns_wc/"),
    "part6": ("Part 6", "Message check (20 messages, two passes)", 15, "wb_corpus_check.html",
              "wb_corpus_check_{ID}.csv", "annotation/returns_wb/"),
    "write": ("Part 7", "Write 15 sentence pairs", 35, "write_pairs.html{x}", "write_pairs_{dim}_{ID}.csv",
              "annotation/returns_written/"),
    "check": ("Part 8", "Check 30 sentence pairs written by other people", 22, "check_pairs.html + stage2/{x}.json",
              "check_pairs_{x}_{ID}.csv", "annotation/returns_hwcheck/"),
    "part12": ("Part 12", "Sentence labels on new outputs (about 150 sentences)", 80,
               "annotate.html + stage2/part12_gold_elic.json", "labels_gold_elic_{ID}.csv", "annotation/returns_gold_elic/"),
    "part13": ("Part 13", "Sentence labels on outputs from the checked written pairs (about 150 sentences)", 80,
               "annotate.html + stage3/part13_gold_hw.json", "labels_gold_hw_{ID}.csv", "annotation/returns_gold_hw/"),
    "tiebreak": ("Part 14", f"Tie-break checks of sentence pairs (up to {TIEBREAK_CAP} pairs; your file may have fewer or none)", 30,
                 "check_pairs.html + stage3/{x}.json", "check_pairs_{x}_{ID}.csv", "annotation/returns_hwcheck/"),
}
# Stage 4 tasks (D-058); kept apart from TASKS so the frozen plan.json "minutes" field (TASKS_MIN) is unchanged
TASKS4 = {
    "intent": ("Part 18", "Did it say what you meant? (10 sentences made from your own pairs)", 15,
               "intent_check.html + stage4/{ID}_intent.json", "intent_check_{ID}.csv", "annotation/returns_intent/"),
    "write2": ("Part 15", f"Write {S4_PAIRS} new speech-act sentence pairs (your own sentences)", 25, "write_pairs.html{x}",
               "write_pairs_speech_act_{ID}.csv", "annotation/returns_written_hw2/"),
    "part19": ("Part 19", "Label sentences: about 13 sentences, 5 practice items first (same task as Part 10)", 10,
               "annotate.html + stage4/{ID}_part19.json", "labels_part19_{ID}.csv", "annotation/returns_arbiter_check/"),
    "repair2": ("Part 17", "Sentence check on new sentences (80 sentences; same task as Part 4)", 47,
                "repair_audit_v2.html + stage4/{ID}_repair_v2.json", "repair_audit_v2_{ID}.csv", "annotation/returns_repair_v2/"),
    "check2": ("Part 16", "Check about 30 new sentence pairs written by other people (same task as Part 8)", 22,
               "check_pairs.html + stage4/{x}.json", "check_pairs_{x}_{ID}.csv", "annotation/returns_hwcheck_hw2/"),
}
# Stage 5 tasks (Parts 20 and 21): everyone, in this order
TASKS5 = {
    "part20": ("Part 20", "Label sentences: 12 sentences, 5 practice items first (same task as Part 10)", 10,
               "annotate.html + stage5/{ID}_part20.json", "labels_part20_{ID}.csv", "annotation/returns_treated_check/"),
    "part21": ("Part 21", "Check messages: 20 short messages, 3 quick questions each, 3 practice messages first", 8,
               "source_check.html + stage5/{ID}_part21.json", "labels_part21_{ID}.csv", "annotation/returns_source_check/"),
}
# Parts 22-25 (added before any Stage 5 return): not everyone does every part; the per-person item counts and minutes come from
# annotation/assignments/stage5_frontier.json (src/make_frontier_parts.py). Names are plain descriptions of the task.
TASKS5_FRONTIER = {
    "part22": ("Part 22", "Read a sentence and the keywords typed for it: {n} items, 4 short questions each, 2 practice items first"),
    "part23": ("Part 23", "Compare a sentence with two possible messages: {n} items, 2 or 3 short questions each, 2 practice items first"),
    "part24": ("Part 24", "Pick the sentence that says the same thing: {n} items, 2 short questions each, 2 practice items first"),
    "part25": ("Part 25", "Read a remark and a sentence: {n} items, 1 or 2 short questions each, 2 practice items first"),
}
S5_EXTRA_RULES = {
    "part22": "- **Part 22:** questions 1 and 2 are about the sentence, questions 3 and 4 only about the keywords (ignore the sentence for those two).",
    "part23": "- **Part 23:** the square-bracket words are buttons the writer pressed; they are not part of the sentence. The questions change between items: read them each time.",
    "part24": "- **Part 24:** judge only the feature named in question 1; question 2 is which sentence you would pick if you had typed those keywords.",
    "part25": "- **Part 25:** the question changes between items (a letter choice for some, two yes/no questions for others): read it each time.",
}
AUDITS_FLEX = ["part4", "part11", "part5", "part6"]
AUDIT_ORDER = ["parts13", "part10", "part4", "part11", "part5", "part6"]   # order within the audit block


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def hord(ids, tag: str) -> list[str]:
    return sorted(ids, key=lambda x: sha(f"{SALT}|{tag}|{x}"))


def parse_ids(s: str) -> list[str]:
    out = []
    for tok in [t.strip() for t in s.split(",") if t.strip()]:
        m = re.fullmatch(r"([A-Za-z]*)(\d+)\.\.([A-Za-z]*)(\d+)", tok)
        if m:
            p, a, _, b = m.groups()
            out += [f"{p}{i:0{len(m.group(2))}d}" for i in range(int(a), int(b) + 1)]
        else:
            out.append(tok)
    if len(set(out)) != len(out):
        raise SystemExit(f"duplicate annotator IDs in {s!r}")
    return out


# ---------------------------------------------------------------- Stage 1 pieces
def elic_sessions() -> list[dict]:
    out = []
    for p in sorted(ELIC_DIR.glob("elic_s*_r*.json")):
        m = re.fullmatch(r"elic_(s\d+)_r(\d+)", p.stem)
        out.append({"set": m.group(1), "replicate": int(m.group(2)), "file": p.stem,
                    "n_messages": len(json.loads(p.read_text())["messages"])})
    if not out:
        raise SystemExit(f"no session files in {ELIC_DIR} (run src/make_elicitation_sets.py)")
    return out


def assign_elic(sessions, roles, ids):
    sets = sorted({s["set"] for s in sessions})
    by = {(s["set"], s["replicate"]): s for s in sessions}
    got = {a: [] for a in ids}
    for i, c in enumerate(roles["part12"]):          # paired sets for Part 12 coders
        g, r = divmod(i, 2)
        for s in sets[2 * g:2 * g + 2]:
            got[c].append(by.pop((s, r + 1)))
    heavy = roles["part10"] + roles["parts13"]
    rest = sorted(by.values(), key=lambda s: (s["replicate"], s["set"]))
    regular = roles["regular"]
    n_left = len(rest) - 2 * len(heavy)
    base, extra = divmod(n_left, len(regular))
    if base < 2 or base + (extra > 0) > 3:
        raise SystemExit(f"cannot give regular annotators 2-3 sessions ({n_left} sessions, {len(regular)} people)")
    cap = {a: 2 for a in heavy} | {a: base + (j < extra) for j, a in enumerate(regular)}
    for t in range(500):
        order = rest if t == 0 else sorted(rest, key=lambda s: sha(f"{SALT}|elic|{t}|{s['file']}"))
        g2 = {a: [] for a in cap}
        ok = True
        for s in order:
            elig = [a for a in cap if len(g2[a]) < cap[a] and s["set"] not in {x["set"] for x in g2[a]}]
            if not elig:
                ok = False; break
            a = max(elig, key=lambda a: (cap[a] - len(g2[a]), -hord(cap, "elic").index(a)))
            g2[a].append(s)
        if ok:
            for a in g2:
                got[a] += g2[a]
            break
    else:
        raise SystemExit("no feasible elicitation assignment found")
    for a in got:
        got[a].sort(key=lambda s: (s["set"], s["replicate"]))
    return got


def offsets_partition(n: int) -> list[list[int]]:
    """Partition 1..18 into 6 triples (chunk c -> offsets of its 3 checkers) with the most even spread of
    co-checker ring distances (fixed seed search: deterministic)."""
    need = 6 * N_REPLICA
    if n - 1 < need:
        raise SystemExit(f"the checker graph needs at least {need + 1} annotators (got {n})")
    rng = random.Random(f"{SALT}|offsets|{n}")
    best = None
    base = list(range(1, need + 1))
    for _ in range(4000):
        rng.shuffle(base)
        tr = [sorted(base[3 * i:3 * i + 3]) for i in range(6)]
        dist = Counter(min((y - x) % n, (x - y) % n) for t in tr for x, y in itertools.combinations(t, 2))
        score = (max(dist.values()), sum(v * v for v in dist.values()))
        if best is None or score < best[0]:
            best = (score, [list(t) for t in tr])
    return sorted(best[1])


def build_plan(ids: list[str]) -> dict:
    n = len(ids)
    if n < N_PART10 + N_PARTS13 + N_PART12 + 6:
        raise SystemExit("need at least 16 annotators for this design")
    L = hord(ids, "roles")
    roles = {"part10": L[:3], "parts13": L[3:6], "part12": L[6:10], "regular": L[10:]}
    role_of = {a: r for r, xs in roles.items() for a in xs}
    sessions = elic_sessions()
    elic = assign_elic(sessions, roles, ids)
    tasks = {a: [] for a in ids}
    for a in roles["part10"]:
        tasks[a] = ["part10"]
    for a in roles["parts13"]:
        tasks[a] = ["parts13"]
    s2_est = 3 * TASKS["check"][2]
    s1_min = {a: len(elic[a]) * TASKS["elic"][2] + N_SESSIONS_WRITE * TASKS["write"][2] + s2_est
              + (TASKS["part12"][2] + TASKS["codebook"][2] if a in roles["part12"] else 0) for a in ids}   # stage 1 + 2
    audit_min = lambda a: sum(TASKS[t][2] for t in tasks[a])  # noqa: E731
    flex = roles["part12"] + roles["regular"]
    hr = hord(ids, "audit")
    count = Counter()
    for t in AUDITS_FLEX:                           # required slots
        for _ in range(REQUIRED[t]):
            elig = [a for a in flex if t not in tasks[a] and audit_min(a) + TASKS[t][2] <= AUDIT_CAP]
            a = min(elig, key=lambda a: (s1_min[a] + audit_min(a), hr.index(a)))
            tasks[a].append(t); count[t] += 1
    while True:                                     # top-up to the floor
        floor = lambda a: AUDIT_FLOOR_PART12 if a in roles["part12"] else AUDIT_FLOOR  # noqa: E731
        low = sorted((a for a in flex if audit_min(a) < floor(a)), key=lambda a: (audit_min(a), hr.index(a)))
        if not low:
            break
        a = low[0]
        opts = [t for t in AUDITS_FLEX if t not in tasks[a] and audit_min(a) + TASKS[t][2] <= AUDIT_CAP]
        if not opts:
            break
        t = min(opts, key=lambda t: (count[t] / REQUIRED[t], AUDITS_FLEX.index(t)))
        tasks[a].append(t); count[t] += 1
    for a in ids:
        tasks[a].sort(key=AUDIT_ORDER.index)
    # Part 7: two dimensions each
    W = hord(ids, "write")
    slots = []                                      # (writer, session, dim)
    for k, a in enumerate(W):
        d1 = k % len(DIMS)
        d2 = (d1 + 1 + (k // len(DIMS)) % (len(DIMS) - 1)) % len(DIMS)
        slots.append([a, 1, DIMS[d1]]); slots.append([a, 2, DIMS[d2]])
    j = Counter()
    writing = {a: [] for a in ids}
    for a, s, d in sorted(slots, key=lambda x: (x[1], W.index(x[0]))):
        rot = WL.rotation(j[d], DIMS.index(d)); j[d] += 1
        writing[a].append({"session": s, "dimension": d, "rot": rot, "n_pairs": PAIRS_PER_SESSION,
                           "fragment": WL.link_fragment(d, rot, PAIRS_PER_SESSION, a), "first_topics": WL.first_topics(rot)})
    for a in ids:
        writing[a].sort(key=lambda x: x["session"])
        if writing[a][0]["rot"] == writing[a][1]["rot"]:     # rotate the second session's topics
            w2 = writing[a][1]
            w2["rot"] = (w2["rot"] + 5) % len(H.TOPICS)
            w2["fragment"] = WL.link_fragment(w2["dimension"], w2["rot"], PAIRS_PER_SESSION, a)
            w2["first_topics"] = WL.first_topics(w2["rot"])
    # Stage 2 checker graph
    R = hord(ids, "check")
    off = offsets_partition(n)
    graph = []
    for i, w in enumerate(R):
        for c in range(6):
            session = 1 + c // 3
            lo = (c % 3) * CHUNK + 1
            for k in range(N_REPLICA):
                chk = R[(i + off[c][k]) % n]
                graph.append({"writer": w, "session": session, "dimension": writing[w][session - 1]["dimension"],
                              "chunk": c, "pair_nos": f"{lo}-{lo + CHUNK - 1}", "replica": k + 1,
                              "offset": off[c][k], "checker": chk, "check_file": f"{chk}_check_{k + 1}"})
    return {"salt": SALT, "annotators": ids, "roles": roles, "role_of": role_of, "dates": DATES,
            "elicitation": {a: [s["file"] for s in elic[a]] for a in ids},
            "elic_sessions": {s["file"]: s for s in sessions},
            "audits": tasks, "writing": writing, "ring": R, "offsets": off, "check_graph": graph,
            "part12_coders": roles["part12"],
            "part12_excluded_sets": sorted({elic_set(f) for a in roles["part12"] for f in [s["file"] for s in elic[a]]}),
            "minutes": TASKS_MIN()}


def select_stage3(plan: dict, tab: dict) -> None:
    """Optional Stage 3 people: the lightest Stage 1+2 loads (ties: hash order), Part 12 coders excluded.
    The 3 lightest do Part 13, the next 6 are tie-breakers (Part 14); the rest, in the same order, are reserves."""
    hs = hord(plan["annotators"], "stage3")
    pool = sorted((a for a in plan["annotators"] if a not in plan["part12_coders"]),
                  key=lambda a: (tab[a]["stage1"] + tab[a]["stage2"], hs.index(a)))
    plan["part13_coders"] = pool[:N_PART13]
    plan["tiebreakers"] = pool[N_PART13:N_PART13 + N_TIEBREAK]
    plan["stage3_reserve"] = pool[N_PART13 + N_TIEBREAK:]


def TASKS_MIN():
    return {k: v[2] for k, v in TASKS.items()}


def elic_set(fname: str) -> str:
    return fname.split("_")[1]


# ---------------------------------------------------------------- rows + checks
def rows_for(plan: dict) -> dict[str, list[dict]]:
    out = {"1": [], "2": [], "3": []}
    for a in plan["annotators"]:
        o = 0
        def add(stage, task, desc, file, minutes, ret, folder, due, **extra):
            nonlocal o
            o += 1
            out[stage].append({"annotator": a, "stage": stage, "order": o, "part": TASKS[task][0], "task": task,
                               "description": desc, "file_or_link": file, "expected_minutes": minutes,
                               "return_file": ret, "return_folder": folder, "due": due, **extra})
        due1, due2 = DATES["stage1_due"], DATES["stage2_due"]
        es = plan["elicitation"][a]
        for i, f in enumerate(es):
            add("1", "elic", f"Keyword elicitation, session {i + 1} of {len(es)} ({plan['elic_sessions'][f]['n_messages']} messages)",
                f"keyword_elicitation.html + elicitation_sets/{f}.json", TASKS["elic"][2],
                f"keyword_elicitation_{f}_{a}.csv", TASKS["elic"][5], due1)
        if any(t in ("parts13", "part10") for t in plan["audits"][a]):
            add("1", "codebook", TASKS["codebook"][1], "CODEBOOK.md", TASKS["codebook"][2], "", "", due1)
        for t in plan["audits"][a]:
            T = TASKS[t]
            add("1", t, T[1], T[3], T[2], T[4].format(ID=a), T[5], due1)
        for w in plan["writing"][a]:
            add("1", "write", f"Write 15 sentence pairs, session {w['session']} of 2: dimension {DIM_LABEL[w['dimension']]}",
                f"write_pairs.html{w['fragment']}", TASKS["write"][2], f"write_pairs_{w['dimension']}_{a}.csv",
                TASKS["write"][5], due1, dimension=w["dimension"], rot=w["rot"])
        o = 0
        files = sorted({g["check_file"] for g in plan["check_graph"] if g["checker"] == a})
        n_pairs = Counter(g["check_file"] for g in plan["check_graph"] if g["checker"] == a)
        for i, f in enumerate(files):
            add("2", "check", f"Check {n_pairs[f] * CHUNK} sentence pairs, file {i + 1} of {len(files)}",
                f"check_pairs.html + stage2/{f}.json", TASKS["check"][2], f"check_pairs_{f}_{a}.csv", TASKS["check"][5], due2)
        if a in plan["part12_coders"]:
            if not any(t in ("parts13", "part10") for t in plan["audits"][a]):
                add("2", "codebook", TASKS["codebook"][1], "CODEBOOK.md", TASKS["codebook"][2], "", "", due2)
            T = TASKS["part12"]
            add("2", "part12", T[1], T[3], T[2], T[4].format(ID=a), T[5], due2)
        o = 0
        due3 = DATES["stage3_due"]
        read_before = any(t in ("parts13", "part10") for t in plan["audits"][a]) or a in plan["part12_coders"]
        if a in plan.get("part13_coders", []):
            if not read_before:
                add("3", "codebook", TASKS["codebook"][1], "CODEBOOK.md", TASKS["codebook"][2], "", "", due3)
            T = TASKS["part13"]
            add("3", "part13", T[1], T[3], T[2], T[4].format(ID=a), T[5], due3)
        if a in plan.get("tiebreakers", []):
            T = TASKS["tiebreak"]; f = f"{a}_tiebreak"
            add("3", "tiebreak", T[1], T[3].format(x=f), T[2], T[4].format(x=f, ID=a), T[5], due3)
    return out


def minutes_table(plan: dict, rows) -> dict[str, dict]:
    tab = {}
    for a in plan["annotators"]:
        r1 = [r for r in rows["1"] if r["annotator"] == a]
        r2 = [r for r in rows["2"] if r["annotator"] == a]
        tab[a] = {"role": plan["role_of"][a],
                  "elic_sessions": len(plan["elicitation"][a]),
                  "elic": sum(r["expected_minutes"] for r in r1 if r["task"] == "elic"),
                  "audits": sum(r["expected_minutes"] for r in r1 if r["task"] not in ("elic", "write")),
                  "write": sum(r["expected_minutes"] for r in r1 if r["task"] == "write"),
                  "stage1": sum(r["expected_minutes"] for r in r1),
                  "stage2": sum(r["expected_minutes"] for r in r2),
                  "stage3": sum(r["expected_minutes"] for r in rows.get("3", []) if r["annotator"] == a),
                  "audit_tasks": " ".join(TASKS[t][0].replace("Part ", "P").replace("Parts ", "P") for t in plan["audits"][a]),
                  "dims": "+".join(w["dimension"] for w in plan["writing"][a])}
        tab[a]["total"] = tab[a]["stage1"] + tab[a]["stage2"] + tab[a]["stage3"]
    return tab


def check_plan(plan: dict, rows) -> dict:
    """Hard constraints (raise) + the coverage summary."""
    ids = plan["annotators"]
    errs = []
    # ordering: elic first, writing last
    for a in ids:
        seq = [r["task"] for r in rows["1"] if r["annotator"] == a]
        first_non = next(i for i, t in enumerate(seq) if t != "elic")
        if any(t == "elic" for t in seq[first_non:]) or seq[0] != "elic":
            errs.append(f"{a}: Part 9 not first")
        lw = [i for i, t in enumerate(seq) if t == "write"]
        if lw != list(range(len(seq) - len(lw), len(seq))) or len(lw) != N_SESSIONS_WRITE:
            errs.append(f"{a}: Part 7 not last / not 2 sessions")
    # elicitation
    allf = [f for a in ids for f in plan["elicitation"][a]]
    if sorted(allf) != sorted(plan["elic_sessions"]):
        errs.append("elicitation: sessions not each assigned exactly once")
    for a in ids:
        st = [elic_set(f) for f in plan["elicitation"][a]]
        if len(st) != len(set(st)):
            errs.append(f"{a}: two replicates of one set")
        if not 2 <= len(st) <= 3:
            errs.append(f"{a}: {len(st)} elicitation sessions")
    per_set = Counter(elic_set(f) for f in allf)
    # audits
    cov = {t: sorted(a for a in ids if t in plan["audits"][a]) for t in REQUIRED}
    for t, need in REQUIRED.items():
        if len(cov[t]) < need:
            errs.append(f"{t}: {len(cov[t])} annotators < {need}")
    heavy = set(plan["roles"]["part10"] + plan["roles"]["parts13"])
    for a in heavy:
        if len(plan["audits"][a]) != 1:
            errs.append(f"{a}: heavy coder with extra audits")
    # writing
    dimw = Counter(w["dimension"] for a in ids for w in plan["writing"][a])
    for a in ids:
        ds = [w["dimension"] for w in plan["writing"][a]]
        if len(set(ds)) != 2:
            errs.append(f"{a}: writing dims {ds}")
        if plan["writing"][a][0]["rot"] == plan["writing"][a][1]["rot"]:
            errs.append(f"{a}: same topic rotation twice")
    if set(dimw) != set(DIMS) or max(dimw.values()) - min(dimw.values()) > 1:
        errs.append(f"dimension coverage uneven {dict(dimw)}")
    # checker graph
    g = plan["check_graph"]
    by_chunk = defaultdict(list)
    for e in g:
        by_chunk[(e["writer"], e["chunk"])].append(e["checker"])
        if e["checker"] == e["writer"]:
            errs.append(f"self-check {e}")
    for k, cs in by_chunk.items():
        if len(set(cs)) != N_REPLICA:
            errs.append(f"chunk {k}: checkers {cs}")
    load = Counter(e["checker"] for e in g)
    fsize = Counter(e["check_file"] for e in g)
    if len(set(load.values())) != 1 or set(fsize.values()) != {6}:
        errs.append(f"checker load uneven {dict(load)}")
    fw = defaultdict(list)
    for e in g:
        fw[e["check_file"]].append(e["writer"])
    if any(len(v) != len(set(v)) for v in fw.values()):
        errs.append("a check file holds two chunks of one writer")
    s3 = plan.get("part13_coders", []) + plan.get("tiebreakers", [])
    if plan.get("part13_coders") is not None:
        if len(plan["part13_coders"]) != N_PART13 or len(plan["tiebreakers"]) != N_TIEBREAK or len(set(s3)) != len(s3):
            errs.append("stage 3 roles wrong")
    if errs:
        raise SystemExit("PLAN CONSTRAINTS FAILED:\n  " + "\n  ".join(errs))
    tab = minutes_table(plan, rows)
    s1 = [v["stage1"] for v in tab.values()]
    return {"coverage": {t: {"required": REQUIRED[t], "n": len(cov[t]), "annotators": " ".join(cov[t])} for t in REQUIRED},
            "elic_sessions_per_set": dict(sorted(per_set.items())),
            "writers_per_dimension": {d: dimw[d] for d in DIMS},
            "pairs_per_dimension": {d: dimw[d] * PAIRS_PER_SESSION for d in DIMS},
            "check_pairs_per_person": {a: load[a] * CHUNK for a in ids},
            "stage1_minutes_min_max": [min(s1), max(s1)],
            "stage2_minutes_min_max": [min(v["stage2"] for v in tab.values()), max(v["stage2"] for v in tab.values())],
            "audit_minutes_min_max_nonheavy": [min(v["audits"] for a, v in tab.items() if a not in heavy),
                                               max(v["audits"] for a, v in tab.items() if a not in heavy)],
            "stage3_people": {"part13": plan.get("part13_coders"), "tiebreak": plan.get("tiebreakers"),
                              "reserve": plan.get("stage3_reserve")},
            "person_hours": {"stage1": round(sum(s1) / 60, 1), "stage2": round(sum(v["stage2"] for v in tab.values()) / 60, 1),
                             "stage3": round(sum(v["stage3"] for v in tab.values()) / 60, 1)},
            "minutes": tab}


# ---------------------------------------------------------------- sheets
RULES = """**Rules (all parts)**
- Work **alone**. Do not discuss any item with anyone until all stages are finished ({END}).
- **No AI tools, chatbots, translation tools or search engines** for any part. Your own judgment is the data.
- Use only the files in `annotation_package/`. Do not open the project repository or any other files.
- Use the same ID, **{ID}**, everywhere. Do the steps **in the order listed**: the order matters for the study.
- Each tool saves progress in your browser, but **click "Download CSV" at the end of every step** and keep the files.
- If something is unclear, write a short note (the tools have note boxes) and carry on; don't ask other annotators."""


LATER = True   # Stage 1 hand-out: Stage 2/3 appear as "coming later" notes (their files are built after Stage 1)


def sheet(plan, rows, tab, a, later: bool = LATER) -> str:
    m = tab[a]
    L = [f"# Task sheet for {a}", "",
         f"You need this sheet and `annotation_package.zip` (unzip it; all files below are in that folder). Stage 1: **{DATES['stage1']}**, due **{DATES['stage1_due']}**. "
         f"Stage 2: opens **{DATES['stage2_open']}**, due **{DATES['stage2_due']}**.", "",
         (f"Expected time: Stage 1 about **{m['stage1']} min** (plus breaks); Stage 2 about 1-2.5 h. " if later else
          f"Expected time: Stage 1 about **{m['stage1']} min**, Stage 2 about **{m['stage2']} min** (plus breaks). ") +
         "Instructions for every part are in `README.md` (section \"Part N\"). Read only the section of the step you are doing.", "",
         RULES.format(ID=a, END=DATES["stage3_due"].split(",")[0]), "",
         f"## Stage 1 ({DATES['stage1']}; send all Stage 1 files by {DATES['stage1_due']})", ""]
    r1 = [r for r in rows["1"] if r["annotator"] == a]
    blocks = {"elic": "**A. Keyword choice first** (before you see any other part: please don't open other tools yet).",
              "audit": "**B. Checks and labels** (in this order).",
              "write": "**C. Writing last.**"}
    cur = None
    for r in r1:
        blk = "elic" if r["task"] == "elic" else "write" if r["task"] == "write" else "audit"
        if blk != cur:
            L += ["", blocks[blk], ""]; cur = blk
        L.append(item_line(r, a))
    L += ["", f"Stage 1 return: email every CSV above to the coordinator by {DATES['stage1_due']} "
          f"(subject `AAC annotation {a} stage 1`), with the time you spent and any notes.", ""]
    if later:
        L += [f"## Stage 2 ({DATES['stage2']}; coming later)", "",
              f"Checking sentence pairs written by other annotators (never your own), and for some people one more "
              f"labelling file. You'll receive instructions and the files on {DATES['stage2_open']} (re-download the zip "
              f"then). Due {DATES['stage2_due']}.", "",
              f"## Stage 3 (optional, {DATES['stage3']}; coming later)", "",
              "Some annotators will be asked for about one more hour (labels or a few extra checks). You'll receive "
              f"instructions if this applies to you. Due {DATES['stage3_due']}.", "",
              "Thank you! Your work is anonymous: only your ID is recorded. You can stop at any time."]
        return "\n".join(L) + "\n"
    L += [
          f"## Stage 2 ({DATES['stage2']}; send all Stage 2 files by {DATES['stage2_due']})", "",
          f"The Stage 2 files are not in the zip yet: each file arrives at `annotation_package/stage2/...`; "
          f"**re-download the zip on {DATES['stage2_open']}** (the coordinator will tell you when) and use the new folder.", ""]
    for r in [r for r in rows["2"] if r["annotator"] == a]:
        L.append(item_line(r, a))
    L += ["", f"Stage 2 return: email every CSV above to the coordinator by {DATES['stage2_due']} "
          f"(subject `AAC annotation {a} stage 2`).", ""]
    r3 = [r for r in rows.get("3", []) if r["annotator"] == a]
    if r3:
        L += [f"## Stage 3 (OPTIONAL, {DATES['stage3']}; send by {DATES['stage3_due']})", "",
              f"Only if you can spare about {m['stage3']} more minutes. If you can't, tell the coordinator by "
              f"{DATES['stage2_due']} so a reserve can be asked. The files arrive at `annotation_package/stage3/...`; "
              f"**re-download the zip on {DATES['stage3_open']}**.", ""]
        L += [item_line(r, a) for r in r3]
        L += ["", f"Stage 3 return: email the CSVs to the coordinator by {DATES['stage3_due']} "
              f"(subject `AAC annotation {a} stage 3`).", ""]
    L += ["Thank you! Your work is anonymous: only your ID is recorded. You can stop at any time."]
    return "\n".join(L) + "\n"


def item_line(r, a) -> str:
    t = r["task"]
    label = f"{r['part']}: " if r["part"] != "-" else ""
    head = f"- [ ] **{r['order']}. {label}{r['description']}** (about {r['expected_minutes']} min)"
    if t == "elic":
        body = (f"Open `keyword_elicitation.html`, click **Message file**, choose `{r['file_or_link'].split(' + ')[1]}`, "
                f"enter `{a}`. README: Part 9.")
    elif t == "write":
        frag = r["file_or_link"][len("write_pairs.html"):]
        body = (f"Open `write_pairs.html`, add `{frag}` to the end of the address in the address bar, press Enter, then "
                f"**reload the page** (F5). The page then shows dimension *{DIM_LABEL[r['dimension']]}* and your ID. "
                "README: Part 7 (includes the CC BY 4.0 release you agree to in the tool).")
    elif t == "check":
        f = r["file_or_link"].split(" + ")[1]
        body = (f"Open `check_pairs.html`, click **Check file**, choose `{f}`, enter `{a}`. "
                "README: Part 8.")
    elif t == "codebook":
        body = "About 10 minutes, once. Short definitions also stay on screen in the tool."
    elif t == "parts13":
        body = (f"Open `annotate.html`, enter `{a}`, load `part1_core.json` and do the 5 practice items, then all items; "
                "Download CSV. Repeat with `part2_extraA.json` and `part3_extraB.json`. The browser names all three "
                f"`labels_main1_{a}.csv` (the 2nd and 3rd may get `(1)`, `(2)` added); rename them to the names under Return. README: Setup and Parts 1-3.")
    elif t in ("part10", "part12", "part13"):
        f = r["file_or_link"].split(" + ")[1]
        when = {"part12": "", "part13": f" (arrives on {DATES['stage3_open']})"}.get(t, "")
        body = (f"Open `annotate.html`, enter `{a}`, load `{f}`{when}, do the 5 practice items, then every item. "
                f"README: Part 10{' (this part is the same task on a new file)' if t != 'part10' else ''}.")
    elif t == "tiebreak":
        f = r["file_or_link"].split(" + ")[1]
        body = (f"Open `check_pairs.html`, click **Check file**, choose `{f}` (arrives on {DATES['stage3_open']}), enter `{a}`. "
                "Same task as Part 8 (README: Part 8). Your file may be empty: if the tool says \"This is not a check file "
                "(no check_id or items)\", you have no pairs and nothing to do or send.")
    elif t == "intent":
        body = (f"Open `intent_check.html`, choose `stage4/{a}_intent.json`, enter `{a}`. Do this first: it needs nothing else. "
                "README: Part 18.")
    elif t == "part19":
        body = (f"Open `annotate.html`, enter `{a}`, load `stage4/{a}_part19.json`, do the 5 practice items, then every item "
                "(about 13 sentences). Same tool and questions as Part 10 (README: Part 10 and Part 19). Label only what the "
                "words on the page say; the codebook is not needed for this part, the short definitions on the screen are "
                "enough. Click **Download CSV** at the end. The file name will be `labels_part19_" + a + ".csv`.")
    elif t == "write2":
        frag = r["file_or_link"][len("write_pairs.html"):]
        body = (f"Open `write_pairs.html`, add `{frag}` to the end of the address in the address bar, press Enter, then "
                f"**reload the page** (F5). The page shows dimension *speech act* and your ID. Same tool and rules as Part 7 "
                "(README: Part 7, including the CC BY 4.0 release you agree to in the tool). "
                "**Write every sentence yourself: do not copy, reuse, adapt or paraphrase any sentence you have seen "
                "anywhere (earlier parts, examples in the tool, model sentences from Part 18, anyone else's work).** "
                "Your pairs are compared with every earlier pair, and near-copies are rejected.")
    elif t == "repair2":
        body = (f"Open your own file `stage4/repair_audit_v2_{a}.html` (everything is inside it), enter `{a}`. Same task as "
                "Part 4, with 80 sentences. README: Part 17.")
    elif t == "check2":
        f = r["file_or_link"].split(" + ")[1]
        body = (f"Open `check_pairs.html`, click **Check file**, choose `{f}` (arrives {DATES['stage4_check_open']}; "
                "re-download the zip then, the file in the zip before that is an empty placeholder), enter "
                f"`{a}`. Same task as Part 8 (README: Part 8). You never get a pair you wrote.")
    else:
        body = f"Open `{r['file_or_link']}`, enter `{a}`. README: {r['part']}."
    ret = f" Return: `{r['return_file']}`." if r["return_file"] else ""
    return f"{head}  \n  {body}{ret}"


def stage2_readme(plan) -> str:
    return ("# Stage 2 files\n\n"
            "- `<ID>_check_1.json`, `<ID>_check_2.json`, `<ID>_check_3.json`: your Part 8 check files (sentence pairs "
            "written by other annotators; never your own). Open them with `../check_pairs.html`.\n"
            "- `part12_gold_elic.json`: the Part 12 labelling file, for the annotators whose sheet lists Part 12. "
            "Open it with `../annotate.html`.\n\n"
            "Follow your sheet `assignments/<ID>_stage2.md`. Due " + DATES["stage2_due"] + ".\n")


def stage3_readme(plan) -> str:
    return (f"# Stage 3 files (optional; arrive {DATES['stage3_open']})\n\n"
            "This folder is empty until Stage 2 is finished. On " + DATES["stage3_open"] + " it holds:\n\n"
            "- `part13_gold_hw.json`: the Part 13 labelling file (open with `../annotate.html`), for the annotators "
            "whose sheet lists Part 13.\n"
            "- `<ID>_tiebreak.json`: Part 14 tie-break check files (open with `../check_pairs.html`), for the annotators "
            "whose sheet lists Part 14. A file can be empty (0 pairs): then there is nothing to do.\n\n"
            "Re-download `annotation_package.zip` on " + DATES["stage3_open"] + ". Due " + DATES["stage3_due"] + ".\n")


def handout(plan, tab, later: bool = LATER) -> str:
    """Stage 1 hand-out text; once the Stage 4 roster exists (stage4_plan.json) its section is included, so a
    regeneration reproduces the committed HANDOUT.md."""
    txt = _handout_stage1(plan, tab, later)
    if S4_PLAN.exists():
        s4 = json.loads(S4_PLAN.read_text())
        txt = insert_stage4_section(txt, stage4_handout_section(s4, rows_stage4(s4, plan["annotators"])))
    if (ASSIGN_DIR / "stage5.csv").exists():
        txt = insert_stage5_section(txt, stage5_handout_section(rows_stage5(plan["annotators"])))
    return txt


def _handout_stage1(plan, tab, later: bool = LATER) -> str:
    ids = plan["annotators"]
    if later:
        return f"""# Hand-out (coordinator, one page)

**What to send each annotator** (now, once): `annotation_package.zip` and their own sheet
`annotation_package/assignments/<ID>.md` (also inside the zip). IDs: {ids[0]}-{ids[-1]}. Send nothing else; never send
files from `annotation/` (answer keys, model labels).

**Deadlines**
- **Stage 1** (handed out for {DATES['stage1']}): **all returned {DATES['stage2_open']}**. Keyword choice first, then checks/labels, then writing:
  the order on the sheet is mandatory. About {min(v['stage1'] for v in tab.values())}-{max(v['stage1'] for v in tab.values())} min each, plus breaks.
- **Stage 2** (opens **{DATES['stage2_open']}**): due **{DATES['stage2_due']}**. Instructions and files sent {DATES['stage2_open']}
  (annotators re-download the zip).
- Stage 3 (optional, {DATES['stage3']}) for a few people; instructions later.

**Return method:** annotators email the CSVs named on their sheet, unchanged, to the coordinator: one email per stage,
subject `AAC annotation <ID> stage <N>`, with the time spent and any notes. The coordinator saves each file into the
`return_folder` given in `annotation/assignments/stage1.csv` and commits it.

**Rules to repeat when sending:** work alone; no AI tools or search engines; use only the package; same ID everywhere;
follow the order on the sheet. Part 7 asks writers to release their sentences under CC BY 4.0 (consent box in the tool).
"""
    return f"""# Hand-out (coordinator, one page)

**What to send each annotator** (today, once): `annotation_package.zip` and their own sheet
`annotation_package/assignments/<ID>.md` (also inside the zip). IDs: {ids[0]}-{ids[-1]}. Nothing else; never send
files from `annotation/` (keys, model labels).

**Two deadlines**
- **Stage 1** ({DATES['stage1']}): due **{DATES['stage1_due']}**. Keyword choice first, then checks/labels, then writing
  (the order on the sheet is mandatory). About {min(v['stage1'] for v in tab.values())}-{max(v['stage1'] for v in tab.values())} min.
- **Stage 2** (opens **{DATES['stage2_open']}**): due **{DATES['stage2_due']}**. Checking other people's pairs (3 files each) and,
  for {len(plan['part12_coders'])} people, Part 12. About {min(v['stage2'] for v in tab.values())}-{max(v['stage2'] for v in tab.values())} min.
  Stage 2 files appear in `stage2/` of the zip; tell everyone to **re-download the zip on {DATES['stage2_open']}**.

- **Stage 3, optional** (opens **{DATES['stage3_open']}**): due **{DATES['stage3_due']}**. Part 13 for
  {', '.join(plan['part13_coders'])}; Part 14 tie-breaks for {', '.join(plan['tiebreakers'])}. Reserves if someone declines,
  in order: {', '.join(plan['stage3_reserve']) or 'none'}. Files appear in `stage3/`; re-download the zip on {DATES['stage3_open']}.
  Feeds CALE-AI; SE4All only if back on time.

**Return method:** annotators email the CSVs named on their sheet (unchanged) to the coordinator, one email per stage,
subject `AAC annotation <ID> stage <1|2>`, with time spent and notes. The coordinator saves each file into the
`return_folder` given in `annotation/assignments/stage{{1,2}}.csv` and commits it.

**Rules to repeat when sending:** work alone; no AI tools or search engines; use only the package; same ID everywhere;
follow the order. Consent: Part 7 asks writers to release their sentences under CC BY 4.0 (in the tool).

**Between the stages (coordinator):** `annotation/assignments/COORDINATOR.md` (commands only).
"""


# ---------------------------------------------------------------- writing outputs
def write_csv(path: Path, rows: list[dict], fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def run_stage1(ids, out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR, out_stage2=STAGE2_DIR, written=WRITTEN,
               elic_assign=ROOT / "annotation" / "elicitation_assignment.csv", pkg=PKG, quiet=False) -> dict:
    plan = build_plan(ids)
    rows = rows_for(plan)
    select_stage3(plan, minutes_table(plan, rows))
    rows = rows_for(plan)
    summ = check_plan(plan, rows)
    cols = ["annotator", "stage", "order", "part", "task", "description", "file_or_link", "expected_minutes",
            "return_file", "return_folder", "due"]
    write_csv(out_assign / "stage1.csv", rows["1"], cols)
    if not LATER:
        write_csv(out_assign / "stage2.csv", rows["2"], cols)
        write_csv(out_assign / "stage3.csv", rows["3"], cols)
    if not LATER:
        write_csv(out_assign / "check_graph.csv", plan["check_graph"])
        (out_assign / "part12_coders.txt").write_text("\n".join(plan["part12_coders"]) + "\n")
    (out_assign / "plan.json").write_text(json.dumps({k: v for k, v in plan.items()}, indent=1) + "\n")
    (out_assign / "coverage.json").write_text(json.dumps({k: v for k, v in summ.items()}, indent=1) + "\n")
    write_csv(written / "writer_assignment.csv",
              [{"writer_id": a, "dimension": w["dimension"], "rot": w["rot"], "n_pairs": w["n_pairs"],
                "first_topics": w["first_topics"], "link_fragment": w["fragment"], "session": w["session"]}
               for a in ids for w in plan["writing"][a]],
              ["writer_id", "dimension", "rot", "n_pairs", "first_topics", "link_fragment", "session"])
    er = sorted(({"set": s["set"], "replicate": s["replicate"], "file": f"elicitation_sets/{f}.json",
                  "n_messages": s["n_messages"], "annotator": a}
                 for a in ids for f in plan["elicitation"][a] for s in [plan["elic_sessions"][f]]),
                key=lambda r: (r["replicate"], r["set"]))
    write_csv(elic_assign, er, ["set", "replicate", "file", "n_messages", "annotator"])
    tab = summ["minutes"]
    if not LATER:
        out_stage3 = out_stage2.parent / "stage3"
        out_stage3.mkdir(parents=True, exist_ok=True)
        (out_stage3 / "README.md").write_text(stage3_readme(plan))
        out_stage2.mkdir(parents=True, exist_ok=True)
        (out_stage2 / "README.md").write_text(stage2_readme(plan))
    out_sheets.mkdir(parents=True, exist_ok=True)
    for a in ids:
        (out_sheets / f"{a}.md").write_text(sheet(plan, rows, tab, a))
    (pkg / "HANDOUT.md").write_text(handout(plan, tab, LATER))
    if not quiet:
        report(plan, summ)
    return {"plan": plan, "rows": rows, "summary": summ}


def report(plan, summ):
    tab = summ["minutes"]
    print("annotator role     elic(n) audits write stage1 stage2 total  audit tasks / writing dims")
    for a in plan["annotators"]:
        v = tab[a]
        print(f"{a:9} {v['role']:8} {v['elic']:4}({v['elic_sessions']}) {v['audits']:6} {v['write']:5} {v['stage1']:6} "
              f"{v['stage2']:6} {v['total']:5}  {v['audit_tasks']} / {v['dims']}")
    print("stage 1 minutes min/max:", summ["stage1_minutes_min_max"], "; stage 2:", summ["stage2_minutes_min_max"],
          "; audit minutes (non-heavy) min/max:", summ["audit_minutes_min_max_nonheavy"], "; person-hours:", summ["person_hours"])
    print("coverage:", {t: f"{v['n']}/{v['required']}" for t, v in summ["coverage"].items()})
    print("elic sessions per set:", set(summ["elic_sessions_per_set"].values()), "; writers per dim:", summ["writers_per_dimension"],
          "; pairs per dim:", summ["pairs_per_dimension"])
    print("stage 3:", summ["stage3_people"])
    print("check pairs per person:", set(summ["check_pairs_per_person"].values()), "; Part 12 coders:", plan["part12_coders"],
          "; Part 12 excluded sets:", plan["part12_excluded_sets"])


# ---------------------------------------------------------------- Stage 2/3 sheets from the frozen plan
def later_sheet(plan, rows, tab, a, stage: str) -> str | None:
    rs = [r for r in rows[stage] if r["annotator"] == a]
    if not rs:
        return None
    if stage == "2":
        title = f"# Stage 2 task sheet for {a} ({DATES['stage2']}; due {DATES['stage2_due']})"
        intro = (f"Download the current `annotation_package.zip`: your files are in its `stage2/` folder. "
                 f"About **{tab[a]['stage2']} min**.")
    else:
        title = f"# Stage 3 task sheet for {a} (OPTIONAL, {DATES['stage3']}; due {DATES['stage3_due']})"
        intro = (f"Only if you can spare about **{tab[a]['stage3']} min**; if not, tell the coordinator by "
                 f"{DATES['stage2_due']} so a reserve can be asked. Re-download `annotation_package.zip` on "
                 f"{DATES['stage3_open']}: your files are in its `stage3/` folder.")
    L = [title, "", intro, "", RULES.format(ID=a, END=DATES["stage3_due"].split(",")[0]), "", "## Steps (in this order)", ""]
    L += [item_line(r, a) for r in rs]
    L += ["", f"Return: email every CSV above to the coordinator by {DATES[f'stage{stage}_due']} "
          f"(subject `AAC annotation {a} stage {stage}`), with the time you spent and any notes.", "",
          "Thank you! Your work is anonymous: only your ID is recorded. You can stop at any time."]
    return "\n".join(L) + "\n"


def prepare_later(plan_path=ASSIGN_DIR / "plan.json", out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR,
                  out_stage2=STAGE2_DIR, out_stage3=STAGE3_DIR) -> dict:
    """Write the Stage 2/3 sheets, CSVs and folder READMEs from the frozen plan.json (Stage 1 files untouched)."""
    plan = json.loads(Path(plan_path).read_text())
    rows = rows_for(plan)
    tab = minutes_table(plan, rows)
    cols = ["annotator", "stage", "order", "part", "task", "description", "file_or_link", "expected_minutes",
            "return_file", "return_folder", "due"]
    write_csv(out_assign / "stage2.csv", rows["2"], cols)
    write_csv(out_assign / "stage3.csv", rows["3"], cols)
    write_csv(out_assign / "check_graph.csv", plan["check_graph"])
    (out_assign / "part12_coders.txt").write_text("\n".join(plan["part12_coders"]) + "\n")
    (out_assign / "stage3_people.json").write_text(json.dumps(
        {"part13": plan["part13_coders"], "tiebreak": plan["tiebreakers"], "reserve": plan["stage3_reserve"]}, indent=1) + "\n")
    out_sheets.mkdir(parents=True, exist_ok=True)
    n = Counter()
    for a in plan["annotators"]:
        for st in ("2", "3"):
            txt = later_sheet(plan, rows, tab, a, st)
            if txt:
                (out_sheets / f"{a}_stage{st}.md").write_text(txt); n[st] += 1
    out_stage2.mkdir(parents=True, exist_ok=True); out_stage3.mkdir(parents=True, exist_ok=True)
    (out_stage2 / "README.md").write_text(stage2_readme(plan))
    (out_stage3 / "README.md").write_text(stage3_readme(plan))
    print(f"stage 2 sheets {n['2']}, stage 3 sheets {n['3']} -> {out_sheets}; stage 2 min "
          f"{min(v['stage2'] for v in tab.values())}-{max(v['stage2'] for v in tab.values())}; stage 3 "
          f"{ {a: v['stage3'] for a, v in tab.items() if v['stage3']} }")
    return {"rows": rows, "minutes": tab}


# ---------------------------------------------------------------- Stage 2 fill
def chunk_of(pair_no: int) -> int:
    return min(2, (int(pair_no) - 1) // CHUNK)


def _match(chunks, slots, ok):
    """Deterministic bipartite matching (Kuhn), chunks and slots in the given orders."""
    owner = {}
    def try_(i, seen):
        for j, s in enumerate(slots):
            if j in seen or not ok(chunks[i], s):
                continue
            seen.add(j)
            if j not in owner or try_(owner[j], seen):
                owner[j] = i
                return True
        return False
    for i in range(len(chunks)):
        try_(i, set())
    return {i: slots[j] for j, i in owner.items()}


def fill_stage2(plan: dict, cands: list[dict], absent=(), still_checking=(), returned_writers=None) -> dict:
    """Map accepted candidates onto the fixed graph; returns {file -> [family ids]}, assignment, log."""
    ids, R = plan["annotators"], plan["ring"]
    sess = {(a, w["dimension"]): w["session"] for a in ids for w in plan["writing"][a]}
    members = defaultdict(list)        # (writer, chunk) -> family ids
    log = []
    for c in sorted(cands, key=lambda c: c["family_id"]):
        w, d = c["writer_id"], c["writer_dimension"]
        s = sess.get((w, d))
        if s is None:
            log.append(f"{c['family_id']}: writer {w} dimension {d} not in the plan; not checked"); continue
        members[(w, 3 * (s - 1) + chunk_of(c["writer_pair_no"]))].append(c["family_id"])
    n_by_writer = Counter(w for (w, _), fs in members.items() for _ in fs)
    missing = [w for w in R if n_by_writer[w] == 0]
    returned = set(returned_writers) if returned_writers is not None else set(n_by_writer)
    absent_set = (set(absent) | {w for w in missing if w not in returned}) - set(still_checking)
    edges = [dict(e) for e in plan["check_graph"]]   # chunk-replica -> checker/file
    for e in edges:
        e["reassigned"] = ""
    # freed slots: edges whose writer is missing, checker present
    freed = [e for e in edges if e["writer"] in missing and e["checker"] not in absent_set]
    for d in sorted(absent_set, key=R.index):
        todo = [e for e in edges if e["checker"] == d and e["writer"] not in missing and members.get((e["writer"], e["chunk"]))]
        cur = defaultdict(set)
        for e in edges:
            cur[(e["writer"], e["chunk"])].add(e["checker"])
        own = sorted([f for f in freed if f["writer"] == d], key=lambda f: (R.index(f["checker"]), f["replica"]))
        def ok(e, f):
            return f["checker"] != e["writer"] and f["checker"] not in cur[(e["writer"], e["chunk"])] and f["checker"] not in absent_set
        m = _match(todo, own, ok)
        used = set()
        for i, e in enumerate(todo):
            if i in m:
                f = m[i]; used.add(id(f))
                log.append(f"absent {d}: {e['writer']} chunk {e['chunk']} r{e['replica']} -> {f['checker']} ({f['check_file']}, freed by {d})")
                e["checker"], e["check_file"], e["reassigned"] = f["checker"], f["check_file"], f"from {d} (freed slot)"
            else:
                load = Counter()
                for x in edges:
                    if x["checker"] not in absent_set:
                        load[x["checker"]] += len(members.get((x["writer"], x["chunk"]), []))
                elig = [p for p in R if p not in absent_set and p != e["writer"] and p not in cur[(e["writer"], e["chunk"])]]
                if not elig:
                    log.append(f"absent {d}: {e['writer']} chunk {e['chunk']} r{e['replica']}: no eligible checker; 2 checks only")
                    e["checker"], e["check_file"], e["reassigned"] = "", "", f"from {d}: unfilled"
                    continue
                p = min(elig, key=lambda p: (load[p], R.index(p)))
                fl = Counter()
                for x in edges:
                    if x["checker"] == p:
                        fl[x["check_file"]] += len(members.get((x["writer"], x["chunk"]), []))
                files = [f"{p}_check_{k}" for k in range(1, N_REPLICA + 1)]
                f = min(files, key=lambda f: (fl[f], f))
                log.append(f"absent {d}: {e['writer']} chunk {e['chunk']} r{e['replica']} -> {p} ({f}, lowest load)")
                e["checker"], e["check_file"], e["reassigned"] = p, f, f"from {d} (lowest load)"
            cur[(e["writer"], e["chunk"])] = {x["checker"] for x in edges if (x["writer"], x["chunk"]) == (e["writer"], e["chunk"])}
        freed = [f for f in freed if id(f) not in used]
    files = defaultdict(list)
    for e in edges:
        if e["checker"] and e["checker"] not in absent_set and e["writer"] not in missing:
            files[e["check_file"]] += members.get((e["writer"], e["chunk"]), [])
    # invariant checks
    checkers_of = defaultdict(list)
    for f, fids in files.items():
        for fid in fids:
            checkers_of[fid].append(f.rsplit("_check_", 1)[0])
    fam_writer = {c["family_id"]: c["writer_id"] for c in cands}
    for fid, cs in checkers_of.items():
        assert fam_writer[fid] not in cs, (fid, cs)
        assert len(cs) == len(set(cs)), (fid, cs)
    return {"files": dict(files), "edges": edges, "missing_writers": missing, "absent": sorted(absent_set),
            "log": log, "checkers_of": checkers_of, "members": {f"{w}|{c}": v for (w, c), v in members.items()}}


def run_stage2(plan_path=ASSIGN_DIR / "plan.json", cand_path=WRITTEN / "hw_candidates.jsonl", out_stage2=STAGE2_DIR,
               key_path=WRITTEN / "check_key.csv", out_assign=ASSIGN_DIR, absent=(), still_checking=(),
               returns_glob=str(ROOT / "annotation" / "returns_written" / "write_pairs_*_*.csv")) -> dict:
    import make_check_batches as MB
    plan = json.loads(Path(plan_path).read_text())
    cands = [json.loads(l) for l in Path(cand_path).open() if l.strip()]
    by = {c["family_id"]: c for c in cands}
    returned = {Path(p).stem.rsplit("_", 1)[1] for p in glob.glob(returns_glob)} if returns_glob else None
    res = fill_stage2(plan, cands, absent, still_checking, returned)
    out_stage2.mkdir(parents=True, exist_ok=True)
    for old in out_stage2.glob("*_check_*.json"):
        old.unlink()
    fill_rows = []
    for f, fids in sorted(res["files"].items()):
        if not fids:
            continue
        items = []
        for fid in sorted(fids, key=MB.item_id):
            c = by[fid]
            items.append({"item_id": MB.item_id(fid), "dimension": c["dimension"], "options": c["critical_options"],
                          "context": c["context"], "A": c["variants"]["A"]["source"], "B": c["variants"]["B"]["source"],
                          "bare": c["bare"], "noncritical": c["noncritical"]})
        assert all(set(x) == set(MB.BLIND_FIELDS) for x in items)
        writers = sorted({by[x]["writer_id"] for x in fids})
        doc = {"check_id": f, "tool": MB.TOOL, "version": 1, "n_items": len(items),
               "exclude": sorted(MB.id_hash(w) for w in writers), "items": items}
        (out_stage2 / f"{f}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        fill_rows.append({"check_id": f, "file": f"annotation_package/stage2/{f}.json", "checker": f.rsplit("_check_", 1)[0],
                          "n_pairs": len(items), "writers": " ".join(writers),
                          "dimensions": " ".join(f"{k}:{v}" for k, v in sorted(Counter(by[x]["dimension"] for x in fids).items()))})
    files_of = defaultdict(list)
    for f, fids in res["files"].items():
        for x in fids:
            files_of[x].append(f)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "check_id", "family_id", "writer_id", "dimension", "value_A", "value_B", "source_A", "source_B", "bare"])
        for fid in sorted(by):
            c = by[fid]
            w.writerow([MB.item_id(fid), " ".join(sorted(files_of.get(fid, []))), fid, c["writer_id"], c["dimension"],
                        c["variants"]["A"]["critical_value"], c["variants"]["B"]["critical_value"],
                        c["variants"]["A"]["source"], c["variants"]["B"]["source"], c["bare"]])
    write_csv(out_assign / "stage2_fill.csv", fill_rows, ["check_id", "file", "checker", "n_pairs", "writers", "dimensions"])
    n_checks = Counter(len(v) for v in res["checkers_of"].values())
    unchecked = [fid for fid in by if fid not in res["checkers_of"]]
    summ = {"candidates": len(cands), "files_written": len(fill_rows), "pairs_by_n_checkers": dict(n_checks),
            "not_in_any_file": unchecked, "missing_writers": res["missing_writers"], "absent": res["absent"],
            "load_pairs": {r["checker"]: 0 for r in fill_rows}, "log": res["log"]}
    for r in fill_rows:
        summ["load_pairs"][r["checker"]] += r["n_pairs"]
    (out_assign / "stage2_fill.json").write_text(json.dumps(summ, indent=1) + "\n")
    lp = list(summ["load_pairs"].values())
    print(f"{len(cands)} candidates -> {len(fill_rows)} check files in {out_stage2}; pairs by #checkers {dict(n_checks)}; "
          f"load per checker min {min(lp, default=0)} max {max(lp, default=0)}; missing writers {res['missing_writers']}; "
          f"absent {res['absent']}")
    for l in res["log"]:
        print(" ", l)
    if unchecked:
        print(f"warning: {len(unchecked)} candidate(s) in no file: {unchecked[:10]}")
    return summ


# ---------------------------------------------------------------- Stage 3 routing (tie-breaks)
def route_tiebreaks(plan: dict, items: list[dict], planned: dict, absent=(), cap: int = TIEBREAK_CAP) -> dict:
    """Deterministic Part 14 routing. items = rows of analysis/hw_checks/items.csv (Stage 2 scoring);
    planned = family_id -> checkers whose Stage 2 files held the pair.
      need    priority 1: pairs with n_checks < 3 (a checker did not return / a check was dropped): 3 - n_checks
              extra checks; priority 2: pairs with a 2-1 split (n_checks == 3, n_pass == 2), the only split a 4th
              check can change under the majority rule (3/4 keep, 2/4 drop); 1-2 splits stay dropped.
      order   priority, then sha1(SALT|tiebreak|family_id).
      who     the tie-breaker (plan order) with the lowest current load among those who are not the writer, not a
              planned or actual checker of the pair, not already routed this pair, not absent, below cap.
    Overflow (no eligible tie-breaker below cap) is listed, never forced."""
    tbs = [t for t in plan["tiebreakers"] if t not in set(absent)]
    need = []
    for r in items:
        n, k = int(r["n_checks"]), int(r["n_pass"])
        if n < 3:
            need.append((1, r, 3 - n))
        elif n == 3 and k == 2:
            need.append((2, r, 1))
    need.sort(key=lambda x: (x[0], sha(f"{SALT}|tiebreak|{x[1]['family_id']}")))
    load, routed, overflow = Counter(), defaultdict(list), []
    for pri, r, k in need:
        fid = r["family_id"]
        excl = {r["writer_id"]} | set((r.get("checkers") or "").split()) | set(planned.get(fid, []))
        for _ in range(k):
            elig = [t for t in tbs if t not in excl and load[t] < cap]
            if not elig:
                overflow.append({"family_id": fid, "priority": pri}); break
            t = min(elig, key=lambda t: (load[t], tbs.index(t)))
            routed[t].append(fid); load[t] += 1; excl.add(t)
    return {"routed": {t: routed.get(t, []) for t in plan["tiebreakers"]}, "overflow": overflow,
            "n_need": {1: sum(1 for x in need if x[0] == 1), 2: sum(1 for x in need if x[0] == 2)}, "absent": sorted(absent)}


def run_stage3(plan_path=ASSIGN_DIR / "plan.json", items_path=ROOT / "analysis" / "hw_checks" / "items.csv",
               key_path=WRITTEN / "check_key.csv", cand_path=WRITTEN / "hw_candidates.jsonl", out_stage3=STAGE3_DIR,
               out_assign=ASSIGN_DIR, absent=()) -> dict:
    import make_check_batches as MB
    plan = json.loads(Path(plan_path).read_text())
    with open(items_path, newline="", encoding="utf-8") as f:
        items = list(csv.DictReader(f))
    with open(key_path, newline="", encoding="utf-8") as f:
        key = list(csv.DictReader(f))
    planned = defaultdict(list)
    for k in key:
        for cid in (k.get("check_id") or "").split():
            if "_check_" in cid:
                planned[k["family_id"]].append(cid.rsplit("_check_", 1)[0])
    by = {c["family_id"]: c for c in map(json.loads, Path(cand_path).open()) if c}
    res = route_tiebreaks(plan, items, planned, absent)
    out_stage3.mkdir(parents=True, exist_ok=True)
    rows = []
    for t, fids in res["routed"].items():
        if t in res["absent"]:
            continue
        cid = f"{t}_tiebreak"
        its = []
        for fid in sorted(fids, key=MB.item_id):
            c = by[fid]
            its.append({"item_id": MB.item_id(fid), "dimension": c["dimension"], "options": c["critical_options"],
                        "context": c["context"], "A": c["variants"]["A"]["source"], "B": c["variants"]["B"]["source"],
                        "bare": c["bare"], "noncritical": c["noncritical"]})
        writers = sorted({by[x]["writer_id"] for x in fids})
        doc = {"check_id": cid, "tool": MB.TOOL, "version": 1, "n_items": len(its),
               "exclude": sorted(MB.id_hash(w) for w in writers), "items": its}
        (out_stage3 / f"{cid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        rows.append({"check_id": cid, "file": f"annotation_package/stage3/{cid}.json", "checker": t, "n_pairs": len(its),
                     "writers": " ".join(writers)})
    # extend the key's check_id column so returns are traceable
    tb_of = defaultdict(list)
    for t, fids in res["routed"].items():
        for x in fids:
            tb_of[x].append(f"{t}_tiebreak")
    for k in key:
        extra = [c for c in tb_of.get(k["family_id"], []) if c not in (k["check_id"] or "").split()]
        k["check_id"] = " ".join(filter(None, [k["check_id"]] + extra))
    write_csv(Path(key_path), key, list(key[0]) if key else None)
    write_csv(out_assign / "stage3_fill.csv", rows, ["check_id", "file", "checker", "n_pairs", "writers"])
    (out_assign / "stage3_fill.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"tie-break need: {res['n_need']} (1 = missing checks, 2 = 2-1 splits); routed "
          f"{ {t: len(v) for t, v in res['routed'].items()} }; overflow {len(res['overflow'])} -> {out_stage3}")
    return res


# ---------------------------------------------------------------- Stage 4 (D-058)
S4_COLS = ["annotator", "stage", "order", "part", "task", "description", "file_or_link", "expected_minutes",
           "return_file", "return_folder", "due"]


def select_stage4(plan: dict, tab: dict, prior_writers: dict[str, set], used_rots: set, writers=None, raters=None,
                  checkers=None) -> dict:
    """Roster for Stage 4.
    writers  4 people who never wrote speech_act in Stage 1 (and not P06, whose speech-act pair is excluded, D-058);
             preferring people NOT in the Part 17 rater list, then the lowest total Stage 1-3 planned load, then hash.
             Topic rotations are the speech-act rotations not used by any earlier speech-act writer.
    checkers 6 people who are neither Part 15 writers nor Part 17 raters, lowest load, hash tie-break; the rest of that
             pool are ordered reserves (used by --absent in the check fill)."""
    ids = plan["annotators"]
    raters = list(raters or PART17_RATERS)
    load = {a: tab[a]["total"] for a in ids}
    hs = hord(ids, "stage4")
    key = lambda a: (a in raters, load[a], hs.index(a))  # noqa: E731
    never = [a for a in ids if a not in prior_writers.get("speech_act", set()) and a != "P06"]
    if writers:
        bad = [w for w in writers if w not in never]
        if bad:
            raise SystemExit(f"Part 15 writers must never have written speech_act and not be P06: {bad}")
        writers = list(writers)
    else:
        writers = sorted(never, key=key)[:N_S4_WRITERS]
    if len(writers) != N_S4_WRITERS and not writer_override_ok(writers):
        raise SystemExit(f"need {N_S4_WRITERS} Part 15 writers, got {writers}")
    free = [r for r in range(len(H.TOPICS)) if r not in used_rots]
    if len(free) < len(writers):
        raise SystemExit(f"only {len(free)} unused speech_act topic rotations for {len(writers)} writers")
    rot = {w: free[i] for i, w in enumerate(sorted(writers, key=lambda a: hs.index(a)))}
    pool = sorted((a for a in ids if a not in writers and a not in raters), key=lambda a: (load[a], hs.index(a)))
    if checkers:
        checkers = list(checkers)
        bad = [c for c in checkers if c in writers or c in raters]
        if bad:
            raise SystemExit(f"Part 16 checkers must not be Part 15 writers or Part 17 raters: {bad}")
    else:
        checkers = pool[:N_S4_CHECKERS]
    reserve = [a for a in pool if a not in checkers]
    return {"salt": SALT, "batch": S4_BATCH, "writers": writers, "writer_rot": rot, "raters": raters, "checkers": checkers,
            "check_reserve": reserve, "absent_checkers": [], "everyone_part18": list(ids),
            "load_before_stage4": load, "speech_act_rotations_used_before": sorted(used_rots), "dates": {
                k: v for k, v in DATES.items() if k.startswith("stage4")}}


def writer_override_ok(writers) -> bool:
    return len(writers) >= 1       # explicit --writers may name fewer/more than 4 (coordinator's call)


def prior_dimension_writers(path=WRITTEN / "writer_assignment.csv"):
    by, rots = defaultdict(set), defaultdict(set)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by[r["dimension"]].add(r["writer_id"]); rots[r["dimension"]].add(int(r["rot"]))
    return by, rots


def rows_stage4(s4: dict, ids) -> list[dict]:
    out = []
    for a in ids:
        o = 0

        def add(task, file, ret_x=None, due=None):
            nonlocal o
            T = TASKS4[task]; o += 1
            out.append({"annotator": a, "stage": "4", "order": o, "part": T[0], "task": task, "description": T[1],
                        "file_or_link": file, "expected_minutes": T[2],
                        "return_file": T[4].format(ID=a, x=ret_x or ""), "return_folder": T[5],
                        "due": due or DATES["stage4_due"]})
        add("intent", T4("intent", a))
        add("part19", T4("part19", a))
        if a in s4["writers"]:
            w = s4["writer_rot"][a]
            add("write2", "write_pairs.html" + WL.link_fragment("speech_act", w, S4_PAIRS, a))
        if a in s4["raters"]:
            add("repair2", T4("repair2", a))
        if a in s4["checkers"]:
            add("check2", f"check_pairs.html + stage4/{a}_check_hw2.json", ret_x=f"{a}_check_hw2", due=DATES["stage4_check_due"])
    return out


def T4(task: str, a: str) -> str:
    return TASKS4[task][3].format(ID=a)


def stage4_sheet(s4: dict, rows: list[dict], a: str) -> str:
    rs = [r for r in rows if r["annotator"] == a]
    tot = sum(r["expected_minutes"] for r in rs)
    split = ", ".join(f"{r['part']} {r['expected_minutes']} min" for r in rs)
    late = [r for r in rs if r["task"] == "check2"]
    L = [f"# Stage 4 task sheet for {a} (OPTIONAL; {DATES['stage4']}; due {DATES['stage4_due']}"
         + (f", Part 16 due {DATES['stage4_check_due']}" if late else "") + ")", "",
         f"Stage 4 is a short top-up and **optional**: if you cannot do it, tell the coordinator now so someone else can be asked. "
         f"Download the current `annotation_package.zip`: your files are in its `stage4/` folder and the tools are in the "
         f"package folder. About **{tot} min** in total ({split}), plus breaks.", "",
         RULES.format(ID=a, END=DATES["stage4_end"]), ""]
    extra = ["- **Your own words only.** Every sentence you write or rate is your own work or your own judgment: do not copy, "
             "reuse or adapt anyone else's sentences, and do not ask anyone for examples."]
    if a in s4["writers"]:
        extra += ["- **Part 15 (writing): stress.** Write every sentence yourself. Do not copy, adapt, shorten, extend or "
                  "paraphrase any sentence you have seen anywhere: examples in the tool or README, sentences from earlier "
                  "parts, the model sentences in Part 18, other people's pairs. Every new pair is compared with all earlier "
                  "pairs (exact and near-copies), and copies are rejected before anyone checks them."]
    extra += ["- **Part 19:** label what each sentence says, using only the words on the page. Do not search for the sentences "
              "or ask anyone or any tool; if the sentence is odd or unclear, say so with the unsure key (`S`)."]
    if a in s4["raters"]:
        extra += ["- **Part 17:** rate each sentence on its own, as in Part 4. Do not look for patterns across sentences "
                  "and do not discuss them. Some of the 80 sentences may be weak or odd: answer honestly."]
    if late:
        extra += [f"- **Part 16** opens {DATES['stage4_check_open']}. Do Parts 18 and 19 first, then wait for the message that "
                  "Part 15 is back; re-download the zip then."]
    L += ["**Extra rules for Stage 4**"] + extra + ["", "## Steps (in this order)", "",
          "Order: **Part 18 first** (it needs no other context), then **Part 19**, then the rest of the list."]
    L += [""] + [item_line(r, a) for r in rs] + [""]
    early = [r for r in rs if r["due"] == DATES["stage4_due"]]
    L += [f"**Return files (names must be exact):** " + "; ".join(f"`{r['return_file']}` ({r['part']})" for r in rs) + ".", ""]
    L += [f"Return: email the CSV files for {', '.join(r['part'] for r in early)} to the coordinator by {DATES['stage4_due']} "
          f"(subject `AAC annotation {a} stage 4`), with the time you spent and any notes."]
    if late:
        L += [f"Email the Part 16 CSV by {DATES['stage4_check_due']} (same subject)."]
    L += ["", "Thank you! Your work is anonymous: only your ID is recorded. You can stop at any time."]
    return "\n".join(L) + "\n"


def stage4_handout_section(s4: dict, rows: list[dict]) -> str:
    mins = lambda a: sum(r["expected_minutes"] for r in rows if r["annotator"] == a)  # noqa: E731
    only18 = [a for a in s4["everyone_part18"] if a not in s4["writers"] + s4["raters"] + s4["checkers"]]
    tot = sum(r["expected_minutes"] for r in rows)
    fmt = lambda ids: ", ".join(f"{a} ({mins(a)} min)" for a in ids)  # noqa: E731
    return (f"""<!-- stage4:start -->
- **Stage 4, optional** (opens **{DATES['stage4_open']}**): Parts 15, 17, 18, 19 due **{DATES['stage4_due']}**; Part 16 opens
  {DATES['stage4_check_open']} and is due **{DATES['stage4_check_due']}**. Files appear in `stage4/`; re-download the zip.
  About {tot / 60:.1f} person-hours. **Everyone does Part 18 first** (15 min, all 20: `intent_check.html` +
  `stage4/<ID>_intent.json`, return `intent_check_<ID>.csv`), **then Part 19** (10 min, all 20: `annotate.html` +
  `stage4/<ID>_part19.json`, about 13 sentences, return `labels_part19_<ID>.csv`). Sheets: `assignments/<ID>_stage4.md`.
  - Part 15, speech-act writing, 25 min (`write_pairs.html` link on the sheet): {fmt(s4['writers'])}.
    Return `write_pairs_speech_act_<ID>.csv`.
  - Part 17, new-sentence check, 80 sentences, 47 min (your own file `stage4/repair_audit_v2_<ID>.html`):
    {fmt(s4['raters'])}. Return `repair_audit_v2_<ID>.csv`.
  - Part 16, blind checks of the Part 15 pairs, about 22 min, after Part 15 is back:
    {fmt(s4['checkers'])}. Reserves in order: {', '.join(s4['check_reserve'])}. Return `check_pairs_<ID>_check_hw2_<ID>.csv`.
  - Parts 18 and 19 only (25 min): {', '.join(only18)}.
<!-- stage4:end -->
""")


def insert_stage4_section(txt: str, section: str) -> str:
    if "<!-- stage4:start -->" in txt:
        a, rest = txt.split("<!-- stage4:start -->", 1)
        txt = a.rstrip("\n") + "\n" + rest.split("<!-- stage4:end -->\n", 1)[1]
    anchor = "\n<!-- stage5:start -->" if "<!-- stage5:start -->" in txt else "\n**Return method:**"
    assert anchor in txt, "HANDOUT.md layout changed"
    txt = txt.replace(anchor, "\n" + section + anchor, 1)
    return txt.replace("subject `AAC annotation <ID> stage <1|2>`", "subject `AAC annotation <ID> stage <1|2|3|4>`")


def update_handout(section: str, path=PKG / "HANDOUT.md") -> None:
    Path(path).write_text(insert_stage4_section(Path(path).read_text(), section))


def check_placeholder(cid: str) -> dict:
    import make_check_batches as MB
    return {"check_id": cid, "tool": MB.TOOL, "version": 1, "n_items": 0, "exclude": [], "items": []}


def write_stage4_outputs(s4: dict, plan: dict, out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR, out_stage4=STAGE4_DIR,
                         written=S4_WRITTEN, pkg=PKG, placeholders=True, handout_path=None) -> list[dict]:
    rows = rows_stage4(s4, plan["annotators"])
    write_csv(out_assign / "stage4.csv", rows, S4_COLS)
    (out_assign / "stage4_plan.json").write_text(json.dumps(s4, indent=1) + "\n")
    out_sheets.mkdir(parents=True, exist_ok=True)
    for a in plan["annotators"]:
        (out_sheets / f"{a}_stage4.md").write_text(stage4_sheet(s4, rows, a))
    written.mkdir(parents=True, exist_ok=True)
    write_csv(written / "writer_assignment.csv",
              [{"writer_id": w, "dimension": "speech_act", "rot": s4["writer_rot"][w], "n_pairs": S4_PAIRS,
                "first_topics": WL.first_topics(s4["writer_rot"][w]),
                "link_fragment": WL.link_fragment("speech_act", s4["writer_rot"][w], S4_PAIRS, w), "session": 1}
               for w in s4["writers"]],
              ["writer_id", "dimension", "rot", "n_pairs", "first_topics", "link_fragment", "session"])
    if placeholders:
        out_stage4.mkdir(parents=True, exist_ok=True)
        keep = {f"{c}_check_hw2.json" for c in s4["checkers"]}
        for old in out_stage4.glob("*_check_hw2.json"):
            if old.name not in keep:
                old.unlink()
        for c in s4["checkers"]:
            f = out_stage4 / f"{c}_check_hw2.json"
            if not f.exists() or json.loads(f.read_text()).get("n_items", 0) == 0:   # never clobber a filled file
                f.write_text(json.dumps(check_placeholder(f"{c}_check_hw2"), indent=1) + "\n")
    update_handout(stage4_handout_section(s4, rows), handout_path or pkg / "HANDOUT.md")
    return rows


def run_stage4(plan_path=ASSIGN_DIR / "plan.json", out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR, out_stage4=STAGE4_DIR,
               written=S4_WRITTEN, pkg=PKG, writers=None, raters=None, checkers=None, rebuild=False,
               prior_path=WRITTEN / "writer_assignment.csv", quiet=False, handout_path=None) -> dict:
    plan = json.loads(Path(plan_path).read_text())
    plan_file = out_assign / "stage4_plan.json"
    if plan_file.exists() and not (rebuild or writers or raters or checkers):
        s4 = json.loads(plan_file.read_text())          # roster is frozen once chosen
    else:
        tab = minutes_table(plan, rows_for(plan))
        by, rots = prior_dimension_writers(prior_path)
        s4 = select_stage4(plan, tab, by, rots["speech_act"], writers, raters, checkers)
    rows = write_stage4_outputs(s4, plan, out_assign, out_sheets, out_stage4, written, pkg, handout_path=handout_path)
    if not quiet:
        mins = lambda a: sum(r["expected_minutes"] for r in rows if r["annotator"] == a)  # noqa: E731
        print("Part 15 writers:", {w: (s4["writer_rot"][w], mins(w)) for w in s4["writers"]}, "(rot, minutes)")
        print("Part 17 raters:", {a: mins(a) for a in s4["raters"]})
        print("Part 16 checkers:", {a: mins(a) for a in s4["checkers"]}, "reserves:", s4["check_reserve"])
        print("Parts 18 + 19 only:", [a for a in plan["annotators"] if mins(a) == TASKS4["intent"][2] + TASKS4["part19"][2]])
        print(f"person-hours {sum(r['expected_minutes'] for r in rows) / 60:.1f}")
    return {"plan": plan, "stage4": s4, "rows": rows}


def assign_checkers(fids: list[str], checkers: list[str], writer_of: dict, per_pair=S4_PER_PAIR) -> dict[str, list[str]]:
    """3 distinct checkers per pair, never its writer; lowest load first, then least co-assignment, then hash."""
    load, co = Counter(), Counter()
    res = {}
    for fid in sorted(fids, key=lambda f: sha(f"{SALT}|s4check|{f}")):
        elig = [c for c in checkers if c != writer_of[fid]]
        chosen = []
        for _ in range(min(per_pair, len(elig))):
            c = min((c for c in elig if c not in chosen),
                    key=lambda c: (load[c], sum(co[tuple(sorted((c, x)))] for x in chosen), sha(f"{SALT}|s4|{fid}|{c}")))
            chosen.append(c)
        for c in chosen:
            load[c] += 1
        for x, y in itertools.combinations(sorted(chosen), 2):
            co[(x, y)] += 1
        res[fid] = sorted(chosen)
    return res


def run_stage4_fill(plan_path=ASSIGN_DIR / "plan.json", cand_path=S4_WRITTEN / "hw_candidates.jsonl",
                    out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR, out_stage4=STAGE4_DIR, written=S4_WRITTEN, pkg=PKG,
                    absent=(), handout_path=None, quiet=False) -> dict:
    """Part 16: fill stage4/<ID>_check_hw2.json (3 checkers per accepted hw2 pair, never the writer)."""
    import make_check_batches as MB
    plan = json.loads(Path(plan_path).read_text())
    s4 = json.loads((out_assign / "stage4_plan.json").read_text())
    absent = sorted(set(absent) | set(s4.get("absent_checkers", [])))
    if absent:
        pool = [c for c in s4["checkers"] + s4["check_reserve"] if c not in absent]
        s4["checkers"] = pool[:N_S4_CHECKERS]
        s4["check_reserve"] = pool[N_S4_CHECKERS:]
        s4["absent_checkers"] = absent
    cands = [c for c in map(json.loads, (l for l in Path(cand_path).open(encoding="utf-8") if l.strip()))]
    by = {c["family_id"]: c for c in cands}
    checkers = s4["checkers"]
    assert not set(checkers) & set(s4["writers"]) and not set(checkers) & set(s4["raters"])
    asg = assign_checkers(list(by), checkers, {f: c["writer_id"] for f, c in by.items()})
    files = defaultdict(list)
    for fid, cs in asg.items():
        for c in cs:
            assert c != by[fid]["writer_id"]
            files[c].append(fid)
    out_stage4.mkdir(parents=True, exist_ok=True)
    rows_out, fill_rows = write_stage4_outputs(s4, plan, out_assign, out_sheets, out_stage4, written, pkg,
                                               placeholders=False, handout_path=handout_path), []
    for old in out_stage4.glob("*_check_hw2.json"):
        old.unlink()
    for c in checkers:
        fids = files.get(c, [])
        items = []
        for fid in sorted(fids, key=MB.item_id):
            x = by[fid]
            items.append({"item_id": MB.item_id(fid), "dimension": x["dimension"], "options": x["critical_options"],
                          "context": x["context"], "A": x["variants"]["A"]["source"], "B": x["variants"]["B"]["source"],
                          "bare": x["bare"], "noncritical": x["noncritical"]})
        assert all(set(i) == set(MB.BLIND_FIELDS) for i in items)
        writers = sorted({by[f]["writer_id"] for f in fids})
        cid = f"{c}_check_hw2"
        doc = ({"check_id": cid, "tool": MB.TOOL, "version": 1, "n_items": len(items),
                "exclude": sorted(MB.id_hash(w) for w in writers), "items": items} if items else check_placeholder(cid))
        (out_stage4 / f"{cid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        fill_rows.append({"check_id": cid, "file": f"annotation_package/stage4/{cid}.json", "checker": c, "n_pairs": len(items),
                          "writers": " ".join(writers)})
    with open(written / "check_key.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "check_id", "family_id", "writer_id", "dimension", "value_A", "value_B", "source_A", "source_B", "bare"])
        for fid in sorted(by):
            c = by[fid]
            w.writerow([MB.item_id(fid), " ".join(f"{x}_check_hw2" for x in asg[fid]), fid, c["writer_id"], c["dimension"],
                        c["variants"]["A"]["critical_value"], c["variants"]["B"]["critical_value"],
                        c["variants"]["A"]["source"], c["variants"]["B"]["source"], c["bare"]])
    write_csv(out_assign / "stage4_fill.csv", fill_rows, ["check_id", "file", "checker", "n_pairs", "writers"])
    summ = {"candidates": len(by), "checkers": checkers, "reserve": s4["check_reserve"], "absent": absent,
            "pairs_by_n_checkers": dict(Counter(len(v) for v in asg.values())),
            "load_pairs": {r["checker"]: r["n_pairs"] for r in fill_rows}}
    (out_assign / "stage4_fill.json").write_text(json.dumps(summ, indent=1) + "\n")
    if not quiet:
        print(f"{len(by)} hw2 candidates -> {len(fill_rows)} check files in {out_stage4}; pairs by #checkers "
              f"{summ['pairs_by_n_checkers']}; load {summ['load_pairs']}; absent {absent}")
    return summ


# ---------------------------------------------------------------- Stage 5 (Parts 20 and 21)
def frontier_plan(path=None) -> dict | None:
    p = Path(path or S5_FRONTIER)
    return json.loads(p.read_text()) if p.exists() else None


def rows_stage5(ids, fplan=None) -> list[dict]:
    """Parts 20 and 21 for everyone, then each person's share of Parts 22-25 (in part order)."""
    fplan = fplan if fplan is not None else frontier_plan()
    out = []
    for a in ids:
        o = 0
        for task, T in TASKS5.items():
            o += 1
            out.append({"annotator": a, "stage": "5", "order": o, "part": T[0], "task": task, "description": T[1],
                        "file_or_link": T[3].format(ID=a), "expected_minutes": T[2], "return_file": T[4].format(ID=a),
                        "return_folder": T[5], "due": DATES["stage5_due"]})
        for task, (label, desc) in TASKS5_FRONTIER.items():
            mine = (fplan or {}).get("per_person", {}).get(a, {}).get(task)
            if not mine:
                continue
            o += 1
            out.append({"annotator": a, "stage": "5", "order": o, "part": label, "task": task,
                        "description": desc.format(n=mine["n_items"]),
                        "file_or_link": f"rate_items.html + stage5/{a}_{task}.json", "expected_minutes": mine["minutes"],
                        "return_file": f"labels_{task}_{a}.csv", "return_folder": f"annotation/returns_{task}/", "due": DATES["stage5_due"]})
    return out


def stage5_item_line(r, a) -> str:
    head = f"- [ ] **{r['order']}. {r['part']}: {r['description']}** (about {r['expected_minutes']} min)"
    if r["task"] == "part20":
        body = (f"Open `annotate.html`, enter `{a}`, load `stage5/{a}_part20.json`, do the 5 practice items, then every item "
                "(12 sentences). Same tool and questions as Part 10 (README: Part 10 and Part 20). Label only what the words on the "
                "page say; the codebook is not needed, the short definitions on the screen are enough. Click **Download CSV** at "
                f"the end. The file name will be `labels_part20_{a}.csv`.")
    elif r["task"] == "part21":
        body = (f"Open `source_check.html`, click the file button, choose `stage5/{a}_part21.json`, enter `{a}`. Do the 3 practice "
                "messages, then every message (20): is it negated, is it polite, and is it a statement, a question or a request. "
                f"README: Part 21. Click **Download CSV** at the end. The file name will be `labels_part21_{a}.csv`.")
    else:
        body = (f"Open `rate_items.html`, click the file button, choose `stage5/{a}_{r['task']}.json`, enter `{a}`. Do the 2 practice "
                f"items (you see feedback), then every item. README: {r['part']}. Click **Download CSV** at the end. "
                f"The file name will be `labels_{r['task']}_{a}.csv`.")
    return f"{head}  \n  {body} Return: `{r['return_file']}`."


def split_sittings(rs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Two sittings at a part boundary, as close to half the minutes as possible."""
    tot = sum(r["expected_minutes"] for r in rs)
    cum = [sum(r["expected_minutes"] for r in rs[:k]) for k in range(1, len(rs))]
    best = 1 + min(range(len(cum)), key=lambda k: abs(cum[k] - tot / 2))
    return rs[:best], rs[best:]


def stage5_sheet(rows: list[dict], a: str) -> str:
    rs = sorted((r for r in rows if r["annotator"] == a), key=lambda r: int(r["order"]))
    tot = sum(r["expected_minutes"] for r in rs)
    split = ", ".join(f"{r['part']} {r['expected_minutes']} min" for r in rs)
    big = len(rs) > 2
    L = [f"# Stage 5 task sheet for {a} (OPTIONAL; {DATES['stage5']}; due {DATES['stage5_due']})", "",
         "Stage 5 is a top-up and **optional**: if you cannot do it, tell the coordinator now so it can be planned without you. "
         "Download the current `annotation_package.zip`: your files are in its `stage5/` folder and the tools are in the package "
         f"folder. About **{tot} min** in total ({split}), plus breaks."
         + (" The practice items are included in these times." if big else ""), ""]
    if big:
        s1, s2 = split_sittings(rs)
        L += [f"**Two sittings are fine.** Each tool saves your progress in your browser (use the same browser and computer), so you "
              f"can stop between items. Suggested split: first sitting {', '.join(r['part'] for r in s1)} "
              f"(about {sum(r['expected_minutes'] for r in s1)} min), second sitting {', '.join(r['part'] for r in s2)} "
              f"(about {sum(r['expected_minutes'] for r in s2)} min). Keep the order below, and download each part's CSV as soon as "
              "you finish that part.", ""]
    L += [RULES.format(ID=a, END=DATES["stage5_end"]), "",
          "**Extra rules for Stage 5**",
          "- **Part 20:** label what each sentence says, using only the words on the page. Do not search for the sentences or ask "
          "anyone or any tool; if a sentence is odd or unclear, say so with the unsure key (`S`).",
          "- **Part 21:** answer from the words of the message only. Use unsure when you cannot tell. Do not look for patterns "
          "across messages."]
    L += [S5_EXTRA_RULES[r["task"]] for r in rs if r["task"] in S5_EXTRA_RULES]
    if big:
        L += ["- **Parts 22-25:** answer from the words on the page only. Do not search for the sentences or ask anyone or any tool. "
              "If an item is odd, pick the closest answer (or `other` / `cannot tell` where offered) and add a short note."]
    L += ["", "## Steps (in this order)", "", f"Order: **Part 20 first**, then {', then '.join(r['part'] for r in rs[1:])}.", ""]
    L += [stage5_item_line(r, a) for r in rs] + [""]
    L += ["**Return files (names must be exact):** " + "; ".join(f"`{r['return_file']}` ({r['part']})" for r in rs) + ".", ""]
    L += [f"Return: email the CSV files for {', '.join(r['part'] for r in rs)} to the coordinator by {DATES['stage5_due']} "
          f"(subject `AAC annotation {a} stage 5`), with the time you spent and any notes.", "",
          "Thank you! Your work is anonymous: only your ID is recorded. You can stop at any time."]
    return "\n".join(L) + "\n"


def stage5_handout_section(rows: list[dict]) -> str:
    ids = sorted({r["annotator"] for r in rows})
    tot = sum(r["expected_minutes"] for r in rows)
    per = {a: sum(r["expected_minutes"] for r in rows if r["annotator"] == a) for a in ids}
    fr = [t for t in TASKS5_FRONTIER if any(r["task"] == t for r in rows)]
    lines = ["<!-- stage5:start -->",
             f"- **Stage 5, optional** (opens **{DATES['stage5_open']}**, built after Stage 4 had been returned): due **{DATES['stage5_due']}**. "
             f"Files appear in `stage5/`; re-download the zip. About {tot / 60:.1f} person-hours"
             + (f", {min(per.values())}-{max(per.values())} min each (two sittings are fine)" if fr else "")
             + ". Sheets: `assignments/<ID>_stage5.md`.",
             f"  - Parts 20 and 21 for all {len(ids)} people, in this order:",
             "    - Part 20, 10 min (`annotate.html` + `stage5/<ID>_part20.json`, 12 sentences). Return `labels_part20_<ID>.csv`.",
             "    - Part 21, 8 min (`source_check.html` + `stage5/<ID>_part21.json`, 20 short messages). Return `labels_part21_<ID>.csv`."]
    if fr:
        lines.append("  - Parts 22-25, a share of each (every person's sheet lists which parts and how many items; `rate_items.html` + "
                     "`stage5/<ID>_part22..25.json`, 2 practice items first). Return `labels_part22_<ID>.csv` ... `labels_part25_<ID>.csv`:")
        for t in fr:
            rr = [r for r in rows if r["task"] == t]
            lines.append(f"    - {rr[0]['part']}: {len(rr)} people, {min(r['expected_minutes'] for r in rr)}-"
                         f"{max(r['expected_minutes'] for r in rr)} min each ({TASKS5_FRONTIER[t][1].split(':')[0]}).")
    lines.append("<!-- stage5:end -->")
    return "\n".join(lines) + "\n"


def insert_stage5_section(txt: str, section: str) -> str:
    if "<!-- stage5:start -->" in txt:
        a, rest = txt.split("<!-- stage5:start -->", 1)
        txt = a.rstrip("\n") + "\n" + rest.split("<!-- stage5:end -->\n", 1)[1]
    anchor = "\n**Return method:**"
    assert anchor in txt, "HANDOUT.md layout changed"
    txt = txt.replace(anchor, "\n" + section + anchor, 1)
    return txt.replace("stage <1|2|3|4>`", "stage <1|2|3|4|5>`")


def run_stage5(plan_path=ASSIGN_DIR / "plan.json", out_assign=ASSIGN_DIR, out_sheets=SHEET_DIR, stage5_dir=STAGE5_DIR,
               pkg=PKG, handout_path=None, quiet=False, frontier_path=None) -> dict:
    plan = json.loads(Path(plan_path).read_text())
    ids = plan["annotators"]
    fplan = frontier_plan(frontier_path)
    if fplan is None and not quiet:
        print("WARNING: no stage5_frontier.json (run src/make_frontier_parts.py first): writing Parts 20 and 21 only")
    rows = rows_stage5(ids, fplan)
    need = [(a, r["task"]) for a in ids for r in rows if r["annotator"] == a]
    missing = [str(stage5_dir / f"{a}_{t}.json") for a, t in need if not (stage5_dir / f"{a}_{t}.json").exists()]
    if missing and not quiet:
        print(f"WARNING: {len(missing)} part files missing (run src/make_treated_check.py, src/make_source_check.py and "
              f"src/make_frontier_parts.py first), e.g. {missing[:2]}")
    write_csv(out_assign / "stage5.csv", rows, S4_COLS)
    out_sheets.mkdir(parents=True, exist_ok=True)
    for a in ids:
        (out_sheets / f"{a}_stage5.md").write_text(stage5_sheet(rows, a))
    hp = Path(handout_path or pkg / "HANDOUT.md")
    hp.write_text(insert_stage5_section(hp.read_text(), stage5_handout_section(rows)))
    if not quiet:
        per = [sum(r["expected_minutes"] for r in rows if r["annotator"] == a) for a in ids]
        print(f"Stage 5: {len(ids)} sheets, {sum(per) / 60:.1f} person-hours, minutes per person {min(per)}-{max(per)}")
    return {"plan": plan, "rows": rows, "missing": missing, "frontier": fplan}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["1", "2", "3", "4", "5"], required=True)
    ap.add_argument("--annotators", default="P01..P20", help="e.g. P01..P20 or P01,P02,...")
    ap.add_argument("--absent", default="", help="stage 2/3: people who will not do that stage")
    ap.add_argument("--still-checking", default="", help="stage 2: non-returning writers who still check")
    ap.add_argument("--candidates", default=str(WRITTEN / "hw_candidates.jsonl"))
    ap.add_argument("--prepare", action="store_true",
                    help="with --stage 2: only write the Stage 2/3 sheets and CSVs from the frozen plan.json")
    ap.add_argument("--writers", default="", help="stage 4: override the Part 15 writers (default: chosen by rule)")
    ap.add_argument("--raters", default="", help="stage 4: override the Part 17 raters")
    ap.add_argument("--checkers", default="", help="stage 4: override the Part 16 checkers")
    ap.add_argument("--fill-checks", action="store_true", help="stage 4: fill Part 16 check files from hw2 candidates")
    ap.add_argument("--rebuild", action="store_true", help="stage 4: re-choose the roster (default: keep stage4_plan.json)")
    a = ap.parse_args(argv)
    if a.stage == "1":
        run_stage1(parse_ids(a.annotators))
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
    if a.stage == "2" and a.prepare:
        prepare_later()
    elif a.stage == "2":
        run_stage2(cand_path=Path(a.candidates), absent=split(a.absent), still_checking=split(a.still_checking))
    elif a.stage == "3":
        run_stage3(cand_path=Path(a.candidates), absent=split(a.absent))
    elif a.stage == "4" and a.fill_checks:
        run_stage4_fill(cand_path=S4_WRITTEN / "hw_candidates.jsonl" if a.candidates == str(WRITTEN / "hw_candidates.jsonl")
                        else Path(a.candidates), absent=split(a.absent))
    elif a.stage == "5":
        run_stage5()
    elif a.stage == "4":
        run_stage4(writers=split(a.writers), raters=split(a.raters), checkers=split(a.checkers), rebuild=a.rebuild)
    return 0


if __name__ == "__main__":
    sys.exit(main())
