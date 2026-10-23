"""Local phase bindings plus predecessor hash audit; no performance rerun."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
phase = root / 'log/20261022/functional_error_structure'
previous = json.loads((root / 'log/20261022/query_teacher_resolution/VERIFICATION.json').read_text(encoding='utf-8'))
drift = [name for name, digest in previous['files'].items()
         if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
bindings = json.loads((phase / 'PRECOMPUTE_BINDINGS.json').read_text(encoding='utf-8'))
for name, digest in bindings.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for role in ('frontier', 'skeptic', 'biology'):
    assert (phase / role / 'INDEPENDENT.md').is_file()
    assert (phase / role / 'CROSS.md').is_file()
files = sorted(p for p in phase.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json')
files += sorted((root / 'research/functional_error_structure_20261022').glob('*.py'))
files.append(root / 'log/20261022/functional_error_structure_console.txt')
result = {'status': 'PASS_LOCAL' if not drift else 'PASS_CURRENT_WITH_PREDECESSOR_DRIFT',
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Current phase bindings only; not global provenance certification',
          'files': {str(p.relative_to(root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(phase / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'files': len(result['files']), 'predecessor_drift': drift}))
