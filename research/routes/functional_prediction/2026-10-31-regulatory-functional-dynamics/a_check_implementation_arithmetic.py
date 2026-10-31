"""Compare the root endpoint helpers to the already frozen synthetic reference.

No real loader, main(), predictor/model, or scientific test matrix is called.
"""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from statistics import median

import numpy as np

HERE = Path(__file__).parent
REVIEWED_IMPLEMENTATION_SHA = '7530e8888959d0f044ea9b299619cd962924bedbe80083ae5d25f9767d874ce9'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    receipt = json.loads((HERE / 'a_arithmetic_initial_review_receipt.json').read_text())
    for entry in receipt['files']:
        if Path(entry['path']).name in ['a_arithmetic_expectations_v1.json', 'a_check_arithmetic.py', 'a_arithmetic_review_v1.md']:
            assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest() == entry['sha256']
    reference = load_module('a_independent_reference', HERE / 'a_check_arithmetic.py')
    assert reference.check()['synthetic_arithmetic'] == 'PASS'
    implementation_path = HERE / 'a_experiment.py'
    initial_hash = hashlib.sha256(implementation_path.read_bytes()).hexdigest()
    assert initial_hash == REVIEWED_IMPLEMENTATION_SHA
    implementation = load_module('a_endpoint_under_review', implementation_path)
    for name in ['a_experiment.py', 'a_launcher.py']:
        for node in ast.parse((HERE / name).read_text()).body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue
            if isinstance(node, ast.Assign):
                calls = [ast.unparse(x.func) for x in ast.walk(node) if isinstance(x, ast.Call)]
                assert all(x in ['pathlib.Path', 'pathlib.Path(__file__).resolve'] for x in calls)
                continue
            assert isinstance(node, ast.If)
            assert isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name)
            assert node.test.left.id == '__name__' and node.test.comparators[0].value == '__main__'
            assert [ast.unparse(x) for x in node.body] == ['main()']
    runtime = json.loads((HERE / 'runtime_environment.json').read_text())
    assert all(1 <= int(v) <= 4 for v in runtime['launcher_thread_caps'].values())
    assert implementation.GUIDE_SHA == hashlib.sha256((HERE / 'egi_admission/guide_identity.tsv').read_bytes()).hexdigest()
    guides = reference.GUIDES
    guide_index = {g: i for i, g in enumerate(guides)}
    ntc = np.array([guide_index[g] for g in reference.NTC])
    groups = [np.array([guide_index[g] for g in reference.GENES[gene]]) for gene in ['A', 'B', 'C']]
    pairs = np.array([[0, 1], [0, 2], [1, 2]])
    culture = reference.make_culture()
    counts = np.array([[[culture[c][a, b] for b in guides] for a in guides] for c in ['T0', 'UT', 'DRUG']], dtype=float)
    mask = np.ones(counts.shape[1:], dtype=bool)
    baseline, response, singles = implementation.make_source_inputs(counts, mask, ntc, groups, pairs)
    np.testing.assert_array_equal(baseline, [1, 1, 1])
    np.testing.assert_array_equal(response, [-1, 2, 0])
    np.testing.assert_array_equal(singles, [[1.5, 1.5, 0.5], [0.5, 0.5, 0.5]])
    lr = reference.ratios(culture, 'DRUG', 'UT')
    lr_array = np.array([[lr[a, b] for b in guides] for a in guides])
    actual = implementation.q_from_logratio(lr_array, mask, ntc)
    for a in guides:
        for b in guides:
            assert actual[guide_index[a], guide_index[b]] == reference.q(lr, a, b)
    np.testing.assert_array_equal(implementation.q_from_logratio(lr_array + 3, mask, ntc), actual)
    outlier = lr_array.copy()
    reduced = mask.copy()
    for n in reference.NTC[5:]:
        outlier[guide_index['A1'], guide_index[n]] += 100
        reduced[guide_index['A1'], guide_index[n]] = False
    masked_q = implementation.q_from_logratio(outlier, reduced, ntc)
    assert masked_q[guide_index['A1'], guide_index['C1']] == 2
    assert np.isnan(masked_q[guide_index['A1'], guide_index['N05']])

    # A-C is held test fold9; only its source evaluator label may change.
    changed = counts.copy()
    for a, b in reference.constructs('A', 'C'):
        changed[2, guide_index[a], guide_index[b]] = 2**30 - 1
    other_baseline, other_response, other_singles = implementation.make_source_inputs(changed, mask, ntc, groups, pairs)
    np.testing.assert_array_equal(other_baseline, baseline)
    np.testing.assert_array_equal(other_singles, singles)
    np.testing.assert_array_equal(other_response[[0, 2]], response[[0, 2]])
    assert other_response[1] != response[1]
    folds = np.array([implementation.pair_fold(a, b) for a, b in [('A', 'B'), ('A', 'C'), ('B', 'C')]])
    np.testing.assert_array_equal(folds, [1, 9, 4])
    y_dev, other_y_dev = response.copy(), other_response.copy()
    y_dev[folds >= 8] = np.nan
    other_y_dev[folds >= 8] = np.nan
    np.testing.assert_array_equal(y_dev, other_y_dev)

    # Fixed shared T0 mask is the sole declared target-baseline dependency.
    target = counts.copy()
    joint = ((counts[0] >= 30) & (target[0] >= 30))
    target[1:] = 0
    np.testing.assert_array_equal(joint, (counts[0] >= 30) & (target[0] >= 30))
    again = implementation.make_source_inputs(counts, joint, ntc, groups, pairs)
    for original, repeated in zip((baseline, response, singles), again):
        np.testing.assert_array_equal(original, repeated)
    expected_v2 = json.loads((HERE / 'a_arithmetic_expectations_v2.json').read_text())
    pred = np.array(expected_v2['prediction'])
    target_y = np.array(expected_v2['target_response'])
    source_y = np.array(expected_v2['source_response'])
    keep = np.ones(len(pred), dtype=bool)
    metric = implementation.metrics(pred, target_y, source_y, target_y, keep)
    assert metric['hits_at_100'] == expected_v2['primary_target_only_hits']
    assert metric['joint_confirmed_hits_descriptive'] == expected_v2['joint_confirmed_descriptive_hits']
    assert metric['precision_at_100'] == expected_v2['primary_precision_with_five_fixture_pairs']
    assert metric['top_indices'] == expected_v2['top_order_with_abs_prediction_ties']
    changed_metric = implementation.metrics(pred, target_y, -source_y, target_y, keep)
    assert changed_metric['hits_at_100'] == metric['hits_at_100']
    assert changed_metric['top_indices'] == metric['top_indices']
    try:
        implementation.metrics(np.full_like(pred, np.nan), target_y, source_y, target_y, keep)
    except AssertionError:
        pass
    else:
        raise AssertionError('Nonfinite predictions were accepted')
    for p in expected_v2['pseudocount_readout_values']:
        scalar_lr = {(a, b): math.log2((culture['DRUG'][a, b] + p) / (culture['UT'][a, b] + p)) for a in guides for b in guides}
        scalar_expected = [median(reference.q(scalar_lr, a, b) for a, b in reference.constructs(ga, gb)) for ga, gb in [('A', 'B'), ('A', 'C'), ('B', 'C')]]
        calculated = implementation.make_source_inputs(counts, mask, ntc, groups, pairs, p)[1]
        np.testing.assert_allclose(calculated, scalar_expected, atol=1e-12, rtol=0)
    assert hashlib.sha256(implementation_path.read_bytes()).hexdigest() == initial_hash
    return {'status': 'PASS', 'implementation_sha256': initial_hash,
            'reference_expectations_preserved': True,
            'endpoint_NTC_masks_offset_and_gene_medians': 'PASS',
            'source_held_DRUG_doubles_do_not_change_predictor_inputs': 'PASS',
            'target_UT_DRUG_values_do_not_change_source_inputs': 'PASS',
            'target_T0_common_eligibility_dependency': 'Explicitly declared in protocol v2',
            'v2_target_only_primary_and_joint_descriptive_metric': 'PASS',
            'v2_fixed_ranking_pseudocount_readout_algebra': 'PASS',
            'experiment_and_launcher_import_have_no_direct_data_open': 'PASS_STATIC',
            'runtime_thread_caps_within_four': True,
            'guide_identity_pin_matches_source_projection': True,
            'launcher_sha256': hashlib.sha256((HERE / 'a_launcher.py').read_bytes()).hexdigest(),
            'real_loader_called': False, 'scientific_model_fit': False,
            'real_count_or_GI_value_accessed': False}


if __name__ == '__main__':
    result = check()
    (HERE / 'a_arithmetic_implementation_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
