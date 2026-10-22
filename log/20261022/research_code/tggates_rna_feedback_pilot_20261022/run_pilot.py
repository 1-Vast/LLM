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
