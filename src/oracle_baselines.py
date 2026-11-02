"""Baseline oracles for comparison with the LLM-judge oracle (analysis/oracle_real/PLAN.md).

(i)  surface_label(dim, text) -> critical label from regex/lexicon rules; surface_pass applies the
     production critical_match to it.
(ii) overlap_pass(text, ref_src, other_src): contains a token unique to the reference source
     relative to its minimal-pair partner (the critical surface form); privileged, generous baseline.
Both are pure deterministic functions."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import critical_match  # noqa: E402

NEG = re.compile(r"\b(not|never|no|nothing|nobody|none|neither|nor|cannot|without)\b|n't", re.I)
HEDGE = re.compile(r"\b(maybe|perhaps|probably|possibly|might|may|i think|i guess|not sure|could be|seems?|likely)\b", re.I)
BOOST = re.compile(r"\b(definitely|really|for sure|certainly|absolutely|of course|surely|i'm sure|i am sure|no doubt|totally)\b", re.I)
POLITE = re.compile(r"\b(please|thank you|thanks|sorry|excuse me|could you|would you|would you mind|may i|if possible|kindly)\b", re.I)
FIRST = re.compile(r"\b(i|me|my|mine|i'm|i'll|i've|i'd|myself)\b", re.I)
SECOND = re.compile(r"\b(you|your|yours|you're|you'll|you've|yourself)\b", re.I)
WE = re.compile(r"\b(we|us|our|let's|ours|we're|we'll)\b", re.I)
IMPER = {"bring", "take", "open", "close", "give", "send", "call", "put", "get", "come", "go", "turn", "help", "wait", "tell",
         "show", "check", "pass", "buy", "make", "stop", "leave", "read", "write", "clean", "let", "please", "sit", "stand", "look",
         "listen", "try", "keep", "bring", "hold", "move", "pick", "turn", "switch", "set", "bring"}
Q_AUX = {"can", "could", "will", "would", "do", "does", "did", "is", "are", "was", "were", "have", "has", "should", "may", "shall"}
PAST = re.compile(r"\b(yesterday|earlier|ago|last (night|week|month|year|weekend)|already|was|were|did|had|used to)\b|\b[a-z]{3,}ed\b"
                  r"|\b(went|ate|saw|took|got|came|made|gave|bought|told|found|left|met|ran|wrote|felt|slept|paid|said|heard|brought)\b", re.I)
LATER = re.compile(r"\b(will|tomorrow|tonight|later|soon|next|going to|gonna|shall|won't)\b|'ll", re.I)
NOW = re.compile(r"\b(now|right now|currently|today|at the moment|am|is|are)\b|\b[a-z]{3,}ing\b|'m|'re", re.I)
NUMW = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}
INV = {v: k for k, v in NUMW.items()}


def _first_word(t):
    m = re.match(r"\W*([A-Za-z']+)", t)
    return m.group(1).lower() if m else ""


def label_polarity(t):
    return "negated" if NEG.search(t) else "affirmative"


def label_speech_act(t):
    s, fw = t.strip(), _first_word(t)
    if re.search(r"\b(no thanks|i'll pass|i'd rather not|i won't|i will not|no, i|i refuse)\b", s, re.I):
        return "refusal"
    if re.match(r"(let's|how about|shall we|we should|we could|would you like|do you want)", s, re.I):
        return "offer/suggestion"
    if s.endswith("?"):
        if re.match(r"(can|could|would|will) you\b", s, re.I):
            return "request/command"
        return "question"
    if re.match(r"(yes|sure|okay|ok|of course)\b.*\b(i'll|i will|i can)\b", s, re.I):
        return "acceptance"
    if "please" in s.lower() or fw in IMPER:
        return "request/command"
    return "statement"


def label_agent(t):
    s, fw = t.strip(), _first_word(t)
    if WE.search(s):
        return "we/joint"
    if fw in IMPER and not re.match(r"(let's)", s, re.I):
        return "addressee"
    f, y = FIRST.search(s), SECOND.search(s)
    if f and y:
        return "speaker" if f.start() < y.start() else "addressee"
    if f:
        return "speaker"
    if y:
        return "addressee"
    return "third party"


def label_certainty(t):
    if t.strip().endswith("?") or label_speech_act(t) == "request/command":
        return "n/a (question/request)"
    h, b = HEDGE.search(t), BOOST.search(t)
    if h and not b:
        return "hedged/uncertain"
    if b and not h:
        return "strongly certain/emphatic"
    return "plain assertion"


def label_politeness(t):
    return "polite" if POLITE.search(t) else "plain"


def label_time(t):
    if LATER.search(t):
        return "later"
    if PAST.search(t):
        return "past"
    if NOW.search(t):
        return "now"
    return "unclear/mixed"


def label_quantity(t):
    nums = set()
    for m in re.finditer(r"\b\d+\b|\b[a-z]+\b", t.lower()):
        w = m.group(0)
        if w.isdigit():
            nums.add(INV.get(int(w), w))
        elif w in NUMW:
            nums.add(w)
    return nums.pop() if len(nums) == 1 else "unclear/mixed"


def label_time_quantity(t, ref=None):
    """hw/test 'time_quantity' families mix time (past/now/later) and number values."""
    if ref in ("past", "now", "later"):
        return label_time(t)
    return label_quantity(t)


def surface_label(dim, text, ref=None):
    if dim == "polarity":
        return label_polarity(text)
    if dim == "speech_act":
        return label_speech_act(text)
    if dim == "agent":
        return label_agent(text)
    if dim == "certainty":
        return label_certainty(text)
    if dim == "politeness":
        return label_politeness(text)
    if dim in ("time", "time_quantity"):
        return label_time_quantity(text, ref)
    if dim == "quantity":
        return label_quantity(text)
    return "unclear/mixed"


def surface_pass(dim, ref, text):
    return bool(critical_match(dim, ref, surface_label(dim, text, ref)))


# ---------------------------------------------------------------- (ii) overlap
def _norm_tokens(t):
    t = t.lower().replace("’", "'")
    for p, r in [(r"\bcan't\b", "can not"), (r"\bcannot\b", "can not"), (r"\bwon't\b", "will not"), (r"n't\b", " not"),
                 (r"'m\b", " am"), (r"'re\b", " are"), (r"'ll\b", " will"), (r"'ve\b", " have"), (r"let's", "let us")]:
        t = re.sub(p, r, t)
    toks = re.findall(r"\?|[a-z0-9]+", t)

    def stem(w):
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                return w[:-len(suf)]
        return w
    return {stem(w) for w in toks}


def unique_tokens(ref_src, other_src):
    a, b = _norm_tokens(ref_src), _norm_tokens(other_src)
    return a - b, b - a


def overlap_pass(text, ref_src, other_src):
    u_ref, u_oth = unique_tokens(ref_src, other_src)
    toks = _norm_tokens(text)
    if u_ref:
        return bool(u_ref & toks)
    return not (u_oth & toks)
