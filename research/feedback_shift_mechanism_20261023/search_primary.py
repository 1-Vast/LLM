"""Bounded Europe PMC primary-source search with retained HTTP responses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/feedback_shift_mechanism/root'
QUERIES = {
    'world_update': '("virtual cell" OR "perturbation prediction") AND ("adaptation" OR "uncertainty" OR "batch") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
    'learned_feedback': '("drug response") AND ("meta-learning" OR "test-time adaptation" OR "batch effects") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for label, query in QUERIES.items():
        target = OUT / label
        assert not target.with_suffix('.receipt.json').exists()
        receipt = dict(query=query, utc=datetime.now(timezone.utc).isoformat())
        try:
            response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                    params=dict(query=query, format='json', pageSize=12, resultType='core'), timeout=(15, 40))
            target.with_suffix('.body').write_bytes(response.content)
            receipt.update(url=response.url, status=response.status_code, bytes=len(response.content),
                           sha256=hashlib.sha256(response.content).hexdigest())
            if response.status_code == 200:
                results = response.json().get('resultList', {}).get('result', [])
                projection = [{k:r.get(k) for k in ('title', 'doi', 'pmcid', 'firstPublicationDate', 'abstractText')} for r in results]
                target.with_suffix('.projection.json').write_text(json.dumps(projection, indent=2), encoding='utf-8')
                print(json.dumps(dict(label=label, hits=response.json().get('hitCount'), results=[{k:r.get(k) for k in ('title','doi','pmcid')} for r in results]), indent=2))
        except requests.RequestException as exc:
            receipt.update(error=type(exc).__name__, message=str(exc))
        target.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
