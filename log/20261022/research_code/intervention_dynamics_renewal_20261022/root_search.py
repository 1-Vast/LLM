"""Registered public-source requests; never a hidden-outcome experiment."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/intervention_dynamics_renewal/root_scout'
QUERY = '(antibiotic[Title/Abstract]) AND (memory[Title/Abstract] OR fluctuating[Title/Abstract] OR pulses[Title/Abstract]) AND (single-cell[Title/Abstract] OR microfluidic[Title/Abstract]) AND (2022:2026[dp])'
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def write(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def get(name, url, cap=3_000_000):
    if (OUT/f'{name}.NETWORK.json').exists() or (OUT/f'{name}.raw.xml').exists():
        raise FileExistsError('request_name_already_started_or_retained')
    record = {'url': url, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'retries': 0, 'automatic_redirects': False,
              'body_cap_bytes': cap,
              'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    body = b''
    try:
        opener = urllib.request.build_opener(NoRedirect)
        request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-research-source-audit/1.0'})
        try:
            response = opener.open(request, timeout=25)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read(cap+1)
            record.update({'status': response.status, 'headers': dict(response.headers)})
        if len(body) > cap:
            raise ValueError('response_cap_exceeded')
    except Exception as error:
        record['error_type'] = type(error).__name__
    record.update({'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                   'ended_utc': datetime.now(timezone.utc).isoformat()})
    (OUT/f'{name}.raw.xml').write_bytes(body)
    write(OUT/f'{name}.NETWORK.json', record)
    return record, body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    marker = OUT/'STARTED.json'
    write(marker, {'utc': datetime.now(timezone.utc).isoformat(), 'planned_GETs': 2})
    query = urllib.parse.urlencode({'db': 'pubmed', 'term': QUERY, 'retmax': 12, 'retmode': 'xml'})
    record, body = get('search', BASE+'esearch.fcgi?'+query)
    if record.get('status') != 200 or 'error_type' in record:
        print(json.dumps({'status': 'SEARCH_ACCESS_FAILED', 'receipt': record}))
        return 1
    try:
        tree = ET.fromstring(body)
        ids = [e.text for e in tree.findall('./IdList/Id')]
        write(OUT/'SEARCH.json', {'count': tree.findtext('Count'), 'ids': ids, 'query': QUERY})
        if not ids:
            print('NO_HITS_IN_REGISTERED_QUERY')
            return 0
        query = urllib.parse.urlencode({'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'xml'})
        record, body = get('abstracts', BASE+'efetch.fcgi?'+query)
        if record.get('status') != 200 or 'error_type' in record:
            print(json.dumps({'status': 'ABSTRACT_ACCESS_FAILED', 'receipt': record}))
            return 1
        tree = ET.fromstring(body)
        articles = []
        for node in tree.findall('./PubmedArticle'):
            articles.append({'pmid': node.findtext('./MedlineCitation/PMID'),
                'title': ''.join(node.find('./MedlineCitation/Article/ArticleTitle').itertext()),
                'abstract': [{'label': a.attrib.get('Label'), 'text': ''.join(a.itertext())}
                              for a in node.findall('./MedlineCitation/Article/Abstract/AbstractText')],
                'ids': {a.attrib['IdType']: a.text for a in node.findall('./PubmedData/ArticleIdList/ArticleId')},
                'journal': node.findtext('./MedlineCitation/Article/Journal/Title')})
        write(OUT/'ARTICLES.json', articles)
        print(json.dumps(articles, ensure_ascii=False))
        return 0
    except Exception as error:
        write(OUT/'PARSE_FAILURE.json', {'error_type': type(error).__name__, 'network_retry': False})
        print('PARSE_FAILED_RETAINED')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
