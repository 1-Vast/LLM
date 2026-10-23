"""Reconstruct formulas from stored legal fold objects; no raw workbook or forecast import."""
from pathlib import Path
from statistics import mean
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/rechallenge_forecast'
folds_path = OUT / 'pilot/FORECASTS.json'
folds = json.loads(folds_path.read_text())
result = json.loads((OUT / 'pilot/RESULT.json').read_text())
freeze = json.loads((OUT / 'FREEZE.json').read_text())
for filename, expected in freeze['files'].items():
    assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == expected
seal = json.loads((OUT / 'pilot/FORECAST_SEAL.json').read_text())
assert hashlib.sha256(folds_path.read_bytes()).hexdigest() == seal['sha256']

def line(xs, ys, qs):
    mx, my = mean(xs), mean(ys)
    den = sum((x-mx)**2 for x in xs)
    b = sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den if den else 0
    return [my+b*(q-mx) for q in qs]

def deltas(curves):
    return {a: [y-x for r, v in curves.items() for a0,x,y in zip(r,v,v[1:]) if a0==a]
            for a in ('A','N')}

errors, structures, rebuilt = [], [], []
for fold in folds:
    source, target = fold['source_values'], fold['target_prefix']
    sd, td = deltas(source), deltas(target)
    structures.append(dict(source=fold['source'], target=fold['target'],
                           source_event={a:mean(v) for a,v in sd.items()},
                           target_prefix_event={a:mean(v) for a,v in td.items()}))
    for r in ('AAAA','ANAN'):
        s,y = source[r],target[r]
        res=[a-b for a,b in zip(y,s)]
        p={'persistence':[y[2]]*2, 'target_linear':line([0,1,2],y,[3,4]),
           'target_last_interval':[y[2]+j*(y[2]-y[1]) for j in (1,2)],
           'source_curve':s[3:], 'source_offset':[v+mean(res) for v in s[3:]],
           'source_affine':line(s[:3],y,s[3:]),
           'source_residual_trend':[a+b for a,b in zip(s[3:],line([0,1,2],res,[3,4]))]}
        for method, refit in [('source_event',False),('pooled_event_refit',True)]:
            rates={a:mean(sd[a]+(td[a] if refit else [])) for a in ('A','N')}
            p[method]=[y[2]+sum(rates[a] for a in r[2:h]) for h in (3,4)]
        scored=next(g for g in result['scored'] if g['target']==fold['target'] and g['regimen']==r)
        scores={}
        for method, values in p.items():
            errors.extend(abs(a-b) for a,b in zip(values,fold['predictions'][r][method]))
            signed=[a-b for a,b in zip(values,scored['truth'])]
            sq=[v*v for v in signed]
            ab=[abs(v) for v in signed]
            scores[method]=dict(mse=mean(sq),mae=mean(ab))
            for key, vals in [('signed',signed),('squared',sq),('absolute',ab)]:
                errors.extend(abs(a-b) for a,b in zip(vals,scored['errors'][method][key]))
            errors.extend(abs(v-scored['errors'][method][key]) for key,v in scores[method].items())
        rebuilt.append(scores)
for method, summary in result['summary'].items():
    for metric, value in summary.items():
        errors.append(abs(value-mean(g[method][metric] for g in rebuilt)))
gate=all(g['pooled_event_refit']['mse']<g[b]['mse'] for g in rebuilt for b in ('source_event','persistence'))
assert gate is result['descriptive_gate']
assert max(errors)<1e-10
report=dict(scope='Stored legal-data/formula audit; no raw-workbook parse or new experiment',
            comparisons=len(errors),max_abs_discrepancy=max(errors),all_freeze_hashes_match=True,
            forecast_seal_matches=True,descriptive_gate=gate,event_structure=structures)
(OUT/'critic/RESULT_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
