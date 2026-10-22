"""At most six primary/manifest metadata GETs; no response arrays."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/functional_dynamics_gate/functional_auditor'
PROTOCOL = ROOT / 'log/20261022/functional_dynamics_gate/ROOT_PROTOCOL.md'
LIMIT = 3_000_000


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    tag, url = sys.argv[1:]
    if not PROTOCOL.exists() or not (OUT / 'PROTOCOL.md').exists():
        raise ValueError('protocol_not_ready')
    OUT.mkdir(parents=True, exist_ok=True)
    prior = list(OUT.glob('REQUEST_*.json'))
    if len(prior) >= 6:
        raise ValueError('six_GET_budget_exhausted')
    stem = f'{len(prior) + 1:02d}_{tag}'
    record = {'url': url, 'method': 'GET', 'utc_start': utc(), 'max_body_bytes': LIMIT,
              'redirects_followed': False, 'automatic_retries': 0, 'timeout_seconds': 25,
              'purpose': 'primary literature or exact public manifest only; no response arrays',
              'root_protocol_sha256': hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()}
    payload = bytearray()
    started = time.monotonic()
    try:
        with requests.get(url, timeout=25, allow_redirects=False, stream=True,
                          headers={'User-Agent': 'MAESTRO-bounded-functional-metadata-audit/1.0'}) as response:
            record['status'] = response.status_code
            record['content_type'] = response.headers.get('Content-Type')
            record['declared_content_length'] = response.headers.get('Content-Length')
            record['location'] = response.headers.get('Location')
            if record['declared_content_length'] and int(record['declared_content_length']) > LIMIT:
                record['disposition'] = 'STOP_DECLARED_BODY_ABOVE_CAP'
            else:
                while len(payload) < LIMIT:
                    if time.monotonic() - started > 25:
                        record['disposition'] = 'STOP_TOTAL_DEADLINE_PARTIAL_BODY'
                        break
                    chunk = response.raw.read(min(65536, LIMIT - len(payload)), decode_content=True)
                    if not chunk:
                        record['disposition'] = 'COMPLETE_BODY'
                        break
                    payload.extend(chunk)
                else:
                    record['disposition'] = 'STOP_CAP_REACHED_NO_FURTHER_READ'
    except Exception as error:
        record['error_type'] = type(error).__name__
        record['disposition'] = 'FAILED_NO_RETRY'
    record.update({'utc_end': utc(), 'elapsed_seconds': time.monotonic() - started,
                   'body_bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    body = OUT / f'RESPONSE_{stem}.body'
    with body.open('xb') as handle:
        handle.write(payload)
    record['body_path'] = str(body)
    with (OUT / f'REQUEST_{stem}.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
