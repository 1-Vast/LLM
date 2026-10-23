"""Retrieve publisher article HTML and list actual supplement link targets."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import requests
from attachment import OUT

URLS = [('publisher_article', 'https://www.jhep-reports.eu/article/S2589-5559(25)00103-X/fulltext'),
        ('sciencedirect', 'https://www.sciencedirect.com/science/article/pii/S258955592500103X')]


def fetch(item):
    name, url = item
    start = datetime.now(timezone.utc).isoformat()
    r = requests.get(url, timeout=40)
    (OUT/f'{name}.html').write_bytes(r.content)
    links = sorted(set(re.findall(r'(?:https?[^\s"<>]+)?(?:mmc\d+\.[a-z0-9]+|[^\s"<>]*\.xlsx)',
                                  r.text, flags=re.I)))
    return {'name': name, 'url': url, 'final_url': r.url, 'status': r.status_code,
            'utc_start': start, 'utc_end': datetime.now(timezone.utc).isoformat(),
            'bytes': len(r.content), 'sha256': hashlib.sha256(r.content).hexdigest(),
            'candidate_links': links[:50]}


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fetch, URLS))
    (OUT/'PUBLISHER_RECEIPTS.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
