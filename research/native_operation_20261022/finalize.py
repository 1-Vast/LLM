"""Seal this research decision without rerunning any scientific experiment."""
import ast
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/native_operation'
OUT = LOG / 'root'
CODE = [ROOT / 'research' / name for name in (
    'native_operation_20261022', 'native_improver_20261022', 'native_biological_20261022')]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def main():
    spec = importlib.util.spec_from_file_location('previous_preservation',
        ROOT / 'research/cipa_control_information_20261022/preserve.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    preservation = previous.verify()
    for name in ('cipa_control_information', 'contrast_gate_check', 'mse_source_gate'):
        manifest = ROOT / f'log/20261022/{name}/FINAL_FILE_INVENTORY.json'
        preservation['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
        for record in load(manifest)['files']:
            path = ROOT / record['path']
            preservation['checks'].append({'path': record['path'], 'passed': path.is_file()
                and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    assert len(preservation['checks']) == 6580
    preservation.update(passed=all(row['passed'] for row in preservation['checks']),
                        utc=datetime.now(timezone.utc).isoformat())
    assert preservation['passed']

    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def bound(path, expected, label, size=None):
        # Navigation is intentionally mutable. Its exact pre-edit content was
        # retained before the new navigation entry; original seals stay intact.
        actual = OUT / 'START_REPORT_SNAPSHOT.md' if path == ROOT / 'research/REPORT.md' else path
        check(label, actual.is_file() and sha(actual) == expected
              and (size is None or actual.stat().st_size == size))

    def walk(value, seal):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                path = Path(value['path'])
                if not path.is_absolute():
                    path = ROOT / path if (ROOT / path).is_file() else seal.parent / path
                bound(path, value['sha256'], f'{seal.relative_to(LOG)}:{value["path"]}', value.get('bytes'))
            for child in value.values():
                walk(child, seal)
        elif isinstance(value, list):
            for child in value:
                walk(child, seal)

    seals = sorted(LOG.rglob('*SEAL.json'))
    for mandatory in ('proposer/INITIAL_SEAL.json', 'improver/INDEPENDENT_SEAL.json',
                      'biology/INDEPENDENT_SEAL.json', 'improver/OPPOSING_STENCIL_SEAL.json',
                      'biology/CROSS_CRITIQUE_SEAL.json', 'improver/OPPOSING_BIOLOGY_SEAL.json',
                      'proposer/FINAL_SEAL.json', 'improver/FINAL_REVIEW_SEAL.json',
                      'improver/POSTSEAL_REJOINDERS_SEAL.json', 'biology/FINAL_REVIEW_SEAL.json'):
        check('required_seal:' + mandatory, LOG / mandatory in seals)
    for seal in seals:
        walk(load(seal), seal)

    for folder in CODE:
        for path in sorted(folder.glob('*.py')):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            check('python_parse:' + path.relative_to(ROOT).as_posix(), True)

    proposer = load(LOG / 'proposer/EXACT_FALSIFIER_RESULT.json')
    check('proposer_all_recorded_checks', proposer['passed'] and all(c['passed'] for c in proposer['checks']))
    check('proposer_29_algebra_13_artifact_checks', proposer['unique_algebra_checks'] == 29
          and proposer['sealed_artifacts_verified'] == 13 and len(proposer['checks']) == 42)
    bound(CODE[0] / 'proposer_exact_falsifier.py', proposer['code_sha256'], 'proposer_result_code_binding')
    bound(LOG / 'proposer/INITIAL_SEAL.json', proposer['initial_seal_sha256'], 'proposer_result_initial_binding')
    improver = load(LOG / 'improver/OPERATION_CHECK.json')
    check('improver_243_and_9_exact_cases', improver['exact_outer_update_equivalence_cases'] == 243
          and improver['collinear_scalar_step_equivalence_cases'] == 9)
    check('improver_faithful_control_zero_gap', improver['new_minus_faithful_conventional_utility'] == '0'
          and improver['later_external_loss'] == {'old': '1', 'new': '0', 'conventional': '0'})
    bound(CODE[1] / 'check_operation.py', improver['code_sha256'], 'improver_result_code_binding')
    biology = load(LOG / 'biology/algebra_result.json')
    check('biology_five_synthetic_assertions', biology['all_passed']
          and len(biology['checks']) == 5 and all(biology['checks'].values()))

    source_receipts = sorted((OUT / 'sources').glob('*.receipt.json'))
    check('two_root_fulltext_receipts', len(source_receipts) == 2)
    for receipt in source_receipts:
        data = load(receipt)
        prefix = receipt.name.removesuffix('.receipt.json')
        bound(receipt.with_name(prefix + '.body'), data['sha256'], 'primary_html:' + prefix, data['bytes'])
        bound(receipt.with_name(prefix + '.txt'), data['projection_sha256'], 'primary_projection:' + prefix)
        check('primary_http_200:' + prefix, data['status'] == 200)
    search_receipts = sorted((OUT / 'search').glob('*.receipt.json'))
    check('four_root_metadata_receipts', len(search_receipts) == 4)
    for receipt in search_receipts:
        data = load(receipt)
        prefix = receipt.name.removesuffix('.receipt.json')
        bound(receipt.with_name(prefix + '.body'), data['sha256'], 'search_body:' + prefix, data['bytes'])
        check('search_http_200:' + prefix, data['status'] == 200)
    for data in load(LOG / 'improver/PRIMARY_SOURCE_RECEIPTS.json'):
        bound(LOG / 'improver' / (data['name'] + '.html'), data['sha256'], 'improver_primary:' + data['name'], data['bytes'])
    data = load(LOG / 'biology/supplement_get_receipt.json')
    bound(LOG / 'biology/supplement3.xlsx', data['sha256'], 'public_biology_supplement', data['bytes'])

    for name in ('DECISION.md', 'CONTINUATION.md', 'DEBATE_SYNTHESIS.md', 'ROOT_AUDIT.md'):
        check('root_evidence:' + name, (OUT / name).is_file())
    for name in ('proposer/CROSS_EXCHANGE.md', 'biology/CROSS_EXCHANGE.md',
                 'improver/RECIPROCAL_EXCHANGE_FINAL.md', 'improver/POSTSEAL_REJOINDERS.md'):
        check('actual_exchange:' + name, (LOG / name).is_file())
    check('zero_proposer_biological_result', proposer['predictive_fits'] == 0
          and proposer['assay_fields_read'] == 0 and not proposer['biological_success'])
    check('zero_improver_biological_result', improver['biological_predictive_fits'] == 0
          and improver['new_biological_values_accessed'] == 0 and improver['api_calls'] == 0)
    write('PREDECESSOR_PRESERVATION.json', preservation)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
        'predecessor_entries': len(preservation['checks']),
        'preservation_report_sha256': sha(OUT / 'PREDECESSOR_PRESERVATION.json'),
        'independent_seals_verified': [p.relative_to(LOG).as_posix() for p in seals],
        'navigation_input_resolution': 'Exact START_REPORT_SNAPSHOT.md is used for historical research/REPORT.md inputs; original seals unchanged.',
        'new_deepseek_calls': 0, 'new_predictive_fits': 0, 'biological_assay_scalar_decodes': 0,
        'scientific_performance_success': False, 'full_goal': 'ACTIVE / NOT_ACHIEVED',
        'utc': datetime.now(timezone.utc).isoformat()})
    files = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for folder in [LOG] + CODE for p in sorted(folder.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': files, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'integrity_checks': len(checks),
                      'predecessor_entries': 6580, 'new_phase_files': len(files)}))


if __name__ == '__main__':
    main()
