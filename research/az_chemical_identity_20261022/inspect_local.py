"""Read only previously captured primary narrative and identity metadata."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'log/20261022/intervention_program_renewal/data_auditor'
OUT = ROOT / 'log/20261022/az_chemical_identity'
OUT.mkdir(parents=True, exist_ok=True)

used = []
def read(path):
    data = path.read_bytes()
    used.append({'path': str(path.relative_to(ROOT)), 'bytes': len(data),
                 'sha256': hashlib.sha256(data).hexdigest()})
    return data

article = ET.fromstring(read(OLD / 'az_primary.body'))
paragraphs = []
for node in article.iter():
    if node.tag in ('p', 'title'):
        text = ' '.join(''.join(node.itertext()).split())
        if any(term in text.lower() for term in (
            '37 ', '46 ', 'drug id', 'drug_id', 'compound',
            'supplementary table', 'figshare', 'data availability')):
            paragraphs.append(text)
links = []
for node in article.iter():
    if node.tag in ('supplementary-material', 'media', 'ext-link'):
        attrs = dict(node.attrib)
        if node.tag != 'ext-link' or any(s in str(attrs).lower() for s in ('figshare', 'github', 'supp')):
            links.append({'tag': node.tag, 'attributes': attrs,
                          'text': ' '.join(''.join(node.itertext()).split())})
manifests = {}
for name in ('az_well_manifest.body', 'az_matrix_manifest.body',
             'az_author_repo.body', 'az_supp1_code.body', 'az_figure1_code.body'):
    path = OLD / name
    raw = read(path)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = {'identity_or_link_lines': [line for line in raw.decode('utf-8').splitlines()
                 if any(term in line.lower() for term in ('drug', 'compound', 'http', 'supp'))]}
    if isinstance(value, dict):
        manifests[name] = {k: value[k] for k in ('id', 'title', 'description', 'files') if k in value}
        if name.endswith('_code.body') or name == 'az_author_repo.body':
            manifests[name] = value
    else:
        manifests[name] = value
design_path = ROOT / 'log/20261022/az_paid_reference_gate/DESIGN.json'
design = json.loads(read(design_path))
design_projection = {key: design[key] for key in ('query_pairs', 'target_pairs')}
result = {'paragraphs': paragraphs, 'links': links, 'manifests': manifests,
          'design_pairs': design_projection, 'local_source_receipts': used}
(OUT / 'LOCAL_PRIMARY_PROJECTION.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
