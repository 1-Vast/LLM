"""Recover three decision-changing primary texts; keep bytes and section locators."""
import concurrent.futures
import hashlib
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'sources'
ITEMS = [
    ('cellchain', 'https://arxiv.org/html/2610.16346v1', 'html'),
    ('subclones', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11282632/fullTextXML', 'xml'),
    ('erk', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8322260/fullTextXML', 'xml'),
]


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'li', 'tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def recover(item):
    name, url, kind = item
    receipt = {'name': name, 'url': url, 'kind': kind,
               'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-Research/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            body = response.read(8_000_001)
            receipt.update(status=response.status, content_type=response.headers.get('Content-Type'),
                           final_url=response.url)
        if len(body) > 8_000_000:
            raise ValueError('body too large')
        (ROOT / f'{name}.{kind}').write_bytes(body)
        receipt.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        if kind == 'xml':
            tree = ET.fromstring(body)
            title = tree.findtext('.//article-title')
            sections = []
            for sec in tree.findall('.//sec'):
                heading = ''.join(sec.find('title').itertext()) if sec.find('title') is not None else ''
                own = [' '.join(''.join(node.itertext()).split()) for node in sec
                       if node.tag != 'sec']
                sections.append({'id': sec.get('id'), 'title': heading, 'text': '\n'.join(own)})
            receipt['title'] = title
            receipt['links'] = [dict(node.attrib) for node in tree.findall('.//ext-link')]
            receipt['supplements'] = [ET.tostring(n, encoding='unicode')
                                      for n in tree.findall('.//supplementary-material')]
            (ROOT / f'{name}_sections.json').write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding='utf-8')
            text = '\n\n'.join(f'[{s["id"]}] {s["title"]}\n{s["text"]}' for s in sections)
        else:
            parser = TextHTML()
            parser.feed(body.decode('utf-8'))
            text = '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())
        (ROOT / f'{name}_text.txt').write_text(text, encoding='utf-8')
        receipt['extracted_chars'] = len(text)
    except Exception as exc:
        receipt['error'] = str(exc)
    (ROOT / f'{name}_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return {k: receipt.get(k) for k in ('name', 'status', 'title', 'bytes', 'extracted_chars', 'error')}


if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(recover, ITEMS):
            print(json.dumps(result, ensure_ascii=False))
