"""Bounded recovery of public P100 sources; no credentials or model execution."""
import concurrent.futures, hashlib, json, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'sources'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(v for k, v in attrs if k == 'href')


def fetch(name, url, suffix):
    rec = {'name': name, 'url': url, 'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-Research/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read(10_000_001)
            rec.update(status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'))
        if len(body) > 10_000_000:
            raise ValueError('source exceeds 10MB bound')
        (OUT / f'{name}.{suffix}').write_bytes(body)
        rec.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if suffix == 'html':
            parser = Links()
            parser.feed(body.decode('utf-8', errors='replace'))
            rec['links'] = sorted(set(parser.links))
    except Exception as exc:
        rec['error'] = str(exc)
    (OUT / f'{name}_receipt.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    return rec


def main():
    OUT.mkdir(exist_ok=True)
    query = urllib.parse.urlencode({'query': 'DOI:10.1038/s41597-021-01008-4', 'format': 'json', 'resultType': 'core'})
    jobs = [('p100_2021_metadata', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+query, 'json'),
            ('panorama_dashboard', 'https://panoramaweb.org/project/LINCS/P100/begin.view', 'html')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for rec in pool.map(lambda args: fetch(*args), jobs):
            print(json.dumps(rec, ensure_ascii=False)[:3000])
    path = OUT / 'p100_2021_metadata.json'
    if not path.exists():
        return
    for rec in json.loads(path.read_text(encoding='utf-8')).get('resultList', {}).get('result', []):
        print(json.dumps({k: rec.get(k) for k in ('title', 'doi', 'pmcid', 'firstPublicationDate')}, ensure_ascii=False))
        if not rec.get('pmcid'):
            continue
        print(json.dumps(fetch('p100_2021', 'https://www.ebi.ac.uk/europepmc/webservices/rest/'+rec['pmcid']+'/fullTextXML', 'xml')))
        xmlpath = OUT / 'p100_2021.xml'
        if not xmlpath.exists():
            continue
        tree = ET.fromstring(xmlpath.read_bytes())
        sections = [{'id': s.get('id'), 'title': ''.join(s.find('title').itertext()) if s.find('title') is not None else '',
                     'text': '\n'.join(' '.join(''.join(n.itertext()).split()) for n in s if n.tag != 'sec')}
                    for s in tree.findall('.//sec')]
        links = [{'type': n.tag, 'attrs': n.attrib, 'text': ' '.join(''.join(n.itertext()).split())}
                 for n in tree.iter() if n.tag in ('ext-link', 'supplementary-material', 'media')]
        for label, value in [('sections', sections), ('links', links)]:
            (OUT / f'p100_2021_{label}.json').write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps([{'id': s['id'], 'title': s['title'], 'chars': len(s['text'])} for s in sections], ensure_ascii=False))


if __name__ == '__main__':
    main()
