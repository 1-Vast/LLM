"""Download exact public supplement; list members before bounded metadata views."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import requests
import sys
import zipfile

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
URL = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-11001-9/MediaObjects/41586_2026_11001_MOESM3_ESM.zip'

def fetch():
    assert not (OUT / 'archive.receipt.json').exists(), 'Single request only'
    receipt = dict(url=URL, started_utc=datetime.now(timezone.utc).isoformat(),
                   cap=256*1024*1024, automatic_redirects=False)
    digest = hashlib.sha256()
    total = 0
    try:
        with requests.get(URL, stream=True, timeout=45, allow_redirects=False) as response:
            receipt.update(status=response.status_code, final_url=response.url, headers=dict(response.headers))
            with (OUT / 'archive.body').open('wb') as target:
                for chunk in response.iter_content(1024*1024):
                    if total + len(chunk) > receipt['cap']:
                        receipt['body_capped'] = True
                        break
                    target.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
    except requests.RequestException as exc:
        receipt['error'] = repr(exc)
    receipt.update(bytes=total, sha256=digest.hexdigest(), ended_utc=datetime.now(timezone.utc).isoformat())
    (OUT / 'archive.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

def listing():
    with zipfile.ZipFile(OUT / 'archive.body') as archive:
        result = [dict(name=member.filename, bytes=member.file_size,
                       compressed_bytes=member.compress_size, crc=member.CRC) for member in archive.infolist()]
    (OUT / 'ARCHIVE_MEMBERS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    fetch() if sys.argv[1] == 'fetch' else listing()
