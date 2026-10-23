"""Retain one bounded public metadata/code GET; never fetch bulk biological payload implicitly."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
LOG_OUT = ROOT / 'log/20261023/distribution_health_qualification/source'
DATA_OUT = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'


if __name__ == '__main__':
    name, url = sys.argv[1:]
    if not name.replace('_', '').isalnum():
        raise ValueError('Simple record name required')
    LOG_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    target = LOG_OUT / (name + '.json')
    body_path = DATA_OUT / (name + '.body')
    if target.exists() or body_path.exists():
        raise FileExistsError(target if target.exists() else body_path)
    record = {'url': url, 'utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'One logical public GET; no hidden retry policy'}
    try:
        response = requests.get(url, timeout=45)
        body = response.content
        body_path.write_bytes(body)
        record.update(status=response.status_code, final_url=response.url,
                      bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except requests.RequestException as error:
        record.update(status='FAILED', error_type=type(error).__name__)
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
