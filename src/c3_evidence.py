"""Offline evidence map, provenance reconciliation and display checks.

Consumes completed analyses only. It never calls a model or judge, and never reruns a freeze recorder.
Every number in analysis/EVIDENCE_MAP.md is formatted here from its source file and checked twice:
against the source and, where feasible, by recomputation from stored scored tables and outputs.
Order (all CPU, idempotent):
  OPENBLAS_NUM_THREADS=1 .venv/bin/python src/validate_cue_inputs.py replay
  OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/acceptance_check.py
  OPENBLAS_NUM_THREADS=1 .venv/bin/python src/c3_evidence.py      # writes current.json + EVIDENCE_MAP.md
  OPENBLAS_NUM_THREADS=1 .venv/bin/python src/refresh_captions.py  # captions + example manifests
  OPENBLAS_NUM_THREADS=1 .venv/bin/python src/c3_evidence.py      # re-verifies captions/manifests
"""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
import tarfile

import pandas as pd

from provenance_paths import (GUARD_INCREMENT, SELECTOR, SELECTOR_V1_PATCH, STORY_V1, STORY_V2,
                              published, resolve)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/evidence_c3'
MAP = ROOT / 'analysis/EVIDENCE_MAP.md'
CAPTIONS = ROOT / 'paper/figs/CAPTIONS.md'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_blob(data: bytes):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def js(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def row(path, **match):
    d = pd.read_csv(ROOT / path)
    for k, v in match.items():
        d = d[d[k].eq(v)]
    assert len(d) == 1, (path, match, len(d))
    return d.iloc[0].to_dict()


# ------------------------------------------------------------------ formatting (single source)
def n(x):
    return f'{int(round(x)):,}'


def p2(x):
    return f'{100 * x:.2f}'


def ci(lo, hi):
    return f'[{100 * lo:.2f}, {100 * hi:.2f}]'.replace('-', '−')


def rate(k, m, lo, hi):
    return f'{n(k)}/{n(m)} = {p2(k / m)}% {ci(lo, hi)}'


def pp(est, lo, hi):
    return f'{100 * est:+.2f} pp {ci(lo, hi)}'.replace('-', '−')


# ------------------------------------------------------------------ selector provenance
def reconcile_story():
    """Versioned selector manifest: v1 (recovered original), v1.1 (committed), v2 (current)."""
    old = js(STORY_V1)
    new = js(STORY_V2)
    selector_key = next(k for k in new['sha256'] if published(k) == SELECTOR)  # path as recorded in the manifests
    assert old['cards'] == new['cards'], 'Selection rules/occurrences/rates changed; block display'
    assert new['verified_occurrences'] == old['verified_occurrences'] == 31
    for p, h in new['sha256'].items():
        assert sha(resolve(p)) == h, ('v2 story input changed', p)
    lines = {}
    for c in new['cards']:
        assert c['selection_rule'] and c['rates']
        for r in c['outputs']:
            run = r['run']
            if run not in lines:
                lines[run] = (ROOT / f'runs/{run}/outputs.jsonl').read_text().splitlines()
            stored = json.loads(lines[run][r['jsonl_line'] - 1])
            assert all(stored[k] == r[k] for k in ['output_id', 'request_key', 'input_text', 'text',
                                                  'family_id', 'variant', 'model', 'channel', 'prompt_id'])
        for v in c['rates'].values():
            if 'k' in v:
                assert v['n'] > 0 and 0 <= v['k'] <= v['n'] and abs(v['percent'] - 100 * v['k'] / v['n']) < 1e-10
    # v1: the source whose hash the original manifest recorded, recovered byte-exactly by reversing the
    # post-run assertion patch (analysis/examples/select_story_v1_to_v1.1.patch, `index d381610..16e6fa5`).
    # The patch added three assertion lines after the v1 run; reversing it yields the recorded SHA-256.
    v1 = (OUT / 'select_story_v1_original.py').read_bytes()
    with tarfile.open(OUT / 'history_v1.tar.gz') as t:
        v11 = t.extractfile(selector_key).read()
    v2 = (ROOT / SELECTOR).read_bytes()
    patch = (ROOT / SELECTOR_V1_PATCH).read_text()
    assert hashlib.sha256(v1).hexdigest() == old['sha256'][selector_key]
    assert f'index {git_blob(v1)}..{git_blob(v11)}' in patch, 'recovery patch index line not found'
    assert hashlib.sha256(v2).hexdigest() == new['sha256'][selector_key]
    diffs = {}
    for name, a, b, fa, fb in [('v1_to_v1.1', v1, v11, 'v1_original_hash_ab30b3', 'v1.1_committed_a9d996'),
                               ('v1.1_to_v2', v11, v2, 'v1.1_committed_a9d996', 'v2_current_549409')]:
        text = ''.join(difflib.unified_diff(a.decode().splitlines(True), b.decode().splitlines(True), fa, fb))
        (OUT / f'selector_{name}.diff').write_text(text)
        diffs[name] = dict(path=f'analysis/evidence_c3/selector_{name}.diff',
                           added=[l[1:].rstrip() for l in text.splitlines() if l.startswith('+') and not l.startswith('+++')],
                           removed=[l[1:].rstrip() for l in text.splitlines() if l.startswith('-') and not l.startswith('---')])
    assert not diffs['v1_to_v1.1']['removed'] and len(diffs['v1_to_v1.1']['added']) == 3
    assert all('assert' in l or l.strip().startswith('eligible =') for l in diffs['v1_to_v1.1']['added'])
    assert set(diffs['v1.1_to_v2']['removed']) == {
        "Path(__file__).with_name('story_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\\n')"}
    (OUT / 'selector_source.diff').unlink(missing_ok=True)   # superseded by the two versioned diffs
    versions = dict(
        status='retrospective provenance reconciliation; selection rules unchanged; not a prospective freeze',
        versions=[
            dict(version='v1', sha256=hashlib.sha256(v1).hexdigest(), git_blob=git_blob(v1),
                 source='analysis/evidence_c3/select_story_v1_original.py',
                 recovered_from=f'{SELECTOR_V1_PATCH} (reverse of the post-run assertion patch)',
                 produced=STORY_V1, manifest_sha256=sha(ROOT / STORY_V1)),
            dict(version='v1.1', sha256=hashlib.sha256(v11).hexdigest(), git_blob=git_blob(v11),
                 source='analysis/evidence_c3/history_v1.tar.gz (committed selector source)',
                 change='adds 3 lines: recomputes S1/S5 eligible counts and asserts them against the W-C manifest rates; '
                        'no selection expression changed', produced=None),
            dict(version='v2', sha256=hashlib.sha256(v2).hexdigest(), git_blob=git_blob(v2),
                 source=SELECTOR,
                 change='adds argparse --out so a replay cannot overwrite the v1 manifest; no selection expression changed',
                 produced=STORY_V2,
                 manifest_sha256=sha(ROOT / STORY_V2))],
        diffs=diffs, cards_rules_rates_equal=True, verified_occurrences=31,
        changed_input_hashes={published(p): dict(v1=h, v2=new['sha256'][p]) for p, h in old['sha256'].items()
                              if h != new['sha256'][p]},
        changed_input_reason={SELECTOR: 'v1 → v2 source versions above',
                              'src/interventions.py': 'report-status hook only (annotate_report); scoring/policy byte-identical otherwise',
                              'analysis/interventions/report.md': 'human-validation supersession notice and inline pointers; historical tables unchanged'},
        namespace='c3:S4 is the appointment P2/S3 menu; c2:S4 is the accident sequence')
    write('analysis/evidence_c3/selector_versions.json', versions)
    rec = dict(status=versions['status'], v1_manifest=STORY_V1,
               v2_manifest=STORY_V2, versions='analysis/evidence_c3/selector_versions.json',
               original_hash_matching_source_recovered=True,
               review='The v1 source matching the recorded hash ab30b3… was recovered byte-exactly and reviewed: '
                      'v1→v1.1 adds only a 3-line eligible-count assertion for S1/S5; v1.1→v2 adds only an --out argument. '
                      'No selection expression changed. The v2 replay reproduces all cards, rules, 31 occurrences, rates and '
                      'menu slots exactly; v1 manifest and its recorded hash stay byte-preserved. Displays use v2.',
               verified_occurrences=31, cards_rules_rates_equal=True,
               supersedes='earlier note that the original source was unrecoverable')
    write('analysis/evidence_c3/selector_reconciliation.json', rec)
    return rec


# ------------------------------------------------------------------ evidence collection
def collect():
    synth = js(GUARD_INCREMENT)
    inc = synth['guard_increment']
    for p in ['runs/guard1/scored.parquet', 'runs/guard1/generations.jsonl',
              'annotation/label_resolution.jsonl', 'annotation/judge_validation_main1.json']:
        assert sha(ROOT / p) == synth['sha256'][p], ('C35 input changed', p)
    old_code = (OUT / 'interventions_source_v1.py').read_text()
    new_code = (ROOT / 'src/interventions.py').read_text()
    assert old_code.replace('    out.write_text("\\n".join(L) + "\\n")\n',
           '    out.write_text("\\n".join(L) + "\\n")\n'
           '    from evidence_status import annotate_report\n    annotate_report(out)\n') == new_code
    assert hashlib.sha256(old_code.encode()).hexdigest() == synth['sha256']['src/interventions.py']
    assert inc['n'] == 1392 and inc['n_missing'] == 0 and inc['n_families'] == 58
    assert inc['pass_counts'] == {'G1': 1375, 'G1s': 1346, 'P0': 1312}
    ladder = {ch: row('analysis/r2c/channel_ladder.csv', dimension='speech_act', channel=ch,
                      metric='critical_match') for ch in ['chip1', 'full']}
    gap = row('analysis/r2c/channel_differences.csv', dimension='speech_act', metric='chip1-full')
    first = js('analysis/applicability/results.json')['derivative']['first_slots']['full']
    for arm in ['P0', 'P2', 'S3', 'P2_minus_S3', 'P2_minus_P0']:
        csv = row('analysis/applicability/first_slot_diagnostics.csv', channel='full',
                  endpoint='first_output_mismatch', arm=arm)
        for k in ['estimate', 'lo', 'hi', 'clusters']:
            assert abs(first[arm][k] - csv[k]) < 1e-12
    # P0 has one output, so its first-slot count must equal its any-of-set count (independent of S3).
    sets_full = pd.read_csv(ROOT / 'analysis/applicability/sets_full.csv')
    m = sets_full[sets_full.matched].groupby('prompt').any_fail.agg(['sum', 'count'])
    assert (int(m.loc['P0', 'sum']), int(m.loc['P0', 'count'])) == (int(first['P0']['k']), first['P0']['n'])
    frozen = js('analysis/applicability/freeze_manifest.json')
    archive = ROOT / 'analysis/applicability/evidence.tar.gz'
    assert sha(archive) == frozen['archive_sha256']
    with tarfile.open(archive) as t:
        name = next(x for x in t.getnames() if x.endswith('runs/r2c1/scored.parquet'))
        archived_scored = hashlib.sha256(t.extractfile(name).read()).hexdigest()
    assert archived_scored == frozen['inputs']['runs/r2c1/scored.parquet']
    assert archived_scored != sha(ROOT / 'runs/r2c1/scored.parquet')
    return {'C35': inc, 'C34_v2': {'ladder': ladder, 'gap': gap},
            'C36': first, 'C36_note': 'C36 = first-output diagnostic (C30 companion). Guard transfer = C37 (D-045).',
            'applicability_pre_arbitration_sha256': archived_scored,
            'current_wc_scored_sha256': sha(ROOT / 'runs/r2c1/scored.parquet')}


def transfer_status():
    acc = js('analysis/guard_wc/acceptance_check.json')
    h = js('analysis/guard_wc/headline.json')
    hashes = js('analysis/guard_wc/result_hashes.json')
    mism = [p for p, v in hashes.items() if sha(ROOT / 'analysis/guard_wc' / p) != v]
    assert not mism and acc['verdict'] == 'ACCEPT WITH QUALIFICATIONS' and h['transfer_success']
    return dict(claim='C37 (renumbered from the second C36 row; D-045)', status=h['status'],
                verdict=h['transfer_verdict'], acceptance=acc['verdict'],
                acceptance_record='analysis/guard_wc/ACCEPTANCE.md', report='analysis/guard_wc/report.md',
                result_hash_mismatches=mism, display_allowed=True,
                qualifications=['937 is not a generation count: 766 generation / 207 judge-batch HTTP calls',
                                'judge concurrency 12 within frozen limit, above later ≤8 operating limit',
                                'one uninstrumented readiness probe', 'baseline parity: dtype-only historical false alarm',
                                'scored partial predicate; repaired-text quality unvalidated'])


# ------------------------------------------------------------------ recomputation from stored tables
def recompute_wc():
    d = pd.read_parquet(ROOT / 'analysis/r2c/scored.parquet')
    p = d[d.prompt_id.eq('P0')]
    sa, po, pl = (p[p.dimension.eq(x)] for x in ['speech_act', 'polarity', 'politeness'])
    q = sa[sa.channel.eq('chip1') & sa.cv.eq('question')]
    plain = pl[pl.channel.eq('full') & pl.cv.eq('plain')]
    polite = pl[pl.channel.eq('full') & pl.cv.eq('polite')]
    neg = po[po.channel.eq('chip1') & po.cv.eq('negated')]
    bare = po[po.channel.eq('bare') & po.variant.eq('A')]
    return dict(chip1=(int(sa[sa.channel.eq('chip1')].critical_match.sum()), int(sa[sa.channel.eq('chip1')].critical_match.notna().sum())),
                full=(int(sa[sa.channel.eq('full')].critical_match.sum()), int(sa[sa.channel.eq('full')].critical_match.notna().sum())),
                question_fail=(int((q.critical_match == False).sum()), int(q.critical_match.notna().sum())),  # noqa: E712
                question_request=int((q.crit == 'request/command').sum()),
                additions=(int((plain.crit == 'polite').sum()), int(plain.crit.notna().sum())),
                additions_gemma=int(plain[plain.model.str.startswith('gemma')].crit.eq('polite').sum()),
                removals=(int((polite.crit == 'plain').sum()), int(polite.crit.notna().sum())),
                negated_chip1=(int(neg.critical_match.sum()), int(neg.critical_match.notna().sum())),
                bare_affirmative=(int(bare.crit.eq('affirmative').sum()), len(bare),
                                  int(bare.crit.isin(['affirmative', 'negated']).sum())))


# ------------------------------------------------------------------ the displayed values
def values(ev):
    V = {}
    c35 = ev['C35']
    pc = c35['pass_counts']
    V['disc_pass'] = f"{n(pc['P0'])} / {n(pc['G1s'])} / {n(pc['G1'])} of {n(c35['n'])}"
    V['c35'] = f"+{c35['estimate_pp']:.2f} pp [{c35['ci95_pp'][0]:.2f}, {c35['ci95_pp'][1]:.2f}]"
    V['c35_disc'] = f"{c35['G1_only_pass']} G1-only / {c35['G1s_only_pass']} G1s-only"
    rep = js('analysis/interventions/report.json')
    g = rep['guard']
    fix = g['G1_cue']['fix']
    V['repairs'] = f"{n(fix['estimate'] * fix['n'])}/{fix['n']} = {p2(fix['estimate'])}% {ci(fix['ci_low'], fix['ci_high'])}"
    V['residual'] = f"{n((1 - fix['estimate']) * fix['n'])}/{fix['n']}"
    V['changed_all'] = f"{n(g['G1_all']['overcorr']['estimate'] * g['G1_all']['overcorr']['n'])}/{n(g['G1_all']['overcorr']['n'])}"
    V['changed_cue'] = f"{n(g['G1_cue']['overcorr']['estimate'] * g['G1_cue']['overcorr']['n'])}/{n(g['G1_cue']['overcorr']['n'])}"
    V['cost_inputs'] = f"{n(g['cost']['inputs'])} distinct inputs"
    sp = rep['span']
    t = sp['polarity+certainty']
    V['i2_target'] = f"{n(t['P2']['estimate'] * 80)}/80 → {n(t['I2']['estimate'] * 80)}/80"
    for dim, key in [('politeness', 'i2_pol'), ('speech_act', 'i2_act')]:
        s = sp[dim]
        m_, k2 = s['diff_I2']['n'], s['I2']['estimate'] * s['I2']['n']
        k1 = k2 - s['diff_I2']['estimate'] * m_
        V[key] = f"{n(k1)}/{m_} → {n(k2)}/{m_} ({pp(s['diff_I2']['estimate'], s['diff_I2']['ci_low'], s['diff_I2']['ci_high'])})"
    V['i2_cost'] = f"{sp['cost_I2']['calls_per_set']:.2f} calls/set"
    h = js('annotation/judge_validation_main1.json')['human']
    tests = [v['sampled_test/final'] for v in h['judge'].values()]
    vio = h['verdict']['violation']['primary']
    V['h7'] = (f"held-out κ {min(x['kappa'] for x in tests):.3f}–{max(x['kappa'] for x in tests):.3f}".replace('0.', '.')
               + f", lowest lower 95% bound {min(x['kappa_ci'][0] for x in tests):.3f}".replace('0.', '.')
               + f", n = {min(x['n'] for x in tests)}–{max(x['n'] for x in tests)}")
    V['h7_vio'] = (f"{vio['agree_k']}/{vio['n']} [{100 * vio['agree_ci'][0]:.1f}, {100 * vio['agree_ci'][1]:.1f}]%, "
                   f"κ = {vio['kappa']:.3f}".replace('0.9', '.9') + f"; {vio['judge_T_ref_T']} both-positive, "
                   f"{vio['judge_T_ref_F']} judge-only, {vio['judge_F_ref_T']} human-only, {vio['judge_F_ref_F']} both-negative")
    V['h7_items'] = f"{h['n_items']} items"
    pr = js('analysis/r2c/primary.json')['primaries']
    hp = lambda x: f"{x:.4f}".lstrip('0')  # noqa: E731
    V['P1'] = f"{pp(pr['P1']['estimate'], pr['P1']['ci_low'], pr['P1']['ci_high'])}, {pr['P1']['n']}/{pr['P1']['n_total']} paired targets / {pr['P1']['n_clusters']} clusters, Holm p = {hp(pr['P1']['p_holm'])}"
    V['P2'] = f"{pp(pr['P2']['estimate'], pr['P2']['ci_low'], pr['P2']['ci_high'])}, {pr['P2']['n']} pairs / {pr['P2']['n_clusters']} clusters, Holm p = {hp(pr['P2']['p_holm'])}"
    a = pr['P3']['affirmative_share']
    V['P3_share'] = f"{rate(a['sum'], a['n'], a['ci_low'], a['ci_high'])} directional; {n(a['sum'])}/{a['n_total']} all outputs"
    V['P3'] = f"{V['P3_share']}, Holm p = {hp(pr['P3']['p_holm'])}"
    L, gap = ev['C34_v2']['ladder'], ev['C34_v2']['gap']
    V['c34_chip'] = rate(L['chip1']['sum'], L['chip1']['n'], L['chip1']['ci_low'], L['chip1']['ci_high'])
    V['c34_full'] = rate(L['full']['sum'], L['full']['n'], L['full']['ci_low'], L['full']['ci_high'])
    V['c34_gap'] = f"{pp(gap['estimate'], gap['ci_low'], gap['ci_high'])}, {int(gap['n'])} pairs / {int(gap['n_clusters'])} clusters"
    qm = row('analysis/r2c/cue_value_match.csv', dimension='speech_act', cv='question')
    V['c11'] = rate(qm['n'] - qm['sum'], qm['n'], 1 - qm['ci_high'], 1 - qm['ci_low'])
    tr = pd.read_csv(ROOT / 'analysis/r2c/speech_act_transitions.csv')
    tq = tr[tr.cv.eq('question')]
    V['c11_req'] = f"{int(tq[tq.crit.eq('request/command')].n.sum())}/{int(tq.n.sum())}"
    nm = row('analysis/r2c/cue_value_match.csv', dimension='polarity', cv='negated')
    V['neg_chip'] = rate(nm['sum'], nm['n'], nm['ci_low'], nm['ci_high'])
    s1 = js(STORY_V2)
    cards = {c['id']: c for c in s1['cards']}
    r1 = cards['S1']['rates']['manifest_rate_with_ci']
    V['additions'] = rate(r1['sum'], r1['n'], r1['ci_low'], r1['ci_high'])
    pdm = pd.read_csv(ROOT / 'analysis/r2c/politeness_direction_by_model.csv')
    V['additions_gemma'] = f"{int(pdm[pdm.model.eq('gemma3-4b') & pdm.cv.eq('plain')]['sum'].iloc[0])}/80"
    V['removals'] = f"{int(pdm[pdm.cv.eq('polite')]['sum'].sum())}/{int(pdm[pdm.cv.eq('polite')]['n'].sum())}"
    res = js('analysis/applicability/results.json')
    f = res['preserved']['H1/full']
    V['c30'] = (f"P2 {rate(f['P2']['k'], f['P2']['n'], f['P2']['lo'], f['P2']['hi'])}; S3 {rate(f['S3']['k'], f['S3']['n'], f['S3']['lo'], f['S3']['hi'])}; "
                f"paired {pp(f['P2_minus_S3']['estimate'], f['P2_minus_S3']['lo'], f['P2_minus_S3']['hi'])}, {f['P2']['clusters']} clusters, "
                f"{n(f['P2']['n'])}/{n(f['available_targets'])} planned targets")
    fs = ev['C36']
    V['c36'] = (f"P2 {rate(fs['P2']['k'], fs['P2']['n'], fs['P2']['lo'], fs['P2']['hi'])}; S3 {rate(fs['S3']['k'], fs['S3']['n'], fs['S3']['lo'], fs['S3']['hi'])}; "
                f"paired {pp(fs['P2_minus_S3']['estimate'], fs['P2_minus_S3']['lo'], fs['P2_minus_S3']['hi'])}")
    V['c36_p0'] = rate(fs['P0']['k'], fs['P0']['n'], fs['P0']['lo'], fs['P0']['hi'])
    e = res['preserved']['H1/exact_partner']
    V['c31'] = f"P2 {rate(e['P2']['k'], e['P2']['n'], e['P2']['lo'], e['P2']['hi'])} vs S3 {rate(e['S3']['k'], e['S3']['n'], e['S3']['lo'], e['S3']['hi'])}, {e['P2']['clusters']} clusters"
    h2 = res['preserved']['H2']
    w = res['derivative']['wd_pooled_repeat_floors']
    V['wd'] = (f"NOT×YOU {rate(h2['NOT|YOU']['k'], h2['NOT|YOU']['n'], h2['NOT|YOU']['lo'], h2['NOT|YOU']['hi'])}; other cells "
               f"{n(h2['other']['k'])}/{n(h2['other']['n'])}; {h2['damage_scenarios']}/80 scenarios")
    dm, db = w['primary']['damage'], w['both']['damage_minus_both_repeat']
    V['wd_floor'] = (f"Llama/STATEMENT damage {rate(dm['k'], dm['n'], dm['ci_low'], dm['ci_high'])}; minus both-repeat floor "
                     f"{pp(db['estimate'], db['ci_low'], db['ci_high'])}")
    wb = js('analysis/wb/contract_audit.json')
    est = {(e['sample'], e['metric']): e for e in wb['estimates']
           if e['subset'] == 'all_restored' and e['dim'] == 'ALL' and e['model'] == 'pooled'}
    ar, ae = est[('random', 'actual_input_general_match')], est[('enriched', 'actual_input_general_match')]
    V['wb_conf'] = f"{wb['inventory']['statuses']['definite_conflict']}/{wb['inventory']['messages']}"
    V['wb_maybe'] = f"{wb['example']['k']}/{wb['example']['n']}"
    V['wb_actual'] = (f"{rate(ar['k'], ar['n'], *ar['ci95'])} random; {rate(ae['k'], ae['n'], *ae['ci95'])} enriched")
    r5 = js('analysis/r5_validator/replay.json')
    vv = r5['verdicts']
    V['r5'] = (f"{r5['agrees_with_audit']}/{r5['n']} agree with the frozen audit; {vv['compatible']} compatible, "
               f"{vv['compatible_but_coarser']} compatible-but-coarser, {vv['conflicting']} conflicting, "
               f"{vv['unknown']} unknown, {vv['unchanged_noop']} unchanged/no-op")
    gh = js('analysis/guard_wc/headline.json')
    acc = js('analysis/guard_wc/acceptance_check.json')
    arms = {a_: (gh[f'{a_}_joint_pass'], gh[f'{a_}_joint_pass_ci_low'], gh[f'{a_}_joint_pass_ci_high']) for a_ in ['p0', 'g1', 'g1s']}
    V['gt_joint'] = '; '.join(f"{lab} {p2(v[0])}% {ci(v[1], v[2])}" for lab, v in zip(['P0', 'G1', 'G1s'], arms.values()))
    G = gh['paired']['G1']
    V['gt_gain'] = pp(G['joint_gain']['estimate'], G['joint_gain']['ci_low'], G['joint_gain']['ci_high'])
    V['gt_repair'] = rate(G['strict_repair']['k'], G['strict_repair']['n'], G['strict_repair']['ci_low'], G['strict_repair']['ci_high'])
    V['gt_changed'] = rate(G['strict_changed_correct']['k'], G['strict_changed_correct']['n'],
                           G['strict_changed_correct']['ci_low'], G['strict_changed_correct']['ci_high'])
    V['gt_p2f'] = f"{n(G['strict_pass_to_fail']['k'])}/{n(G['strict_pass_to_fail']['n'])}"
    V['gt_resid'] = rate(G['strict_residual']['k'], G['strict_residual']['n'], G['strict_residual']['ci_low'], G['strict_residual']['ci_high'])
    cmpj = js('analysis/guard_wc/closure_audit.json')['comparator']['joint']
    V['gt_cmp'] = (f"{pp(cmpj['family']['estimate'], cmpj['family']['ci_low'], cmpj['family']['ci_high'])} joint; "
                   f"{cmpj['G1_only_pass']} G1-only / {cmpj['G1s_only_pass']} G1s-only passes")
    cl = acc['calls']
    V['gt_calls'] = f"{cl['retry_generation_http']} generation / {cl['judge_batch_http']} judge-batch HTTP calls"
    V['gt_inv'] = f"{gh['n_families']} families, {n(gh['n_targets'])} target occurrences / {n(gh['n_unique'])} unique first passes, F = {gh['F']}"
    return V


def cross_check(V, ev, W):
    """Displayed values must also follow from stored scored tables, not only from report files."""
    L = ev['C34_v2']['ladder']
    assert W['chip1'] == (int(L['chip1']['sum']), int(L['chip1']['n'])) == (457, 624)
    assert W['full'] == (int(L['full']['sum']), int(L['full']['n']))
    assert V['c11'].startswith(f"{W['question_fail'][0]}/{W['question_fail'][1]} ")
    assert V['c11_req'] == f"{W['question_request']}/{W['question_fail'][1]}"
    assert V['additions'].startswith(f"{W['additions'][0]}/{W['additions'][1]} ")
    assert V['additions_gemma'] == f"{W['additions_gemma']}/80"
    assert V['removals'] == f"{W['removals'][0]}/{W['removals'][1]}"
    assert V['neg_chip'].startswith(f"{W['negated_chip1'][0]}/{W['negated_chip1'][1]} ")
    b = W['bare_affirmative']
    assert V['P3_share'].startswith(f"{b[0]}/{b[2]} ") and f"{b[0]}/{b[1]} all outputs" in V['P3_share']
    g = pd.read_parquet(ROOT / 'analysis/guard_wc/paired_G1.parquet')
    assert V['gt_repair'].startswith(f"{int((g.strict_P0.eq(0) & g.strict_arm.eq(1)).sum())}/{int(g.strict_P0.eq(0).sum())} ")
    return {k: list(v) if isinstance(v, tuple) else v for k, v in W.items()}


# ------------------------------------------------------------------ the map
def write_map(V, story, transfer):
    t = f"""# Current evidence map

As of **2026-11-01**. This is the single current routing table for both target papers. It is generated by
`src/c3_evidence.py` from the files linked in each row. Every displayed number is formatted from its source
and re-checked ([display_verification.json](evidence_c3/display_verification.json)). It is a retrospective
reconciliation, not a preregistration. **0 generation / 0 judge calls.** Freezes: SE4All evidence November 10,
CALE-AI November 16. HUMANE is a non-submitted draft (D-014). Newer results supersede older shorthand,
and historical tables and snapshots are preserved.

| Population / version | Authoritative files | Current result (ledger) | Interpretation limits |
|---|---|---|---|
| **Discovery** (main1, guard1, span1): 58 primary / 60 designed families, four fixed models; act-10/act-16 quarantined | [main1 headline table](main1/report.md); [interventions](interventions/report.md); [reconciliation](reconciliation.md); `annotation/label_resolution.jsonl` (arbiter > agreement > unknown) | Cue-target strict passes P0 / strip-only G1s / G1: **{V['disc_pass']}**. **C35** G1−G1s **{V['c35']}**, 58 family clusters, {V['c35_disc']} passes. Guard repairs **{V['repairs']}**, residual **{V['residual']}** (C13/C20); changed-correct **{V['changed_all']}** all channels, **{V['changed_cue']}** cue channels; cost over **{V['cost_inputs']}**. I2 target coverage **{V['i2_target']}** (separate stratum); politeness coverage **{V['i2_pol']}**; speech act **{V['i2_act']}**; **{V['i2_cost']}** (C14). | Exploratory paired stored configurations. No feedback-causal effect, fluency or usable-repair prevalence. The 2 G1s-only passes are relative to G1, not newly broken P0-correct outputs. Original discovery CIs: 2,000 family resamples, seed 20261031. C35: 10,000, seed 20261101. |
| **Human extraction gate H7 (D-031, C25)**, earlier main1 extraction inventory only | [human JSON](../annotation/judge_validation_main1.json) `human.judge.*.sampled_test/final`; [gate log](oracle/human_gate.log) | **PASSED**: {V['h7']}, seven fields. Violation agreement {V['h7_vio']}. Two annotators, {V['h7_items']} (100 double-coded core, 87 single-coded extras). | Plurality reference with ties/unsure excluded, converted labels, no adjudication or per-item timing. Does not validate repaired-text completeness, W-B admissibility, or new W-C/W-D/guard-transfer boundaries. D-033 keys unchanged. **Supersession pointers** to stale “human pending” prose are now in [oracle report](oracle/report.md) and [intervention report](interventions/report.md) (top notice plus inline “→ D-031” marks). Historical tables are kept verbatim. |
| **W-C, current arbitrated** confirmation: 240 designed / 238 analyzed families (80 polarity, 78 act, 80 politeness) | [report](r2c/report.md), [primary.json](r2c/primary.json), [arbitration](r2c/arbitration.md), `r2c/{{channel_ladder,channel_differences,cue_value_match}}.csv`, `runs/r2c1/arbiter.jsonl` | **C28 v2** H-act/P1 **{V['P1']}**. H-politeness/P2 **{V['P2']}**. H-default/P3 **{V['P3']}**. **C34 v2 (completed)** chip1 **{V['c34_chip']}**, full **{V['c34_full']}**, gap **{V['c34_gap']}**. **C11** question failures **{V['c11']}**, of which **{V['c11_req']}** become requests. Negated chip1 match **{V['neg_chip']}**. Full-input politeness additions **{V['additions']}** (Gemma {V['additions_gemma']}), removals {V['removals']}. | Only the three Holm-tested pooled contrasts are confirmatory; the rest is descriptive. 177 decisions resolved 259 rows; zero critical unknowns. Early-cache (48 requests) and post-outcome-arbitration qualifications remain. P1/P2/P3 contrast names are not prompt IDs. CIs: 10,000 recorded-cluster resamples, seed 20261031. The unknown-masked +31.65 is a sensitivity analysis only. |
| **W-C frozen pre-arbitration applicability derivative**, distinct from current W-C | [applicability report](applicability/report.md), [freeze manifest](applicability/freeze_manifest.json), [archive](applicability/evidence.tar.gz), [first-slot CSV](applicability/first_slot_diagnostics.csv) | **C30** {V['c30']}. **C36** first-output companion: {V['c36']} (P0 single output {V['c36_p0']}). **C31** exact partner-source sets {V['c31']}. | **Frozen protocol-masked snapshot**: archived scored hash `{story['app_hash'][:12]}…` differs intentionally from current W-C `{story['cur_hash'][:12]}…`. Never recompute it with arbitrated labels. Exploratory; first-slot equalizes the number of inspected outputs only (prompt, temperature and generation still differ). Category mismatch is not semantic reversal. I2 was not tested on supplied input. Seed 20261101. |
| **W-D** composition: 80 scenarios, two repeats, model × encoding × protected dimension | [report](r2d/report.md), `r2d/primary.json`, transitions/repeats parquets; [C32 derivative](applicability/report.md) | **C27/C32** {V['wd']}. {V['wd_floor']}. | Exploratory cell decomposition, not an independent replication. A model/encoding-specific regression; no request mechanism or universally safe encoding. CB-7/general-label limits and freeze qualifications are retained. |
| **W-B** final generation + complete restoration-contract audit: 139 restorations / 556 outputs | [W-B report](wb/report.md), [contract audit](wb/contract_audit.md), [JSON](wb/contract_audit.json), inventory/diff/estimates CSVs, hashed archives | **C33** definite chip/source conflicts **{V['wb_conf']}**; `[MAYBE]` conflicts: {V['wb_maybe']} outputs follow the visible chip and fail the source. Actual-input general fidelity **{V['wb_actual']}** (C23). **R5 validator replay** ([README](r5_validator/README.md)): {V['r5']}. | Source fidelity, actual-input fidelity and the aligned sensitivity are separate endpoints/populations. Machine-assessed; the W-B human admissibility audit has zero completed fields. A changed-population exclusion is never an intervention gain. Random and enriched samples are never pooled. R5 is demonstrated on historical inputs; historical requests are unchanged. |
| **Guard transfer to W-C** (separate frozen inventory, **C37**, accepted with qualifications) | [report](guard_wc/report.md), [ACCEPTANCE](guard_wc/ACCEPTANCE.md), [FREEZE](guard_wc/FREEZE.md), `headline.json`, `closure_audit.json`, `acceptance_check.json` | **PASS** on all fixed criteria: {V['gt_inv']}. Joint pass {V['gt_joint']}; gain **{V['gt_gain']}**. Strict repairs **{V['gt_repair']}**; correct-text changed **{V['gt_changed']}**; pass→fail {V['gt_p2f']}; residual strict failures **{V['gt_resid']}**. G1−G1s {V['gt_cmp']}. Cost: {V['gt_calls']}. | Machine-scored partial predicate on 78 speech-act families; no usable-repair, fluency or causal feedback claim. H7 does not cover new repairs. “937 calls” (D-042) is corrected to the counts shown. Judge concurrency of 12 was within the frozen limit but above the later ≤8 limit. The P0 baseline is the frozen arbitrated W-C with its chronology qualifications. Separate from discovery and C30. |

## Display and example contract

Current exact examples: [v2 example manifest](examples/story_evidence.v2.json), mirrored in
[`paper/figs/example_manifest_c3.json`](../paper/figs/example_manifest_c3.json). Selector provenance:
[versioned selector manifest](evidence_c3/selector_versions.json). The source matching the original recorded hash
was **recovered byte-exactly** (`select_story_v1_original.py`) and reviewed. v1→v1.1 adds a 3-line count assertion,
and v1.1→v2 adds an `--out` argument. No selection rule changed, and the v2 replay reproduces all **31/31** occurrences,
strings, rules, rates and menu slots. The v1 manifest is byte-preserved. Namespace: **c3:S4** is the appointment
menu and **c2:S4** is the accident sequence.

| Display | Required adjacent denominator / endpoint | Population |
|---|---|---|
| c3:S2 `feel well` four-channel sequence | Bare affirmative {V['P3_share']}; negated chip1 {V['neg_chip']}. Marginal endpoints, not a paired repair probability. | Arbitrated W-C |
| c3:S1 jar, full-input constructed test | Additions {V['additions']}, Gemma {V['additions_gemma']}, removals {V['removals']}. No observed AAC-user episode. | Arbitrated W-C |
| c3:S5 parcel question cue | {V['c11']} question failures; {V['c11_req']} specifically requests. | Arbitrated W-C |
| c3:S7/S9 repair and fragment; S8 residual | Repairs {V['repairs']}, residual {V['residual']}. The exact `Ask you ` prefix (4/63) is a post hoc lexical count, not a fluency prevalence. | Discovery, quarantine excluded |
| c3:S10 complete P2/I2 knock/come menus | Politeness {V['i2_pol']}; target {V['i2_target']} is a separate stratum. | Discovery |
| c3:S4 complete P2/S3 appointment menus | Exact partner-source sets {V['c31']}; all six outputs. Not the C30 category-mismatch rate. | Judge-free lexical endpoint |

Long locators stay in the manifests. A display is blocked by a missing denominator, an exact-string mismatch, an
unresolved source, a mismatched scoring population, or a source/macro disagreement. No evidence here supports a
usable-repair prevalence, full semantic guarantee, actual user effort, agency, experienced harm, human-validated W-B
transfer, or causal feedback advantage. Pointwise exploratory intervals do not correct for search or oracle error.
"""
    MAP.write_text(t)
    return t


def verify_display(V):
    checks = []
    text = MAP.read_text()
    for k, v in V.items():
        checks.append(dict(file='analysis/EVIDENCE_MAP.md', key=k, string=v, present=v in text))
    if CAPTIONS.exists():
        cap = CAPTIONS.read_text()
        for k in ['disc_pass', 'c35', 'c35_disc', 'c34_chip', 'c34_full', 'c34_gap', 'c11', 'c11_req', 'c36', 'c31',
                  'gt_gain', 'gt_repair', 'gt_changed', 'gt_resid', 'gt_cmp', 'r5', 'wb_conf']:
            checks.append(dict(file='paper/figs/CAPTIONS.md', key=k, string=V[k], present=V[k] in cap))
    mirror = ROOT / 'paper/figs/example_manifest_c3.json'
    if mirror.exists():
        m = json.loads(mirror.read_text())
        ok = m['cards'] == js(STORY_V2)['cards'] and \
            m['source_sha256'] == sha(ROOT / STORY_V2)
        checks.append(dict(file='paper/figs/example_manifest_c3.json', key='cards==v2', string='', present=ok))
    em = ROOT / 'paper/figs/example_manifest.json'
    if em.exists():
        m = json.loads(em.read_text())
        ok = all(m['scored_sha256'][r] == sha(ROOT / f'runs/{r}/scored.parquet') for r in m['scored_sha256']) and \
            m['resolution_sha256'] == sha(ROOT / 'annotation/label_resolution.jsonl')
        checks.append(dict(file='paper/figs/example_manifest.json', key='scored+resolution hashes', string='', present=ok))
    return checks


def main():
    story = reconcile_story()
    data = collect()
    transfer = transfer_status()
    W = recompute_wc()
    V = values(data)
    recomputed = cross_check(V, data, W)
    write('analysis/evidence_c3/current.json', {
        'date': '2026-11-01', 'status': 'retrospective current evidence map; not a prospective freeze',
        'generation_calls': 0, 'judge_calls': 0, 'evidence': data, 'story': story, 'guard_transfer': transfer,
        'r5_validator': js('analysis/r5_validator/replay.json'), 'displayed_values': V,
        'recomputed_from_stored_tables': recomputed,
        'claim_ids': {'C35': 'discovery G1−G1s comparator', 'C36': 'first-output diagnostic (C30 companion)',
                      'C37': 'W-C guard transfer (renumbered from duplicate C36; D-045)',
                      'C34 v2 completion': 'W-C speech-act chip1/full numerators and CI'}})
    write_map(V, {'app_hash': data['applicability_pre_arbitration_sha256'],
                  'cur_hash': data['current_wc_scored_sha256']}, transfer)
    checks = verify_display(V)
    failed = [c for c in checks if not c['present']]
    write('analysis/evidence_c3/display_verification.json', dict(
        checked=len(checks), failed=len(failed), checks=checks,
        stored_output_examples_verified=story['verified_occurrences'],
        note='String presence of every source-formatted value; W-C and guard-transfer values also recomputed '
             'from stored scored tables; example strings matched line-by-line to runs/*/outputs.jsonl.'))
    print(json.dumps({'checked': len(checks), 'failed': [(c['file'], c['key']) for c in failed]}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
