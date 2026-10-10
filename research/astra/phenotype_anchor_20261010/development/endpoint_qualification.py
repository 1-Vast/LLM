import sys, json, numpy as np
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0,"research/astra/phenotype_anchor_20261010")
import phenotypes as P
allf=sorted((p.stem for p in Path("research/astra/phenotype_anchor_20261010/obs").glob("*.h5ad.json")), key=lambda s:int(s[1:-5]))
allf=[f for f in allf if f not in P.HELDOUT]
table,names=P.load_counts(allf)
med={f:np.median([v["n"] for (ff,l,p),v in table.items() if ff==f and l!=P.DMSO]) for f in allf}
low=sorted(allf,key=lambda f:med[f])[:6]
print("lowest-count lines:",[(f,names[f],med[f]) for f in low])
def analyse(files,tag):
    ph=P.phenotype_frame(table,files,files)
    byl=defaultdict(set)
    for (f,lab,pl) in ph: byl[lab].add(pl)
    reps=sorted(l for l,p in byl.items() if len(p)==2 and all((f,l,pl) in ph for f in files for pl in p))
    pairs=Counter(tuple(sorted(byl[l])) for l in reps)
    def inter(M): return M-M.mean(1,keepdims=True)-M.mean(0,keepdims=True)+M.mean()
    print(f"--- {tag}: {len(files)} lines, {len(reps)} replicate labels; plate pairs {pairs.most_common(4)}")
    res={}
    for ep in ("survival","G1","S","G2M"):
        X=np.array([[ph[(f,lab,sorted(byl[lab])[0])][ep] for f in files] for lab in reps])
        Y=np.array([[ph[(f,lab,sorted(byl[lab])[1])][ep] for f in files] for lab in reps])
        rl=np.array([np.corrcoef(inter(X)[j],inter(Y)[j])[0,1] for j in range(len(reps))])
        print(f"{ep:9s} raw r={np.corrcoef(X.ravel(),Y.ravel())[0,1]:.3f} drug-mean r={np.corrcoef(X.mean(1),Y.mean(1))[0,1]:.3f} line-mean r={np.corrcoef(X.mean(0),Y.mean(0))[0,1]:.3f} interaction r={np.corrcoef(inter(X).ravel(),inter(Y).ravel())[0,1]:.3f} per-drug median={np.median(rl):.3f} frac>0.5={np.mean(rl>0.5):.2f}")
        res[ep]=(X,Y)
    return ph,reps,byl,res
ph,reps,byl,res=analyse(allf,"all 45")
keep=[f for f in allf if med[f]>=200]
print("excluded (median<200 cells):",[names[f] for f in allf if f not in keep])
ph,reps,byl,res=analyse(keep,"count-qualified")
# bridge plausibility: survival interaction vs same-well phase shifts (all wells, not just replicates)
files=keep
keys=[k for k in ph if k[0] in files]
S=np.array([ph[k]["survival"] for k in keys]); G=np.array([[ph[k][p] for p in ("G1","S","G2M")] for k in keys])
# center by label and line (two-way) approx via per-label then per-line demeaning
lab=np.array([k[1]+k[2] for k in keys]); ln=np.array([k[0] for k in keys])
def demean(v):
    v=v.copy()
    for _ in range(5):
        for g in (lab,ln):
            u,inv=np.unique(g,return_inverse=True); m=np.bincount(inv,weights=v)/np.bincount(inv); v-=m[inv]
    return v
Sd=demean(S); Gd=np.column_stack([demean(G[:,i]) for i in range(3)])
beta,*_=np.linalg.lstsq(Gd,Sd,rcond=None); pred=Gd@beta
print("same-well phase shifts explain survival interaction: R2=",round(1-((Sd-pred)**2).sum()/(Sd**2).sum(),3),"beta",beta.round(3))
for i,p in enumerate(("G1","S","G2M")): print(" corr survival~",p,round(np.corrcoef(Sd,Gd[:,i])[0,1],3))
import re
print("\n=== replicate set activity vs all labels ===")
files=keep
def labsd(lab,pl,ep): return np.std([ph[(f,lab,pl)][ep] for f in files if (f,lab,pl) in ph])
allw=sorted({(k[1],k[2]) for k in ph})
for ep in ("survival","G1"):
    a=np.array([labsd(l,p,ep) for l,p in allw]); r=np.array([labsd(l,sorted(byl[l])[0],ep) for l in reps])
    print(ep,"across-line sd: all wells median",np.median(a).round(3),"p90",np.percentile(a,90).round(3)," replicate labels median",np.median(r).round(3))
print("replicate doses:",Counter(re.search(r", ([0-9.]+), 'uM'",l).group(1) for l in reps))
print("\n=== cross-dose consistency (0.5 vs 5 uM, different plates), interaction ===")
drug=lambda l: re.sub(r", [0-9.]+, 'uM'\)\]$","",l)
bydose=defaultdict(lambda: defaultdict(list))
for (f,lab,pl) in ph:
    m=re.search(r", ([0-9.]+), 'uM'\)\]$",lab)
    if m and f in files: bydose[drug(lab)][float(m.group(1))].append((f,lab,pl))
for ep in ("survival","G1","S","G2M"):
    A=[];B=[];names_=[]
    for d,dd in bydose.items():
        if 5.0 in dd and 0.5 in dd:
            va=defaultdict(list); vb=defaultdict(list)
            for k in dd[5.0]: va[k[0]].append(ph[k][ep])
            for k in dd[0.5]: vb[k[0]].append(ph[k][ep])
            if all(f in va and f in vb for f in files):
                A.append([np.mean(va[f]) for f in files]); B.append([np.mean(vb[f]) for f in files]); names_.append(d)
    A=np.array(A);B=np.array(B)
    def inter(M): return M-M.mean(1,keepdims=True)-M.mean(0,keepdims=True)+M.mean()
    rl=np.array([np.corrcoef(inter(A)[j],inter(B)[j])[0,1] for j in range(len(A))])
    act=inter(A).std(1)
    top=act>=np.percentile(act,75)
    print(f"{ep:9s} n={len(A)} drug-mean r={np.corrcoef(A.mean(1),B.mean(1))[0,1]:.3f} interaction r={np.corrcoef(inter(A).ravel(),inter(B).ravel())[0,1]:.3f} per-drug median={np.median(rl):.3f}; top-quartile-active 5uM drugs median={np.median(rl[top]):.3f} frac>0.5={np.mean(rl[top]>0.5):.2f}")
import pandas as pd
print("\n=== LOO-line context priors for the interaction (5uM labels, single wells) ===")
cm=pd.read_parquet("data/external/tahoe_phenotype_20261010/metadata/tahoe_cells.parquet")
dm=pd.read_parquet("data/external/tahoe_phenotype_20261010/metadata/tahoe_drugs.parquet")
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
organ={}; drivers=defaultdict(set)
for _,r in cm.iterrows():
    organ[norm(r.cell_name)]=r.Organ
    if r.Driver_Mech_InferDM=="GoF" or r.Driver_GeneType_DM=="Oncogene": drivers[norm(r.cell_name)].add(str(r.Driver_Gene_Symbol))
ln_org={f:organ.get(norm(names[f])) for f in files}; print("organ matched",sum(v is not None for v in ln_org.values()),"/",len(files), Counter(ln_org.values()).most_common(8))
targets={norm(r.drug):set(str(r.targets).replace(" ","").split(",")) if r.targets else set() for _,r in dm.iterrows()}
labs5=sorted({k[1] for k in ph if ", 5.0, 'uM')]" in k[1] and all((f,k[1],sorted(byl[k[1]])[0]) in ph for f in files)})
pl_of={l:sorted(byl[l])[0] for l in labs5}
for ep in ("survival","G1"):
    M=np.array([[ph[(f,l,pl_of[l])][ep] for f in files] for l in labs5])  # labels x lines
    I=M-M.mean(1,keepdims=True)-M.mean(0,keepdims=True)+M.mean()
    r_org=[];r_drv=[]
    for j,f in enumerate(files):
        same=[i for i,g in enumerate(files) if i!=j and ln_org[g]==ln_org[f] and ln_org[f] is not None]
        others=[i for i in range(len(files)) if i!=j]
        Io=M[:,others]-M[:,others].mean(1,keepdims=True)  # LOO interaction proxy
        if same:
            pred=(M[:,same]-M[:,others].mean(1,keepdims=True)).mean(1); r_org.append(np.corrcoef(pred,I[:,j])[0,1])
        # driver-target prior: label's drug targets one of line's GoF drivers -> predicted more negative survival / more G1
        dg=drivers.get(norm(names[f]),set())
        hit=np.array([len(targets.get(norm(re.sub(r"^\[\('","",drug(l))),set()) & dg)>0 for l in labs5],float)
        if hit.sum()>0 and hit.sum()<len(hit): r_drv.append((np.corrcoef(hit,I[:,j])[0,1], int(hit.sum())))
    print(f"{ep}: same-organ LOO prior r median={np.median(r_org):.3f} (n lines={len(r_org)}); driver-target r median={np.median([x[0] for x in r_drv]) if r_drv else float('nan'):.3f} over {len(r_drv)} lines, hits/line median {np.median([x[1] for x in r_drv]) if r_drv else 0}")
