"""Describe frozen nomination counts; never select pairs or read workbook."""
import hashlib
import json
from pathlib import Path

p = Path('log/20261023/rank_reversal_mechanism')
raw = (p / 'FDR_ANNOTATION.json').read_bytes()
r = json.loads(raw)
models = ['source_mean', 'calibration', 'score_direct', 'identity_ordinary', 'gi_oracle']
out = {'annotation_sha256': hashlib.sha256(raw).hexdigest(), 'rows': [], 'averages': [],
       'scope': 'Descriptive counts per frozen top20; masks/budgets are not independent observations; oracle outcome-selected.'}
for budget in [128, 512]:
    for context in r['panel']:
        records = [x for x in r['records'] if x['budget'] == budget and x['context'] == context]
        out['rows'].append({'budget': budget, 'context': context, 'denominator_per_case': 20,
                            'counts': {m: {rule: [x['annotations'][m][rule]['supported_negative'] for x in records]
                                           for rule in ['conservative', 'optimistic_sensitivity']} for m in models}})
    records = [x for x in r['records'] if x['budget'] == budget]
    out['averages'].append({'budget': budget, 'per_top20': {
        m: {rule: sum(x['annotations'][m][rule]['supported_negative'] for x in records) / len(records)
            for rule in ['conservative', 'optimistic_sensitivity']} for m in models}})
(p / 'constructive' / 'ANNOTATION_SUMMARY.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
