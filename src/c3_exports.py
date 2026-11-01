"""Shared c3 numeric macros for the two target papers. No printed statistic is hand-entered.

Source: analysis/evidence_c3/current.json (written by src/c3_evidence.py). The C36 first-output macros
`c3_app_first_<arm>` cover arms p0, p2, s3, p2_minus_s3 and p2_minus_p0. Each is self-checked against its own
row of analysis/applicability/first_slot_diagnostics.csv (channel=full). `c3_app_first_p0` is the P0 single
output (38/1,850, CI [1.41, 2.76]). Its count equals S3's first-slot count (38/1,850, CI [1.39, 2.79]) by
coincidence. It is a distinct population, checked independently against P0's any-of-set count in
analysis/applicability/sets_full.csv. Papers comparing P2 with sample sets must use `c3_app_first_s3`.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _first_slot_rows():
    with (ROOT / 'analysis/applicability/first_slot_diagnostics.csv').open() as f:
        return {r['arm']: r for r in csv.DictReader(f)
                if r['channel'] == 'full' and r['endpoint'] == 'first_output_mismatch'}


def _p0_any_of_set():
    k = m = 0
    with (ROOT / 'analysis/applicability/sets_full.csv').open() as f:
        for r in csv.DictReader(f):
            if r['matched'] == 'True' and r['prompt'] == 'P0':
                m += 1
                k += r['any_fail'] in ('True', '1', '1.0')
    return k, m


def macros():
    d = json.loads((ROOT / 'analysis/evidence_c3/current.json').read_text())['evidence']
    c = d['C35']
    m = {'c3_guard_increment': f"{c['estimate_pp']:.2f}",
         'c3_guard_increment_lo': f"{c['ci95_pp'][0]:.2f}",
         'c3_guard_increment_hi': f"{c['ci95_pp'][1]:.2f}",
         'c3_guard_increment_n': f"{c['n']:,}",
         'c3_guard_increment_clusters': str(c['n_families']),
         'c3_guard_g1_only': str(c['G1_only_pass']), 'c3_guard_strip_only': str(c['G1s_only_pass'])}
    for arm, k in c['pass_counts'].items():
        m[f'c3_guard_pass_{arm.lower()}'] = f'{k:,}'
    rows = _first_slot_rows()
    for arm, r in d['C36'].items():
        # Self-check: every arm's macro comes from that arm's own CSV row, never a neighbour's.
        src = rows[arm]
        for key in ('estimate', 'lo', 'hi'):
            assert abs(r[key] - float(src[key])) < 1e-12, (arm, key)
        if 'k' in r:
            assert int(r['k']) == int(float(src['k'])) and int(r['n']) == int(float(src['n'])), arm
        prefix = 'c3_app_first_' + arm.lower()
        for k, suffix in [('estimate', ''), ('lo', '_lo'), ('hi', '_hi')]:
            m[prefix + suffix] = f"{100*r[k]:.2f}"
        for k in ['k', 'n', 'clusters']:
            if k in r:
                m[prefix + '_' + k] = f"{int(r[k]):,}"
    assert (int(d['C36']['P0']['k']), d['C36']['P0']['n']) == _p0_any_of_set(), 'P0 first-slot != P0 single output'
    assert m['c3_app_first_s3_lo'] != m['c3_app_first_p0_lo'], 'P0 and S3 macros must be distinct rows'
    return m


if __name__ == '__main__':
    for key, value in sorted(macros().items()):
        print(key, value)
