"""Bind this bounded phase locally; does not certify historical integrity."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
phase = root / 'log/20261022/query_teacher_resolution'
files = sorted(p for p in phase.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json')
for folder in ('query_teacher_resolution_20261022', 'query_teacher_resolution_frontier_20261022'):
    files += sorted((root / 'research' / folder).glob('*.py'))
files.append(root / 'log/20261022/query_teacher_resolution_query_console.txt')
source = phase / 'frontier/sources/ebm.body'
receipt = json.loads((source.with_suffix('.receipt.json')).read_text(encoding='utf-8'))
assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt['sha256']
check = json.loads((phase / 'skeptic/CHECK.json').read_text(encoding='utf-8'))
assert check['outer_gradient_max_abs_difference'] < 1e-9
assert check['code_sha256'] == hashlib.sha256((root / 'research/query_teacher_resolution_20261022/skeptic_check.py').read_bytes()).hexdigest()
for role in ('frontier', 'skeptic', 'biology'):
    assert (phase / role / 'INDEPENDENT.md').is_file()
    assert (phase / role / 'CROSS.md').is_file()
result = {'status': 'PASS_LOCAL', 'scope': 'Current phase only; historical provenance drift unresolved',
          'files': {str(p.relative_to(root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(phase / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': result['status'], 'files': len(result['files'])}))
