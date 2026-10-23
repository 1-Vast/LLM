"""Independently check retained annotation; no workbook access or model import."""
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[3]
out = root/'log/20261023/rank_reversal_mechanism'
prior = root/'log/20261023/interaction_error_diagnostic'
report = json.loads((out/'FDR_ANNOTATION.json').read_text())
freeze = json.loads((out/'ANNOTATION_FREEZE.json').read_text())
qsave = np.load(out/'FDR_DEVELOPMENT.npz', allow_pickle=False)
saved = np.load(prior/'PREDICTIONS.npz', allow_pickle=False)
ids = json.loads((prior/'PAIR_IDS.json').read_text())
old = json.loads((prior/'RESULTS.json').read_text())
dev = ['MCF7', 'MDAMB231', 'MCF10A', 'CAL27', 'CAL33']
checks = []

def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))
    if not condition:
        raise AssertionError(name)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def count(idx, y, q):
    known = np.isfinite(q[idx])
    sig = known & (q[idx] <= .1)
    return dict(n=len(idx), known_q=int(known.sum()), q_supported=int(sig.sum()),
                supported_negative=int((sig & (y[idx] < 0)).sum()), unknown=int((~known).sum()))

for rel, digest in freeze['files'].items():
    check('freeze:'+rel, sha(root/rel) == digest)
check('report_bindings', report['bindings'] == freeze['files'])
check('q_binding', sha(out/'FDR_DEVELOPMENT.npz') == report['q_sha256'])
check('allowed_contexts', report['metadata']['parsed_columns'] == dev)
check('sheet_scope', report['metadata']['source_sheet'] == 'cell-line-fdrs')
check('eligible', len(ids) == 11621 == report['metadata']['eligible'])
check('id_unique', len(set(map(tuple, ids))) == len(ids))
check('no_lung_keys', not any('A549' in k or 'A427' in k for k in qsave.files))
high, low = qsave['maximum_q'], qsave['minimum_q']
y = saved['development_scores']
inc = qsave['incomplete']
for name, a in [('high', high), ('low', low), ('incomplete', inc), ('scores', y)]:
    check('shape_'+name, a.shape == (11621, 5))
for name, a in [('high', high), ('low', low)]:
    finite = np.isfinite(a)
    check('range_'+name, np.all((a[finite] >= 0) & (a[finite] <= 1)))
check('ordered_min_max', np.all(low[np.isfinite(high)] <= high[np.isfinite(high)]))
check('incomplete_count', int(inc.sum()) == report['metadata']['incomplete_cells'])
check('unknown_agrees', np.array_equal(~np.isfinite(high), inc))
check('records20', len(report['records']) == len(old['records']) == 20)
methods = ['source_mean', 'calibration', 'score_direct', 'identity_ordinary', 'gi_oracle']
for record, base in zip(report['records'], old['records']):
    name, salt, budget = (record[k] for k in ['context', 'salt', 'budget'])
    check('case_order', all(record[k] == base[k] for k in ['context', 'salt', 'budget']))
    prefix = f'{name}_{salt}_{budget}'
    j = dev.index(name)
    query = saved[prefix+'_query']
    for method in methods:
        pred = y[query, j] if method == 'gi_oracle' else saved[prefix+'_'+method]
        chosen = query[np.argsort(pred, kind='stable')[:20]]
        annotation = record['annotations'][method]
        check(prefix+method+'_ids', chosen.tolist() == annotation['pair_indices'])
        for mode, q in [('conservative', high), ('optimistic_sensitivity', low)]:
            check(prefix+method+mode, count(chosen, y[:, j], q[:, j]) == annotation[mode])
    check(prefix+'_calibration_identity', record['annotations']['source_mean'] == record['annotations']['calibration'])
for j, name in enumerate(dev):
    for mode, q in [('conservative', high), ('optimistic_sensitivity', low)]:
        check('panel_'+name+mode, count(np.arange(len(ids)), y[:, j], q[:, j]) == report['panel'][name][mode])
check('contrasts10', len(report['contrasts']) == 10)
for contrast in report['contrasts']:
    a, b = dev.index(contrast['context_a']), dev.index(contrast['context_b'])
    for mode, q in [('conservative', high), ('optimistic_sensitivity', low)]:
        supported = np.isfinite(q[:, a]) & np.isfinite(q[:, b]) & (q[:, a] <= .1) & (q[:, b] <= .1)
        ab = supported & (y[:, a] < 0) & (y[:, b] > 0)
        ba = supported & (y[:, a] > 0) & (y[:, b] < 0)
        expected = dict(both_q_supported=int(supported.sum()), opposite_sign=int((ab | ba).sum()),
                        negative_a_positive_b=int(ab.sum()), positive_a_negative_b=int(ba.sum()))
        check('contrast_'+str(a)+str(b)+mode, expected == contrast[mode])
summary = dict(checks=len(checks), failures=0, details=checks,
               finite_primary=int(np.isfinite(high).sum()), exact_point_one_primary=int((high == .1).sum()),
               exact_point_one_sensitivity=int((low == .1).sum()),
               primary_sensitivity_different_cells=int((high != low).sum()),
               code_sha256=sha(Path(__file__)), workbook_read=False, model_fit=False,
               scope='Saved-array arithmetic and bindings only; no raw FDR authentication')
(out/'source/RESULT_AUDIT.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'details'}))
