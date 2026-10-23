"""Source identities only; no biological value analysis."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_source_qualification'
SOURCE = ROOT / 'log/20261022/early_update_mechanism/biology/decryptE_fulltext.xml'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = SOURCE.read_bytes()
    tree = ET.fromstring(raw)
    records = []
    for elem in tree.iter():
        if elem.tag in ('supplementary-material', 'media', 'ext-link'):
            hrefs = {k: v for k, v in elem.attrib.items() if 'href' in k}
            if elem.tag != 'ext-link' or any(x in str(hrefs).lower() for x in ('proteomics', 'massive', 'shiny', 'supp', 'github')):
                records.append({'tag': elem.tag, 'attributes': elem.attrib,
                                'text': ' '.join(''.join(elem.itertext()).split())})
    result = {'source': str(SOURCE), 'sha256': hashlib.sha256(raw).hexdigest(),
              'decoded': 'archived article XML only, no supplementary tables',
              'records': records}
    (OUT / 'AUTHOR_LINKS.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
