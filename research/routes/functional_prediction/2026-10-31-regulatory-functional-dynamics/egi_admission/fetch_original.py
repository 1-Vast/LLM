"""Bounded public original acquisition; redirects/errors are separate attempts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urljoin, urlsplit
import requests

OUT = Path(__file__).parent
STORE = OUT / 'originals'
LOG = OUT / 'request_receipts.jsonl'
ATTEMPT_LIMIT = 22
DECODED_LIMIT = 48_000_000

def records():
    return [json.loads(x) for x in LOG.read_text(encoding='utf-8').splitlines()] if LOG.exists() else []

def fetch(url, filename):
    STORE.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({'User-Agent': 'MAESTRO-source-admission/20261031 (public design metadata audit)', 'Accept-Encoding': 'identity'})
    for hop in range(6):
        old = records()
        if len(old) >= ATTEMPT_LIMIT:
            raise RuntimeError('Attempt allocation exhausted')
        used = sum(x.get('saved_decoded_body_bytes', 0) for x in old)
        if used >= DECODED_LIMIT:
            raise RuntimeError('Decoded-body allocation exhausted')
        origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
        same = [x for x in old if x['origin'] == origin]
        if same:
            time.sleep(max(0, 1.1 - (time.time() - same[-1]['ended_epoch'])))
        i = len(old) + 1
        target = STORE / f'{i:02d}_{filename}'
        record = {'attempt': i, 'url': url, 'origin': origin, 'method': 'GET', 'started_utc': datetime.now(timezone.utc).isoformat(), 'started_epoch': time.time(), 'path': str(target), 'redirect_hop': hop, 'saved_decoded_body_bytes': 0, 'completed': False, 'no_automatic_retry': True}
        digest = hashlib.sha256()
        response = None
        try:
            response = session.get(url, stream=True, timeout=(15, 45), allow_redirects=False)
            record.update({'status': response.status_code, 'response_headers': {k: v for k, v in response.headers.items() if k.lower() != 'set-cookie'}})
            with target.open('wb') as handle:
                for chunk in response.iter_content(65536):
                    if not chunk:
                        continue
                    if used + record['saved_decoded_body_bytes'] + len(chunk) > DECODED_LIMIT:
                        record['discarded_decoded_chunk_bytes'] = len(chunk)
                        raise RuntimeError('Decoded-body limit would be exceeded')
                    handle.write(chunk)
                    digest.update(chunk)
                    record['saved_decoded_body_bytes'] += len(chunk)
            record['completed'] = True
            record['sha256'] = digest.hexdigest()
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
            record['partial_traffic_unknown'] = True
            record['sha256_saved_partial'] = digest.hexdigest()
        finally:
            if response is not None:
                response.close()
            record.update({'ended_epoch': time.time(), 'ended_utc': datetime.now(timezone.utc).isoformat()})
            with LOG.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(record) + '\n')
        print(json.dumps({k: record.get(k) for k in ['attempt', 'status', 'path', 'saved_decoded_body_bytes', 'completed', 'sha256', 'error']}))
        if not record['completed']:
            return
        if record['status'] in {301, 302, 303, 307, 308}:
            url = urljoin(url, response.headers['Location'])
            continue
        return
    raise RuntimeError('Redirect limit reached; no further request attempted')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('filename')
    args = parser.parse_args()
    fetch(args.url, args.filename)
