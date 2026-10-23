"""Verify actual HTTP receipts and the immediate predecessor, then seal locally."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/plk1_payload_qualification'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


previous = json.loads((ROOT / 'log/20261022/update_signal_reassessment/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
requests = {'GSE203237': 200, 'GSM6165155': 200, 'alternative/biorxiv': 200,
            'alternative/primary': 429, 'alternative/epmc_primary': 500}
for name, status in requests.items():
    receipt = json.loads((OUT / (name + '.receipt.json')).read_text(encoding='utf-8'))
    body = OUT / (name + '.body')
    assert receipt['status'] == status
    assert receipt['sha256'] == digest(body)
    assert receipt['bytes'] == body.stat().st_size
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'http_receipts_checked': len(requests),
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Local receipt and byte integrity only; no biological experiment or global provenance certification',
          'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
