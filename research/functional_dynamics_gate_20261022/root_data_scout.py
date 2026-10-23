"""Two bounded public primary-metadata requests; no numerical dataset read."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/functional_dynamics_gate/root_scout'
QUERY = '(drug[tiab]) AND ("time-resolved"[tiab] OR longitudinal[tiab] OR kinetic*[tiab]) AND (organoid*[tiab] OR "live-cell"[tiab]) AND (screen*[tiab] OR dataset[tiab]) AND (2024:2026[dp]) NOT review[pt]'
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def write(path, data):
    with path.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def get(name, url, cap=3_000_000):
    OUT.mkdir(parents=True, exist_ok=True)
    body_path, receipt_path = OUT/f'{name}.body', OUT/f'{name}.NETWORK.json'
    if body_path.exists() or receipt_path.exists():
        raise FileExistsError('request_already_started')
    r = {'url': url, 'started_utc': datetime.now(timezone.utc).isoformat(),
         'retries': 0, 'automatic_redirects': False, 'cap': cap, 'timeout': 25}
    raw = b''
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-functional-research/1.0'})
        try:
            response = urllib.request.build_opener(NoRedirect).open(req, timeout=25)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            r.update({'status': response.status, 'content_type': response.headers.get('Content-Type'),
                      'location': response.headers.get('Location')})
            raw = response.read(cap+1)
        if len(raw) > cap:
            raise ValueError('response_cap_exceeded')
    except Exception as exc:
        r['error_type'] = type(exc).__name__
    r.update({'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
              'ended_utc': datetime.now(timezone.utc).isoformat(), 'body_path': str(body_path)})
    with body_path.open('xb') as f:
        f.write(raw)
    write(receipt_path, r)
    return r, raw


def main():
    url = BASE+'esearch.fcgi?'+urllib.parse.urlencode({'db': 'pubmed', 'term': QUERY,
        'retmax': 10, 'retmode': 'xml'})
    r, raw = get('search', url)
    if r.get('status') != 200 or 'error_type' in r:
        print('ROOT_SEARCH_FAILURE_RETAINED')
        return 1
    doc = ET.fromstring(raw)
    ids = [e.text for e in doc.findall('./IdList/Id')]
    write(OUT/'SEARCH.json', {'query': QUERY, 'count': doc.findtext('Count'), 'ids': ids})
    if not ids:
        print('NO_HITS_IN_QUERY')
        return 0
    r, raw = get('abstracts', BASE+'efetch.fcgi?'+urllib.parse.urlencode({
        'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'xml'}))
    if r.get('status') != 200 or 'error_type' in r:
        print('ROOT_ABSTRACT_FAILURE_RETAINED')
        return 1
    entries = []
    for article in ET.fromstring(raw).findall('PubmedArticle'):
        a = article.find('MedlineCitation/Article')
        entries.append({'pmid': article.findtext('MedlineCitation/PMID'),
            'title': ''.join(a.find('ArticleTitle').itertext()),
            'abstract': [''.join(p.itertext()) for p in a.findall('Abstract/AbstractText')],
            'ids': {i.get('IdType'): i.text for i in article.findall('PubmedData/ArticleIdList/ArticleId')}})
    write(OUT/'ARTICLES.json', entries)
    print(json.dumps(entries, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
