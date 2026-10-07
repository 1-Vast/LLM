"""Development-only diagnosis of source noise and original kernel composition."""
from pathlib import Path
import json,hashlib,time
import numpy as np,pandas as pd,h5py
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parents[4];OLD=R/'research/astra/state_dual_core_20261007';OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=time.perf_counter();plan=read(OLD/'world/metadata_freeze.json');contract=read(OLD/'world/contract.json');table=pd.read_csv(OLD/'world/conditions.csv');legal=table.split.isin(['train','development']);selected=[r for r in plan['conditions'] if r['split'] in ['train','development']]
manifest=read(OLD/'RUN_MANIFEST.json');checks=[]
for name,x in manifest['files'].items():
 p=OLD/name;checks.append({'path':name,'sha256_matches':sha(p)==x['sha256'],'bytes_match':p.stat().st_size==x['bytes']})
assert all(x['sha256_matches'] and x['bytes_match'] for x in checks)
(OUT/'prior_preservation_before.json').write_text(json.dumps({'status':'PASS','manifest_sha256':sha(OLD/'RUN_MANIFEST.json'),'files':checks},indent=2)+'\n')
rows=[];deltas=[];halves=[]
with h5py.File(contract['hashes']['dataset']['path'],'r') as h:
 matrix=h['obsm']['X_hvg'];obsids=h['obs'][h['obs'].attrs['_index']].asstr()[:]
 controls={p:np.asarray(matrix[v['reference_rows']],dtype=float) for p,v in plan['controls'].items()}
 for row in selected:
  x=np.asarray(matrix[row['treated_rows']],dtype=float);c=controls[row['plate']];delta=x.mean(0)-c.mean(0);deltas.append(delta)
  noise_t=float(np.mean(x.var(0,ddof=1))/len(x));noise_c=float(np.mean(c.var(0,ddof=1))/len(c));sq=float(np.mean(delta**2));noise=noise_t+noise_c
  item={k:row[k] for k in ['condition_id','drug','split','plate','dose_uM','chemical_group']};item.update(treated_n=len(x),reference_n=len(c),observed_rms=np.sqrt(sq),observed_squared_rms=sq,estimated_treated_sampling_noise=noise_t,estimated_reference_sampling_noise=noise_c,estimated_total_sampling_noise=noise,unclipped_noise_subtracted_squared_rms=sq-noise,noise_fraction_of_squared_rms=noise/sq);rows.append(item)
  if row['dose_uM']==5:
   order=sorted(range(len(x)),key=lambda i:hashlib.sha256(('diagnostic-halves-v1:'+str(obsids[row['treated_rows'][i]])).encode()).hexdigest());a,b=x[order[::2]],x[order[1::2]];ca,cb=c[::2],c[1::2]
   if min(len(a),len(b),len(ca),len(cb))<2:continue
   def rms(v):return float(np.sqrt(np.mean(v*v)))
   halves.append({'drug':row['drug'],'split':row['split'],'plate':row['plate'],'treated_n':len(x),'rms_a_shared':rms(a.mean(0)-c.mean(0)),'rms_b_shared':rms(b.mean(0)-c.mean(0)),'rms_a_disjoint_control':rms(a.mean(0)-ca.mean(0)),'rms_b_disjoint_control':rms(b.mean(0)-cb.mean(0)),'reference_half_discrepancy_rms':rms(ca.mean(0)-cb.mean(0)),'treated_half_discrepancy_rms':rms(a.mean(0)-b.mean(0))})
f=pd.DataFrame(rows);h=pd.DataFrame(halves);f.to_csv(OUT/'development_noise_rows.csv',index=False);h.to_csv(OUT/'development_half_rows.csv',index=False);y=np.asarray(deltas);train=np.flatnonzero(f.split.eq('train'));dev=np.flatnonzero(f.split.eq('development'))
def corr(a,b):return float(np.corrcoef(a,b)[0,1])
def mse(pred):return float(np.mean((y[dev]-pred[dev])**2))
# Fit source-plate means on TRAIN ONLY; missing plates fall back to train global mean.
plate_pred=np.array([y[train[f.iloc[train].plate.to_numpy()==p]].mean(0) if np.any(f.iloc[train].plate.to_numpy()==p) else y[train].mean(0) for p in f.plate]);dose_pred=np.array([y[train[f.iloc[train].dose_uM.to_numpy()==d]].mean(0) for d in f.dose_uM])
# Original kernels sliced to TRAIN+DEV ONLY; no evaluation outcomes opened.
old=np.load(OLD/'model_run1/kernels.npz');idx=np.flatnonzero(legal);K1=old['M1'][np.ix_(idx,idx)];K2=old['M2'][np.ix_(idx,idx)];state=5*K2-4*K1
assert np.allclose(K2,.8*K1+.2*state)
with threadpool_limits(limits=2):
 def pred(K,alpha=.1):
  mu=y[train].mean(0);return K[:,train]@np.linalg.solve(K[np.ix_(train,train)]+alpha*np.eye(len(train)),y[train]-mu)+mu
 losses={name:mse(pred(K)) for name,K in [('M1_original',K1),('M1_scaled_to_80pct',.8*K1),('M2_original',K2),('M1_plus_quarter_STATE_preserved_capacity',K1+.25*state)]}
summary={'scope':'TRAIN and DEVELOPMENT only; 30 chemical groups,90 conditions; no calibration/evaluation numerical outcomes read. Descriptive within-source technical diagnostics, not biological replication.','partitions':{},'kernel_fixed_alpha_0_1_development_mse':losses,'kernel_identity':'Original M2=.8*M1+.2*Kstate; equivalent additive M1+.25*Kstate with alpha increased1.25x. Original grid not nested at identical M1 capacity.','plate_and_dose_development_mse':{'train_plate_mean':mse(plate_pred),'train_dose_mean':mse(dose_pred)},'noise_formula':'E||mean(treated)-mean(control)||²/G = true_squared_shift + mean_gene_variance(treated)/n_t + mean_gene_variance(control)/n_c under independent sampled cells. Descriptive approximation; correlation and source effects may violate assumptions. Negative corrected values retained.','API_calls':0,'downloaded_bytes':0,'wall_seconds':time.perf_counter()-start}
for split in ['train','development']:
 q=f[f.split==split];v=h[h.split==split];summary['partitions'][split]={'conditions':len(q),'drug_groups':int(q.drug.nunique()),'median_treated_n':float(q.treated_n.median()),'median_reference_n':float(q.reference_n.median()),'median_observed_rms':float(q.observed_rms.median()),'median_noise_fraction':float(q.noise_fraction_of_squared_rms.median()),'noise_fraction_gt_half':int(q.noise_fraction_of_squared_rms.gt(.5).sum()),'negative_noise_subtracted_squared_rms':int(q.unclipped_noise_subtracted_squared_rms.lt(0).sum()),'rms_vs_inverse_sqrt_n_correlation':corr(q.observed_rms,1/np.sqrt(q.treated_n)),'technical_highdose_halves_correlation_shared_control':corr(v.rms_a_shared,v.rms_b_shared),'technical_highdose_halves_correlation_disjoint_controls':corr(v.rms_a_disjoint_control,v.rms_b_disjoint_control),'median_reference_half_discrepancy_rms':float(v.reference_half_discrepancy_rms.median()),'median_treated_half_discrepancy_rms':float(v.treated_half_discrepancy_rms.median())}
(OUT/'development_diagnosis.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
