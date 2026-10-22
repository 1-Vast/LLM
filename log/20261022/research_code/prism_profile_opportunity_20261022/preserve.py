"""Validate all completed evidence, saving only new-phase receipts."""
import argparse
import json

from prepare import LOG, PREVIOUS, ROOT, sha, write


def verify():
    baseline = json.loads((PREVIOUS / 'BASELINE_PRESERVATION.json').read_text(encoding='utf-8'))
    manifests = dict(baseline['manifest_sha256'])
    name = (PREVIOUS / 'FINAL_FILE_INVENTORY.json').relative_to(ROOT).as_posix()
    manifests[name] = sha(ROOT / name)
    checks = []
    for name, expected in manifests.items():
        assert sha(ROOT / name) == expected
        inventory = json.loads((ROOT / name).read_text(encoding='utf-8'))
        for record in inventory['files']:
            path = ROOT / record['path']
            checks.append({'path': record['path'], 'passed': path.is_file()
                           and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    return {'passed': all(row['passed'] for row in checks), 'checks': checks, 'manifest_sha256': manifests}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label', choices=('BASELINE', 'FINAL'))
    label = parser.parse_args().label
    result = verify()
    write(LOG / (label + '_PRESERVATION.json'), result)
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks'])}))
    if not result['passed']:
        raise SystemExit(1)
