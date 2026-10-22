"""Independent postrun arithmetic audit; reads only saved JSON, never the workbook."""
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
import hashlib
import json
from pathlib import Path
import re

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/efaecalis_dynamic_qualification/rank_pilot'
METHODS = ['ridge6', 'day6', 'ridge1', 'prefix_mean', 'knn3', 'calendar']
COMPARATORS = ['day6', 'ridge1']
SALT = 'efaecalis-rank-gate-v1'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def load(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def id_hash(kind, ident):
    return hashlib.sha256(f'{SALT}|{kind}|{ident}'.encode()).hexdigest()


def sorted_midranks(matrix):
    """Group a stable sorted list, assigning the mean occupied percentile."""
    answer = np.empty_like(matrix, dtype=float)
    for row_number, row in enumerate(matrix):
        order = sorted(range(len(row)), key=lambda j: row[j])
        start = 0
        while start < len(row):
            end = start + 1
            while end < len(row) and row[order[end]] == row[order[start]]:
                end += 1
            answer[row_number, order[start:end]] = (start + end)/(2*len(row))
            start = end
    return answer


def augmented_ridge(x, y, new_x):
    """Solve penalized least squares with an explicit unpenalized intercept."""
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.column_stack([np.zeros(x.shape[1]), np.eye(x.shape[1])])
    coefficients = np.linalg.lstsq(np.vstack([design, penalty]),
                                  np.r_[y, np.zeros(x.shape[1])], rcond=None)[0]
    return np.column_stack([np.ones(len(new_x)), new_x]) @ coefficients


def independent_predictions(prefix, historical_future, dev, test):
    train = sorted_midranks(prefix[:, np.array(dev)-1]).T
    new = sorted_midranks(prefix[:, np.array(test)-1]).T
    target = sorted_midranks(historical_future).mean(axis=0)
    knn = []
    for row in new:
        neighbors = sorted(range(len(dev)), key=lambda j:
                           (sum((train[j]-row)**2), id_hash('tie', dev[j])))[:3]
        knn.append(np.mean(target[neighbors]))
    return {'ridge6': augmented_ridge(train, target, new),
            'ridge1': augmented_ridge(train[:, -1:], target, new[:, -1:]),
            'day6': new[:, -1], 'prefix_mean': new.mean(axis=1),
            'knn3': np.array(knn), 'calendar': np.full(len(test), .5)}


def choose(predictions, ids):
    return {m: sorted(range(len(ids)), key=lambda j:
                     (predictions[m][j], id_hash('tie', ids[j]), j))[:3] for m in METHODS}


def evaluate(predictions, future, ids):
    quality = 1-sorted_midranks(future).mean(axis=0)
    selected = choose(predictions, ids)
    return {m: float(quality[selected[m]].mean()) for m in METHODS}, selected, quality


def close(actual, expected):
    return bool(np.allclose(actual, expected, rtol=0, atol=1e-12))


def main():
    opened, result = load('OPENED_RESPONSES.json'), load('RESULT.json')
    freeze, started, sensitivity = load('FREEZE.json'), load('READ_STARTED.json'), load('SENSITIVITY.json')
    checks = {}
    coordinates = {f'{chr(column)}{row}' for column in range(ord('D'), ord('W')+1)
                   for row in [*range(35, 41), *range(42, 48)]}
    checks['exact240_coordinate_set'] = set(opened['values']) == coordinates == set(freeze['response_coordinates']) and len(coordinates) == 240
    plain = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')
    checks['all_saved_values_plain_finite'] = all(isinstance(v, str) and plain.fullmatch(v)
                                               and Decimal(v).is_finite() for v in opened['values'].values())
    checks['identity_metadata'] = (opened['sheet'] == 'Fig4B' and opened['days_prefix'] == list(range(1, 7))
                                   and opened['days_future'] == list(range(8, 14))
                                   and opened['ids_in_source_column_order'] == list(range(1, 21)))
    source_record = next(f for f in freeze['files'] if f['path'].endswith('.raw.xlsx'))
    checks['source_hash_receipts_agree'] = (source_record['sha256'] == opened['source_sha256'] == started['source_sha256']
                                           == '273cc82c826f245be228a7fd21673fca13eaee1b949183f3b179b86bbce1fb27')
    prefix = np.array([[float(opened['values'][f'{chr(c)}{r}']) for c in range(ord('D'), ord('W')+1)] for r in range(35, 41)])
    future = np.array([[float(opened['values'][f'{chr(c)}{r}']) for c in range(ord('D'), ord('W')+1)] for r in range(42, 48)])
    checks['float_arrays_finite'] = bool(np.isfinite(prefix).all() and np.isfinite(future).all())
    ordered = sorted(range(1, 21), key=lambda ident: id_hash('split', ident))
    dev, test = ordered[:10], ordered[10:]
    checks['split_exact'] = dev == freeze['development_ids'] == result['development_ids'] and test == freeze['test_ids'] == result['test_ids']
    predictions = independent_predictions(prefix, future[:, np.array(dev)-1], dev, test)
    changed_future = future.copy()
    changed_future[:, np.array(test)-1] = -12345
    changed_predictions = independent_predictions(prefix, changed_future[:, np.array(dev)-1], dev, test)
    checks['test_future_perturbation_does_not_change_predictions'] = all(np.array_equal(predictions[m], changed_predictions[m]) for m in METHODS)
    checks['all_predictions_match'] = all(close(predictions[m], result['predictions'][m]) for m in METHODS)
    test_future = future[:, np.array(test)-1]
    utilities, selected, quality = evaluate(predictions, test_future, test)
    rosters = {m: [test[j] for j in selected[m]] for m in METHODS}
    checks['all_rosters_match'] = rosters == result['selected_ids']
    checks['all_utilities_match'] = all(close(utilities[m], result['utilities'][m]) for m in METHODS)
    checks['future_quality_match'] = close(quality, result['test_future_relative_rank_quality'])
    exact_quality = []
    for j in range(len(test)):
        rank_sum = sum((Fraction(2*sum(row < row[j])+sum(row == row[j]), 2*len(test)) for row in test_future), Fraction())
        exact_quality.append(1-rank_sum/6)
    exact_utilities = {m: sum((exact_quality[j] for j in selected[m]), Fraction())/3 for m in METHODS}
    checks['rational_utilities_match'] = all(close(float(exact_utilities[m]), utilities[m]) for m in METHODS)
    rng = np.random.default_rng(20261022)
    bootstrap = {m: [] for m in COMPARATORS}
    for _ in range(10000):
        indices = rng.integers(0, len(test), len(test))
        sampled = {m: predictions[m][indices] for m in METHODS}
        utility, _, _ = evaluate(sampled, test_future[:, indices], [test[j] for j in indices])
        for m in COMPARATORS:
            bootstrap[m].append(utility['ridge6']-utility[m])
    checks['all10000_bootstrap_differences_match'] = all(close(bootstrap[m], sensitivity['bootstrap_paired_differences'][m]) for m in COMPARATORS)
    quantiles = {m: np.quantile(bootstrap[m], [.025, .5, .975]).tolist() for m in COMPARATORS}
    checks['all_bootstrap_quantiles_match'] = all(close(quantiles[m], result['bootstrap_sensitivity_quantiles'][m]) for m in COMPARATORS)
    deletion = []
    for removed in combinations(range(len(test)), 2):
        indices = [j for j in range(len(test)) if j not in removed]
        utility, _, _ = evaluate({m: predictions[m][indices] for m in METHODS}, test_future[:, indices], [test[j] for j in indices])
        deletion.append({'removed_ids': [test[j] for j in removed], 'differences': {m: utility['ridge6']-utility[m] for m in COMPARATORS}})
    checks['all45_delete_two_differences_match'] = len(deletion) == len(sensitivity['delete_two']) == 45 and all(
        a['removed_ids'] == b['removed_ids'] and all(close(a['differences'][m], b['differences'][m]) for m in COMPARATORS)
        for a, b in zip(deletion, sensitivity['delete_two']))
    checks['sensitivity_not_nominal_CI'] = sensitivity['fixed_fit'] is True and sensitivity['nominal_CI_claim'] is False
    differences = {m: utilities['ridge6']-utilities[m] for m in COMPARATORS}
    gate_conditions = {m: {'point_at_least_0.10': differences[m] >= .10, 'lower_quantile_above_0': quantiles[m][0] > 0} for m in COMPARATORS}
    passed = all(all(conditions.values()) for conditions in gate_conditions.values())
    checks['primary_differences_match'] = all(close(differences[m], result['primary_differences'][m]) for m in COMPARATORS)
    checks['registered_stop_matches'] = not passed and result['status'] == 'STOP_THIS_SOURCE_CONFIGURATION_FOR_FRAMEWORK_EXPANSION'
    checks['freeze_before_read_before_result'] = datetime.fromisoformat(freeze['utc']) < datetime.fromisoformat(started['utc']) < datetime.fromisoformat(result['utc'])
    frozen_checks = [{'path': f['path'], 'independently_rehashed': True, 'unchanged': sha(f['path']) == f['sha256']}
                     for f in freeze['files'] if f['path'] != source_record['path']]
    checks['all10_nonworkbook_frozen_files_unchanged'] = len(frozen_checks) == 10 and all(f['unchanged'] for f in frozen_checks)
    checks['all11_root_execution_freeze_checks_pass'] = len(result['frozen_checks']) == len(freeze['files']) == 11 and all(f['unchanged'] for f in result['frozen_checks'])
    checks['source_census_budget_and_claims'] = (result['response_census'] == {'plain_finite_numeric': 240, 'excluded': 0, 'imputed': 0}
        and result['budget'] == {'development_prefix': 60, 'development_future': 60, 'test_prefix': 60, 'test_future_evaluation': 60, 'future_verification_slots_per_arm': 18}
        and result['claims'] == {'world_model': 'NOT_TESTED', 'agent': 'NOT_TESTED', 'inheritance': 'NOT_TESTED', 'RSI': 'NOT_TESTED', 'novel_algorithm': False})
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS_INDEPENDENT_ARITHMETIC_AUDIT' if all(checks.values()) else 'AUDIT_MISMATCH',
              'checks': checks, 'development_ids': dev, 'test_ids': test, 'utilities': utilities,
              'exact_utilities': {m: str(value) for m, value in exact_utilities.items()}, 'selected_ids': rosters,
              'test_quality_by_id': {str(ident): str(value) for ident, value in zip(test, exact_quality)},
              'primary_differences': differences, 'bootstrap_sensitivity_quantiles': quantiles,
              'gate_conditions': gate_conditions, 'nonworkbook_frozen_checks': frozen_checks,
              'original_workbook_reopened': False, 'main_program_rerun': False, 'API_calls': 0,
              'input_hashes': {name: sha(OUT/name) for name in ['OPENED_RESPONSES.json', 'RESULT.json', 'SENSITIVITY.json', 'FREEZE.json', 'READ_STARTED.json']},
              'verification_code_sha256': sha(__file__),
              'limits': ['Source workbook hash is taken from matching freeze/read/execution receipts; auditor did not reopen workbook.',
                         'This verifies saved arithmetic, not independent biological replication or nominal CI coverage.',
                         'Bootstrap recomputation is a postrun audit of existing arrays, not a second source-opening experiment.']}
    with (OUT/'POSTRUN_VERIFICATION.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({k: report[k] for k in ['status', 'checks', 'exact_utilities', 'gate_conditions']}))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
