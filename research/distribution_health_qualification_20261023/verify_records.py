"""Verify phase-local retained GET bodies/ranges and final membership records."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/distribution_health_qualification'
LOG_SOURCE = OUT / 'source'
DATA_SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    for path in sorted(LOG_SOURCE.glob('*.json')):
        receipt = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(receipt, dict) or not {'url', 'sha256', 'bytes'} <= receipt.keys():
            continue
        body = DATA_SOURCE / (path.stem + '.body')
        checks.append({'receipt': str(path.relative_to(OUT)),
                       'pass': receipt['status'] in (200, 206)
                       and body.stat().st_size == receipt['bytes'] and sha(body) == receipt['sha256']})
    for folder in ('remote_schema', 'remote_image_metadata'):
        for receipt in json.loads((LOG_SOURCE / folder / 'RANGES.json').read_text(encoding='utf-8')):
            body = DATA_SOURCE / folder / f"block_{receipt['index']}.body"
            checks.append({'receipt': f"{folder}/block_{receipt['index']}",
                           'pass': receipt['status'] == 206 and body.stat().st_size == receipt['bytes']
                           and sha(body) == receipt['sha256']})
    membership = json.loads((OUT / 'ELIGIBILITY_RECORD.json').read_text(encoding='utf-8'))
    membership_ok = all(sha(OUT / name) == expected for name, expected in membership['sha256'].items())
    result = {'scope': 'Local retained byte/record consistency only, not whole-database MD5 or biological validation',
              'public_get_receipts': checks, 'membership_hashes_pass': membership_ok,
              'pass': len(checks) == 20 and all(c['pass'] for c in checks) and membership_ok}
    (OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'receipt_count': len(checks), 'membership_hashes_pass': membership_ok,
                      'pass': result['pass']}, indent=2))
    if not result['pass']:
        raise SystemExit(1)
