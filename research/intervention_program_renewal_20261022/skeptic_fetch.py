"""Bounded primary-method retrieval; no biological response files."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT = Path('log/20261022/intervention_program_renewal/skeptic')
CAP = 8 * 1024 * 1024


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('url')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    receipts = list(OUT.glob('*_RECEIPT.json'))
    if len(receipts) >= 8:
        raise RuntimeError('Eight-attempt request budget exhausted')
    receipt_path = OUT / f'{args.label}_RECEIPT.json'
    body_path = OUT / f'{args.label}.body'
    if receipt_path.exists() or body_path.exists():
        raise RuntimeError('Do not repeat/overwrite an attempt')
    meta = {'url': args.url, 'method': 'GET', 'started_utc': datetime.now(timezone.utc).isoformat(),
            'timeout_seconds': 25, 'cap_bytes': CAP, 'automatic_retries': 0,
            'follow_redirects': False, 'body_file': str(body_path), 'status': None}
    receipt_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    body = bytearray()
    try:
        with requests.Session() as session:
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
            with session.get(args.url, timeout=25, allow_redirects=False, stream=True,
                             headers={'User-Agent': 'MAESTRO-primary-method-review/1.0'}) as response:
                meta['status'] = response.status_code
                meta['headers'] = dict(response.headers)
                meta['response_url'] = response.url
                meta['truncated'] = False
                for chunk in response.iter_content(65536):
                    remaining = CAP - len(body)
                    body.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        meta['truncated'] = True
                        break
    except Exception as exc:
        meta['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    body_path.write_bytes(body)
    meta.update({'finished_utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(body),
                 'sha256': hashlib.sha256(body).hexdigest()})
    receipt_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(json.dumps({key: meta.get(key) for key in ('url', 'status', 'bytes', 'sha256', 'truncated', 'error')}))


if __name__ == '__main__':
    main()
