"""Verify acquisition receipts and local artifact continuity; no performance claims."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/replogle_growth_acquisition'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


previous = json.loads((ROOT / 'log/20261022/multi_context_state_function/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
statuses = Counter()
for receipt_file in sorted(OUT.rglob('*.receipt.json')):
    receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
    body = receipt_file.with_name(receipt_file.name.removesuffix('.receipt.json') + '.body')
    assert body.stat().st_size == receipt['bytes'], body
    assert digest(body) == receipt['sha256'], body
    statuses[receipt['status']] += 1
assert dict(statuses) == {200: 11, 403: 1, 401: 1}, statuses
for stem in ('public_asset', 'public_asset1'):
    with (OUT / 'root_sources' / (stem + '.body')).open('rb') as stream:
        assert stream.read(4) == b'PK\x03\x04'
identity = json.loads((OUT / 'IDENTITY_JOIN.json').read_text(encoding='utf-8'))
assert identity['state_rows'] == identity['summary_rows'] == identity['state_in_library'] == identity['state_in_summary'] == 11258
assert identity['library_rows'] == 11294 and identity['target_ensembl_groups'] == 9853
assert identity['numeric_expression_or_assay_values_decoded'] is False
assert identity['functional_gamma_join'] == 'NOT_AUTHENTICATED'
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL',
          'http_status_counts': dict(statuses),
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Local receipts, file signatures and recorded identity counts; no biological performance or global provenance repair',
          'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
