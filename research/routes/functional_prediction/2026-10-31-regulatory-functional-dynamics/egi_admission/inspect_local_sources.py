"""Project original source/design metadata only; never execute deposited code."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET

BASE = Path('D:/MAESTRO/data/external/conditional_interventions_20261030/egi')
OUT = Path(__file__).parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def flat(node):
    return ' '.join(''.join(node.itertext()).split())

root = ET.parse(BASE / '04_primary_fulltext.xml').getroot()
supplements = []
for node in root.iter('supplementary-material'):
    supplements.append({
        'id': node.get('id'), 'text': flat(node),
        'links': [x.get('{http://www.w3.org/1999/xlink}href') for x in node.iter() if x.get('{http://www.w3.org/1999/xlink}href')],
    })
xrefs = []
for node in root.iter('xref'):
    if node.get('rid', '').startswith('SD'):
        xrefs.append({'rid': node.get('rid'), 'label': flat(node)})

tree = json.loads((BASE / '01_github_tree.json').read_text(encoding='utf-8'))
paths = [x.get('path') for x in tree.get('tree', [])]

with zipfile.ZipFile(BASE / '08_primary_supplementary.zip') as z:
    archive_members = [{'name': x.filename, 'bytes': x.file_size} for x in z.infolist()]

notebooks = {}
for filename, selected in [
    ('06_call_genetic_interactions.ipynb', list(range(19, 30))),
    ('08_differential_analysis.ipynb', [2, 7, 12, 13]),
]:
    obj = json.loads((BASE / filename).read_text(encoding='utf-8'))
    notebooks[filename] = [{'cell': i, 'cell_type': obj['cells'][i]['cell_type'], 'source': ''.join(obj['cells'][i].get('source', []))} for i in selected]
    if filename.startswith('06'):
        growth_source = ''.join(obj['cells'][5].get('source', []))
        notebooks[filename].append({'cell': 5, 'projection': 'growthScores keys only; values excluded', 'keys': re.findall(r"['\"](expt[12]_rep[12]_[a-z0-9]+)['\"]\s*:", growth_source)})

projection = {
    'scope': 'Source, variable, identity, archive-member metadata only. No notebook outputs, GI numerical cells, count values or response summaries.',
    'sources': {filename: {'sha256': sha(BASE / filename), 'bytes': (BASE / filename).stat().st_size} for filename in ['04_primary_fulltext.xml', '01_github_tree.json', '08_primary_supplementary.zip', '06_call_genetic_interactions.ipynb', '08_differential_analysis.ipynb']},
    'supplements': supplements, 'supplement_xrefs': xrefs, 'github_paths': paths, 'archive_members': archive_members,
    'notebook_source_cells': notebooks,
}
(OUT / 'local_source_projection.json').write_text(json.dumps(projection, indent=2), encoding='utf-8')
print(json.dumps({'supplements': supplements, 'supplement_xrefs': xrefs, 'github_paths': paths, 'archive_members': archive_members}, indent=2))

try:
    from pypdf import PdfReader
    reader = PdfReader(BASE / 'NIHMS2148368-supplement-MMC1.pdf')
    captions = []
    for page_i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        for line in text.splitlines():
            if re.match(r'^\s*(?:Table|Supplementary Table|Data)\s*S?\s*\d+\b', line, re.I):
                captions.append({'page_1based': page_i + 1, 'line': line})
    pdf_projection = {'source': str(BASE / 'NIHMS2148368-supplement-MMC1.pdf'), 'sha256': sha(BASE / 'NIHMS2148368-supplement-MMC1.pdf'), 'pages': len(reader.pages), 'table_caption_start_lines': captions}
    (OUT / 'pdf_table_heading_projection.json').write_text(json.dumps(pdf_projection, indent=2), encoding='utf-8')
    print(json.dumps(pdf_projection, indent=2))
except ImportError as exc:
    print(json.dumps({'pdf_projection_error': str(exc)}))
