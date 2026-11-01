"""Reproduce cycle-3 illustrations (adapted from cycle 2) and verify their exact stored occurrences. CPU only."""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from interventions import guard_frame, sha1, span_sets

ORDER = {m: i for i, m in enumerate(['qwen2.5-7b', 'llama3.1-8b', 'gemma3-4b', 'gpt-6.1-terra'])}
used = set()


def read(p):
    used.add(p)
    return pd.read_parquet(ROOT / p)


def js(p):
    used.add(p)
    return json.loads((ROOT / p).read_text())


def items(p):
    used.add(p)
    return {x['family_id']: x for x in map(json.loads, (ROOT / p).open())}


def rate(k, n):
    return {'k': int(k), 'n': int(n), 'percent': 100 * int(k) / int(n)}


def order(d):
    return d.assign(mo=d.model.map(ORDER)).sort_values(
        ['family_id', 'variant', 'mo', 'sample_idx', 'suggestion_idx', 'output_id'])


cards = []
occurrences = []


def occurrence(run, row, suffix=''):
    rec = {k: row[k + suffix] for k in ['output_id', 'request_key', 'text']}
    rec.update({k: row[k] for k in ['model', 'family_id', 'variant', 'channel', 'input_text']})
    rec.update(run=run, prompt_id='G1' if suffix else row['prompt_id'])
    occurrences.append(rec)
    return rec


def card(cid, rule, source, outputs, rates):
    cards.append(dict(id=cid, selection_rule=rule, source=source, outputs=outputs, rates=rates))


wc = read('analysis/r2c/scored.parquet')
wp = wc[wc.prompt_id.eq('P0')]
wc_items = items('data/items/r2_c1.jsonl') | items('data/items/r2_c2.jsonl')
manifest = js('analysis/r2c/examples.json')
for cid, cat in [('S1', 'Full-input politeness addition'), ('S5', 'Question cue failure')]:
    ex = next(x for x in manifest if x['category'] == cat)
    assert ex['source'] == wc_items[ex['family_id']]['variants'][ex['variant']]['source']
    row = wp[(wp.output_id == ex['output_id']) & (wp.family_id == ex['family_id']) &
             (wp.variant == ex['variant']) & (wp.channel == ex['channel'])].iloc[0]
    rr = ex['rate']
    card(cid, 'Reuse analysis/r2c/examples.json SHA256-minimum rule: ' + ex['rule'],
         ex['source'], [occurrence('r2c1', row)],
         {'manifest_event': rate(rr['sum'], rr['n']), 'manifest_rate_with_ci': rr})
    if cid == 'S5':
        questions = wp[wp.dimension.eq('speech_act') & wp.channel.eq('chip1') & wp.cv.eq('question')]
        cards[-1]['rates']['question_to_request'] = rate(questions.crit.eq('request/command').sum(), questions.crit.notna().sum())

neg = order(wp[wp.dimension.eq('polarity') & wp.channel.eq('bare') & wp.cv.eq('negated')])
r = neg.iloc[0]
assert r.source == wc_items[r.family_id]['variants'][r.variant]['source']
ladder = wp[(wp.family_id == r.family_id) & (wp.variant == r.variant) & (wp.model == r.model)]
bare = wp[wp.dimension.eq('polarity') & wp.channel.eq('bare')].drop_duplicates('output_id')
chips = wp[wp.dimension.eq('polarity') & wp.channel.eq('chip1') & wp.cv.eq('negated')]
card('S2', 'First P0 bare negated polarity target by family, variant, fixed model order; display same target bare/noncrit/chip1/full.',
     r.source, [occurrence('r2c1', ladder[ladder.channel.eq(c)].iloc[0]) for c in ['bare', 'noncrit', 'chip1', 'full']],
     {'bare_affirmative_all': rate(bare.crit.eq('affirmative').sum(), len(bare)),
      'bare_affirmative_directional': rate(bare.crit.eq('affirmative').sum(), bare.crit.isin(['affirmative','negated']).sum()),
      'negated_chip_match': rate(chips.critical_match.sum(), chips.critical_match.notna().sum())})

it = items('data/items/test.jsonl')
main = read('runs/main1/scored.parquet')
p0 = main[main.prompt_id.eq('P0') & ~main.quarantine_refusal_acceptance]
cer = order(p0[p0.dimension.eq('certainty') & p0.channel.eq('bare') & p0.variant_value.eq('hedged/uncertain')])
r = cer.iloc[0]
ladder = p0[(p0.family_id == r.family_id) & (p0.variant == r.variant) & (p0.model == r.model)]
cb = p0[p0.dimension.eq('certainty') & p0.channel.eq('bare')].drop_duplicates('output_id')
ch = p0[p0.dimension.eq('certainty') & p0.channel.eq('chip1') & p0.variant_value.eq('hedged/uncertain')]
cf = p0[p0.dimension.eq('certainty') & p0.channel.eq('full') & p0.variant_value.eq('hedged/uncertain')]
card('S3', 'First hedged certainty P0 bare target by family, variant, fixed model order; display bare/chip1/full (retained cycle-1 E2).',
     it[r.family_id]['variants'][r.variant]['source'],
     [occurrence('main1', ladder[ladder.channel.eq(c)].iloc[0]) for c in ['bare','chip1','full']],
     {'bare_plain': rate(cb.critical.eq('plain assertion').sum(), len(cb)),
      'hedged_chip_match': rate(ch.critical_match.sum(), len(ch)),
      'full_hedge_lost': rate(cf.critical.ne('hedged/uncertain').sum(), len(cf))})

# Replace the unquantified scope-error diagnostic with a judge-free menu endpoint.
import re

def norm(text):
    return " ".join(re.sub(r"[^a-z0-9\s]", "", text.lower().replace("’", "'")).split())

lex = wc[wc.dimension.eq('polarity') & wc.channel.eq('full')].copy()
lex['copy_partner'] = [norm(r.text) == norm(wc_items[r.family_id]['variants'][
    'B' if r.variant == 'A' else 'A']['source']) for r in lex.itertuples()]
keys = ['family_id', 'variant', 'model', 'channel']
lexsets = lex.groupby(keys + ['prompt_id']).agg(n=('text','size'),
    copy_partner=('copy_partner','any')).reset_index()
ok = lexsets[lexsets.prompt_id.isin(['P2','S3']) & lexsets.n.eq(3)].groupby(keys).prompt_id.nunique()
ok = ok[ok.eq(2)].reset_index()[keys]
lexsets = lexsets.merge(ok, on=keys)
ex = lex[lex.prompt_id.eq('P2') & lex.copy_partner].merge(ok,on=keys).sort_values(
    ['family_id','model','variant','suggestion_idx']).iloc[0]
chosen = lex[(lex.family_id==ex.family_id) & (lex.model==ex.model) & (lex.variant==ex.variant)]
outs = [occurrence('r2c1',r) for _,r in chosen[chosen.prompt_id.isin(['P2','S3'])].sort_values(
    ['prompt_id','sample_idx','suggestion_idx']).iterrows()]
assert len(outs)==6
card('S4', 'First complete full-P2 polarity set reproducing its normalized partner source; sort family_id, model (lexical), variant, suggestion_idx; show all P2 and S3 slots.',
    wc_items[ex.family_id]['variants'][ex.variant]['source'], outs,
    {p:rate(z.copy_partner.sum(),len(z)) for p,z in lexsets.groupby('prompt_id')})

trans = read('analysis/r2d/transitions.parquet')
q = trans[(trans.encoding=='STATEMENT') & (trans.dimension=='polarity') & trans.damage]
q = q.assign(mo=q.model.map(ORDER)).sort_values(['scenario','mo','encoding','dimension','cell','draw'])
r = q.iloc[0]
wd = read('runs/r2d1/scored.parquet')
outs = []
for enc in ['STATEMENT','TELL']:
    rr = trans[(trans.scenario==r.scenario) & (trans.model==r.model) & (trans.encoding==enc) &
               (trans.dimension==r.dimension) & (trans.cell==r.cell) & (trans.draw==r.draw)].iloc[0]
    for suffix in ['_s','_b']:
        match = wd[(wd.request_key==rr['request_key'+suffix]) & (wd.output_id==rr['output_id'+suffix]) &
                   (wd.family_id==r.family_id) & (wd.variant==r.variant)]
        outs.append(occurrence('r2d1', order(match).iloc[0]))
llama = trans[(trans.encoding=='STATEMENT') & (trans.dimension=='polarity') & trans.model.eq('llama3.1-8b')]
repeats = read('analysis/r2d/repeats.parquet')
repeats_both = read('analysis/r2d/repeats_both.parquet')
rep = repeats[(repeats.encoding=='STATEMENT') & (repeats.dimension=='polarity') & repeats.model.eq('llama3.1-8b')]
rb = repeats_both[(repeats_both.encoding=='STATEMENT') & (repeats_both.dimension=='polarity') & repeats_both.model.eq('llama3.1-8b')]
card('S6', 'First STATEMENT polarity damage by scenario, fixed model order, encoding, dimension, cell, draw; show paired TELL control.',
     'Controlled NOT|YOU cell; protected dimension polarity.', outs,
     {'llama_statement_damage': rate(llama.damage.sum(),len(llama)),
      'affected_scenarios': rate(llama[llama.damage].scenario.nunique(),llama.scenario.nunique()),
      'pooled_statement_damage': rate(len(q),len(trans[(trans.encoding=='STATEMENT') & (trans.dimension=='polarity')])),
      'llama_single_repeat': rate(rep.repeat_disagreement.sum(),len(rep)),
      'llama_both_repeat': rate(rb.repeat_disagreement.sum(),len(rb))})

used.update(['src/interventions.py','annotation/label_resolution.jsonl',
             'runs/guard1/scored.parquet','runs/span1/scored.parquet'])
_, arms = guard_frame(ROOT / 'runs/guard1')
g = arms['G1']
g = g[g.channel.isin(['chip1','chipall','full']) & ~g.family_id.isin(['act-10','act-16'])].copy()
g['h'] = [sha1(*t) for t in zip(g.base_key,g.family_id,g.variant,g.channel)]
g = g.sort_values(['h','output_id'])
fixed = g[g.strict_fail & ~g.strict_fail_G1]
unfixed = g[g.strict_fail & g.strict_fail_G1]
for cid, row, rule in [('S7',fixed.iloc[0],'First failure→pass'),
                       ('S8',unfixed.iloc[0],'First failure→failure'),
                       ('S9',fixed.iloc[1],'Second failure→pass, retained independently of fragment wording')]:
    card(cid, rule + '; cue channels, quarantine excluded; SHA1(base request key,family,variant,channel), output ID tie-break.',
         it[row.family_id]['variants'][row.variant]['source'],
         [occurrence('guard1',row),occurrence('guard1',row,'_G1')],
         {'fixed_initial_failures':rate(len(fixed),g.strict_fail.sum()),
          'residual_initial_failures':rate(len(unfixed),g.strict_fail.sum()),
          'final_failures_all_cue_targets':rate(g.strict_fail_G1.sum(),len(g)),
          'ask_you_prefix_among_fixed':rate(fixed.text_G1.str.startswith('Ask you ').sum(),len(fixed))})

_, sets = span_sets(ROOT / 'runs/span1')
w = sets.pivot_table(index=['model','family_id','dimension'],columns='prompt_id',values='coverage').reset_index()
w = w[~w.family_id.isin(['act-10','act-16'])]
w['h'] = [sha1(m,f) for m,f in zip(w.model,w.family_id)]
w = w.sort_values(['h','model','family_id'])
polite = w[w.dimension.eq('politeness')]
loss = polite[(polite.P2==1)&(polite.I2==0)]
r = loss.iloc[0]
sp = read('runs/span1/scored.parquet')
outputs=[]
for arm in ['P2','I2']:
    rows=sp[(sp.family_id==r.family_id)&(sp.model==r.model)&(sp.variant=='A')&
            (sp.channel=='bare')&(sp.prompt_id==arm)].sort_values(['sample_idx','suggestion_idx'])
    assert len(rows)==3
    outputs.extend(occurrence('span1',row) for _,row in rows.iterrows())
pc=w[w.dimension.isin(['polarity','certainty'])]
card('S10','First politeness set losing both-reading coverage, SHA1(model,family); show all three original slots in both P2 and I2.',
     {v:x['source'] for v,x in it[r.family_id]['variants'].items()},outputs,
     {'politeness_covered_P2':rate(polite.P2.sum(),len(polite)),
      'politeness_covered_I2':rate(polite.I2.sum(),len(polite)),
      'politeness_coverage_lost':rate(len(loss),len(polite)),
      'target_coverage_P2':rate(pc.P2.sum(),len(pc)),
      'target_coverage_I2':rate(pc.I2.sum(),len(pc))})

# Independent verification against original JSONL; preserve every exact string.
for run in sorted({r['run'] for r in occurrences}):
    path=f'runs/{run}/outputs.jsonl'
    used.add(path)
    rows=[(n,json.loads(s)) for n,s in enumerate((ROOT/path).open(),1)]
    for rec in [r for r in occurrences if r['run']==run]:
        matches=[(n,x) for n,x in rows if all(x[k]==rec[k] for k in
                 ['output_id','request_key','model','family_id','variant','channel','prompt_id'])]
        assert len(matches)==1,(run,rec,matches)
        n,x=matches[0]
        assert x['text']==rec['text'] and x['input_text']==rec['input_text']
        rec['jsonl_line']=n

used.update(['annotation/judge_validation_main1.json','analysis/r2c/report.md',
             'analysis/applicability/report.md','analysis/interventions/report.md',
             'ideas/cycles/c3/select_story.py'])
result={'date':'2026-11-01','status':'post-outcome illustrative selection; rates describe the declared stratum',
        'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(used)},
        'verified_occurrences':len(occurrences),'cards':sorted(cards,key=lambda x:int(x['id'][1:]))}
Path(__file__).with_name('story_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for c in result['cards']:
    print(c['id'],c['source'],json.dumps(c['rates']))
    for r in c['outputs']:
        print(r['run'],r['family_id'],r['variant'],r['model'],r['prompt_id'],r['channel'],r['output_id'],r['jsonl_line'],repr(r['input_text']),'->',repr(r['text']))
print('Verified',len(occurrences),'stored occurrences across',len(cards),'cards.')
