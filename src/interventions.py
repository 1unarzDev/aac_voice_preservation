"""Two practical interventions, evaluated with the standard judge/attribute pipeline.

I1  commitment guard (runtime monitor, generate -> check -> repair)
    After a P0 generation, a deterministic checker (layer0 + a small time/number add-on)
    compares the output with every commitment the user SUPPLIED at runtime:
      - chip channels: the chips parsed from the visible input (CHIP_TO_GENERAL sets);
      - `full`: layer0 labels of the typed source sentence (the "The user typed:" text);
      - bare/noncrit: nothing, except the politeness rule below.
    Unsupplied politeness: a polite marker (please / softener / thanks) in the output when
    no [PLEASE] was given and the typed source (if any) had none.
    On a mismatch the model is asked again (same conversation + one short feedback turn,
    "Your sentence must keep: negated; no added politeness ..."), up to --max-retries
    times. The returned output is the first attempt with no flags, else the attempt with
    the fewest flags (ties -> earliest, so an unfixable output stays unchanged).
    Arms written to the run:  P0  (first pass, copied), G1 (guard), G1s (strip-only:
    deterministic removal of an unsupplied 'please', no model call).

I2  ambiguity-complete suggestion set (bare channel)
    Start from the cached P2 set [s1, s2, s3]. For each unresolved dimension in priority
    order (polarity, certainty) check with layer0 whether the set already holds the
    alternative reading of s1 (polarity: negated <-> affirmative; certainty: hedged <->
    not hedged). If not, the highest unprotected slot (3, then 2) is replaced by an LLM
    rewrite of s1 with an explicit instruction ("make it NEGATED ..."), verified by layer0
    and retried once with feedback. s1 is never changed. Arms: P2, S3 (copied), I2.

Each arm is written in the standard run format (runs/<run>/generations.jsonl with
targets), so explode.py / judge.py / attribute.py work unchanged; intervention-specific
fields (flags, attempts, extra calls, latency, tokens) are extra keys on the generation
rows and are joined back by request_key in the report.

Calls are cached in runs/cache/<key>.json like generate.py (key = sha1 of model, tag,
messages, temperature, seed). One local server at a time (D-008): run one model per
invocation (parts/<model>.jsonl), then `assemble`.

  python src/interventions.py guard --base runs/main1 --run guard1 --models qwen2.5-7b
  python src/interventions.py span  --base runs/main1 --run span1  --models qwen2.5-7b
  python src/interventions.py assemble --run guard1          # merge parts -> generations.jsonl
  python src/explode.py --run runs/guard1 && python src/explode.py --run runs/guard1 --by-input
  python src/judge.py --run guard1 && python src/attribute.py --run guard1 --fallback J1
  python src/interventions.py report --guard guard1 --span span1 --out analysis/interventions/report.md
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layer0  # noqa: E402
import models as M  # noqa: E402
import prompts as P  # noqa: E402
import runio  # noqa: E402
from build_requests import request_key  # noqa: E402
from generate import CACHE, SEED_BASE, parse_output  # noqa: E402
from labels import CHIP_TO_GENERAL, EMPH, NA_CERTAINTY, PLAIN_A, POLITE_VALUES  # noqa: E402

ROOT = runio.ROOT
HEDGED = "hedged/uncertain"
CERTAIN = frozenset({PLAIN_A, EMPH})
NUM_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
             "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100}
FUTURE = re.compile(r"\b(will|'ll|won't|going to|gonna|later|tomorrow|tonight|soon|next)\b")
PASTW = re.compile(r"\b(yesterday|ago|earlier|last (?:night|week|month|year|time))\b")
# spaCy-sm mis-tags some irregular past forms (e.g. 'forgot' -> VBP); listed explicitly.
IRREGULAR_PAST = {"forgot", "went", "came", "saw", "took", "gave", "ate", "left", "lost", "broke",
                  "fell", "got", "had", "did", "was", "were", "said", "made", "told", "found",
                  "bought", "brought", "thought", "felt", "sent", "spent", "won", "wrote", "ran",
                  "sat", "slept", "woke", "drove", "rode", "flew", "knew", "heard", "paid", "met",
                  "kept", "began", "drank", "forgotten", "stole", "threw", "wore", "chose", "spoke"}


def sha1(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


# ------------------------------------------------------------------ deterministic checker

def numbers_in(text: str) -> set[int]:
    w = re.findall(r"[a-z]+|\d+", text.lower())
    return {int(x) for x in w if x.isdigit()} | {NUM_WORDS[x] for x in w if x in NUM_WORDS}


def time_class(text: str) -> str | None:
    """Coarse tense: past | later | now, or None when not clear (conservative)."""
    low = " " + text.lower().replace("’", "'") + " "
    doc = layer0.nlp()(text)
    fut = bool(FUTURE.search(low))
    past = bool(PASTW.search(low)) or any(t.tag_ == "VBD" or t.lower_ in IRREGULAR_PAST
                                          or "Past" in t.morph.get("Tense") and t.tag_ != "VBN"
                                          for t in doc) or (
        any(t.tag_ == "VBN" for t in doc) and any(t.lower_ in ("have", "has", "'ve", "had") for t in doc))
    if fut and not past:
        return "later"
    if past and not fut:
        return "past"
    if not fut and not past:
        return "now"
    return None


def supplied(input_text: str, src_label: dict | None = None) -> dict:
    """Commitments the user supplied at runtime: dim -> set of honouring values,
    plus 'number' (set of ints), 'time' (class) and 'polite_ok' (bool)."""
    spec: dict = {}
    if input_text.startswith("The user typed:"):
        src = input_text.split(":", 1)[1].strip()
        L = src_label or layer0.label(src)
        spec["polarity"] = frozenset({L["polarity"]}) if L["polarity"] != "mixed/unclear" else None
        spec["speech_act"] = frozenset({L["speech_act"]}) if L["speech_act"] != "other" else None
        spec["agent"] = frozenset({L["agent"]}) if L["agent"] != "unspecified" else None
        c = L["certainty"]
        spec["certainty"] = (None if c == NA_CERTAINTY else
                             frozenset({HEDGED}) if c == HEDGED else CERTAIN)
        spec["politeness"] = frozenset(POLITE_VALUES) if L["politeness"] != "none" else frozenset({"none"})
        spec["polite_ok"] = L["politeness"] != "none"
        spec["number"] = numbers_in(src) or None
        spec["time"] = time_class(src)
        return {k: v for k, v in spec.items() if v is not None or k == "polite_ok"}
    chips = re.findall(r"\[[^\]]+\]", input_text)
    for c in chips:
        if c in CHIP_TO_GENERAL:
            d, v = CHIP_TO_GENERAL[c]
            spec[d] = v
        elif re.fullmatch(r"\[\d+\]", c):
            spec.setdefault("number", set()).add(int(c[1:-1]))
        elif c in ("[PAST]", "[NOW]", "[LATER]"):
            spec["time"] = c[1:-1].lower()
    spec["polite_ok"] = "[PLEASE]" in chips
    return spec


def check(text: str, spec: dict, label: dict | None = None) -> list[str]:
    """Flag list: '<dim>:<required>' for every supplied commitment the output misses,
    plus 'politeness:added' for an unsupplied polite marker."""
    L = label or layer0.label(text)
    flags = []
    for d in ("polarity", "speech_act", "agent", "certainty", "politeness"):
        s = spec.get(d)
        if s is not None and L[d] not in s:
            if d == "politeness" and frozenset(s) == frozenset({"none"}):
                continue   # reported once below as politeness:added
            flags.append(f"{d}:{sorted(s)[0] if len(s) == 1 else ('polite' if d == 'politeness' else 'certain')}")
    if not spec.get("polite_ok") and L["politeness"] != "none":
        flags.append("politeness:added")
    if spec.get("number") and not (spec["number"] & numbers_in(text)):
        flags.append("number:" + ",".join(str(n) for n in sorted(spec["number"])))
    if spec.get("time"):
        tc = time_class(text)
        if tc is not None and tc != spec["time"]:
            flags.append("time:" + spec["time"])
    return flags


PHRASE = {
    "polarity:negated": "negated (it must say not/never/no)",
    "polarity:affirmative": "affirmative (no negation)",
    "speech_act:question": "a question",
    "speech_act:request/command": "a request to the listener",
    "speech_act:refusal": "declining (a refusal)",
    "speech_act:statement": "a plain statement",
    "speech_act:offer/suggestion": "an offer or suggestion",
    "agent:speaker": "I am the one who does it",
    "agent:addressee": "the listener (you) does it",
    "agent:we/joint": "we do it together",
    "agent:third party": "someone or something else does it",
    "certainty:hedged/uncertain": "uncertain (maybe/might)",
    "certainty:certain": "certain (no maybe/might/I think)",
    "politeness:polite": "polite (please)",
    "politeness:added": "no added politeness (no please, could you, would you or thanks)",
    "time:past": "past time (it already happened)", "time:now": "happening now",
    "time:later": "later (future)",
}


def feedback(flags: list[str]) -> str:
    parts = [PHRASE.get(f) or ("the number " + f.split(":", 1)[1] if f.startswith("number:") else f)
             for f in flags]
    return ("Your sentence must keep: " + "; ".join(parts) +
            ". Write the sentence again with the same meaning otherwise. Output only the sentence.")


def strip_please(text: str) -> str:
    t = re.sub(r"(?i)\s*,?\s*\b(please|pls|plz)\b\s*,?", " ", text)
    t = re.sub(r"\s+([.!?,])", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip().lstrip(",").strip()
    return t[:1].upper() + t[1:] if t else text


# ------------------------------------------------------------------------- model calls

class Caller:
    def __init__(self, conc_local=4, conc_api=8, retries=5):
        self.sem = {}
        self.conc_local, self.conc_api, self.retries = conc_local, conc_api, retries
        self.client = None

    def _sem(self, spec):
        if spec.name not in self.sem:
            self.sem[spec.name] = asyncio.Semaphore(self.conc_api if spec.kind == "api" else self.conc_local)
        return self.sem[spec.name]

    async def chat(self, model: str, tag: str, messages: list[dict], max_tokens=96) -> dict:
        spec = M.get(model)
        body = {"model": spec.model, "messages": messages, "temperature": 0.0, "max_tokens": max_tokens}
        if spec.supports_seed:
            body["seed"] = SEED_BASE
        key = sha1(spec.model, tag, messages, 0.0, body.get("seed"))
        cpath = CACHE / f"{key}.json"
        if cpath.exists():
            return {**json.loads(cpath.read_text()), "cached": True, "key": key}
        err = None
        async with self._sem(spec):
            for attempt in range(1, self.retries + 1):
                t0 = time.perf_counter()
                try:
                    r = await self.client.post(spec.base_url + "/chat/completions", json=body,
                                               headers=M.headers(spec), timeout=180)
                    if r.status_code == 200:
                        j = r.json()
                        res = {"raw_text": j["choices"][0]["message"].get("content") or "",
                               "finish_reason": j["choices"][0].get("finish_reason"),
                               "latency_s": round(time.perf_counter() - t0, 3), "usage": j.get("usage")}
                        tmp = cpath.with_suffix(".tmp")
                        tmp.write_text(json.dumps(res, ensure_ascii=False)); tmp.replace(cpath)
                        return {**res, "cached": False, "key": key}
                    err = f"HTTP {r.status_code}: {r.text[:200]}"
                    if r.status_code < 500 and r.status_code != 429:
                        break
                except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                    err = f"{type(e).__name__}: {e}"[:200]
                await asyncio.sleep(2 ** attempt)
        return {"error": err, "key": key}


def _ctok(res: dict) -> int:
    return ((res.get("usage") or {}).get("completion_tokens") or 0)


# ------------------------------------------------------------------------------ I1 guard

def load_base(base: Path, prompt_ids: set[str], models: set[str] | None) -> list[dict]:
    return [g for g in runio.read_jsonl(base / "generations.jsonl")
            if g["prompt_id"] in prompt_ids and (models is None or g["model"] in models)
            and not g.get("error")]


def render_checked(g: dict, items: dict) -> str:
    fam = items[g["family_id"]]
    prompt = P.render(g["prompt_id"], g["input_text"], fam.get("context"))
    spec = M.get(g["model"])
    k = request_key(spec.model, g["prompt_id"], prompt, g["temperature"], g["sample_idx"], g.get("namespace"))
    if k != g["request_key"]:
        raise SystemExit(f"re-rendered prompt does not reproduce request_key {g['request_key']}")
    return prompt


async def guard_one(caller: Caller, g: dict, items: dict, max_retries: int, src_cache: dict) -> list[dict]:
    prompt = render_checked(g, items)
    text0 = g["suggestions"][0] if g["suggestions"] else ""
    t0 = time.perf_counter()
    src_lab = None
    if g["input_text"].startswith("The user typed:"):
        s = g["input_text"].split(":", 1)[1].strip()
        src_lab = src_cache.setdefault(s, layer0.label(s))
    spec = supplied(g["input_text"], src_lab)
    flags0 = check(text0, spec) if text0 else ["empty"]
    check_ms = (time.perf_counter() - t0) * 1000
    attempts = [{"text": text0, "flags": flags0, "raw": g.get("raw_text") or text0}]
    calls, lat, ctok, errors = 0, 0.0, 0, []
    msgs = [{"role": "user", "content": prompt}]
    flags = flags0
    while flags and len(attempts) <= max_retries and text0:
        msgs = msgs + [{"role": "assistant", "content": attempts[-1]["raw"]},
                       {"role": "user", "content": feedback(flags)}]
        res = await caller.chat(g["model"], "I1-guard-v1", msgs)
        calls += 1
        if "error" in res:
            errors.append(res["error"]); break
        lat += res.get("latency_s") or 0.0
        ctok += _ctok(res)
        sug, _, _ = parse_output(res["raw_text"], 1)
        t = sug[0] if sug else ""
        flags = check(t, spec) if t else ["empty"]
        attempts.append({"text": t, "flags": flags, "raw": res["raw_text"] or t})
    best = min(range(len(attempts)), key=lambda i: (len(attempts[i]["flags"]), i))
    final = attempts[best]
    base = {k: v for k, v in g.items() if k not in ("suggestions", "raw_text", "cached")}
    common = {"base_request_key": g["request_key"], "guard_spec": {k: sorted(v) if isinstance(v, (set, frozenset)) else v
                                                                     for k, v in spec.items()},
              "flags_initial": flags0, "check_ms": round(check_ms, 2)}
    g1 = {**base, **common, "prompt_id": "G1", "request_key": sha1(g["request_key"], "G1")[:40],
          "raw_text": final["raw"], "suggestions": [final["text"]] if final["text"] else [],
          "parse_ok": bool(final["text"]), "flags_final": final["flags"], "chosen_attempt": best,
          "attempts": [{"text": a["text"], "flags": a["flags"]} for a in attempts],
          "extra_calls": calls, "extra_latency_s": round(lat, 3), "extra_completion_tokens": ctok,
          "changed": final["text"] != text0, "guard_errors": errors}
    # strip-only arm: deterministic removal of an unsupplied 'please' (no model call)
    st = text0
    if "politeness:added" in flags0 and re.search(r"(?i)\b(please|pls|plz)\b", text0):
        st = strip_please(text0)
    g1s = {**base, **common, "prompt_id": "G1s", "request_key": sha1(g["request_key"], "G1s")[:40],
           "raw_text": st, "suggestions": [st] if st else [], "parse_ok": bool(st),
           "flags_final": check(st, spec) if st else ["empty"], "extra_calls": 0, "extra_latency_s": 0.0,
           "extra_completion_tokens": 0, "changed": st != text0}
    p0 = {**g, **common, "flags_final": flags0}
    return [p0, g1, g1s]


# ------------------------------------------------------------------------------ I2 span

def flip_target(dim: str, L: dict) -> str:
    if dim == "polarity":
        return "affirmative" if L["polarity"] == "negated" else "negated"
    return "certain" if L["certainty"] == HEDGED else "hedged"


def has_value(dim: str, value: str, L: dict) -> bool:
    if dim == "polarity":
        return L["polarity"] == value
    if value == "hedged":
        return L["certainty"] == HEDGED
    return L["certainty"] in CERTAIN


INSTR = {
    ("polarity", "negated"): "make it NEGATED: it must say the opposite with not/never/no (e.g. 'I want X' -> 'I don't want X')",
    ("polarity", "affirmative"): "make it AFFIRMATIVE: remove the negation so it says the positive version",
    ("certainty", "hedged"): "make it UNCERTAIN: a statement that is not sure (use maybe, might or I think)",
    ("certainty", "certain"): "make it CERTAIN: a plain statement of fact with no maybe, might or I think",
}


def rewrite_prompt(fam: dict, input_text: str, top: str, dim: str, target: str, which: str = "The top") -> str:
    ctx = f"Situation: {fam['context'].strip()}\n" if fam.get("context") else ""
    return ("You are the sentence-composition feature of an AAC (augmentative and alternative\n"
            "communication) app. The user entered keywords, and the input does not say which\n"
            f"reading they mean. {which} suggestion is:\n\"{top}\"\n\n"
            f"Write one alternative suggestion for the same keywords: {INSTR[(dim, target)]}.\n"
            "Keep everything else the same: the same content words, who does it, and the kind of\n"
            "sentence. Do not add please, thanks or other politeness, and do not add new facts.\n"
            "Output only the sentence.\n\n" + ctx + input_text)


async def span_one(caller: Caller, g: dict, items: dict, dims: list[str], mode: str = "inplace") -> dict:
    """mode 'top' (arm I2t): the replaced slot becomes a rewrite of s1 (minimal pair with the
    top suggestion). mode 'inplace' (arm I2): the replaced slot's OWN sentence is rewritten
    to the missing reading, so the slot keeps its agent / speech act; for certainty a
    statement slot is preferred. Slot order of preference: 3, then 2."""
    fam = items[g["family_id"]]
    sug = list(g["suggestions"][:3])
    labs = layer0.label_many(sug) if sug else []
    protected = {0} if sug else set()
    calls, lat, ctok, plan, errors = 0, 0.0, 0, [], []
    for dim in dims:
        if not sug:
            break
        target = flip_target(dim, labs[0])
        have = [i for i in range(len(sug)) if has_value(dim, target, labs[i])]
        if have:
            protected.add(have[0]); plan.append({"dim": dim, "target": target, "slot": have[0], "rewritten": False})
            continue
        free = [i for i in range(2, 0, -1) if i not in protected]
        if not free:
            plan.append({"dim": dim, "target": target, "slot": None, "rewritten": False}); continue
        if mode == "inplace" and dim == "certainty":
            free.sort(key=lambda i: labs[i]["speech_act"] != "statement")   # stable: keeps 3 before 2
        slot = free[0]
        src_text = sug[0] if mode == "top" else sug[slot]
        msgs = [{"role": "user", "content": rewrite_prompt(fam, g["input_text"], src_text, dim, target,
                                                           "The top" if mode == "top" else "One")}]
        text, ok = None, False
        for attempt in range(2):
            res = await caller.chat(g["model"], "I2-span-v1", msgs)
            calls += 1
            if "error" in res:
                errors.append(res["error"]); break
            lat += res.get("latency_s") or 0.0
            ctok += _ctok(res)
            p, _, _ = parse_output(res["raw_text"], 1)
            cand = p[0] if p else ""
            if cand:
                text = cand
                ok = has_value(dim, target, layer0.label(cand))
            if ok:
                break
            msgs = msgs + [{"role": "assistant", "content": res["raw_text"] or ""},
                           {"role": "user", "content": f"That is not {target}. {INSTR[(dim, target)][0].upper()}"
                                                        f"{INSTR[(dim, target)][1:]}. Output only the sentence."}]
        if text:
            while len(sug) <= slot:
                sug.append(text); labs.append(layer0.label(text))
            sug[slot], labs[slot] = text, layer0.label(text)
            protected.add(slot)
        plan.append({"dim": dim, "target": target, "slot": slot, "rewritten": bool(text), "verified": ok})
    base = {k: v for k, v in g.items() if k not in ("suggestions", "raw_text", "cached")}
    pid = "I2" if mode == "inplace" else "I2t"
    return {**base, "prompt_id": pid, "request_key": sha1(g["request_key"], pid)[:40],
            "base_request_key": g["request_key"], "raw_text": json.dumps(sug, ensure_ascii=False),
            "suggestions": sug, "parse_ok": len(sug) == 3, "base_suggestions": g["suggestions"],
            "span_plan": plan, "extra_calls": calls, "extra_latency_s": round(lat, 3),
            "extra_completion_tokens": ctok, "changed": sug != list(g["suggestions"][:3]),
            "span_errors": errors}


# ---------------------------------------------------------------------------- drivers

async def drive(kind: str, a) -> None:
    base = Path(a.base) if Path(a.base).exists() else ROOT / "runs" / a.base
    run = ROOT / "runs" / a.run
    (run / "parts").mkdir(parents=True, exist_ok=True)
    items = runio.load_items()
    mods = set(a.models.split(",")) if a.models else None
    caller = Caller(conc_local=a.local_concurrency, conc_api=a.api_concurrency)
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=32)) as client:
        caller.client = client
        if kind == "guard":
            chans = set(a.channels.split(","))
            gens = [g for g in load_base(base, {"P0"}, mods)
                    if any(t["channel"] in chans for t in g["targets"])]
            src_cache: dict = {}
            outs = await asyncio.gather(*(guard_one(caller, g, items, a.max_retries, src_cache) for g in gens))
            rows = [r for o in outs for r in o]
        else:
            gens = [g for g in load_base(base, {"P2"}, mods)
                    if any(t["channel"] == "bare" for t in g["targets"])]
            new = await asyncio.gather(*(span_one(caller, g, items, a.dims.split(","), mode)
                                         for mode in ("inplace", "top") for g in gens))
            bare_keys = {g["input_text"] for g in gens}
            s3 = [g for g in load_base(base, {"S3"}, mods) if g["input_text"] in bare_keys
                  and any(t["channel"] == "bare" for t in g["targets"])]
            rows = gens + s3 + list(new)
    for m in sorted({r["model"] for r in rows}):
        part = [r for r in rows if r["model"] == m]
        runio.write_jsonl(run / "parts" / f"{kind}_{m}.jsonl", part)
        errs = sum(bool(r.get("guard_errors") or r.get("span_errors")) for r in part)
        print(f"{kind} {m}: {len(part)} rows, {errs} with call errors -> parts/{kind}_{m}.jsonl")
        if errs:
            print("  re-run with the server up to retry the failed calls", file=sys.stderr)


def assemble(a) -> None:
    run = ROOT / "runs" / a.run
    rows = []
    for p in sorted((run / "parts").glob("*.jsonl")):
        rows += runio.read_jsonl(p)
    # targets restricted to the channels the arm covers (guard: chosen channels; span: bare)
    runio.write_jsonl(run / "generations.jsonl", rows)
    cfg = {"run_id": a.run, "kind": "intervention", "parts": sorted(p.name for p in (run / "parts").glob("*.jsonl")),
           "n_rows": len(rows), "by_prompt": dict(Counter(r["prompt_id"] for r in rows)),
           "code_sha256": hashlib.sha256((Path(__file__)).read_bytes()).hexdigest(),
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (run / "config.json").write_text(json.dumps(cfg, indent=2))
    print(f"assembled {len(rows)} rows -> {run/'generations.jsonl'} {cfg['by_prompt']}")


# ----------------------------------------------------------------------------- report

CUE = ["chip1", "chipall", "full"]


def _fb(df, col, n_boot):
    from analyze import family_bootstrap
    d = df[["family_id", col]].dropna()
    if not len(d):
        return {"estimate": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
    return family_bootstrap(d.astype({col: float}), col, n_boot=n_boot)


def _fmt(r, pct=True):
    if not r["n"]:
        return "n/a"
    k = 100 if pct else 1
    return f"{k*r['estimate']:.1f} [{k*r['ci_low']:.1f}, {k*r['ci_high']:.1f}]"


def _kappa(a, b):
    from agree_stats import cohen_kappa
    return cohen_kappa([str(x) for x in a], [str(x) for x in b])


def guard_frame(run: Path):
    import pandas as pd
    sc = pd.read_parquet(run / "scored.parquet")
    gens = {g["request_key"]: g for g in runio.read_jsonl(run / "generations.jsonl")}
    sc["base_key"] = [gens[k].get("base_request_key", k) if k in gens else k for k in sc.request_key]
    for f in ("flags_initial", "flags_final", "extra_calls", "extra_latency_s", "extra_completion_tokens",
              "changed", "chosen_attempt", "check_ms", "attempts"):
        sc[f] = [gens.get(k, {}).get(f) for k in sc.request_key]
    sc["strict_fail"] = [None if (cp is None or pd.isna(cp)) else bool((not cp) or (pa is True))
                         for cp, pa in zip(sc.constraint_preserving, sc.politeness_added)]
    sc["pol_add"] = sc.politeness_added.astype("float")
    keys = ["base_key", "family_id", "variant", "channel"]
    wide = sc[sc.prompt_id == "P0"].set_index(keys)
    out = {}
    for arm in ("G1", "G1s"):
        x = sc[sc.prompt_id == arm].set_index(keys)
        j = wide.join(x, lsuffix="", rsuffix="_" + arm, how="inner")
        out[arm] = j.reset_index()
    return sc, out


def guard_section(run: Path, n_boot: int, name: str) -> tuple[list[str], dict]:
    import pandas as pd
    sc, pairs = guard_frame(run)
    L, res = [], {}
    cue = sc[sc.channel.isin(CUE) & sc.valid]
    L.append(f"### Guard ({name}): judged outcomes on cue channels (chip1/chipall/full), P0 first pass vs guard\n")
    L.append("Rates in %, family-cluster bootstrap 95% CI (2000 resamples). One row per (model, family, "
             "variant, channel) target. strict pass = constraint-preserving (critical match, no contradiction "
             "of a supplied dimension) AND no politeness addition.\n")
    L.append("| arm | critical match | any contradiction | politeness added | constraint-preserving | strict pass | n |")
    L.append("|---|---|---|---|---|---|---|")
    for arm in ("P0", "G1", "G1s"):
        g = cue[cue.prompt_id == arm].copy()
        g["cm"] = g.critical_match.astype(float)
        g["ct"] = g.any_contra.astype(float)
        g["cp"] = g.constraint_preserving.astype(float)
        g["sp"] = 1 - g.strict_fail.astype(float)
        r = {c: _fb(g, c, n_boot) for c in ("cm", "ct", "pol_add", "cp", "sp")}
        res[arm] = r
        L.append(f"| {arm} | {_fmt(r['cm'])} | {_fmt(r['ct'])} | {_fmt(r['pol_add'])} | {_fmt(r['cp'])} | "
                 f"{_fmt(r['sp'])} | {r['cm']['n']} |")
    # bare/noncrit politeness additions (the only check that applies there)
    amb = sc[sc.channel.isin(["bare", "noncrit"]) & sc.valid]
    if len(amb):
        L.append("\nAmbiguous channels (bare/noncrit; only the unsupplied-politeness rule applies): politeness added %\n")
        L.append("| arm | politeness added | n |\n|---|---|---|")
        for arm in ("P0", "G1", "G1s"):
            r = _fb(amb[amb.prompt_id == arm], "pol_add", n_boot)
            L.append(f"| {arm} | {_fmt(r)} | {r['n']} |")
    # fix / over-correction
    L.append(f"\n### Guard ({name}): fixes, over-correction, cost\n")
    L.append("Judged violation = P0 output with strict_fail (critical violation, contradiction of a supplied "
             "dimension, or politeness added). fixed = the arm's output is a strict pass. already-correct = "
             "P0 strict pass; over-correction = text changed (and, stricter, became a judged failure).\n")
    L.append("| arm | channels | judged violations (P0) | flagged by layer0 | fixed | fix rate | already-correct | changed | over-correction rate | broken (pass->fail) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for arm, j in pairs.items():
        for chs, lab in ((CUE, "cue"), (["bare", "noncrit"], "ambiguous")):
            x = j[j.channel.isin(chs) & j.valid & j["valid_" + arm]].copy()
            x = x[x.strict_fail.notna() & x["strict_fail_" + arm].notna()]
            if not len(x):
                continue
            x["flag0"] = [bool(f) for f in x.flags_initial]
            bad = x[x.strict_fail.astype(bool)].copy()
            bad["fixed"] = (~bad["strict_fail_" + arm].astype(bool)).astype(float)
            ok = x[~x.strict_fail.astype(bool)].copy()
            ok["chg"] = ok["changed_" + arm].astype(float)
            ok["brk"] = ok["strict_fail_" + arm].astype(float)
            rf, rc, rb = _fb(bad, "fixed", n_boot), _fb(ok, "chg", n_boot), _fb(ok, "brk", n_boot)
            res[f"{arm}_{lab}"] = {"fix": rf, "overcorr": rc, "broken": rb, "n_bad": len(bad), "n_ok": len(ok)}
            L.append(f"| {arm} | {lab} | {len(bad)} | {int(bad.flag0.sum())} | {int(bad.fixed.sum())} | {_fmt(rf)} | "
                     f"{len(ok)} | {int(ok.chg.sum())} | {_fmt(rc)} | {int(ok.brk.sum())} |")
    # cost: per guarded generation (unique request, not per target)
    gens = [g for g in runio.read_jsonl(run / "generations.jsonl") if g["prompt_id"] == "G1"]
    if gens:
        import numpy as np
        L.append(f"\n### Guard ({name}): cost per input (unique generations)\n")
        L.append("| model | inputs | flagged | regenerated->changed | extra calls / input | extra calls / flagged | "
                 "extra latency s / input (mean) | extra latency s / flagged (median) | extra completion tokens / input | layer0 check ms (median) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for m in sorted({g["model"] for g in gens}) + ["all"]:
            gg = [g for g in gens if m == "all" or g["model"] == m]
            fl = [g for g in gg if g["flags_initial"]]
            L.append(f"| {m} | {len(gg)} | {len(fl)} ({100*len(fl)/len(gg):.1f}%) | {sum(g['changed'] for g in gg)} | "
                     f"{np.mean([g['extra_calls'] for g in gg]):.3f} | "
                     f"{np.mean([g['extra_calls'] for g in fl]) if fl else 0:.2f} | "
                     f"{np.mean([g['extra_latency_s'] for g in gg]):.3f} | "
                     f"{np.median([g['extra_latency_s'] for g in fl]) if fl else 0:.2f} | "
                     f"{np.mean([g['extra_completion_tokens'] for g in gg]):.2f} | "
                     f"{np.median([g['check_ms'] for g in gg]):.1f} |")
        fc = Counter(f.split(":")[0] for g in gens for f in g["flags_initial"])
        L.append(f"\nInitial flag types (unique generations): {dict(fc)}. Still flagged after the guard: "
                 f"{sum(bool(g['flags_final']) for g in gens)} of {sum(bool(g['flags_initial']) for g in gens)} flagged.\n")
        L.append("Latency is measured per call against a single local llama.cpp server at 4 slots (API for terra); "
                 "cached first-pass latency is not counted. The strip-only arm (G1s) adds 0 calls and only the "
                 "layer0 check time.\n")
    # agreement layer0 vs judge
    j = pairs.get("G1")
    if j is not None:
        x = j[j.channel.isin(CUE) & j.valid & j.valid_G1 & j.strict_fail.notna()].copy()
        x["flag0"] = [bool(f) for f in x.flags_initial]
        x["jfail0"] = x.strict_fail.astype(bool)
        tp = int((x.flag0 & x.jfail0).sum()); fp = int((x.flag0 & ~x.jfail0).sum())
        fn = int((~x.flag0 & x.jfail0).sum()); tn = int((~x.flag0 & ~x.jfail0).sum())
        L.append(f"\n### Guard ({name}): layer0 monitor vs LLM judge (cue channels)\n")
        L.append(f"First pass, flag (layer0) vs judged failure: TP {tp}, FP {fp}, FN {fn}, TN {tn}; "
                 f"precision {tp/max(tp+fp,1):.2f}, recall {tp/max(tp+fn,1):.2f}, "
                 f"kappa {_kappa(x.flag0, x.jfail0)}.")
        rep = x[x.changed_G1.astype(bool) & x.strict_fail_G1.notna()].copy()
        if len(rep):
            rep["l0_ok"] = [not f for f in rep.flags_final_G1]
            rep["j_ok"] = ~rep.strict_fail_G1.astype(bool)
            a = int((rep.l0_ok == rep.j_ok).sum())
            L.append(f"Repaired (changed) items, n={len(rep)}: layer0 says fixed {int(rep.l0_ok.sum())}, judge says "
                     f"pass {int(rep.j_ok.sum())}; agreement {a}/{len(rep)} = {a/len(rep):.2f}, "
                     f"kappa {_kappa(rep.l0_ok, rep.j_ok)}. Cross-tab (layer0 ok, judge ok): "
                     f"{dict(Counter(zip(rep.l0_ok, rep.j_ok)))}.")
            res["agree_repaired"] = {"n": len(rep), "agree": a / len(rep)}
        # per-dimension agreement on repaired items where the flag named a dimension
        rows = []
        for _, r in rep.iterrows() if len(rep) else []:
            for f in r.flags_initial:
                d = f.split(":")[0]
                if d in ("polarity", "speech_act", "agent", "certainty"):
                    rows.append((d, f.split(":", 1)[1], r[d + "_G1"]))
        if rows:
            L.append("Judge label of the repaired output on the flagged dimension (layer0 target -> judge value): " +
                     ", ".join(f"{k}: {v}" for k, v in Counter((d, t == jv or (t == 'certain' and jv in CERTAIN))
                                                               for d, t, jv in rows).items()) + " (True = judge agrees target reached).")
        res["l0_vs_judge"] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    return L, res


def span_sets(run: Path):
    import pandas as pd
    sc = pd.read_parquet(run / "scored.parquet")
    sc = sc[(sc.channel == "bare") & (sc.variant == "A")]
    sc = sc[sc.prompt_id.isin(["P2", "S3", "I2", "I2t"])]
    rows = []
    for (m, p, f), g in sc.groupby(["model", "prompt_id", "family_id"]):
        g = g.sort_values(["sample_idx", "suggestion_idx"]).head(3)
        ch = set(g.chose.dropna())
        unknown = bool((g.valid & g.critical.isna()).any())
        cov = 1.0 if {"A", "B"} <= ch else (float("nan") if unknown else 0.0)
        rows.append({"model": m, "prompt_id": p, "family_id": f, "dimension": g.dimension.iloc[0],
                     "coverage": cov, "n_sugg": len(g), "texts": g.text.tolist(), "chose": g.chose.tolist()})
    return sc, pd.DataFrame(rows)


ARMS2 = ("S3", "P2", "I2t", "I2")


def span_section(run: Path, n_boot: int, name: str) -> tuple[list[str], dict]:
    import numpy as np
    import pandas as pd
    sc, sets = span_sets(run)
    L, res = [], {}
    L.append(f"### Ambiguity-complete set ({name}): coverage@3 under bare input\n")
    L.append("coverage@3 = both variants' critical values appear among the 3 suggestions (judge labels, J1 "
             "fallback). One set per (model, family); bare is shared by A and B. % with family-cluster 95% CI.\n")
    groups = [("polarity+certainty", ["polarity", "certainty"])] + [(d, [d]) for d in
              ["polarity", "certainty", "agent", "speech_act", "politeness", "time_quantity"]] + \
             [("all", None)]
    L.append("| dimension | S3 | P2 | I2t (rewrite top) | I2 (rewrite in place) | I2t - P2 | I2 - P2 | n sets/arm |")
    L.append("|---|---|---|---|---|---|---|---|")
    for lab, dims in groups:
        s = sets if dims is None else sets[sets.dimension.isin(dims)]
        cells = {p: _fb(s[s.prompt_id == p], "coverage", n_boot) for p in ARMS2}
        w = s.pivot_table(index=["model", "family_id"], columns="prompt_id", values="coverage").reset_index()
        dd = {}
        for arm in ("I2t", "I2"):
            if {arm, "P2"} <= set(w.columns):
                w["d"] = w[arm] - w["P2"]
                dd[arm] = _fb(w, "d", n_boot)
            else:
                dd[arm] = {"n": 0}
        res[lab] = {**cells, "diff_I2t": dd["I2t"], "diff_I2": dd["I2"]}
        L.append(f"| {lab} | " + " | ".join(_fmt(cells[p]) for p in ARMS2) +
                 f" | {_fmt(dd['I2t'])} | {_fmt(dd['I2'])} | {cells['P2']['n']} |")
    L.append("\nPer model, polarity+certainty families:\n")
    L.append("| model | S3 | P2 | I2t | I2 |\n|---|---|---|---|---|")
    pc = sets[sets.dimension.isin(["polarity", "certainty"])]
    for m in sorted(pc.model.unique()):
        s = pc[pc.model == m]
        L.append(f"| {m} | " + " | ".join(_fmt(_fb(s[s.prompt_id == p], "coverage", n_boot)) for p in ARMS2) + " |")
    # per-suggestion additions (all targets, valid)
    full = __import__("pandas").read_parquet(run / "scored.parquet")
    full = full[(full.channel == "bare") & full.valid & full.prompt_id.isin(list(ARMS2))]
    full = full.assign(ac=(full.added_content == "yes").astype(float),
                       pa=full.politeness_added.astype(float), ha=full.hedge_added.astype(float),
                       ea=full.emphatic_added.astype(float), sa=full.any_stance_addition.astype(float))
    gens = {g["request_key"]: g for g in runio.read_jsonl(run / "generations.jsonl")}
    full["slot_kind"] = ["base" for _ in range(len(full))]
    for i, (k, si) in enumerate(zip(full.request_key, full.suggestion_idx)):
        g = gens.get(k, {})
        if g.get("prompt_id") in ("I2", "I2t"):
            rw = {p["slot"] for p in g.get("span_plan", []) if p.get("rewritten")}
            full.iat[i, full.columns.get_loc("slot_kind")] = "rewrite" if si in rw else "kept"
    L.append("\nPer-suggestion additions under bare (% of suggestions; targets A and B both counted, since "
             "the reference spec differs by variant). hedge added is BY DESIGN for certainty rewrites.\n")
    L.append("| arm | politeness added | hedge added | emphatic added | any stance addition | added content | n |")
    L.append("|---|---|---|---|---|---|---|")
    for lab, g in [("S3", full[full.prompt_id == "S3"]), ("P2", full[full.prompt_id == "P2"]),
                   *[(f"{arm} {lab}", full[(full.prompt_id == arm) & sel(full)]) for arm in ("I2t", "I2")
                     for lab, sel in (("all slots", lambda f: f.slot_kind != ""),
                                      ("kept slots", lambda f: f.slot_kind == "kept"),
                                      ("rewritten slots", lambda f: f.slot_kind == "rewrite"))]]:
        r = {c: _fb(g, c, n_boot) for c in ("pa", "ha", "ea", "sa", "ac")}
        L.append(f"| {lab} | " + " | ".join(_fmt(r[c]) for c in ("pa", "ha", "ea", "sa", "ac")) + f" | {r['pa']['n']} |")
    # cost
    for arm in ("I2t", "I2"):
        i2 = [g for g in gens.values() if g["prompt_id"] == arm]
        if i2:
            L.append(f"\n### Ambiguity-complete set ({name}): cost per bare input, arm {arm}\n")
            L.append("| model | sets | sets changed | rewrites | extra calls / set | layer0-verified rewrites | "
                     "extra latency s / set (mean) | extra completion tokens / set |")
            L.append("|---|---|---|---|---|---|---|---|")
            for m in sorted({g["model"] for g in i2}) + ["all"]:
                gg = [g for g in i2 if m == "all" or g["model"] == m]
                rw = [p for g in gg for p in g["span_plan"] if p.get("rewritten")]
                L.append(f"| {m} | {len(gg)} | {sum(g['changed'] for g in gg)} | {len(rw)} | "
                         f"{np.mean([g['extra_calls'] for g in gg]):.2f} | {sum(bool(p.get('verified')) for p in rw)}/{len(rw)} | "
                         f"{np.mean([g['extra_latency_s'] for g in gg]):.2f} | "
                         f"{np.mean([g['extra_completion_tokens'] for g in gg]):.1f} |")
            # judge check of the rewrites on their target dimension (general labels)
            ok = Counter()
            for _, r in full[(full.prompt_id == arm) & (full.slot_kind == "rewrite") & (full.variant == "A")].iterrows():
                g = gens[r.request_key]
                for p in g["span_plan"]:
                    if p.get("rewritten") and p["slot"] == r.suggestion_idx:
                        jv = r["polarity"] if p["dim"] == "polarity" else r["certainty"]
                        hit = (jv == p["target"]) if p["dim"] == "polarity" else (
                            jv == HEDGED if p["target"] == "hedged" else jv in CERTAIN)
                        ok[(p["dim"], p["target"], bool(hit), bool(p.get("verified")))] += 1
            L.append(f"\n{arm} rewrites: (dimension, target, judge general label reaches target, layer0 verified) -> count: " +
                     ", ".join(f"{k}: {v}" for k, v in sorted(ok.items())) + "\n")
            res[f"rewrite_check_{arm}"] = {str(k): v for k, v in ok.items()}
    res["_sets"] = sets
    return L, res


def examples(guard_run: Path, span_run: Path) -> list[str]:
    """6 before/after triples, deterministic: within each category, the rows with the
    smallest sha1(base_request_key, family, variant, channel)."""
    import pandas as pd
    L = ["### Examples (deterministic rule)\n",
         "Rule: guard categories (a) fixed: P0 judged failure -> G1 strict pass (2 rows); (b) unfixed: "
         "P0 judged failure, G1 still failing or unchanged (1); (c) over-correction: P0 strict pass, G1 changed (1); "
         "I2 (d) polarity/certainty sets where I2 covers both readings and P2 does not (2). Within a category "
         "rows are ordered by sha1 of (base_request_key, family, variant, channel) and the first ones taken.\n"]
    _, pairs = guard_frame(guard_run)
    j = pairs["G1"]
    j = j[j.channel.isin(CUE) & j.strict_fail.notna() & j.strict_fail_G1.notna()].copy()
    j["h"] = [sha1(*t) for t in zip(j.base_key, j.family_id, j.variant, j.channel)]
    j = j.sort_values("h")
    cats = [("fixed", j[j.strict_fail.astype(bool) & ~j.strict_fail_G1.astype(bool)], 2),
            ("unfixed", j[j.strict_fail.astype(bool) & j.strict_fail_G1.astype(bool)], 1),
            ("over-correction", j[~j.strict_fail.astype(bool) & j.changed_G1.astype(bool)], 1)]
    n = 0
    for lab, g, k in cats:
        for _, r in g.head(k).iterrows():
            n += 1
            L.append(f"{n}. **I1 {lab}** ({r.model}, {r.family_id}/{r.variant}, {r.channel}; truth: {r.variant_value})  \n"
                     f"   input: `{r.input_text}`  \n   before (P0): \"{r.text}\" flags={list(r.flags_initial)}  \n"
                     f"   after (G1): \"{r.text_G1}\" flags={list(r.flags_final_G1)}; judge critical {r.critical} -> {r.critical_G1}, "
                     f"politeness {r.politeness} -> {r.politeness_G1}\n")
    _, sets = span_sets(span_run)
    w = sets.pivot_table(index=["model", "family_id", "dimension"], columns="prompt_id", values="coverage").reset_index()
    w = w[w.dimension.isin(["polarity", "certainty"]) & (w.get("I2") == 1) & (w.get("P2") == 0)].copy()
    w["h"] = [sha1(m, f) for m, f in zip(w.model, w.family_id)]
    for _, r in w.sort_values("h").head(2).iterrows():
        n += 1
        p2 = sets[(sets.model == r.model) & (sets.family_id == r.family_id) & (sets.prompt_id == "P2")].iloc[0]
        i2 = sets[(sets.model == r.model) & (sets.family_id == r.family_id) & (sets.prompt_id == "I2")].iloc[0]
        it = runio.load_items()[r.family_id]
        L.append(f"{n}. **I2 coverage gain** ({r.model}, {r.family_id}; readings A={it['variants']['A']['critical_value']}, "
                 f"B={it['variants']['B']['critical_value']})  \n   input: `Keywords: {it['bare']}`  \n"
                 f"   before (P2): {json.dumps(p2.texts, ensure_ascii=False)} -> judge {p2.chose}  \n"
                 f"   after (I2): {json.dumps(i2.texts, ensure_ascii=False)} -> judge {i2.chose}\n")
    return L


def write_report(a) -> None:
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    groot = lambda r: Path(r) if Path(r).exists() else ROOT / "runs" / r  # noqa: E731
    L = [f"# {a.title}\n", f"Generated by `src/interventions.py report --guard {a.guard} --span {a.span}`.\n"]
    gl, gres = guard_section(groot(a.guard), a.n_boot, a.guard)
    sl, sres = span_section(groot(a.span), a.n_boot, a.span)
    L += gl + [""] + sl + [""] + examples(groot(a.guard), groot(a.span))
    out.write_text("\n".join(L) + "\n")
    summ = {"guard": {k: v for k, v in gres.items()}, "span": {k: v for k, v in sres.items() if k != "_sets"}}
    out.with_suffix(".json").write_text(json.dumps(summ, indent=1, default=str))
    print(f"wrote {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for k in ("guard", "span"):
        s = sub.add_parser(k)
        s.add_argument("--base", required=True, help="run with the cached first pass (P0 / P2+S3)")
        s.add_argument("--run", required=True)
        s.add_argument("--models")
        s.add_argument("--local-concurrency", type=int, default=4)
        s.add_argument("--api-concurrency", type=int, default=8)
        if k == "guard":
            s.add_argument("--channels", default="bare,noncrit,chip1,chipall,full")
            s.add_argument("--max-retries", type=int, default=2)
        else:
            s.add_argument("--dims", default="polarity,certainty")
    s = sub.add_parser("assemble"); s.add_argument("--run", required=True)
    s = sub.add_parser("report")
    s.add_argument("--guard", required=True); s.add_argument("--span", required=True)
    s.add_argument("--out", required=True); s.add_argument("--title", default="Interventions")
    s.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()
    if a.cmd in ("guard", "span"):
        asyncio.run(drive(a.cmd, a))
    elif a.cmd == "assemble":
        assemble(a)
    else:
        write_report(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
