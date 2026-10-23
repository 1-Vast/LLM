"""Retrieve official EPMC supplementary archive; inventory only, no PDF table decoding."""
from datetime import datetime, timezone
import hashlib
import io
import json
import zipfile
import requests
from attachment import OUT

if __name__ == '__main__':
    target = OUT/'epmc_supplements.zip'
    assert not target.exists()
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12205652/supplementaryFiles'
    start = datetime.now(timezone.utc).isoformat()
    r = requests.get(url, timeout=45)
    target.write_bytes(r.content)
    receipt = {'url': url, 'final_url': r.url, 'status': r.status_code, 'bytes': len(r.content),
               'sha256': hashlib.sha256(r.content).hexdigest(), 'utc_start': start,
               'utc_end': datetime.now(timezone.utc).isoformat(),
               'is_zip': zipfile.is_zipfile(io.BytesIO(r.content)),
               'outcome_bytes_acquired': 'All supplementary archive members if successful; no numerical decoding'}
    (OUT/'EPMC_SUPP_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if receipt['is_zip']:
        with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
            inventory = [{'path': info.filename, 'bytes': info.file_size} for info in archive.infolist()]
        (OUT/'EPMC_SUPP_INVENTORY.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
        receipt['inventory'] = inventory
    print(json.dumps(receipt, indent=2))
