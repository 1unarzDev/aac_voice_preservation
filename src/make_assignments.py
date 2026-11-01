"""Two-stage annotation plan for a fixed annotator pool (default P01..P20): assignments, task sheets, Stage 2 fill.

usage:
  python src/make_assignments.py --stage 1 --annotators P01..P20      # plan BOTH stages now, write sheets
  python src/make_assignments.py --stage 2 --prepare                  # Stage 2/3 sheets + CSVs from plan.json
  python src/make_assignments.py --stage 2 [--absent P07,...] [--still-checking P09,...]
                                                                       # between stages: fill the fixed Stage 2 files
  python src/make_assignments.py --stage 3 [--absent P11,...]         # after Stage 2 scoring: route Part 14 tie-breaks

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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["1", "2", "3"], required=True)
    ap.add_argument("--annotators", default="P01..P20", help="e.g. P01..P20 or P01,P02,...")
    ap.add_argument("--absent", default="", help="stage 2/3: people who will not do that stage")
    ap.add_argument("--still-checking", default="", help="stage 2: non-returning writers who still check")
    ap.add_argument("--candidates", default=str(WRITTEN / "hw_candidates.jsonl"))
    ap.add_argument("--prepare", action="store_true",
                    help="with --stage 2: only write the Stage 2/3 sheets and CSVs from the frozen plan.json")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
