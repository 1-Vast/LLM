"""Offline projection of retained STACK primary prose; no workbook access."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'log/20261022/functional_dynamics_gate/functional_auditor/RESPONSE_05_05_primary_efetch.body'
DEST = ROOT / 'log/20261022/stack_raw_qualification/skeptic/PRIMARY_PROJECTION.json'
body = SOURCE.read_bytes()
tree = ET.fromstring(body)
pattern = re.compile(r'persist|disappear|lethal fraction|\bLF\b|censor|biological replicate|1,833|1,819|five 384', re.I)
paragraphs = []
for index, node in enumerate(tree.iter('p')):
    text = ''.join(node.itertext())
    if pattern.search(text):
        paragraphs.append({'paragraph_index': index, 'text': text})
DEST.parent.mkdir(parents=True, exist_ok=True)
with DEST.open('x', encoding='utf-8') as f:
    json.dump({'source': str(SOURCE.relative_to(ROOT)),
               'sha256': hashlib.sha256(body).hexdigest(),
               'scope': 'retained primary narrative only; no workbook/response arrays/network',
               'paragraphs': paragraphs}, f, ensure_ascii=False, indent=2)
    f.write('\n')
for p in paragraphs:
    if re.search(r'persist|disappear|lethal fraction.*\(|censor', p['text'], re.I):
        print(json.dumps(p, ensure_ascii=False))
