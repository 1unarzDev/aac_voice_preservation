"""Deterministic attribution (SPEC "Deterministic attribution" + "Endpoints", D-007).

Joins occurrences (explode.py outputs.jsonl), non-completions (generations.jsonl),
judgments.jsonl, an optional arbiter.jsonl and the item specs. No model is called here:
Violation / Assumption / stance additions are pure functions of extracted labels,
the item spec and the channel.

Per occurrence (one row per generation x suggestion x target in scored.parquet):
  cue_in_input       channel in {chip1, chipall, full}
  critical_match     extracted critical honours the variant value (D-007: on certainty,
                     plain OR emphatic honour 'plain assertion')
  violation          cue_in_input & valid & critical known & not critical_match
  assumption         channel in {bare, noncrit} & valid & critical committed (not unclear)
  chose              A | B | other | unclear  (which variant's value the output commits to)
  in_input_<d>       general dim d is explicitly given by the channel's input
  contra_<d>         in_input & output value not in the variant's spec set (d != the
                     family's critical dimension, which is scored above)
  addition_<d>       NOT in_input & output value not in spec set (stance addition)
  politeness_added / hedge_added / emphatic_added   directed stance additions
  constraint_preserving  (co-primary 1, cue channels) valid & critical_match &
                     no contra_<d>; non-completion = False; unknown critical = NA
Custom channels (D-012, families with `custom_channels`, Exp B/C): the channel's
`commitments` (build_requests.custom_spec) replace the chip1/chipall lookup;
cue_in_input = the variant's critical chips are among them, otherwise the channel
is ambiguous for the critical dimension and scored as Assumption. Standard items
are scored exactly as before.
Critical label source: J1==J2 agreement, else arbiter.jsonl, else (with
--fallback J1|J2) that variant, else NA (row excluded from rates; counted).

  python src/attribute.py --run pilot1            # writes scored.parquet + endpoints.json
  python src/attribute.py --run fixture --fallback J1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layer0  # noqa: E402
import runio  # noqa: E402
from build_requests import custom_spec  # noqa: E402
from labels import (EMPH, GENERAL_DIMS, NA_CERTAINTY, critical_match,  # noqa: E402
                    dims_in_chips, general_spec, is_unclear)

CUE_CHANNELS = {"chip1", "chipall", "full"}
AMBIG_CHANNELS = {"bare", "noncrit"}


def non_completions(run_dir: Path) -> list[dict]:
    """Targets of generations that failed or produced no suggestion (explode skips them)."""
    p = run_dir / "generations.jsonl"
    if not p.exists():
        return []
    out = []
    for g in runio.read_jsonl(p):
        if g.get("error") or not g.get("suggestions"):
            for t in g.get("targets", []):
                out.append({"output_id": None, "text_id": None, "text": "",
                            "request_key": g.get("request_key"), "model": g.get("model"),
                            "prompt_id": g.get("prompt_id"), "temperature": g.get("temperature"),
                            "sample_idx": g.get("sample_idx", 0), "suggestion_idx": 0,
                            "dimension": g.get("dimension"), "split": g.get("split"),
                            "input_text": g.get("input_text"), "finish_reason": g.get("finish_reason"),
                            "parse_ok": False, "valid": False, "error": g.get("error"), **t})
    return out


def channel_dims(channel: str, var: dict, custom: dict | None = None) -> set[str]:
    if custom is not None:
        return dims_in_chips(custom["commitments"])
    if channel == "full":
        return set(GENERAL_DIMS)
    if channel == "chip1":
        return dims_in_chips(var.get("chips", []))
    if channel == "chipall":
        return dims_in_chips(var.get("all_chips", []))
    return set()


def score(run_dir: Path, items_path=None, fallback: str | None = None) -> pd.DataFrame:
    occ = runio.load_occurrences(run_dir) + non_completions(run_dir)
    items = runio.load_items(runio.items_path_for(run_dir, items_path))
    jpath = run_dir / "judgments.jsonl"
    judg = {(j["text_id"], j["family_id"], j["input_text"]): j
            for j in (runio.read_jsonl(jpath) if jpath.exists() else [])}
    apath = run_dir / "arbiter.jsonl"
    arb = {(a["text_id"], a["family_id"], a["input_text"]): a["critical"]
           for a in (runio.read_jsonl(apath) if apath.exists() else [])}
    # layer0 on the SOURCE sentences: reference for 'emphatic added' (D-007)
    srcs = sorted({v["source"] for it in items.values() for v in it["variants"].values()})
    src_l0 = dict(zip(srcs, layer0.label_many(srcs)))

    rows = []
    for o in occ:
        it = items[o["family_id"]]
        var = it["variants"][o["variant"]]
        other = next(v for k, v in it["variants"].items() if k != o["variant"])
        vA, vB = it["variants"]["A"]["critical_value"], it["variants"]["B"]["critical_value"]
        dim = it["dimension"]
        cust = custom_spec(it, o["variant"], o["channel"]) if it.get("custom_channels") else None
        j = judg.get((o.get("text_id"), o["family_id"], o["input_text"])) if o["valid"] else None
        r = {k: o.get(k) for k in ("output_id", "text_id", "request_key", "model", "prompt_id",
                                   "temperature", "sample_idx", "suggestion_idx", "family_id",
                                   "variant", "channel", "split", "input_text", "text",
                                   "valid", "parse_ok", "finish_reason")}
        r.update(dimension=dim, variant_value=var["critical_value"],
                 other_value=other["critical_value"], judged=j is not None)

        crit, src = None, None
        if j is not None:
            r["critical_J1"], r["critical_J2"] = j.get("J1_critical"), j.get("J2_critical")
            r["needs_arbiter"] = bool(j.get("needs_arbiter"))
            k = (o["text_id"], o["family_id"], o["input_text"])
            if j.get("critical") is not None:
                crit, src = j["critical"], "agree"
            elif k in arb:
                crit, src = arb[k], "arbiter"
            elif fallback:
                crit, src = j.get(f"{fallback}_critical"), fallback
        r["critical"], r["critical_source"] = crit, src
        if cust is None:
            r["cue_in_input"] = o["channel"] in CUE_CHANNELS
            r["ambig_channel"] = o["channel"] in AMBIG_CHANNELS
        else:
            r["cue_in_input"] = set(var["chips"]) <= set(cust["commitments"])
            r["ambig_channel"] = not r["cue_in_input"]
        r["critical_match"] = critical_match(dim, var["critical_value"], crit)
        r["committed"] = None if crit is None else not is_unclear(crit)
        if crit is None:
            r["chose"] = None
        elif is_unclear(crit):
            r["chose"] = "unclear"
        elif critical_match(dim, vA, crit):
            r["chose"] = "A"
        elif critical_match(dim, vB, crit):
            r["chose"] = "B"
        else:
            r["chose"] = "other"
        r["violation"] = (None if not r["cue_in_input"] else
                          None if not o["valid"] or crit is None else not r["critical_match"])
        r["assumption"] = (None if not r["ambig_channel"] or not o["valid"]
                           or crit is None else r["committed"])

        spec = general_spec(var.get("all_chips", []), var.get("general_spec"))
        given = channel_dims(o["channel"], var, cust)
        any_contra, any_add = False, False
        for d in GENERAL_DIMS:
            val = j.get(d) if j else None
            r[d] = val
            r[f"in_input_{d}"] = d in given
            s = spec[d]
            # the family's own critical dimension is scored as Violation/Assumption, not here
            comparable = d != dim and val is not None and s is not None and not (
                d == "certainty" and (val == NA_CERTAINTY or NA_CERTAINTY in s))
            bad = comparable and val not in s
            r[f"contra_{d}"] = bool(bad and d in given) if comparable else None
            r[f"addition_{d}"] = bool(bad and d not in given) if comparable else None
            any_contra |= bool(r[f"contra_{d}"])
            any_add |= bool(r[f"addition_{d}"])
        r["any_contra"], r["any_stance_addition"] = (any_contra, any_add) if j else (None, None)
        r["added_content"] = j.get("added_content") if j else None
        pol, cert = r["politeness"], r["certainty"]
        r["politeness_added"] = None if pol is None else (pol != "none" and spec["politeness"] == {"none"})
        r["hedge_added"] = None if cert is None else (
            cert == "hedged/uncertain" and "hedged/uncertain" not in (spec["certainty"] or ()))
        r["emphatic_added"] = None if cert is None else (
            cert == EMPH and src_l0[var["source"]]["certainty"] != EMPH)
        if r["cue_in_input"]:
            if not o["valid"]:
                r["constraint_preserving"] = False
            elif crit is None:
                r["constraint_preserving"] = None
            else:
                r["constraint_preserving"] = bool(r["critical_match"] and not any_contra)
        else:
            r["constraint_preserving"] = None
        rows.append(r)
    return pd.DataFrame(rows)


def _rate(s: pd.Series):
    s = s.dropna().astype(bool)
    return {"rate": round(float(s.mean()), 3) if len(s) else None, "n": int(len(s))}


def endpoints(df: pd.DataFrame) -> dict:
    ep: dict = {"n_rows": len(df), "n_invalid": int((~df["valid"]).sum()),
                "n_critical_unresolved": int((df["valid"] & df["critical"].isna()).sum()),
                "n_families": int(df["family_id"].nunique())}
    cue = df[df["cue_in_input"]]
    ep["cp1_constraint_preserving"] = {
        f"{m}|{p}|{c}": _rate(g["constraint_preserving"])
        for (m, p, c), g in cue.groupby(["model", "prompt_id", "channel"])}
    ep["violation_by_dim"] = {f"{m}|{d}": _rate(g["violation"])
                              for (m, d), g in cue.groupby(["model", "dimension"])}
    amb = df[df["ambig_channel"]]
    # A and B share bare/noncrit requests: count each (request, suggestion) once.
    amb1 = amb.drop_duplicates(["request_key", "suggestion_idx", "channel", "family_id"])
    ep["cp2_commitment"] = {f"{m}|{p}|{c}": _rate(g["assumption"])
                            for (m, p, c), g in amb1.groupby(["model", "prompt_id", "channel"])}
    dirn = {}
    for (m, d), g in amb1[amb1["committed"] == True].groupby(["model", "dimension"]):  # noqa: E712
        vc = g["chose"].value_counts()
        n = int(vc.get("A", 0) + vc.get("B", 0))
        dirn[f"{m}|{d}"] = {"A": int(vc.get("A", 0)), "B": int(vc.get("B", 0)),
                            "other": int(vc.get("other", 0)),
                            "share_A": round(vc.get("A", 0) / n, 3) if n else None}
    ep["cp2_direction_vs_50pct"] = dirn
    # coverage@3: P2 = 3 suggestions of one response, S3 = 3 samples of one input
    cov = {}
    multi = df[df["prompt_id"].isin(["P2", "S3", "I2", "I2t"]) & df["valid"]]   # I2/I2t: src/interventions.py
    for (m, p, c), g in multi.groupby(["model", "prompt_id", "channel"]):
        hits = []
        for _, s in g.groupby(["family_id", "variant"]):
            ch = set(s["chose"].dropna())
            hits.append(("A" in ch) and ("B" in ch))
        cov[f"{m}|{p}|{c}"] = {"coverage@3": round(sum(hits) / len(hits), 3), "n_sets": len(hits)}
    ep["coverage_at_3"] = cov
    ep["stance_additions"] = {
        f"{m}|{p}": {k: _rate(g[k])["rate"] for k in
                     ["any_stance_addition", "politeness_added", "hedge_added", "emphatic_added"]}
        | {"added_content": round(float((g["added_content"] == "yes").mean()), 3)}
        for (m, p), g in df[df["judged"]].groupby(["model", "prompt_id"])}
    return ep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--items", type=Path, default=None)
    ap.add_argument("--fallback", choices=["J1", "J2"], default=None,
                    help="use this judge variant when J1/J2 disagree and no arbiter label")
    a = ap.parse_args()
    run_dir = Path(a.run) if Path(a.run).exists() else runio.ROOT / "runs" / a.run
    df = score(run_dir, a.items, a.fallback)
    out = run_dir / "scored.parquet"
    df.to_parquet(out, index=False)
    ep = endpoints(df)
    (run_dir / "endpoints.json").write_text(json.dumps(ep, indent=1))
    print(f"wrote {out} ({len(df)} rows) and endpoints.json")
    for k in ("n_rows", "n_invalid", "n_critical_unresolved", "n_families"):
        print(f"  {k}: {ep[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
