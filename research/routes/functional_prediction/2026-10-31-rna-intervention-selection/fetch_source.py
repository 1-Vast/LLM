"""Bounded original-source acquisition with separate role receipts; no retries."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.parse

import requests

HERE = pathlib.Path(__file__).resolve().parent
ALLOCATIONS = {'root': (36, 202), 'encode': (22, 19), 'aso': (22, 27),
               'scout': (5, 2), 'challenge': (11, 6)}


def fetch(url, name, role='root', limit=8 * 1024 * 1024):
    attempts, mib = ALLOCATIONS[role]
    area = HERE / role
    raw = area / 'sources'
    raw.mkdir(parents=True, exist_ok=True)
    ledger = area / 'http_receipts.jsonl'
    history = [json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    for hop in range(6):
        used = sum(x.get('completed_decoded_body_bytes', 0) + x.get('known_partial_decoded_body_bytes', 0) for x in history)
        bound = min(limit, mib * 1024 * 1024 - used)
        if len(history) >= attempts or bound <= 0:
            raise RuntimeError('Role acquisition budget exhausted')
        dest = raw / (name if hop == 0 else f'{name}.hop{hop}')
        if dest.exists():
            raise FileExistsError(dest)
        origin = urllib.parse.urlsplit(url).netloc
        previous = [x for x in history if x['origin'] == origin]
        if previous:
            time.sleep(max(0, 1.05 - (time.time() - previous[-1]['finished_unix'])))
        rec = {'attempt': len(history) + 1, 'url': url, 'origin': origin, 'method': 'GET',
               'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'completed_decoded_body_bytes': 0, 'known_partial_decoded_body_bytes': 0,
               'wire_bytes_certified': False}
        count = 0
        location = None
        try:
            with requests.get(url, stream=True, allow_redirects=False, timeout=(15, 45),
                              headers={'User-Agent': 'MAESTRO-RNA-research/1.0',
                                       'Accept-Encoding': 'identity'}) as response:
                rec['status'] = response.status_code
                rec['response_headers'] = dict(response.headers)
                declared = response.headers.get('Content-Length')
                if declared and int(declared) > bound:
                    rec['disposition'] = 'header_size_rejected_body_unread'
                else:
                    digest = hashlib.sha256()
                    with dest.open('wb') as handle:
                        for chunk in response.iter_content(32768):
                            count += len(chunk)
                            if count > bound:
                                rec['disposition'] = 'partial_body_limit_abort'
                                rec['known_partial_decoded_body_bytes'] = count
                                break
                            handle.write(chunk)
                            digest.update(chunk)
                        else:
                            rec['disposition'] = 'complete'
                            rec['completed_decoded_body_bytes'] = count
                            rec['sha256'] = digest.hexdigest()
                    rec['local_path'] = str(dest.relative_to(HERE))
                location = response.headers.get('Location')
        except Exception as exc:
            rec['disposition'] = 'exception'
            rec['error'] = f'{type(exc).__name__}: {exc}'
            rec['known_partial_decoded_body_bytes'] = count
        rec['finished_unix'] = time.time()
        rec['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        with ledger.open('a', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(rec, ensure_ascii=False) + '\n')
        history.append(rec)
        print(json.dumps({key: rec.get(key) for key in ('attempt', 'status', 'disposition', 'completed_decoded_body_bytes', 'known_partial_decoded_body_bytes', 'local_path', 'error')}), flush=True)
        if rec.get('status') in (301, 302, 303, 307, 308) and location and rec['disposition'] == 'complete':
            target = urllib.parse.urljoin(url, location)
            if any(part in urllib.parse.urlsplit(target).path.lower() for part in ('/login', '/signin', '/captcha')):
                return rec
            url = target
            continue
        return rec
    raise RuntimeError('Redirect ceiling reached')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('name')
    parser.add_argument('--role', choices=ALLOCATIONS, default='root')
    parser.add_argument('--limit', type=int, default=8 * 1024 * 1024)
    args = parser.parse_args()
    fetch(args.url, args.name, args.role, args.limit)
