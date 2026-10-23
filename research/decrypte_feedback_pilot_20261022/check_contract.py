"""Synthetic checks of target-query leakage and support/evaluation separation."""
import json
from pathlib import Path
import numpy as np
from run_pilot import nested_evaluate, predict, METHODS, SUPPORT, QUERY, GRIDS

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/decrypte_feedback_pilot'


def main():
    rng = np.random.default_rng(20261022)
    y = rng.normal(size=(6, 5))
    features = rng.normal(size=(6, 4))
    chemical = features @ features.T
    data = {'y': y.tolist(), 'chemical': chemical.tolist(), 'drugs': list('abcdef'), 'groups': list('abcdef')}
    before = nested_evaluate(data)
    changed = y.copy()
    changed[0, QUERY] += 1000
    after = nested_evaluate({**data, 'y': changed.tolist()})
    errors = []
    for budget in SUPPORT:
        assert not set(SUPPORT[budget]) & set(QUERY)
        for method in METHODS:
            a = np.array(before['predictions'][str(budget)][method])[0]
            b = np.array(after['predictions'][str(budget)][method])[0]
            errors.append(float(np.max(np.abs(a-b))))
        assert np.array_equal(before['selected_predictions'][str(budget)][0], after['selected_predictions'][str(budget)][0])
    assert max(errors) == 0
    flat = np.ones((6, 5))
    for budget in SUPPORT:
        for method in METHODS:
            hyper = GRIDS[method][0]
            prediction = predict(method, np.arange(1, 6), 0, flat, chemical, budget, hyper, flat[0, SUPPORT[budget]])
            assert np.all(np.isfinite(prediction))
            assert np.max(np.abs(prediction-1)) < 1e-12
    record = {'synthetic_target_query_perturbation_max_prediction_change': max(errors),
              'selected_prediction_unchanged': True, 'support_query_overlap': False,
              'flat_source_safe': True, 'seed': 20261022, 'status': 'PASS'}
    (OUT / 'SYNTHETIC_CHECKS.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
