"""Re-read archived original article XML prose only; no supplementary data."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/early_update_mechanism/biology/decryptE_fulltext.xml'
OUT = ROOT / 'log/20261022/decrypte_molecular_increment/review'
body = SOURCE.read_bytes()
tree = ET.fromstring(body)
sections = []
for sec in tree.findall('.//body//sec'):
    title = sec.find('title')
    heading = '' if title is None else ''.join(title.itertext())
    for p in sec.findall('p'):
        text = ''.join(p.itertext())
        if re.search(r'predict|machine learning|regression|random forest|correlat|cluster|activation|curve fitting|sigmoid|fitted', text, re.I):
            sections.append({'heading': heading, 'text': text})
result = {'source': str(SOURCE), 'sha256': hashlib.sha256(body).hexdigest(),
          'scope': 'Original saved paper body prose targeted paragraphs only, not data matrices', 'paragraphs': sections}
(OUT / 'PAPER_SCOPE_QUOTES.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
