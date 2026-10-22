import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_eval as E
P=T.Prep(); ex=P.R.experiments(1); dev=ex[(ex.part=='dev')&ex.y.notna()].reset_index(drop=True)
dr=X.Direct(P)
res=[]
for c in sorted(dev.cell.unique()):
    tr=dev[dev.cell!=c]; te=dev[dev.cell==c].copy()
    te['single']=True
    for kind in ['lr','hgb']:
        te['m0_'+kind]=dr.fit_predict(tr,te,kind)
    te['b0']=[dr.priors(tr,c,d)[0] for d in te.perts]; te['b1']=[dr.priors(tr,c,d)[1] for d in te.perts]
    te[['b0','b1']]=te[['b0','b1']].fillna(float(tr.y.mean()))
    for sc in ['b0','b1','m0_lr','m0_hgb']:
        m=E.background_metrics(te,tr,score=sc); m.update(cell=c,score=sc); res.append(m)
r=pd.DataFrame(res); pd.set_option('display.width',200)
pd.set_option("display.max_columns",20); print(r.groupby("score")[["auroc_all","auroc_pool","prec_at_k_pool","oracle_prec_pool","pool_prevalence","brier_pool"]].mean().round(3).to_string())
print(r[r.score=='b0'][['cell','pool_n','prec_at_k_pool','pool_prevalence']])
