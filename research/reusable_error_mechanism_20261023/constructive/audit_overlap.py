"""Independent saved-state reconstruction; never imports experiment implementation."""
import json
import math
from pathlib import Path
import numpy as np

root=Path('D:/MAESTRO/log/20261023')
p=root/'reusable_error_mechanism'
s=np.load(root/'mixed_feedback_estimator/STATE_BY_GEM.npz',allow_pickle=False)
old=np.load(root/'mixed_feedback_estimator/OOF_STATE.npz',allow_pickle=False)
new=np.load(p/'OVERLAP_ARRAYS.npz',allow_pickle=False)
reported=json.loads((p/'OVERLAP_RESULT.json').read_text(encoding='utf-8'))
lookup={(str(n),str(g)):v for n,g,v in zip(s['group_names'],s['gems'],s['mean_log1pCP10K'])}
errs={}
def delta(name,a,b):
    errs[name]=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
def fit(x,y):
    # Explicit scalar least squares using independently summed normal-equation terms.
    xx=math.fsum(float(v)*float(v) for v in x.ravel())
    xy=math.fsum(float(a)*float(b) for a,b in zip(x.ravel(),y.ravel()))
    return min(1.,max(0.,xy/xx)) if xx else 0.
def mse(x,y):
    return math.fsum((float(a)-float(b))**2 for a,b in zip(x.ravel(),y.ravel()))/x.size
assert np.array_equal(new['pairs'],old['pairs'])
assert np.array_equal(new['folds'],old['folds'])
rows=[]
for direction,ig,tg in [('A_to_B','1234','5678'),('B_to_A','5678','1234')]:
    hs=[];rs=[]
    for pair in old['pairs']:
        a,b=str(pair).split('|')
        hg=[];rg=[]
        for g in ig:
            aa=lookup[(a,g)]-lookup[('CONTROL',g)]
            bb=lookup[(b,g)]-lookup[('CONTROL',g)]
            # Branch expression computes the piecewise min restriction independently.
            hh=np.zeros(len(aa))
            for j,(av,bv) in enumerate(zip(aa,bb)):
                if av>0 and bv>0: hh[j]=-min(av,bv)
                elif av<0 and bv<0: hh[j]=min(-av,-bv)
            hg.append(hh)
        for g in tg:
            rg.append(lookup[(str(pair),g)]-lookup[(a,g)]-lookup[(b,g)]+lookup[('CONTROL',g)])
        hs.append(np.mean(hg,axis=0));rs.append(np.mean(rg,axis=0))
    h=np.array(hs);r=np.array(rs)
    delta(direction+'_h',h,new[direction+'__h'])
    delta(direction+'_r_new',r,new[direction+'__truth'])
    delta(direction+'_r_old',r,old['mean_log1pCP10K__'+direction+'__truth'])
    delta(direction+'_direct',new[direction+'__direct'],old['mean_log1pCP10K__'+direction+'__linear_ridge'])
    predictions=np.zeros_like(r);thetas=[]
    rep=next(x for x in reported['directions'] if x['direction']==direction)
    for f in range(5):
        tr=old['folds']!=f;te=~tr
        theta=fit(h[tr],r[tr]);thetas.append(theta);predictions[te]=theta*h[te]
        rr=next(x for x in rep['folds'] if x['fold']==f)
        delta(direction+'_theta'+str(f),theta,rr['theta'])
        delta(direction+'_fold'+str(f),mse(r[te],predictions[te]),rr['MSE'])
    delta(direction+'_prediction',predictions,new[direction+'__prediction'])
    for name in ['additive','linear_ridge','q_ridge','bilinear_ridge','mean']:
        pred=old['mean_log1pCP10K__'+direction+'__'+name]
        delta(direction+'_score_'+name,mse(r,pred),rep['scores'][name])
    score=mse(r,predictions);direct=rep['scores']['linear_ridge'];add=rep['scores']['additive']
    delta(direction+'_score_overlap',score,rep['scores']['bounded_overlap'])
    oracle=fit(h,r)
    delta(direction+'_oracle_theta',oracle,rep['theta_oracle'])
    delta(direction+'_oracle_mse',mse(r,oracle*h),rep['scores']['in_sample_global_scalar_oracle'])
    passed=score<direct and score<add
    assert passed==rep['strict_direct_and_additive_pass']
    rows.append({'direction':direction,'thetas':thetas,'overlap_mse':score,'relative_direct_improvement_percent':100*(direct-score)/direct,'necessary_gate':passed})
result={'status':'PASS' if max(errs.values())<1e-12 else 'FAIL','max_abs_error':max(errs.values()),'checks':errs,'directions':rows,'scope':'Independent saved-state/h/r/10theta/OOF/oracle reconstruction; no raw extraction, biological replication or new fitting choice'}
(p/'constructive/RESULT_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
