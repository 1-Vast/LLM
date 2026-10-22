"""Retain bounded primary literature requests; no assay datasets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import requests
import xml.etree.ElementTree as ET

OUT = Path('D:/MAESTRO/log/20261022/operator_renewal/frontier')
for name, url in zip(sys.argv[1::2], sys.argv[2::2]):
    target = OUT / (name + '.body')
    if target.exists():
        raise FileExistsError(target)
    receipt = dict(name=name, url=url, utc=datetime.now(timezone.utc).isoformat())
    try:
        r = requests.get(url, timeout=40)
        target.write_bytes(r.content)
        receipt.update(status=r.status_code, final_url=r.url,
                       bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
        if 'api/query' in url and r.status_code == 200:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            entries = [{k: e.findtext('a:' + k, namespaces=ns) for k in
                        ['id', 'title', 'summary', 'published', 'updated']}
                       for e in ET.fromstring(r.content).findall('a:entry', ns)]
            (OUT / (name + '.entries.json')).write_text(json.dumps(entries, indent=2), encoding='utf-8')
            print(json.dumps(entries))
    except Exception as exc:
        receipt['error'] = repr(exc)
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
