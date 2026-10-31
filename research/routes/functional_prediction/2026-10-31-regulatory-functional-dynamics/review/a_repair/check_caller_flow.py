"""Repair regression: exact caller-loop AST, entirely synthetic values.

Never calls load_counts, main, predict_source, a launcher or any estimator fit.
"""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent
EPISODE = OUT.parents[1]
CORRECTED_SHA = '7e94ea162d1e1cc46a8f5913da59035ea884d01aa3f1ff62d3644ef5eea922d0'
LAUNCHER_SHA = '6f4c9f0dfb28721edfc67888c0e7759ac3e29e4685fa47a0f15dd99857be0c30'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parsed(name):
    return ast.parse((EPISODE / name).read_text())


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def floor_loop(main):
    candidates = [n for n in ast.walk(main) if isinstance(n, ast.For)
                  and any(isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'low' for t in x.targets) for x in n.body)]
    assert len(candidates) == 1
    return candidates[0]


def dump(node):
    return ast.dump(node, include_attributes=False)


def import_safe(name, file):
    spec = importlib.util.spec_from_file_location(name, EPISODE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RenameFloor(ast.NodeTransformer):
    def visit_Name(self, node):
        node.id = {'a': 'ga', 'b': 'gb'}.get(node.id, node.id)
        return node


class RenameConstants(ast.NodeTransformer):
    def __init__(self, replacements):
        self.replacements = replacements

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = self.replacements.get(node.value, node.value)
        return node


def check():
    original_freeze = json.loads((EPISODE / 'a_freeze.json').read_text())
    for name, expected in original_freeze['files'].items():
        assert sha(EPISODE / name) == expected, name
    assert sha(EPISODE / 'a_experiment_corrected.py') == CORRECTED_SHA
    assert sha(EPISODE / 'a_launcher_corrected.py') == LAUNCHER_SHA
    original, corrected = parsed('a_experiment.py'), parsed('a_experiment_corrected.py')
    for node in original.body:
        if isinstance(node, ast.FunctionDef) and node.name not in ['main', 'source_features']:
            assert dump(node) == dump(function(corrected, node.name)), node.name
    old_features = function(original, 'source_features')
    new_features = function(corrected, 'source_features')
    assert isinstance(new_features.body[0], ast.Assert)
    assert dump(ast.Module(old_features.body, [])) == dump(ast.Module(new_features.body[1:], []))
    expected_main = deepcopy(function(original, 'main'))
    RenameFloor().visit(floor_loop(expected_main))
    RenameConstants({'a_results': 'a_results_corrected'}).visit(expected_main)
    assert dump(expected_main) == dump(function(corrected, 'main'))
    old_launcher = parsed('a_launcher.py')
    replacements = {'a_freeze.json': 'a_freeze_corrected.json',
                    'a_launch_receipt.json': 'a_launch_corrected_receipt.json',
                    'a_run_stdout.txt': 'a_run_corrected_stdout.txt',
                    'a_run_stderr.txt': 'a_run_corrected_stderr.txt',
                    'a_experiment.py': 'a_experiment_corrected.py'}
    RenameConstants(replacements).visit(old_launcher)
    for node in ast.walk(old_launcher):
        if isinstance(node, ast.Dict):
            for i, key in enumerate(node.keys):
                if isinstance(key, ast.Constant) and key.value in ['matrix_number', 'spare_used']:
                    node.values[i] = ast.Constant(2 if key.value == 'matrix_number' else True)
    assert dump(old_launcher) == dump(parsed('a_launcher_corrected.py'))

    # Hand-computable fixture: three genes, two guides each, three gene pairs.
    groups = [np.array([0, 1]), np.array([2, 3]), np.array([4, 5])]
    pairs = np.array([[0, 1], [0, 2], [1, 2]])
    baseline = np.array([[1., 2., 3.], [4., 5., 6.]])
    singles = np.array([[0., 1., 2.], [3., 4., 5.]])
    counts = np.full((2, 3, 6, 6), 100.)
    counts[0, 1][np.ix_(groups[0], groups[1])] = 0
    expected_floor = np.array([[True, False, False], [False, False, False]])

    def run_synthetic_loop(tree):
        namespace = {'np': np, 'counts': counts.copy(), 'mask': np.ones((6, 6), dtype=bool),
                     'groups': groups, 'pairs': pairs, 'floor_pair': np.zeros((2, 3), dtype=bool),
                     'b': baseline.copy()}
        fragment = ast.fix_missing_locations(ast.Module([deepcopy(floor_loop(function(tree, 'main')))], []))
        exec(compile(fragment, '<synthetic-floor-loop-only>', 'exec'), namespace)
        return namespace

    broken = run_synthetic_loop(original)
    repaired = run_synthetic_loop(corrected)
    np.testing.assert_array_equal(broken['floor_pair'], expected_floor)
    np.testing.assert_array_equal(repaired['floor_pair'], expected_floor)
    np.testing.assert_array_equal(broken['b'], [4, 5])
    np.testing.assert_array_equal(repaired['b'], baseline)
    old_module = import_safe('a_original_caller_review', 'a_experiment.py')
    new_module = import_safe('a_corrected_caller_review', 'a_experiment_corrected.py')
    try:
        old_module.source_features(broken['b'][0], singles, pairs, 3)
    except ValueError as error:
        assert 'size 1' in str(error) and 'size 3' in str(error)
        original_error = str(error)
    else:
        raise AssertionError('Original shadowing failure was not reproduced')
    for source in [0, 1]:
        actual = new_module.source_features(repaired['b'][source], singles, pairs, 3)
        expected = old_module.source_features(baseline[source], singles, pairs, 3)
        assert actual[0].shape == (3, 16) and actual[1].shape == (3, 3)
        assert all(np.isfinite(x).all() for x in actual)
        for x, y in zip(actual, expected):
            np.testing.assert_array_equal(x, y)
    try:
        new_module.source_features(broken['b'][0], singles, pairs, 3)
    except AssertionError:
        pass
    else:
        raise AssertionError('Corrected shape guard accepted a scalar baseline')
    assert sha(EPISODE / 'a_experiment_corrected.py') == CORRECTED_SHA
    assert sha(EPISODE / 'a_launcher_corrected.py') == LAUNCHER_SHA
    return {'status': 'PASS_SYNTHETIC_CALLER_FLOW_AND_STATIC_REPAIR_ONLY',
            'original_failure_reproduced': original_error,
            'root_cause': 'floor loop overwrites baseline b with a two-guide index vector',
            'corrected_baseline_shape': [2, 3], 'feature_shape': [3, 16],
            'graph_shape': [3, 3], 'floor_QC_unchanged': True,
            'all_other_experiment_functions_AST_unchanged': True,
            'corrected_experiment_sha256': CORRECTED_SHA,
            'corrected_launcher_sha256': LAUNCHER_SHA,
            'original_frozen_files_unchanged': True,
            'real_values_accessed': False, 'model_fit_or_real_launch': False,
            'forbidden_functions_called': []}


if __name__ == '__main__':
    result = check()
    (OUT / 'regression_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
