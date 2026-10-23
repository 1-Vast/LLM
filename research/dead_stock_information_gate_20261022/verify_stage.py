"""No-fit source, historical-preservation and stopped-run verification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/dead_stock_information_gate'
OLD = ROOT/'log/20261022/functional_dynamics_gate'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    checks = []

    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})

    old_inventory = load(OLD/'FINAL_FILE_INVENTORY.json')
    for entry in old_inventory['files']:
        p = ROOT/entry['path']
        check('old_unchanged:'+entry['path'], p.stat().st_size == entry['bytes'] and
              hashlib.sha256(p.read_bytes()).hexdigest() == entry['sha256'])
    receipts = (list((LOG/'root_stack').glob('*.NETWORK.json'))+
                list((LOG/'skeptic').glob('*_RECEIPT.json'))+
                list((LOG/'data_auditor').glob('REQUEST_*.json')))
    requests = []
    for p in sorted(receipts):
        r = load(p)
        body_path = r.get('body_path')
        body = Path(body_path) if body_path else p.with_name(p.name.replace('REQUEST_', 'RESPONSE_')).with_suffix('.body')
        raw = body.read_bytes()
        size = r.get('bytes', r.get('retained_bytes', r.get('body_bytes')))
        sha = r.get('sha256', r.get('body_sha256'))
        check('receipt_size:'+p.name, size == len(raw))
        check('receipt_sha256:'+p.name, sha == hashlib.sha256(raw).hexdigest())
        requests.append({'receipt': str(p.relative_to(ROOT)), 'status': r.get('status'),
                         'http_body_bytes': len(raw)})
    gate = LOG/'hct_gate'
    freeze = load(gate/'PRE_RESPONSE_FREEZE.json')
    cache = load(gate/'PREFIX_ONLY_KINETIC_CACHE.json')
    for path, sha in freeze['hashes'].items():
        check('current_frozen:'+path, hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha)
    check('known_terminal_failure', 'invalid_observed_readout' in (gate/'FAILURE.txt').read_text())
    check('no_fold_predictions', not list(gate.glob('FOLD_*.json')))
    check('no_final_score', not (gate/'RESULT.json').exists())
    check('no_combined_predictions', not (gate/'ALL_OUTER_PREDICTIONS_BEFORE_SCORING.json').exists())
    check('prefix_only_target_not_read_yet', cache['future_target_values_accessed'] is False)
    check('ninety_six_unique_wells', len(set(map(tuple, freeze['keys']))) == 96)
    check('all_768_local_starts_success', all(r['success'] for fits in cache['kinetic'].values()
                                           for fit in fits for r in fit['runs']))
    check('all_prefix_fits_count', sum(len(fits) for fits in cache['kinetic'].values()) == 192)
    check('repaired_tests_pass', 'Ran 9 tests' in (LOG/'TESTS_REPAIRED.txt').read_text() and
          '\nOK' in (LOG/'TESTS_REPAIRED.txt').read_text())
    check('original_failed_test_retained', 'FAILED (failures=1)' in (LOG/'TESTS.txt').read_text())
    skeptic = load(LOG/'skeptic/POST_RUN_AUDIT.json')
    check('independent_nonfit_audit_pass', len(skeptic['checks']) == 56 and
          all(c['pass'] for c in skeptic['checks']))
    stack2, stack1 = load(LOG/'root_stack/INITIAL_STATE.json'), load(LOG/'root_stack/V1_INITIAL_STATE.json')
    check('v2_soft404_not_absence_of_all_versions', stack2['dataset']['status'] == 404)
    check('v1_actual_snapshot', stack1['dataset']['status'] == 200 and
          stack1['dataset']['snapshot']['doi'] == '10.17632/3pnv5wh5jm.1')
    check('v1_raw_files_still_unresolved', stack1['files']['list'] == [] and stack1['files']['filesLoading'])
    audit = {'checks': checks, 'all_pass': all(c['pass'] for c in checks), 'check_count': len(checks),
             'resources': {'public_GETs': len(receipts), 'HTTP_body_bytes': sum(r['http_body_bytes'] for r in requests),
                'requests': requests, 'deepseek_calls': 0, 'measured_gate_attempts': 1,
                'completed_direct_fits': 0, 'prefix_local_fits': 192, 'prefix_optimization_starts': 768,
                'kinetic_summary': cache['kinetic_summary'], 'wet_lab_experiments': 0},
             'prior_phase_unchanged_file_count': len(old_inventory['files']),
             'scientific_status': 'TARGET_QUALIFICATION_ABORT_NOT_A_CHANNEL_NEGATIVE'}
    with (LOG/'VERIFICATION.json').open('x', encoding='utf-8') as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'all_pass': audit['all_pass'], 'checks': len(checks),
                      'public_GETs': len(receipts), 'HTTP_body_bytes': audit['resources']['HTTP_body_bytes'],
                      'old_files_unchanged': len(old_inventory['files'])}))
    return 0 if audit['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
