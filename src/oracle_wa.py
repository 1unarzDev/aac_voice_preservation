"""W-A oracle validation (round-2 protocol): identity + scoped-mutation injection, challenge judging.

  python src/oracle_wa.py prepare      # build runs/oracle_inject and runs/oracle_challenges
  python src/oracle_wa.py judge        # production judge (J1+J2, layer0 tiebreak), concurrency 8
  python src/oracle_wa.py arbiter-todo # list J1!=J2 critical rows needing the arbiter

Keys are frozen before judging: annotation/challenge_items{,_r2}.jsonl and
analysis/oracle/source_mutations.jsonl (sha256 in analysis/oracle/challenge_keys_frozen.sha256).
The judge, arbiter rule and attribute pipeline are the production ones (src/judge.py,
src/attribute.py); nothing here changes them. Injected texts are judged exactly as a
`full`-channel output of the source (input = "The user typed: <source>").
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runio  # noqa: E402

ROOT = runio.ROOT
INJ = ROOT / "runs/oracle_inject"
CHAL = ROOT / "runs/oracle_challenges"
OUT = ROOT / "analysis/oracle"
TEST = ROOT / "data/items/test.jsonl"


def _occ(text, family_id, variant, channel, input_text, model, dimension):
    rk = hashlib.sha1(json.dumps([model, family_id, variant, text]).encode()).hexdigest()
    return {"output_id": rk[:16], "text": text, "suggestion_idx": 0, "parse_ok": True,
            "request_key": rk, "model": model, "prompt_id": "INJ", "temperature": 0.0,
            "sample_idx": 0, "dimension": dimension, "split": "oracle",
            "input_text": input_text, "finish_reason": "stop", "family_id": family_id,
            "variant": variant, "channel": channel, "valid": True}


def load_challenges() -> list[dict]:
    """24 old (annotation/challenge_items.jsonl; options/input from gold_core.json) + 48 new."""
    core = {i["item_id"]: i for i in json.loads((ROOT / "annotation/gold_core.json").read_text())["items"]}
    out = []
    for r in runio.read_jsonl(ROOT / "annotation/challenge_items.jsonl"):
        g = core[r["cid"]]
        out.append({**r, "group": "r1_" + r["dimension"], "role": "r1", "pair": None,
                    "critical_options": g["critical"]["options"], "input_text": g["input_text"],
                    "contract_value": r["key"]["critical"]})
    out += runio.read_jsonl(ROOT / "annotation/challenge_items_r2.jsonl")
    return out


def prepare() -> None:
    items = runio.load_items(TEST)
    muts = {(m["family_id"], m["variant"]): m for m in runio.read_jsonl(OUT / "source_mutations.jsonl")}
    occ = []
    for fid, it in items.items():
        for v, var in it["variants"].items():
            inp = f"The user typed: {var['source']}"
            occ.append(_occ(var["source"], fid, v, "full", inp, "identity", it["dimension"]))
            occ.append(_occ(muts[(fid, v)]["mutant"], fid, v, "full", inp, "mutant", it["dimension"]))
    INJ.mkdir(parents=True, exist_ok=True)
    runio.write_jsonl(INJ / "outputs.jsonl", occ)
    (INJ / "config.json").write_text(json.dumps({"run_id": "oracle_inject", "items_path": str(TEST.relative_to(ROOT)),
                                                 "note": "W-A identity + scoped mutation injection (no generation)"}, indent=1))
    ch = load_challenges()
    fams, occ = [], []
    for c in ch:
        fams.append({"family_id": c["cid"], "dimension": c["dimension"], "split": "challenge",
                     "context": None, "critical_options": c["critical_options"],
                     "bare": c["input_text"], "noncritical": "",
                     "variants": {"A": {"source": c["text"], "critical_value": c["contract_value"],
                                        "chips": [], "all_chips": []},
                                  "B": {"source": c["text"], "critical_value": "__contract_complement__",
                                        "chips": [], "all_chips": []}}})
        occ.append(_occ(c["text"], c["cid"], "A", "bare", c["input_text"], "challenge", c["dimension"]))
    CHAL.mkdir(parents=True, exist_ok=True)
    runio.write_jsonl(CHAL / "items.jsonl", fams)
    runio.write_jsonl(CHAL / "outputs.jsonl", occ)
    (CHAL / "config.json").write_text(json.dumps({"run_id": "oracle_challenges",
                                                  "items_path": str((CHAL / "items.jsonl").relative_to(ROOT))}, indent=1))
    print(f"prepared {INJ} ({240} occurrences) and {CHAL} ({len(occ)} challenges)")


def judge() -> None:
    import judge as J
    J.CONCURRENCY = 8          # shared API limit is 16; this worker uses <= 8
    for d in (INJ, CHAL):
        asyncio.run(J.judge_run(d, None, J.JUDGE_MODEL, "low", ["J1", "J2"]))
        J._SEM = None          # new event loop -> new semaphore


def arbiter_todo() -> None:
    for d in (INJ, CHAL):
        rows = [r for r in runio.read_jsonl(d / "judgments.jsonl") if r["needs_arbiter"]]
        print(f"{d.name}: {len(rows)} critical disagreements")
        for r in rows:
            print(json.dumps({k: r[k] for k in ("text_id", "family_id", "input_text", "text", "dimension",
                                                "critical_options", "J1_critical", "J2_critical")}, ensure_ascii=False))


# ------------------------------------------------------------------ contract verdicts

def crit_match(dim, value, label, raw=False):
    """labels.critical_match; raw=True reproduces ORACLE_RAW=1 (no acceptance~statement relaxation)."""
    from labels import EMPH, PLAIN_A, critical_match
    if label is None:
        return None
    if raw:
        if dim == "certainty" and value == PLAIN_A:
            return label in (PLAIN_A, EMPH)
        return label == value
    return critical_match(dim, value, label)


def verdict(dim: str, var: dict, channel: str, L: dict, strict: bool = False) -> dict:
    """Production contract verdict (attribute.score, standard items) from labels L
    (critical + general dims). As in production, a missing general label is not
    comparable (ignored); strict=True makes constraint_preserving None instead."""
    from attribute import AMBIG_CHANNELS, CUE_CHANNELS, channel_dims
    from labels import GENERAL_DIMS, NA_CERTAINTY, critical_match, general_spec, is_unclear
    crit = L.get("critical")
    cue, amb = channel in CUE_CHANNELS, channel in AMBIG_CHANNELS
    cm = critical_match(dim, var["critical_value"], crit)
    out = {"critical_match": cm,
           "violation": (None if crit is None else not cm) if cue else None,
           "assumption": (None if crit is None else not is_unclear(crit)) if amb else None}
    spec = general_spec(var.get("all_chips", []), var.get("general_spec"))
    given = channel_dims(channel, var)
    contra, unknown = False, False
    for d in GENERAL_DIMS:
        if d == dim or d not in given:
            continue
        val, s_ = L.get(d), spec[d]
        if s_ is None:
            continue
        if val is None:
            unknown = strict
            continue
        if d == "certainty" and (val == NA_CERTAINTY or NA_CERTAINTY in s_):
            continue
        contra |= val not in s_
    if cue:
        out["constraint_preserving"] = (None if crit is None or (unknown and not contra and cm)
                                         else bool(cm and not contra))
    else:
        out["constraint_preserving"] = None
    return out


if __name__ == "__main__":
    {"prepare": prepare, "judge": judge, "arbiter-todo": arbiter_todo}[sys.argv[1]]()
