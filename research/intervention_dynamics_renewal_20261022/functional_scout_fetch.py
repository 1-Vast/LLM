"""Six-request primary metadata/fulltext scout; no outcome-table access."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/intervention_dynamics_renewal/functional_scout'
LIMIT = 3_000_000


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    tag, url = sys.argv[1:]
    existing = list(OUT.glob('REQUEST_*.json'))
    if len(existing) >= 6:
        raise ValueError('six_request_budget_exhausted')
    index = len(existing)+1
    receipt = OUT/f'REQUEST_{index:02d}_{tag}.json'
    body = OUT/f'RESPONSE_{index:02d}_{tag}.bin'
    record = {'url': url, 'utc_start': utc(), 'method': 'GET', 'max_body_bytes': LIMIT,
              'redirects_followed': False, 'automatic_retries': 0, 'bytes': 0}
    payload = bytearray()
    try:
        with requests.get(url, timeout=(20, 45), stream=True, allow_redirects=False,
                          headers={'User-Agent': 'MAESTRO-research-metadata-audit/1.0'}) as response:
            record['status'] = response.status_code
            record['content_type'] = response.headers.get('Content-Type')
            length = response.headers.get('Content-Length')
            record['declared_content_length'] = length
            if length is not None and int(length) > LIMIT:
                record['disposition'] = 'STOP_DECLARED_BODY_EXCEEDS_CAP'
            else:
                while len(payload) < LIMIT:
                    chunk = response.raw.read(min(65536, LIMIT-len(payload)), decode_content=True)
                    if not chunk:
                        break
                    payload.extend(chunk)
                record['disposition'] = 'CAP_REACHED_NO_FURTHER_READ' if len(payload) == LIMIT else 'BODY_RECEIVED'
    except Exception as error:
        record['error_type'] = type(error).__name__
        record['disposition'] = 'FAILED_NO_RETRY'
    record.update({'utc_end': utc(), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    if payload:
        with body.open('xb') as handle:
            handle.write(payload)
        record['body_file'] = str(body)
    with receipt.open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
