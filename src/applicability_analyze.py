"""Reproduce fixed round-2 H1/H2 endpoints from a frozen, CPU-only archive.

No generation, judging, item rebuilding, or additional hypothesis search. The
archived mine_hyp.py prefix supplies the original endpoints and CI helpers.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/applicability"
CHANNELS = ["full", "chip1", "chipall"]
MODELS = ["qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"]
EARLY = {"r2act-007", "r2act-029", "r2act-030", "r2act-032", "r2plt-002", "r2pol-004"}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def flat_stat(row, prefix, value):
    row.update({f"{prefix}_{k}": int(v) if k == "k" else v for k, v in value.items()})


def md_table(frame):
    # Avoid an optional tabulate dependency.
    vals = [[str(v).replace("|", "×").replace("\n", " ") for v in row]
            for row in frame.itertuples(index=False, name=None)]
    return "\n".join(["| " + " | ".join(frame.columns) + " |",
                      "|" + "---|" * len(frame.columns),
                      *["| " + " | ".join(row) + " |" for row in vals]])


def pct(stat, counts=True):
    result = f"{100*stat['estimate']:.2f} [{100*stat['lo']:.2f}, {100*stat['hi']:.2f}]"
    return (f"{int(stat['k'])}/{stat['n']}; " if counts else "") + result


def bounds(z, planned):
    """Known failures stay failures, including in partly unknown sets."""
    k = int(z.any_fail.sum())
    uncertain = int((~z.any_fail & (~z.known | ~z.complete)).sum())
    absent = planned - len(z)
    assert absent >= 0
    return dict(planned=planned, present=len(z), absent=absent,
                incomplete=int((~z.complete).sum()), unknown=int((~z.known).sum()),
                unknown_and_incomplete=int((~z.known & ~z.complete).sum()),
                definite_failures=k, uncertain_no_known_failure=uncertain,
                lower=k/planned, upper=(k+uncertain+absent)/planned)


def audit_wd(frozen):
    """Check every stored cell/source and channel independently of builder code."""
    rows = [json.loads(l) for l in (frozen / "data/items/r2_d.jsonl").read_text().splitlines()]
    by_scenario = {}
    for item in rows:
        by_scenario.setdefault(item["factorial_family"], []).append(item)
    assert len(rows) == 320 and len(by_scenario) == 80
    audit, allowed = [], set()
    for scenario, records in sorted(by_scenario.items()):
        checks, sources = [], {}
        unique = {enc: set() for enc in ["TELL", "STATEMENT"]}
        assert len(records) == 4
        bare = {r["bare"] for r in records}
        checks.append(len(bare) == 1)
        for item in records:
            assert item["dimension"] in ["polarity", "agent"]
            for var, v in item["variants"].items():
                pol, actor = v["cell"].split("|")
                source = v["source"]
                # This audit checks polarity and actor compatibility, not every
                # semantic property or temporal recoverability from keywords.
                checks += [pol in ["YES", "NOT"], actor in ["I", "YOU"]]
                expected_prefix = "I" if actor == "I" else "You"
                checks.append(bool(re.match(rf"^{expected_prefix}(?: |')", source)))
                negative = bool(re.search(r"\b(?:didn't|haven't)\b", source))
                checks.append(negative == (pol == "NOT"))
                checks.append(source.endswith(".") and "?" not in source)
                # Reviewed single-predicate past/perfect reports: no embedded
                # finite/infinitival clause or possessive actor change.
                checks.append(not re.search(r"\b(?:my|your|want|need|try|forget)\b", source, re.I))
                if item["tense"] == "past":
                    checks.append(bool(re.match(rf"^{expected_prefix} (?:didn't |[a-z]+ )", source)))
                else:
                    checks.append(bool(re.match(rf"^{expected_prefix}(?:'ve | haven't )", source)))
                checks.append(v["critical_value"] == (
                    {"YES": "affirmative", "NOT": "negated"}[pol] if item["dimension"] == "polarity"
                    else {"I": "speaker", "YOU": "addressee"}[actor]))
                sources.setdefault(v["cell"], set()).add(source)
                for enc in ["TELL", "STATEMENT"]:
                    for name, cues in [("neither", ["[TELL]"]),
                                       ("pol", [f"[{pol}]", "[TELL]"]),
                                       ("actor", ["[TELL]", f"[{actor}]"]),
                                       ("both", [f"[{pol}]", "[TELL]", f"[{actor}]"])]:
                        channel = f"{name}_{enc}"
                        spec = item["custom_channels"][var][channel]
                        actual = re.findall(r"\[[^\]]+\]", spec["input"])
                        normalized = ["[TELL]" if c == "[STATEMENT]" else c for c in actual]
                        checks += [set(normalized) == set(cues), len(normalized) == len(cues),
                                   set(spec["commitments"]) == set(cues), spec["prompts"] == ["P0x"],
                                   spec["input"].endswith(" " + item["bare"]),
                                   spec["input"] == "Keywords: " + " ".join(actual + [item["bare"]]),
                                   (f"[{enc}]" in actual)]
                        unique[enc].add(spec["input"])
                        allowed.add((item["family_id"], var, channel, spec["input"]))
        checks += [set(sources) == {"YES|I", "YES|YOU", "NOT|I", "NOT|YOU"},
                   all(len(s) == 1 for s in sources.values()),
                   all(len(s) == 9 for s in unique.values())]
        # The same literal report appears in both focal representations;
        # remove the subject/auxiliary and compare the shared predicate.
        texts = {k: next(iter(v)) for k, v in sources.items()}
        for pol in ["YES", "NOT"]:
            checks.append(re.sub(r"^(?:I|You)", "SUBJ", texts[f"{pol}|I"]) ==
                          re.sub(r"^(?:I|You)", "SUBJ", texts[f"{pol}|YOU"]))
        audit.append(dict(scenario=scenario, bare=next(iter(bare)), tense=records[0]["tense"],
                          n_records=4, n_sources=len(sources), unique_inputs_per_encoding=9,
                          checks=len(checks), failed_checks=len(checks)-sum(checks),
                          compatible=all(checks), **{k.replace("|", "_"): v for k,v in texts.items()}))
    frame = pd.DataFrame(audit)
    assert frame.compatible.all(), frame[~frame.compatible].to_dict("records")
    # Actual stored outputs and frozen requests must use the verified contracts.
    requests = [json.loads(l) for l in (frozen / "runs/requests/r2d.jsonl").read_text().splitlines()]
    return frame, allowed, requests


def main():
    manifest = json.loads((OUT / "freeze_manifest.json").read_text())
    archive = OUT / "evidence.tar.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["archive_sha256"]
    with tempfile.TemporaryDirectory(prefix="aac-applicability-") as tmp:
        frozen = Path(tmp) / "inputs"
        frozen.mkdir()
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(frozen, filter="data")
        for p, sha in manifest["inputs"].items():
            assert hashlib.sha256((frozen / p).read_bytes()).hexdigest() == sha, p
        original = json.loads((frozen / "ideas/cycles/c2/hyp_checks.json").read_text())
        assert original["seed"] == 20261101 and original["n_boot"] == 10000
        replay = Path(tmp) / "replay"
        replay.mkdir()
        source = (frozen / "ideas/cycles/c2/mine_hyp.py").read_text().split("# H3:")[0]
        tree = ast.parse(source)
        # Only I/O roots change; every H1/H2 operation and random seed is retained.
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in ["ROOT", "OUT"]:
                    node.value = ast.Call(func=ast.Name(id="Path", ctx=ast.Load()),
                                          args=[ast.Constant(str(frozen if target.id == "ROOT" else replay))], keywords=[])
        ns = {"__file__": str(ROOT / "analysis/derived/r2_mine_hyp.py")}
        exec(compile(ast.fix_missing_locations(tree), "archived_mine_hyp_H1_H2", "exec"), ns)
        mined = ns["results"]
        for k, value in mined.items():
            assert value == original["results"][k], f"Reproducibility failure: {k}"
        pd.testing.assert_frame_equal(pd.read_csv(replay / "supplied_sets.csv"),
                                     pd.read_csv(frozen / "ideas/cycles/c2/supplied_sets.csv"))
        print("PASS: all five fixed H1/H2 result blocks, exact CIs and supplied_sets.csv reproduced", flush=True)
        c, sets, keys = ns["c"], ns["sets"], ns["keys"]
        rate, difference = ns["rate"], ns["difference"]
        # Compare complete P0/P2/S3 targets on the original shared eligibility.
        summary, models, diagnostics, missing = [], [], [], []
        new = {"first_slots": {}, "missingness": {}, "early_cache_sensitivity": {}, "wd_cells": {}}
        target_ids = ["family_id", "variant", "model", "channel"]
        assert not sets.duplicated(target_ids + ["prompt"]).any()
        assert c[c.channel.isin(CHANNELS)].groupby(target_ids).input_text.nunique().eq(1).all()
        slots = c[c.channel.isin(CHANNELS)]
        for channel in CHANNELS:
            s = mined[f"H1/{channel}"]
            all_z = sets[sets.channel.eq(channel)]
            elig = all_z[all_z.known & all_z.complete].groupby(keys).prompt.nunique()
            elig = elig[elig.eq(3)].reset_index()[keys]
            z = all_z.merge(elig, on=keys)
            planned = 1904
            ms = {p: bounds(all_z[all_z.prompt.eq(p)], planned) for p in ["P0", "P2", "S3"]}
            ms["paired_delta_bounds"] = [ms["P2"]["lower"]-ms["S3"]["upper"],
                                          ms["P2"]["upper"]-ms["S3"]["lower"]]
            ms["matched_complete_targets"] = len(elig)
            ms["excluded_targets"] = planned-len(elig)
            new["missingness"][channel] = ms
            for p in ["P0", "P2", "S3"]:
                missing.append(dict(channel=channel, prompt=p, **ms[p]))
            first = slots[slots.channel.eq(channel)].merge(elig, on=keys)
            # P2 slot zero; S3's first sample, each with suggestion zero.
            first = first[first.suggestion_idx.eq(0) & first.sample_idx.eq(0)].copy()
            assert first.groupby(keys).prompt_id.nunique().eq(3).all()
            first["fail"] = (~first.match).astype(float)
            fs = {p: rate(a, "fail") for p,a in first.groupby("prompt_id")}
            fs["P2_minus_S3"] = difference(first, "fail", "prompt_id", "P2", "S3")
            fs["P2_minus_P0"] = difference(first, "fail", "prompt_id", "P2", "P0")
            new["first_slots"][channel] = fs
            new["early_cache_sensitivity"][channel] = difference(
                z[~z.family_id.isin(EARLY)], "any_fail", "prompt", "P2", "S3")
            row = dict(channel=channel, planned=planned, n=len(elig), clusters=s["P2"]["clusters"])
            for p in ["P0", "P2", "S3", "P2_minus_S3", "P2_minus_P0"]:
                flat_stat(row, p, s[p])
            summary.append(row)
            for model in MODELS:
                a = z[z.model.eq(model)]
                row = dict(model=model, channel=channel, planned=476, n=len(a)//3)
                for p in ["P0", "P2", "S3"]:
                    flat_stat(row, p, rate(a[a.prompt.eq(p)], "any_fail"))
                flat_stat(row, "delta", s["by_model"][model]["delta"])
                f = first[first.model.eq(model)]
                for p in ["P2", "S3"]:
                    flat_stat(row, f"first_{p}", rate(f[f.prompt_id.eq(p)], "fail"))
                models.append(row)
            for p in ["P0", "P2", "S3", "P2_minus_S3", "P2_minus_P0"]:
                diagnostics.append(dict(channel=channel, endpoint="first_output_mismatch", arm=p, **fs[p]))
            # Every excluded occurrence is retained for missingness review.
            tagged = all_z.merge(elig.assign(matched=True), on=keys, how="left")
            tagged["matched"] = tagged.matched.fillna(False).astype(bool)
            tagged.to_csv(OUT / f"sets_{channel}.csv", index=False)
        full_bound = mined["H1/full"]["all_target_missingness_bound_P2_minus_S3"]
        assert np.allclose(full_bound, new["missingness"]["full"]["paired_delta_bounds"], atol=1e-15)
        pd.DataFrame(summary).to_csv(OUT / "channel_summary.csv", index=False)
        pd.DataFrame(models).to_csv(OUT / "model_channel.csv", index=False)
        pd.DataFrame(diagnostics).to_csv(OUT / "first_slot_diagnostics.csv", index=False)
        pd.DataFrame(missing).to_csv(OUT / "missingness.csv", index=False)
        # Preserve the separate lexical population: no judge-knownness filter.
        lexsets = ns["lexsets"]
        lexsets.to_csv(OUT / "exact_partner_sets.csv", index=False)
        audit, allowed, requests = audit_wd(frozen)
        audit.to_csv(OUT / "wd_scenario_audit.csv", index=False)
        wd = ns["wd"]
        assert all((r.family_id, r.variant, r.channel, r.input_text) in allowed for r in wd.itertuples())
        # Check the complete stored request inventory as well as its outputs.
        assert len(requests) == 11520
        request_keys = {r["request_key"] for r in requests}
        assert len(request_keys) == 11520
        for request in requests:
            assert request["prompt_id"] == "P0x" and request["namespace"] in ["d1", "d2"]
            for target in request["targets"]:
                assert (target["family_id"], target["variant"], target["channel"],
                        request["input_text"]) in allowed
        assert set(wd.request_key) == request_keys
        print(f"PASS: {len(audit)}/80 W-D specifications; all 40,960 scored inputs match audited contracts", flush=True)
        t = ns["t"]
        repeats = pd.read_parquet(frozen / "analysis/r2d/repeats.parquet")
        both = pd.read_parquet(frozen / "analysis/r2d/repeats_both.parquet")
        wd_primary = json.loads((frozen / "analysis/r2d/primary.json").read_text())
        # Cell decomposition is fixed to the C27 Llama/STATEMENT/polarity case.
        sel = lambda x: x[x.model.eq("llama3.1-8b") & x.encoding.eq("STATEMENT") & x.dimension.eq("polarity")].copy()
        tx, rx, bx = sel(t), sel(repeats), sel(both)
        assert tx.damage.eq(tx.match_s & ~tx.match_b).all()
        assert rx.repeat_disagreement.eq(rx.match_d1 != rx.match_d2).all()
        assert bx.repeat_disagreement.eq(bx.match_d1 != bx.match_d2).all()
        tx["cluster_id"] = tx.scenario
        wd_rows = []
        for cell in ["YES|I", "YES|YOU", "NOT|I", "NOT|YOU"]:
            z = tx[tx.cell.eq(cell)]
            pol, actor = cell.split("|")
            # Single-cue repeat input fixes polarity, so its actor is shared
            # across the two corresponding cells, rather than double-counted.
            r = rx[rx.input_text.str.contains(f"[{pol}]", regex=False)].assign(cluster_id=lambda d:d.scenario)
            b = bx[bx.input_text.str.contains(f"[{pol}]", regex=False) &
                   bx.input_text.str.contains(f"[{actor}]", regex=False)].assign(cluster_id=lambda d:d.scenario)
            vals = dict(damage=rate(z,"damage"), single_repeat=rate(r,"repeat_disagreement"),
                        both_repeat=rate(b,"repeat_disagreement"))
            paired_s = pd.concat([z.assign(arm="D", value=z.damage.astype(float)),
                                  r.assign(arm="R", value=r.repeat_disagreement.astype(float))])
            paired_b = pd.concat([z.assign(arm="D", value=z.damage.astype(float)),
                                  b.assign(arm="R", value=b.repeat_disagreement.astype(float))])
            vals["damage_minus_single_repeat"] = difference(paired_s,"value","arm","D","R")
            vals["damage_minus_both_repeat"] = difference(paired_b,"value","arm","D","R")
            new["wd_cells"][cell] = vals
            row = dict(model="llama3.1-8b", encoding="STATEMENT", dimension="polarity", cell=cell)
            for k,v in vals.items(): flat_stat(row,k,v)
            wd_rows.append(row)
        pd.DataFrame(wd_rows).to_csv(OUT / "wd_cells.csv", index=False)
        # Keep the original report's pooled-cell repeat-floor CIs/seed exactly.
        new["wd_pooled_repeat_floors"] = dict(
            seed=20261031, n_boot=10000,
            primary=wd_primary["by_encoding_dimension_model"]["STATEMENT"]["polarity"]["llama3.1-8b"],
            both=wd_primary["repeat_endpoint_sensitivity"]["STATEMENT"]["polarity"]["llama3.1-8b"])
        assert int(tx.damage.sum()) == 55 and int(rx.repeat_disagreement.sum()) == 0
        assert int(bx.repeat_disagreement.sum()) == 5
        examples = ns["examples"]
        wd_items = {r["family_id"]: r for r in (
            json.loads(line) for line in (frozen / "data/items/r2_d.jsonl").read_text().splitlines())}
        for ex in examples:
            ex["selection_is_outcome_conditioned"] = True
            if ex["label"].startswith("H1"):
                ex["authored_source"] = ns["items"][ex["family_id"]]["variants"][ex["variant"]]["source"]
                ex["selection_rule"] = (
                    "First complete full-P2 polarity set with normalized partner-source reproduction, "
                    "sorting family_id, model, variant, suggestion_idx; retain its complete paired P0/P2/S3 inventory.")
                ex["phenomenon_rate"] = mined["H1/exact_partner"]
                ex["interpretation"] = "Selected stored counterexample; narrow exact-string endpoint, not typicality or complete semantics."
            else:
                ex["authored_source"] = wd_items[ex["family_id"]]["variants"][ex["variant"]]["source"]
                ex["selection_rule"] = (
                    "First damaged Llama/STATEMENT protected-polarity transition, sorting scenario, cell, draw; "
                    "retain both single-cue and both-cue stored endpoints.")
                ex["phenomenon_rate"] = dict(damage_all_cells=dict(k=55,n=640),
                                              damage_NOT_YOU=dict(k=55,n=160),
                                              scenarios_with_damage=dict(k=30,n=80))
                ex["interpretation"] = "Selected C27 counterexample; protected single-cue pass is not all-contract pass; no mechanism claim."
        dump(OUT / "examples.json", examples)
        new["audit"] = dict(scenarios=80, compatible=int(audit.compatible.sum()),
                            scored_input_occurrences=len(wd), request_keys=11520,
                            n_specification_checks=int(audit.checks.sum()),
                            independent_human_review=False)
        new["reproducibility"] = dict(result_blocks=list(mined), exact_match=True, sets_csv_exact_match=True)
        result = dict(schema_version=1, status="frozen exploratory derivative; Action 5", date="2026-11-01",
                      generator_calls=0, judge_calls=0, bootstrap=dict(n_boot=10000, seed=20261101),
                      preserved=mined, derivative=new, archive_sha256=manifest["archive_sha256"])
        dump(OUT / "results.json", result)
        write_report(result, models, wd_rows, examples)
    # Hash every derivative deliverable; no timestamps, enabling exact replay.
    outputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())
               if p.is_file() and p.name not in ["deliverables.sha256.json", "reproduce.log"]}
    outputs["src/applicability_analyze.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dump(OUT / "deliverables.sha256.json", outputs)
    print("PASS: frozen derivative, manuscript inputs, complete menus and hashes written", flush=True)


def write_report(result, models, wd_rows, examples):
    p, d = result["preserved"], result["derivative"]
    lines = ["# Applicability of diversification and compatible cue composition",
             "", "Frozen derivative for **cycle 2, Action 5**, 2026-11-01. **Exploratory** extra W-C prompt/channel comparisons and a decomposition of C27; none is an additional confirmatory primary contrast. Zero generator calls, zero judge calls, no GPU servers, no additional hypothesis search. This snapshot is separate from any later Action 2 arbitration update.",
             "", "## Result and scope", "",
             "On full input, P2 has a focal-label mismatch in 1,161/1,850 three-output sets versus 50/1,850 equal-size S3 sets: **+60.05 pp [57.31, 62.70]**. This is a partial categorical endpoint, not an opposite-meaning rate. The independent exact-string endpoint finds the partner source in **21/639 P2 sets versus 2/639 S3 sets**, +2.97 pp [1.55, 4.54]. Diversifying readings left open by keywords and preserving values fixed by supplied input are different requirements.",
             "", "W-D's Llama/STATEMENT protected-polarity damage is confined to NOT×YOU: **55/160**, versus **0/480** other-cell transitions. It remains above both repeat floors. All 80 stored scenario specifications have compatible polarity, actor and constant statement cues under the audit below. All 55 damaged outputs are currently coded **statement**; a request/imperative mechanism is unsupported and is abandoned.",
             "", "## Fixed estimands, populations and uncertainty", "",
             "W-C: 240 designed families; exclude r2act-078/079 (D-018), leaving 238 families × two targets × four fixed models = **1,904 planned targets per channel**. Units are (family, target variant, model, channel); P0 has one output, P2 has three suggestions from one greedy request, S3 has three separate P0 samples at temperature .7. Original shared eligibility requires all three arms complete and every focal label known. P2/S3 each have exactly three outputs, P0 one; the P0 any-mismatch comparison is an opportunity-count diagnostic. Actual input text agrees across arms for each target.",
             "", "A mismatch means critical_match=False in at least one output. Mask critical_source=J1 as unknown, as in the protocol-aligned mined snapshot; no single-J1 fallback enters W-C estimates. An observed unclear/mixed category is a label, distinct from unresolved extraction. This tests the supplied focal dimension only, not joint semantics, fluency, scope, intent or usability. P2 versus S3 controls the number of opportunities, but not prompt, temperature, nor joint versus separate generation.",
             "", "The existing mine_hyp.py H1/H2 prefix was replayed without statistical changes. All five result blocks, their full-precision CIs and supplied_sets.csv reproduce exactly. Archived original files are never rewritten. All original 14 mined-input hashes were verified when freezing. New diagnostics use the same helpers: **10,000 joint whole recorded seed/construction-cluster percentile resamples, seed 20261101** (physical scenarios for W-D). Pooled estimates describe a fixed roster, not a population of models. Intervals are pointwise and do not correct exploratory selection or oracle error. Zero-event empirical intervals do not establish zero future risk.",
             "", "W-C chronology remains qualified: 48 cached requests predate final item freeze; 12 distinct primary requests predate final item mtimes. The original W-C snapshot masks 259 fallback critical scored rows across its full inventory. The passed human gate covers earlier main1 extraction, not independent validation of these extra W-C comparisons, W-D outputs, or usable repairs. No additional human budget was consumed.",
             "", "## W-C supplied-input any-focal-mismatch", "",
             "All rates are percentages; contrasts are percentage points. Brackets are 95% cluster intervals. These channel-specific matched populations must not be pooled as a common sample.", ""]
    rows = []
    for ch in CHANNELS:
        s = p[f"H1/{ch}"]
        rows.append([ch, str(s["P2"]["n"])+"/1904", str(s["P2"]["clusters"]),
                     pct(s["P0"]), pct(s["P2"]), pct(s["S3"]), pct(s["P2_minus_S3"],False)])
    lines += [md_table(pd.DataFrame(rows, columns=["Channel","Matched/planned","Clusters","P0 (one)","P2 (three)","S3 (three)","P2−S3, pp"])),
              "", "### Compact model × channel table", "",
              "Counts / matched targets; percentages in parentheses. The final column is the paired P2−S3 contrast with 95% CI. Full precision, P0 and first-slot diagnostics: model_channel.csv. Rows use each model's channel-specific shared eligibility.", ""]
    rows=[]
    for r in models:
        rows.append([r["model"],r["channel"],str(r["n"])+"/476",
                     f"{int(r['P0_k'])}/{r['n']} ({100*r['P0_estimate']:.2f})",
                     f"{int(r['P2_k'])}/{r['n']} ({100*r['P2_estimate']:.2f})",
                     f"{int(r['S3_k'])}/{r['n']} ({100*r['S3_estimate']:.2f})",
                     f"{100*r['delta_estimate']:.2f} [{100*r['delta_lo']:.2f}, {100*r['delta_hi']:.2f}]"])
    table=md_table(pd.DataFrame(rows,columns=["Model","Channel","Matched/planned","P0","P2","S3","P2−S3, pp"]))
    (OUT / "model_channel.md").write_text(table+"\n")
    lines += [table,"", "### First-output diagnostics", "",
              "P2 slot 1 (stored suggestion_idx=0) versus S3 draw 1 (sample_idx=0, suggestion_idx=0), on the same complete shared targets. This fixes one output opportunity in each arm but is still a configuration comparison. No user-selection behavior is observed. P0 counts/CIs are in the preceding table.", ""]
    rows=[]
    for ch in CHANNELS:
        s=d["first_slots"][ch]
        rows.append([ch,pct(s["P2"]),pct(s["S3"]),pct(s["P2_minus_S3"],False)])
    lines += [md_table(pd.DataFrame(rows,columns=["Channel","P2 first output","S3 first output","P2−S3, pp"])),
              "", "For full P2, the original slot-specific mismatch counts are **539/1850**, **626/1850** and **628/1850** for slots 1–3 (29.14%, 33.84%, 33.95%). Any-mismatch **1161/1850** counts each set once. First slots are ordered outputs, not a randomized test of position.",
              "", "## Exclusions and missingness bounds", "",
              "Each channel has 1,904 planned targets. Excluded targets fail the joint completeness/knownness rule in one or more arms. Incomplete and unknown sets can overlap. No missing suggestion is fabricated. Missingness.csv contains arm counts; sets_<channel>.csv retains every arm and its matched flag.", ""]
    rows=[]
    for ch in CHANNELS:
        ms=d["missingness"][ch]
        rows.append([ch,str(ms["excluded_targets"]),
                     "; ".join(f"{a}: {ms[a]['incomplete']}/{ms[a]['unknown']}/{ms[a]['absent']}" for a in ["P0","P2","S3"]),
                     f"[{100*ms['paired_delta_bounds'][0]:.2f}, {100*ms['paired_delta_bounds'][1]:.2f}]"])
    lines += [md_table(pd.DataFrame(rows,columns=["Channel","Excluded targets","Incomplete / unknown / absent sets","All-planned P2−S3 bound, pp"])),
              "", "These are deterministic worst-case identification bounds, not confidence intervals. An observed failure fixes a set's endpoint to failure even if another output is unknown or absent. Otherwise an incomplete/unknown set may be either pass or fail. Absent sets may be either. Subtract S3's upper bound from P2's lower, and vice versa. Bounds use every planned target and need not center on the complete-case estimate: some excluded sets already contain known failures.",
              "", "Exclude the six previously identified early-cache families (no new exclusion search):", ""]
    lines += [md_table(pd.DataFrame([[ch,pct(d['early_cache_sensitivity'][ch],False)] for ch in CHANNELS],
                                    columns=["Channel","P2−S3, pp [CI]"])),
              "", "This sensitivity cannot repair the retrospective chronology qualification. The original full-input family-only bootstrap and leave-one-cluster-out range remain in results.json under preserved.H1/full; recorded clusters, rather than families, remain the main analysis.",
              "", "## Exact normalized partner-source reproduction", "",
              "Judge-free lexical endpoint, full-input polarity only. Normalize with the archived rule: lowercase, convert curly apostrophe to ASCII, remove all non-ASCII-alphanumeric/non-whitespace characters (including punctuation and apostrophes), collapse whitespace. A set is positive if any output equals its authored partner source after this normalization. This is narrow lexical evidence: other paraphrased reversals can be missed; categorical polarity disagreements can also occur without a semantic reversal. It is not a complete semantic failure measure.",
              "", "Both P2 and S3 must have three outputs; judge-knownness is not required, and P0 does not determine eligibility. Thus **639/640 planned polarity targets**, **79 clusters**, differ from the 622 full-input categorical polarity targets and from the pooled 1,850. P0 is a one-output diagnostic on this population.", ""]
    ex=p["H1/exact_partner"]
    lines += [md_table(pd.DataFrame([[a,pct(ex[a])] for a in ["P0","P2","S3"]],columns=["Arm","Sets with partner reproduction, % [CI]"])),
              "",f"Paired P2−S3: **{pct(ex['P2_minus_S3'],False)} pp**. The one unmatched planned target has an incomplete set. A conservative all-planned bound allowing the missing set endpoint either value is [18/640, 20/640] = [2.81, 3.12] pp; this identification bound is not a CI.",
              "", "### Complete stored appointment menus", "",
              "Selected counterexample, not typical: retain the existing H1 rule, first complete full-P2 polarity set reproducing its normalized partner source, sorting family_id, model, variant, suggestion_idx. It selects Llama r2pol-024/B. **Rate: P2 21/639 versus S3 2/639**, as above. All six menu slots below are verbatim stored outputs, including repeated S3 text. Provenance and exact input strings are in examples.json; this replay verifies them against archived outputs.jsonl.", ""]
    chosen=[x for x in examples if x["label"] == "H1 paired full-output inventory"]
    lines += ["Authored source:", "", "> "+chosen[0]["input_text"].removeprefix("The user typed: "), "",
              "Generator-visible input (the source is visible in full mode):", "", "> "+chosen[0]["input_text"], ""]
    for arm in ["P2","S3"]:
        lines += [f"**{arm}**", ""]
        slots=sorted([x for x in chosen if x["prompt_id"]==arm], key=lambda x:(x["sample_idx"],x["suggestion_idx"]))
        assert len(slots)==3
        for i,x in enumerate(slots,1):
            lines += [f"{i}. {x['text']} (`{x['output_id']}`)"]
        lines += [""]
    lines += ["## W-D four-cell decomposition and repeat floors", "",
              "Decomposition fixed to Llama/STATEMENT protected polarity, the C27 regression case; **80 physical scenario clusters**, two greedy namespace draws. Damage means a protected-polarity single-cue pass becomes a protected-polarity both-cue fail. It does not require that the initial sentence pass the entire contract. There are 160 transitions per cell; cells share their physical scenarios. Single-cue repeat pairs fix polarity and are shared across actor cells; both-cue repeat pairs fix the complete cell.", ""]
    rows=[]
    for cell,v in d["wd_cells"].items():
        rows.append([cell,pct(v["damage"]),pct(v["single_repeat"]),pct(v["both_repeat"]),
                     pct(v["damage_minus_single_repeat"],False),pct(v["damage_minus_both_repeat"],False)])
    lines += [md_table(pd.DataFrame(rows,columns=["Cell","Damage, % [CI]","Single repeat, % [CI]","Both repeat, % [CI]","D−Rsingle, pp","D−Rboth, pp"])),
              "", "Cell CIs use seed 20261101, 10,000 scenario resamples. Across all four cells, retain the existing W-D report's **seed 20261031** estimates: damage **55/640 = 8.59% [6.25, 11.09]**, single-repeat **0/160**, D−Rsingle **+8.59 pp [6.25, 11.09]**; both-repeat **5/320 = 1.56% [0.31, 3.12]**, D−Rboth **+7.03 pp [4.38, 9.84]**. These are ratio contrasts on jointly resampled scenarios, not subtraction of independent CI endpoints. Do not compare NOT×YOU's 34.38% cell rate with an unmatched pooled repeat rate.",
              "", "Damage occurs in **30/80** scenarios, with **29/80** events in draw d1 and **26/80** in d2 for NOT×YOU. Other cells: **0/480**. The NOT×YOU−other contrast is **+34.38 pp [24.38, 44.38]**, preserved from c2. Both focal judges agree at both ends of all **640/640** transitions. All **55/55** damaged outputs lack the checked lexical negation markers; all **55/55** have speech_act=statement. These are lexical/label diagnostics, not a causal explanation or complete semantics. No request/imperative mechanism is claimed.",
              "", "### Compatibility audit of every scenario", "",
              f"**80/80 compatible**, **320/320 stored A/B records**, **640 variant references to four sources per scenario**; {d['audit']['n_specification_checks']:,} explicit source/cell/channel checks passed. wd_scenario_audit.csv lists each scenario's four real sources, tense, keyword input, check count and verdict. All 40,960 stored scored input occurrences match an audited custom-channel specification; the 11,520 unique request keys cover the balanced design.",
              "", "Audit rule: each scenario must contain all four YES/NOT×I/YOU cells with one consistent source per cell across polarity/agent focal representations. Every source is a plain past/perfect report with the appropriate subject and negation; the actor switch retains the same predicate, with no my/your change or embedded want/need/try/forget clause. Inspect the authored predicate inventory (everyday single actions, including phrasal verbs); no polarity–actor contradiction was found. Each encoding must expose exactly nine unique inputs. Neither/polarity/actor/both channels must carry exactly the corresponding compatible cues; [STATEMENT] is the visible alias of semantic [TELL], not an extra cue. The constant statement instruction is present at both endpoints. The audit checks internal specification compatibility, not independent human linguistic validation. Temporal detail absent from the keywords is outside this protected endpoint.",
              "", "The W-D source builder was read, but neither called nor used as the audit oracle; historical items and requests were not regenerated. This audit does not repair the incomplete prospective item/codebook freeze. W-D generally uses agreement else J1 fallback; the focal Llama polarity case has agreement throughout. The Qwen/TELL agent CB-7 limitation remains and is not promoted into a semantic-damage claim here. No universally safe encoding or model-general interference follows.",
              "", "## Engineering implication and manuscript inputs", "",
              "Condition diversification on which dimensions the input leaves open. Under a declared full-sentence mode, exact copy is the zero-generation preservation baseline; the present analysis does not test a new router, prompt rescue, I2 transfer or guard transfer. The positive C27 cell decomposition is a model/encoding regression test, not an independent replication.",
              "", "Manuscript-ready CSVs use proportions for estimates/CI endpoints, integer counts for k/n, and explicit planned/matched denominators: channel_summary.csv (pooled channels), model_channel.csv and model_channel.md (compact roster table), first_slot_diagnostics.csv, missingness.csv, exact_partner_sets.csv, wd_cells.csv, wd_scenario_audit.csv. results.json retains original and derivative endpoints with separate seeds. examples.json stores exact selected occurrences; no new selected example is introduced.",
              "", "## Freeze and reproduce", "",
              "Run from the repo root (CPU only):", "", "```bash",
              "setsid nohup env OPENBLAS_NUM_THREADS=1 .venv/bin/python src/applicability_analyze.py > analysis/applicability/reproduce.log 2>&1 < /dev/null &",
              "```", "",
              "evidence.tar.gz contains byte-preserved input files, including original c2 mining code/results/sets/examples, both scored inventories, raw output JSONL, W-D derived transition/repeat inventories and item/request specifications. freeze_manifest.json records original SHA256 hashes, archive hash, all 14 original mined-hash checks and context-only read hashes. The analyzer verifies archive and input hashes before replaying only the original H1/H2 prefix; H3/H4 and the rejected searches are not executed. It compares original results and CIs exactly, verifies every selected output against stored raw text, audits all 80 W-D specifications, and writes deliverables.sha256.json. Archive changes or reproducibility failures abort the analysis; later scoring changes require a separately versioned snapshot, never silent replacement of this one.",
              "", "No manuscript source, registered primary estimate, original item/output, or prior evidence report was changed by Action 5. Claims C30/C31 and a C27 decomposition update C32 are appended to the claims ledger with the exploratory limitations above. C33 belongs to Action 1; no W-B corrected headline is inferred here."]
    (OUT / "report.md").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    main()
