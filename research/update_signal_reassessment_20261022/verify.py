"""Seal this bounded evidence phase and check its immediate predecessor."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/update_signal_reassessment'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


previous = json.loads((ROOT / 'log/20261022/decision_update_mechanism/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
files = {}
for folder in (PHASE, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL',
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Local byte integrity only; no biological reproduction or global provenance repair',
          'files': files}
(PHASE / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
