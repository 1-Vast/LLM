"""Retain one bounded public metadata/code GET; never fetch bulk biological payload implicitly."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/distribution_health_qualification/source'


if __name__ == '__main__':
    name, url = sys.argv[1:]
    if not name.replace('_', '').isalnum():
        raise ValueError('Simple record name required')
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (name + '.json')
    if target.exists():
        raise FileExistsError(target)
    record = {'url': url, 'utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'One logical public GET; no hidden retry policy'}
    try:
        response = requests.get(url, timeout=45)
        body = response.content
        (OUT / (name + '.body')).write_bytes(body)
        record.update(status=response.status_code, final_url=response.url,
                      bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except requests.RequestException as error:
        record.update(status='FAILED', error_type=type(error).__name__)
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
