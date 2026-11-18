import sys,json;sys.path.insert(0,'src')
import numpy as np,pandas as pd
import score_coverage as S
from pathlib import Path
B=10000
key=S.load_key()
sv,r1=S.qc(S.read_returns(Path('annotation/returns_part26'),'part26'),key,'sv',['send','hard'])
pl,r2=S.qc(S.read_returns(Path('annotation/returns_part27'),'part27'),key,'pool',['ver','acc'])
a=S.analyse(key,sv,pl,B,None); IA,P,SV,ARM=a['IA'],a['P'],a['SV'],a['ARM']
out={}
print('ver x acc'); print(pd.crosstab(P.ver,P.acc))
# drafts rated other / else per origin and cond
P['origin']=P.pool_arms.str.split().str[0].str.split(':').str[0]
print(pd.crosstab([P.cond,P.origin],P.ver,normalize='index').round(3))
print(pd.crosstab([P.cond,P.origin],P.ver))
# per-arm rate of drafts rated other (all shown drafts of that arm)
rows=[]
for cond in('bare','chip'):
  for arm in S.ARMS+['D3pU']:
    ds=P[(P.cond==cond)&P.pool_arms.str.contains(rf'(^| ){arm}:')]
    if len(ds): rows.append(dict(cond=cond,arm=arm,drafts=len(ds),other=(ds.ver=='other').mean(),meant=(ds.ver=='meant').mean(),acc_no_given_meant=(ds[ds.ver=='meant'].acc=='no').mean()))
OT=pd.DataFrame(rows);print(OT.round(3))
# direct contrasts, unpaired
def dcon(a_,ca,b_,cb):
  x=SV[(SV.arm==a_)&(SV.cond==ca)];y=SV[(SV.arm==b_)&(SV.cond==cb)]
  return S.cluster_boot2(S.by_writer(x,'direct_cov'),S.by_writer(y,'direct_cov'),B)
dc=[]
for n,args in {'C3-D3p bare':('C3','bare','D3p','bare'),'E3-D3p bare':('E3','bare','D3p','bare'),'C3bare-G1chip':('C3','bare','G1','chip'),'E3bare-G1chip':('E3','bare','G1','chip'),'E3-G1 chip':('E3','chip','G1','chip'),'C3-G1 chip':('C3','chip','G1','chip'),'D3p-G1 chip':('D3p','chip','G1','chip'),'cue tap':('G1','chip','G1','bare')}.items():
  e,l,h=dcon(*args);dc.append(dict(name=n,diff_pp=100*e,lo=100*l,hi=100*h))
DC=pd.DataFrame(dc);print(DC.round(1))
# direct arm rates with CI
dr=[]
for (c,ar),g in SV.groupby(['cond','arm']):
  e,l,h=S.cluster_boot(S.by_writer(g,'direct_cov'),B);dr.append(dict(cond=c,arm=ar,n=len(g),direct_cov=e,lo=l,hi=h))
DR=pd.DataFrame(dr);print(DR.round(3))
# cost per covered with writer cluster CI, and diff vs G1 chip
def cpc(g,r,fb):
  c=S.cost(g,r,fallback=fb);return c,(g.h_cov==1).astype(float)
def boot_cpc(g,r,fb,Bn=2000,seed=S.SEED):
  c,h=cpc(g,r,fb);g=g.assign(c=c.values,h=h.values);ws=sorted(g.writer.unique());rng=np.random.default_rng(seed)
  grp={w:g[g.writer==w][['c','h']].to_numpy() for w in ws};out=[]
  for _ in range(Bn):
    m=np.vstack([grp[ws[i]] for i in rng.integers(0,len(ws),len(ws))]);out.append(m[:,0].sum()/max(1,m[:,1].sum()))
  return c.sum()/max(1,h.sum()),np.percentile(out,2.5),np.percentile(out,97.5)
cr=[]
for cond in('bare','chip'):
  for arm in S.ARMS+(['D3pU'] if cond=='chip' else []):
    g=IA[(IA.cond==cond)&(IA.arm==arm)]
    for r in(0.5,1.0):
      for fb in(True,False):
        e,l,h=boot_cpc(g,r,fb);cr.append(dict(cond=cond,arm=arm,r=r,fallback=fb,cpc=e,lo=l,hi=h))
CR=pd.DataFrame(cr);print(CR[(CR.r==0.5)].round(1).to_string())
# breakeven r*: r at which arm cpc == G1 chip cpc (no fallback and with)
be=[]
for fb in(True,False):
  g1=IA[(IA.cond=='chip')&(IA.arm=='G1')]
  for cond in('bare','chip'):
    for arm in ('D3p','C3','E3'):
      g=IA[(IA.cond==cond)&(IA.arm==arm)];rs=np.linspace(0.01,4,400);d=[cpc_ for cpc_ in []]
      f=lambda gg,r:S.cost(gg,r,fallback=fb).sum()/max(1,(gg.h_cov==1).sum())
      diff=np.array([f(g,r)-f(g1,r) for r in rs]);cross=rs[np.where(diff>0)[0][0]] if (diff>0).any() and (diff<=0).any() else None
      be.append(dict(fallback=fb,cond=cond,arm=arm,diff_at_r0=diff[0],diff_at_r4=diff[-1],breakeven_r=cross))
BE=pd.DataFrame(be);print(BE.round(2))
# sensitivities for primary contrasts: exclude short sets; strict
sens=[]
kk=key[key.kind=='sv'];short=set(kk[kk.n_shown.astype(int)<kk.k.astype(int)].cv_item)
print('short sets items',short)
IA2=IA[~IA.cv_item.isin(short)]
def pc(ia,a_,b_,cond,col):
  v=S.paired(ia,a_,b_,cond,col);return S.cluster_boot(v,B)
for lab,ia,col in(('all','IA','h_cov'),('strict_as_is','IA','h_strict'),('excl_short','IA2','h_cov')):
  d=IA if ia=='IA' else IA2
  for n,(x,y,c) in {'S1_C3':('C3','D3p','bare'),'S1_E3':('E3','D3p','bare'),'S3_E3':('E3','G1','chip'),'S3x_C3':('C3','G1','chip'),'S3x_D3p':('D3p','G1','chip')}.items():
    e,l,h=pc(d,x,y,c,col);sens.append(dict(variant=lab,name=n,diff_pp=100*e,lo=100*l,hi=100*h))
SE=pd.DataFrame(sens);print(SE.round(1).to_string())
# Coverage ceiling: share of items where ANY draft of any arm in pool is covering
anyc=P.groupby(['cv_item','cond']).h_cov.max().reset_index();print('ceiling any draft',anyc.groupby('cond').h_cov.agg(['mean','size']))
# by dimension direction
d=IA.groupby(['dimension','cond','arm']).h_cov.mean().unstack('arm').round(2);print(d)
# per writer G1chip, E3chip heterogeneity: share of writers where E3>G1 in chip
w=IA[(IA.cond=='chip')].groupby(['writer','arm']).h_cov.mean().unstack();print('writers chip E3>G1',(w.E3>w.G1).sum(),'tie',(w.E3==w.G1).sum(),'< ',(w.E3<w.G1).sum(), 'D3p>G1',(w.D3p>w.G1).sum(),(w.D3p==w.G1).sum(),(w.D3p<w.G1).sum())
w=IA[(IA.cond=='bare')].groupby(['writer','arm']).h_cov.mean().unstack();print('bare E3>D3p',(w.E3>w.D3p).sum(),(w.E3==w.D3p).sum(),(w.E3<w.D3p).sum())
# proxy concordance incl by-origin AUROC, 8 cell spearman
pr=P[P.rated&(P.proxy_intended.astype(str)!='')];x=pr.proxy_intended.astype(int).to_numpy();y=pr.h_match.to_numpy()
print('ALL kappa',S.kappa(x,y),'auroc',S.auroc(x,y))
by={}
for o,g in pr.groupby('origin'):
  by[o]=dict(n=len(g),kappa=S.kappa(g.proxy_intended.astype(int),g.h_match),auroc=S.auroc(g.proxy_intended.astype(int),g.h_match),proxy=g.proxy_intended.astype(int).mean(),human=g.h_match.mean())
print(pd.DataFrame(by).T.round(3))
A8=ARM[ARM.arm!='D3pU'];print('spearman8',S.spearman(A8.proxy_cov.to_numpy(),A8.h_cov.to_numpy()))
# set-level agreement proxy_cov vs h_cov
print('set-level agree',(IA.proxy_cov==IA.h_cov).mean(),'proxy=1,h=0',((IA.proxy_cov==1)&(IA.h_cov==0)).mean(),'proxy0 h1',((IA.proxy_cov==0)&(IA.h_cov==1)).mean())
# writers' base rates: writers with zero ever covered
wc=IA.groupby('writer').h_cov.mean();print(wc.describe())
# part 18 overlap
print('seen_in_part18 col' , [c for c in key.columns])
for n,df in dict(DC=DC,DR=DR,OT=OT,CR=CR,BE=BE,SE=SE).items(): df.to_csv(f'tmp/{n}.csv',index=False)
# cue effect by dimension on G1
