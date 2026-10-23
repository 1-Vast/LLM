"""Try the canonical PMC article attachment route after retained instance-route 403."""
from datetime import datetime, timezone
import hashlib
import io
import json
import zipfile
import requests
from attachment import OUT

if __name__ == '__main__':
    target = OUT/'mmc2_canonical.docx'
    assert not target.exists()
    url = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12205652/bin/mmc2.docx'
    start = datetime.now(timezone.utc).isoformat()
    r = requests.get(url, timeout=45)
    target.write_bytes(r.content)
    receipt = {'url': url, 'final_url': r.url, 'status': r.status_code, 'bytes': len(r.content),
               'sha256': hashlib.sha256(r.content).hexdigest(), 'utc_start': start,
               'utc_end': datetime.now(timezone.utc).isoformat(),
               'is_zip': zipfile.is_zipfile(io.BytesIO(r.content))}
    (OUT/'CANONICAL_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
