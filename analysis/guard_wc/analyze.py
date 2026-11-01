"""Action 6 paired analysis; CPU only, never invokes a model or edits paper/."""
from pathlib import Path
import sys, json, hashlib, sqlite3, time, argparse
from collections import Counter
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import runio, analyze as A, attribute, labels
from explode import normalise
OUT=ROOT/'analysis/guard_wc'; RUN=ROOT/'runs/guard_wc'
NBOOT=10000; SEED=20261101
KEY=['model','family_id','variant','channel']

def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.generic):x=x.item()
    if isinstance(x,float) and not np.isfinite(x):return None
    return x
def write(name,obj): (OUT/name).write_text(json.dumps(clean(obj),indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metric(g,values,eligible=None,cluster='family_id'):
    vals=pd.Series(values,index=g.index,dtype=float)
    if eligible is None:eligible=pd.Series(True,index=g.index)
    vals=vals.where(eligible)
    f=pd.DataFrame({'family_id':g[cluster],'value':vals})
    r=A.family_bootstrap(f,'value',n_boot=NBOOT,seed=SEED)
    r.update(k=float(vals.sum()) if vals.notna().any() else None,
             n_total=int(eligible.sum()),n_missing=int((eligible & vals.isna()).sum()),
             n_planned=len(g),cluster_by=cluster)
    return r
def fmt(r):
    if not r['n']:return f'unknown (0/{r["n_total"]})'
    return f'{100*r["estimate"]:.2f} [{100*r["ci_low"]:.2f}, {100*r["ci_high"]:.2f}] (n={r["n"]}/{r["n_total"]})'
def count(r):return f'{int(round(r["k"]))}/{r["n"]}' if r['n'] else '0/0'

def cost():
    rows=[]
    if (OUT/'budget.sqlite').exists():
        c=sqlite3.connect(OUT/'budget.sqlite')
        rows=pd.read_sql_query('SELECT * FROM calls ORDER BY id',c).to_dict('records');c.close()
    pd.DataFrame(rows).to_csv(OUT/'actual_calls.csv',index=False)
    gen=[r for r in rows if r['kind']=='generation']; judge=[r for r in rows if r['kind']=='judge']
    logical=runio.read_jsonl(RUN/'logical_calls.jsonl') if (RUN/'logical_calls.jsonl').exists() else []
    launch=json.loads((OUT/'launch.json').read_text())
    return dict(actual_generation_calls=len(gen),actual_judge_batch_calls=len(judge),new_arbitration_calls=0,
        generation_http_failures=sum(r['status']!=200 for r in gen),
        judge_http_failures=sum(r['status']!=200 for r in judge),logical_guard_attempts=len(logical),
        cached_guard_attempts=sum(r.get('cached',False) for r in logical),
        logical_guard_errors=sum(bool(r.get('error')) for r in logical),
        actual_generation_http_latency_sum_s=sum(r['end']-r['start'] for r in gen if r['end']),
        actual_judge_http_latency_sum_s=sum(r['end']-r['start'] for r in judge if r['end']),
        wall_elapsed_s=time.time()-launch['start_epoch'],generation_cap=2000,judge_batch_cap=400,wall_cap_s=14400,
        actual_by_model=dict(Counter(r['model'] for r in gen)))

def score():
    items=runio.load_items(OUT/'items.jsonl')
    base=pd.read_parquet(OUT/'baseline_scored.parquet')
    base_lookup={tuple(r[k] for k in KEY):r for r in base.to_dict('records')}
    raw=attribute.score(RUN,OUT/'items.jsonl')
    # P0 and exact unchanged outputs retain their frozen evaluation byte-for-field.
    # Changed outcomes receive the standard blind evaluation and cached arbiter only.
    records=[]
    for r in raw.to_dict('records'):
        b=base_lookup[tuple(r[k] for k in KEY)]
        if r['prompt_id']=='P0' or r['text']==b['text']:
            identity={k:r[k] for k in ['output_id','text_id','request_key','prompt_id','text','input_text']}
            r={**b,**identity,'evaluation_provenance':'frozen first-pass label reuse'}
        else:r['evaluation_provenance']='blind J1/J2; existing A-unit arbiter > agreement > unresolved'
        records.append(r)
    raw=pd.DataFrame(records)
    assert len(raw)==5616 and not raw.duplicated(KEY+['prompt_id']).any()
    raw.to_parquet(RUN/'scored.parquet',index=False)
    frame=A.normalize_table(raw,items)
    gens={g['request_key']:g for g in runio.read_jsonl(RUN/'generations.jsonl')}
    for col in ['base_key','flags_initial','flags_final','changed','extra_calls','extra_latency_s','check_ms','guard_errors']:
        if col=='base_key':frame[col]=[gens[k].get('base_request_key',k) for k in frame.request_key]
        elif col=='changed':frame[col]=[bool(gens[k].get(col,False)) for k in frame.request_key]
        else:frame[col]=[gens[k].get(col) for k in frame.request_key]
    frame['cluster_id']=frame.family_id.map(lambda f:items[f]['cluster_id'])
    frame['joint']=pd.to_numeric(frame.constraint_preserving).astype(float)
    strict=[]
    for r in frame.itertuples():
        cp=r.joint
        spec=labels.general_spec(items[r.family_id]['variants'][r.variant].get('all_chips',[]),
                                 items[r.family_id]['variants'][r.variant].get('general_spec'))
        if cp==0 or r.politeness_added is True:strict.append(0.)
        elif not A.known(cp) or (spec['politeness']=={'none'} and not A.known(r.politeness)):strict.append(np.nan)
        else:strict.append(1.)
    frame['strict']=strict
    frame.to_parquet(OUT/'scored.parquet',index=False)
    baseline=A.normalize_table(base,items).set_index(KEY).sort_index()
    now=frame[frame.prompt_id.eq('P0')].set_index(KEY).sort_index()
    for col in ['crit']+labels.GENERAL_DIMS+['constraint_preserving']:
        assert baseline[col].fillna('MISSING').equals(now[col].fillna('MISSING')),col
    return frame,gens

def arm_metrics(g,cluster='family_id'):
    return {name:metric(g,g[col],cluster=cluster) for name,col in
            [('joint_pass','joint'),('strict_pass','strict'),('critical_match','critical_match'),('politeness_added','politeness_added')]}
def pair_frame(frame,arm):
    b=frame[frame.prompt_id.eq('P0')].set_index(KEY)
    t=frame[frame.prompt_id.eq(arm)].set_index(KEY)
    p=b.join(t,lsuffix='_P0',rsuffix='_arm',validate='one_to_one').reset_index()
    p['cluster_id']=p.cluster_id_P0
    assert len(p)==1872
    return p
def pair_metrics(p,cluster='family_id'):
    result={}
    for ep in ['joint','strict']:
        b=p[ep+'_P0'];t=p[ep+'_arm']
        bad=b.eq(0);ok=b.eq(1)
        result[ep+'_gain']=metric(p,t-b,cluster=cluster)
        result[ep+'_repair']=metric(p,t,bad,cluster=cluster)
        # Explicit conservative scored-repair count keeps every known initial failure.
        result[ep+'_repair_lower']=metric(p,t.eq(1).astype(float),bad,cluster=cluster)
        result[ep+'_changed_correct']=metric(p,p.changed_arm.astype(float),ok,cluster=cluster)
        result[ep+'_pass_to_fail']=metric(p,1-t,ok,cluster=cluster)
        result[ep+'_residual']=metric(p,1-t,cluster=cluster)
        result[ep+'_unknown_among_initial_fail']=int((bad & t.isna()).sum())
        result[ep+'_unknown_among_initial_pass']=int((ok & t.isna()).sum())
        lower=t.fillna(0)-b.fillna(1);upper=t.fillna(1)-b.fillna(0)
        result[ep+'_gain_identification_bound']=[float(lower.mean()),float(upper.mean())]
    result['initial_flagged_targets']=int(p.flags_initial_P0.map(bool).sum())
    result['residual_flagged_targets']=int(p.flags_final_arm.map(bool).sum())
    result['strict_residual_flagged']=int((p.strict_arm.eq(0)&p.flags_final_arm.map(bool)).sum())
    result['strict_residual_targets']=int(p.strict_arm.eq(0).sum())
    result['changed_targets']=int(p.changed_arm.sum())
    return result

def audit(frame):
    b=frame[frame.prompt_id.eq('P0')].set_index(KEY)
    g=frame[frame.prompt_id.eq('G1')].set_index(KEY)
    rows=[];meta={}
    for group,candidates in [('changed',g[g.changed]),('unchanged_correct',g[(~g.changed)&b.strict.eq(1)])]:
        candidates=candidates.reset_index().sort_values(KEY)
        candidates['norm']=candidates.text.map(normalise)
        candidates['selection_hash']=candidates.norm.map(lambda s:hashlib.sha256(s.encode()).hexdigest())
        distinct=candidates.drop_duplicates('norm').sort_values(['selection_hash']+KEY)
        meta[group]=dict(eligible_occurrences=len(candidates),eligible_distinct=len(distinct),selected=min(20,len(distinct)),
                         selection='fixed ascending SHA256(normalized text); deterministic, not probability sampling')
        for r in distinct.head(20).to_dict('records'):
            rows.append(dict(group=group,selection_hash=r['selection_hash'],text=r['text'],model=r['model'],
                family_id=r['family_id'],variant=r['variant'],channel=r['channel'],input_text=r['input_text'],
                output_id=r['output_id'],n_memberships=int(candidates.norm.eq(r['norm']).sum()),
                HUMAN_complete='',HUMAN_preservation_beyond_focal=''))
    pd.DataFrame(rows).to_csv(OUT/'audit_sample.csv',index=False)
    meta.update(human_labels_completed=0,new_human_time_allocated=0,sample_sha256=sha(OUT/'audit_sample.csv'))
    write('audit_manifest.json',meta)

def main(exit_code):
    c=cost()
    if not (RUN/'judgments.jsonl').exists() or not (RUN/'generations.jsonl').exists():
        verdict='INCOMPLETE; transfer not established'
        write('headline.json',dict(status='incomplete',transfer_verdict=verdict,cost=c,exit_code=exit_code))
        (OUT/'report.md').write_text(f'# W-C guard transfer\n\n{verdict}. Pipeline exit {exit_code}.\n\n'
            'The full frozen population is retained; no model/failure subset is substituted.\n\n'+
            f'Actual calls: {c["actual_generation_calls"]} generation, {c["actual_judge_batch_calls"]} judge batches. '
            'See FREEZE.md, admission.json, runner.log and actual_calls.csv. No usable-repair claim.\n')
        return
    frame,gens=score()
    arms={a:arm_metrics(g) for a,g in frame.groupby('prompt_id')}
    pairs={a:pair_frame(frame,a) for a in ['G1','G1s']}
    comparisons={a:pair_metrics(p) for a,p in pairs.items()}
    companion={a:pair_metrics(p,'cluster_id') for a,p in pairs.items()}
    bymodel={};bychannel={};table=[]
    for field,out in [('model',bymodel),('channel',bychannel)]:
        for val,g in frame.groupby(field):
            out[val]={'arms':{a:arm_metrics(x) for a,x in g.groupby('prompt_id')},
                      'paired':{a:pair_metrics(p[p[field].eq(val)]) for a,p in pairs.items()}}
            for a,pr in out[val]['paired'].items():
                for m,r in pr.items():
                    if isinstance(r,dict) and 'estimate' in r:
                        table.append(dict(stratum_type=field,stratum=val,arm=a,metric=m,**r))
    pd.DataFrame(table).to_csv(OUT/'stratified_effects.csv',index=False)
    for a,p in pairs.items():p.to_parquet(OUT/f'paired_{a}.parquet',index=False)
    # Each cost unit is a unique request, never a repeated target occurrence.
    unique=[g for g in gens.values() if g['prompt_id']=='G1']
    costs_by_model={}
    for model in sorted({g['model'] for g in unique}):
        us=[g for g in unique if g['model']==model]
        flagged=[g for g in us if g['flags_initial']]
        costs_by_model[model]=dict(inputs=len(us),flagged=len(flagged),logical_attempts=sum(g['extra_calls'] for g in us),
            changed=sum(g['changed'] for g in us),residual_flags=sum(bool(g['flags_final']) for g in us),
            stored_extra_latency_s_sum=sum(g['extra_latency_s'] for g in us),
            stored_extra_latency_s_per_input=sum(g['extra_latency_s'] for g in us)/len(us),
            stored_extra_latency_s_flagged_median=float(np.median([g['extra_latency_s'] for g in flagged])) if flagged else None,
            check_ms_median=float(np.median([g['check_ms'] for g in us])),
            errors=sum(bool(g['guard_errors']) for g in us),actual_generation_calls=c['actual_by_model'].get(model,0))
    c['by_model']=costs_by_model
    c['calls_per_input']=c['actual_generation_calls']/len(unique)
    c['calls_per_flagged']=c['actual_generation_calls']/508
    c['initial_flags']=dict(Counter(f for g in unique for f in g['flags_initial']))
    c['final_flags']=dict(Counter(f for g in unique for f in g['flags_final']))
    c['residual_flagged_unique']=sum(bool(g['flags_final']) for g in unique)
    g=comparisons['G1']
    complete=exit_code==0 and len(unique)==1848
    criteria=dict(repair_ge_30=g['strict_repair_lower']['estimate']>=.30,
                  changed_correct_le_10=g['strict_changed_correct']['estimate']<=.10,
                  positive_joint_gain_lower95_gt0=g['joint_gain']['ci_low']>0,
                  completed_full_design=complete,
                  within_budget=c['actual_generation_calls']<=2000 and c['actual_judge_batch_calls']<=400 and c['wall_elapsed_s']<=14400)
    success=all(criteria.values())
    verdict=('PASS: frozen guard transfers on the scored partial predicate endpoint' if success else
             'FAIL: frozen guard does not meet the memo\'s transfer criteria' if complete else
             'INCOMPLETE: transfer not established')
    head=dict(status='complete' if complete else 'incomplete',n_families=78,n_targets=1872,n_unique=1848,F=508,
              transfer_success=success,transfer_verdict=verdict,criteria=criteria,arms=arms,paired=comparisons,
              recorded_cluster_sensitivity=companion,per_model=bymodel,per_channel=bychannel,cost=c,
              n_boot=NBOOT,seed=SEED,usable_repair_validated=False,
              freeze_sha256=sha(OUT/'FREEZE.md'),launch_manifest_sha256=sha(OUT/'launch_manifest.json'))
    for a,r in arms.items():
        for m in ['joint_pass','strict_pass']:
            for key in ['estimate','ci_low','ci_high','n','n_total','n_missing']:
                head[f'{a.lower()}_{m}'+('' if key=='estimate' else '_'+key)]=r[m][key]
    for a,r in comparisons.items():
        for m in ['joint_gain','strict_repair','strict_changed_correct','strict_pass_to_fail']:
            for key in ['estimate','ci_low','ci_high','n','n_total','n_missing']:
                head[f'{a.lower()}_{m}'+('' if key=='estimate' else '_'+key)]=r[m][key]
    audit(frame)
    L=['# W-C speech-act guard transfer (cycle-2 Action 6)\n',f'**{verdict}.**\n',
       'This is the single optional CALE-AI guard-transfer experiment, launched early under D-040 and the user instruction. '
       'No guard/prompt tuning, new models, extra families or I2 generation. The prior discovery guard result is a separate population.\n',
       '## Prospective freeze, inventory and endpoint\n',
       f'FREEZE.md and its SHA256 `{sha(OUT/"FREEZE.md")}` precede all retry requests; launch_manifest.json freezes the adapter/analysis code. '
       'Frozen inputs, first passes and labels are byte-preserved under frozen/. 78 speech-act families, two variants, four fixed models, '
       'three cue channels (chip1/chipall/full): **1,872 target occurrences / 1,848 unique requests**. D-018 excludes r2act-078/079. '
       '**F=508; 2F=1,016 ≤2,000**, so the full design was admitted; the memo judge formula gives 164 initial batches before cache reuse.\n',
       'G1 and G1s call the unchanged src/interventions.py policy functions. G1 uses at most two monitor-triggered retries; first unflagged '
       'else fewest flags, earliest on ties. G1s only strips unsupplied please/pls/plz. The monitor never sees evaluation labels. '
       'Generation uses temperature 0, local seed 1000, 96 tokens; local serving is one llama.cpp server at a time under flock /tmp/aacv_gpu.lock, '
       '4 slots × 1024 context, NGL=99; API concurrency 8 and judge concurrency 12. All long work launched with setsid nohup.\n',
       'Primary joint pass is the existing analyze.normalize_table constraint-preserving endpoint: focal value and all other scored supplied '
       'predicates, with missing needed labels unknown unless a known failure dominates. Strict pass also prohibits politeness addition '
       'and supplies the earlier guard\'s repair/changed-correct criteria. Numbers below are machine-scored partial predicates. '
       'Neither sentence completeness nor full meaning nor communicative usefulness is certified.\n',
       '## Paired P0 / G1 / G1s\n',
       'Rates and pointwise 95% percentile intervals in percent; n=observed/planned eligible target occurrences. '
       '10,000 whole-family resamples, seed 20261101, paired arms/models/channels retained jointly. '
       'No resampling of models and no multiplicity claim.\n',
       '| arm | joint supplied-predicate pass | strict pass | focal match | politeness added |',
       '|---|---|---|---|---|']
    for a in ['P0','G1','G1s']:
        r=arms[a];L.append(f'| {a} | {fmt(r["joint_pass"])} | {fmt(r["strict_pass"])} | {fmt(r["critical_match"])} | {fmt(r["politeness_added"])} |')
    L+=['\nPaired differences in percentage points. Repair rates condition on initial strict failures; changed-correct and pass→fail condition '
        'on initial strict passes. Unknown returned labels remain unknown. The conservative repair criterion counts only known returned passes '
        'over **all** known initial failures, including unresolved returned outcomes in its denominator.\n',
        '| arm | joint-pass gain, pp | strict failures repaired | correct-text changed | pass→fail | residual strict failures |',
        '|---|---|---|---|---|---|']
    for a in ['G1','G1s']:
        r=comparisons[a];L.append(f'| {a} | {fmt(r["joint_gain"])} | {count(r["strict_repair"])}; {fmt(r["strict_repair"])} | '
            f'{count(r["strict_changed_correct"])}; {fmt(r["strict_changed_correct"])} | {count(r["strict_pass_to_fail"])}; '
            f'{fmt(r["strict_pass_to_fail"])} | {count(r["strict_residual"])}; {fmt(r["strict_residual"])} |')
    L+=['\n## Transfer criteria\n','| fixed criterion | result | passes |','|---|---|---|',
        f'| strict repairs ≥30% (conservative full initial-failure denominator) | {fmt(g["strict_repair_lower"])} | {criteria["repair_ge_30"]} |',
        f'| initially strict-correct text changed ≤10% | {fmt(g["strict_changed_correct"])} | {criteria["changed_correct_le_10"]} |',
        f'| paired joint-pass gain lower 95% bound >0 | {fmt(g["joint_gain"])} pp | {criteria["positive_joint_gain_lower95_gt0"]} |',
        f'| completed fixed design / resource cap | {complete} / {criteria["within_budget"]} | {complete and criteria["within_budget"]} |',
        '\nFailure of any criterion is negative transfer, not a tuning invitation. The old human extraction gate H7 passed on the '
        'main1 inventory; it does not independently validate new repairs. No usable-repair rate is claimed.\n',
        '## Per-model and channel effects\n','| model | P0 joint | G1 joint | G1s joint | G1−P0 joint, pp | G1 strict repair | G1 correct-text changed | G1 pass→fail |',
        '|---|---|---|---|---|---|---|---|']
    for m,r in bymodel.items():
        ar=r['arms'];pr=r['paired']['G1']
        L.append(f'| {m} | {fmt(ar["P0"]["joint_pass"])} | {fmt(ar["G1"]["joint_pass"])} | {fmt(ar["G1s"]["joint_pass"])} | '
                 f'{fmt(pr["joint_gain"])} | {count(pr["strict_repair"])}; {fmt(pr["strict_repair"])} | '
                 f'{count(pr["strict_changed_correct"])} | {count(pr["strict_pass_to_fail"])} |')
    L+=['\n| channel | P0 joint | G1 joint | G1s joint | G1−P0 joint, pp |','|---|---|---|---|---|']
    for ch,r in bychannel.items():
        ar=r['arms'];L.append(f'| {ch} | {fmt(ar["P0"]["joint_pass"])} | {fmt(ar["G1"]["joint_pass"])} | '
            f'{fmt(ar["G1s"]["joint_pass"])} | {fmt(r["paired"]["G1"]["joint_gain"])} |')
    L+=['\nFull per-model/channel endpoint, harm and missingness estimates: stratified_effects.csv and headline.json.\n',
        '## Unknowns, scoring and cluster sensitivity\n',
        'Frozen P0 labels are retained exactly. An unchanged output reuses its baseline labels. Existing W-C arbitration may be reused '
        'only on the same production A-unit (text ID, critical dimension and options). All new critical J1/J2 disagreements are '
        'recorded in unresolved.jsonl and receive no J1 fallback or new arbitration. General labels retain production J1/J2 agreement, '
        'otherwise the existing layer0 tie-break; agreement-only sensitivity below removes this source of dependence. Known contradictions '
        'dominate missingness; unknowns are never silently promoted to passes.\n']
    unresolved=runio.read_jsonl(OUT/'unresolved.jsonl')
    L.append(f'New unresolved critical J-units: **{len(unresolved)}**; distinct A-units: '
        f'**{len({(r["text_id"],r["dimension"],tuple(r["critical_options"])) for r in unresolved})}**. '
        'The target counts below may repeat an extraction decision.\n')
    for a in ['P0','G1','G1s']:
        x=frame[frame.prompt_id.eq(a)]
        L.append(f'- {a}: critical unknown {int(x.crit.isna().sum())}; joint unknown {int(x.joint.isna().sum())}; '
            f'strict unknown {int(x.strict.isna().sum())}; invalid {int((~x.valid).sum())}.')
    for a,r in comparisons.items():
        bounds=r['joint_gain_identification_bound'];rs=companion[a]
        L.append(f'- {a}−P0 joint gain over all planned targets: identification bound '
            f'[{100*bounds[0]:.2f}, {100*bounds[1]:.2f}] pp (not a CI). Recorded seed/construction-cluster '
            f'bootstrap: {fmt(rs["joint_gain"])} pp, {rs["joint_gain"]["n_families"]} clusters. '
            f'Initial strict failures with unknown returned labels: {r["strict_unknown_among_initial_fail"]}; '
            f'initial passes with unknown returned labels: {r["strict_unknown_among_initial_pass"]}.')
    # Agreement-only general-label sensitivity is fixed before launch, applied to every arm.
    sens=frame.copy()
    raw=pd.read_parquet(RUN/'scored.parquet')
    lookup={tuple(r[k] for k in KEY+[ 'prompt_id']):r for r in raw.to_dict('records')}
    # raw stores general final labels, while J1/J2 values are in judgments.
    jj={(r['text_id'],r['family_id'],r['input_text']):r for r in runio.read_jsonl(RUN/'judgments.jsonl')}
    for ix,r in sens.iterrows():
        j=jj.get((r.text_id,r.family_id,r.input_text),{})
        for d in labels.GENERAL_DIMS:
            if j.get('J1_'+d)!=j.get('J2_'+d):sens.at[ix,d]=None
    sen=A.normalize_table(sens,runio.load_items(OUT/'items.jsonl'))
    sen['joint']=pd.to_numeric(sen.constraint_preserving).astype(float)
    sensitivity={}
    for a in ['G1','G1s']:
        p=pair_frame(sen,a);r=metric(p,p.joint_arm-p.joint_P0)
        sensitivity[a]=r
        L.append(f'- General-label agreement-only sensitivity, {a} joint gain: {fmt(r)} pp. '
            'New critical disagreements remain unresolved in this sensitivity.')
    head['general_agreement_only_gain']=sensitivity
    L+=['\nW-C\'s early-cache and post-outcome baseline arbitration qualifications travel with this transfer. '
        'The new retry freeze is prospective, but cannot repair the original baseline chronology. '
        'Family bootstrap is the requested primary uncertainty; shared recorded clusters are reported as a companion. '
        'No independent quality audit or W-C-specific human source validation is created here.\n',
        '## Monitor, residual flags and resource use\n',
        f'G1 residual flags: **{c["residual_flagged_unique"]}/1,848 unique returned requests**. '
        f'Among {g["strict_residual_targets"]} known residual strict target failures, '
        f'**{g["strict_residual_flagged"]}** remain flagged; {g["residual_flagged_targets"]}/1,872 returned target '
        'occurrences carry any flag. Flags are monitor diagnostics, not measured warning benefit.\n',
        f'Actual HTTP calls: **{c["actual_generation_calls"]} generation** / 2,000; '
        f'**{c["actual_judge_batch_calls"]} judge batches** / 400 (all failures/retries included); '
        f'**0 new arbitration**. Logical guard attempts {c["logical_guard_attempts"]}, '
        f'cache hits {c["cached_guard_attempts"]}, logical errors {c["logical_guard_errors"]}. '
        f'Actual extra calls/input {c["calls_per_input"]:.4f}, /flagged input {c["calls_per_flagged"]:.4f}. '
        f'Elapsed through analysis {c["wall_elapsed_s"]:.1f} s / 14,400 s.\n',
        '| model | inputs | initially flagged | logical attempts / actual calls | residual flagged unique | extra stored latency s/input | flagged median s | monitor median ms |',
        '|---|---|---|---|---|---|---|---|']
    for m,r in costs_by_model.items():
        L.append(f'| {m} | {r["inputs"]} | {r["flagged"]} | {r["logical_attempts"]} / {r["actual_generation_calls"]} | '
            f'{r["residual_flags"]} | {r["stored_extra_latency_s_per_input"]:.3f} | '
            f'{r["stored_extra_latency_s_flagged_median"]:.3f} | {r["check_ms_median"]:.2f} |')
    L+=['\nLatency is the sum of per-call generation service times, not total elapsed wall time; concurrent calls overlap. '
        'Stored latency includes the original cost of cached retry responses; actual HTTP duration and cache counts are separate '
        'in headline.json and actual_calls.csv. First-pass historical latency is excluded. G1s uses zero model calls. '
        'Hardware-specific latency is not an AAC deployment prediction.\n',
        '## Declared-rule examples (selected, not typical)\n',
        'Each row below is the first SHA256([base_request_key, family, variant, channel]) in its pre-frozen event category. '
        'Exact output/input strings are joined to stored run outputs; category rates accompany them. No quality-based filtering.\n']
    examples=[]
    for label,arm in [('strict fail→pass','G1'),('residual strict failure','G1'),('correct-text-changed','G1'),
                       ('pass→fail','G1'),('G1s strict fail→pass','G1s')]:
        p=pairs[arm]
        if 'fail→pass' in label:
            eligible=p.strict_P0.eq(0)&p.strict_arm.notna();event=p.strict_P0.eq(0)&p.strict_arm.eq(1)
        elif label=='residual strict failure':eligible=p.strict_arm.notna();event=p.strict_arm.eq(0)
        elif label=='correct-text-changed':eligible=p.strict_P0.eq(1);event=eligible&p.changed_arm
        else:eligible=p.strict_P0.eq(1)&p.strict_arm.notna();event=p.strict_P0.eq(1)&p.strict_arm.eq(0)
        cand=p[event].copy();rate=f'{int(event.sum())}/{int(eligible.sum())}'
        if not len(cand):L.append(f'- **{label}**: absent ({rate}).');continue
        cand['example_sha256']=[hashlib.sha256(json.dumps([r.base_key_P0,r.family_id,r.variant,r.channel],ensure_ascii=False).encode()).hexdigest() for r in cand.itertuples()]
        r=cand.sort_values('example_sha256').iloc[0]
        # Check exact membership of both quotations in stored outputs, including baseline.
        ex=dict(category=label,arm=arm,model=r.model,family_id=r.family_id,variant=r.variant,channel=r.channel,
            input_text=r.input_text_P0,before=r.text_P0,after=r.text_arm,before_output_id=r.output_id_P0,
            after_output_id=r.output_id_arm,selection_sha256=r.example_sha256,event_k=int(event.sum()),eligible_n=int(eligible.sum()))
        examples.append(ex)
        L.append(f'- **{label}** ({rate} target occurrences), {r.model}, {r.family_id}/{r.variant}, {r.channel}. '
            f'Input: `{r.input_text_P0}`. P0: {json.dumps(r.text_P0,ensure_ascii=False)} → {arm}: '
            f'{json.dumps(r.text_arm,ensure_ascii=False)}. IDs `{r.output_id_P0}` → `{r.output_id_arm}`.')
    write('examples.json',examples)
    L+=['\n## Audit and reproducibility\n',
        'audit_sample.csv applies the pre-frozen text-hash selection to 20 distinct changed G1 texts and 20 unchanged '
        'baseline-correct controls (all eligible counts and memberships in audit_manifest.json). HUMAN fields are empty; '
        'selection is deterministic, not a probability sample, and no representative usable-repair percentage follows. '
        'No human time was allocated or consumed by this run.\n',
        'Reproduce locally: `OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/guard_wc/analyze.py --exit-code 0`. '
        'Do not rerun prepare.py or launch to manufacture a retrospective freeze. Frozen inputs and wrapper code hashes '
        'are recorded before launch; final output hashes are in result_hashes.json. paired_G1/G1s.parquet retain '
        'all target transitions; scored.parquet retains all three arms; residual flags and attempt traces are in '
        'runs/guard_wc/generations.jsonl. Resource records include every HTTP attempt without secrets.\n']
    write('headline.json',head)
    (OUT/'report.md').write_text('\n'.join(L)+'\n')
    outputs=['headline.json','report.md','scored.parquet','paired_G1.parquet','paired_G1s.parquet',
             'stratified_effects.csv','examples.json','actual_calls.csv','audit_sample.csv','audit_manifest.json']
    write('result_hashes.json',{p:sha(OUT/p) for p in outputs})
    print(verdict,flush=True)
    print(json.dumps(clean(dict(arms=arms,paired=comparisons,criteria=criteria,cost=c)),indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--exit-code',type=int,default=0);a=ap.parse_args();main(a.exit_code)
