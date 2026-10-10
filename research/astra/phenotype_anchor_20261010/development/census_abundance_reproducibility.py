import json, numpy as np, itertools
from collections import defaultdict
HELD = {"c12.h5ad","c20.h5ad","c26.h5ad","c27.h5ad","c31.h5ad"}
C = "research/astra/zeroshot_context_20261007/census/"
N = {}; names={}
for i in range(50):
    f=f"c{i}.h5ad"
    if f in HELD: continue
    d=json.load(open(C+f+".json")); names[f]=d["cell_names"][0]
    for lab,pl,n in d["condition_plate_counts"]:
        N[(f,lab,pl)]=n
lines=sorted(names); labs=sorted({k[1] for k in N}); plates=sorted({k[2] for k in N})
print(len(lines),"ref lines", len(labs),"labels", len(plates),"plates")
L={l:i for i,l in enumerate(lines)}
cells=defaultdict(dict)
for (f,lab,pl),n in N.items(): cells[(lab,pl)][f]=n
# completeness
miss=sum(1 for k,v in cells.items() if len(v)<len(lines)); print("wells with missing lines",miss,"of",len(cells))
D={k:sum(v.values()) for k,v in cells.items()}
tot=np.array(list(D.values())); print("well totals: median",np.median(tot),"p5",np.percentile(tot,5),"p95",np.percentile(tot,95))
dm=[k for k in cells if k[0].startswith("[('DMSO_TF'")]
def lfc(lab,pl):
    v=cells[(lab,pl)]; d0=cells[("[('DMSO_TF', 0.0, 'uM')]",pl)]
    a=np.array([np.log2((v.get(l,0)+0.5)/D[(lab,pl)]) for l in lines]); b=np.array([np.log2((d0.get(l,0)+0.5)/D[("[('DMSO_TF', 0.0, 'uM')]",pl)]) for l in lines])
    return a-b
# replicate labels
byl=defaultdict(list)
for (lab,pl) in cells: byl[lab].append(pl)
reps=[l for l,p in byl.items() if len(p)==2 and not l.startswith("[('DMSO")]
print("labels on exactly 2 plates:",len(reps))
X=[];Y=[]
for lab in reps:
    p1,p2=sorted(byl[lab]); X.append(lfc(lab,p1)); Y.append(lfc(lab,p2))
X=np.array(X);Y=np.array(Y)
print("raw LFC r across plates:",np.corrcoef(X.ravel(),Y.ravel())[0,1])
# interaction: remove label mean (over lines) and line mean (over labels) per plate-replicate
def inter(M): return M - M.mean(1,keepdims=True) - M.mean(0,keepdims=True) + M.mean()
Xi,Yi=inter(X),inter(Y)
print("interaction r:",np.corrcoef(Xi.ravel(),Yi.ravel())[0,1])
print("label-centered r:",np.corrcoef((X-X.mean(1,keepdims=True)).ravel(),(Y-Y.mean(1,keepdims=True)).ravel())[0,1])
# per-label selective magnitude and reproducibility for strong labels
sd=(Xi.std(1)+Yi.std(1))/2; order=np.argsort(-sd)
for j in order[:12]:
    print(reps[j][:60], round(sd[j],3), round(np.corrcoef(Xi[j],Yi[j])[0,1],3))
r_lab=np.array([np.corrcoef(Xi[j],Yi[j])[0,1] for j in range(len(reps))])
print("per-label interaction r: median",np.median(r_lab)," frac>0.5",np.mean(r_lab>0.5), "top quartile sd median r", np.median(r_lab[sd>np.percentile(sd,75)]))
# variance decomposition on avg of replicates
M=(X+Y)/2; tot=M.var();
print("var: label main",M.mean(1).var()/tot," line main",M.mean(0).var()/tot," inter",inter(M).var()/tot)
noise=((X-Y)**2).mean()/4  # var of mean-of-two noise
print("noise var of mean-of-2 / interaction var:", noise/inter(M).var())
print("\n=== plate-median baseline ===")
# log fraction matrix per well
W=sorted(cells); Wi={w:i for i,w in enumerate(W)}
LF=np.array([[np.log2((cells[w].get(l,0)+0.5)/D[w]) for l in lines] for w in W])
plate_of=np.array([w[1] for w in W]); isd=np.array([w[0].startswith("[('DMSO") for w in W])
base={}
for pl in plates:
    m=(plate_of==pl)
    base[pl]=np.median(LF[m],axis=0)
LFCm=np.array([LF[i]-base[W[i][1]] for i in range(len(W))])
X2=np.array([LFCm[Wi[(lab,sorted(byl[lab])[0])]] for lab in reps]); Y2=np.array([LFCm[Wi[(lab,sorted(byl[lab])[1])]] for lab in reps])
print("raw r",np.corrcoef(X2.ravel(),Y2.ravel())[0,1]," interaction r",np.corrcoef(inter(X2).ravel(),inter(Y2).ravel())[0,1])
r_lab=np.array([np.corrcoef(inter(X2)[j],inter(Y2)[j])[0,1] for j in range(len(reps))])
sd2=(inter(X2).std(1)+inter(Y2).std(1))/2
print("per-label r median",np.median(r_lab),"frac>0.5",np.mean(r_lab>0.5))
for q in (50,75,90):
    m=sd2>np.percentile(sd2,q); print(f" labels with sd>p{q}: n={m.sum()} median r={np.median(r_lab[m]):.3f}")
# how noisy is a 'null' well: dispersion of LFCm in wells of likely-inert labels
print("DMSO wells LFC sd (per plate median):",np.median([LFCm[(plate_of==pl)&isd].std() for pl in plates]))
print("all wells LFC sd median:",np.median(LFCm.std(1)))
# poisson expectation: per line count ~ D/45
print("median count per line-well:",np.median([v for w in W for v in cells[w].values()]))
# check DMSO well vs plate median agreement
for pl in plates[:4]:
    i=Wi[("[('DMSO_TF', 0.0, 'uM')]",pl)]; print(pl, "DMSO-vs-median sd", np.std(LF[i]-base[pl]).round(3))
print("\n=== by dose ===")
import re
dose=np.array([float(re.search(r", ([0-9.]+), 'uM'",l).group(1)) for l in reps])
for dv in sorted(set(dose)):
    m=dose==dv; print(dv, m.sum(), "median r", np.median(r_lab[m]).round(3), "frac>0.5", np.mean(r_lab[m]>0.5).round(3))
# signal-to-noise per label: var of interaction of mean vs noise
snr=[]
for j in range(len(reps)):
    a,b=inter(X2)[j],inter(Y2)[j]; s=np.var((a+b)/2); n=np.var(a-b)/4; snr.append((s-n)/s if s>0 else 0)
snr=np.array(snr); print("per-label reliability of mean-of-2 (1-noise/total): median",np.median(snr).round(3),"frac>0.5",np.mean(snr>0.5).round(3))
# single-plate labels: compare 5uM vs 0.5uM same drug selectivity (cross-dose consistency)
drug=lambda l: re.sub(r", [0-9.]+, 'uM'\)\]$","",l)
bydrug=defaultdict(dict)
for (lab,pl) in cells:
    if lab.startswith("[('DMSO"): continue
    m=re.search(r", ([0-9.]+), 'uM'\)\]$",lab)
    if m: bydrug[drug(lab)].setdefault(float(m.group(1)),[]).append(Wi[(lab,pl)])
rs=[]; strong=[]
for dname,dd in bydrug.items():
    if 5.0 in dd and 0.5 in dd:
        a=LFCm[dd[5.0]].mean(0); b=LFCm[dd[0.5]].mean(0)
        a=a-a.mean(); b=b-b.mean(); rs.append(np.corrcoef(a,b)[0,1]); strong.append(a.std())
rs=np.array(rs); strong=np.array(strong)
print("drugs with 5 and 0.5uM:",len(rs),"cross-dose selectivity r median",np.median(rs).round(3))
for q in (0,50,75,90):
    m=strong>=np.percentile(strong,q); print(f" 5uM sd>=p{q}: n={m.sum()} median r={np.median(rs[m]):.3f} frac>0.5={np.mean(rs[m]>0.5):.3f}")
print("\n=== absolute well totals ===")
lt={w: np.log2(D[w]) - np.median([np.log2(D[x]) for x in W if x[1]==w[1]]) for w in W}
vals=np.array(list(lt.values())); print("well total log2 vs plate median: sd",vals.std().round(3))
for key in ["Homoharringtonine', 5.0","Idarubicin (hydrochloride)', 5.0","Bortezomib","Trametinib (DMSO_TF solvate)', 5.0","Paclitaxel","Staurosporine","Panobinostat"]:
    ws=[w for w in W if key in w[0]]
    for w in ws[:4]: print(w[0][:55],w[1],round(lt[w],2))
# replicate correlation of well total across 2-plate labels
a=[lt[(lab,sorted(byl[lab])[0])] for lab in reps]; b=[lt[(lab,sorted(byl[lab])[1])] for lab in reps]
print("well-total replicate r:",np.corrcoef(a,b)[0,1].round(3))
# absolute per-line LFC (raw count vs plate-median count) reproducibility
LC=np.array([[np.log2(cells[w].get(l,0)+0.5) for l in lines] for w in W])
baseA={pl:np.median(LC[plate_of==pl],axis=0) for pl in plates}
ABS=np.array([LC[i]-baseA[W[i][1]] for i in range(len(W))])
Xa=np.array([ABS[Wi[(lab,sorted(byl[lab])[0])]] for lab in reps]); Ya=np.array([ABS[Wi[(lab,sorted(byl[lab])[1])]] for lab in reps])
print("absolute LFC replicate r (all):",np.corrcoef(Xa.ravel(),Ya.ravel())[0,1].round(3)," label-mean r:",np.corrcoef(Xa.mean(1),Ya.mean(1))[0,1].round(3))
