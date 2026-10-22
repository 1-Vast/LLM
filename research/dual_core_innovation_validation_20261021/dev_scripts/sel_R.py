import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
from pathlib import Path
import numpy as np, pandas as pd, ptv_tasks as T, ptv_eval as E, eval_R as R
from sklearn.metrics import roc_auc_score
P=T.Prep(); sc=pd.read_pickle('D:/MAESTRO/tmp/sel_scores.pkl'); run=Path('D:/MAESTRO/research/dual_core_innovation_validation_20261021/RUN/sel')
ex,hold,train=R.stage_inputs(P,'sel')
rows=[]
for v,n in R.NAMES.items():
    for ep in (15,30,45):
        parts=[]
        for f in sorted(run.glob(f'sel_*_{v}_s0.npz')):
            z=np.load(f,allow_pickle=True)
            parts.append(pd.DataFrame({'cell':z['cell'],'perts':z['perts'],'y':z['lab'],'single':z['single'],'p':z[f'p_e{ep}']}))
        pr=pd.concat(parts); pr=pr[pr.single]
        m=sc.merge(pr[['cell','perts','p']].rename(columns={'p':'w'}),on=['cell','perts'],how='left')
        dt=R.decision_table(m,train,['w'])
        bce=-np.mean(m.y*np.log(m.w.clip(1e-4,1-1e-4))+(1-m.y)*np.log(1-m.w.clip(1e-4,1-1e-4)))
        rows.append(dict(model=n,epoch=ep,bce_all=bce,auroc_all=dt.auroc_all.mean(),auroc_pool=dt.auroc_pool.mean(),prec5=dt.prec_at_k_pool.mean(),brier_pool=dt.brier_pool.mean()))
print(pd.DataFrame(rows).round(3).to_string())
