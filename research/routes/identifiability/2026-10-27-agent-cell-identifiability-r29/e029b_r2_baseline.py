# -*- coding: utf-8 -*-
"""E029b: the correct baseline for a constant predictor is R^2, not Spearman.
Recompute per-fold model R^2 vs constant R^2 (constant = training mean)."""
import json, hashlib
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT/"data"/"external"/"gdsc_combinations"/"jaaks2022_figshare"/"Original screen_All tissues_fitted data.csv"
OUT = ROOT/"research"/"2026-10-27-agent-cell-identifiability-r29"
METRIC="SYNERGY_DELTA_AUC"; LAMBDA=1.0; SEED=20261027; N_BOOT=1000

d = pd.read_csv(ORIG, low_memory=False, usecols=["CELL_LINE_NAME","Tissue","ANCHOR_NAME","LIBRARY_NAME",
     "ANCHOR_PATHWAY","LIBRARY_PATHWAY",METRIC,"Synergy"])
d[METRIC]=pd.to_numeric(d[METRIC],errors="coerce"); d=d[np.isfinite(d[METRIC])].copy()
for c in ("ANCHOR_PATHWAY","LIBRARY_PATHWAY","Tissue","ANCHOR_NAME","LIBRARY_NAME"):
    d[c]=d[c].astype(str).fillna("NA")
drugs=sorted(set(d.ANCHOR_NAME)|set(d.LIBRARY_NAME))
pa=sorted(d.ANCHOR_PATHWAY.unique()); pl=sorted(d.LIBRARY_PATHWAY.unique()); ti=sorted(d.Tissue.unique())
def design(f):
    X=np.zeros((len(f), len(pa)+len(pl)+len(ti)))
    for k,v in enumerate(pa): X[:,k]=(f.ANCHOR_PATHWAY==v).to_numpy(float)
    o=len(pa)
    for k,v in enumerate(pl): X[:,o+k]=(f.LIBRARY_PATHWAY==v).to_numpy(float)
    o2=o+len(pl)
    for k,v in enumerate(ti): X[:,o2+k]=(f.Tissue==v).to_numpy(float)
    return X
X=design(d); y=d[METRIC].to_numpy(float)
a=d.ANCHOR_NAME.to_numpy(); l=d.LIBRARY_NAME.to_numpy()
rows=[]
for drug in drugs:
    te=(a==drug)|(l==drug); tr=~te
    if te.sum()<50 or tr.sum()<200: continue
    Xtr,ytr=X[tr],y[tr]; mu,sd=Xtr.mean(0),Xtr.std(0); sd[sd==0]=1
    Xs=(Xtr-mu)/sd; Xte=(X[te]-mu)/sd
    w=np.linalg.solve(Xs.T@Xs+LAMBDA*np.eye(Xs.shape[1]), Xs.T@(ytr-ytr.mean()))
    pred=ytr.mean()+Xte@w
    yt=y[te]; const=np.full(len(yt), ytr.mean())
    ss_tot=float(((yt-yt.mean())**2).sum())
    r2_model=1-float(((yt-pred)**2).sum())/ss_tot if ss_tot>0 else np.nan
    r2_const=1-float(((yt-const)**2).sum())/ss_tot if ss_tot>0 else np.nan
    rows.append({"drug":drug,"n_test":int(te.sum()),"r2_model":r2_model,"r2_const":r2_const})
r=pd.DataFrame(rows)
def bsum(v,off):
    v=np.asarray(v,float); v=v[np.isfinite(v)]
    rng=np.random.default_rng(SEED+off)
    b=[float(np.mean(rng.choice(v,size=len(v),replace=True))) for _ in range(N_BOOT)]
    return {"n":int(len(v)),"mean":float(v.mean()),"median":float(np.median(v)),
            "ci95":[float(np.quantile(b,0.025)),float(np.quantile(b,0.975))]}
diff=r.r2_model-r.r2_const
res={"kind":"leave_one_drug_out_r2_baseline_correction",
     "audit":{"folds":int(len(r)),"test_rows_total":int(r.n_test.sum())},
     "r2_model":bsum(r.r2_model,91),"r2_const":bsum(r.r2_const,92),"r2_diff":bsum(diff,93),
     "frac_drugs_model_better":float((diff>0).mean()),
     "note":"Spearman against a constant prediction is undefined (zero variance); R^2 is the correct baseline metric."}
(OUT/"E029B_R2.json").write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(res,indent=1,ensure_ascii=False))
