"""Extract section text from cached primary XML, not experimental matrices."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/feedback_shift_mechanism/root'

if __name__ == '__main__':
    label = sys.argv[1]
    root = ET.fromstring((OUT / (label + '.body')).read_bytes())
    sections = []
    for sec in root.findall('.//body//sec'):
        title = sec.find('title')
        title = ''.join(title.itertext()) if title is not None else ''
        paragraphs = [''.join(p.itertext()) for p in sec.findall('p')]
        if paragraphs:
            sections.append(dict(title=title, paragraphs=paragraphs))
    target = OUT / (label + '.sections.json')
    assert not target.exists()
    target.write_text(json.dumps(sections, indent=2), encoding='utf-8')
    for sec in sections:
        if any(s in sec['title'].lower() for s in ('method', 'adapt', 'meta', 'data', 'availability', 'limit', 'train', 'task')):
            print(sec['title'])
            print('\n'.join(sec['paragraphs']))
    for item in root.findall('.//ext-link'):
        link = item.get('{http://www.w3.org/1999/xlink}href')
        if link and any(s in link.lower() for s in ('github', 'zenodo', 'figshare')):
            print(link)
