"""Stage 5 wave 1, Parts 22-25: per-person item files and the (private) assignment, from the four frontier annotation requests.

Part 22  default_profiles  (analysis/frontier/default_profiles/ANNOTATION_REQUEST.md): 223 source messages x 2 coders
Part 23  whole_message R-WM-1 (analysis/frontier/whole_message/ANNOTATION_REQUEST.md): 120 items x 3 coders
Part 24  value_of_cue (analysis/frontier/value_of_cue/ANNOTATION_REQUEST.md): speech-act stratum A (36) + whole stratum B (37) = 73 items x 2
Part 25  partner_context round 3 (analysis/frontier/partner_context/ANNOTATION_REQUEST.md): 258 items x 3 coders

Nothing is drawn here: the items and keys are the ones the requests built (annotation/frontier_*_items.json, *_key.csv). This script
only decides WHO rates WHAT (seeded, frozen; --force redraws) and writes
  annotation_package/stage5/<ID>_part22.json ... <ID>_part25.json   blind files for annotation_package/item_check.html
  annotation/assignments/stage5_frontier_assignment.csv             part, item_id, annotator (PRIVATE; never in the package)
  annotation/assignments/stage5_frontier.json                       per-person items and minutes + design record (read by make_assignments.py --stage 5)
Rules (checked by tests/test_stage5_frontier.py):
  * coder counts: Part 22 and 24 two coders, Parts 23 and 25 three, all distinct people.
  * exclusions: nobody rates an item built on a pair they wrote or checked (Parts 23, 25: hw1 writer, every Part 8 checker, every routed
    tie-break checker) or on a message whose keywords they typed in Part 9 (Parts 22, 24, 25 r2 seeds: the typed set, and every annotator
    of that message's elicitation set, a superset, as in Part 21).
  * Part 23: nobody rates two outputs made from the same input (family and variant).
  * balance: each rating is given to the eligible person with the least work so far, then work is moved from the busiest to the least
    busy person until the spread is under 30 seconds.
Parts: --parts 22,23,24,25 (default all) and --old 20,21 (the already-built Stage 5 parts; default both) choose what the wave contains;
the same script then re-balances, so a smaller wave is one flag away.

usage: python src/make_frontier_parts.py [--parts 22,23,24,25] [--old 20,21] [--force]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "annotation"
PKG = ROOT / "annotation_package"
OUT_DIR = PKG / "stage5"
ASSIGN_CSV = ANN / "assignments" / "stage5_frontier_assignment.csv"
PLAN_JSON = ANN / "assignments" / "stage5_frontier.json"
TOOL = "item_check_v1"
SALT = "s5f-20261103"
SEC_PRACTICE = 60          # three practice items, about one minute
# seconds per rating, from each request's own estimate (minutes per person x 60 / items per person)
SEC = {"part22": 21.5, "part23": 33.3, "part24": 49.7, "part25": 23.3}
K = {"part22": 2, "part23": 3, "part24": 2, "part25": 3}
OLD_MIN = {"part20": 10, "part21": 8}
PART_NAME = {"part22": "Part 22", "part23": "Part 23", "part24": "Part 24", "part25": "Part 25"}


def fnv(s: str) -> str:
    x = 2166136261
    for c in s:
        x = ((x ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return f"{x:08x}"


def id_hash(annotator: str, check: str) -> str:
    return fnv(annotator.strip().upper() + "|" + check)


def jl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- who is blocked from what
def elicitation_blocks():
    """item_id (el-xxxxxx) -> annotators of that message's elicitation set (any replicate)."""
    sets = defaultdict(set)
    for r in rows(ANN / "elicitation_assignment.csv"):
        sets[r["set"]].add(r["annotator"])
    return {j["item_id"]: set(sets[j["set"]]) for j in jl(ANN / "elicitation_key.jsonl")}


def hw_blocks():
    """family_id -> everyone who wrote or checked that pair (hw1): writer, Part 8 checkers, routed Part 14 tie-break checkers."""
    out = defaultdict(set)
    for j in jl(ANN / "written" / "hw_candidates.jsonl"):
        out[j["family_id"]].add(j["writer_id"])
    for r in rows(ANN / "written" / "check_key.csv"):
        out[r["family_id"]].add(r["writer_id"])
        out[r["family_id"]].update(c.split("_")[0] for c in r["check_id"].split())
    hc = ROOT / "analysis" / "hw_checks" / "items.csv"
    if hc.exists():
        for r in rows(hc):
            out[r["family_id"]].update(r["checkers"].split())
            if r.get("writer_id"):
                out[r["family_id"]].add(r["writer_id"])
    for p in (ANN / "assignments" / "stage3_fill.json", ANN / "assignments" / "stage3_people.json"):
        if p.exists() and "fill" in p.name:
            for who, fams in json.loads(p.read_text())["routed"].items():
                for f in fams:
                    out[f].add(who)
    return out


# ---------------------------------------------------------------- the four parts: units, questions, practice
def qdef(title, text, options):
    return {"title": title, "text": text, "options": options}


def opts(*pairs):
    return [{"v": v, "label": l} for v, l in pairs]


YN = ["yes", "no"]
CHIP_HELP = ("Buttons in square brackets show what the writer pressed: [NOT] not, [YES] yes, [?] a question, [TELL] a statement, "
             "[ASK] a request, [I] I, [YOU] you, [THEY] someone else, [WE] we, [MAYBE] unsure, [SURE] very sure, [PLEASE] polite, "
             "[PLAIN] plain, [PAST] already happened, [NOW] happening now, [LATER] will happen later.")


def part22(blocked_el):
    items = json.load(open(ANN / "frontier_default_profiles_items.json"))["items"]
    key = {r["item_id"]: r for r in rows(ANN / "frontier_default_profiles_key.csv")}
    units = []
    for it in items:
        k = key[it["item_id"]]
        b = set(blocked_el[k["item"]]) | {k["unit"].split("|")[1].replace("human_", "")}
        units.append({"item_id": it["item_id"], "blocks": [{"label": "Sentence", "text": it["text"]},
                      {"label": "Keywords (the short words a person typed to make this sentence)", "text": it["keywords"]}],
                      "qs": ["q1", "q2", "q3", "q4"], "blocked": b, "group": None})
    spec = {
        "title": "Read a sentence and its keywords",
        "intro": ["You will see a sentence and the few keywords a person typed for it. Answer four short questions about the words on the page.",
                  "Questions 1 and 2 are about the sentence. Questions 3 and 4 are about the keywords only: ignore the sentence for those two."],
        "help": [{"term": "What it does", "text": "statement tells something (including 'I want tea.'). question asks for information or permission. "
                  "request/command asks someone to do something. other if none of these fits."},
                 {"term": "Polite", "text": "polite if it has please, thank you, sorry, excuse me, could you, would you or a similar polite or softened form."},
                 {"term": "Keywords only", "text": "For questions 3 and 4, look only at the keywords. Would a reader of the keywords alone already know it is a question or request "
                  "(or polite)? Words like 'where', 'can you', 'please' would show it."}],
        "questions": {
            "q1": qdef("What does the sentence do?", "Look at the sentence.", opts(("statement", "statement"), ("question", "question"),
                       ("request/command", "request or command"), ("other", "other"))),
            "q2": qdef("Is the sentence polite?", "Please, thank you, sorry, softened wording like 'could you'.", opts(("polite", "polite"), ("not polite", "not polite"))),
            "q3": qdef("Keywords only: a question or request?", "Look ONLY at the keywords. Do the keywords by themselves already show a question or a request (not a plain statement)?", YN),
            "q4": qdef("Keywords only: polite?", "Look ONLY at the keywords. Do the keywords by themselves already show politeness?", YN)},
        "practice": [
            {"item_id": "prac-1", "blocks": [{"label": "Sentence", "text": "Please open the window."},
                                            {"label": "Keywords (the short words a person typed to make this sentence)", "text": "open window"}],
             "qs": ["q1", "q2", "q3", "q4"], "expected": {"q1": "request/command", "q2": "polite", "q3": "no", "q4": "no"},
             "fb": "It asks someone to do something (a request) and uses 'please' (polite). The keywords 'open window' show neither."},
            {"item_id": "prac-2", "blocks": [{"label": "Sentence", "text": "The bus is late."},
                                            {"label": "Keywords (the short words a person typed to make this sentence)", "text": "bus late"}],
             "qs": ["q1", "q2", "q3", "q4"], "expected": {"q1": "statement", "q2": "not polite", "q3": "no", "q4": "no"},
             "fb": "It tells something: a statement, not polite. The keywords do not show a question or politeness."},
            {"item_id": "prac-3", "blocks": [{"label": "Sentence", "text": "Where are my keys?"},
                                            {"label": "Keywords (the short words a person typed to make this sentence)", "text": "where keys"}],
             "qs": ["q1", "q2", "q3", "q4"], "expected": {"q1": "question", "q2": "not polite", "q3": "yes", "q4": "no"},
             "fb": "It asks for information (question), no polite word. The keyword 'where' already shows a question by itself."}]}
    return units, spec


def part23(hw):
    items = json.load(open(ANN / "frontier_whole_message_items.json"))["items"]
    key = {r["id"]: r for r in rows(ANN / "frontier_whole_message_key.csv")}
    units = []
    for it in items:
        k = key[it["id"]]
        if it["type"] == "O":
            blocks = [{"label": "Keywords the writer typed", "text": it["input_text"].replace("Keywords: ", "", 1)},
                      {"label": "Message A", "text": it["version_A"]}, {"label": "Message B", "text": it["version_B"]},
                      {"label": "Sentence shown", "text": it["output"]}]
            qs, group = ["q1", "q2", "q3"], (k["family_id"], k["variant"])
        else:
            blocks = [{"label": "Keywords the writer typed", "text": it["input_text"].replace("Keywords: ", "", 1)},
                      {"label": "Sentence shown", "text": it["output"]}]
            qs, group = ["q4", "q5"], None
        units.append({"item_id": it["id"], "blocks": blocks, "qs": qs, "blocked": set(hw[k["family_id"]]), "group": group})
    spec = {
        "title": "Compare a sentence with two possible messages",
        "intro": ["A writer typed a few keywords (sometimes with buttons in square brackets) to make a sentence. For most items you also see two messages, "
                  "A and B, that the writer might have meant. Say which one the sentence expresses, and whether it fits what the writer asked for.",
                  "Some items show only the keywords and the sentence; they have two other questions."],
        "help": [{"term": "Buttons", "text": CHIP_HELP},
                 {"term": "Which message", "text": "A or B if the sentence says that one. something else if it says neither. cannot tell if you cannot decide."},
                 {"term": "Added or left out", "text": "added: the sentence says something the writer did not ask for. left out: it drops something they meant. "
                  "both, or neither."},
                 {"term": "Accept", "text": "yes if you would be happy to say it as the message; yes with a small edit if a word or two should change; no otherwise."}],
        "questions": {
            "q1": qdef("Which message does the sentence say?", "Compare the sentence with Message A and Message B.",
                       opts(("A", "A"), ("B", "B"), ("something else", "something else"), ("cannot tell", "cannot tell"))),
            "q2": qdef("Added or left out?", "Does the sentence add anything the writer did not ask for, or leave out something they meant?",
                       opts(("added", "added something"), ("left out", "left something out"), ("both", "both"), ("neither", "neither"))),
            "q3": qdef("Would you accept it?", "Would you accept the sentence as the writer's message?",
                       opts(("yes", "yes"), ("yes with a small edit", "yes, with a small edit"), ("no", "no"))),
            "q4": qdef("Anything beyond the keywords?", "Does the sentence say anything beyond the keywords and buttons?", YN),
            "q5": qdef("A complete sentence?", "Is it a complete sentence you could say as it is?", YN)},
        "practice": [
            {"item_id": "prac-1", "blocks": [{"label": "Keywords the writer typed", "text": "[I] [PAST] buy bread"},
                                            {"label": "Message A", "text": "I bought bread this morning."},
                                            {"label": "Message B", "text": "I buy bread every day."},
                                            {"label": "Sentence shown", "text": "I bought bread this morning."}],
             "qs": ["q1", "q2", "q3"], "expected": {"q1": "A", "q2": "neither", "q3": "yes"},
             "fb": "The sentence is Message A word for word, so it says A, adds and drops nothing, and is acceptable."},
            {"item_id": "prac-2", "blocks": [{"label": "Keywords the writer typed", "text": "[NOT] go school"},
                                            {"label": "Message A", "text": "She did not go to school today."},
                                            {"label": "Message B", "text": "She went to school today."},
                                            {"label": "Sentence shown", "text": "She went to school and had lots of fun with her friends."}],
             "qs": ["q1", "q2", "q3"], "expected": {"q1": "B", "q2": "added", "q3": "no"},
             "fb": "It says B (she went), not the 'not' the writer asked for, and adds the fun with friends. Not acceptable."},
            {"item_id": "prac-3", "blocks": [{"label": "Keywords the writer typed", "text": "[PLEASE] help me"},
                                            {"label": "Sentence shown", "text": "Please help me carry my big heavy bags to the car."}],
             "qs": ["q4", "q5"], "expected": {"q4": "yes", "q5": "yes"},
             "fb": "It says more than the keywords (the bags and the car), and it is a complete sentence."}]}
    return units, spec


DIM_Q = {"polarity": "q1_neg", "speech_act": "q1_act", "politeness": "q1_pol"}


def part24(blocked_el):
    items = {j["id"]: j for j in json.load(open(ANN / "frontier_value_of_cue_items.json"))}
    units = []
    for k in rows(ANN / "frontier_value_of_cue_key.csv"):
        a = k["stratum"].startswith("A") and k["dimension"] == "speech_act"
        if not (a or k["stratum"].startswith("B")):
            continue
        it = items[k["id"]]
        units.append({"item_id": it["id"], "blocks": [{"label": "The original message", "text": it["original"]},
                      {"label": "Keywords the writer typed", "text": it["keywords"]},
                      {"label": "Sentence A", "text": it["sentence_A"]}, {"label": "Sentence B", "text": it["sentence_B"]}],
                      "qs": [DIM_Q[k["dimension"]], "q2"], "blocked": set(blocked_el[k["item_id"]]) | {k["writer"]}, "group": None})
    cho = opts(("A", "A"), ("B", "B"), ("both", "both equally"), ("neither", "neither"))
    spec = {
        "title": "Pick the sentence that says the same thing",
        "intro": ["You will see a message a person wanted to say, the keywords they typed, and two sentences, A and B, a writing tool might offer.",
                  "First say which sentence matches the original message on one feature (it is named in the question). Then say which sentence you would tap if you had typed those keywords."],
        "help": [{"term": "Same thing", "text": "Judge only the one feature named in question 1 (for example 'not', a question or request, or polite wording). "
                  "both equally if both match it as well as each other; neither if neither does."},
                 {"term": "Which would you tap", "text": "Imagine you typed those keywords and meant the original message. A, B, or neither if you would tap neither."}],
        "questions": {
            "q1_neg": qdef("Same thing about 'not'?", "Which sentence says the same thing as the original message about whether it is negated (says something is NOT so)?", cho),
            "q1_act": qdef("Same thing: question or request?", "Which sentence says the same thing as the original message about whether it is a question or request rather than a plain statement?", cho),
            "q1_pol": qdef("Same thing about politeness?", "Which sentence says the same thing as the original message about whether it uses polite wording (please, thank you, could you)?", cho),
            "q2": qdef("Which would you tap?", "If you had typed those keywords, which sentence would you tap to say your message?",
                       opts(("A", "A"), ("B", "B"), ("neither", "neither")))},
        "practice": [
            {"item_id": "prac-1", "blocks": [{"label": "The original message", "text": "I do not like loud music."},
                                            {"label": "Keywords the writer typed", "text": "like loud music"},
                                            {"label": "Sentence A", "text": "I like loud music."}, {"label": "Sentence B", "text": "I do not like loud music."}],
             "qs": ["q1_neg", "q2"], "expected": {"q1_neg": "B", "q2": "B"},
             "fb": "Only B keeps the 'not' of the original message, so B says the same thing about negation and is the one to tap."},
            {"item_id": "prac-2", "blocks": [{"label": "The original message", "text": "Can you open the door?"},
                                            {"label": "Keywords the writer typed", "text": "open door"},
                                            {"label": "Sentence A", "text": "I open the door."}, {"label": "Sentence B", "text": "Could you open the door?"}],
             "qs": ["q1_act", "q2"], "expected": {"q1_act": "B", "q2": "B"},
             "fb": "The original asks someone to do something; B does too, A is a plain statement."},
            {"item_id": "prac-3", "blocks": [{"label": "The original message", "text": "Thank you, the soup is good."},
                                            {"label": "Keywords the writer typed", "text": "soup good"},
                                            {"label": "Sentence A", "text": "The soup is good."}, {"label": "Sentence B", "text": "Thanks, the soup is good."}],
             "qs": ["q1_pol", "q2"], "expected": {"q1_pol": "B", "q2": "B"},
             "fb": "The original is polite (thank you); B keeps that, A does not."}]}
    return units, spec


def part25(hw, blocked_el):
    items = json.load(open(ANN / "frontier_partner_context_r3_items.json"))
    key = {r["id"]: r for r in rows(ANN / "frontier_partner_context_r3_key.csv")}
    seeds = {}
    for j in jl(ROOT / "analysis" / "frontier" / "partner_context" / "items_r2.jsonl"):
        seeds[j["family_id"]] = (j.get("seed_text") or "").strip().lower()
    el_by_text = {}
    for j in jl(ANN / "elicitation_key.jsonl"):
        el_by_text[j["text"].strip().lower()] = j["item_id"]
    units = []
    for it in items:
        fam = key[it["id"]]["family_id"]
        b = set(hw.get(fam, set()))
        if seeds.get(fam) in el_by_text:
            b |= blocked_el[el_by_text[seeds[fam]]]
        if it["part"] == "A":
            blocks = [{"label": "Keywords", "text": it["keywords"]}, {"label": "Something the other person said", "text": it["turn"]},
                      {"label": "The sentence", "text": it["sentence"]}]
            qs = ["pa"]
        else:
            blocks = [{"label": "Something the other person said", "text": it["turn"]}, {"label": "The sentence", "text": it["sentence"]}]
            qs = ["pb1", "pb2"]
        units.append({"item_id": it["id"], "blocks": blocks, "qs": qs, "blocked": b, "group": None})
    spec = {
        "title": "Read a remark and a sentence",
        "intro": ["You will see something one person said, and a sentence another person might say in a conversation. Some items also show the keywords that sentence was made from.",
                  "Answer from the words on the page only. The question changes between items: read it each time."],
        "help": [{"term": "Restates", "text": "says the same thing as the remark, in the same or different words."},
                 {"term": "Reply", "text": "answers the remark: agrees with it, or acknowledges it (for example starting 'yes', 'oh', 'I know')."},
                 {"term": "Invented", "text": "says something negative that neither the keywords nor the remark support."},
                 {"term": "Plain statement", "text": "something the person could say about the keywords' event without the remark at all."}],
        "questions": {
            "pa": qdef("Which describes the sentence?", "Compared with the other person's remark, which best describes the sentence?", opts(
                ("a", "(a) it restates the remark in other words"),
                ("b", "(b) it is a reply to the remark (agrees with or acknowledges it)"),
                ("c", "(c) it adds something negative that neither the keywords nor the remark support (invented)"),
                ("d", "(d) it is a plain statement about the keywords' event that the person could say without the remark"),
                ("e", "(e) other or unclear"))),
            "pb1": qdef("Same wording as the remark?", "Does the sentence re-use the other person's own wording about the outcome (the same negative phrase, word for word or nearly)?", YN),
            "pb2": qdef("Phrased as a reply?", "Is the sentence phrased as a reply to the other person (starts with yes, oh, I heard, I know, or acknowledges what they said)?", YN)},
        "practice": [
            {"item_id": "prac-1", "blocks": [{"label": "Keywords", "text": "cook dinner"}, {"label": "Something the other person said", "text": "Nothing was cooked tonight."},
                                            {"label": "The sentence", "text": "No dinner was cooked tonight."}],
             "qs": ["pa"], "expected": {"pa": "a"}, "fb": "It says what the remark says in nearly the same words: it restates it."},
            {"item_id": "prac-2", "blocks": [{"label": "Keywords", "text": "wash car"}, {"label": "Something the other person said", "text": "Did you see the weather today?"},
                                            {"label": "The sentence", "text": "I wash the car on Sundays."}],
             "qs": ["pa"], "expected": {"pa": "d"}, "fb": "It is a plain statement about washing the car that needs no remark."},
            {"item_id": "prac-3", "blocks": [{"label": "Something the other person said", "text": "No sign of the parcel."},
                                            {"label": "The sentence", "text": "Yes, I know, it has not come."}],
             "qs": ["pb1", "pb2"], "expected": {"pb1": "no", "pb2": "yes"},
             "fb": "It does not repeat the remark's wording, and it answers the remark ('Yes, I know'): a reply."}]}
    return units, spec


# ---------------------------------------------------------------- allocation
class Alloc:
    def __init__(self, people, rnd):
        self.people, self.rnd = list(people), rnd
        self.load = {p: 0.0 for p in people}
        self.who = defaultdict(list)                       # (part, item) -> people
        self.mine = {p: [] for p in people}                # person -> [(part, item)]
        self.grp = set()                                   # (person, part, group)
        self.cost, self.unit = {}, {}

    def ok(self, p, part, u):
        return (p not in u["blocked"] and p not in self.who[(part, u["item_id"])]
                and (u["group"] is None or (p, part, u["group"]) not in self.grp))

    def put(self, p, part, u):
        self.who[(part, u["item_id"])].append(p); self.mine[p].append((part, u["item_id"])); self.load[p] += SEC[part]
        if u["group"] is not None:
            self.grp.add((p, part, u["group"]))

    def drop(self, p, part, u):
        self.who[(part, u["item_id"])].remove(p); self.mine[p].remove((part, u["item_id"])); self.load[p] -= SEC[part]
        if u["group"] is not None:
            self.grp.discard((p, part, u["group"]))

    def run(self, parts):
        tasks = [(part, u) for part, units in parts.items() for u in units]
        self.unit = {(part, u["item_id"]): u for part, u in tasks}
        order = sorted(tasks, key=lambda t: (sum(1 for p in self.people if p not in t[1]["blocked"]) - K[t[0]], self.rnd.random()))
        for part, u in order:
            for _ in range(K[part]):
                cand = [p for p in self.people if self.ok(p, part, u)]
                assert cand, f"no eligible annotator for {part} {u['item_id']}"
                self.put(min(cand, key=lambda p: (self.load[p], self.rnd.random())), part, u)
        for _ in range(100000):
            ps = sorted(self.people, key=lambda p: self.load[p])
            moved = False
            for hi in reversed(ps):
                for lo in ps:
                    gap = self.load[hi] - self.load[lo]
                    if gap < 30:
                        break
                    mine = self.mine[hi][:]; self.rnd.shuffle(mine)
                    for part, iid in mine:
                        u = self.unit[(part, iid)]
                        if SEC[part] < gap and self.ok(lo, part, u):
                            self.drop(hi, part, u); self.put(lo, part, u); moved = True; break
                    if moved:
                        break
                if moved:
                    break
            if not moved:
                break


def build(parts_wanted, old, force=False, write=True):
    plan_ids = json.loads((ANN / "assignments" / "plan.json").read_text())["annotators"]
    be, hw = elicitation_blocks(), hw_blocks()
    builders = {"part22": lambda: part22(be), "part23": lambda: part23(hw), "part24": lambda: part24(be), "part25": lambda: part25(hw, be)}
    built = {p: builders[p]() for p in parts_wanted}
    rnd = random.Random(int(hashlib.sha256(SALT.encode()).hexdigest(), 16) % 2**32)
    al = Alloc(plan_ids, rnd)
    al.run({p: built[p][0] for p in built})
    per = {a: {} for a in plan_ids}
    for p in built:
        units, spec = built[p]
        for a in plan_ids:
            mine = [u for u in units if a in al.who[(p, u["item_id"])]]
            sec = len(mine) * SEC[p] + SEC_PRACTICE
            per[a][p] = {"n_items": len(mine), "minutes": math.ceil(sec / 60)}
            if write:
                doc = {"check_id": p, "tool": TOOL, "version": 1, "n_items": len(mine), "for": id_hash(a, p), **{k: spec[k] for k in
                       ("title", "intro", "help", "questions", "practice")},
                       "items": [{"item_id": u["item_id"], "blocks": u["blocks"], "qs": u["qs"]} for u in mine]}
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                (OUT_DIR / f"{a}_{p}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    tot = {a: sum(v["minutes"] for v in per[a].values()) + sum(OLD_MIN[o] for o in old) for a in plan_ids}
    plan = {"salt": SALT, "parts": list(built), "old_parts": list(old), "seconds_per_rating": {p: SEC[p] for p in built},
            "practice_seconds": SEC_PRACTICE, "coders": {p: K[p] for p in built}, "n_items": {p: len(built[p][0]) for p in built},
            "per_person": per, "total_minutes": tot,
            "note": "minutes per part = ceil((items x seconds per rating + 60 s practice) / 60); Parts 20 and 21 are 10 and 8 minutes"}
    if write:
        PLAN_JSON.write_text(json.dumps(plan, indent=1) + "\n")
        with open(ASSIGN_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["part", "item_id", "annotator"])
            for p in built:
                for u in built[p][0]:
                    for a in sorted(al.who[(p, u["item_id"])]):
                        w.writerow([p, u["item_id"], a])
    return plan, al, built


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parts", default="22,23,24,25")
    ap.add_argument("--old", default="20,21", help="already-built Stage 5 parts kept in the wave (comma list, or 'none')")
    ap.add_argument("--force", action="store_true", help="overwrite an existing frozen assignment")
    a = ap.parse_args(argv)
    if PLAN_JSON.exists() and not a.force:
        print(f"{PLAN_JSON} exists (frozen); use --force to redraw"); return 0
    parts = ["part" + x.strip() for x in a.parts.split(",") if x.strip()]
    old = [] if a.old == "none" else ["part" + x.strip() for x in a.old.split(",") if x.strip()]
    plan, al, built = build(parts, old)
    t = plan["total_minutes"]
    print(f"parts {parts} + old {old}: minutes per person min {min(t.values())} max {max(t.values())} mean {sum(t.values()) / len(t):.1f}")
    for p in built:
        print(p, plan["n_items"][p], "items x", K[p], "coders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
