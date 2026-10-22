"""Non-fitting verification and exact resource accounting for this phase."""
import hashlib
import json
from pathlib import Path

import numpy as np

from hts_gate import LOG, OUT as GATE, ROOT, macro_losses


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    checks = []

    def check(name, ok):
        checks.append({'name': name, 'pass': bool(ok)})

    receipts = (list((LOG/'root_scout').glob('*.NETWORK.json')) +
                list((LOG/'skeptic').glob('*_RECEIPT.json')) +
                list((LOG/'functional_auditor').glob('REQUEST_*.json')))
    request_rows = []
    for path in sorted(receipts):
        r = load(path)
        body = Path(r['body_path'])
        raw = body.read_bytes()
        expected_len = r.get('bytes', r.get('retained_bytes', r.get('body_bytes')))
        check(path.name+'_length', len(raw) == expected_len)
        check(path.name+'_sha256', hashlib.sha256(raw).hexdigest() == r['sha256'])
        request_rows.append({'receipt': str(path.relative_to(ROOT)),
                             'status': r.get('status'), 'body_bytes': len(raw)})
    for name, md5 in [('hts001.body', 'a5959a38166685707e840369ce34d74d'),
        ('hct116_replicates_fresh_object.body', 'ae55aacf1f6549b04471f9d9d68e6cfe'),
        ('hct116_dose_response_fresh_object.body', '010489434a9e563f4f23afa304c70aca')]:
        check(name+'_manifest_md5', hashlib.md5((LOG/'root_scout'/name).read_bytes()).hexdigest() == md5)
    freeze, result = load(GATE/'MODEL_FREEZE_BEFORE_TEST_TARGETS.json'), load(GATE/'RESULT.json')
    identity = load(GATE/'IDENTITY_SPLIT_BEFORE_RESPONSES.json')
    check('split_partition_unique_14', len(set(sum(identity['split'].values(), []))) == 14)
    check('eligible_no_exclusions', identity['eligible'] == 1960 and identity['excluded'] == [])
    check('test_group_size', identity['counts']['test'] == result['test_n_wells'] == 420)
    check('training_only_alpha_11_trials', len(freeze['alpha_trials']) == 11)
    check('direct_14_trials', len(freeze['direct_trials']) == 14)
    for path, sha in freeze['sha256'].items():
        check('frozen_'+path, hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha)
    check('freeze_precedes_result_mtime',
          (GATE/'MODEL_FREEZE_BEFORE_TEST_TARGETS.json').stat().st_mtime_ns <
          (GATE/'RESULT.json').stat().st_mtime_ns)
    y = np.array(result['test_targets'])
    for name, pred in freeze['test_predictions'].items():
        recomputed = macro_losses([tuple(k) for k in freeze['test_keys']], np.array(pred), y)
        check('recompute_macro_'+name, recomputed == result['scores'][name])
    pp = freeze['test_predictions']
    check('exact_search_equals_updater', pp['equal_budget_search'] == pp['inherited_psi1'])
    check('exact_preset_mixture_equals_updater', pp['simple_half_mixture'] == pp['inherited_psi1'])
    check('gate_stopped', result['advance_signal'] is False)
    resources = {'public_get_count': len(receipts),
        'root_get_count': sum('root_scout' in str(p) for p in receipts),
        'skeptic_get_count': sum('skeptic' in str(p) for p in receipts),
        'functional_auditor_get_count': sum('functional_auditor' in str(p) for p in receipts),
        'retained_http_body_bytes': sum(r['body_bytes'] for r in request_rows),
        'requests': request_rows,
        'deepseek': load(LOG/'DEEPSEEK_RECEIPT.json')['provider_usage'],
        'completion_transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT',
        'measured_gate_executions': 1, 'direct_fits_train': 14,
        'direct_selected_refits_train_validation': 1, 'alpha_program_trials': 11,
        'ordinary_equal_budget_program_trials': 11,
        'gate_elapsed_seconds': result['elapsed_seconds'],
        'new_wet_lab_experiments': 0, 'author_contacts': 0}
    audit = {'checks': checks, 'all_pass': all(c['pass'] for c in checks),
             'check_count': len(checks), 'resources': resources}
    with (LOG/'VERIFICATION.json').open('x', encoding='utf-8') as f:
        json.dump(audit, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({'all_pass': audit['all_pass'], 'checks': len(checks),
                      'public_get_count': len(receipts),
                      'retained_http_body_bytes': resources['retained_http_body_bytes'],
                      'gate_elapsed_seconds': result['elapsed_seconds']}))
    return 0 if audit['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
