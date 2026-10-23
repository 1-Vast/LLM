"""Save public primary responses and retrieval receipts without exposing secrets."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/rechallenge_task/root'

if __name__ == '__main__':
    label, url, purpose = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (label + '.receipt.json')
    assert not target.exists()
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), url=url, purpose=purpose)
    try:
        response = requests.get(url, timeout=45)
        payload = response.content
        (OUT / (label + '.body')).write_bytes(payload)
        receipt.update(status=response.status_code, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    except requests.RequestException as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
