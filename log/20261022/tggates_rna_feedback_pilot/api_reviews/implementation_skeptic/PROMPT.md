你是实施审查者。下面是首次数值模型执行前的实际代码，而非方案。找出真实bug、泄漏、违反冻结合同、计数错误或缺失关键对照；不要提出扩数据/改门槛/新架构。源24、dev7且High在模型输入中全NaN、later未开。真实CEL已开始独立单阵列转换，但未聚合建模。普通受限联合预测不是新核心。请优先给出可复现问题与最小修正，明确严重度；没发现就说没有。特别审查RR、g derivative、nested owner bank、weighted refit完整重算source残差、devHigh隔离、64配置4336fits预算、source选择偏差、输入聚合数据身份和null关联诊断。下列三项现在定死：四基因共享同一basebank的alpha和同一内外折；weighted deploymentMiddle refit发生在prediction seal之前且无High；null只复用basebank不再拟合base。rho0保留零列与两block尺度；weighted原transform均值/RMS不变但WLS内部居中和截距重算。失败首CEL只有QC accessor修复，旧code/receipt保留。

数值协议修订：
# Frozen numerical protocol: authoritative amendments

Read with the adopted independent contract below. No biological RNA value has been opened when these decisions are frozen. Scope, split, assay units, original utility thresholds, nested fold ownership and stops are adopted unchanged. No new algorithm core is cleared. The experiment can falsify a useful feedback regularization hypothesis, and cannot establish agents, inheritance or RSI.

1. Preprocessing is PREPROCESS_PROTOCOL.md. Use original manufacturer CDF environment through native affy lookup; namespace installation failed. Fixed 54675 probe coordinates. Four-gene mapping is already independently frozen, so add the ordinary four-gene baseline now, before RNA conversion. Its eight configurations: shared b-alpha .1/1, direct penalty .01/.1/1/10. Predict y_H-b_H by ridge from [designM/H, y_M/SD, four mean-log difference gene values, b_M/b_H], with the shared fold-local base b; no actual all-probe x_M in this family. Add b_H. Same eight source-selection configurations.

2. Fit means one estimator coefficient solution, including multioutput with a shared loss. Two correction maps count two fits. A b/f/h pack counts three. Exact base cache uses 301 training sets x2 alphas x3=1806. Corrections:3rho x8configs x24outer x2maps +3selected x2=1158. Direct/KRR/noRNA:3x8x24+3=579. Weighted refit:8x24x3 +7development x3=597. Four-gene:8x24+1=193. Null:2maps+1direct=3. Total conservative ceiling4336 estimator fits. Pipeline evaluations, transform fits, SVD, retries, and cache hits are separate counters. No extra grid, retry selection or uncounted coefficient fits. If exact code factoring yields fewer actual solves, disclose reuse rather than pretend budget was spent. The old 3567 count is an error, not a valid alternative estimator accounting convention.

3. Weighted refit: source observation weights1 and exactly one added compound-mean Middle row weight w in {1,4,16,64}. Original source-fitted input block transforms retained (including original h transform), but weighted centering/intercepts recomputed. For each estimator minimize sum_i w_i||Y_i-predict_i||² + n_rows*alpha||A||². This fixes regularization convention: w acts as multiplicity; denominator is row count, not sum weights. Update b first; recompute b_new for ALL source and query rows, and recompute ALL h targets y-b_new and b-derived features. Update f with source M/H and queryMiddle. Update h using actual states and recomputed residuals. Each update is one coefficient fit, no hidden target. Refit prediction uses updated g(updated f_H,H). No queryHigh RNA/function.

4. One shared nuisance bank for corrections and all direct families. For outer i, inner j nuisance excludes BOTH i,j; targets for j are accessed only after that prediction, and outer i High cannot appear in any train feature/transform. Final error rows use leave-one-source-out; final nuisance is all-source. Fixed probeset coordinates across folds. Same fit/config maps for all 2x2 route masks; no retuning masks. v-only still uses observedRNA. Genuine no-observedRNA family removes all actualRNA-derived features.

5. Low-rank maps use float64 NumPy SVD with fixed software/version receipt, stable sorted singular values and explicit numerical-rank tolerance max(shape)*eps*smax. Q sign cancels in QQ'; no sign-dependent claims. rho0 retains two-block normalization and zeroed cross-block weights. Store low-rank factors. Centered RBF kernel uses a trained intercept. All block scales are training-only energy RMS. Ridge duplicate columns can change effective regularization; report the frozen feature set instead of claiming duplication invariance.

6. Relative to actual strongest nonisomorphic ordinary comparator, useful gain must be strictly >.02 absolute DNA MAE AND >=10% relative. All prior nine families and new ordinary families are reported. rho0's exact ordinary copy merged. Mixture is fixed50/50 and not tuned. Route comparisons and noRNA comparison require strictly lower MAE to support their respective increments; derangement is descriptive only, cannot rescue primary failure or establish significance. No bootstrap is confirmatory. Development already historically exposed. No single-N sample-efficiency claim.

7. Before modeling, code must pass independent primal/dual, weighted WLS, full-rank reduced-ridge identity, collapsed-sequential identity, train-only scaling, and fold-owner/heldoutHigh-sentinel tests. Seal exact numerical code/data/outputs and prediction files before isolated scoring reads developmentHigh function. This does not restore historical blinding. Numerical execution needs a separate code freeze; this protocol only permits the fixed array-local conversion after preprocessing authorization.

8. API audit: first two direct reviews used thinking with9000 completion tokens and returned EMPTY content with finish_reason=length (27264total tokens); these are failed review artifacts, not substantive reviews, despite the original client receipt label RESPONSE_RETAINED. Second calls use no-thinking and retained nonempty texts. Construction advocate and skeptic both treat candidate as ordinary constrained linear prediction. Root rejects reviewers' suggestions that the erroneous3567 count is valid under a second estimator convention, that duplicating ridge inputs never changes predictions, or that Q sign changes predictions. Root accepts source-residual recomputation, literal WLS weights, strict nuisance ownership and separate measurement ablation. Opposing replies and exact costs remain separate from empirical evidence.


--- linear_models.py ---
"""Small-sample dual estimators; fit transformations only on supplied rows."""
import numpy as np
COUNTERS={'transform_fits':0,'coefficient_fits':0,'linear_solves':0,'svd_calls':0}


class Blocks:
    def fit(self, blocks):
        COUNTERS['transform_fits']+=1
        self.means = [np.mean(x, axis=0) for x in blocks]
        self.scales = [float(np.sqrt(np.mean(np.sum((x-m)**2, axis=1)))) or 1.
                       for x,m in zip(blocks,self.means)]
        return self

    def transform(self, blocks, weights=None):
        assert len(blocks) == len(self.means)
        weights = [1.]*len(blocks) if weights is None else weights
        return np.concatenate([(x-m)/s*w for x,m,s,w in
            zip(blocks,self.means,self.scales,weights)],axis=1)/np.sqrt(len(blocks))


class Ridge:
    def fit(self, blocks, y, penalty, weights=None):
        self.transformer=Blocks().fit(blocks)
        return self.fit_transformed(self.transformer.transform(blocks), y, penalty, weights)

    def fit_transformed(self, x, y, penalty, weights=None):
        COUNTERS['coefficient_fits']+=1;COUNTERS['linear_solves']+=1
        n=len(x); assert penalty > 0
        w=np.ones(n) if weights is None else np.asarray(weights,dtype=float)
        assert np.all(w>0)
        self.xmean=np.average(x,axis=0,weights=w)
        self.ymean=np.average(y,axis=0,weights=w)
        # weights are literal observation multiplicities; penalty is n*lambda
        self.x=(x-self.xmean)*np.sqrt(w[:,None])
        self.dual=np.linalg.solve(self.x@self.x.T+n*penalty*np.eye(n),
                                 (y-self.ymean)*np.sqrt(w[:,None]))
        return self

    def predict_transformed(self, x):
        return self.ymean+((x-self.xmean)@self.x.T)@self.dual

    def predict(self, blocks):
        return self.predict_transformed(self.transformer.transform(blocks))


class ReducedRidge:
    def fit(self, blocks, y, penalty, rank, weights):
        COUNTERS['coefficient_fits']+=1;COUNTERS['svd_calls']+=1
        self.transformer=Blocks().fit(blocks)
        self.weights=weights
        x=self.transformer.transform(blocks,weights)
        self.xmean=x.mean(0); self.ymean=y.mean(0)
        u,s,vt=np.linalg.svd(x-self.xmean,full_matrices=False)
        tol=(s[0] if len(s) else 0)*max(x.shape)*np.finfo(float).eps
        keep=s>tol; u,s,vt=u[:,keep],s[keep],vt[keep]
        n=len(x)
        uy=u.T@(y-self.ymean)
        z=(s/np.sqrt(s*s+n*penalty))[:,None]*uy
        if not len(s):
            self.left=np.zeros((x.shape[1],0)); self.right=np.zeros((0,y.shape[1]))
        else:
            COUNTERS['svd_calls']+=1
            _,_,q=np.linalg.svd(z,full_matrices=False)
            q=q[:min(rank,len(s),y.shape[1])].T
            self.left=vt.T@((s/(s*s+n*penalty))[:,None]*(uy@q))
            self.right=q.T
        return self

    def predict(self,blocks):
        x=self.transformer.transform(blocks,self.weights)
        return self.ymean+((x-self.xmean)@self.left)@self.right


class RBF:
    def fit(self,blocks,y,penalty,factor):
        COUNTERS['coefficient_fits']+=1;COUNTERS['linear_solves']+=1
        self.transformer=Blocks().fit(blocks)
        self.x=self.transformer.transform(blocks)
        d=self.dist(self.x,self.x); positive=d[d>0]
        self.bandwidth=factor*np.median(positive) if len(positive) else 1.
        self.ymean=y.mean(0)
        k=np.exp(-d/self.bandwidth)
        # Intercept via centered kernel, consistent for new rows.
        self.kmean=k.mean(0); self.kgrand=k.mean()
        kc=k-self.kmean[None,:]-self.kmean[:,None]+self.kgrand
        self.dual=np.linalg.solve(kc+len(k)*penalty*np.eye(len(k)),y-self.ymean)
        return self

    @staticmethod
    def dist(x,y):
        return np.maximum(np.sum(x*x,1)[:,None]+np.sum(y*y,1)[None,:]-2*x@y.T,0)

    def predict(self,blocks):
        x=self.transformer.transform(blocks)
        k=np.exp(-self.dist(x,self.x)/self.bandwidth)
        kc=k-k.mean(1)[:,None]-self.kmean[None,:]+self.kgrand
        return self.ymean+kc@self.dual


--- pilot_core.py ---
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


--- prepare_numeric_inputs.py ---
"""Build fixed-coordinate input arrays; never cast development High function."""
import csv,hashlib,json,math
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def project_function(rows):
    output=[];casts={'source':0,'development':0}
    for row in rows:
        assert row['role'] in {'source','development'}
        keep={k:row[k] for k in ['compound_label','block_id','role','fingerprint_on_bits','unit']}
        keep['doses']={}
        for level,dose in row['doses'].items():
            result={'concentration':float(dose['concentration'])}
            if row['role']=='source' or level=='Middle':
                for key in ['mean','sd']:
                    result[key]=[float(v) for v in dose[key]]
                    assert all(math.isfinite(v) for v in result[key])
                    casts[row['role']]+=len(result[key])
            keep['doses'][level]=result
        output.append(keep)
    return output,casts


def main():
    dest=P/'numeric_inputs';dest.mkdir(exist_ok=True)
    assert not (dest/'DATA.npz').exists()
    old=ROOT/'log/20261022/tggates_feedback_headroom/CONDITION_MEANS.json'
    # JSON decimal tokens stay strings; only selected means/SD are cast above.
    rows,casts=project_function(json.loads(old.read_text(encoding='utf-8'),parse_float=str))
    rows=sorted(rows,key=lambda x:x['compound_label'])
    assert len(rows)==31 and sum(r['role']=='source' for r in rows)==24
    assert len({r['block_id'] for r in rows})==31
    manifest=json.loads((P/'RNA_IDENTITY_MANIFEST.json').read_text(encoding='utf-8'))
    freeze=json.loads((P/'PREPROCESS_FREEZE_V2.json').read_text(encoding='utf-8'))
    grouped=defaultdict(list);values={};ids=None;inputs={}
    for sample in manifest['samples']:
        identity=sample['identity'];barcode=identity['BARCODE']
        receipt_path=P/'mas5_v2'/(barcode+'.receipt.json')
        receipt=json.loads(receipt_path.read_text())
        assert receipt['status']=='complete' and receipt['protocol_sha256']==freeze['protocol_sha256']
        table=P/'mas5_v2'/(barcode+'.tsv')
        assert receipt['outputs'][str(table)]==sha(table)
        with table.open(newline='',encoding='utf-8') as f:
            records=list(csv.DictReader(f,delimiter='\t'))
        names=[r['probeset'] for r in records]
        assert len(names)==54675 and names==sorted(names) and len(set(names))==54675
        if ids is None:ids=names
        assert names==ids
        vector=np.array([float(r['log2_signal']) for r in records]);assert np.isfinite(vector).all()
        values[barcode]=vector
        grouped[(identity['COMPOUND_NAME'],identity['DOSE_LEVEL'])].append(sample)
        inputs[table.relative_to(ROOT).as_posix()]=sha(table)
    n,p=len(rows),len(ids);xm=np.empty((n,p));xh=np.full((n,p),np.nan)
    y=np.full((n,3,2),np.nan);sd=y.copy();dose=np.empty((n,3));chem=np.zeros((n,2048))
    categories=sorted({r['unit'] for r in rows});units=np.zeros((n,len(categories)));joins=[]
    for i,row in enumerate(rows):
        label=row['compound_label'];control=grouped[(label,'Control')]
        assert len(control)==2
        cmean=np.mean([values[s['identity']['BARCODE']] for s in control],axis=0)
        for level in ['Middle']+(['High'] if row['role']=='source' else []):
            samples=grouped[(label,level)];assert len(samples)==2
            for field in ['EXP_ID','COMPOUND_NO','MATERIAL_ID','ARR_DESIGN','DOSE_UNIT','SACRIFICE_PERIOD']:
                assert len({s['identity'][field] for s in samples+control})==1,(label,level,field)
            assert {s['identity']['INDIVIDUAL_ID'] for s in samples}=={'1','2'}
            assert {Decimal(s['identity']['DOSE']) for s in samples}=={Decimal(str(row['doses'][level]['concentration']))}
            state=np.mean([values[s['identity']['BARCODE']] for s in samples],axis=0)-cmean
            if level=='Middle':xm[i]=state
            else:xh[i]=state
            joins.append(dict(compound=label,level=level,treated=[s['identity']['BARCODE'] for s in samples],
                              controls=[s['identity']['BARCODE'] for s in control]))
        for j,level in enumerate(['Low','Middle','High']):
            dose[i,j]=row['doses'][level]['concentration']
            if row['role']=='source' or level=='Middle':
                y[i,j]=row['doses'][level]['mean'];sd[i,j]=row['doses'][level]['sd']
        chem[i,[int(v) for v in row['fingerprint_on_bits']]]=1
        units[i,categories.index(row['unit'])]=1
    mapping=json.loads((P/'annotation/FOUR_GENE_MAPPING.json').read_text())
    gene_indices=[[ids.index(probe) for probe in mapping['mapping'][gene]] for gene in mapping['genes']]
    source=[i for i,r in enumerate(rows) if r['role']=='source'];dev=[i for i,r in enumerate(rows) if r['role']=='development']
    assert np.isnan(y[dev,2]).all() and np.isnan(xh[dev]).all()
    with (dest/'DATA.npz').open('xb') as f:np.savez(f,chem=chem,units=units,dose=dose,y=y,sd=sd,xm=xm,xh=xh)
    metadata=dict(rows=rows,source=source,development=dev,unit_categories=categories,gene_indices=gene_indices,
        gene_order=mapping['genes'],probesets=ids,joins=joins,function_numeric_casts=casts,
        development_high_function_casts=0,later_function_casts=0,inputs_sha256=inputs,
        historical_function_input_sha256=sha(old),data_sha256=sha(dest/'DATA.npz'))
    with (dest/'METADATA.json').open('x',encoding='utf-8') as f:json.dump(metadata,f,indent=2)
    print(json.dumps(dict(status='PREPARED',arrays=len(values),source=len(source),development=len(dev),
                         development_high_absent=True)))

if __name__=='__main__':main()


--- run_pilot.py ---
"""Run one separately frozen source/development prediction experiment, without scoring devHigh."""
import argparse,hashlib,itertools,json,pickle,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import psutil
from threadpoolctl import threadpool_limits,threadpool_info
from linear_models import COUNTERS
from pilot_core import Data,Base,select_record,histories,training_targets,configurations,feedback_fit_predict,ordinary_refit,derange_history

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False)
def key(c):return json.dumps(c,sort_keys=True,separators=(',',':'))


class Bank:
    def __init__(self,data,source,development,directory,ledger):
        self.data,self.source,self.development=data,tuple(source),tuple(development)
        self.directory=directory;directory.mkdir();self.ledger=ledger;self.index={}

    def name(self,train,alpha):return hashlib.sha256(key(dict(train=sorted(train),alpha=alpha)).encode()).hexdigest()

    def build(self):
        for omitted_count in [2,1,0]:
            for omitted in itertools.combinations(self.source,omitted_count):
                train=tuple(i for i in self.source if i not in omitted)
                query=omitted or self.development
                for alpha in [.1,1.]:
                    name=self.name(train,alpha);path=self.directory/(name+'.pkl')
                    pack=Base(self.data,train,alpha).export(query)
                    with path.open('xb') as f:pickle.dump(pack,f,protocol=5)
                    self.index[name]=dict(file=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                        train=list(train),query=list(query),alpha=alpha)
                    self.ledger['base_packs']+=1;self.ledger['estimator_fits']+=3
            print(json.dumps(dict(stage='bank',omitted=omitted_count,packs=self.ledger['base_packs'])),flush=True)
        write(self.directory/'INDEX.json',self.index)

    def get(self,train,alpha):
        entry=self.index[self.name(train,alpha)];path=ROOT/entry['file']
        assert sha(path)==entry['sha256']
        with path.open('rb') as f:pack=pickle.load(f)
        assert tuple(sorted(train))==pack['train'] and alpha==pack['alpha']
        self.ledger['bank_cache_hits']+=1
        return pack


def training_history(data,bank,train,alpha,outer=()):
    records=[]
    for j in train:
        pack=bank.get([i for i in train if i!=j],alpha)
        records.append(select_record(pack,j))
    h=histories(data,train,records,outer)
    return h,training_targets(data,train,h)


def execute(freeze):
    meta=json.loads((P/'numeric_inputs/METADATA.json').read_text(encoding='utf-8'))
    with np.load(P/'numeric_inputs/DATA.npz',allow_pickle=False) as raw:
        data=Data(**{k:raw[k] for k in ['chem','units','dose','y','sd','xm','xh']},
                  source=meta['source'],gene_indices=meta['gene_indices'])
    source,dev=meta['source'],meta['development']
    assert len(source)==24 and len(dev)==7
    assert np.isnan(data.y[dev,2]).all() and np.isnan(data.xh[dev]).all()
    assert np.isfinite(data.y[source]).all() and np.isfinite(data.xm).all() and np.isfinite(data.xh[source]).all()
    configs=sorted(configurations(),key=key)
    assert configs==freeze['configurations']
    ledger=dict(status='STARTED',estimator_fits=0,base_packs=0,bank_cache_hits=0,pipeline_evaluations=0)
    start=time.monotonic();journal=P/'NUMERICAL_JOURNAL.jsonl'
    write(P/'NUMERICAL_STARTED.json',dict(utc=datetime.now(timezone.utc).isoformat(),freeze=freeze,
        software=dict(numpy=np.__version__,threadpool=threadpool_info()),source=source,development=dev))
    try:
        bank=Bank(data,source,dev,P/'nuisance_bank',ledger);bank.build()
        predictions={key(c):[] for c in configs};states={key(c):[] for c in configs if c['family'].startswith('rho_')}
        for outer in source:
            train=[i for i in source if i!=outer]
            for alpha in [.1,1.]:
                h,target=training_history(data,bank,train,alpha,[outer])
                pack=bank.get(train,alpha);q=histories(data,[outer],[select_record(pack,outer)])
                for c in configs:
                    if c['alpha']!=alpha:continue
                    if c['family']=='refit':
                        pred=ordinary_refit(data,train,outer,alpha,c['weight'],pack['transforms'],ledger);extra={}
                    else:pred,extra=feedback_fit_predict(h,target,q,c,ledger)
                    assert np.isfinite(pred).all(),c
                    predictions[key(c)].append(dict(index=outer,prediction=pred[0].tolist()))
                    if 'dx' in extra:
                        states[key(c)].append(dict(index=outer,
                            prior_mse=float(np.mean((data.xh[outer]-pack['fh'][0])**2)),
                            updated_mse=float(np.mean((data.xh[outer]-pack['fh'][0]-extra['dx'][0])**2))))
                    ledger['pipeline_evaluations']+=1
            with journal.open('a',encoding='utf-8') as f:
                f.write(json.dumps(dict(stage='source_outer_complete',outer=outer,**ledger))+'\n')
            print(json.dumps(dict(stage='source_outer_complete',outer=outer,fits=ledger['estimator_fits'])),flush=True)
        scores=[]
        for c in configs:
            pred=np.array([r['prediction'] for r in predictions[key(c)]])
            assert [r['index'] for r in predictions[key(c)]]==source
            scores.append(dict(config=c,dna_mae=float(np.mean(np.abs(pred[:,0]-data.y[source,2,0])))))
        selected={}
        for item in scores:
            family=item['config']['family']
            if family not in selected or (item['dna_mae'],key(item['config'])) < (selected[family]['dna_mae'],key(selected[family]['config'])):
                selected[family]=item
        write(P/'SOURCE_FIXED_CONFIG_PREDICTIONS.json',predictions)
        write(P/'SOURCE_STATE_ERRORS.json',states)
        write(P/'SOURCE_SELECTION.json',dict(scores=scores,selected=selected,selection_exposed=True))
        final={};route_masks=None
        for family,item in selected.items():
            c=item['config'];alpha=c['alpha'];pack=bank.get(source,alpha)
            if family=='refit':
                pred=np.concatenate([ordinary_refit(data,source,j,alpha,c['weight'],pack['transforms'],ledger) for j in dev])
                ledger['pipeline_evaluations']+=len(dev)
            else:
                h,target=training_history(data,bank,source,alpha)
                q=histories(data,dev,[select_record(pack,j) for j in dev])
                pred,extra=feedback_fit_predict(h,target,q,c,ledger)
                if family=='rho_0':route_masks={k:v.tolist() for k,v in extra['masks'].items()}
                ledger['pipeline_evaluations']+=1
            assert np.isfinite(pred).all();final[family]=pred.tolist()
        final['fixed_half_mixture']=(.5*np.array(final['rho_0'])+.5*np.array(final['direct'])).tolist()
        nulls={};null_mapping={}
        for family in ['rho_0','direct']:
            c=selected[family]['config'];alpha=c['alpha'];pack=bank.get(source,alpha)
            h,target=training_history(data,bank,source,alpha);h,mapping=derange_history(h)
            q=histories(data,dev,[select_record(pack,j) for j in dev])
            pred,_=feedback_fit_predict(h,target,q,c,ledger)
            nulls[family]=pred.tolist();null_mapping[family]=mapping.tolist()
            ledger['pipeline_evaluations']+=1
        assert ledger['estimator_fits']==4336,ledger
        assert COUNTERS['coefficient_fits']==4336,COUNTERS
        assert ledger['base_packs']==602 and ledger['pipeline_evaluations']==1552
        write(P/'DEVELOPMENT_RNA_PREDICTIONS.json',dict(indices=dev,labels=[meta['rows'][j]['compound_label'] for j in dev],
            predictions=final,route_masks=route_masks,nulls=nulls,null_mapping=null_mapping,
            development_high_function_read=False))
        ledger.update(status='PREDICTIONS_COMPLETE_UNSCORED',operations=dict(COUNTERS),
            elapsed_seconds=time.monotonic()-start,
            peak_working_set_bytes=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss))
        write(P/'NUMERICAL_RECEIPT.json',ledger)
        paths=[P/'DEVELOPMENT_RNA_PREDICTIONS.json',P/'NUMERICAL_RECEIPT.json',P/'SOURCE_SELECTION.json',
               P/'numeric_inputs/DATA.npz',P/'numeric_inputs/METADATA.json']
        write(P/'PREDICTION_SEAL.json',dict(status='SEALED_BEFORE_SEPARATE_DEVELOPMENT_SCORING',
            utc=datetime.now(timezone.utc).isoformat(),files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
            code=freeze['artifacts_sha256']))
    except Exception as e:
        ledger.update(status='FAILED_RETAINED',error=f'{type(e).__name__}: {e}',operations=dict(COUNTERS),elapsed_seconds=time.monotonic()-start)
        write(P/'NUMERICAL_FAILURE.json',ledger)
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',type=Path,required=True);args=parser.parse_args()
    freeze=json.loads(args.freeze.read_text(encoding='utf-8'))
    assert freeze['numerical_execution_authorized'] is True
    for path,digest in freeze['artifacts_sha256'].items():assert sha(ROOT/path)==digest,path
    for name in COUNTERS:COUNTERS[name]=0
    with threadpool_limits(limits=1):execute(freeze)

if __name__=='__main__':main()


--- score_pilot.py ---
"""Separate scorer: verify sealed forecasts, then cast only already-exposed devHigh means."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
OLD=ROOT/'log/20261022/tggates_feedback_headroom'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def evaluate(predictions,target,labels,masks):
    scores={};losses={}
    for family,pred in predictions.items():
        value=np.asarray(pred);assert value.shape==target.shape and np.isfinite(value).all()
        err=np.abs(value-target)
        scores[family]=dict(dna_mae=float(err[:,0].mean()),ldh_mae=float(err[:,1].mean()))
        losses[family]=[dict(label=label,dna_absolute_error=float(e[0]),ldh_absolute_error=float(e[1])) for label,e in zip(labels,err)]
    ordinary=[name for name in predictions if name!='rho_0' and not name.startswith('route_') and not name.startswith('null_')]
    best=min(ordinary,key=lambda name:(scores[name]['dna_mae'],name))
    candidate=scores['rho_0']['dna_mae'];baseline=scores[best]['dna_mae']
    absolute=baseline-candidate;relative=absolute/baseline if baseline>0 else 0.
    utility=absolute>.02 and relative>=.1
    state_increment=candidate<scores['route_01']['dna_mae']
    function_increment=candidate<scores['route_10']['dna_mae']
    observed_increment=candidate<scores['no_rna']['dna_mae']
    proceed=utility and state_increment and function_increment and observed_increment
    return dict(status='DEVELOPMENT_ONLY_NOT_CONFIRMATORY',scores=scores,losses=losses,
        strongest_nonisomorphic_ordinary=best,absolute_dna_gain=absolute,relative_dna_gain=relative,
        useful_gain_gate=utility,state_route_increment=state_increment,function_route_increment=function_increment,
        observed_rna_increment=observed_increment,
        decision='GO_ONLY_TO_NEW_QUALIFICATION_NOT_RSI_PROOF' if proceed else 'STOP_THIS_CONFIGURATION_EXPANSION',
        agent_benefit='NOT_TESTED',inheritance_benefit='NOT_TESTED',rsi_c4='NOT_TESTED',later_opened=False)


def main():
    assert not (P/'RNA_PILOT_RESULT.json').exists()
    seal=json.loads((P/'PREDICTION_SEAL.json').read_text())
    assert seal['status']=='SEALED_BEFORE_SEPARATE_DEVELOPMENT_SCORING'
    for relative,digest in dict(seal['files'],**seal['code']).items():assert sha(ROOT/relative)==digest,relative
    new=json.loads((P/'DEVELOPMENT_RNA_PREDICTIONS.json').read_text());labels=new['labels']
    rows=json.loads((OLD/'CONDITION_MEANS.json').read_text(encoding='utf-8'),parse_float=str)
    selected={r['compound_label']:r for r in rows if r['role']=='development'}
    assert set(labels)==set(selected) and len(labels)==7
    target=np.asarray([[float(v) for v in selected[label]['doses']['High']['mean']] for label in labels])
    predictions=dict(new['predictions'])
    old=json.loads((OLD/'DEVELOPMENT_PREDICTIONS.json').read_text(),parse_float=str)
    for family,records in old.items():
        lookup={r['compound_label']:r for r in records}
        assert set(lookup)==set(labels)
        # Old target fields are skipped. These predictions were already frozen in the earlier phase.
        predictions['prior_'+family]=[[float(v) for v in lookup[label]['prediction']] for label in labels]
    predictions.update({'route_'+k:v for k,v in new['route_masks'].items()})
    predictions.update({'null_'+k:v for k,v in new['nulls'].items()})
    result=evaluate(predictions,target,labels,new['route_masks'])
    result.update(prediction_seal_sha256=sha(P/'PREDICTION_SEAL.json'),
        development_high_function_casts=14,later_function_casts=0,development_high_rna_opened=False,
        warning='Historical development exposure and source selection remain; intervals would be descriptive only.')
    with (P/'RNA_PILOT_RESULT.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in {'scores','losses'}},indent=2))

if __name__=='__main__':main()


--- test_pilot_core.py ---
"""Synthetic ownership and end-to-end comparator tests; no real RNA loaded."""
import copy,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pilot_core import Data,Base,select_record,histories,training_targets,configurations,feedback_fit_predict,ordinary_refit,derange_history


class PilotTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(9321);n,p=7,9
        y=rng.normal(size=(n,3,2));y[-1,[0,2]]=np.nan
        xh=rng.normal(size=(n,p));xh[-1]=np.nan
        self.data=Data(rng.integers(0,2,size=(n,12)),np.eye(2)[np.arange(n)%2],
            np.tile([1.,3.,10.],(n,1)),y,np.full((n,3,2),.1),rng.normal(size=(n,p)),xh,
            range(6),[[0,1],[2],[3],[4,5]])

    def make(self,data,outer=0):
        train=[i for i in data.source if i!=outer];records=[]
        for j in train:
            pack=Base(data,[i for i in train if i!=j],.1).export([j])
            records.append(select_record(pack,j))
        h=histories(data,train,records,[outer]);t=training_targets(data,train,h)
        pack=Base(data,train,.1).export([outer]);q=histories(data,[outer],[select_record(pack,outer)])
        return train,h,t,pack,q

    def test_all64_configurations_and_expected_source_fit_count(self):
        counts={}
        for c in configurations():counts[c['family']]=counts.get(c['family'],0)+1
        self.assertEqual(set(counts.values()),{8});self.assertEqual(len(counts),8)
        source_fits=24*(3*8*2+4*8+8*3)
        final_fits=3*2+3+7*3+1+3
        self.assertEqual(301*2*3+source_fits+final_fits,4336)

    def test_heldout_high_sentinel_changes_no_comparator_forecast(self):
        a=self.make(self.data)
        changed=copy.deepcopy(self.data);changed.y[0,2]=1e15;changed.xh[0]=1e15
        b=self.make(changed)
        for config in configurations():
            if config['alpha']!=.1:continue
            led={'estimator_fits':0}
            if config['family']=='refit':
                pa=ordinary_refit(self.data,a[0],0,.1,config['weight'],a[3]['transforms'],led)
                pb=ordinary_refit(changed,b[0],0,.1,config['weight'],b[3]['transforms'],led)
            else:
                pa,_=feedback_fit_predict(a[1],a[2],a[4],config,led)
                pb,_=feedback_fit_predict(b[1],b[2],b[4],config,led)
            np.testing.assert_allclose(pa,pb,atol=1e-11,err_msg=str(config))

    def test_real_no_observed_rna_family_ignores_queried_rna(self):
        a=self.make(self.data)
        changed=copy.deepcopy(self.data);changed.xm[0]*=1e7
        b=self.make(changed)
        config=dict(family='no_rna',alpha=.1,penalty=.1)
        pa,_=feedback_fit_predict(a[1],a[2],a[4],config,{'estimator_fits':0})
        pb,_=feedback_fit_predict(b[1],b[2],b[4],config,{'estimator_fits':0})
        np.testing.assert_allclose(pa,pb,atol=1e-11)

    def test_g_derivative_matches_actual_composition_and_mask_identity(self):
        train,h,t,pack,q=self.make(self.data)
        base=Base(self.data,train,.1)
        config=dict(family='rho_0',alpha=.1,penalty=.1,rank=2,rho=0.)
        prediction,extra=feedback_fit_predict(h,t,q,config,{'estimator_fits':0})
        actual=base.g(pack['fh']+extra['dx'],[0],[2])
        delta_function=extra['masks']['01']-extra['masks']['00']
        np.testing.assert_allclose(prediction,actual+delta_function,atol=1e-11)
        np.testing.assert_allclose(extra['masks']['11']-extra['masks']['10'],delta_function,atol=1e-11)

    def test_bad_fold_owner_is_rejected(self):
        train,h,t,pack,q=self.make(self.data)
        bad=copy.deepcopy(h['records']);bad[0]['owner_train']+=(0,)
        with self.assertRaises(AssertionError):histories(self.data,train,bad,[0])

    def test_development_high_absent_yet_all_methods_forecast(self):
        d=self.data;train=list(d.source);records=[]
        for j in train:
            p=Base(d,[i for i in train if i!=j],.1).export([j]);records.append(select_record(p,j))
        h=histories(d,train,records);t=training_targets(d,train,h)
        pack=Base(d,train,.1).export([6]);q=histories(d,[6],[select_record(pack,6)])
        for config in configurations():
            if config['alpha']!=.1:continue
            led={'estimator_fits':0}
            if config['family']=='refit':p=ordinary_refit(d,train,6,.1,config['weight'],pack['transforms'],led)
            else:p,_=feedback_fit_predict(h,t,q,config,led)
            self.assertTrue(np.isfinite(p).all(),str(config))

    def test_diagnostic_derangement_moves_paired_bundle_only(self):
        _,h,_,_,_=self.make(self.data)
        moved,order=derange_history(h)
        self.assertTrue(np.all(order!=np.arange(len(order))))
        for name in ['um','vm','ym','xm']:
            np.testing.assert_array_equal(moved[name],h[name][order])
        for name in ['fh','fm','g0','bm','bh','design']:
            np.testing.assert_array_equal(moved[name],h[name])

if __name__=='__main__':unittest.main()


--- test_linear_models.py ---
"""Numerical identities and fold ownership; fixtures contain no biological values."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from linear_models import Blocks,Ridge,ReducedRidge,RBF

class NumericalTests(unittest.TestCase):
    def setUp(self):
        self.rng=np.random.default_rng(15079)
        self.x=self.rng.normal(size=(12,7));self.y=self.rng.normal(size=(12,5))
        self.q=self.rng.normal(size=(4,7))

    def test_dual_matches_primal_and_unpenalized_intercept(self):
        model=Ridge().fit([self.x],self.y,.3)
        x=model.transformer.transform([self.x]);q=model.transformer.transform([self.q])
        a=np.linalg.solve((x-x.mean(0)).T@(x-x.mean(0))+12*.3*np.eye(7),
                          (x-x.mean(0)).T@(self.y-self.y.mean(0)))
        np.testing.assert_allclose(model.predict([self.q]),self.y.mean(0)+(q-x.mean(0))@a,atol=1e-12)

    def test_full_rank_reduced_ridge_equals_ridge(self):
        full=Ridge().fit([self.x],self.y,.3)
        reduced=ReducedRidge().fit([self.x],self.y,.3,5,[1])
        np.testing.assert_allclose(full.predict([self.q]),reduced.predict([self.q]),atol=1e-12)

    def test_weighted_dual_matches_weighted_primal(self):
        w=np.arange(1,13,dtype=float)
        m=Ridge().fit([self.x],self.y,.3,w)
        x=m.transformer.transform([self.x]);q=m.transformer.transform([self.q])
        xc=x-np.average(x,axis=0,weights=w);ym=np.average(self.y,axis=0,weights=w)
        a=np.linalg.solve(xc.T@(xc*w[:,None])+12*.3*np.eye(7),xc.T@((self.y-ym)*w[:,None]))
        np.testing.assert_allclose(m.predict([self.q]),ym+(q-m.xmean)@a,atol=1e-12)

    def test_no_test_row_influences_transform_or_fit(self):
        before=Ridge().fit([self.x],self.y,.3).predict([self.q[:1]])
        altered=self.q.copy();altered[1:]*=1e9
        after=Ridge().fit([self.x],self.y,.3).predict([altered])[:1]
        np.testing.assert_allclose(before,after,atol=1e-12)

    def test_rank_bound_and_constant_block(self):
        m=ReducedRidge().fit([self.x,np.ones((12,2))],self.y,.3,1,[1,0])
        pred=m.predict([self.q,np.ones((4,2))])-m.ymean
        self.assertLessEqual(np.linalg.matrix_rank(pred,tol=1e-10),1)
        self.assertTrue(np.isfinite(pred).all())

    def test_rbf_constant_target_and_constant_input(self):
        m=RBF().fit([np.ones((12,3))],np.ones((12,2)),.3,.5)
        np.testing.assert_allclose(m.predict([np.ones((4,3))]),1)

    def test_sequential_linear_correction_collapses_exactly(self):
        # Independent explicit collapsed expression checks no hidden nonlinear claim.
        p,q=7,2; u=self.rng.normal(size=(4,p));v=self.rng.normal(size=(4,q))
        f=self.rng.normal(size=(4,p));cx=self.rng.normal(size=(p,p));cy=self.rng.normal(size=(q,q))
        g=self.rng.normal(size=(p,q));b=self.rng.normal(size=q)
        sequential=(f+u@cx)@g+b+v@cy
        collapsed=f@g+b+u@(cx@g)+v@cy
        np.testing.assert_allclose(sequential,collapsed,atol=1e-12)

if __name__=='__main__':unittest.main()
