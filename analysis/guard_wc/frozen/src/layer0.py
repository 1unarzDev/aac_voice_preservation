"""Layer 0: deterministic general-dimension extraction (spaCy + lexicons).

Emits the SPEC option strings (src/labels.py) for polarity, speech_act, agent,
certainty and politeness from the OUTPUT text alone. Used for routing, as features,
and as a cheap cross-check of the LLM judge. It is NOT the measurement instrument:
rules are deliberately simple and their known blind spots are listed in
src/README_judge.md.

Hedges come from ~/aac-voice-preservation-old/src/hedges.txt (cited lexicon), matched
longest-first and non-overlapping (fixes the old metrics.py double count where
"i think" also counted "think"). spaCy splits "don't" into "do" + "n't"; we re-merge
clitics into surface words before matching, so "if you don't mind" still matches.
Because hedges.txt is a hedge-RATE lexicon, some entries are deontic/ability modals,
frequency adverbs, quantity approximators or politeness softeners rather than
epistemic uncertainty; those are routed away from `certainty` by the explicit sets
below (documented, reviewable).

  python src/layer0.py "I don't think I can come tonight."
  python src/layer0.py --jsonl runs/<run>/unique_outputs.jsonl --out runs/<run>/layer0.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import GENERAL_OPTIONS, NA_CERTAINTY  # noqa: E402

HEDGE_FILE = Path.home() / "aac-voice-preservation-old/src/hedges.txt"
LOCAL_HEDGE_COPY = Path(__file__).resolve().parent / "s1_hedges.txt"  # fallback only

# hedges.txt entries that are not epistemic uncertainty in short AAC sentences.
NOT_EPISTEMIC = {
    # ability / deontic / conditional modals ("I can come", "you should rest")
    "can", "could", "would", "should",
    # bare mental verbs: only the "i think"/"i guess" multiword forms are hedges
    "think", "thinks", "thought", "feel", "feels", "believe", "believes", "believed",
    "guess", "suppose", "supposed", "suggest", "suggests", "claim", "assumption",
    # frequency / generality, not certainty
    "often", "sometimes", "usually", "typically", "generally", "mainly", "largely",
    "tend", "tends", "tended", "tendency", "relatively", "virtually", "essentially",
    # quantity approximators belong to time/quantity, not certainty
    "about", "around", "approximately", "almost", "a couple of", "or so", "ish",
    # minimisers / degree words
    "just", "merely", "only", "simply", "slightly", "barely", "hardly", "quite",
    "rather", "fairly", "a bit", "a little", "a touch", "lil", "partially", "partly",
    # discourse particles
    "i mean", "you know", "to be fair", "if i'm honest", "sort of like",
}
# hedges.txt entries that are politeness softeners -> politeness, not certainty.
SOFTENERS_FROM_LEXICON = {
    "would you mind", "do you mind", "if you don't mind", "if possible", "if you like",
    "if that's okay", "if that's alright", "if that works", "if you get a chance",
    "when you get a chance", "whenever you get a chance", "no rush", "no pressure",
    "i was wondering", "i wonder", "i wondered",
}
APOLOGY_FROM_LEXICON = {"sorry"}
EXTRA_HEDGES = {"not sure", "don't know", "i don't think", "not certain", "might", "may",
                "i hope", "hopefully", "possibly", "i'm not sure"}
BOOSTERS = {"definitely", "certainly", "absolutely", "really", "totally", "surely",
            "for sure", "of course", "i'm sure", "i am sure", "i know", "no doubt",
            "without a doubt", "clearly", "obviously", "completely", "for real",
            "seriously", "i'm positive", "i am positive", "i promise", "100%", "always",
            "never ever", "really really"}
# D-007: "can you ...?" is a request but NOT a polite marker; polite = please, could you,
# would you (mind), thanks/sorry.
EXTRA_SOFTENERS = {"could you", "would you", "could i", "may i", "would it be possible", "would you be able", "is it okay if",
                   "is it ok if", "would it be okay", "do you think you could",
                   "if it's okay", "if it's ok"}
THANKS = {"thank", "thanks", "thank you", "sorry", "excuse me", "pardon", "apologize",
          "apologies", "my apologies", "i apologize"}

NEG_WORDS = {"not", "n't", "never", "no", "nothing", "nobody", "none", "nowhere",
             "neither", "nor", "noone", "cannot"}
REPLY_NO = {"no", "nope", "nah"}
REFUSAL_PATTERNS = [r"^(no|nope|nah)\b", r"\bno,? thank", r"\bi'?ll pass\b",
                    r"\bi('d| would) rather not\b", r"\bi refuse\b", r"\bnot for me\b",
                    r"\bi won't\b", r"\bi will not\b", r"\bi'm good,? thanks?\b"]
OFFER_Q = [r"^(shall|should) (i|we)\b", r"^how about\b", r"^what about\b",
           r"^why don't (we|you|i)\b", r"^do you want (me|to)\b", r"^would you like\b",
           r"^want to\b", r"^do you wanna\b"]
# D-007: "Can I ...?" / "Can we ...?" are questions; "Can you ...?" is a request.
REQUEST_Q = [r"^(please )?(can|could|would|will) you\b",
             r"^would you mind\b", r"^do you mind\b", r"^would it be possible\b",
             r"^is it (ok|okay) if\b", r"^would it be (ok|okay)\b", r"^do you think you could\b"]
OFFER_S = [r"^let'?s\b", r"^let us\b", r"^(maybe )?we (could|should|can|might)\b",
           r"^how about\b", r"^what about\b", r"^i (can|could|will|'ll)\b.*\bfor you\b",
           r"^you (could|should|might want to)\b", r"^maybe you (could|should)\b",
           r"^(i|we) suggest\b"]
# CB-1: "You need to ..." / "You're coming ..." are statements, not requests.
REQUEST_S = [r"^please\b", r"\bplease[.!]?$", r"^i (need|want) you to\b",
             r"^i('d| would) like you to\b"]
DESIRE_VERBS = {"want", "need", "like", "love", "hope", "wish", "plan", "try", "have",
                "would", "go"}
PRONOUN_AGENT = {"i": "speaker", "me": "speaker", "myself": "speaker",
                 "you": "addressee", "yourself": "addressee", "u": "addressee",
                 "we": "we/joint", "us": "we/joint", "ourselves": "we/joint",
                 "it": "unspecified", "there": "unspecified", "this": "unspecified",
                 "that": "unspecified"}
# Utterances made only of these words are formulaic ("Thank you so much!", "Hi!").
FORMULAIC = {"thanks", "thank", "you", "hi", "hello", "bye", "goodbye", "ok", "okay", "yes",
             "yeah", "sorry", "wow", "oh", "so", "much", "very", "a", "lot", "lots", "hey",
             "great", "cool", "good", "morning", "night"}
# Framing verbs: "I think he's coming" -> the main action is the complement clause.
FRAME_VERBS = {"think", "guess", "know", "believe", "hope", "feel", "bet", "suppose",
               "wonder", "say", "mean", "expect", "doubt", "heard", "hear"}
STATAL_BE = {"is", "are", "am", "'s", "'re", "'m"}
POSS_AGENT = {"my": "speaker", "your": "addressee", "our": "we/joint"}
BODY_PARTS = {"back", "cut", "ankle", "knee", "head", "leg", "arm", "hand", "foot", "feet",
              "stomach", "tooth", "teeth", "throat", "eye", "ear", "chest", "neck", "shoulder",
              "wrist", "skin", "nose", "hip", "finger", "toe", "body", "wound", "rash", "tummy"}
CLITICS = {"n't", "'s", "'m", "'re", "'ve", "'ll", "'d", "na"}


# ------------------------------------------------------------------ lexicon + matcher

def _words(s: str) -> list[str]:
    s = s.lower().replace("’", "'").replace("‘", "'")
    return re.findall(r"[a-z0-9%]+(?:'[a-z]+)*", s)


@lru_cache(maxsize=1)
def hedge_lexicon() -> tuple[str, ...]:
    path = HEDGE_FILE if HEDGE_FILE.exists() else LOCAL_HEDGE_COPY
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            out.append(" ".join(_words(line)))
    return tuple(dict.fromkeys(out))


@lru_cache(maxsize=1)
def phrase_table() -> dict[tuple[str, ...], str]:
    """phrase tokens -> category (hedge | booster | softener | thanks | please).

    Specific categories are written after hedges so they win for shared entries.
    """
    table: dict[tuple[str, ...], str] = {}
    for h in hedge_lexicon():
        if h in NOT_EPISTEMIC:
            continue
        cat = ("softener" if h in SOFTENERS_FROM_LEXICON
               else "thanks" if h in APOLOGY_FROM_LEXICON else "hedge")
        table[tuple(h.split())] = cat
    for cat, words in (("hedge", EXTRA_HEDGES), ("booster", BOOSTERS),
                       ("softener", EXTRA_SOFTENERS), ("thanks", THANKS),
                       ("please", {"please", "pls", "plz"})):
        for w in words:
            table[tuple(_words(w))] = cat
    return table


def match_phrases(words: list[str]) -> list[tuple[int, int, str, str]]:
    """Greedy longest-match, non-overlapping. Returns (start, end, phrase, category)."""
    table = phrase_table()
    max_len = max(len(k) for k in table)
    i, hits = 0, []
    while i < len(words):
        for n in range(min(max_len, len(words) - i), 0, -1):
            key = tuple(words[i:i + n])
            if key in table:
                hits.append((i, i + n, " ".join(key), table[key]))
                i += n
                break
        else:
            i += 1
    return hits


def surface_words(doc) -> list[str]:
    """spaCy tokens re-merged into surface words: 'do' + "n't" -> "don't",
    'ca' + "n't" -> "can't", 'gon' + 'na' -> 'gonna'. Punctuation dropped."""
    out: list[str] = []
    for t in doc:
        w = t.text.lower().replace("’", "'")
        if t.is_punct or t.is_space:
            continue
        glued = t.i > 0 and not doc[t.i - 1].whitespace_   # no space in the original
        if out and glued and (w in CLITICS or w.startswith("'")):
            out[-1] += w
            continue
        out.extend(_words(w) or [w])
    return out


@lru_cache(maxsize=1)
def nlp():
    import spacy
    return spacy.load("en_core_web_sm")


# ----------------------------------------------------------------------- dimensions

def _clean(text: str) -> str:
    t = text.strip().strip('"').strip("'").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", t)


def _has_any(pats: list[str], s: str) -> str | None:
    for p in pats:
        m = re.search(p, s)
        if m:
            return m.group(0)
    return None


def _neg_tokens(sub) -> list:
    return [t for t in sub if t.dep_ == "neg" or t.lower_ in NEG_WORDS - {"no"}
            or (t.lower_ == "no" and t.dep_ in ("det", "neg"))]


def polarity(doc, low: str) -> tuple[str, str]:
    """negated if every main clause (root + conj) is negated in its own clause or its
    xcomp/ccomp chain; mixed/unclear if only some are, or negation sits only in an
    adverbial/relative clause; affirmative otherwise. A reply 'No ...' negates."""
    first = _words(low)[:1]
    if first and first[0] in REPLY_NO:
        return "negated", first[0]
    heads = [t for t in doc if t.dep_ == "ROOT"]
    heads += [t for h in list(heads) for t in h.conjuncts if t.pos_ in ("VERB", "AUX", "ADJ")]

    def clause_neg(h) -> list:
        found, stack = [], [h]
        while stack:
            x = stack.pop()
            for c in x.children:
                if c.dep_ == "neg" or c.lower_ in {"never", "nothing", "nobody", "none",
                                                     "nowhere", "neither", "nor"} \
                        or (c.lower_ == "no" and c.dep_ in ("det", "neg", "intj")):
                    found.append(c)
                if c.dep_ in ("xcomp", "ccomp", "aux", "dobj", "attr", "acomp", "prep",
                              "pobj", "npadvmod", "advmod") and c not in heads:
                    stack.append(c)
        return found

    per = [clause_neg(h) for h in heads]
    all_neg = _neg_tokens(doc)
    if heads and all(per):
        return "negated", " ".join(t.text for t in per[0])
    if any(per) or all_neg:
        ev = all_neg[0].text if all_neg else ""
        return "mixed/unclear", ev
    return "affirmative", ""


def speech_act(doc, low: str) -> tuple[str, str]:
    s = re.sub(r"^(hey|hi|um|uh|oh|ok|okay|well|so|mom|dad),?\s+", "", low)
    s_nopunct = s.rstrip(" .!?")
    if (m := _has_any(REFUSAL_PATTERNS, s)):
        return "refusal", m
    is_q = low.rstrip().endswith("?")
    if is_q:
        if (m := _has_any(REQUEST_Q, s)):
            return "request/command", m
        if (m := _has_any(OFFER_Q, s)):
            return "offer/suggestion", m
        return "question", "?"
    if (m := _has_any(OFFER_S, s)):
        return "offer/suggestion", m
    if (m := _has_any(REQUEST_S, s_nopunct)):
        return "request/command", m
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    verbs = [t for t in doc if t.pos_ in ("VERB", "AUX")]
    words0 = _words(low)
    if words0 and all(w in FORMULAIC for w in words0):
        return "other", words0[0]
    if root is not None and root.tag_ == "VB" and not any(
            c.dep_ in ("nsubj", "nsubjpass", "expl") for c in root.children) \
            and root.i == next(t.i for t in doc if not t.is_punct and t.pos_ != "INTJ"):
        return "request/command", root.text
    words = _words(low)
    if words and all(w in FORMULAIC for w in words):
        return "other", words[0]
    return "statement", ""


def agent(doc, act: str, low: str) -> tuple[str, str]:
    s = re.sub(r"^(hey|hi|um|oh|ok|okay|well|so|please|no|yes),?\s+", "", low)
    if re.match(r"^let'?s\b|^let us\b", s):
        return "we/joint", "let's"
    if re.match(r"^let me\b", s):
        return "speaker", "let me"
    if m := re.match(r"^(can|could|would|will|may|shall|should|do) (i|you|we)\b", s):
        return PRONOUN_AGENT[m.group(2)], m.group(0)
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    if root is None:
        return "unspecified", ""

    def subj_of(v):
        for c in v.children:
            if c.dep_ in ("nsubj", "csubj", "expl"):
                return c
        # statal passive ("my cut is infected", "the lift is broken"): the subject holds
        # the state (CB-4); eventive/past passives ("was opened") stay agentless.
        if any(c.dep_ == "auxpass" and c.lower_ in STATAL_BE for c in v.children):
            for c in v.children:
                if c.dep_ == "nsubjpass":
                    return c
        return None

    v = root
    # "I want you to call" / "I need to go": main action is the complement verb.
    if root.lemma_ in DESIRE_VERBS | FRAME_VERBS:
        for c in root.children:
            if c.dep_ in ("xcomp", "ccomp") and c.pos_ in ("VERB", "AUX"):
                v = c
                break
    subj = subj_of(v) or (subj_of(root) if v is not root else None)
    if subj is None:
        if any(c.dep_ == "nsubjpass" for c in root.children):
            by = [c for c in root.children if c.dep_ == "agent"]
            return ("third party", by[0].text) if by else ("unspecified", "passive")
        if act == "request/command" or root.tag_ == "VB":
            return "addressee", root.text
        return "unspecified", ""
    w = subj.lower_
    if w in PRONOUN_AGENT:
        return PRONOUN_AGENT[w], subj.text
    # CB-4: the speaker's / listener's own body part ("my cut", "your back")
    poss = [c.lower_ for c in subj.children if c.dep_ == "poss"]
    if subj.pos_ == "NOUN" and poss and poss[0] in POSS_AGENT and subj.lemma_ in BODY_PARTS:
        return POSS_AGENT[poss[0]], f"{poss[0]} {subj.text}"
    if subj.pos_ in ("PRON", "PROPN", "NOUN"):
        if any(t.lower_ in ("i", "me") for t in subj.subtree) and any(
                t.dep_ == "cc" for t in subj.subtree):
            return "we/joint", " ".join(t.text for t in subj.subtree)
        return "third party", subj.text
    return "unspecified", subj.text


def label(text: str, doc=None) -> dict:
    """All five general dimensions for one output sentence, plus evidence strings."""
    text = _clean(text)
    low = text.lower()
    doc = doc if doc is not None else nlp()(text)
    words = surface_words(doc)
    hits = match_phrases(words)
    cats = {}
    for _, _, ph, cat in hits:
        cats.setdefault(cat, []).append(ph)

    pol, pol_ev = polarity(doc, low)
    act, act_ev = speech_act(doc, low)
    if act == "statement" and "please" in cats:
        act, act_ev = "request/command", "please"
    ag, ag_ev = agent(doc, act, low)

    if act in ("question", "request/command"):
        cert, cert_ev = NA_CERTAINTY, act
    elif "hedge" in cats:
        cert, cert_ev = "hedged/uncertain", cats["hedge"][0]
    elif "booster" in cats:
        cert, cert_ev = "strongly certain/emphatic", cats["booster"][0]
    else:
        cert, cert_ev = "plain assertion", ""

    # priority: please > softened request > thanks/apology > none
    soft = cats.get("softener", [])
    if "please" in cats:
        pol_lbl, pol_lbl_ev = "please", "please"
    elif soft:
        pol_lbl, pol_lbl_ev = "softened request (could you/would you mind)", soft[0]
    elif "thanks" in cats:
        pol_lbl, pol_lbl_ev = "thanks/apology", cats["thanks"][0]
    else:
        pol_lbl, pol_lbl_ev = "none", ""

    out = {"polarity": pol, "speech_act": act, "agent": ag, "certainty": cert,
           "politeness": pol_lbl,
           "evidence": {"polarity": pol_ev, "speech_act": act_ev, "agent": ag_ev,
                        "certainty": cert_ev, "politeness": pol_lbl_ev},
           "lexicon_hits": [[ph, cat] for _, _, ph, cat in hits]}
    for d, opts in GENERAL_OPTIONS.items():
        assert out[d] in opts, (d, out[d])
    return out


def label_many(texts: list[str]) -> list[dict]:
    cleaned = [_clean(t) for t in texts]
    return [label(t, d) for t, d in zip(cleaned, nlp().pipe(cleaned, batch_size=256))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("text", nargs="*")
    ap.add_argument("--jsonl", type=Path, help="file with {output_id, text} rows")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.jsonl:
        rows = [json.loads(l) for l in a.jsonl.read_text().splitlines() if l.strip()]
        labs = label_many([r["text"] for r in rows])
        out = a.out or a.jsonl.with_name("layer0.jsonl")
        with out.open("w") as fh:
            for r, l in zip(rows, labs):
                fh.write(json.dumps({"output_id": r["output_id"], **l}) + "\n")
        print(f"wrote {out} ({len(rows)} rows)")
        return 0
    for t in a.text:
        print(json.dumps({"text": t, **label(t)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
