"""Independent, read-only acceptance audit of the closed W-C guard transfer (cycle-3).

Recomputes call counts, concurrency, wall clock, baseline parity and headline
arithmetic from the stored artifacts. No model, judge or network calls. Writes
only analysis/guard_wc/acceptance_check.json.
  OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/acceptance_check.py
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/guard_wc'
RUN = ROOT / 'runs/guard_wc'
sys.path.insert(0, str(ROOT / 'src'))
import analyze as A  # noqa: E402
import labels  # noqa: E402
import runio  # noqa: E402

KEY = ['model', 'family_id', 'variant', 'channel']
FROZEN = dict(retry_generation_http=2000, judge_batch_http=400, wall_clock_h=4.0,
              api_generation_concurrency=8, api_generation_concurrency_ceiling=12,
              judge_concurrency=12, local_slots=4)
LATER_OPERATIONAL_API_LIMIT = 8   # cycle-3 instruction for codex-lb; not part of FREEZE.md
API = {'gpt-6.1-terra', 'gpt-6.1-sol'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def peak(frame):
    events = sorted([(s, 1) for s in frame.start] + [(e, -1) for e in frame.end])
    cur = top = 0
    for _, d in events:
        cur += d
        top = max(top, cur)
    return top


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec='seconds')


def main():
    res = {'frozen_limits': FROZEN}
    # 1. Two call ledgers must agree row-for-row.
    csv = pd.read_csv(OUT / 'actual_calls.csv')
    with sqlite3.connect(OUT / 'budget.sqlite') as c:
        db = pd.read_sql('select * from calls order by id', c)
    assert csv.reset_index(drop=True).equals(db.reset_index(drop=True)), 'actual_calls.csv != budget.sqlite'
    launch = json.loads((OUT / 'launch.json').read_text())
    L = launch['start_epoch']
    assert abs(launch['deadline_epoch'] - L - 4 * 3600) < 1e-6
    status = {f'{k}/{s}': int(n) for (k, s), n in db.groupby(['kind', 'status']).size().items()}
    kinds = Counter(db.kind)
    logical = runio.read_jsonl(RUN / 'logical_calls.jsonl')
    gens = runio.read_jsonl(RUN / 'generations.jsonl')
    extra = sum(g.get('extra_calls', 0) for g in gens if g['prompt_id'] == 'G1')
    assert len(logical) == extra == kinds['generation']
    assert sum(g.get('extra_calls', 0) for g in gens if g['prompt_id'] == 'G1s') == 0
    adm = json.loads((OUT / 'admission.json').read_text())
    res['calls'] = dict(
        retry_generation_http=kinds['generation'],
        retry_generation_success=status.get('generation/200', 0),
        retry_generation_failed=kinds['generation'] - status.get('generation/200', 0),
        logical_guard_attempts=len(logical), judge_batch_http=kinds['judge'],
        judge_batch_success=status.get('judge/200', 0),
        judge_batch_failed=kinds['judge'] - status.get('judge/200', 0),
        by_kind_status=status, total_instrumented_http=len(db),
        generation_records=len(gens), admission=adm,
        within_retry_cap=kinds['generation'] <= FROZEN['retry_generation_http'],
        within_2F=kinds['generation'] <= 2 * 508,
        within_judge_cap=kinds['judge'] <= FROZEN['judge_batch_http'])
    # 2. Where could "937" come from?  Instrumented calls before the 13:28 local (UTC-6) resume.
    resume_first_judge = db[(db.kind == 'judge') & (db.start - L > 3000)].start.min()
    early = db[db.start < resume_first_judge]
    res['figure_937'] = dict(
        quoted_in=['orchestration/decision_log.md D-042 ("Action-6 generation complete (937 calls)")',
                   'ideas/cycles/c3/decision.md Action 1 ("reuse 937 completed calls")'],
        reproduced_exactly=False,
        retry_generation_http=kinds['generation'],
        instrumented_http_before_resume=len(early),
        instrumented_breakdown_before_resume=dict(Counter(early.kind)),
        note='No stored count equals 937. Generation used 766 HTTP calls; 766 generation + 170 failed '
             'pre-resume judge batches = 936 instrumented calls. 937 is most plausibly that pre-resume '
             'all-call total off by one (or including one uninstrumented request); it is not a generation count.')
    # 3. Concurrency against the frozen limits and against the later operational limit.
    peaks = {f'{k}/{m}': peak(g) for (k, m), g in db.groupby(['kind', 'model'])}
    api_gen = peak(db[(db.kind == 'generation') & db.model.isin(API)])
    judge = peak(db[db.kind == 'judge'])
    local = db[(db.kind == 'generation') & ~db.model.isin(API)]
    spans = sorted((g.start.min(), g.end.max(), m) for m, g in local.groupby('model'))
    nonoverlap = all(a[1] <= b[0] for a, b in zip(spans, spans[1:]))
    pre = db[(db.kind == 'judge') & (db.start < resume_first_judge)]
    post = db[(db.kind == 'judge') & (db.start >= resume_first_judge)]
    res['concurrency'] = dict(
        peaks_by_kind_model=peaks, api_generation_peak=api_gen, judge_peak=judge,
        judge_peak_pre_resume=peak(pre), judge_peak_resume=peak(post),
        local_peak_max=max(peak(g) for _, g in local.groupby('model')),
        local_server_windows_nonoverlapping=nonoverlap,
        local_windows_s_from_launch={m: [round(a - L, 1), round(b - L, 1)] for a, b, m in spans},
        within_frozen=(api_gen <= FROZEN['api_generation_concurrency'] and judge <= FROZEN['judge_concurrency']
                       and all(peak(g) <= FROZEN['local_slots'] for _, g in local.groupby('model')) and nonoverlap),
        within_later_operational_api_limit_8=max(api_gen, judge) <= LATER_OPERATIONAL_API_LIMIT)
    # 4. Wall clock and chronology.
    freeze_note = (OUT / 'FREEZE.md').read_text()
    res['wall_clock'] = dict(
        launch_utc=utc(L), deadline_utc=utc(launch['deadline_epoch']),
        first_call_utc=utc(db.start.min()), last_call_end_utc=utc(db.end.max()),
        last_call_end_h_after_launch=round((db.end.max() - L) / 3600, 4),
        all_calls_inside_window=bool(((db.start >= L) & (db.end <= launch['deadline_epoch'])).all()),
        resume_first_judge_utc=utc(resume_first_judge),
        freeze_written_before_launch='2026-11-01T18:28:32' in freeze_note and utc(L) > '2026-11-01T18:28:32')
    # The resume script's readiness probe (orchestration/guard_wc_resume.sh) is an HTTP request to
    # gpt-6.1-sol that the budget ledger does not instrument. Its loop sleeps 120 s after a failed
    # probe; the first resumed judge call starts <120 s after the 13:28 local (UTC-6) gate, so exactly one probe ran.
    gate = datetime(2026, 11, 1, 19, 28, tzinfo=timezone.utc).timestamp()
    res['uninstrumented_http'] = dict(
        source='orchestration/guard_wc_resume.sh readiness probe ("hi" to gpt-6.1-sol)',
        seconds_from_gate_to_first_resumed_judge=round(resume_first_judge - gate, 1),
        inferred_probe_calls=1 if resume_first_judge - gate < 120 else None,
        counted_in_budget=False)
    # 5. Baseline parity: values vs dtype, before and after the resume.
    items = runio.load_items(OUT / 'items.jsonl')
    base = A.normalize_table(pd.read_parquet(OUT / 'baseline_scored.parquet'), items).set_index(KEY).sort_index()
    cols = ['text', 'crit', *labels.GENERAL_DIMS, 'constraint_preserving']
    parity = {}
    for stage, path in [('before_resume', OUT / 'closure_inputs/before_resume_scored.parquet'),
                        ('after_resume', OUT / 'scored.parquet')]:
        f = pd.read_parquet(path)
        p0 = f[f.prompt_id.eq('P0')].set_index(KEY).sort_index()
        assert p0.index.equals(base.index)
        diffs = {c: int((~base[c].astype(object).where(base[c].notna(), '<NA>').eq(
            p0[c].astype(object).where(p0[c].notna(), '<NA>'))).sum()) for c in cols}
        parity[stage] = dict(
            value_differences=diffs,
            constraint_preserving_dtype=dict(baseline=str(base.constraint_preserving.dtype),
                                             p0=str(p0.constraint_preserving.dtype)),
            original_assertion_holds=all(base[c].fillna('MISSING').equals(p0[c].fillna('MISSING')) for c in cols),
            missing_constraint_preserving_by_arm={k: int(v) for k, v in
                                                  f.groupby('prompt_id').constraint_preserving.apply(lambda s: s.isna().sum()).items()})
    assert all(v == 0 for s in parity.values() for v in s['value_differences'].values())
    assert not parity['before_resume']['original_assertion_holds'] and parity['after_resume']['original_assertion_holds']
    parity['explanation'] = ('Before the resume, judgments were missing for changed G1/G1s texts, so the whole-frame '
                             'constraint_preserving column held None and became dtype object; the P0 slice inherited '
                             'that dtype. pandas .equals is dtype-sensitive, so the assertion failed although no P0 '
                             'value differed. After judging completed, the column is all-known bool and the original '
                             'assertion holds unchanged.')
    res['baseline_parity'] = parity
    # 6. Result hashes and headline arithmetic from the paired tables.
    hashes = json.loads((OUT / 'result_hashes.json').read_text())
    res['result_hash_mismatches'] = [p for p, h in hashes.items() if sha(OUT / p) != h]
    h = json.loads((OUT / 'headline.json').read_text())
    arith = {}
    for arm in ['G1', 'G1s']:
        p = pd.read_parquet(OUT / f'paired_{arm}.parquet')
        assert len(p) == 1872 and p.joint_P0.notna().all() and p.joint_arm.notna().all()
        fail, ok = p.strict_P0.eq(0), p.strict_P0.eq(1)
        a = dict(p0_joint=p.joint_P0.mean(), arm_joint=p.joint_arm.mean(), joint_gain=(p.joint_arm - p.joint_P0).mean(),
                 strict_repair_k=int((fail & p.strict_arm.eq(1)).sum()), strict_repair_n=int(fail.sum()),
                 changed_correct_k=int((ok & p.changed_arm).sum()), changed_correct_n=int(ok.sum()),
                 pass_to_fail_k=int((ok & p.strict_arm.eq(0)).sum()),
                 strict_residual_k=int(p.strict_arm.eq(0).sum()))
        q = h['paired'][arm]
        assert abs(a['joint_gain'] - q['joint_gain']['estimate']) < 1e-12
        assert a['strict_repair_k'] == q['strict_repair']['k'] and a['strict_repair_n'] == q['strict_repair']['n']
        assert a['changed_correct_k'] == q['strict_changed_correct']['k'] and a['changed_correct_n'] == q['strict_changed_correct']['n']
        assert a['pass_to_fail_k'] == q['strict_pass_to_fail']['k']
        arith[arm] = a
    g = h['paired']['G1']
    crit = dict(repair_ge_30=g['strict_repair']['estimate'] >= .30,
                changed_correct_le_10=g['strict_changed_correct']['estimate'] <= .10,
                joint_gain_lower_gt_0=g['joint_gain']['ci_low'] > 0)
    assert crit == {k: h['criteria'][k2] for k, k2 in [('repair_ge_30', 'repair_ge_30'),
                    ('changed_correct_le_10', 'changed_correct_le_10'),
                    ('joint_gain_lower_gt_0', 'positive_joint_gain_lower95_gt0')]}
    res['headline_arithmetic'] = arith
    res['criteria_recomputed'] = crit
    v = json.loads((OUT / 'verification.json').read_text())
    res['verify_results'] = dict(passed=v['passed'], closure_comparator_verified=v.get('closure_comparator_verified'),
                                 current_api_concurrency_limit_8_met=v.get('current_api_concurrency_limit_8_met'))
    res['verdict'] = ('ACCEPT WITH QUALIFICATIONS' if not res['result_hash_mismatches'] and all(crit.values())
                      and res['calls']['within_retry_cap'] and res['calls']['within_judge_cap']
                      and res['concurrency']['within_frozen'] and res['wall_clock']['all_calls_inside_window']
                      else 'REJECT')
    (OUT / 'acceptance_check.json').write_text(json.dumps(res, indent=2, default=str) + '\n')
    print(json.dumps({k: res[k] for k in ['verdict', 'calls', 'figure_937', 'concurrency', 'uninstrumented_http']},
                     indent=1, default=str))


if __name__ == '__main__':
    main()
