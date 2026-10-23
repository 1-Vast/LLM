"""Retained literature-only details; no additional network or assay reads."""
import hashlib
import json
import re
from pathlib import Path
from skeptic_project import OUT, Paragraphs

sources = {
    'specrsi_reused': Path('log/20261022/functional_dynamics_gate/skeptic/SPECRSI_PRIMARY.body'),
    'vclmu_v1': OUT / 'vclmu_v1.body',
    'adaptive_v2': OUT / 'adaptive_v2.body',
    'vcworld_v1': OUT / 'vcworld_v1.body',
    'cellforge_v1': OUT / 'cellforge_v1.body',
}
details = {}
for label, path in sources.items():
    body = path.read_bytes()
    html = body.decode('utf-8', errors='replace')
    parsed = Paragraphs()
    parsed.feed(html)
    selected = []
    if label == 'specrsi_reused':
        selected = [item for item in parsed.items if re.search(
            r'biology|biological|scientific domain|simulat|same.state|starting.artifact|\breset\b',
            item['text'], re.I)]
    details[label] = {
        'source': str(path), 'sha256': hashlib.sha256(body).hexdigest(),
        'document_date_strings': re.findall(r'\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}|20\d{2}-\d{2}-\d{2})\b', html)[:15],
        'meta': re.findall(r'<meta\b[^>]+>', html)[:25],
        'selected': selected,
        'tail_complete': '</html>' in html[-2000:].lower(),
    }
output = OUT / 'SOURCE_DETAILS.json'
if output.exists():
    raise RuntimeError('Do not overwrite source projection')
output.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: {'dates': value['document_date_strings'],
                        'selected_paragraphs': len(value['selected']),
                        'tail_complete': value['tail_complete']}
                  for key, value in details.items()}, ensure_ascii=False))
