import os, json, hashlib, time, platform, subprocess
os.environ.update({"OMP_NUM_THREADS":"3","MKL_NUM_THREADS":"3","OPENBLAS_NUM_THREADS":"3","NUMEXPR_NUM_THREADS":"3"})
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'VERIFY_FULL_61'; OUT.mkdir(exist_ok=True)
DATA=Path(r'D:/MAESTRO/data/processed/generic_axis_transfer_20261031/dev_pool.npz')
SEED=20261101; KLIST=[2,5,10,20,50,100]; METHODS=['raw_k5','raw_k20','chemistry_k20','gat_d5_k20','global_residual_diagnostic','full_flat_residual_k20','gat_permuted_null']+[f'pca_residual_k{k}' for k in KLIST]+[f'random_residual_k{k}' for k in KLIST]+['ridge_raw']

def folds_from_ik(ik, frozen_fold=None):
    f=[]
    for i,x in enumerate(ik):
        s=str(x)
        if s: f.append(int(hashlib.sha256(s.encode()).hexdigest(),16)%5)
        elif frozen_fold is not None: f.append(int(frozen_fold[i]))
        else: f.append(int(hashlib.sha256(f'missing-singleton-{i}'.encode()).hexdigest(),16)%5)
    return np.asarray(f,int)

def cosine_options(A,B):
    # A/B are n x options x genes, with an entire option either finite or missing.
    no=A.shape[1]; sims=np.zeros((A.shape[0],B.shape[0])); cnt=np.zeros_like(sims)
    for o in range(no):
        av=np.isfinite(A[:,o,0]); bv=np.isfinite(B[:,o,0]);
        if not av.any() or not bv.any(): continue
        aa=np.nan_to_num(A[av,o],nan=0.0); bb=np.nan_to_num(B[bv,o],nan=0.0)
        an=np.linalg.norm(aa,axis=1); bn=np.linalg.norm(bb,axis=1)
        ok=(an>0)[:,None] & (bn>0)[None,:]
        z=(aa@bb.T)/np.maximum(an[:,None]*bn[None,:],1e-12); z[~ok]=np.nan
        ix=np.where(av)[0][:,None]; jx=np.where(bv)[0][None,:];
        sims[np.ix_(np.where(av)[0],np.where(bv)[0])] += np.nan_to_num(z,nan=0.0)
        cnt[np.ix_(np.where(av)[0],np.where(bv)[0])] += np.isfinite(z)
    return np.divide(sims,cnt,out=np.full_like(sims,np.nan),where=cnt>0)

def flat_cos(A,B):
    aa=np.nan_to_num(A,nan=0.0); bb=np.nan_to_num(B,nan=0.0)
    # flattened residuals are zero for missing options; denominator is ordinary norm.
    an=np.linalg.norm(aa,axis=1); bn=np.linalg.norm(bb,axis=1)
    z=aa@bb.T/np.maximum(an[:,None]*bn[None,:],1e-12); z[(an[:,None]<=0)|(bn[None,:]<=0)]=np.nan
    return z

def cosine_matrix(A,B):
    an=np.linalg.norm(A,axis=1); bn=np.linalg.norm(B,axis=1)
    z=A@B.T/np.maximum(an[:,None]*bn[None,:],1e-12)
    z[(an[:,None]<=0)|(bn[None,:]<=0)]=np.nan
    return z

def weighted_knn(sim, Y, k, perm=None):
    n=sim.shape[0]; out=np.full((n,Y.shape[1]),np.nan)
    for i in range(n):
        s=sim[i]; finite=np.where(np.isfinite(s))[0];
        if not len(finite): continue
        # stable original order after descending similarity
        order=finite[np.argsort(-s[finite],kind='stable')[:min(k,len(finite))]]
        w=np.clip(s[order],0,None); w=w if np.any(w>0) else np.ones(len(order))
        yy=Y[order] if perm is None else perm[order]
        ok=np.isfinite(yy); den=(ok*w[:,None]).sum(0)
        out[i]=np.divide(np.nansum(np.where(ok,yy,0)*w[:,None],0),den,out=np.full(Y.shape[1],np.nan),where=den>1e-12)
    return out

def residualize(y,g):
    ok=np.isfinite(y)&np.isfinite(g)
    if ok.sum()<2:return np.full_like(y,np.nan)
    X=np.c_[np.ones(ok.sum()),g[ok]]
    try: b=np.linalg.lstsq(X,y[ok],rcond=None)[0]
    except: return np.full_like(y,np.nan)
    r=np.full_like(y,np.nan); r[ok]=y[ok]-X@b; return r

def pearson(a,b,min_n=3):
    ok=np.isfinite(a)&np.isfinite(b)
    if ok.sum()<min_n:return np.nan
    aa=a[ok];bb=b[ok]
    if aa.std()<1e-12 or bb.std()<1e-12:return np.nan
    return float(np.corrcoef(aa,bb)[0,1])

def metrics(pred,obs,g,active,neigh,rawneigh):
    pr=residualize(pred,g); ob=residualize(obs,g); ok=np.isfinite(pr)&np.isfinite(ob)
    hit=reg=np.nan
    if ok.sum()>=40 and pr[ok].std()>=1e-12 and ob[ok].std()>=1e-12:
        m=max(1,int(round(.1*ok.sum()))); ids=np.where(ok)[0]; order=ids[np.argsort(-pr[ids],kind='stable')[:m]]; sens=-ob
        # response hit threshold follows exposed active rule on observed LFC
        hit=float(np.mean(obs[order]<=-1))
        oracle=np.sort(sens[ids])[::-1][:m].mean(); reg=float(oracle-sens[order].mean())
    rawr=pearson(pred,obs); mae=float(np.nanmean(np.abs(pred-obs))) if np.any(np.isfinite(pred)&np.isfinite(obs)) else np.nan
    sr=pearson(pr,ob)
    jo=np.nan
    if neigh is not None and rawneigh is not None: jo=len(set(neigh)&set(rawneigh))/len(set(neigh)|set(rawneigh))
    return [hit, (1-hit if np.isfinite(hit) else np.nan), reg,sr,rawr,mae,jo]

def main():
    t0=time.time(); z=np.load(DATA); sig=z['signature'].astype(np.float64); Y=z['profile'].astype(np.float64); fp=z['fingerprint']; drug=z['drug']; line=z['line']; ik=z['ik14']; n,L=Y.shape
    frozen=np.load(ROOT/'RUN/predictions.npz',allow_pickle=True)['fold']; folds=folds_from_ik(ik,frozen)
    active=np.nanmean(np.where(np.isfinite(Y),Y<=-1,False),axis=1)>=.05
    pred={m:np.full((n,L),np.nan) for m in METHODS}; neighs={m:[None]*n for m in METHODS}; rawneigh=[None]*n
    rng=np.random.default_rng(SEED); fold_records=[]
    for fold in range(5):
        tic=time.time(); qi=np.where(folds==fold)[0]; ri=np.where(folds!=fold)[0]; sr=sig[ri]; sq=sig[qi]; yr=Y[ri]; yq=Y[qi]
        g=np.nanmean(yr,axis=0)
        means=np.nanmean(sr,axis=0); rr=sr-means[None,:,:]; rq=sq-means[None,:,:]
        rr_flat=np.nan_to_num(rr,nan=0).reshape(len(ri),-1); rq_flat=np.nan_to_num(rq,nan=0).reshape(len(qi),-1)
        rawsim=cosine_options(sq,sr); raw5=weighted_knn(rawsim,yr,5); raw20=weighted_knn(rawsim,yr,20)
        chem=np.zeros((len(qi),len(ri)))
        for a,i in enumerate(qi):
            inter=np.minimum(fp[i],fp[ri]).sum(1); union=np.maximum(fp[i],fp[ri]).sum(1); chem[a]=np.divide(inter,union,out=np.zeros_like(inter,dtype=float),where=union>0)
        chemp=weighted_knn(chem,yr,20)
        # PCA directions on reference-centred flattened states; remove D directions.
        pca5=PCA(n_components=100,svd_solver='randomized',iterated_power=3,n_oversamples=10,power_iteration_normalizer='QR',random_state=SEED+fold).fit(rr_flat)
        # remove only the first five fitted directions while retaining the PCA mean convention
        rr5=rr_flat-(pca5.mean_ + pca5.transform(rr_flat)[:,:5]@pca5.components_[:5]); rq5=rq_flat-(pca5.mean_ + pca5.transform(rq_flat)[:,:5]@pca5.components_[:5]); rr5o=rr5.reshape(len(ri),18,-1); rq5o=rq5.reshape(len(qi),18,-1)
        gsim=cosine_options(rq5o,rr5o); gat=weighted_knn(gsim,yr,20); full=weighted_knn(flat_cos(rq_flat,rr_flat),yr,20)
        permrng=np.random.default_rng(SEED+1000+fold); py=yr[permrng.permutation(len(yr))]; null=weighted_knn(gsim,py,20)
        # randomized projection: one 17604x100 Gaussian draw per fold, QR reduced.
        G=rng.normal(size=(rr_flat.shape[1],100)); Q,_=np.linalg.qr(G,mode='reduced');
        pcas={}; rands={}
        pca=pca5
        rc=pca.transform(rr_flat); qc=pca.transform(rq_flat)
        for k in KLIST: pcas[k]=weighted_knn(cosine_matrix(qc[:,:k],rc[:,:k]),yr,20); rands[k]=weighted_knn(cosine_matrix(rq_flat@Q[:,:k],rr_flat@Q[:,:k]),yr,20)
        # ridge with reference mean imputation, raw flattened signatures.
        rawflat=np.nan_to_num(sr,nan=0).reshape(len(ri),-1); qraw=np.nan_to_num(sq,nan=0).reshape(len(qi),-1); fmean=np.nanmean(np.where(np.isfinite(sr),sr,np.nan),axis=0).reshape(-1); rawflat=np.where(np.isfinite(sr.reshape(len(ri),-1)),sr.reshape(len(ri),-1),fmean); qraw=np.where(np.isfinite(sq.reshape(len(qi),-1)),sq.reshape(len(qi),-1),fmean); ymean=np.nanmean(yr,axis=0); yfit=np.where(np.isfinite(yr),yr,ymean); ridge=Ridge(alpha=100,solver='cholesky').fit(rawflat,yfit).predict(qraw)
        vals={'raw_k5':raw5,'raw_k20':raw20,'chemistry_k20':chemp,'gat_d5_k20':gat,'global_residual_diagnostic':gat,'full_flat_residual_k20':full,'gat_permuted_null':null,'ridge_raw':ridge}
        vals.update({f'pca_residual_k{k}':pcas[k] for k in KLIST}); vals.update({f'random_residual_k{k}':rands[k] for k in KLIST})
        for m,v in vals.items(): pred[m][qi]=v
        for a,idx in enumerate(qi):
            # neighbor lists for overlap diagnostics
            rawneigh[idx]=np.argsort(-np.nan_to_num(rawsim[a],nan=-np.inf),kind='stable')[:20].tolist()
            for m,sx,k in [('raw_k5',rawsim,5),('raw_k20',rawsim,20),('gat_d5_k20',gsim,20),('full_flat_residual_k20',flat_cos(rq_flat,rr_flat),20)]+[(f'pca_residual_k{k}',cosine_matrix(qc[:,:k],rc[:,:k]),20) for k in KLIST]+[(f'random_residual_k{k}',cosine_matrix(rq_flat@Q[:,:k],rr_flat@Q[:,:k]),20) for k in KLIST]+[('chemistry_k20',chem,20)]: neighs[m][idx]=np.argsort(-np.nan_to_num(sx[a],nan=-np.inf),kind='stable')[:k].tolist()
        fold_records.append({'fold':fold,'n_query':len(qi),'elapsed_seconds':time.time()-tic}); print(json.dumps(fold_records[-1]),flush=True)
    rows=[]
    for i in range(n):
        for m in METHODS:
            met=metrics(pred[m][i],Y[i],np.nanmean(Y[folds!=folds[i]],axis=0),active[i],neighs[m][i],rawneigh[i] if m not in ('raw_k20',) else rawneigh[i]); rows.append([i,drug[i],int(folds[i]),bool(active[i]),m,*met])
    df=pd.DataFrame(rows,columns=['query_index','drug','fold','active','method','hit_precision','miss_rate','regret','selective_r','raw_r','raw_mae','neighbor_overlap_vs_raw']); df.to_csv(OUT/'per_query_metrics.csv',index=False)
    np.savez_compressed(OUT/'predictions.npz',drug=drug,line=line,fold=folds,active=active,**pred)
    summaries={}
    for m in METHODS:
        summaries[m]={}
        for typ,mask in [('active',df.active),('all',np.ones(len(df),bool))]:
            x=df[(df.method==m)&mask]; summaries[m][typ]={c:(None if x[c].dropna().empty else float(x[c].mean())) for c in ['hit_precision','miss_rate','regret','selective_r','raw_r','raw_mae','neighbor_overlap_vs_raw']}
    result={'study':'task_sufficient_transfer_mvp_20261101','status':'exploratory_non_confirmatory','data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'n_compounds':n,'n_lines':L,'n_active':int(active.sum()),'n_folds':5,'methods':METHODS,'summaries':summaries,'fold_records':fold_records,'elapsed_seconds':time.time()-t0,'science_gate':'NON_CONFIRMATORY','model_budget_telemetry':None}
    (OUT/'RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    env={'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'scipy':__import__('scipy').__version__,'sklearn':__import__('sklearn').__version__,'pid':os.getpid(),'threads':'3'}; (OUT/'environment.json').write_text(json.dumps(env,indent=2),encoding='utf-8')
if __name__=='__main__': main()
