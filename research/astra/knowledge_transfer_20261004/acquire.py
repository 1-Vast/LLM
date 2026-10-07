"""Bounded public downloads. This command does not parse outcome columns."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets'
SOURCES = {
    'jaaks.csv': ('https://ndownloader.figshare.com/files/34006655',
                  '1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278'),
    'jaaks_metadata.json': ('https://api.figshare.com/v2/articles/16843597', None),
    'omnipath.tsv': ('https://omnipathdb.org/interactions?datasets=omnipath&genesymbols=1&fields=sources,references&license=commercial', None),
    'collectri.tsv': ('https://omnipathdb.org/interactions?datasets=collectri&genesymbols=1&fields=sources,references&license=commercial', None),
    'omnipath_resources.json': ('https://omnipathdb.org/resources?format=json', None),
    'hgnc.tsv': ('https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt', None),
}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def fetch(item):
    name, (url, expected) = item
    path = ASSETS / name
    started = time.time()
    try:
        if not path.exists():
            temporary = path.with_suffix(path.suffix + '.part')
            req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'})
            with urllib.request.urlopen(req, timeout=45) as r, temporary.open('wb') as f:
                while True:
                    b = r.read(1024 * 1024)
                    if not b: break
                    f.write(b)
            temporary.rename(path)
        actual = digest(path)
        if expected and actual != expected:
            raise ValueError(f'original data hash mismatch: {actual}')
        row = dict(file=name, url=url, bytes=path.stat().st_size, sha256=actual,
                   retrieved_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   elapsed_seconds=round(time.time()-started, 2), status='downloaded')
    except Exception as e:
        row = dict(file=name, url=url, status='failed', error=str(e))
    print(json.dumps({k: v for k, v in row.items() if k != 'url'}), flush=True)
    return row

if __name__ == '__main__':
    ASSETS.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        rows = list(ex.map(fetch, SOURCES.items()))
    (HERE / 'download_manifest.json').write_text(json.dumps(rows, indent=2)+'\n')
