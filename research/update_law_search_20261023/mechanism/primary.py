import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

out = Path('log/20261023/update_law_search/mechanism')
sources = {
    'perturbode': 'https://arxiv.org/html/2501.02409v2',
    'mra2025': 'https://academic.oup.com/bib/article/26/2/bbaf098/8086866',
    'spectra2026': 'https://www.biorxiv.org/content/10.64898/2026.09.21.752624v1.full',
}
records = []
for name, url in sources.items():
    try:
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40) as r:
            body = r.read()
            status = r.status
            final = r.url
        (out / f'{name}.body').write_bytes(body)
        txt = re.sub('<[^>]+>', ' ', body.decode('utf8', errors='replace'))
        (out / f'{name}.txt').write_text(re.sub(r'\s+', ' ', txt), encoding='utf8')
        records.append(dict(name=name, url=url, final=final, status=status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
    except Exception as e:
        records.append(dict(name=name, url=url, error=repr(e)))
(out / 'PRIMARY_RECEIPTS.json').write_text(json.dumps(records, indent=2), encoding='utf8')
print(json.dumps(records, indent=2))
