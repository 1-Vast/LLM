"""Bounded primary-source discovery with exact bodies and HTTP receipts."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlencode
import hashlib
import json
import sys
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

OUT = Path('D:/MAESTRO/log/20261022/frontier_mechanism_renewal/sources')
OUT.mkdir(parents=True, exist_ok=True)

def fetch(label, url):
    record = dict(label=label, url=url, utc=datetime.now(timezone.utc).isoformat())
    try:
        response = requests.get(url, timeout=60, headers={'User-Agent': 'MAESTRO primary-source research/1.0'})
        data = response.content
        (OUT / f'{label}.body').write_bytes(data)
        record.update(status=response.status_code, final_url=response.url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), headers=dict(response.headers))
        parser = 'xml' if 'xml' in response.headers.get('content-type', '') else 'html.parser'
        (OUT / f'{label}.txt').write_text(BeautifulSoup(data, parser).get_text(' ', strip=True), encoding='utf-8')
    except Exception as exc:
        record['error'] = repr(exc)
    (OUT / f'{label}.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))

def search():
    queries = [
        ('search_nested', 'submittedDate:[202501010000 TO 202610222359] AND (all:"nested learning" OR all:"learned optimizer" OR all:"meta-gradient")'),
        ('search_revision', 'submittedDate:[202501010000 TO 202610222359] AND (all:"self-revision" OR all:"reflective optimization" OR all:"gradient surgery") AND (cat:cs.CL OR cat:cs.CV)'),
        ('search_counterfactual', 'submittedDate:[202501010000 TO 202610222359] AND (all:"update rule" OR all:"learning to learn") AND (cat:cs.CL OR cat:cs.CV)'),
    ]
    for label, query in queries:
        fetch(label, 'https://export.arxiv.org/api/query?' + urlencode(dict(search_query=query, start=0, max_results=12, sortBy='submittedDate', sortOrder='descending')))
    entries = []
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    for label, _ in queries:
        try:
            for item in ET.fromstring((OUT / f'{label}.body').read_bytes()).findall('a:entry', ns):
                entries.append(dict(source=label, **{key:item.findtext('a:'+key, namespaces=ns) for key in ['id','title','published','updated','summary']}))
        except Exception as exc:
            entries.append(dict(source=label, parse_error=repr(exc)))
    (OUT.parent / 'SEARCH_RESULTS.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        search()
    else:
        fetch(sys.argv[1], sys.argv[2])
