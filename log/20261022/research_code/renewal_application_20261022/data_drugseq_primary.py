"""Project primary narrative/design/accession evidence, not numerical assay tables."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/data'
path = OUT / 'drugseq_primary.body'
root = ET.fromstring(path.read_bytes())
paragraphs = []
for index, element in enumerate(root.findall('.//body//p') + root.findall('.//back//p')):
    text = ' '.join(''.join(element.itertext()).split())
    if text:
        paragraphs.append({'index': index, 'id': element.attrib.get('id'), 'text': text})
pattern = re.compile(r'viab|growth|U2OS|GSE\d|accession|replicat|384|cytotoxic|cell.?titer|24.?h|72.?h|dos|github|data avail|data set|deposited', re.I)
selected = [p for p in paragraphs if pattern.search(p['text'])]
links = []
for element in root.iter():
    for key, value in element.attrib.items():
        if key.endswith('href'):
            links.append({'tag': element.tag, 'href': value, 'label': ' '.join(''.join(element.itertext()).split())[:300]})
result = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'paper_title': ''.join(root.find('.//article-title').itertext()),
    'paragraphs': paragraphs, 'design_function_accession_excerpts': selected,
    'accessions': sorted(set(re.findall(r'GSE\d+|GSM\d+|PRJ[A-Z]+\d+', ' '.join(p['text'] for p in paragraphs)))),
    'links': links, 'data_arrays_downloaded_or_converted': False}
(OUT / 'DRUGSEQ_PRIMARY_PROJECTION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'drugseq_primary.txt').write_text('\n\n'.join(f"[{p['index']}] {p['text']}" for p in paragraphs), encoding='utf-8')
print(json.dumps({'accessions': result['accessions'], 'paragraphs': len(paragraphs), 'excerpts': selected,
                  'asset_links': [v for v in links if any(t in v['href'].lower() for t in ('geo', 'github', 'suppl', '.xlsx', '.csv', '.zip'))]}, ensure_ascii=False))
