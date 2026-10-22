"""Read already-downloaded primary text and supplementary identity metadata only."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/functional_dynamics_gate/functional_auditor'
SOURCE = OUT / 'RESPONSE_05_05_primary_efetch.body'


def main():
    body = SOURCE.read_bytes()
    root = ET.fromstring(body)
    excerpts = []
    keywords = ['replicate', 'independent', 'biological', 'supplement', 'data avail', 'figshare',
                'github', 'three times', 'technical', '1,819', '1819', 'every 2', 'every 4',
                '48 h', '72 h', '96 h', 'cell lines', 'HT-1080', 'T98G', 'NucLight', 'IncuCyte']
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] != 'p':
            continue
        text = ' '.join(''.join(element.itertext()).split())
        matches = [word for word in keywords if word.casefold() in text.casefold()]
        if matches:
            excerpts.append({'matched_keywords': matches, 'text': text})
    supplements = []
    links = []
    for element in root.iter():
        tag = element.tag.rsplit('}', 1)[-1]
        if tag == 'supplementary-material':
            supplements.append({'attributes': element.attrib,
                                'text': ' '.join(''.join(element.itertext()).split()),
                                'media': [{'tag': node.tag, 'attributes': node.attrib} for node in element.iter()
                                          if any('href' in name for name in node.attrib)]})
        if tag == 'ext-link':
            links.append({'attributes': element.attrib, 'text': ''.join(element.itertext())})
    result = {'source_sha256': hashlib.sha256(body).hexdigest(), 'supplementary_objects': supplements,
              'external_links': links, 'primary_method_excerpts': excerpts,
              'response_array_access': False}
    with (OUT / 'PRIMARY_EVIDENCE.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
