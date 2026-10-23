"""Fetch public primary text; save all outcomes, never overwrite receipts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/feedback_shift_mechanism/root'

if __name__ == '__main__':
    label, url = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / label
    assert not target.with_suffix('.receipt.json').exists()
    receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat())
    try:
        response = requests.get(url, timeout=(15, 40))
        target.with_suffix('.body').write_bytes(response.content)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest())
    except requests.RequestException as exc:
        receipt.update(error=type(exc).__name__, message=str(exc))
    target.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
