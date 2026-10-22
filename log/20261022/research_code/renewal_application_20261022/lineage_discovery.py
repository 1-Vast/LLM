"""One focused discovery of measured lineage-linked drug survival sources."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/root_sources'


if __name__ == '__main__':
    query = '(Watermelon AND persister) OR (Rewind AND "drug resistance") OR (ClonMapper AND cancer)'
    response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                            params={'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 20}, timeout=45)
    path = OUT / 'lineage_discovery.body'
    with path.open('xb') as stream:
        stream.write(response.content)
    (OUT / 'lineage_discovery.http.json').write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
          'query': query, 'url': response.url, 'status': response.status_code, 'bytes': len(response.content),
          'sha256': hashlib.sha256(response.content).hexdigest(), 'evidence': 'Index/abstract discovery only'}, indent=2) + '\n', encoding='utf-8')
    response.raise_for_status()
    rows = [{key: item.get(key) for key in ('id', 'pmcid', 'doi', 'title', 'firstPublicationDate', 'abstractText')}
            for item in response.json()['resultList']['result']]
    (OUT / 'lineage_discovery.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(rows, ensure_ascii=False))
