"""HEAD each exact authenticated official compound archive; zero payload GET."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_rna_feedback_pilot'
MANIFEST = LOG/'RNA_IDENTITY_MANIFEST.json'


def main():
    out = LOG/'rna_sources/archive_heads'
    out.mkdir(exist_ok=False)
    manifest = json.loads(MANIFEST.read_bytes())
    def one(args):
        index, row = args
        url = row['official_HTTPS_mirror_URL']
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'method': 'HEAD', 'logical_request': 1,
                   'compound_label': row['compound_label'], 'role': row['role'], 'url': url,
                   'RNA_payload_body_bytes_downloaded': 0}
        start = time.monotonic()
        try:
            response = requests.head(url, timeout=30, allow_redirects=False)
            receipt.update(status=response.status_code, headers=dict(response.headers), final_url=response.url)
        except Exception as exc:
            receipt['error_type'] = type(exc).__name__
        receipt['elapsed_seconds'] = time.monotonic()-start
        with (out/f'request_{index:02}.json').open('x', encoding='utf-8') as stream:
            json.dump(receipt, stream, indent=2)
        return receipt
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(one, enumerate(manifest['compounds'])))
    lengths = []
    for row in receipts:
        value = row.get('headers', {}).get('Content-Length') or row.get('headers', {}).get('content-length')
        if value:
            lengths.append(int(value))
    result = {'logical_HEAD_requests': len(receipts), 'status_counts': {},
              'known_content_length_archives': len(lengths), 'known_sum_archive_bytes': sum(lengths),
              'RNA_payload_body_bytes_downloaded': 0, 'receipts': receipts,
              'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}
    for row in receipts:
        key = str(row.get('status', row.get('error_type')))
        result['status_counts'][key] = result['status_counts'].get(key,0)+1
    with (LOG/'RNA_ARCHIVE_HEADS.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k != 'receipts'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
