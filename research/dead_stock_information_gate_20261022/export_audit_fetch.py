"""Bounded exact-blob source audit, never downloads a numerical CSV."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/dead_stock_information_gate/data_auditor'
CODE = Path(__file__).resolve().parent / 'published_code'
TREE = ROOT / 'log/20261022/functional_dynamics_gate/skeptic/BESTDR_CODE_TREE.body'
OLD = [TREE,
       ROOT / 'log/20261022/functional_dynamics_gate/skeptic/BESTDR_CODE_PATHS.json',
       ROOT / 'log/20261022/functional_dynamics_gate/skeptic/BESTDR_PRIMARY.body',
       ROOT / 'log/20261022/functional_dynamics_gate/skeptic/BESTDR_DATA_PATHS.json']
CAP = 3_000_000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    target, = sys.argv[1:]
    if not (OUT / 'PROTOCOL.md').exists():
        raise ValueError('protocol_missing')
    tree = json.loads(TREE.read_text(encoding='utf-8'))
    if tree['truncated']:
        raise ValueError('manifest_truncated')
    entry, = [item for item in tree['tree'] if item['path'] == target]
    if entry['type'] != 'blob' or Path(target).suffix.lower() not in ['.r', '.rd', '.md'] or entry['size'] > 25000:
        raise ValueError('outside_small_code_doc_scope')
    previous = list(OUT.glob('REQUEST_*.json'))
    if len(previous) >= 4:
        raise ValueError('four_GET_budget_exhausted')
    before = {str(path): sha(path) for path in OLD}
    record = {'utc_start': utc(), 'method': 'GET', 'url': entry['url'], 'path': target,
              'manifest_sha': tree['sha'], 'expected_blob_sha1': entry['sha'],
              'expected_decoded_bytes': entry['size'], 'redirects_followed': False,
              'automatic_retries': 0, 'timeout_seconds': 25, 'body_cap_bytes': CAP,
              'previous_evidence_hashes_before': before}
    payload = bytearray()
    started = time.monotonic()
    try:
        with requests.get(entry['url'], allow_redirects=False, timeout=25, stream=True,
                          headers={'User-Agent': 'MAESTRO-bounded-source-audit/1.0'}) as response:
            record['status'] = response.status_code
            record['content_type'] = response.headers.get('Content-Type')
            record['declared_content_length'] = response.headers.get('Content-Length')
            if record['declared_content_length'] and int(record['declared_content_length']) > CAP:
                record['disposition'] = 'STOP_DECLARED_CAP'
            else:
                while len(payload) < CAP:
                    if time.monotonic() - started > 25:
                        record['disposition'] = 'STOP_DEADLINE_PARTIAL'
                        break
                    chunk = response.raw.read(min(65536, CAP-len(payload)), decode_content=True)
                    if not chunk:
                        record['disposition'] = 'COMPLETE_BODY'
                        break
                    payload.extend(chunk)
                else:
                    record['disposition'] = 'STOP_BODY_CAP'
    except Exception as error:
        record.update({'error_type': type(error).__name__, 'disposition': 'FAILED_NO_RETRY'})
    stem = f'{len(previous)+1:02d}_{Path(target).name.replace(".", "_")}'
    body = OUT / f'RESPONSE_{stem}.body'
    with body.open('xb') as handle:
        handle.write(payload)
    record.update({'utc_end': utc(), 'elapsed_seconds': time.monotonic()-started,
                   'body_path': str(body), 'body_bytes': len(payload),
                   'body_sha256': hashlib.sha256(payload).hexdigest()})
    if record.get('status') == 200 and record.get('disposition') == 'COMPLETE_BODY':
        blob = json.loads(payload)
        decoded = base64.b64decode(blob['content'], validate=False)
        actual = hashlib.sha1(b'blob '+str(len(decoded)).encode()+b'\0'+decoded).hexdigest()
        record['blob_verified'] = actual == entry['sha'] == blob['sha'] and len(decoded) == entry['size']
        if not record['blob_verified']:
            raise ValueError('git_blob_verification_failed')
        path = CODE / target
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(decoded)
        record.update({'decoded_path': str(path), 'decoded_bytes': len(decoded), 'decoded_sha256': sha(path)})
    record['previous_evidence_unchanged'] = all(sha(Path(path)) == digest for path, digest in before.items())
    with (OUT / f'REQUEST_{stem}.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
