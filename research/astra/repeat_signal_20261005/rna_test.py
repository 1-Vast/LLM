"""Cheap, simple condition-specific RNA regression with dev-only selection."""
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from .analyze import (HERE,ROOT,SOURCE,HIERARCHY,HKEY,SEED,prepare_design,event_labels,
                      plain,dump,line_boot,wcorr,top,sha256,jaaks,open_vault)

RNA=ROOT/'research/astra/knowledge_transfer_20261004/context/pathway_125_lines.csv'
LAMBDAS=[1000000.,1000.,100.,10.,1.]
BASES=['same_y','same_p','both_y','mean_p','product_p','min_p']


def baselines(Y,H,rev):
    count=np.isfinite(Y).sum(axis=0)
    sy=(np.nansum(Y,axis=0)+2*np.nanmean(Y))/(count+2)
    sp=(np.nansum(H,axis=0)+2*np.nanmean(H))/(np.isfinite(H).sum(axis=0)+2)
    return {'same_y':sy,'same_p':sp,'both_y':(sy+sy[rev])/2,'mean_p':(sp+sp[rev])/2,
            'product_p':sp*sp[rev],'min_p':np.minimum(sp,sp[rev])}


def fitted(Y,H,X,Z,rev):
    base=baselines(Y,H,rev)
    out={k:np.tile(v,(len(Z),1)) for k,v in base.items()}
    mu=X.mean(axis=0);sd=X.std(axis=0);sd[sd<1e-8]=1
    X=(X-mu)/sd;Z=(Z-mu)/sd
    B={lam:np.zeros((X.shape[1],Y.shape[1])) for lam in LAMBDAS}
    for j in range(Y.shape[1]):
        use=np.isfinite(Y[:,j]);xx=X[use];yy=Y[use,j]-base['same_y'][j]
        if not use.any():continue
        gram=xx.T@xx;rhs=xx.T@yy
        for lam in LAMBDAS:B[lam][:,j]=np.linalg.solve(gram+lam*np.eye(len(mu)),rhs)
    for lam,b in B.items():out[f'rna_{lam:g}']=base['same_y'][None,:]+Z@b
    return out


def run():
    out=HERE/'rna_results';out.mkdir(exist_ok=False)
    open_vault(HERE/'freeze_rna.json',HERE/'outcome_access.jsonl',purpose='POST HOC exploratory condition-specific RNA test, dev folds exclude all 14 repeats',source=SOURCE,root=ROOT)
    pairs=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={k:str for k in ['ANCHOR_ID','LIBRARY_ID','LIBRARY_CONC','anchor_set']})
    repeats=set(pairs.SIDM)
    raw=jaaks._read(SOURCE,jaaks.DESIGN_COLUMNS+jaaks.OUTCOME_COLUMNS)
    events,_,_=event_labels(prepare_design(raw,pd.read_csv(HIERARCHY,dtype=str)))
    h=events[~events.SIDM.isin(repeats)&events.valid&events.n_anchor.eq(2)&events.in_menu].copy()
    h=h.groupby(HKEY+['SIDM'],as_index=False).agg(y=('y','mean'),hit=('hit','mean'))
    h.hit=h.hit.ge(.5).astype(float)
    context=pd.read_csv(RNA,index_col=0)
    rng=np.random.default_rng(SEED)
    development=[];predictions=[];selection={};fold_records={}
    for tissue,g in h.groupby('Tissue'):
        g=g.copy();ts=pairs[pairs.Tissue.eq(tissue)].copy()
        keys=sorted({tuple(v) for v in g[HKEY].itertuples(index=False,name=None)} | {tuple(v) for v in ts[HKEY].itertuples(index=False,name=None)})
        ki={k:i for i,k in enumerate(keys)};lines=sorted(g.SIDM.unique());li={s:i for i,s in enumerate(lines)}
        Y=np.full((len(lines),len(keys)),np.nan);H=Y.copy()
        for row in g.to_dict('records'):
            j=ki[tuple(row[k] for k in HKEY)];i=li[row['SIDM']];Y[i,j]=row['y'];H[i,j]=row['hit']
        rev=[]
        for k in keys:
            other=[j for j,a in enumerate(keys) if a[0]==k[0] and a[1]==k[2] and a[2]==k[1]]
            rev.append(sorted(other,key=lambda j:(-np.isfinite(Y[:,j]).sum(),keys[j]))[0] if other else ki[k])
        rev=np.array(rev)
        X=context.loc[lines].to_numpy();order=rng.permutation(len(lines));fold=np.empty(len(lines),int);fold[order]=np.arange(len(lines))%5
        fold_records[tissue]={lines[i]:int(fold[i]) for i in range(len(lines))}
        targets=sorted(ts.SIDM.unique());XT=context.loc[targets].to_numpy()
        perm_train=rng.permutation(len(lines));perm_test=rng.permutation(len(targets))
        role_map={tuple(row[k] for k in HKEY):row['role'] for row in events[events.Tissue.eq(tissue)&events.in_menu].to_dict('records')}
        roles=np.array([role_map[k] for k in keys])
        candidate={};means={}
        for arm,xx,xt in [('rna',X,XT),('shuffled_rna',X[perm_train],XT[perm_test])]:
            recs=[]
            for f in range(5):
                train=fold!=f;test=~train
                # Permutations stay wholly inside training or validation fold to avoid using validation-cell identity in training.
                xtrain=X[train];xval=X[test]
                if arm=='shuffled_rna':
                    prng=np.random.default_rng([SEED,f,len(lines)])
                    xtrain=xtrain[prng.permutation(len(xtrain))];xval=xval[prng.permutation(len(xval))]
                pp=fitted(Y[train],H[train],xtrain,xval,rev)
                for pos,i in enumerate(np.flatnonzero(test)):
                    for role in ['SV','VS']:
                        use=np.isfinite(Y[i])&np.isfinite(H[i])&(roles==role)
                        ids=np.array([str(k) for k in keys])[use]
                        for name,mat in pp.items():
                            score=mat[pos,use];sel=top(score,ids)
                            recs.append({'arm':arm,'Tissue':tissue,'SIDM':lines[i],'fold':f,'role':role,'method':name,
                                'positives':float(H[i,use][sel].sum()),'rho':wcorr(rankdata(score),rankdata(Y[i,use]),np.ones(use.sum()))})
            candidate[arm]=pd.DataFrame(recs)
            means[arm]=candidate[arm].groupby('method').positives.mean().to_dict()
            development.extend(recs)
        # One simple comparator selected from true-arm folds, then identical fallback for both learning arms.
        best=max(BASES,key=lambda k:means['rna'][k])
        selection[tissue]={'baseline':best,'baseline_dev_positives':means['rna'][best],'arms':{}}
        for arm,xx,xt in [('rna',X,XT),('shuffled_rna',X[perm_train],XT[perm_test])]:
            options=[best]+[f'rna_{lam:g}' for lam in LAMBDAS]
            winner=max(options,key=lambda k:means[arm][k])
            selection[tissue]['arms'][arm]={'selected':winner,'dev_scores':means[arm]}
            pp=fitted(Y,H,xx,xt,rev);ti={s:i for i,s in enumerate(targets)}
            for row in ts.to_dict('records'):
                j=ki[tuple(row[k] for k in HKEY)];i=ti[row['SIDM']]
                if arm=='rna':
                    row['simple_score']=float(pp[best][i,j]);row['rna_score']=float(pp[winner][i,j]);predictions.append(row)
            if arm=='shuffled_rna':
                # Keyed lookup, never rely on incidental row iteration order between arms.
                lookup={(s,tuple(k)):float(pp[winner][ti[s],ki[tuple(k)]]) for s,k in zip(ts.SIDM,ts[HKEY].itertuples(index=False,name=None))}
                for row in predictions:
                    if row['Tissue']==tissue:row['shuffled_score']=lookup[(row['SIDM'],tuple(row[k] for k in HKEY))]
    d=pd.DataFrame(predictions);records=[]
    for (t,s,role),g in d.groupby(['Tissue','SIDM','role']):
        rec={'Tissue':t,'SIDM':s,'role':role,'n':len(g)}
        for arm in ['simple','rna','shuffled']:
            score=g[f'{arm}_score'].to_numpy();sel=top(score,g.pair)
            rec[f'R2_positive_{arm}']=float(g.hit2.to_numpy(float)[sel].sum())
            rec[f'rho_{arm}']=wcorr(rankdata(score),rankdata(g.y2),np.ones(len(g)))
            M=int(np.ceil(.2*len(g)));ns=int(np.floor(.7*M));order=np.lexsort((g.pair.to_numpy(),-score));screen=order[:ns]
            hits=screen[g.hit1.to_numpy(float)[screen]>0];verify=hits[:M-ns]
            rec[f'P2_confirmed_{arm}']=float(g.hit2.to_numpy(float)[verify].sum());rec[f'P2_measurements_{arm}']=ns+len(verify)
            use=np.isfinite(g.y3)
            gg=g[use];sel3=top(gg[f'{arm}_score'],gg.pair)
            rec[f'R3_positive_{arm}']=float(gg.hit3.to_numpy(float)[sel3].sum())
        for metric in ['R2_positive','R3_positive','rho','P2_confirmed','P2_measurements']:
            for arm in ['rna','shuffled']:rec[f'{metric}_{arm}_minus_simple']=rec[f'{metric}_{arm}']-rec[f'{metric}_simple']
        records.append(rec)
    per=pd.DataFrame(records);line=per.groupby(['Tissue','SIDM']).mean(numeric_only=True).reset_index();summary=line_boot(line)
    result={'label':'Post hoc exploratory, no untouched evaluation; cheap same-condition RNA diagnostic','selection':selection,'summary':summary,'training_lines':len(set(h.SIDM)),'evaluation_lines':len(repeats),'training_evaluation_overlap':len(set(h.SIDM)&repeats),'context_columns':list(context.columns),'folds':fold_records}
    dump(out/'summary.json',plain(result));pd.DataFrame(development).to_csv(out/'development.csv.gz',index=False,compression={'method':'gzip','mtime':0});d.to_csv(out/'predictions.csv.gz',index=False,compression={'method':'gzip','mtime':0});per.to_csv(out/'per_role.csv',index=False)
    print(json.dumps(plain({'selection':selection,'summary':summary})))

if __name__=='__main__':run()
