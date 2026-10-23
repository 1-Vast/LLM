"""Project primary article sections and public links; no assay files are parsed."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/rechallenge_task/root'

if __name__ == '__main__':
    for label in sys.argv[1:]:
        root = ET.fromstring((OUT / (label + '.body')).read_bytes())
        text = lambda element: ' '.join(''.join(element.itertext()).split())
        sections = [dict(title=text(s.find('title')) if s.find('title') is not None else '',
                         paragraphs=[text(p) for p in s.findall('p')]) for s in root.iter('sec')]
        links = [e.attrib for e in root.iter('ext-link')]
        output = dict(title=[text(e) for e in root.iter('article-title')][:1], sections=sections, links=links)
        (OUT / (label + '.projection.json')).write_text(json.dumps(output, indent=2), encoding='utf-8')
        print(label, output['title'])
        print('SECTION TITLES:', [s['title'] for s in sections])
        for section in sections:
            if any(word in section['title'].lower() for word in ('data avail', 'code avail', 'drug', 'sensitivity', 'sequen', 'viability', 'machine learning')):
                print(section['title'], '\n'.join(section['paragraphs'])[:12000])
        print('PUBLIC LINKS:', links)
