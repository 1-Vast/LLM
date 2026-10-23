"""Independent NumPy inference reconstruction; never imports or trains root models."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'log/20261023/feedback_law_discovery'
PILOT = BASE/'pilot'
OUT = BASE/'constructive'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(pred, y, mask, groups):
    per = []
    for p, t, m in zip(pred, y, mask):
        p, t = p[m], t[m]
        regret = t[np.argsort(p, kind='stable')[:3]].mean()-np.sort(t)[:3].mean()
        per.append([np.mean((p-t)**2), regret])
    per = np.array(per)
    return np.mean([per[groups == g].mean(axis=0) for g in sorted(set(groups))], axis=0)


def main():
    receipt = json.loads((PILOT/'RUN_RECEIPT.json').read_text())
    result = json.loads((PILOT/'RESULT.json').read_text())
    assert receipt['status'] == result['status'] == 'COMPLETED'
    assert receipt['returncode'] == 0
    freeze = json.loads((BASE/'PILOT_FREEZE.json').read_text())
    freeze_matches = {p: digest(ROOT/Path(p)) == h for p, h in freeze['files'].items()}
    assert all(freeze_matches.values())
    manifest = json.loads((PILOT/'MANIFEST.json').read_text())
    with np.load(ROOT/'tmp/context_transfer_20261017/beataml_domain.npz', allow_pickle=False) as cache:
        full_y = cache['Y'].astype(np.float64)
        contexts, items, full_groups = (cache[k].astype(str) for k in ('contexts', 'items', 'groups'))
    row_map, item_map = {s:i for i,s in enumerate(contexts)}, {s:i for i,s in enumerate(items)}
    assert len(row_map) == len(contexts) and len(item_map) == len(items)
    rows = np.array([row_map[s] for s in manifest['query_contexts']])
    columns = np.array([item_map[s] for s in manifest['drugs']])
    y = full_y[np.ix_(rows, columns)]
    groups = full_groups[rows]
    means, scales = np.array(manifest['source_means']), np.array(manifest['source_scales'])
    indices = np.array(manifest['support_indices'])
    observed = np.take_along_axis((y-means)/scales, indices, axis=1)
    mask = np.isfinite(y)
    np.put_along_axis(mask, indices, False, axis=1)
    source_groups = set(manifest['normalization_and_covariance_groups'])
    assert source_groups.isdisjoint(set(groups))
    hfun = lambda s: int(hashlib.sha256(s.encode()).hexdigest(), 16)
    folds = np.array([hfun('context-transfer-subject:'+g)%5 for g in full_groups])
    source_rows = np.flatnonzero(folds != 0)
    expected_columns = np.flatnonzero(np.isfinite(full_y[source_rows]).sum(axis=0) >= 100)
    assert np.array_equal(columns, expected_columns)
    source_y = full_y[np.ix_(source_rows,columns)]
    assert np.array_equal(np.nanmean(source_y,axis=0), means)
    assert np.array_equal(np.maximum(np.nanstd(source_y,axis=0),1e-6), scales)
    full_selected = full_y[:,columns]
    eligible = np.isfinite(full_selected).sum(axis=1) >= 16
    assert np.array_equal(rows,np.flatnonzero((folds == 0)&eligible))
    assert contexts[np.flatnonzero((folds != 0)&eligible)].tolist() == manifest['train_contexts']
    for row, support in zip(rows, indices):
        available = np.flatnonzero(np.isfinite(full_selected[row]))
        expected = sorted(available,key=lambda j:hfun('consistency-pilot-support:'+contexts[row]+':'+items[columns[j]]))[:8]
        assert list(support) == expected
    assert all(hfun('context-transfer-subject:'+g)%5 == 0 for g in groups)
    assert all(hfun('context-transfer-subject:'+g)%5 != 0 for g in source_groups)
    errors, scores = [], {}
    result_records = {(r['kind'],r['seed']):r for r in result['records']}
    with np.load(PILOT/'PREDICTIONS.npz', allow_pickle=False) as saved:
        assert np.array_equal(mask, saved['query_mask'])
        assert np.allclose(y, saved['truth'], rtol=0, atol=0, equal_nan=True)
        for seed in (0, 1, 2):
            for kind in ('fixed', 'augmented', 'consistent'):
                path = PILOT/f'{kind}_{seed}.pt'
                weights = torch.load(path, weights_only=True, map_location='cpu')
                embedding = weights['embedding'].numpy().astype(np.float64)
                step = np.logaddexp(0, weights['step'].numpy().astype(np.float64))
                for mode, packages in [('AB', [range(4), range(4,8)]),
                                       ('BA', [range(4,8), range(4)]),
                                       ('union', [range(8)])]:
                    h = np.zeros((len(rows), embedding.shape[1]), dtype=np.float64)
                    for package in packages:
                        idx = indices[:, list(package)]
                        values = observed[:, list(package)]
                        state = np.tanh(h)
                        predicted = np.einsum('nkw,nw->nk', embedding[idx], state)
                        gradient = np.einsum('nk,nkw->nw', predicted-values, embedding[idx])
                        gradient *= (1-state**2)/8
                        h -= gradient*step
                    standardized = np.tanh(h)@embedding.T
                    raw = standardized*scales+means
                    key = f'{kind}_{seed}'+('' if mode == 'AB' else '_'+mode)
                    old = saved[key]
                    errors.append(dict(kind=kind, seed=seed, view=mode,
                                       standardized_max_abs=float(np.max(np.abs(standardized-(old-means)/scales))),
                                       raw_auc_max_abs=float(np.max(np.abs(raw-old))),
                                       weight_sha256=digest(path)))
                    if mode == 'AB':
                        scores[(kind,seed)] = score(raw,y,mask,groups)
                        recorded = result_records[(kind,seed)]['metrics']
                        scores_error = np.abs(scores[(kind,seed)]-[recorded['mse'],recorded['regret']])
                        errors[-1]['cluster_metric_max_abs'] = float(scores_error.max())
        for kind in ('mean','covariance','set'):
            for seed in ((0,1,2) if kind == 'set' else (None,)):
                key = kind+(f'_{seed}' if seed is not None else '')
                scores[(kind,seed)] = score(saved[key],y,mask,groups)
    per_seed = {str(s): bool(np.all(scores[('consistent',s)] < scores[('augmented',s)])) for s in (0,1,2)}
    average = lambda k: np.mean([scores[(k,s)] for s in (0,1,2)],axis=0)
    consistent = average('consistent')
    sentinel = {k: bool(np.all(consistent < (average(k) if k == 'set' else scores[(k,None)])))
                for k in ('mean','covariance','set')}
    output = dict(status='INDEPENDENT_INFERENCE_AND_GATE_RECONSTRUCTED',
                  freeze_sha256=digest(BASE/'PILOT_FREEZE.json'), freeze_matches=freeze_matches,
                  authorized_payload='Y,contexts,items,groups only; manifest and saved predictions/weights',
                  source_patient_disjoint=True, inference_rows=errors,
                  independently_rebuilt_source_scales_filters_and_support=True,
                  maximum_standardized_error=max(r['standardized_max_abs'] for r in errors),
                  maximum_raw_auc_error=max(r['raw_auc_max_abs'] for r in errors),
                  per_seed_both_metrics_better_than_augmented=per_seed,
                  sentinel_both_metrics_pass=sentinel,
                  continuation_gate=all(per_seed.values()) and all(sentinel.values()),
                  scores={f'{k}_{s}':v.tolist() for (k,s),v in scores.items()},
                  limitations='No training replay/gradient audit or new experiment; Float64 NumPy inference versus Float32 torch saved outputs')
    (OUT/'PILOT_INDEPENDENT_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('inference_rows','freeze_matches','scores')},indent=2))


if __name__ == '__main__':
    main()
