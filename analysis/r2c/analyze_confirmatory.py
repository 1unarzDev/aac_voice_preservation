"""W-C local-only registered contrast analysis. Run with the project venv from repo root.

FREEZE.md and eligibility files must already exist. This script never rewrites them.
"""
from pathlib import Path
import sys, json, hashlib, re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import analyze as A
from labels import GENERAL_DIMS
O=ROOT/'analysis/r2c'; B=10000; SEED=20261031
items=A.load_items(str(ROOT/'data/items/r2_c[12].jsonl'))
assert (O/'FREEZE.md').exists() and (O/'h1_eligibility.csv').exists() and (O/'h2_construction.csv').exists()
raw=pd.read_parquet(ROOT/'runs/r2c1/scored.parquet')
assert set(raw.family_id)==set(items) and len(items)==240
assert not raw.duplicated(['family_id','variant','channel','model','prompt_id','request_key','sample_idx','suggestion_idx']).any()
fallback=raw.critical_source.isin(['J1','J2'])
strict=raw.copy(); strict.loc[fallback,['critical','critical_source']]=None
all_df=A.normalize_table(strict,items)
for c in ['cluster_id','construction','primary_exclude']:
 all_df[c]=all_df.family_id.map(lambda f:items[f].get(c,''))
assert all_df.cluster_id.ne('').all()
excluded={f for f,i in items.items() if i.get('primary_exclude') or (i['dimension']=='speech_act' and any(v['critical_value'] in {'refusal','acceptance'} for v in i['variants'].values()))}
df=all_df[~all_df.family_id.isin(excluded)].copy()
df.to_parquet(O/'scored.parquet',index=False)
MODELS=sorted(df.model.unique()); headline={}; tables={}

def boot(g,col='value',test=False):
 # Reuse analyze.py exact row-weighted multinomial bootstrap, with the true cluster
 # substituted only for its grouping column. Never rename the actual family identifier.
 x=g.copy(); x['family_id']=x.cluster_id
 r=A.family_bootstrap(x,col,n_boot=B,seed=SEED)
 r['n_clusters']=r.pop('n_families'); r['n_clusters_observed']=r.pop('n_families_observed')
 r['n_families']=int(g.family_id.nunique())
 counts=g.groupby('cluster_id',sort=True)[col].count().astype(float)
 r['n_clusters_effective']=float(counts.sum()**2/(counts**2).sum()) if counts.sum() else 0.
 if r['n']:
  r['sum']=float(pd.to_numeric(g[col]).sum())
 if test and r['n']:
  agg=x.groupby('family_id',sort=True)[col].agg(['sum','count'])
  w=np.random.default_rng(SEED).multinomial(len(agg),np.full(len(agg),1/len(agg)),size=B)
  den=w@agg['count'].to_numpy(float); draws=(w@agg['sum'].to_numpy(float))[den>0]/den[den>0]
  centered=draws-r['estimate']; n=len(draws)
  r['p_one_sided']=(1+int((centered>=r['estimate']-1e-12).sum()))/(n+1)
  r['p_two_sided']=(1+int((abs(centered)>=abs(r['estimate'])-1e-12).sum()))/(n+1)
  r['bootstrap_degenerate']=bool(np.ptp(draws)==0)
 return r

def summarize(g,groups,metrics):
 rows=[]
 for key,x in g.groupby(groups,sort=True,dropna=False):
  if not isinstance(key,tuple):key=(key,)
  for col in metrics: rows.append(dict(zip(groups,key))|{'metric':col}|boot(x,col))
 return pd.DataFrame(rows)

def export(key,r):
 for k in ['estimate','ci_low','ci_high','n','n_clusters','n_clusters_effective','n_total','n_missing']:
  if k in r:headline[key if k=='estimate' else key+'_'+k]=r[k]

def primary_frames(d):
 p0=d[d.prompt_id.eq('P0')]
 keys=['family_id','cluster_id','construction','variant','model']
 act=p0[p0.dimension.eq('speech_act') & ~p0.family_id.isin(excluded)]
 a=act.pivot(index=keys,columns='channel',values='critical_match').reset_index()
 a['value']=pd.to_numeric(a.chip1).astype(float)-pd.to_numeric(a.noncrit).astype(float)
 pol=p0[p0.dimension.eq('politeness') & p0.channel.eq('full')].copy()
 # A direction switch can only be established for an extracted target value;
 # unclear is observed non-switch, missing label stays missing.
 pol['switch']=[np.nan if not A.known(r.crit) or not r.valid else float(r.crit==('polite' if r.cv=='plain' else 'plain')) for r in pol.itertuples()]
 b=pol.pivot(index=['family_id','cluster_id','construction','model'],columns='cv',values='switch').reset_index()
 b['value']=b.plain-b.polite
 amb=A.unique_ambiguous(p0[p0.dimension.eq('polarity') & p0.channel.eq('bare')]).copy()
 amb['value']=[float(r.crit=='affirmative')-.5 if r.valid and r.crit in {'affirmative','negated'} else np.nan for r in amb.itertuples()]
 return {'P1':a,'P2':b,'P3':amb}

def holm(rs,pkey,outkey):
 order=sorted(rs,key=lambda k:rs[k][pkey]);prev=0
 for j,k in enumerate(order):
  prev=max(prev,min(1.,(len(order)-j)*rs[k][pkey]));rs[k][outkey]=prev

frames=primary_frames(df)
primary={k:boot(v,test=True) for k,v in frames.items()}
holm(primary,'p_one_sided','p_holm');holm(primary,'p_two_sided','p_holm_two_sided')
for k,r in primary.items():r['reject_holm_005']=bool(r['p_holm']<=.05 and r['estimate']>0);export(k.lower(),r)
primary_strata=[]
for k,g in frames.items():
 for field in ['model','construction']:
  for name,x in g.groupby(field):primary_strata.append(dict(contrast=k,stratum_type=field,stratum=name)|boot(x))
 for (model,con),x in g.groupby(['model','construction']):primary_strata.append(dict(contrast=k,stratum_type='model/construction',stratum=model+'/'+con)|boot(x))
tables['primary_strata']=pd.DataFrame(primary_strata)
# Arm rates preserve all available labels; paired counts are separate above.
act=df[df.prompt_id.eq('P0') & df.dimension.eq('speech_act') & df.channel.isin(['noncrit','chip1'])]
arm=summarize(act,['channel'],['critical_match']).assign(contrast='P1')
f=df[df.prompt_id.eq('P0') & df.dimension.eq('politeness') & df.channel.eq('full')].copy()
f['switch']=[np.nan if not A.known(r.crit) or not r.valid else float(r.crit==('polite' if r.cv=='plain' else 'plain')) for r in f.itertuples()]
arms=summarize(f,['cv'],['switch']).assign(contrast='P2')
for cv,key in [('plain','politeness_addition'),('polite','politeness_removal')]:export(key,arms[arms.cv.eq(cv)].iloc[0].to_dict())
bare=frames['P3'].copy();bare['affirmative_share']=bare.value+.5
p3rate=boot(bare,'affirmative_share');export('bare_affirmative_share',p3rate)
primary['P3']['affirmative_share']=p3rate
primary['P2']['addition']=arms[arms.cv.eq('plain')].iloc[0].to_dict();primary['P2']['removal']=arms[arms.cv.eq('polite')].iloc[0].to_dict()
tables['primary_arms']=pd.concat([arm,arms],ignore_index=True)
tables['politeness_direction_by_model']=summarize(f,['model','cv'],['switch'])
# Sensitivities do not replace the registered fixed sample.
early=json.loads((O/'pre_freeze_cache.json').read_text());earlyf={t['family_id'] for r in early for t in r['targets']}
sens=[]
for name,d in [('exclude_any_pre_freeze_cache_family',df[~df.family_id.isin(earlyf)]),('exclude_negative_question_r2pol077',df[~df.family_id.eq('r2pol-077')]),('supplied_J1_fallback',A.normalize_table(raw,items))]:
 if 'cluster_id' not in d:
  d=d.copy()
  for c in ['cluster_id','construction']:d[c]=d.family_id.map(lambda f:items[f][c])
 for k,g in primary_frames(d).items():sens.append(dict(sensitivity=name,contrast=k)|boot(g))
# P3 alternate denominator: all known outputs (including unclear/other).
x=A.unique_ambiguous(df[df.prompt_id.eq('P0') & df.dimension.eq('polarity') & df.channel.eq('bare')]).copy()
x['value']=[np.nan if not A.known(r.crit) else float(r.valid and r.crit=='affirmative')-.5 for r in x.itertuples()]
sens.append(dict(sensitivity='P3_all_known_outputs',contrast='P3')|boot(x))
tables['primary_sensitivity']=pd.DataFrame(sens)
# P0 five-channel ladder, pooled and per model.
p0=df[df.prompt_id.eq('P0')]
tables['channel_ladder']=summarize(p0,['dimension','channel'],['critical_match','constraint_preserving','input_actions','input_characters'])
tables['channel_ladder_by_model']=summarize(p0,['dimension','channel','model'],['critical_match','constraint_preserving'])
# channel differences also support C2/C3 descriptive checks.
keys=['family_id','cluster_id','construction','variant','dimension','model']
a=p0.pivot(index=keys,columns='channel',values='critical_match').reset_index()
for hi,lo in [('chip1','noncrit'),('noncrit','bare'),('chip1','full')]:a[hi+'-'+lo]=pd.to_numeric(a[hi]).astype(float)-pd.to_numeric(a[lo]).astype(float)
tables['channel_differences']=summarize(a,['dimension'],['chip1-noncrit','noncrit-bare','chip1-full'])
amb=A.unique_ambiguous(df)
amb['affirmative']=[np.nan if not A.known(r.crit) else float(r.valid and r.crit=='affirmative') for r in amb.itertuples()]
tables['commitment']=summarize(amb,['dimension','channel','prompt_id'],['commitment','affirmative'])
# Set outputs remain target-specific for costs; coverage deduplicates A/B.
sets=A.suggestion_sets(df)
for c in ['cluster_id','construction']:sets[c]=sets.family_id.map(lambda f:items[f][c])
sets.to_csv(O/'suggestion_sets.csv',index=False)
u=sets.sort_values('variant').drop_duplicates(['family_id','channel','model','prompt_id','set_id','input_text'])
tables['coverage']=summarize(u,['dimension','channel','prompt_id'],['coverage_at_3','n_suggestions'])
tables['coverage_by_model']=summarize(u,['dimension','channel','prompt_id','model'],['coverage_at_3'])
uc=sets.pivot(index=['family_id','variant','cluster_id','dimension','channel','model','input_text'],columns='prompt_id',values='coverage_at_3').reset_index()
uc=uc.sort_values('variant').drop_duplicates(['family_id','channel','model','input_text'])
uc['value']=pd.to_numeric(uc.P2).astype(float)-pd.to_numeric(uc.S3).astype(float)
tables['coverage_difference']=summarize(uc,['dimension','channel'],['value'])
for r in tables['coverage'].query("metric=='coverage_at_3' and channel=='bare'").to_dict('records'):export('coverage_'+r['dimension']+'_'+r['prompt_id'].lower(),r)
# All stance counts preserve target references. Ambiguous input does not identify intent.
metrics=[f'addition_{d}' for d in GENERAL_DIMS]+['politeness_added','certainty_raised','added_content']
tables['stance_additions']=summarize(df[df.channel.isin(['bare','noncrit'])],['dimension','channel','prompt_id'],metrics)
tables['stance_by_model']=summarize(df[df.channel.isin(['bare','noncrit'])],['dimension','channel','prompt_id','model'],['politeness_added','certainty_raised','addition_speech_act','addition_agent'])
# Nominal selection costs: 0 top target, 1 another set slot, otherwise critical-chip count.
single=p0[p0.channel.isin(['bare','noncrit'])].copy()
single['extra_actions']=[0 if r.chose==r.variant else r.repair_chip_cost if A.known(r.chose) or not r.valid else np.nan for r in single.itertuples()]
single['first_choice']=single.chose
cost=pd.concat([single,sets],ignore_index=True)
cost['reading']=['default' if r.first_choice==r.variant else 'non-default' if r.first_choice in {'A','B'} else 'unidentified' for r in cost.itertuples()]
tables['nominal_action_cost']=summarize(cost,['dimension','channel','prompt_id','reading'],['extra_actions'])
# H1 frozen source eligibility; no outcome-dependent exclusions.
elig=pd.read_csv(O/'h1_eligibility.csv'); eligf=set(elig[elig.eligible].family_id)
h=p0[p0.family_id.isin(eligf) & p0.channel.isin(['chipall','full'])].copy()
h['retention']=[np.nan if not r.valid or not A.known(r.speech_act) else float(r.speech_act=='request/command') for r in h.itertuples()]
tables['h1_arms']=summarize(h,['channel','model','cv'],['retention','critical_match','constraint_preserving'])
hp=h.pivot(index=['family_id','cluster_id','construction','model','channel'],columns='cv',values='retention').reset_index();hp['value']=hp.plain-hp.polite
tables['h1_difference']=summarize(hp,['channel','model'],['value'])
for row in tables['h1_difference'].to_dict('records'):
 row['passes_replication_threshold']=row['estimate']<=-.2 and row['ci_high']<0
 if row['model']=='llama3.1-8b':export('h1_llama_'+row['channel'],row)
# Save derived promotion flags separately (no inferential multiplicity claim).
h1=[r|{'passes_replication_threshold':bool(r['estimate']<=-.2 and r['ci_high']<0)} for r in tables['h1_difference'].to_dict('records')]
# General label sensitivities on H1, using existing judge records only.
judges={(r['text_id'],r['family_id'],r['input_text']):r for r in map(json.loads,(ROOT/'runs/r2c1/judgments.jsonl').open())}
jrows=[]
for judge in ['J1','J2']:
 z=h.copy(); z['retention']=[(float(judges[(r.text_id,r.family_id,r.input_text)].get(judge+'_speech_act')=='request/command') if judges.get((r.text_id,r.family_id,r.input_text),{}).get(judge+'_speech_act') is not None else np.nan) for r in z.itertuples()]
 zp=z.pivot(index=['family_id','cluster_id','model','channel'],columns='cv',values='retention').reset_index();zp['value']=zp.plain-zp.polite
 jrows.append(summarize(zp,['model','channel'],['value']).assign(label_sensitivity=judge))
tables['h1_judge_sensitivity']=pd.concat(jrows,ignore_index=True)
# H2 frozen before scored read; one analyst only; descriptive.
coding=pd.read_csv(O/'h2_construction.csv')
q=p0[p0.dimension.eq('speech_act') & p0.cv.eq('question') & p0.channel.isin(['chip1','chipall','full'])].merge(coding[['family_id','variant','construction_label']],on=['family_id','variant'])
q['loss']=1-pd.to_numeric(q.critical_match)
tables['h2_question_loss']=summarize(q,['channel','construction_label'],['loss'])
# Jointly resample construction clusters for action-minus-state rate differences.
h2gaps=[]
for ch,z in q[q.construction_label.isin(['action/event','state/evaluation'])].groupby('channel'):
 agg=z.groupby(['cluster_id','construction_label']).loss.agg(['sum','count']).unstack('construction_label').fillna(0.)
 w=np.random.default_rng(SEED).multinomial(len(agg),np.full(len(agg),1/len(agg)),size=B)
 vals={};ns={}
 for lab in ['action/event','state/evaluation']:
  sn=agg[('sum',lab)].to_numpy(float);dn=agg[('count',lab)].to_numpy(float)
  den=w@dn
  vals[lab]=np.divide(w@sn,den,out=np.full(B,np.nan),where=den>0)
  ns[lab]=int(z[z.construction_label.eq(lab)].cluster_id.nunique())
 draws=vals['action/event']-vals['state/evaluation']; draws=draws[np.isfinite(draws)]
 est=float(z[z.construction_label.eq('action/event')].loss.mean()-z[z.construction_label.eq('state/evaluation')].loss.mean())
 lo,hi=np.quantile(draws,[.025,.975])
 h2gaps.append(dict(channel=ch,estimate=est,ci_low=lo,ci_high=hi,n=int(z.loss.count()),n_total=len(z),n_missing=int(z.loss.isna().sum()),n_clusters=len(agg),n_clusters_observed=len(agg),n_clusters_effective=float('nan'),action_clusters=ns['action/event'],state_clusters=ns['state/evaluation'],n_boot_valid=len(draws),numeric_threshold_met=ns['action/event']>=10 and ns['state/evaluation']>=10 and est>=.10 and lo>0,independent_audit_complete=False))
tables['h2_action_minus_state']=pd.DataFrame(h2gaps)
# C11 transitions, includes question/request targets and all three dimensions.
tables['cue_value_match_by_model']=summarize(p0[p0.channel.eq('chip1')],['dimension','model','cv'],['critical_match'])
tables['cue_value_match']=summarize(p0[p0.channel.eq('chip1')],['dimension','cv'],['critical_match'])
trans=p0[p0.dimension.eq('speech_act') & p0.channel.eq('chip1')].groupby(['cv','crit'],dropna=False).size().reset_index(name='n')
tables['speech_act_transitions']=trans
# D-018 diagnostic only, not in primary or other endpoints.
tables['excluded_d018_diagnostic']=summarize(all_df[all_df.family_id.isin(excluded) & all_df.prompt_id.eq('P0')],['family_id','channel'],['critical_match'])
# Freeze chronology as it applies to each registered contrast.
early_primary=[]
for r in early:
 if r['prompt_id']!='P0':continue
 for t in r['targets']:
  f0,ch=t['family_id'],t['channel']
  k='P1' if f0.startswith('r2act') and ch in ['chip1','noncrit'] else 'P2' if f0.startswith('r2plt') and ch=='full' else 'P3' if f0.startswith('r2pol') and ch=='bare' else None
  if k:early_primary.append(dict(contrast=k,**{a:r[a] for a in ['request_key','model','created_utc']},family_id=f0,channel=ch))
tables['primary_pre_freeze_cache']=pd.DataFrame(early_primary).drop_duplicates()
# Deterministic examples and exact output provenance.
outkeys=['family_id','variant','model','prompt_id','channel','request_key','sample_idx','suggestion_idx']
stored={tuple(r[k] for k in outkeys):r for r in map(json.loads,(ROOT/'runs/r2c1/outputs.jsonl').open())}
examples=[]; estr=['# W-C deterministic example manifest\n',f'Seed {SEED}. For each declared phenomenon below, rank eligible stored output occurrences by SHA256(JSON([seed, category, [family, variant, model, prompt, channel, request, sample, suggestion]])). Select the smallest hash; no manual substitution. Outcome-conditioned illustrative selection; rates use the full declared stratum, never the selected example. Exact input/output strings are checked against runs/r2c1/outputs.jsonl.\n']
def example(category,pop,event,rule):
 r=boot(pop.assign(event=event.astype(float)),'event'); candidates=pop[event.fillna(False)].copy()
 estr.append(f'\n## {category}\n\nRule: {rule}. Rate: {fmt(r)}.\n')
 if not len(candidates):estr.append('No qualifying observed occurrence.\n');return
 def rank(v):return hashlib.sha256(json.dumps([SEED,category,[str(v[k]) for k in outkeys]]).encode()).hexdigest()
 records=candidates.to_dict('records');chosen=min(records,key=rank)
 st=stored[tuple(chosen[k] for k in outkeys)];assert st['text']==chosen['text'] and st['input_text']==chosen['input_text']
 e={k:chosen[k] for k in outkeys+['output_id','text_id','text','input_text','source']};e.update(category=category,selection_sha256=rank(chosen),rule=rule,rate=r)
 if category.startswith('P2 coverage miss'):
  os=sorted([v for k,v in stored.items() if all(v[c]==chosen[c] for c in ['family_id','variant','model','prompt_id','channel','request_key'])],key=lambda v:v['suggestion_idx'])
  e['output_set']=[{'output_id':v['output_id'],'text':v['text']} for v in os]
  estr.append('Complete stored set: '+json.dumps([v['text'] for v in os],ensure_ascii=False)+'\n')
 examples.append(e)
 estr.append(f"`{chosen['family_id']}/{chosen['variant']}`, {chosen['model']}, {chosen['channel']}, output `{chosen['output_id']}`; label `{chosen['crit']}`.\n\nSource: {json.dumps(chosen['source'],ensure_ascii=False)}\n\nInput: {json.dumps(chosen['input_text'],ensure_ascii=False)}\n\nOutput: {json.dumps(chosen['text'],ensure_ascii=False)}\n")

def fmt(r,pp=False):
 if not A.known(r.get('estimate')):return f"NA; n=0/{r.get('n_total',0)}"
 mult=100;unit=' pp' if pp else '%'
 return f"{r['estimate']*mult:.2f}{unit} [{r['ci_low']*mult:.2f}, {r['ci_high']*mult:.2f}]; n={r['n']}/{r['n_total']}, clusters={r['n_clusters_observed']}/{r['n_clusters']}, eff={r['n_clusters_effective']:.1f}"

z=A.unique_ambiguous(p0[p0.dimension.eq('polarity') & p0.channel.eq('bare')]);example('Bare affirmative default',z,z.crit.eq('affirmative'),'P0 bare polarity; affirmative event; shared A/B target deduplicated')
z=f[f.cv.eq('plain') & f.crit.notna()];example('Full-input politeness addition',z,z.crit.eq('polite'),'P0 full politeness plain targets, known critical label; plain→polite event')
z=p0[p0.dimension.eq('speech_act') & p0.channel.eq('chip1') & p0.cv.eq('question') & p0.critical_match.notna()];example('Question cue failure',z,z.critical_match.eq(False),'P0 question chip1 targets with observed match; failure event')
z=h[h.model.eq('llama3.1-8b') & h.channel.eq('chipall') & h.cv.eq('plain') & h.retention.notna()];example('H1 Llama plain request loss',z,z.retention.eq(0),'Frozen H1 eligible Llama P0 plain chipall; non-request event')
for dim in ['polarity','speech_act','politeness']:
 z=df[df.dimension.eq(dim) & df.channel.eq('bare') & df.prompt_id.eq('P2') & df.variant.eq('A')].merge(u[['family_id','model','prompt_id','channel','set_id','coverage_at_3']],on=['family_id','model','prompt_id','channel'])
 z=z[z.suggestion_idx.eq(0) & z.coverage_at_3.notna()]
 example('P2 coverage miss '+dim,z,z.coverage_at_3.eq(False),'P2 bare sets with known coverage; event=the set misses at least one pair value; complete stored set displayed and first slot identifies the occurrence')
(O/'examples.md').write_text('\n'.join(estr));dump=lambda p,v:(O/p).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,(np.integer,)):return int(x)
 if isinstance(x,(np.bool_,)):return bool(x)
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 return x
for name,t in tables.items():t.to_csv(O/(name+'.csv'),index=False)
dump('examples.json',examples)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=dict(table='runs/r2c1/scored.parquet',input_sha256=sha(ROOT/'runs/r2c1/scored.parquet'),n_boot=B,seed=SEED,cluster='cluster_id',exclusions=sorted(excluded),fallback_rows=int(fallback.sum()),versions={'pandas':pd.__version__,'numpy':np.__version__},files={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/analyze.py',ROOT/'src/labels.py',O/'FREEZE.md',O/'h1_eligibility.csv',O/'h2_construction.csv',ROOT/'annotation/CODEBOOK.md',ROOT/'annotation/CB_rules.md',ROOT/'runs/r2c1/config.json',ROOT/'runs/requests/r2c.jsonl',ROOT/'runs/r2c1/judgments.jsonl',ROOT/'runs/r2c1/generations.jsonl',ROOT/'runs/r2c1/outputs.jsonl',ROOT/'paper/figs/make_figs.py'] if p.exists()})
dump('metadata.json',meta)
primary_json=dict(status='registered_contrasts_with_cache_and_unresolved_adjudication_qualifications',alpha=.05,multiplicity='Holm across three pooled positive-direction tests',n_boot=B,seed=SEED,cluster='cluster_id',primaries=primary,strata=primary_strata,metadata=meta)
dump('primary.json',primary_json)
headline.update(n= len(df),n_clusters=int(df.cluster_id.nunique()),n_families=int(df.family_id.nunique()),n_families_inclusive=240,n_models=4,n_boot=B,seed=SEED,pre_freeze_cache_requests=len(early),fully_fresh_confirmation=0,unadjudicated_fallback_rows=int(fallback.sum()))
for k,r in primary.items():headline[k.lower()+'_p_holm']=r['p_holm'];headline[k.lower()+'_reject_holm_005']=int(r['reject_holm_005'])
dump('headline.json',headline)
# CALE legacy report.json readiness; the flat headline is imported separately by both macro scripts.
dump('report.json',dict(primary=primary,h1=h1,population={'n_families':238,'n_clusters':df.cluster_id.nunique()},headline=headline))
# Human gate is external evidence; do not claim W-C-specific human annotation.
jvpath=ROOT/'annotation/judge_validation_main1.json';human=json.loads(jvpath.read_text()).get('human') if jvpath.exists() else None
report=['# W-C: registered contrasts and discovery replication\n',
f'**{sum(r["reject_holm_005"] for r in primary.values())}/3 registered directions pass Holm α=.05 in the protocol-aligned analysis. Confirmation is qualified:** 48 cached requests predate the final item freeze (20 also predate the PREREG mtime), and the supplied scoring used unadjudicated J1 fallback. The primary analysis treats fallback critical labels as unresolved; neither an unqualified wholly fresh sample nor completed cross-family adjudication is claimed. See [FREEZE.md](FREEZE.md), [primary.json](primary.json), and sensitivities below.\n',
'## Population, chronology and scoring\n',
'All generation records contributing to a registered primary contrast postdate the PREREG mtime. Twelve distinct primary requests predate the final item mtimes: eight P1 noncrit requests and four P3 bare requests; P2 has none. Thus primary prereg-before-generation ordering is supported locally, while final-item-freeze-before-every-primary-generation ordering is not. [Primary timestamp audit](primary_pre_freeze_cache.csv).\n',
f'Fixed 240 approved families: 80 polarity, 80 speech act, 80 politeness; 40 seeded/30 drafted/10 adversarial per dimension. No resizing or new calls. D-018 excludes r2act-078/079 from primary speech act (78 families). They remain in the inclusive scored input and [diagnostic](excluded_d018_diagnostic.csv). Other descriptive tables exclude these families consistently. Inclusive recorded clusters: {all_df.cluster_id.nunique()}; analyzed clusters: {df.cluster_id.nunique()}. Cross-file shared seeds and the r2pol-044/052 construction cluster are kept intact. Four models are a fixed roster.\n',
f'Input contains {len(raw):,} target rows; analyzed {len(df):,}; P0 has all 9,600 planned inclusive target rows. All five channels are present for P0/P2/S3. PREREG called for P2/S3 bare; D-022 describes bare/noncrit, but the stored manifest actually generated all five channels for all three prompt regimes. Extra generated channels do not enlarge the primary test family. 38,300 unique generation records map to 48,000 request targets and {len(raw):,} exploded/scored suggestions. The cache audit found {len(early)} early requests across {len(earlyf)} families: {", ".join(sorted(earlyf))}. All 48,000 request input targets match current source specs exactly. The fixed primary sample is retained; family-exclusion sensitivity is supplementary. Hash/timestamp evidence cannot prove these cache outputs followed the final freeze.\n',
f'Supplied critical_source counts: {raw.critical_source.value_counts(dropna=False).to_dict()}. No r2c1 arbiter file exists. {int(fallback.sum())} fallback rows are converted to unknown critical labels, without altering the input parquet. General dimensions retain the supplied production labels, including its existing general-label resolution. Scored invalid completions: {int((~raw.valid).sum())}; critical unknown after masking: {int(all_df.crit.isna().sum())}. General missingness: {raw[GENERAL_DIMS].isna().sum().to_dict()}. Critical unknowns are excluded; invalid completions count as match failures. The available human-gold report '+('contains human validation' if human else 'has no completed human section')+' on the earlier validation inventory; this is not a W-C human spot-check or proof of every new boundary label.\n',
'## PRIMARY registered contrasts\n',
'Estimate and pointwise 95% percentile CI; differences in percentage points. n is observed/total analysis units (paired targets for P1; paired family×model directional switches for P2; unique family×model bare outputs with affirmative/negated readings for P3). Each P2 pair comprises two outputs. Cluster counts are observed/available, with Kish effective clusters from cluster row denominators. Holm tests the three pooled contrasts only; per-model/construction entries are descriptive. P1/P2 contrast names are not prompt IDs; all three use prompt P0.\n']
rows=[]
for k,r in primary.items():rows.append({'contrast':k,'estimand':{'P1':'speech-act chip1−noncrit match','P2':'full politeness addition−removal','P3':'bare affirmative share−0.5'}[k],'estimate [95% CI], n, clusters':fmt(r,True),'p one-sided':r['p_one_sided'],'Holm p':r['p_holm'],'reject .05':r['reject_holm_005']})
report += [A.markdown_table(pd.DataFrame(rows)),f'P3 affirmative share: {fmt(p3rate)}. The denominator is 317 affirmative + 2 negated; one observed unclear reading is outside the directional denominator (not an unknown judge label). The all-known-output sensitivity is 317/320 = 99.06%. Full politeness addition: {fmt(primary["P2"]["addition"])}; removal: {fmt(primary["P2"]["removal"])}.\n',
'Bootstrap: 10,000 whole recorded seed/construction-cluster multinomial resamples, seed 20261031, row-weighted means, paired comparisons retained jointly. Helpers from src/analyze.py are reused with cluster_id as the resampling group. No independent model bootstrap or independence assumption across outputs within a cluster. Unadjusted 95% CIs are not simultaneous Holm intervals. PREREG did not specify test tails or a p-value algorithm: the analysis freeze declares null-centered one-sided bootstrap tests in the expected positive direction; two-sided centered-bootstrap Holm sensitivity is included in primary.json. The Monte Carlo p floor is 1/10001. Boundary bootstrap intervals may collapse and do not establish zero population risk.\n',
'### Descriptive per-model and construction estimates\n']
for field in ['model','construction']:
 t=tables['primary_strata'];t=t[t.stratum_type.eq(field)]
 report.append(A.markdown_table(pd.DataFrame([{'contrast':r['contrast'],'stratum':r['stratum'],'estimate [95% CI], n, clusters':fmt(r,True)} for r in t.to_dict('records')])))
report+=['### Primary sensitivity (descriptive; no sample substitution)\n',A.markdown_table(pd.DataFrame([{'sensitivity':r['sensitivity'],'contrast':r['contrast'],'estimate [95% CI], n, clusters':fmt(r,True)} for r in sens])),
'## Secondary/descriptive endpoints\n',
'The descriptive results refine several discovery claims: C2 does not establish equivalence of a noncritical word and bare input; C3 does not hold at full-input fidelity for speech act; C4’s “not polarity” clause does not repeat (P2−S3 polarity coverage is +7.19 pp); C7 repeats as a pooled direction, with Qwen and Llama having more removals than additions. C11 speech-act chips are weakest among the three tested dimensions, and statements are weaker than question/request targets here. C5 and C9 cannot be tested by this design; C10’s encoding-comparison clause cannot be tested.\n',
'### Full channel ladder\n\nP0 critical match is reference agreement for bare/noncrit, supplied-critical preservation for chip1/chipall/full. Ambiguous agreement is not accuracy. Joint supplied predicates are a partial contract; fluency and complete semantic equivalence are not evaluated.\n']
for tab,metric,groupcols in [('channel_ladder','critical_match',['dimension','channel']),('coverage','coverage_at_3',['dimension','channel','prompt_id']),('coverage_difference','value',['dimension','channel'])]:
 if tab=='coverage':report.append('### Coverage@3: P2 versus S3\n\nBoth pair values among the first three suggestions; shared A/B targets deduplicated. P2 uses one greedy three-suggestion request; S3 uses three T=.7 draws. Unknown labels yield unknown coverage unless both values are already observed. Noncrit sometimes renders words in different source order across variants: those distinct inputs remain distinct set occurrences; shared inputs are deduplicated. P2−S3 comparisons pair by target and actual input text before deduplicating shared inputs. Incomplete sets are retained and flagged; no fabricated third output.\n')
 t=tables[tab];t=t[t.metric.eq(metric)]
 report.append(A.markdown_table(pd.DataFrame([{**{k:r[k] for k in groupcols},'estimate [95% CI], n, clusters':fmt(r,tab=='coverage_difference')} for r in t.to_dict('records')])))
report+=['### Stance additions\n\nTarget-reference-relative additions under ambiguous input, not errors against unknowable private intent. General speech act/agent mismatch and politeness addition use source all_chips/general_spec. Certainty n/a is excluded; certainty_raised follows analyze.py, and added_content remains judge-defined. All dimensions/prompts/channels are in [stance_additions.csv](stance_additions.csv) and per-model rates in [stance_by_model.csv](stance_by_model.csv).\n']
st=tables['stance_additions'];st=st[st.prompt_id.eq('P0') & st.channel.eq('bare') & st.metric.isin(['politeness_added','certainty_raised','addition_speech_act','addition_agent'])]
report.append(A.markdown_table(pd.DataFrame([{'dimension':r['dimension'],'metric':r['metric'],'rate [95% CI], n, clusters':fmt(r)} for r in st.to_dict('records')])))
report+=['### Nominal action cost, default versus non-default\n\nDefault is each output/set top-1 A/B reading. Unclear/other top-1 is unidentified and separately retained. A target costs 0 extra selections if top-1 matches, 1 if another of three matches, otherwise the number of target critical chips. Fallback is a nominal input cost with no guarantee of preservation; it excludes typing time, motor effort and retry cost. Not a user study. Both channel definitions, all prompts and unidentified rates are in [nominal_action_cost.csv](nominal_action_cost.csv). Figure cost defines the family modal default instead and labels that descriptive rule explicitly.\n']
co=tables['nominal_action_cost'];co=co[co.channel.eq('bare')]
report.append(A.markdown_table(pd.DataFrame([{'dimension':r['dimension'],'prompt':r['prompt_id'],'reading':r['reading'],'mean actions [95% CI]':f"{r['estimate']:.3f} [{r['ci_low']:.3f}, {r['ci_high']:.3f}]",'n':r['n'],'clusters':r['n_clusters']} for r in co.to_dict('records')])))
report+=['## Discovery-claim replication (secondary unless explicitly PRIMARY above)\n',
'Original C1–C11 and C17 are discovery claims. Fresh matching endpoints test transfer of the pattern, not confirm every clause of the original claim. Only registered P1/P2/P3 have confirmatory multiplicity control. An absence of difference is not equivalence.\n']
lad=tables['channel_ladder'];dif=tables['channel_differences'];cov=tables['coverage']
def line(tab,**filters):
 x=tab
 for k,v in filters.items():x=x[x[k].eq(v)]
 return fmt(x.iloc[0].to_dict(),tab is dif) if len(x) else 'not available'
claims=[('C1','PRIMARY P3 counterpart',fmt(p3rate)),('C2','Descriptive length-control check','; '.join(d+': '+line(dif,dimension=d,metric='noncrit-bare') for d in ['polarity','speech_act','politeness'])+'; no equivalence margin was registered.'),('C3','Descriptive chip1 versus full','; '.join(d+': '+line(dif,dimension=d,metric='chip1-full') for d in ['polarity','speech_act','politeness'])+'; no noninferiority margin, so “full-level” is not formally established.'),('C4','Descriptive P2−S3 coverage','; '.join(r['dimension']+': '+fmt(r,True) for r in tables['coverage_difference'].query("channel=='bare'").to_dict('records'))),('C5','Not testable in W-C','AACText natural-corpus POS-cap4 cue prevalence requires S1/W-B; authored balanced pairs cannot estimate corpus prevalence.'),('C6','PRIMARY P2 related endpoint','Full politeness addition '+fmt(primary['P2']['addition'])+'; literal please-only counts are reported below.'),('C7','PRIMARY P2 counterpart','Addition−removal '+fmt(primary['P2'],True)+'; model directions may differ from discovery.'),('C8','Partial replication','Polarity '+fmt(p3rate)+'; certainty/agent-critical strata absent, so their discovery default rates are not retested.'),('C9','Not testable in W-C','No controlled factorial YES/NOT × I/YOU composition/repeats; use W-D.'),('C10','Partial descriptive diagnostic','PLAIN/ASK behavior in W-C is observable, but Exp B alias/NL factor and constant-content perturbation design are absent; no encoding superiority replication.'),('C11','Descriptive + registered P1','Speech-act chip1 value-specific matches and transitions below; “weakest” is scoped to three W-C dimensions, not all discovery dimensions.'),('C17','Frozen-eligibility secondary replication','H1: 74 eligible / 6 ineligible families; model/channel retention contrasts and thresholds below.')]
report.append(A.markdown_table(pd.DataFrame(claims,columns=['claim','status','W-C evidence / scope'])))
report.append(A.markdown_table(pd.DataFrame([{'dimension':r['dimension'],'source target':r['cv'],'chip1 match [95% CI], n, clusters':fmt(r)} for r in tables['cue_value_match'].to_dict('records')])))
plainfull=p0[p0.dimension.eq('politeness') & p0.channel.eq('full') & p0.cv.eq('plain')].copy();plainfull['please_only']=plainfull.politeness.eq('please').astype(float)
report.append('C6 literal please-only extraction: '+fmt(boot(plainfull,'please_only'))+'. This category is narrower than any-polite addition.\n')
report+=['### H1 / C17: paired request retention\n\nEligibility was written from source specs before loading scored outcomes: [h1_eligibility.csv](h1_eligibility.csv). Six excluded families: '+', '.join(elig[~elig.eligible].family_id)+'. Both source variants must be explicit requests with the same expressible actor. Llama is the focal secondary replication; other models descriptive. Success threshold is plain−polite ≤−20 pp and upper 95% bound <0. A chip-only effect remains encoding-specific.\n',A.markdown_table(pd.DataFrame([{'model':r['model'],'channel':r['channel'],'plain−polite [95% CI], n, clusters':fmt(r,True),'threshold met':r['passes_replication_threshold']} for r in h1]))]
report.append('C17 replicates the large Llama request-retention gap under chipall, with the cache-provenance qualification. It does not replicate perfect plain-register match: Llama matches plain register on 69/74 chipall targets; request retention is 9/74 plain versus 74/74 polite. Full request retention is 62/74 versus 72/74. The full-input gap is below the registered magnitude threshold, so the promoted replication is encoding-specific.\n')
for r in h1:
 if r['model']=='llama3.1-8b':report.append(f"Llama {r['channel']}: "+('meets' if r['passes_replication_threshold'] else 'does not meet')+' the frozen replication threshold.\n')
report.append('Plain/polite arm retention, register match and joint preservation are in [h1_arms.csv](h1_arms.csv); raw per-judge retention differences are in [h1_judge_sensitivity.csv](h1_judge_sensitivity.csv). General-label judge sensitivity does not replace the production endpoint.\n')
report+=['### H2: question construction coding (descriptive)\n\n53 question sources were coded before scored inspection: action/event, state/evaluation, unresolved. D-018 leaves 52 analyzed question sources. [h2_construction.csv](h2_construction.csv) retains all 53 and their exclusions. A single analyst coded predicates/source syntax; independent coding audit is not available, so the construction headline is not promoted.\n',A.markdown_table(pd.DataFrame([{'channel':r['channel'],'construction':r['construction_label'],'question loss [95% CI], n, clusters':fmt(r)} for r in tables['h2_question_loss'].to_dict('records')]))]
report.append('Action-minus-state question-loss differences (joint seed/construction-cluster resampling, not independent resampling of overlapping construction strata):\n')
report.append(A.markdown_table(pd.DataFrame([{'channel':r['channel'],'gap pp [95% CI]':f"{100*r['estimate']:.2f} [{100*r['ci_low']:.2f}, {100*r['ci_high']:.2f}]",'n':r['n'],'action/state clusters':f"{r['action_clusters']}/{r['state_clusters']}",'numeric threshold met':r['numeric_threshold_met'],'independent audit':False} for r in h2gaps])))
report+=['## Limitations and reproducibility\n',
'Items/source hashes and actual timestamp ordering are in FREEZE.md; that file was written during analysis, not before generation. Caches include earlier generations; exclusion sensitivity cannot establish prospective registration retroactively. The request builder deduplicated identical visible inputs and reuses them as multiple target occurrences where applicable; recorded cluster_id preserves known seed/construction dependence, but distinct authored families can still share a model request. Sensitivity excluding early-cache families does not repair every possible content overlap. New item human spot-check completion is not established here. Automated labels and a partial contract cannot certify full meaning, fluency, communicative usefulness or population-wide model behavior.\n',
'J1 fallback was a deviation in orchestration/r2c_judge.sh. Protocol-aligned unknown masking prevents an arbitrary fallback from entering the primary estimate; final arbiter adjudication is still outstanding. Complete-case analysis can be biased by outcome-related missingness; supplied-J1 sensitivity is not adjudication. General labels follow the stored production resolution. Per-model and construction intervals are pointwise descriptive with small adversarial construction inventories.\n',
'Reproduce with `.venv/bin/python analysis/r2c/analyze_confirmatory.py` (set OPENBLAS_NUM_THREADS=1 for predictable local performance). Do not rerun freeze_analysis.py after outcomes: FREEZE.md is an audit record, not regenerated output. All analysis is CPU/local files; no API, judge or GPU server calls. [metadata.json](metadata.json) hashes the inputs, source eligibility and analysis helpers. [headline.json](headline.json) is flat numeric unit-scale estimates (multiply by 100 for percentages/pp); `<key>_ci_low`, `_ci_high`, `_n`, `_n_clusters` accompany each estimate. Top-level n counts analyzed target/suggestion rows, while endpoint-specific n is authoritative. [report.json](report.json) supplies the CALE readiness compatibility artifact.\n',
'Figure reproduction: `.venv/bin/python paper/figs/make_figs.py --table runs/r2c1/scored.parquet --items \'data/items/r2_c[12].jsonl\' --out paper/figs/r2c --n-boot 10000 --seed 20261031 --cluster-by-items --strict-critical --exclude-primary`. Publication figures and their numeric manifest: [paper/figs/r2c](../../paper/figs/r2c/). Examples: [examples.md](examples.md), with [machine-readable provenance](examples.json). Complete table index:\n']
report.append('\n'.join('- ['+n+'.csv]('+n+'.csv)' for n in tables))
(O/'report.md').write_text('\n'.join(report))
print(json.dumps(clean(primary),indent=2)); print('Wrote',O,'tables',len(tables))
