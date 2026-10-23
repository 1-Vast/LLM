"""Retain readable original XML sections and reference URLs."""
import json
import xml.etree.ElementTree as ET
from retrieve import OUT

root = ET.parse(OUT / 'temporal_attention.xml').getroot()
text = '\n\n'.join(' '.join(e.itertext()) for e in root.findall('.//article-title')
                   + root.findall('.//abstract') + root.findall('.//body') + root.findall('.//back'))
(OUT / 'temporal_attention.txt').write_text(text, encoding='utf-8')
sections = [{'title': ' '.join(e.find('title').itertext()) if e.find('title') is not None else '',
             'text': ' '.join(e.itertext())} for e in root.findall('.//sec')]
(OUT / 'temporal_sections.json').write_text(json.dumps(sections, indent=2), encoding='utf-8')
links = sorted({e.attrib.get('{http://www.w3.org/1999/xlink}href')
                for e in root.iter() if e.attrib.get('{http://www.w3.org/1999/xlink}href')})
print(json.dumps({'title': [' '.join(e.itertext()) for e in root.findall('./front/article-meta/title-group/article-title')],
                  'ids': [e.attrib | {'text': e.text} for e in root.findall('./front/article-meta/article-id')],
                  'abstract': [' '.join(e.itertext()) for e in root.findall('.//abstract')],
                  'sections': [s['title'] for s in sections], 'links': links}, indent=2))
