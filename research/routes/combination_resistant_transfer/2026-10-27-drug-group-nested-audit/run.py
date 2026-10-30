import hashlib,json,os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np,pandas as pd
from scipy.linalg import eigh
from scipy.stats import spearmanr
from sklearn.preprocessing import OneHotEncoder,StandardScaler
R=Path(r'D:\MAESTRO');O=R/'research/2026-10-27-drug-group-nested-audit';D=R/'data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv'
L=np.array([1.,10.,100.,1000.,10000.,100000.]);SEED=20261065

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def predict(g,tr,te,cols,y):
 enc=OneHotEncoder(handle_unknown='ignore',dtype=np.float64);x=enc.fit_transform(g.iloc[tr][cols]);v=enc.transform(g.iloc[te][cols]);sc=StandardScaler(with_mean=False);x=sc.fit_transform(x);v=sc.transform(v)
 mu=np.asarray(x.mean(axis=0)).ravel();ym=y[tr].mean();rhs=np.asarray(x.T@(y[tr]-ym)).ravel();gram=(x.T@x).toarray()-len(tr)*np.outer(mu,mu)
 val,q=eigh(gram,check_finite=False);val=np.maximum(val,0);w=q@((q.T@rhs)[:,None]/(val[:,None]+L[None,:]));return ym+np.asarray(v@w)-mu@w

def main():
 cols=['CELL_LINE_NAME','ANCHOR_NAME','LIBRARY_NAME','ANCHOR_PATHWAY','LIBRARY_PATHWAY','SYNERGY_DELTA_EMAX'];d=pd.read_csv(D,usecols=cols,low_memory=False)
 d['emax']=pd.to_numeric(d.SYNERGY_DELTA_EMAX,errors='coerce');d['cell']=d.CELL_LINE_NAME.astype(str);d['key']=d.cell+'|'+d.ANCHOR_NAME.astype(str)+' + '+d.LIBRARY_NAME.astype(str)
 g=d.groupby('key',as_index=False).agg(a=('ANCHOR_NAME','first'),b=('LIBRARY_NAME','first'),ap=('ANCHOR_PATHWAY','first'),lp=('LIBRARY_PATHWAY','first'),y=('emax','mean'))
 for c in ['a','b','ap','lp']:g[c]=g[c].astype(str).fillna('NA')
 g=g[np.isfinite(g.y)].reset_index(drop=True);y=g.y.to_numpy();A=g.a.to_numpy();B=g.b.to_numpy();drugs=sorted(set(A)|set(B));rng=np.random.default_rng(SEED)
 conflicts={c:int(g.groupby(a)[c].nunique().gt(1).sum()) for a,c in [('a','ap'),('b','lp')]};rows=[];audits=[];outer=[]
 for rep in range(8):
  ds=drugs[:];rng.shuffle(ds);held=set(ds[:max(3,round(.2*len(ds)))]);am=np.isin(A,list(held));bm=np.isin(B,list(held));tr=np.flatnonzero(~am&~bm);te=np.flatnonzero(am&bm);td=set(A[tr])|set(B[tr])
  assert td.isdisjoint(held) and (set(A[te])|set(B[te])).issubset(held)
  if len(te)<150:raise RuntimeError(f'outer {rep} small')
  outer.append({'rep':rep,'held':sorted(held),'n_train':len(tr),'n_test':len(te)});chunks=np.array_split(np.random.default_rng(SEED+rep).permutation(len(tr)),3)
  folds={'row':[(tr[np.setdiff1d(np.arange(len(tr)),v)],tr[v]) for v in chunks]};gd=[];ir=np.random.default_rng(SEED+10000+rep)
  for k in range(3):
   dl=sorted(td);ir.shuffle(dl);ih=set(dl[:max(3,round(.3*len(dl)))]);ia=np.isin(A[tr],list(ih));ib=np.isin(B[tr],list(ih));it=tr[~ia&~ib];iv=tr[ia&ib];overlap=(set(A[it])|set(B[it]))&(set(A[iv])|set(B[iv]));assert not overlap
   if len(iv)<20 or len(it)<100:raise RuntimeError(f'inner {rep} {k} too small')
   gd.append((it,iv));audits.append({'rep':rep,'fold':k,'held':sorted(ih),'n_train':len(it),'n_valid':len(iv),'drug_intersection':len(overlap)})
  folds['drug']=gd;ua=float(np.mean(~g.iloc[te].ap.isin(set(g.iloc[tr].ap))));ub=float(np.mean(~g.iloc[te].lp.isin(set(g.iloc[tr].lp))))
  for arm,features in [('identity',['a','b']),('identity_path',['a','b','ap','lp'])]:
   for method,fs in folds.items():
    scores=np.mean([np.mean((predict(g,it,iv,features,y)-y[iv,None])**2,axis=0) for it,iv in fs],axis=0);ties=np.flatnonzero(np.isclose(scores,scores.min(),rtol=1e-10,atol=1e-12));best=int(ties[0]);p=predict(g,tr,te,features,y)[:,best];rho=None if np.std(p)<1e-10 else float(spearmanr(y[te],p).statistic)
    rows.append({'rep':rep,'method':method,'arm':arm,'n_train':len(tr),'n_test':len(te),'unknown_ap_fraction':ua,'unknown_lp_fraction':ub,'lambda':float(L[best]),'lambda_ties':len(ties),'lambda_max':bool(best==len(L)-1),'mse':float(np.mean((y[te]-p)**2)),'rho':rho,'prediction_sd':float(np.std(p))})
  print('completed rep',rep,flush=True)
 r=pd.DataFrame(rows);r.to_csv(O/'results.csv',index=False);(O/'splits.json').write_text(json.dumps({'outer':outer,'inner':audits},indent=2),encoding='utf-8')
 out={'dataset_sha256':sha(D),'protocol_sha256':sha(O/'PROTOCOL.md'),'script_sha256':sha(Path(__file__)),'splits_sha256':sha(O/'splits.json'),'seed':SEED,'reps':8,'mapping_conflicts_by_role':conflicts,'groups':{}}
 for (method,arm),sub in r.groupby(['method','arm']):out['groups'][method+'_'+arm]={'mean_mse':float(sub.mse.mean()),'rho_defined':int(sub.rho.notna().sum()),'mean_rho_defined':float(sub.rho.mean()) if sub.rho.notna().any() else None,'range_rho_defined':[float(sub.rho.min()),float(sub.rho.max())] if sub.rho.notna().any() else None,'lambda_max_count':int(sub.lambda_max.sum())}
 (O/'results.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
