"""Retrieve public archive with bounded route recovery; never inspect response cells."""
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/organoid_schedule_qualification/root'
EXPECTED = '2bb8b263de42e71615691d2cebfe445023734f760567312f07a6214e63d6dc86'
URLS = [
    'https://datadryad.org/api/v2/files/4089491/download',
    'https://datadryad.org/downloads/file_stream/4089491',
    'https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.0vt4b8h8x/download',
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(URLS, 1):
        dest = OUT / f'GET{i}'
        if dest.with_suffix('.receipt.json').exists():
            raise FileExistsError('Preserve prior receipts; do not repeat this acquisition.')
        receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat())
        try:
            response = requests.get(url, timeout=(15, 40))
            body = response.content
            digest = hashlib.sha256(body).hexdigest()
            dest.with_suffix('.body').write_bytes(body)
            receipt.update(status=response.status_code, final_url=response.url,
                           bytes=len(body), sha256=digest,
                           content_type=response.headers.get('Content-Type'),
                           expected_sha256=EXPECTED, matches_published=digest == EXPECTED)
        except requests.RequestException as exc:
            receipt.update(error=type(exc).__name__, message=str(exc))
        dest.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt), flush=True)
        if receipt.get('matches_published'):
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                members = [dict(name=x.filename, bytes=x.file_size,
                                compressed_bytes=x.compress_size) for x in archive.infolist()]
            (OUT / 'ARCHIVE_STRUCTURE.json').write_text(json.dumps(members, indent=2), encoding='utf-8')
            print(json.dumps(members), flush=True)
            return


if __name__ == '__main__':
    main()
