"""Retrieve the exact newly indexed split-control preprint; no data or code."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/feedback_law_discovery/root_sources'


if __name__ == '__main__':
    target = OUT/'split_control.receipt.json'
    assert not target.exists(), 'Do not repeat the exact request'
    url = 'https://www.biorxiv.org/content/10.64898/2026.10.05.756906v1.full'
    record = dict(utc=datetime.now(timezone.utc).isoformat(), url=url,
                  purpose='Read exact original few-shot adaptation/control-error criterion, not asset qualification')
    try:
        response = requests.get(url, timeout=45)
        (OUT/'split_control.body').write_bytes(response.content)
        record.update(status=response.status_code, final_url=response.url,
                      bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest())
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
