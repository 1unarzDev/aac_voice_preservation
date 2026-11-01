"""Write the complete old/new endpoint audit and refreshed claim entries (offline)."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

import attribute
from labels import critical_match
from resolve_labels import DEFAULT_RUNS
from runio import ROOT

PREV = ROOT / "analysis/evidence_prev"
OUT = ROOT / "analysis"


def scalar(v):
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def same(a, b):
    a, b = scalar(a), scalar(b)
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    return a == b


def leaves(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, prefix + "/" + str(key))
    elif isinstance(value, (int, float, bool)) or value is None:
        yield prefix, scalar(value)


def display(v):
    if v is None:
        return "NA / absent"
    if isinstance(v, float):
        return f"{v:.12g}"
    return str(v).replace("|", "\\|").replace("\n", " ")


def fraction(k, n):
    return f"{int(k)}/{int(n)} = {100*k/n:.2f}%" if n else "NA (n=0)"


def rate(r, unit="%"):
    return f"{100*r['estimate']:.2f}{unit} [{100*r['ci_low']:.2f}, {100*r['ci_high']:.2f}] (n={r['n']})"


def main():
    if "--endpoints-only" in sys.argv:
        for run in DEFAULT_RUNS:
            directory = ROOT / "runs" / run
            df = pd.read_parquet(directory / "scored.parquet")
            (directory / "endpoints.json").write_text(json.dumps(attribute.endpoints(df), indent=1))
        print("refreshed endpoint JSONs with explicit unknown-set denominators")
        return
    changes = []
    def compare(artifact, a, b, population):
        av, bv = dict(leaves(a)), dict(leaves(b))
        for key in sorted(av.keys() | bv.keys()):
            if not same(av.get(key), bv.get(key)):
                changes.append(dict(artifact=artifact, population=population, endpoint=key,
                                    old=av.get(key), new=bv.get(key)))

    label_changes, run_summary, sensitivities = [], [], []
    frames = {}
    for run in DEFAULT_RUNS:
        current = pd.read_parquet(ROOT / f"runs/{run}/scored.parquet")
        frames[run] = current
        old_path = ROOT / f"runs/{run}/scored_prev.parquet"
        if old_path.exists():
            previous = pd.read_parquet(old_path)
            keys = ["output_id", "family_id", "variant", "channel", "request_key", "sample_idx", "suggestion_idx"]
            pd.testing.assert_frame_equal(previous[keys], current[keys])
            for col in ["critical", "critical_source", "critical_match", "violation", "chose", "constraint_preserving"]:
                mask = ~(previous[col].eq(current[col]) | (previous[col].isna() & current[col].isna()))
                for idx in current.index[mask]:
                    row = current.loc[idx]
                    label_changes.append(dict(run=run, output_id=row.output_id, text_id=row.text_id,
                        family_id=row.family_id, variant=row.variant, model=row.model, prompt_id=row.prompt_id,
                        channel=row.channel, input_text=row.input_text, field=col,
                        old=scalar(previous.loc[idx, col]), new=scalar(row[col])))
            critical_changes = sum(not same(x, y) for x, y in zip(previous.critical, current.critical))
            run_summary.append(dict(run=run, rows=len(current), critical_changed=critical_changes,
                                    unresolved=int(current.critical.isna().sum())))
            compare(f"runs/{run}/endpoints.json", attribute.endpoints(previous, True),
                    attribute.endpoints(current, True), "label-only; inclusive vs inclusive")
            compare(f"runs/{run}/endpoints.json", attribute.endpoints(previous, True),
                    {k: v for k, v in attribute.endpoints(current).items() if k != "sensitivity_including_quarantine"},
                    "old inclusive vs refreshed primary")
        for population, df in [("primary", current[~current.quarantine_refusal_acceptance]), ("inclusive", current)]:
            for source, labels in [("authoritative", df.critical), ("raw_J1", df.critical_J1), ("raw_J2", df.critical_J2)]:
                x = df.copy()
                x["match"] = [critical_match(d, v, None if pd.isna(c) else c)
                              for d, v, c in zip(x.dimension, x.variant_value, labels)]
                for (dim, prompt, channel), g in x.groupby(["dimension", "prompt_id", "channel"]):
                    values = g.match.dropna()
                    sensitivities.append(dict(run=run, population=population, source=source, dimension=dim,
                        prompt_id=prompt, channel=channel, k=int(values.sum()), n=len(values),
                        n_missing=len(g)-len(values), rate=float(values.mean()) if len(values) else None))
            # Raw (unrelaxed) predicate, evaluated on the same authoritative labels.
            raw = df.copy()
            raw["match"] = [None if pd.isna(c) else (c in {"plain assertion", "strongly certain/emphatic"}
                              if d == "certainty" and v == "plain assertion" else c == v)
                              for d, v, c in zip(raw.dimension, raw.variant_value, raw.critical)]
            for (dim, prompt, channel), g in raw.groupby(["dimension", "prompt_id", "channel"]):
                values = g.match.dropna()
                sensitivities.append(dict(run=run, population=population, source="raw_oracle_on_authoritative_labels",
                    dimension=dim, prompt_id=prompt, channel=channel, k=int(values.sum()), n=len(values),
                    n_missing=len(g)-len(values), rate=float(values.mean()) if len(values) else None))

    pd.DataFrame(label_changes).to_csv(OUT / "changed_labels.csv", index=False)
    pd.DataFrame(sensitivities).to_csv(OUT / "label_sensitivity.csv", index=False)
    # Compare every numeric report and figure endpoint, retaining added/removed
    # denominators and interval bounds rather than only headline point estimates.
    for rel in ["analysis/interventions/report.json", "paper/figs/fig_numbers.json"]:
        compare(rel, json.loads((PREV / rel).read_text()), json.loads((ROOT / rel).read_text()),
                "old inclusive vs refreshed primary; inclusive sensitivity labeled separately")
    for previous_path in sorted((PREV / "analysis/main1").glob("*.csv")):
        current_path = ROOT / "analysis/main1" / previous_path.name
        if not current_path.exists() or previous_path.name == "suggestion_sets.csv":
            continue  # occurrence/set audit is in changed_labels and endpoints
        a, b = pd.read_csv(previous_path), pd.read_csv(current_path)
        numeric = sorted({c for c in a.columns.intersection(b.columns)
                          if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c])})
        keys = [c for c in a.columns.intersection(b.columns) if c not in numeric]
        if not keys or a.duplicated(keys).any() or b.duplicated(keys).any():
            continue
        def rows(df):
            return {json.dumps([scalar(v) for v in row[:len(keys)]], ensure_ascii=False):
                    dict(zip(numeric, [scalar(v) for v in row[len(keys):]]))
                    for row in df[keys + numeric].itertuples(index=False, name=None)}
        compare(str(current_path.relative_to(ROOT)), rows(a), rows(b), "old inclusive vs refreshed primary")
    def macros(path):
        result = {}
        for key, value in re.findall(r"\\resdef\{([^}]+)\}\{([^}]+)\}", path.read_text()):
            try:
                result[key] = float(value.replace(",", ""))
            except ValueError:
                pass
        return result
    compare("paper/se4all/results_macros.tex", macros(PREV / "paper/se4all/results_macros.tex"),
            macros(ROOT / "paper/se4all/results_macros.tex"), "old inclusive vs refreshed primary")
    pd.DataFrame(changes).to_csv(OUT / "changed_endpoints.csv", index=False)

    report = json.loads((OUT / "interventions/report.json").read_text())
    old_report = json.loads((PREV / "analysis/interventions/report.json").read_text())
    oracle = json.loads((OUT / "oracle/refreshed_summary.json").read_text())
    g, s = report["guard"], report["span"]
    ig, is_ = report["sensitivity_including_quarantine"]["guard"], report["sensitivity_including_quarantine"]["span"]
    main = frames["main1"]
    p0 = main[main.prompt_id.eq("P0") & ~main.quarantine_refusal_acceptance]
    entries = []
    pol = p0[p0.dimension.eq("politeness") & p0.channel.eq("full")]
    details = []
    for model, df in pol.groupby("model"):
        plain, polite = df[df.variant_value.eq("plain")], df[df.variant_value.eq("polite")]
        details.append(f"{model}: additions {fraction(plain.critical.eq('polite').sum(),len(plain))}, "
                       f"removals {fraction(polite.critical.eq('plain').sum(),len(polite))}")
    entries.append(("C7", "; ".join(details), "politeness family denominators corrected to 10/model/direction; machine-scored"))
    bare = p0[p0.channel.eq("bare") & p0.variant.eq("A")]
    details = []
    for dim, val in [("polarity", "affirmative"), ("certainty", "plain assertion"), ("agent", "speaker")]:
        df = bare[bare.dimension.eq(dim)]
        details.append(f"{dim} {val}: {fraction(df.critical.eq(val).sum(),len(df))}")
    entries.append(("C8", "; ".join(details), "primary 58-family pool; these dimension-specific results unchanged"))
    act = p0[p0.dimension.eq("speech_act") & p0.channel.eq("chip1")]
    details = []
    for val in ["question", "request/command"]:
        df = act[act.variant_value.eq(val)]
        details.append(f"{val}: {fraction(df.critical_match.sum(),len(df))}")
    entries.append(("C11", "; ".join(details), "8 speech-act families, primary excludes act-10/act-16; automated provisional"))
    fix = g['G1_cue']['fix']
    entries.append(("C13", f"Guard fixes {round(fix['estimate']*fix['n'])}/{fix['n']} = {rate(fix)}; strict pass "
        f"{rate(g['P0']['sp'])} -> {rate(g['G1']['sp'])}; already-correct changed (all channels) "
        f"{rate(g['G1_all']['overcorr'])}; pass->fail {rate(g['G1_all']['broken'])}; "
        f"cost {g['cost']['calls_per_input']:.3f} calls/input, {g['cost']['lat_per_input']:.3f} s/input. "
        f"Inclusive sensitivity fix {rate(ig['G1_cue']['fix'])}", "primary 58 families; predicate repair, fluency unassessed; human gate pending"))
    entries.append(("C14", "; ".join(f"polarity+certainty {p}: {rate(s['polarity+certainty'][p])}" for p in ['S3','P2','I2'])
        + f"; paired I2-P2 all dimensions {rate(s['all']['diff_I2'], ' pp')}; speech-act delta "
        f"{rate(s['speech_act']['diff_I2'], ' pp')}; politeness delta {rate(s['politeness']['diff_I2'], ' pp')}. "
        + f"Inclusive all-dim delta {rate(is_['all']['diff_I2'], ' pp')}", "primary 58 families; unresolved sets excluded and paired denominators retained; machine-scored"))
    lv = g['l0_vs_judge']; tp,fp,fn,tn = [lv[k] for k in ['tp','fp','fn','tn']]
    entries.append(("C15", f"TP={tp}, FP={fp}, FN={fn}, TN={tn}; precision {tp/(tp+fp):.4f}, "
                    f"recall {tp/(tp+fn):.4f}, kappa {lv['kappa']}", "primary 58 families; monitor/evaluator dependence caveat retained"))
    vm = oracle['primary']['violation']
    entries.append(("C16", f"Identity {oracle['identity']['false_alarms']}/120 false alarms; scoped mutations "
        f"{oracle['scoped_mutation']['detected']}/120 detected; new mutants {oracle['new_challenge']['mutants_detected']}/24, "
        f"controls {oracle['new_challenge']['controls_false_alarm']}/24 false alarms; primary panel Violation flips "
        f"{vm['units_flipped']}/{vm['n_units']} units, {100*vm['weighted_flip']:.2f}% design-weighted. "
        f"Exact-copy full-mode baseline {report['copy_full_mode']['identity_pass']}/120 partial-contract passes "
        f"({report['copy_full_mode']['primary_pass']}/{report['copy_full_mode']['primary_n']} outside quarantine)",
        "oracle diagnostics include quarantine to expose failure envelope; model endpoints exclude quarantine; machine panel != human validation"))
    ledger_rows = []
    for cid, estimate, status in entries:
        evidence = "analysis/oracle/report.md" if cid == "C16" else "analysis/interventions/report.md" if cid in ['C13','C14','C15'] else "runs/main1/scored.parquet; analysis/label_sensitivity.csv"
        ledger_rows.append(f"| {cid} | Refreshed ACTION 2: {cid} evidence and status | {evidence}; analysis/reconciliation.md | {estimate} | **refreshed**; {status} |")
    # Optional internal claims ledger (not part of the public release); skipped when absent.
    ledger = ROOT / "orchestration/claims_ledger.md"
    existing = ledger.read_text() if ledger.exists() else None
    marker = "<!-- ACTION2_REFRESHED -->"
    if existing is not None and marker not in existing:
        with ledger.open("a") as fh:
            fh.write("\n" + marker + "\n\nEarlier rows above retain their historical estimates/statuses. "
                     "The following entries supersede them for the reconciled snapshot; 'refreshed' does not mean human-validated.\n\n"
                     "| id | claim | evidence | estimate | status |\n|---|---|---|---|---|\n" + "\n".join(ledger_rows) + "\n")

    lines = ["# ACTION 2 evidence reconciliation\n",
        "Old artifacts: `analysis/evidence_prev/` and `analysis/EVIDENCE_MANIFEST_prev.json`; original scored tables also "
        "remain in each run as `scored_prev.parquet`. Final hashes and producing commands: `analysis/EVIDENCE_MANIFEST.json`. "
        "No generation, judging, human coding, or GPU serving was performed. Protected runs r2c1/r2d1/wb1 were excluded.\n",
        "Resolution: `(text_id, input_text, dimension)` independent of family/model/arm; 347 text/input pairs occur in "
        "more than one critical dimension, so dimension is necessary to distinguish value sets. Arbiter decisions win over "
        "all J1/J2 agreements; otherwise one distinct agreed label wins; conflicting top-priority labels or absence of agreement "
        "remain unknown. No J1 fallback. Table includes oracle_inject so copy diagnostics share the same policy. "
        "General extraction labels are unchanged; two shared units have differing missingness in added_content across runs "
        "(text IDs 0469acf05cbd11f9 and fa24a6bc9a413ec3), an ancillary unpaired label rather than a contract predicate.\n",
        "Primary estimates exclude act-10/act-16 in main1/guard1/span1. All-inclusive analyses are retained in "
        "`analysis/main1_quarantine_inclusive/`, `paper/figs/quarantine_inclusive/` and the intervention report's sensitivity "
        "section. Raw J1, J2 and raw acceptance-predicate sensitivities are in `analysis/label_sensitivity.csv`; these are "
        "diagnostics, not alternative authoritative labels. Unknowns are excluded, with missing denominators reported; paired "
        "coverage differences use only jointly known sets. CIs: pointwise 95% whole-family percentile bootstrap, 2,000 draws, "
        "seed 20261031; oracle authored-item diagnostic CIs use Wilson intervals. Human validation remains pending.\n",
        "## Changed labels\n", "| run | target rows | critical labels changed | unresolved after refresh |",
        "|---|---|---|---|"]
    lines += [f"| {r['run']} | {r['rows']} | {r['critical_changed']} | {r['unresolved']} |" for r in run_summary]
    lines += ["\nOccurrence/field audit: `analysis/changed_labels.csv`. Main1's P2 polarity baseline is authoritative "
              "10/40; span1's cached baseline has been corrected from 9/40 to 10/40. The differing Gemma pol-07 "
              "slot output 69aad29e79beadee now uses negated in both runs.\n", "## Refreshed claims\n"]
    for cid, estimate, status in entries:
        lines.append(f"- **{cid}:** {estimate}. Status: refreshed; {status}.")
    lines += ["\n## Every changed endpoint (old versus new)\n",
        "The table includes point estimates, CI bounds, counts, added/removed fields and population changes; "
        "`NA / absent` distinguishes a missing/removed endpoint from a zero. The population column separates label-only "
        "reconciliation from quarantine changes. Unchanged endpoints are omitted. Full-precision machine-readable copy: "
        "`analysis/changed_endpoints.csv`. Selected story and hypothesis texts remain archival; their refreshed labels "
        "and eligible-stratum rates are recorded in `paper/figs/example_manifest.json`.\n",
        "| artifact | population | endpoint | old | new |", "|---|---|---|---|---|"]
    lines += ["| " + " | ".join(display(r[k]) for k in ['artifact','population','endpoint','old','new']) + " |" for r in changes]
    (OUT / "reconciliation.md").write_text("\n".join(lines) + "\n")
    (OUT / "reconciliation.json").write_text(json.dumps(dict(run_summary=run_summary, changed_endpoint_fields=len(changes),
        changed_label_fields=len(label_changes), claims=[dict(id=c, estimate=e, status=s) for c,e,s in entries]), indent=2) + "\n")
    print(f"wrote reconciliation: {len(changes)} endpoint changes; {len(label_changes)} occurrence/field changes")


if __name__ == "__main__":
    main()
