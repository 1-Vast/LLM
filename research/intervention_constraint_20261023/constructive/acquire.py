"""Bounded primary-source search; no biological outcomes or fits."""
import hashlib
import json
from pathlib import Path
import requests

OUT = Path('log/20261023/intervention_constraint/constructive')
queries = {
    'global_epistasis': 'global epistasis genetic interactions saturation nonlinear phenotype',
    'perturb_factor': 'perturbation interaction tensor factorization multi readout',
    'modular_2025': 'single cell perturbation shared gene programs nonlinear interactions 2025',
}
receipts = []
for name, query in queries.items():
    url = 'https://api.openalex.org/works'
    try:
        r = requests.get(url, params={'search': query, 'per-page': 8, 'filter': 'from_publication_date:2025-01-01,to_publication_date:2026-10-23'}, timeout=45)
        body = r.content
        (OUT / f'{name}.body').write_bytes(body)
        receipts.append({'name': name, 'url': r.url, 'status': r.status_code, 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)})
        if r.status_code == 200:
            items = [{'title': x['title'], 'doi': x['doi'], 'date': x['publication_date'], 'abstract': x.get('abstract_inverted_index'), 'primary': x.get('primary_location')} for x in r.json()['results']]
            (OUT / f'{name}.projection.json').write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
            print(name, [(x['title'],x['doi']) for x in items])
    except Exception as exc:
        receipts.append({'name':name, 'error':repr(exc)})
(OUT / 'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
