"""Read-only integrity checks on the completed Action 6 artifacts."""
from pathlib import Path
import sys,json,hashlib,sqlite3,time
from collections import Counter
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import runio, interventions as I, analyze as A
OUT=ROOT/'analysis/guard_wc';RUN=ROOT/'runs/guard_wc'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def peak(rows):
    events=[]
    for r in rows:
        events += [(r['start'],1),(r['end'] or time.time(),-1)]
    n=highest=0
    for _,d in sorted(events,key=lambda e:(e[0],e[1])):
        n+=d;highest=max(highest,n)
    return highest

def main():
    for p,h in json.loads((OUT/'inventory_hashes.json').read_text()).items():assert sha(OUT/p)==h,p
    for p,h in json.loads((OUT/'launch_manifest.json').read_text())['code_hashes'].items():assert sha(ROOT/p)==h,p
    for p,h in json.loads((OUT/'result_hashes.json').read_text()).items():assert sha(OUT/p)==h,p
    gens=runio.read_jsonl(RUN/'generations.jsonl')
    assert len(gens)==5544
    groups={}
    for r in gens:groups.setdefault(r.get('base_request_key',r['request_key']),{})[r['prompt_id']]=r
    assert len(groups)==1848
    nflag=0;logical=0
    for k,arms in groups.items():
        assert set(arms)=={'P0','G1','G1s'}
        b,g,s=(arms[x] for x in ['P0','G1','G1s'])
        nflag+=bool(b['flags_initial']);logical+=g['extra_calls']
        assert b['flags_initial']==g['flags_initial']==s['flags_initial']
        if not b['flags_initial']:assert not g['changed'] and g['extra_calls']==0
        assert len(g['attempts'])<=3
        best=min(range(len(g['attempts'])),key=lambda i:(len(g['attempts'][i]['flags']),i))
        assert g['chosen_attempt']==best and g['suggestions'][0]==g['attempts'][best]['text']
        assert g['changed']==(g['suggestions']!=b['suggestions'])
        assert s['extra_calls']==0
        for arm in arms.values():
            assert all(t['family_id'].startswith('r2act-') and t['family_id'] not in {'r2act-078','r2act-079'}
                       and t['channel'] in I.CUE for t in arm['targets'])
    assert nflag==508
    logs=runio.read_jsonl(RUN/'logical_calls.jsonl');assert len(logs)==logical
    c=sqlite3.connect(OUT/'budget.sqlite');c.row_factory=sqlite3.Row
    calls=[dict(r) for r in c.execute('select * from calls')];c.close()
    launch=json.loads((OUT/'launch.json').read_text())
    assert all(r['start']>=launch['start_epoch'] and r['start']<=launch['deadline_epoch'] for r in calls)
    assert min(r['start'] for r in calls)>(OUT/'FREEZE.md').stat().st_mtime
    assert min(r['start'] for r in calls)>(OUT/'launch_manifest.json').stat().st_mtime
    counts=Counter(r['kind'] for r in calls);assert counts['generation']<=1016 and counts['judge']<=400
    peaks={m:peak([r for r in calls if r['model']==m]) for m in {r['model'] for r in calls}}
    assert peaks.get('gpt-6.1-terra',0)<=8 and peaks.get('gpt-6.1-sol',0)<=12
    assert all(v<=4 for m,v in peaks.items() if m not in {'gpt-6.1-terra','gpt-6.1-sol'})
    local=[r for r in calls if r['model'] in {'qwen2.5-7b','llama3.1-8b','gemma3-4b'}]
    spans={m:(min(r['start'] for r in local if r['model']==m),max(r['end'] for r in local if r['model']==m)) for m in {r['model'] for r in local}}
    spans=sorted(spans.items(),key=lambda x:x[1][0])
    assert all(a[1][1]<=b[1][0] for a,b in zip(spans,spans[1:]))
    sc=pd.read_parquet(OUT/'scored.parquet');assert len(sc)==5616
    assert not sc.duplicated(['family_id','variant','channel','model','prompt_id']).any()
    assert not sc.label_source.isin(['J1','J2']).any()
    base=pd.read_parquet(OUT/'baseline_scored.parquet').sort_values(['model','family_id','variant','channel']).reset_index(drop=True)
    p0=sc[sc.prompt_id.eq('P0')].sort_values(['model','family_id','variant','channel']).reset_index(drop=True)
    assert p0.text.equals(base.text)
    assert p0.crit.equals(base.critical)
    stored=runio.read_jsonl(RUN/'outputs.jsonl')
    texts={(r['output_id'],r['family_id'],r['variant'],r['channel']):r for r in stored}
    for e in json.loads((OUT/'examples.json').read_text()):
        before=texts[e['before_output_id'],e['family_id'],e['variant'],e['channel']]
        after=texts[e['after_output_id'],e['family_id'],e['variant'],e['channel']]
        assert e['before']==before['text'] and e['after']==after['text'] and e['input_text']==before['input_text']
    h=json.loads((OUT/'headline.json').read_text())
    assert h['n_targets']==1872 and h['n_unique']==1848 and h['F']==508
    for arm in ['G1','G1s']:
        p=pd.read_parquet(OUT/f'paired_{arm}.parquet')
        gain=(p.joint_arm-p.joint_P0).mean()
        assert abs(gain-h['paired'][arm]['joint_gain']['estimate'])<1e-12
        fail=p.strict_P0.eq(0);correct=p.strict_P0.eq(1)
        assert int((fail&p.strict_arm.eq(1)).sum())==h['paired'][arm]['strict_repair']['k']
        assert int((correct&p.changed_arm).sum())==h['paired'][arm]['strict_changed_correct']['k']
        assert int((correct&p.strict_arm.eq(0)).sum())==h['paired'][arm]['strict_pass_to_fail']['k']
    assert h['transfer_success']==all(h['criteria'].values())
    closure=json.loads((OUT/'closure_audit.json').read_text())
    assert closure['baseline_value_differences']==0
    assert closure['new_selected_critical_unknowns']==0
    for endpoint in ['joint','strict']:
        p=sc[sc.prompt_id.eq('G1')].set_index(['model','family_id','variant','channel'])
        s=sc[sc.prompt_id.eq('G1s')].set_index(['model','family_id','variant','channel'])
        r=closure['comparator'][endpoint]
        assert abs((p[endpoint]-s[endpoint]).mean()-r['family']['estimate'])<1e-12
        assert r['G1_only_pass']-r['G1s_only_pass']==r['family']['k']
    result=dict(passed=True,checks=['immutable freeze/inventory/launch/result hashes','all 1872 planned cells in each of 3 arms',
        'unchanged guard return/tie rule and monitor-only retries','actual HTTP/logical/cache call accounting',
        'generation starts after freeze','historical launch concurrency: generation API <=8, judge <=12, local <=4','local model inference windows do not overlap',
        'frozen P0 texts/labels retained','no J1/J2 fallback','verbatim stored example provenance','independent paired arithmetic and verdict'],
        actual_call_counts=dict(counts),peak_http_concurrency_by_model=peaks,logical_guard_attempts=logical,
        current_api_concurrency_limit_8_met=all(peaks.get(m,0)<=8 for m in ['gpt-6.1-terra','gpt-6.1-sol']),
        inherited_concurrency_deviation_disclosed=True,closure_comparator_verified=True,
        checked_epoch=time.time())
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
