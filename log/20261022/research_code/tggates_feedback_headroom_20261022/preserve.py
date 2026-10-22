"""Preserve completed evidence before source/development functional access."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/tggates_feedback_headroom'
PREVIOUS = ROOT / 'log/20261022/api_evidence_innovation'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify():
    manifests = dict(json.loads((PREVIOUS / 'BASELINE_PRESERVATION.json').read_text(encoding='utf-8'))['manifest_sha256'])
    latest = PREVIOUS / 'FINAL_FILE_INVENTORY.json'
    manifests[latest.relative_to(ROOT).as_posix()] = sha(latest)
    checks = []
    for name, expected in manifests.items():
        assert sha(ROOT / name) == expected
        for record in json.loads((ROOT / name).read_text(encoding='utf-8'))['files']:
            path = ROOT / record['path']
            checks.append({'path': record['path'], 'passed': path.is_file() and path.stat().st_size == record['bytes']
                           and sha(path) == record['sha256']})
    return {'passed': all(item['passed'] for item in checks), 'checks': checks, 'manifest_sha256': manifests}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label', choices=('BASELINE', 'FINAL'))
    result = verify()
    with (LOG / (parser.parse_args().label + '_PRESERVATION.json')).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks'])}))
    assert result['passed']
