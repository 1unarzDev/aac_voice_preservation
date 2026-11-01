"""Offline integration checks on the actual frozen evidence, not model calls."""
from __future__ import annotations

import hashlib
import json
import re

import pandas as pd

from resolve_labels import DEFAULT_RUNS, build
from runio import ROOT, read_jsonl, load_items


def main():
    table = read_jsonl(ROOT / "annotation/label_resolution.jsonl")
    assert table == build(DEFAULT_RUNS), "Resolution is not reproducible from production judgments"
    keys = [(r['text_id'], r['input_text'], r['dimension']) for r in table]
    assert len(keys) == len(set(keys))
    lookup = dict(zip(keys, table))
    frozen = json.loads((ROOT / "analysis/EVIDENCE_MANIFEST_prev.json").read_text())
    old_hash = {r['path']:r['sha256'] for r in frozen['files']}
    frames = {}
    total_rows = 0
    for run in DEFAULT_RUNS:
        df = pd.read_parquet(ROOT / f"runs/{run}/scored.parquet")
        frames[run] = df
        total_rows += len(df)
        assert not df.critical_source.isin(['J1','J2']).any()
        for r in df[df.valid].itertuples():
            authoritative = lookup[(r.text_id, r.input_text, r.dimension)]
            value = None if pd.isna(r.critical) else r.critical
            source = None if pd.isna(r.critical_source) else r.critical_source
            assert value == authoritative['critical'], (run,r.output_id)
            assert source == authoritative['critical_source'], (run,r.output_id)
        old = ROOT / f"runs/{run}/scored_prev.parquet"
        if old.exists():
            assert hashlib.sha256(old.read_bytes()).hexdigest() == old_hash[f"runs/{run}/scored.parquet"]
        endpoint = json.loads((ROOT / f"runs/{run}/endpoints.json").read_text())
        assert endpoint['n_rows'] == len(df[~df.quarantine_refusal_acceptance])
        assert endpoint['sensitivity_including_quarantine']['n_rows'] == len(df)
    combined = pd.concat(list(frames.values()), ignore_index=True)
    assert combined.groupby(['text_id','input_text','dimension']).critical.nunique(dropna=False).max() == 1
    for run in ['main1','span1']:
        df = frames[run]
        x = df[df.channel.eq('bare') & df.prompt_id.eq('P2') & df.dimension.eq('polarity') & df.variant.eq('A')]
        values = x.groupby(['family_id','model']).chose.agg(lambda s: {'A','B'} <= set(s.dropna()))
        assert (int(values.sum()),len(values)) == (10,40), run
    primary = pd.read_parquet(ROOT / 'analysis/main1/scored.parquet')
    inclusive = pd.read_parquet(ROOT / 'analysis/main1_quarantine_inclusive/scored.parquet')
    assert primary.family_id.nunique() == 58 and inclusive.family_id.nunique() == 60
    assert not primary.family_id.isin(['act-10','act-16']).any()
    assert inclusive.family_id.isin(['act-10','act-16']).any()
    numbers = json.loads((ROOT / 'paper/figs/fig_numbers.json').read_text())
    macros = dict(re.findall(r'\\resdef\{([^}]+)\}\{([^}]+)\}', (ROOT / 'paper/se4all/results_macros.tex').read_text()))
    for channel in ['bare','noncrit','chip1','chipall','full']:
        figure = numbers['fig_channel_ladder']['all_dims'][channel]
        for suffix,key in [('', 'estimate'),('_lo','ci_low'),('_hi','ci_high')]:
            assert macros[f'match_{channel}{suffix}'] == f"{100*figure[key]:.1f}"
    for prompt in ['P2','S3']:
        assert macros[f'cov_{prompt.lower()}_all'] == f"{100*numbers['fig_sets']['pooled'][prompt]['estimate']:.1f}"
    identity = frames['oracle_inject'][frames['oracle_inject'].model.eq('identity')]
    items = load_items(ROOT / 'data/items/test.jsonl')
    assert len(identity) == 120 and identity.constraint_preserving.eq(True).all()
    assert all(r.text == items[r.family_id]['variants'][r.variant]['source'] for r in identity.itertuples())
    intervention = json.loads((ROOT / 'analysis/interventions/report.json').read_text())
    assert intervention['guard']['G1_cue']['n_bad'] == 80
    assert intervention['guard']['G1_cue']['fix']['estimate'] == 63/80
    assert intervention['span']['polarity+certainty']['P2']['estimate'] == 15/80
    assert intervention['span']['polarity+certainty']['I2']['estimate'] == 78/80
    for group, arms in intervention['span'].items():
        if isinstance(arms, dict):
            for arm, estimate in arms.items():
                if isinstance(estimate, dict) and 'n_total' in estimate:
                    assert estimate['n_total'] == estimate['n'] + estimate['n_missing'], (group,arm)
    example_manifest = json.loads((ROOT / 'paper/figs/example_manifest.json').read_text())
    assert len(example_manifest['examples']) == 33
    for cid in ['C7','C8','C11','C13','C14','C15','C16']:
        assert any(l.startswith(f'| {cid} |') and '**refreshed**' in l
                   for l in (ROOT / 'orchestration/claims_ledger.md').read_text().splitlines())
    assert (ROOT / 'orchestration/claims_ledger.md').read_text().startswith(
        (ROOT / 'analysis/evidence_prev/orchestration/claims_ledger.md').read_text())
    outcome = dict(status='passed', runs=DEFAULT_RUNS, resolved_units=len(table), target_rows_verified=total_rows,
                   shared_critical_consistency=True, preserved_scored_hashes=True,
                   primary_quarantine_excluded=True, macros_and_figures_agree=True,
                   main_and_span_polarity_P2='10/40', identity_contract='120/120',
                   selected_example_occurrences=33, regression_tests='tests/test_resolution.py; tests/test_analyze.py; tests/test_layer0.py')
    (ROOT / 'analysis/verify_reconciliation.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(outcome))


if __name__ == '__main__':
    main()
