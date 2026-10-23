"""Follow the identified original publisher metadata routes, not guessed files."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
crossref = json.loads((OUT / 'crossref.body').read_bytes())['message']
tdm = next(item['URL'] for item in crossref['link'] if item['content-type'] == 'text/xml')
publisher_html = (OUT / 'publisher.body').read_text(encoding='utf-8')
from urllib.parse import unquote
redirect = re.search(r'name="redirectURL" value="([^"]+)"', publisher_html).group(1)
cell_url = unquote(redirect).split('?')[0]


def fetch(name, url):
    assert not (OUT / (name + '.body')).exists()
    response = requests.get(url, timeout=45)
    (OUT / (name + '.body')).write_bytes(response.content)
    receipt = {'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
               'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    if response.status_code == 200:
        links = sorted(set(re.findall(r'(?:href|src)=["\']([^"\']+)', response.text)))
        try:
            tree = ET.fromstring(response.content)
            for node in tree.iter():
                for key, value in node.attrib.items():
                    if key.endswith(('href', 'url', 'locator')):
                        links.append(value)
        except ET.ParseError:
            pass
        useful = [link for link in links if any(term in link.lower() for term in ('supp', 'mmc', 'xlsx', 'attachment', 'ars.els'))]
        (OUT / (name + '.links.json')).write_text(json.dumps(useful, indent=2), encoding='utf-8')
        print(json.dumps(useful, indent=2)[:12000])


with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(lambda pair: fetch(*pair), [('tdm', tdm), ('cell', cell_url)]))
