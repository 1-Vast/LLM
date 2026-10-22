"""Check completed inventories without changing any completed evidence."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/renewal_application'
PREVIOUS = ROOT / 'log/20261022/prism_profile_opportunity'


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def verify():
    previous = json.loads((PREVIOUS / 'BASELINE_PRESERVATION.json').read_text(encoding='utf-8'))
    manifests = dict(previous['manifest_sha256'])
    last = PREVIOUS / 'FINAL_FILE_INVENTORY.json'
    manifests[last.relative_to(ROOT).as_posix()] = sha(last)
    checks = []
    for name, expected in manifests.items():
        assert sha(ROOT / name) == expected
        for row in json.loads((ROOT / name).read_text(encoding='utf-8'))['files']:
            path = ROOT / row['path']
            checks.append({'path': row['path'], 'passed': path.is_file()
                           and path.stat().st_size == row['bytes'] and sha(path) == row['sha256']})
    return {'passed': all(x['passed'] for x in checks), 'checks': checks, 'manifest_sha256': manifests}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label', choices=('BASELINE', 'FINAL'))
    result = verify()
    with (LOG / (parser.parse_args().label + '_PRESERVATION.json')).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks'])}))
    assert result['passed']
