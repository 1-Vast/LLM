import json
import math
from pathlib import Path
import numpy as np

p=Path('D:/MAESTRO/log/20261023/attenuation_identifiability')
s=np.load(p.parent/'mixed_feedback_estimator/STATE_BY_GEM.npz',allow_pickle=False)
d=np.load(p/'DECOMPOSITION.npz',allow_pickle=False)
j=json.loads((p/'RESULT.json').read_text(encoding='utf-8'))
old=np.load(p.parent/'mixed_feedback_estimator/OOF_STATE.npz',allow_pickle=False)
lm={};ell={}
for n,g,m,l in zip(s['group_names'],s['gems'],s['mean_CP10K'],s['mean_log1pCP10K']):
    lm[(str(n),str(g))]=m;ell[(str(n),str(g))]=l
assert np.array_equal(d['pairs'],old['pairs']) and np.array_equal(d['genes'],s['genes'])
M=[];R=[];L=[];J=[]
for pair in d['pairs']:
    a,b=str(pair).split('|');mc=[];rr=[];ll=[];jj=[]
    for g in '12345678':
        ks=[(str(pair),g),(a,g),(b,g),('CONTROL',g)]
        signs=[1,-1,-1,1]
        ts=[np.log1p(lm[k]) for k in ks]
        js=[t-ell[k] for t,k in zip(ts,ks)]
        mc.append(lm[(a,g)]+lm[(b,g)]-lm[('CONTROL',g)])
        rr.append(sum(q*ell[k] for q,k in zip(signs,ks)))
        ll.append(sum(q*t for q,t in zip(signs,ts)))
        jj.append(sum(q*t for q,t in zip(signs,js)))
    M.append(mc);R.append(rr);L.append(ll);J.append(jj)
M,R,L,J=map(np.array,[M,R,L,J]);errors={}
def check(k,a,b):errors[k]=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
for k,v in [('normalized_mean_cf',M),('ell',R),('logmean',L),('jensen',J)]:check(k,v,d[k])
check('identity',R,L-J)
stats={'coordinates':M.size,'pair_gems':M.shape[0]*M.shape[1],'negative':int(np.sum(M<0)),
       'log_math_invalid_le_minus_one':int(np.sum(M<=-1)),'above_10000':int(np.sum(M>10000)),
       'selected_sum_above_10000':int(np.sum(M.sum(axis=2)>10000)),
       'pair_gems_with_any_bad_coordinate':int(np.sum(np.any((M<0)|(M>10000),axis=2))),
       'minimum':float(M.min()),'maximum':float(M.max())}
for k,v in stats.items():check('domain_'+k,v,j['normalized_mean_additive_domain'][k])
rows=[]
def dot(a,b):return math.fsum(float(x)*float(y) for x,y in zip(a.ravel(),b.ravel()))
for name,ig,tg in [('A_to_B','1234',slice(4,8)),('B_to_A','5678',slice(0,4))]:
    g=[]
    for pair in d['pairs']:
        a,b=str(pair).split('|')
        g.append(np.mean([2*ell[('CONTROL',i)]-ell[(a,i)]-ell[(b,i)] for i in ig],axis=0))
    g=np.array(g);check(name+'_g',g,d[name+'__g'])
    rr=R[:,tg].mean(axis=1);ll=L[:,tg].mean(axis=1);jj=J[:,tg].mean(axis=1)
    check(name+'_old_truth',rr,old['mean_log1pCP10K__'+name+'__truth'])
    rep=next(x for x in j['directions'] if x['direction']==name)
    norm=dot(g,g);numerators=[dot(g,v) for v in [rr,ll,jj]];proj=[x/norm for x in numerators]
    for key,v in zip(['observed','logmean','mixed_J'],proj):check(name+'_proj_'+key,v,rep['signed_projection'][key])
    check(name+'_numerators',numerators,rep['signed_projection']['signed_numerators']);check(name+'_denominator',norm,rep['signed_projection']['denominator'])
    es=[dot(rr,rr)/rr.size,dot(ll,ll)/ll.size,dot(jj,jj)/jj.size,-2*dot(ll,jj)/jj.size]
    for key,v in zip(['mean_r2','mean_logmean2','mean_jensen2','minus_twice_cross'],es):check(name+'_energy_'+key,v,rep['energy'][key])
    rows.append({'direction':name,'signed_projection':proj,'projection_identity_abs':abs(proj[0]-proj[1]+proj[2]),'energy_identity_abs':abs(es[0]-sum(es[1:]))})
baseline=np.array([1000.,9000.]);single=np.array([3000.,7000.]);g=-2*(np.log1p(single)-np.log1p(baseline))
for rep,cells in zip(j['synthetic_constructed'],[np.array([[5000.,5000.]]),np.array([[1000.,9000.],[9000.,1000.]])]):
    mc=cells.mean(axis=0)-2*single+baseline
    rl=np.log1p(cells).mean(axis=0)-2*np.log1p(single)+np.log1p(baseline)
    check(rep['name']+'_toy_m',mc,rep['normalized_mean_CP_mixed']);check(rep['name']+'_toy_ell',rl,rep['mean_log_mixed']);check(rep['name']+'_toy_projection',dot(g,rl)/dot(g,g),rep['descriptive_projection'])
out={'status':'PASS' if max(errors.values())<1e-12 else 'FAIL','max_abs_error':max(errors.values()),'checks':errors,'domain':stats,'directions':rows,'scope':'Independent complete saved aggregate reconstruction and toy arithmetic; no root code import, model fitting or raw extraction'}
(p/'constructive/RESULT_AUDIT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
