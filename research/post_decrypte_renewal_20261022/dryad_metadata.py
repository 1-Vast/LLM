"""Dryad dataset and file identity metadata only; no file downloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/skeptic/source'
url = 'https://datadryad.org/api/v2/datasets/' + urllib.parse.quote('doi:10.5061/dryad.4xgxd25f0', safe='')
for index in range(2):
    started = datetime.now(timezone.utc).isoformat()
    with urllib.request.urlopen(url, timeout=45) as r:
        body = r.read()
        receipt = {'url': url, 'status': r.status, 'headers': dict(r.headers),
                   'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
                   'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    (OUT / f'dryad_metadata_{index}.body').write_bytes(body)
    (OUT / f'dryad_metadata_{index}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    data = json.loads(body)
    if index == 0:
        print(json.dumps({k: data.get(k) for k in ('title','abstract','usageNotes','methods','_links')}, ensure_ascii=False))
        url = 'https://datadryad.org' + data['_links']['stash:version']['href'] + '/files'
    else:
        print(json.dumps(data, ensure_ascii=False))
