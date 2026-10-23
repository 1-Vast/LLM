"""Independent raw CSV / augmented-least-squares reconstruction, no main import."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT/'log/20261023/organoid_schedule_forecast'
DEST = LOG/'source/RESULT_AUDIT.json'
ARCHIVE = ROOT/'log/20261023/organoid_schedule_qualification/root/zenodo_archive.body'
DOMAINS = {'FAC': list('abcdef'), 'OLA-IBET': list('ab')}


def model_matrix(rows, domain, center, scale):
    values = []
    for row in rows:
        z0, z1 = [(row[k]-center[j])/scale[j] for j,k in enumerate(('t0','t1'))]
        flags = [float(row['seq'] == c) for c in domain]
        values.append([z0,z1]+flags+[v*z0 for v in flags]+[v*z1 for v in flags])
    return np.asarray(values)


def estimate(train, query, domain, center, scale):
    x, q = [model_matrix(r,domain,center,scale) for r in (train,query)]
    y = np.asarray([r['cv'] for r in train])
    xm, ym = x.mean(axis=0), y.mean()
    # Independently solve augmented least squares rather than normal equations.
    design = np.vstack((x-xm, np.eye(x.shape[1])))
    response = np.concatenate((y-ym, np.zeros(x.shape[1])))
    coeff = np.linalg.lstsq(design,response,rcond=None)[0]
    ridge = (ym+(q-xm)@coeff).tolist()
    neighbors, local = [], []
    for row in query:
        distances = [sum(((row[k]-r[k])/scale[j])**2 for j,k in enumerate(('t0','t1')))
                     + (0 if row['seq']==r['seq'] else 2) for r in train]
        indices = [i for i,d in enumerate(distances) if d == min(distances)]
        neighbors.append(indices)
        local.append(float(np.asarray([train[i]['cv'] for i in indices]).mean()))
    return {'ridge':ridge,'mean':[float(ym)]*len(query),'nn':local}, neighbors


def loss(y, p):
    e = [a-b for a,b in zip(p,y)]
    return {'mae':math.fsum(abs(v) for v in e)/len(e),
            'mse':math.fsum(v*v for v in e)/len(e)}


if __name__ == '__main__':
    freeze = json.loads((LOG/'FREEZE.json').read_text())
    for p,h in freeze['files'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    forecast_file = LOG/'pilot/FORECASTS.json'
    forecasts = json.loads(forecast_file.read_text())
    seals = json.loads((LOG/'pilot/FORECAST_SEAL.json').read_text())
    assert hashlib.sha256(forecast_file.read_bytes()).hexdigest()==seals['sha256']
    stored = json.loads((LOG/'pilot/RESULT.json').read_text())
    tables, raw_tokens = {}, {}
    with zipfile.ZipFile(ARCHIVE) as z:
        for campaign in DOMAINS:
            names = [n for n in z.namelist() if n.endswith('/'+campaign+'/sequential/data/data_'+campaign+'_seq.csv')]
            assert len(names)==1
            rows = list(csv.DictReader(io.StringIO(z.read(names[0]).decode('utf-8-sig'))))
            raw_tokens[campaign] = [{k:r[k] for k in ('seq','t0','t1','cv','gen','number')} for r in rows]
            tables[campaign] = [dict(seq=r['seq'],t0=float(r['t0']),t1=float(r['t1']),cv=float(r['cv']),
                                     gen=int(r['gen']),number=int(r['number'])) for r in rows]
    checks = []
    def verify(name, expected, actual):
        difference=abs(float(expected)-float(actual))
        assert difference <= 1e-9*max(1.,abs(float(expected))), (name,expected,actual)
        checks.append((name,difference))
    batches, campaign_results, scalers = [], {}, {}
    point_errors = []
    for campaign, rows in tables.items():
        initial = [r for r in rows if r['gen']==0]
        raw_x = np.asarray([[r['t0'],r['t1']] for r in initial])
        center, scale = raw_x.mean(axis=0), raw_x.std(axis=0)
        scale[scale==0]=1
        scalers[campaign]={'mean':center.tolist(),'population_sd':scale.tolist()}
        predictions_by_gen = {}
        for g in sorted({r['gen'] for r in rows}-{0}):
            query = [r for r in rows if r['gen']==g]
            history = [r for r in rows if r['gen']<g]
            f = next(x for x in forecasts if x['campaign']==campaign and x['gen']==g)
            score = next(x for x in stored['batches'] if x['campaign']==campaign and x['gen']==g)
            assert all('cv' not in q and 'cv_err' not in q for q in f['queries'])
            for key, expected in [('initial',initial),('history',history),('queries',query)]:
                assert len(f[key])==len(expected)
                for index,(e,a) in enumerate(zip(expected,f[key])):
                    assert a['seq']==e['seq'] and a['gen']==e['gen'] and a['number']==e['number']
                    for field in ('t0','t1')+(('cv',) if key!='queries' else ()):
                        verify(f'legal/{campaign}/{g}/{key}/{index}/{field}',e[field],a[field])
            truth=[r['cv'] for r in query]
            for i,v in enumerate(truth): verify(f'truth/{campaign}/{g}/{i}',v,score['truth'][i])
            preds, losses, neighbors = {}, {}, {}
            for prefix, train in [('frozen',initial),('cumulative',history)]:
                values, neighbor_indices = estimate(train,query,DOMAINS[campaign],center,scale)
                neighbors[prefix]=neighbor_indices
                for family,p in values.items():
                    method=prefix+'_'+family
                    preds[method]=p
                    for i,v in enumerate(p): verify(f'pred/{campaign}/{g}/{method}/{i}',v,f['predictions'][method][i])
                    losses[method]=loss(truth,p)
                    for metric,v in losses[method].items(): verify(f'loss/{campaign}/{g}/{method}/{metric}',v,score['losses'][method][metric])
                    for i,(v,t) in enumerate(zip(p,truth)):
                        point_errors.append(dict(campaign=campaign,gen=g,number=query[i]['number'],method=method,
                                                 prediction=v,truth=t,signed=v-t,absolute=abs(v-t),squared=(v-t)**2))
            pairs={}
            for family in ('ridge','mean','nn'):
                pairs[family]={m:losses['cumulative_'+family][m]-losses['frozen_'+family][m] for m in ('mae','mse')}
                for metric,v in pairs[family].items(): verify(f'pair/{campaign}/{g}/{family}/{metric}',v,score['paired_differences'][family][metric])
                if g==1: assert preds['frozen_'+family]==preds['cumulative_'+family]
            predictions_by_gen[g]=preds
            batches.append(dict(campaign=campaign,gen=g,losses=losses,paired_differences=pairs,neighbors=neighbors))
        future=[r['cv'] for g in sorted(predictions_by_gen) if g>=2 for r in rows if r['gen']==g]
        campaign_results[campaign]={}
        for method in predictions_by_gen[1]:
            p=[v for g in sorted(predictions_by_gen) if g>=2 for v in predictions_by_gen[g][method]]
            campaign_results[campaign][method]=loss(future,p)
            for metric,v in campaign_results[campaign][method].items(): verify(f'campaign/{campaign}/{method}/{metric}',v,stored['campaigns'][campaign][method][metric])
    gate=all(b['losses']['cumulative_ridge']['mae']<b['losses']['frozen_ridge']['mae'] for b in batches if b['gen']>=2)
    gate=gate and all(c['cumulative_ridge']['mae']<c[m]['mae'] for c in campaign_results.values() for m in ('cumulative_mean','cumulative_nn'))
    assert gate==stored['descriptive_gate']
    assert stored['decision']=='STOP_EXPANDING_THIS_FIXED_RIDGE_FEEDBACK_CONFIGURATION'
    audit=dict(status='PASS_RAW_ARITHMETIC_AUDIT_NOT_SCIENTIFIC_GATE',raw_label_count=sum(map(len,tables.values())),
               raw_tokens=raw_tokens,scalers=scalers,batches=batches,campaigns=campaign_results,point_errors=point_errors,
               descriptive_gate=gate,comparisons=len(checks),max_absolute_difference=max(x[1] for x in checks),
               response_ranges={c:dict(min=min(r['cv'] for r in rows),max=max(r['cv'] for r in rows)) for c,rows in tables.items()},
               scope='Raw released cv units; no automatic percentage-point/count claim; no main import or rerun.')
    assert not DEST.exists()
    DEST.write_text(json.dumps(audit,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ('status','raw_label_count','comparisons','max_absolute_difference','descriptive_gate','response_ranges','campaigns')},indent=2))
