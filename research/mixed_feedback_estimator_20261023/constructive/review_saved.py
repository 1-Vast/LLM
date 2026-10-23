"""Independent saved-result arithmetic. Run only after root authorizes review.

No model fits, no raw matrix or function outcome reads, no imports of predictor.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'log/20261023/mixed_feedback_estimator'
ARMS = ['additive', 'mean', 'q_ridge', 'linear_ridge', 'bilinear_ridge', 'fixed_mixture']
FIT_ARMS = ['mean', 'diagonal', 'q_ridge', 'linear_ridge', 'bilinear_ridge']


def hash_integer(pair, salt):
    return int.from_bytes(hashlib.sha256((salt + pair).encode()).digest()[:8], 'big')


def main():
    state = np.load(BASE / 'STATE_BY_GEM.npz', allow_pickle=False)
    saved = np.load(BASE / 'OOF_STATE.npz', allow_pickle=False)
    scores = pd.read_csv(BASE / 'SCORES.csv')
    fold_scores = pd.read_csv(BASE / 'FOLD_SCORES.csv')
    selections = json.loads((BASE / 'SELECTIONS.json').read_text())
    costs = json.loads((BASE / 'FIT_COSTS.json').read_text())
    result = json.loads((BASE / 'RESULT.json').read_text())
    assert result['pairs'] == 73 and result['readouts'] == 103
    assert result['functional_outcomes_read'] == 0
    assert len(scores) == len(result['scores']) == 28 and len(fold_scores) == 140
    metadata = pd.read_csv(BASE / 'support/SOURCE_PAIR_METADATA.csv')
    pairs = sorted(metadata.loc[metadata['identity_qc_cells'] > 0, 'pair'].tolist())
    assert len(pairs) == len(set(pairs)) == 73
    assert saved['pairs'].tolist() == pairs
    folds = np.array([hash_integer(p, 'MAESTRO_MIXED_DIAGONAL_V1|') % 5 for p in pairs])
    order = np.array([hash_integer(p, 'MAESTRO_MIXED_INNER_V1|') for p in pairs], dtype=np.uint64)
    assert np.array_equal(saved['folds'], folds)
    lookup = {(name, str(gem)): i for i, (name, gem) in
              enumerate(zip(state['group_names'].tolist(), state['gems'].tolist()))}
    errors, summaries, checks = [], [], 0
    for space in ['mean_log1pCP10K', 'mean_CP10K']:
        values = state[space]
        assert values.shape[1] == 103 and np.isfinite(values).all()
        for direction, target_gems in [('A_to_B', range(5, 9)), ('B_to_A', range(1, 5))]:
            truth = []
            for pair in pairs:
                a, b = pair.split('|')
                rows = []
                for gem in target_gems:
                    # Independent raw arithmetic, no predictor helper imports.
                    rows.append(values[lookup[(pair, str(gem))]]
                                - values[lookup[(a, str(gem))]]
                                - values[lookup[(b, str(gem))]]
                                + values[lookup[('CONTROL', str(gem))]])
                truth.append(np.add.reduce(rows) / len(rows))
            truth = np.array(truth)
            key = space + '__' + direction
            errors.append(float(np.max(np.abs(truth - saved[key + '__truth']))))
            assert np.allclose(truth, saved[key + '__truth'], atol=1e-12, rtol=1e-12)
            assert np.count_nonzero(saved[key + '__additive']) == 0
            assert np.allclose(saved[key + '__fixed_mixture'],
                               (saved[key + '__diagonal'] + saved[key + '__q_ridge']) / 2,
                               atol=0, rtol=0)
            mse = {}
            fold_mse = {}
            for arm in ['diagonal'] + ARMS:
                pred = saved[key + '__' + arm]
                assert pred.shape == truth.shape and np.isfinite(pred).all()
                value = float(np.mean((pred - truth) ** 2))
                mse[arm] = value
                row = scores[(scores.space == space) & (scores.direction == direction) & (scores.model == arm)]
                assert len(row) == 1
                errors.append(abs(value - float(row.MSE.iloc[0])))
                assert np.isclose(value, row.MSE.iloc[0], atol=1e-11, rtol=1e-12)
                result_rows = [r for r in result['scores'] if r['space'] == space
                               and r['direction'] == direction and r['model'] == arm]
                assert len(result_rows) == 1
                assert np.isclose(value, result_rows[0]['MSE'], atol=1e-11, rtol=1e-12)
                fold_mse[arm] = []
                for fold in range(5):
                    assess = np.where(folds == fold)[0]
                    assert len(assess) > 0
                    loss = float(np.mean((pred[assess] - truth[assess]) ** 2))
                    fold_mse[arm].append(loss)
                    fr = fold_scores[(fold_scores.space == space) & (fold_scores.direction == direction)
                                     & (fold_scores.model == arm) & (fold_scores.fold == fold)]
                    assert len(fr) == 1 and int(fr.pairs.iloc[0]) == len(assess)
                    errors.append(abs(loss - float(fr.MSE.iloc[0])))
                    assert np.isclose(loss, fr.MSE.iloc[0], atol=1e-11, rtol=1e-12)
                    if arm == 'mean':
                        train = np.where(folds != fold)[0]
                        assert np.allclose(pred[assess], truth[train].mean(axis=0), atol=1e-12, rtol=1e-12)
                    checks += 1
            best = min(ARMS, key=lambda arm: mse[arm])
            summaries.append({'space': space, 'direction': direction, 'diagonal_MSE': mse['diagonal'],
                              'best_conventional': best, 'best_MSE': mse[best],
                              'relative_gain': 1 - mse['diagonal'] / mse[best],
                              'folds_improved': sum(a < b for a, b in zip(fold_mse['diagonal'], fold_mse[best])),
                              'all_MSE': mse})
    assert len(selections) == 100
    for record in selections:
        fold = record['fold']
        train = np.where(folds != fold)[0]
        assess = np.where(folds == fold)[0]
        sorted_train = train[np.argsort(order[train])]
        boundary = len(train) * 3 // 4
        assert record['train'] == train.tolist() and record['assess'] == assess.tolist()
        assert record['inner'] == sorted_train[:boundary].tolist()
        assert record['validation'] == sorted_train[boundary:].tolist()
        assert not set(record['inner']) & set(record['validation'])
        candidates = record['candidates']
        expected = [None] if record['model'] == 'mean' else [.001, .01, .1, 1., 10., 100.]
        assert [r['penalty'] for r in candidates] == expected
        assert record['selected'] == min(range(len(candidates)), key=lambda i: candidates[i]['validation_MSE'])
    assert len(costs) == result['fit_calls'] == 600
    assert all(c['seconds'] >= 0 for c in costs)
    for name in FIT_ARMS:
        assert sum(c['model'] == name for c in costs) == (40 if name == 'mean' else 140)
    assert np.isclose(sum(c['seconds'] for c in costs), result['summed_fit_seconds'])
    primary, reverse = summaries[0], summaries[1]
    passed = primary['relative_gain'] >= .05 and primary['folds_improved'] >= 4 and reverse['relative_gain'] > 0
    report = {'status': 'SAVED_ARITHMETIC_VERIFIED', 'fits_run_by_reviewer': 0,
              'raw_matrix_reads': 0, 'function_outcome_reads': 0, 'peer_result_reports_read': False,
              'fold_score_checks': checks, 'max_numeric_difference': max(errors),
              'summaries': summaries, 'declared_gate_pass': bool(passed),
              'decision': 'PASS_SOURCE_STRUCTURE_ONLY' if passed else 'STOP_CURRENT_DIAGONAL_MIXED_LAW_CONFIGURATION',
              'limits': 'No fit recomputation; saved inner validation losses not independently regenerated. No independent biological replication, function, causal mechanism, agent or RSI evidence.'}
    (BASE / 'constructive/SAVED_AUDIT.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
