"""Read exact saved original Methods sections without a further request."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_mechanism_frontier'
root = ET.fromstring((OUT / 'source/GET2_primary.xml').read_bytes())
selected = []
for sec in root.findall('.//sec'):
    title = ' '.join(sec.findtext('title', '').split())
    if any(key in title.lower() for key in ['cell viability', 'clonogenic', 'mathematical', 'dynamic', 'dynamical', 'cell proliferation']):
        selected.append(dict(title=title, paragraphs=[' '.join(''.join(p.itertext()).split()) for p in sec.findall('p')]))
(OUT / 'root_sources/return.METHODS.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(selected, indent=2))
