"""Bounded public SQLite prefix request; retain bytes, inspect schema strings only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import requests

ROOT = Path(__file__).resolve().parents[2]
LOG_OUT = ROOT / 'log/20261023/distribution_health_qualification/source'
DATA_OUT = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'

if __name__ == '__main__':
    LOG_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = LOG_OUT / 'sqlite_prefix.json'
    body_path = DATA_OUT / 'sqlite_prefix.body'
    schema_path = DATA_OUT / 'SQLITE_SCHEMA_STRINGS.txt'
    if receipt_path.exists() or body_path.exists() or schema_path.exists():
        raise FileExistsError(receipt_path if receipt_path.exists() else body_path)
    url = 'https://ndownloader.figshare.com/files/18506036'
    limit = 1024 * 1024
    started = time.monotonic()
    record = {'url': url, 'utc': datetime.now(timezone.utc).isoformat(),
              'request_range': f'bytes=0-{limit-1}',
              'scope': 'Public ES2 plate SQ00014613 prefix, not full database; may contain state bytes, no health values requested'}
    try:
        with requests.get(url, headers={'Range': f'bytes=0-{limit-1}'},
                          stream=True, timeout=45) as response:
            final = urlsplit(response.url)
            record.update(status=response.status_code, final_url=f'{final.scheme}://{final.netloc}{final.path}',
                          final_url_query_omitted=bool(final.query),
                          content_range=response.headers.get('Content-Range'),
                          content_length=response.headers.get('Content-Length'))
            body = response.raw.read(limit + 1)
            record['exceeded_bound'] = len(body) > limit
            body = body[:limit]
        body_path.write_bytes(body)
        record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                      sqlite_header=body[:16] == b'SQLite format 3\x00')
        strings = re.findall(rb'[\x20-\x7e\r\n\t]{80,}', body)
        schema = [s.decode('ascii') for s in strings if b'CREATE TABLE' in s or b'CREATE INDEX' in s]
        schema_path.write_text('\n\n'.join(schema), encoding='utf-8')
        record['schema_strings'] = len(schema)
    except requests.RequestException as error:
        record.update(status='FAILED', error_type=type(error).__name__)
    record['wall_seconds'] = time.monotonic() - started
    receipt_path.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
