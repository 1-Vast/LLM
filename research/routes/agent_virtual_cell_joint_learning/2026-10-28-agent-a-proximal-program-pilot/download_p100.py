"""Acquire a small official-linked P100 subset, preserving original GCT bytes."""
import concurrent.futures, hashlib, json, re, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / 'data/external/p100_program_pilot_20261028/raw'


def download(url):
    name = url.rsplit('/', 1)[-1]
    rec = {'source_url': url, 'filename': name,
           'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'MAESTRO-Research/1.0'}), timeout=40) as response:
            body = response.read(100_000_001)
            rec.update(status=response.status, content_type=response.headers.get('Content-Type'))
        if len(body) > 100_000_000 or not body.lstrip().startswith(b'#1.'):
            raise ValueError('not a bounded GCT body')
        path = RAW / name
        digest = hashlib.sha256(body).hexdigest()
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('existing source differs; preserve it and stop this file')
        if not path.exists():
            path.write_bytes(body)
        rec.update(path=str(path.relative_to(ROOT)), bytes=len(body), sha256=digest,
                   header_lines=body.decode('utf-8-sig').splitlines()[:3])
    except Exception as exc:
        rec['error'] = str(exc)
    return rec


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    links = json.loads((HERE / 'sources/p100_dataset_links.json').read_text(encoding='utf-8'))
    patterns = [r'PRM_Plate28_annotated.*(?<!LVL3)(?<!LVL4)(?<!processed)\.gct$',
                r'DIA_Plate29_annotated.*(?<!LVL3)(?<!LVL4)(?<!processed)\.gct$',
                r'PRM_Plate32_annotated.*(?<!LVL3)(?<!LVL4)(?<!processed)\.gct$']
    selected = []
    for pattern in patterns:
        found = [u for u in links if re.search(pattern, u) and not re.search(r'(_LVL[34]|\.processed)\.gct$', u)]
        if len(found) != 1:
            raise ValueError(f'ambiguous/missing official link for {pattern}: {found}')
        selected.extend(found)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(download, selected))
    (HERE / 'p100_download_receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding='utf-8')
    for rec in receipts:
        print(json.dumps(rec, ensure_ascii=False)[:1800])


if __name__ == '__main__':
    main()
