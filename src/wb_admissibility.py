"""W-B source-blind admissibility coding by the codex annotator panel (PREREG_R2 W-B).

Two independent codex models code every message in two SEPARATE calls:
  pass 1 (source-blind): coder sees ONLY the POS-cap4 keywords. Per dimension it lists every
          plausible reading (value + witness paraphrase) and marks the dimension ambiguous
          when >= 2 readings are admissible.
  pass 2 (source-revealed, separate call/session): coder sees ONLY the full source text and
          records the single commitment the source makes on each dimension.
Batches of ~20 messages (frozen shuffled order), opaque item ids (w001..), codex exec run in
an EMPTY temporary directory with a read-only sandbox, --ephemeral, and the instruction not
to read files or run commands. Output is forced with --output-schema and validated; invalid
or incomplete batches are retried (max 3). Raw outputs are cached per (model, pass, batch).

Derived per (message, dimension, coder c):
  amb_c       = >= 2 distinct admissible reading values (the coder's own flag is stored too)
  src_c       = coder c's pass-2 source value
  supplied_c  = not amb_c and the single admissible reading == src_c
Panel: confirmed_ambiguous = amb_1 & amb_2; supplied = supplied_1 & supplied_2;
       source_value = src_1 if src_1 == src_2 else None (disagreement).

  python src/wb_admissibility.py run   [--models gpt-5.6-sol,gpt-6-astra] [--jobs 4]
  python src/wb_admissibility.py merge     # -> annotation/wb_admissibility/panel.jsonl + agreement.json
  python src/wb_admissibility.py audit     # -> annotation/wb_audit.json (20 random messages)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agree_stats import cohen_kappa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data/specs/wb_sample.jsonl"
OUTDIR = ROOT / "annotation/wb_admissibility"
MODELS = ["gpt-5.6-sol", "gpt-6-astra"]
BATCH = 20
SEED = 20261101
DIMS = {
    "polarity": ["affirmative", "negated", "mixed/unclear"],
    "speech_act": ["statement", "question", "request/command", "refusal", "offer/suggestion", "other"],
    "agent": ["speaker", "addressee", "we/joint", "third party", "unspecified"],
    "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic",
                  "n/a (question/request)"],
    "politeness": ["none", "please", "softened request (could you/would you mind)", "thanks/apology"],
}

CODEBOOK = """Dimension definitions (use exactly these option strings):
- polarity: is the main statement/request negated (not/never/no/don't/can't)? affirmative | negated | mixed/unclear ("I'm not sure"-type uncertainty, or one clause negated and one not).
- speech_act: statement (tells) | question (asks for information or permission; "Can I ...?" is a question) | request/command (asks the listener to do something: imperatives, "can/could/would you ...?", "I'd like ...", asks with please) | refusal (explicitly declines: "no thanks", "I won't", "I don't want to") | offer/suggestion ("let's", "how about", "shall we", "do you want to ...?") | other (greetings, thanks only).
- agent: who does the main content action: speaker (I, incl. own body part) | addressee (you; imperatives and "can you" requests) | we/joint (we, let's) | third party (other people or things) | unspecified (dummy it/there, agentless).
- certainty: plain assertion | hedged/uncertain (maybe, might, probably, I think, I guess, not sure) | strongly certain/emphatic (definitely, really, for sure, of course) | n/a (question/request) for questions and requests/commands.
- politeness: none | please | softened request (could you/would you mind) (could you, would you, would you mind, may I, if possible, I'd like) | thanks/apology (thank you, thanks, sorry, excuse me). If several, the first in this order: please > softened > thanks/apology."""

GUARD = """STRICT RULES: Do NOT read, list, open or search any files. Do NOT run any shell commands or tools. Everything you need is in this message. Answer only with the JSON object required by the output schema."""

PASS1 = """You are an independent linguistic coder for an AAC (augmentative and alternative communication) study.
A person who uses an AAC app selected the KEYWORDS below; the app must turn them into the one sentence the person means. You do NOT know the original sentence.

For EACH item and EACH of the five dimensions, list every reading that is ADMISSIBLE: a fluent, ordinary sentence that a person could plausibly mean with exactly these keywords (you may add function words, pronouns, auxiliaries, negation, question form, hedges or politeness words, but not new content nouns/verbs/adjectives that change the topic). For each admissible reading give the dimension value and one short witness paraphrase (a full sentence using the keywords that has that value). Include a reading only if a typical listener would find it a natural intended meaning, not merely grammatically possible. Mark ambiguous=true if two or more DIFFERENT values are admissible, else false. For every dimension, explicitly consider EACH option value in turn (e.g. would a negated version, a question, a request, a hedged version, a polite version, a different doer be a natural intended meaning of these keywords?) and include it only if it is plausible. Do not list the same value twice. Never use "mixed/unclear" as a reading unless the keywords themselves force an uncertain/mixed reading.

{codebook}

{guard}

Items (id: keywords):
{items}"""

PASS1G = PASS1.replace(
    "Mark ambiguous=true if two or more DIFFERENT values are admissible, else false.",
    "Tag every reading with plausibility: \"likely\" = a typical listener would consider it one of the main "
    "candidate meanings of these keywords; \"possible\" = coherent and natural enough to be meant, but a "
    "less expected interpretation. Do not list readings that are merely grammatical stretches. "
    "Mark ambiguous=true if two or more DIFFERENT values are admissible (likely or possible), else false.")
assert PASS1G != PASS1

PASS2 = """You are an independent linguistic coder for an AAC (augmentative and alternative communication) study.
Below are complete messages that people want to say. For EACH message and EACH of the five dimensions, record the single value the message itself explicitly commits to (code the words on the page, the main clause / first sentence for speech act and agent), and copy the shortest exact evidence words ("" when the value rests on absence, e.g. an unmarked affirmative or no politeness).

{codebook}

{guard}

Messages (id: text):
{items}"""


def schema(pass_: str) -> dict:
    props = {}
    for d, opts in DIMS.items():
        if pass_ in ("p1", "p1g"):
            props[d] = {"type": "object", "additionalProperties": False,
                        "required": ["readings", "ambiguous"],
                        "properties": {"readings": {"type": "array", "items": {
                            "type": "object", "additionalProperties": False,
                            "required": ["value", "witness"] + (["plausibility"] if pass_ == "p1g" else []),
                            "properties": {"value": {"type": "string", "enum": opts},
                                           "witness": {"type": "string"},
                                           **({"plausibility": {"type": "string", "enum": ["likely", "possible"]}}
                                              if pass_ == "p1g" else {})}}},
                            "ambiguous": {"type": "boolean"}}}
        else:
            props[d] = {"type": "object", "additionalProperties": False,
                        "required": ["value", "evidence"],
                        "properties": {"value": {"type": "string", "enum": opts},
                                       "evidence": {"type": "string"}}}
    item = {"type": "object", "additionalProperties": False, "required": ["id", *DIMS],
            "properties": {"id": {"type": "string"}, **props}}
    return {"type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "items": item}}}


def load_sample() -> list[dict]:
    rows = [json.loads(l) for l in SAMPLE.open()]
    rng = random.Random(SEED)
    order = sorted(rows, key=lambda r: r["rank"])
    rng.shuffle(order)
    for i, r in enumerate(order, 1):
        r["wid"] = f"w{i:03d}"
    return order


def batches(rows):
    return [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]


def prompt_for(pass_: str, batch: list[dict]) -> str:
    if pass_ in ("p1", "p1g"):
        items = "\n".join(f"{r['wid']}: {' '.join(r['pos_cap4'])}" for r in batch)
        return (PASS1 if pass_ == "p1" else PASS1G).format(codebook=CODEBOOK, guard=GUARD, items=items)
    items = "\n".join(f"{r['wid']}: {r['text']}" for r in batch)
    return PASS2.format(codebook=CODEBOOK, guard=GUARD, items=items)


def validate(out: dict, batch: list[dict], pass_: str) -> str | None:
    got = {o["id"]: o for o in out.get("items", [])}
    missing = [r["wid"] for r in batch if r["wid"] not in got]
    if missing:
        return f"missing {missing}"
    if pass_ in ("p1", "p1g"):
        for o in got.values():
            for d in DIMS:
                if not o[d]["readings"]:
                    return f"{o['id']}/{d} no readings"
    return None


def run_job(model: str, pass_: str, bi: int, batch: list[dict], effort: str) -> str:
    raw = OUTDIR / "raw" / f"{model}_{pass_}_b{bi:02d}.json"
    if raw.exists():
        try:
            if validate(json.loads(raw.read_text()), batch, pass_) is None:
                return f"cached {raw.name}"
        except Exception:  # noqa: BLE001
            pass
    raw.parent.mkdir(parents=True, exist_ok=True)
    prompt = prompt_for(pass_, batch)
    (OUTDIR / "prompts").mkdir(parents=True, exist_ok=True)
    (OUTDIR / "prompts" / f"{model}_{pass_}_b{bi:02d}.txt").write_text(prompt)
    err = None
    for attempt in range(3):
        with tempfile.TemporaryDirectory(prefix="wb_codex_") as tmp:
            sp = Path(tmp) / "schema.json"
            sp.write_text(json.dumps(schema(pass_)))
            work = Path(tmp) / "empty"; work.mkdir()
            op = Path(tmp) / "out.json"
            cmd = ["codex", "exec", "-m", model, "-c", f'model_reasoning_effort="{effort}"',
                   "-s", "read-only", "-C", str(work), "--skip-git-repo-check", "--ephemeral",
                   "--output-schema", str(sp), "-o", str(op), "-"]
            p = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=1800)
            (OUTDIR / "logs").mkdir(parents=True, exist_ok=True)
            (OUTDIR / "logs" / f"{model}_{pass_}_b{bi:02d}_a{attempt}.log").write_text(
                p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-20000:])
            try:
                out = json.loads(op.read_text())
                err = validate(out, batch, pass_)
            except Exception as e:  # noqa: BLE001
                err = f"parse: {e}"
            if err is None:
                out["_meta"] = {"model": model, "pass": pass_, "batch": bi, "effort": effort,
                                "attempt": attempt, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(),
                                "schema_sha": hashlib.sha256(sp.read_bytes()).hexdigest(),
                                "returncode": p.returncode}
                raw.write_text(json.dumps(out, indent=1))
                return f"ok {raw.name} (attempt {attempt})"
    return f"FAILED {raw.name}: {err}"


def cmd_run(a) -> None:
    rows = load_sample()
    bs = batches(rows)
    jobs = [(m, p, i, b) for m in a.models.split(",") for p in a.passes.split(",") for i, b in enumerate(bs)]
    with ThreadPoolExecutor(a.jobs) as ex:
        for msg in ex.map(lambda j: run_job(*j, a.effort), jobs):
            print(msg, flush=True)


def load_raw(model: str, pass_: str, rows) -> dict:
    out = {}
    for bi, b in enumerate(batches(rows)):
        d = json.loads((OUTDIR / "raw" / f"{model}_{pass_}_b{bi:02d}.json").read_text())
        out.update({o["id"]: o for o in d["items"]})
    return out


def cmd_merge(a) -> None:
    rows = load_sample()
    models = a.models.split(",")
    p1 = {m: load_raw(m, "p1", rows) for m in models}
    p2 = {m: load_raw(m, "p2", rows) for m in models}
    have_g = all((OUTDIR / "raw" / f"{m}_p1g_b{bi:02d}.json").exists()
                 for m in models for bi in range(len(batches(rows))))
    p1g = {m: load_raw(m, "p1g", rows) for m in models} if have_g else None
    panel = []
    for r in sorted(rows, key=lambda r: r["wid"]):
        rec = {"id": r["id"], "wid": r["wid"], "sample": r["sample"], "stratum": r["stratum"],
               "focal_dim": r["focal_dim"], "text": r["text"], "pos_cap4": " ".join(r["pos_cap4"]),
               "dims": {}}
        for d in DIMS:
            e = {}
            for ci, m in enumerate(models, 1):
                rd = p1[m][r["wid"]][d]
                vals = sorted({x["value"] for x in rd["readings"]})
                e[f"readings_{ci}"] = rd["readings"]
                e[f"values_{ci}"] = vals
                e[f"flag_{ci}"] = rd["ambiguous"]
                e[f"amb_{ci}"] = len(vals) >= 2
                e[f"src_{ci}"] = p2[m][r["wid"]][d]["value"]
                e[f"src_evidence_{ci}"] = p2[m][r["wid"]][d]["evidence"]
                e[f"supplied_{ci}"] = (len(vals) == 1 and vals[0] == e[f"src_{ci}"])
                e[f"src_admissible_{ci}"] = e[f"src_{ci}"] in vals
                if p1g:
                    rg = p1g[m][r["wid"]][d]["readings"]
                    lik = sorted({x["value"] for x in rg if x["plausibility"] == "likely"})
                    e[f"readings_g_{ci}"] = rg
                    e[f"values_likely_{ci}"] = lik
                    e[f"amb_strict_{ci}"] = len(lik) >= 2
                    e[f"supplied_strict_{ci}"] = (len(lik) == 1 and lik[0] == e[f"src_{ci}"])
            if p1g:
                a1, a2 = e["amb_strict_1"], e["amb_strict_2"]
                u1, u2 = e["supplied_strict_1"], e["supplied_strict_2"]
                e["status_strict"] = ("confirmed_ambiguous" if a1 and a2 else "supplied" if u1 and u2 else
                                      "coder_disagree" if a1 != a2 or u1 != u2 else "unambiguous_wrong")
            e["confirmed_ambiguous"] = e["amb_1"] and e["amb_2"]
            e["supplied"] = e["supplied_1"] and e["supplied_2"]
            e["source_value"] = e["src_1"] if e["src_1"] == e["src_2"] else None
            e["status"] = ("confirmed_ambiguous" if e["confirmed_ambiguous"] else
                           "supplied" if e["supplied"] else
                           "coder_disagree" if e["amb_1"] != e["amb_2"] or e["supplied_1"] != e["supplied_2"]
                           else "unambiguous_wrong" )
            rec["dims"][d] = e
        panel.append(rec)
    with (OUTDIR / "panel.jsonl").open("w") as f:
        for p in panel:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    agr = {"models": models, "n_messages": len(panel), "by_dim": {}}
    for d in DIMS:
        es = [p["dims"][d] for p in panel]
        a1, a2 = [e["amb_1"] for e in es], [e["amb_2"] for e in es]
        s1, s2 = [e["src_1"] for e in es], [e["src_2"] for e in es]
        u1, u2 = [e["supplied_1"] for e in es], [e["supplied_2"] for e in es]
        agr["by_dim"][d] = {
            "ambiguous_rate_1": round(sum(a1) / len(es), 3), "ambiguous_rate_2": round(sum(a2) / len(es), 3),
            "ambiguous_agree": round(sum(x == y for x, y in zip(a1, a2)) / len(es), 3),
            "ambiguous_kappa": _r(cohen_kappa(a1, a2)),
            "confirmed_ambiguous_n": sum(e["confirmed_ambiguous"] for e in es),
            "supplied_agree": round(sum(x == y for x, y in zip(u1, u2)) / len(es), 3),
            "supplied_kappa": _r(cohen_kappa(u1, u2)),
            "supplied_n": sum(e["supplied"] for e in es),
            "source_value_agree": round(sum(x == y for x, y in zip(s1, s2)) / len(es), 3),
            "source_value_kappa": _r(cohen_kappa(s1, s2)),
            "flag_inconsistent_1": sum(e["flag_1"] != e["amb_1"] for e in es),
            "flag_inconsistent_2": sum(e["flag_2"] != e["amb_2"] for e in es),
            "status_counts": {s: sum(e["status"] == s for e in es) for s in
                              ("confirmed_ambiguous", "supplied", "coder_disagree", "unambiguous_wrong")}}
        if p1g:
            b1, b2 = [e["amb_strict_1"] for e in es], [e["amb_strict_2"] for e in es]
            agr["by_dim"][d]["strict"] = {
                "ambiguous_rate_1": round(sum(b1) / len(es), 3), "ambiguous_rate_2": round(sum(b2) / len(es), 3),
                "ambiguous_agree": round(sum(x == y for x, y in zip(b1, b2)) / len(es), 3),
                "ambiguous_kappa": _r(cohen_kappa(b1, b2)),
                "status_counts": {s: sum(e["status_strict"] == s for e in es) for s in
                                  ("confirmed_ambiguous", "supplied", "coder_disagree", "unambiguous_wrong")}}
    agr["strict_available"] = bool(p1g)
    (OUTDIR / "agreement.json").write_text(json.dumps(agr, indent=1))
    print(json.dumps(agr, indent=1))


def _r(x):
    return None if x is None else round(x, 3)


def cmd_audit(a) -> None:
    panel = [json.loads(l) for l in (OUTDIR / "panel.jsonl").open()]
    rng = random.Random(SEED + 7)
    pick = rng.sample(panel, 20)
    items = []
    for p in pick:
        dims = {}
        for d, e in p["dims"].items():
            dims[d] = {"coder1_readings": e["readings_1"], "coder2_readings": e["readings_2"],
                       "panel_status": e["status"],
                       "coder1_source": e["src_1"], "coder2_source": e["src_2"],
                       "HUMAN_ambiguous_yes_no": "", "HUMAN_source_value": "",
                       "HUMAN_panel_correct_yes_no": "", "HUMAN_note": ""}
        items.append({"audit_id": p["wid"], "keywords_shown_first": p["pos_cap4"],
                      "full_source_reveal_after": p["text"], "dims": dims})
    doc = {"instructions": (
        "W-B admissibility audit (20 random messages of 160). For each item: FIRST look only at "
        "keywords_shown_first and decide, per dimension, whether >=2 different values are plausible "
        "(HUMAN_ambiguous_yes_no). THEN read full_source_reveal_after and give the value the source "
        "commits to (HUMAN_source_value; options in 'options'). Finally say whether the panel status "
        "is right (HUMAN_panel_correct_yes_no). Coder readings are shown for reference; to stay "
        "source-blind, cover them until you have made your own ambiguity judgement."),
        "options": DIMS, "panel_models": MODELS, "sampling": f"random.Random({SEED + 7}).sample(panel, 20)",
        "items": items}
    out = ROOT / "annotation/wb_audit.json"
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"wrote {out} ({len(items)} items)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["run", "merge", "audit"])
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--passes", default="p1,p2", help="p1 (primary), p2 (source), p1g (graded sensitivity)")
    a = ap.parse_args()
    {"run": cmd_run, "merge": cmd_merge, "audit": cmd_audit}[a.cmd](a)


if __name__ == "__main__":
    main()
