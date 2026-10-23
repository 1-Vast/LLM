"""Independent retained-count arithmetic audit; never opens raw counts.body."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

root = Path(__file__).resolve().parents[2]
out = root/'log/20261023/replicated_contrast'
report = json.loads((out/'CONTRAST_RESULT.json').read_text())
freeze = json.loads((out/'NUMERICAL_FREEZE.json').read_text())
pre = json.loads((out/'EXECUTION_PREFLIGHT.json').read_text())
receipt = json.loads((out/'counts.receipt.json').read_text())
prior = json.loads((root/'log/20261023/interaction_error_diagnostic/PAIR_IDS.json').read_text())
pairs = json.loads((out/'SELECTED_PAIR_IDS.json').read_text())
ids = json.loads((out/'CONSTRUCT_IDS.json').read_text())
arrays = np.load(out/'CONTRAST_ARRAYS.npz', allow_pickle=False)
checks, maximum_error = [], 0.0

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(name, value):
    checks.append(dict(name=name, passed=bool(value)))
    if not value:
        raise AssertionError(name)

def near(name, actual, expected):
    global maximum_error
    actual, expected = np.asarray(actual), np.asarray(expected)
    error = float(np.max(np.abs(actual-expected)))
    maximum_error = max(maximum_error, error)
    check(name, np.allclose(actual, expected, rtol=1e-12, atol=1e-12))

for label, bound in [('numeric', freeze), ('preflight', pre)]:
    for rel, digest in bound['files'].items():
        path = root/rel
        if path.name == 'counts.body':
            check(label+'_raw_receipt_binding', digest == receipt['sha256'])
        else:
            check(label+':'+rel, sha(path) == digest)
check('array_hash', sha(out/'CONTRAST_ARRAYS.npz') == report['arrays_sha256'])
check('ids_hash', sha(out/'CONSTRUCT_IDS.json') == report['ids_sha256'])
check('sample_columns', report['selected_columns'] == ['MCF7_T9_1','MDAMB231_T9_1','MCF7_T9_2','MDAMB231_T9_2'])
expected = sorted(prior, key=lambda p: hashlib.sha256(('replicated-contrast-v1|'+'|'.join(p)).encode()).hexdigest())[:1024]
check('identity_hash_selection', pairs == expected)
check('unique_pairs', len(pairs) == len(set(map(tuple, pairs))) == 1024)
check('canonical_eligible', all(a < b and a not in ['AAVS','nontargeting'] and b not in ['AAVS','nontargeting'] for a,b in pairs))
counts, mapping = arrays['counts'], arrays['pair_row']
check('count_shape', counts.shape == (len(ids),4) and len(ids) == report['construct_rows'])
check('counts_finite_integer_nonnegative', np.all(np.isfinite(counts) & (counts >= 0) & (counts == np.floor(counts))))
check('construct_unique', len(ids) == len(set(ids)))
check('mapping_shape_range', mapping.shape == (len(ids),) and np.issubdtype(mapping.dtype,np.integer) and mapping.min() == 0 and mapping.max() == 1023)
for i, name in enumerate(ids):
    probes = name.split('__')
    check('construct_name_mapping_'+str(i), len(probes) == 2 and sorted(p.rsplit('-',1)[0] for p in probes) == pairs[int(mapping[i])])
sizes = np.bincount(mapping, minlength=1024)
check('fixed_sizes', np.isin(sizes,[9,18]).all())
check('saved_sizes', np.array_equal(sizes,arrays['construct_sizes']))
means = np.stack([np.log2(counts[mapping == i]+1).mean(axis=0) for i in range(1024)])
near('means', means, arrays['pair_means'])
differences = np.stack([means[2*k]-means[2*k+1] for k in range(512)])
delta = differences[:,[0,2]]-differences[:,[1,3]]
near('context_differences', differences, arrays['context_differences'])
near('delta', delta, arrays['delta'])
discovery = np.abs(delta[:,0]) >= .5
confirmation = discovery & (np.sign(delta[:,0]) == np.sign(delta[:,1])) & (delta[:,0] != 0) & (np.abs(delta[:,1]) >= .25)
check('discovery_mask', np.array_equal(discovery,arrays['discovery']))
check('confirmation_mask', np.array_equal(confirmation,arrays['confirmation']))
n, confirmed = int(discovery.sum()), int(confirmation.sum())
check('discovery_n', n == report['discovery_n'])
check('confirmation_n', confirmed == report['confirmation_n'])
fraction = confirmed/n if n else None
check('fraction', fraction == report['confirmation_fraction'])
check('screen', bool(n >= 20 and fraction is not None and fraction >= .8) == report['measurement_screen'])
same = (np.sign(delta[:,0]) == np.sign(delta[:,1])) & (delta[:,0] != 0) & (delta[:,1] != 0)
near('all_concordance', same.mean(), report['all_contrast_sign_concordance'])
defined = bool((delta.std(axis=0) > 0).all())
check('correlation_defined', defined == report['correlation_defined'])
if defined:
    near('pearson', np.corrcoef(delta.T)[0,1], report['pearson'])
    near('spearman', np.corrcoef(rankdata(delta[:,0]),rankdata(delta[:,1]))[0,1], report['spearman'])
else:
    check('undefined_nulls', report['pearson'] is None and report['spearman'] is None)
for j, name in enumerate(report['selected_columns']):
    near('zeros_'+name, (counts[:,j] == 0).mean(), report['count_zero_fraction'][name])
    near('low_'+name, (counts[:,j] <= 5).mean(), report['count_le_five_fraction'][name])
summary = dict(checks=len(checks), failures=0, maximum_numeric_error=maximum_error,
               details=checks, construct_rows=len(ids), sizes_9=int((sizes == 9).sum()),
               sizes_18=int((sizes == 18).sum()), discovery=n, confirmation=confirmed,
               failures_in_discovery=n-confirmed, all_concordant=int(same.sum()),
               fraction=fraction, measurement_screen=report['measurement_screen'],
               code_sha256=sha(Path(__file__)), raw_count_body_opened=False,
               model_fit=False, scope='Retained-array arithmetic and local bindings, not independent raw extraction or biology')
(out/'source/ARRAY_AUDIT.json').write_text(json.dumps(summary, indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'details'}))
