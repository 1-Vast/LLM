"""Independent saved-prediction audit. No pilot imports, optimization or X access."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'log/20261023/feedback_law_discovery'
PILOT = BASE/'pilot'
OUT = BASE/'critic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def h(value):
    return int(hashlib.sha256(value.encode()).hexdigest(), 16)


def evaluate(p, y, mask, groups):
    sample_mse, sample_regret, tie_rows = [], [], 0
    for i in range(len(y)):
        js = np.flatnonzero(mask[i])
        actual, predicted = y[i, js], p[i, js]
        assert np.isfinite(actual).all() and np.isfinite(predicted).all()
        assert len(js) >= 8
        sample_mse.append(float(np.dot(actual-predicted, actual-predicted)/len(js)))
        # Python stable sort independently reproduces ascending original-column tie rule.
        order = sorted(range(len(js)), key=lambda k: float(predicted[k]))
        best = sorted(range(len(js)), key=lambda k: float(actual[k]))
        sample_regret.append(float(sum(actual[k] for k in order[:3])/3-
                                   sum(actual[k] for k in best[:3])/3))
        tie_rows += int(predicted[order[2]] == predicted[order[3]])
    labels = sorted(set(groups.tolist()))
    cm = [float(np.mean([sample_mse[i] for i, g in enumerate(groups) if g == key])) for key in labels]
    cr = [float(np.mean([sample_regret[i] for i, g in enumerate(groups) if g == key])) for key in labels]
    return dict(mse=float(np.mean(cm)), regret=float(np.mean(cr)), context_mse=sample_mse,
                context_regret=sample_regret, groups=labels, cluster_mse=cm,
                cluster_regret=cr, top3_boundary_tie_contexts=tie_rows)


def main():
    result = json.loads((PILOT/'RESULT.json').read_text())
    receipt = json.loads((PILOT/'RUN_RECEIPT.json').read_text())
    assert result['status'] == 'COMPLETED'
    assert receipt['status'] == 'COMPLETED' and receipt['returncode'] == 0
    freeze = json.loads((BASE/'PILOT_FREEZE.json').read_text())
    checked = {name: digest(ROOT/name) == expected for name, expected in freeze['files'].items()}
    assert all(checked.values()), checked
    manifest = json.loads((PILOT/'MANIFEST.json').read_text())
    cache = ROOT/'tmp/context_transfer_20261017/beataml_domain.npz'
    assert digest(cache) == manifest['cache_sha256']
    with np.load(cache, allow_pickle=False) as data:
        y = data['Y'].astype(float)
        groups, contexts, items = [data[k].astype(str) for k in ('groups', 'contexts', 'items')]
    folds = np.array([h('context-transfer-subject:'+g)%5 for g in groups])
    source = np.flatnonzero(folds != 0)
    drug_indices = np.flatnonzero(np.sum(np.isfinite(y[source]), axis=0) >= 100)
    y, items = y[:, drug_indices], items[drug_indices]
    valid = [np.flatnonzero(np.isfinite(row)) for row in y]
    eligible = np.array([len(v) >= 16 for v in valid])
    train = np.flatnonzero((folds != 0)&eligible)
    test = np.flatnonzero((folds == 0)&eligible)
    assert not set(groups[train]) & set(groups[test])
    supports = np.array([sorted(valid[i], key=lambda j: h('consistency-pilot-support:'+contexts[i]+':'+items[j]))[:8] for i in test])
    mask = np.isfinite(y[test])
    for i, support in enumerate(supports):
        mask[i, support] = False
    assert items.tolist() == manifest['drugs']
    assert contexts[train].tolist() == manifest['train_contexts']
    assert contexts[test].tolist() == manifest['query_contexts']
    assert groups[test].tolist() == manifest['query_groups']
    assert contexts[source].tolist() == manifest['normalization_and_covariance_contexts']
    assert groups[source].tolist() == manifest['normalization_and_covariance_groups']
    assert np.array_equal(supports, manifest['support_indices'])
    np.testing.assert_allclose(np.nanmean(y[source], axis=0), manifest['source_means'], rtol=0, atol=0)
    np.testing.assert_allclose(np.maximum(np.nanstd(y[source], axis=0), 1e-6), manifest['source_scales'], rtol=0, atol=0)
    assert len(result['records']) == 14
    audit, largest_delta = [], 0.0
    with np.load(PILOT/'PREDICTIONS.npz', allow_pickle=False) as saved:
        np.testing.assert_allclose(saved['truth'], y[test], rtol=0, atol=0, equal_nan=True)
        assert np.array_equal(saved['query_mask'], mask)
        assert np.array_equal(saved['support_indices'], supports)
        for record in result['records']:
            key = record['kind'] if record['seed'] is None else f"{record['kind']}_{record['seed']}"
            rebuilt = evaluate(saved[key], y[test], mask, groups[test])
            for field in ('mse', 'regret', 'context_mse', 'context_regret', 'cluster_mse', 'cluster_regret'):
                a, b = np.asarray(rebuilt[field]), np.asarray(record['metrics'][field])
                largest_delta = max(largest_delta, float(np.max(np.abs(a-b))))
                np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-9)
            assert rebuilt['groups'] == record['metrics']['groups']
            audit.append(dict(key=key, **rebuilt))
    table = {r['key']: r for r in audit}
    assert len(table) == 14
    per_seed = {str(s): all(table[f'consistent_{s}'][m] < table[f'augmented_{s}'][m]
                           for m in ('mse', 'regret')) for s in (0,1,2)}
    avg = lambda k, m: float(np.mean([table[f'{k}_{s}'][m] for s in (0,1,2)]))
    sentinels = {k: all(avg('consistent', m) < (avg(k,m) if k == 'set' else table[k][m])
                       for m in ('mse','regret')) for k in ('mean','covariance','set')}
    report = dict(status='PASS_INDEPENDENT_SAVED_PREDICTION_AUDIT',
        frozen_files_unchanged=checked, run_receipt=receipt,
        records=14, source_contexts=len(source), train_contexts=len(train),
        query_contexts=len(test), query_patients=len(set(groups[test])), drugs=len(items),
        max_metric_absolute_difference=largest_delta, per_seed_both_metric_gate=per_seed,
        seed_average_sentinel_gate=sentinels,
        continue_gate=all(per_seed.values()) and all(sentinels.values()), rebuilt_metrics=audit,
        limits=['Saved outputs and source provenance reconstructed, not training trajectory independently reproduced.',
                'No X/events/G decoded, no model imported, trained or tuned.',
                'Runtime cost is reported, not independently measured; fixed steps do not equal FLOPs.',
                'No new biological tasks or causal/clinical/world-model/RSI claim.'])
    (OUT/'PILOT_RESULT_AUDIT.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('status','max_metric_absolute_difference','per_seed_both_metric_gate','seed_average_sentinel_gate','continue_gate')}, indent=2))


if __name__ == '__main__':
    main()
