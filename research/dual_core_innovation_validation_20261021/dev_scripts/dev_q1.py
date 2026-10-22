import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_eval as E, ptv_episodes as EP
from sklearn.metrics import roc_auc_score
P=T.Prep(); ex=P.R.experiments(1); dev=ex[(ex.part=='dev')&ex.y.notna()].reset_index(drop=True); dr=X.Direct(P)
rows=[]
for c in sorted(dev.cell.unique()):
    tr=dev[dev.cell!=c]; te=dev[dev.cell==c]
    tool=EP.MolTool(P,dr,tr)
    pool=T.contested_pool(tr,list(te.perts)); te=te.set_index('perts')
    m0=dr.fit_predict(tr,te.reset_index().assign(single=True),'hgb'); m0=pd.Series(m0,index=te.index)
    ms={d:tool.score(tr,c,d)[0] for d in pool}
    ms=pd.Series(ms); y=te.y[pool]
    rows.append(dict(cell=c,auc_m0=roc_auc_score(y,m0[pool]),auc_mol=roc_auc_score(y,ms[pool]),
        p5_m0=T.precision_at_k(m0[pool],y),p5_mol=T.precision_at_k(ms[pool],y), auc_all_m0=roc_auc_score(te.y,m0),))
r=pd.DataFrame(rows); print(r.round(3).to_string()); print(r.mean(numeric_only=True).round(3))
