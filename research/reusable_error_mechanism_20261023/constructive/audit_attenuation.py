import json
import math
from pathlib import Path
import numpy as np

p=Path('D:/MAESTRO/log/20261023/reusable_error_mechanism')
s=np.load(p.parent/'mixed_feedback_estimator/STATE_BY_GEM.npz',allow_pickle=False)
o=np.load(p/'OVERLAP_ARRAYS.npz',allow_pickle=False)
a=np.load(p/'ATTENUATION_ARRAYS.npz',allow_pickle=False)
j=json.loads((p/'ATTENUATION_RESULT.json').read_text(encoding='utf-8'))
lut={(str(n),str(g)):v for n,g,v in zip(s['group_names'],s['gems'],s['mean_log1pCP10K'])}
checks={};rows=[]
def error(k,x,y):checks[k]=float(np.max(np.abs(np.asarray(x)-np.asarray(y))))
def fit(x,y):
    norm=math.fsum(float(t)**2 for t in x.ravel())
    dot=math.fsum(float(t)*float(v) for t,v in zip(x.ravel(),y.ravel()))
    return max(0.,min(1.,dot/norm)) if norm else 0.
def loss(x,y):return math.fsum((float(t)-float(v))**2 for t,v in zip(x.ravel(),y.ravel()))/x.size
assert np.array_equal(a['pairs'],o['pairs']) and np.array_equal(a['folds'],o['folds'])
for d,gems in [('A_to_B','1234'),('B_to_A','5678')]:
    gs=[]
    for pair in o['pairs']:
        x,y=str(pair).split('|')
        gs.append(np.mean([2*lut[('CONTROL',gem)]-lut[(x,gem)]-lut[(y,gem)] for gem in gems],axis=0))
    g=np.array(gs);r=o[d+'__truth'];pred=np.zeros_like(r)
    error(d+'_g',g,a[d+'__g'])
    rep=next(z for z in j['directions'] if z['direction']==d)
    bs=[]
    for f in range(5):
        tr=o['folds']!=f;te=~tr
        beta=fit(g[tr],r[tr]);bs.append(beta);pred[te]=g[te]*beta
        fr=next(z for z in rep['folds'] if z['fold']==f)
        error(d+'_beta'+str(f),beta,fr['beta'])
        error(d+'_fold'+str(f),loss(r[te],pred[te]),fr['MSE'])
    error(d+'_prediction',pred,a[d+'__prediction'])
    mse=loss(r,pred);overlap=loss(r,o[d+'__prediction']);direct=loss(r,o[d+'__direct'])
    error(d+'_mse',mse,rep['attenuation_MSE']);error(d+'_overlap',overlap,rep['overlap_MSE']);error(d+'_direct',direct,rep['direct_MSE'])
    b=fit(g,r);error(d+'_oracle_beta',b,rep['oracle_beta']);error(d+'_oracle_mse',loss(r,b*g),rep['in_sample_scalar_oracle_MSE'])
    assert (overlap<mse)==rep['overlap_strictly_better']
    rows.append({'direction':d,'betas':bs,'attenuation_mse':mse,'overlap_mse':overlap,'relative_error_reduction_vs_overlap_percent':100*(overlap-mse)/overlap,'overlap_specific_gate':overlap<mse})
assert not all(z['overlap_specific_gate'] for z in rows)
result={'status':'PASS' if max(checks.values())<1e-12 else 'FAIL','max_abs_error':max(checks.values()),'checks':checks,'directions':rows,'decision':'STOP_OVERLAP_SPECIFIC_ADVANTAGE','scope':'Independent saved-state g/scalarLS/OOF/oracle audit; no root implementation import, no raw biological extraction'}
(p/'constructive/ATTENUATION_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
