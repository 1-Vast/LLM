import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
from pathlib import Path
import numpy as np, pandas as pd, ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_eval as E, eval_R as R
P=T.Prep(); dr=X.Direct(P)
run=Path('D:/MAESTRO/research/dual_core_innovation_validation_20261021/RUN/dev')
sc=R.direct_scores(P,dr,'dev',None)
for v,n in R.NAMES.items():
    pr=E.load_preds(run,'dev',v,0)
    if pr.empty: continue
    pr=pr[pr.single].rename(columns={'p':n})[['cell','perts',n]]
    sc=sc.merge(pr,on=['cell','perts'],how='left')
ex,hold,train=R.stage_inputs(P,'dev')
cols=[c for c in ['b0','b1','m0_lr','m0_hgb','M1','M2','M3'] if c in sc]
sc=sc[sc.y.notna()]
dt=R.decision_table(sc.dropna(subset=[c for c in cols if c in ('M1','M2','M3')]) if False else sc,train,cols)
pd.set_option('display.width',200)
print(dt.groupby('score')[['auroc_all','auroc_pool','prec_at_k_pool','brier_pool','brier_all']].mean().round(3).to_string())
print(dt.pivot(index='cell',columns='score',values='prec_at_k_pool').round(2).to_string())
sc.to_pickle('D:/MAESTRO/tmp/dev_scores.pkl')
