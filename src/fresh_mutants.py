"""Fresh lexicon-blind meaning-change set (problem #10 part B). Rules: analysis/fresh_validation/PLAN.md sections B1-B3 (frozen before any call).
Builds CANDIDATES + private key only; no judge, no baselines, no scoring.

  python src/fresh_mutants.py stats   # template yield per family on the pool (no API calls)
  python src/fresh_mutants.py build   # templates + gemini-3.1-flash-lite (call cap 150); writes analysis/fresh_validation/mutants/*

Written without reading src/oracle_baselines.py or src/oracle_real_ops.py. oracle_baselines is imported only in finalize() to compute lex_visible
mechanically after the texts exist; it is never used to select or filter.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/fresh_validation/mutants"
RUNO = ROOT / "runs/fresh_validation"
SEED = 20261118
CALL_CAP = 150
N_MUT, N_CTL = 20, 10
FAMILIES = ["scope", "counterfactual", "obligation", "possessive_agent", "aspect"]
TARGET = {"scope": "polarity", "counterfactual": "certainty", "obligation": "speech_act", "possessive_agent": "agent", "aspect": "time_quantity"}
REFCOLS = ["polarity", "speech_act", "agent", "certainty", "politeness", "added_content"]

ROLES = ("mother father sister brother nurse friend doctor teacher ride driver aide helper caregiver therapist neighbor boss son daughter wife husband "
         "grandmother grandfather aunt uncle cousin partner coach tutor babysitter manager colleague roommate bus dad mom parents family team").split()
ROLE_RE = "|".join(ROLES)
APPLIC = {
    "scope": re.compile(r"\b(all|every|everyone|everything|both|any|anyone|never)\b|n't\b|\bnot\b", re.I),
    "counterfactual": re.compile(r"\b(will|am going to|are going to|is going to)\b|\b(I|we|you|they|he|she)\s+[a-z]+ed\b|\b(went|took|ate|saw|got|came|made|gave|bought|told|found|left|met|ran|wrote|paid|said|brought|had|did)\b", re.I),
    "obligation": re.compile(r"\b(can|can't|cannot|must|need|should|have to|may|will you|could)\b", re.I),
    "possessive_agent": re.compile(rf"\b(my|your|his|her|their|our) ({ROLE_RE})\b", re.I),
    "aspect": re.compile(r"\b(I|we|you|they|he|she|it)\s+(am|are|is|was|were|have|has|had|[a-z]+s?|[a-z]+ed)\b", re.I),
}
PRON = {"my": "your", "your": "my", "his": "my", "her": "your", "their": "my", "our": "your"}
PART = {"go": "gone", "take": "taken", "eat": "eaten", "see": "seen", "do": "done", "give": "given", "come": "come", "drive": "driven", "leave": "left",
        "get": "got", "bring": "brought", "buy": "bought", "make": "made", "send": "sent", "call": "called", "ask": "asked", "pick": "picked",
        "finish": "finished", "start": "started", "help": "helped", "visit": "visited", "clean": "cleaned", "cook": "cooked", "write": "written", "meet": "met"}
ING = {"going": "go", "taking": "take", "eating": "eat", "seeing": "see", "doing": "do", "giving": "give", "coming": "come", "driving": "drive",
       "leaving": "leave", "getting": "get", "bringing": "bring", "buying": "buy", "making": "make", "sending": "send", "calling": "call", "asking": "ask",
       "picking": "pick", "finishing": "finish", "starting": "start", "helping": "help", "visiting": "visit", "cleaning": "clean", "cooking": "cook",
       "writing": "write", "meeting": "meet"}
SUBJ = r"(I|We|You|They)"

PROMPTS = {
    "scope": "Rewrite the sentence so that the SCOPE of its negation or quantifier flips, changing the meaning while keeping the same words as far as possible. "
             "Examples: 'Not all of them came' -> 'All of them did not come'; 'I do not want everything' -> 'I want nothing'; 'Not every day is good' -> 'Every day is not good'. "
             "Output only the rewritten sentence, one sentence.\nSentence: {s}",
    "counterfactual": "Rewrite the sentence so that a real event or plan becomes a counterfactual (something that did not or will not happen), or a counterfactual becomes real. "
                      "Examples: 'I will go' -> 'I would have gone'; 'I took it' -> 'I would have taken it'; 'If I had gone' -> 'As I went'. Keep the rest as close as possible. "
                      "Output only the rewritten sentence, one sentence.\nSentence: {s}",
    "obligation": "Rewrite the sentence so that permission, obligation and necessity are swapped: a requirement becomes a permission or the reverse, or a prohibition becomes "
                  "'not needed'. Examples: 'You must not go' -> 'You need not go'; 'I must call' -> 'I may call'; \"You can't\" -> 'You shouldn't'. Keep the rest as close as possible. "
                  "Output only the rewritten sentence, one sentence.\nSentence: {s}",
    "possessive_agent": "Rewrite the sentence so that the person named by a possessive and a relationship noun changes to a different person, "
                        "and so the one who acts changes. Examples: 'My nurse gave it' -> 'Your nurse gave it'; 'Her mother will drive' -> 'My mother will drive'; "
                        "'Their ride is here' -> 'Your ride is here'. Change nothing else. Output only the rewritten sentence, one sentence.\nSentence: {s}",
    "aspect": "Rewrite the sentence so that the tense or aspect of the verb shifts, changing when the event happens, WITHOUT adding any time word such as "
              "yesterday, tomorrow, now, today, later, soon, ago. Examples: 'I was eating' -> 'I have eaten'; 'I eat' -> 'I am about to eat'; "
              "'I used to take it' -> 'I take it'; 'I am leaving' -> 'I have left'. Output only the rewritten sentence, one sentence.\nSentence: {s}",
}
TIME_BAN = re.compile(r"\b(yesterday|tomorrow|tonight|ago|now|today|later|soon)\b", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def toks(t):
    return re.findall(r"[a-z0-9']+", t.lower())


# ------------------------------------------------------------------ mutant templates (family -> list of fn(text)->text|None)
def t_scope(t):
    m = re.match(rf"^(.*?\b){SUBJ} (?:don't|do not) (\w+) (everything|everyone)\b(.*)$", t)
    if m:
        pre, s, v, obj, rest = m.groups()
        return f"{pre}{s} {v} {'nothing' if obj == 'everything' else 'no one'}{rest}"
    m = re.match(rf"^(.*?\b){SUBJ} never (\w+)\b(.*)$", t)
    if m and m.group(3).lower() not in ("be", "am", "are"):
        return f"{m.group(1)}{m.group(2)} don't always {m.group(3)}{m.group(4)}"
    m = re.match(rf"^(.*?\b){SUBJ} (?:don't|do not) always (\w+)\b(.*)$", t)
    if m:
        return f"{m.group(1)}{m.group(2)} never {m.group(3)}{m.group(4)}"
    return None


def t_counterfactual(t):
    m = re.match(rf"^(Yes, |Okay, )?{SUBJ} will ([a-z]+)\b(.*)$", t)
    if m and m.group(3) in PART:
        pre, s, v, rest = m.group(1) or "", m.group(2), m.group(3), m.group(4)
        return f"{pre}{s} would have {PART[v]}{rest}"
    m = re.match(rf"^(Yes, |Okay, )?{SUBJ}'ll ([a-z]+)\b(.*)$", t)
    if m and m.group(3) in PART:
        return f"{m.group(1) or ''}{m.group(2)} would have {PART[m.group(3)]}{m.group(4)}"
    return None


def t_obligation(t):
    if t.strip().endswith("?"):
        return None
    for a, b in [(r"\bmust not\b", "need not"), (r"\bneed not\b", "must not"), (r"\bmustn't\b", "needn't"), (r"\bdon't have to\b", "mustn't"),
                 (r"\bcan't\b", "shouldn't"), (r"\bcannot\b", "should not"), (r"\bshouldn't\b", "can't"), (r"\bhave to\b", "may"),
                 (r"\bmust\b", "may"), (r"\bshould\b", "may"), (r"\bmay\b", "must"), (r"\bcan\b", "must")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


def t_possessive_agent(t):
    m = re.search(rf"\b(my|your|his|her|their|our) ({ROLE_RE})\b", t, re.I)
    if not m:
        return None
    w = m.group(1)
    new = PRON[w.lower()]
    if w[0].isupper():
        new = new.capitalize()
    return t[:m.start(1)] + new + t[m.end(1):]


def t_aspect(t):
    m = re.match(rf"^(Yes, |Okay, )?(I|We|You|They|He|She) (am|are|is|was|were) ([a-z]+ing)\b(.*)$", t)
    if m and m.group(4) in ING and ING[m.group(4)] in PART:
        pre, s, _, ing, rest = m.groups()
        aux = "has" if s in ("He", "She") else "have"
        return f"{pre or ''}{s} {aux} {PART[ING[ing]]}{rest}"
    m = re.match(rf"^(Yes, |Okay, )?{SUBJ} ([a-z]+)\b(.*)$", t)
    if m and m.group(3) in PART and m.group(3) not in ("do",) and not t.strip().endswith("?"):
        aux = "am" if m.group(2) == "I" else "are"
        return f"{m.group(1) or ''}{m.group(2)} {aux} about to {m.group(3)}{m.group(4)}"
    return None


TEMPLATES = {"scope": t_scope, "counterfactual": t_counterfactual, "obligation": t_obligation, "possessive_agent": t_possessive_agent, "aspect": t_aspect}


# ------------------------------------------------------------------ control edits (meaning preserving, same family surface forms)
def c_scope(t):
    for a, b in [(r"\bnot all\b", "not every"), (r"\bnot every\b", "not all"), (r"\beveryone\b", "everybody"), (r"\beverybody\b", "everyone"),
                 (r"\bnobody\b", "no one"), (r"\bno one\b", "nobody"), (r"\bdon't\b", "do not"), (r"\bdoesn't\b", "does not"), (r"\bdidn't\b", "did not"),
                 (r"\bcan't\b", "cannot"), (r"\bwon't\b", "will not"), (r"\bisn't\b", "is not"), (r"\baren't\b", "are not")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


def c_counterfactual(t):
    for a, b in [(r"\bwould have\b", "would've"), (r"\bwould've\b", "would have"), (r"\bI will\b", "I'll"), (r"\bWe will\b", "We'll"),
                 (r"\bThey will\b", "They'll"), (r"\bYou will\b", "You'll"), (r"\bI would\b", "I'd"), (r"\bI'll\b", "I will")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


def c_obligation(t):
    for a, b in [(r"\bmust not\b", "mustn't"), (r"\bmustn't\b", "must not"), (r"\bcannot\b", "can't"), (r"\bcan't\b", "cannot"),
                 (r"\bneed not\b", "do not need to"), (r"\bdon't have to\b", "do not have to"), (r"\bshouldn't\b", "should not"), (r"\bshould not\b", "shouldn't")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


def c_possessive_agent(t):
    m = re.search(rf"\b(my|your) ({ROLE_RE})\b", t, re.I)
    if m:
        w, r = m.group(1).lower(), m.group(2)
        a = t[:m.start()] + f"the {r} of {'mine' if w == 'my' else 'yours'}" + t[m.end():]
        return a[0].upper() + a[1:] if t[:1].isupper() and m.start() == 0 else a
    return None


def c_aspect(t):
    for a, b in [(r"\bI am\b", "I'm"), (r"\bThey are\b", "They're"), (r"\bWe are\b", "We're"), (r"\bYou are\b", "You're"), (r"\bHe is\b", "He's"),
                 (r"\bShe is\b", "She's"), (r"\bI'm\b", "I am"), (r"\bI have been\b", "I've been")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


CONTROLS = {"scope": c_scope, "counterfactual": c_counterfactual, "obligation": c_obligation, "possessive_agent": c_possessive_agent, "aspect": c_aspect}
CTL_APPLIC = APPLIC  # control source must also be an applicable sentence of the family


# ------------------------------------------------------------------ pool
def pool(excl_ids, excl_texts):
    import pandas as pd
    d = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
    d = d[d.valid & d.channel.isin(["chip1", "chipall", "full"]) & (d.critical_match == True) & d.critical_source.isin(["agree", "arbiter"])  # noqa: E712
          & (~d.quarantine_refusal_acceptance)]
    rows, seen = [], set()
    for fid, g in d.sort_values(["family_id", "output_id"]).groupby("family_id", sort=True):
        for r in g.to_dict("records"):
            t = r["text"].strip()
            nw = len(t.split())
            if r["text_id"] in excl_ids or norm(t) in excl_texts or r["text_id"] in seen or not (3 <= nw <= 22):
                continue
            if re.findall(r"[.?!]", t[:-1]):
                continue
            seen.add(r["text_id"])
            rows.append(r)
    return rows


def exclusions():
    ids, texts = set(), set()
    for l in (ROOT / "analysis/oracle_real/sample.jsonl").read_text().splitlines():
        j = json.loads(l)
        ids.add(j["orig_text_id"])
        for k in ("original", "orig_text", "text"):
            if k in j:
                texts.add(norm(j[k]))
    for l in (ROOT / "analysis/oracle_indep/key.private.jsonl").read_text().splitlines():
        ids.add(json.loads(l)["text_id"])
    for l in (ROOT / "analysis/oracle_indep/candidates.jsonl").read_text().splitlines():
        texts.add(norm(json.loads(l)["original"]))
    return ids, texts


def valid_mut(s, o):
    if not o or norm(o) == norm(s):
        return False
    if not (0.5 <= len(o) / max(len(s), 1) <= 2.5) or re.findall(r"[.?!]", o.strip()[:-1]):
        return False
    if len(set(toks(s)) ^ set(toks(o))) > 6:
        return False
    if TIME_BAN.search(o) and not TIME_BAN.search(s):
        return False
    return True


class Gem:
    def __init__(self):
        import models
        self.spec = models.REGISTRY["gemini-3.1-flash-lite"]
        self.n, self.log, self.cache = 0, [], {}

    async def ask(self, client, fam, s):
        import gemini_backend as GB
        if (fam, s) in self.cache:
            return self.cache[(fam, s)]
        for attempt in range(2):                 # one retry on transport error
            if self.n >= CALL_CAP:
                return None
            self.n += 1
            r = await GB.call(client, {"prompt": PROMPTS[fam].format(s=s), "temperature": 0.0, "max_tokens": 96}, self.spec)
            txt = (r.get("raw_text") or "").strip().split("\n")[0].strip().strip('"')
            self.log.append({"family": fam, "src": s, "out": txt, "finish": r.get("finish_reason"), "err": r.get("error")})
            if not r.get("error"):
                self.cache[(fam, s)] = txt
                return txt
        return None


def draw_plan(P):
    """Per-family shuffled walks (seed fixed). Returns {family: [rows]}"""
    walks = {}
    for fam in FAMILIES:
        o = P[:]
        random.Random(f"{SEED}|fresh|{fam}").shuffle(o)
        walks[fam] = o
    return walks


async def build_async():
    import httpx
    ex_ids, ex_txt = exclusions()
    P = pool(ex_ids, ex_txt)
    walks = draw_plan(P)
    used_text, used_fam, gem = set(), set(), Gem()
    rows, short, ncalls_by = [], {}, {}
    synth_cap_note = "no synthetic sources used"
    # --- controls first (template edits only, no calls); sources are other families than any mutant source
    cg = {f: 0 for f in FAMILIES}
    for fam in FAMILIES:
        o = P[:]
        random.Random(f"{SEED}|fresh|ctl|{fam}").shuffle(o)
        for r in o:
            if cg[fam] >= N_CTL:
                break
            t = r["text"].strip()
            if r["text_id"] in used_text or r["family_id"] in used_fam or not CTL_APPLIC[fam].search(t):
                continue
            m = CONTROLS[fam](t)
            if m and norm(m) != norm(t):
                used_text.add(r["text_id"]); used_fam.add(r["family_id"]); cg[fam] += 1
                rows.append((r, "control", fam, m, "template", "real"))
    # --- pass 1: templates over the whole walk
    got = {f: 0 for f in FAMILIES}
    for fam in FAMILIES:
        for r in walks[fam]:
            if got[fam] >= N_MUT:
                break
            t = r["text"].strip()
            if r["text_id"] in used_text or r["family_id"] in used_fam or not APPLIC[fam].search(t):
                continue
            m = TEMPLATES[fam](t)
            if m and valid_mut(t, m):
                used_text.add(r["text_id"]); used_fam.add(r["family_id"]); got[fam] += 1
                rows.append((r, "mutant", fam, m, "template", "real"))
    # --- pass 2: LLM for the remainder
    async with httpx.AsyncClient() as client:
        for fam in FAMILIES:
            for r in walks[fam]:
                if got[fam] >= N_MUT:
                    break
                t = r["text"].strip()
                if r["text_id"] in used_text or r["family_id"] in used_fam or not APPLIC[fam].search(t):
                    continue
                m = await gem.ask(client, fam, t)
                if m is None and gem.n >= CALL_CAP:
                    break
                if m and valid_mut(t, m):
                    used_text.add(r["text_id"]); used_fam.add(r["family_id"]); got[fam] += 1
                    rows.append((r, "mutant", fam, m, "gemini", "real"))
            ncalls_by[fam] = gem.n
    short = {f: N_MUT - got[f] for f in FAMILIES if got[f] < N_MUT}
    return rows, gem, P, got, cg, short, ncalls_by


def finalize(rows, gem, P, got, cg, short):
    import oracle_baselines as B
    rng = random.Random(f"{SEED}|fresh|order")
    order = list(range(len(rows)))
    rng.shuffle(order)
    OUT.mkdir(parents=True, exist_ok=True)
    RUNO.mkdir(parents=True, exist_ok=True)
    cands, keys, counts = [], [], {}
    for i, k in enumerate(order):
        r, kind, fam, m, meth, stype = rows[k]
        cid = f"X{i:03d}"
        t = r["text"].strip()
        lex = bool((B.NEG.search(m) and not B.NEG.search(t)) or (B.PAST.search(m) and not B.PAST.search(t)) or (B.LATER.search(m) and not B.LATER.search(t)))
        cands.append({"id": cid, "original": t, "mutant": m, "dimension_hint": TARGET[fam]})
        keys.append({"id": cid, "kind": kind, "family": fam, "method": meth, "expected": "meaning_changed" if kind == "mutant" else "meaning_preserved",
                     "source_type": stype, "target_dimension": TARGET[fam], "text_id": r["text_id"], "family_id": r["family_id"], "model": r["model"],
                     "ref_labels": {c: (None if r.get(c) is None else str(r.get(c))) for c in REFCOLS}, "ref_dimension": r["dimension"], "ref_value": r["variant_value"],
                     "lex_visible": lex, "sentence_order_first": "mutant" if random.Random(f"{SEED}|fresh|coin|{cid}").random() < 0.5 else "original"})
        counts.setdefault(fam, {"mutant_template": 0, "mutant_gemini": 0, "control": 0})
        counts[fam]["control" if kind == "control" else f"mutant_{meth}"] += 1
    w = lambda p, xs: p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in xs))
    w(OUT / "candidates.jsonl", cands)
    w(OUT / "key.private.jsonl", keys)
    w(RUNO / "gemini_calls.jsonl", gem.log)
    draw = {"seed": SEED, "pool_size": len(P), "counts_by_family": counts, "n_mutants": sum(1 for x in keys if x["kind"] == "mutant"),
            "n_controls": sum(1 for x in keys if x["kind"] == "control"), "shortfall_mutants_by_family": short,
            "gemini_calls": gem.n, "call_cap": CALL_CAP, "model": "gemini-3.1-flash-lite", "synthetic_sources": 0,
            "lex_visible_mutants": sum(1 for x in keys if x["kind"] == "mutant" and x["lex_visible"]),
            "lex_visible_controls": sum(1 for x in keys if x["kind"] == "control" and x["lex_visible"])}
    (OUT / "draw.json").write_text(json.dumps(draw, indent=1))
    fz = {f: hashlib.sha256(p.read_bytes()).hexdigest() for f, p in (("candidates.jsonl", OUT / "candidates.jsonl"), ("key.private.jsonl", OUT / "key.private.jsonl"),
                                                                       ("src/fresh_mutants.py", Path(__file__)))}
    (OUT / "FREEZE_B.json").write_text(json.dumps(fz, indent=1))
    return draw


def stats():
    ex_ids, ex_txt = exclusions()
    P = pool(ex_ids, ex_txt)
    print("pool", len(P))
    for fam in FAMILIES:
        ap = [r for r in P if APPLIC[fam].search(r["text"].strip())]
        tm = [r for r in ap if (m := TEMPLATES[fam](r["text"].strip())) and valid_mut(r["text"].strip(), m)]
        ct = [r for r in ap if (m := CONTROLS[fam](r["text"].strip())) and norm(m) != norm(r["text"].strip())]
        print(fam, "applicable", len(ap), "template-ok", len(tm), "control-ok", len(ct), "| e.g.", [(r["text"], TEMPLATES[fam](r["text"].strip())) for r in tm[:2]])


def build():
    rows, gem, P, got, cg, short, nc = asyncio.run(build_async())
    d = finalize(rows, gem, P, got, cg, short)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    {"stats": stats, "build": build}[sys.argv[1]]()
