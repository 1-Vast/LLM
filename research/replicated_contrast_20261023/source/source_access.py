"""Code and HTTP metadata only. Never request a count-table GET body."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

out = Path('log/20261023/replicated_contrast/source')
out.mkdir(parents=True, exist_ok=True)
base = 'https://raw.githubusercontent.com/samsonfong/SCHEMATIC/218cf1bb8c83204da846256951ba5f6b0092890b/'
receipts = []
for name, path in [('fitness', 'src/decipher/scores/fitness.py'), ('utils', 'src/decipher/scores/utils.py')]:
    response = requests.get(base+path, timeout=40)
    (out/(name+'.py.body')).write_bytes(response.content)
    receipts.append(dict(method='GET', name=name, url=response.url, status=response.status_code,
                         bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest(),
                         utc=datetime.now(timezone.utc).isoformat()))
    (out/'HTTP_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    response.raise_for_status()
url = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-024-01971-9/MediaObjects/41588_2024_1971_MOESM3_ESM.txt'
response = requests.head(url, timeout=40, allow_redirects=True)
receipts.append(dict(method='HEAD', name='supplementary_data1_counts_metadata', url=url,
                     final_url=response.url, status=response.status_code, headers=dict(response.headers),
                     body_bytes_retained=0, utc=datetime.now(timezone.utc).isoformat()))
(out/'HTTP_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
