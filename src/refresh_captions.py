"""Regenerate figure captions and selected-example rates from the frozen tables."""
from __future__ import annotations

import hashlib
import json
import math

import pandas as pd

from analyze import family_bootstrap
from runio import ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(r):
    return f"{100*r['estimate']:.2f}% [{100*r['ci_low']:.2f}, {100*r['ci_high']:.2f}]"


def main():
    directory = ROOT / "paper/figs"
    nums = json.loads((directory / "fig_numbers.json").read_text())
    tables = {run: pd.read_parquet(ROOT / f"runs/{run}/scored.parquet") for run in ['main1','guard1','span1']}
    d = nums['fig_defaults']; ladder = nums['fig_channel_ladder']; cost = nums['fig_cost_asymmetry']
    sets = nums['fig_sets']; ratchet = nums['fig_politeness_ratchet']; pipeline = nums['fig_pipeline']
    lines = ["# Figure captions (refreshed ACTION 2)\n",
        "Generated from `runs/main1/scored.parquet` with `annotation/label_resolution.jsonl` by "
        "`paper/figs/make_figs.py` and `src/refresh_captions.py`. Original captions and numbers remain in "
        "`analysis/evidence_prev/paper/figs/`. The generated figure numbers, macros and example manifest share this scoring version. "
        "The design contains 60 test families; primary estimates use **58 families**, excluding act-10 and act-16. "
        "Four fixed models. Quarantine-inclusive figures and numbers are in `quarantine_inclusive/`. "
        "All automated rates are provisional; human oracle validation remains pending.\n",
        "CIs are pointwise 95% percentile intervals from 2,000 whole-family bootstrap resamples, seed 20261031. "
        "Families are resampled jointly over models, targets and paired arms. Exact counts and denominators are retained "
        "in `fig_numbers.json` and `example_manifest.json`. Primary exclusions apply to every figure. "
        "Time and quantity each contain five families and are displayed separately.\n",
        "## fig_pipeline\n",
        f"**Channel-controlled attribution.** Minimal-pair family pol-07, with stored {pipeline['model']} P0 bare output "
        f"{json.dumps(pipeline['output'], ensure_ascii=False)}. Noncritical input uses the stored order `like new medication`. "
        "Bare/noncritical reference match measures a model's chosen reading; the added word is a length control and "
        "default-sensitivity diagnostic. Supplied-cue correctness is assessed in chip1/chipall/full. Full means source "
        "visible to the generator; extraction remains blind to source, model and channel. Loss, Violation and Assumption "
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
    (directory / "CAPTIONS.md").write_text("\n".join(lines) + "\n")

    examples = []
    story = json.loads((ROOT / "ideas/cycles/c1/story_evidence.json").read_text())
    for card in story['examples']:
        examples.extend((card['id'], record['run'], record) for record in card['outputs'])
    for record in json.loads((ROOT / "ideas/cycles/c1/hyp_examples.json").read_text()):
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
                    source_manifests=['ideas/cycles/c1/story_evidence.json','ideas/cycles/c1/hyp_examples.json'],
                    n_boot=2000, seed=20261031, examples=output)
    def clean_json(value):
        if isinstance(value, dict):
            return {k: clean_json(v) for k,v in value.items()}
        if isinstance(value, list):
            return [clean_json(v) for v in value]
        return None if isinstance(value, float) and not math.isfinite(value) else value
    (directory / "example_manifest.json").write_text(json.dumps(clean_json(manifest), indent=2, default=str, allow_nan=False) + "\n")
    print(f"refreshed captions and {len(output)} selected example occurrences")


if __name__ == "__main__":
    main()
