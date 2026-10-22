import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_tasks as T, ptv_direct as X, eval_R as R
P=T.Prep(); dr=X.Direct(P)
sc=R.direct_scores(P,dr,'sel',None); ex,hold,train=R.stage_inputs(P,'sel'); sc=sc[sc.y.notna()]
dt=R.decision_table(sc,train,['b0','b1','m0_lr','m0_hgb'])
pd.set_option('display.width',200)
print(dt.groupby('score')[['auroc_all','auroc_pool','auprc_pool','prec_at_k_pool','brier_pool','pool_n']].mean().round(3).to_string())
print(dt.pivot(index='cell',columns='score',values='prec_at_k_pool').round(2).to_string())
sc.to_pickle('D:/MAESTRO/tmp/sel_scores.pkl')
