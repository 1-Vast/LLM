import hashlib
import json
from pathlib import Path
import requests
import html
import re

out = Path('log/20261023/intervention_constraint/constructive')
sources = {
 'cofluct': 'https://www.biorxiv.org/content/10.1101/2025.06.27.661814v1.full',
 'helix_epistasis': 'https://www.nature.com/articles/s41467-026-70627-5',
 'cellxpert': 'https://arxiv.org/html/2605.00930v1',
 'perturbdiff': 'https://arxiv.org/html/2602.19685v1',
}
receipts = []
for name, url in sources.items():
 try:
  r = requests.get(url, timeout=45)
  (out / f'{name}.body').write_bytes(r.content)
  cleaned = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', r.text, flags=re.S|re.I)
  text = html.unescape(re.sub(r'<[^>]+>', ' ', cleaned))
  text = re.sub(r'\s+', ' ', text)
  title = re.search(r'<title[^>]*>(.*?)</title>', r.text, flags=re.S|re.I)
  (out / f'{name}.text.txt').write_text(text, encoding='utf-8')
  receipts.append(dict(name=name, url=r.url, status=r.status_code, bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(), title=title.group(1) if title else None))
  print(name,r.status_code,len(r.content), title.group(1) if title else None)
 except Exception as e: receipts.append(dict(name=name,error=repr(e)))
(out / 'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
