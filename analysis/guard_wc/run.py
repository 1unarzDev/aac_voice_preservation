"""Action-6 adapter. Calls the unchanged frozen guard and judge implementations."""
from pathlib import Path
import sys, os, json, time, hashlib, sqlite3, asyncio, argparse, math, subprocess
from collections import Counter
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
import runio, interventions as I, models as M, judge as J
import httpx

OUT = ROOT/'analysis/guard_wc'
RUN = ROOT/'runs/guard_wc'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(name): return json.loads((OUT/name).read_text())
def append(path,row):
    with Path(path).open('a') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n')

def verify():
    for name,h in read('inventory_hashes.json').items():
        assert sha(OUT/name)==h, f'Frozen inventory changed: {name}'
    hashes=read('input_hashes.json')
    # Only the entry-point shell gains an Action-6 route; the frozen policy modules do not change.
    for name,h in hashes.items():
        if name.startswith(('src/','prompts/')) and name!='src/run_interventions.sh':
            assert sha(ROOT/name)==h, f'Frozen policy/code changed: {name}'
    if (OUT/'launch_manifest.json').exists():
        for name,h in read('launch_manifest.json')['code_hashes'].items():
            assert sha(ROOT/name)==h, f'Launch implementation changed: {name}'

def db():
    c=sqlite3.connect(OUT/'budget.sqlite', timeout=30)
    c.execute('CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, kind TEXT, model TEXT, start REAL, end REAL, status INTEGER)')
    return c

def reserve(kind,model):
    launch=read('launch.json')
    if time.time()>=launch['deadline_epoch']: raise RuntimeError('Action 6 wall-clock budget exhausted')
    c=db()
    try:
        c.execute('BEGIN IMMEDIATE')
        n=c.execute('SELECT COUNT(*) FROM calls WHERE kind=?',(kind,)).fetchone()[0]
        cap=2000 if kind=='generation' else 400
        if kind=='generation': cap=min(cap,read('admission.json')['max_guard_calls'])
        if n>=cap: raise RuntimeError(f'Action 6 {kind} call cap exhausted')
        cur=c.execute('INSERT INTO calls(kind,model,start) VALUES (?,?,?)',(kind,model,time.time()))
        c.commit()
        return cur.lastrowid
    finally: c.close()

def events(kind):
    async def request(req):
        body=json.loads(req.content)
        req.extensions['guard_wc_id']=reserve(kind,body.get('model','unknown'))
    async def response(resp):
        c=db()
        c.execute('UPDATE calls SET end=?,status=? WHERE id=?',
                  (time.time(),resp.status_code,resp.request.extensions['guard_wc_id']))
        c.commit();c.close()
    return dict(request=[request],response=[response])

class Caller(I.Caller):
    def __init__(self): super().__init__(conc_local=4,conc_api=8,retries=1)
    async def chat(self,model,tag,messages,max_tokens=96):
        start=time.time()
        res=await super().chat(model,tag,messages,max_tokens)
        append(RUN/'logical_calls.jsonl',dict(model=model,key=res.get('key'),cached=res.get('cached',False),
               error=res.get('error'),start_epoch=start,end_epoch=time.time(),latency_s=res.get('latency_s')))
        return res

async def guard(model):
    verify()
    assert read('admission.json')['admitted']
    items=runio.load_items(OUT/'items.jsonl')
    gens=[g for g in runio.read_jsonl(OUT/'first_passes.jsonl') if g['model']==model]
    replay={r['request_key']:r for r in runio.read_jsonl(OUT/'monitor_replay.jsonl')}
    path=RUN/'parts'/f'guard_{model}.jsonl'
    existing=runio.read_jsonl(path) if path.exists() else []
    done={r.get('base_request_key',r['request_key']) for r in existing}
    assert len(existing)==3*len(done)
    caller=Caller()
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=16),event_hooks=events('generation')) as client:
        caller.client=client
        async def one(g):
            result=await I.guard_one(caller,g,items,2,{})
            assert result[0]['flags_initial']==replay[g['request_key']]['flags']
            for row in result: append(path,row)
        await asyncio.gather(*(one(g) for g in gens if g['request_key'] not in done))
    print(f'Completed {model}: {len(gens)} unique first passes',flush=True)

def assemble():
    rows=[]
    for p in sorted((RUN/'parts').glob('*.jsonl')): rows+=runio.read_jsonl(p)
    expected=read('admission.json')['n_unique']*3
    assert len(rows)==expected,(len(rows),expected)
    assert len({(r['request_key'],r['prompt_id']) for r in rows})==expected
    runio.write_jsonl(RUN/'generations.jsonl',rows)
    (RUN/'config.json').write_text(json.dumps(dict(run_id='guard_wc',items_path='analysis/guard_wc/items.jsonl',
        kind='Action 6 frozen guard transfer',freeze_sha256=sha(OUT/'FREEZE.md'),
        launch_manifest_sha256=sha(OUT/'launch_manifest.json'),n_rows=len(rows)),indent=2)+'\n')
    subprocess.run([sys.executable,'src/explode.py','--run',str(RUN)],cwd=ROOT,check=True)

def judge_plan():
    ju,au,bu=J.build_units(RUN,OUT/'items.jsonl')
    rows=[]
    for v in ['J1','J2']:
        cache=J.Cache(v)
        for pass_,units,key in [('A',au,J.key_a),('B',bu,J.key_b)]:
            missing=sum(not cache.get(key(v,J.JUDGE_MODEL,u)) for u in units.values())
            rows.append(dict(variant=v,pass_=pass_,total_units=len(units),uncached_units=missing,
                             initial_batch_calls=math.ceil(missing/25)))
        cache.fh.close()
    plan=dict(passes=rows,initial_batch_calls=sum(r['initial_batch_calls'] for r in rows),batch_size=25,
              judge_concurrency=12,cap=400)
    (OUT/'judge_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert plan['initial_batch_calls']<=400
    print(json.dumps(plan,indent=2),flush=True)

async def judge():
    verify();judge_plan()
    import openai
    original=openai.AsyncOpenAI
    # The request hook counts every HTTP attempt. SDK retries are disabled so hidden
    # retries cannot exceed the externally fixed budget.
    def budget_client(**kwargs):
        kwargs['max_retries']=0
        kwargs['http_client']=httpx.AsyncClient(event_hooks=events('judge'),
            limits=httpx.Limits(max_connections=12))
        return original(**kwargs)
    openai.AsyncOpenAI=budget_client
    J.CONCURRENCY=12
    J._SEM=None
    rows=await J.judge_run(RUN,OUT/'items.jsonl',J.JUDGE_MODEL,'low',['J1','J2'])
    (RUN/'judge_report.json').write_text(json.dumps(J.agreement_report(rows),indent=2)+'\n')
    # Reuse only actual pre-existing arbitration on the SAME production A-unit.
    frozen=OUT/'frozen/runs/r2c1'
    old={}
    for a in runio.read_jsonl(frozen/'arbiter.jsonl'):
        it=runio.load_items(OUT/'items.jsonl')[a['family_id']]
        k=(a['text_id'],it['dimension'],tuple(it['critical_options']))
        if k in old: assert old[k]['critical']==a['critical']
        old[k]=a
    arbs=[];unresolved=[]
    for r in rows:
        if r['J1_critical']!=r['J2_critical'] or r['critical'] is None:
            k=(r['text_id'],r['dimension'],tuple(r['critical_options']))
            if k in old:
                arbs.append(dict(text_id=r['text_id'],family_id=r['family_id'],input_text=r['input_text'],
                    text=r['text'],critical=old[k]['critical'],provenance='reused frozen r2c1 A-unit arbitration',
                    original=old[k]))
            else:
                unresolved.append({**r,'resolution':'unresolved; zero new arbiter calls; no J1 fallback'})
    runio.write_jsonl(RUN/'arbiter.jsonl',arbs)
    runio.write_jsonl(OUT/'unresolved.jsonl',unresolved)

def launch():
    verify()
    assert read('admission.json')['admitted']
    RUN.mkdir(exist_ok=True);(RUN/'parts').mkdir(exist_ok=True)
    assert not (OUT/'launch.json').exists(),'Already launched; preserve original clock.'
    code=['analysis/guard_wc/run.py','analysis/guard_wc/analyze.py','analysis/guard_wc/execute.sh','src/run_interventions.sh']
    manifest=dict(created_epoch=time.time(),code_hashes={p:sha(ROOT/p) for p in code},
                  inventory_hashes_sha256=sha(OUT/'inventory_hashes.json'))
    (OUT/'launch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    start=time.time()
    (OUT/'launch.json').write_text(json.dumps(dict(start_epoch=start,deadline_epoch=start+14400),indent=2)+'\n')
    c=db();c.close()
    print(f'Launch frozen at {start}; deadline {start+14400}',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('cmd',choices=['launch','verify','guard','assemble','judge']);ap.add_argument('--model')
    a=ap.parse_args()
    if a.cmd=='guard':asyncio.run(guard(a.model))
    elif a.cmd=='judge':asyncio.run(judge())
    else:globals()[a.cmd]()
