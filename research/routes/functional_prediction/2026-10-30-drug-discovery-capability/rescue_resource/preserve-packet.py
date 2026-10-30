from pathlib import Path
import xml.etree.ElementTree as E
p=Path(__file__).parent;r=E.fromstring((p/'request03-ras-primary.body').read_bytes())
ids={'Par17','Par18','Par19','Par20','Par21','Par22','Par23','Par24','Par25','Par26','Par27','Par28','Par29','Par30','Par49','Par56','Par67','Par68','Par69','Par70','Par92'}
a=['# Exact selected Nature Medicine primary passages','Source: request03-ras-primary.body; DOI10.1038/s41591-026-04537-w; PMC13472880.1. Article-level effects EXPOSED. This packet contains article passages, not source-data outcomes. No new retrieval.']
for el in r.iter('p'):
 if el.attrib.get('id') in ids:a+=['\n## '+el.attrib['id'],' '.join(''.join(el.itertext()).split())]
a+=['\n## Public source media declarations (not fetched; sizes not advertised in acquired XML)']
for el in r.iter('media'):
 a+=['- '+el.attrib.get('{http://www.w3.org/1999/xlink}href','')+': '+' '.join(''.join(el.itertext()).split())]
(p/'ras-selected-primary-passages.md').write_text('\n'.join(a),encoding='utf-8')
