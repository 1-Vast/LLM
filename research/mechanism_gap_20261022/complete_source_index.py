"""Read two exact author-linked inventories without experimental payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mechanism_gap/root/source_completion'
REQUESTS = {
    'imaging_index': 'https://www.ebi.ac.uk/biostudies/files/S-BIAD696/table%20of%20contents.json',
    'code_tree': 'https://api.github.com/repos/arjunrajlaboratory/FateMap_Goyal2023/git/trees/v1.0.0?recursive=1',
}


def main():
    files = [OUT.parent / 'SOURCE_INDEX_PROTOCOL.md', OUT / 'RECEIPTS.json',
             OUT / 'imaging_manifest.body', OUT / 'code_manifest.body', Path(__file__)]
    with (OUT / 'INDEX_FREEZE.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'before_requests': True, 'utc': datetime.now(timezone.utc).isoformat(),
            'requests': REQUESTS, 'files': [{'path': p.relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}, handle, indent=2)
    receipts = []
    for name, url in REQUESTS.items():
        row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
        try:
            with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
                body = response.read(8_000_001)
                row.update(status=response.status, final_url=response.url, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest(),
                           content_type=response.headers.get('Content-Type'))
            with (OUT / (name + '.body')).open('xb') as handle:
                handle.write(body)
            assert len(body) <= 8_000_000, 'fixed manifest size limit'
            data = json.loads(body)
            if name == 'code_tree':
                row.update(tree_sha=data.get('sha'), truncated=data.get('truncated'),
                           entries=len(data.get('tree', [])))
                assert data.get('truncated') is False
                projection = [{k: item[k] for k in ('path', 'type', 'sha', 'size') if k in item}
                              for item in data['tree']]
                with (OUT / 'code_tree_names.json').open('x', encoding='utf-8', newline='\n') as handle:
                    json.dump(projection, handle, indent=2)
            else:
                row['json_type'] = type(data).__name__
        except Exception as exc:
            row.update(error_type=type(exc).__name__, error=str(exc))
        receipts.append(row)
    with (OUT / 'INDEX_RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
