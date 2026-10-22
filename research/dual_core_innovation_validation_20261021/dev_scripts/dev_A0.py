import sys,warnings,re; warnings.filterwarnings('ignore'); sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_tasks as T, ptv_direct as X, ptv_episodes as EP, ptv_env as ENV, programs_a0 as P0, eval_R as R
if __name__=='__main__':
    P=T.Prep(); dr=X.Direct(P)
    sc=pd.read_pickle('D:/MAESTRO/tmp/dev_scores.pkl')
    out={}
    for wname,col in [('M0','m0_hgb'),('B0','b0'),('M1','M1')]:
        ws=sc[['cell','perts',col]].rename(columns={col:'w'}).dropna()
        eps=EP.build_episodes(P,dr,'dev',ws,with_mol=False)
        for kappa in [0.0,0.25,0.5,1.0,2.0]:
            src=P0.A0.replace('kappa = 0.5',f'kappa = {kappa}')
            ys=[ENV.run_program(src,e['kwargs'])['yield'] for e in eps]
            out[(wname,kappa)]=ys
        # static direct confirmation = top5 by score
        print(wname,'pools',[len(e['kwargs']['drugs']) for e in eps])
    for k,v in out.items(): print(k,v,np.mean(v).round(2))
