"""Read-only audit of frozen code and exported gate products; no CSV or fit access."""
import ast
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/dead_stock_information_gate'
OUT = BASE / 'hct_gate'
CHECKS = []


def check(name, condition, detail=None):
    CHECKS.append({'name': name, 'pass': bool(condition), 'detail': detail})


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


freeze = load('PRE_RESPONSE_FREEZE.json')
cache = load('PREFIX_ONLY_KINETIC_CACHE.json')
source_path = ROOT / 'research/dead_stock_information_gate_20261022/hct_gate.py'
source = source_path.read_text(encoding='utf-8')
tree = ast.parse(source)
functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
for rel, expected in freeze['hashes'].items():
    if rel.endswith('hct_gate.py') or rel.endswith('HCT116_GATE_PROTOCOL.md'):
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        check('frozen_hash_' + Path(rel).name, actual == expected, actual)

keys = [tuple(k) for k in cache['keys']]
check('cache_keys_equal_freeze', cache['keys'] == freeze['keys'])
check('96_unique_physical_well_keys', len(keys) == len(set(keys)) == 96)
check('96_unique_well_ids', len({k[2] for k in keys}) == 96)
check('8_doses_4_contexts_3_wells', len({k[0] for k in keys}) == 8 and
      len({k[1] for k in keys}) == 4 and
      set(Counter(k[:2] for k in keys).values()) == {3})
check('prefix_cache_no_target_access', cache['future_target_values_accessed'] is False)
check('freeze_pre_response_marker', freeze['response_values_converted'] is False)
check('crossfit_scope_explicit', freeze['scope'] == 'grouped_crossfit_not_globally_unseen_test')
doses = freeze['outer_doses']
for outer, fold in freeze['folds'].items():
    train, val, historical = fold['inner_train'], fold['inner_validation'], fold['outer_train']
    check('split_' + outer, len(train) == 6 and len(historical) == 7 and
          outer not in historical and val not in train and
          set(train + [val]) == set(historical) == set(doses) - {outer})
    expected_val = min(historical, key=lambda c: hashlib.sha256(
        ('HCT116-deadstock-inner-v1|' + c).encode()).hexdigest())
    check('hash_validation_' + outer, val == expected_val)

summary = {}
for arm, fits in cache['kinetic'].items():
    check(arm + '_96_local_fits', len(fits) == 96)
    check(arm + '_four_fixed_starts', all(len(f['runs']) == 4 for f in fits))
    check(arm + '_finite_predictions', all(math.isfinite(f['prediction']) for f in fits))
    check(arm + '_prefix_loss_winner', all(f['winner'] == min(range(4),
          key=lambda i: (f['runs'][i]['cost'], i)) for f in fits))
    check(arm + '_winner_prediction_export', all(f['prediction'] ==
          f['runs'][f['winner']]['prediction'] for f in fits))
    check(arm + '_all_run_finite_and_bounds', all(math.isfinite(r['cost']) and
          math.isfinite(r['prediction']) and len(r['parameters']) == 5 and
          all(0 <= v <= .2 for v in r['parameters'][:4]) and
          0 <= r['parameters'][4] <= 1 and 0 < r['nfev'] <= 300
          for f in fits for r in f['runs']))
    check(arm + '_success_status_consistency', all(r['success'] == (r['status'] > 0)
          for f in fits for r in f['runs']))
    check(arm + '_unconverged_flag_truthful', all(f['all_starts_unconverged'] ==
          (not any(r['success'] for r in f['runs'])) and f['selected_converged'] ==
          f['runs'][f['winner']]['success'] for f in fits))
    check(arm + '_all_cap_mechanism_disqualification', all(
          (f['mechanism_qualification'] == 'UNQUALIFIED_FOR_MECHANISM') ==
          f['all_starts_unconverged'] for f in fits))
    computed = {'wells': len(fits),
                'all_starts_unconverged': sum(f['all_starts_unconverged'] for f in fits),
                'selected_unconverged': sum(not f['selected_converged'] for f in fits),
                'starts_unconverged': sum(not r['success'] for f in fits for r in f['runs']),
                'total_nfev': sum(r['nfev'] for f in fits for r in f['runs']),
                'total_seconds': sum(f['seconds'] for f in fits)}
    check(arm + '_summary_reconciles', computed == cache['kinetic_summary'][arm])
    summary[arm] = computed
    summary[arm]['status_counts'] = dict(Counter(str(r['status']) for f in fits for r in f['runs']))
    if arm == 'live_only':
        check('live_only_clearance_zero', all(r['parameters'][3] == 0
              for f in fits for r in f['runs']))

check('96_finite_ols_predictions', len(cache['ols_predictions']) == 96 and
      all(math.isfinite(v) for v in cache['ols_predictions']))
check('prefix_arithmetic_diagnostic_finite', math.isfinite(cache['prefix_total_identity_maxabs']))

def field_calls(node):
    return [call.args[2].value for call in ast.walk(node) if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name) and call.func.id == 'mean_field'
            and len(call.args) >= 3 and isinstance(call.args[2], ast.Constant)]

check('label_only_live_field_static', field_calls(functions['labels']) == ['intersect_live_cells'])
check('prefix_only_L_D_total_fields_static', set(field_calls(functions['prefix'])) ==
      {'intersect_live_cells', 'intersect_dead_cells', 'tot_cells'})
check('no_result_or_outer_prediction_products', not (OUT / 'RESULT.json').exists() and
      not (OUT / 'ALL_OUTER_PREDICTIONS_BEFORE_SCORING.json').exists())
check('no_fold_products', not list(OUT.glob('FOLD_*.json')))
failure = (OUT / 'FAILURE.txt').read_text(encoding='utf-8')
check('preserved_invalid_readout_failure', 'ValueError: invalid_observed_readout' in failure)
check('failure_at_first_training_label', 'ytrain = labels(choose_groups(train), train_doses)' in failure)
test_initial = (BASE / 'TESTS.txt').read_text(encoding='utf-8')
test_fixed = (BASE / 'TESTS_REPAIRED.txt').read_text(encoding='utf-8')
check('initial_synthetic_failure_retained', 'FAILED' in test_initial)
check('repaired_nine_tests_pass_retained', 'Ran 9 tests' in test_fixed and '\nOK' in test_fixed)
report = {'audit_scope': 'frozen code, freeze/cache/failure/test exports only; no raw CSV; no fit or rerun',
          'checks': CHECKS, 'n_checks': len(CHECKS), 'n_pass': sum(c['pass'] for c in CHECKS),
          'kinetic_summary': summary,
          'prefix_total_identity_maxabs': cache['prefix_total_identity_maxabs'],
          'decision': 'DATA_TARGET_QUALIFICATION_ABORT_NO_INFORMATION_RESULT'}
dest = BASE / 'skeptic/POST_RUN_AUDIT.json'
with dest.open('x', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False, allow_nan=False)
    f.write('\n')
print(json.dumps({'n_checks': report['n_checks'], 'n_pass': report['n_pass'],
                  'failed': [c for c in CHECKS if not c['pass']],
                  'kinetic_summary': summary,
                  'prefix_total_identity_maxabs': cache['prefix_total_identity_maxabs'],
                  'decision': report['decision']}, ensure_ascii=False))
