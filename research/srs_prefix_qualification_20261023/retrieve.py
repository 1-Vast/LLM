"""Bounded public-source acquisition; bodies and failures stay in log/."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/srs_prefix_qualification/root'


def get(label, url):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/label
    assert not path.exists()
    record = dict(utc=datetime.now(timezone.utc).isoformat(), url=url)
    try:
        response = requests.get(url, timeout=40, headers={'User-Agent':'MAESTRO-Research/1.0'})
        path.write_bytes(response.content)
        record.update(status=response.status_code, final_url=response.url, bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest(),
                      content_type=response.headers.get('Content-Type'))
    except requests.RequestException as error:
        record['error'] = str(error)
    (OUT/(label+'.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    get(sys.argv[1], sys.argv[2])
