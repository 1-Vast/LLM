"""Retrieve primary metadata/method code only; no assay matrices or outcome tables."""
import hashlib
import json
from pathlib import Path
import requests

OUT = Path('log/20261023/intervention_constraint/biology')
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {
    'correction': 'https://www.nature.com/articles/s41588-025-02090-9',
    'repo_metadata': 'https://api.github.com/repos/samsonfong/SCHEMATIC',
    'repo_tree': 'https://api.github.com/repos/samsonfong/SCHEMATIC/git/trees/main?recursive=1',
    'primary_metadata': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41588-024-01971-9&format=json',
}
receipts = []
for name, url in SOURCES.items():
    try:
        r = requests.get(url, timeout=60)
        body = r.content
        (OUT / (name + '.body')).write_bytes(body)
        receipts.append(dict(name=name, url=url, final_url=r.url, status=r.status_code,
                             bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
    except requests.RequestException as e:
        receipts.append(dict(name=name, url=url, error=str(e)))
(OUT / 'RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
