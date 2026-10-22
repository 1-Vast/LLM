"""Verify predecessor preservation and seal this bounded scouting iteration."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/contrast_gate_check'
PAIRS = ('contrast_gate_check', 'contrast_mechanism_scout',
         'contrast_independent_review', 'biological_decision_scout')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def main():
    spec = importlib.util.spec_from_file_location(
        'preserve_preceding', ROOT / 'research/cipa_control_information_20261022/preserve.py')
    preserve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preserve)
    predecessor = preserve.verify()
    manifest = ROOT / 'log/20261022/cipa_control_information/FINAL_FILE_INVENTORY.json'
    predecessor['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
    for record in read(manifest)['files']:
        path = ROOT / record['path']
        predecessor['checks'].append({'path': record['path'], 'passed': path.is_file()
                                     and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    predecessor['passed'] = all(r['passed'] for r in predecessor['checks'])
    assert predecessor['passed'] and len(predecessor['checks']) == 6308
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

    logs = [ROOT / 'log/20261022' / pair for pair in PAIRS]
    for folder in logs:
        for seal in sorted({*folder.glob('*SEAL.json'), *folder.glob('*.seal.json')}):
            data = read(seal)
            for key in ('files', 'input_files', 'evidence_hashes', 'reviewed_input_hashes', 'review_files'):
                records = data.get(key, {})
                records = records.items() if isinstance(records, dict) else ((r['path'], r['sha256']) for r in records)
                for name, expected in records:
                    check(resolve(name, seal.parent), expected, seal)
            for prefix in ('opinion', 'review'):
                if prefix + '_file' in data:
                    check(resolve(data[prefix + '_file'], seal.parent), data[prefix + '_sha256'], seal)
            if 'sha256' in data:
                key = next(k for k in ('file', 'path', 'artifact', 'report') if k in data)
                check(resolve(data[key], seal.parent), data['sha256'], seal)
    result_path = OUT / 'RESULT.json'
    assert read(result_path)['passed'] and read(result_path)['checks'] == 6
    for name, expected in read(result_path)['files'].items():
        check(ROOT / name, expected, result_path)
    scout = ROOT / 'log/20261022/contrast_mechanism_scout'
    usages = []
    for name in ('api', 'api_direct'):
        receipt_path = scout / name / 'RECEIPT.json'
        receipt = read(receipt_path)
        response = scout / name / 'RESPONSE.md'
        normalized_hash = hashlib.sha256(response.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
        checks.append({'seal': receipt_path.relative_to(ROOT).as_posix(),
                       'path': response.relative_to(ROOT).as_posix(),
                       'passed': normalized_hash == receipt['response_sha256'],
                       'hash_semantics': 'universal-newline decoded logical text; raw bytes inventoried separately'})
        usages.append(receipt['usage'])
    assert sum(r['total_tokens'] for r in usages) == 16408
    assert all(r['passed'] for r in checks), [r for r in checks if not r['passed']]
    write('PREDECESSOR_PRESERVATION.json', predecessor)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
          'predecessors': 6308, 'predecessor_report_sha256': sha(OUT / 'PREDECESSOR_PRESERVATION.json'),
          'actual_provider_logical_calls': 2, 'actual_provider_tokens': 16408,
          'new_biological_fits': 0, 'root_exact_arithmetic_checks': 6,
          'full_goal': 'ACTIVE / NOT_ACHIEVED', 'utc': datetime.now(timezone.utc).isoformat()})
    folders = logs + [ROOT / 'research' / (pair + '_20261022') for pair in PAIRS]
    rows = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
            for folder in folders for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': rows, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'integrity_checks': len(checks), 'files': len(rows), 'predecessors': 6308}))


if __name__ == '__main__':
    main()
