"""Retain selected primary methods and availability without parsing assay values."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/sustained_function_task/root'
tree = ET.fromstring((OUT / 'bcl11b_primary.body').read_bytes())
sections = []
for section in tree.findall('.//sec'):
    title = section.find('title')
    if title is None:
        continue
    heading = ' '.join(''.join(title.itertext()).split())
    if any(term in heading.lower() for term in (
        'availab', 'organoid', 'drug', 'prolifer', 'rna', 'sequenc', 'rechallenge',
    )):
        sections.append(dict(title=heading, text=' '.join(''.join(section.itertext()).split())))
links = [dict(e.attrib) for e in tree.iter() if e.tag.endswith('ext-link')]
result = dict(sections=sections, links=links)
target = OUT / 'bcl11b_methods.json'
assert not target.exists()
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
