"""Verify all phase seals and predecessor inventories before finalizing once."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

from gate import OUT, ROOT, load, sha, write

PAIRS = ('mse_source_gate', 'mse_source_gate_audit', 'mse_source_gate_review', 'mse_mechanism_renewal')


def main():
    spec = importlib.util.spec_from_file_location('predecessors', ROOT / 'research/cipa_control_information_20261022/preserve.py')
    preserve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preserve)
    predecessor = preserve.verify()
    for name in ('cipa_control_information', 'contrast_gate_check'):
        manifest = ROOT / f'log/20261022/{name}/FINAL_FILE_INVENTORY.json'
        predecessor['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
        for record in load(manifest)['files']:
            path = ROOT / record['path']
            predecessor['checks'].append({'path': record['path'], 'passed': path.is_file()
                and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    assert len(predecessor['checks']) == 6488
    predecessor['passed'] = all(r['passed'] for r in predecessor['checks'])
    assert predecessor['passed']
    checks = []

    def resolve(name, directory):
        path = Path(name)
        if path.is_absolute():
            return path
        return ROOT / path if (ROOT / path).is_file() else directory / path

    def check(path, expected, seal):
        checks.append({'seal': seal.relative_to(ROOT).as_posix(),
                       'path': path.relative_to(ROOT).as_posix(),
                       'passed': path.is_file() and sha(path) == expected})

    logs = [ROOT / 'log/20261022' / name for name in PAIRS]
    seals = sorted({p for folder in logs for pattern in ('*SEAL.json', '*.seal.json') for p in folder.rglob(pattern)})
    seals.append(OUT / 'FREEZE.json')
    for seal in seals:
        data = load(seal)
        for key in ('files', 'input_files', 'inputs', 'evidence_hashes', 'review_files', 'reviewed_input_hashes'):
            records = data.get(key, {})
            records = records.items() if isinstance(records, dict) else ((r['path'], r['sha256']) for r in records)
            for name, expected in records:
                check(resolve(name, seal.parent), expected, seal)
        for key in ('opinion', 'review'):
            if key + '_sha256' in data:
                name = data.get(key + '_file', data.get(key))
                check(resolve(name, seal.parent), data[key + '_sha256'], seal)
        if 'sha256' in data:
            key = next(k for k in ('path', 'file', 'artifact', 'report') if k in data)
            check(resolve(data[key], seal.parent), data['sha256'], seal)
    assert all(c['passed'] for c in checks), [c for c in checks if not c['passed']]
    result = load(OUT / 'RESULT.json')
    assert result['checks'] == {'all_required_values_finite_and_in_contract': True,
                              'descriptive_oracle_gap_at_least_0.10': False,
                              'at_least_10_mixed_hit_patient_groups': True}
    assert result['decision'] == 'STOP_EXACT_CONFIGURATION'
    assert result['opportunity']['gap_exact'] == '181/3300'
    assert result['source_required_field_attempts'] == 10500
    audit = load(ROOT / 'log/20261022/mse_source_gate_audit/postrun/FINAL_NUMERICAL_AUDIT.json')
    assert audit['passed']
    assert (ROOT / 'log/20261022/mse_source_gate_audit/postrun/POSTRUN_REVIEW.md').is_file()
    assert (ROOT / 'log/20261022/mse_source_gate_review/POSTRUN_BIOLOGICAL_INTERPRETATION.md').is_file()
    assert (ROOT / 'log/20261022/mse_mechanism_renewal/BIOLOGICAL_EXCHANGE_SEAL.json').is_file()
    usage = []
    mechanism = ROOT / 'log/20261022/mse_mechanism_renewal'
    for name in ('api_constructive', 'api_critique'):
        receipt_path = mechanism / name / 'RECEIPT.json'
        receipt = load(receipt_path)
        # This phase's responses are byte-bound in its independent seal.
        check(mechanism / name / 'RESPONSE.md', receipt['response_sha256'], receipt_path)
        usage.append(receipt['usage']['total_tokens'])
    assert sum(usage) == 5222
    assert len(load(mechanism / 'ALGEBRA_RESULT.json')['checks']) == 4
    assert all(r['passed'] for r in load(mechanism / 'ALGEBRA_RESULT.json')['checks'])
    assert all(c['passed'] for c in checks)
    write('PREDECESSOR_PRESERVATION.json', predecessor)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
          'predecessor_entries': 6488, 'predecessor_report_sha256': sha(OUT / 'PREDECESSOR_PRESERVATION.json'),
          'provider_logical_calls': 2, 'provider_reported_tokens': 5222,
          'root_source_scalar_field_attempts': 10500, 'new_predictive_solver_fits': 0,
          'source_lopo_label_aggregations': 55, 'unique_final_synthetic_tests': 6,
          'mechanism_exact_checks': 4, 'development_later_scalar_accesses': 0,
          'full_goal': 'ACTIVE / NOT_ACHIEVED', 'utc': datetime.now(timezone.utc).isoformat()})
    folders = logs + [ROOT / 'research' / (name + '_20261022') for name in PAIRS]
    files = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for folder in folders for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': files, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'predecessors': 6488, 'integrity_checks': len(checks), 'new_files': len(files)}))


if __name__ == '__main__':
    main()
