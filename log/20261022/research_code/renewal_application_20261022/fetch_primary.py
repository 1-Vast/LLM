"""Full primary texts selected from retained discovery; failures stay evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/root_sources'


def main():
    for pmcid in ('PMC13663777', 'PMC13557097'):
        path = OUT / (pmcid + '.body')
        assert not path.exists()
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/' + pmcid + '/fullTextXML'
        response = requests.get(url, timeout=45)
        path.write_bytes(response.content)
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'requested_url': url, 'final_url': response.url,
                   'status': response.status_code, 'bytes': len(response.content),
                   'sha256': hashlib.sha256(response.content).hexdigest()}
        (OUT / (pmcid + '.http.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        if response.status_code != 200:
            print(json.dumps(receipt))
            continue
        root = ET.fromstring(response.content)
        paragraphs = [' '.join(''.join(node.itertext()).split()) for node in root.iter()
                      if node.tag in ('article-title', 'title', 'p')]
        (OUT / (pmcid + '.txt')).write_text('\n\n'.join(paragraphs) + '\n', encoding='utf-8')
        selected = [p for p in paragraphs if any(word in p.lower() for word in
                    ('code availability', 'data availability', 'github', 'active learning', 'identifia', 'outperform', 'benchmark'))]
        print(json.dumps({'receipt': receipt, 'first_paragraphs': paragraphs[:5], 'relevant': selected[:8]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
