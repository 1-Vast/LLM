"""Bounded release inspection: archive names and README text, no table values."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/functional_transition_law/root_sources'

if __name__ == '__main__':
    target = OUT / 'release_inspection_v2.json'
    assert not target.exists(), 'Do not repeat an initiated inspection'
    manifest = json.loads((OUT / 'zenodo.MANIFEST.json').read_text(encoding='utf-8'))
    entry = manifest['files'][0]
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(),
                   purpose='Check whether declared release supports timed intervention feedback and paired live/death observations; inspect members/README only')
    try:
        url = entry['links']['self']
        receipt['url'] = url
        response = requests.get(url, timeout=45)
        payload = response.content
        (OUT / 'release.zip.body').write_bytes(payload)
        receipt.update(status=response.status_code, bytes=len(payload),
                       sha256=hashlib.sha256(payload).hexdigest())
        response.raise_for_status()
        assert len(payload) == entry['size']
        assert 'md5:' + hashlib.md5(payload).hexdigest() == entry['checksum']
        with ZipFile(BytesIO(payload)) as archive:
            receipt['members'] = [dict(name=i.filename, bytes=i.file_size) for i in archive.infolist()]
            readmes = {}
            for i in archive.infolist():
                if Path(i.filename).name.lower().startswith('readme') and i.file_size < 100000:
                    readmes[i.filename] = archive.read(i).decode('utf-8', errors='replace')
            receipt['readmes'] = readmes
        receipt['boundary'] = 'Downloaded archive bytes; numeric payload members not decoded; author code not executed. Names/README alone do not verify schemas, joins, or values.'
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
