"""Retrieve exactly two author-linked public manifests, never response payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mechanism_gap/root/source_completion'
REQUESTS = {
    'imaging_manifest': 'https://www.ebi.ac.uk/biostudies/api/v1/studies/S-BIAD696',
    'code_manifest': 'https://zenodo.org/api/records/8000328',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = OUT.parent / 'SOURCE_COMPLETION_PROTOCOL.md'
    code = Path(__file__)
    with (OUT / 'FREEZE.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'requests': REQUESTS,
            'files': [{'path': p.relative_to(ROOT).as_posix(),
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [protocol, code]],
            'before_source_requests': True, 'raw_response_datasets_permitted': False}, handle, indent=2)
    receipts = []
    for name, url in REQUESTS.items():
        row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
        try:
            with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
                body = response.read(8_000_001)
                row.update(status=response.status, final_url=response.url,
                           content_type=response.headers.get('Content-Type'), bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
            with (OUT / (name + '.body')).open('xb') as handle:
                handle.write(body)
            assert len(body) <= 8_000_000, 'manifest exceeds fixed metadata size limit'
            data = json.loads(body)
            row['json_top_level_keys'] = list(data) if isinstance(data, dict) else 'not a dict'
        except Exception as exc:
            row.update(error_type=type(exc).__name__, error=str(exc))
        receipts.append(row)
    with (OUT / 'RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
