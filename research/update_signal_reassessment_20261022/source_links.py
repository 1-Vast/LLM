"""Inventory links only from the authenticated primary XML, never fetch values."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_signal_reassessment/root_sources'
target = OUT / 'PLK1_LINK_INVENTORY.json'
assert not target.exists()
tree = ET.fromstring((OUT / 'plk1.body').read_bytes())
links = []
for element in tree.iter():
    href = element.attrib.get('{http://www.w3.org/1999/xlink}href')
    if href and element.tag in ('ext-link', 'supplementary-material', 'media'):
        links.append({'tag': element.tag, 'href': href,
                      'text': ' '.join(' '.join(element.itertext()).split()),
                      'content_type': element.attrib.get('content-type')})
target.write_text(json.dumps(links, indent=2), encoding='utf-8')
print(json.dumps([entry for entry in links if entry['tag'] != 'ext-link' or 'GSE' in entry['text']], indent=2))
