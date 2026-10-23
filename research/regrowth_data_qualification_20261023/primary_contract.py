"""Retain primary section identities and selected experimental contracts."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'log/20261023/sustained_function_task/root/bcl11b_primary.body'
tree = ET.fromstring(source.read_bytes())
sections = []
for section in tree.findall('.//sec'):
    title = section.find('title')
    if title is None:
        continue
    heading = ' '.join(''.join(title.itertext()).split())
    paragraphs = [' '.join(''.join(p.itertext()).split()) for p in section.findall('p')]
    sections.append(dict(title=heading, paragraphs=paragraphs))
selected = [s for s in sections if any(term in s['title'].lower() for term in (
    'tnf', 'viability', 'drug treatment', 'microscop', 'quantification',
))]
result = dict(source=str(source.relative_to(ROOT)),
              titles=[s['title'] for s in sections], selected=selected)
out = ROOT / 'log/20261023/regrowth_data_qualification/root/PRIMARY_CONTRACT.json'
out.parent.mkdir(parents=True, exist_ok=True)
assert not out.exists()
out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
