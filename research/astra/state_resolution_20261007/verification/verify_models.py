"""Independent matched additive-head reconstruction; original experiment not imported."""
from pathlib import Path
import json,hashlib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
B=Path(__file__).resolve().parents[1];OLD=B.parent/'state_dual_core_20261007';M=B/'models_run2';O=B/'verification';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();frame=pd.read_csv(OLD/'world/conditions.csv');rep=np.load(B/'world/representations.npz');old=np.load(OLD/'model_run1/kernels.npz');orig=np.load(OLD/'model_run1/predictions.npz');v=np.load(M/'vector_predictions.npz');sc=np.load(M/'scalar_predictions.npz');vm=read(M/'vector_metrics.json');sm=read(M/'scalar_metrics.json');obs=pd.read_csv(B/'observations/bias_corrected_observations.csv');train=np.flatnonzero(frame.split.eq('train'));dev=np.flatnonzero(frame.split.eq('development'));ev=np.flatnonzero(frame.split.eq('evaluation'));y=v['observed']
assert sha(B/'PROTOCOL.json')==read(B/'PROTOCOL_FREEZE.json')['sha256']
for name,h in read(M/'manifest.json').items():assert sha(M/name)==h
np.testing.assert_array_equal(v['M1'],orig['M1'])
def linear(x,t):
 x=np.asarray(x,float);x=x-x[t].mean(0);return x@x.T/max(float(np.mean(np.sum(x[t]**2,axis=1))),1e-12)
def predict(K,t,y):
 mu=y[t].mean(0);return K[:,t]@np.linalg.solve(K[np.ix_(t,t)]+.1*np.eye(len(t)),y[t]-mu)+mu
def groups(a,b,sub,ix):return pd.DataFrame({'group':sub.iloc[ix].chemical_group.to_numpy(),'e':np.mean((a[ix]-b[ix])**2,axis=1) if a.ndim==2 else (a[ix]-b[ix])**2}).groupby('group').e.mean().to_numpy()
def contrast(a,b):
 d=a-b;rng=np.random.default_rng(1907);return {'difference':float(d.mean()),'descriptive_95':np.quantile(d[rng.integers(len(d),size=(2000,len(d)))].mean(1),[.025,.975]).tolist(),'groups':len(d)}
base=old['M1'];basal=linear(rep['basal_mean'][0],train);adds={'matched_nonSTATE':basal,'raw32':linear(rep['raw_delta'][0],train),'raw256':linear(rep['raw_delta'][1],train),'paired32':linear(rep['counterfactual_delta'][0],train),'paired256':linear(rep['counterfactual_delta'][1],train),'permuted256':linear(rep['counterfactual_delta'][1][old['permutation']],train)}
with threadpool_limits(limits=2):
 for name,A in adds.items():
  trials=[]
  for gamma in [0.,.25,1.]:
   p=predict(base+gamma*A,train,y);trials.append((float(np.mean((p[dev]-y[dev])**2)),gamma,p))
  _,g,p=min(trials,key=lambda q:(q[0],q[1]));assert g==vm['selection'][name]['gamma'];np.testing.assert_allclose(p,v[name],atol=1e-12)
  np.testing.assert_allclose(np.mean(groups(y,p,frame,ev)),vm['methods'][name]['evaluation_group_mse'],rtol=1e-12)
 rebuilt_primary={name:contrast(groups(y,v['paired256'],frame,ev),groups(y,v[name],frame,ev)) for name in ['matched_nonSTATE','basal_only']}
 for name,c in rebuilt_primary.items():np.testing.assert_allclose(c['descriptive_95'],vm['primary'][name]['descriptive_95'],atol=1e-15)
 scalar_checks={}
 for role in ['full','technical_validation','screen']:
  subset=obs[obs.role==role].reset_index(drop=True);ix=np.array([frame.index[frame.condition_id==x][0] for x in subset.condition_id]);t=np.flatnonzero(subset.split.eq('train'));d=np.flatnonzero(subset.split.eq('development'));e=np.flatnonzero(subset.split.eq('evaluation'));target=subset.signed_effect.to_numpy();np.testing.assert_allclose(target,sc[role+'__observed'],atol=1e-15)
  for name,A in [('matched_nonSTATE',basal),('paired256',adds['paired256'])]:
   g=sm[role]['selection'][name]['gamma'];p=predict(base[np.ix_(ix,ix)]+g*A[np.ix_(ix,ix)],t,target);np.testing.assert_allclose(p,sc[role+'__'+name],atol=1e-12)
   if role=='screen':assert g==sm['technical_validation']['selection'][name]['gamma']
  ref=sm[role]['reference_selected_on_development'];new=contrast(groups(target,sc[role+'__paired256'],subset,e),groups(target,sc[role+'__'+ref],subset,e));scalar_checks[role]={'reference':ref,'grouped_contrast':new}
for artifact in ['vector_predictions.npz','scalar_predictions.npz']:
 a=np.load(B/'models_run1'/artifact);b=np.load(M/artifact);assert set(a.files)==set(b.files);assert all(np.array_equal(a[k],b[k]) for k in a.files)
receipt={'status':'PASS_CANONICAL_RUN2_WITH_PRESERVED_RUN1_ERRATUM','run1_run2_predictions_bitwise_identical':True,'vector_primary':rebuilt_primary,'primary_success':vm['success'],'primary_paired256_gamma':vm['selection']['paired256']['gamma'],'STATE_addition_selected_for_primary':vm['selection']['paired256']['gamma']!=0,'zero_gamma_bitwise_M1':bool(np.array_equal(v['paired256'],orig['M1'])),'scalar_reconstructed':scalar_checks,'matched_training_and_development_grid_rebuilt':True,'screen_gamma_shared_with_validation':True,'scope':'Independent model arithmetic. Calibration/source dependence and noisy corrected signed outcomes remain limitations.'};(O/'models_independent_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
original_scalar=read(B/'models_run1/scalar_metrics.json')
err={'status':'CORRECTION_PRESERVING_ORIGINAL','artifact':'models_run1/scalar_metrics.json:full:STATE_minus_reference_mse','issue':'Original interval resampled36dose rows rather than12chemical groups; point estimate unchanged with balanced3doses/group','corrected':scalar_checks['full']['grouped_contrast'],'old':original_scalar['full']['STATE_minus_reference_mse'],'no_model_or_endpoint_reselection':True};(O/'full_scalar_group_uncertainty_erratum.json').write_text(json.dumps(err,indent=2)+'\n');print(json.dumps(receipt,indent=2))
