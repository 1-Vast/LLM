"""Reuse saved primary XML for published sequence-design statements only."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

LOG = Path('log/20261022/intervention_dynamics_renewal')


def text(node):
    return re.sub(r'\s+', ' ', ''.join(node.itertext())).strip() if node is not None else ''


def main():
    root = ET.fromstring((LOG / 'functional_scout/RESPONSE_03_melanoma_sequence_fulltext.bin').read_bytes())
    out = {'source': 'Reused primary XML; no new GET', 'fig4_captions': [], 'sequence_paragraphs': []}
    for fig in root.findall('.//fig'):
        if text(fig.find('label')).lower().replace(' ', '') in ('fig.4', 'fig4', 'figure4'):
            out['fig4_captions'].append({'label': text(fig.find('label')), 'caption': text(fig.find('caption'))})
    for sec in root.findall('.//sec'):
        title = text(sec.find('title'))
        for p in sec.findall('p'):
            value = text(p)
            if re.search(r'sequential|following the 24|three technical|three independent experiments', value, re.I):
                out['sequence_paragraphs'].append({'section': title, 'text': value})
    (LOG / 'melanoma_sequence/PRIMARY_DESIGN_ALIGNMENT.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
