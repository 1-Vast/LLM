"""Verify all finalized predecessor inventory entries, without decoding outcomes."""
from pathlib import Path
import importlib.util
import hashlib
import json
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cipa_control_information'

def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def verify():
    spec = importlib.util.spec_from_file_location('previous_preservation', ROOT / 'research/cipa_calibration_probe_20261022/preserve.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    result = previous.verify()
    manifest = ROOT / 'log/20261022/cipa_calibration_probe/FINAL_FILE_INVENTORY.json'
    result['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
    for row in json.loads(manifest.read_text())['files']:
        path = ROOT / row['path']
        result['checks'].append({'path': row['path'], 'passed': path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256']})
    result.update(utc=datetime.now(timezone.utc).isoformat(), passed=all(r['passed'] for r in result['checks']))
    assert len(result['checks']) == 6195
    return result

if __name__ == '__main__':
    result = verify()
    name = sys.argv[1] if len(sys.argv) > 1 else 'BASELINE_PRESERVATION.json'
    assert name in ('BASELINE_PRESERVATION.json', 'FINAL_PREDECESSOR_PRESERVATION.json')
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({'passed': result['passed'], 'files': len(result['checks'])}), flush=True)
    assert result['passed']
