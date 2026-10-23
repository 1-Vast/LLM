"""Verify independent/cross seals and the listed predecessor, then bind phase."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bindings):
    for name, expected in bindings.items():
        assert digest(ROOT / name.replace('\\', '/')) == expected, name
    return len(bindings)


checks = {}
for name in ('frontier/PROPOSAL_SEAL.json', 'frontier/CROSS_REVIEW_SEAL.json',
             'recursive/PROPOSAL_SEAL.json', 'recursive/CROSS_SEAL.json',
             'biology/INDEPENDENT_SEAL.json', 'biology/CROSS_REVIEW_SEAL.json'):
    seal = json.loads((OUT / name).read_text('utf-8-sig'))
    bindings = {row['path']: row['sha256'] for row in seal.get('files', [])}
    bindings.update(seal.get('bindings', {}))
    bindings.update(seal.get('inputs', {}))
    if 'file' in seal:
        bindings[seal['file']] = seal['sha256']
    assert bindings, name
    checks[name] = verify(bindings)
predecessor = ROOT / 'log/20261022/ptpc_late_information/FINAL_BINDINGS.json'
checks['listed_predecessor_phase'] = verify(json.loads(predecessor.read_text('utf-8'))['files'])
target = OUT / 'FINAL_BINDINGS.json'
assert not target.exists()
folders = [OUT] + sorted((ROOT / 'research').glob('early_update_mechanism*_20261022'))
paths = sorted(p for folder in folders for p in folder.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts)
record = {'created_utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Local listed phase, independent/cross bindings and listed predecessor only',
          'goal': 'ACTIVE / NOT_ACHIEVED',
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'platform': platform.platform(), 'numpy': numpy.__version__,
          'checks': checks, 'predecessor_manifest_sha256': digest(predecessor),
          'files': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'checks': checks, 'new_files_bound': len(paths), 'result': 'PASS'}))
