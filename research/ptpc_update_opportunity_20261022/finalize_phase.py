"""Verify the prediction contract, then bind this completed phase locally."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_update_opportunity'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


freeze = json.loads((OUT / 'BASELINE_PREDICTION_FREEZE.json').read_text('utf-8'))
for name, expected in freeze['bindings'].items():
    assert digest(ROOT / name) == expected, name

target = OUT / 'FINAL_BINDINGS.json'
assert not target.exists()
paths = sorted(p for folder in (OUT, Path(__file__).parent)
               for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
record = {
    'scope': 'Local listed phase files only; no global historical integrity claim',
    'goal_status': 'ACTIVE / NOT_ACHIEVED',
    'prediction_contract_checks': len(freeze['bindings']),
    'files': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'prediction_contract_checks': len(freeze['bindings']),
                  'local_files_bound': len(paths), 'result': 'PASS'}))
