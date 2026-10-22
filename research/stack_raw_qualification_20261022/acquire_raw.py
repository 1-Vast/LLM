"""Acquire exact manifest files and verify size/SHA256; do not parse workbooks."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
sys.path.insert(0, str(ROOT / 'research/functional_dynamics_gate_20261022'))
import root_data_scout as fetch

fetch.OUT = LOG / 'raw'


def download(item):
    details = item['content_details']
    receipt, body = fetch.get(item['id'], details['download_url'], cap=100_000_000)
    check = {'id': item['id'], 'filename': item['filename'],
             'status': receipt.get('status'), 'expected_size': details['size'],
             'size_match': len(body) == details['size'],
             'sha256_match': hashlib.sha256(body).hexdigest() == details['sha256_hash'],
             'body_path': receipt['body_path']}
    check['qualified_download'] = (receipt.get('status') == 200 and
                                    'error_type' not in receipt and check['size_match'] and
                                    check['sha256_match'])
    return check


def main():
    manifest = json.loads((LOG / 'network/v1_root_files.body').read_text(encoding='utf-8'))
    assert len(manifest) == 4
    assert all(item['status'] == 'COMPLETED' and item['content_details']['size'] < 100_000_000
               for item in manifest)
    assert sum(item['content_details']['size'] for item in manifest) <= 250_000_000
    assert all(item['content_details']['download_url'].startswith(
        'https://data.mendeley.com/public-files/datasets/3pnv5wh5jm/files/' + item['id'] + '/')
        for item in manifest)
    with ThreadPoolExecutor(max_workers=4) as executor:
        checks = list(executor.map(download, manifest))
    report = {'dataset': '3pnv5wh5jm', 'version': 1, 'files': checks,
              'all_qualified': all(item['qualified_download'] for item in checks),
              'response_cells_inspected': False}
    fetch.write(LOG / 'RAW_ACQUISITION.json', report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['all_qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
