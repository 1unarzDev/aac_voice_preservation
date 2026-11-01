"""LLM extraction judge (SPEC v0.1 "Label schema"), two prompt variants J1/J2.

Blindness by construction. Two separate calls per batch:
  pass A  extraction: the judge sees ONLY the output sentence + the family's critical
          dimension question/options + the general dimensions. No input, source,
          model, prompt or channel.
  pass B  added_content: the judge sees the output sentence + the VISIBLE input string
          (keywords/chips, or the typed sentence for the `full` channel). Nothing else.
J1 and J2 differ in wording and in option order (J2 lists every option set reversed;
item order within a batch also differs). The critical label is routed to
`needs_arbiter` when J1 != J2.

Units (text_id = explode.py's sha1 of the normalised text, so identical texts from
different models/requests are judged once)
  A-unit = (text_id, critical dimension, critical_options)  -- dedups across families
  B-unit = (text_id, visible input)
  judgments.jsonl has one row per J-unit = (text_id, family_id, input_text), i.e. per
  distinct (text, critical question, visible input) occurring in the run.

Cache: cache/judge/<variant>.jsonl, key = sha256(variant, template sha, model, text,
dimension, options[, input]). Re-running costs nothing for cached items.

  python src/judge.py --run fixture                 # both variants, writes judgments.jsonl
  python src/judge.py --run fixture --report-only   # recompute agreement report
  python src/judge.py --run fixture --gold tests/fixtures/fixture_gold.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layer0  # noqa: E402
import runio  # noqa: E402
from labels import (ADDED_CONTENT_OPTIONS, DEFINITIONS, GENERAL_DIMS,  # noqa: E402
                    GENERAL_OPTIONS)

ROOT = runio.ROOT
CACHE_DIR = ROOT / "cache/judge"
LEGEND = (ROOT / "prompts/chip_legend.txt")
JUDGE_MODEL = "gpt-6.1-sol"
API_BASE = "https://codex.lunarz.dev/v1"
BATCH = 25
CONCURRENCY = 16
MAX_TRIES = 5

# Critical-dimension questions, mirrored in annotation/CODEBOOK.md (decision_log D-007).
CRITICAL_Q = {
    "polarity": "Is the main thing the sentence says negated (not/never/no/don't) or "
                "affirmative? Uncertainty wording like 'not sure' is unclear/mixed.",
    "agent": "Who does the main (content) action of the sentence? speaker = I/me, incl. the "
             "speaker's own body part; addressee = you (incl. commands and 'can you ...?'); "
             "we/joint = we, let's, you and I; third party = other people or inanimate things; "
             "in 'I think X' code X's doer; unclear/mixed = no doer or several.",
    "certainty": "How sure does the sentence sound about its claim? plain assertion = stated "
                 "as fact; hedged/uncertain = maybe, might, probably, I think; strongly "
                 "certain/emphatic = definitely, really, for sure. Questions, requests or "
                 "no claim = unclear/mixed.",
    "speech_act": "What does the sentence do? statement = tells; question = asks for "
                  "information or permission ('Can I ...?' is a question); request/command "
                  "= asks the listener to do something ('Can you ...?' is a request); "
                  "refusal = declines; acceptance = agrees/accepts ('Yes, I'll ...'); "
                  "offer/suggestion = proposes (let's, how about). Several = unclear/mixed.",
    "politeness": "Does the sentence contain an explicit polite marker? polite = please, "
                  "could you, would you (mind), thank you/thanks, sorry. plain = none of "
                  "these ('can you ...?' alone is plain).",
    "time": "When does the main event happen? past = already happened; now = happening at "
            "the moment or right now; later = in the future. Use tense and time words. No "
            "time or several = unclear/mixed.",
    "quantity": "What exact number does the sentence state for the main thing? If no number, "
                "a vague amount (some, a few) or several numbers = unclear/mixed.",
}
GENERIC_Q = "What value does this sentence express for '{dim}'? Choose unclear/mixed if it " \
            "does not commit to one option."


def critical_question(dimension: str, options: list[str]) -> str:
    if dimension == "time_quantity":   # pilot items mix time and number families
        return CRITICAL_Q["time" if {"past", "now", "later"} & set(options) else "quantity"]
    return CRITICAL_Q.get(dimension, GENERIC_Q.format(dim=dimension))


RULES_J1 = """Decision rules:
- Label only what the sentence itself explicitly says. Do not guess the writer's intent.
- polarity: negation of the main clause or its complement ("I don't want to go" = negated). "No," as a reply = negated. Negation that only expresses uncertainty ("I'm not sure") = mixed/unclear. One clause negated and another not = mixed/unclear.
- speech_act: request/command = imperatives, "can/could/would/will you ...?", any sentence with "please" that asks for something. A declarative with a "you" subject ("You need to ...", "You're coming ...", "You'll ...") is a statement unless it is imperative or a question-form request. offer/suggestion = "let's", "how about", "we should/could", "shall we", "do you want to ...?", "would you like ...?". refusal = an explicit declining formula ("no thanks", "I'll pass", "I'd rather not", "I won't"). "I want/need X" = statement. "Can I ...?" / "May I ...?" (asking permission or information) = question. Greetings/thanks only = other.
- agent: the doer of the CONTENT verb, not of the speech act ("No, you can't borrow my car" -> addressee; "I still owe you" -> speaker). "I want/need to X" -> subject of X (speaker). "I want/need X" with no second verb ("I want the window open", "I need help with my shoes") -> speaker (CB-6). "I want you to X" -> addressee. Imperatives -> addressee. "let's"/"we"/"you and I" -> we/joint. In hedged sentences ("I think X", "Maybe X") code the agent of the embedded clause X, never the "I" of "I think". Other people and inanimate things (the bus, the lift, the sauce, dinner) -> third party, but the speaker's own body parts ("my back", "my cut") -> speaker (yours -> addressee). Dummy "it/there" or passive with no doer -> unspecified.
- certainty: questions and requests/commands -> "n/a (question/request)". hedged/uncertain = maybe, might, may, probably, I think, I guess, not sure. strongly certain/emphatic = definitely, really, for sure, of course, absolutely, I'm sure. Otherwise plain assertion. An exclamation mark alone does not count.
- politeness: pick the highest present: please > softened request (could you / would you / would you mind / may I / if possible / when you get a chance) > thanks/apology (thank you, sorry, excuse me) > none. "Can you ...?" alone is NOT a softener (none).
- critical: use ONLY that item's options; choose unclear/mixed when the sentence commits to none or to more than one.
- evidence: copy the shortest exact words from the sentence (max 6 words) that decide the critical label; "" if the label rests on absence."""

RULES_J2 = """How to code (apply literally):
* Code the words on the page, never the person's probable meaning.
* critical: answer with one option from that item's own list. If the sentence does not commit, or commits to two, answer unclear/mixed.
* politeness - if several markers occur, keep the strongest in this order: "please", then a softened request (would you mind / could you / would you / may I / if possible), then thanks/apology. No marker -> none. A bare "can you ...?" has no marker -> none.
* certainty - for questions or requests/commands always "n/a (question/request)". Words like definitely, for sure, really, of course, absolutely = strongly certain/emphatic. Words like maybe, might, probably, perhaps, I think, not sure = hedged/uncertain. "!" by itself changes nothing. Otherwise plain assertion.
* agent - the doer of the content verb (not of the speech act: "No, you can't borrow my car" -> addressee). Commands and "can you ...?" -> addressee. "I need to go" -> speaker; "I want the window open"/"I need help" (no second verb) -> speaker (CB-6); "I want you to go" -> addressee; "we"/"let's" -> we/joint; other people and inanimate subjects (the bus, mom, the lift, dinner) -> third party; the speaker's own body part ("my ankle hurts") -> speaker, the listener's -> addressee; no doer (it/there, agentless passive) -> unspecified. In "I think X" or "Maybe X", code X's subject, never the "I" of "I think".
* speech_act - "let's ...", "how about ...", "we should ...", "do you want to ...?", "would you like ...?" are offer/suggestion. Imperatives, "could/can/would you ...?" and asks containing "please" are request/command. Declaratives with a "you" subject ("You need to ...", "You're driving ...", "You'll ...") are statement unless imperative or a question-form request. "Can I ...?" / "May I ...?" are question. A refusal needs explicit declining ("no thanks", "I'd rather not", "I won't"). Saying "I want X" is a statement. Only greetings/thanks -> other.
* polarity - negated when the main clause (or what it embeds, as in "I don't want to go") is negated, incl. a reply "No, ...". "I'm not sure" style uncertainty, or one negated plus one affirmative clause -> mixed/unclear.
* evidence - shortest exact quote (<= 6 words) from the sentence that decides the critical answer; "" when the answer rests on something being absent."""

ADDED_J1 = """Each item gives the INPUT the user typed (content keywords, optional bracketed chips, or a typed sentence) and a SENTENCE produced from it.
Question: does the SENTENCE assert a fact, reason, person, place or time that is NOT in the INPUT?
- Grammar and function words (the, to, is, a), inflections, pronouns, and the meanings of chips in the INPUT do not count.
- Changes of negation, certainty/hedging words (maybe, I think, definitely), politeness words (please, sorry), question form or who does it are NOT added content: they are coded separately.
- Count as added: a new time word (today, tonight, later), a new person (mom, everyone), a new place, a reason or explanation ("because ...", "it's hot"), a new object or fact.
- Answer yes or no, and put the added words in `evidence` ("" if no).
"""
ADDED_J2 = """You will see pairs: TYPED = what a user entered (words, maybe chips in brackets, or a full sentence) and OUTPUT = a sentence built from it.
For each pair decide: does OUTPUT state any new information that TYPED does not contain - a person, place, time, reason or fact?
Ignore small grammar words, word endings, pronouns, and anything a chip in TYPED already says.
Also ignore negation, hedges or boosters (maybe, I think, really), politeness words and question form; those are coded elsewhere. Only new facts count.
New time words (now, today), new people, new places, explanations ("because", "it's raining") and new objects all count as new.
Reply no or yes; in `evidence` quote the new words ("" for no).
"""


def legend() -> str:
    return LEGEND.read_text().strip() if LEGEND.exists() else ""


def _h(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def template_sha(variant: str) -> str:
    rules = RULES_J1 if variant == "J1" else RULES_J2
    added = ADDED_J1 if variant == "J1" else ADDED_J2
    return _h(rules, added, CRITICAL_Q, GENERIC_Q, DEFINITIONS, GENERAL_OPTIONS, legend())[:12]


def opts(variant: str, options: list[str]) -> list[str]:
    return list(options) if variant == "J1" else list(reversed(options))


# ------------------------------------------------------------------------- prompts

def build_a(variant: str, batch: list[dict]) -> tuple[list[dict], dict]:
    gen_block = "\n".join(
        f"- {d}: {DEFINITIONS[d]} Options: {json.dumps(opts(variant, GENERAL_OPTIONS[d]))}"
        for d in (GENERAL_DIMS if variant == "J1" else list(reversed(GENERAL_DIMS))))
    items = [{"id": u["key_id"], "sentence": u["text"],
              "critical_question": critical_question(u["dimension"], u["critical_options"]),
              "critical_options": opts(variant, u["critical_options"])} for u in batch]
    if variant == "J1":
        sys_msg = ("You are a careful linguistic annotator. You extract what a short message "
                   "explicitly expresses, one dimension at a time.")
        user = (f"Label every item. For each item answer its own critical question, then the "
                f"general dimensions.\n\nGeneral dimensions (same for all items):\n{gen_block}\n\n"
                f"{RULES_J1}\n\nItems:\n{json.dumps(items, ensure_ascii=False, indent=0)}")
    else:
        sys_msg = ("You code short everyday messages for a linguistics study. Accuracy and "
                   "literal reading matter more than interpretation.")
        user = (f"{RULES_J2}\n\nEvery message also gets these five codes:\n{gen_block}\n\n"
                f"Messages to code (answer each message's critical_question with one of its "
                f"critical_options):\n{json.dumps(items, ensure_ascii=False, indent=0)}")
    crit_union = sorted({o for u in batch for o in u["critical_options"]})
    props = {"id": {"type": "string", "enum": [u["key_id"] for u in batch]},
             "critical": {"type": "string", "enum": crit_union},
             "evidence": {"type": "string"}}
    for d in GENERAL_DIMS:
        props[d] = {"type": "string", "enum": opts(variant, GENERAL_OPTIONS[d])}
    order = ["id", "critical", "evidence"] + GENERAL_DIMS
    schema = _wrap(props, order)
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}], schema


def build_b(variant: str, batch: list[dict]) -> tuple[list[dict], dict]:
    if variant == "J1":
        items = [{"id": u["key_id"], "INPUT": u["input_text"], "SENTENCE": u["text"]} for u in batch]
        user = f"{ADDED_J1}\n{legend()}\n\nItems:\n{json.dumps(items, ensure_ascii=False, indent=0)}"
        sys_msg = "You are a careful linguistic annotator."
    else:
        items = [{"id": u["key_id"], "TYPED": u["input_text"], "OUTPUT": u["text"]} for u in batch]
        user = f"{ADDED_J2}\n{legend()}\n\nPairs:\n{json.dumps(items, ensure_ascii=False, indent=0)}"
        sys_msg = "You code short everyday messages for a linguistics study."
    props = {"id": {"type": "string", "enum": [u["key_id"] for u in batch]},
             "added_content": {"type": "string", "enum": opts(variant, ADDED_CONTENT_OPTIONS)},
             "evidence": {"type": "string"}}
    return ([{"role": "system", "content": sys_msg}, {"role": "user", "content": user}],
            _wrap(props, ["id", "added_content", "evidence"]))


def _wrap(props: dict, order: list[str]) -> dict:
    return {"type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": order,
                "properties": {k: props[k] for k in order}}}}}


# --------------------------------------------------------------------------- cache

class Cache:
    def __init__(self, variant: str):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.path = CACHE_DIR / f"{variant}.jsonl"
        self.d: dict[str, dict] = {}
        if self.path.exists():
            for l in self.path.read_text().splitlines():
                if l.strip():
                    r = json.loads(l)
                    self.d[r["key"]] = r["value"]
        self.fh = self.path.open("a")

    def get(self, k):
        return self.d.get(k)

    def put(self, k, v):
        self.d[k] = v
        self.fh.write(json.dumps({"key": k, "value": v}, ensure_ascii=False) + "\n")
        self.fh.flush()


def key_a(variant, model, u) -> str:
    return _h(variant, template_sha(variant), model, u["text"], u["dimension"],
              u["critical_options"])


def key_b(variant, model, u) -> str:
    return _h(variant, template_sha(variant), model, u["text"], "added_content",
              ADDED_CONTENT_OPTIONS, u["input_text"])


# ------------------------------------------------------------------------- calling

class Stats:
    def __init__(self):
        self.calls = 0; self.fail = 0; self.latency = []; self.prompt_tok = 0
        self.compl_tok = 0; self.reason_tok = 0; self.t0 = time.time()


async def call_batch(client, sem, stats, log, model, effort, variant, pass_, batch):
    """Call one batch; validate; retry missing/invalid items. Returns {key_id: value}."""
    build = build_a if pass_ == "A" else build_b
    todo, got = list(batch), {}
    for attempt in range(MAX_TRIES):
        if not todo:
            break
        msgs, schema = build(variant, todo)
        t = time.time()
        try:
            async with sem:
                r = await client.chat.completions.create(
                    model=model, messages=msgs, reasoning_effort=effort,
                    response_format={"type": "json_schema", "json_schema": {
                        "name": f"judge_{pass_}", "strict": True, "schema": schema}},
                    timeout=180)
            dt = time.time() - t
            stats.calls += 1; stats.latency.append(dt)
            u = r.usage
            if u:
                stats.prompt_tok += u.prompt_tokens or 0
                stats.compl_tok += u.completion_tokens or 0
                rt = getattr(u.completion_tokens_details, "reasoning_tokens", 0) or 0
                stats.reason_tok += rt
            out = json.loads(r.choices[0].message.content)["items"]
        except Exception as e:  # noqa: BLE001 -- network, 429, bad JSON: retry
            stats.fail += 1
            log.write(json.dumps({"variant": variant, "pass": pass_, "n": len(todo),
                                  "error": f"{type(e).__name__}: {str(e)[:200]}",
                                  "attempt": attempt}) + "\n")
            await asyncio.sleep(min(60, 2 ** attempt + random.random()))
            continue
        log.write(json.dumps({"variant": variant, "pass": pass_, "n": len(todo),
                              "latency_s": round(dt, 2), "attempt": attempt,
                              "prompt_tokens": u.prompt_tokens if u else None,
                              "completion_tokens": u.completion_tokens if u else None}) + "\n")
        by_id = {u_["key_id"]: u_ for u_ in todo}
        for o in out:
            unit = by_id.get(o.get("id"))
            if unit is None or o["id"] in got:
                continue
            if pass_ == "A" and o["critical"] not in unit["critical_options"]:
                continue  # option from another item's list: re-ask
            got[o["id"]] = {k: v for k, v in o.items() if k != "id"}
        todo = [u_ for u_ in todo if u_["key_id"] not in got]
    return got


_SEM: asyncio.Semaphore | None = None


def shared_sem() -> asyncio.Semaphore:
    """One semaphore for ALL passes/variants: total in-flight calls <= CONCURRENCY."""
    global _SEM
    if _SEM is None:
        _SEM = asyncio.Semaphore(CONCURRENCY)
    return _SEM


async def run_pass(units, variant, pass_, model, effort, stats, log, batch_size=BATCH):
    from openai import AsyncOpenAI
    import models  # harness registry: reads the key, never prints it
    client = AsyncOpenAI(base_url=API_BASE, api_key=models.api_key(), max_retries=2)
    cache = Cache(variant)
    keyf = key_a if pass_ == "A" else key_b
    for u in units:
        u["key_id"] = "k" + keyf(variant, model, u)[:10]
        u["_ck"] = keyf(variant, model, u)
    results = {u["key_id"]: cache.get(u["_ck"]) for u in units if cache.get(u["_ck"])}
    todo = list({u["key_id"]: u for u in units if u["key_id"] not in results}.values())
    rng = random.Random(f"{variant}-{pass_}")
    rng.shuffle(todo)   # different item order per variant
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    sem = shared_sem()
    by_key = {u["key_id"]: u for u in units}

    async def one(b):   # cache each batch as soon as it returns (resumable after a crash)
        got = await call_batch(client, sem, stats, log, model, effort, variant, pass_, b)
        for kid, v in got.items():
            cache.put(by_key[kid]["_ck"], v)
            results[kid] = v
    await asyncio.gather(*[one(b) for b in batches])
    missing = [u for u in units if u["key_id"] not in results]
    print(f"  {variant}/{pass_}: {len(units)} units, {len(todo)} uncached, "
          f"{len(batches)} calls, {len(missing)} still missing")
    return {u["_ck"]: results.get(u["key_id"]) for u in units}


# ------------------------------------------------------------------------ assembly

def build_units(run_dir: Path, items_path: Path | None):
    occ = [o for o in runio.load_occurrences(run_dir) if o["valid"]]
    items = runio.load_items(runio.items_path_for(run_dir, items_path))
    junits, a_units, b_units = {}, {}, {}
    for o in occ:
        it = items.get(o["family_id"])
        if it is None:
            raise SystemExit(f"family {o['family_id']} not in items file")
        jk = (o["text_id"], o["family_id"], o["input_text"])
        if jk in junits:
            continue
        ak = (o["text_id"], it["dimension"], tuple(it["critical_options"]))
        bk = (o["text_id"], o["input_text"])
        junits[jk] = {"text_id": o["text_id"], "family_id": o["family_id"],
                      "input_text": o["input_text"], "text": o["text"],
                      "dimension": it["dimension"],
                      "critical_options": it["critical_options"], "_ak": ak, "_bk": bk}
        a_units.setdefault(ak, {"text": o["text"], "dimension": it["dimension"],
                                "critical_options": it["critical_options"]})
        b_units.setdefault(bk, {"text": o["text"], "input_text": o["input_text"]})
    return list(junits.values()), a_units, b_units


def _final(a, b, tiebreak=None):
    if a == b:
        return a, False
    if tiebreak is not None and tiebreak in (a, b):
        return tiebreak, True
    return None, True


async def judge_run(run_dir: Path, items_path, model, effort, variants):
    junits, a_units, b_units = build_units(run_dir, items_path)
    stats = Stats()
    log = (run_dir / "judge_calls.jsonl").open("a")
    res = {}
    jobs = [(v, p) for v in variants for p in ("A", "B")]   # all share one <=16 semaphore
    outs = await asyncio.gather(*[
        run_pass([dict(u) for u in (a_units if p == "A" else b_units).values()],
                 v, p, model, effort, stats, log) for v, p in jobs])
    got = dict(zip(jobs, outs))
    for v in variants:
        res[v] = ({k: got[(v, "A")][key_a(v, model, u)] for k, u in a_units.items()},
                  {k: got[(v, "B")][key_b(v, model, u)] for k, u in b_units.items()})
    elapsed = time.time() - stats.t0
    l0 = dict(zip([u["text_id"] for u in junits],
                  layer0.label_many([u["text"] for u in junits])))
    rows = []
    for u in junits:
        r = {k: u[k] for k in ("text_id", "family_id", "input_text", "text", "dimension",
                               "critical_options")}
        for v in variants:
            a = res[v][0].get(u["_ak"]) or {}
            b = res[v][1].get(u["_bk"]) or {}
            r[f"{v}_critical"] = a.get("critical")
            r[f"{v}_evidence"] = a.get("evidence")
            for d in GENERAL_DIMS:
                r[f"{v}_{d}"] = a.get(d)
            r[f"{v}_added_content"] = b.get("added_content")
            r[f"{v}_added_evidence"] = b.get("evidence")
        L = l0[u["text_id"]]
        for d in GENERAL_DIMS:
            r[f"L0_{d}"] = L[d]
        if len(variants) == 2:
            j1, j2 = variants
            r["critical"], r["needs_arbiter"] = _final(r[f"{j1}_critical"], r[f"{j2}_critical"])
            r["general_disagree"] = []
            for d in GENERAL_DIMS:
                # general dims: agreement, else layer0 breaks the tie, else null
                r[d], dis = _final(r[f"{j1}_{d}"], r[f"{j2}_{d}"], L[d])
                if dis:
                    r["general_disagree"].append(d)
            r["added_content"], dis = _final(r[f"{j1}_added_content"], r[f"{j2}_added_content"])
            if dis:
                r["general_disagree"].append("added_content")
        rows.append(r)
    runio.write_jsonl(run_dir / "judgments.jsonl", rows)
    lat = sorted(stats.latency) or [0]
    perf = {"model": model, "reasoning_effort": effort, "api_calls": stats.calls,
            "failed_calls": stats.fail, "elapsed_s": round(elapsed, 1),
            "calls_per_min": round(stats.calls / max(elapsed, 1e-9) * 60, 1),
            "latency_median_s": round(lat[len(lat) // 2], 2), "latency_max_s": round(lat[-1], 2),
            "prompt_tokens": stats.prompt_tok, "completion_tokens": stats.compl_tok,
            "reasoning_tokens": stats.reason_tok,
            "template_sha": {v: template_sha(v) for v in variants}}
    print(f"wrote {run_dir/'judgments.jsonl'} ({len(rows)} rows)\nperf: {json.dumps(perf)}")
    (run_dir / "judge_perf.json").write_text(json.dumps(perf, indent=1))
    return rows


# -------------------------------------------------------------------------- report

def agreement_report(rows: list[dict], gold: list[dict] | None = None) -> dict:
    """J1-J2 agreement (critical, general, added), layer0-vs-judge per general dim,
    and optionally judge-vs-gold accuracy."""
    import pandas as pd
    from agree_stats import cohen_kappa
    rep: dict = {"n_units": len(rows)}

    def agree(a, b):
        pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
        if not pairs:
            return None
        x, y = zip(*pairs)
        return {"n": len(pairs), "agree": round(sum(p == q for p, q in pairs) / len(pairs), 3),
                "kappa": cohen_kappa(list(x), list(y))}

    df = pd.DataFrame(rows)
    rep["J1_vs_J2"] = {d: agree(df[f"J1_{d}"], df[f"J2_{d}"])
                       for d in ["critical"] + GENERAL_DIMS + ["added_content"]}
    rep["J1_vs_J2_critical_by_dim"] = {
        dim: agree(g["J1_critical"], g["J2_critical"]) for dim, g in df.groupby("dimension")}
    rep["needs_arbiter"] = int(df["needs_arbiter"].sum())
    # one row per output for general dims (general labels don't depend on family)
    dfo = df.drop_duplicates("text_id")
    rep["layer0_vs_J1"] = {d: agree(dfo[f"L0_{d}"], dfo[f"J1_{d}"]) for d in GENERAL_DIMS}
    rep["layer0_vs_J2"] = {d: agree(dfo[f"L0_{d}"], dfo[f"J2_{d}"]) for d in GENERAL_DIMS}
    if gold:
        g = {(x["text_id"], x["family_id"], x["input_text"]): x for x in gold}
        acc: dict = {}
        for src in ["J1", "J2", "L0", "final"]:
            for d in ["critical"] + GENERAL_DIMS + ["added_content"]:
                if src == "L0" and d in ("critical", "added_content"):
                    continue
                col = d if src == "final" else f"{src}_{d}"
                pr = [(r[col], g[k][d]) for r in rows
                      if (k := (r["text_id"], r["family_id"], r["input_text"])) in g]
                n_ok = sum(a == b for a, b in pr)
                acc.setdefault(src, {})[d] = {"n": len(pr), "acc": round(n_ok / len(pr), 3),
                                              "n_null": sum(a is None for a, _ in pr)}
        rep["vs_fixture_gold"] = acc
        errs = []
        for r in rows:
            k = (r["text_id"], r["family_id"], r["input_text"])
            if k not in g:
                continue
            for d in ["critical"] + GENERAL_DIMS + ["added_content"]:
                for src in ("J1", "J2"):
                    if r[f"{src}_{d}"] != g[k][d]:
                        errs.append(f"{src} {d:13s} gold={g[k][d]!r:32} got={r[f'{src}_{d}']!r:32} "
                                    f"| {r['text']}" + (f"  [in: {r['input_text']}]"
                                                         if d == "added_content" else ""))
        rep["gold_errors"] = errs
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True, help="run id (runs/<run>) or a path")
    ap.add_argument("--items", type=Path, default=None)
    ap.add_argument("--model", default=JUDGE_MODEL)
    ap.add_argument("--effort", default="low", choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--variants", default="J1,J2")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--concurrency", type=int, default=16,
                    help="max in-flight judge calls (default 16; D-019: <=8 when the endpoint is shared)")
    ap.add_argument("--gold", type=Path, default=None, help="optional hand labels to score")
    a = ap.parse_args()
    run_dir = Path(a.run) if Path(a.run).exists() else ROOT / "runs" / a.run
    globals()["CONCURRENCY"] = a.concurrency   # read by shared_sem()
    if a.report_only:
        rows = runio.read_jsonl(run_dir / "judgments.jsonl")
    else:
        rows = asyncio.run(judge_run(run_dir, a.items, a.model, a.effort, a.variants.split(",")))
    gold = runio.read_jsonl(a.gold) if a.gold else None
    rep = agreement_report(rows, gold)
    (run_dir / "judge_report.json").write_text(json.dumps(rep, indent=1))
    for k, v in rep.items():
        if k == "gold_errors":
            print(f"\n{k} ({len(v)}):"); print("\n".join("  " + e for e in v))
        else:
            print(f"{k}: {json.dumps(v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
