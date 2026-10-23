"""Restore exact reviewed protocol bytes after moving accounting edits to a versioned file."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'
target = OUT/'PILOT_PROTOCOL.md'
seal = json.loads((OUT/'critic/PRE_EXECUTION_REVIEW.seal.json').read_text(encoding='utf-8'))
expected = next(e['sha256'].lower() for e in seal['files'] if e['path'].endswith('PILOT_PROTOCOL.md'))
body = target.read_bytes().rstrip(b'\r\n')
for ending in (b'\n', b'\n\n', b'\r\n', b'\r\n\r\n'):
    candidate = body+ending
    if hashlib.sha256(candidate).hexdigest() == expected:
        target.write_bytes(candidate)
        (OUT/'PROTOCOL_RESTORATION.json').write_text(json.dumps(dict(status='RESTORED_EXACT_REVIEWED_BYTES', sha256=expected,
            scope='Accounting additions retained separately in PILOT_PROTOCOL_ACCOUNTED.md and pilot_accounted.py; original reviewed code also restored exactly')), encoding='utf-8')
        print('RESTORED_EXACT_REVIEWED_BYTES')
        break
else:
    raise RuntimeError('Cannot reconstruct sealed bytes; do not rewrite seal')
