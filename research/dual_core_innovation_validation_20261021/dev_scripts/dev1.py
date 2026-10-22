import sys; sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_data as d
r=d.Release(); ex=r.experiments(1); ex=ex[(ex.part=='dev')&ex.y.notna()]
M=ex.pivot(index='perts',columns='cell',values='y'); cells=list(M.columns)
for lo,hi in [(0.2,0.8),(0.1,0.9),(0.0,1.0)]:
  for k in (3,5,8):
    res=[]
    for c in cells:
        tr=M.drop(columns=c); pr=tr.mean(axis=1); te=M[c].dropna()
        pool=[x for x in te.index if pr[x]>=lo and pr[x]<=hi] if (lo,hi)!=(0.0,1.0) else list(te.index)
        if len(pool)<k+1: continue
        t=te[pool]; p=pr[pool]
        top=p.sort_values(ascending=False,kind='stable').index[:k]
        res.append((t[top].mean(), t.mean(), min(1,t.sum()/k), len(pool)))
    a=np.array(res); print(lo,hi,'k',k,'prior',a[:,0].mean().round(3),'random',a[:,1].mean().round(3),'oracle',a[:,2].mean().round(3),'pool',a[:,3].mean())
# pairs in dev: label counts and relation to single labels
pe=r.experiments(2); pe=pe[(pe.part=='dev')&pe.y.notna()]
print('dev pair exps',len(pe),'pos',int(pe.y.sum()))
print(pe[pe.y>0][['cell','perts']])
