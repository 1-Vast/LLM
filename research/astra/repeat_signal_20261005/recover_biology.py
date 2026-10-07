"""Recovery rerun of the previously executed biological and static-control arms."""
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from .analyze import HERE,ROOT,SOURCE,HIERARCHY,HKEY,ID,COND,SEED,jaaks,prepare_design,event_labels,top,wcorr,line_boot,dump,plain,open_vault
from .rna_test import baselines,LAMBDAS,BASES
ARMS=['hotspot','hotspot_shuffled','dependency','dependency_shuffled','target_dependency','target_shuffled','rna_binary']
CONTROLS={'hotspot':'hotspot_shuffled','dependency':'dependency_shuffled','target_dependency':'target_shuffled'}

def simple_scores(Y,H,rev):
    b=baselines(Y,H,rev);valid=np.isfinite(H)&np.isfinite(H[:,rev]);joint=H*H[:,rev]
    b['joint_p']=(np.nansum(joint,axis=0)+2*np.nanmean(joint))/(valid.sum(axis=0)+2)
    return b

def features(arm,lines,keys,frames,gene_map):
    if arm.startswith('hotspot'):return frames['hotspot'].reindex(lines).to_numpy(float)
    if arm=='rna_binary':return frames['rna'].reindex(lines).to_numpy(float)
    dep=frames['dependency'].reindex(lines)
    if arm in ['dependency','dependency_shuffled']:return dep.to_numpy(float)
    def aggregate(drug):
        genes=set()
        for component in drug.split('|'):genes.update(gene_map.get(component,[]))
        cols=[g for g in sorted(genes) if g in dep]
        if not cols:return np.full(len(lines),np.nan),np.full(len(lines),np.nan)
        z=dep[cols].to_numpy();valid=np.isfinite(z);n=valid.sum(axis=1)
        mean=np.divide(np.nansum(z,axis=1),n,out=np.full(len(z),np.nan),where=n>0)
        minimum=np.where(n>0,np.min(np.where(valid,z,np.inf),axis=1),np.nan)
        return mean,minimum
    values=[]
    for k in keys:
        a,amin=aggregate(k[1]);b,bmin=aggregate(k[2]);values.append(np.c_[a,amin,b,bmin,a*b,amin*bmin])
    return np.stack(values,axis=1)

def shuffle_rows(x,seed):
    x=x.copy();ids=np.flatnonzero(np.isfinite(x).any(axis=tuple(range(1,x.ndim))))
    x[ids]=x[np.random.default_rng(seed).permutation(ids)];return x

def learn(H,X,Z,prior):
    outputs={lam:np.full((len(Z),H.shape[1]),np.nan) for lam in LAMBDAS};cache={}
    for j in range(H.shape[1]):
        x=X if X.ndim==2 else X[:,j,:];z=Z if Z.ndim==2 else Z[:,j,:]
        use=np.isfinite(H[:,j])&np.isfinite(x).any(axis=1);available=np.isfinite(z).any(axis=1)
        if use.sum()<3 or not available.any():continue
        key=use.tobytes() if X.ndim==2 else j
        if key not in cache:
            xx=x[use];n=np.isfinite(xx).sum(axis=0)
            mu=np.divide(np.nansum(xx,axis=0),n,out=np.zeros(xx.shape[1]),where=n>0)
            xx=np.where(np.isfinite(xx),xx,mu);sd=xx.std(axis=0);sd[sd<1e-8]=1
            xx=(xx-mu)/sd;zz=(np.where(np.isfinite(z),z,mu)-mu)/sd
            gram=xx@xx.T;cross=zz@xx.T
            cache[key]=({lam:np.linalg.solve(gram+lam*np.eye(len(xx)),cross.T).T for lam in LAMBDAS},available)
        projections,available=cache[key];residual=H[use,j]-prior[j]
        for lam,P in projections.items():outputs[lam][available,j]=prior[j]+(P@residual)[available]
    return outputs

def blend(base,pred,alpha):
    b=rankdata(base)/len(base)
    if alpha==0:return b
    use=np.isfinite(pred);q=b.copy()
    if use.any():q[use]=rankdata(pred[use])/use.sum()
    return (1-alpha)*b+alpha*q

def run():
    out=HERE/'recovered_biology_results';out.mkdir(exist_ok=False)
    open_vault(HERE/'freeze_recovery.json',HERE/'outcome_access.jsonl',purpose='Recovery rerun of known biological results and post hoc zero-feature prior control; no new heldout claim',source=SOURCE,root=ROOT)
    pairs=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={k:str for k in ID+COND});repeats=set(pairs.SIDM)
    raw=jaaks._read(SOURCE,jaaks.DESIGN_COLUMNS+jaaks.OUTCOME_COLUMNS)
    events,_,_=event_labels(prepare_design(raw,pd.read_csv(HIERARCHY,dtype=str)))
    history=events[~events.SIDM.isin(repeats)&events.valid&events.n_anchor.eq(2)&events.in_menu]
    h=history.groupby(HKEY+['SIDM'],as_index=False).agg(y=('y','mean'),hit=('hit','mean'));h.hit=h.hit.ge(.5).astype(float)
    assert h.SIDM.nunique()==111 and not set(h.SIDM)&repeats
    frames={'hotspot':pd.read_csv(HERE/'inputs/hotspot_mapped.csv.gz',index_col=0),'dependency':pd.read_csv(HERE/'inputs/target_dependency.csv',index_col=0),'rna':pd.read_csv(HERE/'inputs/pathway_125_lines.csv',index_col=0)}
    genes=pd.read_csv(HERE/'inputs/drug_target_annotation.csv',dtype={'drug_id':str}).dropna(subset=['gene'])
    gene_map={d:sorted(set(g.gene)) for d,g in genes.groupby('drug_id')}
    bank=sorted(frames['dependency'].columns);gp=dict(zip(bank,np.random.default_rng(SEED+20).permutation(bank)))
    shuffled_map={d:[gp.get(g,g) for g in gs] for d,gs in gene_map.items()}
    rng=np.random.default_rng(SEED);development=[];predictions=[];selection={};folds={}
    for tissue,g in h.groupby('Tissue'):
        target=pairs[pairs.Tissue.eq(tissue)];keys=sorted(set(g[HKEY].itertuples(index=False,name=None))|set(target[HKEY].itertuples(index=False,name=None)))
        ki={k:j for j,k in enumerate(keys)};lines=sorted(g.SIDM.unique());li={s:i for i,s in enumerate(lines)};targets=sorted(target.SIDM.unique());ti={s:i for i,s in enumerate(targets)}
        Y=np.full((len(lines),len(keys)),np.nan);H=Y.copy()
        for row in g.to_dict('records'):
            i=li[row['SIDM']];j=ki[tuple(row[k] for k in HKEY)];Y[i,j]=row['y'];H[i,j]=row['hit']
        rev=[]
        for k in keys:
            other=[j for j,z in enumerate(keys) if z[1]==k[2] and z[2]==k[1]]
            rev.append(min(other,key=lambda j:(-np.isfinite(Y[:,j]).sum(),keys[j])) if other else ki[k])
        rev=np.array(rev);rolemap={tuple(row[k] for k in HKEY):row['role'] for row in events[events.Tissue.eq(tissue)&events.in_menu].to_dict('records')}
        roles=np.array([rolemap[k] for k in keys]);ids=np.array([str(k) for k in keys]);order=rng.permutation(len(lines));fold=np.empty(len(lines),int);fold[order]=np.arange(len(lines))%5
        folds[tissue]={s:int(fold[i]) for i,s in enumerate(lines)}
        cvbase={k:np.full_like(H,np.nan) for k in BASES+['joint_p']};splits=[]
        for f in range(5):
            tr=fold!=f;va=~tr;b=simple_scores(Y[tr],H[tr],rev);splits.append((tr,va,b))
            for k,v in b.items():cvbase[k][va]=v
        def score_matrix(mat):
            vals=[]
            for i in range(len(lines)):
                for role in ['SV','VS']:
                    use=np.isfinite(H[i])&(roles==role);vals.append(H[i,use][top(mat[i,use],ids[use])].sum())
            return float(np.mean(vals))
        base_dev={k:score_matrix(v) for k,v in cvbase.items()};best=max(base_dev,key=base_dev.get);fullbase=simple_scores(Y,H,rev)
        selection[tissue]={'baseline':best,'simple_development':base_dev,'arms':{}}
        for row in target.to_dict('records'):
            row['simple_score']=fullbase[best][ki[tuple(row[k] for k in HKEY)]];predictions.append(row)
        for ai,arm in enumerate(ARMS+['prior_control']):
            if arm=='prior_control':
                cv={LAMBDAS[0]:cvbase['same_p']};raw_preds={LAMBDAS[0]:np.tile(fullbase['same_p'],(len(targets),1))};lambdas=LAMBDAS[:1]
            else:
                gm=shuffled_map if arm=='target_shuffled' else gene_map
                X=features(arm,lines,keys,frames,gm);Z=features(arm,targets,keys,frames,gm);cv={lam:np.full_like(H,np.nan) for lam in LAMBDAS};lambdas=LAMBDAS
                for f,(tr,va,b) in enumerate(splits):
                    xx,zz=X[tr],X[va]
                    if arm in ['hotspot_shuffled','dependency_shuffled']:xx=shuffle_rows(xx,[SEED,ai,f,1]);zz=shuffle_rows(zz,[SEED,ai,f,2])
                    pp=learn(H[tr],xx,zz,b['same_p'])
                    for lam,z in pp.items():cv[lam][va]=z
                if arm in ['hotspot_shuffled','dependency_shuffled']:X=shuffle_rows(X,[SEED,ai,99,1]);Z=shuffle_rows(Z,[SEED,ai,99,2])
                raw_preds=learn(H,X,Z,fullbase['same_p'])
            options=[(0.,LAMBDAS[0],base_dev[best])]
            for alpha in [.25,.5,1.]:
                for lam in lambdas:
                    mat=np.full_like(H,np.nan)
                    for i in range(len(lines)):
                        for role in ['SV','VS']:
                            use=np.isfinite(H[i])&(roles==role);mat[i,use]=blend(cvbase[best][i,use],cv[lam][i,use],alpha)
                    options.append((alpha,lam,score_matrix(mat)))
            alpha,lam,value=max(options,key=lambda z:z[2]);selection[tissue]['arms'][arm]={'alpha':alpha,'lambda':lam,'dev_positives':value}
            development.extend({'Tissue':tissue,'arm':arm,'alpha':a,'lambda':l,'positives':v} for a,l,v in options)
            for s in targets:
                for role in ['SV','VS']:
                    ix=[i for i,row in enumerate(predictions) if row['Tissue']==tissue and row['SIDM']==s and row['role']==role]
                    jj=np.array([ki[tuple(predictions[i][k] for k in HKEY)] for i in ix]);scores=blend(fullbase[best][jj],raw_preds[lam][ti[s],jj],alpha)
                    for i,v in zip(ix,scores):predictions[i][arm+'_score']=float(v)
    d=pd.DataFrame(predictions);rawpairs=pd.read_csv(HERE/'raw_results/paired_actions.csv.gz',dtype={'ANCHOR_ID':str,'LIBRARY_ID':str})
    d=d.merge(rawpairs[ID+['raw_y2']],on=ID,how='left',validate='one_to_one');records=[];contrib=[];selected=[]
    for (t,s,r),g in d.groupby(['Tissue','SIDM','role']):
        n=len(g);M=int(np.ceil(.2*n));ns=int(np.floor(.7*M));row={'Tissue':t,'SIDM':s,'role':r,'n':n,'dependency_available':s in frames['dependency'].index}
        h1=g.hit1.to_numpy(float)>0;h2=g.hit2.to_numpy(float)>0;row['P2_oracle']=min(ns,M-ns,int(sum(h1&h2)));masks={}
        for arm in ['simple']+ARMS+['prior_control']:
            score=g[arm+'_score'].to_numpy();sel=top(score,g.pair);order=np.lexsort((g.pair.to_numpy(),-score));screen=order[:ns];verify=screen[h1[screen]][:M-ns]
            vm=np.zeros(n);vm[verify]=1;masks[arm]=(sel.astype(float)*h2,vm*h2)
            row['R2_positive_'+arm]=float(sum(h2[sel]));row['P2_confirmed_'+arm]=float(sum(h2[verify]));row['P2_cost_'+arm]=ns+len(verify)
            row['rho_'+arm]=wcorr(rankdata(score),rankdata(g.y2),np.ones(n))
            use=np.isfinite(g.raw_y2);row['raw_rho_'+arm]=wcorr(rankdata(score[use]),rankdata(g.raw_y2[use]),np.ones(use.sum()))
            gg=g[np.isfinite(g.y3)];q=top(gg[arm+'_score'],gg.pair);row['R3_positive_'+arm]=float(gg.hit3.to_numpy(float)[q].sum())
            for stage,ix in [('screen',screen),('verify',verify)]:
                for i in ix:selected.append({'Tissue':t,'SIDM':s,'role':r,'arm':arm,'stage':stage,'pair':g.pair.iloc[i],'confirmed':bool(h1[i]&h2[i]) if stage=='verify' else None})
        for arm in ARMS+['prior_control']:
            for m in ['R2_positive','P2_confirmed','P2_cost','rho','raw_rho','R3_positive']:
                row[m+'_'+arm+'_minus_simple']=row[m+'_'+arm]-row[m+'_simple']
                row[m+'_'+arm+'_minus_prior']=row[m+'_'+arm]-row[m+'_prior_control']
            for i,p in enumerate(g.pair):contrib.append({'Tissue':t,'SIDM':s,'pair':p,'arm':arm,'R2_positive_delta':float(masks[arm][0][i]-masks['simple'][0][i]),'P2_confirmed_delta':float(masks[arm][1][i]-masks['simple'][1][i])})
        for arm,control in CONTROLS.items():
            for m in ['R2_positive','P2_confirmed']:row[m+'_'+arm+'_minus_control']=row[m+'_'+arm]-row[m+'_'+control]
        records.append(row)
    roles=pd.DataFrame(records);lines=roles.groupby(['Tissue','SIDM']).mean(numeric_only=True).reset_index();summary=line_boot(lines);c=pd.DataFrame(contrib)
    rng=np.random.default_rng(SEED+40);ls=sorted(c.SIDM.unique());ps=sorted(c.pair.unique());li={s:i for i,s in enumerate(ls)};strata=[np.array([li[s] for s in g.SIDM]) for _,g in lines.groupby('Tissue')]
    lw=np.array([np.bincount(np.concatenate([rng.choice(z,len(z)) for z in strata]),minlength=len(ls)) for _ in range(1000)])
    pw=np.array([np.bincount(rng.integers(len(ps),size=len(ps)),minlength=len(ps)) for _ in range(1000)])
    boots={};points={}
    for arm,g in c.groupby('arm'):
        for metric in ['R2_positive','P2_confirmed']:
            mat=g.pivot_table(index='SIDM',columns='pair',values=metric+'_delta',aggfunc='sum').reindex(index=ls,columns=ps).fillna(0).to_numpy()/2
            b=np.einsum('bi,ij,bj->b',lw,mat,pw)/len(ls);boots[(arm,metric)]=b;points[(arm,metric)]=mat.sum()/len(ls)
            summary[metric+'_'+arm+'_minus_simple']['line_pair_ci95']=np.quantile(b,[.025,.975]).tolist()
    for metric in ['R2_positive','P2_confirmed']:
        centered=np.column_stack([boots[(a,metric)]-points[(a,metric)] for a in ARMS]);radius=float(np.quantile(np.max(np.abs(centered),axis=1),.95))
        for arm in ARMS:
            point=points[(arm,metric)];summary[metric+'_'+arm+'_minus_simple']['simultaneous_seven_arm_ci95']=[point-radius,point+radius]
            summary[metric+'_'+arm+'_minus_prior']['line_pair_ci95']=np.quantile(boots[(arm,metric)]-boots[('prior_control',metric)],[.025,.975]).tolist()
        for arm,control in CONTROLS.items():summary[metric+'_'+arm+'_minus_control']['line_pair_ci95']=np.quantile(boots[(arm,metric)]-boots[(control,metric)],[.025,.975]).tolist()
    result={'label':'Recovery rerun; prior control is post hoc; all data exposed exploratory','selection':selection,'summary':summary,'dependency_covered':line_boot(lines[lines.dependency_available.eq(1)].reset_index(drop=True)),'folds':folds,'gene_permutation':gp,'training_lines':111,'target_lines':14,'overlap':0,'bootstrap_note':'Conditional on history, development choices and fixed selection; no retraining bootstrap.'}
    dump(out/'summary.json',plain(result));pd.DataFrame(development).to_csv(out/'development.csv',index=False);roles.to_csv(out/'per_role.csv',index=False)
    for name,frame in [('predictions',d),('candidate_contributions',c),('selected_actions',pd.DataFrame(selected))]:frame.to_csv(out/(name+'.csv.gz'),index=False,compression={'method':'gzip','mtime':0})
    print(json.dumps({k:v for k,v in summary.items() if k.startswith('P2_confirmed') or k=='P2_oracle'}))

if __name__=='__main__':run()
