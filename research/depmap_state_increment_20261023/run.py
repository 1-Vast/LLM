"""Frozen conventional measured-state functional reconstruction experiment."""
import json
from pathlib import Path
import time
from zipfile import ZipFile
import numpy as np
import pandas as pd
import scipy
import threadpoolctl
from scipy.linalg import eigh
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/depmap_state_increment'
SOURCE=ROOT/'log/20261023/functional_source_bridge/root'
LAM=np.array([.001,.01,.1,1.,10.])
ORDER=['A','B','C','H','D','E','F','G']
RESTRICTED=['A','B','C','H']


def gene_prior(y,genes,tr,query):
    avg={g:float(np.mean(y[tr[genes[tr]==g]])) for g in np.unique(genes[tr])}
    fallback=float(y[tr].mean())
    return np.array([avg.get(g,fallback) for g in genes[query]])


def center(raw,tr,query):
    block=raw[np.ix_(tr,tr)]
    mu=block.mean(axis=0); grand=float(mu.mean())
    train=block-mu[None,:]-mu[:,None]+grand
    cross=raw[np.ix_(query,tr)]
    cross=cross-cross.mean(axis=1)[:,None]-mu[None,:]+grand
    return train,cross


def normalize(a,b):
    scale=float(np.diag(a).mean())
    if scale<=1e-12:
        return np.zeros_like(a),np.zeros_like(b)
    return a/scale,b/scale


def kernel(name,grams,qc,genes,tr,query):
    if name=='B':
        sd=qc[tr].std(axis=0); sd=np.where(sd>1e-12,sd,1.)
        mean=qc[tr].mean(axis=0)
        a=(qc[tr]-mean)/sd; b=(qc[query]-mean)/sd
        return normalize(a@a.T,b@a.T)
    raw=grams[{'C':'context','H':'context','D':'absolute','E':'relative','F':'relative'}[name]]
    if name=='C':
        a=np.zeros((len(tr),len(tr)));b=np.zeros((len(query),len(tr)))
        for g in np.unique(genes[tr]):
            ti=np.flatnonzero(genes[tr]==g); qi=np.flatnonzero(genes[query]==g)
            at,bt=center(raw,tr[ti],query[qi])
            a[np.ix_(ti,ti)]=at; b[np.ix_(qi,ti)]=bt
        return normalize(a,b)
    if name in ['D','E']:
        return normalize(*center(raw,tr,query))
    diag=np.diag(raw)
    d=diag[tr,None]+diag[None,tr]-2*raw[np.ix_(tr,tr)]
    d=np.maximum(d,0.)
    positive=d[d>1e-12]
    length=float(np.median(positive)) if positive.size else 1.
    e=np.maximum(diag[query,None]+diag[None,tr]-2*raw[np.ix_(query,tr)],0.)
    a=np.exp(-d/(2*length));b=np.exp(-e/(2*length))
    if name=='H':
        a*=genes[tr,None]==genes[None,tr]
        b*=genes[query,None]==genes[None,tr]
    return a,b


def all_grid(y,genes,lines,grams,qc,tr,query,counters):
    base=gene_prior(y,genes,tr,query)
    residual=y[tr]-gene_prior(y,genes,tr,tr)
    result={'A':base[:,None]}
    for name in ORDER[1:-1]:
        a,b=kernel(name,grams,qc,genes,tr,query)
        val,vec=eigh(a,check_finite=False,driver='evr')
        val=np.maximum(val,0.)
        weights=(vec.T@residual)[:,None]/(val[:,None]+len(tr)*LAM[None,:])
        result[name]=base[:,None]+(b@vec)@weights
        counters['eigendecompositions']+=1
        counters['lambda_fits']+=len(LAM)
    return result


def line_mse(actual,pred,lines):
    return float(np.mean([np.mean((actual[lines==l]-pred[lines==l])**2) for l in np.unique(lines)]))


def nested(y,genes,lines,groups,grams,qc,tr,query,counters):
    source_groups=sorted(set(groups[tr]))
    assert len(source_groups)>=2
    mapping={g:i%3 for i,g in enumerate(source_groups)}
    inner=np.array([mapping[groups[i]] for i in tr])
    validation={name:np.full((len(tr),1 if name=='A' else len(LAM)),np.nan) for name in ORDER[:-1]}
    inner_records=[]
    for fold in sorted(set(inner)):
        fit=tr[inner!=fold]; val=tr[inner==fold]
        predictions=all_grid(y,genes,lines,grams,qc,fit,val,counters)
        for name,p in predictions.items():
            validation[name][inner==fold]=p
        inner_records.append(dict(fold=int(fold),train=fit.tolist(),validation=val.tolist(),
            prior_fallback_query=int(sum(g not in set(genes[fit]) for g in genes[val]))))
    scores={name:[line_mse(y[tr],p[:,j],lines[tr]) for j in range(p.shape[1])] for name,p in validation.items()}
    choices={name:int(np.argmin(v)) for name,v in scores.items()}
    selected={name:p[:,choices[name]] for name,p in validation.items()}
    selected['G']=.5*(selected['C']+selected['E'])
    selection_score={name:line_mse(y[tr],p,lines[tr]) for name,p in selected.items()}
    restricted=min(RESTRICTED,key=lambda x:selection_score[x])
    full=min(ORDER,key=lambda x:selection_score[x])
    final=all_grid(y,genes,lines,grams,qc,tr,query,counters)
    output={name:final[name][:,choices[name]] for name in final}
    output['G']=.5*(output['C']+output['E'])
    output['restricted']=output[restricted];output['full']=output[full]
    selection=dict(choices=choices,lambda_grid=LAM.tolist(),scores=scores,selection_score=selection_score,
                   restricted=restricted,full=full,folds=inner_records,
                   prior_fallback_query=int(sum(g not in set(genes[tr]) for g in genes[query])))
    return output,selection,{**selected,**{'grid_'+name:p for name,p in validation.items()}}


def prepare():
    assert (OUT/'FREEZE.json').exists()
    state=pd.read_csv(OUT/'pseudobulk.csv',header=[0,1],index_col=0)
    assert state.columns.is_unique and state.index.is_unique
    keys=list(state.columns);lines=np.array([x[0] for x in keys]);genes=np.array([x[1] for x in keys])
    counts=state.to_numpy(dtype=np.float64).T
    filled={}
    for line in np.unique(lines):
        ix=np.flatnonzero(lines==line); block=counts[ix].copy(); mask=np.isnan(block)
        assert np.all(mask.all(axis=0)|(~mask).all(axis=0)), 'isolated missing counts'
        filled[line]=int(mask.sum()); block[mask]=0.; counts[ix]=block
    assert np.all(np.isfinite(counts)) and np.all(counts>=0) and np.all(counts==np.floor(counts))
    total=counts.sum(axis=1);assert np.all(total>0)
    qc=np.stack([np.log1p(total),(counts>0).mean(axis=1)],axis=1)
    log=np.log1p(counts/total[:,None]*1e6)
    contexts=np.empty_like(log)
    for line in np.unique(lines):
        mask=lines==line;contexts[mask]=log[mask].mean(axis=0)
    relative=log-contexts
    labels=pd.read_csv(SOURCE/'crispr_table.csv',usecols=['cell_line','guide','gene_effect'])
    assert not labels.duplicated(['cell_line','guide']).any()
    lookup=labels.set_index(['cell_line','guide']).gene_effect
    y=np.array([lookup.loc[k] for k in keys],dtype=float)
    finite=np.isfinite(y)
    design=json.loads((SOURCE/'IDENTITY_JOIN.json').read_text())['cell_line_design']
    batches={x['cell_line']:x['batch'] for x in design}
    summary=dict(raw_shape=list(counts.shape),finite_function=int(finite.sum()),dropped_nonfinite=int((~finite).sum()),
                 padding_cells=filled,library_versions=dict(numpy=np.__version__,pandas=pd.__version__,
                     scipy=scipy.__version__,threadpoolctl=threadpoolctl.__version__),
                 by_line={l:int(np.sum(finite&(lines==l))) for l in np.unique(lines)},
                 by_gene={g:int(np.sum(finite&(genes==g))) for g in np.unique(genes)},
                 missing_function_pairs=[list(keys[i]) for i in np.flatnonzero(~finite)],
                 batch_by_line=batches,batch_count=len(set(batches.values())),
                 information='retrospective measured full selected-panel state')
    assert min(summary['by_line'].values())>=10
    # Context uses all measured states even if function is missing, as predeclared.
    arrays=dict(y=y[finite],genes=genes[finite],lines=lines[finite],
        groups=np.array([batches[l] for l in lines[finite]]),qc=qc[finite],
        log=log[finite],context=contexts[finite],relative=relative[finite],transcripts=state.index.to_numpy(dtype=str))
    np.savez_compressed(OUT/'prepared.npz',**arrays)
    (OUT/'PREPARED.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return arrays


def metrics(y,p,genes,lines):
    result={}
    for line in np.unique(lines):
        ix=np.flatnonzero(lines==line)
        chosen=sorted(ix,key=lambda i:(float(p[i]),str(genes[i])))[:10]
        oracle=sorted(ix,key=lambda i:(float(y[i]),str(genes[i])))[:10]
        cutoff=float(p[chosen[-1]])
        result[line]=dict(mse=float(np.mean((y[ix]-p[ix])**2)),
            regret=float(y[chosen].mean()-y[oracle].mean()),
            cutoff_ties=int(np.sum(p[ix]==cutoff)),n=len(ix))
    return result


def run():
    assert not (OUT/'RESULT.json').exists()
    start=time.perf_counter();d=prepare()
    grams={name:d[key]@d[key].T for name,key in [('absolute','log'),('context','context'),('relative','relative')]}
    y,genes,lines=d['y'],d['genes'],d['lines'];n=len(y)
    counters=dict(eigendecompositions=0,lambda_fits=0,
        mixture='G combines separately selected C/E:25possible lambda pairs; no25pair joint search; no extra solve',
        selection='restricted4programs; full8programs; shared inner predictions; costs not equalized',
        outer_fits=0)
    summary={}; choices=[];prediction_rows=[]
    for scheme in ['line','batch']:
        groups=lines if scheme=='line' else d['groups']
        output={name:np.full(n,np.nan) for name in ORDER+['restricted','full']}
        for group in sorted(set(groups)):
            query=np.flatnonzero(groups==group);tr=np.flatnonzero(groups!=group)
            pred,choice,inner=nested(y,genes,lines,groups,grams,d['qc'],tr,query,counters)
            counters['outer_fits']+=1
            for name,p in pred.items():output[name][query]=p
            choices.append(dict(scheme=scheme,group=group,train=tr.tolist(),query=query.tolist(),**choice))
            # Store source validation predictions for every selected program as well.
            np.savez_compressed(OUT/f'inner_{scheme}_{group}.npz',train=tr,**inner)
            print(json.dumps(dict(scheme=scheme,group=group,restricted=choice['restricted'],full=choice['full'])),flush=True)
        summary[scheme]={}
        for name,p in output.items():
            assert np.isfinite(p).all()
            per=metrics(y,p,genes,lines)
            summary[scheme][name]=dict(mse=float(np.mean([r['mse'] for r in per.values()])),
                                     regret=float(np.mean([r['regret'] for r in per.values()])),per_line=per)
            for i in range(n):prediction_rows.append(dict(scheme=scheme,program=name,line=lines[i],gene=genes[i],actual=y[i],prediction=p[i]))
    gains={s:1-summary[s]['full']['mse']/summary[s]['restricted']['mse'] for s in summary}
    wins=int(sum(summary['line']['full']['per_line'][l]['mse']<summary['line']['restricted']['per_line'][l]['mse'] for l in set(lines)))
    nonworse=all(summary[s]['full']['regret']<=summary[s]['restricted']['regret']+1e-12 for s in summary)
    gate=bool(gains['line']>=.05 and wins>=12 and gains['batch']>0 and nonworse)
    pd.DataFrame(prediction_rows).to_csv(OUT/'predictions.csv',index=False)
    (OUT/'CHOICES.json').write_text(json.dumps(choices,indent=2),encoding='utf-8')
    result=dict(summary=summary,gain=gains,strict_line_wins=wins,top10_nonworse=nonworse,
                gate=gate,decision='GO_COMPONENT_SIGNAL_ONLY' if gate else 'STOP_FIXED_COMPONENT_MENU',
                counters=counters,seconds=time.perf_counter()-start)
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='summary'}),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2):
        run()
