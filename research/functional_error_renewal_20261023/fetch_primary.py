"""Read the exact BeatAML original from its authenticated PMC record."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/functional_error_renewal/root_sources'
name = sys.argv[1] if len(sys.argv) > 1 else 'beataml_primary'
url = (sys.argv[2] if len(sys.argv) > 2 else
       'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9378589/fullTextXML')
target = OUT/f'{name}.receipt.json'
if target.exists():
    raise FileExistsError(target)
receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat())
try:
    result = requests.get(url, timeout=45)
    body = result.content
    (OUT/f'{name}.body').write_bytes(body)
    receipt.update(status=result.status_code, bytes=len(body), final_url=result.url,
                   sha256=hashlib.sha256(body).hexdigest())
    if result.status_code == 200:
        tree = ET.fromstring(body)
        sections = []
        for section in tree.findall('.//sec'):
            title = section.find('title')
            heading = ''.join(title.itertext()) if title is not None else ''
            paragraphs = [''.join(node.itertext()) for node in section if node.tag in {'p', 'title'}]
            if paragraphs:
                sections.append('\n'.join(paragraphs))
        if not sections:
            sections = [''.join(p.itertext()) for p in tree.findall('.//passage/text')]
        (OUT/f'{name}.txt').write_text('\n\n'.join(sections), encoding='utf-8')
except (requests.RequestException, ET.ParseError) as error:
    receipt.update(error=type(error).__name__)
target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
