"""Retain bounded primary-index discovery, never treat abstracts as full papers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/root_sources'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    queries = {
        'paired_function': '(transcriptomic OR transcriptional OR "cell state") AND ("drug response" OR "drug discovery") AND (viability OR secretion OR functional) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
        'adaptive_experimental': '("virtual cell" OR "cellular world model" OR "perturbation model") AND ("active learning" OR "experimental design" OR adaptation) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]'}
    for name, query in queries.items():
        body_path = OUT / (name + '.body')
        assert not body_path.exists()
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                 params={'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 30, 'sort': 'FIRST_PDATE_D desc'},
                                 timeout=45)
        body = response.content
        body_path.write_bytes(body)
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'query': query, 'url': response.url,
                   'status': response.status_code, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                   'evidence': 'Primary index metadata/abstract discovery only, not full text or data qualification.'}
        (OUT / (name + '.http.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        response.raise_for_status()
        payload = response.json()
        rows = [{key: row.get(key) for key in ('id', 'source', 'pmcid', 'doi', 'title', 'firstPublicationDate', 'authorString', 'abstractText')}
                for row in payload['resultList']['result']]
        (OUT / (name + '.json')).write_text(json.dumps({'hit_count': payload.get('hitCount'), 'results': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'query': name, 'hit_count': payload.get('hitCount'), 'results': [
              {key: row.get(key) for key in ('id', 'pmcid', 'doi', 'title', 'firstPublicationDate')} for row in rows]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
