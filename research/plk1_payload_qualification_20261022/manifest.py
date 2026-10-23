"""Bounded remaining author-linked metadata checks; no response arrays."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/plk1_payload_qualification'
OUT.mkdir(parents=True, exist_ok=True)
tree = ET.fromstring((ROOT / 'log/20261022/update_signal_reassessment/root_sources/plk1.body').read_bytes())
supplements = []
for item in tree.iter('supplementary-material'):
    supplements.append({'id': item.get('id'), 'description': ' '.join(' '.join(item.itertext()).split()),
                        'files': [node.get('{http://www.w3.org/1999/xlink}href') for node in item.iter('media')]})
(OUT / 'SUPPLEMENT_DESCRIPTIONS.json').write_text(json.dumps(supplements, indent=2), encoding='utf-8')


def fetch(accession):
    target = OUT / accession
    assert not target.with_suffix('.body').exists()
    response = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi',
                            params={'acc': accession, 'targ': 'self', 'form': 'text', 'view': 'full'}, timeout=45)
    target.with_suffix('.body').write_bytes(response.content)
    target.with_suffix('.receipt.json').write_text(json.dumps({
        'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
        'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
    response.raise_for_status()
    keys = ('!Series_title', '!Series_overall_design', '!Series_type', '!Series_supplementary_file',
            '!Sample_title', '!Sample_source_name', '!Sample_characteristics', '!Sample_molecule',
            '!Sample_library', '!Sample_data_processing', '!Sample_supplementary_file', '!Sample_relation')
    lines = [line for line in response.text.splitlines() if line.startswith(keys)]
    assert lines
    target.with_suffix('.metadata.json').write_text(json.dumps(lines, indent=2), encoding='utf-8')
    return accession, lines


with ThreadPoolExecutor(max_workers=2) as pool:
    for accession, lines in pool.map(fetch, ['GSE203237', 'GSM6165155']):
        print(json.dumps({'accession': accession, 'metadata': lines}, indent=2))
print('Supplement descriptions:', len(supplements))
