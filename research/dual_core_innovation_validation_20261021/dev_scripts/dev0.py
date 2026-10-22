import sys; sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, pandas as pd, ptv_data as d
from sklearn.linear_model import LogisticRegression
r=d.Release(); ex=r.experiments(1); ex=ex[(ex.part=='dev')&ex.y.notna()].reset_index(drop=True)
print(len(ex), ex.groupby('cell').y.agg(['size','mean']))
M=ex.pivot(index='perts',columns='cell',values='y'); print(M.shape, M.notna().sum().tolist())
# drug effect consistency: fraction of variance explained by drug main effect (LOBO)
cells=list(M.columns); P5=[]; base=[]
for c in cells:
    tr=M.drop(columns=c); pr=tr.mean(axis=1)           # LOBO drug prior
    te=M[c].dropna(); pr=pr.reindex(te.index).fillna(tr.values[~np.isnan(tr.values)].mean())
    top=pr.sort_values(ascending=False).index[:5]
    P5.append(te[top].mean()); base.append(te.mean())
    print(c, 'prec@5 drugprior', te[top].mean(), 'prevalence', te.mean(), 'n_pos', int(te.sum()))
print('mean prec@5',np.mean(P5),'prevalence',np.mean(base))
# oracle ceiling for k=5
print('oracle', [min(1,M[c].dropna().sum()/5) for c in cells])
# between-background agreement on each drug: how many drugs have mixed labels
mix=((M.mean(axis=1)>0)&(M.mean(axis=1)<1)).mean(); print('drugs with mixed labels across 5 bg:',mix)
# AUROC of drug prior LOBO
from sklearn.metrics import roc_auc_score
aucs=[]
for c in cells:
    tr=M.drop(columns=c); te=M[c].dropna(); pr=tr.mean(axis=1).reindex(te.index)
    m=pr.notna(); aucs.append(roc_auc_score(te[m],pr[m]))
print('AUROC drug prior LOBO',np.round(aucs,3),np.mean(aucs))
