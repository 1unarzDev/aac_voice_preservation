"""R5 at the input-builder boundary: validate a *rendered* cue against its claimed source requirement.

The check runs before generation and has no side effects. It decodes only what a model would
see in the rendered input string. It never reads hidden metadata as evidence. It compares the
decoded accepted predicate set with the requirement the builder claims to restore:

  compatible               every value the cue accepts satisfies the requirement (certifiable)
  compatible_but_coarser   overlap, but the cue also accepts values outside the requirement:
                           it cannot supply the finer distinction (e.g. [SURE] vs emphatic)
  conflicting              the cue accepts no value that satisfies the requirement
                           (or several cues for one dimension contradict each other)
  unknown                  the cue or the requirement cannot be decoded soundly: unsupported
                           word/chip, ambiguous word, unclear/unexpressible or non-consensus source
  unchanged_noop           the rendered input is identical to its baseline, so nothing was
                           restored, whatever its compatibility (relation reported separately)

Precedence: conflicting > unchanged_noop > unknown > compatible_but_coarser > compatible.
Only `compatible` certifies that the input supplies the source requirement.

Scope (deliberately narrow): the `Keywords:` wrapper; every chip in labels.CHIP_TO_GENERAL;
and politeness word markers at the coarse "any explicit polite marker" endpoint (please/pls/plz,
thanks/thank/thx, could you / would you, apology `sorry` except after a feeling verb). Any other
word evidence is `unknown`; no linguistic census is attempted.

  python src/validate_cue_inputs.py check --input "Keywords: [MAYBE] extra pillow" \
      --dimension certainty --requires "plain assertion"
  python src/validate_cue_inputs.py replay      # W-B 139-restoration replay -> analysis/r5_validator/
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels import CHIP_TO_GENERAL, EMPH, GENERAL_OPTIONS, PLAIN_A, POLITE_VALUES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ("compatible", "compatible_but_coarser", "conflicting", "unknown", "unchanged_noop")
NONCOMMIT = frozenset({"mixed/unclear", "unclear/mixed", "unclear", "mixed", "unspecified", "other"})
WRAPPER = "Keywords:"
POLITE = frozenset(POLITE_VALUES)
# Word markers supported at the coarse polite-marker endpoint (CB-2; [PLEASE] semantics).
POLITE_WORDS = {"please": "please", "pls": "please", "plz": "please",
                "thanks": "thanks", "thank": "thanks", "thx": "thanks", "sorry": "apology"}
POLITE_BIGRAMS = {("could", "you"), ("would", "you")}
FEELING_VERBS = {"feel", "feels", "felt", "feeling"}   # "feel sorry" may be sympathy, not apology


class CueContractError(ValueError):
    """Raised by require_valid() when a rendered cue may not be sent to generation."""


@dataclass(frozen=True)
class Requirement:
    """The source requirement a builder claims the rendered input restores."""
    dimension: str
    value: str | None
    basis: str = "panel_consensus"   # or "detector_fallback" (source coders disagreed)


@dataclass
class Verdict:
    verdict: str
    relation: str                       # compatible / coarser / conflicting / unknown
    dimension: str
    required: list | None
    accepted: list | None
    evidence: list = field(default_factory=list)
    changed: bool | None = None
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def certifies_source(self) -> bool:
        return self.verdict == "compatible"

    def to_dict(self):
        return {**asdict(self), "certifies_source": self.certifies_source}


def requirement_set(dimension: str, value: str | None) -> frozenset | None:
    """Output values that honour the source requirement, mirroring wb_report.honours()."""
    if value is None or value in NONCOMMIT or value not in GENERAL_OPTIONS.get(dimension, ()):
        return None
    if dimension == "certainty" and value == PLAIN_A:
        return frozenset({PLAIN_A, EMPH})
    if dimension == "politeness" and value in POLITE:
        return POLITE
    return frozenset({value})


def _norm(text: str) -> str:
    return " ".join(text.replace("’", "'").split())


def decode(rendered: str) -> dict:
    """Decode the visible cue. Returns {'ok', 'dims': {dim: (accepted|None, evidence)}, 'unsupported', 'conflicts'}."""
    text = _norm(rendered)
    if not text.startswith(WRAPPER):
        return dict(ok=False, dims={}, unsupported=[], conflicts=[],
                    reason=f"unsupported wrapper (expected '{WRAPPER} ...'); full-text inputs are out of scope")
    body = text[len(WRAPPER):].strip()
    chips = re.findall(r"\[[^\]]+\]", body)
    words = [w for w in re.sub(r"\[[^\]]+\]", " ", body).lower().split()]
    dims: dict[str, list] = {}
    unsupported, ambiguous = [], []
    for chip in chips:
        if chip in CHIP_TO_GENERAL:
            d, vals = CHIP_TO_GENERAL[chip]
            dims.setdefault(d, []).append((frozenset(vals), chip))
        else:
            unsupported.append(chip)
    for i, w in enumerate(words):
        prev = words[i - 1] if i else None
        if w in POLITE_WORDS:
            if w == "sorry" and prev in FEELING_VERBS:
                ambiguous.append(f"{prev} {w}")
                continue
            dims.setdefault("politeness", []).append((POLITE, w))
        if i + 1 < len(words) and (w, words[i + 1]) in POLITE_BIGRAMS:
            dims.setdefault("politeness", []).append((POLITE, f"{w} {words[i + 1]}"))
    out, conflicts = {}, []
    for d, items in dims.items():
        acc = frozenset.intersection(*[v for v, _ in items])
        if not acc:
            conflicts.append(d)
        out[d] = (acc, [e for _, e in items])
    return dict(ok=True, dims=out, unsupported=unsupported, conflicts=conflicts,
                ambiguous=ambiguous, words=words, chips=chips)


def validate(rendered: str, requirement: Requirement, baseline: str | None = None,
             metadata_commitments: list | None = None) -> Verdict:
    """Pure function: no I/O, no model or network calls, inputs are never modified."""
    d = requirement.dimension
    req = requirement_set(d, requirement.value)
    dec = decode(rendered)
    reasons, warnings = [], []
    accepted, evidence = (dec["dims"].get(d) or (None, [])) if dec["ok"] else (None, [])
    if not dec["ok"]:
        reasons.append(dec["reason"])
    elif d in dec["conflicts"]:
        reasons.append(f"rendered cues for {d} contradict each other: {evidence}")
    elif accepted is None:
        why = []
        if dec["ambiguous"]:
            why.append("ambiguous word marker(s) " + ", ".join(repr(a) for a in dec["ambiguous"]))
        if dec["unsupported"]:
            why.append("unsupported chip(s) " + ", ".join(dec["unsupported"]))
        reasons.append(f"no decodable {d} cue in the rendered input" + (f" ({'; '.join(why)})" if why else
                       "; word evidence for this dimension is outside the supported scope"))
    # Relation between the decoded cue and the claimed requirement.
    if dec["ok"] and d in dec["conflicts"]:
        relation = "conflicting"
    elif accepted is None:
        relation = "unknown"
    elif req is None:
        relation = "unknown"
        reasons.append(f"source requirement {requirement.value!r} for {d} is unclear/unexpressible or not a {d} option")
    elif not (accepted & req):
        relation = "conflicting"
        reasons.append(f"cue accepts {sorted(accepted)}, disjoint from the required {sorted(req)}")
    elif accepted <= req:
        relation = "compatible"
    else:
        relation = "compatible_but_coarser"
        reasons.append(f"cue also accepts {sorted(accepted - req)}; it cannot supply the finer required "
                       f"distinction {sorted(req)}")
    if requirement.basis != "panel_consensus" and relation != "conflicting":
        reasons.append(f"requirement basis is {requirement.basis!r} (no source consensus); provisional "
                       f"relation {relation!r} is not certifiable")
        relation_for_verdict = "unknown"
    else:
        relation_for_verdict = relation
    changed = None if baseline is None else _norm(rendered) != _norm(baseline)
    if relation == "conflicting" and requirement.basis == "panel_consensus":
        verdict = "conflicting"
    elif changed is False:
        verdict = "unchanged_noop"
        reasons.append("rendered input is identical to its baseline; nothing was restored")
    else:
        verdict = relation_for_verdict if relation_for_verdict != "conflicting" else "unknown"
    if metadata_commitments is not None and dec["ok"]:
        hidden = [c for c in metadata_commitments if c not in dec["chips"]]
        if hidden:
            warnings.append(f"metadata commitments {hidden} are not visible in the rendered input; ignored")
    return Verdict(verdict=verdict, relation=relation, dimension=d,
                   required=sorted(req) if req is not None else None,
                   accepted=sorted(accepted) if accepted is not None else None,
                   evidence=list(evidence), changed=changed, reasons=reasons, warnings=warnings)


def require_valid(rendered: str, requirement: Requirement, baseline: str | None = None,
                  allow_coarser: bool = False) -> Verdict:
    """Builder hook: raise before generation unless the cue is certifiably compatible."""
    v = validate(rendered, requirement, baseline)
    ok = v.verdict == "compatible" or (allow_coarser and v.verdict == "compatible_but_coarser")
    if not ok:
        raise CueContractError(f"{v.verdict}: {rendered!r} vs {requirement.dimension}={requirement.value!r}: "
                               + "; ".join(v.reasons))
    return v


# ---------------------------------------------------------------- W-B replay (read-only inputs)

def _expected_from_audit(row) -> str:
    """Map the frozen audit's inventory row to the validator class it implies."""
    if row["status"] == "definite_conflict":
        return "conflicting"
    if str(row["changed_visible_input"]) == "False":
        return "unchanged_noop"
    if row["status"] != "aligned":
        return "unknown"
    if row["relation"] == "coarsened_SURE_plain_or_emphatic":
        return "compatible_but_coarser"
    return "compatible"


def replay(out_dir: Path) -> dict:
    import hashlib
    import pandas as pd

    def sha(p):
        return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    inputs = ["data/items/wb.jsonl", "runs/requests/wb1.jsonl", "runs/wb1/outputs.jsonl",
              "analysis/wb/contract_audit_inventory.csv", "analysis/wb/contract_audit.json"]
    before = {p: sha(p) for p in inputs}
    audit = pd.read_csv(ROOT / "analysis/wb/contract_audit_inventory.csv").set_index("family_id")
    items = {json.loads(l)["family_id"]: json.loads(l) for l in (ROOT / "data/items/wb.jsonl").read_text().splitlines() if l.strip()}
    stored = {}
    for line in (ROOT / "runs/wb1/outputs.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("channel") == "restored":
            stored.setdefault(r["family_id"], set()).add(r["input_text"])
    rows = []
    for fid in sorted(audit.index):
        it, a = items[fid], audit.loc[fid]
        d = it["focal_dim"]
        ch = it["custom_channels"]["A"]
        rendered, baseline = ch["restored"]["input"], ch["pos_cap4"]["input"]
        assert stored[fid] == {rendered}, (fid, "rendered input differs from the stored historical request")
        assert rendered == a["input_text"]
        req = Requirement(d, it["variants"]["A"]["general_spec"][d],
                          "panel_consensus" if it["value_source"][d] == "panel" else "detector_fallback")
        v = validate(rendered, req, baseline, ch["restored"]["commitments"])
        expected = _expected_from_audit(a)
        rows.append(dict(family_id=fid, sample=it["sample"], mode=it["restoration"]["mode"], dimension=d,
                         rendered_input=rendered, baseline_input=baseline, claimed_value=req.value,
                         claim_basis=req.basis, accepted=json.dumps(v.accepted), required=json.dumps(v.required),
                         relation=v.relation, verdict=v.verdict, certifies_source=v.certifies_source,
                         changed=v.changed, reasons=" | ".join(v.reasons), warnings=" | ".join(v.warnings),
                         audit_status=a["status"], audit_relation=a["relation"],
                         audit_changed_visible_input=a["changed_visible_input"],
                         audit_accepted=a["visible_accepted_general_values"], expected_from_audit=expected,
                         agrees_with_audit=v.verdict == expected))
    df = pd.DataFrame(rows)
    after = {p: sha(p) for p in inputs}
    assert before == after, "replay must not change historical inputs"
    conflicts = df[df.audit_status.eq("definite_conflict")]
    sure = df[df.audit_relation.eq("coarsened_SURE_plain_or_emphatic")]
    words = df[df["mode"].eq("word")]
    summary = dict(
        n=len(df), verdicts=df.verdict.value_counts().to_dict(),
        verdict_by_mode=df.groupby(["mode", "verdict"]).size().rename("n").reset_index().to_dict("records"),
        agrees_with_audit=int(df.agrees_with_audit.sum()),
        accepted_set_agrees_with_audit=int((df.accepted == df.audit_accepted.where(df.audit_accepted.notna(), "null")).sum()),
        known_conflicts_rejected=int(conflicts.verdict.eq("conflicting").sum()), known_conflicts=len(conflicts),
        sure_granularity_flagged=int(sure.verdict.eq("compatible_but_coarser").sum()), sure_cases=len(sure),
        coarse_certified=int(sure.certifies_source.sum()),
        word_cases=words[["family_id", "rendered_input", "claimed_value", "verdict", "relation", "audit_status"]]
            .to_dict("records"),
        unknown_reasons=df[df.verdict.eq("unknown")].groupby("audit_status").size().to_dict(),
        certified=int(df.certifies_source.sum()),
        hidden_metadata_warnings=int(df.warnings.ne("").sum()),
        input_sha256=before, inputs_unchanged=True, generation_calls=0, judge_calls=0)
    assert summary["agrees_with_audit"] == 139 and summary["known_conflicts_rejected"] == 7 == summary["known_conflicts"]
    assert summary["accepted_set_agrees_with_audit"] == 139
    assert summary["sure_granularity_flagged"] == 8 and summary["coarse_certified"] == 0
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "replay.csv", index=False)
    (out_dir / "replay.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    write_readme(out_dir, df, summary)
    return summary


def write_readme(out_dir: Path, df, s: dict) -> None:
    """Short artifact example; every string/count below is read from the replay table."""
    audit = json.loads((ROOT / "analysis/wb/contract_audit.json").read_text())
    ex = audit["example"]
    v = s["verdicts"]

    def table(frame, cols, heads):
        lines = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(heads)]
        for r in frame[cols].itertuples(index=False):
            lines.append("| " + " | ".join(f"`{x}`" if i == 1 else str(x) for i, x in enumerate(r)) + " |")
        return "\n".join(lines)
    short = df.assign(family=df.family_id.str.removeprefix("wb-aactext-"))
    conf = short[short.verdict.eq("conflicting")]
    sure = short[short.verdict.eq("compatible_but_coarser")]
    unk = short[short.verdict.eq("unknown")].copy()
    unk["why"] = [("source coders disagree; detector fallback " + repr(c)) if b == "detector_fallback" else
                  ("unclear/mixed source reference" if c == "mixed/unclear" else "word cue outside supported scope")
                  for c, b in zip(unk.claimed_value, unk.claim_basis)]
    noop = short[short.verdict.eq("unchanged_noop")]
    text = f"""# R5 input-builder validator: what it rejects before generation

`src/validate_cue_inputs.py` is a side-effect-free check for the **input-builder boundary** (cycle-3 Action 5, R5).
It decodes only the *rendered* input a model would see, never hidden metadata, and compares the accepted
predicate set with the source requirement the builder claims to restore. Only `compatible` certifies the source.
Tests: `.venv/bin/python -m unittest tests.test_validate_cue_inputs`. Replay (writes only this directory):
`OPENBLAS_NUM_THREADS=1 .venv/bin/python src/validate_cue_inputs.py replay`. **0 generator / 0 judge calls.**

```text
$ .venv/bin/python src/validate_cue_inputs.py check --dimension certainty --requires "plain assertion" \\
      --input "{conf.rendered_input.iloc[0]}"
verdict: conflicting   accepted: ['hedged/uncertain']   required: ['plain assertion', 'strongly certain/emphatic']
exit status 2 (reject before generation); builder hook: require_valid(...) raises CueContractError
```

## Replay of the frozen W-B restoration inventory

All **{s['n']}** restored inputs (131 chips + 8 words) from `data/items/wb.jsonl`, each equal to its stored
`runs/wb1` request input, against the claimed source requirement in the item's `general_spec` (basis: panel
consensus or detector fallback). The verdict equals the class implied by the frozen
[contract audit](../wb/contract_audit.md) for **{s['agrees_with_audit']}/{s['n']}** inputs, and the decoded accepted
set equals the audit's for **{s['accepted_set_agrees_with_audit']}/{s['n']}**. Input hashes are identical before and
after; no historical request was rebuilt.

| verdict | inputs |
|---|---|
""" + "\n".join(f"| {k} | {v.get(k, 0)} |" for k in VERDICTS) + f"""

**Rejected as conflicting: {s['known_conflicts_rejected']}/{s['known_conflicts']} known definite conflicts** (none escapes).
In the five `[MAYBE]` cases, stored outputs followed the visible chip and failed the source in
{ex['k']}/{ex['n']} outputs ({ex['message_clusters']} messages); the validator would have stopped those requests
before generation.

{table(conf, ['family', 'rendered_input', 'claimed_value', 'accepted'], ['family', 'rendered input', 'claimed source', 'cue accepts'])}

**Compatible but coarser: {s['sure_granularity_flagged']}/{s['sure_cases']} `[SURE]` cases.** D-007 lets `[SURE]` accept plain
*or* emphatic, so the chip cannot supply the emphatic source distinction; {s['coarse_certified']} are certified.

{table(sure, ['family', 'rendered_input', 'claimed_value'], ['family', 'rendered input', 'claimed source'])}

**Unknown: {v.get('unknown', 0)}**, never certified. Unclear references and non-consensus sources stay unknown
even when the chip would map; an uncertain word stays unknown.

{table(unk, ['family', 'rendered_input', 'why'], ['family', 'rendered input', 'reason'])}

**Unchanged/no-op: {v.get('unchanged_noop', 0)}** word restorations are byte-identical to their POS-cap4 baseline
(relation shown separately; `feel sorry` is also unknown). Seven word records carry a hidden metadata
`[PLEASE]` that is not visible; the validator warns and ignores it.

{table(noop, ['family', 'rendered_input', 'relation'], ['family', 'rendered input', 'relation if it had changed'])}

## Boundary

The supported scope is narrow by design: the `Keywords:` wrapper, every chip in `labels.CHIP_TO_GENERAL`, and
politeness word markers at the coarse polite-marker endpoint. Any other word evidence, full-text input, unsupported chip,
unclear or unexpressible reference, or non-consensus source is `unknown`. This is a requirement check against
machine-assessed W-B source labels, not human-validated ground truth or a semantic-equivalence guarantee.
It is demonstrated on historical inputs; it was not part of the original W-B generation.
"""
    (out_dir / "README.md").write_text(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate one rendered input")
    c.add_argument("--input", required=True)
    c.add_argument("--dimension", required=True, choices=list(GENERAL_OPTIONS))
    c.add_argument("--requires", default=None, help="claimed source value (omit if unknown)")
    c.add_argument("--basis", default="panel_consensus", choices=["panel_consensus", "detector_fallback"])
    c.add_argument("--baseline", default=None)
    r = sub.add_parser("replay", help="replay the frozen W-B restoration inventory")
    r.add_argument("--out", type=Path, default=ROOT / "analysis/r5_validator")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        v = validate(a.input, Requirement(a.dimension, a.requires, a.basis), a.baseline)
        print(json.dumps(v.to_dict(), indent=1))
        return 0 if v.certifies_source else 2
    print(json.dumps({k: v for k, v in replay(a.out).items() if k != "word_cases"}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
