"""Acquire fixed public primary/metadata records without executing source content."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

ROOT = Path('log/20261022/next_mechanism/recursive')
URLS = {
    'crossref_discorl': 'https://api.crossref.org/works?query.title=Discovering%20state-of-the-art%20reinforcement%20learning%20algorithms&rows=3',
    'dgm_html': 'https://arxiv.org/html/2505.22954v2',
    'alphaevolve_html': 'https://arxiv.org/html/2506.13131v1',
}

def main():
    receipts = []
    for name, url in URLS.items():
        started = datetime.now(timezone.utc).isoformat()
        try:
            r = requests.get(url, timeout=60)
            body = r.content
            suffix = '.json' if name.startswith('crossref') else '.html'
            path = ROOT / (name + suffix)
            path.write_bytes(body)
            receipts.append(dict(name=name, url=url, final_url=r.url, status=r.status_code,
                started=started, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), path=str(path)))
        except requests.RequestException as exc:
            receipts.append(dict(name=name, url=url, started=started, error=str(exc)))
    (ROOT / 'ACQUISITION.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    print(json.dumps(receipts, indent=2))

if __name__ == '__main__':
    main()
