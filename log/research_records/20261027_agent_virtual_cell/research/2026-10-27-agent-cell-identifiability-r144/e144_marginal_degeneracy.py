# -*- coding: utf-8 -*-
import numpy as np, pandas as pd
from pathlib import Path
R = Path(r"D:\MAESTRO")
ORIG = R/"data"/"external"/"gdsc_combinations"/"jaaks2022_figshare"/"Original screen_All tissues_fitted data.csv"
d = pd.read_csv(ORIG, low_memory=False, usecols=["CELL_LINE_NAME","ANCHOR_NAME","LIBRARY_NAME","SYNERGY_DELTA_EMAX"])
d["emax"]=pd.to_numeric(d["SYNERGY_DELTA_EMAX"],errors="coerce")
d["cell"]=d["CELL_LINE_NAME"].astype(str)
d["combo"]=d["ANCHOR_NAME"].astype(str)+" + "+d["LIBRARY_NAME"].astype(str)
d["key"]=d["cell"]+"|"+d["combo"]
g=d.groupby("key",as_index=False).agg(cell=("CELL_LINE_NAME","first"),a=("ANCHOR_NAME","first"),
    b=("LIBRARY_NAME","first"),emax=("emax","mean"))
for c in ("cell","a","b"): g[c]=g[c].astype(str)
g=g[np.isfinite(g["emax"])].reset_index(drop=True)
A=g["a"].to_numpy(); B=g["b"].to_numpy(); y=g["emax"].to_numpy(float)
drugs=sorted(set(A)|set(B)); rng=np.random.default_rng(20261047)
sds=[]; exact=0; n=0
for rep in range(60):
    ds=drugs[:]; rng.shuffle(ds)
    held=set(ds[:max(3,int(round(0.20*len(ds))))])
    au=np.array([x in held for x in A]); bu=np.array([z in held for z in B])
    tr=np.where((~au)&(~bu))[0]; te=np.where(au&bu)[0]
    if len(tr)<15000 or len(te)<200: continue
    grand=y[tr].mean(); acc={}
    for i in tr:
        acc.setdefault(A[i],[]).append(y[i]); acc.setdefault(B[i],[]).append(y[i])
    meff={k:float(np.mean(v))-grand for k,v in acc.items()}
    pred=np.array([meff.get(A[i],0.0)+meff.get(B[i],0.0)+grand for i in te])
    sd=float(np.std(pred)); sds.append(sd); n+=1
    if sd==0.0: exact+=1
print("reps:", n, "| exactly-zero sd:", exact, "| max sd: %.3e | mean sd: %.3e" % (max(sds), float(np.mean(sds))))
print("all below 1e-12:", all(s<1e-12 for s in sds))
