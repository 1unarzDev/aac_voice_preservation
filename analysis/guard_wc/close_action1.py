"""CPU-only closure of the completed resume; no generation/judging or baseline writes.

Consumes the preserved resume snapshot. Frozen launch code is deliberately unchanged.
Run with OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/close_action1.py.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/guard_wc'
SNAP = OUT / 'closure_inputs'
sys.path.insert(0, str(ROOT / 'src'))
import analyze as A
import labels
import runio

spec = importlib.util.spec_from_file_location('guard_analysis', OUT / 'analyze.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(G.clean(data), indent=2, ensure_ascii=False) + '\n')


def parity(reference, candidate, cols, stage):
    """Compare keyed values after normalizing nulls, independently of pandas dtype."""
    x = reference.set_index(G.KEY).sort_index()
    y = candidate.set_index(G.KEY).sort_index()
    assert x.index.equals(y.index), stage
    rows = []
    diffs = []
    for col in cols:
        same = x[col].astype(object).where(x[col].notna(), '<MISSING>').eq(
            y[col].astype(object).where(y[col].notna(), '<MISSING>'))
        rows.append(dict(stage=stage, column=col, n_rows=len(x), value_differences=int((~same).sum()),
                         reference_dtype=str(x[col].dtype), candidate_dtype=str(y[col].dtype),
                         pandas_series_equals=x[col].fillna('MISSING').equals(y[col].fillna('MISSING'))))
        for key in x.index[~same]:
            diffs.append(dict(stage=stage, **dict(zip(G.KEY, key)), column=col,
                              reference=str(x.loc[key, col]), candidate=str(y.loc[key, col])))
    return rows, diffs


def main():
    assert 'RESUMEDONE' in (SNAP / 'analyze_resume.log').read_text()
    for name, digest in json.loads((SNAP / 'manifest.json').read_text()).items():
        assert sha(SNAP / name) == digest, name
    for name, digest in json.loads((OUT / 'inventory_hashes.json').read_text()).items():
        assert sha(OUT / name) == digest, name
    for name, digest in json.loads((OUT / 'input_hashes.json').read_text()).items():
        assert sha(OUT / 'frozen' / name) == digest, name
    for name, digest in json.loads((OUT / 'launch_manifest.json').read_text())['code_hashes'].items():
        assert sha(ROOT / name) == digest, name
    items = runio.load_items(OUT / 'items.jsonl')
    base = pd.read_parquet(OUT / 'baseline_scored.parquet')
    frozen_base = pd.read_parquet(OUT / 'frozen/runs/r2c1/scored.parquet')
    frozen_base = frozen_base[frozen_base.prompt_id.eq('P0') &
        frozen_base.family_id.isin(base.family_id.unique()) & frozen_base.channel.isin(['chip1', 'chipall', 'full'])]
    # The subset's parquet round trip narrows all-known object booleans to bool.
    pd.testing.assert_frame_equal(base.reset_index(drop=True), frozen_base.reset_index(drop=True), check_dtype=False)
    ref = A.normalize_table(base, items)
    old = pd.read_parquet(SNAP / 'before_resume_scored.parquet')
    frame = pd.read_parquet(SNAP / 'scored.parquet')
    cols = ['text', 'crit', *labels.GENERAL_DIMS, 'constraint_preserving']
    rows, diffs = parity(ref, old[old.prompt_id.eq('P0')], cols, 'before_resume')
    r, d = parity(ref, frame[frame.prompt_id.eq('P0')], cols, 'after_resume')
    rows += r
    diffs += d
    assert not diffs, diffs
    # Regression fixture: this is the exact historical false alarm, reduced to P0.
    cp = next(r for r in rows if r['stage'] == 'before_resume' and r['column'] == 'constraint_preserving')
    assert cp['value_differences'] == 0 and not cp['pandas_series_equals']
    pd.DataFrame(rows).to_csv(OUT / 'baseline_parity_columns.csv', index=False)
    pd.DataFrame(diffs, columns=['stage', *G.KEY, 'column', 'reference', 'candidate']).to_csv(
        OUT / 'baseline_parity_diff.csv', index=False)
    assert len(frame) == 5616 and not frame.duplicated(G.KEY + ['prompt_id']).any()
    assert frame.groupby('prompt_id').size().to_dict() == {'G1': 1872, 'G1s': 1872, 'P0': 1872}
    pairs = {a: G.pair_frame(frame, a) for a in ['G1', 'G1s']}
    head = json.loads((SNAP / 'headline.json').read_text())
    for arm, p in pairs.items():
        for ep in ['joint', 'strict']:
            assert abs((p[ep + '_arm'] - p[ep + '_P0']).mean() -
                       head['paired'][arm][ep + '_gain']['estimate']) < 1e-12
    # Same target rows, same resampling group, direct regeneration vs zero-call comparator.
    g = frame[frame.prompt_id.eq('G1')].set_index(G.KEY).sort_index()
    s = frame[frame.prompt_id.eq('G1s')].set_index(G.KEY).sort_index()
    comparator = {}
    for ep in ['joint', 'strict']:
        t = g.reset_index()
        delta = (g[ep] - s[ep]).to_numpy()
        comparator[ep] = dict(family=G.metric(t, delta), recorded_cluster=G.metric(t, delta, cluster='cluster_id'),
            G1_only_pass=int((g[ep].eq(1) & s[ep].eq(0)).sum()),
            G1s_only_pass=int((s[ep].eq(1) & g[ep].eq(0)).sum()))
    judgments = runio.read_jsonl(ROOT / 'runs/guard_wc/judgments.jsonl')
    jj = {(r['text_id'], r['family_id'], r['input_text']): r for r in judgments}
    raw = pd.read_parquet(ROOT / 'runs/guard_wc/scored.parquet')
    # Every unresolved row is an extraction disagreement still lacking new arbitration,
    # but frozen baseline reuse can make the selected evaluated outcome known.
    unresolved = []
    for u in runio.read_jsonl(SNAP / 'unresolved.jsonl'):
        match = raw[raw.text_id.eq(u['text_id']) & raw.family_id.eq(u['family_id']) & raw.input_text.eq(u['input_text'])]
        assert len(match) and match.evaluation_provenance.eq('frozen first-pass label reuse').all()
        for r in match.to_dict('records'):
            unresolved.append(dict(text_id=u['text_id'], family_id=r['family_id'], variant=r['variant'],
                channel=r['channel'], model=r['model'], arm=r['prompt_id'], J1=u['J1_critical'], J2=u['J2_critical'],
                retained_critical=r['critical'], retained_source=r['critical_source'],
                provenance=r['evaluation_provenance']))
    pd.DataFrame(unresolved).to_csv(OUT / 'unresolved_reconciliation.csv', index=False)
    disagreements = []
    sens = frame.copy()
    for ix, r in sens.iterrows():
        j = jj[(r.text_id, r.family_id, r.input_text)]
        for dim in labels.GENERAL_DIMS:
            if j['J1_' + dim] != j['J2_' + dim]:
                disagreements.append(dict(arm=r.prompt_id, model=r.model, family_id=r.family_id,
                    variant=r.variant, channel=r.channel, text_id=r.text_id, dimension=dim,
                    J1=j['J1_' + dim], J2=j['J2_' + dim], L0=j['L0_' + dim], production=r[dim]))
                sens.at[ix, dim] = None
    pd.DataFrame(disagreements).to_csv(OUT / 'general_label_disagreements.csv', index=False)
    sens = A.normalize_table(sens, items)
    assert sens.constraint_preserving.equals(frame.constraint_preserving)
    # Validate every displayed quotation AND the prospective category/hash selection.
    outputs = {(r['output_id'], r['family_id'], r['variant'], r['channel']): r
               for r in runio.read_jsonl(ROOT / 'runs/guard_wc/outputs.jsonl')}
    for e in json.loads((SNAP / 'examples.json').read_text()):
        p = pairs[e['arm']]
        if 'fail→pass' in e['category']:
            event = p.strict_P0.eq(0) & p.strict_arm.eq(1)
            eligible = p.strict_P0.eq(0)
        elif e['category'] == 'residual strict failure':
            event = p.strict_arm.eq(0)
            eligible = p.strict_arm.notna()
        else:
            eligible = p.strict_P0.eq(1)
            event = eligible & p.changed_arm
        assert int(event.sum()) == e['event_k'] and int(eligible.sum()) == e['eligible_n']
        hashes = [hashlib.sha256(json.dumps([r.base_key_P0, r.family_id, r.variant, r.channel],
                   ensure_ascii=False).encode()).hexdigest() for r in p[event].itertuples()]
        assert e['selection_sha256'] == min(hashes)
        for prefix, textcol in [('before', 'before'), ('after', 'after')]:
            o = outputs[(e[prefix + '_output_id'], e['family_id'], e['variant'], e['channel'])]
            assert o['text'] == e[textcol] and o['input_text'] == e['input_text']
    with sqlite3.connect(f'file:{OUT / "budget.sqlite"}?mode=ro', uri=True) as c:
        calls = pd.read_sql_query('select * from calls order by id', c)
    launch = json.loads((OUT / 'launch.json').read_text())
    # Original cost() ran at analysis START. The commit containing the exact completed
    # artifacts supplies a conservative completion upper bound, including CPU analysis.
    analysis_start_elapsed = head['cost']['wall_elapsed_s']
    completion_commit = '55d85db2e41f2a37e821ee740736e3be7b2e6a70'
    for name in ['report.md', 'headline.json', 'result_hashes.json']:
        committed = subprocess.check_output(['git', 'show', f'{completion_commit}:analysis/guard_wc/{name}'], cwd=ROOT)
        assert committed == (SNAP / name).read_bytes(), name
    completed = int(subprocess.check_output(['git', 'show', '-s', '--format=%ct', completion_commit], cwd=ROOT))
    elapsed = completed - launch['start_epoch']
    assert calls.end.notna().all() and calls.status.notna().all()
    assert calls.start.ge(launch['start_epoch']).all() and calls.end.le(completed).all()
    assert completed <= launch['deadline_epoch']
    counts = calls.groupby(['kind', 'status']).size().reset_index(name='n')
    counts.to_csv(OUT / 'http_call_counts.csv', index=False)
    assert calls.kind.value_counts().to_dict() == {'generation': 766, 'judge': 207}
    assert int((calls.kind.eq('generation') & calls.status.eq(200)).sum()) == 726
    assert int((calls.kind.eq('judge') & calls.status.eq(200)).sum()) == 34
    # Existing resume used judge concurrency 12. Disclose it; this closure makes no API calls.
    events = sorted([(r.start, 1) for r in calls[calls.kind.eq('judge')].itertuples()] +
                    [(r.end, -1) for r in calls[calls.kind.eq('judge')].itertuples()], key=lambda v: (v[0], v[1]))
    live = peak = 0
    for _, delta in events:
        live += delta
        peak = max(peak, live)
    cost_audit = dict(actual_generation_http_calls=766, successful_generation_http_calls=726,
        failed_generation_http_calls=40, judge_batch_http_calls=207, successful_judge_batches=34,
        failed_judge_batches=173, total_instrumented_http_calls=973, new_arbitration_calls=0,
        closure_generation_calls=0, closure_judge_calls=0,
        recorded_analysis_start_elapsed_s=analysis_start_elapsed,
        completed_analysis_elapsed_upper_bound_s=elapsed, completion_evidence_commit=completion_commit,
        completed_analysis_utc_upper_bound=datetime.fromtimestamp(completed, timezone.utc).isoformat(),
        last_instrumented_http_end_utc=datetime.fromtimestamp(float(calls.end.max()), timezone.utc).isoformat(),
        original_launch_utc=datetime.fromtimestamp(launch['start_epoch'], timezone.utc).isoformat(),
        original_deadline_utc=datetime.fromtimestamp(launch['deadline_epoch'], timezone.utc).isoformat(),
        judge_peak_concurrency=peak, inherited_resume_exceeds_current_concurrency_8=peak > 8,
        resource_caps_met=True, memo_937_generation_count_supported=False)
    write('closure_audit.json', dict(baseline_value_differences=0, historical_parity_failure='dtype-only bool versus object',
        comparator=comparator, cost=cost_audit, unresolved_J_units=10,
        unresolved_selected_target_rows=len(unresolved), new_selected_critical_unknowns=0,
        general_disagreement_target_fields=len(disagreements),
        general_disagreement_fields_by_dimension=dict(Counter(d['dimension'] for d in disagreements)),
        general_agreement_only_joint_outcome_changes=0, all_displayed_examples_verified=True,
        source_snapshot_manifest_sha256=sha(SNAP / 'manifest.json')))
    supplement = render_supplement(head, comparator, cost_audit, unresolved, disagreements)
    original = (SNAP / 'report.md').read_text()
    original = original.replace('New unresolved critical J-units: **10**; distinct A-units: **10**.',
        'Critical disagreements without a run-local arbiter entry: **10 J-units / 10 A-units**; '
        'every affected selected output reuses an already arbitrated frozen baseline label (see closure audit).')
    original = original.replace('Reproduce locally: `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/analyze.py --exit-code 0`.',
        'Reproduce the closed result locally: `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/close_action1.py`. '
        'The original analyzer and its launch hash remain unchanged; closure uses the completed resume snapshot and its recorded completion time.')
    original = original.replace('Elapsed through analysis 3605.3 s / 14,400 s.',
        f'Elapsed at analysis start 3605.3 s; completed-artifact commit bounds full elapsed at {elapsed:.1f} s / 14,400 s (closure audit below).')
    original = original.replace('Resource records include every HTTP attempt without secrets.',
        'Resource records count instrumented generator retries and judge batches; availability-probe traffic is disclosed separately below.')
    original = original.replace('API concurrency 8 and judge concurrency 12.',
        'Historical generation API concurrency 8 and inherited judge concurrency 12; the latter exceeds the current user limit of 8 and is disclosed below. Closure makes no API calls.')
    (OUT / 'report.md').write_text(original + supplement)
    head['closure'] = json.loads((OUT / 'closure_audit.json').read_text())
    head['G1_minus_G1s'] = comparator
    write('headline.json', head)
    files = list(json.loads((SNAP / 'result_hashes.json').read_text())) + [
        'closure_audit.json', 'baseline_parity_columns.csv', 'baseline_parity_diff.csv',
        'unresolved_reconciliation.csv', 'general_label_disagreements.csv', 'http_call_counts.csv', 'close_action1.py', 'verify_results.py']
    write('result_hashes.json', {name: sha(OUT / name) for name in files})
    print(json.dumps(dict(status='closed', transfer_success=head['transfer_success'],
                         comparator=comparator, cost=cost_audit), indent=2))


def render_supplement(head, comparator, cost, unresolved, disagreements):
    lines = ['\n## Cycle-3 Action 1 closure audit (2026-11-01)\n',
        'This closure consumes the existing completed resume after `RESUMEDONE`; it performs **0 generation / 0 judge / 0 arbiter calls**, '
        'starts no GPU server, and changes neither the frozen baseline, arbitration, inventory, policy nor launch budget. '
        'The automatically produced resume report and numeric files are preserved under `closure_inputs/`, with hashes in its manifest.\n',
        '### Baseline parity and the earlier completion marker\n',
        '`baseline_parity_columns.csv` compares all 1,872 P0 rows by model/family/variant/channel, before and after the resume, '
        'against `baseline_scored.parquet`: **zero differences** in text, critical label, all five general labels and normalized joint pass. '
        '`baseline_parity_diff.csv` is the empty row/column value diff. The historical failing table is byte-preserved from git '
        '`9a61459` as `closure_inputs/before_resume_scored.parquet`. The minimized failure is pandas '
        '`Series.equals`: identical P0 values had dtype `bool` in the baseline and `object` in the combined table because other arms had nulls. '
        'Value comparison with explicit null normalization passes; the frozen code is preserved rather than retrospectively changing its hash.\n',
        'The earlier `GUARD_WC_COMPLETE` marker meant the shell commands returned, not that labels or analysis were complete. '
        'The original judge logged 170 failed HTTP attempts, zero successful batches, and 166 A / 240 B uncached units still missing per prompt. '
        'Its driver nevertheless returned successfully; the EXIT-trap analysis failed its dtype-sensitive parity assertion. '
        'That table had G1 critical/joint/strict labels for only **1,708/1,872** targets and G1s for **1,790/1,872**. '
        'Neither marker nor the partial parquet established evaluated transfer. The resume logged zero uncached units still missing in all four passes, '
        'and all three arms now have **1,872/1,872** known critical/joint/strict outcomes.\n',
        '### Direct comparator and joint-preservation harms\n',
        '| arm | joint passes / planned | strict passes / planned | unknown joint / strict |',
        '|---|---|---|---|',
        *[f'| {a} | {G.count(head["arms"][a]["joint_pass"]) } | {G.count(head["arms"][a]["strict_pass"])} | 0 / 0 |'
          for a in ['P0', 'G1s', 'G1']],
        '\n',
        '| endpoint, G1−G1s | paired gain, pp [95% family CI] | G1-only / G1s-only passes | recorded-cluster CI, pp |',
        '|---|---|---|---|']
    for ep, r in comparator.items():
        f = r['family']; c = r['recorded_cluster']
        lines.append(f'| {ep} | {100*f["estimate"]:.2f} [{100*f["ci_low"]:.2f}, {100*f["ci_high"]:.2f}] | '
                     f'{r["G1_only_pass"]} / {r["G1s_only_pass"]} | [{100*c["ci_low"]:.2f}, {100*c["ci_high"]:.2f}] |')
    lines += ['\nAll 1,872 identical target occurrences are paired; 78 whole-family clusters and 55 recorded seed/construction clusters, '
        '10,000 resamples, seed 20261101. This compares stored configurations; it does not isolate a causal contribution of feedback.\n',
        '| arm | joint failures repaired | joint-correct texts changed | joint pass→fail |', '|---|---|---|---|']
    for arm in ['G1', 'G1s']:
        p = head['paired'][arm]
        lines.append(f'| {arm} | {G.count(p["joint_repair"])}; {G.fmt(p["joint_repair"])} | '
                     f'{G.count(p["joint_changed_correct"])}; {G.fmt(p["joint_changed_correct"])} | '
                     f'{G.count(p["joint_pass_to_fail"])}; {G.fmt(p["joint_pass_to_fail"])} |')
    lines += ['\nThe two G1s joint pass→fail outcomes arise among initially joint-correct outputs; those outputs were already strict failures '
        'because of added politeness. Thus zero strict pass→fail and two joint pass→fail for G1s are compatible. '
        'All repair/change rates above count target occurrences, with deduplicated request-level resource units kept separate.\n',
        '### Resolution and general-label dependence\n',
        f'All **10** rows in the run-local unresolved extraction list concern selected outcomes with frozen first-pass label reuse '
        f'(**{len(unresolved)} arm/target rows**; `unresolved_reconciliation.csv`). Their baseline arbitration remains authoritative. '
        'There are **zero new changed-output unresolved critical labels** in the selected returns and zero new arbiter calls. '
        'Do not call these ten new unresolved treated outputs, or substitute J1 for them.\n',
        f'`general_label_disagreements.csv` enumerates **{len(disagreements)} target×arm×dimension fields** where the production rule can use L0. '
        'The agreement-only sensitivity actually removes these fields and recomputes the endpoint; it changes **zero joint outcomes**. '
        'Disagreements on the focal dimension are handled by the critical label, while unsupplied/unscored predicates and known failures '
        'can leave the joint endpoint unchanged. Identical sensitivity estimates do not imply universal judge agreement.\n',
        '### Calls, elapsed time and deviations\n',
        f'The shared, never-reset SQLite counter records **766 generation HTTP calls (726 successful, 40 failed)** and '
        '**207 judge-batch HTTP calls (34 successful, 173 failed)**, **973 instrumented HTTP calls total**. '
        'Generation logical attempts are 766 with zero cache hits. The pre-resume database contains 766 generation plus 170 failed judge calls '
        '(936 instrumented calls). The decision memo’s “937 generation calls” is unsupported by generation traces or the HTTP counter; '
        'it is not used as the generator denominator. The resume shell also makes an uninstrumented availability probe before judging; '
        'no probe attempt ledger exists, so its exact HTTP count is unknown. It is not a generator retry or a judge batch. '
        'No claim of complete endpoint-wide HTTP accounting is made.\n',
        f'Original launch: **{cost["original_launch_utc"]}**. The original 3605.3 s cost measurement was taken at analysis start, '
        f'not completion. Git commit `{cost["completion_evidence_commit"]}` contains the exact completed report, headline and result hashes '
        f'by **{cost["completed_analysis_utc_upper_bound"]}**, bounding full elapsed at **{cost["completed_analysis_elapsed_upper_bound_s"]:.1f} s**, '
        'including the rate-limit wait and analysis, '
        f'before the unchanged **{cost["original_deadline_utc"]}** deadline. Last instrumented response: '
        f'**{cost["last_instrumented_http_end_utc"]}**. All recorded responses completed before analysis. '
        'Resource caps 2,000 generation / 400 judge batches / 14,400 s were met; subsequent CPU-only auditing does not reset or extend the experiment.\n',
        f'**Concurrency deviation:** the inherited, already completed resume reached **{cost["judge_peak_concurrency"]} concurrent judge HTTP requests**. '
        'That follows its original launch configuration but exceeds this task’s current ≤8 API instruction. It is disclosed rather than hidden; '
        'this closure sends no API requests and does not relaunch any work. This deviation is separate from the frozen call/time transfer criteria.\n',
        '### Verdict and reproduction\n',
        '**The completed fixed inventory meets all frozen scored-transfer criteria within its original call/time budget.** '
        'The observed call failures, rate-limit interruption and inherited concurrency deviation remain disclosed. '
        'This is scored partial-predicate transfer on the fixed roster, with W-C’s early-cache and post-outcome arbitration qualifications. '
        'It supplies no independent usable-repair, fluency, deployment or human-effect evidence. No paper or claims-ledger promotion is performed by this action.\n',
        'Reproduce: `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/close_action1.py`, then '
        '`OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/verify_results.py`. '
        'Closure verifies immutable hashes, the historical dtype regression, both baseline comparisons, inventory and arithmetic, '
        'frozen-label reuse, selected examples and category minima, general-label sensitivity and actual HTTP timestamps. '
        'It retains the recorded completion time so later read-only reproduction cannot turn an on-time experiment into an artificial timeout.\n']
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
