"""Official repository tree/source acquisition only; never datasets or weights."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_almanac_mechanism/root/assay_code'


def get(url, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / (stem + '.receipt.json')).exists()
    started = datetime.now(timezone.utc).isoformat()
    response = requests.get(url, timeout=60)
    body = response.content
    (OUT / (stem + '.body')).write_bytes(body)
    (OUT / (stem + '.receipt.json')).write_text(json.dumps({
        'url': url, 'status': response.status_code, 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(body),
        'sha256': hashlib.sha256(body).hexdigest()}, indent=2), encoding='utf-8')
    response.raise_for_status()
    return response


def main():
    if sys.argv[1] == 'tree':
        data = get('https://api.github.com/repos/Genentech/assayloop/git/trees/main?recursive=1', 'tree').json()
        listing = [{'path': x['path'], 'sha': x['sha'], 'size': x.get('size')} for x in data['tree']
                   if x['type'] == 'blob' and x['path'].endswith(('.py', '.yaml', '.toml'))]
        (OUT / 'SOURCE_INVENTORY.json').write_text(json.dumps({'commit_tree': data['sha'],
            'truncated': data.get('truncated'), 'files': listing}, indent=2), encoding='utf-8')
        print(json.dumps(listing, indent=2))
    else:
        inventory = json.loads((OUT / 'SOURCE_INVENTORY.json').read_text())
        path = sys.argv[1]
        matches = [x for x in inventory['files'] if x['path'] == path]
        assert len(matches) == 1 and path.endswith('.py')
        item = matches[0]
        assert item['size'] < 200000
        stem = path.replace('/', '_').removesuffix('.py')
        response = get('https://raw.githubusercontent.com/Genentech/assayloop/' + inventory['commit_tree'] + '/' + path, stem)
        blob_hash = hashlib.sha1(b'blob ' + str(len(response.content)).encode() + b'\0' + response.content).hexdigest()
        assert blob_hash == item['sha']
        text = response.text
        lines = text.splitlines()
        hits = set()
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in ('reward', 'reference', 'baseline', 'context_delta', 'remaining_return')):
                hits.update(range(max(0, i - 4), min(len(lines), i + 7)))
        excerpts = '\n'.join(f'{i + 1}: {lines[i]}' for i in sorted(hits))
        (OUT / (stem + '.EXCERPTS.txt')).write_text(excerpts, encoding='utf-8')
        print(excerpts)


if __name__ == '__main__':
    main()
