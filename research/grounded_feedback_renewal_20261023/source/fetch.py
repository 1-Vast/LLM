"""Bounded primary metadata/source retrieval; no large numeric dataset access."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import sys
import requests

out = Path('log/20261023/grounded_feedback_renewal/source')
out.mkdir(parents=True,exist_ok=True)
name,url = sys.argv[1:3]
response = requests.get(url,timeout=50)
(out/(name+'.body')).write_bytes(response.content)
receipt = dict(url=url,final_url=response.url,status=response.status_code,bytes=len(response.content),
               sha256=hashlib.sha256(response.content).hexdigest(),utc=datetime.now(timezone.utc).isoformat())
(out/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
