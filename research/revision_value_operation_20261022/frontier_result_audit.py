"""Recompute saved prediction scores only; no S4, feature arrays, or model fitting."""
import collections
import hashlib
import json
from pathlib import Path

path = Path('log/20261022/cdk_functional_increment/RESULT.json')
payload = json.loads(path.read_text(encoding='utf8'))
report = {'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Saved-output arithmetic and exclusion audit only, not independent raw-data extraction or refitting','challenges':{}}
for challenge, result in payload['results'].items():
    summaries = {}
    for key, summary in result['summary'].items():
        for method, expected in summary.items():
            rows = [r for r in result['rows'] if str(r['lambda']) == key and r['method']==method]
            grouped = collections.defaultdict(list)
            for row in rows:
                assert set(row['test']).isdisjoint(row['train'])
                assert len(row['train']) == len(result['eligible'])-2
                p = row['predictions'][0]-row['predictions'][1]
                t = row['truth'][0]-row['truth'][1]
                assert t != 0
                loss = .5 if abs(p)<=1e-12 else float((p>0)!=(t>0))
                assert loss==row['loss']
                assert row['baseline'][0]==row['baseline'][1]
                grouped[row['group']].append(loss)
            macro = sum(sum(v)/len(v) for v in grouped.values())/len(grouped) if grouped else None
            assert macro==expected['macro_loss'] and len(rows)==expected['pairs']
            assert {g:sum(v)/len(v) for g,v in grouped.items()}==expected['group_loss']
            summaries[f'{key}:{method}']={'macro_loss':macro,'group_pair_counts':{g:len(v) for g,v in grouped.items()},'pooled_fallback_pairs':sum(any(r['pooled_fallback']) for r in rows)}
    report['challenges'][challenge]={'eligible_n':len(result['eligible']),'missing_n':len(result['missing']),'true_ties_n':len(result['true_ties']),'nonestimable':result['nonestimable'],'summaries':summaries}
out = Path('log/20261022/revision_value_operation/frontier/RESULT_ARITHMETIC.json')
out.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
