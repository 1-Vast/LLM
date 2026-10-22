"""Bind reviewed inputs before any real predictive fits."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cipa_calibration_probe'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for name, expected in json.loads((OUT / 'ENDPOINT_ARTIFACT_SEAL.json').read_text()).items():
    assert digest(OUT / name) == expected
for record in json.loads((OUT / 'ENDPOINT_INPUT_SEAL.json').read_text()).values():
    assert digest(ROOT / record['path']) == record['sha256']
review = (OUT / 'CODE_PREFIT_REVIEW.md').read_text(encoding='utf-8')
assert 'ALLOW_FREEZE_AND_ORDINARY_PROBE' in review
code = ROOT / 'research/cipa_calibration_probe_20261022'
assert digest(code / 'model_probe.py') == '447f7a16cfe1697b427719a5d794b1a6abed1e47f57c9f04f8f9489f6f12bc93'
files = [p for p in OUT.iterdir() if p.is_file()]
files += [p for p in code.iterdir() if p.is_file()]
seal = {'utc': datetime.now(timezone.utc).isoformat(), 'real_predictive_fits_before_freeze': 0,
        'purpose': 'Ordinary development opportunity probe; not novelty or RSI validation',
        'files': {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}}
with (OUT / 'FREEZE.json').open('x', encoding='utf-8') as handle:
    json.dump(seal, handle, indent=2)
print(json.dumps({'frozen_files': len(files), 'sha256': digest(OUT / 'FREEZE.json')}))
