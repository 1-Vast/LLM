"""Bind the approved single experiment before reading its saved state arrays."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reusable_error_mechanism'
OLD = ROOT / 'log/20261023/mixed_feedback_estimator'
assert not (OUT / 'OVERLAP_FREEZE.json').exists()
paths = [OUT / 'OVERLAP_PROTOCOL.md', Path(__file__), Path(__file__).with_name('overlap.py'),
         OLD / 'STATE_BY_GEM.npz', OLD / 'OOF_STATE.npz', OLD / 'support/SOURCE_PAIR_METADATA.csv']
for role in ['constructive', 'source', 'critic']:
    assert (OUT / role / 'INDEPENDENT.md').exists() and (OUT / role / 'CROSS.md').exists(), role
    paths.extend((OUT / role).glob('*.md'))
record = dict(utc=datetime.now(timezone.utc).isoformat(),
              independent_opposition='all three original and actual cross reports retained before experiment',
              files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))})
(OUT / 'OVERLAP_FREEZE.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(bound_files=len(record['files']), utc=record['utc']), indent=2))
