"""Retain public source response bytes with a purpose-specific receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/public_recovery_task/root'

if __name__ == '__main__':
    label, url, purpose = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = OUT / (label + '.receipt.json')
    assert not receipt_path.exists()
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), url=url, purpose=purpose)
    try:
        response = requests.get(url, timeout=45)
        body = response.content
        (OUT / (label + '.body')).write_bytes(body)
        receipt.update(status=response.status_code, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
    except requests.RequestException as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
