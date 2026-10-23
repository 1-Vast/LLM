"""Independent S4 coordinate and complete fixed-pair ridge audit; no main-module import."""
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import hashlib
import json
import time
import zipfile
import xml.etree.ElementTree as X
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/cdk_functional_increment'
OLD = ROOT / 'log/20261022/cdk_middle_feedback'
DEST = PHASE / 'audit'
SOURCE = ROOT / 'log/20261022/next_mechanism/source/cdk_review/table_s4.body'
URI = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def original_selected(tasks):
    names = {f'{er}_{drug}R_{rep}': i for i, (drug, er, rep) in enumerate(tasks)}
    values = np.full((len(tasks), 2), np.nan)
    records, coordinates, seen = [], [], set()
    with zipfile.ZipFile(SOURCE) as z:
        shared = list(X.fromstring(z.read('xl/sharedStrings.xml')))
        sheet = X.fromstring(z.read('xl/worksheets/sheet1.xml'))
        def value(cell):
            if cell is None:
                return ''
            assert cell.find(URI+'f') is None
            v = cell.find(URI+'v')
            if cell.get('t') == 'inlineStr':
                return ''.join(n.text or '' for n in cell.iter(URI+'t'))
            if v is None:
                return ''
            if cell.get('t') == 's':
                return ''.join(n.text or '' for n in shared[int(v.text)].iter(URI+'t'))
            return v.text or ''
        for row in sheet.iter(URI+'row'):
            cells = {''.join(filter(str.isalpha,c.get('r'))): c for c in row}
            if 'B' not in cells:
                continue
            name = value(cells['B']).strip()  # identity metadata only for other rows
            if name not in names:
                assert name == 'Samples' or '_Vehicle_' in name
                continue  # never decode vehicle C/D
            assert name not in seen
            seen.add(name)
            for j,col in enumerate(('C','D')):
                raw = value(cells.get(col)).strip()
                if raw not in ('','N/A'):
                    parsed = float(raw)
                    assert np.isfinite(parsed) and parsed > 0
                    values[names[name], j] = parsed
                record = dict(sample=name,task=tasks[names[name]],column=col,raw=raw,
                              eligible=bool(np.isfinite(values[names[name],j])))
                records.append(record)
                coordinates.append(dict(record, cell=f'{col}{row.get("r")}'))
    assert seen == set(names)
    return values, records, coordinates


def independent_predictions(features, y, group, train, pair, penalty):
    # Center explicit sqrt features within SOURCE condition. No global Q matrix.
    subsets = {g:[i for i in train if group[i]==g] for g in set(group)}
    means = {g: features[ids if ids else train].mean(axis=0) for g,ids in subsets.items()}
    source_x = np.stack([features[i]-means[group[i]] for i in train])
    test_x = np.stack([features[i]-means[group[i]] for i in pair])
    rank = np.empty(len(train))
    for k,i in enumerate(train):
        ids = subsets[group[i]]
        rank[k] = sum(float(y[j]<y[i])+.5*float(y[j]==y[i]) for j in ids)/len(ids)
    centers = {g:float(np.mean([rank[k] for k,i in enumerate(train) if group[i]==g]))
               if ids else float(rank.mean()) for g,ids in subsets.items()}
    residual = rank - np.array([centers[group[i]] for i in train])
    gram = source_x @ source_x.T
    scale = float(np.diag(gram).mean())
    scale = scale if scale > 1e-12 else 1.
    # Independent spectral ridge implementation, rather than main linear solve.
    eig,vec = np.linalg.eigh(gram)
    coef = vec @ ((vec.T @ residual)/(eig+penalty*scale))
    pred = np.array([centers[group[i]] for i in pair])+test_x @ source_x.T @ coef
    return pred, [centers[group[i]] for i in pair], [not subsets[group[i]] for i in pair]


def main():
    started=time.perf_counter()
    assert (PHASE/'RESULT.json').exists(), 'Root execution must complete first'
    assert not (DEST/'NUMERICAL_AUDIT.json').exists(), 'No silent rerun'
    result=json.loads((PHASE/'RESULT.json').read_text())
    prep=json.loads((OLD/'PREPARATION.json').read_text())
    assert result['tasks']==prep['tasks']
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='76e61a74f2574ff0e50bf70e514773ff14a14f3f98225367c6dfcb0818e51345'
    assert hashlib.sha256((OLD/'prepared.npz').read_bytes()).hexdigest()==prep['prepared_sha256']
    values,records,coords=original_selected(result['tasks'])
    assert records==result['source_records']
    # Access materializes the existing full E/M/End member. End is not used.
    composition=np.load(OLD/'prepared.npz')['compositions']
    early=np.sqrt(composition[:,0]); middle=np.sqrt(composition[:,1])
    features={'early':early,'early_middle':np.concatenate((early,middle),axis=1)/np.sqrt(2.)}
    group=[f'{d}_{e}' for d,e,_ in result['tasks']]
    maxdiff=0.; checked=0; challenge_counts={}
    for c,challenge in enumerate(('palbociclib','abemaciclib')):
        y=values[:,c]; saved=result['results'][challenge]
        eligible=np.flatnonzero(np.isfinite(y)).tolist()
        assert saved['eligible']==eligible
        assert saved['missing']==np.flatnonzero(~np.isfinite(y)).tolist()
        expected_rows=[]; ties=[]; nonestimable=[]
        for a,b in combinations(eligible,2):
            if group[a]!=group[b]:continue
            if y[a]==y[b]:ties.append([a,b]);continue
            train=[i for i in eligible if i!=a and i!=b]
            if len(train)<2:
                nonestimable.append(dict(test=[a,b],group=group[a],reason='fewer_than_two_eligible_source_cultures',train=train));continue
            for penalty in (.1,1,10):
                for method, f in features.items():
                    pred,base,fallback=independent_predictions(f,y,group,train,[a,b],penalty)
                    diff=float(pred[0]-pred[1]); loss=.5 if abs(diff)<=1e-12 else float((diff>0)!=(y[a]>y[b]))
                    expected_rows.append(dict(test=[a,b],group=group[a],train=train,method=method,
                        **{'lambda':penalty},predictions=pred.tolist(),baseline=base,
                        pooled_fallback=fallback,loss=loss,truth=[float(y[a]),float(y[b])]))
        assert saved['true_ties']==ties and saved['nonestimable']==nonestimable
        assert len(saved['rows'])==len(expected_rows)
        for row,expected in zip(saved['rows'],expected_rows):
            for k in expected:
                if k=='predictions':
                    err=float(np.max(np.abs(np.array(row[k])-expected[k])));maxdiff=max(maxdiff,err)
                    np.testing.assert_allclose(row[k],expected[k],atol=1e-9,rtol=1e-9)
                elif k=='baseline':np.testing.assert_allclose(row[k],expected[k],atol=1e-14,rtol=0)
                else:assert row[k]==expected[k],(challenge,k,row,expected)
            checked+=1
        for penalty in (.1,1,10):
            for method in features:
                rows=[r for r in expected_rows if r['lambda']==penalty and r['method']==method]
                losses=defaultdict(list)
                for r in rows:losses[r['group']].append(r['loss'])
                groups={g:float(np.mean(l)) for g,l in sorted(losses.items())}
                macro=float(np.mean(list(groups.values()))) if groups else None
                assert saved['summary'][str(penalty)][method]==dict(group_loss=groups,macro_loss=macro,pairs=len(rows))
        assert saved['condition_baseline_loss']==(.5 if expected_rows else None)
        challenge_counts[challenge]=dict(eligible=len(eligible),missing=len(y)-len(eligible),
                                       true_tie_pairs=len(ties),nonestimable_pairs=len(nonestimable),row_checks=len(expected_rows))
    report=dict(status='PASS',scope='Independent original selected S4 joins and all fixed pair/lambda predictions and metrics; no new tuning',
       source_coordinate_records=coords,vehicle_outcomes_decoded=0,prediction_rows_checked=checked,
       maximum_prediction_difference=maxdiff,challenge_counts=challenge_counts,
       End_scope='Full authorized NPZ member materialized; only Early/Middle used; End never in feature/fitting/evaluation computations',
       raw_S3_recertification=False,wall_seconds=time.perf_counter()-started,
       code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (DEST/'NUMERICAL_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_coordinate_records'},indent=2))

if __name__=='__main__':main()
