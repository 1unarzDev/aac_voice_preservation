"""Guard v2 (G2) = G1 + post-repair acceptance check A.  Plan: analysis/guard_v2/PLAN.md (frozen 2026-11-18).

G1 code (interventions.supplied/check/feedback/Caller/render_checked) is imported unchanged and not modified.

  python src/guard_v2.py run --models gemma3-4b [--local-concurrency 4] [--api-concurrency 4]   # runs/guard_v2/parts/
  python src/guard_v2.py assemble          # runs/guard_v2/generations.jsonl
  python src/guard_v2.py preuse            # section-2 pre-use check on synthetic fixtures (CPU only)
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
import time
import zlib
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import interventions as I  # noqa: E402
import layer0  # noqa: E402
import runio  # noqa: E402
from generate import parse_output  # noqa: E402
from labels import CHIP_TO_GENERAL  # noqa: E402

ROOT = runio.ROOT
OUT = ROOT / "analysis/guard_v2"
RUN = ROOT / "runs/guard_v2"
DIMS = ("polarity", "speech_act", "agent", "certainty", "politeness")
TAG1, TAG2 = "I1-guard-v1", "I1-guard-v2"   # TAG1 when the retry message equals G1's (cache reuse)
MAX_RETRIES = 2

DANGLING = {"and", "or", "but", "the", "a", "an", "to", "of", "for", "with", "that", "if", "because",
            "my", "your", "is", "are"}
ABBR = re.compile(r"\b(Mr|Mrs|Dr|e\.g)\.", re.I)
META = re.compile(r"^\W*(sure|here is|here's|rewritten|output)\b", re.I)
ECHO_START = re.compile(r"^\W*(ask|tell|request|command|order)\s+(you|them|him|her|me)\b", re.I)
FIXED_ECHO = ("ask you", "tell you", "speech act", "polarity")


def _chip_labels() -> list[str]:
    out = []
    for k in CHIP_TO_GENERAL:
        t = k.strip("[]").strip().lower()
        if len(t.split()) >= 2:
            out.append(t)
    return out


def _words(t: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", t.lower())


def _legend_text() -> str:
    p = ROOT / "prompts/chip_legend.txt"
    return p.read_text() if p.exists() else ""


def _ngrams(ws: list[str], n: int = 4) -> set[tuple]:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def _flag_dims(flags: list[str]) -> set[str]:
    return {f.split(":", 1)[0] for f in flags}


def complete_reasons(cand: str, first: str) -> list[str]:
    """(ii) complete sentence."""
    t = (cand or "").strip()
    if not t:
        return ["incomplete"]
    body = ABBR.sub(lambda m: m.group(0).replace(".", "․"), t)
    body = re.sub(r"(?<=\d)\.(?=\d)", "․", body)
    if not re.search(r"[.?!][\"')\]]*$", body):
        return ["incomplete"]
    if re.search(r"[.?!]+[\"')\]]*\s+\S", body):      # terminal punctuation mid-text: more than one sentence
        return ["incomplete"]
    if not re.match(r"^[A-Za-z0-9]", t):
        return ["incomplete"]
    toks = t.split()
    if len(toks) < 3:
        return ["incomplete"]
    if re.sub(r"[^a-z']", "", toks[-1].lower()) in DANGLING:
        return ["incomplete"]
    if t.count('"') % 2 or t.count("(") != t.count(")") or t.count("[") != t.count("]") or t.count("{") != t.count("}"):
        return ["incomplete"]
    if re.search(r"\[[^\]]*\]", t) or META.match(t):
        return ["incomplete"]
    nf = len(first.split())
    if nf and not (0.4 <= len(toks) / nf <= 2.5):
        return ["incomplete"]
    return []


def echo_reasons(cand: str, chip_text: str) -> list[str]:
    low = (cand or "").lower()
    if ECHO_START.match(cand or ""):
        return ["echo"]
    for s in _chip_labels() + list(FIXED_ECHO):
        if re.search(r"\b" + re.escape(s) + r"\b", low):
            return ["echo"]
    prompt_words = _words(_legend_text() + " " + re.sub(r"[\[\]]", " ", chip_text or ""))
    if _ngrams(_words(cand)) & _ngrams(prompt_words):
        return ["echo"]
    return []


def collateral_reasons(cand: str, first: str, flags_first: list[str]) -> list[str]:
    """(i) no collateral change on dimensions that were not flagged."""
    cl, fl = layer0.label(cand), layer0.label(first)
    fd = _flag_dims(flags_first)
    out = [f"collateral:{d}" for d in DIMS if d not in fd and cl[d] != fl[d]]
    if not (I.numbers_in(first) <= I.numbers_in(cand)):
        out.append("collateral:number")
    tf = I.time_class(first)
    if tf is not None and "time" not in fd and I.time_class(cand) != tf:
        out.append("collateral:time")
    return out


def acceptance(cand: str, first: str, spec: dict, flags_first: list[str], chip_text: str = "") -> list[str]:
    """A(cand, first, spec): [] when accepted, else reason codes (collateral:<dim> | incomplete | echo)."""
    return (collateral_reasons(cand, first, flags_first) + complete_reasons(cand, first)
            + echo_reasons(cand, chip_text))


EXTRA = {"collateral": "Do not change anything else about the meaning",
         "incomplete": "write one complete sentence",
         "echo": "do not copy the cue words"}


def reason_words(reasons: list[str]) -> str:
    kinds = []
    for r in reasons:
        k = r.split(":", 1)[0]
        if k not in kinds:
            kinds.append(k)
    s = "; ".join(EXTRA[k] for k in kinds)
    return s[:1].upper() + s[1:] + "."


def retry_message(flags: list[str], reasons: list[str]) -> str:
    if not reasons:
        return I.feedback(flags)          # identical to G1 -> shared cache
    base = I.feedback(flags) if flags else "Your sentence must keep the user's meaning exactly. Output only the sentence."
    return base + " " + reason_words(reasons)


async def guard2_one(caller: I.Caller, g: dict, items: dict, src_cache: dict) -> dict:
    prompt = I.render_checked(g, items)
    text0 = g["suggestions"][0] if g["suggestions"] else ""
    if not text0:
        return {"base_request_key": g["request_key"], "g2_eligible": False}
    src_lab = None
    if g["input_text"].startswith("The user typed:"):
        s = g["input_text"].split(":", 1)[1].strip()
        src_lab = src_cache.setdefault(s, layer0.label(s))
    spec = I.supplied(g["input_text"], src_lab)
    flags0 = I.check(text0, spec)
    chip_text = g["input_text"] if not g["input_text"].startswith("The user typed:") else ""
    attempts = [{"text": text0, "flags": flags0, "reasons": [], "raw": g.get("raw_text") or text0}]
    calls, lat, ctok, errors, n_new_tag = 0, 0.0, 0, [], 0
    msgs = [{"role": "user", "content": prompt}]
    flags, reasons = flags0, []
    accepted = 0 if not flags0 else None      # no first-pass flag: not a repair candidate
    while accepted is None and len(attempts) <= MAX_RETRIES:
        tag = TAG1 if not reasons else TAG2
        msgs = msgs + [{"role": "assistant", "content": attempts[-1]["raw"]},
                       {"role": "user", "content": retry_message(flags, reasons)}]
        res = await caller.chat(g["model"], tag, msgs)
        calls += 1
        n_new_tag += tag == TAG2
        if "error" in res:
            errors.append(res["error"]); break
        lat += res.get("latency_s") or 0.0
        ctok += I._ctok(res)
        sug, _, _ = parse_output(res["raw_text"], 1)
        t = sug[0] if sug else ""
        if not t:
            flags, reasons = ["empty"], []
            attempts.append({"text": "", "flags": flags, "reasons": ["empty"], "raw": res["raw_text"] or ""})
            continue
        flags = I.check(t, spec)
        reasons = acceptance(t, text0, spec, flags0, chip_text)
        attempts.append({"text": t, "flags": flags, "reasons": reasons, "raw": res["raw_text"] or t})
        if not flags and not reasons:
            accepted = len(attempts) - 1
    if accepted:                               # a retry was accepted
        final, rej = attempts[accepted], None
    else:                                      # fall back to the first pass, flagged
        final = attempts[0]
        rej = None if accepted == 0 else sorted({r for a in attempts[1:] for r in a["reasons"]}
                                                | {"check:" + f for a in attempts[1:] for f in a["flags"]})
    base = {k: v for k, v in g.items() if k not in ("suggestions", "raw_text", "cached")}
    return {**base, "base_request_key": g["request_key"], "prompt_id": "G2",
            "request_key": I.sha1(g["request_key"], "G2")[:40],
            "guard_spec": {k: sorted(v) if isinstance(v, (set, frozenset)) else v for k, v in spec.items()},
            "flags_initial": flags0, "raw_text": final["raw"], "suggestions": [final["text"]],
            "parse_ok": True, "flags_final": final["flags"], "chosen_attempt": accepted or 0,
            "g2_rejected": rej, "g2_accepted": bool(accepted),
            "attempts": [{"text": a["text"], "flags": a["flags"], "reasons": a["reasons"]} for a in attempts],
            "extra_calls": calls, "new_tag_calls": n_new_tag, "extra_latency_s": round(lat, 3),
            "extra_completion_tokens": ctok, "changed": final["text"] != text0, "guard_errors": errors,
            "g2_eligible": True}


def load_frame() -> list[dict]:
    return list(csv.DictReader((OUT / "frame.csv").open()))


async def drive(a) -> None:
    (RUN / "parts").mkdir(parents=True, exist_ok=True)
    items = runio.load_items(ROOT / "analysis/guard_wc/items.jsonl")
    frame = {r["base_request_key"] for r in load_frame()}
    mods = set(a.models.split(","))
    seen, gens = set(), []
    for g in runio.read_jsonl(ROOT / "analysis/guard_wc/first_passes.jsonl"):
        if g["request_key"] in frame and g["model"] in mods and not g.get("error") and g["request_key"] not in seen:
            seen.add(g["request_key"]); gens.append(g)
    caller = I.Caller(conc_local=a.local_concurrency, conc_api=a.api_concurrency, retries=3)
    src_cache: dict = {}
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=16)) as client:
        caller.client = client
        outs = await asyncio.gather(*(guard2_one(caller, g, items, src_cache) for g in gens))
    for m in sorted(mods):
        part = [o for o in outs if o.get("model") == m]
        runio.write_jsonl(RUN / "parts" / f"g2_{m}.jsonl", part)
        errs = sum(bool(o.get("guard_errors")) for o in part)
        print(f"G2 {m}: {len(part)} rows, extra_calls {sum(o['extra_calls'] for o in part)}, with errors {errs}")


def assemble() -> None:
    rows = []
    for p in sorted((RUN / "parts").glob("g2_*.jsonl")):
        rows += runio.read_jsonl(p)
    runio.write_jsonl(RUN / "generations.jsonl", rows)
    (RUN / "config.json").write_text(json.dumps({"run_id": "guard_v2", "kind": "G2", "n_rows": len(rows),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2))
    print(f"assembled {len(rows)} rows")


# ------------------------------------------------------------------ pre-use check (plan section 2)

def _clean_sentences(n=100) -> list[str]:
    seen, out = set(), []
    rows = sorted((r for r in runio.read_jsonl(ROOT / "runs/hw1/outputs.jsonl")
                   if r["prompt_id"] == "P0" and r.get("parse_ok")), key=lambda r: r["output_id"])
    for r in rows:
        t = r["text"].strip()
        k = re.sub(r"\W+", " ", t.lower())
        if k in seen or not (3 <= len(t.split()) <= 22) or not re.search(r"[.?!]$", t) or re.search(r"[.?!]\s+\S", t):
            continue
        if re.search(r"(?i)\bplease\b|\[", t):
            continue
        seen.add(k); out.append(t)
        if len(out) == n:
            break
    return out


def _l1(s):
    return s[:1].lower() + s[1:]


def fixtures(clean: list[str]) -> dict:
    """Planted faults: (first, cand, flags_first). first = clean sentence + ', thank you' (planted 'politeness:added' flaw);
    clean_same: first == cand == clean sentence; clean_pair: label-preserving contraction rewrite (first = original);
    cand = a clean repair or a repair carrying one planted fault (fault type cycles deterministically)."""
    out = {"collateral": [], "fragment": [], "echo": [], "clean_pair": [], "clean_same": []}
    ff = ["politeness:added"]
    for i, s in enumerate(clean):
        first = s.rstrip(".?!") + ", thank you" + s[-1]
        out["clean_same"].append((s, s, ff))
        # label-preserving legitimate rewrite: expand/contract an auxiliary (layer0 labels must not move)
        alt = re.sub(r"\bI am\b", "I'm", s, 1) if re.search(r"\bI am\b", s) else re.sub(r"\bdo not\b", "don't", s, 1)
        if alt != s:
            out["clean_pair"].append((s, alt, ff))
        body = s.rstrip(".?!")
        w = body.split()
        coll = [f"Do you think {_l1(body)}?", f"Maybe {_l1(body)}.", f"Yesterday {_l1(body)}.",
                f"{w[0]} {w[1]} not {' '.join(w[2:])}.", f"Tomorrow {_l1(body)}."]
        out["collateral"].append((first, coll[i % len(coll)], ff))
        frag = [f"{w[0]} {w[1]} the", w[0], f"{body} and", f"{body}. {body}.", f"Rewritten: {body}.", f"[ASK] {body}.",
                f"Sure, {_l1(body)}"]
        out["fragment"].append((first, frag[i % len(frag)], ff))
        ech = [f"Ask you to {_l1(body)}.", f"Tell you that {_l1(body)}.", f"{body} (speech act: request).",
               f"The polarity is affirmative and {_l1(body)}.", f"Command you to {_l1(body)}."]
        out["echo"].append((first, ech[i % len(ech)], ff))
    return out


def preuse() -> int:
    clean = _clean_sentences(100)
    res = {}
    for k, v in fixtures(clean).items():
        rej = [bool(acceptance(c, f, {}, fl)) for f, c, fl in v]
        res[k] = {"n": len(v), "reject_rate": round(sum(rej) / len(v), 3)}
    out = {"n_clean": len(clean), **res,
           "recall": {k: res[k]["reject_rate"] for k in ("collateral", "fragment", "echo")},
           "false_reject": {k: res[k]["reject_rate"] for k in ("clean_pair", "clean_same")}}
    out["pass"] = all(v >= 0.9 for v in out["recall"].values()) and all(v <= 0.1 for v in out["false_reject"].values())
    OUT.mkdir(parents=True, exist_ok=True)
    print(json.dumps(out, indent=1))
    (OUT / "preuse_check.json").write_text(json.dumps(out, indent=1))
    return 0 if out["pass"] else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--models", required=True)
    r.add_argument("--local-concurrency", type=int, default=4); r.add_argument("--api-concurrency", type=int, default=4)
    sp.add_parser("assemble"); sp.add_parser("preuse")
    a = ap.parse_args()
    if a.cmd == "run":
        asyncio.run(drive(a))
    elif a.cmd == "assemble":
        assemble()
    else:
        return preuse()
    return 0


if __name__ == "__main__":
    sys.exit(main())
