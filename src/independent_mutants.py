"""Independent mutation set (analysis/oracle_indep/PLAN.md, plan section B3). Builds CANDIDATES only; no judge scoring.

  python src/independent_mutants.py build     # seeded draw + templates + gemini-3.1-flash-lite (<=150 calls)
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402
import gemini_backend as GB  # noqa: E402
import models  # noqa: E402
import oracle_baselines as B  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/oracle_indep"
RUNO = ROOT / "runs/oracle_indep"
SEED = 20261117
CALL_CAP = 150
QUOTA = [("neg_fail_to", 13), ("neg_refuse_to", 13), ("neg_hardly", 12), ("neg_nobody", 10), ("role_passive", 14),
         ("role_embed", 12), ("q_embed", 12), ("time_implied", 14)]
OP_DIM = {"neg_fail_to": "polarity", "neg_refuse_to": "polarity", "neg_hardly": "polarity", "neg_nobody": "polarity",
          "role_passive": "agent", "role_embed": "agent", "q_embed": "speech_act", "time_implied": "time_quantity"}
TEMPLATE_OPS = {"neg_fail_to", "neg_refuse_to", "neg_hardly"}
N_CTL_CONTRACT, N_CTL_PARA = 10, 40
DIMS = ["agent", "certainty", "polarity", "politeness", "speech_act", "time_quantity"]

PROMPTS = {
    "neg_nobody": "Rewrite the sentence so that its meaning is reversed by making the subject a negative quantifier (for example 'Nobody ...' or 'No one ...') "
                  "instead of the original subject. Keep everything else as close as possible. Output only the rewritten sentence.\nSentence: {s}",
    "role_passive": "Rewrite the sentence so that the roles are swapped: whoever was doing the action becomes the one receiving it, and the receiver becomes the doer "
                    "(you may use the passive voice or a role inversion). Keep it one short natural sentence. Output only the rewritten sentence.\nSentence: {s}",
    "role_embed": "Rewrite the sentence as a report that someone else says or thinks it, e.g. 'She says that ...' or 'The nurse believes that ...', so the original speaker is no "
                  "longer the one making the claim or doing the action. Keep it one sentence. Output only the rewritten sentence.\nSentence: {s}",
    "q_embed": "Rewrite the question as a statement that embeds it, e.g. 'I wonder whether ...' or 'I am asking if ...' or 'She wants to know whether ...', so it is no longer a "
               "question but a declarative sentence. Output only the rewritten sentence.\nSentence: {s}",
    "time_implied": "Rewrite the sentence so the TIME of the event changes (past to future, future to past, or now to later) but express it only through verb tense or implication, "
                    "WITHOUT using explicit time words such as yesterday, tomorrow, tonight, ago, now, today, later, soon. Keep the rest the same. Output only the rewritten sentence.\nSentence: {s}",
    "ctl_paraphrase": "Paraphrase the sentence using different words or structure while keeping EXACTLY the same meaning: same polarity (do not add or remove any negation), same kind of "
                      "utterance (statement, question or request), same people doing and receiving the action, same time, same certainty, same politeness. "
                      "Output only the paraphrase as one sentence.\nSentence: {s}",
}
TIME_BAN = re.compile(r"\b(yesterday|tomorrow|tonight|ago)\b", re.I)
IRREG = set("took went ate saw got came made gave bought told found left met ran wrote felt slept paid said heard brought had did was were".split())
NOVERB = set("will can would could should must may might am are is was were have has do did want need like love think feel know shall 'll".split())
SUBJ = r"(I|We|You|They)"


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def pool(excl_ids):
    import pandas as pd
    d = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
    d = d[d.valid & d.channel.isin(["chip1", "chipall", "full"]) & (d.critical_match == True) & d.critical_source.isin(["agree", "arbiter"])  # noqa: E712
          & (~d.quarantine_refusal_acceptance)]
    out = {}
    for dim in DIMS:
        sub = d[d.dimension == dim].sort_values(["family_id", "output_id"])
        rng = random.Random(f"{SEED}|pool|{dim}")
        seen, rows = set(), []
        for fid, g in sub.groupby("family_id", sort=True):
            recs = g.to_dict("records")
            rng.shuffle(recs)
            for r in recs:
                t = r["text"].strip()
                nw = len(t.split())
                if r["text_id"] in excl_ids or r["text_id"] in seen or not (3 <= nw <= 22):
                    continue
                if len(re.findall(r"[.?!]", t[:-1])) > 0:
                    continue
                seen.add(r["text_id"]); rows.append(r); break
        out[dim] = rows
    return out


def tmpl_neg(op, t):
    m = re.match(rf"^(Yes, )?{SUBJ}( will| 'll)? ([a-z]+)\b(.*)$", t)
    m2 = re.match(rf"^(Yes, )?{SUBJ} (am|are)\b(.*)$", t) if op == "neg_hardly" else None
    m3 = re.match(rf"^(Yes, )?{SUBJ} can\b(.*)$", t) if op == "neg_hardly" else None
    if m3:
        return f"{m3.group(1) or ''}{m3.group(2)} can hardly{m3.group(3)}"
    if m2:
        return f"{m2.group(1) or ''}{m2.group(2)} {m2.group(3)} hardly{m2.group(4)}"
    if not m:
        return None
    pre, s, modal, v, rest = m.group(1) or "", m.group(2), m.group(3) or "", m.group(4), m.group(5)
    if v.lower() in NOVERB or v in IRREG or v.endswith("ed") or v.endswith("s"):
        return None
    if op == "neg_fail_to":
        return f"{pre}{s}{modal} fail to {v}{rest}"
    if op == "neg_refuse_to":
        return f"{pre}{s}{modal} refuse to {v}{rest}"
    if op == "neg_hardly":
        return f"{pre}{s}{modal} hardly {v}{rest}"
    return None


def tmpl_contract(t):
    if B.NEG.search(t):
        return None
    for a, b in [(r"\bI am\b", "I'm"), (r"\bThey are\b", "They're"), (r"\bWe are\b", "We're"), (r"\bYou are\b", "You're"),
                 (r"\bI will\b", "I'll"), (r"\bThey will\b", "They'll"), (r"\bWe will\b", "We'll"), (r"\bYou will\b", "You'll"),
                 (r"\bI have\b", "I've"), (r"\bWhat is\b", "What's"), (r"\bThere is\b", "There's")]:
        if re.search(a, t):
            return re.sub(a, b, t, count=1)
    return None


class Gem:
    def __init__(self):
        self.spec = models.REGISTRY["gemini-3.1-flash-lite"]
        self.n = 0
        self.log = []
        self.cache = {}
        f = RUNO / "gemini_calls.jsonl"
        if f.exists():  # reuse earlier temperature-0 responses (same op+sentence) so calls are not re-spent
            for l in f.read_text().splitlines():
                x = json.loads(l)
                if not x.get("err") and x.get("out") is not None:
                    self.cache[(x["op"], x["src"])] = x
                self.log.append(x)
                if not x.get("cached"):
                    self.n += 1

    async def ask(self, client, op, s):
        if (op, s) in self.cache:
            return self.cache[(op, s)]["out"]
        if self.n >= CALL_CAP:
            return None
        self.n += 1
        req = {"prompt": PROMPTS[op].format(s=s), "temperature": 0.0, "max_tokens": 96}
        r = await GB.call(client, req, self.spec)
        txt = (r.get("raw_text") or "").strip().split("\n")[0].strip().strip('"')
        ent = {"op": op, "src": s, "out": txt, "finish": r.get("finish_reason"), "err": r.get("error")}
        self.log.append(ent)
        if not ent["err"]:
            self.cache[(op, s)] = ent
        return txt

    def valid(self, op, s, o):
        if not o or norm(o) == norm(s):
            return False
        if not (0.5 <= len(o) / max(len(s), 1) <= 2.5) or len(re.findall(r"[.?!]", o[:-1])) > 0:
            return False
        if op != "ctl_paraphrase" and TIME_BAN.search(o) and not TIME_BAN.search(s):
            return False
        if op == "q_embed" and o.strip().endswith("?"):
            return False
        return True


async def build_async():
    ex = {json.loads(l)["orig_text_id"] for l in (ROOT / "analysis/oracle_real/sample.jsonl").read_text().splitlines()}
    P = pool(ex)
    used, rows, gem = set(), [], Gem()
    def take(dim, op, pred=lambda r: True):
        o = P[dim][:]
        random.Random(f"{SEED}|{op}").shuffle(o)
        return [r for r in o if pred(r)]
    async with httpx.AsyncClient() as client:
        for op, n in QUOTA:
            dim = OP_DIM[op]
            pred = (lambda r: r["variant_value"] == "affirmative") if dim == "polarity" else (
                (lambda r: r["variant_value"] == "question" and r["text"].strip().endswith("?")) if op == "q_embed" else (lambda r: True))
            got = 0
            cand = take(dim, op, pred)
            if op in TEMPLATE_OPS:  # polarity pool is small after exclusions: top up with non-negated texts from other dimensions
                extra = [r for d2 in DIMS if d2 != dim for r in take(d2, op) if not B.NEG.search(r["text"]) and r["text"].strip()[-1] != "?"]
                cand = cand + extra
            for r in cand:
                if got >= n:
                    break
                if r["text_id"] in used:
                    continue
                if op in TEMPLATE_OPS:
                    m = tmpl_neg(op, r["text"].strip())
                    meth = "template"
                else:
                    m, meth = None, "gemini"
                    for _ in range(2):
                        m = await gem.ask(client, op, r["text"].strip())
                        if m is None or gem.valid(op, r["text"], m):
                            break
                    if m is None or not gem.valid(op, r["text"], m):
                        m = None
                if not m:
                    continue
                used.add(r["text_id"]); got += 1
                rows.append((r, "mutant", op, m, meth))
        # controls
        got = 0
        allp = [(d, r) for d in DIMS for r in P[d]]
        random.Random(f"{SEED}|ctl_contraction").shuffle(allp)
        for d, r in allp:
            if got >= N_CTL_CONTRACT:
                break
            if r["text_id"] in used:
                continue
            m = tmpl_contract(r["text"].strip())
            if m:
                used.add(r["text_id"]); got += 1; rows.append((r, "control", "ctl_contraction", m, "template"))
        random.Random(f"{SEED}|ctl_paraphrase").shuffle(allp)
        got = 0
        for d, r in allp:
            if got >= N_CTL_PARA:
                break
            if r["text_id"] in used:
                continue
            m = None
            for _ in range(2):
                m = await gem.ask(client, "ctl_paraphrase", r["text"].strip())
                if m is None or gem.valid("ctl_paraphrase", r["text"], m):
                    break
            if m is None and gem.n >= CALL_CAP:
                break
            if not m or not gem.valid("ctl_paraphrase", r["text"], m):
                continue
            used.add(r["text_id"]); got += 1; rows.append((r, "control", "ctl_paraphrase", m, "gemini"))
    return rows, gem, P


def build():
    rows, gem, P = asyncio.run(build_async())
    rng = random.Random(f"{SEED}|order")
    order = list(range(len(rows)))
    rng.shuffle(order)
    OUT.mkdir(parents=True, exist_ok=True); RUNO.mkdir(parents=True, exist_ok=True)
    cands, keys, counts = [], [], {}
    for i, k in enumerate(order):
        r, kind, op, m, meth = rows[k]
        cid = f"I{i:03d}"
        t = r["text"].strip()
        cands.append({"id": cid, "original": t, "mutant": m})
        lex = bool((B.NEG.search(m) and not B.NEG.search(t)) or (B.PAST.search(m) and not B.PAST.search(t) and op == "time_implied")
                   or (B.LATER.search(m) and not B.LATER.search(t) and op == "time_implied"))
        keys.append({"id": cid, "kind": kind, "op": op, "method": meth, "expected": "meaning_changed" if kind == "mutant" else "meaning_preserved",
                     "dimension": r["dimension"], "ref_value": r["variant_value"], "text_id": r["text_id"], "family_id": r["family_id"],
                     "variant": r["variant"], "model": r["model"], "channel": r["channel"], "lex_visible": lex})
        counts[op] = counts.get(op, 0) + 1
    w = lambda p, xs: p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in xs))
    w(OUT / "candidates.jsonl", cands)
    w(OUT / "key.private.jsonl", keys)
    w(RUNO / "gemini_calls.jsonl", gem.log)
    (OUT / "draw.json").write_text(json.dumps({"seed": SEED, "pool_sizes": {d: len(v) for d, v in P.items()}, "counts_by_operator": counts,
                                               "n_mutants": sum(1 for x in keys if x["kind"] == "mutant"),
                                               "n_controls": sum(1 for x in keys if x["kind"] == "control"),
                                               "gemini_calls": gem.n, "model": "gemini-3.1-flash-lite",
                                               "lex_visible_mutants": sum(1 for x in keys if x["kind"] == "mutant" and x["lex_visible"])}, indent=1))
    print(json.dumps(counts, indent=1), gem.n)


if __name__ == "__main__":
    if sys.argv[1:] == ["build"]:
        build()
