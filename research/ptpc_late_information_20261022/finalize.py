"""Verify local frozen inputs and predecessor phase; bind listed new evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_late_information'
OLD = ROOT / 'log/20261022/ptpc_update_opportunity/FINAL_BINDINGS.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks = {}
for label, manifest, key in [('prediction', OUT / 'PREDICTION_FREEZE.json', 'bindings'),
                             ('predecessor_phase', OLD, 'files')]:
    bindings = json.loads(manifest.read_text('utf-8'))[key]
    for name, expected in bindings.items():
        assert digest(ROOT / name) == expected, name
    checks[label] = len(bindings)
target = OUT / 'FINAL_BINDINGS.json'
assert not target.exists()
files = sorted(p for folder in (OUT, Path(__file__).parent,
                                ROOT / 'research/ptpc_late_information_audit_20261022')
               for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
record = {'scope': 'Listed local files and predecessor phase only; historical provenance drift remains unresolved',
          'goal': 'ACTIVE / NOT_ACHIEVED', 'checks': checks,
          'files': {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'checks': checks, 'new_files_bound': len(files), 'result': 'PASS'}))
