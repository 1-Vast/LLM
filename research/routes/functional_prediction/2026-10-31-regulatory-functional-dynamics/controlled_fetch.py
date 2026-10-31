"""Finite, auditable original-source retrieval; never parses profile values."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.parse

import requests

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / 'sources'
RAW.mkdir(exist_ok=True)
LEDGER = HERE / 'http_receipts.jsonl'
MAX_ATTEMPTS = 24
MAX_BYTES = 40_000_000


def records():
    return [json.loads(line) for line in LEDGER.read_text(encoding='utf-8').splitlines()] if LEDGER.exists() else []


def fetch(url, name, limit, expected_size=None, expected_etag=None):
    history = records()
    for hop in range(8):
        if len(history) >= MAX_ATTEMPTS:
            raise RuntimeError('Attempt ceiling reached')
        completed = sum(r.get('completed_decoded_body_bytes', 0) for r in history)
        if completed >= MAX_BYTES:
            raise RuntimeError('Completed body ceiling reached')
        origin = urllib.parse.urlsplit(url).netloc
        previous = [r for r in history if r['origin'] == origin]
        if previous:
            time.sleep(max(0, 1.01 - (time.time() - previous[-1]['finished_unix'])))
        rec = {'attempt': len(history) + 1, 'hop': hop, 'url': url, 'origin': origin,
               'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'method': 'GET', 'known_partial_decoded_body_bytes': 0,
               'completed_decoded_body_bytes': 0, 'wire_bytes_certified': False}
        dest = RAW / (name if hop == 0 else f'{name}.hop{hop}')
        body_count = 0
        try:
            headers = {'User-Agent': 'MAESTRO-source-admission/1.0', 'Accept-Encoding': 'identity'}
            if expected_etag:
                headers['If-Match'] = expected_etag
            with requests.get(url, timeout=(20, 90), stream=True, allow_redirects=False,
                              headers=headers) as response:
                rec['status'] = response.status_code
                rec['response_headers'] = dict(response.headers)
                bound = min(limit, MAX_BYTES - completed)
                declared = response.headers.get('Content-Length')
                if expected_size is not None and response.status_code == 200 and (not declared or int(declared) != expected_size):
                    rec['disposition'] = 'identity_size_mismatch_body_unread'
                elif expected_etag and response.status_code == 200 and response.headers.get('ETag') != expected_etag:
                    rec['disposition'] = 'identity_etag_mismatch_body_unread'
                elif declared and int(declared) > bound:
                    rec['disposition'] = 'header_size_rejected_body_unread'
                else:
                    digest = hashlib.sha256()
                    with dest.open('wb') as handle:
                        for chunk in response.iter_content(1024 * 256):
                            if body_count + len(chunk) > bound:
                                rec['disposition'] = 'partial_body_limit_abort'
                                rec['known_partial_decoded_body_bytes'] = body_count + len(chunk)
                                break
                            body_count += len(chunk)
                            handle.write(chunk)
                            digest.update(chunk)
                        else:
                            rec['disposition'] = 'complete'
                            rec['completed_decoded_body_bytes'] = body_count
                            rec['sha256'] = digest.hexdigest()
                    rec['local_path'] = str(dest)
                    if rec['disposition'] != 'complete':
                        rec['known_partial_decoded_body_bytes'] = max(body_count, rec['known_partial_decoded_body_bytes'])
                location = response.headers.get('Location')
        except Exception as exc:
            rec['disposition'] = 'exception'
            rec['error'] = f'{type(exc).__name__}: {exc}'
            rec['known_partial_decoded_body_bytes'] = body_count
            location = None
        rec['finished_unix'] = time.time()
        rec['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        with LEDGER.open('a', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(rec, ensure_ascii=False) + '\n')
        history.append(rec)
        print(json.dumps({k: rec.get(k) for k in ('attempt', 'status', 'disposition', 'completed_decoded_body_bytes', 'known_partial_decoded_body_bytes', 'local_path', 'error')}))
        if rec.get('status') in (301, 302, 303, 307, 308) and location and rec['disposition'] == 'complete':
            url = urllib.parse.urljoin(url, location)
            continue
        return rec
    raise RuntimeError('Redirect hop bound reached')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('name')
    parser.add_argument('--limit', type=int, default=12_000_000)
    args = parser.parse_args()
    fetch(args.url, args.name, args.limit)
