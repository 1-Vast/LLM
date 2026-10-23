"""Fetch the exact official code archive and inspect ZIP member identities only."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
metadata = json.loads((OUT/'MANIFEST_CHECK.json').read_text(encoding='utf-8'))
record = next(row for row in metadata['sources'] if row['name'] == 'zenodo')['metadata']['files'][0]
url = record['links']['self']
receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat(),
               contract_sha256=hashlib.sha256((OUT/'ARCHIVE_PROTOCOL.md').read_bytes()).hexdigest())
body = bytearray()
manifest = []
try:
    with requests.get(url, stream=True, timeout=40) as response:
        receipt['status'] = response.status_code
        for part in response.iter_content(65536):
            if len(body)+len(part) > 8*1024*1024:
                receipt['stop'] = 'COMPRESSED_CAP'
                break
            body.extend(part)
        else:
            receipt['stop'] = 'COMPLETE'
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                   md5=hashlib.md5(body).hexdigest(), declared_checksum=record['checksum'])
    receipt['checksum_match'] = 'md5:'+receipt['md5'] == record['checksum']
    if receipt['status'] == 200 and receipt['stop'] == 'COMPLETE' and receipt['checksum_match']:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            manifest = [dict(name=entry.filename, bytes=entry.file_size, compressed_bytes=entry.compress_size)
                        for entry in archive.infolist()]
except Exception as error:
    receipt.update(error_type=type(error).__name__, error=str(error))
(OUT/'author_archive.body').write_bytes(body)
(OUT/'author_archive.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
(OUT/'ARCHIVE_MANIFEST.json').write_text(json.dumps(dict(receipt=receipt, members=manifest), indent=2), encoding='utf-8')
print(json.dumps(dict(receipt=receipt, members=len(manifest),
                     non_tree_figure=[row for row in manifest if '/trees/' not in row['name'] and '/figures/' not in row['name']]), indent=2))
