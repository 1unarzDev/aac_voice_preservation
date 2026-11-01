"""Regenerate figure captions and selected-example rates from the frozen tables."""
from __future__ import annotations

import hashlib
import json
import math

import pandas as pd

from analyze import family_bootstrap
from provenance_paths import MAIN1_HYP_EXAMPLES, MAIN1_STORY, STORY_V2
from runio import ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(r):
    return f"{100*r['estimate']:.2f}% [{100*r['ci_low']:.2f}, {100*r['ci_high']:.2f}]"


def human_status():
    h = json.loads((ROOT / "annotation/judge_validation_main1.json").read_text())["human"]
    tests = [d["sampled_test/final"] for d in h["judge"].values()]
    assert all(d["kappa"] >= .6 for d in tests)
    v = h["verdict"]["violation"]["primary"]
    return (f"D-031: **human extraction gate H7 passed** on the earlier main1 inventory: "
            f"two annotators, {h['n_items']} items (100 double-coded core, 87 single-coded extras). "
            f"Held-out `sampled_test/final` κ={min(d['kappa'] for d in tests):.3f}–{max(d['kappa'] for d in tests):.3f}; "
            f"lowest lower 95% bound {min(d['kappa_ci'][0] for d in tests):.3f}. "
            f"Primary Violation verdict agreement {v['agree_k']}/{v['n']} [91.5, 99.0]%, κ={v['kappa']:.3f}; "
            f"judge-positive {v['judge_positive']}, human-positive {v['ref_positive']}, "
            f"{v['judge_T_ref_F']} judge-only and {v['judge_F_ref_T']} human-only. "
            "The broader sampled/final κ=.899–.977 is a different view. Plurality reference with ties/unsure excluded; "
            "labels converted from another format, no per-item timing. Humans corrected the shared ‘can't wait’ "
            "error but both retain ‘two’ for ‘a couple of’ against the frozen key (D-033). "
            "Rates remain machine-scored. H7 does not validate repaired-text quality, W-B admissibility, "
            "or every new W-C/W-D boundary.\n")


def wb_contract_caption():
    path = ROOT / "analysis/wb/contract_audit.json"
    if not path.exists():
        return ""
    audit = json.loads(path.read_text())
    assert audit['inventory']['messages'] == 139 and audit['inventory']['outputs'] == 556
    return ("## W-B restoration contract status\n\n"
            "**Source match and actual-input fidelity are separate endpoints.** Complete audit: 139 messages / 556 stored outputs; "
            "131 chip mappings and eight word inputs. Seven definite chip/source conflicts preclude a model-ignored-the-source-cue "
            "attribution on their 28 outputs. Five certainty conflicts: 20/20 source failures honour visible `[MAYBE]`. "
            "Six word cases are aligned at the coarse polite-marker endpoint; two remain unknown. "
            "Nine unclear source references and five detector fallbacks lacking panel consensus remain withheld from "
            "the aligned/expressible sensitivity (116 messages, 464 occurrences). Eight aligned `[SURE]` sources demand "
            "a finer emphatic distinction than that chip supplies; four source failures honour the coarse cue. "
            "Original restored general source failures: 12/223 random, 55/276 enriched; actual-input general failures: "
            "9/231 random, 38/316 enriched. Aligned/expressible general source failures: 8/219 and 26/244; "
            "actual-input failures in that sensitivity: 8/219 and 22/244. Different populations are never an intervention gain. "
            "POS-cap4 non-default polarity source-honouring counts are 0/36 and 2/84; strictly negated counts are 0/32 and 2/48. "
            "W-B is final generation, machine-assessed; the separate 20-message human admissibility audit is absent. "
            "See `analysis/wb/contract_audit.md`, its complete eligibility/verdict diff and hashed snapshot. "
            "New audit CIs: 10,000 whole-message resamples, seed 20261101, samples separate; original W-B tables retained.\n")


def main():
    directory = ROOT / "paper/figs"
    nums = json.loads((directory / "fig_numbers.json").read_text())
    tables = {run: pd.read_parquet(ROOT / f"runs/{run}/scored.parquet") for run in ['main1','guard1','span1']}
    d = nums['fig_defaults']; ladder = nums['fig_channel_ladder']; cost = nums['fig_cost_asymmetry']
    sets = nums['fig_sets']; ratchet = nums['fig_politeness_ratchet']; pipeline = nums['fig_pipeline']
    lines = ["# Shared figure captions (discovery tables retained)\n",
        "**Version routing:** [current evidence map](../../analysis/EVIDENCE_MAP.md) is authoritative for population/status. "
        "Discovery figures below use main1 shared-label resolution; `r2c/CAPTIONS.md` and its figures use current arbitrated W-C. "
        "C30/C36 applicability keeps its explicitly frozen **pre-arbitration protocol-masked** snapshot; do not substitute current W-C labels. "
        "W-D, the W-B contract audit and the accepted guard transfer (C37) remain separate populations. "
        f"Current exact examples: `{STORY_V2}`, mirrored in `example_manifest_c3.json`; "
        "original manifest and historical discovery captions/tables are preserved.\n",
        "Generated from `runs/main1/scored.parquet` with `annotation/label_resolution.jsonl` by "
        "`paper/figs/make_figs.py` and `src/refresh_captions.py`. Original captions and numbers remain in "
        "`analysis/evidence_prev/paper/figs/`. The generated figure numbers, macros and example manifest share this scoring version. "
        "The design contains 60 test families; primary estimates use **58 families**, excluding act-10 and act-16. "
        "Four fixed models. Quarantine-inclusive figures and numbers are in `quarantine_inclusive/`. "
        + human_status(),
        "CIs are pointwise 95% percentile intervals from 2,000 whole-family bootstrap resamples, seed 20261031. "
        "Families are resampled jointly over models, targets and paired arms. Exact counts and denominators are retained "
        "in `fig_numbers.json` and `example_manifest.json`. Primary exclusions apply to every figure. "
        "Time and quantity each contain five families and are displayed separately.\n",
        "## fig_pipeline\n",
        f"**Channel-controlled attribution.** Minimal-pair family pol-07, with stored {pipeline['model']} P0 bare output "
        f"{json.dumps(pipeline['output'], ensure_ascii=False)}. Noncritical input uses the stored order `like new medication`. "
        "Bare/noncritical reference match measures a model's chosen reading; the added word is a length control and "
        "default-sensitivity diagnostic. Supplied-cue correctness is assessed in chip1/chipall/full. Full means source "
        "visible to the generator; critical/general extraction is output-only and blind to model/channel; "
        "added-content extraction sees the visible input. Loss, Violation and Assumption "
        "have different denominators. Only the bare channel's connector is drawn solid: the shown output came from bare input; "
        "the other channels' connectors are faint. The arbiter (J1/J2 disagreements only) sees the visible input. "
        "This is a selected example, not a typicality claim.\n",
        "## fig_defaults\n",
        f"**Choices under ambiguous keywords.** P0 bare, {d['n_outputs']} distinct family/model outputs from "
        f"{d['n_families']} primary families. A/B duplicate requests count once. "
        + "; ".join(f"{dim} {value}: {pct(d[dim]['shares'][value])} (n={d[dim]['n']})"
            for dim,value in [('polarity','affirmative'),('certainty','plain assertion'),('agent','speaker'),('speech_act','statement')])
        + ". The 50% line follows from balanced authored pairs, not a population preference or fairness target.\n",
        "## fig_channel_ladder\n",
        f"**Reference match and supplied-predicate preservation.** P0, {ladder['n_outputs']} target occurrences "
        f"({ladder['n_families']} families × two targets × five channels × four models). "
        + "; ".join(f"{ch}: {pct(r)}" for ch,r in ladder['all_dims'].items())
        + ". Bare/noncritical values are ambiguous reference match (dotted segment, not accuracy); chip1/chipall/full assess supplied cues "
        "(solid segment); the pooled line is deliberately not continued across that boundary. "
        "The orange dashed line adds joint preservation of scored supplied predicates. "
        + "; ".join(f"joint {ch}: {pct(r)} (n={r['n']})" for ch,r in ladder['joint_supplied_predicates'].items())
        + ". Two refusal/acceptance families are quarantined rather than counted as primary passes.\n",
        "## fig_cost_asymmetry\n",
        f"**Nominal extra selections.** {cost['n_families_with_default']} primary families have an identified default; "
        f"{len(cost['families_without_default'])} primary families lack one and are excluded. "
        "Default is the modal bare P0 pair value across four models; ties use cached P2/S3 outputs. "
        "Cost is zero for a matching first suggestion, one when the target occurs later in the three-suggestion set, "
        "otherwise the critical chip count. "
        + "; ".join(f"{arm}: {r['estimate']:.3f} [{r['ci_low']:.3f}, {r['ci_high']:.3f}] (n={r['n']})"
                     for arm,r in cost['pooled'].items())
        + ". This counts nominal selections, omits reading/navigation time, and does not guarantee the chip repair succeeds.\n",
        "## fig_politeness_ratchet\n",
        "**Full-mode politeness additions and removals.** P0, ten politeness families: plain→polite "
        f"{pct(ratchet['Politeness']['Pooled']['added to a plain source'])} (9/40), polite→plain "
        f"{pct(ratchet['Politeness']['Pooled']['removed from a polite source'])} (2/40). "
        "Per-model addition counts are "
        + ", ".join(f"{lab} {ratchet['Politeness'][m]['added to a plain source']['k']}/{ratchet['Politeness'][m]['added to a plain source']['n']}"
                    for lab, m in [("Qwen", "qwen2.5-7b"), ("Llama", "llama3.1-8b"), ("Gemma", "gemma3-4b"), ("Terra", "gpt-6.1-terra")])
        + "; these are ten-family intervals. Hedging control (certainty families, printed as a note): "
        f"{ratchet['Hedging_control_P0']['added'][0]}/{ratchet['Hedging_control_P0']['added'][1]} additions, "
        f"{ratchet['Hedging_control_P0']['removed'][0]}/{ratchet['Hedging_control_P0']['removed'][1]} removals. "
        f"Across primary families whose source spec is plain, {round(ratchet['politeness_added_all_plain_sources']['Pooled']*ratchet['politeness_added_all_plain_sources']['n'])}/"
        f"{ratchet['politeness_added_all_plain_sources']['n']} full-mode outputs add politeness. "
        "Cached P1 sensitivity is drawn as a separate grey row, not a primary arm: "
        f"{ratchet['Politeness']['P1_Pooled']['added to a plain source']['k']}/{ratchet['Politeness']['P1_Pooled']['added to a plain source']['n']} additions, "
        f"{ratchet['Politeness']['P1_Pooled']['removed from a polite source']['k']}/{ratchet['Politeness']['P1_Pooled']['removed from a polite source']['n']} removals.\n",
        "## fig_sets\n",
        "**Coverage of both authored readings among three suggestions.** Bare, one set per family/model/arm. "
        + "; ".join(f"{pr}: {pct(r)} ({round(r['estimate']*r['n'])}/{r['n']} sets)" for pr,r in sets['pooled'].items())
        + ". P2 requests three different meanings; S3 samples three P0 outputs at temperature 0.7. "
        f"Polarity P2 is {pct(sets['by_dim']['polarity']['P2'])} (10/40), after propagating the arbiter to "
        "span1. This is authored-pair coverage under machine labels, not coverage of all admissible meanings.\n"]
    lines.append(wb_contract_caption())
    current = json.loads((ROOT / 'analysis/evidence_c3/current.json').read_text())
    V = current['displayed_values']   # formatted once from source files by src/c3_evidence.py
    lines += ["## Discovery guard comparator (C35; current display)\n",
              f"P0 / zero-call strip-only G1s / regeneration G1 strict passes: {V['disc_pass']} cue target occurrences. "
              f"Paired G1−G1s **{V['c35']}**, 58 family clusters, {V['c35_disc']} passes; no missing matched targets. "
              "These discordances compare G1 with G1s; they are not newly broken P0-correct outputs. "
              "Exploratory stored-configuration comparison; 10,000 whole-family joint resamples, seed 20261101. "
              f"No causal feedback or usable-repair claim. Repairs {V['repairs']}, residual {V['residual']}; "
              f"changed-correct {V['changed_all']} all channels and {V['changed_cue']} cue channels. "
              f"Costs use {V['cost_inputs']}; pass rates use cue target occurrences.\n",
              "## Current W-C and applicability displays\n",
              f"C34 v2 (completed): speech-act chip1 {V['c34_chip']}, full {V['c34_full']}; gap {V['c34_gap']}. "
              f"C11: question failures {V['c11']}, specifically requests {V['c11_req']}. "
              "C30 remains the older complete-matched **pre-arbitration protocol-masked** derivative; do not substitute current W-C labels. "
              f"C36 first-output companion: {V['c36']}. This equalizes inspected slots only, not prompt/temperature/generation. "
              f"The c3:S4 appointment menu illustrates exact partner-source reproduction, {V['c31']}; "
              "it is not the C30 category-mismatch endpoint. Retain all six strings. "
              "Guard fragment c3:S9 is a selected counterexample (exact Ask-you prefix 4/63 scored repairs), "
              "not a measured fluency prevalence. The human gate does not validate repaired quality. "
              "All examples are post-outcome selections with declared rules and adjacent rates.\n",
              "## Guard transfer to W-C (C37; separate frozen population)\n",
              f"Frozen guard on {V['gt_inv']}. PASS on all fixed criteria, accepted with qualifications "
              f"(`analysis/guard_wc/ACCEPTANCE.md`): joint-pass gain {V['gt_gain']}; strict repairs {V['gt_repair']}; "
              f"initially correct texts changed {V['gt_changed']}; pass→fail {V['gt_p2f']}; residual strict failures {V['gt_resid']}. "
              f"Comparator G1−G1s {V['gt_cmp']}. Cost {V['gt_calls']}. 10,000 whole-family resamples, seed 20261101. "
              "Machine-scored partial predicate; repaired-text quality unvalidated; not a discovery replication.\n",
              "## W-B restoration contract and R5 builder check\n",
              f"Definite chip/source conflicts {V['wb_conf']}. R5 validator replay of the restored inputs: {V['r5']}. "
              "Coarser = the cue (e.g. [SURE]) cannot supply the finer source distinction; unknown is never certified. "
              "See `analysis/r5_validator/README.md`.\n"]
    (directory / "CAPTIONS.md").write_text("\n".join(lines) + "\n")

    examples = []
    story = json.loads((ROOT / MAIN1_STORY).read_text())
    for card in story['examples']:
        examples.extend((card['id'], record['run'], record) for record in card['outputs'])
    for record in json.loads((ROOT / MAIN1_HYP_EXAMPLES).read_text()):
        examples.append((record['label'], record['stored_file'].split('/')[1], record))
    output = []
    for label, run, reference in examples:
        table = tables[run]
        matches = table[table.output_id.eq(reference['output_id'])]
        for key in ['family_id','variant','channel','model','request_key']:
            if key in reference:
                matches = matches[matches[key].eq(reference[key])]
        if len(matches) != 1:
            raise ValueError(f"Ambiguous selected occurrence {label}: {len(matches)} rows")
        row = matches.iloc[0]
        assert row.text == reference['text'] and row.input_text == reference['input_text']
        primary = table[~table.quarantine_refusal_acceptance]
        # Same model/critical dimension/target value/channel/arm, across families.
        stratum = primary[primary.model.eq(row.model) & primary.dimension.eq(row.dimension)
                          & primary.variant_value.eq(row.variant_value) & primary.channel.eq(row.channel)
                          & primary.prompt_id.eq(row.prompt_id)]
        metric = 'constraint_preserving' if row.cue_in_input else 'critical_match'
        r = family_bootstrap(stratum, metric)
        clean = {k: (None if pd.isna(v) else v.item() if hasattr(v,'item') else v) for k,v in row.items()}
        output.append(dict(example=label, run=run, occurrence=clean, eligible_stratum=dict(
            rule="primary; same model/dimension/target critical value/channel/arm; all families",
            metric=metric, k=int(stratum[metric].sum()), **r),
            note="Selected counterexample; no representative-selection claim. A quarantined example has diagnostic status only."))
    manifest = dict(label_resolution="annotation/label_resolution.jsonl", resolution_sha256=sha(ROOT / "annotation/label_resolution.jsonl"),
                    scored_sha256={run:sha(ROOT / f"runs/{run}/scored.parquet") for run in tables},
                    selection="Existing story gallery and hypothesis examples, unchanged exact strings and declared order; no reselection",
                    source_manifests=[MAIN1_STORY, MAIN1_HYP_EXAMPLES],
                    n_boot=2000, seed=20261031, examples=output)
    def clean_json(value):
        if isinstance(value, dict):
            return {k: clean_json(v) for k,v in value.items()}
        if isinstance(value, list):
            return [clean_json(v) for v in value]
        return None if isinstance(value, float) and not math.isfinite(value) else value
    (directory / "example_manifest.json").write_text(json.dumps(clean_json(manifest), indent=2, default=str, allow_nan=False) + "\n")
    c3 = json.loads((ROOT / STORY_V2).read_text())
    mirror = dict(namespace='c3', source_manifest=STORY_V2,
                  source_sha256=sha(ROOT / STORY_V2),
                  reconciliation='analysis/evidence_c3/selector_reconciliation.json',
                  status='retrospective verified replay; not prospective selection or typicality',
                  cards=c3['cards'], verified_occurrences=c3['verified_occurrences'])
    (directory / 'example_manifest_c3.json').write_text(json.dumps(mirror, ensure_ascii=False, indent=2) + '\n')
    print(f"refreshed captions and {len(output)} selected example occurrences")


if __name__ == "__main__":
    main()
