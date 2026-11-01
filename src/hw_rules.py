"""Shared rules for human-written minimal pairs (B1): writer checks, extra word, chip derivation.

The writer tool annotation_package/write_pairs.html carries a JavaScript port of
`check_pair` / `extra_words` (same word lists, same order of checks). The parity test
tests/test_hw_rules_parity.js runs both on tests/fixtures/hw_rule_cases.json, so a change here
must be mirrored there. Word counting and keyword-to-source matching reuse
src/validate_items.py (`toks`, `matches`, `IRREG`, `CUE_WORDS`) unchanged.

Dimensions (writer value -> family critical value, chip):
  polarity    affirmative [YES] / negated [NOT]
  speech_act  statement [TELL] / question [?] / request/command [ASK]
  politeness  plain [PLAIN] / polite [PLEASE]
  certainty   plain assertion [SURE] / hedged/uncertain [MAYBE]
  agent       speaker [I] / addressee [YOU] / third party [THEY]
  time        past [PAST] / now [NOW] / later [LATER]   (family dimension 'time_quantity')
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_items import CUE_WORDS, IRREG, matches, toks  # noqa: E402

DIMS = {
    "polarity": {"code": "pol", "family_dim": "polarity",
                 "values": ["affirmative", "negated"],
                 "options": ["negated", "affirmative", "unclear/mixed"],
                 "chip": {"negated": "[NOT]", "affirmative": "[YES]"}},
    "speech_act": {"code": "act", "family_dim": "speech_act",
                   "values": ["statement", "question", "request/command"],
                   "options": ["statement", "question", "request/command", "refusal", "acceptance",
                               "offer/suggestion", "unclear/mixed"],
                   "chip": {"statement": "[TELL]", "question": "[?]", "request/command": "[ASK]"}},
    "politeness": {"code": "plt", "family_dim": "politeness",
                   "values": ["plain", "polite"],
                   "options": ["polite", "plain", "unclear/mixed"],
                   "chip": {"polite": "[PLEASE]", "plain": "[PLAIN]"}},
    "certainty": {"code": "cer", "family_dim": "certainty",
                  "values": ["plain assertion", "hedged/uncertain"],
                  "options": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
                  "chip": {"plain assertion": "[SURE]", "hedged/uncertain": "[MAYBE]"}},
    "agent": {"code": "agt", "family_dim": "agent",
              "values": ["speaker", "addressee", "third party"],
              "options": ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"],
              "chip": {"speaker": "[I]", "addressee": "[YOU]", "third party": "[THEY]"}},
    "time": {"code": "tim", "family_dim": "time_quantity",
             "values": ["past", "now", "later"],
             "options": ["past", "now", "later", "unclear/mixed"],
             "chip": {"past": "[PAST]", "now": "[NOW]", "later": "[LATER]"}},
}
# Writer CSVs may carry short value names; map them to the canonical critical values.
VALUE_ALIASES = {"request": "request/command", "hedged": "hedged/uncertain", "plain_assertion": "plain assertion",
                 "third_party": "third party", "third-party": "third party", "later/future": "later"}
TOPICS = ["health", "sensory", "boundaries", "work/school", "plans", "food", "transport", "money",
          "relationships", "self-advocacy", "hobbies"]

QWORDS = {"what", "where", "when", "who", "whom", "whose", "why", "how", "which"}
NEG_EXTRA = {"nothing", "nobody", "none", "nowhere", "neither", "nor", "cannot", "dont", "doesnt", "didnt",
             "wont", "cant", "isnt", "arent", "wasnt", "werent", "shouldnt", "couldnt", "wouldnt", "havent",
             "hasnt", "hadnt", "aint", "n't"}
POLITE = {"please", "pls", "plz", "thanks", "thank", "sorry", "kindly", "excuse", "mind"}
AUX = {"can", "will", "shall", "should", "must", "may", "might", "does", "did", "is", "are", "am", "was",
       "were", "would", "could", "'ll", "ll", "wo"}
PRON = {"him", "her", "them", "us", "our", "their", "his", "hers", "its", "it", "myself", "yourself",
        "yourselves", "ourselves", "themselves", "himself", "herself", "mine", "yours", "ours", "theirs",
        "someone", "somebody", "everyone", "everybody", "anyone", "anybody", "let's", "lets", "i'm", "i'll",
        "i've", "i'd", "you're", "you'll", "you've", "you'd", "we're", "we'll", "they're", "they'll",
        "he's", "she's", "it's", "y'all"}
HEDGES = {"maybe", "might", "may", "probably", "perhaps", "possibly", "likely", "unlikely", "guess", "suppose",
          "think", "believe", "seems", "seem", "apparently", "presumably", "kinda", "sorta", "prolly", "dunno",
          "doubt", "possible", "uncertain", "unclear", "suspect", "wonder"}
BOOSTERS = {"definitely", "really", "certainly", "absolutely", "surely", "totally", "sure", "obviously",
            "clearly", "honestly"}
TIME_WORDS = {"yesterday", "tomorrow", "today", "tonight", "now", "later", "soon", "already", "last", "next",
              "ago", "yet", "recently", "currently", "earlier", "then", "still", "just", "before", "after"}
CUES_ALL = CUE_WORDS | QWORDS | NEG_EXTRA | POLITE | AUX | PRON | HEDGES | BOOSTERS | TIME_WORDS
# Time words that may serve as the extra word outside the time dimension (as in r2: today, tonight).
NONCRIT_TIME_OK = {"yesterday", "tomorrow", "today", "tonight", "now", "later", "soon"}
# Function words never used as the extra (noncritical) word.
STOP = {"a", "an", "the", "to", "of", "in", "on", "at", "for", "with", "from", "by", "and", "or", "but",
        "so", "if", "as", "into", "onto", "about", "up", "out", "off", "over", "this", "that", "these",
        "those", "there", "here", "be", "been", "being", "do", "have", "has", "had", "i", "me", "my", "you",
        "your", "we", "our", "they", "them", "he", "she", "it", "its", "his", "her", "their", "is", "are",
        "am", "was", "were", "not", "no", "very", "too", "also", "some", "any", "all", "s", "t", "'s", "re",
        "ve", "d", "m", "ll", "than", "again", "back", "get", "got", "go", "going", "gone", "come", "every", "each",
        "other", "another", "more", "most", "much", "many", "few", "own", "same", "such", "both", "either",
        "something", "anything", "everything", "thing", "way", "lot", "bit"} | CUES_ALL
# Dimensions where the morphology of the keyword itself carries the cue (tense, person agreement):
# a keyword that matches one sentence exactly and the other only by inflection is an error, not a warning.
STRICT_FORM_DIMS = {"time", "agent"}
NEGATION_RE = re.compile(r"\b(not|never|no|nothing|nobody|none|neither|nor|cannot)\b|n't\b")
POLITE_RE = re.compile(r"\bplease\b|\bcould you\b|\bwould you\b|\bthank(s| you)\b|\bsorry\b")
HEDGE_RE = re.compile(r"\b(maybe|might|may|probably|perhaps|possibly|likely|i think|i guess|i suppose|not sure"
                      r"|could be|i doubt|i believe|seems?|apparently)\b")
BOOST_RE = re.compile(r"\b(definitely|really|certainly|absolutely|for sure|of course|i'm sure|surely|totally)\b")
PAST_RE = re.compile(r"\b(yesterday|ago|last|already|did|was|were|had)\b|\w{3,}ed\b")
LATER_RE = re.compile(r"\b(will|tomorrow|next|later|soon|tonight|going to)\b|'ll\b")
NOW_RE = re.compile(r"\b(now|right now|at the moment|currently|today)\b|\b(am|is|are|i'm|you're|we're|they're|"
                    r"he's|she's|it's)\s+\w+ing\b")
SPEAKER_RE = re.compile(r"\b(i|i'm|i'll|i've|i'd|my|me)\b")
ADDRESSEE_RE = re.compile(r"\b(you|you're|you'll|you've|you'd|your)\b")


def norm(s: str) -> str:
    return (s or "").lower().replace("’", "'").replace("‘", "'")


def cue_set(dim: str) -> set[str]:
    """Words that may never be keywords for this dimension."""
    return CUES_ALL


def base_of(w: str, t: str) -> bool:
    """Keyword w is the base form of source token t (finish/finished, make/made, bake/baking)."""
    return t.startswith(w) or IRREG.get(t) == w or (len(w) > 3 and w[-1] in "ey" and t.startswith(w[:-1]))


def kw_split(keywords: str) -> list[str]:
    return [w for w in re.split(r"[\s,]+", norm(keywords).strip()) if w]


def extra_words(a: str, b: str, kws: list[str], dim: str) -> list[str]:
    """Shared non-keyword content words, in sentence-A order: candidates for the noncritical word.
    The time words in NONCRIT_TIME_OK are allowed except for the time dimension (they would carry the cue there)."""
    tb = set(toks(b))
    excl = STOP if dim == "time" else (STOP - NONCRIT_TIME_OK)
    out = []
    for t in toks(a):
        if t in tb and t not in out and t not in excl and (len(t) >= 3 or t.isdigit()) \
                and not any(matches(w, t) for w in kws):
            out.append(t)
    return out


def check_pair(p: dict, dim: str) -> dict:
    """p = {A, B, valA, valB, keywords, situation}. Returns problems (blocking), warnings, extra words.
    Each problem/warning is (field, message)."""
    P, W = [], []
    vals = DIMS[dim]["values"]
    a, b = (p.get("A") or "").strip(), (p.get("B") or "").strip()
    ta, tb = toks(a), toks(b)
    for k, t in (("A", ta), ("B", tb)):
        if not t:
            P.append((k, f"Write sentence {k}."))
        elif not 4 <= len(t) <= 12:
            P.append((k, f"Sentence {k} has {len(t)} words; use 4 to 12."))
    if ta and tb and " ".join(ta) == " ".join(tb):
        P.append(("B", "Sentences A and B are the same; change B on the dimension only."))
    va, vb = p.get("valA") or "", p.get("valB") or ""
    if va not in vals:
        P.append(("valA", "Choose the value of sentence A."))
    if vb not in vals:
        P.append(("valB", "Choose the value of sentence B."))
    if va in vals and va == vb:
        P.append(("valB", "A and B must have different values."))
    raw = norm(p.get("keywords") or "").strip()
    kws = kw_split(raw)
    if not kws:
        P.append(("keywords", "Type the 2 to 4 keywords."))
    elif not 2 <= len(kws) <= 4:
        P.append(("keywords", f"{len(kws)} keywords; use 2 to 4."))
    bad_chars = [w for w in kws if not re.fullmatch(r"[a-z0-9']+", w)]
    if bad_chars:
        P.append(("keywords", "Use letters and numbers only (no ?, ! or hyphens): " + ", ".join(bad_chars)))
    cues = cue_set(dim)
    hits = [w for w in kws if w in cues or "n't" in w]
    if hits:
        P.append(("keywords", "These words give away the difference or are grammar words; leave them out: "
                  + ", ".join(hits)))
    if len(set(kws)) != len(kws):
        P.append(("keywords", "A keyword is repeated."))
    sa, sb = set(ta), set(tb)
    for w in kws:
        if w in hits or w in bad_chars:
            continue
        in_a = any(matches(w, t) for t in ta if len(t) >= 2)
        in_b = any(matches(w, t) for t in tb if len(t) >= 2)
        if not in_a or not in_b:
            miss = " and ".join(x for x, ok in (("A", in_a), ("B", in_b)) if not ok)
            P.append(("keywords", f"Keyword '{w}' is not in sentence {miss}; keywords must be in both."))
        elif (w in sa) != (w in sb) and not any(len(t) >= 2 and matches(w, t) and base_of(w, t)
                                                 for t in (tb if w in sa else ta)):
            if dim in STRICT_FORM_DIMS or w in IRREG:
                P.append(("keywords", f"Keyword '{w}' is the exact form of only one sentence; use the base "
                          "form (e.g. 'finish' for finished / will finish)."))
            else:
                W.append(("keywords", f"Keyword '{w}' matches one sentence exactly and the other only by its "
                          "ending; the base form is better."))
    ex = extra_words(a, b, kws, dim) if ta and tb else []
    if ta and tb and kws and not ex:
        P.append(("B", "Both sentences need one more shared word that is not a keyword (a place, time, object or "
                  "person), e.g. '... on the train'."))
    sit = p.get("situation") or ""
    if "\n" in sit or len(sit) > 140:
        P.append(("situation", "Keep the situation to one short line."))
    # soft checks: does each sentence carry its value's cue, and nothing else?
    for k, s, v in (("A", norm(a), va), ("B", norm(b), vb)):
        if not s or v not in vals:
            continue
        has = lambda rx: bool(rx.search(s))  # noqa: E731
        if dim == "polarity":
            if v == "negated" and not has(NEGATION_RE):
                W.append((k, f"Sentence {k} is marked negated but has no not / n't / never / no."))
            if v == "affirmative" and has(NEGATION_RE):
                W.append((k, f"Sentence {k} is marked affirmative but contains a negation."))
        elif dim == "politeness":
            if v == "polite" and not has(POLITE_RE):
                W.append((k, f"Sentence {k} is marked polite but has no please / could you / would you / thanks / sorry."))
            if v == "plain" and has(POLITE_RE):
                W.append((k, f"Sentence {k} is marked plain but contains a polite word."))
        elif dim == "speech_act":
            q = s.rstrip().endswith("?")
            if v == "question" and not q:
                W.append((k, f"Sentence {k} is marked question but does not end with '?'."))
            if v == "statement" and q:
                W.append((k, f"Sentence {k} is marked statement but ends with '?'."))
            if has(POLITE_RE):
                W.append((k, f"Sentence {k} contains a polite word; keep politeness out of speech-act pairs."))
            if re.search(r"\b(let's|lets|shall we|how about|no thanks)\b", s):
                W.append((k, f"Sentence {k} looks like an offer or refusal; use statement / question / request only."))
        elif dim == "certainty":
            if v == "hedged/uncertain" and not has(HEDGE_RE):
                W.append((k, f"Sentence {k} is marked hedged but has no maybe / might / probably / I think."))
            if v == "plain assertion" and has(HEDGE_RE):
                W.append((k, f"Sentence {k} is marked plain but contains a hedge."))
            if has(BOOST_RE):
                W.append((k, f"Sentence {k} contains a booster (really, definitely); plain means no hedge and no booster."))
            if s.rstrip().endswith("?"):
                W.append((k, f"Sentence {k} is a question; certainty pairs should be statements."))
        elif dim == "agent":
            if v == "speaker" and not has(SPEAKER_RE):
                W.append((k, f"Sentence {k} is marked speaker but has no I / my / me."))
            if v == "addressee" and not has(ADDRESSEE_RE):
                W.append((k, f"Sentence {k} is marked addressee but has no you / your."))
            if v == "third party" and re.match(r"\s*(i|i'm|i'll|i've|you|you're|you'll|we|let's)\b", s):
                W.append((k, f"Sentence {k} is marked third party but starts with I / you / we."))
            if re.search(r"\b(we|let's|us)\b", s):
                W.append((k, f"Sentence {k} mentions we / us; keep to I, you or someone else."))
        elif dim == "time":
            rx = {"past": PAST_RE, "later": LATER_RE, "now": NOW_RE}[v]
            if not has(rx):
                W.append((k, f"Sentence {k} is marked {v} but has no clear {v} tense or time word."))
        if dim != "certainty" and (has(HEDGE_RE) or has(BOOST_RE)):
            W.append((k, f"Sentence {k} contains a hedge or booster (maybe, really, ...); leave these out."))
    return {"problems": P, "warnings": W, "extra": ex, "keywords": kws, "ok": not P}


# ---------------------------------------------------------------- chips (collector only; needs spaCy)

ACT_CHIP = {"statement": "[TELL]", "question": "[?]", "request/command": "[ASK]"}
WANT_RE = re.compile(r"\bwant(s|ed)?\b")
MUST_RE = re.compile(r"\b(need|needs|needed) to\b|\b(have|has|had) to\b|\bmust\b")


def _det(det_fn, s):
    d = det_fn(s)
    lab = d["labels"]
    agent = next((c["chip"] for c in d["cues"] if c["dimension"] == "agent" and c["chip"]), None)
    if agent is None and lab["speech_act"] == "request/command":
        agent = "[YOU]"   # imperatives: the listener does it (codebook agent rule)
    times = {c["value"] for c in d["cues"] if c["dimension"] == "time"}
    return lab, agent, times


def derive_chips(dim: str, A: dict, B: dict, det_fn) -> tuple[dict, list[str]]:
    """Rule-derived chips/all_chips for both variants (r2 conventions, build_r2_c1.py docstring):
    critical chip from the critical value; all_chips adds speech act ([TELL]/[?]/[ASK]), agent when a
    doer is named, [PLAIN]/[PLEASE] on requests, [PAST]/[LATER] on statements/questions (none on
    requests; present gets none), [WANT]/[MUST], and [MAYBE]/[SURE] only when the detector finds a cue.
    Non-critical chips come from a reference variant (the unmarked one: affirmative, plain, plain
    assertion) and are copied to both, so they cannot differ inside a pair; for speech act, agent and
    time they are derived per variant and the critical dimension's own chips come from the values.
    det_fn = s1_cues.detect-like callable. Returns ({'A': {...}, 'B': {...}}, notes)."""
    spec = DIMS[dim]
    notes = []
    per = {k: _det(det_fn, v["source"]) for k, v in (("A", A), ("B", B))}
    ref = {"polarity": "affirmative", "politeness": "plain", "certainty": "plain assertion"}.get(dim)
    rk = None
    if ref:
        rk = "A" if A["critical_value"] == ref else "B"

    def extras(k):
        lab, agent, times = per[rk or k]
        src = norm((A if (rk or k) == "A" else B)["source"])
        act = ACT_CHIP.get(lab["speech_act"])
        if lab["speech_act"] == "refusal":
            act = "[TELL]"
        if act is None:
            notes.append(f"{rk or k}: detector speech act '{lab['speech_act']}' has no chip")
        out = []
        if dim != "speech_act" and act:
            out.append(act)
        if dim != "agent" and agent:
            out.append(agent)
        eff_act = (A if k == "A" else B)["critical_value"] if dim == "speech_act" else lab["speech_act"]
        if dim != "politeness" and eff_act == "request/command":
            s = norm((A if k == "A" else B)["source"])
            if "please" in s:
                out.append("[PLEASE]")
            elif not POLITE_RE.search(s):
                out.append("[PLAIN]")
        if dim != "time" and eff_act in ("statement", "question", "refusal"):
            if "past" in times:
                out.append("[PAST]")
            elif "future" in times:
                out.append("[LATER]")
        if WANT_RE.search(src):
            out.append("[WANT]")
        if MUST_RE.search(src):
            out.append("[MUST]")
        if dim != "certainty" and lab["certainty"] == "hedged/uncertain":
            out.append("[MAYBE]"); notes.append(f"{rk or k}: detector hedge")
        return out

    import prompts as Pm   # noqa: E402  (chip order)
    res = {}
    for k, v in (("A", A), ("B", B)):
        crit = spec["chip"][v["critical_value"]]
        allc = [crit] + [c for c in extras(k) if c != crit]
        res[k] = {"chips": [crit], "all_chips": Pm.sort_chips(list(dict.fromkeys(allc)))}
    if dim in ("speech_act", "time"):   # per-variant agent: drop when the two variants disagree
        ag = [next((c for c in res[k]["all_chips"] if c in ("[I]", "[YOU]", "[WE]", "[THEY]")), None) for k in "AB"]
        if ag[0] != ag[1]:
            for k in "AB":
                res[k]["all_chips"] = [c for c in res[k]["all_chips"] if c not in ("[I]", "[YOU]", "[WE]", "[THEY]")]
            notes.append(f"agent differs between variants ({ag[0]} vs {ag[1]}); agent chip dropped")
    return res, notes
