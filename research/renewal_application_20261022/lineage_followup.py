"""Resolve two exact primary titles, then retain available primary full texts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/root_sources'


def get(name, url, params=None):
    response = requests.get(url, params=params, timeout=45)
    path = OUT / (name + '.body')
    with path.open('xb') as stream:
        stream.write(response.content)
    (OUT / (name + '.http.json')).write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
          'url': response.url, 'status': response.status_code, 'bytes': len(response.content),
          'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2) + '\n', encoding='utf-8')
    return response


if __name__ == '__main__':
    query = 'TITLE:"Cycling cancer persister cells arise" OR TITLE:"Variability within rare cell states"'
    response = get('exact_lineage_titles', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                   {'query': query, 'format': 'json', 'resultType': 'core', 'pageSize': 10})
    response.raise_for_status()
    rows = response.json()['resultList']['result']
    print(json.dumps([{key: r.get(key) for key in ('id', 'pmcid', 'doi', 'title', 'firstPublicationDate')} for r in rows], ensure_ascii=False))
    selected = [r for r in rows if r.get('pmcid') and r.get('source') == 'MED']
    assert len(selected) <= 2
    for record in selected:
        pmcid = record['pmcid']
        full = get(pmcid, 'https://www.ebi.ac.uk/europepmc/webservices/rest/' + pmcid + '/fullTextXML')
        if full.status_code != 200:
            print(json.dumps({'pmcid': pmcid, 'status': full.status_code}))
            continue
        tree = ET.fromstring(full.content)
        paragraphs = [' '.join(''.join(node.itertext()).split()) for node in tree.iter() if node.tag in ('article-title', 'title', 'p')]
        (OUT / (pmcid + '.txt')).write_text('\n\n'.join(paragraphs) + '\n', encoding='utf-8')
        relevant = [p for p in paragraphs if any(word in p.lower() for word in
                   ('data availability', 'gse', 'code availability', 'github', 'watermelon', 'rewind', 'lineage', 'different cell lines'))]
        print(json.dumps({'pmcid': pmcid, 'title': record['title'], 'paragraphs': relevant[:10]}, ensure_ascii=False))
