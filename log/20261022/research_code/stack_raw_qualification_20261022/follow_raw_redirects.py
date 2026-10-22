"""One explicitly validated HTTPS redirect hop for each manifest file."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
sys.path.insert(0, str(ROOT / 'research/functional_dynamics_gate_20261022'))
import root_data_scout as fetch

fetch.OUT = LOG / 'raw'


def follow(item):
    original = json.loads((fetch.OUT / (item['id'] + '.NETWORK.json')).read_text(encoding='utf-8'))
    assert original['status'] == 302
    redirect = urlsplit(original['location'])
    assert redirect.scheme == 'https' and redirect.username is None
    assert redirect.hostname == 'prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com'
    receipt, body = fetch.get(item['id'] + '_redirect1', original['location'], cap=100_000_000)
    details = item['content_details']
    check = {'id': item['id'], 'filename': item['filename'], 'redirect_hops': 1,
             'status': receipt.get('status'), 'bytes': len(body),
             'size_match': len(body) == details['size'],
             'sha256_match': hashlib.sha256(body).hexdigest() == details['sha256_hash'],
             'body_path': receipt['body_path']}
    check['qualified_download'] = (receipt.get('status') == 200 and
                                   'error_type' not in receipt and check['size_match'] and
                                   check['sha256_match'])
    return check


def main():
    manifest = json.loads((LOG / 'network/v1_root_files.body').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as executor:
        checks = list(executor.map(follow, manifest))
    report = {'dataset': '3pnv5wh5jm', 'version': 1, 'files': checks,
              'all_qualified': all(item['qualified_download'] for item in checks),
              'response_cells_inspected': False}
    fetch.write(LOG / 'RAW_ACQUISITION_FINAL.json', report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['all_qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
