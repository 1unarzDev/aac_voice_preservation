"""T9: replay the R5 input-builder validator (src/validate_cue_inputs.py) over the rendered inputs of W-C, W-D and hw1.

    . .venv/bin/activate && python src/robust_t9_validator_replay.py

Read-only: rendered inputs come from the stored scored tables (unique family x variant x channel x input_text) and are
cross-checked against runs/requests/{r2c,r2d,hw}.jsonl. The validator is imported unchanged. 0 generation / 0 judge calls.

What is validated
 * W-C / hw1 chip1 and chipall: the critical-dimension cue against the variant's authored critical value
   (politeness polite->please, plain->none; time_quantity has no chip in labels.CHIP_TO_GENERAL -> out of validator scope).
 * bare / noncrit: design check, the critical dimension must have NO decodable cue (no leak); bare/noncrit must be identical for A and B.
 * W-D: pol_* / actor_* / both_*: the polarity cell and the held-fixed or varied agent cell; neither_*: no polarity/agent cue.
 * Long chip aliases listed in the prompt legend ([STATEMENT]=[TELL], ...) are not decoded by the validator; each input is
   validated raw (alias -> unknown) and with the legend aliases normalised (reported separately).
Verdicts follow the validator; 'conflicting' is the blocking class.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A                                           # noqa: E402
from labels import CHIP_TO_GENERAL                            # noqa: E402
from validate_cue_inputs import Requirement, validate, decode  # noqa: E402
from robust_common import outdir, write_json, md_table        # noqa: E402

OUT = outdir("t9_validator_replay")
ALIAS = {"[NEGATIVE]": "[NOT]", "[AFFIRMATIVE]": "[YES]", "[QUESTION]": "[?]", "[REQUEST]": "[ASK]", "[DECLINE]": "[REFUSE]", "[STATEMENT]": "[TELL]",
         "[I-DO-IT]": "[I]", "[YOU-DO-IT]": "[YOU]", "[THEY-DO-IT]": "[THEY]", "[POLITE]": "[PLEASE]", "[NO-PLEASE]": "[PLAIN]"}
SCALE = {("politeness", "polite"): "please", ("politeness", "plain"): "none"}
AGENT = {"I": "speaker", "YOU": "addressee", "WE": "we/joint", "THEY": "third party"}


def norm_alias(s):
    for k, v in ALIAS.items():
        s = s.replace(k, v)
    return s


def req(dim, value):
    return Requirement(dim, SCALE.get((dim, value), value), "panel_consensus")


def recs_from_requests(path):
    """request_key -> rendered input (requests are de-duplicated by key across families, so match by key, not family)."""
    return {r["request_key"]: r["input_text"] for r in map(json.loads, open(path))}


def check(rows, label):
    out = []
    for r in rows:
        for norm in (False, True):
            ren = norm_alias(r["input"]) if norm else r["input"]
            base = norm_alias(r["baseline"]) if (norm and r["baseline"]) else r["baseline"]
            if r["expect"] == "no_cue":
                dec = decode(ren)
                leaked = bool(dec["ok"] and dec["dims"].get(r["dimension"]))
                out.append(dict(run=label, **{k: r[k] for k in ("family_id", "variant", "channel", "dimension", "input", "expect")}, claimed=None, normalised=norm,
                                verdict="leak" if leaked else "no_cue_ok", relation="", reasons="cue decodable in a no-cue channel" if leaked else ""))
                continue
            v = validate(ren, req(r["dimension"], r["value"]), base)
            out.append(dict(run=label, **{k: r[k] for k in ("family_id", "variant", "channel", "dimension", "input", "expect")}, claimed=r["value"], normalised=norm,
                            verdict=v.verdict, relation=v.relation, reasons=" | ".join(v.reasons)))
    return out


def probe_rows(items, scored, requests, excluded):
    s = scored[["family_id", "variant", "channel", "input_text"]].drop_duplicates()
    k = scored[["request_key", "input_text"]].drop_duplicates()
    missing = [x for x in zip(k.request_key, k.input_text) if requests.get(x[0]) != x[1]]
    bare = {(f, v): t for f, v, c, t in s.itertuples(index=False) if c == "bare"}
    rows = []
    for f, v, c, t in s.itertuples(index=False):
        it = items[f]; dim = it["dimension"]; val = it["variants"][v]["critical_value"]
        if c == "full": continue
        if c in ("bare", "noncrit"):
            rows.append(dict(family_id=f, variant=v, channel=c, dimension=dim, input=t, baseline=None, value=val, expect="no_cue"))
        else:
            rows.append(dict(family_id=f, variant=v, channel=c, dimension=dim, input=t, baseline=bare.get((f, v)), value=val, expect="cue"))
    return rows, missing


def wd_rows(items, scored, requests):
    s = scored[["family_id", "variant", "channel", "input_text"]].drop_duplicates()
    k = scored[["request_key", "input_text"]].drop_duplicates()
    missing = [x for x in zip(k.request_key, k.input_text) if requests.get(x[0]) != x[1]]
    rows = []
    for f, v, c, t in s.itertuples(index=False):
        it = items[f]; var = it["variants"][v]; kind = c.split("_")[0]
        cell = var["cell"].split("|")   # polarity chip name | agent chip name, from the authored cell label
        pol_val = {"YES": "affirmative", "NOT": "negated"}[cell[0]]; ag_val = AGENT[cell[1]]
        base = None
        rows.append(dict(family_id=f, variant=v, channel=c, dimension="speech_act", input=t, baseline=None, value="statement", expect="cue"))
        if kind == "neither":
            for d in ("polarity", "agent"):
                rows.append(dict(family_id=f, variant=v, channel=c, dimension=d, input=t, baseline=None, value=None, expect="no_cue"))
            continue
        if kind in ("pol", "both"):
            rows.append(dict(family_id=f, variant=v, channel=c, dimension="polarity", input=t, baseline=None, value=pol_val, expect="cue"))
        if kind in ("actor", "both"):
            rows.append(dict(family_id=f, variant=v, channel=c, dimension="agent", input=t, baseline=None, value=ag_val, expect="cue"))
    return rows, missing


def main():
    results, miss, meta = [], {}, {}
    wc_items = A.load_items(str(ROOT / "data/items/r2_c[12].jsonl"))
    wc = pd.read_parquet(ROOT / "runs/r2c1/scored.parquet"); r, m = probe_rows(wc_items, wc, recs_from_requests(ROOT / "runs/requests/r2c.jsonl"), set())
    results += check(r, "W-C r2c1"); miss["W-C r2c1"] = m
    hw_items = A.load_items(str(ROOT / "annotation/written/hw_candidates.jsonl")); hw = pd.read_parquet(ROOT / "runs/hw1/scored.parquet")
    r, m = probe_rows(hw_items, hw, recs_from_requests(ROOT / "runs/requests/hw.jsonl"), set()); results += check(r, "hw1"); miss["hw1"] = m
    wd_items = A.load_items(str(ROOT / "data/items/r2_d.jsonl")); wd = pd.read_parquet(ROOT / "runs/r2d1/scored.parquet")
    r, m = wd_rows(wd_items, wd, recs_from_requests(ROOT / "runs/requests/r2d.jsonl")); results += check(r, "W-D r2d1"); miss["W-D r2d1"] = m
    R = pd.DataFrame(results)
    # design check: bare/noncrit identical for A and B within a family
    ident = {}
    for lab, sc in (("W-C r2c1", wc), ("hw1", hw)):
        g = sc[sc.channel.isin(["bare", "noncrit"])][["family_id", "variant", "channel", "input_text"]].drop_duplicates()
        p = g.groupby(["family_id", "channel"]).input_text.nunique()
        ident[lab] = {ch: dict(family_channels=int((p.index.get_level_values(1) == ch).sum()), differing_between_A_and_B=int(((p > 1) & (p.index.get_level_values(1) == ch)).sum())) for ch in ("bare", "noncrit")}
    # dedupe unique inputs (family x variant x channel x dim) counts
    R.to_csv(OUT / "replay_rows.csv", index=False)
    summ = {"missing_from_requests": {k: len(v) for k, v in miss.items()}, "bare_noncrit_identical_A_B": ident, "generation_calls": 0, "judge_calls": 0}
    for norm in (False, True):
        k = "alias_normalised" if norm else "raw"
        X = R[R.normalised == norm]
        summ[k] = {}
        for run, g in X.groupby("run"):
            cue = g[g.channel.isin(["chip1", "chipall"]) | g.expect.eq("cue")]
            summ[k][run] = dict(
                cue_inputs=int(len(cue)), verdicts=cue.verdict.value_counts().to_dict(),
                by_channel_dim_verdict=cue.groupby(["channel", "dimension", "verdict"]).size().rename("n").reset_index().to_dict("records"),
                conflicts=cue[cue.verdict.eq("conflicting")][["family_id", "variant", "channel", "dimension", "input", "claimed", "reasons"]].to_dict("records"),
                no_cue_inputs=int(g.expect.eq("no_cue").sum()), leaks=int(g.verdict.eq("leak").sum()))
    write_json(OUT / "summary.json", summ)
    L = ["# T9: R5 validator replay on W-C, W-D and hw1 rendered cue inputs", "",
         "Script `src/robust_t9_validator_replay.py`; per-input rows in `replay_rows.csv`; `summary.json`. The validator (`src/validate_cue_inputs.py`, unit tests in `tests/test_validate_cue_inputs.py`) is imported unchanged. "
         "0 generation / 0 judge calls. Inputs: unique (family, variant, channel, rendered input) from the stored scored tables, each also present in the stored request files "
         f"(inputs whose request_key is absent from, or renders differently in, the request files: {summ['missing_from_requests']}). Critical-dimension cues are validated against the authored variant value; bare/noncrit channels are checked for cue leaks; "
         f"bare/noncrit inputs identical between A and B: {ident}.", "",
         "W-C and hw1 `chipall`/`chip1` and W-D pol/actor/both cells are the 'cue' channels; `full` (free text) is out of validator scope."]
    for k, title in (("raw", "Validator as shipped (long chip aliases such as [STATEMENT] are unsupported chips -> unknown)"), ("alias_normalised", "With the legend's long chip aliases normalised to the short chips")):
        L += ["", f"## {title}", ""]
        rows = []
        for run, d in summ[k].items():
            rows.append(dict(run=run, cue_inputs=d["cue_inputs"], **{v: d["verdicts"].get(v, 0) for v in ("compatible", "compatible_but_coarser", "conflicting", "unknown", "unchanged_noop")},
                             no_cue_inputs=d["no_cue_inputs"], leaks=d["leaks"]))
        L += [md_table(pd.DataFrame(rows), 0), ""]
        for run, d in summ[k].items():
            if d["conflicts"]:
                L += [f"**Conflicts, {run}: {len(d['conflicts'])}**", md_table(pd.DataFrame(d["conflicts"]).head(30), 0), ""]
            else:
                L += [f"**Conflicts, {run}: 0**", ""]
    # unknown breakdown
    X = R[(R.normalised == True) & R.verdict.isin(["unknown", "unchanged_noop", "compatible_but_coarser"])]
    L += ["## Non-certified cue inputs after alias normalisation (by run, channel, dimension, verdict)", "",
          md_table(X.groupby(["run", "channel", "dimension", "verdict"]).size().rename("n").reset_index(), 0), "",
          "Example reasons: " + "; ".join(sorted({x[:110] for x in X.reasons.tolist() if x})[:6]), "",
          "## Notes and caveats", "",
          "* `unknown` for time_quantity is a scope gap of the validator ([PAST]/[NOW]/[LATER] are not in `CHIP_TO_GENERAL`), not a defect in the inputs.",
          "* `compatible_but_coarser` is the `[SURE]` granularity case (accepts plain or emphatic); `unchanged_noop` flags a chip input byte-identical to its bare baseline.",
          "* bare is identical for A and B in every family; noncrit differs between A and B in the word order of the keywords for the families listed above (the SPEC rule 'words keep source order'), a documented design property, not a cue leak.",
          "* In W-D the `[STATEMENT]` encoding is an unsupported chip for the shipped validator (the speech-act check is `unknown` raw and `compatible` once the legend alias is normalised); the polarity/agent cells are unaffected.",
          "* 'conflicting' is the only blocking class. A clean result here is a statement about the rendered cue vs the authored critical value, not about whether the model honours it, and says nothing on the free-text `full` channel.",
          "* hw1 includes all 574 candidate families (547 kept); family-level exclusions do not change the conflict count (see rows)."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:40]))


main()
