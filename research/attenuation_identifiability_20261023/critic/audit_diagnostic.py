"""Independent saved-source reconstruction. Never imports root code."""
import hashlib
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[3]
folder=root/'log/20261023/attenuation_identifiability'
freeze=json.loads((folder/'FREEZE.json').read_text())
bad=[p for p,h in freeze['files'].items() if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
assert not bad
state=np.load(root/'log/20261023/mixed_feedback_estimator/STATE_BY_GEM.npz')
old=np.load(root/'log/20261023/reusable_error_mechanism/OVERLAP_ARRAYS.npz')
atten=np.load(root/'log/20261023/reusable_error_mechanism/ATTENUATION_ARRAYS.npz')
saved=np.load(folder/'DECOMPOSITION.npz')
result=json.loads((folder/'RESULT.json').read_text())
assert np.array_equal(saved['pairs'],old['pairs']) and np.array_equal(saved['genes'],state['genes'])
m=state['mean_CP10K']; ell=state['mean_log1pCP10K']
assert np.isfinite(m).all() and np.isfinite(ell).all()
assert (m>=0).all() and (m<=10000).all() and (m.sum(axis=1)<=10000).all()
L=np.log1p(m); J=L-ell
assert float(J.min())==result['group_J_min']
index={(str(n),str(g)):i for i,(n,g) in enumerate(zip(state['group_names'],state['gems']))}
rows={k:[] for k in ['ell','logmean','jensen','normalized_mean_cf']}
for pair in saved['pairs']:
    a,b=str(pair).split('|')
    current={k:[] for k in rows}
    for gem in map(str,range(1,9)):
        p,ia,ib,c=[index[n,gem] for n in [str(pair),a,b,'CONTROL']]
        for key,arr in [('ell',ell),('logmean',L),('jensen',J)]:
            current[key].append(arr[p]-arr[ia]-arr[ib]+arr[c])
        current['normalized_mean_cf'].append(m[ia]+m[ib]-m[c])
    for key in rows:
        rows[key].append(current[key])
rows={k:np.array(v) for k,v in rows.items()}
errors={k:float(np.max(abs(v-saved[k]))) for k,v in rows.items()}
assert max(errors.values())<1e-12
identity=float(np.max(abs(rows['ell']-rows['logmean']+rows['jensen'])))
assert abs(identity-result['per_gem_identity_max_abs'])<1e-12
cf=rows['normalized_mean_cf']
domain={'coordinates':int(cf.size),'pair_gems':int(cf.shape[0]*cf.shape[1]),
        'negative':int(np.sum(cf<0)),'log_math_invalid_le_minus_one':int(np.sum(cf<=-1)),
        'above_10000':int(np.sum(cf>10000)),
        'selected_sum_above_10000':int(np.sum(cf.sum(axis=2)>10000)),
        'pair_gems_with_any_bad_coordinate':int(np.sum(np.any((cf<0)|(cf>10000),axis=2))),
        'minimum':float(cf.min()),'maximum':float(cf.max())}
for k,v in domain.items():
    assert abs(v-result['normalized_mean_additive_domain'][k])<1e-12
directions=[]
for item,sl in zip(result['directions'],[slice(4,8),slice(0,4)]):
    d=item['direction']; g=atten[d+'__g']
    assert np.array_equal(g,saved[d+'__g'])
    r,l,j=[rows[k][:,sl,:].mean(axis=1) for k in ['ell','logmean','jensen']]
    assert np.max(abs(r-old[d+'__truth']))<1e-12
    den=float(np.sum(g*g)); nums=[float(np.sum(g*x)) for x in [r,l,j]]
    assert den>0
    projections=[v/den for v in nums]
    sp=item['signed_projection']
    for x,y in zip(projections,[sp['observed'],sp['logmean'],sp['mixed_J']]): assert abs(x-y)<1e-12
    assert max(abs(x-y) for x,y in zip(nums,sp['signed_numerators']))<1e-12
    assert abs(den-sp['denominator'])<1e-12
    energies=[float(np.mean(r*r)),float(np.mean(l*l)),float(np.mean(j*j)),float(-2*np.mean(l*j))]
    for x,y in zip(energies,[item['energy'][k] for k in ['mean_r2','mean_logmean2','mean_jensen2','minus_twice_cross']]): assert abs(x-y)<1e-12
    assert abs(energies[0]-sum(energies[1:]))<1e-12
    directions.append({'direction':d,'numerators':nums,'denominator':den,'unclipped_projections':projections,
                       'energy_terms':energies,'energy_identity_abs':abs(energies[0]-sum(energies[1:]))})
# Independently reconstruct the declared two-gene mean-composition example.
c=np.array([1000.,9000.]); a=np.array([3000.,7000.]); b=a.copy()
g=-2*(np.log1p(a)-np.log1p(c))
for item,dcells in zip(result['synthetic_constructed'],[np.array([[5000.,5000.]]),np.array([[1000.,9000.],[9000.,1000.]])]):
    mixed=dcells.mean(axis=0)-a-b+c
    logmixed=np.log1p(dcells).mean(axis=0)-np.log1p(a)-np.log1p(b)+np.log1p(c)
    q=float(g@logmixed/(g@g))
    assert np.max(abs(mixed-np.array(item['normalized_mean_CP_mixed'])))<1e-12
    assert np.max(abs(logmixed-np.array(item['mean_log_mixed'])))<1e-12
    assert abs(q-item['descriptive_projection'])<1e-12
assert result['model_fit_calls']==0
out={'result':'PASS','freeze_files_checked':len(freeze['files']),'freeze_mismatches':bad,
     'array_reconstruction_max_abs':errors,'per_gem_identity_max_abs':identity,
     'domain':domain,'directions':directions,'synthetic_constructed_check':'PASS',
     'scope':'Saved-source reconstruction, parent scalar summaries known; no peer result audits/root imports/new fits/raw matrix/function reads.'}
(folder/'critic/RESULT_AUDIT.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
