"""Bounded primary-index search for feedback-conditioned learning algorithms."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2]/'log/20261023/mechanism_reentry/root_sources'
ITEMS = [('optimizer', 'learning optimizer update rules generalization'),
         ('intervention', 'intervention feedback system identification world model adaptation'),
         ('decision', 'decision focused meta learning experimental design drug response')]


def get(item):
    name, query = item
    record = dict(query=query, utc=datetime.now(timezone.utc).isoformat())
    try:
        response = requests.get('https://api.crossref.org/works', params=dict(query=query, rows=12,
            filter='from-pub-date:2025-01-01,until-pub-date:2026-10-23'), timeout=35)
        (OUT/f'{name}.body').write_bytes(response.content)
        record.update(url=response.url, status=response.status_code, bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            entries = [{key: row.get(key) for key in ['title', 'DOI', 'URL', 'published', 'abstract', 'link']}
                       for row in response.json()['message']['items']]
            (OUT/f'{name}.entries.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
            record['titles'] = [dict(title=row['title'], DOI=row['DOI']) for row in entries]
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    (OUT/f'{name}.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(get, ITEMS)), indent=2))
