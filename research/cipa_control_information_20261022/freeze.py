"""Freeze the source-only protocol and reviewed implementation before fitting."""
from pathlib import Path
import hashlib
import json
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
OUT = ROOT / 'log/20261022/cipa_control_information'
OLD = ROOT / 'log/20261022/cipa_calibration_probe'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sys.executable.lower().replace('\\', '/') == 'd:/anaconda/envs/maestro/python.exe'
assert sha(CODE / 'probe.py') == '407eb492269f8bad40cce85134128c23e40041a7bf2f55572c5fef12336d298f'
assert json.loads((OUT / 'PREPARE_AUDIT.json').read_text())['status'] == 'PASS'
assert json.loads((OUT / 'BASELINE_PRESERVATION.json').read_text())['passed']
assert 'Ran 7 tests' in (OUT / 'MAESTRO_BOUNDARY_TEST_TRANSCRIPT.txt').read_text()
assert 'OK' in (OUT / 'MAESTRO_BOUNDARY_TEST_TRANSCRIPT.txt').read_text()
for name, expected in json.loads((OLD / 'ENDPOINT_ARTIFACT_SEAL.json').read_text()).items():
    assert sha(OLD / name) == expected
for record in json.loads((OLD / 'ENDPOINT_INPUT_SEAL.json').read_text()).values():
    assert sha(ROOT / record['path']) == record['sha256']
for copy_name in ('SOURCE_ONLY_BUNDLES.json', 'SOURCE_ONLY_ROWS.json'):
    record = json.loads((OUT / copy_name).read_text())
    assert sha(ROOT / record['source_path']) == record['source_sha256']
files = [p for p in OUT.iterdir() if p.is_file()] + [p for p in CODE.iterdir() if p.is_file()]
files += [ROOT / 'research/cipa_calibration_probe_20261022/model_probe.py']
files += [OLD / name for name in ('ENDPOINT_INPUT_SEAL.json', 'ENDPOINT_ARTIFACT_SEAL.json', 'SOURCE_DEV_BUNDLES.json', 'SOURCE_DEV_ROWS.json')]
with (OUT / 'FREEZE.json').open('x', encoding='utf-8') as handle:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'predictive_fits_before_freeze': 0,
        'interpreter': sys.executable, 'full_goal': 'ACTIVE / NOT_ACHIEVED',
        'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}}, handle, indent=2)
print(json.dumps({'files': len(files), 'freeze_sha256': sha(OUT / 'FREEZE.json')}))
