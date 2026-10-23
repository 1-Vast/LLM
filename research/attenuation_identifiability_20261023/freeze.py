"""Freeze independent reviews and exact diagnostic before saved-state access."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/attenuation_identifiability'
assert not (OUT / 'FREEZE.json').exists()
paths = [Path(__file__), Path(__file__).with_name('diagnostic.py'), OUT / 'PROTOCOL.md',
         ROOT / 'log/20261023/mixed_feedback_estimator/STATE_BY_GEM.npz',
         ROOT / 'log/20261023/reusable_error_mechanism/OVERLAP_ARRAYS.npz',
         ROOT / 'log/20261023/reusable_error_mechanism/ATTENUATION_ARRAYS.npz']
for role in ['constructive', 'critic', 'source']:
    assert (OUT / role / 'INDEPENDENT.md').exists() and (OUT / role / 'CROSS.md').exists(), role
    paths.extend((OUT / role).glob('*.md'))
result = dict(utc=datetime.now(timezone.utc).isoformat(),
              files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))})
(OUT / 'FREEZE.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(result['files']), utc=result['utc']), indent=2))
