"""Independent saved-output arithmetic review; run only after root completion signal."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'
DEST = OUT / 'prior'
CONTROLS = ['additive', 'mean', 'q_ridge', 'linear_ridge', 'bilinear_ridge', 'fixed_mixture']
ARMS = CONTROLS + ['diagonal']
SPACES = ['mean_log1pCP10K', 'mean_CP10K']
DIRECTIONS = ['A_to_B', 'B_to_A']
GRID = [.001, .01, .1, 1., 10., 100.]


def hashed(pair, salt):
    return int.from_bytes(hashlib.sha256((salt + pair).encode()).digest()[:8], 'big')


def main():
    inputs = ['OOF_STATE.npz', 'SCORES.csv', 'FOLD_SCORES.csv', 'SELECTIONS.json', 'RESULT.json',
              'FIT_COSTS.json', 'EXTRACTION.json']
    arrays = np.load(OUT / 'OOF_STATE.npz')
    scores = pd.read_csv(OUT / 'SCORES.csv')
    foldscores = pd.read_csv(OUT / 'FOLD_SCORES.csv')
    selections = json.loads((OUT / 'SELECTIONS.json').read_text())
    root_result = json.loads((OUT / 'RESULT.json').read_text())
    costs = json.loads((OUT / 'FIT_COSTS.json').read_text())
    extraction = json.loads((OUT / 'EXTRACTION.json').read_text())
    assert root_result['status'] == 'COMPLETED_FIXED_RECIPE'
    pairs, folds = arrays['pairs'].tolist(), arrays['folds']
    assert len(pairs) == len(set(pairs)) == 73
    expected_folds = np.array([hashed(p, 'MAESTRO_MIXED_DIAGONAL_V1|') % 5 for p in pairs])
    np.testing.assert_array_equal(folds, expected_folds)
    assert set(folds) == set(range(5))
    assert len(scores) == 28 and len(foldscores) == 140
    review = {'scope': 'Saved outputs and code only; no refit or raw matrix/function access',
              'pair_count': len(pairs), 'fold_counts': np.bincount(folds).tolist(), 'contexts': []}
    recomputed = {}
    for space in SPACES:
        for direction in DIRECTIONS:
            prefix = space + '__' + direction
            truth = arrays[prefix + '__truth']
            assert truth.shape == (73, 103) and np.isfinite(truth).all()
            aggregate, byfold = {}, {}
            for arm in ARMS:
                pred = arrays[prefix + '__' + arm]
                assert pred.shape == truth.shape and np.isfinite(pred).all()
                mse = float(np.mean((pred-truth)**2))
                aggregate[arm] = mse
                found = scores[(scores.space == space) & (scores.direction == direction) & (scores.model == arm)]
                assert len(found) == 1
                np.testing.assert_allclose(found.MSE.item(), mse, rtol=1e-11, atol=1e-12)
                byfold[arm] = []
                for fold in range(5):
                    mask = folds == fold
                    fmse = float(np.mean((pred[mask]-truth[mask])**2))
                    byfold[arm].append(fmse)
                    found = foldscores[(foldscores.space == space) & (foldscores.direction == direction)
                                       & (foldscores.model == arm) & (foldscores.fold == fold)]
                    assert len(found) == 1 and found.pairs.item() == int(mask.sum())
                    np.testing.assert_allclose(found.MSE.item(), fmse, rtol=1e-11, atol=1e-12)
                np.testing.assert_allclose(np.average(byfold[arm], weights=np.bincount(folds)), mse,
                                           rtol=1e-12, atol=1e-12)
            np.testing.assert_array_equal(arrays[prefix+'__additive'], np.zeros_like(truth))
            np.testing.assert_allclose(arrays[prefix+'__fixed_mixture'],
                .5*(arrays[prefix+'__diagonal'] + arrays[prefix+'__q_ridge']), rtol=0, atol=0)
            winner = min(CONTROLS, key=aggregate.__getitem__)
            gain = 1. - aggregate['diagonal']/aggregate[winner]
            wins = sum(a < b for a,b in zip(byfold['diagonal'], byfold[winner]))
            context = {'space': space, 'direction': direction, 'MSE': aggregate,
                       'strongest_conventional_arm': winner, 'relative_diagonal_gain': gain,
                       'positive_folds_against_that_arm': wins,
                       'fold_MSE': byfold,
                       'five_percent_and_four_folds': bool(gain >= .05 and wins >= 4),
                       'strictly_better_than_strongest': bool(aggregate['diagonal'] < aggregate[winner])}
            review['contexts'].append(context)
            recomputed[(space, direction)] = context
    assert len(root_result['scores']) == 28
    for row in root_result['scores']:
        expected = recomputed[(row['space'],row['direction'])]['MSE'][row['model']]
        np.testing.assert_allclose(row['MSE'], expected, rtol=1e-11, atol=1e-12)
    expected_choice_keys = {(s,d,f,m) for s in SPACES for d in DIRECTIONS for f in range(5)
                            for m in ['mean','diagonal','q_ridge','linear_ridge','bilinear_ridge']}
    seen, candidate_calls = set(), 0
    cost_index = 0
    cost_summary = {}
    for row in selections:
        key = row['space'], row['direction'], row['fold'], row['model']
        assert key in expected_choice_keys and key not in seen
        seen.add(key)
        train, assess = np.flatnonzero(folds != row['fold']), np.flatnonzero(folds == row['fold'])
        assert row['train'] == train.tolist() and row['assess'] == assess.tolist()
        ordering = sorted(train, key=lambda i: hashed(pairs[i], 'MAESTRO_MIXED_INNER_V1|'))
        boundary = 3*len(train)//4
        assert row['inner'] == ordering[:boundary] and row['validation'] == ordering[boundary:]
        assert not set(row['train']) & set(row['assess'])
        assert not set(row['inner']) & set(row['validation'])
        candidates = row['candidates']
        expected_penalties = [None] if row['model']=='mean' else GRID
        assert [c['penalty'] for c in candidates] == expected_penalties
        losses = [c['validation_MSE'] for c in candidates]
        assert np.isfinite(losses).all()
        assert row['selected'] == min(range(len(losses)), key=losses.__getitem__)
        candidate_calls += len(candidates)
        expected_fits = [(c['penalty'], len(row['inner']), len(row['validation'])) for c in candidates]
        expected_fits.append((candidates[row['selected']]['penalty'], len(row['train']), len(row['assess'])))
        for penalty, train_count, assess_count in expected_fits:
            cost = costs[cost_index]
            assert cost['model'] == row['model'] and cost['penalty'] == penalty
            assert cost['train_pairs'] == train_count and cost['assess_pairs'] == assess_count
            assert np.isfinite(cost['seconds']) and cost['seconds'] >= 0
            summary = cost_summary.setdefault(row['model'], {'calls': 0, 'seconds': 0.})
            summary['calls'] += 1
            summary['seconds'] += cost['seconds']
            cost_index += 1
    assert seen == expected_choice_keys
    assert cost_index == len(costs) == root_result['fit_calls'] == 600
    fit_seconds = sum(c['seconds'] for c in costs)
    np.testing.assert_allclose(fit_seconds, root_result['summed_fit_seconds'], rtol=1e-12, atol=1e-12)
    assert root_result['seconds'] >= fit_seconds
    assert extraction['status'] == 'PASS' and extraction['pair_cells_retained'] == 20395
    primary = recomputed[('mean_log1pCP10K','A_to_B')]
    reverse = recomputed[('mean_log1pCP10K','B_to_A')]
    gate = primary['five_percent_and_four_folds'] and reverse['strictly_better_than_strongest']
    review.update({'arithmetic_status': 'PASS', 'selection_rows_checked': len(selections),
        'inner_fit_calls_inferred': candidate_calls, 'outer_refit_calls_inferred': len(selections),
        'total_fit_calls_inferred': candidate_calls+len(selections),
        'fit_call_definition': 'Includes deterministic mean and diagonal calls; fixed mixture/additive need no fits',
        'reported_wall_seconds': root_result['seconds'],
        'summed_fit_seconds': fit_seconds, 'fit_costs_by_model': cost_summary,
        'extraction_seconds': extraction['seconds'],
        'compute_limit': 'Fit timers exclude design/extraction costs; equal candidate count is not equal cost or penalty meaning',
        'primary_full_gate_pass': bool(gate),
        'fixed_decision': 'RETAIN_ONLY_SOURCE_STATE_CAPABILITY' if gate else 'STOP_CURRENT_DIAGONAL_MIXED_LAW_CONFIGURATION',
        'input_sha256': {name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in inputs},
        'new_biological_values_accessed': 'Saved source-state predictions/truth only; no new raw observations',
        'functional_values_read': 0,
        'limits': ['73 historically selected source pairs in one K562 map',
                   '103 historically selected named expression readouts',
                   'Gemgroups are batches, not independent biological contexts',
                   'Relative 5% threshold is a design screen, not significance',
                   'No function/drug/WM necessity/agent/inheritance/joint/RSI claim']})
    (DEST/'SAVED_REVIEW.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
