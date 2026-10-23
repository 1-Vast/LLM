"""Fetch exactly three manifested public code blobs; never execute their content."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/intervention_dynamics_renewal/ap1_code_io'
MANIFEST = ROOT / 'log/20261022/intervention_dynamics_renewal/root_scout/AP1_REPOSITORY_MANIFEST.json'
TARGETS = ['code/incucyte/tram.Rmd', 'code/incucyte/ap1i/jnk_stat.Rmd',
           'code/dexmemFISH/dexmemfish_function.R']
LIMIT = 3_000_000


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    requested = sys.argv[1]
    number = TARGETS.index(requested)+1
    receipt = OUT/f'REQUEST_{number:02d}.json'
    if receipt.exists():
        raise ValueError('attempt_already_recorded_no_retry')
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest['tree_sha'] != 'ed565d810bd1aa0b067c761c13bfb98989240417' or manifest['truncated']:
        raise ValueError('unexpected_or_truncated_manifest')
    target = next(e for e in manifest['entries'] if e['path'] == requested)
    record = {'url': target['url'], 'utc_start': utc(), 'method': 'GET', 'path': requested,
              'expected_git_blob_sha1': target['sha'], 'expected_decoded_size': target['size'],
              'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
              'max_body_bytes': LIMIT, 'redirects_followed': False, 'automatic_retries': 0}
    payload = bytearray()
    try:
        with requests.get(target['url'], timeout=(20, 45), stream=True, allow_redirects=False,
                          headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'MAESTRO-code-io-audit/1.0'}) as response:
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
        if payload:
            body_path = OUT/f'RESPONSE_{number:02d}.json'
            with body_path.open('xb') as handle:
                handle.write(payload)
            record['body_file'] = str(body_path)
        if record['status'] == 200 and record['disposition'] == 'BODY_RECEIVED':
            blob = json.loads(payload)
            if blob['encoding'] != 'base64':
                raise ValueError('unexpected_blob_encoding')
            decoded = base64.b64decode(blob['content'])
            git_sha = hashlib.sha1(b'blob '+str(len(decoded)).encode()+b'\0'+decoded).hexdigest()
            record['decoded_bytes'] = len(decoded)
            record['decoded_sha256'] = hashlib.sha256(decoded).hexdigest()
            record['computed_git_blob_sha1'] = git_sha
            record['git_blob_verified'] = git_sha == target['sha'] == blob['sha'] and len(decoded) == target['size'] == blob['size']
            if not record['git_blob_verified']:
                raise ValueError('git_blob_identity_mismatch')
            code_path = Path(__file__).parent / 'ap1_published_code' / requested
            code_path.parent.mkdir(parents=True, exist_ok=True)
            with code_path.open('xb') as handle:
                handle.write(decoded)
            record['decoded_file'] = str(code_path)
    except Exception as error:
        record['error_type'] = type(error).__name__
        record['disposition'] = 'FAILED_NO_RETRY'
    record.update({'utc_end': utc(), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    with receipt.open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
