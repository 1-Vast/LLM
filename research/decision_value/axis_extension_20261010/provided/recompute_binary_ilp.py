import sys
import sys, importlib.util, json, numpy as np, time
from scipy.sparse import csr_matrix, lil_matrix
from scipy.optimize import milp, Bounds, LinearConstraint
from pathlib import Path
here=(Path(__file__).resolve().parent/'replay'/'research'/'decision_value'/'axis_recovery_20261010'/'calibration_v2') if len(sys.argv)<2 else (Path(sys.argv[1]).resolve()/'research'/'decision_value'/'axis_recovery_20261010'/'calibration_v2')
p=here/'diagnosis'/'index_discrimination.py'
spec=importlib.util.spec_from_file_location('idx',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
protocol=json.load(open(here/'PROTOCOL.json'))
layouts=json.load(open(here/'INDEX_LAYOUTS.json'))
manifest=json.load(open(here/'ROW_MANIFEST.json'))['groups']
result=json.load(open(here/'diagnosis'/'RESULTS.json'))
for f in result['files']:
 t0=time.perf_counter();file=f['file'];jobs=layouts[file]
 names=json.load(open(here/'inputs'/(file+'_GENES.json')))
 expected=[names.index(s) for s in protocol['endpoint']['symbols']]
 old_discovery={r for g in manifest if g['file']==file for r in g['discovery_rows']}
 old_holdout={r for g in manifest if g['file']==file for r in g['holdout_rows']}
 src=mod.IndexSource(file)
 row_indices=[]
 for job in jobs:
  idx=np.frombuffer(b''.join(src.at(a,b) for a,b in job['indices']),dtype='<i4')
  row_indices.append(idx)
 pointer=[0]
 for idx in row_indices:pointer.append(pointer[-1]+len(idx))
 M=csr_matrix((np.ones(pointer[-1],dtype=bool),np.concatenate(row_indices),np.array(pointer,dtype=np.int64)),shape=(len(jobs),len(names)));M.sort_indices()
 row_lookup={j['row']:i for i,j in enumerate(jobs)}
 old=[row_lookup[r] for r in sorted(old_discovery)]
 aliases=mod.patterns(M,old,expected)
 pairs=[(e,j) for e,group in zip(expected,aliases) for j in group if j!=e]
 candidates=np.array([i for i,j in enumerate(jobs) if j['row'] not in old_discovery and j['row'] not in old_holdout],dtype=int)
 distinct_genes=sorted({j for pair in pairs for j in pair}); local={g:k for k,g in enumerate(distinct_genes)}
 restricted=M[candidates][:,distinct_genes].toarray().astype(np.int8)
 A=np.array([(restricted[:,local[i]]!=restricted[:,local[j]]).astype(np.float64) for i,j in pairs])
 assert (A.sum(axis=1)>0).all()
 constraint=LinearConstraint(csr_matrix(A),np.ones(len(pairs)),np.full(len(pairs),np.inf))
 print(file,'constraints',len(pairs),'candidate rows',len(candidates),'maxcoverage',int(A.sum(axis=0).max()),'elapsed',round(time.perf_counter()-t0,3),flush=True)
 out=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=constraint, options={'time_limit':15.,'mip_rel_gap':0.01})
 if out.x is None:
  print('NO SOLUTION',out.message,flush=True);continue
 sel=candidates[np.nonzero(out.x>0.5)[0]]
 print('MILP status',out.status,out.message, 'n',len(sel),'lowerbound',out.mip_dual_bound,'gap',out.mip_gap,'elapsed',round(time.perf_counter()-t0,3),flush=True)
 print('MILP ROWS',[jobs[i]['row'] for i in sel], 'coverage',int((A[:,np.nonzero(out.x>0.5)[0]].sum(axis=1)>0).sum()),flush=True)
 # try cost minimization with cardinality fixed
 cost=np.array([jobs[i]['nnz']*4+8000 for i in candidates],dtype=np.float64)
 const_card=LinearConstraint(csr_matrix(np.ones((1,len(candidates)))),[len(sel)],[len(sel)])
 out2=milp(cost,integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=[constraint,const_card],options={'time_limit':15.,'mip_rel_gap':0.005})
 if out2.x is not None:
  sel2=candidates[np.nonzero(out2.x>0.5)[0]]
  print('COST n',len(sel2),'status',out2.status,'total estimated gross',sum(jobs[i]['nnz']*4+8000 for i in sel2),'ROWS',[jobs[i]['row'] for i in sel2],flush=True)
