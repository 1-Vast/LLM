"""Alternative literature metadata service after preserved Europe PMC503s."""
import json
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/post_decrypte_renewal/root/crossref'
QUERIES = ('time resolved proteomics drug response viability',
           'drug combination temporal signaling cell fate prediction',
           'self improving learned optimizer scientific experiment world model')


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    for index, query in enumerate(QUERIES):
        url = 'https://api.crossref.org/works?' + urlencode({'query': query, 'rows': 8,
              'filter': 'from-pub-date:2025-01-01,until-pub-date:2026-10-22'})
        record = {'query': query, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
        body = b''
        try:
            try:
                response = urlopen(Request(url, headers={'User-Agent': 'MAESTRO-research/1.0'}), timeout=35)
            except HTTPError as error:
                response = error
            with response:
                record['status'] = response.code
                body = response.read(4_000_001)
            assert record['status'] == 200 and len(body) <= 4_000_000
            projected = [{k:r.get(k) for k in ('title','DOI','abstract','published','link','URL')}
                         for r in json.loads(body)['message']['items']]
            (OUT / f'{index}.projected.json').write_text(json.dumps(projected, indent=2), encoding='utf-8')
        except Exception as error:
            record['error'] = str(error)
        (OUT / f'{index}.body').write_bytes(body)
        record.update({'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        (OUT / f'{index}.receipt.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
