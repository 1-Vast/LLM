import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd
p=Path(r'D:\MAESTRO\research\2026-10-27-agent-cell-identifiability-r163\e163_tuned_headline.py')
s=importlib.util.spec_from_file_location('e163',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
d=pd.read_csv(m.ORIG,low_memory=False,usecols=m.USE)
d['emax']=pd.to_numeric(d['SYNERGY_DELTA_EMAX'],errors='coerce'); d['cell']=d['CELL_LINE_NAME'].astype(str)
d['key']=d['cell']+'|'+d['ANCHOR_NAME'].astype(str)+' + '+d['LIBRARY_NAME'].astype(str)
g=d.groupby('key',as_index=False).agg(a=('ANCHOR_NAME','first'),b=('LIBRARY_NAME','first'),emax=('emax','mean'))
g=g[np.isfinite(g.emax)].reset_index(drop=True)
A=g.a.to_numpy(); B=g.b.to_numpy(); drugs=sorted(set(A)|set(B)); rng=np.random.default_rng(m.SEED)
rows=[]; tests=[]
for rep in range(m.REPS):
 ds=drugs[:]; rng.shuffle(ds); held=set(ds[:max(3,round(.2*len(ds)))])
 au=np.isin(A,list(held)); bu=np.isin(B,list(held)); outer=np.flatnonzero(~au & ~bu); test=np.flatnonzero(au & bu)
 if len(test)<150: continue
 tests.append(set(test.tolist()))
 folds=np.array_split(np.random.default_rng(m.SEED+rep).permutation(len(outer)),m.FOLDS)
 for va in folds:
  train=np.setdiff1d(np.arange(len(outer)),va)
  ptrain=set(zip(A[outer[train]],B[outer[train]])); pval=list(zip(A[outer[va]],B[outer[va]]))
  dtrain=set(A[outer[train]])|set(B[outer[train]])
  rows.append({'pair_overlap_fraction':sum(x in ptrain for x in pval)/len(pval),'both_drugs_seen_fraction':sum(a in dtrain and b in dtrain for a,b in pval)/len(pval)})
pairs=[len(a&b)/len(a|b) for i,a in enumerate(tests) for b in tests[i+1:] if a|b]
x=pd.DataFrame(rows); result=pd.read_csv(m.OUT/'E163_rows.csv'); b=result[result.pool=='both_unseen']
out={'input_sha256':m.sha256(m.ORIG),'outer_reps':len(tests),'folds':len(rows),'mean_pair_overlap_fraction':x.pair_overlap_fraction.mean(),'min_pair_overlap_fraction':x.pair_overlap_fraction.min(),'max_pair_overlap_fraction':x.pair_overlap_fraction.max(),'mean_both_drugs_seen_fraction':x.both_drugs_seen_fraction.mean(),'outer_test_pairwise_jaccard_mean':float(np.mean(pairs)),'outer_test_pairwise_jaccard_max':float(np.max(pairs)),'path_lambda_at_max_count':int((b.lam_pathway==max(m.LAMBDAS)).sum()),'notes':'Overlap uses ordered anchor-library pairs; Jaccard uses cell-pair keys. No refitting or confidence interval recalibration.'}
Path(r'D:\MAESTRO\research\2026-10-27-handoff-method-audit\split_diagnostic.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
