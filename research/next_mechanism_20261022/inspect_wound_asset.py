"""Inspect author-released filenames for matched reporter/density availability."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root/literature'
BASE = 'https://api.github.com/repos/mechanoChem/inference-wound-healing'


def acquire(name, url, receipts):
    row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
            body = response.read(3_000_001)
            row.update(status=response.status, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        with (OUT / (name + '.body')).open('xb') as handle:
            handle.write(body)
        assert len(body) <= 3_000_000
        receipts.append(row)
        return json.loads(body)
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
        receipts.append(row)
        return None


def main():
    with (OUT / 'WOUND_INDEX_PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'before_requests': True,
            'question': 'Paper methods specify cells engineered for Akt/ERK reporters but use only nuclei. Does released file inventory authenticate matched reporter observations beyond density?',
            'scope': 'repository metadata and recursive tree names only; no matrix, archive, images or counts',
            'stop': 'No biological numerical protocol without actual relevant observation/sample contract; one drug alone cannot provide independent later drug families',
            'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, handle, indent=2)
    receipts = []
    repo = acquire('wound_repo', BASE, receipts)
    if repo:
        tree = acquire('wound_tree', BASE + '/git/trees/' + repo['default_branch'] + '?recursive=1', receipts)
        if tree:
            rows = [{key: r.get(key) for key in ('path', 'type', 'size', 'sha')} for r in tree['tree']]
            with (OUT / 'wound_names.json').open('x', encoding='utf-8', newline='\n') as handle:
                json.dump({'sha': tree['sha'], 'truncated': tree['truncated'], 'files': rows}, handle, indent=2)
    with (OUT / 'WOUND_INDEX_RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
