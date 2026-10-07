"""Independent saved-artifact reconstruction; does not import model implementation."""
from pathlib import Path
import json,hashlib,time
import numpy as np
import pandas as pd
import h5py
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from threadpoolctl import threadpool_limits
B=Path(__file__).resolve().parents[1];R=B.parents[2];W=B/'world';M=B/'model_run1';O=B/'verification'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(8<<20),b''):h.update(c)
 return h.hexdigest()
def col(g,k):
 x=g[k]
 if isinstance(x,h5py.Group):return np.array(x['categories'].asstr()[:])[x['codes'][:]]
 return x.asstr()[:]
def group_error(y,p,idx,groups):return pd.DataFrame({'group':groups[idx],'error':np.mean((y[idx]-p[idx])**2,axis=1)}).groupby('group').error.mean()
def linear(x,idx):
 x=np.asarray(x,float);x=x-x[idx].mean(0);return (x@x.T)/max(np.mean((x[idx]**2).sum(1)),1e-12)
t=time.perf_counter();f=pd.read_csv(W/'conditions.csv');plan=read(W/'metadata_freeze.json');c=read(W/'contract.json');p=np.load(M/'predictions.npz');k=np.load(M/'kernels.npz');z=np.load(W/'sealed_outcomes.npz');s=np.load(W/'state_features.npz');basal=np.load(W/'basal_controls.npz');sel=read(M/'model_selection.json');metrics=read(M/'metrics.json')
assert sha(B/'PROTOCOL.json')==read(B/'PROTOCOL_FREEZE.json')['sha256']
for name,h in read(B/'PROTOCOL.json')['frozen_inputs'].items():assert sha(B/name)==h
for name,h in read(M/'manifest.json').items():assert sha(M/name)==h,name
assert sha(B/'run_models.py')==read(M/'resources.json')['source_sha256']
assert np.array_equal(f.condition_id,p['condition_id']) and np.array_equal(f.condition_id,z['condition_id']) and np.array_equal(f.condition_id,s['condition_id'])
assert len(f)==144 and f.chemical_group.nunique()==48 and f.groupby('chemical_group').split.nunique().eq(1).all()
assert dict(f.groupby('split').drug.nunique())=={'train':24,'development':6,'calibration':6,'evaluation':12}
controls=set();reference=set();treated=set()
with h5py.File(c['hashes']['dataset']['path'],'r') as h:
 labels=col(h['obs'],'drugname_drugconc');plates=col(h['obs'],'plate');mat=h['obsm']['X_hvg']
 for plate,rows in plan['controls'].items():
  a,b=rows['basal_rows'],rows['reference_rows'];assert not set(a)&set(b)
  controls.update(a);reference.update(b);assert np.array_equal(basal[plate],mat[a]);assert all(plates[a]==plate) and all(plates[b]==plate)
  assert len(set(labels[a]))==len(set(labels[b]))==1 and labels[a[0]]==labels[b[0]]
 for i,row in enumerate(plan['conditions']):
  ix=row['treated_rows'];treated.update(ix);assert all(labels[ix]==row['label']) and all(plates[ix]==str(row['plate']))
  mean=np.asarray(mat[ix]).mean(0);ref=np.asarray(mat[plan['controls'][row['plate']]['reference_rows']]).mean(0)
  np.testing.assert_array_equal(mean,z['observed_mean'][i]);np.testing.assert_array_equal(ref,z['reference_mean'][i]);np.testing.assert_array_equal(mean-ref,z['observed_delta'][i])
assert not treated&(controls|reference)
np.testing.assert_array_equal(z['observed_delta'],p['observed_delta']);np.testing.assert_allclose(np.sqrt((z['observed_delta']**2).mean(1)),z['magnitude'],rtol=1e-7)
np.testing.assert_array_equal(s['predicted_mean']-s['basal_mean'],s['state_delta'])
train=np.flatnonzero(f.split.eq('train'));dev=np.flatnonzero(f.split.eq('development'));cal=np.flatnonzero(f.split.eq('calibration'));ev=np.flatnonzero(f.split.eq('evaluation'));g=f.chemical_group.to_numpy();y=p['observed_delta'];ym=p['observed_magnitude']
# Independently derive chemistry/target/dose kernels and training-only normalization.
meta=pd.read_parquet(R/'tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/tahoe_drugs.raw');lookup={str(r.drug).strip().lower():r for r in meta.itertuples()};rows=[lookup[d.strip().lower()] for d in f.drug];gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=1024);fps=[gen.GetFingerprint(Chem.MolFromSmiles(r.canonical_smiles)) for r in rows]
chem=np.array([[DataStructs.TanimotoSimilarity(a,b) for b in fps] for a in fps]);ts=[set(r.targets.split(',')) if isinstance(r.targets,str) else set() for r in rows];tar=np.array([[len(a&b)/max(np.sqrt(len(a)*len(b)),1) for b in ts] for a in ts]);dose=np.equal.outer(f.dose_uM.to_numpy(),f.dose_uM.to_numpy()).astype(float);bk=linear(s['basal_mean'],train);sk=linear(s['state_delta'],train);perm=k['permutation']
np.testing.assert_array_equal(np.sort(perm),np.arange(len(f)));assert np.array_equal(f.split,f.iloc[perm].split) and np.array_equal(f.dose_uM,f.iloc[perm].dose_uM) and np.array_equal(f.plate,f.iloc[perm].plate)
assert np.any(perm!=np.arange(len(f)));assert not np.array_equal(s['state_delta'][perm],s['state_delta'])
expected={'M1':(chem+tar+dose+bk)/4,'M2':(chem+tar+dose+bk+sk)/5,'metadata_only':(chem+tar+dose)/3,'basal_only':(bk+dose)/2,'missingness_only':(linear([[not bool(t)] for t in ts],train)+dose)/2,'permuted_STATE':(chem+tar+dose+bk+linear(s['state_delta'][perm],train))/5}
with threadpool_limits(limits=2):
 for name,K in expected.items():
  np.testing.assert_allclose(K,k[name],atol=1e-12)
  trials=[]
  for alpha in [.1,1.,10.]:
   mu=y[train].mean(0);pred=K[:,train]@np.linalg.solve(K[np.ix_(train,train)]+np.eye(len(train))*alpha,y[train]-mu)+mu
   trials.append((group_error(y,pred,dev,g).mean(),alpha,pred))
  _,a,pred=min(trials,key=lambda v:(v[0],v[1]));assert a==sel[name]['alpha'];np.testing.assert_allclose(pred,p[name],atol=1e-12)
  mu=ym[train].mean();predm=K[:,train]@np.linalg.solve(K[np.ix_(train,train)]+np.eye(len(train))*a,ym[train]-mu)+mu;np.testing.assert_allclose(predm,p['scalar_'+name],atol=1e-12)
errors={};recomputed={}
for name in metrics['methods']:
 err=group_error(y,p[name],ev,g);errors[name]=err.to_numpy();np.testing.assert_allclose(err.mean(),metrics['methods'][name]['evaluation_group_mse'],rtol=1e-12)
 sm=p['scalar_'+name];cg=pd.DataFrame({'g':g[cal],'v':abs(sm[cal]-ym[cal])}).groupby('g').v.max();width=np.sort(cg.to_numpy())[int(np.ceil((len(cg)+1)*.8))-1];np.testing.assert_allclose(width,metrics['methods'][name]['interval_halfwidth_80'],rtol=1e-12)
 high=ev[f.iloc[ev].dose_uM.to_numpy()==5];acc=[]
 for ai,a in enumerate(high):
  for b in high[ai+1:]:acc.append(.5 if sm[a]==sm[b] or ym[a]==ym[b] else float(np.sign(sm[a]-sm[b])==np.sign(ym[a]-ym[b])))
 np.testing.assert_allclose(np.mean(acc),metrics['methods'][name]['high_dose_pair_ordering'])
 recomputed[name]={'mse':float(err.mean()),'scalar_mae':float(np.mean(abs(sm[ev]-ym[ev]))),'high_dose_ordering':float(np.mean(acc))}
rng=np.random.default_rng(731);contrasts={}
for baseline in [sel['M0_selected'],'M1']:
 d=errors['M2']-errors[baseline];ci=np.quantile(d[rng.integers(len(d),size=(2000,len(d)))].mean(1),[.025,.975]);saved=metrics['primary'][baseline];np.testing.assert_allclose(d.mean(),saved['M2_minus_comparator_mse'],atol=1e-15);np.testing.assert_allclose(ci,saved['descriptive_drug_bootstrap_95'],atol=1e-15);contrasts[baseline]={'difference':float(d.mean()),'interval':ci.tolist()}
assert metrics['primary_success_rule_passed']==all(x['interval'][1]<0 for x in contrasts.values())
# Static source audit complements real source-row reconstruction.
infer=(W/'execution_source.py.txt').read_text().split('def infer():')[1].split('def outcomes():')[0];assert 'treated_rows' not in infer and 'h5py' not in infer and 'sealed_outcomes' not in infer
receipt={'status':'PASS','source_outcomes_reconstructed':144,'chemical_groups':48,'evaluation_groups':12,'control_rows_disjoint':True,'treated_rows_never_in_controls':True,'trained_model_kernel_and_alpha_rebuilt':6,'primary':contrasts,'primary_success':metrics['primary_success_rule_passed'],'method_metrics':recomputed,'permutation_changed_rows':int((perm!=np.arange(len(f))).sum()),'permutation_preserves_split_dose_plate':True,'checkpoint_forward_count':read(W/'inference_resources.json')['forwards'],'source_manifest_hashes_checked':len(read(M/'manifest.json')),'cross_assay_labels_used':False,'wall_seconds':time.perf_counter()-t,'scope':'Independent reconstruction of native RNA results, not biological replication or pretraining-isolation certification','model_fit_accounting_note':'Saved model_fits=30 counts 18 vector selection+6 scalar+6 efficiency; six additional isolation-check solves are executed and must be included if reporting all solver fits (36).'}
(O/'world_independent_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))



