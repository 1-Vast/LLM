"""Read author-linked supplement labels/URLs from the cached article only."""
import hashlib
import json
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'log/20261023/function_update_renewal/root_sources/multilineage.body'
OUT = ROOT/'log/20261023/replicated_contrast'
tree = html.fromstring(SOURCE.read_bytes())
links = []
for anchor in tree.xpath('//a[@href]'):
    url = anchor.attrib['href']
    if 'MOESM' not in url:
        continue
    parent = anchor.getparent()
    links.append(dict(url=url, label=' '.join(anchor.itertext()).strip(),
                      immediate_parent_text=' '.join(parent.itertext()).strip()[:800]))
target = OUT/'SOURCE_INDEX.json'
assert not target.exists()
target.write_text(json.dumps(dict(cached_source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                                 links=links, scope='Supplement labels/URLs only'), indent=2), encoding='utf-8')
print(json.dumps(links, indent=2))
