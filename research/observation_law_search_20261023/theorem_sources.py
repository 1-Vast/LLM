"""Retrieve cited identification originals, without rerunning earlier requests."""
from concurrent.futures import ThreadPoolExecutor
import json
from fulltexts import fetch, OUT

if __name__ == '__main__':
    sources = [
        ('drift_identification', 'https://arxiv.org/html/2410.22729v3'),
        ('gradient_identification', 'https://arxiv.org/html/2505.21770v1'),
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fetch, sources))
    (OUT.parent / 'THEOREM_SOURCES.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
