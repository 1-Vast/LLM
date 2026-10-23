"""Small primary-source searches with retained raw responses and exact queries."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/root'
QUERIES = {
    'longitudinal_function': '(TITLE_ABS:phosphoproteomic OR TITLE_ABS:proteomic OR TITLE_ABS:transcriptomic) AND (TITLE_ABS:"time-resolved" OR TITLE_ABS:longitudinal) AND TITLE_ABS:drug AND (TITLE_ABS:viability OR TITLE_ABS:sensitivity) AND FIRST_PDATE:[2024-01-01 TO 2026-10-22]',
    'combination_dynamics': '(TITLE_ABS:"drug combination" OR TITLE_ABS:"sequential treatment") AND (TITLE_ABS:dynamics OR TITLE_ABS:"time course") AND (TITLE_ABS:signaling OR TITLE_ABS:proteomic OR TITLE_ABS:transcriptomic) AND FIRST_PDATE:[2024-01-01 TO 2026-10-22]',
    'compositional_world': '(TITLE_ABS:"neural operator" OR TITLE_ABS:"world model" OR TITLE_ABS:"system identification") AND (TITLE_ABS:cell OR TITLE_ABS:biological) AND (TITLE_ABS:perturbation OR TITLE_ABS:intervention) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]'
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, query in QUERIES.items():
        target = OUT / name
        target.mkdir(exist_ok=False)
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode(
            {'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 25, 'sort': 'FIRST_PDATE_D'})
        record = {'query': query, 'url': url, 'started': datetime.now(timezone.utc).isoformat()}
        body = b''
        try:
            try:
                response = urlopen(Request(url, headers={'User-Agent': 'MAESTRO-research/1.0'}), timeout=35)
            except HTTPError as error:
                response = error
            with response:
                record['status'] = response.code
                body = response.read(4_000_001)
                record['final_url'] = response.url
            assert record['status'] == 200 and len(body) <= 4_000_000
            data = json.loads(body)
            projected = [{k: row.get(k) for k in ('title','doi','pmcid','firstPublicationDate','abstractText')}
                         for row in data.get('resultList', {}).get('result', [])]
            (target / 'PROJECTED.json').write_text(json.dumps(projected, indent=2), encoding='utf-8')
            record['hit_count'] = data.get('hitCount')
        except Exception as error:
            record['error'] = str(error)
        (target / 'SOURCE.body').write_bytes(body)
        record.update({'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                       'finished': datetime.now(timezone.utc).isoformat()})
        (target / 'RECEIPT.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        print(json.dumps({'query': name, 'status': record.get('status'), 'hits': record.get('hit_count'), 'error': record.get('error')}), flush=True)


if __name__ == '__main__':
    main()
