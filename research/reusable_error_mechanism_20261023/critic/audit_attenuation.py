"""Independent control-array audit; root code is never imported."""
import hashlib
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[3]
folder=root/'log/20261023/reusable_error_mechanism'
freeze=json.loads((folder/'ATTENUATION_FREEZE.json').read_text())
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
z=np.load(folder/'ATTENUATION_ARRAYS.npz')
o=np.load(folder/'OVERLAP_ARRAYS.npz')
s=np.load(root/'log/20261023/mixed_feedback_estimator/STATE_BY_GEM.npz')
r=json.loads((folder/'ATTENUATION_RESULT.json').read_text())
assert np.array_equal(z['pairs'],o['pairs']) and np.array_equal(z['folds'],o['folds'])
lookup={(str(n),str(g)):v for n,g,v in zip(s['group_names'],s['gems'],s['mean_log1pCP10K'])}
records=[]
for item,gems in zip(r['directions'],[('1','2','3','4'),('5','6','7','8')]):
    d=item['direction']
    g=[]
    for pair in z['pairs']:
        a,b=str(pair).split('|')
        g.append(-np.mean([lookup[a,t]-lookup['CONTROL',t]+lookup[b,t]-lookup['CONTROL',t] for t in gems],axis=0))
    g=np.array(g)
    gd=float(np.max(abs(g-z[d+'__g'])))
    assert gd<1e-14
    truth=o[d+'__truth']
    pred=np.zeros_like(truth)
    betas=[]
    for k in range(5):
        train,test=z['folds']!=k,z['folds']==k
        beta=float(np.clip(np.sum(g[train]*truth[train])/np.sum(g[train]**2),0,1))
        pred[test]=beta*g[test]
        row=item['folds'][k]
        assert abs(beta-row['beta'])<1e-14
        assert abs(float(np.mean((pred[test]-truth[test])**2))-row['MSE'])<1e-14
        assert abs(float(np.mean((o[d+'__prediction'][test]-truth[test])**2))-row['overlap_MSE'])<1e-14
        betas.append(beta)
    pd=float(np.max(abs(pred-z[d+'__prediction'])))
    assert pd<1e-14
    beta_oracle=float(np.clip(np.sum(g*truth)/np.sum(g*g),0,1))
    mse=float(np.mean((pred-truth)**2))
    oracle_mse=float(np.mean((beta_oracle*g-truth)**2))
    assert abs(beta_oracle-item['oracle_beta'])<1e-14
    assert abs(oracle_mse-item['in_sample_scalar_oracle_MSE'])<1e-14
    assert abs(mse-item['attenuation_MSE'])<1e-14
    assert mse<item['overlap_MSE']<item['direct_MSE']
    records.append({'direction':d,'feature_max_abs_difference':gd,'prediction_max_abs_difference':pd,
                    'betas':betas,'oracle_beta':beta_oracle,'MSE':mse,
                    'relative_improvement_over_overlap':1-mse/item['overlap_MSE']})
assert r['fit_calls']==12
out={'result':'PASS','freeze_files_checked':len(freeze['files']),'coefficients_checked':10,'oracle_coefficients_checked':2,
     'fit_count_arithmetic':12,'directions':records,
     'scope':'Independent saved numerical reconstruction; parent scalar summaries known before audit, peer audit files unread.'}
(folder/'critic/CONTROL_AUDIT.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
