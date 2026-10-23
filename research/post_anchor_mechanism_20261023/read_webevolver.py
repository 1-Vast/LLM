"""Read official PDF; store source/projection under the user's log constraint."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests
from pypdf import PdfReader

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
url='https://aclanthology.org/2025.emnlp-main.454.pdf'
r=requests.get(url,timeout=40)
target=OUT/'webevolver.pdf'
target.write_bytes(r.content)
rec=dict(url=url,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),utc=datetime.now(timezone.utc).isoformat())
(OUT/'webevolver_pdf.receipt.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
if r.ok and r.content.startswith(b'%PDF'):
    pages=PdfReader(target).pages
    (OUT/'webevolver_pdf.txt').write_text('\n'.join(f'\nPAGE {i+1}\n'+p.extract_text() for i,p in enumerate(pages)),encoding='utf-8')
print(json.dumps(rec))
