"""Current human-gate notice shared by report generators; reads local evidence only."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def human_gate_notice():
    h = json.loads((ROOT / 'annotation/judge_validation_main1.json').read_text())['human']
    tests = [v['sampled_test/final'] for v in h['judge'].values()]
    assert len(tests) == 7 and all(v['kappa'] >= .6 for v in tests)
    v = h['verdict']['violation']['primary']
    return (
        '**D-031 supersession (cycle-3 Action 3, 2026-11-01).** '
        'The earlier main1 human extraction gate H7 **passed**. '
        f"Two annotators labeled {h['n_items']} items (100 double-coded core, 87 single-coded extras); "
        f"held-out `sampled_test/final` κ={min(x['kappa'] for x in tests):.3f}–"
        f"{max(x['kappa'] for x in tests):.3f}, lowest lower 95% bound "
        f"{min(x['kappa_ci'][0] for x in tests):.3f}, n={min(x['n'] for x in tests)}–"
        f"{max(x['n'] for x in tests)} across seven fields. "
        f"Violation agreement {v['agree_k']}/{v['n']} "
        f"[{100*v['agree_ci'][0]:.1f}, {100*v['agree_ci'][1]:.1f}]%, κ={v['kappa']:.3f}; "
        f"both positive {v['judge_T_ref_T']}, judge-only {v['judge_T_ref_F']}, "
        f"human-only {v['judge_F_ref_T']}, both negative {v['judge_F_ref_F']}. "
        'Plurality reference, ties/unsure excluded; converted human labels, no per-item times; no adjudication. '
        'This supersedes every historical “human pending”, “zero human returns”, and '
        '“human gate not evaluable” statement below **only for that earlier extraction inventory**. '
        'Historical machine-panel tables remain unchanged. Humans corrected the shared “can’t wait” '
        'error; they did not resolve every shared key departure (D-033). '
        'H7 does not validate repaired-text completeness, complete meaning, W-B admissibility, '
        'or every new W-C/W-D/guard-transfer boundary. '
        'Evidence: [human validation JSON](../../annotation/judge_validation_main1.json), '
        '[gate log](../oracle/human_gate.log), '
        '[current evidence map](../EVIDENCE_MAP.md). Inline “→ D-031” pointers mark each stale prose statement; '
        'historical table cells (e.g. “not evaluable, 0 human returns”, “human gate pending”) are kept verbatim as the pre-H7 record.\n'
    )


POINTER = ' *[→ D-031: superseded for the earlier main1 inventory; H7 passed, see notice at top]*'
# Stale pre-H7 prose; table rows are left verbatim (historical record).
STALE = ['human oracle validation is pending.',
         'and no human returns exist yet (annotation/returns/ is absent).**',
         'There are zero human returns.',
         'stay provisional until the human double-coding of gold_core',
         'Remaining W-A work: human double-coding of gold_core (100 items) with `score_gold.py --human`;']


def point_stale(text):
    out = []
    for line in text.replace(POINTER, '').split('\n'):
        if not line.lstrip().startswith('|'):
            for phrase in STALE:
                line = line.replace(phrase, phrase + POINTER)
        out.append(line)
    return '\n'.join(out)


def annotate_report(path):
    """Idempotently mark a retained historical report without changing its tables."""
    text = point_stale(path.read_text())
    marker = '<!-- CURRENT_H7_STATUS -->'
    if marker in text:
        first, rest = text.split(marker, 1)
        _, rest = rest.split('<!-- END_CURRENT_H7_STATUS -->', 1)
        text = first + rest.lstrip('\n')
    title, rest = text.split('\n', 1)
    path.write_text(title + '\n\n' + marker + '\n' + human_gate_notice() +
                    '<!-- END_CURRENT_H7_STATUS -->\n\n' + rest.lstrip('\n'))


if __name__ == '__main__':
    for relative in ['analysis/oracle/report.md', 'analysis/interventions/report.md']:
        annotate_report(ROOT / relative)
        n = (ROOT / relative).read_text().count(POINTER)
        print(relative, 'inline D-031 pointers:', n)
