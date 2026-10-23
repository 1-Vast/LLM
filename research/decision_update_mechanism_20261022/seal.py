"""Current phase source and predecessor bindings; not global integrity proof."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
phase = root / 'log/20261022/decision_update_mechanism'
previous = json.loads((root / 'log/20261022/functional_error_structure/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, digest in previous['files'].items()
         if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
for stem in ('selectttrl', 'rettt'):
    source = phase / f'frontier/sources/{stem}.body'
    receipt = json.loads(source.with_suffix('.receipt.json').read_text(encoding='utf-8'))
    assert receipt['status'] == 200
    assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt['sha256']
for role in ('frontier', 'skeptic', 'biology'):
    assert (phase / role / 'INDEPENDENT.md').is_file()
    assert (phase / role / 'CROSS.md').is_file()
api = json.loads((phase / 'api/RECEIPT.json').read_text(encoding='utf-8'))
assert api['status'] == 'VALID_RESPONSE' and api['generated_code_executed'] is False
request_path = phase / 'api/EXACT_REQUEST.txt'
request_text = request_path.read_text(encoding='utf-8')
assert request_text == (phase / 'API_PROMPT.md').read_text(encoding='utf-8')
assert hashlib.sha256(request_text.encode('utf-8')).hexdigest() == api['request_sha256']
files = sorted(p for p in phase.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json')
files += sorted((root / 'research/decision_update_mechanism_20261022').glob('*.py'))
files.append(root / 'log/20261022/decision_update_mechanism_api_console.txt')
result = {'status': 'PASS_LOCAL' if not drift else 'PASS_CURRENT_WITH_PREDECESSOR_DRIFT',
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'api_request_text_sha256': api['request_sha256'],
          'api_request_persisted_bytes_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest(),
          'scope': 'Sources and current files only; no biological performance reproduction or global provenance certification',
          'files': {str(p.relative_to(root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(phase / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'files': len(result['files']), 'predecessor_drift': drift}))
