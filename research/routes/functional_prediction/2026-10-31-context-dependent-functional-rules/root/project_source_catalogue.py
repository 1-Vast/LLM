"""Project only original EGI supplement identities; never response cells."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
source = Path('D:/MAESTRO/reference/papers/doi-10.1016-j.molcel.2026.01.025/supp-04_primary_fulltext.xml')
root = ET.fromstring(source.read_bytes())
rows = []
for node in root.iter('supplementary-material'):
    rows.append({'id': node.get('id'),
                 'label': ' '.join(node.findtext('label', '').split()),
                 'caption': ' '.join(' '.join(node.find('caption').itertext()).split()) if node.find('caption') is not None else '',
                 'links': [{key: value for key, value in element.attrib.items()} for element in node.iter('media')]})
result = {'scope': 'Supplement labels/captions/media attributes only. No article response prose, numerical cells or counts.',
          'source_path': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'supplements': rows}
(HERE/'egi_supplement_catalogue.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
