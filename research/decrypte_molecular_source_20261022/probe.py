"""Archive author-linked public metadata responses; never print assay values."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/decrypte_feedback_pilot/molecular'

def main():
    key, url = sys.argv[1:3]
    record = {'url': url, 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'public source metadata/web application; no molecular abundance decoding'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'MAESTRO-source-audit/1.0'}), timeout=45) as response:
            body = response.read(12 * 1024 * 1024 + 1)
            record.update(status=response.status, final_url=response.url, headers=dict(response.headers),
                          truncated=len(body) > 12*1024*1024, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        (OUT / (key + '.body')).write_bytes(body)
    except Exception as exc:
        record.update(error=type(exc).__name__, message=str(exc))
    (OUT / (key + '.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))

if __name__ == '__main__':
    main()
