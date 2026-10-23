"""Independent post-result audit; never imports the experiment fitter."""
import json
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from scipy.linalg import solve
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/depmap_state_increment'
ORDER=['A','B','C','H','D','E','F','G']
RESTRICTED=['A','B','C','H']


def mse(y,p,lines):
    return float(np.mean([np.mean(np.square(y[lines==l]-p[lines==l])) for l in np.unique(lines)]))


def independent_predict(d,tr,query,method,lam):
    g=d['genes'];y=d['y']
    means={gene:float(y[tr[g[tr]==gene]].mean()) for gene in set(g[tr])}
    def prior(ix):return np.array([means.get(g[i],float(y[tr].mean())) for i in ix])
    base=prior(query)
    if method=='A':return base
    residual=y[tr]-prior(tr)
    if method=='C':
        # Construct gated centered feature Grams directly, not Gram-centering helper.
        x=d['context'];a=np.zeros((len(tr),len(tr)));b=np.zeros((len(query),len(tr)))
        for gene in set(g[tr]):
            ti=np.flatnonzero(g[tr]==gene);qi=np.flatnonzero(g[query]==gene)
            mu=x[tr[ti]].mean(axis=0)
            u=x[tr[ti]]-mu;v=x[query[qi]]-mu
            a[np.ix_(ti,ti)]=u@u.T;b[np.ix_(qi,ti)]=v@u.T
    elif method in ['B','D','E']:
        x=d[{'B':'qc','D':'log','E':'relative'}[method]]
        mu=x[tr].mean(axis=0);u=x[tr]-mu;v=x[query]-mu
        if method=='B':
            sd=x[tr].std(axis=0);sd[sd<=1e-12]=1.
            u=u/sd;v=v/sd
        a=u@u.T;b=v@u.T
    else:
        x=d['context' if method=='H' else 'relative']
        # Independent pairwise formula, with the same specified cancellation clip.
        u=x[tr];v=x[query]
        aa=np.maximum((u*u).sum(1)[:,None]+(u*u).sum(1)[None,:]-2*(u@u.T),0)
        bb=np.maximum((v*v).sum(1)[:,None]+(u*u).sum(1)[None,:]-2*(v@u.T),0)
        pos=aa[aa>1e-12];length=float(np.median(pos)) if pos.size else 1.
        a=np.exp(-aa/(2*length));b=np.exp(-bb/(2*length))
        if method=='H':
            a*=g[tr,None]==g[None,tr];b*=g[query,None]==g[None,tr]
    if method in ['B','C','D','E']:
        scale=float(np.diag(a).mean())
        if scale<=1e-12:return base
        a/=scale;b/=scale
    coef=solve(a+len(tr)*lam*np.eye(len(tr)),residual,assume_a='pos',check_finite=True)
    return base+b@coef


def main():
    assert (OUT/'RESULT.json').exists(), 'Do not access numeric payload before result'
    result=json.loads((OUT/'RESULT.json').read_text())
    choices=json.loads((OUT/'CHOICES.json').read_text())
    d=np.load(OUT/'prepared.npz',allow_pickle=False)
    frame=pd.read_csv(OUT/'predictions.csv')
    errors=[];summaries={};max_metric_error=0.
    for (scheme,program),part in frame.groupby(['scheme','program'],sort=True):
        per={}
        for line,p in part.groupby('line',sort=True):
            yy=p.actual.to_numpy();pp=p.prediction.to_numpy();gg=p.gene.to_numpy()
            selected=sorted(range(len(p)),key=lambda i:(pp[i],gg[i]))[:10]
            oracle=sorted(range(len(p)),key=lambda i:(yy[i],gg[i]))[:10]
            cutoff=pp[selected[-1]]
            per[line]=dict(mse=float(np.mean((yy-pp)**2)),regret=float(yy[selected].mean()-yy[oracle].mean()),
                           cutoff_ties=int(sum(pp==cutoff)),n=len(p))
        own=dict(mse=float(np.mean([r['mse'] for r in per.values()])),
                 regret=float(np.mean([r['regret'] for r in per.values()])),per_line=per)
        summaries.setdefault(scheme,{})[program]=own
        ref=result['summary'][scheme][program]
        for key in ['mse','regret']:
            max_metric_error=max(max_metric_error,abs(own[key]-ref[key]))
        for line,r in per.items():
            for key in ['mse','regret','cutoff_ties','n']:
                max_metric_error=max(max_metric_error,abs(r[key]-ref['per_line'][line][key]))
    if max_metric_error>1e-10:errors.append('metrics')
    inner_max_error=0.;inner_choices=[]
    for c in choices:
        stored=np.load(OUT/f"inner_{c['scheme']}_{c['group']}.npz")
        tr=np.array(c['train']); scores={};selected={};indices={}
        for name in ORDER[:-1]:
            grid=stored['grid_'+name]
            values=[mse(d['y'][tr],grid[:,j],d['lines'][tr]) for j in range(grid.shape[1])]
            scores[name]=values;indices[name]=int(np.argmin(values))
            selected[name]=grid[:,indices[name]]
            inner_max_error=max(inner_max_error,float(np.max(np.abs(np.array(values)-c['scores'][name]))))
        selected['G']=(selected['C']+selected['E'])/2
        if any(not np.allclose(selected[name],stored[name],rtol=0,atol=1e-12) for name in ORDER):
            errors.append('stored selected grid '+c['scheme']+'/'+c['group'])
        ss={name:mse(d['y'][tr],p,d['lines'][tr]) for name,p in selected.items()}
        r=min(RESTRICTED,key=lambda n:ss[n]);f=min(ORDER,key=lambda n:ss[n])
        ok=indices==c['choices'] and r==c['restricted'] and f==c['full']
        inner_choices.append(dict(scheme=c['scheme'],group=c['group'],matches=ok))
        if not ok:errors.append('inner choice '+c['scheme']+'/'+c['group'])
    if inner_max_error>1e-10:errors.append('inner scores')
    gains={s:1-v['full']['mse']/v['restricted']['mse'] for s,v in summaries.items()}
    wins=sum(summaries['line']['full']['per_line'][l]['mse']<summaries['line']['restricted']['per_line'][l]['mse'] for l in summaries['line']['full']['per_line'])
    nonworse=all(v['full']['regret']<=v['restricted']['regret']+1e-12 for v in summaries.values())
    gate=gains['line']>=.05 and wins>=12 and gains['batch']>0 and nonworse
    if gate!=result['gate'] or wins!=result['strict_line_wins'] or nonworse!=result['top10_nonworse']:errors.append('gate')
    predictions=[]
    for scheme,group in [('line','C4I'),('batch','apollo31')]:
        c=next(c for c in choices if c['scheme']==scheme and c['group']==group)
        tr=np.array(c['train']);query=np.array(c['query']);cache={}
        def get(name):
            if name not in cache:
                if name=='G':cache[name]=(get('C')+get('E'))/2
                else:cache[name]=independent_predict(d,tr,query,name,c['lambda_grid'][c['choices'][name]])
            return cache[name]
        for label in ['restricted','full']:
            name=c[label];own=get(name)
            part=frame[(frame.scheme==scheme)&(frame.program==label)]
            lookup={(r.line,r.gene):r.prediction for r in part.itertuples()}
            reference=np.array([lookup[(d['lines'][i],d['genes'][i])] for i in query])
            delta=float(np.max(np.abs(own-reference)))
            predictions.append(dict(scheme=scheme,group=group,selected=name,n=len(query),max_abs_error=delta))
            if delta>2e-7:errors.append('selected prediction '+scheme+'/'+label)
    report=dict(scope='All stored outer metrics and all stored-inner selection; two outer folds independently refit via direct solve; not full inner-fit reproduction',
                max_metric_error=max_metric_error,max_inner_score_error=inner_max_error,inner_choices=inner_choices,
                selected_prediction_checks=predictions,gains=gains,wins=int(wins),top10_nonworse=nonworse,
                gate=bool(gate),errors=errors,passed=not errors,
                inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'RESULT.json',OUT/'CHOICES.json',OUT/'predictions.csv']})
    (OUT/'skeptic/NUMERICAL.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))
    assert not errors,errors


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
