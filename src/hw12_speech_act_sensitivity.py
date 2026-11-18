"""hw1+hw2 speech-act chip gain (P1) sensitivity: splits, Can-you / I-want-please recodes. Writes analysis/hw12/speech_act_sensitivity.json. Run: python src/hw12_speech_act_sensitivity.py"""
import sys, json, re
sys.path.insert(0,'src')
import numpy as np, pandas as pd
import robust_t6_small_cluster as T, analyze_hw1 as H1
import robust_t4_codebook as T4
items, raw = T.load(['data/items/hw.jsonl','data/items/hw2.jsonl'],['runs/hw1','runs/hw2'])
print(raw.columns.tolist())
def p1(raw, keepfam=None, recode=None):
    r = raw.copy()
    if recode:
        txt = r['text'] if 'text' in r else None
        isreq = r.critical.eq('request/command') & r.dimension.eq('speech_act')
        if recode=='can':
            m = isreq & txt.map(lambda t: bool(T4.CAN_YOU.search(t))); r.loc[m,'critical']='question'
        if recode=='want':
            m = isreq & txt.map(lambda t: bool(T4.WANT_PLEASE.search(t))); r.loc[m,'critical']='statement'
        if recode=='both':
            m = isreq & txt.map(lambda t: bool(T4.CAN_YOU.search(t)) or bool(T4.WANT_PLEASE.search(t))); r.loc[m,'critical']=np.where(txt[m].map(lambda t: bool(T4.CAN_YOU.search(t))),'question','statement')
    its = items if keepfam is None else {f:i for f,i in items.items() if f in keepfam}
    d,_ = H1.build(its, r)
    p0=d[d.prompt_id.eq("P0")]
    a=p0[p0.dimension.eq("speech_act")].pivot(index=["family_id","writer_id","variant","model"],columns="channel",values="critical_match").reset_index()
    a["value"]=pd.to_numeric(a.chip1).astype(float)-pd.to_numeric(a.noncrit).astype(float)
    g = T.agg(a); est,se,_ = T.ratio(g); lo,hi,p = T.tci(est,se,len(g))
    return dict(writers=len(g), rows=int(g.n.sum()), est=round(100*est,1), lo=round(100*lo,1), hi=round(100*hi,1)), a
hw1=set(f for f in items if not f.startswith('hw2-')); hw2=set(items)-hw1
out={}
for name,fam in [('hw12',None),('hw1',hw1),('hw2',hw2)]:
    out[name],a = p1(raw,fam)
    if name=='hw2':
        c1=a.chip1.astype(float); nc=a.noncrit.astype(float)
        out['hw2_chip1_rate']=round(100*c1.mean(),1); out['hw2_noncrit_rate']=round(100*nc.mean(),1)
        out['hw2_by_model']={}
    if name=='hw12':
        out['hw12_chip1_rate']=round(100*a.chip1.astype(float).mean(),1); out['hw12_noncrit_rate']=round(100*a.noncrit.astype(float).mean(),1)
for rc in ('can','want','both'):
    out['hw12_recode_'+rc],_ = p1(raw,None,rc)
    out['hw2_recode_'+rc],_ = p1(raw,hw2,rc)
# hw2 only: per-model mean and writer means
_,a=p1(raw,hw2)
out['hw2_model_gain']={m:round(100*g.value.mean(),1) for m,g in a.groupby('model')}
out['hw2_writer_gain']={m:round(100*g.value.mean(),1) for m,g in a.groupby('writer_id')}
_,a=p1(raw,None)
out['hw12_family_neg_share']=round(100*(a.groupby('family_id').value.mean()<=0).mean(),1)
out['hw12_n_families']=int(a.family_id.nunique())
out['hw12_families_gain_le0']=int((a.groupby('family_id').value.mean()<=0).sum())
# "Can you" / want-please counts among hw2 request outputs
r2=raw[raw.family_id.isin(hw2)&raw.dimension.eq('speech_act')]
req=r2[r2.critical.eq('request/command')]
out['hw2_request_outputs']=len(req); out['hw2_can_you']=int(req.text.map(lambda t:bool(T4.CAN_YOU.search(t))).sum()); out['hw2_want_please']=int(req.text.map(lambda t:bool(T4.WANT_PLEASE.search(t))).sum())
print(json.dumps(out,indent=1)); json.dump(out,open('analysis/hw12/speech_act_sensitivity.json','w'),indent=1)
