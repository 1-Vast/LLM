"""Verify this source/schema acquisition phase, including recorded HTTP failures."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/multi_context_state_function'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


previous = json.loads((ROOT / 'log/20261022/plk1_payload_qualification/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
statuses = Counter()
for receipt_file in sorted((OUT / 'root_sources').glob('*.receipt.json')):
    stem = receipt_file.name.removesuffix('.receipt.json')
    receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
    filename = {'annotation': 'annotated_embedding_coordinates.csv',
                'growth_workbook': 'NIHMS1812939-supplement-11.xlsx'}.get(stem, stem + '.body')
    body = receipt_file.parent / filename
    assert body.stat().st_size == receipt['bytes']
    assert digest(body) == receipt['sha256']
    statuses[receipt['status']] += 1
download = json.loads((OUT / 'data/DOWNLOAD_RECEIPT.json').read_text(encoding='utf-8'))
state = OUT / 'data/K562_gwps_raw_bulk_01.h5ad'
assert state.stat().st_size == download['bytes'] == 374587922
assert digest(state) == download['sha256']
statuses[download['status']] += 1
assert dict(statuses) == {200: 13, 429: 1, 403: 1, 404: 1}, statuses
assert json.loads((OUT / 'root_sources/SUPPLEMENT_WORKBOOK_SCHEMAS.json').read_text(encoding='utf-8')) == {}
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'http_status_counts': dict(statuses),
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Artifact identity/byte receipts/schema only; not a functional join or biological performance validation',
          'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
