"""Bounded source recovery for the program-evidence brief; no model execution."""
import concurrent.futures
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sources'
QUERIES = [
    ('Q1', 'arxiv', 'id_list=2610.16346'),
    ('Q2', 'epmc', 'TITLE_ABS:LINCS AND (TITLE_ABS:phosphoproteomic OR TITLE_ABS:P100)'),
    ('Q3', 'epmc', 'TITLE_ABS:HPN AND TITLE_ABS:DREAM'),
    ('Q4', 'epmc', 'TITLE_ABS:drug AND TITLE_ABS:"signaling dynamics" AND (TITLE_ABS:viability OR TITLE_ABS:proliferation)'),
]


def get_one(spec):
    tag, channel, query = spec
    if channel == 'arxiv':
        url = 'https://export.arxiv.org/api/query?' + query
        suffix = 'xml'
    else:
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urllib.parse.urlencode(
            {'query': query, 'format': 'json', 'pageSize': 25, 'resultType': 'core'})
        suffix = 'json'
    receipt = {'tag': tag, 'channel': channel, 'query': query, 'url': url,
               'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-Research/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read(8_000_001)
            receipt.update(status=response.status, content_type=response.headers.get('Content-Type'),
                           final_url=response.url)
        if len(body) > 8_000_000:
            raise ValueError('response exceeds bounded body size')
        path = OUT / f'{tag}.{suffix}'
        path.write_bytes(body)
        receipt.update(path=str(path.relative_to(ROOT)), bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        if channel == 'epmc':
            parsed = json.loads(body)
            records = parsed.get('resultList', {}).get('result', [])
            receipt.update(total=parsed.get('hitCount'), returned=len(records))
            receipt['records'] = [{k: r.get(k) for k in
                ('title', 'doi', 'pmcid', 'id', 'pubYear', 'isOpenAccess', 'authorString')}
                for r in records]
        else:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            entries = ET.fromstring(body).findall('a:entry', ns)
            receipt['records'] = [{k: e.findtext('a:' + k, default='', namespaces=ns)
                                   for k in ('id', 'title', 'summary', 'published', 'updated')}
                                  for e in entries]
    except Exception as exc:
        receipt['error'] = str(exc)
    (OUT / f'{tag}_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt


def main():
    OUT.mkdir(exist_ok=True)
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(get_one, QUERIES))
    summary = {'queries_used': len(QUERIES), 'query_cap': 4,
               'elapsed_s': time.perf_counter() - started, 'records': records}
    (OUT / 'source_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    for record in records:
        print(json.dumps({k: record.get(k) for k in ('tag', 'total', 'returned', 'error')}, ensure_ascii=False))
        for row in record.get('records', []):
            print(json.dumps({k: row.get(k) for k in ('title', 'doi', 'pmcid', 'id')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
