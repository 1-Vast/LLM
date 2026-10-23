"""Exact retained-array ordering check; no fitting or workbook read."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT/'log/20261023/interaction_error_diagnostic'
records = json.loads((LOG/'RESULTS.json').read_text(encoding='utf-8'))['records']
checks = []
with np.load(LOG/'PREDICTIONS.npz',allow_pickle=False) as arrays:
    for record in records:
        prefix = f"{record['context']}_{record['salt']}_{record['budget']}"
        source = np.argsort(arrays[prefix+'_source_mean'],kind='stable')
        calibrated = np.argsort(arrays[prefix+'_calibration'],kind='stable')
        checks.append({'case':prefix,'full_argsort_equal':bool(np.array_equal(source,calibrated)),
                       'ordered_top20_equal':bool(np.array_equal(source[:20],calibrated[:20])),
                       'top20_set_equal':bool(set(source[:20])==set(calibrated[:20])),
                       'source_mse':record['metrics']['source_mean']['mse'],
                       'calibration_mse':record['metrics']['calibration']['mse']})
summary = {'cases':len(checks),'all_full_argsort_equal':all(r['full_argsort_equal'] for r in checks),
           'all_ordered_top20_equal':all(r['ordered_top20_equal'] for r in checks),'checks':checks,
           'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(LOG/'critic/CALIBRATION_RANK_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ('cases','all_full_argsort_equal','all_ordered_top20_equal')}))
