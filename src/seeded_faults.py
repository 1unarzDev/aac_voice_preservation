"""Seeded-fault sweep of the harness (task B1). CPU only. See analysis/seeded_faults/PLAN.md (written before any run).

  python src/seeded_faults.py run [--jobs 6] [--only SF01,SF02] [--keep]   # full sweep; writes analysis/seeded_faults/*
  python src/seeded_faults.py baseline                                      # clean-code baseline only
  python src/seeded_faults.py validate                                      # generator checks only (apply+compile, no tests)

Each mutant is built in its own copy tmp/sf/<id>/ (src/, tests/, prompts/ copied; data dirs symlinked read-only;
runs/fixture and analysis/robust are private real dirs because tests write there). The real src/ is never touched.
The mutated copy is then exercised by the existing self-tests (pytest, oracle identity/injection/challenge re-scoring,
R5 validator replay, T9 replay, re-scoring of stored runs against frozen endpoints.json) plus one supplementary
column (request_rebuild). `_harness` runs inside the mutant copy and compares with FROZEN files in the real repo.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REAL = Path(__file__).resolve().parents[1]
SF = REAL / "tmp" / "sf"
OUT = REAL / "analysis" / "seeded_faults"
PY = str(REAL / ".venv" / "bin" / "python")
PREFIX = "round2_" if "--round2" in sys.argv else ""   # round 1 files keep their names; round 2 writes round2_*
DEPS = SF / "_deps"          # pytest installed with --target (the project venv has no pytest)


# =============================================================================== mutation table
def M(mid, cls, file, desc, *pairs):
    return dict(id=mid, cls=cls, file=file, desc=desc, pairs=[list(p) for p in pairs])


A, L, J, B, O, V, Y = ("src/attribute.py", "src/labels.py", "src/judge.py", "src/build_requests.py",
                       "src/oracle_wa.py", "src/validate_cue_inputs.py", "src/layer0.py")

MUTATIONS = [
    # ---- K1 verdict rules (attribute.py)
    M("SF01", "K1", A, "Violation: drop `not` (violation = critical_match)",
      ('None if not o["valid"] or crit is None else not r["critical_match"])',
       'None if not o["valid"] or crit is None else r["critical_match"])')),
    M("SF02", "K1", A, "Assumption: negate committed",
      ('or crit is None else r["committed"])', 'or crit is None else not r["committed"])')),
    M("SF03", "K1", A, "committed: drop `not` (committed = is_unclear)",
      ('r["committed"] = None if crit is None else not is_unclear(crit)',
       'r["committed"] = None if crit is None else is_unclear(crit)')),
    M("SF04", "K1", A, "chose: variant-A value reported as B",
      ('r["chose"] = "A"', 'r["chose"] = "B"')),
    M("SF05", "K1", A, "constraint_preserving: `and` -> `or`",
      ('bool(r["critical_match"] and not any_contra)', 'bool(r["critical_match"] or not any_contra)')),
    M("SF06", "K1", A, "non-completion on a cue channel counted as constraint-preserving",
      ('                r["constraint_preserving"] = False', '                r["constraint_preserving"] = True')),
    M("SF07", "K1", A, "general-dim comparison also scores the family's own critical dimension",
      ('comparable = d != dim and val is not None', 'comparable = val is not None')),
    M("SF08", "K1", A, "hedge_added inverted",
      ('cert == "hedged/uncertain" and "hedged/uncertain" not in (spec["certainty"] or ())',
       'cert == "hedged/uncertain" and "hedged/uncertain" in (spec["certainty"] or ())')),
    M("SF09", "K1", A, "emphatic_added reference test inverted (!= -> ==)",
      ('src_l0[var["source"]]["certainty"] != EMPH', 'src_l0[var["source"]]["certainty"] == EMPH')),
    M("SF10", "K1", A, "arbiter labels never used when J1 != J2",
      ('elif k in arb:', 'elif False and k in arb:')),
    # ---- K2 channel-to-commitment mapping
    M("SF11", "K2", A, "contra: counts dimensions NOT given by the channel",
      ('r[f"contra_{d}"] = bool(bad and d in given) if comparable else None',
       'r[f"contra_{d}"] = bool(bad and d not in given) if comparable else None')),
    M("SF12", "K2", A, "stance addition: counts dimensions given by the channel",
      ('r[f"addition_{d}"] = bool(bad and d not in given) if comparable else None',
       'r[f"addition_{d}"] = bool(bad and d in given) if comparable else None')),
    M("SF13", "K2", A, "`full` is no longer a cue channel",
      ('CUE_CHANNELS = {"chip1", "chipall", "full"}', 'CUE_CHANNELS = {"chip1", "chipall"}')),
    M("SF14", "K2", A, "`noncrit` is no longer an ambiguous channel",
      ('AMBIG_CHANNELS = {"bare", "noncrit"}', 'AMBIG_CHANNELS = {"bare"}')),
    M("SF15", "K2", A, "channel_dims: chip1 gives the all_chips dimensions",
      ('return dims_in_chips(var.get("chips", []))', 'return dims_in_chips(var.get("all_chips", []))')),
    M("SF16", "K2", A, "channel_dims: full channel gives no general dimension",
      ('return set(GENERAL_DIMS)', 'return set()')),
    M("SF17", "K2", A, "custom channel: cue test reversed subset",
      ('set(var["chips"]) <= set(cust["commitments"])', 'set(var["chips"]) >= set(cust["commitments"])')),
    M("SF18", "K2", L, "chip table: [NOT] -> affirmative",
      ('"[NOT]": ("polarity", frozenset({"negated"})),', '"[NOT]": ("polarity", frozenset({"affirmative"})),')),
    M("SF19", "K2", L, "chip table: [YOU] -> speaker",
      ('"[YOU]": ("agent", frozenset({"addressee"})),', '"[YOU]": ("agent", frozenset({"speaker"})),')),
    M("SF20", "K2", L, "general_spec: requests no longer make certainty n/a",
      ('acts & {"question", "request/command"}', 'acts & {"question"}')),
    # ---- K3 judge post-processing
    M("SF21", "K3", J, "_final: agreement is flagged as disagreement",
      ('        return a, False', '        return a, True')),
    M("SF22", "K3", J, "_final: tiebreak returns J1 instead of layer0 value",
      ('return tiebreak, True', 'return a, True')),
    M("SF23", "K3", J, "_final: unresolved disagreement keeps J1 label",
      ('return None, True', 'return a, True')),
    M("SF24", "K3", J, "general-dim tiebreak uses the polarity layer0 label for every dimension",
      ('_final(r[f"{j1}_{d}"], r[f"{j2}_{d}"], L[d])', '_final(r[f"{j1}_{d}"], r[f"{j2}_{d}"], L["polarity"])')),
    M("SF25", "K3", J, "critical label: J2 ignored (J1 compared with itself)",
      ('_final(r[f"{j1}_critical"], r[f"{j2}_critical"])', '_final(r[f"{j1}_critical"], r[f"{j1}_critical"])')),
    M("SF26", "K3", J, "added_content read from the extraction pass instead of pass B",
      ('r[f"{v}_added_content"] = b.get("added_content")', 'r[f"{v}_added_content"] = a.get("added_content")')),
    # ---- K4 input builder
    M("SF27", "K4", B, "chip1 channel emits all_chips (wrong chip set)",
      ('P.sort_chips(v["chips"]) + [fam["bare"]]', 'P.sort_chips(v["all_chips"]) + [fam["bare"]]')),
    M("SF28", "K4", B, "chipall channel emits only the critical chips",
      ('P.sort_chips(v["all_chips"]) + [fam["bare"]]', 'P.sort_chips(v["chips"]) + [fam["bare"]]')),
    M("SF29", "K4", B, "chipall channel puts keywords before the chips",
      ('" ".join(P.sort_chips(v["all_chips"]) + [fam["bare"]])', '" ".join([fam["bare"]] + P.sort_chips(v["all_chips"]))')),
    M("SF30", "K4", B, "full channel types the bare keywords instead of the source sentence",
      ("return f\"The user typed: {v['source']}\"", "return f\"The user typed: {fam['bare']}\"")),
    M("SF31", "K4", B, "noncrit channel drops the noncritical word",
      ('words = insert_in_source_order(fam["bare"], fam["noncritical"], v["source"])', 'words = fam["bare"]')),
    M("SF32", "K4", B, "noncritical word inserted at the wrong position (> -> <)",
      ('if p > wpos), len(kws))', 'if p < wpos), len(kws))')),
    M("SF33", "K4", B, "request_key no longer depends on sample_idx",
      ('parts = [model, prompt_id, prompt, temperature, sample_idx]', 'parts = [model, prompt_id, prompt, temperature]')),
    M("SF34", "K4", B, "identical renders no longer merge their targets",
      ('reqs[key]["targets"].append(target)', 'pass')),
    # ---- K5 oracle acceptance
    M("SF35", "K5", L, "critical_match: plain no longer honoured by emphatic",
      ('return label in (PLAIN_A, EMPH)', 'return label == PLAIN_A')),
    M("SF36", "K5", L, "critical_match: acceptance relaxed to also accept refusal",
      ('return label in ("acceptance", "statement")', 'return label in ("acceptance", "statement", "refusal")')),
    M("SF37", "K5", L, "critical_match: plain~emphatic relaxation applied to every certainty value",
      ('if dimension == "certainty" and variant_value == PLAIN_A:', 'if dimension == "certainty":')),
    M("SF38", "K5", L, "critical_match: acceptance~statement relaxation removed",
      ('variant_value == "acceptance" and not _RAW:', 'variant_value == "acceptance" and False:')),
    M("SF39", "K5", L, "critical_match: final equality inverted",
      ('return label == variant_value', 'return label != variant_value')),
    M("SF40", "K5", O, "oracle verdict(): violation = critical_match",
      ('"violation": (None if crit is None else not cm) if cue else None,',
       '"violation": (None if crit is None else cm) if cue else None,')),
    M("SF41", "K5", O, "oracle verdict(): contradiction test inverted",
      ('contra |= val not in s_', 'contra |= val in s_')),
    # ---- K6 cue validator
    M("SF42", "K6", V, "requirement_set: plain no longer honoured by emphatic",
      ('return frozenset({PLAIN_A, EMPH})', 'return frozenset({PLAIN_A})')),
    M("SF43", "K6", V, "requirement_set: polite values no longer a class",
      ('        return POLITE\n    return frozenset({value})', '        return frozenset({value})\n    return frozenset({value})')),
    M("SF44", "K6", V, "decode: several cues for one dimension are unioned instead of intersected",
      ('acc = frozenset.intersection(*[v for v, _ in items])', 'acc = frozenset.union(*[v for v, _ in items])')),
    M("SF45", "K6", V, "validate: disjoint accepted/required sets no longer conflict",
      ('elif not (accepted & req):', 'elif False:')),
    M("SF46", "K6", V, "validate: compatible test reversed (req <= accepted)",
      ('elif accepted <= req:', 'elif req <= accepted:')),
    M("SF47", "K6", V, "validate: conflicting verdict only for non-consensus claims",
      ('if relation == "conflicting" and requirement.basis == "panel_consensus":',
       'if relation == "conflicting" and requirement.basis != "panel_consensus":')),
    M("SF48", "K6", V, "decode: 'would you' no longer a politeness marker",
      ('POLITE_BIGRAMS = {("could", "you"), ("would", "you")}', 'POLITE_BIGRAMS = {("could", "you")}')),
    M("SF49", "K6", V, "decode: 'feel sorry' no longer treated as ambiguous",
      ('if w == "sorry" and prev in FEELING_VERBS:', 'if w == "sorry" and prev in ():')),
    # ---- K7 deterministic labeler
    M("SF50", "K7", Y, "layer0: requests no longer certainty n/a",
      ('if act in ("question", "request/command"):\n        cert, cert_ev = NA_CERTAINTY, act',
       'if act == "question":\n        cert, cert_ev = NA_CERTAINTY, act')),
    M("SF51", "K7", Y, "layer0: booster outranks hedge",
      ('    elif "hedge" in cats:\n        cert, cert_ev = "hedged/uncertain", cats["hedge"][0]\n'
       '    elif "booster" in cats:\n        cert, cert_ev = "strongly certain/emphatic", cats["booster"][0]',
       '    elif "booster" in cats:\n        cert, cert_ev = "strongly certain/emphatic", cats["booster"][0]\n'
       '    elif "hedge" in cats:\n        cert, cert_ev = "hedged/uncertain", cats["hedge"][0]')),
    M("SF52", "K7", Y, "layer0: polarity negated if ANY main clause is negated",
      ('if heads and all(per):', 'if heads and any(per):')),
    # ---- K8 data plumbing and aggregation
    M("SF53", "K8", "src/runio.py", "occurrence validity: `and` -> `or`",
      ('out["valid"] = bool(out["valid"]) and bool(txt.strip())', 'out["valid"] = bool(out["valid"]) or bool(txt.strip())')),
    M("SF54", "K8", "src/explode.py", "text normalisation no longer lower-cases",
      ('t = re.sub(r"\\s+", " ", t.lower()).strip()', 't = re.sub(r"\\s+", " ", t).strip()')),
    M("SF55", "K8", "src/analyze.py", "bootstrap point estimate divides by families, not valid rows",
      ('estimate = float(agg["sum"].sum() / n)', 'estimate = float(agg["sum"].sum() / len(agg))')),
    M("SF56", "K8", "src/analyze.py", "paired difference direction reversed",
      ('pairs["critical_match_difference"] = pairs[high] - pairs[low]', 'pairs["critical_match_difference"] = pairs[low] - pairs[high]')),
    M("SF57", "K8", A, "ambiguous-channel dedupe ignores channel",
      ('amb1 = amb.drop_duplicates(["request_key", "suggestion_idx", "channel", "family_id"])',
       'amb1 = amb.drop_duplicates(["request_key", "suggestion_idx", "family_id"])')),
    M("SF58", "K8", A, "endpoints: quarantined refusal/acceptance families are KEPT in primary estimates",
      ('df = df[~df.quarantine_refusal_acceptance.fillna(False).astype(bool)]',
       'df = df[df.quarantine_refusal_acceptance.fillna(False).astype(bool) | True]')),
]
EXISTING_TESTS = None  # filled below (list of column names 1-7); request_rebuild is supplementary
HARNESS_TESTS = ["oracle_identity", "oracle_injection", "oracle_challenge", "validator_r5_replay",
                 "validator_t9_replay", "rescore_frozen_endpoints", "request_rebuild"]
SUPPLEMENTARY = ["request_rebuild"]
# runs re-scored against frozen runs/<run>/endpoints.json; option fixed from the clean baseline probe
RESCORE = {"expB1": {}, "expC1": {}, "oracle_inject": {}, "pilot1": {}, "hw2": {}, "legend1": {},
           "ext_legend1_nemo": {}, "ext_hw_nemo": {}, "ext_hw_qwen14": {}, "ext_legend1_qwen14": {},
           "wb1": {}, "wb1i": {}, "main1": {}, "elic1": {}, "hwctl1": {}, "r2c1": {},
           "r2d1": {"fallback": "J1"}, "span1": {"resolution": True}, "guard1": {"resolution": True},
           "gem_31-flash-lite_legend": {}, "gem_35-flash_legend": {}}
# stored request files rebuilt from their items file (probe on clean decides which are kept; see REBUILD)
REBUILD = ["expB1", "wb1", "pilot", "test", "hw"]


def mutation_table_sha() -> str:
    return hashlib.sha256(json.dumps(MUTATIONS, sort_keys=True).encode()).hexdigest()


# =============================================================================== workdir building
def build_workdir(mid: str, mut: dict | None) -> Path:
    wd = SF / mid
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    for d in ("src", "tests", "prompts"):
        shutil.copytree(REAL / d, wd / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    shutil.rmtree(wd / "tests" / "fixtures", ignore_errors=True)
    shutil.copytree(REAL / "tests" / "fixtures", wd / "tests" / "fixtures")
    private = {"runs": {"fixture"}, "analysis": {"robust"}}
    for name in ("data", "annotation", "annotation_package", "analysis", "runs", "cache", "models", "orchestration", "lit"):
        src = REAL / name
        if not src.exists():
            continue
        if name in private:
            (wd / name).mkdir()
            for e in src.iterdir():
                if e.name in private[name]:
                    continue
                (wd / name / e.name).symlink_to(e)
            for p in private[name]:
                (wd / name / p).mkdir()
        else:
            (wd / name).symlink_to(src)
    # analysis/robust: read by tests (t2_posterior, ...), so symlink every entry except the T9 output dir
    for e in (REAL / "analysis" / "robust").iterdir():
        if e.name != "t9_validator_replay":
            (wd / "analysis" / "robust" / e.name).symlink_to(e)
    (wd / "tmp").mkdir()
    if mut is not None:
        apply_mutation(wd, mut)
    return wd


def apply_mutation(wd: Path, mut: dict) -> None:
    p = wd / mut["file"]
    text = p.read_text(encoding="utf-8")
    new = text
    for find, rep in mut["pairs"]:
        n = new.count(find)
        if n != 1:
            raise RuntimeError(f"{mut['id']}: target text occurs {n} times in {mut['file']}: {find[:70]!r}")
        new = new.replace(find, rep)
    if new == text:
        raise RuntimeError(f"{mut['id']}: mutation did not change {mut['file']}")
    p.write_text(new, encoding="utf-8")
    subprocess.run([PY, "-c", "import sys,py_compile;py_compile.compile(sys.argv[1],doraise=True,cfile=sys.argv[2])", str(p),
                    str(wd / "tmp" / "check.pyc")], check=True, capture_output=True)


# =============================================================================== running tests on a workdir
def run_pytest(wd: Path, timeout=900) -> dict:
    junit = wd / "tmp" / "junit.xml"
    env = dict(os.environ, PYTHONPATH=str(DEPS), PYTHONDONTWRITEBYTECODE="1", SF_REAL=str(REAL))
    t = time.time()
    try:
        r = subprocess.run([PY, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"],
                           cwd=wd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"timeout": True, "files": {}, "secs": time.time() - t}
    files: dict[str, dict] = {}
    import xml.etree.ElementTree as ET
    if junit.exists():
        for tc in ET.parse(junit).getroot().iter("testcase"):
            m = re.search(r"(test_[a-z0-9_]+)", (tc.get("classname") or "") + " " + (tc.get("name") or "") + " " + (tc.get("file") or ""))
            f = m.group(1) if m else "unknown"
            d = files.setdefault(f, {"n": 0, "fail": 0, "err": 0, "first": ""})
            d["n"] += 1
            bad = tc.find("failure")
            kind = "fail"
            if bad is None:
                bad = tc.find("error")
                kind = "err"
            if bad is not None:
                d[kind] += 1
                if not d["first"]:
                    d["first"] = f"{tc.get('classname')}.{tc.get('name')}: {(bad.get('message') or '')[:150]}"
    return {"timeout": False, "rc": r.returncode, "files": files, "secs": time.time() - t,
            "tail": r.stdout[-400:] + r.stderr[-300:]}


def run_harness(wd: Path, tests=None, timeout=1500) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SF_REAL=str(REAL))
    outp = wd / "tmp" / "harness.json"
    cmd = [PY, str(REAL / "src" / "seeded_faults.py"), "_harness", str(wd), str(outp)] + (list(tests) if tests else [])
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=wd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"__timeout__": True}
    if not outp.exists():
        return {"__crash__": (r.stderr or r.stdout)[-500:]}
    d = json.loads(outp.read_text())
    d["__secs__"] = time.time() - t
    return d


# =============================================================================== harness (runs INSIDE the mutant copy)
class Mismatch(Exception):
    """A comparison with frozen output failed (detection by assertion, not by crash)."""


def _setup_paths(wd: Path):
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
    sys.path.insert(0, str(wd / "src"))


def _norm(v):
    import pandas as pd
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ""
    if isinstance(v, bool) or str(v) in ("True", "False"):
        return str(v)
    return str(v)


def _frame_equal(got, froz, key, cols, what):
    got = {tuple(r[k] for k in key): r for r in got}
    froz = {tuple(r[k] for k in key): r for r in froz}
    if set(got) != set(froz):
        raise Mismatch(f"{what}: row sets differ ({len(set(got) ^ set(froz))} keys)")
    bad = []
    for k, fr in froz.items():
        for c in cols:
            if _norm(got[k].get(c)) != _norm(fr.get(c)):
                bad.append((k, c, _norm(got[k].get(c)), _norm(fr.get(c))))
    if bad:
        raise Mismatch(f"{what}: {len(bad)} cell mismatches, e.g. {bad[0]}")


def _injection_rows(wd: Path):
    import pandas as pd
    import attribute, runio
    from oracle_wa import crit_match
    from labels import GENERAL_DIMS
    df = attribute.score(wd / "runs/oracle_inject", resolution=wd / "annotation/label_resolution.jsonl")
    df["raw_match"] = [crit_match(d, v, c, raw=True) for d, v, c in zip(df.dimension, df.variant_value, df.critical)]
    df["contra_dims"] = [",".join(d for d in GENERAL_DIMS if r[f"contra_{d}"] is True) for _, r in df.iterrows()]
    return df.to_dict("records")


INJ_COLS = ["critical", "critical_source", "critical_match", "raw_match", "violation", "constraint_preserving",
            "contra_dims", "added_content", "polarity", "speech_act", "agent", "certainty", "politeness"]


def _frozen_csv(rel):
    with open(REAL / rel, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def t_oracle_identity(wd):
    got = [r for r in _injection_rows(wd) if r["model"] == "identity"]
    froz = [r for r in _frozen_csv("analysis/oracle/injection_results.csv") if r["model"] == "identity"]
    if len(froz) != 120:
        raise RuntimeError("frozen identity rows != 120")
    _frame_equal(got, froz, ("family_id", "variant"), INJ_COLS, "identity")
    if sum(1 for r in got if r["critical_match"] is False) != sum(1 for r in froz if r["critical_match"] == "False"):
        raise Mismatch("identity false-alarm count differs")


def t_oracle_injection(wd):
    got = [r for r in _injection_rows(wd) if r["model"] == "mutant"]
    froz = [r for r in _frozen_csv("analysis/oracle/injection_results.csv") if r["model"] == "mutant"]
    if len(froz) != 120:
        raise RuntimeError("frozen mutant rows != 120")
    _frame_equal(got, froz, ("family_id", "variant"), INJ_COLS, "injection")
    if sum(1 for r in got if r["violation"] is True) != sum(1 for r in froz if r["violation"] == "True"):
        raise Mismatch("detected-mutation count differs")


def t_oracle_challenge(wd):
    import oracle_wa as W, runio
    shas = (REAL / "analysis/oracle/challenge_keys_frozen.sha256").read_text().splitlines()
    for line in shas:
        m = re.match(r"^([0-9a-f]{64})\s+(\S+)", line)
        if m and hashlib.sha256((wd / m.group(2)).read_bytes()).hexdigest() != m.group(1):
            raise Mismatch(f"frozen key file changed: {m.group(2)}")
    ch = {c["cid"]: c for c in W.load_challenges()}
    judg = {j["family_id"]: j for j in runio.read_jsonl(wd / "runs/oracle_challenges/judgments.jsonl")}
    ap = wd / "runs/oracle_challenges/arbiter.jsonl"
    arb = {a["family_id"]: a["critical"] for a in runio.read_jsonl(ap)} if ap.exists() else {}
    recs = []
    for cid, c in ch.items():
        j = judg[cid]
        crit, src = j["critical"], "agree"
        if crit is None:
            crit, src = arb.get(cid), "arbiter" if cid in arb else "unresolved"
        gk = {d: v for d, v in c["key"].items() if d != "critical"}
        recs.append({"cid": cid, "judge_critical": crit, "source": src,
                     "match_prod": W.crit_match(c["dimension"], c["contract_value"], crit),
                     "match_raw": W.crit_match(c["dimension"], c["contract_value"], crit, raw=True),
                     "label_ok": crit == c["key"]["critical"], "general_keyed": len(gk),
                     "general_ok": sum((j.get(d) == v) for d, v in gk.items()),
                     "general_errors": "; ".join(f"{d}: key={v} judge={j.get(d)}" for d, v in gk.items() if j.get(d) != v)})
    froz = _frozen_csv("analysis/oracle/challenge_results.csv")
    _frame_equal(recs, froz, ("cid",), ["judge_critical", "source", "match_prod", "match_raw", "label_ok", "general_keyed",
                                         "general_ok", "general_errors"], "challenge")
    role = {r["cid"]: r["role"] for r in froz}
    new = [r for r in recs if role[r["cid"]] in ("control", "mutant")]
    det = sum(1 for r in new if role[r["cid"]] == "mutant" and r["match_prod"] is False)
    fa = sum(1 for r in new if role[r["cid"]] == "control" and r["match_prod"] is False)
    fdet = sum(1 for r in froz if r["role"] == "mutant" and r["match_prod"] == "False")
    ffa = sum(1 for r in froz if r["role"] == "control" and r["match_prod"] == "False")
    if (det, fa) != (fdet, ffa):
        raise Mismatch(f"challenge gate counts ({det},{fa}) != frozen ({fdet},{ffa})")


def _json_equal(a, b, path="", tol=1e-9):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return f"{path}: keys differ {sorted(set(a) ^ set(b))[:4]}"
        for k in a:
            r = _json_equal(a[k], b[k], f"{path}/{k}", tol)
            if r:
                return r
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: len {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            r = _json_equal(x, y, f"{path}[{i}]", tol)
            if r:
                return r
        return None
    if isinstance(a, float) or isinstance(b, float):
        try:
            if a is None or b is None:
                return None if a == b else f"{path}: {a} != {b}"
            return None if math.isclose(float(a), float(b), abs_tol=tol, rel_tol=1e-9) else f"{path}: {a} != {b}"
        except (TypeError, ValueError):
            return f"{path}: {a!r} != {b!r}"
    return None if a == b else f"{path}: {a!r} != {b!r}"


def t_validator_r5_replay(wd):
    import validate_cue_inputs as V
    out = wd / "tmp" / "r5"
    try:
        s = V.replay(out)                       # internal asserts (139/139, 7/7, 8 SURE, 0 coarse certified)
    except AssertionError as e:
        raise Mismatch(f"replay internal assertion failed: {e}") from e
    froz_json = json.loads((REAL / "analysis/r5_validator/replay.json").read_text())
    got_json = json.loads((out / "replay.json").read_text())
    got_json["input_sha256"], froz_json["input_sha256"] = {}, {}
    r = _json_equal(got_json, froz_json)
    if r:
        raise Mismatch("replay.json " + r)
    a = (out / "replay.csv").read_text()
    b = (REAL / "analysis/r5_validator/replay.csv").read_text()
    if a != b:
        raise Mismatch("replay.csv differs from frozen")


def t_validator_t9_replay(wd):
    import robust_t9_validator_replay as T
    out = wd / "tmp" / "t9"
    out.mkdir(parents=True, exist_ok=True)
    T.OUT = out
    T.main()
    got = json.loads((out / "summary.json").read_text())
    froz = json.loads((REAL / "analysis/robust/t9_validator_replay/summary.json").read_text())
    r = _json_equal(got, froz)
    if r:
        raise Mismatch("t9 summary " + r)


def t_rescore_frozen_endpoints(wd):
    import attribute
    bad = []
    for run, opt in RESCORE.items():
        kw = dict(opt)
        if kw.pop("resolution", False):
            kw["resolution"] = wd / "annotation/label_resolution.jsonl"
        ep = json.loads(json.dumps(attribute.endpoints(attribute.score(wd / "runs" / run, **kw))))
        froz = json.loads((REAL / "runs" / run / "endpoints.json").read_text())
        r = _json_equal(ep, froz)
        if r:
            bad.append(f"{run}{r}")
    if bad:
        raise Mismatch(f"{len(bad)}/{len(RESCORE)} runs differ from frozen endpoints: " + " | ".join(x[:110] for x in bad[:3]))


def t_request_rebuild(wd):
    import build_requests as B
    import runio
    bad = []
    for name in REBUILD:
        stored = {r["request_key"]: r for r in runio.read_jsonl(wd / "runs/requests" / f"{name}.jsonl")}
        files = sorted({r["items_file"] for r in stored.values()})
        fams = []
        for f in files:
            ip = wd / "data/items" / f
            if not ip.exists():
                ip = wd / "annotation/written" / f
            for line in ip.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    fam = json.loads(line)
                    fam["_file"] = f
                    if fam.get("dropped") is True:
                        continue
                    fams.append(fam)
        want_fam = {r["family_id"] for r in stored.values()}
        fams = [f for f in fams if f["family_id"] in want_fam]
        models = sorted({r["model"] for r in stored.values()})
        prompts = sorted({r["prompt_id"] for r in stored.values()})
        nss = sorted({r.get("namespace") for r in stored.values()}, key=lambda x: (x is not None, x or ""))
        chans = sorted({t["channel"] for r in stored.values() for t in r["targets"]})
        std = [c for c in B.CHANNELS if c in chans]
        built = {r["request_key"]: r for r in B.build(fams, models, prompts, std, nss)}
        if set(built) != set(stored):
            bad.append(f"{name}: key sets differ ({len(set(built) ^ set(stored))})")
            continue
        for k, r in stored.items():
            b = built[k]
            if (b["input_text"] != r["input_text"] or b["prompt"] != r["prompt"]
                    or sorted(map(json.dumps, b["targets"])) != sorted(map(json.dumps, r["targets"]))):
                bad.append(f"{name}: request {k[:8]} differs")
                break
    if bad:
        raise Mismatch(f"{len(bad)} request files differ: " + " | ".join(bad[:3]))


HARNESS_FUNCS = {"oracle_identity": t_oracle_identity, "oracle_injection": t_oracle_injection,
                 "oracle_challenge": t_oracle_challenge, "validator_r5_replay": t_validator_r5_replay,
                 "validator_t9_replay": t_validator_t9_replay, "rescore_frozen_endpoints": t_rescore_frozen_endpoints,
                 "request_rebuild": t_request_rebuild}


def harness_main(wd: Path, outp: Path, tests: list[str]):
    _setup_paths(wd)
    res = {}
    for name in (tests or HARNESS_TESTS):
        t = time.time()
        try:
            HARNESS_FUNCS[name](wd)
            res[name] = {"status": "pass", "secs": round(time.time() - t, 1)}
        except Mismatch as e:
            res[name] = {"status": "fail", "kind": "mismatch", "detail": str(e)[:300], "secs": round(time.time() - t, 1)}
        except BaseException as e:  # noqa: BLE001 -- any exception = the test failed (crash)
            res[name] = {"status": "fail", "kind": "crash", "detail": f"{type(e).__name__}: {str(e)[:250]}",
                         "secs": round(time.time() - t, 1)}
    outp.write_text(json.dumps(res, indent=1))


# =============================================================================== orchestration
def git_snapshot() -> str:
    """Fingerprint (content hash) of everything the sweep could have touched in the real tree. Other work in the repo
    is ignored on purpose (concurrent agents): only the mutation targets and the paths tests/harness write to."""
    h = hashlib.sha256()
    paths = sorted({REAL / m["file"] for m in MUTATIONS})
    for root in ("tests/fixtures", "runs/fixture", "analysis/robust/t9_validator_replay", "analysis/r5_validator",
                 "analysis/oracle", "runs/oracle_inject", "runs/oracle_challenges"):
        paths += sorted(p for p in (REAL / root).rglob("*") if p.is_file())
    for p in paths:
        h.update(str(p).encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def evaluate(mid: str, mut: dict | None) -> dict:
    t = time.time()
    wd = build_workdir(mid, mut)
    pt = run_pytest(wd)
    hn = run_harness(wd)
    return {"id": mid, "pytest": pt, "harness": hn, "secs": round(time.time() - t, 1)}


def column_status(res: dict) -> dict:
    """test column -> (failed?, kind, detail) for one evaluated workdir."""
    cols = {}
    pt = res["pytest"]
    if pt.get("timeout"):
        cols["pytest_all"] = (True, "timeout", "pytest timeout")
    else:
        failed_files = {f: d for f, d in pt["files"].items() if d["fail"] or d["err"]}
        n = sum(d["n"] for d in pt["files"].values())
        cols["pytest_all"] = (bool(failed_files) or pt.get("rc", 0) not in (0, 5) or n == 0,
                              "assert" if any(d["fail"] for d in failed_files.values()) else "crash" if failed_files else "",
                              "; ".join(d["first"] for d in list(failed_files.values())[:2]))
        for f, d in pt["files"].items():
            cols[f"pytest:{f}"] = (bool(d["fail"] or d["err"]), "assert" if d["fail"] else "crash" if d["err"] else "", d["first"])
    h = res["harness"]
    for name in HARNESS_TESTS:
        if "__timeout__" in h:
            cols[name] = (True, "timeout", "harness timeout")
        elif "__crash__" in h:
            cols[name] = (True, "crash", "harness process crash: " + h["__crash__"][-120:])
        else:
            r = h[name]
            cols[name] = (r["status"] == "fail", "assert" if r.get("kind") == "mismatch" else r.get("kind", ""), r.get("detail", ""))
    return cols


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def baseline() -> dict:
    res = evaluate("CLEAN", None)
    cols = column_status(res)
    bad = {k: v for k, v in cols.items() if v[0]}
    return {"res": res, "cols": cols, "bad": bad}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "_harness":
        harness_main(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4:])
        return
    SF.mkdir(parents=True, exist_ok=True)
    if cmd == "validate":
        for m in MUTATIONS:
            wd = build_workdir("V_" + m["id"], m)
            shutil.rmtree(wd)
        print(f"{len(MUTATIONS)} mutations apply and compile; sha {mutation_table_sha()[:12]}")
        return
    if cmd == "baseline":
        b = baseline()
        print(json.dumps({k: [v[0], v[1], v[2][:200]] for k, v in b["cols"].items()}, indent=1))
        print("BASELINE", "OK" if not b["bad"] else f"FAILED: {sorted(b['bad'])}")
        print(json.dumps(b["res"]["harness"], indent=1)[:3000])
        return
    # ---- run
    jobs = 6
    only = None
    keep = "--keep" in sys.argv
    if "--jobs" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1])
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    snap0 = git_snapshot()
    ids = [m["id"] for m in MUTATIONS]
    assert len(ids) == len(set(ids)) and 40 <= len(ids) <= 60
    b = baseline()
    if b["bad"]:
        print("CLEAN BASELINE FAILS; stopping:", {k: v[2][:200] for k, v in b["bad"].items()})
        sys.exit(2)
    print(f"clean baseline passes all columns ({b['res']['secs']}s)", flush=True)
    base_files = sorted(f for f in b["res"]["pytest"]["files"])
    muts = [m for m in MUTATIONS if only is None or m["id"] in only]
    results = {}

    def one(m):
        r = evaluate(m["id"], m)
        shutil.rmtree(SF / m["id"], ignore_errors=True)
        print(f"  {m['id']} done in {r['secs']}s", flush=True)
        return m["id"], r
    with ThreadPoolExecutor(jobs) as ex:
        for mid, r in ex.map(one, muts):
            results[mid] = r
    snap1 = git_snapshot()
    report(muts, results, b, base_files, snap0 == snap1)
    if not keep:
        shutil.rmtree(SF, ignore_errors=True)


# =============================================================================== report
def report(muts, results, b, base_files, tree_unchanged):
    OUT.mkdir(parents=True, exist_ok=True)
    pt_cols = [f"pytest:{f}" for f in base_files]
    existing = ["pytest_all"] + pt_cols + [t for t in HARNESS_TESTS if t not in SUPPLEMENTARY]
    allcols = existing + SUPPLEMENTARY
    matrix, detail = {}, {}
    for m in muts:
        cs = column_status(results[m["id"]])
        matrix[m["id"]] = {c: (cs.get(c, (False, "", ""))[0]) for c in allcols}
        detail[m["id"]] = {c: {"kind": cs[c][1], "detail": cs[c][2]} for c in allcols if cs.get(c, (False,))[0]}
    N = len(muts)
    primary = ["pytest_all"] + [t for t in HARNESS_TESTS if t not in SUPPLEMENTARY]       # pooled columns
    killed_by = {m["id"]: [c for c in primary if matrix[m["id"]][c]] for m in muts}
    killed_any = [mid for mid, v in killed_by.items() if v]
    surv = [m for m in muts if not killed_by[m["id"]]]
    killed_with_supp = [m["id"] for m in muts if killed_by[m["id"]] or matrix[m["id"]]["request_rebuild"]]
    # kind of the kills: semantic (assertion) vs crash-only
    def kinds(mid):
        ks = set()
        for c in primary:
            if matrix[mid][c]:
                ks.add(detail[mid][c]["kind"] or "?")
        return ks
    crash_only = [mid for mid in killed_any if kinds(mid) <= {"crash", "timeout"}]
    per_test = {}
    for c in allcols:
        k = sum(matrix[m["id"]][c] for m in muts)
        per_test[c] = {"killed": k, "n": N, "score": round(k / N, 4), "wilson95": [round(x, 3) for x in wilson(k, N)],
                       "unique_kills": sum(1 for m in muts if matrix[m["id"]][c] and len(killed_by[m["id"]]) == 1 and c in killed_by[m["id"]])}
    cls = {}
    for m in muts:
        d = cls.setdefault(m["cls"], {"n": 0, "killed": 0, "killed_with_supplementary": 0})
        d["n"] += 1
        d["killed"] += bool(killed_by[m["id"]])
        d["killed_with_supplementary"] += m["id"] in killed_with_supp
    summ = {"n_mutants": N, "mutation_table_sha256": mutation_table_sha(), "clean_baseline_passes_all_columns": not b["bad"],
            "real_tree_unchanged_by_sweep": tree_unchanged,
            "pooled_existing_tests": {"killed": len(killed_any), "n": N, "score": round(len(killed_any) / N, 4),
                                      "wilson95": [round(x, 3) for x in wilson(len(killed_any), N)]},
            "pooled_with_supplementary_request_rebuild": {"killed": len(killed_with_supp), "n": N,
                                                           "score": round(len(killed_with_supp) / N, 4)},
            "killed_only_by_crash_or_timeout": len(crash_only),
            "killed_by_assertion_or_mismatch": len(killed_any) - len(crash_only),
            "pytest_files": base_files, "per_test": per_test, "by_class": cls,
            "survivors": [m["id"] for m in surv], "pooled_columns": primary, "supplementary_columns": SUPPLEMENTARY,
            "baseline_secs": b["res"]["secs"]}
    (OUT / (PREFIX + "summary.json")).write_text(json.dumps(summ, indent=1))
    (OUT / (PREFIX + "mutant_results.json")).write_text(json.dumps(
        {m["id"]: {"cls": m["cls"], "file": m["file"], "desc": m["desc"], "killed_by": killed_by[m["id"]],
                   "also_killed_by_supplementary": matrix[m["id"]]["request_rebuild"], "detail": detail[m["id"]]}
         for m in muts}, indent=1))
    with open(OUT / (PREFIX + "kill_matrix.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["mutant", "class", "file", "description", "killed_by_existing"] + allcols)
        for m in muts:
            w.writerow([m["id"], m["cls"], m["file"], m["desc"], int(bool(killed_by[m["id"]]))] +
                       [int(matrix[m["id"]][c]) for c in allcols])
        w.writerow(["TOTAL_KILLED", "", "", "", len(killed_any)] + [per_test[c]["killed"] for c in allcols])
        w.writerow(["SCORE", "", "", "", round(len(killed_any) / N, 4)] + [per_test[c]["score"] for c in allcols])
    print(json.dumps({k: summ[k] for k in ("pooled_existing_tests", "killed_only_by_crash_or_timeout", "survivors")}, indent=1))
    print("per-test:", {c: v["killed"] for c, v in per_test.items()})
    print("report skeleton written; survivor explanations are added by hand in report.md")


if __name__ == "__main__":
    main()
