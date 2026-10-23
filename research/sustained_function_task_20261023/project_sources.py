"""Project retained search metadata, or original methods/availability paragraphs."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/sustained_function_task/root'

if __name__ == '__main__':
    label = sys.argv[1]
    raw = OUT/(label+'.body')
    if label.startswith('search'):
        body = json.loads(raw.read_text(encoding='utf-8'))
        projected = [dict(id=r.get('id'),pmcid=r.get('pmcid'),doi=r.get('doi'),title=r.get('title'),
                          date=r.get('firstPublicationDate'),abstract=r.get('abstractText'))
                     for r in body['resultList']['result']]
    else:
        tree = ET.fromstring(raw.read_bytes())
        paragraphs = [' '.join(''.join(p.itertext()).split()) for p in tree.findall('.//p')]
        projected = [p for p in paragraphs if any(k in p.lower() for k in ('data availab','github','zenodo','figshare','rechalleng','washout','wash-out','re-challeng','live-cell imag'))]
    (OUT/(label+'.projection.json')).write_text(json.dumps(projected,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(projected,indent=2,ensure_ascii=False))
