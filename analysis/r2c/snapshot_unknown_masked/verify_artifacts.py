"""Cross-artifact audit from original scored columns, not the analysis script's frames."""
from pathlib import Path
import hashlib,json,re,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'analysis/r2c'
sys.path.insert(0,str(ROOT/'src'))
from analyze import family_bootstrap,load_items
items=load_items(str(ROOT/'data/items/r2_c[12].jsonl'))
r=pd.read_parquet(ROOT/'runs/r2c1/scored.parquet');r=r[r.prompt_id.eq('P0')].copy()
r.loc[r.critical_source.isin(['J1','J2']),'critical']=None
r['cluster']=r.family_id.map(lambda f:items[f]['cluster_id'])
r['target']=[items[f]['variants'][v]['critical_value'] for f,v in zip(r.family_id,r.variant)]
r['m']=[float(t==c) if pd.notna(c) else np.nan for t,c in zip(r.target,r.critical)]
p=json.loads((O/'primary.json').read_text())['primaries'];head=json.loads((O/'headline.json').read_text())
# Independently rebuild the paired endpoint units from the original table.
a=r[r.dimension.eq('speech_act') & ~r.family_id.isin(['r2act-078','r2act-079'])].pivot(index=['family_id','cluster','variant','model'],columns='channel',values='m').reset_index();a['v']=a.chip1-a.noncrit
f=r[r.dimension.eq('politeness') & r.channel.eq('full')].copy();f['switch']=[float(c==('polite' if t=='plain' else 'plain')) if pd.notna(c) else np.nan for t,c in zip(f.target,f.critical)]
b=f.pivot(index=['family_id','cluster','model'],columns='target',values='switch').reset_index();b['v']=b.plain-b.polite
c=r[r.dimension.eq('polarity') & r.channel.eq('bare')].sort_values('variant').drop_duplicates(['family_id','model','request_key','sample_idx','suggestion_idx']).copy();c['v']=[float(x=='affirmative')-.5 if x in {'affirmative','negated'} else np.nan for x in c.critical]
for k,z in [('P1',a),('P2',b),('P3',c)]:
 assert z['v'].count()==p[k]['n'] and len(z)==p[k]['n_total'],k
 assert z['cluster'].nunique()==p[k]['n_clusters'],k
 z=z.copy();z['family_id']=z['cluster']
 q=family_bootstrap(z,'v',n_boot=10000,seed=20261031)
 for key in ['estimate','ci_low','ci_high']:assert np.isclose(q[key],p[k][key],atol=1e-14), (k,key)
 assert head[k.lower()]==p[k]['estimate']
order=sorted(p,key=lambda k:p[k]['p_one_sided']);last=0
for j,k in enumerate(order):
 last=max(last,min(1,(3-j)*p[k]['p_one_sided']));assert last==p[k]['p_holm']
assert all(type(v) in {int,float} and np.isfinite(v) for v in head.values())
for key in head:
 if key.endswith('_ci_low'):
  base=key[:-7];assert head[key]<=head[base]<=head[base+'_ci_high'];assert base+'_n' in head and base+'_n_clusters' in head
fig=json.loads((ROOT/'paper/figs/r2c/fig_numbers.json').read_text())
assert fig['n_boot']==10000 and fig['seed']==20261031 and fig['cluster_unit']=='cluster_id'
assert fig['strict_critical'] and fig['exclude_primary']
lad=pd.read_csv(O/'channel_ladder.csv');cov=pd.read_csv(O/'coverage.csv')
for d in ['polarity','speech_act','politeness']:
 for ch in ['bare','noncrit','chip1','chipall','full']:
  z=lad[(lad.dimension==d)&(lad.channel==ch)&(lad.metric=='critical_match')].iloc[0]
  for key in ['estimate','ci_low','ci_high']:assert np.isclose(fig['fig_channel_ladder'][d][ch][key],z[key]),(d,ch,key)
 for prompt in ['P2','S3']:
  z=cov[(cov.dimension==d)&(cov.channel=='bare')&(cov.prompt_id==prompt)&(cov.metric=='coverage_at_3')].iloc[0]
  for key in ['estimate','ci_low','ci_high','n']:assert np.isclose(fig['fig_sets']['by_dim'][d][prompt][key],z[key]),(d,prompt,key)
for arm,typ in [('addition','added to a plain source'),('removal','removed from a polite source')]:
 for key in ['estimate','ci_low','ci_high','n']:assert np.isclose(fig['fig_politeness_ratchet']['Politeness']['Pooled'][typ][key],p['P2'][arm][key])
assert np.isclose(fig['fig_defaults']['polarity']['shares']['affirmative']['estimate'],317/320)
keys=['family_id','variant','model','prompt_id','channel','request_key','sample_idx','suggestion_idx']
stored={tuple(x[k] for k in keys):x for x in map(json.loads,(ROOT/'runs/r2c1/outputs.jsonl').open())}
ex=json.loads((O/'examples.json').read_text())
d=pd.read_parquet(O/'scored.parquet');p0=d[d.prompt_id.eq('P0')]
elig=pd.read_csv(O/'h1_eligibility.csv');eligible=set(elig[elig.eligible].family_id)
sets=pd.read_csv(O/'suggestion_sets.csv')
for x in ex:
 s=stored[tuple(x[k] for k in keys)];assert s['text']==x['text'] and s['input_text']==x['input_text']
 rank=hashlib.sha256(json.dumps([20261031,x['category'],[str(x[k]) for k in keys]]).encode()).hexdigest();assert rank==x['selection_sha256']
 if 'output_set' in x:
  os=sorted([v for v in stored.values() if all(v[k]==x[k] for k in ['family_id','variant','model','channel','prompt_id','request_key'])],key=lambda v:v['suggestion_idx'])
  assert x['output_set']==[dict(output_id=v['output_id'],text=v['text']) for v in os]
 cat=x['category']
 if cat=='Bare affirmative default':
  candidates=p0[p0.dimension.eq('polarity') & p0.channel.eq('bare')].sort_values('variant').drop_duplicates(['family_id','model','request_key','sample_idx','suggestion_idx'])
  candidates=candidates[candidates.crit.eq('affirmative')]
 elif cat=='Full-input politeness addition':
  candidates=p0[p0.dimension.eq('politeness') & p0.channel.eq('full') & p0.cv.eq('plain') & p0.crit.eq('polite')]
 elif cat=='Question cue failure':
  candidates=p0[p0.dimension.eq('speech_act') & p0.channel.eq('chip1') & p0.cv.eq('question') & p0.critical_match.eq(False)]
 elif cat=='H1 Llama plain request loss':
  candidates=p0[p0.family_id.isin(eligible) & p0.model.eq('llama3.1-8b') & p0.channel.eq('chipall') & p0.cv.eq('plain') & p0.speech_act.notna() & ~p0.speech_act.eq('request/command')]
 else:
  dim=cat.removeprefix('P2 coverage miss ')
  base=d[d.dimension.eq(dim) & d.prompt_id.eq('P2') & d.channel.eq('bare') & d.variant.eq('A') & d.suggestion_idx.eq(0)]
  candidates=base.merge(sets[['family_id','variant','model','prompt_id','channel','request_key','coverage_at_3']],on=['family_id','variant','model','prompt_id','channel','request_key'])
  candidates=candidates[candidates.coverage_at_3.eq(False)]
 ranks=[hashlib.sha256(json.dumps([20261031,cat,[str(v[k]) for k in keys]]).encode()).hexdigest() for v in candidates.to_dict('records')]
 assert min(ranks)==x['selection_sha256'],('selection rule',cat)
for name in ['fig_channel_ladder','fig_cost_asymmetry','fig_defaults','fig_pipeline','fig_politeness_ratchet','fig_sets']:
 for ext in ['pdf','png']:assert (ROOT/'paper/figs/r2c'/f'{name}.{ext}').stat().st_size>1000
for file,sh in json.loads((O/'metadata.json').read_text())['files'].items():
 assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==sh,('hash changed',file)
assert hashlib.sha256((ROOT/'runs/r2c1/scored.parquet').read_bytes()).hexdigest()==json.loads((O/'metadata.json').read_text())['input_sha256']
checks=dict(status='passed',primary_units_and_ci_recomputed=True,holm_recomputed=True,figures_match_analysis=True,example_occurrences_verified=len(ex),example_minimum_hash_rule_verified=True,flat_headline_numeric=True,source_hashes_verified=True,helper_regression_tests=13,macro_verification=json.loads((O/'macro_verification.json').read_text()))
(O/'verification.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
