"""Deterministic scoped mutation operators and meaning-preserving surface edits for the
real-output oracle study (analysis/oracle_real/PLAN.md). Same operator families as W-A's
hand-written mutants: negation, speech-act flip, agent swap, certainty hedge/booster,
politeness add/remove, time shift. Each returns (mutant_text, expected_label) or None when
not applicable. No LLM, no randomness except a hash-chosen variant."""
from __future__ import annotations

import hashlib
import re

AUX = r"(?:is|are|was|were|am|can|could|will|would|should|may|might|must|shall|do|does|did|have|has|had)"
SUBJ = (r"(?:I|you|he|she|it|we|they|this|that|there|(?:the|my|your|our|his|her|their|a|an) [A-Za-z]+|[A-Z][a-z]+)")


def _h(text: str, salt: str, n: int) -> int:
    return int(hashlib.sha256((salt + "|" + text).encode()).hexdigest(), 16) % n


def _decap(s: str) -> str:
    if s.startswith("I ") or s.startswith("I'") or not s:
        return s
    return s[0].lower() + s[1:]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _sub1(pat, rep, t, flags=0):
    new, n = re.subn(pat, rep, t, count=1, flags=flags)
    return new if n else None


# ---------------------------------------------------------------- polarity
def negation_insert(t: str):
    if re.search(r"\b(not|never|no|n't|nothing|nobody|cannot)\b|n't", t, re.I):
        return None
    m = re.search(rf"\b({AUX})\b", t)
    if m and "?" not in t:
        a = m.group(1)
        rep = {"can": "cannot", "do": "do not", "does": "does not"}.get(a, a + " not")
        return t[:m.start()] + rep + t[m.end():], "negated"
    m = re.match(r"^(I|you|we|they) ([a-z]+)\b", t)
    if m and "?" not in t:
        return f"{m.group(1)} do not {m.group(2)}" + t[m.end():], "negated"
    m = re.match(r"^(he|she|it) ([a-z]+?)s\b", t)
    if m and "?" not in t:
        return f"{m.group(1)} does not {m.group(2)}" + t[m.end():], "negated"
    if "?" not in t:
        return "It is not the case that " + _decap(t), "negated"
    return None


def negation_remove(t: str):
    reps = [(r"\bcannot\b", "can"), (r"\bcan't\b", "can"), (r"\bwon't\b", "will"), (r"\bdon't\b", "do"),
            (r"\bdoesn't\b", "does"), (r"\bdidn't\b", "did"), (r"\b(is|are|was|were|has|have|had|could|would|should|must)n't\b", r"\1"),
            (r"\b(is|are|was|were|am|will|can|could|would|should|do|does|did|has|have|had) not\b", r"\1"),
            (r"\bnever\b", "always"), (r"\bnothing\b", "something"), (r"\bno (?=[a-z])", "some "), (r"\bnobody\b", "somebody")]
    for p, r in reps:
        new = _sub1(p, r, t, re.I)
        if new and new != t:
            return new, "affirmative"
    return None


# ---------------------------------------------------------------- speech act
def _invert_to_statement(t: str):
    m = re.match(rf"^({AUX}) ({SUBJ}) (.+)\?$", t, re.I)
    if not m:
        return None
    aux, subj, rest = m.groups()
    if subj.lower() in ("i", "you", "he", "she", "it", "we", "they", "this", "that", "there"):
        subj = "I" if subj.lower() == "i" else _cap(subj)
    else:
        subj = _cap(subj)
    return f"{subj} {aux.lower()} {rest}."


def speech_act_flip(t: str):
    t = t.strip()
    if t.endswith("?"):
        s = _invert_to_statement(re.sub(r"^please[, ]+", "", t, flags=re.I))
        return (s, "statement") if s else None
    # imperative -> statement with 'you'
    m = re.match(r"^(?:please[, ]+)?(bring|take|open|close|give|send|call|put|get|come|go|turn|help|wait|tell|show|check|pass|buy|make|let|stop|leave|read|write|clean|bring)\b(.*)$", t, re.I)
    if m:
        return f"You {m.group(1).lower()}{m.group(2)}", "statement"
    m = re.match(rf"^({SUBJ}) ({AUX}) (.+)\.$", t)
    if m:
        subj, aux, rest = m.groups()
        subj_l = subj if subj == "I" else _decap(subj)
        return f"{_cap(aux)} {subj_l} {rest}?", "question"
    if t.endswith("."):
        return "Is it true that " + _decap(t[:-1]) + "?", "question"
    return None


# ---------------------------------------------------------------- agent
def agent_swap(t: str, ref: str = ''):
    tl = t
    if ref == 'third party':
        m = re.match(r"^(They|He|She) (?!(?:told|asked|said|gave|showed)\b)(.+)$", t)
        if m and not re.search(r"\b(I|me|my|you|your|we|us|our)\b", t, re.I):
            rest = re.sub(r"^are\b", "am", re.sub(r"^were\b", "was", m.group(2)))
            return f"I {rest}", 'speaker'
        return None
    if ref == 'speaker' and re.search(r"\b(you|your|we|us|our|let's)\b", t, re.I):
        return None
    if ref == 'addressee' and re.search(r"\b(I|me|my|we|us|our)\b", t):
        return None
    if re.search(r"\b(I|me|my|I'm|I'll|I've|I'd|mine)\b", tl) and not re.search(r"\b(you|your|we|us|our|let's)\b", tl, re.I):
        out = tl
        for p, r in [(r"\bI am\b", "you are"), (r"\bI'm\b", "you're"), (r"\bI was\b", "you were"), (r"\bI'll\b", "you'll"),
                     (r"\bI've\b", "you've"), (r"\bI'd\b", "you'd"), (r"\bI\b", "you"), (r"\bme\b", "you"), (r"\bmy\b", "your"),
                     (r"\bmine\b", "yours")]:
            out = re.sub(p, r, out)
        out = _cap(out)
        return (out, "addressee") if out != t else None
    if re.search(r"\b(you|your|you're|you'll|you've|yours)\b", tl, re.I) and not re.search(r"\b(I|me|my|we|us|our)\b", tl):
        out = tl
        for p, r in [(r"\b[Yy]ou are\b", "I am"), (r"\b[Yy]ou're\b", "I'm"), (r"\b[Yy]ou were\b", "I was"), (r"\b[Yy]ou'll\b", "I'll"),
                     (r"\b[Yy]ou've\b", "I've"), (r"\b[Yy]ou\b", "I"), (r"\b[Yy]our\b", "my"), (r"\b[Yy]ours\b", "mine")]:
            out = re.sub(p, r, out)
        out = _cap(out)
        return (out, "speaker") if out != t else None
    m = re.match(r"^(Bring|Take|Open|Close|Give|Send|Call|Put|Get|Come|Go|Turn|Help|Wait|Tell|Show|Check|Pass|Buy|Make|Stop|Leave|Read|Write|Clean)\b(.*)$", t)
    if m:  # imperative (addressee) -> speaker
        return f"I {m.group(1).lower()}{m.group(2)}", "speaker"
    return None


# ---------------------------------------------------------------- certainty
HEDGE_RM = [r"\bmaybe,? ", r"\bperhaps,? ", r"\bprobably ", r"\bI think (?:that )?", r"\bI guess (?:that )?",
            r"\bI'm not sure (?:if |that )?", r"\bpossibly "]


def hedge_insert(t: str):
    if re.search(r"maybe|perhaps|probably|might|I think|I guess|not sure|possibly", t, re.I) or t.endswith("?"):
        return None
    return "Maybe " + _decap(t), "hedged/uncertain"


def booster_insert(t: str):
    if t.endswith("?"):
        return None
    return "Definitely, " + _decap(t), "strongly certain/emphatic"


def hedge_remove(t: str):
    out = t
    for p in HEDGE_RM:
        out = re.sub(p, "", out, flags=re.I)
    out = re.sub(r"\bmight\b|\bmay\b", "will", out)
    out = _cap(out.strip())
    return (out, "plain assertion") if out != t else None


# ---------------------------------------------------------------- politeness
def politeness_add(t: str, salt: str = ""):
    if re.search(r"please|thank|sorry|could you|would you|may I", t, re.I):
        return None
    if _h(t, salt + "pol", 2) == 0:
        return t.rstrip() + " Thank you." if t.rstrip()[-1] in ".!?" else t + ". Thank you.", "polite"
    return "Sorry, " + _decap(t), "polite"


def politeness_remove(t: str):
    out = t
    for p, r in [(r"\bplease,? ", ""), (r",? please\b", ""), (r"\s*Thank you[.!]?", ""), (r"\s*Thanks[.!]?", ""),
                 (r"^Sorry,? ", ""), (r"\bsorry,? ", ""), (r"^(Thank you|Thanks),? ", ""), (r"\bCould you\b", "Can you"),
                 (r"\bcould you\b", "can you"), (r"\bWould you mind\b", "Can you"), (r"\bWould you\b", "Can you"),
                 (r"\bwould you\b", "can you"), (r"\bMay I\b", "Can I"), (r"\bmay I\b", "can I")]:
        out = re.sub(p, r, out)
    out = _cap(out.strip())
    return (out, "plain") if out != t and out else None


# ---------------------------------------------------------------- time
IRR = {"went": "go", "ate": "eat", "saw": "see", "took": "take", "got": "get", "came": "come", "made": "make", "gave": "give",
       "bought": "buy", "told": "tell", "found": "find", "left": "leave", "met": "meet", "ran": "run", "wrote": "write",
       "felt": "feel", "slept": "sleep", "paid": "pay", "said": "say", "heard": "hear", "brought": "bring", "drank": "drink",
       "forgot": "forget", "lost": "lose", "sent": "send", "spoke": "speak", "woke": "wake"}
EVERB = {"like", "love", "use", "move", "close", "change", "hope", "share", "arrive", "live", "decide", "phone", "bake", "wave",
         "save", "type", "joke", "hate", "wipe", "smile", "taste", "wake", "serve", "raise", "pause", "price", "place", "name"}
NOT_VERB = {"need", "feed", "speed", "indeed", "bed", "red", "seed", "weed", "used", "hundred", "wicked", "naked", "tired", "worried"}


def _past_to_base(w: str):
    wl = w.lower()
    if wl in IRR:
        return IRR[wl]
    if wl.endswith("ed") and len(wl) > 4 and wl not in NOT_VERB:
        if wl.endswith("ied"):
            return wl[:-3] + "y"
        if wl[:-1] in EVERB:
            return wl[:-1]
        b = wl[:-2]
        return b[:-1] if len(b) > 2 and b[-1] == b[-2] and b[-1] not in "ls" else b
    return None


def _past_verb_to_future(t: str):
    out, done = [], False
    for tok in re.split(r"(\s+)", t):
        m = re.match(r"^([A-Za-z]+)(\W*)$", tok)
        if m and not done:
            b = _past_to_base(m.group(1))
            if b and tok != t.split()[0] or (b and tok == t.split()[0] and m.group(1)[0].islower()):
                out.append("will " + b + m.group(2)); done = True; continue
        out.append(tok)
    return "".join(out) if done else t


def _shift_rules(src: str, dst: str, t: str):
    R = {
        ("past", "later"): [(r"\byesterday\b", "tomorrow"), (r"\blast (night|week|month|year|weekend)\b", r"next \1"),
                            (r"\bearlier\b", "later"), (r"\b(\d+|a|an|one|two|three|few) (minutes?|hours?|days?|weeks?) ago\b", r"in \1 \2"),
                            (r"\b(?:was|were)\b", "will be"), (r"\bdid\b", "will"), (r"\bhad\b", "will have"), (r"\balready\b", "soon")],
        ("later", "past"): [(r"\btomorrow\b", "yesterday"), (r"\bnext (night|week|month|year|weekend)\b", r"last \1"),
                            (r"\btonight\b", "last night"), (r"\blater\b", "earlier"), (r"\b(you|we|they) will be\b", r"\1 were"),
                            (r"\bwill be\b", "was"), (r"\b(I|you|we|they|he|she|it|[A-Za-z]+)'ll\b", r"\1 did"), (r"\bwill\b", "did")],
        ("now", "past"): [(r"\bright now\b", "yesterday"), (r"\bnow\b", "yesterday"), (r"\btoday\b", "yesterday"),
                          (r"\b(you|we|they) are\b", r"\1 were"), (r"\bI am\b", "I was"), (r"\b(is|am)\b", "was"), (r"\bare\b", "were"),
                          (r"\bI'm\b", "I was"), (r"\b(you|we|they)'re\b", r"\1 were")],
        ("now", "later"): [(r"\bright now\b", "later"), (r"\bnow\b", "tomorrow"), (r"\btoday\b", "tomorrow"),
                           (r"\b(?:is|are|am)\b", "will be"), (r"\bI'm\b", "I will be"), (r"\b(you|we|they)'re\b", r"\1 will be")],
        ("past", "now"): [(r"\b(?:was)\b", "is"), (r"\bwere\b", "are"), (r"\bdid\b", "do"), (r"\bhad\b", "have")],
        ("later", "now"): [(r"\btomorrow\b", "right now"), (r"\btonight\b", "right now"), (r"\blater\b", "right now"),
                           (r"\bwill be\b", "is"), (r"\bI will\b", "I am"), (r"\b(you|we|they) will\b", r"\1 are")],
    }[(src, dst)]
    out = t
    for p, r in R:
        out = re.sub(p, r, out)
    if (src, dst) == ("past", "later") and out == t:
        out = _past_verb_to_future(t)
    elif (src, dst) == ("past", "later"):
        out = _past_verb_to_future(out)
    return out


def time_shift(t: str, ref: str, salt: str = ""):
    targets = {"past": ["later", "now"], "now": ["past", "later"], "later": ["past", "past"]}[ref]
    k = _h(t, salt + "time", 2)
    for dst in (targets[k], targets[1 - k]):
        out = _shift_rules(ref, dst, t)
        out = _cap(out)
        if out != t:
            return out, dst
    return None


# ---------------------------------------------------------------- dispatch
def mutate(dim: str, ref: str, t: str, salt: str = ""):
    """-> (operator, mutant, expected) or None. Operator names are the reporting unit."""
    r = None
    if dim == "polarity":
        if ref == "affirmative":
            r = negation_insert(t); op = "negation_insert"
        else:
            r = negation_remove(t); op = "negation_remove"
    elif dim == "speech_act":
        r = speech_act_flip(t)
        op = None if r is None else ("speech_act_to_question" if r[1] == "question" else "speech_act_to_statement")
    elif dim == "agent":
        r = agent_swap(t, ref); op = "agent_swap"
    elif dim == "certainty":
        if ref == "plain assertion":
            if _h(t, salt + "cert", 4) == 0:
                r = booster_insert(t); op = "booster_insert"
            else:
                r = hedge_insert(t); op = "hedge_insert"
        else:
            r = hedge_remove(t); op = "hedge_remove"
    elif dim == "politeness":
        if ref == "plain":
            r = politeness_add(t, salt); op = "politeness_add"
        else:
            r = politeness_remove(t); op = "politeness_remove"
    elif dim == "time_quantity":
        if ref in ("past", "now", "later"):
            r = time_shift(t, ref, salt); op = "time_shift"
    if r is None or r[0].strip() == t.strip():
        return None
    return op, r[0], r[1]


# ---------------------------------------------------------------- controls
SYN = {"big": "large", "large": "big", "small": "little", "little": "small", "start": "begin", "begin": "start",
       "buy": "purchase", "purchase": "buy", "car": "vehicle", "vehicle": "car", "medicine": "medication",
       "medication": "medicine", "shop": "store", "store": "shop", "movie": "film", "film": "movie",
       "kids": "children", "children": "kids", "mom": "mother", "dad": "father", "fix": "repair", "repair": "fix",
       "finish": "complete", "choose": "pick", "quick": "fast", "fast": "quick", "couch": "sofa", "sofa": "couch",
       "sick": "ill", "ill": "sick", "bathroom": "restroom", "restroom": "bathroom", "phone": "telephone"}
_CON_X = [(r"\bdon't\b", "do not"), (r"\bdoesn't\b", "does not"), (r"\bdidn't\b", "did not"), (r"\bisn't\b", "is not"),
          (r"\baren't\b", "are not"), (r"\bwasn't\b", "was not"), (r"\bwon't\b", "will not"), (r"\bcan't\b", "cannot"),
          (r"\bI'm\b", "I am"), (r"\byou're\b", "you are"), (r"\bwe're\b", "we are"), (r"\bthey're\b", "they are"),
          (r"\bI'll\b", "I will"), (r"\byou'll\b", "you will"), (r"\bI've\b", "I have"), (r"\blet's\b", "let us")]
_CON_C = [(r"\bdo not\b", "don't"), (r"\bdoes not\b", "doesn't"), (r"\bdid not\b", "didn't"), (r"\bis not\b", "isn't"),
          (r"\bare not\b", "aren't"), (r"\bwas not\b", "wasn't"), (r"\bwill not\b", "won't"), (r"\bcannot\b", "can't"),
          (r"\bI am\b", "I'm"), (r"\byou are\b", "you're"), (r"\bwe are\b", "we're"), (r"\bthey are\b", "they're"),
          (r"\bI will\b", "I'll"), (r"\byou will\b", "you'll"), (r"\bI have\b", "I've")]


def control_contraction(t: str):
    t = t.replace("\u2019", "'")
    for p, r in _CON_X + _CON_C:
        new = _sub1(p, r, t)
        if new and new != t:
            return new
    return None


def control_period(t: str):
    t2 = t.rstrip()
    return t2[:-1] if t2.endswith(".") and len(t2) > 3 else None


def control_commas(t: str):
    return re.sub(r"\s*,", "", t) if "," in t else None


def control_lowercase(t: str):
    return t[0].lower() + t[1:] if t and t[0].isupper() and not re.match(r"I\b", t) and not re.match(r"[A-Z][a-z]+ [A-Z]", t) else None


def control_synonym(t: str):
    for w in re.findall(r"[A-Za-z']+", t):
        if w.lower() in SYN:
            r = SYN[w.lower()]
            r = _cap(r) if w[0].isupper() else r
            return re.sub(rf"\b{re.escape(w)}\b", r, t, count=1)
    return None


CONTROL_TYPES = {"synonym": control_synonym, "contraction": control_contraction, "punctuation_commas": control_commas,
                 "case_initial": control_lowercase, "punctuation_period": control_period}


def control_edit(t: str, usage: dict):
    """Pick the applicable edit type used least so far (ties: declaration order). -> (type, edited) | None."""
    cands = []
    for k, (name, fn) in enumerate(CONTROL_TYPES.items()):
        out = fn(t)
        if out and out.strip() != t.strip():
            cands.append((usage.get(name, 0), k, name, out))
    if not cands:
        return None
    _, _, name, out = min(cands)
    return name, out
