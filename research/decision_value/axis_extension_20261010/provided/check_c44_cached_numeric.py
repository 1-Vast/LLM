import sys
import json, pathlib, importlib.util
import numpy as np, h5py
from scipy.sparse import csr_matrix
from datetime import datetime
R=pathlib.Path(__file__).resolve().parent.joinpath('replay','research','decision_value') if len(sys.argv)<2 else pathlib.Path(sys.argv[1]).resolve().joinpath('research','decision_value')
old=R/'observation_reliability/axis'; new=R/'axis_recovery_20261010/calibration_v2'
s=importlib.util.spec_from_file_location('oldverify',old/'verify.py');o=importlib.util.module_from_spec(s);s.loader.exec_module(o)
s=importlib.util.spec_from_file_location('idx',new/'diagnosis/index_discrimination.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
file='c44.h5ad'
receipts=[json.loads(x) for x in (old/'NETWORK.jsonl').read_text().splitlines()]
census=json.loads((old/'CENSUSES.json').read_text())
old_results=json.loads((old/'RESULTS.json').read_text())
oldrows=next(x['row_ids'] for x in old_results['files'] if x['file']==file)
src=o.RetainedSource(file,census[file]['file_bytes'],receipts)
hvg_offset=census[file]['layouts']['obsm/X_hvg']['offset']
coords=np.array([r['coordinate'] for r in json.loads((old/'PROTOCOL.json').read_text())['endpoint']['original_primary']['mapped']])
allrows=[];allidx=[];allvalues=[];alltgt=[]
with h5py.File(src,'r') as h5:
 for row in oldrows:
  begin,end=map(int,o.array_slice(src,h5['X/indptr'],row,row+2))
  idx=o.array_slice(src,h5['X/indices'],begin,end).astype(int).copy()
  vals=o.array_slice(src,h5['X/data'],begin,end).astype(float).copy()
  tgt=np.frombuffer(src.bytes_at(hvg_offset+row*8000,hvg_offset+(row+1)*8000-1),dtype='<f4')[coords].astype(float)
  allrows.append(('old_control',int(row)));allidx.append(idx);allvalues.append(vals);alltgt.append(tgt)
proto=json.loads((new/'PROTOCOL.json').read_text())
manifest=json.loads((new/'ROW_MANIFEST.json').read_text())['groups']
role={r:k for g in manifest if g['file']==file for k in ['discovery_rows','holdout_rows'] for r in g[k]}
layout=json.loads((new/'INDEX_LAYOUTS.json').read_text())[file]
lookup={j['row']:j for j in layout};source=i.IndexSource(file)
import hashlib
source.spans=[]
for r in i.lines(new/'NETWORK.jsonl')+i.lines(new/'CACHE_REUSE.jsonl'):
 if r.get('file') != file or r.get('status') not in ('RETAINED','REUSED'):continue
 path=new/r['path']
 if not path.exists():continue
 payload=path.read_bytes()
 assert len(payload)==r['bytes'] and hashlib.sha256(payload).hexdigest()==r['sha256']
 source.spans.append((r['start'],payload))
source.spans.sort(key=lambda x:x[0])
for row in sorted(role):
 job=lookup[row]
 idx=np.frombuffer(b''.join(source.at(a,b) for a,b in job['indices']),dtype='<i4').astype(int).copy()
 val=np.frombuffer(b''.join(source.at(a,b) for a,b in job['values']),dtype='<f4').astype(float).copy()
 hv=np.frombuffer(source.at(hvg_offset+row*8000,hvg_offset+(row+1)*8000-1),dtype='<f4')[coords].astype(float).copy()
 assert len(idx)==len(val)
 allrows.append(('new_'+('discovery' if role[row]=='discovery_rows' else 'holdout'),int(row)))
 allidx.append(idx);allvalues.append(val);alltgt.append(hv)
assert len(set(row for _,row in allrows))==len(allrows)
print('reads old',len(oldrows),'new',len(role),'index lengths',len(allidx),'sum nnz',sum(map(len,allidx)),flush=True)
ptr=[0]
for x in allidx:ptr.append(ptr[-1]+len(x))
M=csr_matrix((np.concatenate(allvalues),np.concatenate(allidx),np.array(ptr,dtype=np.int64)),shape=(len(allrows),62710));M.sort_indices()
T=np.array(alltgt)
names=json.loads((new/'inputs/c44.h5ad_GENES.json').read_text())
expected=[names.index(x) for x in proto['endpoint']['symbols']]
X=np.log1p(M.toarray())
err=np.max(np.abs(X[:,expected]-T),axis=0)
print('expected mapping max error',float(err.max()),'all pass?',bool(np.all(err<=1e-5)),flush=True)
# Check across all 62710 using all252 rows, then old+discovery (243 rows)
for subset_name, mask in [('combined_old_and_discovery',np.array([name!='new_holdout' for name,_ in allrows])),('combined_all_retained',np.ones(len(allrows),dtype=bool))]:
 xx=X[mask];tt=T[mask]
 c=[]
 for j,g in enumerate(expected):
  matches=[]
  for start in range(0,62710,4096):
   end=min(62710,start+4096)
   good=np.max(np.abs(xx[:,start:end]-tt[:,j,None]),axis=0)<=1e-5
   matches.extend((np.flatnonzero(good)+start).tolist())
  c.append(matches)
 print(subset_name,'verified',sum(len(v)==1 and v[0]==g for v,g in zip(c,expected)),'/39','ambiguous',[(proto['endpoint']['symbols'][j],len(v),[names[x] for x in v[:3]]) for j,v in enumerate(c) if len(v)>1 or (len(v)==1 and v[0]!=expected[j])],flush=True)
