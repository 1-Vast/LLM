"""Meaningful synthetic isolation/degeneracy/equivalence checks, no biological inputs."""
import json
from pathlib import Path
import numpy as np
from evaluate import Engine, METHODS, QUERY, evaluate

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/decrypte_molecular_increment'


def main():
    rng = np.random.default_rng(20261022)
    y = rng.normal(1, .1, (8, 5))
    x = rng.uniform(0, 3, (8, 12))
    x[2:4, 0] = np.nan
    x[:, 1] = np.nan
    x[:2, 1] = [2., 3.]  # This holdout-only identifier may never become a source feature.
    chem_features = rng.normal(size=(8, 4))
    chem = chem_features @ chem_features.T
    groups = np.array(['a', 'a', 'b', 'b', 'c', 'd', 'e', 'f'])
    original = Engine(y, chem, x, groups)
    before = evaluate(original, list('abcdefgh'))
    json.dumps(before)  # Complete numerical evidence must be serializable, including source indices.
    changed = y.copy()
    changed[:2, QUERY] += 1000
    after = evaluate(Engine(changed, chem, x, groups), list('abcdefgh'))
    max_query_change = max(float(np.max(np.abs(np.array(before['predictions'][m])[:2] - np.array(after['predictions'][m])[:2]))) for m in METHODS)
    assert max_query_change == 0
    for portfolio in ('functional', 'molecular'):
        assert np.array_equal(np.array(before['selected_predictions'][portfolio])[:2], np.array(after['selected_predictions'][portfolio])[:2])
    train = np.arange(2, 8)
    initial = original.fold(train)
    altered_x = x.copy()
    altered_x[:2] = 1e6
    new = Engine(y, chem, altered_x, groups).fold(train)
    for key in ('value_eligible', 'mask_eligible', 'value_mean', 'value_scale'):
        assert np.array_equal(initial[key], new[key]), key
    assert not initial['value_eligible'][1] and not initial['mask_eligible'][1]
    features = initial['pc_features']
    sx = features[train]
    sx = sx - sx.mean(0)
    response = y[np.ix_(train, QUERY)]
    mean = response.mean(0)
    penalty = .1
    primal = mean + (features[:2]-features[train].mean(0)) @ np.linalg.solve(sx.T@sx/len(train)+penalty*np.eye(sx.shape[1]), sx.T@(response-mean)/len(train))
    dual = original.predict('M-joint-PC', train, [0, 1], penalty)
    error = float(np.max(np.abs(primal-dual)))
    assert error < 1e-8
    flat = Engine(np.ones((8, 5)), chem, np.ones((8, 12)), groups)
    for method in METHODS:
        pred = flat.predict(method, train, [0, 1], penalty)
        assert np.all(np.isfinite(pred)) and np.max(np.abs(pred-1)) < 1e-10, method
    result = {'seed': 20261022, 'multi_member_holdout_query_perturbation_max_error': max_query_change,
              'source_feature_selection_scaling_invariant_to_holdout_values': True,
              'holdout_only_identifiers_excluded': True, 'joint_PC_primal_dual_max_error': error,
              'all_nine_empty_block_flat_output_checks': True, 'status': 'PASS'}
    (OUT / 'SYNTHETIC_CHECKS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
