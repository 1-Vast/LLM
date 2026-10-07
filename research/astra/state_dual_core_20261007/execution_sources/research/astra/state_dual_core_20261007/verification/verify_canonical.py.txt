from pathlib import Path
import hashlib,json,time,math
import pandas as pd
import numpy as np
ROOT=Path(r'D:/MAESTRO'); BASE=ROOT/'research/astra/functional_data_20261007'; OUT=ROOT/'research/astra/state_dual_core_20261007/verification'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
t=time.perf_counter(); m=json.loads((BASE/'RUN_MANIFEST.json').read_text()); checks=[]
for key,root in [('files',BASE),('external_prerequisites',ROOT)]:
 for rel,x in m.get(key,{}).items():
  p=root/rel;checks.append({'path':str(p.relative_to(ROOT)),'exists':p.exists(),'sha256_matches':p.exists() and sha(p)==x['sha256'],'size_matches':p.exists() and p.stat().st_size==x['bytes']})
print('manifest keys',list(m))
for protocol,freeze in [('PROTOCOL.json','PROTOCOL_FREEZE.json'),('WORLD_PROTOCOL.json','WORLD_FREEZE.json')]:
 f=json.loads((BASE/freeze).read_text());assert sha(BASE/protocol)==f['sha256']
p=pd.read_csv(BASE/'world_results/heldout_predictions.csv.gz');p['ae']=(p.prediction-p.viability).abs();p['se']=(p.prediction-p.viability)**2
v=p.groupby(['arm','sidm'])[['ae','se']].mean().groupby('arm').mean();v['rmse']=np.sqrt(v.se)
s=pd.read_csv(BASE/'world_results/summary.csv',index_col='arm');assert np.allclose(v.ae,s.mae,rtol=1e-12);assert np.allclose(v.rmse,s.rmse,rtol=1e-12)
f=pd.read_csv(BASE/'data_run3/candidate_features.csv.gz');r=pd.read_csv(BASE/'prism_qualified/reference_observations.csv.gz')
trace=[json.loads(x) for x in (BASE/'ranking_results/purchase_traces.jsonl').read_text().splitlines()];df=pd.DataFrame(trace)
g=df.groupby(['arm','SIDM','role']);assert all(sorted(x.spent)==list(range(1,len(x)+1)) for _,x in g)
rebuild=df.assign(confirmed=(df.stage.eq('confirm')&df.positive)).groupby('arm').agg(spent=('spent','size'),confirmations=('confirmed','sum'))
saved=pd.read_csv(BASE/'ranking_results/summary.csv',index_col='arm');assert rebuild[['spent','confirmations']].equals(saved[['spent','confirmations']])
result={'status':'PASS' if all(x['sha256_matches'] and x['size_matches'] for x in checks) else 'FAIL','manifest_checks':checks,'protocol_freezes_match':True,'candidate_coverage':[int(f.exact_eligible.sum()),len(f)],'historical_cells':int(p.sidm.nunique()),'prism_qualified_rows':len(r),'prism_cells':int(r.sidm.nunique()),'world_metrics':v.reset_index().to_dict('records'),'paid_replay_totals':rebuild.reset_index().to_dict('records'),'replayed_campaigns':len(g),'paid_events':len(trace),'wall_seconds':time.perf_counter()-t,'claim':'Independent reconstruction of canonical saved artifacts; no prospective biological confirmation.'}
(OUT/'canonical_independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='manifest_checks'},indent=2))

