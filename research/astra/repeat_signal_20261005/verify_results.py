"""Second implementation of saved labels/metrics, using csv + scalar aggregation.

This is not an independent agent review. It never changes frozen outputs.
"""
import csv,json,collections,math
import numpy as np
import pandas as pd
from .analyze import HERE,ROOT,SOURCE,HIERARCHY,sha256,open_vault,plain,dump


def run():
    ticket=open_vault(HERE/'freeze.json',HERE/'outcome_access.jsonl',purpose='Post hoc second-implementation reconstruction of selected R1/R2/R3 labels and policy counts',source=SOURCE,root=ROOT)
    pairs=pd.read_csv(HERE/'results/paired_actions.csv.gz',dtype={'ANCHOR_ID':str,'LIBRARY_ID':str})
    plate={r['BARCODE']:r for r in csv.DictReader(HIERARCHY.open())}
    selected=set()
    for r in pairs.to_dict('records'):
        for i in [1,2,3]:
            if isinstance(r[f'event{i}'],str):selected.add((r['SIDM'],r['ANCHOR_ID'],r['LIBRARY_ID'],r[f'event{i}']))
    gathered=collections.defaultdict(lambda:collections.defaultdict(list))
    with SOURCE.open() as handle:
        for r in csv.DictReader(handle):
            k=(r['SIDM'],r['ANCHOR_ID'],r['LIBRARY_ID'],plate[r['BARCODE']]['event'])
            if k not in selected:continue
            vals=[float(r[c]) for c in ['SYNERGY_DELTA_EMAX','SYNERGY_OBS_EMAX','SYNERGY_RMSE','LIBRARY_RMSE']]
            if not all(math.isfinite(v) for v in vals) or vals[2]>.2 or vals[3]>.2:continue
            syn=r['Synergy'].strip().upper() in ['TRUE','1','1.0']
            gathered[k][r['ANCHOR_CONC']].append((vals[0],syn))
    checks=0;maxerr=0
    for r in pairs.to_dict('records'):
        for i in [1,2,3]:
            if not isinstance(r[f'event{i}'],str):continue
            g=gathered[(r['SIDM'],r['ANCHOR_ID'],r['LIBRARY_ID'],r[f'event{i}'])]
            assert len(g)==2
            y=max(sum(z[0] for z in a)/len(a) for a in g.values())
            hit=any(sum(z[1] for z in a)/len(a)>=.5 for a in g.values())
            strict=any(sum(z[1] for z in a)/len(a)>.5 for a in g.values())
            error=abs(y-r[f'y{i}']);maxerr=max(maxerr,error)
            assert error<1e-12 and hit==bool(r[f'hit{i}']) and strict==bool(r[f'strict_hit{i}'])
            checks+=1
    main=json.loads((HERE/'results/summary.json').read_text())
    pearson=[]
    for _,line in pairs.groupby('SIDM'):
        pearson.append(np.mean([np.corrcoef(g.y1,g.y2)[0,1] for _,g in line.groupby('role')]))
    assert abs(np.mean(pearson)-main['main']['pearson']['mean'])<1e-12
    predictions=pd.read_csv(HERE/'rna_results/predictions.csv.gz')
    rna=json.loads((HERE/'rna_results/summary.json').read_text())
    assert rna['training_evaluation_overlap']==0
    train={s for v in rna['folds'].values() for s in v};test=set(predictions.SIDM)
    assert not train & test and len(train)==111 and len(test)==14
    role_results=[];policy_rows=0
    for (t,s,role),g in predictions.groupby(['Tissue','SIDM','role']):
        rr={'Tissue':t,'SIDM':s,'role':role}
        for arm in ['simple','rna','shuffled']:
            rank=sorted(g.to_dict('records'),key=lambda r:(-r[f'{arm}_score'],r['pair']))
            k=math.ceil(.2*len(rank));first=rank[:k];M=k;ns=math.floor(.7*M)
            screened=rank[:ns];verify=[r for r in screened if r['hit1']][:M-ns]
            rr[f'R2_positive_{arm}']=sum(bool(r['hit2']) for r in first)
            rr[f'P2_confirmed_{arm}']=sum(bool(r['hit2']) for r in verify)
            assert ns+len(verify)<=M
            policy_rows+=1
        role_results.append(rr)
    means=pd.DataFrame(role_results).groupby('SIDM').mean(numeric_only=True).mean()
    for k,v in means.items():assert abs(v-rna['summary'][k]['mean'])<1e-12
    frozen={}
    for name in ['freeze.json','freeze_matched.json','freeze_rna.json']:
        files=json.loads((HERE/name).read_text())['files']
        bad=[p for p,h in files.items() if sha256(ROOT/p)!=h]
        assert not bad;frozen[name]={'checked':len(files),'mismatched':bad}
    result={'label':'Second implementation by the same executor, not independent-agent verification','event_labels_reconstructed':checks,'max_absolute_delta_error':maxerr,'primary_pearson_reconstructed':float(np.mean(pearson)), 'policy_runs_reconstructed':policy_rows,'training_lines':len(train),'evaluation_lines':len(test),'overlap':0,'freezes':frozen,'status':'PASS','ticket':ticket}
    dump(HERE/'verification.json',plain(result));print(json.dumps(plain(result)))

if __name__=='__main__':run()
