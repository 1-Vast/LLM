import sys, json, numpy as np
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,"research/astra/phenotype_anchor_20261010")
import phenotypes as P
files=sorted(p.stem for p in Path("research/astra/phenotype_anchor_20261010/obs").glob("*.h5ad.json"))
files=[f for f in files if f not in P.HELDOUT]
print(len(files),"lines")
r0=json.loads(Path(f"research/astra/phenotype_anchor_20261010/obs/{files[0]}.json").read_text()); print(r0["categories"]["phase"], r0["categories"]["pass_filter"])
table,names=P.load_counts(files)
ph=P.phenotype_frame(table,files,files)
byl=defaultdict(set)
for (f,lab,pl) in ph: byl[lab].add(pl)
reps=sorted(l for l,p in byl.items() if len(p)==2 and all((f,l,pl) in ph for f in files for pl in p))
print(len(reps),"complete replicate labels")
def inter(M): return M-M.mean(1,keepdims=True)-M.mean(0,keepdims=True)+M.mean()
for ep in ("survival","G1","S","G2M"):
    X=np.array([[ph[(f,lab,sorted(byl[lab])[0])][ep] for f in files] for lab in reps])
    Y=np.array([[ph[(f,lab,sorted(byl[lab])[1])][ep] for f in files] for lab in reps])
    rl=np.array([np.corrcoef(inter(X)[j],inter(Y)[j])[0,1] for j in range(len(reps))])
    M=(X+Y)/2; tot=M.var()
    print(f"{ep:9s} raw r={np.corrcoef(X.ravel(),Y.ravel())[0,1]:.3f} label-mean r={np.corrcoef(X.mean(1),Y.mean(1))[0,1]:.3f} interaction r={np.corrcoef(inter(X).ravel(),inter(Y).ravel())[0,1]:.3f} per-label median={np.median(rl):.3f} frac>0.5={np.mean(rl>0.5):.2f} | var label={M.mean(1).var()/tot:.2f} line={M.mean(0).var()/tot:.2f} inter={inter(M).var()/tot:.2f}")
