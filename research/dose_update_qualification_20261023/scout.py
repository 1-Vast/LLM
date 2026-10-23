"""Retain bounded primary-index searches; no response labels or model calls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification/sources'
QUERIES = {
    'dose_adaptation': 'drug dose response target engagement adaptive resistance cell feedback',
    'sequential_perturbation': 'sequential drug perturbation single cell recovery washout resistance',
    'active_cell_model': 'mechanistic cell model active learning drug response experiment design',
}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'SEARCHES.json').exists()
    receipts = []
    for name, query in QUERIES.items():
        url = 'https://api.crossref.org/works'
        row = dict(name=name, query=query, start=datetime.now(timezone.utc).isoformat())
        try:
            response = requests.get(url, params={'query': query, 'rows': 8,
                'filter': 'from-pub-date:2025-01-01,until-pub-date:2026-10-23',
                'select': 'DOI,title,published,URL,abstract,link'}, timeout=45)
            body = response.content
            (OUT / (name + '.json')).write_bytes(body)
            row.update(url=response.url, status=response.status_code, bytes=len(body),
                sha256=hashlib.sha256(body).hexdigest())
            response.raise_for_status()
            items = response.json()['message']['items']
            print(json.dumps(dict(name=name, items=[{k: item.get(k) for k in
                ['DOI', 'title', 'published']} for item in items]), ensure_ascii=False))
        except Exception as exc:
            row.update(error_type=type(exc).__name__)
            print(json.dumps(dict(name=name, error_type=type(exc).__name__)))
        row['end'] = datetime.now(timezone.utc).isoformat()
        receipts.append(row)
        (OUT / 'SEARCHES.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
