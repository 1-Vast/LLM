"""Frozen-contract nuisance predictions and ordinary feedback comparators.

Dataset input: source/development compounds; y[:, L/M/H, DNA/LDH], source xH,
all xM, metadata-only designs. Development High values must be absent (NaN).
This module does not choose models or score development.
"""
import itertools
import numpy as np
from linear_models import Blocks,Ridge,ReducedRidge,RBF

LEVELS={'Low':0,'Middle':1,'High':2}


class Data:
    def __init__(self,chem,units,dose,y,sd,xm,xh,source,gene_indices):
        self.chem,self.units,self.dose=chem,units,dose
        self.y,self.sd,self.xm,self.xh=y,sd,xm,xh
        self.source=tuple(source);self.gene_indices=gene_indices
        self.four=np.column_stack([xm[:,indices].mean(1) for indices in gene_indices])

    def design(self,indices,levels):
        indices=np.asarray(indices,dtype=int);levels=np.asarray(levels,dtype=int)
        return [self.chem[indices],self.units[indices],np.column_stack([
            np.log10(self.dose[indices,levels]),
            np.log10(self.dose[indices,2]/self.dose[indices,1])])]

    def rows(self,indices,levels):
        return np.repeat(indices,len(levels)),np.tile(levels,len(indices))


def fit_fixed(blocks,y,alpha,transform,weights):
    model=Ridge();model.transformer=transform
    return model.fit_transformed(transform.transform(blocks),y,alpha,weights)


class Base:
    def __init__(self,data,train,alpha):
        assert set(train)<=set(data.source)
        self.data,self.train,self.alpha=data,tuple(train),alpha
        i,l=data.rows(train,[0,1,2]);self.b=Ridge().fit(data.design(i,l),data.y[i,l],alpha)
        i,l=data.rows(train,[1,2]);design=data.design(i,l)
        x=np.stack([data.xm[j] if level==1 else data.xh[j] for j,level in zip(i,l)])
        self.f=Ridge().fit(design,x,alpha)
        b=self.b.predict(design)
        self.h=Ridge().fit([x,np.concatenate(design,axis=1),b],data.y[i,l]-b,alpha)

    def g(self,x,indices,levels):
        design=self.data.design(indices,levels);b=self.b.predict(design)
        return b+self.h.predict([x,np.concatenate(design,axis=1),b])

    def export(self,query):
        assert not(set(query)&set(self.train))
        data=self.data;n=len(query);dm=data.design(query,[1]*n);dh=data.design(query,[2]*n)
        fm,fh=self.f.predict(dm),self.f.predict(dh)
        # g's derivative with respect to raw fixed-coordinate RNA. No p-by-p map.
        p=data.xm.shape[1]
        slope=self.h.x[:,:p].T@self.h.dual/(self.h.transformer.scales[0]*np.sqrt(3))
        return dict(query=tuple(query),train=self.train,alpha=self.alpha,fm=fm,fh=fh,
            gm=self.g(data.xm[list(query)],query,[1]*n),gmp=self.g(fm,query,[1]*n),
            g0=self.g(fh,query,[2]*n),bm=self.b.predict(dm),bh=self.b.predict(dh),
            slope=slope,transforms=(self.b.transformer,self.f.transformer,self.h.transformer))


def select_record(pack,index):
    pos=pack['query'].index(index)
    return {name:pack[name][pos] for name in ['fm','fh','gm','gmp','g0','bm','bh']} | {
        'slope':pack['slope'],'owner_train':pack['train'],'index':index}


def histories(data,indices,records,outer_excluded=()):
    # No xH/yH is accessed by this function, including for source queries.
    for i,r in zip(indices,records):
        assert r['index']==i and i not in r['owner_train']
        assert not(set(outer_excluded)&set(r['owner_train']))
    fields={name:np.stack([r[name] for r in records]) for name in ['fm','fh','gm','gmp','g0','bm','bh']}
    fields.update(xm=data.xm[list(indices)],ym=data.y[list(indices),1],sd=data.sd[list(indices),1],
                  four=data.four[list(indices)])
    fields['um']=fields['xm']-fields['fm'];fields['vm']=fields['ym']-fields['gm']
    fields['design']=np.concatenate(data.design(indices,[1]*len(indices))+
                                    data.design(indices,[2]*len(indices)),axis=1)
    fields['records']=records
    return fields


def training_targets(data,indices,history):
    assert set(indices)<=set(data.source)
    uh=data.xh[list(indices)]-history['fh']
    gh=history['g0']+np.stack([u@r['slope'] for u,r in zip(uh,history['records'])])
    return dict(uh=uh,vh=data.y[list(indices),2]-gh,yh=data.y[list(indices),2])


def feature_blocks(history,family):
    h=history
    if family=='four_gene':
        return [h['design'],np.c_[h['ym'],h['sd']],h['four'],np.c_[h['bm'],h['bh']]]
    if family=='no_rna':
        return [h['design'],np.c_[h['ym'],h['sd']],h['fm'],h['fh'],np.c_[h['bm'],h['bh']],
                h['gmp'],h['g0'],h['ym']-h['gmp']]
    assert family in {'direct','rbf'}
    return [h['design'],h['xm'],np.c_[h['ym'],h['sd']],h['fm'],h['fh'],h['um'],h['vm'],
            np.c_[h['bm'],h['bh']],h['gm'],h['g0']]


def configurations():
    configs=[]
    for rho in [0.,.5,1.]:
        for alpha,penalty,rank in itertools.product([.1,1.],[.1,1.],[1,2]):
            configs.append(dict(family=f'rho_{rho:g}',alpha=alpha,penalty=penalty,rank=rank,rho=rho))
    for family in ['direct','no_rna','four_gene']:
        for alpha,penalty in itertools.product([.1,1.],[.01,.1,1.,10.]):
            configs.append(dict(family=family,alpha=alpha,penalty=penalty))
    for alpha,penalty,factor in itertools.product([.1,1.],[.1,1.],[.5,2.]):
        configs.append(dict(family='rbf',alpha=alpha,penalty=penalty,factor=factor))
    for alpha,weight in itertools.product([.1,1.],[1.,4.,16.,64.]):
        configs.append(dict(family='refit',alpha=alpha,weight=weight))
    return configs


def feedback_fit_predict(train,targets,query,config,ledger):
    family=config['family'];penalty=config['penalty']
    if family.startswith('rho_'):
        rho=config['rho'];rank=config['rank']
        bx=ReducedRidge().fit([train['um'],train['vm']],targets['uh'],penalty,rank,[1,np.sqrt(rho)])
        by=ReducedRidge().fit([train['um'],train['vm']],targets['vh'],penalty,rank,[np.sqrt(rho),1])
        ledger['estimator_fits']+=2
        dx=bx.predict([query['um'],query['vm']]);dy=by.predict([query['um'],query['vm']])
        routed=np.stack([delta@r['slope'] for delta,r in zip(dx,query['records'])])
        masks={f'{state}{function}':query['g0']+state*routed+function*dy
               for state,function in itertools.product([0,1],repeat=2)}
        return masks['11'],dict(masks=masks,dx=dx)
    blocks=feature_blocks(train,family);qblocks=feature_blocks(query,family)
    baseline='bh' if family=='four_gene' else 'g0'
    if family=='rbf':
        model=RBF().fit(blocks,targets['yh']-train[baseline],penalty,config['factor'])
    else:model=Ridge().fit(blocks,targets['yh']-train[baseline],penalty)
    ledger['estimator_fits']+=1
    return query[baseline]+model.predict(qblocks),{}


def ordinary_refit(data,train,query,alpha,weight,transforms,ledger):
    # Query High is never read, even if query is a held-out source compound.
    assert query not in train
    btransform,ftransform,htransform=transforms
    i,l=data.rows(train,[0,1,2]);i=np.r_[i,query];l=np.r_[l,1]
    weights=np.r_[np.ones(len(i)-1),weight]
    b=fit_fixed(data.design(i,l),data.y[i,l],alpha,btransform,weights)
    i,l=data.rows(train,[1,2]);i=np.r_[i,query];l=np.r_[l,1]
    x=np.stack([data.xm[j] if level==1 else data.xh[j] for j,level in zip(i,l)])
    weights=np.r_[np.ones(len(i)-1),weight];design=data.design(i,l)
    f=fit_fixed(design,x,alpha,ftransform,weights)
    bnew=b.predict(design)
    h=fit_fixed([x,np.concatenate(design,axis=1),bnew],data.y[i,l]-bnew,alpha,htransform,weights)
    dh=data.design([query],[2]);fh=f.predict(dh);bh=b.predict(dh)
    prediction=bh+h.predict([fh,np.concatenate(dh,axis=1),bh])
    ledger['estimator_fits']+=3
    return prediction


def derange_history(history,seed=20261022):
    # One descriptive association null; no raw arrays move between fit owners.
    n=len(history['ym']);rng=np.random.default_rng(seed)
    order=rng.permutation(n);shift=np.roll(order,1);mapping=np.empty(n,dtype=int);mapping[order]=shift
    assert np.all(mapping!=np.arange(n))
    result=dict(history)
    for name in ['xm','ym','sd','four','um','vm','gm']:
        result[name]=history[name][mapping]
    return result,mapping
